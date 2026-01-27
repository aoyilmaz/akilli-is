from PyQt6.QtWidgets import QDoubleSpinBox, QLineEdit
from PyQt6.QtCore import QTimer


class CurrencyInput(QDoubleSpinBox):
    """
    Para birimi girişi için özelleştirilmiş SpinBox.
    - Suffix olarak para birimi simgesi (varsayılan: ₺)
    - Odaklanıldığında içeriği seçme
    - Binlik ayracı açık
    """

    def __init__(self, parent=None, currency_symbol="₺"):
        super().__init__(parent)
        self.setGroupSeparatorShown(True)
        self.setSuffix(f" {currency_symbol}")
        self.setDecimals(2)  # Varsayılan 2, gerekirse 4 yapılabilir
        self.setRange(0, 999999999)

        # Line edit event filter
        line_edit = self.findChild(QLineEdit)
        if line_edit:
            self._original_focus_in = line_edit.focusInEvent
            line_edit.focusInEvent = self._focus_in_handler

    def _focus_in_handler(self, event):
        """Odaklanma olayını yakala ve tümünü seç"""
        if self._original_focus_in:
            self._original_focus_in(event)

        # Qt'un varsayılan davranışını ezmek için timer kullan
        QTimer.singleShot(0, self.selectAll)


class NumericInput(QDoubleSpinBox):
    """
    Genel sayısal girişler için özelleştirilmiş SpinBox.
    - Odaklanıldığında içeriği seçme
    - Binlik ayracı açık (opsiyonel)
    """

    def __init__(self, parent=None, decimals=2, suffix=""):
        super().__init__(parent)
        self.setGroupSeparatorShown(True)
        if suffix:
            self.setSuffix(f" {suffix}")
        self.setDecimals(decimals)
        self.setRange(0, 999999999)

        # Line edit event filter
        line_edit = self.findChild(QLineEdit)
        if line_edit:
            self._original_focus_in = line_edit.focusInEvent
            line_edit.focusInEvent = self._focus_in_handler

    def _focus_in_handler(self, event):
        if self._original_focus_in:
            self._original_focus_in(event)
        QTimer.singleShot(0, self.selectAll)
