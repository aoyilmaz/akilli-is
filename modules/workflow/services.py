"""
Akıllı İş - Workflow Engine Servisi

SAP standartlarında dinamik onay akışı yönetimi.

Özellikler:
- Koşullu akış seçimi (total_amount > 10000 gibi)
- Rol/izin/kullanıcı bazlı onaylayıcı belirleme
- Dinamik onaylayıcı (döküman alanından)
- Delegasyon ve bilgi talebi desteği
- AuditLog entegrasyonu
- Bildirim sistemi entegrasyonu
"""

from typing import Optional, List, Dict, Any, Tuple
from datetime import datetime
from decimal import Decimal

from sqlalchemy.orm import joinedload

from database.base import get_session
from database.models.workflow import (
    WorkflowDefinition,
    WorkflowStep,
    WorkflowInstance,
    WorkflowAction,
    WorkflowStatus,
    WorkflowActionType,
)
from database.models.user import User, Role, AuditLog


class WorkflowError(Exception):
    """Workflow işlem hatası"""

    pass


class ConditionEvaluator:
    """
    Güvenli koşul değerlendirici.

    eval() yerine kısıtlı bir parser kullanır.
    Desteklenen operatörler: >, <, >=, <=, ==, !=, and, or, in

    Kullanım:
        evaluator = ConditionEvaluator()
        result = evaluator.evaluate("total_amount > 10000", {"total_amount": 15000})
        # result = True
    """

    ALLOWED_OPERATORS = {
        ">": lambda a, b: a > b,
        "<": lambda a, b: a < b,
        ">=": lambda a, b: a >= b,
        "<=": lambda a, b: a <= b,
        "==": lambda a, b: a == b,
        "!=": lambda a, b: a != b,
    }

    @classmethod
    def evaluate(cls, condition: str, context: Dict[str, Any]) -> bool:
        """
        Koşulu değerlendir.

        Args:
            condition: "total_amount > 10000" gibi bir ifade
            context: {"total_amount": 15000, "department": "IT"} gibi değerler

        Returns:
            True/False
        """
        if not condition or not condition.strip():
            return True

        condition = condition.strip()

        # "and" ile bölünmüş koşullar
        if " and " in condition.lower():
            parts = condition.split(" and ")
            if len(parts) == 2:
                return cls._evaluate_single(
                    parts[0].strip(), context
                ) and cls._evaluate_single(parts[1].strip(), context)

        # "or" ile bölünmüş koşullar
        if " or " in condition.lower():
            parts = condition.split(" or ")
            if len(parts) == 2:
                return cls._evaluate_single(
                    parts[0].strip(), context
                ) or cls._evaluate_single(parts[1].strip(), context)

        return cls._evaluate_single(condition, context)

    @classmethod
    def _evaluate_single(cls, condition: str, context: Dict[str, Any]) -> bool:
        """Tek bir koşulu değerlendir."""
        # Operatörü bul (uzundan kısaya sırala)
        for op_str in [">=", "<=", "!=", "==", ">", "<"]:
            if op_str in condition:
                parts = condition.split(op_str)
                if len(parts) == 2:
                    left = cls._get_value(parts[0].strip(), context)
                    right = cls._get_value(parts[1].strip(), context)

                    # Tip dönüşümü
                    if isinstance(left, (int, float, Decimal)):
                        try:
                            if isinstance(right, str):
                                right = type(left)(right)
                        except (ValueError, TypeError):
                            pass

                    op_func = cls.ALLOWED_OPERATORS[op_str]
                    return op_func(left, right)

        # "in" operatörü
        if " in " in condition:
            parts = condition.split(" in ")
            if len(parts) == 2:
                item = cls._get_value(parts[0].strip(), context)
                collection = cls._get_value(parts[1].strip(), context)
                if isinstance(collection, (list, tuple, set, str)):
                    return item in collection

        return True  # Anlaşılamayan koşul için True

    @classmethod
    def _get_value(cls, token: str, context: Dict[str, Any]) -> Any:
        """Token'dan değer al."""
        # String literal
        if token.startswith(("'", '"')) and token.endswith(("'", '"')):
            return token[1:-1]

        # Sayı
        try:
            if "." in token:
                return float(token)
            return int(token)
        except ValueError:
            pass

        # Liste literal [a, b, c]
        if token.startswith("[") and token.endswith("]"):
            items = token[1:-1].split(",")
            return [cls._get_value(i.strip(), context) for i in items]

        # Context'ten al (nested field desteği: "user.department.code")
        if "." in token:
            parts = token.split(".")
            value = context
            for part in parts:
                if isinstance(value, dict):
                    value = value.get(part)
                elif hasattr(value, part):
                    value = getattr(value, part)
                else:
                    return None
            return value

        return context.get(token, token)


