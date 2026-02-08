from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTabWidget, QLabel
from ui.components import PageHeader
from .job_posting_list import JobPostingListPage
from .application_list import ApplicationListPage
from .interview_page import InterviewPage


class RecruitmentModule(QWidget):
    """
    İşe Alım (Recruitment) Ana Modülü
    """

    def __init__(self):
        super().__init__()
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(20)

        # Başlık
        self.header = PageHeader(
            "İşe Alım Yönetimi",
            "ph.user-plus",
            "İş ilanları, başvurular ve mülakat süreçlerini yönetin.",
        )
        layout.addWidget(self.header)

        # Sekmeler
        self.tabs = QTabWidget()

        # 1. İş İlanları
        self.posting_page = JobPostingListPage()
        self.tabs.addTab(self.posting_page, "İş İlanları")

        # 2. Başvurular
        self.application_page = ApplicationListPage()
        self.tabs.addTab(self.application_page, "Başvurular")

        # 3. Mülakatlar
        self.interview_page = InterviewPage()
        self.tabs.addTab(self.interview_page, "Mülakat Takvimi")

        layout.addWidget(self.tabs)
