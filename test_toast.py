import sys
import os

# Proje dizinini path'e ekle
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QVBoxLayout, QWidget
from ui.components.toast import show_toast


def test():
    app = QApplication(sys.argv)

    window = QMainWindow()
    window.setWindowTitle("Toast Test")
    window.setFixedSize(400, 300)

    central = QWidget()
    window.setCentralWidget(central)
    layout = QVBoxLayout(central)

    btn_info = QPushButton("Bilgi Bildirimi (INFO)")
    btn_info.clicked.connect(lambda: show_toast("Bu bir bilgi mesajıdır.", "INFO"))
    layout.addWidget(btn_info)

    btn_success = QPushButton("Başarı Bildirimi (SUCCESS)")
    btn_success.clicked.connect(
        lambda: show_toast("İşlem başarıyla tamamlandı!", "SUCCESS")
    )
    layout.addWidget(btn_success)

    btn_warning = QPushButton("Uyarı Bildirimi (WARNING)")
    btn_warning.clicked.connect(
        lambda: show_toast("Dikkat, eksik veri var.", "WARNING")
    )
    layout.addWidget(btn_warning)

    btn_error = QPushButton("Hata Bildirimi (ERROR)")
    btn_error.clicked.connect(lambda: show_toast("Bir hata oluştu!", "ERROR"))
    layout.addWidget(btn_error)

    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    test()
