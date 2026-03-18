"""Application settings and constants"""

import os

# Email settings defaults (override via environment variables to avoid storing secrets in source control)
DEFAULT_EMAIL = os.getenv("SALESUP_EMAIL", "")
DEFAULT_SMTP_SERVER = os.getenv("SALESUP_SMTP_SERVER", "")
DEFAULT_SMTP_PORT = os.getenv("SALESUP_SMTP_PORT", "587")
DEFAULT_IMAP_SERVER = os.getenv("SALESUP_IMAP_SERVER", "")
DEFAULT_IMAP_PORT = os.getenv("SALESUP_IMAP_PORT", "143")
DEFAULT_PASSWORD = os.getenv("SALESUP_PASSWORD", "")

# Email configuration
BATCH_SIZE = 1  # Liczba maili na jedno połączenie
MAX_RETRIES = 5  # Maksymalnie 5 prób na maila
BATCH_DELAY = 15  # Opóźnienie między batchami (sekundy)
EMAIL_DELAY = 10  # Opóźnienie między mailami (sekundy)

# Header mapping
HEADER_TO_METRIC = {
    'Godziny': 'Ilość godzin',
    'Sprzedaż': 'Sprzedaż',
    'Wartość sztywna': 'Wartość sztywna',
    'Wartość AKC': 'Wartość AKC',
    '% 999': '% dziewiątek IMEI',
    'Realizacja godzin': 'Realizacja godzin',
    'Realizacja obrót': 'Realizacja obrót',
    'Realizacja akc': 'Realizacja akc',
    'Target godziny': 'Target godziny',
    'Target Obrót': 'Target Obrót',
    'Target akcesoria': 'Target akcesoria'
}

# IMAP settings
IMAP_DEFAULT_FOLDER = "SENT.PodsumowaniaIndywidualne"

# Application window settings
# Most window dimensions are integers to avoid type errors in GUI frameworks
WINDOW_WIDTH = 700
WINDOW_HEIGHT = 1000
WINDOW_MIN_WIDTH = 500
WINDOW_MIN_HEIGHT = 400
WINDOW_PADDING = "20"  # still a string for use in geometry calculations if needed
