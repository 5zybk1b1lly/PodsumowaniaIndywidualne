"""HTML and text report generation functions"""

from datetime import timedelta
from src.utils.date_utils import get_week_end_date, get_month_name
from src.utils.formatters import format_number_value
from src.utils.data_utils import parse_format_type, apply_format_to_value
from src.config.colors import PRIMARY_COLOR, SECONDARY_COLOR, SUCCESS_COLOR, ERROR_COLOR, ACCENT_COLOR


def generuj_html_raport(promotor, tydzien, data, report_end_date=None, format_data=None,
                         pre_table_text=None, post_table_text=None):
    """Generuje piękny HTML raportu
    
    Args:
        promotor: Imię promotora
        tydzien: Numer tygodnia
        data: Słownik metryk i wartości
        report_end_date: Data końcowa raportu (opcjonalnie)
        format_data: Słownik formatów dla kolumn (opcjonalnie)
        pre_table_text: opcjonalny tekst (lub fragment HTML) wstawiany przed tabelą;
            jeżeli podano, zastępuje domyślny wstęp.
        post_table_text: opcjonalny tekst (lub fragment HTML) wstawiany po tabeli;
            jeżeli podano, zastępuje domyślne uwagi/dziękczynne akapity.
    Returns:
        str: HTML raportu
    """
    # Użyj list comprehension dla szybszego budowania HTML
    rows = []
    if format_data is None:
        format_data = {}
    
    for metryka, wartosc in data.items():
        # Get format for this metric if available
        metryka_format_info = format_data.get(metryka, "")
        
        # Handle both old format (string) and new format (dict with format and decimal_places)
        if isinstance(metryka_format_info, dict):
            # New format from dialog: {'format': 'zł', 'decimal_places': 2}
            format_type = metryka_format_info.get('format', "")
            decimal_places = metryka_format_info.get('decimal_places', 2)
            metryka_format_spec = parse_format_type(format_type)
            metryka_format_spec['decimal_places'] = decimal_places
        else:
            # Old format: just a string like "zł" or "%"
            metryka_format_spec = parse_format_type(metryka_format_info)
        
        # Format wartość używając specyficznego formatu jeśli dostępny, inaczej auto-detect
        if metryka_format_spec.get('type') != 'auto':
            wartosc_formatted = apply_format_to_value(wartosc, metryka_format_spec)
        else:
            # Fall back to default formatting based on metric name
            wartosc_formatted = format_number_value(wartosc, metryka)
        
        metryka_lower = metryka.lower()
        
        # Określ styl na podstawie typu metryki
        style = ""
        
        # Sprawdź czy to % dziewiątek IMEI i czy > 5%
        if "% dziewiątek" in metryka_lower or "dziewiątek" in metryka_lower:
            try:
                wartosc_num = float(wartosc)
                # jeśli wartość < 1, to jest w formacie dziesiętnym (0.08 = 8%)
                # jeśli wartość > 1, to już procent (8 = 8%)
                if wartosc_num < 1:
                    wartosc_num = wartosc_num * 100
                if wartosc_num > 5:
                    # Czerwone tło gdy dziewiątki > 5%
                    style = 'background-color: #FF0000; border-left: 4px solid #CC0000;'
            except Exception:
                pass
        
        # Jeśli nie ma warunkowego koloru, zastosuj standardowy
        if not style:
            if "realizacja" in metryka_lower:
                # Realizacja - niebieskie tło
                style = f'background-color: #E3F2FD; border-left: 4px solid {PRIMARY_COLOR};'
            elif "target" in metryka_lower:
                # Target - żółte tło
                style = f'background-color: #FFFDE7; border-left: 4px solid {ACCENT_COLOR};'
            elif "estymacja" in metryka_lower:
                # Estymacja - zielone tło
                style = f'background-color: #E8F5E9; border-left: 4px solid {SUCCESS_COLOR};'
            else:
                # Pozostałe - jednolity szary kolor
                style = 'background-color: #F0F0F0;'
        
        # Określ kolor tekstu - biały dla czerwonego tła, szary dla standardowych, kolorowy dla realizacji/target
        if "background-color: #FF0000" in style:
            # Czerwone tło - biały tekst
            text_color = "white"
            value_color = "white"
        elif "background-color: #E3F2FD" in style or "background-color: #FFFDE7" in style:
            # Realizacja lub target - standardowe kolory
            text_color = SECONDARY_COLOR
            value_color = PRIMARY_COLOR
        else:
            # Standardowe wartości - szary tekst
            text_color = "#666666"
            value_color = "#666666"
        
        rows.append(f"""
        <tr style="{style}">
            <td style="padding: 12px; border-bottom: 1px solid #DDDDDD; font-weight: 500; color: {text_color};">{metryka}</td>
            <td style="padding: 12px; border-bottom: 1px solid #DDDDDD; text-align: right; color: {value_color}; font-weight: 600;">{wartosc_formatted}</td>
        </tr>
        """)
    
    rows_html = ''.join(rows)

    # Określ datę końcową raportu: użyj przekazanej wartości lub oblicz z numeru tygodnia
    if report_end_date is None:
        report_end_date = get_week_end_date(tydzien)
    week_start_date = report_end_date - timedelta(days=6)  # poniedziałek (6 dni wcześniej)
    
    # Początek miesiąca oparty na wybranej dacie końcowej raportu
    month_start_date = report_end_date.replace(day=1)
    formatted_date_start = month_start_date.strftime("%d.%m.%Y")
    formatted_date_end = report_end_date.strftime("%d.%m.%Y")
    
    # Nazwa miesiąca, którego dotyczy raport (na podstawie report_end_date)
    current_month = get_month_name(report_end_date)

    # jeśli dostępne, wczytaj logo jako base64 (plik w katalogu roboczym)
    logo_data = ""
    try:
        import base64, os
        logo_path = os.path.join(os.getcwd(), "salesup.png")
        with open(logo_path, "rb") as imgf:
            logo_data = base64.b64encode(imgf.read()).decode()
    except Exception:
        pass

    # przygotuj opcjonalne bloki wstępu i zakończenia
    if pre_table_text is not None:
        intro_html = f"<div class=\"intro-text\">{pre_table_text}</div>"
    else:
        intro_html = f"""
                <div class="greeting">Cześć {promotor}! 👋</div>
                
                <div class="intro-text">
                    Poniżej znajdziesz podsumowanie Twoich wyników miesięcznych z uwzględnieniem ostatniego tygodnia. 
                    <br>Jeśli masz jakiekolwiek pytania dotyczące tych danych lub coś nie zgadza się z Twoimi obliczeniami, skontaktuj się z nami.
                </div>
        """

    if post_table_text is not None:
        # podziel na dwie części oddzielone pustą linią - pierwsza to uwagi, druga to podziękowania
        parts = post_table_text.split("\n\n", 1)
        uwagi = parts[0]
        thanks = parts[1] if len(parts) > 1 else "Dziękujemy za Twoją ciężką pracę! 🙌<br>Świetnie, że należysz do naszego zespołu!"
        post_html = f"""
                <div class="intro-text" style="text-align: center; margin-top: 30px; color: {ERROR_COLOR}; font-weight: 500;">
                    {uwagi}
                </div>
                <div class="intro-text" style="text-align: center; margin-top: 30px; color: {PRIMARY_COLOR}; font-weight: 500;">
                    {thanks}
                </div>
        """
    else:
        post_html = f"""
                <div class="intro-text" style="text-align: center; margin-top: 30px; color: {ERROR_COLOR}; font-weight: 500;">
                    <b>UWAGI:</b>
                    Limit dopuszczalnych dziewiątek IMEI wynosi 5% całkowitej sprzedaży smartfonów i wszystkie sprzedaże na "999" powyżej tej wartości zostaną usunięte.
                    
                </div>
                <div class="intro-text" style="text-align: center; margin-top: 30px; color: {PRIMARY_COLOR}; font-weight: 500;">
                    Dziękujemy za Twoją ciężką pracę! 🙌
                    <br>Świetnie, że należysz do naszego zespołu! 
                </div>
        """

    html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background-color: #F5F7FA;
                margin: 0;
                padding: 20px;
                color: #2C3E50;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #FFFFFF;
                border-radius: 10px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                overflow: hidden;
            }}
            .header {{
                background: linear-gradient(135deg, {PRIMARY_COLOR} 0%, #1E5A96 100%);
                color: #FFFFFF;
                padding: 30px;
                text-align: center;
            }}
            .header h1 {{
                
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 14px;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px;
            }}
            .greeting {{
                font-size: 18px;
                color: {SECONDARY_COLOR};
                margin-bottom: 20px;
                font-weight: 500;
            }}
            .intro-text {{
                font-size: 14px;
                color: #555555;
                line-height: 1.6;
                margin-bottom: 20px;
                text-align: center;
            }}
            table {{
                width: 100%;
                border-collapse: collapse;
                margin: 20px 0;
            }}
            th {{
                background-color: {PRIMARY_COLOR};
                color: #FFFFFF;
                padding: 15px;
                text-align: left;
                font-weight: 600;
                font-size: 14px;
            }}
            td {{
                padding: 12px 15px;
            }}
            .footer {{
                background-color: #F8F9FA;
                padding: 20px 30px;
                text-align: center;
                border-top: 1px solid #EEEEEE;
                font-size: 12px;
                color: #888888;
            }}
            .footer-text {{
                margin: 5px 0;
            }}
            .badge {{
                display: inline-block;
                background-color: {SUCCESS_COLOR};
                color: #FFFFFF;
                padding: 5px 12px;
                border-radius: 20px;
                font-size: 12px;
                margin-left: 10px;
            }}
            .divider {{
                height: 2px;
                background: linear-gradient(to right, {PRIMARY_COLOR}, transparent);
                margin: 20px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                {f"<img src=\"data:image/png;base64,{logo_data}\" style=\"max-width:120px;margin-bottom:10px;\"/>" if logo_data else ""}
                <h1>📊 Raport Miesięczny - {current_month} po {tydzien} tygodniu</h1>
                <p><span class="badge">{formatted_date_start} - {formatted_date_end}</span></p>
            </div>
            
            <div class="content">
                {intro_html}
                
                <div class="divider"></div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Metryka</th>
                            <th style="text-align: right;">Wartość</th>
                        </tr>
                    </thead>
                    <tbody>
                        {rows_html}
                    </tbody>
                </table>
                
                <div class="divider"></div>

                {post_html}

                
            </div>
            
            <div class="footer">
                <div class="footer-text">
                    <strong>SalesUp Polska SA</strong>
                </div>
                <div class="footer-text">
                    Raport wygenerowany automatycznie
                </div>
                <div class="footer-text" style="margin-top: 10px; color: #AAAAAA;">
                    © 2026 Wszystkie prawa zastrzeżone
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    return html


def generuj_tekst_raport(promotor, tydzien, data, report_end_date=None, format_data=None,
                         pre_table_text=None, post_table_text=None):
    """Generuje tekstową wersję raportu
    
    Args:
        promotor: Imię promotora
        tydzien: Numer tygodnia
        data: Słownik metryk i wartości
        report_end_date: Data końcowa raportu (opcjonalnie)
        format_data: Słownik formatów dla kolumn (opcjonalnie)
        pre_table_text: dodatkowy tekst wstawiony przed listą metryk; jeżeli podany,
            zastępuje standardowy wstęp.
        post_table_text: dodatkowy tekst wstawiony po liście metryk; jeżeli podany,
            zastępuje standardowe "uwagi/dziękczynne" zakończenie.
    Returns:
        str: Tekstowa wersja raportu
    """
    # Określ datę końcową raportu: użyj przekazanej wartości lub oblicz z numeru tygodnia
    if report_end_date is None:
        report_end_date = get_week_end_date(tydzien)
    if format_data is None:
        format_data = {}
    # Początek miesiąca oparty na wybranej dacie końcowej raportu
    month_start_date = report_end_date.replace(day=1)
    formatted_date_start = month_start_date.strftime("%d.%m.%Y")
    formatted_date_end = report_end_date.strftime("%d.%m.%Y")

    current_month = get_month_name(report_end_date)

    if pre_table_text is not None:
        intro_text = pre_table_text
    else:
        intro_text = (
            "Poniżej znajdziesz podsumowanie Twoich wyników miesięcznych z uwzględnieniem ostatniego tygodnia.\n"
            "Świetnie, że należysz do naszego zespołu! \n"
            "Jeśli masz jakiekolwiek pytania dotyczące tych danych lub coś nie zgadza się z Twoimi obliczeniami, skontaktuj się z nami.\n"
        )

    text = f"""Raport Miesięczny - {current_month} po {tydzien} tygodniu

Cześć {promotor}!

{intro_text}
"""

    # Dodaj dane w formacie tekstowym
    for metryka, wartosc in data.items():
        # Get format for this metric if available
        metryka_format_info = format_data.get(metryka, "")
        
        # Handle both old format (string) and new format (dict with format and decimal_places)
        if isinstance(metryka_format_info, dict):
            # New format from dialog: {'format': 'zł', 'decimal_places': 2}
            format_type = metryka_format_info.get('format', "")
            decimal_places = metryka_format_info.get('decimal_places', 2)
            metryka_format_spec = parse_format_type(format_type)
            metryka_format_spec['decimal_places'] = decimal_places
        else:
            # Old format: just a string like "zł" or "%"
            metryka_format_spec = parse_format_type(metryka_format_info)
        
        # Format wartość używając specyficznego formatu jeśli dostępny, inaczej auto-detect
        if metryka_format_spec.get('type') != 'auto':
            wartosc_formatted = apply_format_to_value(wartosc, metryka_format_spec)
        else:
            # Fall back to default formatting based on metric name
            wartosc_formatted = format_number_value(wartosc, metryka)
        
        text += f"{metryka}: {wartosc_formatted}\n"

    if post_table_text is not None:
        text += f"\n{post_table_text}\n"
    else:
        text += f"""

UWAGI:
Limit dopuszczalnych dziewiątek IMEI wynosi 5% całkowitej sprzedaży smartfonów i wszystkie sprzedaże na "999" powyżej tej wartości zostaną usunięte.

Dziękujemy za Twoją ciężką pracę!

SalesUp Polska SA
Raport wygenerowany automatycznie
© 2026 Wszystkie prawa zastrzeżone
"""

    return text
