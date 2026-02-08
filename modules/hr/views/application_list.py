from ui.components import BaseListPage, ColumnConfig
from database.base import SessionLocal
from database.models.hr import JobApplication, JobPosting
from sqlalchemy.orm import joinedload


class ApplicationListPage(BaseListPage):
    """
    Başvurular Liste Sayfası
    """

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("id", "ID", width=50),
            ColumnConfig("code", "Başvuru No", width=120),
            ColumnConfig("candidate", "Aday", width=180),
            ColumnConfig("posting_title", "İlgili İlan", width=180),
            ColumnConfig("status", "Durum", width=100),
            ColumnConfig("applied_at", "Başvuru Tarihi", width=120),
            ColumnConfig("rating", "Puan", width=80),
        ]

        super().__init__(
            title="Aday Başvuruları",
            icon="ph.users-three",
            table_id="applications_table",
            columns=columns,
            parent=parent,
        )
        self.refresh_requested.connect(self.load_data)
        self.load_data()

    def load_data(self):
        """Verileri yükle"""
        db = SessionLocal()
        try:
            apps = (
                db.query(JobApplication)
                .options(joinedload(JobApplication.posting))
                .order_by(JobApplication.applied_at.desc())
                .all()
            )

            self.clear_table()
            self.set_row_count(len(apps))

            for i, app in enumerate(apps):
                self.table.set_text(i, 0, str(app.id))
                self.table.set_text(i, 1, app.code)
                self.table.set_text(i, 2, f"{app.first_name} {app.last_name}")
                self.table.set_text(i, 3, app.posting.title if app.posting else "-")
                self.table.set_status(i, 4, app.status.value, app.status.value)
                self.table.set_text(i, 5, app.applied_at.strftime("%d.%m.%Y %H:%M"))
                self.table.set_text(i, 6, "★" * app.rating if app.rating else "-")

            self.update_count(len(apps))
        finally:
            db.close()
