from __future__ import annotations

"""
Akıllı İş - Modüler Dashboard Sayfası

Kullanıcı özelleştirmeli, grid tabanlı dashboard.
"""

from typing import Optional, Dict, Any

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QDialog,
    QListWidget,
    QListWidgetItem,
    QDialogButtonBox,
    QMessageBox,
    QSizePolicy,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont
from ui.components.toast import show_toast

from config.styles import COLORS, FONT_FAMILY_QT
from core.user_context import get_current_user

from .grid_layout import DashboardGridLayout
from .widget_manager import WidgetManager
from .widgets.base import BaseWidget, WidgetConfig


class AddWidgetDialog(QDialog):
    """Widget ekleme diyaloğu"""

    def __init__(self, available_widgets, parent=None):
        super().__init__(parent)
        self.selected_widget = None
        self.available_widgets = available_widgets

        self.setWindowTitle("Widget Ekle")
        self.setMinimumSize(400, 500)
        self._setup_ui()

    def _setup_ui(self):
        layout = QVBoxLayout(self)

        # Başlık
        title = QLabel("Eklenecek widget'ı seçin:")
        title.setFont(QFont(FONT_FAMILY_QT, 11))
        layout.addWidget(title)

        # Widget listesi
        self.widget_list = QListWidget()
        self.widget_list.setStyleSheet(
            f"""
            QListWidget {{
                border: 1px solid {COLORS['border']};
                border-radius: 4px;
                background: {COLORS['bg_secondary']};
            }}
            QListWidget::item {{
                padding: 12px;
                border-bottom: 1px solid {COLORS['border']};
            }}
            QListWidget::item:selected {{
                background: {COLORS['primary']};
                color: white;
            }}
            QListWidget::item:hover {{
                background: {COLORS['bg_hover']};
            }}
        """
        )

        for widget_def in self.available_widgets:
            item = QListWidgetItem()
            item.setText(f"{widget_def.name}\n{widget_def.description or ''}")
            item.setData(Qt.ItemDataRole.UserRole, widget_def.code)
            self.widget_list.addItem(item)

        self.widget_list.itemDoubleClicked.connect(self.accept)
        layout.addWidget(self.widget_list, 1)

        # Butonlar
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def accept(self):
        current = self.widget_list.currentItem()
        if current:
            self.selected_widget = current.data(Qt.ItemDataRole.UserRole)
        super().accept()


