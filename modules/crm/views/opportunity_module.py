from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from .opportunity_board import OpportunityBoard
from .opportunity_form import OpportunityFormPage
from modules.development import ErrorHandler
from database.base import get_session
from modules.crm.services import CRMService
from database.models.crm import Lead, OpportunityStage
from config.icons import ICONS


class OpportunityModule(QWidget):
    """Fırsat Yönetimi Modülü (Kanban + Form)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = get_session()
        self.service = CRMService(self.session)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # === Header - PageHeader kullanarak ===
        from ui.components.page_header import PageHeader

        self.header = PageHeader(
            title="Fırsat Yönetimi",
            icon=ICONS.MONEY,
            show_search=False,
            show_add=True,
            add_text="Yeni Fırsat",
            parent=self,
        )
        self.header.add_clicked.connect(self._show_add_form)
        self.header.refresh_clicked.connect(self._load_data)

        layout.addWidget(self.header)

        self.stack = QStackedWidget()

        # Kanban Panosu
        self.board_page = OpportunityBoard()
        self.board_page.add_clicked.connect(self._show_add_form)
        self.board_page.card_clicked.connect(self._show_edit_form)
        self.board_page.refresh_clicked.connect(self._load_data)

        self.stack.addWidget(self.board_page)
        layout.addWidget(self.stack)

    def showEvent(self, event):
        super().showEvent(event)
        self._load_data()

    def _load_data(self):
        try:
            # Fırsatları çek
            opportunities = self.service.list_opportunities()

            data = []
            for opp in opportunities:
                d = opp.to_dict()
                # Ekstra bilgiler
                if opp.lead:
                    d["lead_name"] = f"{opp.lead.first_name} {opp.lead.last_name}"
                elif opp.customer:
                    d["customer_name"] = opp.customer.name
                data.append(d)

            self.board_page.load_data(data)

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="OpportunityModule",
                function="_load_data",
                parent_widget=self,
            )

    def _show_add_form(self):
        form = OpportunityFormPage()
        self._populate_leads(form)
        form.saved.connect(self._save_opportunity)
        form.cancelled.connect(self._back_to_board)
        self.stack.addWidget(form)
        self.stack.setCurrentWidget(form)

    def _show_edit_form(self, opp_id: int):
        try:
            opp = self.service.get_opportunity(opp_id)
            if opp:
                d = opp.to_dict()
                if opp.stage:
                    d["stage_name"] = opp.stage.name  # Enum key (NEW, WON etc)

                form = OpportunityFormPage(d)
                self._populate_leads(form)
                form.saved.connect(self._save_opportunity)
                form.cancelled.connect(self._back_to_board)
                self.stack.addWidget(form)
                self.stack.setCurrentWidget(form)
        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="OpportunityModule",
                function="_show_edit_form",
                parent_widget=self,
            )

    def _populate_leads(self, form):
        """Formdaki lead combobox'ını doldur"""
        try:
            leads = self.service.list_leads()
            form.combo_lead.clear()
            form.combo_lead.addItem("İlişkili Aday/Müşteri Yok", None)
            for lead in leads:
                name = f"{lead.first_name} {lead.last_name}"
                if lead.company_name:
                    name += f" ({lead.company_name})"
                form.combo_lead.addItem(name, lead.id)

            # Seçili olanı ayarla
            if form.data.get("lead_id"):
                idx = form.combo_lead.findData(form.data.get("lead_id"))
                if idx >= 0:
                    form.combo_lead.setCurrentIndex(idx)

        except Exception as e:
            ErrorHandler.log_error(e, "OpportunityModule._populate_leads")

    def _save_opportunity(self, data: dict):
        try:
            opp_id = data.pop("id", None)

            if opp_id:
                self.service.update_opportunity_stage(opp_id, data["stage"])
                from database.models.crm import Opportunity

                opp = self.session.query(Opportunity).get(opp_id)
                if opp:
                    opp.name = data["name"]
                    opp.lead_id = data["lead_id"]
                    opp.expected_revenue = data["expected_revenue"]
                    opp.probability = data["probability"]
                    opp.closing_date = data["closing_date"]
                    opp.description = data["description"]
                    opp.next_step = data["next_step"]
                    if isinstance(data["stage"], str):
                        opp.stage = OpportunityStage[data["stage"]]

                    self.session.commit()
                    QMessageBox.information(self, "Başarılı", "Fırsat güncellendi!")

            else:
                if isinstance(data["stage"], str):
                    data["stage"] = OpportunityStage[data["stage"]]

                self.service.create_opportunity(data)
                QMessageBox.information(self, "Başarılı", "Fırsat oluşturuldu!")

            self._back_to_board()
            self._load_data()

        except Exception as e:
            ErrorHandler.handle_error(
                e,
                module="crm",
                screen="OpportunityModule",
                function="_save_opportunity",
                parent_widget=self,
            )

    def _back_to_board(self):
        current = self.stack.currentWidget()
        if current != self.board_page:
            self.stack.setCurrentWidget(self.board_page)
            self.stack.removeWidget(current)
            current.deleteLater()