class WorkflowService:
    """
    Workflow Engine Ana Servisi

    Kullanım:
        service = WorkflowService()

        # Akış başlat
        instance = service.start_workflow("purchase_requests", request.id, user.id)

        # Onay/Red işle
        success, msg = service.process_action(instance.id, user.id, "approve", "Uygun")
    """

    def __init__(self):
        self.session = get_session()
        self.evaluator = ConditionEvaluator()

    # ========================
    # WORKFLOW BAŞLATMA
    # ========================

    def start_workflow(
        self,
        table_name: str,
        document_id: int,
        initiated_by: int,
        document_no: str = None,
        context: Dict[str, Any] = None,
    ) -> Optional[WorkflowInstance]:
        """
        Döküman için uygun iş akışını başlat.

        Args:
            table_name: Hedef tablo adı (örn: "purchase_requests")
            document_id: Döküman ID'si
            initiated_by: Başlatan kullanıcı ID'si
            document_no: Görüntüleme için döküman numarası
            context: Koşul değerlendirmesi için ek bağlam

        Returns:
            WorkflowInstance veya None (akış bulunamazsa)

        Raises:
            WorkflowError: Akış zaten başlatılmışsa
        """
        # Uygun workflow'u bul
        workflow = self._find_applicable_workflow(table_name, context or {})
        if not workflow:
            return None

        # Mevcut aktif instance var mı kontrol et
        existing = (
            self.session.query(WorkflowInstance)
            .filter(
                WorkflowInstance.document_table == table_name,
                WorkflowInstance.document_id == document_id,
                WorkflowInstance.status == WorkflowStatus.PENDING,
            )
            .first()
        )

        if existing:
            raise WorkflowError(
                f"Bu döküman için zaten aktif bir onay süreci var (#{existing.id})"
            )

        # İlk adımı bul
        first_step = self._get_first_applicable_step(workflow, context or {})
        if not first_step:
            raise WorkflowError("Workflow için uygun adım bulunamadı")

        # Instance oluştur
        instance = WorkflowInstance(
            workflow_id=workflow.id,
            document_table=table_name,
            document_id=document_id,
            document_no=document_no,
            current_step_id=first_step.id,
            status=WorkflowStatus.PENDING,
            initiated_by=initiated_by,
            initiated_at=datetime.now(),
        )

        self.session.add(instance)
        self.session.commit()

        # Audit log
        self._log_audit(
            user_id=initiated_by,
            action="WORKFLOW_START",
            module="workflow",
            table_name=table_name,
            record_id=document_id,
            description=f"İş akışı başlatıldı: {workflow.name}",
        )

        # Bildirim gönder (ilk adımdaki onaylayıcılara)
        self._notify_approvers(instance, first_step)

        return instance

    def _find_applicable_workflow(
        self, table_name: str, context: Dict[str, Any]
    ) -> Optional[WorkflowDefinition]:
        """Tablo ve koşullara göre uygun workflow'u bul."""
        workflows = (
            self.session.query(WorkflowDefinition)
            .filter(
                WorkflowDefinition.target_table == table_name,
                WorkflowDefinition.is_active == True,
            )
            .order_by(WorkflowDefinition.priority.desc())
            .all()
        )

        for wf in workflows:
            # Aktivasyon koşulunu kontrol et
            if wf.activation_condition:
                if self.evaluator.evaluate(wf.activation_condition, context):
                    return wf
            elif wf.is_default:
                return wf

        # Varsayılan akışı döndür
        return next(
            (wf for wf in workflows if wf.is_default), workflows[0] if workflows else None
        )

    def _get_first_applicable_step(
        self, workflow: WorkflowDefinition, context: Dict[str, Any]
    ) -> Optional[WorkflowStep]:
        """İlk uygulanabilir adımı bul."""
        for step in workflow.steps:
            if step.condition_script:
                if self.evaluator.evaluate(step.condition_script, context):
                    return step
            else:
                return step
        return None

    # ========================
    # AKSİYON İŞLEME
    # ========================

    def process_action(
        self,
        instance_id: int,
        user_id: int,
        action: str,  # "approve", "reject", "delegate"
        comment: str = None,
        delegate_to: int = None,
    ) -> Tuple[bool, str]:
        """
        Kullanıcının onay/red işlemini işle.

        Args:
            instance_id: Workflow instance ID
            user_id: İşlemi yapan kullanıcı ID
            action: "approve", "reject", "delegate", "request_info"
            comment: Yorum
            delegate_to: Delegasyon için hedef kullanıcı ID

        Returns:
            (success: bool, message: str)
        """
        instance = (
            self.session.query(WorkflowInstance)
            .options(
                joinedload(WorkflowInstance.workflow).joinedload(
                    WorkflowDefinition.steps
                ),
                joinedload(WorkflowInstance.current_step),
            )
            .filter(WorkflowInstance.id == instance_id)
            .first()
        )

        if not instance:
            return False, "İş akışı bulunamadı"

        if instance.status != WorkflowStatus.PENDING:
            return False, f"Bu iş akışı zaten {instance.status.value} durumunda"

        current_step = instance.current_step
        if not current_step:
            return False, "Mevcut adım bulunamadı"

        # Kullanıcının bu adımı onaylama yetkisi var mı?
        if not self._can_user_approve(user_id, current_step, instance):
            return False, "Bu adımı onaylama yetkiniz yok"

        # Aksiyon tipini belirle
        try:
            action_type = WorkflowActionType(action.lower())
        except ValueError:
            return False, f"Geçersiz aksiyon: {action}"

        # Aksiyon kaydı oluştur
        wf_action = WorkflowAction(
            instance_id=instance.id,
            step_id=current_step.id,
            user_id=user_id,
            action=action_type,
            comment=comment,
            delegated_to=(
                delegate_to if action_type == WorkflowActionType.DELEGATE else None
            ),
            delegation_reason=(
                comment if action_type == WorkflowActionType.DELEGATE else None
            ),
        )
        self.session.add(wf_action)

        # Aksiyona göre işlem
        if action_type == WorkflowActionType.APPROVE:
            return self._handle_approve(instance, current_step, user_id, comment)

        elif action_type == WorkflowActionType.REJECT:
            return self._handle_reject(instance, user_id, comment)

        elif action_type == WorkflowActionType.DELEGATE:
            return self._handle_delegate(
                instance, current_step, user_id, delegate_to, comment
            )

        elif action_type == WorkflowActionType.REQUEST_INFO:
            return self._handle_request_info(instance, user_id, comment)

        return False, "Bilinmeyen aksiyon"

    def _handle_approve(
        self,
        instance: WorkflowInstance,
        current_step: WorkflowStep,
        user_id: int,
        comment: str,
    ) -> Tuple[bool, str]:
        """Onay işlemini yönet."""

        if current_step.is_final_step:
            # Son adım - akışı tamamla
            instance.status = WorkflowStatus.APPROVED
            instance.completed_at = datetime.now()
            instance.final_comment = comment

            # Kaynak dökümanın durumunu güncelle
            self._update_document_status(instance, "approved")

            self.session.commit()

            # Audit log
            self._log_audit(
                user_id=user_id,
                action="WORKFLOW_COMPLETE",
                module="workflow",
                table_name=instance.document_table,
                record_id=instance.document_id,
                description=f"İş akışı onaylandı: {instance.workflow.name}",
            )

            # Başlatana bildirim
            self._notify_completion(instance, approved=True)

            return True, "İş akışı başarıyla tamamlandı"
        else:
            # Sonraki adıma geç
            next_step = self._get_next_step(instance.workflow, current_step)
            if next_step:
                instance.current_step_id = next_step.id
                self.session.commit()

                # Sonraki adımdaki onaylayıcılara bildirim
                self._notify_approvers(instance, next_step)

                return True, f"Onaylandı. Sonraki adım: {next_step.name}"
            else:
                # Sonraki adım yok ama final değil - tamamla
                instance.status = WorkflowStatus.APPROVED
                instance.completed_at = datetime.now()
                self._update_document_status(instance, "approved")
                self.session.commit()

                return True, "İş akışı tamamlandı"

    def _handle_reject(
        self, instance: WorkflowInstance, user_id: int, comment: str
    ) -> Tuple[bool, str]:
        """Red işlemini yönet."""
        instance.status = WorkflowStatus.REJECTED
        instance.completed_at = datetime.now()
        instance.final_comment = comment

        # Kaynak dökümanın durumunu güncelle
        self._update_document_status(instance, "rejected")

        self.session.commit()

        # Audit log
        self._log_audit(
            user_id=user_id,
            action="WORKFLOW_REJECT",
            module="workflow",
            table_name=instance.document_table,
            record_id=instance.document_id,
            description=f"İş akışı reddedildi: {comment}",
        )

        # Başlatana bildirim
        self._notify_completion(instance, approved=False)

        return True, "İş akışı reddedildi"

    def _handle_delegate(
        self,
        instance: WorkflowInstance,
        current_step: WorkflowStep,
        user_id: int,
        delegate_to: int,
        comment: str,
    ) -> Tuple[bool, str]:
        """Delegasyon işlemini yönet."""
        if not delegate_to:
            return False, "Delegasyon için hedef kullanıcı belirtilmeli"

        # Hedef kullanıcıya bildirim
        self._notify_delegation(instance, current_step, user_id, delegate_to, comment)

        self.session.commit()

        return True, "Onay görevi devredildi"

    def _handle_request_info(
        self, instance: WorkflowInstance, user_id: int, comment: str
    ) -> Tuple[bool, str]:
        """Bilgi talep işlemini yönet."""
        # Başlatana bilgi talebi bildirimi
        self._notify_info_request(instance, user_id, comment)

        self.session.commit()

        return True, "Bilgi talebi gönderildi"

    # ========================
    # YARDIMCI METODLAR
    # ========================

    def _can_user_approve(
        self, user_id: int, step: WorkflowStep, instance: WorkflowInstance
    ) -> bool:
        """Kullanıcının bu adımı onaylama yetkisi var mı kontrol et."""
        user = self.session.query(User).filter(User.id == user_id).first()
        if not user:
            return False

        # Sabit kullanıcı kontrolü
        if step.approver_user_id:
            return user_id == step.approver_user_id

        # Rol kontrolü
        if step.required_role_id:
            return any(r.id == step.required_role_id for r in user.roles)

        # İzin kontrolü
        if step.required_permission_code:
            return user.has_permission(step.required_permission_code)

        # Dinamik onaylayıcı (döküman alanından)
        if step.dynamic_approver_field:
            doc = self._get_document(instance.document_table, instance.document_id)
            if doc:
                approver_id = self._get_nested_value(doc, step.dynamic_approver_field)
                return user_id == approver_id

        return False

    def _get_next_step(
        self, workflow: WorkflowDefinition, current_step: WorkflowStep
    ) -> Optional[WorkflowStep]:
        """Bir sonraki adımı bul."""
        for step in workflow.steps:
            if step.step_order > current_step.step_order:
                return step
        return None

    def _get_document(self, table_name: str, doc_id: int) -> Optional[Any]:
        """Dökümanı getir (dinamik)."""
        # Tablo adından model sınıfını bul
        table_model_map = {
            "purchase_requests": (
                "database.models.purchasing",
                "PurchaseRequest",
            ),
            "purchase_orders": (
                "database.models.purchasing",
                "PurchaseOrder",
            ),
            "leave_requests": ("database.models.hr", "Leave"),
            "sales_orders": ("database.models.sales", "SalesOrder"),
            "invoices": ("database.models.sales", "Invoice"),
        }

        model_info = table_model_map.get(table_name)
        if not model_info:
            return None

        try:
            module_path, class_name = model_info
            module = __import__(module_path, fromlist=[class_name])
            model_class = getattr(module, class_name)
            return (
                self.session.query(model_class).filter(model_class.id == doc_id).first()
            )
        except Exception:
            return None

    def _get_nested_value(self, obj: Any, field_path: str) -> Any:
        """Nested alan değerini al (örn: "requested_by.manager_id")."""
        parts = field_path.split(".")
        value = obj
        for part in parts:
            if isinstance(value, dict):
                value = value.get(part)
            elif hasattr(value, part):
                value = getattr(value, part)
            else:
                return None
        return value

    def _update_document_status(self, instance: WorkflowInstance, new_status: str):
        """Kaynak dökümanın durumunu güncelle."""
        doc = self._get_document(instance.document_table, instance.document_id)
        if doc and hasattr(doc, "status"):
            # Status enum'a çevir
            if hasattr(doc.status, "__class__") and hasattr(
                doc.status.__class__, "__members__"
            ):
                # Enum tipinde status
                status_enum = doc.status.__class__
                status_value = new_status.upper()
                if status_value in status_enum.__members__:
                    doc.status = status_enum[status_value]
            else:
                doc.status = new_status

    def _log_audit(
        self,
        user_id: int,
        action: str,
        module: str,
        table_name: str,
        record_id: int,
        description: str,
    ):
        """Audit log kaydı oluştur."""
        user = self.session.query(User).filter(User.id == user_id).first()
        log = AuditLog(
            user_id=user_id,
            username=user.username if user else None,
            action=action,
            module=module,
            table_name=table_name,
            record_id=record_id,
            description=description,
        )
        self.session.add(log)

    def _notify_approvers(self, instance: WorkflowInstance, step: WorkflowStep):
        """Onaylayıcılara bildirim gönder."""
        try:
            from modules.system.services import NotificationService

            approvers = self._get_step_approvers(step, instance)
            for approver_id in approvers:
                NotificationService.create(
                    user_id=approver_id,
                    title="Onay Bekliyor",
                    message=f"{instance.document_no or instance.document_table} için onayınız bekleniyor",
                    notification_type="APPROVAL",
                    module="workflow",
                    reference_type=instance.document_table,
                    reference_id=instance.document_id,
                    action_url=f"/workflow/approve/{instance.id}",
                )
        except ImportError:
            pass  # Bildirim servisi yoksa sessizce geç

    def _notify_completion(self, instance: WorkflowInstance, approved: bool):
        """Tamamlanma bildirimi gönder."""
        try:
            from modules.system.services import NotificationService

            status_text = "onaylandı" if approved else "reddedildi"
            NotificationService.create(
                user_id=instance.initiated_by,
                title=f"İş Akışı {status_text.title()}",
                message=f"{instance.document_no or instance.document_table} {status_text}",
                notification_type="INFO" if approved else "WARNING",
                module="workflow",
                reference_type=instance.document_table,
                reference_id=instance.document_id,
            )
        except ImportError:
            pass

    def _notify_delegation(
        self, instance, step, from_user_id, to_user_id, comment
    ):
        """Delegasyon bildirimi."""
        try:
            from modules.system.services import NotificationService

            NotificationService.create(
                user_id=to_user_id,
                title="Onay Görevi Devredildi",
                message=f"Size bir onay görevi devredildi: {instance.document_no}",
                notification_type="APPROVAL",
                module="workflow",
                reference_type=instance.document_table,
                reference_id=instance.document_id,
            )
        except ImportError:
            pass

    def _notify_info_request(self, instance, user_id, comment):
        """Bilgi talebi bildirimi."""
        try:
            from modules.system.services import NotificationService

            NotificationService.create(
                user_id=instance.initiated_by,
                title="Bilgi Talebi",
                message=f"Onay süreciniz için ek bilgi isteniyor: {comment}",
                notification_type="INFO",
                module="workflow",
                reference_type=instance.document_table,
                reference_id=instance.document_id,
            )
        except ImportError:
            pass

    def _get_step_approvers(
        self, step: WorkflowStep, instance: WorkflowInstance
    ) -> List[int]:
        """Adım için onaylayıcı kullanıcı ID'lerini getir."""
        approvers = []

        if step.approver_user_id:
            approvers.append(step.approver_user_id)

        elif step.required_role_id:
            role = (
                self.session.query(Role).filter(Role.id == step.required_role_id).first()
            )
            if role:
                approvers.extend([u.id for u in role.users if u.is_active])

        elif step.dynamic_approver_field:
            doc = self._get_document(instance.document_table, instance.document_id)
            if doc:
                approver_id = self._get_nested_value(doc, step.dynamic_approver_field)
                if approver_id:
                    approvers.append(approver_id)

        return approvers

    # ========================
    # SORGULAMA METODLARI
    # ========================

    def get_instance(self, instance_id: int) -> Optional[WorkflowInstance]:
        """Instance detaylarını getir."""
        return (
            self.session.query(WorkflowInstance)
            .options(
                joinedload(WorkflowInstance.workflow),
                joinedload(WorkflowInstance.current_step),
                joinedload(WorkflowInstance.actions).joinedload(WorkflowAction.user),
                joinedload(WorkflowInstance.actions).joinedload(WorkflowAction.step),
            )
            .filter(WorkflowInstance.id == instance_id)
            .first()
        )

    def get_document_workflow(
        self, table_name: str, doc_id: int
    ) -> Optional[WorkflowInstance]:
        """Döküman için aktif veya son workflow'u getir."""
        return (
            self.session.query(WorkflowInstance)
            .options(
                joinedload(WorkflowInstance.workflow),
                joinedload(WorkflowInstance.current_step),
                joinedload(WorkflowInstance.actions).joinedload(WorkflowAction.user),
                joinedload(WorkflowInstance.actions).joinedload(WorkflowAction.step),
            )
            .filter(
                WorkflowInstance.document_table == table_name,
                WorkflowInstance.document_id == doc_id,
            )
            .order_by(WorkflowInstance.created_at.desc())
            .first()
        )

    def get_pending_approvals(self, user_id: int) -> List[WorkflowInstance]:
        """Kullanıcının onay bekleyen iş akışlarını getir."""
        pending = (
            self.session.query(WorkflowInstance)
            .options(
                joinedload(WorkflowInstance.workflow),
                joinedload(WorkflowInstance.current_step),
            )
            .filter(WorkflowInstance.status == WorkflowStatus.PENDING)
            .all()
        )

        # Kullanıcının onaylayabileceği olanları filtrele
        result = []
        for inst in pending:
            if inst.current_step and self._can_user_approve(
                user_id, inst.current_step, inst
            ):
                result.append(inst)

        return result

    def get_workflow_history(self, instance_id: int) -> List[Dict]:
        """Workflow tarihçesini getir (timeline için)."""
        instance = self.get_instance(instance_id)
        if not instance:
            return []

        history = []

        # Başlatma
        history.append(
            {
                "type": "start",
                "date": instance.initiated_at,
                "user_id": instance.initiated_by,
                "user_name": instance.initiator.full_name if instance.initiator else "?",
                "description": f"İş akışı başlatıldı: {instance.workflow.name}",
                "step_name": None,
                "comment": None,
            }
        )

        # Aksiyonlar
        for action in instance.actions:
            action_text = {
                WorkflowActionType.APPROVE: "Onayladı",
                WorkflowActionType.REJECT: "Reddetti",
                WorkflowActionType.DELEGATE: "Devretti",
                WorkflowActionType.REQUEST_INFO: "Bilgi talep etti",
            }.get(action.action, str(action.action.value))

            history.append(
                {
                    "type": action.action.value,
                    "date": action.created_at,
                    "user_id": action.user_id,
                    "user_name": action.user.full_name if action.user else "?",
                    "description": action_text,
                    "comment": action.comment,
                    "step_name": action.step.name if action.step else None,
                }
            )

        # Tamamlanma
        if instance.status in [WorkflowStatus.APPROVED, WorkflowStatus.REJECTED]:
            status_text = (
                "Onaylandı" if instance.status == WorkflowStatus.APPROVED else "Reddedildi"
            )
            history.append(
                {
                    "type": "complete",
                    "date": instance.completed_at,
                    "user_id": None,
                    "user_name": "Sistem",
                    "description": f"İş akışı {status_text.lower()}",
                    "step_name": None,
                    "comment": instance.final_comment,
                }
            )

        return history

    # ==================== WORKFLOW DEFINITION CRUD ====================

    def list_workflow_definitions(self) -> List[WorkflowDefinition]:
        """Tüm workflow tanımlarını listele"""
        return (
            self.session.query(WorkflowDefinition)
            .options(joinedload(WorkflowDefinition.steps))
            .order_by(WorkflowDefinition.target_table, WorkflowDefinition.priority.desc())
            .all()
        )

    def get_workflow_definition(self, workflow_id: int) -> Optional[WorkflowDefinition]:
        """Workflow tanımını getir"""
        return (
            self.session.query(WorkflowDefinition)
            .options(joinedload(WorkflowDefinition.steps))
            .filter(WorkflowDefinition.id == workflow_id)
            .first()
        )

    def create_workflow_definition(
        self, data: Dict[str, Any], steps_data: List[Dict[str, Any]] = None
    ) -> WorkflowDefinition:
        """Yeni workflow tanımı oluştur"""
        workflow = WorkflowDefinition(
            code=data.get("code"),
            name=data.get("name"),
            description=data.get("description"),
            target_table=data.get("target_table"),
            activation_condition=data.get("activation_condition"),
            priority=data.get("priority", 0),
            is_default=data.get("is_default", False),
            is_active=data.get("is_active", True),
        )
        self.session.add(workflow)
        self.session.flush()

        # Adımları ekle
        if steps_data:
            for step_data in steps_data:
                step = WorkflowStep(
                    workflow_id=workflow.id,
                    step_order=step_data.get("step_order", 1),
                    name=step_data.get("name"),
                    description=step_data.get("description"),
                    required_role_id=step_data.get("required_role_id"),
                    approver_user_id=step_data.get("approver_user_id"),
                    dynamic_approver_field=step_data.get("dynamic_approver_field"),
                    condition_script=step_data.get("condition_script"),
                    timeout_hours=step_data.get("timeout_hours"),
                    is_final_step=step_data.get("is_final_step", False),
                )
                self.session.add(step)

        self.session.commit()
        return workflow

    def update_workflow_definition(
        self, workflow_id: int, data: Dict[str, Any], steps_data: List[Dict[str, Any]] = None
    ) -> Optional[WorkflowDefinition]:
        """Workflow tanımını güncelle"""
        workflow = self.get_workflow_definition(workflow_id)
        if not workflow:
            return None

        # Ana bilgileri güncelle
        workflow.code = data.get("code", workflow.code)
        workflow.name = data.get("name", workflow.name)
        workflow.description = data.get("description", workflow.description)
        workflow.target_table = data.get("target_table", workflow.target_table)
        workflow.activation_condition = data.get("activation_condition", workflow.activation_condition)
        workflow.priority = data.get("priority", workflow.priority)
        workflow.is_default = data.get("is_default", workflow.is_default)
        workflow.is_active = data.get("is_active", workflow.is_active)

        # Adımları güncelle
        if steps_data is not None:
            # Mevcut adım ID'leri
            existing_ids = {s.id for s in workflow.steps}
            new_ids = {s.get("id") for s in steps_data if s.get("id")}

            # Silinecek adımlar
            for step in list(workflow.steps):
                if step.id not in new_ids:
                    self.session.delete(step)

            # Güncelle veya ekle
            for step_data in steps_data:
                step_id = step_data.get("id")
                if step_id and step_id in existing_ids:
                    # Güncelle
                    step = next((s for s in workflow.steps if s.id == step_id), None)
                    if step:
                        step.step_order = step_data.get("step_order", step.step_order)
                        step.name = step_data.get("name", step.name)
                        step.description = step_data.get("description", step.description)
                        step.required_role_id = step_data.get("required_role_id")
                        step.approver_user_id = step_data.get("approver_user_id")
                        step.dynamic_approver_field = step_data.get("dynamic_approver_field")
                        step.condition_script = step_data.get("condition_script")
                        step.timeout_hours = step_data.get("timeout_hours")
                        step.is_final_step = step_data.get("is_final_step", False)
                else:
                    # Yeni ekle
                    step = WorkflowStep(
                        workflow_id=workflow.id,
                        step_order=step_data.get("step_order", 1),
                        name=step_data.get("name"),
                        description=step_data.get("description"),
                        required_role_id=step_data.get("required_role_id"),
                        approver_user_id=step_data.get("approver_user_id"),
                        dynamic_approver_field=step_data.get("dynamic_approver_field"),
                        condition_script=step_data.get("condition_script"),
                        timeout_hours=step_data.get("timeout_hours"),
                        is_final_step=step_data.get("is_final_step", False),
                    )
                    self.session.add(step)

        self.session.commit()
        return workflow

    def delete_workflow_definition(self, workflow_id: int) -> bool:
        """Workflow tanımını sil"""
        workflow = self.get_workflow_definition(workflow_id)
        if not workflow:
            return False

        # İlişkili instance'lar varsa silme
        instance_count = (
            self.session.query(WorkflowInstance)
            .filter(WorkflowInstance.workflow_id == workflow_id)
            .count()
        )
        if instance_count > 0:
            raise ValueError(
                f"Bu iş akışına bağlı {instance_count} adet aktif süreç var. "
                "Önce bu süreçleri tamamlayın veya iptal edin."
            )

        self.session.delete(workflow)
        self.session.commit()
        return True

    def close(self):
        """Session'ı kapat"""
        if self.session:
            self.session.close()
