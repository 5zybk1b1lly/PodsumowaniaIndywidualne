from PySide6 import QtCore, QtWidgets, QtGui
import pandas as pd
import threading
import time

from src.config.colors import (
    SUCCESS_COLOR, ERROR_COLOR,
    SECONDARY_COLOR, ACCENT_COLOR
)
from src.config.settings import (
    DEFAULT_EMAIL, DEFAULT_SMTP_SERVER, DEFAULT_SMTP_PORT,
    DEFAULT_IMAP_SERVER, DEFAULT_IMAP_PORT, DEFAULT_PASSWORD,
    WINDOW_WIDTH, WINDOW_HEIGHT, WINDOW_MIN_WIDTH, WINDOW_MIN_HEIGHT,
    HEADER_TO_METRIC, BATCH_DELAY, EMAIL_DELAY
)
from src.utils.date_utils import get_week_end_date, parse_report_date, get_month_name
from src.utils.excel_utils import get_header_and_format_from_excel
from src.utils.data_utils import filter_empty_values
from src.email_service.email_service import EmailService


class FormatSelectorDialog(QtWidgets.QDialog):
    """Qt dialog for choosing formats and decimal places per column."""

    FORMAT_OPTIONS = ["Auto", "Waluta (zł)", "Procent (%)", "Liczba"]
    FORMAT_MAPPING = {
        "Auto": "",
        "Waluta (zł)": "zł",
        "Procent (%)": "%",
        "Liczba": "number",
    }

    def __init__(self, parent, columns, formats_cache=None):
        super().__init__(parent)
        # set icon if available
        try:
            icon = QtGui.QIcon("salesup.png")
            self.setWindowIcon(icon)
        except Exception:
            pass
        self.setWindowTitle("Wybierz formaty dla kolumn")
        self.resize(750, 450)
        self.columns = columns
        self.formats_cache = formats_cache or {}
        self.result = None

        self._init_ui()
        self.center(parent)

    def center(self, parent):
        if parent:
            geo = parent.geometry()
            self.move(geo.center() - self.rect().center())

    def _init_ui(self):
        layout = QtWidgets.QVBoxLayout(self)
        # header
        lbl = QtWidgets.QLabel("📊 Wybierz format i liczbę miejsc dla każdej kolumny")
        font = lbl.font()
        font.setBold(True)
        lbl.setFont(font)
        layout.addWidget(lbl)

        scroll = QtWidgets.QScrollArea()
        scroll.setWidgetResizable(True)
        inner = QtWidgets.QWidget()
        form = QtWidgets.QFormLayout(inner)
        self.format_widgets = {}
        self.decimal_widgets = {}

        for col in self.columns:
            row_widget = QtWidgets.QWidget()
            row_layout = QtWidgets.QHBoxLayout(row_widget)
            lbl_col = QtWidgets.QLabel(col)
            lbl_col.setMinimumWidth(150)
            row_layout.addWidget(lbl_col)

            combo = QtWidgets.QComboBox()
            combo.addItems(self.FORMAT_OPTIONS)
            # cache
            cache = self.formats_cache.get(col, {})
            fmt_val = cache.get('format', '')
            for name, val in self.FORMAT_MAPPING.items():
                if val == fmt_val:
                    combo.setCurrentText(name)
                    break
            row_layout.addWidget(combo)
            self.format_widgets[col] = combo

            spin = QtWidgets.QSpinBox()
            spin.setRange(0, 5)
            spin.setValue(cache.get('decimal_places', 0))
            row_layout.addWidget(spin)
            self.decimal_widgets[col] = spin

            form.addRow(row_widget)
        scroll.setWidget(inner)
        layout.addWidget(scroll)

        btn_layout = QtWidgets.QHBoxLayout()
        ok = QtWidgets.QPushButton("✓ OK")
        ok.clicked.connect(self.accept)
        err = QtWidgets.QPushButton("✗ Anuluj")
        err.clicked.connect(self.reject)
        btn_layout.addStretch()
        btn_layout.addWidget(ok)
        btn_layout.addWidget(err)
        layout.addLayout(btn_layout)

    def accept(self):
        self.result = {}
        for col, combo in self.format_widgets.items():
            sel = combo.currentText()
            self.result[col] = {
                'format': self.FORMAT_MAPPING.get(sel, ""),
                'decimal_places': self.decimal_widgets[col].value(),
            }
        super().accept()

    def show(self):
        super().exec()
        return self.result


