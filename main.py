# main.py
import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication, QDialog, QMessageBox
from PySide6.QtCore import QTimer

from core.config import JAVA_DIR
from core.utils import ensure_java_organized, import_all_system_java, get_all_installed_java_versions, get_java_path_from_named_folder
from gui.main_window import KuLauncher
from gui.assets_check_dialog import AssetsCheckDialog
from dialogs.java_install_dialog import JavaInstallDialog

def setup_app_style(app):
    app.setStyle('Fusion')
    
    try:
        from PySide6.QtGui import QFontDatabase, QFont
        font_id = QFontDatabase.addApplicationFont(str(Path("assets/mine.ttf")))
        if font_id != -1:
            font_family = QFontDatabase.applicationFontFamilies(font_id)[0]
            app.setFont(QFont(font_family, 12))
    except:
        pass

    from PySide6.QtGui import QPalette, QColor
    from PySide6.QtCore import Qt
    palette = QPalette()
    palette.setColor(QPalette.Window, QColor(25, 25, 25))
    palette.setColor(QPalette.WindowText, Qt.white)
    palette.setColor(QPalette.Base, QColor(18, 18, 18))
    palette.setColor(QPalette.AlternateBase, QColor(30, 30, 30))
    palette.setColor(QPalette.Text, Qt.white)
    palette.setColor(QPalette.Button, QColor(35, 35, 35))
    palette.setColor(QPalette.ButtonText, Qt.white)
    palette.setColor(QPalette.BrightText, Qt.red)
    palette.setColor(QPalette.Link, Qt.white)
    palette.setColor(QPalette.Highlight, QColor(100, 100, 100))
    palette.setColor(QPalette.HighlightedText, Qt.white)
    app.setPalette(palette)

    app.setStyleSheet("""
        * {
            background-color: #2d2d2d;
            color: white;
            font-size: 14px;
        }
        QPushButton {
            background: #3d3d3d;
            border: 2px solid #444;
            border-radius: 8px;
            padding: 8px 16px;
        }
        QLineEdit, QComboBox {
            background: rgba(30, 30, 30, 180);
            border: 2px solid #444;
            border-radius: 6px;
            padding: 8px;
        }
        QProgressBar {
            border: 2px solid #444;
            border-radius: 5px;
            background: #3d3d3d;
        }
    """)

    return app

def check_java_in_named_folders():
    required_versions = [8, 17, 21]
    missing = []
    for v in required_versions:
        if not get_java_path_from_named_folder(v):
            missing.append(v)
    return missing

def ensure_all_java_installed():
    imported = import_all_system_java()
    missing = check_java_in_named_folders()
    if not missing:
        return True

    app = QApplication.instance() or QApplication(sys.argv)
    if not app:
        app = setup_app_style(app)

    dialog = JavaInstallDialog(None, missing, mandatory=True)
    dialog.exec()

    return len(check_java_in_named_folders()) == 0

def main():
    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    setup_app_style(app)

    JAVA_DIR.mkdir(parents=True, exist_ok=True)

    if not ensure_all_java_installed():
        QMessageBox.critical(None, "Ошибка", "Не удалось установить Java.")
        sys.exit(1)

    check_dialog = AssetsCheckDialog()
    if check_dialog.exec() == QDialog.Accepted:
        launcher = KuLauncher([])
        launcher.show()
    else:
        sys.exit(0)

    sys.exit(app.exec())

if __name__ == "__main__":
    main()