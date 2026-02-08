from ui.components import BaseListPage, ColumnConfig
from database.base import SessionLocal
from database.models.hr import JobPosting, Department
from sqlalchemy.orm import joinedload


class JobPostingListPage(BaseListPage):
    """
    İş İlanları Liste Sayfası
    """

    def __init__(self, parent=None):
        columns = [
            ColumnConfig("id", "ID", width=50),
            ColumnConfig("code", "İlan Kodu", width=120),
            ColumnConfig("title", "Pozisyon Başlığı", width=200),
            ColumnConfig("department_name", "Departman", width=150),
            ColumnConfig("headcount", "Kontenjan", width=80),
            ColumnConfig("status", "Durum", width=100),
            ColumnConfig("deadline", "Son Başvuru", width=100),
        ]

        super().__init__(
            title="İş İlanları",
            icon="ph.briefcase",
            table_id="job_postings_table",
            columns=columns,
            parent=parent,
        )
        self.refresh_requested.connect(self.load_data)
        self.load_data()

    def load_data(self):
        """Verileri yükle"""
        db = SessionLocal()
        try:
            postings = (
                db.query(JobPosting).options(joinedload(JobPosting.department)).all()
            )

            self.clear_table()
            self.set_row_count(len(postings))

            for i, posting in enumerate(postings):
                self.table.set_text(i, 0, str(posting.id))
                self.table.set_text(i, 1, posting.code)
                self.table.set_text(i, 2, posting.title)
                self.table.set_text(
                    i, 3, posting.department.name if posting.department else "-"
                )
                self.table.set_text(i, 4, str(posting.headcount))
                self.table.set_status(i, 5, posting.status.value, posting.status.value)
                self.table.set_text(
                    i,
                    6,
                    posting.deadline.strftime("%d.%m.%Y") if posting.deadline else "-",
                )

            self.update_count(len(postings))
        finally:
            db.close()
