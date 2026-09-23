import sys
from pathlib import Path
from PySide6.QtWidgets import QApplication
from ui.widget import MedusaWidget


def main():
    print(f'MEDUSA 0.4.2 — {Path(__file__).resolve().parent}', flush=True)
    app = QApplication(sys.argv)
    app.setApplicationName('MEDUSA')
    app.setOrganizationName('MEDUSA')
    app.setStyle('Fusion')
    window = MedusaWidget()
    window.show()
    sys.exit(app.exec())


if __name__ == '__main__':
    main()
