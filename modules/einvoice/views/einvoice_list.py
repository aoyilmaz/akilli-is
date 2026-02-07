from datetime import datetime
from PyQt6.QtWidgets import QWidget, QHBoxLayout, QTableWidgetItem
from PyQt6.QtCore import Qt, pyqtSignal

from config.icons import ICONS
from ui.components import BaseListPage, ColumnConfig
from database.models.einvoice import EInvoiceStatus


class EInvoiceListPage(BaseListPage):
    """
    e-Faturalar listesi sayfası.
    """

    send_clicked = pyqtSignal(str)  # UUID
    status_check_clicked = pyqtSignal(str)  # UUID
    xml_clicked = pyqtSignal(str)  # UUID
    html_clicked = pyqtSignal(str)  # UUID
    view_clicked = pyqtSignal(str)  # UUID override (Standard uses int id, here uuid)

    STATUS_LABELS = {
        EInvoiceStatus.DRAFT: ("Taslak", "#64748b"),
        EInvoiceStatus.QUEUED: ("Kuyrukta", "#f59e0b"),
        EInvoiceStatus.PROCESSING: ("İşleniyor", "#3b82f6"),
        EInvoiceStatus.SENT: ("Gönderildi", "#10b981"),
        EInvoiceStatus.DELIVERED: ("Teslim Edildi", "#059669"),
        EInvoiceStatus.ACCEPTED: ("Kabul Edildi", "#15803d"),
        EInvoiceStatus.REJECTED: ("Reddedildi", "#ef4444"),
        EInvoiceStatus.ERROR: ("Hata", "#dc2626"),
        EInvoiceStatus.CANCELLED: ("İptal", "#475569"),
    }

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("created_at", "Tarih", width=110, filter_type="date"),
            ColumnConfig("invoice_number", "Fatura No", width=140),
            ColumnConfig("receiver", "Alıcı", width=200, stretch=True),
            ColumnConfig("profile", "Senaryo", width=120, filter_type="text"),
            ColumnConfig("type", "Tip", width=100, filter_type="text"),
            ColumnConfig("status", "Durum", width=120, filter_type="enum"),
            ColumnConfig("gib_status", "GIB Kodu", width=80),
            ColumnConfig(
                "actions", "İşlemler", width=180, resizable=False, movable=False
            ),
        ]

        super().__init__(
            title="e-Faturalar",
            icon=ICONS.INVOICE,
            table_id="einvoices",
            columns=columns,
            show_stats=True,
            show_search=True,
            show_add=False,
            search_placeholder="Ara... (fatura no, alıcı, vkn)",
            parent=parent,
        )
        self.einvoices = []
        self._setup_stat_cards()

    def _setup_stat_cards(self):
        self.add_stat_card("total", "Toplam", "0", "info", ICONS.INVOICE)
        self.add_stat_card("draft", "Taslak", "0", "secondary", ICONS.EDIT)
        self.add_stat_card("sent", "Gönderildi", "0", "info", ICONS.EXPORT)
        self.add_stat_card("error", "Hatalı", "0", "error", ICONS.DANGER)
        self.add_stat_card("accepted", "Kabul", "0", "success", ICONS.CHECK)

    def load_data(self, data: list):
        self.einvoices = data
        self._display_data(data)
        self._update_stats()

    def _display_data(self, data: list):
        self.table.setRowCount(len(data))
        visible_cols = self.table.get_visible_columns()
        for row, item in enumerate(data):
            self._populate_row(row, item, visible_cols)

    def _populate_row(self, row: int, item: dict, visible_cols: list):
        uuid = item.get("uuid")

        for col_idx, col_key in enumerate(visible_cols):
            val = item.get(col_key, "")

            if col_key == "created_at":
                dt = item.get("created_at")
                if isinstance(dt, str):
                    try:
                        dt = datetime.fromisoformat(dt)
                    except:
                        pass
                val = (
                    dt.strftime("%d.%m.%Y %H:%M")
                    if isinstance(dt, datetime)
                    else str(val)
                )
                self.table.setItem(row, col_idx, QTableWidgetItem(val))

            elif col_key == "receiver":
                vkn = item.get("receiver_vkn", "")
                name = item.get("receiver_alias", "")
                text = f"{vkn} - {name}" if vkn else name
                self.table.setItem(row, col_idx, QTableWidgetItem(text))

            elif col_key == "status":
                status = val  # Enum member or string
                text, color = self.STATUS_LABELS.get(status, (str(status), "#000"))
                widget_item = QTableWidgetItem(text)
                # TODO: Set foreground color if supported easily,
                # but QTableWidgetItem doesn't take hex string easily without QColor.
                # skipping color for now or standardizing.
                self.table.setItem(row, col_idx, widget_item)

            elif col_key == "actions":
                self._add_actions(row, col_idx, item)

            else:
                self.table.setItem(
                    row, col_idx, QTableWidgetItem(str(val) if val is not None else "")
                )

    def _add_actions(self, row, col, item):
        from ui.components.action_buttons import create_custom_button

        widget = QWidget()
        layout = QHBoxLayout(widget)
        layout.setContentsMargins(2, 2, 2, 2)
        layout.setSpacing(4)

        uuid = item.get("uuid")
        status = item.get("status")

        # HTML/Preview
        preview_btn = create_custom_button(widget, ICONS.VIEW, "Önizle", "info")
        preview_btn.clicked.connect(lambda: self.html_clicked.emit(uuid))
        layout.addWidget(preview_btn)

        if status == EInvoiceStatus.DRAFT:
            send_btn = create_custom_button(widget, ICONS.EXPORT, "Gönder", "primary")
            send_btn.clicked.connect(lambda: self.send_clicked.emit(uuid))
            layout.addWidget(send_btn)

        elif status not in [
            EInvoiceStatus.DRAFT,
            EInvoiceStatus.ERROR,
            EInvoiceStatus.CANCELLED,
        ]:
            check_btn = create_custom_button(
                widget, ICONS.REFRESH, "Sorgula", "secondary"
            )
            check_btn.setToolTip("GIB Durumunu Sorgula")
            check_btn.clicked.connect(lambda: self.status_check_clicked.emit(uuid))
            layout.addWidget(check_btn)

        layout.addStretch()
        self.table.setCellWidget(row, col, widget)

    def _update_stats(self):
        total = len(self.einvoices)
        draft = sum(
            1 for i in self.einvoices if i.get("status") == EInvoiceStatus.DRAFT
        )
        sent = sum(
            1
            for i in self.einvoices
            if i.get("status")
            in [EInvoiceStatus.SENT, EInvoiceStatus.QUEUED, EInvoiceStatus.PROCESSING]
        )
        error = sum(
            1 for i in self.einvoices if i.get("status") == EInvoiceStatus.ERROR
        )
        accepted = sum(
            1 for i in self.einvoices if i.get("status") == EInvoiceStatus.ACCEPTED
        )

        self.update_stat_card("total", str(total))
        self.update_stat_card("draft", str(draft))
        self.update_stat_card("sent", str(sent))
        self.update_stat_card("error", str(error))
        self.update_stat_card("accepted", str(accepted))
