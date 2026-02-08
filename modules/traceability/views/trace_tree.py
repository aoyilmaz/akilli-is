"""
Akıllı İş - İzlenebilirlik Ağacı (Genealogy) Dialog
"""

from typing import List, Dict, Any
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QTreeWidget,
    QTreeWidgetItem,
    QTabWidget,
    QWidget,
    QLabel,
    QPushButton,
    QFrame,
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon

from database.base import get_session
from modules.traceability.services.trace_engine import TraceEngine


class TraceDialog(QDialog):
    """
    Lot hiyerarşisini (Geriye/İleriye İzleme) gösteren diyalog penceresi.
    """

    def __init__(self, lot_id: int, parent=None):
        super().__init__(parent)
        self.lot_id = lot_id
        self.setWindowTitle("Lot İzlenebilirlik Analizi")
        self.resize(900, 700)

        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Başlık ve Bilgi Paneli
        info_frame = QFrame()
        info_frame.setFrameShape(QFrame.Shape.StyledPanel)
        info_frame.setStyleSheet("background-color: #f8f9fa; border-radius: 8px;")
        info_layout = QVBoxLayout(info_frame)

        self.lbl_lot_no = QLabel("Yükleniyor...")
        self.lbl_lot_no.setStyleSheet(
            "font-size: 18px; font-weight: bold; color: #2c3e50;"
        )
        info_layout.addWidget(self.lbl_lot_no)

        self.lbl_product = QLabel("-")
        self.lbl_product.setStyleSheet("font-size: 14px; color: #7f8c8d;")
        info_layout.addWidget(self.lbl_product)

        layout.addWidget(info_frame)

        # Sekmeler
        self.tabs = QTabWidget()
        self.tabs.setStyleSheet(
            "QTabBar::tab { height: 40px; width: 250px; font-size: 13px; }"
        )

        # Geriye İzleme Sekmesi
        self.tab_backward = QWidget()
        back_layout = QVBoxLayout(self.tab_backward)
        self.tree_backward = QTreeWidget()
        self.tree_backward.setHeaderLabels(
            ["Lot / Parti No", "Ürün Adı", "Kullanılan Mik."]
        )
        self.tree_backward.setColumnWidth(0, 250)
        self.tree_backward.setColumnWidth(1, 350)
        back_layout.addWidget(self.tree_backward)
        self.tabs.addTab(self.tab_backward, "Geriye İzleme (Hammadde/Kaynak)")

        # İleriye İzleme Sekmesi
        self.tab_forward = QWidget()
        fwd_layout = QVBoxLayout(self.tab_forward)
        self.tree_forward = QTreeWidget()
        self.tree_forward.setHeaderLabels(
            ["Lot / Parti No", "Ürün Adı", "Kullanılan Mik."]
        )
        self.tree_forward.setColumnWidth(0, 250)
        self.tree_forward.setColumnWidth(1, 350)
        fwd_layout.addWidget(self.tree_forward)
        self.tabs.addTab(self.tab_forward, "İleriye İzleme (Mamul/Hedef)")

        layout.addWidget(self.tabs)

        # Alt Butonlar
        btn_layout = QVBoxLayout()
        btn_close = QPushButton("Kapat")
        btn_close.setFixedSize(120, 36)
        btn_close.clicked.connect(self.accept)
        layout.addWidget(btn_close, alignment=Qt.AlignmentFlag.AlignRight)

    def load_data(self):
        """Verileri yükle ve ağaçları doldur"""
        db = get_session()
        try:
            engine = TraceEngine(db)

            # Geriye İzleme (Backward Trace)
            back_data = engine.trace_backward(self.lot_id)
            if back_data:
                self.lbl_lot_no.setText(
                    f"Lot Numarası: {back_data.get('lot_number', '-')}"
                )
                self.lbl_product.setText(f"Ürün: {back_data.get('product_name', '-')}")

                self.tree_backward.clear()
                self._populate_tree(
                    self.tree_backward.invisibleRootItem(),
                    back_data.get("components", []),
                    "components",
                )
                self.tree_backward.expandAll()

            # İleriye İzleme (Forward Trace)
            fwd_data = engine.trace_forward(self.lot_id)
            if fwd_data:
                self.tree_forward.clear()
                self._populate_tree(
                    self.tree_forward.invisibleRootItem(),
                    fwd_data.get("usages", []),
                    "usages",
                )
                self.tree_forward.expandAll()

        except Exception as e:
            print(f"Trace data error: {e}")
        finally:
            db.close()

    def _populate_tree(
        self, parent_item: QTreeWidgetItem, items: List[Dict[str, Any]], sub_key: str
    ):
        """Recursive ağaç doldurma"""
        for item_data in items:
            tree_item = QTreeWidgetItem(parent_item)
            tree_item.setText(0, item_data.get("lot_number", "-"))
            tree_item.setText(1, item_data.get("product_name", "-"))
            tree_item.setText(2, f"{item_data.get('quantity_used', 0):.3f}")

            # Alt seviyeleri işle
            sub_trace = item_data.get("sub_trace", {})
            sub_items = sub_trace.get(sub_key, [])
            if sub_items:
                self._populate_tree(tree_item, sub_items, sub_key)
