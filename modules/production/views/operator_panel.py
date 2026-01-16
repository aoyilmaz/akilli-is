from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QGridLayout,
    QFrame,
    QMessageBox,
    QInputDialog,
    QDialog,
    QComboBox,
    QListWidget,
    QListWidgetItem,
    QTabWidget,
)
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QFont

from modules.production.services import WorkOrderService

# --- STYLES ---
TOUCH_BTN_STYLE = """
QPushButton {
    background-color: #3b82f6; 
    color: white; 
    border-radius: 12px; 
    font-size: 18px; 
    font-weight: bold;
    padding: 20px;
}
QPushButton:hover { background-color: #2563eb; }
QPushButton:pressed { background-color: #1d4ed8; }
QPushButton:disabled { background-color: #64748b; color: #cbd5e1; }
"""

SUCCESS_BTN_STYLE = """
QPushButton {
    background-color: #10b981; 
    color: white; 
    border-radius: 12px; 
    font-size: 18px; 
    font-weight: bold;
    padding: 20px;
}
QPushButton:hover { background-color: #059669; }
QPushButton:pressed { background-color: #047857; }
"""

WARNING_BTN_STYLE = """
QPushButton {
    background-color: #f59e0b; 
    color: white; 
    border-radius: 12px; 
    font-size: 18px; 
    font-weight: bold;
    padding: 20px;
}
QPushButton:hover { background-color: #d97706; }
QPushButton:pressed { background-color: #b45309; }
"""

DANGER_BTN_STYLE = """
QPushButton {
    background-color: #ef4444; 
    color: white; 
    border-radius: 12px; 
    font-size: 18px; 
    font-weight: bold;
    padding: 20px;
}
QPushButton:hover { background-color: #dc2626; }
QPushButton:pressed { background-color: #b91c1c; }
"""

CARD_STYLE = """
QFrame {
    background-color: #1e293b;
    border: 1px solid #334155;
    border-radius: 16px;
}
"""


class StationSelectDialog(QDialog):
    """İş istasyonu seçim dialogu"""

    def __init__(self, stations, parent=None):
        super().__init__(parent)
        self.setWindowTitle("İş İstasyonu Seçimi")
        self.setMinimumSize(500, 300)
        self.stations = stations
        self.selected_station = None
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(20)

        title = QLabel("Lütfen Çalışacağınız İstasyonu Seçin")
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title.setFont(QFont("Segoe UI", 16, QFont.Weight.Bold))
        layout.addWidget(title)

        self.combo = QComboBox()
        self.combo.setFixedHeight(50)
        self.combo.setFont(QFont("Segoe UI", 14))
        for s in self.stations:
            self.combo.addItem(f"{s.code} - {s.name}", s)

        layout.addWidget(self.combo)
        layout.addStretch()

        btn = QPushButton("Giriş Yap ->")
        btn.setStyleSheet(SUCCESS_BTN_STYLE)
        btn.clicked.connect(self.accept)
        layout.addWidget(btn)

    def get_selected(self):
        return self.combo.currentData()


