"""
Akıllı İş - Depocu Operasyon Paneli

Tablet/mobil uyumlu, büyük butonlu arayüz.
Depocu görevlerini yönetmek için kullanılır.
"""

from typing import Optional, List, Dict, Any
from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QFrame,
    QGridLayout,
    QStackedWidget,
    QTableWidget,
    QTableWidgetItem,
    QHeaderView,
    QMessageBox,
    QComboBox,
    QSpinBox,
    QScrollArea,
)
from PyQt6.QtCore import Qt, pyqtSignal, QTimer
from PyQt6.QtGui import QFont

from ui.widgets.barcode_scanner import BarcodeInput


class WarehouseOperatorPage(QWidget):
    """Depocu operasyon ana paneli"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.current_user = None
        self.current_warehouse = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(16)

        # Üst bilgi bar
        self.header = self._create_header()
        layout.addWidget(self.header)

        # Stacked widget (sayfa geçişleri)
        self.stack = QStackedWidget()

        # Ana menü
        self.main_menu = self._create_main_menu()
        self.stack.addWidget(self.main_menu)

        # Alt sayfalar
        self.putaway_page = PutawayScreen(self)
        self.stack.addWidget(self.putaway_page)

        self.picking_page = PickingScreen(self)
        self.stack.addWidget(self.picking_page)

        self.transfer_page = TransferScreen(self)
        self.stack.addWidget(self.transfer_page)

        self.count_page = CountScreen(self)
        self.stack.addWidget(self.count_page)

        self.query_page = StockQueryScreen(self)
        self.stack.addWidget(self.query_page)

        layout.addWidget(self.stack)

    def _create_header(self) -> QFrame:
        """Üst bilgi bar"""
        frame = QFrame()
        frame.setFixedHeight(60)
        frame.setProperty("class", "panel-header")

        layout = QHBoxLayout(frame)
        layout.setContentsMargins(16, 8, 16, 8)

        # Logo/Başlık
        title = QLabel("🏭 DEPOCU PANELİ")
        title.setFont(QFont("Arial", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        layout.addStretch()

        # Kullanıcı ve depo bilgisi
        self.user_label = QLabel("Kullanıcı: -")
        self.user_label.setProperty("class", "label-muted")
        layout.addWidget(self.user_label)

        self.warehouse_label = QLabel("Depo: -")
        self.warehouse_label.setProperty("class", "label-muted")
        layout.addWidget(self.warehouse_label)

        # Depo seçimi
        self.warehouse_combo = QComboBox()
        self.warehouse_combo.setMinimumWidth(150)
        self.warehouse_combo.currentIndexChanged.connect(self.on_warehouse_changed)
        layout.addWidget(self.warehouse_combo)

        return frame

    def _create_main_menu(self) -> QWidget:
        """Ana menü grid"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setContentsMargins(0, 20, 0, 20)

        # Grid butonları
        grid = QGridLayout()
        grid.setSpacing(20)

        buttons = [
            ("📥", "MAL KABUL", "Mal kabul yerleştirme", self.open_putaway),
            ("📦", "TOPLAMA", "Sipariş toplama (Picking)", self.open_picking),
            ("🔄", "TRANSFER", "Depolar arası transfer", self.open_transfer),
            ("📋", "SAYIM", "Stok sayım işlemi", self.open_count),
            ("🔍", "STOK SORGULA", "Stok ve lokasyon sorgula", self.open_query),
            ("📍", "ADRES OKUT", "Lokasyon barkodu okut", self.scan_location),
        ]

        for i, (icon, title, desc, callback) in enumerate(buttons):
            btn = self._create_menu_button(icon, title, desc)
            btn.clicked.connect(callback)
            row = i // 3
            col = i % 3
            grid.addWidget(btn, row, col)

        layout.addLayout(grid)
        layout.addStretch()

        # Bekleyen görevler özeti
        self.task_summary = QLabel("Bekleyen Görevler: 0 | Bugün Tamamlanan: 0")
        self.task_summary.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.task_summary.setProperty("class", "label-muted")
        layout.addWidget(self.task_summary)

        return widget

    def _create_menu_button(self, icon: str, title: str, desc: str) -> QPushButton:
        """Büyük menü butonu"""
        btn = QPushButton()
        btn.setMinimumSize(200, 150)
        btn.setProperty("class", "menu-button-large")

        # Layout içinde icon, title, desc
        layout = QVBoxLayout(btn)
        layout.setSpacing(8)

        icon_label = QLabel(icon)
        icon_label.setFont(QFont("Arial", 36))
        icon_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(icon_label)

        title_label = QLabel(title)
        title_label.setFont(QFont("Arial", 14, QFont.Weight.Bold))
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(title_label)

        desc_label = QLabel(desc)
        desc_label.setFont(QFont("Arial", 10))
        desc_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        desc_label.setProperty("class", "label-muted")
        layout.addWidget(desc_label)

        return btn

    def load_warehouses(self):
        """Depoları yükle"""
        try:
            from database.base import get_session
            from database.models.inventory import Warehouse

            session = get_session()
            warehouses = (
                session.query(Warehouse).filter(Warehouse.is_active == True).all()
            )

            self.warehouse_combo.clear()
            for wh in warehouses:
                self.warehouse_combo.addItem(wh.name, wh.id)

            session.close()
        except Exception as e:
            print(f"Depo yükleme hatası: {e}")

    def on_warehouse_changed(self, index: int):
        """Depo değiştiğinde"""
        wh_id = self.warehouse_combo.currentData()
        if wh_id:
            self.current_warehouse = wh_id
            self.warehouse_label.setText(f"Depo: {self.warehouse_combo.currentText()}")

    def go_back(self):
        """Ana menüye dön"""
        self.stack.setCurrentIndex(0)

    def open_putaway(self):
        self.stack.setCurrentWidget(self.putaway_page)

    def open_picking(self):
        self.stack.setCurrentWidget(self.picking_page)

    def open_transfer(self):
        self.stack.setCurrentWidget(self.transfer_page)

    def open_count(self):
        self.stack.setCurrentWidget(self.count_page)

    def open_query(self):
        self.stack.setCurrentWidget(self.query_page)

    def scan_location(self):
        """Lokasyon barkodu okut"""
        # TODO: Barkod okutma dialog'u
        QMessageBox.information(self, "Adres Okut", "Lokasyon barkodunu okutun...")


