"""
Akıllı İş - Hesap Planı Ağaç Görünümü
"""

from PyQt6.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QPushButton,
    QLineEdit,
    QLabel,
    QFrame,
    QHeaderView,
    QMenu,
)
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QAction

from config.styles import (
    BG_SECONDARY, BORDER, TEXT_PRIMARY, TEXT_MUTED, ACCENT,
    INPUT_BG, INPUT_BORDER, get_tree_style,
)
from database.models.accounting import Account, AccountType


class AccountTreeWidget(QWidget):
    """Hiyerarşik hesap planı ağacı"""

    account_selected = pyqtSignal(int)  # account_id
    account_double_clicked = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.accounts = []
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Arama
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Hesap ara...")
        self.search_input.textChanged.connect(self._filter_tree)
        self.search_input.setStyleSheet(
            f"""
            QLineEdit {{
                background-color: {INPUT_BG};
                border: 1px solid {INPUT_BORDER};
                border-radius: 4px;
                padding: 8px 12px;
                color: {TEXT_PRIMARY};
            }}
            QLineEdit:focus {{
                border: 1px solid {ACCENT};
            }}
        """
        )
        search_layout.addWidget(self.search_input)
        layout.addLayout(search_layout)

        # Ağaç
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Kod", "Hesap Adı", "Tür"])
        self.tree.setColumnWidth(0, 100)
        self.tree.setColumnWidth(1, 300)
        self.tree.setColumnWidth(2, 80)

        header = self.tree.header()
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.Stretch)

        self.tree.setAlternatingRowColors(True)
        self.tree.setStyleSheet(get_tree_style())

        self.tree.itemClicked.connect(self._on_item_clicked)
        self.tree.itemDoubleClicked.connect(self._on_item_double_clicked)
        self.tree.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.tree.customContextMenuRequested.connect(self._show_context_menu)

        layout.addWidget(self.tree)

    def load_accounts(self, accounts: list):
        """Hesapları ağaca yükle"""
        self.accounts = accounts
        self.tree.clear()

        # Kod'a göre dict oluştur
        account_dict = {a.code: a for a in accounts}
        items_dict = {}

        # Önce ana grupları ekle
        for account in sorted(accounts, key=lambda a: a.code):
            parent_item = None

            # Parent bul
            if account.parent_id:
                parent = next((a for a in accounts if a.id == account.parent_id), None)
                if parent and parent.code in items_dict:
                    parent_item = items_dict[parent.code]

            item = QTreeWidgetItem()
            item.setText(0, account.code)
            item.setText(1, account.name)
            item.setText(2, self._get_type_label(account.account_type))
            item.setData(0, Qt.ItemDataRole.UserRole, account.id)

            # Renk
            color = self._get_type_color(account.account_type)
            item.setForeground(0, QColor(color))

            # Detay hesap mi?
            if account.is_detail:
                item.setForeground(1, QColor(TEXT_PRIMARY))
            else:
                item.setForeground(1, QColor(TEXT_MUTED))

            if parent_item:
                parent_item.addChild(item)
            else:
                self.tree.addTopLevelItem(item)

            items_dict[account.code] = item

        # Genişlet
        self.tree.expandAll()

    def _get_type_label(self, acc_type: AccountType) -> str:
        labels = {
            AccountType.ASSET: "Varlık",
            AccountType.LIABILITY: "Borç",
            AccountType.EQUITY: "Özkaynak",
            AccountType.REVENUE: "Gelir",
            AccountType.EXPENSE: "Gider",
            AccountType.COST: "Maliyet",
        }
        return labels.get(acc_type, "")

    def _get_type_color(self, acc_type: AccountType) -> str:
        colors = {
            AccountType.ASSET: "#10b981",
            AccountType.LIABILITY: "#ef4444",
            AccountType.EQUITY: "#8b5cf6",
            AccountType.REVENUE: "#3b82f6",
            AccountType.EXPENSE: "#f59e0b",
            AccountType.COST: "#f97316",
        }
        return colors.get(acc_type, "#94a3b8")

    def _filter_tree(self, text: str):
        """Ağacı filtrele"""
        text = text.lower()

        def filter_item(item):
            code = item.text(0).lower()
            name = item.text(1).lower()
            match = text in code or text in name

            # Çocukları kontrol et
            child_match = False
            for i in range(item.childCount()):
                if filter_item(item.child(i)):
                    child_match = True

            visible = match or child_match
            item.setHidden(not visible)
            return visible

        for i in range(self.tree.topLevelItemCount()):
            filter_item(self.tree.topLevelItem(i))

    def _on_item_clicked(self, item, column):
        account_id = item.data(0, Qt.ItemDataRole.UserRole)
        if account_id:
            self.account_selected.emit(account_id)

    def _on_item_double_clicked(self, item, column):
        account_id = item.data(0, Qt.ItemDataRole.UserRole)
        if account_id:
            self.account_double_clicked.emit(account_id)

    def _show_context_menu(self, position):
        item = self.tree.itemAt(position)
        if not item:
            return

        menu = QMenu()
        menu.setStyleSheet(
            f"""
            QMenu {{
                background-color: {BG_SECONDARY};
                border: 1px solid {BORDER};
                border-radius: 4px;
                padding: 4px;
            }}
            QMenu::item {{
                padding: 8px 20px;
                color: {TEXT_PRIMARY};
            }}
            QMenu::item:selected {{
                background-color: {BORDER};
            }}
        """
        )

        edit_action = QAction("✏️ Düzenle", self)
        edit_action.triggered.connect(
            lambda: self.account_double_clicked.emit(
                item.data(0, Qt.ItemDataRole.UserRole)
            )
        )
        menu.addAction(edit_action)

        ledger_action = QAction("📖 Büyük Defter", self)
        menu.addAction(ledger_action)

        menu.exec(self.tree.mapToGlobal(position))

    def get_selected_account_id(self) -> int:
        """Seçili hesap ID'si"""
        item = self.tree.currentItem()
        if item:
            return item.data(0, Qt.ItemDataRole.UserRole)
        return None