class DashboardPage(QWidget):
    """
    Modüler Dashboard Sayfası

    Kullanıcıların widget'ları özelleştirebileceği ana sayfa.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._edit_mode = False
        self._user_context = None

        self._setup_ui()
        self._register_widgets()
        self._load_layout()

    def _setup_ui(self):
        """UI yapısını oluşturur"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(24, 24, 24, 24)
        main_layout.setSpacing(16)

        # Header
        self._create_header(main_layout)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.Shape.NoFrame)
        scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        scroll.setStyleSheet(
            f"""
            QScrollArea {{
                background: transparent;
                border: none;
            }}
            QScrollBar:vertical {{
                background: {COLORS['bg_secondary']};
                width: 8px;
                border-radius: 4px;
            }}
            QScrollBar::handle:vertical {{
                background: {COLORS['border']};
                border-radius: 4px;
                min-height: 30px;
            }}
            QScrollBar::handle:vertical:hover {{
                background: {COLORS['text_secondary']};
            }}
        """
        )

        # Grid container
        self.grid_container = QWidget()
        self.grid_layout = DashboardGridLayout(self.grid_container)
        self.grid_layout.layout_changed.connect(self._on_layout_changed)
        self.grid_layout.cell_clicked.connect(self._on_cell_clicked)

        container_layout = QVBoxLayout(self.grid_container)
        container_layout.setContentsMargins(0, 0, 0, 0)
        container_layout.addWidget(self.grid_layout)
        container_layout.addStretch()

        scroll.setWidget(self.grid_container)
        main_layout.addWidget(scroll, 1)

    def _create_header(self, parent_layout):
        """Header oluşturur"""
        header_layout = QHBoxLayout()

        # Başlık
        title = QLabel("Dashboard")
        title.setFont(QFont(FONT_FAMILY_QT, 20, QFont.Weight.Bold))
        title.setStyleSheet(f"color: {COLORS['text_primary']};")
        header_layout.addWidget(title)

        # Hoş geldin mesajı
        self._user_context = get_current_user()
        if self._user_context:
            welcome = QLabel(
                f"Hoş geldiniz, {self._user_context.full_name or self._user_context.username}"
            )
            welcome.setStyleSheet(
                f"color: {COLORS['text_secondary']}; font-size: 14px;"
            )
            header_layout.addWidget(welcome)

        header_layout.addStretch()

        # Düzenleme butonu
        self.edit_btn = QPushButton("Düzenle")
        self.edit_btn.setFixedHeight(36)
        self.edit_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.edit_btn.clicked.connect(self._toggle_edit_mode)
        self.edit_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLORS['bg_secondary']};
                border: 1px solid {COLORS['border']};
                border-radius: 6px;
                padding: 0 16px;
                color: {COLORS['text_primary']};
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {COLORS['bg_hover']};
                border-color: {COLORS['primary']};
            }}
        """
        )
        header_layout.addWidget(self.edit_btn)

        # Widget ekle butonu (sadece düzenleme modunda)
        self.add_btn = QPushButton("+ Widget Ekle")
        self.add_btn.setFixedHeight(36)
        self.add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.add_btn.clicked.connect(self._show_add_widget_dialog)
        self.add_btn.setVisible(False)
        self.add_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLORS['primary']};
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                color: white;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: {COLORS['primary_hover']};
            }}
        """
        )
        header_layout.addWidget(self.add_btn)

        # Sıfırla butonu
        self.reset_btn = QPushButton("Sıfırla")
        self.reset_btn.setFixedHeight(36)
        self.reset_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.reset_btn.clicked.connect(self._reset_layout)
        self.reset_btn.setVisible(False)
        self.reset_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLORS['warning']};
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                color: white;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: #e69500;
            }}
        """
        )
        header_layout.addWidget(self.reset_btn)

        # Yenile butonu
        self.refresh_btn = QPushButton("Yenile")
        self.refresh_btn.setFixedHeight(36)
        self.refresh_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        self.refresh_btn.clicked.connect(self._refresh_all)
        self.refresh_btn.setStyleSheet(
            f"""
            QPushButton {{
                background: {COLORS['success']};
                border: none;
                border-radius: 6px;
                padding: 0 16px;
                color: white;
                font-size: 13px;
            }}
            QPushButton:hover {{
                background: #28a745;
            }}
        """
        )
        header_layout.addWidget(self.refresh_btn)

        parent_layout.addLayout(header_layout)

    def _register_widgets(self):
        """Widget sınıflarını kaydet"""
        # Stat widget'ları
        try:
            from .widgets.stat_widget import (
                # Mevcut widget'lar
                SalesTodayWidget,
                PendingOrdersWidget,
                LowStockWidget,
                OpenWorkOrdersWidget,
                # Yeni widget'lar - Envanter
                TodayWarehouseEntryWidget,
                TodayWarehouseExitWidget,
                TotalStockValueWidget,
                # Yeni widget'lar - Satınalma
                TodayPurchasesWidget,
                PendingPurchaseOrdersWidget,
                # Yeni widget'lar - Satış/Sevkiyat
                TodayShipmentsWidget,
                PendingShipmentsWidget,
                # Yeni widget'lar - Üretim
                TodayProductionWidget,
                # Yeni widget'lar - Genel
                ActiveCustomersWidget,
                ActiveSuppliersWidget,
            )

            # Mevcut widget'lar
            WidgetManager.register(SalesTodayWidget)
            WidgetManager.register(PendingOrdersWidget)
            WidgetManager.register(LowStockWidget)
            WidgetManager.register(OpenWorkOrdersWidget)
            # Yeni widget'lar - Envanter
            WidgetManager.register(TodayWarehouseEntryWidget)
            WidgetManager.register(TodayWarehouseExitWidget)
            WidgetManager.register(TotalStockValueWidget)
            # Yeni widget'lar - Satınalma
            WidgetManager.register(TodayPurchasesWidget)
            WidgetManager.register(PendingPurchaseOrdersWidget)
            # Yeni widget'lar - Satış/Sevkiyat
            WidgetManager.register(TodayShipmentsWidget)
            WidgetManager.register(PendingShipmentsWidget)
            # Yeni widget'lar - Üretim
            WidgetManager.register(TodayProductionWidget)
            # Yeni widget'lar - Genel
            WidgetManager.register(ActiveCustomersWidget)
            WidgetManager.register(ActiveSuppliersWidget)
        except ImportError as e:
            print(f"Stat widget import hatası: {e}")

        # Dış veri widget'ları (ŞU AN DEVRE DIŞI - API timeout sorunları)
        # try:
        #     from .widgets.weather_widget import WeatherWidget
        #     WidgetManager.register(WeatherWidget)
        # except ImportError as e:
        #     print(f"Weather widget import hatası: {e}")

        # try:
        #     from .widgets.currency_widget import CurrencyWidget
        #     WidgetManager.register(CurrencyWidget)
        # except ImportError as e:
        #     print(f"Currency widget import hatası: {e}")

        # Liste widget'ları
        try:
            from .widgets.notification_widget import NotificationWidget

            WidgetManager.register(NotificationWidget)
        except ImportError as e:
            print(f"Notification widget import hatası: {e}")

        # Workflow widget'ları
        try:
            from .widgets.pending_approvals_widget import PendingApprovalsWidget

            WidgetManager.register(PendingApprovalsWidget)
        except ImportError as e:
            print(f"PendingApprovals widget import hatası: {e}")

        # Aksiyon widget'ları
        try:
            from .widgets.quick_action_widget import QuickActionWidget

            WidgetManager.register(QuickActionWidget)
        except ImportError as e:
            print(f"QuickAction widget import hatası: {e}")

        # Üretim/APS widget'ları
        try:
            from .widgets.bottleneck_widget import CapacityBottleneckDashboardWidget

            WidgetManager.register(CapacityBottleneckDashboardWidget)
        except ImportError as e:
            print(f"Bottleneck widget import hatası: {e}")

        # Gauge widget'ları
        try:
            from .widgets.gauge_widget import (
                CapacityGaugeWidget,
                EfficiencyGaugeWidget,
            )

            WidgetManager.register(CapacityGaugeWidget)
            WidgetManager.register(EfficiencyGaugeWidget)
        except ImportError as e:
            print(f"Gauge widget import hatası: {e}")

    def _load_layout(self):
        """Kullanıcı düzenini yükle"""
        self._user_context = get_current_user()
        if not self._user_context:
            return

        # Düzeni al
        layout_data = WidgetManager.get_effective_layout(self._user_context)

        # Widget'ları oluştur ve yerleştir
        self._apply_layout(layout_data)

    def _apply_layout(self, layout_data: Dict[str, Any]):
        """Düzeni uygular - staggered fade-in animasyonu ile"""
        self.grid_layout.clear_all()

        widgets_data = layout_data.get("widgets", [])
        widget_index = 0  # Animasyon gecikme indeksi

        for widget_data in widgets_data:
            widget_code = widget_data.get("widget_code")
            position = widget_data.get("position", {"row": 0, "col": 0})
            size = widget_data.get("size", {"width": 1, "height": 1})
            config = widget_data.get("config", {})

            # Widget oluştur
            widget_config = WidgetConfig(
                widget_code=widget_code, position=position, size=size, config=config
            )

            widget = WidgetManager.create_widget(
                widget_code, config=widget_config, edit_mode=self._edit_mode
            )

            if widget:
                # Erişim kontrolü
                if widget.can_user_access(self._user_context):
                    # Widget'ı başlangıçta gizle
                    widget.content_widget.setVisible(False)

                    self.grid_layout.add_widget(
                        widget,
                        row=position["row"],
                        col=position["col"],
                        width=size["width"],
                        height=size["height"],
                    )

                    # Staggered animasyon - her widget 50ms aralıkla
                    delay = widget_index * 50
                    QTimer.singleShot(
                        delay + 100, lambda w=widget: self._animate_widget_in(w)
                    )
                    widget_index += 1

    def _animate_widget_in(self, widget: BaseWidget):
        """Widget'ı fade-in animasyonu ile göster ve veri yükle"""
        widget.content_widget.setVisible(True)
        if widget.enable_animations:
            widget.fade_in(duration=300)
        # Veri yüklemesi
        QTimer.singleShot(50, widget.refresh_data)

    def _toggle_edit_mode(self):
        """Düzenleme modunu aç/kapat"""
        self._edit_mode = not self._edit_mode

        if self._edit_mode:
            self.edit_btn.setText("Kaydet")
            self.edit_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {COLORS['success']};
                    border: none;
                    border-radius: 6px;
                    padding: 0 16px;
                    color: white;
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: #28a745;
                }}
            """
            )
            self.add_btn.setVisible(True)
            self.reset_btn.setVisible(True)
        else:
            self.edit_btn.setText("Düzenle")
            self.edit_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background: {COLORS['bg_secondary']};
                    border: 1px solid {COLORS['border']};
                    border-radius: 6px;
                    padding: 0 16px;
                    color: {COLORS['text_primary']};
                    font-size: 13px;
                }}
                QPushButton:hover {{
                    background: {COLORS['bg_hover']};
                    border-color: {COLORS['primary']};
                }}
            """
            )
            self.add_btn.setVisible(False)
            self.reset_btn.setVisible(False)

            # Düzeni kaydet
            self._save_layout()

        self.grid_layout.set_edit_mode(self._edit_mode)

    def _show_add_widget_dialog(self):
        """Widget ekleme diyaloğunu göster"""
        # Mevcut widget'ları al
        current_widgets = set(self.grid_layout.get_all_widgets().keys())

        # Kullanılabilir widget'ları filtrele
        available = WidgetManager.get_available_widgets(self._user_context)
        available = [w for w in available if w.code not in current_widgets]

        if not available:
            show_toast("Eklenebilecek widget kalmadı.", "INFO")
            return

        dialog = AddWidgetDialog(available, self)
        if dialog.exec() == QDialog.DialogCode.Accepted and dialog.selected_widget:
            self._add_widget(dialog.selected_widget)

    def _add_widget(self, widget_code: str):
        """Widget ekle"""
        # Widget tanımını bul
        available = WidgetManager.get_available_widgets(self._user_context)
        widget_def = next((w for w in available if w.code == widget_code), None)

        if not widget_def:
            return

        # Boş pozisyon bul
        position = self.grid_layout.find_empty_position(
            width=widget_def.default_size[0], height=widget_def.default_size[1]
        )

        if not position:
            show_toast("Dashboard'da yeterli boş alan yok.", "WARNING")
            return

        # Widget oluştur
        config = WidgetConfig(
            widget_code=widget_code,
            position={"row": position[0], "col": position[1]},
            size={
                "width": widget_def.default_size[0],
                "height": widget_def.default_size[1],
            },
            config={},
        )

        widget = WidgetManager.create_widget(widget_code, config=config, edit_mode=True)

        if widget:
            self.grid_layout.add_widget(
                widget,
                row=position[0],
                col=position[1],
                width=widget_def.default_size[0],
                height=widget_def.default_size[1],
            )
            QTimer.singleShot(100, widget.refresh_data)

    def _on_cell_clicked(self, row: int, col: int):
        """Hücreye tıklandığında"""
        if self._edit_mode:
            self._show_add_widget_dialog()

    def _on_layout_changed(self):
        """Düzen değiştiğinde"""
        pass  # Otomatik kaydetme için kullanılabilir

    def _save_layout(self):
        """Düzeni kaydet"""
        if not self._user_context or not self._user_context.user_id:
            # Kullanıcı giriş yapmamışsa kaydetme
            return

        layout_data = self.grid_layout.get_layout_data()
        success = WidgetManager.save_user_layout(
            self._user_context.user_id, layout_data
        )

        if not success:
            show_toast("Düzen kaydedilemedi.", "ERROR")

    def _reset_layout(self):
        """Düzeni varsayılana sıfırla"""
        reply = QMessageBox.question(
            self,
            "Onay",
            "Dashboard düzeniniz varsayılana sıfırlanacak. Emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            if self._user_context and self._user_context.user_id:
                WidgetManager.reset_user_layout(self._user_context.user_id)

            # Varsayılan düzeni yükle
            default_layout = WidgetManager.get_default_layout(self._user_context)
            self._apply_layout(default_layout)

    def _refresh_all(self):
        """Tüm widget'ları yenile"""
        self.grid_layout.refresh_all()

    def showEvent(self, event):
        """Sayfa gösterildiğinde"""
        super().showEvent(event)
        # Widget'ları yenile
        QTimer.singleShot(500, self._refresh_all)
