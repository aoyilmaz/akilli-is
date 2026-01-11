"""
Akıllı İş - İş Emirleri Modülü
V5 - Üretime Başla depo seçimi + stok düşürme
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QStackedWidget,
    QMessageBox,
    QDialog,
    QLabel,
    QComboBox,
    QPushButton,
    QHBoxLayout,
    QGridLayout,
    QFrame,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from config.styles import (
    BG_PRIMARY, BG_SECONDARY, BG_TERTIARY, BG_HOVER, BORDER,
    TEXT_PRIMARY, TEXT_MUTED, ACCENT, SUCCESS, WARNING, ERROR,
    get_table_style, get_button_style, get_input_style
)

from .work_order_list import WorkOrderListPage
from .work_order_form import WorkOrderFormPage

from decimal import Decimal
from modules.development import ErrorHandler

class StartProductionDialog(QDialog):
    """Üretime başlama dialogu - Depo seçimi ve malzeme kontrolü"""

    def __init__(self, work_order, warehouses, materials, parent=None):
        super().__init__(parent)
        self.work_order = work_order
        self.warehouses = warehouses
        self.materials = materials
        self.selected_warehouse_id = None

        self.setWindowTitle("Üretime Başla")
        self.setMinimumWidth(600)
        self.setMinimumHeight(400)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Başlık
        title = QLabel(f"🔄 İş Emri: {self.work_order.order_no}")
        layout.addWidget(title)

        # Ürün bilgisi
        product_name = self.work_order.item.name if self.work_order.item else "-"
        info = QLabel(
            f"Ürün: {product_name} | Miktar: {self.work_order.planned_quantity}"
        )
        layout.addWidget(info)

        # Depo seçimi
        warehouse_frame = QFrame()
        warehouse_frame.setStyleSheet(
            """
            QFrame { background-color: rgba(30, 41, 59, 0.5); 
                border: 1px solid #334155; border-radius: 8px; }
        """
        )
        warehouse_layout = QHBoxLayout(warehouse_frame)
        warehouse_layout.setContentsMargins(12, 12, 12, 12)

        warehouse_layout.addWidget(QLabel("Hammadde Deposu:"))

        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setMinimumWidth(250)
        # İş emrinde kaynak depo seçilmişse onu varsayılan yap
        default_index = 0
        for i, w in enumerate(self.warehouses):
            self.warehouse_combo.addItem(f"{w.code} - {w.name}", w.id)
            if (
                self.work_order.source_warehouse_id
                and w.id == self.work_order.source_warehouse_id
            ):
                default_index = i

        if self.warehouses:
            self.warehouse_combo.setCurrentIndex(default_index)

        self.warehouse_combo.currentIndexChanged.connect(self._on_warehouse_changed)
        warehouse_layout.addWidget(self.warehouse_combo)
        warehouse_layout.addStretch()

        layout.addWidget(warehouse_frame)

        # Malzeme tablosu
        table_label = QLabel("📦 Kullanılacak Malzemeler:")
        layout.addWidget(table_label)

        self.materials_table = QTableWidget()
        self.materials_table.setColumnCount(5)
        self.materials_table.setHorizontalHeaderLabels(
            ["Malzeme", "Gerekli", "Mevcut Stok", "Durum", "Maliyet"]
        )
        self.materials_table.horizontalHeader().setSectionResizeMode(
            0, QHeaderView.ResizeMode.Stretch
        )
        self.materials_table.verticalHeader().setVisible(False)
        self.materials_table.setStyleSheet(
            """
            QTableWidget { background-color: rgba(15, 23, 42, 0.5); 
                border: 1px solid #334155; border-radius: 8px; }
            QTableWidget::item { padding: 8px; border-bottom: 1px solid #334155; }
            QHeaderView::section { background-color: #1e293b; color: #94a3b8; 
                font-weight: 600; padding: 8px; border: none; }
        """
        )
        layout.addWidget(self.materials_table)

        # Özet
        self.summary_label = QLabel("")
        layout.addWidget(self.summary_label)

        # Uyarı
        self.warning_label = QLabel("")
        self.warning_label.setVisible(False)
        layout.addWidget(self.warning_label)

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        self.start_btn = QPushButton("🔄 Üretime Başla")
        self.start_btn.clicked.connect(self._on_start)
        btn_layout.addWidget(self.start_btn)

        layout.addLayout(btn_layout)

        # İlk yükleme
        self._update_materials_table()

    def _on_warehouse_changed(self):
        """Depo değiştiğinde malzeme tablosunu güncelle"""
        self._update_materials_table()

    def _update_materials_table(self):
        """Malzeme tablosunu güncelle"""
        warehouse_id = self.warehouse_combo.currentData()

        self.materials_table.setRowCount(len(self.materials))

        total_cost = 0
        has_shortage = False

        for row, mat in enumerate(self.materials):
            # Malzeme adı
            name_item = QTableWidgetItem(
                f"{mat.get('item_code', '')} - {mat.get('item_name', '')}"
            )
            name_item.setForeground(QColor("#818cf8"))
            self.materials_table.setItem(row, 0, name_item)

            # Gerekli miktar
            required = float(mat.get("required_quantity", 0))
            req_item = QTableWidgetItem(f"{required:,.4f}")
            req_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.materials_table.setItem(row, 1, req_item)

            # Mevcut stok (seçili depodan)
            stock = float(mat.get("stock", 0))
            stock_item = QTableWidgetItem(f"{stock:,.4f}")
            stock_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            self.materials_table.setItem(row, 2, stock_item)

            # Durum
            if stock >= required:
                status_item = QTableWidgetItem("✅ Yeterli")
                status_item.setForeground(QColor("#10b981"))
            else:
                status_item = QTableWidgetItem(f"❌ Eksik: {required - stock:,.4f}")
                status_item.setForeground(QColor("#ef4444"))
                has_shortage = True
            status_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
            self.materials_table.setItem(row, 3, status_item)

            # Maliyet
            unit_cost = float(mat.get("unit_cost", 0))
            line_cost = required * unit_cost
            total_cost += line_cost
            cost_item = QTableWidgetItem(f"₺{line_cost:,.2f}")
            cost_item.setTextAlignment(
                Qt.AlignmentFlag.AlignRight | Qt.AlignmentFlag.AlignVCenter
            )
            cost_item.setForeground(QColor("#10b981"))
            self.materials_table.setItem(row, 4, cost_item)

        # Özet
        self.summary_label.setText(
            f"Toplam {len(self.materials)} malzeme | Tahmini Maliyet: ₺{total_cost:,.2f}"
        )

        # Uyarı ve buton durumu
        if has_shortage:
            self.warning_label.setText("⚠️ Yetersiz stok! Üretim başlatılamaz.")
            self.warning_label.setVisible(True)
            self.start_btn.setEnabled(False)
        else:
            self.warning_label.setVisible(False)
            self.start_btn.setEnabled(True)

    def _on_start(self):
        """Üretime başla"""
        self.selected_warehouse_id = self.warehouse_combo.currentData()
        if not self.selected_warehouse_id:
            QMessageBox.warning(self, "Uyarı", "Lütfen depo seçin!")
            return
        self.accept()

    def get_warehouse_id(self) -> int:
        return self.selected_warehouse_id

class CompleteProductionDialog(QDialog):
    """Üretim tamamlama dialogu"""

    def __init__(self, work_order, warehouses, parent=None):
        super().__init__(parent)
        self.work_order = work_order
        self.warehouses = warehouses

        self.setWindowTitle("Üretimi Tamamla")
        self.setMinimumWidth(450)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Başlık
        title = QLabel(f"✅ Üretimi Tamamla: {self.work_order.order_no}")
        layout.addWidget(title)

        # Form
        form = QGridLayout()
        form.setSpacing(12)

        # Planlanan miktar
        form.addWidget(QLabel("Planlanan Miktar:"), 0, 0)
        planned_label = QLabel(f"{self.work_order.planned_quantity:,.4f}")
        form.addWidget(planned_label, 0, 1)

        # Tamamlanan miktar
        form.addWidget(QLabel("Tamamlanan Miktar:"), 1, 0)
        from PyQt6.QtWidgets import QDoubleSpinBox

        self.completed_input = QDoubleSpinBox()
        self.completed_input.setRange(0, float(self.work_order.planned_quantity) * 2)
        self.completed_input.setDecimals(4)
        self.completed_input.setValue(float(self.work_order.planned_quantity))
        form.addWidget(self.completed_input, 1, 1)

        # Fire miktarı
        form.addWidget(QLabel("Fire Miktarı:"), 2, 0)
        self.scrap_input = QDoubleSpinBox()
        self.scrap_input.setRange(0, float(self.work_order.planned_quantity))
        self.scrap_input.setDecimals(4)
        self.scrap_input.setValue(0)
        form.addWidget(self.scrap_input, 2, 1)

        # Hedef depo
        form.addWidget(QLabel("Mamul Deposu:"), 3, 0)
        self.warehouse_combo = QComboBox()
        default_index = 0
        for i, w in enumerate(self.warehouses):
            self.warehouse_combo.addItem(f"{w.code} - {w.name}", w.id)
            if (
                self.work_order.target_warehouse_id
                and w.id == self.work_order.target_warehouse_id
            ):
                default_index = i

        if self.warehouses:
            self.warehouse_combo.setCurrentIndex(default_index)

        form.addWidget(self.warehouse_combo, 3, 1)

        layout.addLayout(form)

        # Bilgi
        info = QLabel("ℹ️ Tamamlanan miktar mamul deposuna giriş yapılacak")
        layout.addWidget(info)

        layout.addStretch()

        # Butonlar
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        cancel_btn = QPushButton("İptal")
        cancel_btn.clicked.connect(self.reject)
        btn_layout.addWidget(cancel_btn)

        complete_btn = QPushButton("✅ Tamamla")
        complete_btn.clicked.connect(self.accept)
        btn_layout.addWidget(complete_btn)

        layout.addLayout(btn_layout)

    def get_data(self) -> dict:
        return {
            "completed_quantity": self.completed_input.value(),
            "scrap_quantity": self.scrap_input.value(),
            "warehouse_id": self.warehouse_combo.currentData(),
        }

class WorkOrderModule(QWidget):
    """İş Emirleri modülü"""

    page_title = "İş Emirleri"

    def __init__(self, parent=None):
        super().__init__(parent)
        self.wo_service = None
        self.bom_service = None
        self.item_service = None
        self.warehouse_service = None
        self.workstation_service = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.stack = QStackedWidget()

        # Liste sayfası
        self.list_page = WorkOrderListPage()
        self.list_page.new_clicked.connect(self._show_new_form)
        self.list_page.edit_clicked.connect(self._show_edit_form)
        self.list_page.view_clicked.connect(self._show_edit_form)
        self.list_page.delete_clicked.connect(self._delete_work_order)
        self.list_page.status_change_requested.connect(self._change_status)
        self.list_page.refresh_requested.connect(self._load_data)
        self.stack.addWidget(self.list_page)

        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._ensure_services()
        self._load_data()

    def _ensure_services(self):
        """Servisleri yükle"""
        if not self.wo_service:
            try:
                from modules.production.services import (
                    WorkOrderService,
                    BOMService,
                    WorkStationService,
                )
                from modules.inventory.services import ItemService, WarehouseService

                self.wo_service = WorkOrderService()
                self.bom_service = BOMService()
                self.workstation_service = WorkStationService()
                self.item_service = ItemService()
                self.warehouse_service = WarehouseService()
            except Exception as e:
                ErrorHandler.handle_error(
                    e,
                    module='production',
                    screen='WorkOrderModule',
                    function='_ensure_services',
                    parent_widget=self,
                    show_message=False
                )

    def _load_data(self):
        """Verileri yükle"""
        if not self.wo_service:
            return

        try:
            status_filter = self.list_page.get_status_filter()

            from database.models.production import WorkOrderStatus

            status = WorkOrderStatus(status_filter) if status_filter else None

            work_orders = self.wo_service.get_all(status=status)

            wo_list = []
            for wo in work_orders:
                progress = 0
                if wo.planned_quantity and wo.planned_quantity > 0:
                    completed = wo.completed_quantity or 0
                    progress = float(completed / wo.planned_quantity * 100)

                wo_list.append(
                    {
                        "id": wo.id,
                        "order_no": wo.order_no,
                        "item_name": wo.item.name if wo.item else "-",
                        "planned_quantity": float(wo.planned_quantity or 0),
                        "completed_quantity": float(wo.completed_quantity or 0),
                        "planned_start": wo.planned_start,
                        "planned_end": wo.planned_end,
                        "progress_rate": progress,
                        "priority": wo.priority.value if wo.priority else "normal",
                        "status": wo.status.value if wo.status else "draft",
                    }
                )

            self.list_page.load_data(wo_list)

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_load_data',
                parent_widget=self
            )
            self.list_page.load_data([])

    def _show_new_form(self):
        """Yeni iş emri formu göster"""
        self._ensure_services()

        form = WorkOrderFormPage()
        form.saved.connect(self._save_work_order)
        form.cancelled.connect(self._show_list)
        form.order_no_requested.connect(lambda: self._generate_order_no(form))
        form.bom_selected.connect(
            lambda item_id: self._load_boms_for_product(form, item_id)
        )

        self._load_form_data(form)
        self._generate_order_no(form)

        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, wo_id: int):
        """Düzenleme formu göster"""
        self._ensure_services()

        wo = self.wo_service.get_by_id(wo_id)
        if not wo:
            QMessageBox.warning(self, "Hata", "İş emri bulunamadı!")
            return

        wo_data = {
            "id": wo.id,
            "order_no": wo.order_no,
            "description": wo.description,
            "item_id": wo.item_id,
            "bom_id": wo.bom_id,
            "planned_quantity": float(wo.planned_quantity or 1),
            "priority": wo.priority.value if wo.priority else "normal",
            "source_warehouse_id": wo.source_warehouse_id,
            "target_warehouse_id": wo.target_warehouse_id,
            "planned_start": wo.planned_start,
            "planned_end": wo.planned_end,
            "status": wo.status.value if wo.status else "draft",
        }

        form = WorkOrderFormPage(wo_data)
        form.saved.connect(self._save_work_order)
        form.cancelled.connect(self._show_list)
        form.bom_selected.connect(
            lambda item_id: self._load_boms_for_product(form, item_id)
        )

        self._load_form_data(form)

        # Seçimleri ayarla
        for i in range(form.product_combo.count()):
            if form.product_combo.itemData(i) == wo.item_id:
                form.product_combo.setCurrentIndex(i)
                break

        self._load_boms_for_product(form, wo.item_id)
        for i in range(form.bom_combo.count()):
            if form.bom_combo.itemData(i) == wo.bom_id:
                form.bom_combo.setCurrentIndex(i)
                break

        # Mevcut operasyonları yükle
        self._load_work_order_operations(form, wo)

        # Depo seçimlerini ayarla
        if wo.source_warehouse_id:
            for i in range(form.source_warehouse_combo.count()):
                if form.source_warehouse_combo.itemData(i) == wo.source_warehouse_id:
                    form.source_warehouse_combo.setCurrentIndex(i)
                    break

        if wo.target_warehouse_id:
            for i in range(form.target_warehouse_combo.count()):
                if form.target_warehouse_combo.itemData(i) == wo.target_warehouse_id:
                    form.target_warehouse_combo.setCurrentIndex(i)
                    break

        # Öncelik seçimini ayarla
        priority_val = wo.priority.value if wo.priority else "normal"
        for i in range(form.priority_combo.count()):
            if form.priority_combo.itemData(i) == priority_val:
                form.priority_combo.setCurrentIndex(i)
                break

        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _load_form_data(self, form: WorkOrderFormPage):
        """Form verilerini yükle"""
        try:
            # Mamul ürünleri
            products = self.item_service.get_all()
            mamul_products = [
                p for p in products if p.item_type and p.item_type.value == "mamul"
            ]
            form.set_products(mamul_products if mamul_products else products)

            # Depolar
            warehouses = self.warehouse_service.get_all()
            form.set_warehouses(warehouses)

            # İş istasyonları
            work_stations = self.workstation_service.get_all(active_only=True)
            ws_list = []
            for ws in work_stations:
                ws_list.append(
                    {
                        "id": ws.id,
                        "code": ws.code,
                        "name": ws.name,
                        "station_type": (
                            ws.station_type.value.lower()
                            if ws.station_type
                            else "machine"
                        ),
                        "default_operation_name": getattr(
                            ws, "default_operation_name", None
                        )
                        or "",
                        "default_setup_time": getattr(ws, "default_setup_time", 0) or 0,
                        "default_run_time_per_unit": float(
                            getattr(ws, "default_run_time_per_unit", 0) or 0
                        ),
                    }
                )
            form.set_work_stations(ws_list)

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_load_form_data',
                parent_widget=self,
                show_message=False
            )

    def _load_boms_for_product(self, form: WorkOrderFormPage, item_id: int):
        """Mamule ait reçeteleri yükle"""
        try:
            boms = self.bom_service.get_by_item(item_id, active_only=False)
            form.set_boms_for_product(boms)

            if boms:
                active_boms = [b for b in boms if b.status.value == "active"]
                if active_boms:
                    bom = self.bom_service.get_by_id(active_boms[0].id)
                    self._load_bom_details(form, bom)
                    for i in range(form.bom_combo.count()):
                        if form.bom_combo.itemData(i) == active_boms[0].id:
                            form.bom_combo.setCurrentIndex(i)
                            break

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_load_boms_for_product',
                parent_widget=self,
                show_message=False
            )

    def _load_bom_details(self, form: WorkOrderFormPage, bom):
        """Reçete malzemelerini yükle"""
        try:
            materials = []
            for line in bom.lines:
                stock = 0
                try:
                    from sqlalchemy import text

                    result = (
                        self.item_service.session.execute(
                            text(
                                f"SELECT COALESCE(SUM(quantity), 0) FROM stock_balances WHERE item_id = {line.item_id}"
                            )
                        ).scalar()
                        or 0
                    )
                    stock = float(result)
                except:
                    stock = 0

                materials.append(
                    {
                        "item_id": line.item_id,
                        "item_code": line.item.code if line.item else "",
                        "item_name": line.item.name if line.item else "",
                        "quantity": line.effective_quantity,
                        "unit_code": line.unit.code if line.unit else "ADET",
                        "unit_cost": (
                            float(line.item.purchase_price or 0) if line.item else 0
                        ),
                        "stock": stock,
                    }
                )

            form.set_bom_materials(materials)

            # BOM'dan operasyonları yükle
            operations = []
            if hasattr(bom, "operations") and bom.operations:
                for op in bom.operations:
                    operations.append(
                        {
                            "id": op.id,
                            "operation_no": op.operation_no,
                            "name": op.name,
                            "work_station_id": op.work_station_id,
                            "setup_time": op.setup_time or 0,
                            "run_time": op.run_time or 0,
                            "description": op.description or "",
                        }
                    )

            form.set_bom_operations(operations)

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_load_bom_details',
                parent_widget=self,
                show_message=False
            )

    def _load_work_order_operations(self, form: WorkOrderFormPage, wo):
        """Mevcut iş emri operasyonlarını yükle"""
        try:
            operations = []
            if wo.operations:
                for op in wo.operations:
                    operations.append(
                        {
                            "id": op.id,
                            "operation_no": op.operation_no,
                            "name": op.name,
                            "work_station_id": op.work_station_id,
                            "setup_time": op.planned_setup_time or 0,
                            "run_time": float(op.planned_run_time or 0),
                            "description": "",
                        }
                    )

            form.set_bom_operations(operations)

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_load_work_order_operations',
                parent_widget=self,
                show_message=False
            )

    def _generate_order_no(self, form: WorkOrderFormPage):
        """Otomatik iş emri numarası üret"""
        try:
            order_no = self.wo_service.generate_order_no()
            form.set_generated_order_no(order_no)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_generate_order_no',
                parent_widget=self,
                show_message=False
            )

    def _save_work_order(self, data: dict):
        """İş emrini kaydet"""
        try:
            wo_id = data.pop("id", None)
            operations_data = data.pop("operations", [])

            from database.models.production import WorkOrderPriority

            priority_val = data.get("priority", "normal")
            data["priority"] = WorkOrderPriority(priority_val)

            if wo_id:
                wo = self.wo_service.update(wo_id, **data)
                if wo:
                    self._save_operations(wo, operations_data)
                    QMessageBox.information(self, "Başarılı", "İş emri güncellendi!")
            else:
                wo = self.wo_service.create(**data)
                if wo:
                    self._save_operations(wo, operations_data)
                    QMessageBox.information(self, "Başarılı", "İş emri oluşturuldu!")

            self._show_list()
            self._load_data()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_save_work_order',
                parent_widget=self
            )

    def _save_operations(self, wo, operations_data: list):
        """Operasyonları kaydet"""
        try:
            from database.models.production import WorkOrderOperation

            for op in list(wo.operations):
                self.wo_service.session.delete(op)

            for op_data in operations_data:
                new_op = WorkOrderOperation(
                    work_order_id=wo.id,
                    operation_no=op_data.get("operation_no", 10),
                    name=op_data.get("name", ""),
                    work_station_id=op_data.get("work_station_id"),
                    planned_setup_time=int(op_data.get("setup_time", 0)),
                    planned_run_time=int(float(op_data.get("run_time", 0))),
                    status="pending",
                )
                self.wo_service.session.add(new_op)

            self.wo_service.session.commit()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_save_operations',
                parent_widget=self,
                show_message=False
            )
            self.wo_service.session.rollback()

    def _change_status(self, wo_id: int, new_status: str):
        """İş emri durumunu değiştir"""
        try:
            from database.models.production import WorkOrderStatus

            # "in_progress" için özel dialog
            if new_status == "in_progress":
                self._start_production(wo_id)
                return

            # "completed" için özel dialog
            if new_status == "completed":
                self._complete_production(wo_id)
                return

            # Diğer durumlar için basit geçiş
            status = WorkOrderStatus(new_status)
            self.wo_service.change_status(wo_id, status)

            status_names = {
                "planned": "planlandı",
                "released": "serbest bırakıldı",
                "closed": "kapatıldı",
                "cancelled": "iptal edildi",
            }
            QMessageBox.information(
                self,
                "Başarılı",
                f"İş emri {status_names.get(new_status, 'güncellendi')}!",
            )
            self._load_data()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_change_status',
                parent_widget=self
            )

    def _start_production(self, wo_id: int):
        """Üretime başla - Depo seçimi ve stok kontrolü"""
        try:
            wo = self.wo_service.get_by_id(wo_id)
            if not wo:
                QMessageBox.warning(self, "Hata", "İş emri bulunamadı!")
                return

            # Depoları al
            warehouses = self.warehouse_service.get_all()

            # Malzemeleri al
            materials = []
            for line in wo.lines:
                # Stok miktarını al
                stock = 0
                try:
                    from sqlalchemy import text

                    warehouse_id = wo.source_warehouse_id or (
                        warehouses[0].id if warehouses else None
                    )
                    if warehouse_id:
                        result = (
                            self.wo_service.session.execute(
                                text(
                                    f"SELECT COALESCE(quantity, 0) FROM stock_balances WHERE item_id = {line.item_id} AND warehouse_id = {warehouse_id}"
                                )
                            ).scalar()
                            or 0
                        )
                        stock = float(result)
                except:
                    stock = 0

                materials.append(
                    {
                        "item_id": line.item_id,
                        "item_code": line.item.code if line.item else "",
                        "item_name": line.item.name if line.item else "",
                        "required_quantity": float(line.required_quantity or 0),
                        "unit_cost": float(line.unit_cost or 0),
                        "stock": stock,
                    }
                )

            # Dialog göster
            dialog = StartProductionDialog(wo, warehouses, materials, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                warehouse_id = dialog.get_warehouse_id()

                # Servisi çağır
                self.wo_service.start_production(wo_id, warehouse_id)

                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Üretim başlatıldı!\n\n"
                    f"İş Emri: {wo.order_no}\n"
                    f"Malzemeler stoktan düşüldü.",
                )
                self._load_data()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_start_production',
                parent_widget=self
            )

    def _complete_production(self, wo_id: int):
        """Üretimi tamamla - Mamul girişi"""
        try:
            wo = self.wo_service.get_by_id(wo_id)
            if not wo:
                QMessageBox.warning(self, "Hata", "İş emri bulunamadı!")
                return

            warehouses = self.warehouse_service.get_all()

            dialog = CompleteProductionDialog(wo, warehouses, self)
            if dialog.exec() == QDialog.DialogCode.Accepted:
                data = dialog.get_data()

                # Servisi çağır
                self.wo_service.complete_production(
                    order_id=wo_id,
                    completed_quantity=Decimal(str(data["completed_quantity"])),
                    scrap_quantity=Decimal(str(data["scrap_quantity"])),
                    target_warehouse_id=data["warehouse_id"],
                )

                QMessageBox.information(
                    self,
                    "Başarılı",
                    f"Üretim tamamlandı!\n\n"
                    f"İş Emri: {wo.order_no}\n"
                    f"Tamamlanan: {data['completed_quantity']:,.4f}\n"
                    f"Fire: {data['scrap_quantity']:,.4f}\n"
                    f"Mamul stoğa eklendi.",
                )
                self._load_data()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_complete_production',
                parent_widget=self
            )

    def _delete_work_order(self, wo_id: int):
        """İş emrini sil"""
        try:
            if self.wo_service.delete(wo_id):
                QMessageBox.information(self, "Başarılı", "İş emri silindi!")
                self._load_data()
            else:
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "İş emri silinemedi! Sadece taslak durumundaki emirler silinebilir.",
                )
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module='production',
                screen='WorkOrderModule',
                function='_delete_work_order',
                parent_widget=self
            )

    def _show_list(self):
        """Liste sayfasına dön"""
        current = self.stack.currentWidget()
        if current != self.list_page:
            self.stack.removeWidget(current)
            current.deleteLater()

        self.stack.setCurrentWidget(self.list_page)
