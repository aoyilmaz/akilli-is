"""
Trace Görüntüleyici Widget
Kullanıcı trace oturumlarını ve detaylarını görüntüler.
"""

from datetime import datetime
from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QSplitter,
    QListWidget,
    QListWidgetItem,
    QTextEdit,
    QLabel,
    QPushButton,
    QGroupBox,
)
from PyQt6.QtCore import Qt

from database.base import get_session
from database.models.development import TraceSession, TraceEvent, TraceEventType
from database.models.user import User


class TraceViewerWidget(QWidget):
    """
    Trace Görüntüleyici
    Sol: Oturum Listesi
    Sağ: Detaylı Log (Renklendirilmiş)
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = None
        self.setup_ui()
        self.load_sessions()

    def setup_ui(self):
        layout = QVBoxLayout(self)

        # Başlık ve Yenile Butonu
        header_layout = QHBoxLayout()
        header_layout.addWidget(QLabel("<h2>🕵️ Trace İnceleme</h2>"))
        header_layout.addStretch()

        refresh_btn = QPushButton("🔄 Yenile")
        refresh_btn.clicked.connect(self.load_sessions)
        header_layout.addWidget(refresh_btn)

        layout.addLayout(header_layout)

        # Splitter (Sol: Liste, Sağ: Detay)
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # --- SOL TARAFF: OTURUM LİSTESİ ---
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)

        left_layout.addWidget(QLabel("<b>Son Oturumlar:</b>"))
        self.session_list = QListWidget()
        self.session_list.currentRowChanged.connect(self.load_trace_detail)
        left_layout.addWidget(self.session_list)

        splitter.addWidget(left_widget)

        # --- SAĞ TARAF: DETAY ---
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)

        right_layout.addWidget(QLabel("<b>Oturum Detayı:</b>"))
        self.log_view = QTextEdit()
        self.log_view.setReadOnly(True)
        self.log_view.setStyleSheet(
            "font-family: Consolas, Monaco, monospace; font-size: 13px;"
        )
        right_layout.addWidget(self.log_view)

        splitter.addWidget(right_widget)

        # Oranlar: %30 liste, %70 detay
        splitter.setSizes([300, 700])

        layout.addWidget(splitter)

    def _get_db_session(self):
        if self.session is None:
            self.session = get_session()
        return self.session

    def load_sessions(self):
        """Son trace oturumlarını listeler"""
        session = self._get_db_session()
        try:
            # Son 50 oturumu çek
            trace_sessions = (
                session.query(TraceSession)
                .join(User)
                .order_by(TraceSession.started_at.desc())
                .limit(50)
                .all()
            )

            self.session_list.clear()
            for ts in trace_sessions:
                user_name = ts.user.username if ts.user else "Bilinmiyor"
                start_str = ts.started_at.strftime("%H:%M:%S")
                date_str = ts.started_at.strftime("%d.%m.%Y")

                item_text = f"{date_str} {start_str} - {user_name} ({ts.status.value})"
                item = QListWidgetItem(item_text)
                item.setData(Qt.ItemDataRole.UserRole, ts.id)
                self.session_list.addItem(item)

        except Exception as e:
            self.log_view.setHtml(
                f"<h3 style='color:red'>Veri yükleme hatası: {e}</h3>"
            )

    def load_trace_detail(self, row_index):
        """Seçili oturumun detaylarını yükle ve formatla"""
        if row_index < 0:
            return

        item = self.session_list.item(row_index)
        session_id = item.data(Qt.ItemDataRole.UserRole)

        session = self._get_db_session()
        try:
            trace_session = session.query(TraceSession).get(session_id)
            if not trace_session:
                return

            events = (
                session.query(TraceEvent)
                .filter(TraceEvent.session_id == session_id)
                .order_by(TraceEvent.timestamp)
                .all()
            )

            # HTML formatını oluştur
            html = self._format_trace_to_html(trace_session, events)
            self.log_view.setHtml(html)

        except Exception as e:
            self.log_view.setHtml(f"<h3 style='color:red'>Detay hatası: {e}</h3>")

    def _format_trace_to_html(self, session, events):
        """
        Kullanıcının istediği format:
        BAŞLANGIÇ: Destek Modu Açıldı (Kullanıcı: Okan)
        SAYFA: SalesOrderPage açıldı.
        ...
        """
        lines = []
        user_name = session.user.username if session.user else "?"
        start_time = session.started_at.strftime("%H:%M:%S")

        # Başlangıç Satırı
        lines.append(
            f"<div style='color:#6c5ce7'><b>BAŞLANGIÇ [{start_time}]:</b> "
            f"Destek Modu Açıldı (Kullanıcı: {user_name})</div>"
        )

        for event in events:
            time_str = event.timestamp.strftime("%H:%M:%S")
            data = event.event_data or {}

            line = ""

            # 1. SAYFA (Navigasyon)
            if event.event_type == TraceEventType.PAGE_NAVIGATION:
                page = event.widget_name or "Bilinmeyen Sayfa"
                line = (
                    f"<span style='color:#e67e22'><b>SAYFA:</b> {page} açıldı.</span>"
                )

            # 2. FİLTRE (Arama / Form Input)
            elif event.event_type == TraceEventType.FORM_INPUT:
                if "SearchInput" in (event.widget_name or "") or data.get(
                    "placeholder", ""
                ).startswith("Ara"):
                    val = data.get("value", "")
                    line = f"<span style='color:#2980b9'><b>FİLTRE:</b> '{val}' araması yapıldı.</span>"
                elif data.get("action") == "clipboard_copy":
                    line = f"<span style='color:#2980b9'><b>COPY (Panoya Kopyalandı):</b> {data.get('source_widget')}</span>"
                elif data.get("action") == "clipboard_paste":
                    content = data.get("content", "")
                    line = f"<span style='color:#2980b9'><b>PASTE (Yapıştırıldı):</b> '{content}'</span>"
                else:
                    field = event.widget_name
                    val = data.get("value", "")
                    line = f"<span><b>GİRİŞ:</b> {field} = '{val}'</span>"

            # 3. SEÇİM (Tablo Seçimi)
            elif event.event_type == TraceEventType.TABLE_SELECTION:
                detail = ""
                if "item_text" in data:
                    detail = f"'{data['item_text']}'"
                elif "row_index" in data:
                    # col_0, col_1 gibi verileri topla
                    cols = [v for k, v in data.items() if k.startswith("col_")]
                    detail = f"Satır {data['row_index']} ({', '.join(cols)})"

                line = f"<span style='color:#27ae60'><b>SEÇİM:</b> {detail} seçildi.</span>"

            # 4. BUTON
            elif event.event_type == TraceEventType.BUTTON_CLICK:
                btn_text = data.get("button_text", event.widget_name)
                line = f"<span style='color:#27ae60'><b>BUTON:</b> '{btn_text}' butonuna tıklandı.</span>"

            # 5. SERVİS (Method Call)
            elif event.event_type == TraceEventType.METHOD_CALL:
                method = event.widget_name
                duration = data.get("duration_ms", 0)
                line = f"<span style='color:#8e44ad'><b>SERVİS:</b> {method} çağrıldı ({duration}ms).</span>"

            # 6. SQL
            elif event.event_type == TraceEventType.SQL_QUERY:
                sql = data.get("sql", "")
                duration = data.get("duration_ms", 0)
                # SQL'i biraz kısalt
                if len(sql) > 150:
                    sql = sql[:150] + "..."
                row_count = data.get("row_count", 0)
                line = f"<span style='color:#7f8c8d'><i>SQL: {sql} (Süre: {duration}ms, Rows: {row_count})</i></span>"

            # 7. LOG / MESSAGE BOX
            elif event.event_type == TraceEventType.LOG_ENTRY:
                msg_type = data.get("type", "")
                if msg_type == "message_box":
                    title = data.get("title", "")
                    msg = data.get("message", "")
                    level = data.get("level", "")
                    color = "red" if level in ("critical", "warning") else "blue"
                    line = f"<span style='color:{color}'><b>UYARI ({level}):</b> [{title}] {msg}</span>"
                else:
                    line = f"<span style='color:#95a5a6'>LOG: {data}</span>"

            # 8. HATA
            elif event.event_type == TraceEventType.ERROR_OCCURRED:
                err_type = data.get("error_type", "Hata")
                err_msg = data.get("error_message", "")
                line = f"<span style='color:#c0392b'><b>HATA:</b> {err_type}: {err_msg}</span>"

            # 9. SYSTEM
            elif event.event_type == TraceEventType.SYSTEM_STATS:
                cpu = data.get("cpu_percent", 0)
                ram = data.get("memory_percent", 0)
                line = f"<span style='color:#34495e'><b>SİSTEM:</b> CPU: %{cpu}, RAM: %{ram}</span>"

            # Diğerleri
            else:
                line = f"<span>{event.event_type.value}: {event.widget_name}</span>"

            if line:
                lines.append(f"<div><small>[{time_str}]</small> {line}</div><br>")

        # Bitiş Satırı
        end_time = (
            session.ended_at.strftime("%H:%M:%S")
            if session.ended_at
            else "Devam Ediyor"
        )
        status_tr = {
            "active": "Aktif",
            "completed": "Tamamlandı",
            "error": "Hata",
            "timeout": "Zaman Aşımı",
        }.get(session.status.value, session.status.value)

        lines.append(
            f"<div style='color:#6c5ce7'><b>BİTİŞ [{end_time}]:</b> "
            f"Trace durumu: {status_tr}.</div>"
        )

        return "".join(lines)

    def closeEvent(self, event):
        if self.session:
            self.session.close()
        super().closeEvent(event)
