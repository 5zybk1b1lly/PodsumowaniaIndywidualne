"""Main entry point for the SalesUp Report Generator application"""

from PySide6 import QtWidgets
from src.gui.gui_qt import ReportGeneratorWindow


def main():
    """Main application entry point (Qt)"""
    app = QtWidgets.QApplication([])
    window = ReportGeneratorWindow()
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