class ReportGeneratorWindow(QtWidgets.QMainWindow):
    status_signal = QtCore.Signal(str, str)  # text, color

    message_signal = QtCore.Signal(str, str, str)  # kind, title, message

    def __init__(self):
        super().__init__()
        # optionally icon
        try:
            icon = QtGui.QIcon("salesup.png")
            self.setWindowIcon(icon)
        except Exception:
            pass
        self.setWindowTitle("Generator i wysyłka raportów SalesUp")
        self.resize(int(WINDOW_WIDTH), int(WINDOW_HEIGHT))
        self.setMinimumSize(int(WINDOW_MIN_WIDTH), int(WINDOW_MIN_HEIGHT))
        self.header_to_metric = HEADER_TO_METRIC.copy()
        self.header_to_format = {}
        self.column_formats_cache = {}
        self._stop_requested = False
        self._init_ui()
        self.status_signal.connect(self._update_status)
        self.message_signal.connect(self._show_message)

    def closeEvent(self, event):
        # Prevent worker thread from updating UI after window is closed
        self._stop_requested = True
        return super().closeEvent(event)

    def _show_message(self, kind: str, title: str, message: str):
        """Show message box from the GUI thread."""
        if kind == "error":
            QtWidgets.QMessageBox.critical(self, title, message)
        elif kind == "warning":
            QtWidgets.QMessageBox.warning(self, title, message)
        else:
            QtWidgets.QMessageBox.information(self, title, message)

    def _init_ui(self):
        central = QtWidgets.QWidget()
        self.setCentralWidget(central)
        main_layout = QtWidgets.QVBoxLayout(central)

        header = QtWidgets.QLabel("📧 Generator Raportów")
        header.setAlignment(QtCore.Qt.AlignCenter)
        font = header.font()
        font.setPointSize(20)
        font.setBold(True)
        header.setFont(font)
        main_layout.addWidget(header)

        form_scroll = QtWidgets.QScrollArea()
        form_scroll.setWidgetResizable(True)
        form_container = QtWidgets.QWidget()
        self.form_layout = QtWidgets.QFormLayout(form_container)
        form_scroll.setWidget(form_container)
        main_layout.addWidget(form_scroll)

        # fields
        self.entry_plik = QtWidgets.QLineEdit()
        btn_plik = QtWidgets.QPushButton("Wybierz...")
        btn_plik.clicked.connect(self._wybierz_plik)
        h = QtWidgets.QHBoxLayout()
        h.addWidget(self.entry_plik)
        h.addWidget(btn_plik)
        self.form_layout.addRow("📁 Plik Excel:", h)

        self.entry_tydzien = QtWidgets.QLineEdit()
        self.form_layout.addRow("📅 Numer tygodnia:", self.entry_tydzien)

        self.entry_report_date = QtWidgets.QLineEdit()
        btn_week = QtWidgets.QPushButton("Ustaw z tygodnia")
        btn_week.clicked.connect(self._ustaw_date_z_tygodnia)
        h2 = QtWidgets.QHBoxLayout()
        h2.addWidget(self.entry_report_date)
        h2.addWidget(btn_week)
        self.form_layout.addRow("🗓️ Data końcowa raportu:", h2)

        self.text_pre = QtWidgets.QTextEdit()
        self.form_layout.addRow("✏️ Tekst przed tabelą:", self.text_pre)
        self.text_post = QtWidgets.QTextEdit()
        self.form_layout.addRow("✏️ Tekst po tabeli:", self.text_post)

        # SMTP/IMAP blocks
        self.entry_email = QtWidgets.QLineEdit(DEFAULT_EMAIL)
        self.entry_smtp = QtWidgets.QLineEdit(DEFAULT_SMTP_SERVER)
        self.entry_port = QtWidgets.QLineEdit(str(DEFAULT_SMTP_PORT))
        self.entry_login = QtWidgets.QLineEdit(DEFAULT_EMAIL)
        self.entry_haslo = QtWidgets.QLineEdit(DEFAULT_PASSWORD)
        self.entry_haslo.setEchoMode(QtWidgets.QLineEdit.Password)

        self.form_layout.addRow("E-mail nadawcy:", self.entry_email)
        self.form_layout.addRow("Serwer SMTP:", self.entry_smtp)
        self.form_layout.addRow("Port SMTP:", self.entry_port)
        self.form_layout.addRow("Login SMTP:", self.entry_login)
        self.form_layout.addRow("Hasło SMTP:", self.entry_haslo)

        self.entry_imap = QtWidgets.QLineEdit(DEFAULT_IMAP_SERVER)
        self.entry_imap_port = QtWidgets.QLineEdit(str(DEFAULT_IMAP_PORT))
        self.form_layout.addRow("Serwer IMAP:", self.entry_imap)
        self.form_layout.addRow("Port IMAP:", self.entry_imap_port)

        self.btn_generate = QtWidgets.QPushButton("🚀 Generuj i wyślij raporty")
        self.btn_generate.clicked.connect(self._generuj_i_wyslij)
        main_layout.addWidget(self.btn_generate)

        self.status_label = QtWidgets.QLabel("Gotowy do wysyłania")
        main_layout.addWidget(self.status_label)

    def _update_status(self, txt, color):
        self.status_label.setText(txt)
        self.status_label.setStyleSheet(f"color:{color}")

    def _wybierz_plik(self):
        fn, _ = QtWidgets.QFileDialog.getOpenFileName(self, "Wybierz plik Excel", filter="Excel files (*.xlsx)")
        if fn:
            self.entry_plik.setText(fn)
            try:
                hdr, fmt = get_header_and_format_from_excel(fn)
                dlg = FormatSelectorDialog(self, list(hdr.keys()), self.column_formats_cache)
                sel = dlg.show()
                if sel is None:
                    self.entry_plik.clear()
                    self.status_signal.emit("Wybór pliku anulowany", ACCENT_COLOR)
                    return
                self.header_to_metric = hdr
                self.header_to_format = sel
                self.column_formats_cache.update(sel)
                cnt = len(self.column_formats_cache)
                self.status_signal.emit(f"Plik: {fn.split('/')[-1]} (formaty ustawione - cache: {cnt})", SUCCESS_COLOR)
            except Exception as e:
                QtWidgets.QMessageBox.critical(self, "Błąd", f"Nie można odczytać nagłówków:\n{e}")
                self.header_to_metric = HEADER_TO_METRIC.copy()
                self.header_to_format = {}
                self.status_signal.emit("Używane domyślne nagłówki", ACCENT_COLOR)

    def _ustaw_date_z_tygodnia(self):
        tyg = self.entry_tydzien.text().strip()
        if not tyg:
            QtWidgets.QMessageBox.critical(self, "Błąd", "Podaj numer tygodnia")
            return
        try:
            date = get_week_end_date(tyg)
            self.entry_report_date.setText(date.strftime("%d.%m.%Y"))
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", f"Nie można obliczyć daty:\n{e}")

    def _generuj_i_wyslij(self):
        # Gather and validate UI input in main thread (Qt objects must not be accessed from worker thread)
        plik = self.entry_plik.text().strip()
        tydzien = self.entry_tydzien.text().strip()
        email_nad = self.entry_email.text().strip()
        haslo = self.entry_haslo.text().strip()
        smtp = self.entry_smtp.text().strip()
        port = self.entry_port.text().strip()
        login = self.entry_login.text().strip()
        imap = self.entry_imap.text().strip()
        imap_port = self.entry_imap_port.text().strip()
        pre = self.text_pre.toPlainText().strip() or None
        post = self.text_post.toPlainText().strip() or None

        if not plik:
            QtWidgets.QMessageBox.critical(self, "Błąd", "Wybierz plik Excel!")
            return
        for field, name in [
            (email_nad, "E-mail"),
            (haslo, "Hasło"),
            (smtp, "SMTP"),
            (port, "Port"),
            (login, "Login"),
            (imap, "IMAP"),
            (imap_port, "Port IMAP"),
        ]:
            if not field:
                QtWidgets.QMessageBox.critical(self, "Błąd", "Wypełnij wszystkie pola logowania SMTP i IMAP!")
                return
        try:
            smtp_port = int(port)
            imapp = int(imap_port)
        except ValueError:
            QtWidgets.QMessageBox.critical(self, "Błąd", "Port musi być liczbą")
            return
        try:
            report_date = parse_report_date(self.entry_report_date.text().strip(), tydzien)
        except Exception as e:
            QtWidgets.QMessageBox.critical(self, "Błąd", f"Nieprawidłowa data końcowa:\n{e}")
            return

        thread = threading.Thread(
            target=self._worker,
            args=(plik, tydzien, email_nad, haslo, smtp, smtp_port, login, imap, imapp, report_date, pre, post),
            daemon=True,
        )
        thread.start()

    def _worker(self, plik, tydzien, email_nad, haslo, smtp, smtp_port, login, imap, imapp, report_date, pre, post):
        # disable button (via main thread)
        QtCore.QMetaObject.invokeMethod(self.btn_generate, "setEnabled", QtCore.Qt.QueuedConnection, QtCore.Q_ARG(bool, False))
        self.status_signal.emit("Przetwarzanie...", ACCENT_COLOR)

        try:
            try:
                df = pd.read_excel(plik)
            except Exception as e:
                self.message_signal.emit("error", "Błąd", f"Nie można otworzyć pliku:\n{e}")
                return

            if 'PROMOTOR' not in df.columns or 'EMAIL' not in df.columns:
                self.message_signal.emit("error", "Błąd", "Brak kolumn 'PROMOTOR' lub 'EMAIL' w pliku.")
                return

            email_service = EmailService(smtp, smtp_port, imap, imapp, login, haslo)
            email_service.connect_smtp()
            email_service.connect_imap()

            sukcesy = 0
            bledy = 0
            total = len(df)
            for index, row in df.iterrows():
                if getattr(self, "_stop_requested", False):
                    break
                self.status_signal.emit(f"Wysyłanie {index+1}/{total}...", ACCENT_COLOR)
                promotor = row['PROMOTOR']
                email = row['EMAIL']
                ph_email = row.get('EMAIL PH')
                if pd.isna(ph_email):
                    ph_email = None

                # Do not include internal columns in the report table
                skip_columns = {"PRZEDSTAWICIEL HANDLOWY", "EMAIL PH"}
                report_data = {
                    self.header_to_metric[col]: row[col]
                    for col in self.header_to_metric
                    if col in df.columns and col not in skip_columns
                }
                report_data = filter_empty_values(report_data)
                sent = email_service.send_report_email(
                    email_nad, email, promotor, tydzien,
                    report_data, report_date,
                    format_data=self.header_to_format,
                    pre_table_text=pre, post_table_text=post,
                    cc_email=ph_email
                )
                if sent:
                    sukcesy += 1
                else:
                    bledy += 1
                if index < total - 1:
                    time.sleep(EMAIL_DELAY)
            email_service.disconnect()

            if bledy == 0:
                self.message_signal.emit("info", "Sukces!", f"Wysłano: {sukcesy} maili")
                self.status_signal.emit(f"✓ Sukces! {sukcesy} maili", SUCCESS_COLOR)
            else:
                self.message_signal.emit("warning", "Wynik", f"Wysłano: {sukcesy} maili\nBłędy: {bledy}")
                self.status_signal.emit("⚠ Ukończono z błędami", ERROR_COLOR)
        except Exception as e:
            self.message_signal.emit("error", "Błąd", f"Nieoczekiwany błąd:\n{e}")
            self.status_signal.emit("Błąd podczas przetwarzania", ERROR_COLOR)
        finally:
            QtCore.QMetaObject.invokeMethod(
                self.btn_generate,
                "setEnabled",
                QtCore.Qt.QueuedConnection,
                QtCore.Q_ARG(bool, True),
            )
