"""
Akıllı İş - Üretim Planlama Modülü
"""

from PyQt6.QtWidgets import QWidget, QVBoxLayout, QMessageBox

from .planning_page import ProductionPlanningPage


class PlanningModule(QWidget):
    """Üretim Planlama modülü"""
    
    page_title = "Üretim Planlama"
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.wo_service = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        self.planning_page = ProductionPlanningPage()
        self.planning_page.work_order_clicked.connect(self._on_work_order_clicked)
        self.planning_page.refresh_requested.connect(self._load_data)
        
        layout.addWidget(self.planning_page)
        
    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()
        
    def _ensure_services(self):
        """Servisleri yükle"""
        if not self.wo_service:
            try:
                from modules.production.services import WorkOrderService
                self.wo_service = WorkOrderService()
            except Exception as e:
                print(f"Servis yükleme hatası: {e}")
                
    def _load_data(self):
        """Verileri yükle"""
        if not self.wo_service:
            return
            
        try:
            # Tüm aktif iş emirlerini getir
            work_orders = self.wo_service.get_all()
            
            wo_list = []
            for wo in work_orders:
                # Sadece planlanmış, serbest veya üretimdeki emirleri göster
                if wo.status.value in ["planned", "released", "in_progress", "completed"]:
                    wo_list.append({
                        "id": wo.id,
                        "order_no": wo.order_no,
                        "item_name": wo.item.name if wo.item else "-",
                        "planned_quantity": float(wo.planned_quantity or 0),
                        "completed_quantity": float(wo.completed_quantity or 0),
                        "planned_start": wo.planned_start,
                        "planned_end": wo.planned_end,
                        "progress_rate": float(wo.progress_rate or 0),
                        "priority": wo.priority.value if wo.priority else "normal",
                        "status": wo.status.value if wo.status else "draft",
                    })
            
            self.planning_page.load_data(wo_list)
            
        except Exception as e:
            print(f"Veri yükleme hatası: {e}")
            self.planning_page.load_data([])
            
    def _on_work_order_clicked(self, wo_id: int):
        """İş emrine tıklandığında"""
        # İş emri detayına git veya popup göster
        QMessageBox.information(
            self, 
            "İş Emri", 
            f"İş Emri ID: {wo_id}\n\nDetay görüntüleme için İş Emirleri sayfasına gidin."
        )