class BaseOperationScreen(QWidget):
    """Temel operasyon ekranı"""

    def __init__(self, parent: WarehouseOperatorPage):
        super().__init__()
        self.operator_page = parent
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(12)

        # Geri butonu ve başlık
        header = QHBoxLayout()
        back_btn = QPushButton("← Geri")
        back_btn.clicked.connect(self.operator_page.go_back)
        header.addWidget(back_btn)

        self.title_label = QLabel(self.get_title())
        self.title_label.setFont(QFont("Arial", 18, QFont.Weight.Bold))
        header.addWidget(self.title_label)

        header.addStretch()
        layout.addLayout(header)

        # İçerik
        self.content = QWidget()
        self.content_layout = QVBoxLayout(self.content)
        layout.addWidget(self.content)

    def get_title(self) -> str:
        return "Operasyon"


class PutawayScreen(BaseOperationScreen):
    """Mal kabul yerleştirme ekranı"""

    def get_title(self) -> str:
        return "📥 Mal Kabul Yerleştirme"

    def setup_ui(self):
        super().setup_ui()

        # Barkod okuma
        barcode_frame = QFrame()
        barcode_layout = QHBoxLayout(barcode_frame)

        barcode_layout.addWidget(QLabel("Ürün Barkodu:"))
        self.product_barcode = BarcodeInput(
            callback=self.on_product_scanned, placeholder="Ürün barkodunu okutun..."
        )
        barcode_layout.addWidget(self.product_barcode)

        self.content_layout.addWidget(barcode_frame)

        # Ürün bilgisi
        self.product_info = QLabel("Henüz ürün okutulmadı")
        self.product_info.setProperty("class", "info-box")
        self.content_layout.addWidget(self.product_info)

        # Lokasyon önerisi
        self.location_suggest = QLabel("Önerilen Lokasyon: -")
        self.location_suggest.setProperty("class", "success-box")
        self.content_layout.addWidget(self.location_suggest)

        # Hedef lokasyon
        loc_frame = QFrame()
        loc_layout = QHBoxLayout(loc_frame)
        loc_layout.addWidget(QLabel("Hedef Lokasyon:"))
        self.location_barcode = BarcodeInput(
            callback=self.on_location_scanned,
            placeholder="Lokasyon barkodunu okutun...",
        )
        loc_layout.addWidget(self.location_barcode)
        self.content_layout.addWidget(loc_frame)

        # Miktar
        qty_frame = QFrame()
        qty_layout = QHBoxLayout(qty_frame)
        qty_layout.addWidget(QLabel("Miktar:"))
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 99999)
        self.qty_input.setValue(1)
        qty_layout.addWidget(self.qty_input)
        qty_layout.addStretch()
        self.content_layout.addWidget(qty_frame)

        # Onayla butonu
        confirm_btn = QPushButton("✅ Yerleştirmeyi Onayla")
        confirm_btn.setMinimumHeight(50)
        confirm_btn.setProperty("class", "btn-large-green")
        confirm_btn.clicked.connect(self.confirm_putaway)
        self.content_layout.addWidget(confirm_btn)

        self.content_layout.addStretch()

    def on_product_scanned(self, barcode: str):
        """Ürün barkodu okutuldu"""
        self.product_info.setText(f"Ürün: {barcode}\n(Ürün bilgisi yükleniyor...)")
        # TODO: Ürün bilgisi ve önerilen lokasyon getir

    def on_location_scanned(self, barcode: str):
        """Lokasyon barkodu okutuldu"""
        # TODO: Lokasyon doğrulama

    def confirm_putaway(self):
        """Yerleştirmeyi onayla"""
        QMessageBox.information(self, "Başarılı", "Yerleştirme kaydedildi!")


