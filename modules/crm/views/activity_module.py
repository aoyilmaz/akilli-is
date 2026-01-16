from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from .activity_timeline import ActivityTimeline
from .activity_form import ActivityFormPage
from modules.development import ErrorHandler
from database.base import get_session
from modules.crm.services import CRMService
from database.models.crm import ActivityType


class ActivityModule(QWidget):
    """Aktivite Yönetimi Modülü"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = get_session()
        self.service = CRMService(self.session)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        self.stack = QStackedWidget()

        # Zaman Çizelgesi
        self.timeline_page = ActivityTimeline()
        self.timeline_page.add_clicked.connect(self._show_add_form)
        self.timeline_page.card_clicked.connect(self._show_edit_form)
        self.timeline_page.refresh_clicked.connect(self._load_data)

        self.stack.addWidget(self.timeline_page)
        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        try:
            # Aktiviteleri çek (Şu anki servicete list_activities yok mu? Kontrol edelim)
            # Service koduna bakmadım ama create_activity, log_activity vardı.
            # list_activities yoksa eklemeli veya query kullanmalıyım.
            # Base service query pattern support ediyor mu?
            # Basic SQLAlchemy ile çekelim.

            from database.models.crm import Activity, Lead

            # Tarihe göre tersten sırala (En yeni en üstte)
            activities = (
                self.session.query(Activity).order_by(Activity.due_date.desc()).all()
            )

            data = []
            for act in activities:
                d = {
                    "id": act.id,
                    "subject": act.subject,
                    "activity_type": act.activity_type.value,  # Display value
                    "activity_type_name": act.activity_type.name,  # Enum key for edit form
                    "due_date": act.due_date.isoformat() if act.due_date else None,
                    "is_completed": act.is_completed,
                    "description": act.description,
                    "result": act.result,
                    "lead_id": act.lead_id,
                }
                if act.lead:
                    d["lead_name"] = f"{act.lead.first_name} {act.lead.last_name}"
                    if act.lead.company_name:
                        d["lead_name"] += f" ({act.lead.company_name})"

                data.append(d)

            self.timeline_page.load_data(data)

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="ActivityModule",
                function="_load_data",
                parent_widget=self,
            )

    def _show_add_form(self):
        form = ActivityFormPage()
        self._populate_leads(form)
        form.saved.connect(self._save_activity)
        form.cancelled.connect(self._back_to_timeline)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, act_id: int):
        try:
            # Fetch activity dict logic logic duplicated above, best to use service if available.
            # Re-query
            from database.models.crm import Activity

            act = self.session.query(Activity).get(act_id)
            if act:
                d = {
                    "id": act.id,
                    "subject": act.subject,
                    "activity_type_name": act.activity_type.name,
                    "due_date": act.due_date.isoformat(),
                    "is_completed": act.is_completed,
                    "completed_at": act.completed_at,
                    "description": act.description,
                    "result": act.result,
                    "lead_id": act.lead_id,
                }
                form = ActivityFormPage(d)
                self._populate_leads(form)
                form.saved.connect(self._save_activity)
                form.cancelled.connect(self._back_to_timeline)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="ActivityModule",
                function="_show_edit_form",
                parent_widget=self,
            )

    def _populate_leads(self, form):
        try:
            # Reusing logic from OpportunityModule
            leads = self.service.list_leads()
            form.combo_lead.clear()
            form.combo_lead.addItem("İlişkili Aday/Müşteri Yok", None)
            for lead in leads:
                name = f"{lead.first_name} {lead.last_name}"
                if lead.company_name:
                    name += f" ({lead.company_name})"
                form.combo_lead.addItem(name, lead.id)

            if form.data.get("lead_id"):
                idx = form.combo_lead.findData(form.data.get("lead_id"))
                if idx >= 0:
                    form.combo_lead.setCurrentIndex(idx)
        except Exception as e:
            ErrorHandler.log_error(e, "ActivityModule._populate_leads")

    def _save_activity(self, data: dict):
        try:
            act_id = data.pop("id", None)

            # Map enum name back to Enum object?
            # Service log_activity expects type to be Enum or string?
            # Model definition says Enum(ActivityType).
            # If we use log_activity from service, it probably handles creation.
            # But we are doing partial manual work here.

            # Let's map it safe.
            if isinstance(data["activity_type"], str):
                data["activity_type"] = ActivityType[data["activity_type"]]

            if act_id:
                # Update
                # Using session directly as service might lack general update
                from database.models.crm import Activity

                act = self.session.query(Activity).get(act_id)
                if act:
                    act.subject = data["subject"]
                    act.activity_type = data["activity_type"]
                    act.due_date = data["due_date"]
                    act.is_completed = data["is_completed"]
                    act.description = data["description"]
                    act.result = data["result"]
                    act.lead_id = data["lead_id"]

                    if act.is_completed and not act.completed_at:
                        from datetime import datetime

                        act.completed_at = datetime.now()

                    self.session.commit()
                    QMessageBox.information(self, "Başarılı", "Aktivite güncellendi!")
            else:
                # Create
                # Service log_activity params: lead_id, type, summary (subject), description
                # Our form has more fields (due_date, result).

                # Better to use Model direct creation to support all fields or update service.
                # For now model direct creation.
                from database.models.crm import Activity

                new_act = Activity(
                    subject=data["subject"],
                    activity_type=data["activity_type"],
                    due_date=data["due_date"],
                    is_completed=data["is_completed"],
                    description=data["description"],
                    result=data["result"],
                    lead_id=data["lead_id"],
                )
                if new_act.is_completed:
                    from datetime import datetime

                    new_act.completed_at = datetime.now()

                self.session.add(new_act)
                self.session.commit()
                QMessageBox.information(self, "Başarılı", "Aktivite oluşturuldu!")

            self._back_to_timeline()
            self._load_data()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="ActivityModule",
                function="_save_activity",
                parent_widget=self,
            )

    def _back_to_timeline(self):
        current = self.stack.currentWidget()
        if current != self.timeline_page:
            self.stack.setCurrentWidget(self.timeline_page)
            self.stack.removeWidget(current)
            current.deleteLater()
