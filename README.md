# SalesUp Report Generator

Aplikacja do automatycznego generowania i wysyłania spersonalizowanych raportów e-mail dla promotorów.

## Struktura projektu

```
├── main.py                          # Główny punkt wejścia aplikacji
├── requirements.txt                 # Zależności Python
├── README.md                        # Dokumentacja
├── salesup.png                      # Logo używane w GUI i mailach
└── src/                            # Moduły aplikacji
    ├── __init__.py
    ├── config/                     # Konfiguracja
    │   ├── __init__.py
    │   ├── colors.py               # Paleta kolorów (używana głównie w GUI)
    │   └── settings.py             # Ustawienia aplikacji
    ├── utils/                      # Funkcje narzędziowe
    │   ├── __init__.py
    │   ├── date_utils.py           # Funkcje do obsługi dat
    │   └── formatters.py           # Formatowanie wartości
    ├── email_service/              # Usługi e-mail
    │   ├── __init__.py
    │   └── email_service.py        # SMTP i IMAP operacje
    ├── templates/                  # Szablony raportów
    │   ├── __init__.py
    │   └── report_generator.py     # Generowanie HTML i tekstu
    └── gui/                        # Interfejs użytkownika
        ├── __init__.py
        └── gui_qt.py               # Qt/PySide6 GUI
```

## Główne moduły

### `config/colors.py`
Definiuje paletę kolorów używaną w interfejsie GUI.

### `config/settings.py`
Zawiera konfigurację aplikacji:
- Domyślne wartości dla SMTP/IMAP
- Mapowanie nagłówków na metryki
- Ustawienia okna aplikacji
- Parametry wysyłania (batch size, retries, opóźnienia)

### `utils/date_utils.py`
Funkcje do obsługi dat:
- `get_week_end_date()` - Oblicza koniec tygodnia
- `parse_report_date()` - Parsuje datę w formacie DD.MM.YYYY
- `get_month_name()` - Zwraca polską nazwę miesiąca

### `utils/formatters.py`
Formatowanie wartości:
- `format_number_value()` - Formatuje liczby z separatorami i jednostkami (zł, %)

### `email_service/email_service.py`
Klasa `EmailService` do zarządzania:
- Połączeniami SMTP i IMAP
- Wysyłaniem raportów
- Zapisywaniem wiadomości w folderach

### `templates/report_generator.py`
Generowanie raportów:
- `generuj_html_raport()` - Tworzenie HTML raportu
- `generuj_tekst_raport()` - Tworzenie tekstowej wersji

### `gui/gui_qt.py`
Nowoczesny interfejs oparty na PySide6/Qt, responsywny i profesjonalny. Pasek tytułu oraz wszystkie okna dialogowe korzystają z ikony `salesup.png`.

## Instalacja

1. Utwórz środowisko Python oraz zainstaluj wymagane pakiety:
```bash
pip install -r requirements.txt
```
(Pakiet `PySide6` dostarcza biblioteki Qt dla GUI.)

## Uruchomienie

```bash
python main.py
```

## Funkcjonalność

1. **Wybór pliku Excel** - Plik musi zawierać kolumny PROMOTOR i EMAIL
2. **Numer tygodnia** - Automatyczne obliczenie końca tygodnia (lub wpisanie ręczne)
3. **Generowanie raportów** - Tworzenie spersonalizowanych HTML i tekstowych raportów; raport HTML zawiera w nagłówku logo SalesUp w postaci osadzonego obrazu.

*Interfejs użytkownika przeniesiono z Tkintera na Qt (PySide6). Wszystkie pola, przyciski i okna są teraz natywnymi widgetami Qt, co zapewnia profesjonalny wygląd i responsywność na wszystkich platformach.*
4. **Wysyłanie e-mail** - Wysłanie do każdego promotora z automatycznymi ponawianiami
5. **Archiwizacja** - Zapisanie wysłanych wiadomości w folderze IMAP6. **Dostosowywanie tekstu** – w interfejsie dodano dwa pola umożliwiające wprowadzenie własnego
   tekstu pojawiającego się przed tabelą metryk oraz po niej. Formatowanie pozostaje takie jak w
   standardowym szablonie (klasa `intro-text`) – możesz wpisać zwykły tekst lub fragment HTML.
## Format pliku Excel

Plik Excel musi zawierać następujące kolumny:

| PROMOTOR | EMAIL | Godziny | Sprzedaż | ... |
|----------|-------|---------|----------|-----|
| Imię     | email@domain | liczba  | liczba | ... |

Obsługiwane metryki (mapowanie z nagłówków):
- Godziny → Ilość godzin
- Sprzedaż → Sprzedaż
- Wartość sztywna → Wartość sztywna
- Wartość AKC → Wartość AKC
- % 999 → % dziewiątek IMEI
- Realizacja godzin → Realizacja godzin
- Realizacja obrót → Realizacja obrót
- Realizacja akc → Realizacja akc
- Target godziny → Target godziny
- Target Obrót → Target Obrót
- Target akcesoria → Target akcesoria

## Konfiguracja poświadczeń (bezpiecznie)

Aby uniknąć przechowywania danych logowania w repozytorium, aplikacja pobiera wartości domyślne (w tym hasło) z zmiennych środowiskowych.

Dostępne zmienne środowiskowe:

- `SALESUP_EMAIL` – adres nadawcy (konto SMTP/IMAP)
- `SALESUP_PASSWORD` – hasło do konta SMTP/IMAP
- `SALESUP_SMTP_SERVER` – serwer SMTP
- `SALESUP_SMTP_PORT` – port SMTP (domyślnie `587`)
- `SALESUP_IMAP_SERVER` – serwer IMAP
- `SALESUP_IMAP_PORT` – port IMAP (domyślnie `143`)

**Uwaga:** aplikacja nie ładuje automatycznie plików `.env`. Aby korzystać z pliku `.env`, zainstaluj pakiet `python-dotenv` (np. `pip install python-dotenv`) i dodaj prostą logikę do `main.py` (lub uruchom skrypt z ustawionymi zmiennymi środowiskowymi).

Przykładowy plik `.env` (ten plik powinien być dodany do `.gitignore`):

```
SALESUP_EMAIL=twoj@adres.pl
SALESUP_PASSWORD=SuperTajneHaslo
SALESUP_SMTP_SERVER=smtp.example.com
SALESUP_SMTP_PORT=587
SALESUP_IMAP_SERVER=imap.example.com
SALESUP_IMAP_PORT=143
```

Jeśli zmienne środowiskowe nie są ustawione, pola w GUI będą puste i trzeba je wypełnić ręcznie.

## Formatowanie raportów

- Liczby ze złotówkami: format polski z separatorami (np. "1 234,56 zł")
- Procenty: konwertowane i formatowane z jednostką (np. "25,5 %")
- Kolory warunkowe w HTML:
  - Dziewiątki > 5%: czerwone tło
  - Realizacja: niebieskie tło
  - Target: żółte tło

## Uwagi

- Limit dziewiątek IMEI: 5% całkowitej sprzedaży
- Opóźnienia między wysyłkami (domyślnie 10s między mailami, 15s między batchami)
- Automatyczne ponowienia (maksymalnie 5 prób na email)
- Wiadomości zapisywane w folderze SENT.PodsumowaniaIndywidualne

## Autor

SalesUp Polska SA

## Licencja

© 2026 Wszystkie prawa zastrzeżone
