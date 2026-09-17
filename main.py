import sys
from pathlib import Path

from PySide6.QtWidgets import QApplication

from ui.widget import MedusaWidget


def main():
    app = QApplication(sys.argv)

    app.setApplicationName("MEDUSA")

    style_path = (
        Path(__file__).parent
        / "styles"
        / "medusa.qss"
    )

    if style_path.exists():
        with open(
            style_path,
            "r",
            encoding="utf-8"
        ) as file:
            app.setStyleSheet(
                file.read()
            )

    window = MedusaWidget()
    window.show()

    sys.exit(
        app.exec()
    )


if __name__ == "__main__":
    main()