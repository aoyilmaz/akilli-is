"""
Akıllı İş - Workflow (İş Akışı) Modülü

SAP standartlarında dinamik onay akışı yönetimi.
Farklı modüllerdeki dökümanların onay süreçlerini merkezi olarak yönetir.

Kullanım:
    from modules.workflow import WorkflowService

    service = WorkflowService()
    instance = service.start_workflow("purchase_requests", doc_id, user_id)
    service.process_action(instance.id, user_id, "approve", "Onaylandı")
"""

from .services import WorkflowService, WorkflowError, ConditionEvaluator

__all__ = ["WorkflowService", "WorkflowError", "ConditionEvaluator"]
