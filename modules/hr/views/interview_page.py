from ui.components import BaseListPage, ColumnConfig
from database.base import SessionLocal
from database.models.hr import Interview, JobApplication
from sqlalchemy.orm import joinedload


class InterviewPage(BaseListPage):
    """
    Mülakat Takvimi ve Liste Sayfası
    """

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("id", "ID", width=50),
            ColumnConfig("scheduled_at", "Tarih/Saat", width=150),
            ColumnConfig("candidate", "Aday", width=180),
            ColumnConfig("interviewer", "Mülakatçı", width=150),
            ColumnConfig("type", "Tip", width=100),
            ColumnConfig("status", "Durum", width=100),
            ColumnConfig("result", "Sonuç", width=100),
        ]

        super().__init__(
            title="Mülakat Takvimi",
            icon="ph.calendar-check",
            table_id="interviews_table",
            columns=columns,
            parent=parent,
        )
        self.refresh_requested.connect(self.load_data)
        self.load_data()

    def load_data(self):
        """Verileri yükle"""
        db = SessionLocal()
        try:
            interviews = (
                db.query(Interview)
                .options(
                    joinedload(Interview.application), joinedload(Interview.interviewer)
                )
                .order_by(Interview.scheduled_at.desc())
                .all()
            )

            self.clear_table()
            self.set_row_count(len(interviews))

            for i, interview in enumerate(interviews):
                app = interview.application
                intr = interview.interviewer

                self.table.set_text(i, 0, str(interview.id))
                self.table.set_text(
                    i, 1, interview.scheduled_at.strftime("%d.%m.%Y %H:%M")
                )
                self.table.set_text(
                    i, 2, f"{app.first_name} {app.last_name}" if app else "-"
                )
                self.table.set_text(i, 3, intr.full_name if intr else "-")
                self.table.set_text(i, 4, interview.interview_type or "-")
                self.table.set_status(i, 5, interview.status, interview.status)
                self.table.set_text(i, 6, interview.result or "Bekliyor")

            self.update_count(len(interviews))
        finally:
            db.close()