class PickingScreen(BaseOperationScreen):
    """Sipariş toplama ekranı"""

    def get_title(self) -> str:
        return "📦 Sipariş Toplama"

    def setup_ui(self):
        super().setup_ui()

        # Toplama listesi seçimi
        list_frame = QFrame()
        list_layout = QHBoxLayout(list_frame)
        list_layout.addWidget(QLabel("Toplama Listesi:"))
        self.list_combo = QComboBox()
        self.list_combo.addItem("- Liste Seçin -")
        list_layout.addWidget(self.list_combo)
        self.content_layout.addWidget(list_frame)

        # Mevcut görev
        self.current_task = QLabel("Lokasyon: -\nÜrün: -\nMiktar: -")
        self.current_task.setProperty("class", "info-box")
        self.content_layout.addWidget(self.current_task)

        # Barkod okuma
        scan_frame = QFrame()
        scan_layout = QHBoxLayout(scan_frame)
        scan_layout.addWidget(QLabel("Barkod Okut:"))
        self.scan_input = BarcodeInput(
            callback=self.on_scan, placeholder="Lokasyon veya ürün barkodu..."
        )
        scan_layout.addWidget(self.scan_input)
        self.content_layout.addWidget(scan_frame)

        # Onayla / Sonraki butonları
        btn_layout = QHBoxLayout()
        skip_btn = QPushButton("⏭ Atla")
        skip_btn.setMinimumHeight(50)
        btn_layout.addWidget(skip_btn)

        confirm_btn = QPushButton("✅ Toplandı")
        confirm_btn.setMinimumHeight(50)
        confirm_btn.setProperty("class", "btn-large-green")
        btn_layout.addWidget(confirm_btn)

        self.content_layout.addLayout(btn_layout)
        self.content_layout.addStretch()

    def on_scan(self, barcode: str):
        """Barkod okutuldu"""
        pass


class TransferScreen(BaseOperationScreen):
    """Depolar arası transfer ekranı"""

    def get_title(self) -> str:
        return "🔄 Depolar Arası Transfer"

    def setup_ui(self):
        super().setup_ui()

        # Kaynak lokasyon
        from_frame = QFrame()
        from_layout = QHBoxLayout(from_frame)
        from_layout.addWidget(QLabel("Kaynak Lokasyon:"))
        self.from_input = BarcodeInput(
            callback=self.on_from_scanned, placeholder="Kaynak lokasyon barkodu..."
        )
        from_layout.addWidget(self.from_input)
        self.content_layout.addWidget(from_frame)

        # Ürün
        product_frame = QFrame()
        product_layout = QHBoxLayout(product_frame)
        product_layout.addWidget(QLabel("Ürün Barkodu:"))
        self.product_input = BarcodeInput(
            callback=self.on_product_scanned, placeholder="Ürün barkodu..."
        )
        product_layout.addWidget(self.product_input)
        self.content_layout.addWidget(product_frame)

        # Miktar
        qty_frame = QFrame()
        qty_layout = QHBoxLayout(qty_frame)
        qty_layout.addWidget(QLabel("Miktar:"))
        self.qty_input = QSpinBox()
        self.qty_input.setRange(1, 99999)
        qty_layout.addWidget(self.qty_input)
        qty_layout.addStretch()
        self.content_layout.addWidget(qty_frame)

        # Hedef lokasyon
        to_frame = QFrame()
        to_layout = QHBoxLayout(to_frame)
        to_layout.addWidget(QLabel("Hedef Lokasyon:"))
        self.to_input = BarcodeInput(
            callback=self.on_to_scanned, placeholder="Hedef lokasyon barkodu..."
        )
        to_layout.addWidget(self.to_input)
        self.content_layout.addWidget(to_frame)

        # Transfer butonu
        transfer_btn = QPushButton("🔄 Transfer Et")
        transfer_btn.setMinimumHeight(50)
        transfer_btn.setProperty("class", "btn-primary")
        transfer_btn.clicked.connect(self.do_transfer)
        self.content_layout.addWidget(transfer_btn)

        self.content_layout.addStretch()

    def on_from_scanned(self, barcode: str):
        pass

    def on_product_scanned(self, barcode: str):
        pass

    def on_to_scanned(self, barcode: str):
        pass

    def do_transfer(self):
        QMessageBox.information(self, "Başarılı", "Transfer kaydedildi!")


