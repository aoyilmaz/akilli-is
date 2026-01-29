"""
Akıllı İş - Workflow (İş Akışı) Modelleri
SAP standartlarında dinamik onay akışı yönetimi

Modeller:
- WorkflowDefinition: Akış tanımı (hangi tablo için hangi adımlar)
- WorkflowStep: Akış adımları (kim onaylayacak, koşullar)
- WorkflowInstance: Başlatılmış akış örneği
- WorkflowAction: Onay/red aksiyonları
"""

import enum
from datetime import datetime
from sqlalchemy import (
    Column,
    Integer,
    String,
    Text,
    Boolean,
    DateTime,
    ForeignKey,
    Enum,
    Index,
)
from sqlalchemy.orm import relationship

from database.base import BaseModel


class WorkflowStatus(enum.Enum):
    """İş akışı durumları"""

    PENDING = "pending"  # Onay bekliyor
    APPROVED = "approved"  # Onaylandı
    REJECTED = "rejected"  # Reddedildi
    CANCELLED = "cancelled"  # İptal edildi


class WorkflowActionType(enum.Enum):
    """Aksiyon türleri"""

    APPROVE = "approve"
    REJECT = "reject"
    DELEGATE = "delegate"  # Başkasına devret
    REQUEST_INFO = "request_info"  # Bilgi talep et


class WorkflowDefinition(BaseModel):
    """
    İş Akışı Tanımı

    Hangi tablo için hangi onay adımlarının uygulanacağını tanımlar.
    Örn: purchase_requests tablosu için "Satın Alma Onay Akışı"

    Attributes:
        code: Benzersiz akış kodu (örn: "PR_APPROVAL")
        name: Akış adı
        target_table: Hedef tablo adı (örn: "purchase_requests")
        is_default: Bu tablo için varsayılan akış mı?
        priority: Birden fazla akış varsa öncelik
        activation_condition: Bu akışın ne zaman uygulanacağı (Python ifadesi)
    """

    __tablename__ = "workflow_definitions"

    code = Column(String(50), unique=True, nullable=False, index=True)
    name = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)

    # Hedef tablo (hangi modül/tablo için)
    target_table = Column(String(100), nullable=False, index=True)

    # Aktiflik ve öncelik
    is_default = Column(Boolean, default=False)
    priority = Column(Integer, default=0)

    # Koşul (bu akışın ne zaman uygulanacağı)
    # Örn: "total_amount > 50000" -> Büyük tutarlı talepler için farklı akış
    activation_condition = Column(Text, nullable=True)

    # İlişkiler
    steps = relationship(
        "WorkflowStep",
        back_populates="workflow",
        cascade="all, delete-orphan",
        order_by="WorkflowStep.step_order",
    )
    instances = relationship("WorkflowInstance", back_populates="workflow")

    __table_args__ = (
        Index("idx_wf_def_table", "target_table"),
        Index("idx_wf_def_active", "is_active", "target_table"),
    )

    def __repr__(self):
        return f"<WorkflowDefinition(code={self.code}, table={self.target_table})>"


