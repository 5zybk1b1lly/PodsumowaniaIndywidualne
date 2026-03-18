"""Main entry point for the SalesUp Report Generator application"""

from PySide6 import QtWidgets
from src.config.credentials import load_credentials
from src.gui.gui_qt import LoginDialog, ReportGeneratorWindow


def main():
    """Main application entry point (Qt)"""
    app = QtWidgets.QApplication([])

    saved_creds = load_credentials()

    # If we have saved credentials, try to login silently first.
    dlg = LoginDialog(saved_creds)
    creds = dlg.exec_and_get_credentials()
    if not creds:
        return

    window = ReportGeneratorWindow(initial_credentials=creds)
    window.show()
    app.exec()


if __name__ == "__main__":
    main()