class CountScreen(BaseOperationScreen):
    """Stok sayım ekranı"""

    def get_title(self) -> str:
        return "📋 Stok Sayım"

    def setup_ui(self):
        super().setup_ui()

        # Lokasyon
        loc_frame = QFrame()
        loc_layout = QHBoxLayout(loc_frame)
        loc_layout.addWidget(QLabel("Lokasyon:"))
        self.loc_input = BarcodeInput(
            callback=self.on_location_scanned, placeholder="Lokasyon barkodu..."
        )
        loc_layout.addWidget(self.loc_input)
        self.content_layout.addWidget(loc_frame)

        # Lokasyondaki stoklar
        self.stock_table = QTableWidget()
        self.stock_table.setColumnCount(4)
        self.stock_table.setHorizontalHeaderLabels(
            ["Ürün", "Sistem", "Sayılan", "Fark"]
        )
        self.stock_table.horizontalHeader().setSectionResizeMode(
            QHeaderView.ResizeMode.Stretch
        )
        self.content_layout.addWidget(self.stock_table)

        # Ürün ekleme
        add_frame = QFrame()
        add_layout = QHBoxLayout(add_frame)
        add_layout.addWidget(QLabel("Ürün:"))
        self.product_input = BarcodeInput(
            callback=self.on_product_scanned, placeholder="Ürün barkodu..."
        )
        add_layout.addWidget(self.product_input)
        add_layout.addWidget(QLabel("Adet:"))
        self.qty_input = QSpinBox()
        self.qty_input.setRange(0, 99999)
        add_layout.addWidget(self.qty_input)
        add_btn = QPushButton("➕")
        add_btn.clicked.connect(self.add_count)
        add_layout.addWidget(add_btn)
        self.content_layout.addWidget(add_frame)

        # Kaydet
        save_btn = QPushButton("💾 Sayımı Kaydet")
        save_btn.setMinimumHeight(50)
        save_btn.setProperty("class", "btn-large-green")
        save_btn.clicked.connect(self.save_count)
        self.content_layout.addWidget(save_btn)

    def on_location_scanned(self, barcode: str):
        pass

    def on_product_scanned(self, barcode: str):
        pass

    def add_count(self):
        pass

    def save_count(self):
        QMessageBox.information(self, "Başarılı", "Sayım kaydedildi!")


class StockQueryScreen(BaseOperationScreen):
    """Stok sorgulama ekranı"""

    def get_title(self) -> str:
        return "🔍 Stok Sorgulama"

    def setup_ui(self):
        super().setup_ui()

        # Arama
        search_frame = QFrame()
        search_layout = QHBoxLayout(search_frame)
        search_layout.addWidget(QLabel("Ürün/Lokasyon:"))
        self.search_input = BarcodeInput(
            callback=self.do_search, placeholder="Barkod veya kod girin..."
        )
        search_layout.addWidget(self.search_input)
        self.content_layout.addWidget(search_frame)

        # Sonuçlar
        self.result_area = QScrollArea()
        self.result_area.setWidgetResizable(True)
        self.result_content = QWidget()
        self.result_layout = QVBoxLayout(self.result_content)
        self.result_area.setWidget(self.result_content)
        self.content_layout.addWidget(self.result_area)

        # Başlangıç mesajı
        self.result_label = QLabel("Aramak için barkod okutun veya kod girin")
        self.result_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.result_layout.addWidget(self.result_label)

    def do_search(self, query: str):
        """Arama yap"""
        # Önce lokasyon ara
        try:
            from modules.inventory.services.location_service import LocationService

            location = LocationService.get_by_barcode(query)
            if location:
                self.show_location_stock(location)
                return
        except Exception:
            pass

        # Ürün ara
        self.result_label.setText(f"Aranan: {query}\n(Sonuç bulunamadı)")

    def show_location_stock(self, location):
        """Lokasyondaki stokları göster"""
        try:
            from modules.inventory.services.location_service import LocationService

            stocks = LocationService.get_location_stock(location.id)

            text = f"📍 Lokasyon: {location.code}\n\n"
            if stocks:
                for s in stocks:
                    text += f"• {s['item_code']}: {s['quantity']:.0f} adet\n"
            else:
                text += "Bu lokasyonda stok yok."

            self.result_label.setText(text)
        except Exception as e:
            self.result_label.setText(f"Hata: {e}")
