"""
Akıllı İş - Workflow Bridge Module

Circular import sorununu önlemek için köprü fonksiyonları.
Diğer modüller bu fonksiyonları kullanarak workflow başlatabilir.

Kullanım:
    from modules.workflow.bridge import start_workflow_for_document

    # Satın alma talebi onaya gönderildiğinde
    instance_id = start_workflow_for_document(
        table_name="purchase_requests",
        document_id=request.id,
        initiated_by=user_id,
        document_no=request.request_no,
        context={"total_amount": 15000}
    )
"""

from typing import Any, Dict, List, Optional


def start_workflow_for_document(
    table_name: str,
    document_id: int,
    initiated_by: int,
    document_no: str = None,
    context: Dict[str, Any] = None,
) -> Optional[int]:
    """
    Döküman için uygun workflow'u bulur ve başlatır.

    Lazy import ile circular import önlenir.

    Args:
        table_name: Hedef tablo adı (örn: "purchase_requests")
        document_id: Döküman ID'si
        initiated_by: Başlatan kullanıcı ID'si
        document_no: Döküman numarası (görüntüleme için)
        context: Koşul değerlendirmesi için ek veriler (örn: {"total_amount": 15000})

    Returns:
        Başlatılan workflow instance ID'si veya None (uygun workflow yoksa)

    Example:
        >>> instance_id = start_workflow_for_document(
        ...     table_name="purchase_requests",
        ...     document_id=123,
        ...     initiated_by=1,
        ...     document_no="PR-2026-0001",
        ...     context={"total_amount": 50000, "department": "IT"}
        ... )
    """
    # Lazy import - circular import önleme
    from modules.workflow.services import WorkflowService

    try:
        service = WorkflowService()
        instance = service.start_workflow(
            table_name=table_name,
            document_id=document_id,
            initiated_by=initiated_by,
            document_no=document_no,
            context=context,
        )
        return instance.id if instance else None
    except Exception as e:
        print(f"[Workflow Bridge] Workflow başlatma hatası: {e}")
        return None


def get_document_workflow_status(
    table_name: str, document_id: int
) -> Optional[Dict[str, Any]]:
    """
    Dökümanın aktif workflow durumunu getirir.

    Args:
        table_name: Hedef tablo adı
        document_id: Döküman ID'si

    Returns:
        Workflow durumu dict veya None:
        {
            "instance_id": int,
            "workflow_name": str,
            "status": str,  # "pending", "approved", "rejected", "cancelled"
            "current_step": str,
            "initiated_by": str,
            "initiated_at": datetime,
            "can_approve": bool,  # Mevcut kullanıcı onaylayabilir mi
        }
    """
    from modules.workflow.services import WorkflowService

    try:
        service = WorkflowService()
        instance = service.get_document_workflow(table_name, document_id)

        if not instance:
            return None

        # WorkflowInstance objesini dict'e çevir
        return {
            "instance_id": instance.id,
            "workflow_name": instance.workflow.name if instance.workflow else None,
            "status": instance.status.value if instance.status else None,
            "current_step": instance.current_step.name if instance.current_step else None,
            "initiated_by": instance.initiated_by,
            "initiated_at": instance.initiated_at,
            "can_approve": True,  # TODO: Yetki kontrolü eklenebilir
        }
    except Exception as e:
        print(f"[Workflow Bridge] Workflow durumu alma hatası: {e}")
        return None


def process_workflow_action(
    instance_id: int,
    user_id: int,
    action: str,
    comment: str = None,
    delegate_to: int = None,
) -> bool:
    """
    Workflow aksiyonu işler (onay/red/delegasyon).

    Args:
        instance_id: Workflow instance ID'si
        user_id: İşlemi yapan kullanıcı ID'si
        action: Aksiyon türü ("approve", "reject", "delegate", "request_info")
        comment: Yorum/gerekçe
        delegate_to: Delegasyon için hedef kullanıcı ID'si

    Returns:
        İşlem başarılı mı
    """
    from modules.workflow.services import WorkflowService

    try:
        service = WorkflowService()
        result = service.process_action(
            instance_id=instance_id,
            user_id=user_id,
            action=action,
            comment=comment,
            delegate_to=delegate_to,
        )
        return result is not None
    except Exception as e:
        print(f"[Workflow Bridge] Aksiyon işleme hatası: {e}")
        return False


def get_pending_approvals_for_user(user_id: int) -> List[Dict[str, Any]]:
    """
    Kullanıcının onay bekleyen dökümanlarını getirir.

    Args:
        user_id: Kullanıcı ID'si

    Returns:
        Onay bekleyen dökümanların listesi:
        [
            {
                "instance_id": int,
                "document_table": str,
                "document_id": int,
                "document_no": str,
                "workflow_name": str,
                "step_name": str,
                "initiated_by": str,
                "initiated_at": datetime,
            },
            ...
        ]
    """
    from modules.workflow.services import WorkflowService

    try:
        service = WorkflowService()
        instances = service.get_pending_approvals(user_id)

        # WorkflowInstance nesnelerini dict'e çevir
        result = []
        for inst in instances:
            result.append({
                "instance_id": inst.id,
                "document_table": inst.document_table,
                "document_id": inst.document_id,
                "document_no": inst.document_no,
                "workflow_name": inst.workflow.name if inst.workflow else "",
                "step_name": inst.current_step.name if inst.current_step else "",
                "initiated_by": inst.initiator.full_name if inst.initiator else "?",
                "initiated_at": inst.initiated_at,
            })
        return result
    except Exception as e:
        print(f"[Workflow Bridge] Bekleyen onayları alma hatası: {e}")
        return []


def get_workflow_timeline(instance_id: int) -> List[Dict[str, Any]]:
    """
    Workflow tarihçesini timeline formatında getirir.

    Args:
        instance_id: Workflow instance ID'si

    Returns:
        Timeline olayları listesi:
        [
            {
                "type": str,  # "start", "approve", "reject", "delegate", "complete"
                "step_name": str,
                "user_name": str,
                "action": str,
                "comment": str,
                "timestamp": datetime,
            },
            ...
        ]
    """
    from modules.workflow.services import WorkflowService

    try:
        service = WorkflowService()
        return service.get_workflow_history(instance_id)
    except Exception as e:
        print(f"[Workflow Bridge] Timeline alma hatası: {e}")
        return []


def cancel_workflow(instance_id: int, user_id: int, reason: str = None) -> bool:
    """
    Aktif workflow'u iptal eder.

    Args:
        instance_id: Workflow instance ID'si
        user_id: İptal eden kullanıcı ID'si
        reason: İptal gerekçesi

    Returns:
        İptal başarılı mı
    """
    from modules.workflow.services import WorkflowService
    from database.models.workflow import WorkflowStatus

    try:
        service = WorkflowService()
        instance = service.get_instance(instance_id)

        if not instance:
            return False

        if instance.status != WorkflowStatus.PENDING:
            print(f"[Workflow Bridge] Sadece bekleyen akışlar iptal edilebilir")
            return False

        # İptal işlemi
        instance.status = WorkflowStatus.CANCELLED
        instance.final_comment = reason or "Kullanıcı tarafından iptal edildi"

        from datetime import datetime

        instance.completed_at = datetime.now()

        service.session.commit()

        # Audit log
        service._log_audit(
            table_name=instance.document_table,
            record_id=instance.document_id,
            action="workflow_cancelled",
            user_id=user_id,
            details={"instance_id": instance_id, "reason": reason},
        )

        return True
    except Exception as e:
        print(f"[Workflow Bridge] Workflow iptal hatası: {e}")
        return False
