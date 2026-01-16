from PyQt6.QtWidgets import QWidget, QVBoxLayout, QStackedWidget, QMessageBox
from .opportunity_board import OpportunityBoard
from .opportunity_form import OpportunityFormPage
from modules.development import ErrorHandler
from database.base import get_session
from modules.crm.services import CRMService
from database.models.crm import Lead, OpportunityStage


class OpportunityModule(QWidget):
    """Fırsat Yönetimi Modülü (Kanban + Form)"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.session = get_session()
        self.service = CRMService(self.session)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
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

            # Lead isimlerini de eklememiz lazım (Join yapmadık serviste basic list var)
            # Service list_opportunities desc sırası ile Opportunity objeleri döner
            # KanbanCard için lead_name veya customer_name lazım.
            # Lazy loading loop'ta sorun olabilir ama MVP için yapalım.

            data = []
            for opp in opportunities:
                d = opp.to_dict()
                # Ekstra bilgiler
                if opp.lead:
                    d["lead_name"] = f"{opp.lead.first_name} {opp.lead.last_name}"
                elif opp.customer:
                    d["customer_name"] = opp.customer.name

                # to_dict status/stage value dönüyor, enum key değil.
                # OpportunityBoard value'yu key'e çeviriyor.
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
                # Stage enum name'i ekleyelim ki form doğru seçsin (form name bekliyor, data value dönüyor)
                # Model'de stage column Enum(OpportunityStage). to_dict -> self.stage.value ("Yeni")
                # Bizim Form findData(name) yapıyor, ama value ("Yeni") daha mantıklı user-facing için.
                # Dur, Form koduna bak:
                # idx = self.combo_stage.findData(stage_name) -> Data olarak Enum.name tutuyor.
                # Opportunity modelinde stage bir Enum objesi döner Python'da.
                # to_dict'te value alınıyor.

                # Form'a enum name lazım:
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

            # Enum Key -> Enum Value/Object conversion Service tarafından halledilmeli mi?
            # Service create_opportunity(data) yapar, data içinde "stage" string key mi olmalı yoksa enum objesi mi?
            # Service koduna bakmak lazım:
            # opp = Opportunity(**data)
            # SQLAlchemy Enum column, string key (veya enum objesi) kabul eder genelde ama
            # model tanımında enum class verdik. SQLAlchemy string name 'NEW' kabul eder genelde.
            # Biz formdan 'NEW' (name) gönderiyoruz (combo.currentData()).
            # Sorun yok gibi.

            if opp_id:
                self.service.update_opportunity_stage(opp_id, data["stage"])
                # Update metodumuz sadece stage update için mi?
                # Service'de update_opportunity genel metodu yok mu?
                # Servis koduna bakmıştım: list_opportunities, update_opportunity_stage var.
                # update_opportunity yok gibiydi. Kontrol etmem lazım.
                # Eğer yoksa eklemeliyim.

                # Geçici çözüm: Stage update ayrı, diğer fieldlar için generic update lazım.
                # Şimdilik basic SQL update yapalım session ile service methodu yoksa.

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
                    # Stage'i ayrıca set et (Enum conversion)
                    if isinstance(data["stage"], str):
                        opp.stage = OpportunityStage[data["stage"]]

                    self.session.commit()
                    QMessageBox.information(self, "Başarılı", "Fırsat güncellendi!")

            else:
                # Create: Service create_opportunity
                # data["stage"] string key 'NEW'.
                # Service: opp = Opportunity(**data) -> stage='NEW' str -> Enum mapping automatic in SQLA?
                # Genelde Enum(OpportunityStage) kullanıyorsak name string çalışır.

                # Ancak service kodunu hatırlıyorum, create_opportunity basic **data pass ediyordu.
                # Enum mapping hatası alabiliriz. Garanti olsun diye çevirelim.
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