class WorkflowStep(BaseModel):
    """
    İş Akışı Adımı

    Her adımda kimin onaylaması gerektiğini ve koşulları tanımlar.

    Onaylayıcı Belirleme (en az biri dolu olmalı):
        - required_role_id: Belirli bir role sahip kullanıcılar
        - required_permission_code: Belirli bir izne sahip kullanıcılar
        - approver_user_id: Sabit bir kullanıcı
        - dynamic_approver_field: Döküman alanından dinamik (örn: "requested_by.manager_id")
    """

    __tablename__ = "workflow_steps"

    workflow_id = Column(
        Integer,
        ForeignKey("workflow_definitions.id", ondelete="CASCADE"),
        nullable=False,
    )

    step_order = Column(Integer, nullable=False)  # 1, 2, 3...
    name = Column(String(200), nullable=False)  # "Departman Müdürü Onayı"
    description = Column(Text, nullable=True)

    # Onaylayıcı belirleme seçenekleri
    required_role_id = Column(Integer, ForeignKey("roles.id"), nullable=True)
    required_permission_code = Column(String(100), nullable=True)
    approver_user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    dynamic_approver_field = Column(String(200), nullable=True)

    # Koşullu adım
    # Örn: "total_amount > 10000" -> Sadece 10K üstü için bu adım
    condition_script = Column(Text, nullable=True)

    # Zaman aşımı (saat)
    timeout_hours = Column(Integer, nullable=True)
    timeout_action = Column(
        String(50), default="escalate"
    )  # escalate, auto_approve, auto_reject

    # Son adım mı?
    is_final_step = Column(Boolean, default=False)

    # Paralel onay için
    is_parallel = Column(Boolean, default=False)  # Bir önceki adımla paralel mi?
    requires_all = Column(
        Boolean, default=True
    )  # Tüm onaylayıcılar mı, herhangi biri mi?

    # İlişkiler
    workflow = relationship("WorkflowDefinition", back_populates="steps")
    required_role = relationship("Role", foreign_keys=[required_role_id])
    approver_user = relationship("User", foreign_keys=[approver_user_id])

    __table_args__ = (Index("idx_wf_step_workflow", "workflow_id", "step_order"),)

    def __repr__(self):
        return f"<WorkflowStep(order={self.step_order}, name={self.name})>"


class WorkflowInstance(BaseModel):
    """
    İş Akışı Örneği

    Bir döküman için başlatılmış iş akışı.
    Her döküman için aynı anda sadece bir aktif instance olabilir.
    """

    __tablename__ = "workflow_instances"

    workflow_id = Column(
        Integer, ForeignKey("workflow_definitions.id"), nullable=False
    )

    # Hangi döküman
    document_table = Column(String(100), nullable=False)
    document_id = Column(Integer, nullable=False)
    document_no = Column(String(100), nullable=True)  # Görüntüleme için

    # Mevcut durum
    current_step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=True)
    status = Column(
        Enum(WorkflowStatus, values_callable=lambda x: [e.value for e in x]),
        default=WorkflowStatus.PENDING
    )

    # Kim başlattı
    initiated_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    initiated_at = Column(DateTime, default=datetime.now)

    # Sonuç
    completed_at = Column(DateTime, nullable=True)
    final_comment = Column(Text, nullable=True)

    # İlişkiler
    workflow = relationship("WorkflowDefinition", back_populates="instances")
    current_step = relationship("WorkflowStep", foreign_keys=[current_step_id])
    initiator = relationship("User", foreign_keys=[initiated_by])
    actions = relationship(
        "WorkflowAction",
        back_populates="instance",
        cascade="all, delete-orphan",
        order_by="WorkflowAction.created_at",
    )

    __table_args__ = (
        Index("idx_wf_inst_doc", "document_table", "document_id"),
        Index("idx_wf_inst_status", "status"),
    )

    def __repr__(self):
        return f"<WorkflowInstance(doc={self.document_table}:{self.document_id}, status={self.status.value})>"


class WorkflowAction(BaseModel):
    """
    İş Akışı Aksiyonu

    Her onay/red işleminin kaydı. Tam tarihçe için.
    """

    __tablename__ = "workflow_actions"

    instance_id = Column(
        Integer,
        ForeignKey("workflow_instances.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_id = Column(Integer, ForeignKey("workflow_steps.id"), nullable=False)

    # Kim, ne zaman
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    action = Column(
        Enum(WorkflowActionType, values_callable=lambda x: [e.value for e in x]),
        nullable=False
    )

    # Yorum
    comment = Column(Text, nullable=True)

    # Delegasyon için
    delegated_to = Column(Integer, ForeignKey("users.id"), nullable=True)
    delegation_reason = Column(Text, nullable=True)

    # İlişkiler
    instance = relationship("WorkflowInstance", back_populates="actions")
    step = relationship("WorkflowStep")
    user = relationship("User", foreign_keys=[user_id])
    delegate = relationship("User", foreign_keys=[delegated_to])

    __table_args__ = (
        Index("idx_wf_action_instance", "instance_id"),
        Index("idx_wf_action_user", "user_id"),
    )

    def __repr__(self):
        return f"<WorkflowAction(action={self.action.value}, user={self.user_id})>"