class OperatorPanel(QWidget):
    page_title = "Operatör Paneli"

    def __init__(self):
        super().__init__()
        self.service = WorkOrderService()
        self.current_station = None
        self.active_operation = None
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_timer)
        self.selected_team_id = None
        self.setup_ui()

    def setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(20)

        # --- SOL TARA (İş Listesi) ---
        left_panel = QFrame()
        left_panel.setFixedWidth(350)
        left_panel.setStyleSheet(CARD_STYLE)
        left_layout = QVBoxLayout(left_panel)

        left_layout.addWidget(QLabel("📋 İş Listesi"))

        self.job_tabs = QTabWidget()
        self.job_tabs.setStyleSheet(
            """
            QTabWidget::pane { border: none; }
            QTabBar::tab { padding: 10px; background: #334155; border-top-left-radius: 8px; border-top-right-radius: 8px; margin-right: 2px; }
            QTabBar::tab:selected { background: #3b82f6; }
        """
        )

        # Bekleyen Listesi
        self.pending_list = QListWidget()
        self._style_job_list(self.pending_list)
        self.pending_list.itemClicked.connect(self._on_job_select)
        self.job_tabs.addTab(self.pending_list, "⏳ Bekleyen")

        # Tamamlanan Listesi
        self.completed_list = QListWidget()
        self._style_job_list(self.completed_list)
        self.completed_list.itemClicked.connect(self._on_job_select)
        self.job_tabs.addTab(self.completed_list, "✅ Biten")

        left_layout.addWidget(self.job_tabs)

        refresh_btn = QPushButton("🔄 Listeyi Yenile")
        refresh_btn.setStyleSheet(
            "padding: 10px; border-radius: 8px; background-color: #475569;"
        )
        refresh_btn.clicked.connect(self._load_jobs)
        left_layout.addWidget(refresh_btn)

        layout.addWidget(left_panel)

        # --- ORTA (Aktif İş Detayı & Kontroller) ---
        center_panel = QFrame()
        center_panel.setStyleSheet("QFrame { background: transparent; }")
        center_layout = QVBoxLayout(center_panel)
        center_layout.setSpacing(20)

        # Header (İstasyon Bilgisi)
        header_frame = QFrame()
        header_frame.setStyleSheet(CARD_STYLE)
        header_layout = QHBoxLayout(header_frame)
        self.station_label = QLabel("İstasyon Seçilmedi")
        self.station_label.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        header_layout.addWidget(self.station_label)
        header_layout.addStretch()

        change_station_btn = QPushButton("İstasyon Değiştir")
        change_station_btn.clicked.connect(self._select_station)
        header_layout.addWidget(change_station_btn)
        center_layout.addWidget(header_frame)

        # Aktif İş Kartı
        self.active_job_card = QFrame()
        self.active_job_card.setStyleSheet(CARD_STYLE)
        self.active_job_card.hide()
        active_layout = QVBoxLayout(self.active_job_card)

        # İş Bilgileri
        self.job_title = QLabel()
        self.job_title.setFont(QFont("Segoe UI", 24, QFont.Weight.Bold))
        self.job_title.setStyleSheet("color: #60a5fa;")
        active_layout.addWidget(self.job_title)

        self.job_detail = QLabel()
        self.job_detail.setFont(QFont("Segoe UI", 16))
        self.job_detail.setWordWrap(True)
        active_layout.addWidget(self.job_detail)

        # Özel Notlar Alanı
        self.notes_label = QLabel()
        self.notes_label.setFont(QFont("Segoe UI", 12))
        self.notes_label.setWordWrap(True)
        self.notes_label.setStyleSheet(
            "background-color: rgba(245, 158, 11, 0.1); border: 1px solid #f59e0b40; "
            "border-radius: 8px; padding: 10px; color: #fbbf24; margin-top: 10px;"
        )
        self.notes_label.hide()
        active_layout.addWidget(self.notes_label)

        # Timer Display
        self.timer_label = QLabel("00:00:00")
        self.timer_label.setFont(QFont("Segoe UI", 48, QFont.Weight.Bold))
        self.timer_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.timer_label.setStyleSheet("color: #ef4444; margin: 20px 0;")
        active_layout.addWidget(self.timer_label)

        # Aksiyon Butonları Grid
        actions_grid = QGridLayout()
        actions_grid.setSpacing(15)

        self.btn_start = QPushButton("▶️ BAŞLAT")
        self.btn_start.setStyleSheet(SUCCESS_BTN_STYLE)
        self.btn_start.clicked.connect(self._start_operation)
        actions_grid.addWidget(self.btn_start, 0, 0, 1, 2)

        self.btn_pause = QPushButton("⏸ DURAKLAT")
        self.btn_pause.setStyleSheet(WARNING_BTN_STYLE)
        self.btn_pause.clicked.connect(self._pause_operation)
        actions_grid.addWidget(self.btn_pause, 0, 0, 1, 2)

        self.btn_scrap = QPushButton("🗑 HURDA GİR")
        self.btn_scrap.setStyleSheet(DANGER_BTN_STYLE)
        self.btn_scrap.clicked.connect(self._report_scrap)
        actions_grid.addWidget(self.btn_scrap, 1, 0)

        self.btn_packet = QPushButton("📦 PAKETLE")
        self.btn_packet.setStyleSheet(TOUCH_BTN_STYLE)
        self.btn_packet.clicked.connect(self._partial_production)
        actions_grid.addWidget(self.btn_packet, 1, 1)

        self.btn_finish = QPushButton("✅ İŞİ BİTİR")
        self.btn_finish.setStyleSheet(
            SUCCESS_BTN_STYLE
        )  # Different blue or success color
        self.btn_finish.setStyleSheet(
            "background-color: #0d9488; color: white; border-radius: 12px; font-size: 18px; font-weight: bold; padding: 20px;"
        )
        self.btn_finish.clicked.connect(self._finish_operation)
        actions_grid.addWidget(self.btn_finish, 2, 0, 1, 2)

        active_layout.addLayout(actions_grid)
        center_layout.addWidget(self.active_job_card)

        # Empty State
        self.empty_state = QLabel(
            "🖱 Lütfen listeden bir iş seçin veya barkod okutun..."
        )
        self.empty_state.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.empty_state.setStyleSheet("color: #94a3b8; font-size: 18px;")
        center_layout.addWidget(self.empty_state)

        center_layout.addStretch()
        layout.addWidget(center_panel, stretch=1)

        # --- SAĞ (Personel Listesi) ---
        right_panel = QFrame()
        right_panel.setFixedWidth(250)
        right_panel.setStyleSheet(CARD_STYLE)
        right_layout = QVBoxLayout(right_panel)

        right_layout.addWidget(QLabel("👥 Çalışanlar"))
        self.personnel_list = QListWidget()
        right_layout.addWidget(self.personnel_list)

        add_personnel_btn = QPushButton("➕ Personel Ekle")
        add_personnel_btn.clicked.connect(self._add_personnel)
        right_layout.addWidget(add_personnel_btn)

        right_layout.addSpacing(20)
        right_layout.addWidget(QLabel("🗑 Hurda/Fire Geçmişi"))
        self.scrap_list = QListWidget()
        self.scrap_list.setStyleSheet("font-size: 11px;")
        right_layout.addWidget(self.scrap_list)

        layout.addWidget(right_panel)

    def _style_job_list(self, list_widget: QListWidget):
        """İş listesi stilini uygula"""
        list_widget.setStyleSheet(
            "QListWidget { background-color: transparent; border: none; font-size: 14px; } "
            "QListWidget::item { padding: 12px; margin-bottom: 8px; background-color: #334155; border-radius: 8px; }"
            "QListWidget::item:selected { background-color: #3b82f6; }"
        )

    def _select_station(self):
        # Tüm istasyonları getir
        # Not: Service'e get_stations eklenmeli veya generic service kullanılmalı.
        # Şimdilik dummy data veya direkt DB sorgusu yapabiliriz ama service'den çekmek doğru.
        # Hızlıca WorkStation modelini import edip sorgulayalım
        from database.models.production import WorkStation

        with self.service.session as session:
            stations = session.query(WorkStation).all()

        dialog = StationSelectDialog(stations, self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            self.current_station = dialog.get_selected()
            self.station_label.setText(
                f"🔧 {self.current_station.code} - {self.current_station.name}"
            )
            self._load_jobs()

    def _load_jobs(self):
        if not self.current_station:
            return

        self.pending_list.clear()
        self.completed_list.clear()

        from database.models.production import WorkOrderOperation
        from sqlalchemy.orm import joinedload

        # Tüm operasyonları çek
        ops = (
            self.service.session.query(WorkOrderOperation)
            .options(joinedload(WorkOrderOperation.work_order))
            .filter(WorkOrderOperation.work_station_id == self.current_station.id)
            .all()
        )

        for op in ops:
            status_icon = "⏳"
            target_list = self.pending_list

            if op.status == "in_progress":
                status_icon = "▶️"
            elif op.status == "paused":
                status_icon = "⏸"
            elif op.status == "completed":
                status_icon = "✅"
                target_list = self.completed_list

            # Tamamlanmamış ve bitmişleri ilgili listeye at
            if op.status in ["pending", "in_progress", "paused"]:
                target_list = self.pending_list
            elif op.status == "completed":
                target_list = self.completed_list
            else:
                continue  # Diğer durumlar (cancelled vs) gösterilmesin

            item = QListWidgetItem(
                f"{status_icon} {op.work_order.order_no} - {op.name}"
            )
            item.setData(Qt.ItemDataRole.UserRole, op.id)
            target_list.addItem(item)

    def _on_job_select(self, item):
        op_id = item.data(Qt.ItemDataRole.UserRole)
        self._load_job_details(op_id)

    def _load_job_details(self, op_id):
        # Detayları service üzerinden alabiliriz veya query
        from database.models.production import WorkOrderOperation, WorkOrder
        from sqlalchemy.orm import joinedload

        op = (
            self.service.session.query(WorkOrderOperation)
            .options(
                joinedload(WorkOrderOperation.work_order).joinedload(WorkOrder.item)
            )
            .get(op_id)
        )

        self.active_operation = op

        # UI Güncelle
        self.empty_state.hide()
        self.active_job_card.show()

        self.job_title.setText(f"{op.work_order.order_no}")
        self.job_detail.setText(
            f"Ürün: {op.work_order.item.name}\n"
            f"Operasyon: {op.name}\n"
            f"Miktar: {op.work_order.planned_quantity} {op.work_order.unit.code if op.work_order.unit else ''}\n"
            f"Tamamlanan: {op.completed_quantity or 0}"
        )

        # Özel Notlar Gösterimi
        notes_text = ""
        if op.work_order.production_notes:
            notes_text += f"🔧 ÜRETİM: {op.work_order.production_notes}\n"
        if op.work_order.quality_notes:
            notes_text += f"🛡️ KALİTE: {op.work_order.quality_notes}\n"
        if op.work_order.shipping_notes:
            notes_text += f"📦 SEVKİYAT: {op.work_order.shipping_notes}"

        if notes_text:
            self.notes_label.setText(notes_text)
            self.notes_label.show()
        else:
            self.notes_label.hide()

        self._update_buttons(op.status)
        self._update_personnel_list()
        self._update_scrap_list()

        # Timer başlat
        if op.status == "in_progress":
            self.timer.start(1000)
        else:
            self.timer.stop()
            self._update_timer()  # Statik göster

    def _update_buttons(self, status):
        if status == "in_progress":
            self.btn_start.hide()
            self.btn_pause.show()
            self.btn_finish.show()
            self.btn_scrap.setEnabled(True)
            self.btn_packet.setEnabled(True)
            self.active_job_card.setStyleSheet(
                CARD_STYLE + "QFrame { border: 2px solid #3b82f6; }"
            )
        elif status == "paused":
            self.btn_start.setText("▶️ DEVAM ET")
            self.btn_start.show()
            self.btn_pause.hide()
            self.btn_finish.hide()
            self.btn_scrap.setEnabled(False)
            self.btn_packet.setEnabled(False)
            self.active_job_card.setStyleSheet(
                CARD_STYLE + "QFrame { border: 2px solid #f59e0b; }"
            )
        elif status == "completed":
            self.btn_start.hide()
            self.btn_pause.hide()
            self.btn_finish.hide()
            self.btn_scrap.setEnabled(False)
            self.btn_packet.setEnabled(False)
            self.active_job_card.setStyleSheet(
                CARD_STYLE + "QFrame { border: 2px solid #10b981; }"
            )
        else:  # pending
            self.btn_start.setText("▶️ BAŞLAT")
            self.btn_start.show()
            self.btn_pause.hide()
            self.btn_finish.hide()
            self.btn_scrap.setEnabled(False)
            self.btn_packet.setEnabled(False)
            self.active_job_card.setStyleSheet(CARD_STYLE)

    def _update_timer(self):
        if not self.active_operation:
            return

        total_seconds = (self.active_operation.actual_run_time or 0) * 60

        if (
            self.active_operation.status == "in_progress"
            and self.active_operation.last_start_time
        ):
            from datetime import datetime

            delta = datetime.now() - self.active_operation.last_start_time
            total_seconds += delta.total_seconds()

        hours = int(total_seconds // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = int(total_seconds % 60)

        self.timer_label.setText(f"{hours:02d}:{minutes:02d}:{seconds:02d}")

    def _start_operation(self):
        if not self.active_operation:
            return
        try:
            self.service.start_operation(self.active_operation.id)
            self._load_job_details(self.active_operation.id)
            self._load_jobs()  # Listeyi güncelle (ikon değişimi)
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _pause_operation(self):
        if not self.active_operation:
            return
        try:
            self.service.pause_operation(self.active_operation.id)
            self._load_job_details(self.active_operation.id)
            self._load_jobs()
        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _partial_production(self):
        if not self.active_operation:
            return

        qty, ok = QInputDialog.getDouble(
            self, "Paketleme", "Paket Miktarı:", 100, 0, 100000, 2
        )
        if ok:
            try:
                result = self.service.create_partial_production(
                    self.active_operation.id, qty
                )
                QMessageBox.information(
                    self,
                    "Etiket Oluşturuldu",
                    f"Etiket ID: {result['pack_id']}\n"
                    f"Ürün: {result['item_name']}\n"
                    f"Miktar: {result['quantity']}",
                )
                self._load_job_details(self.active_operation.id)
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _report_scrap(self):
        if not self.active_operation:
            return

        qty, ok = QInputDialog.getDouble(
            self, "Hurda Girişi", "Hurda Miktarı:", 0, 0, 100000, 2
        )
        if ok:
            try:
                reason, ok2 = QInputDialog.getText(self, "Hurda Nedeni", "Açıklama:")
                if not ok2:
                    return

                # Service layer report_scrap calls for operation_id
                self.service.report_scrap(
                    operation_id=self.active_operation.id, quantity=qty, reason=reason
                )
                QMessageBox.information(self, "Başarılı", "Hurda kaydı alındı.")
                self._update_scrap_list()  # Refresh list
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _finish_operation(self):
        if not self.active_operation:
            return

        reply = QMessageBox.question(
            self,
            "Onay",
            "İş emrini tamamlamak istediğinize emin misiniz?",
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,
        )

        if reply == QMessageBox.StandardButton.Yes:
            try:
                # Tamamla
                self.service.complete_operation(self.active_operation.id)
                QMessageBox.information(self, "Başarılı", "İş emri tamamlandı.")
                self.active_job_card.hide()
                self.empty_state.show()
                self._load_jobs()
            except Exception as e:
                QMessageBox.critical(self, "Hata", str(e))

    def _add_personnel(self):
        if not self.active_operation:
            return

        try:
            # 1. Vardiya Ekiplerini Getir (Sticky Shift)
            if not self.selected_team_id:
                teams = self.service.get_shift_teams()
                if not teams:
                    QMessageBox.warning(
                        self, "Uyarı", "Tanımlı vardiya ekibi bulunamadı!"
                    )
                    # Fallback: Tüm personeli getir
                    users = self.service.get_all_users()
                else:
                    team_list = [f"{t.name}" for t in teams]
                    # Vardiya Seçimi
                    team_name, ok_team = QInputDialog.getItem(
                        self,
                        "Vardiya Seçimi",
                        "Vardiya Ekibi Seçiniz:",
                        team_list,
                        0,
                        False,
                    )

                    if not ok_team:
                        return

                    # Seçilen ekibe göre personeli filtrele
                    idx_team = team_list.index(team_name)
                    selected_team = teams[idx_team]
                    self.selected_team_id = selected_team.id
                    users = self.service.get_users_by_team(self.selected_team_id)
            else:
                users = self.service.get_users_by_team(self.selected_team_id)

            if not users:
                QMessageBox.warning(
                    self,
                    "Uyarı",
                    "Bu vardiyada uygun (meşgul olmayan) personel bulunamadı!",
                )
                return

            # 2. Personel Seçimi
            user_list = [f"{u.first_name} {u.last_name} ({u.username})" for u in users]

            item, ok = QInputDialog.getItem(
                self, "Personel Ekle", "Personel Seçiniz:", user_list, 0, False
            )

            if ok and item:
                # Seçilen personeli bul
                idx = user_list.index(item)
                user = users[idx]

                self.service.assign_personnel(self.active_operation.id, user.id)
                QMessageBox.information(
                    self, "Başarılı", f"{user.first_name} {user.last_name} atandı."
                )
                self._update_personnel_list()

        except Exception as e:
            QMessageBox.critical(self, "Hata", str(e))

    def _update_personnel_list(self):
        """Aktif personelleri sağ listede güncelle"""
        if not self.active_operation:
            self.personnel_list.clear()
            return

        try:
            self.personnel_list.clear()
            active_p = self.service.get_active_personnel(self.active_operation.id)
            for p in active_p:
                if p.user:
                    name = f"{p.user.first_name} {p.user.last_name}"
                    item = QListWidgetItem(f"👤 {name}\n({p.role.upper()})")
                    item.setData(Qt.ItemDataRole.UserRole, p.id)  # Use assignment ID
                    self.personnel_list.addItem(item)
        except Exception as e:
            print(f"Personel listesi güncellenirken hata: {e}")

    def _update_scrap_list(self):
        """Hurda listesini güncelle"""
        if not self.active_operation:
            self.scrap_list.clear()
            return

        try:
            self.scrap_list.clear()
            from database.models.inventory import StockMovement

            scraps = (
                self.service.session.query(StockMovement)
                .filter(
                    StockMovement.document_type == "production_scrap",
                    StockMovement.document_no == str(self.active_operation.id),
                )
                .order_by(StockMovement.movement_date.desc())
                .all()
            )

            for s in scraps:
                item = QListWidgetItem(
                    f"{s.quantity:.2f} - {s.notes or 'Neden Belirtilmedi'}"
                )
                self.scrap_list.addItem(item)
        except Exception as e:
            print(f"Hurda listesi hatası: {e}")
