"""Date and time utility functions"""

from datetime import datetime, timedelta


def get_week_end_date(week_number):
    """Oblicza datę końca tygodnia (niedziela) dla danego numeru tygodnia bieżącego roku
    
    Args:
        week_number: Numer tygodnia w roku
        
    Returns:
        datetime: Data niedzieli na koniec tygodnia
    """
    try:
        # Pobierz bieżący rok
        current_year = datetime.now().year
        
        # Utwórz datę na początku roku
        jan_4 = datetime(current_year, 1, 4)
        
        # Znajdź poniedziałek dla tygodnia zawierającego 4 stycznia
        week_1_monday = jan_4 - timedelta(days=jan_4.weekday())
        
        # Dodaj tygodnie i otrzymaj poniedziałek danego tygodnia
        monday_of_week = week_1_monday + timedelta(weeks=int(week_number) - 1)
        
        # Niedziela to poniedziałek + 6 dni
        sunday_of_week = monday_of_week + timedelta(days=6)
        
        return sunday_of_week
    except Exception:
        return datetime.now()


def parse_report_date(date_str=None, tydzien=None):
    """Parsuje datę końcową raportu z pola GUI (format DD.MM.YYYY).
    Jeśli pole puste - zwraca koniec tygodnia dla podanego numeru tygodnia.
    
    Args:
        date_str: String daty w formacie DD.MM.YYYY
        tydzien: Numer tygodnia (fallback jeśli brak daty)
        
    Returns:
        datetime: Sparsowana data
        
    Raises:
        ValueError: Jeśli data ma nieprawidłowy format
    """
    if not date_str:
        # jeśli brak daty, użyj końca tygodnia
        try:
            return get_week_end_date(tydzien)
        except Exception:
            return datetime.now()
    
    try:
        return datetime.strptime(date_str, "%d.%m.%Y")
    except ValueError:
        raise ValueError("Podaj datę w formacie DD.MM.YYYY, np. 31.01.2026")


def get_month_name(date):
    """Zwraca polską nazwę miesiąca dla danej daty
    
    Args:
        date: datetime object
        
    Returns:
        str: Nazwa miesiąca po polsku
    """
    months = ["", "Styczeń", "Luty", "Marzec", "Kwiecień", "Maj", "Czerwiec",
              "Lipiec", "Sierpień", "Wrzesień", "Październik", "Listopad", "Grudzień"]
    return months[date.month]


def get_month_name_without_polish_chars(date):
    """Zwraca nazwę miesiąca bez polskich znaków (dla folderów IMAP)
    
    Args:
        date: datetime object
        
    Returns:
        str: Nazwa miesiąca bez polskich znaków
    """
    folder_months = ["", "Styczen", "Luty", "Marzec", "Kwiecien", "Maj", "Czerwiec",
                     "Lipiec", "Sierpien", "Wrzesien", "Pazdziernik", "Listopad", "Grudzien"]
    return folder_months[date.month]
