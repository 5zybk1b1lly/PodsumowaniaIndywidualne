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
    rows = []
    if format_data is None:
        format_data = {}

    for metryka, wartosc in data.items():
        metryka_format_info = format_data.get(metryka, "")

        if isinstance(metryka_format_info, dict):
            format_type = metryka_format_info.get('format', "")
            decimal_places = metryka_format_info.get('decimal_places', 2)
            metryka_format_spec = parse_format_type(format_type)
            metryka_format_spec['decimal_places'] = decimal_places
        else:
            metryka_format_spec = parse_format_type(metryka_format_info)

        if metryka_format_spec.get('type') != 'auto':
            wartosc_formatted = apply_format_to_value(wartosc, metryka_format_spec)
        else:
            wartosc_formatted = format_number_value(wartosc, metryka)

        metryka_lower = metryka.lower()

        # Determine row background and accent border
        bg_color = ""
        left_border_color = ""

        if "% dziewiątek" in metryka_lower or "dziewiątek" in metryka_lower:
            try:
                wartosc_num = float(wartosc)
                if wartosc_num < 1:
                    wartosc_num *= 100
                if wartosc_num > 5:
                    bg_color = "#FF0000"
                    left_border_color = "#CC0000"
            except Exception:
                pass

        if not bg_color:
            if "realizacja" in metryka_lower:
                bg_color = "#E3F2FD"
                left_border_color = PRIMARY_COLOR
            elif "target" in metryka_lower:
                bg_color = "#FFFDE7"
                left_border_color = ACCENT_COLOR
            elif "estymacja" in metryka_lower:
                bg_color = "#E8F5E9"
                left_border_color = SUCCESS_COLOR
            else:
                bg_color = "#F7F8FA"

        # Text colors
        if bg_color == "#FF0000":
            text_color = "#FFFFFF"
            value_color = "#FFFFFF"
        elif bg_color in ("#E3F2FD", "#FFFDE7"):
            text_color = SECONDARY_COLOR
            value_color = PRIMARY_COLOR
        else:
            text_color = "#555555"
            value_color = "#555555"

        td1_border = f"border-left: 4px solid {left_border_color};" if left_border_color else "border-left: 4px solid transparent;"

        if bg_color == "#FF0000":
            row_bg = "#FF0000"
        else:
            row_bg = "#FFFFFF"

        rows.append(f"""
        <tr style="background-color: {row_bg};">
            <td style="padding: 13px 16px; border-bottom: 1px solid #F0F0F0; font-weight: 500; color: {text_color}; {td1_border}">{metryka}</td>
            <td style="padding: 13px 16px; border-bottom: 1px solid #F0F0F0; text-align: right; color: {value_color}; font-weight: 700; font-size: 15px;">{wartosc_formatted}</td>
        </tr>
        """)

    rows_html = ''.join(rows)

    if report_end_date is None:
        report_end_date = get_week_end_date(tydzien)

    month_start_date = report_end_date.replace(day=1)
    formatted_date_start = month_start_date.strftime("%d.%m.%Y")
    formatted_date_end = report_end_date.strftime("%d.%m.%Y")
    current_month = get_month_name(report_end_date)

    # Load SalesUp logo
    logo_data = ""
    try:
        import base64, os
        logo_path = os.path.join(os.getcwd(), "salesup.png")
        with open(logo_path, "rb") as imgf:
            logo_data = base64.b64encode(imgf.read()).decode()
    except Exception:
        pass

    # Load Motorola logo
    motorola_data = ""
    try:
        import base64, os
        moto_path = os.path.join(os.getcwd(), "motorola.png")
        with open(moto_path, "rb") as imgf:
            motorola_data = base64.b64encode(imgf.read()).decode()
    except Exception:
        pass

    motorola_img = (
        f'<img src="data:image/png;base64,{motorola_data}" style="height:42px;" alt="Motorola"/>'
        if motorola_data else
        '<span style="font-size:22px;font-weight:900;color:#FFFFFF;letter-spacing:2px;">MOTOROLA</span>'
    )
    salesup_img = (
        f'<img src="data:image/png;base64,{logo_data}" style="height:32px;filter:brightness(0) invert(1);" alt="SalesUp"/>'
        if logo_data else
        '<span style="font-size:18px;font-weight:700;color:#FFFFFF;">SalesUp</span>'
    )

    # Intro section
    if pre_table_text is not None:
        intro_html = f'<p style="font-size:14px;color:#555;line-height:1.7;margin:0 0 24px;">{pre_table_text}</p>'
    else:
        intro_html = f"""
            <p style="font-size:15px;color:#1A2535;margin:0 0 6px;font-weight:600;">Cześć {promotor},</p>
            <p style="font-size:14px;color:#666;line-height:1.7;margin:0 0 24px;">
                Przesyłamy Twoje podsumowanie wyników miesięcznych uwzględniające ostatni tydzień rozliczeniowy.
                W razie pytań lub rozbieżności skontaktuj się ze swoim opiekunem.
            </p>
        """

    # Post-table section
    if post_table_text is not None:
        parts = post_table_text.split("\n\n", 1)
        uwagi = parts[0]
        thanks = parts[1] if len(parts) > 1 else "Dziękujemy za Twoją ciężką pracę!<br>Świetnie, że należysz do naszego zespołu!"
        post_html = f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0 0;">
                <tr>
                    <td style="background:#FFF8F8;border-left:4px solid {ERROR_COLOR};
                               padding:14px 18px;font-size:13px;color:#555;line-height:1.7;">
                        <strong style="color:{ERROR_COLOR};display:block;margin-bottom:4px;font-size:12px;
                                       text-transform:uppercase;letter-spacing:0.5px;">Uwagi</strong>
                        {uwagi}
                    </td>
                </tr>
            </table>
            <p style="text-align:center;color:{PRIMARY_COLOR};font-size:15px;font-weight:600;margin:24px 0 0;">
                {thanks}
            </p>
        """
    else:
        post_html = f"""
            <table width="100%" cellpadding="0" cellspacing="0" style="margin:24px 0 0;">
                <tr>
                    <td style="background:#FFF8F8;border-left:4px solid {ERROR_COLOR};
                               padding:14px 18px;font-size:13px;color:#555;line-height:1.7;">
                        <strong style="color:{ERROR_COLOR};display:block;margin-bottom:4px;font-size:12px;
                                       text-transform:uppercase;letter-spacing:0.5px;">Uwagi</strong>
                        Limit dopuszczalnych dziewiątek IMEI wynosi <strong>5%</strong> całkowitej sprzedaży
                        smartfonów. Sprzedaże na &ldquo;999&rdquo; przekraczające ten próg zostaną usunięte.
                    </td>
                </tr>
            </table>
            <p style="text-align:center;color:{PRIMARY_COLOR};font-size:15px;font-weight:600;margin:28px 0 4px;">
                Dziękujemy za Twoją ciężką pracę! 🙌
            </p>
            <p style="text-align:center;color:#888;font-size:13px;margin:0;">
                Świetnie, że należysz do naszego zespołu!
            </p>
        """

    html = f"""<!DOCTYPE html>
<html lang="pl">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
</head>
<body style="margin:0;padding:0;background-color:#EAECEF;font-family:'Segoe UI',Arial,Helvetica,sans-serif;">

<table width="100%" cellpadding="0" cellspacing="0" style="background-color:#EAECEF;padding:24px 0;">
<tr><td align="center">

<table width="620" cellpadding="0" cellspacing="0"
       style="max-width:620px;background-color:#FFFFFF;border-radius:6px;overflow:hidden;
              box-shadow:0 2px 16px rgba(0,0,0,0.10);">

    <!-- ═══ DARK HEADER ═══ -->
    <tr>
        <td style="background-color:#0D1F3C;padding:0;">

            <!-- Logo row -->
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding:20px 28px;vertical-align:middle;">
                        {motorola_img}
                    </td>
                    <td style="padding:20px 28px;text-align:right;vertical-align:middle;">
                        {salesup_img}
                    </td>
                </tr>
            </table>

            <!-- Blue divider -->
            <div style="height:3px;background-color:{PRIMARY_COLOR};"></div>

            <!-- Title block -->
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="padding:24px 28px 28px;text-align:center;">
                        <p style="margin:0 0 6px;font-size:11px;font-weight:600;color:{PRIMARY_COLOR};
                                  letter-spacing:2px;text-transform:uppercase;">
                            Raport Miesięczny
                        </p>
                        <h1 style="margin:0 0 14px;font-size:26px;font-weight:700;color:#FFFFFF;
                                   letter-spacing:0.5px;">
                            {current_month} &nbsp;&middot;&nbsp; Tydzień {tydzien}
                        </h1>
                        <span style="display:inline-block;background-color:rgba(46,134,193,0.25);
                                     border:1px solid rgba(46,134,193,0.6);
                                     color:#A8CFEA;padding:5px 20px;border-radius:20px;
                                     font-size:13px;letter-spacing:0.5px;">
                            {formatted_date_start} &ndash; {formatted_date_end}
                        </span>
                    </td>
                </tr>
            </table>

        </td>
    </tr>

    <!-- ═══ CONTENT ═══ -->
    <tr>
        <td style="padding:32px 28px 28px;">

            {intro_html}

            <!-- Section label -->
            <p style="margin:0 0 10px;font-size:11px;font-weight:700;color:#AAAAAA;
                      letter-spacing:2px;text-transform:uppercase;">
                Wyniki szczegółowe
            </p>

            <!-- Metrics table -->
            <table width="100%" cellpadding="0" cellspacing="0"
                   style="border-collapse:collapse;border:1px solid #E8EAED;">
                <thead>
                    <tr style="background-color:#0D1F3C;">
                        <th style="padding:12px 16px;text-align:left;font-size:12px;font-weight:600;
                                   color:#A8CFEA;letter-spacing:1px;text-transform:uppercase;
                                   border-bottom:2px solid {PRIMARY_COLOR};">Metryka</th>
                        <th style="padding:12px 16px;text-align:right;font-size:12px;font-weight:600;
                                   color:#A8CFEA;letter-spacing:1px;text-transform:uppercase;
                                   border-bottom:2px solid {PRIMARY_COLOR};">Wartość</th>
                    </tr>
                </thead>
                <tbody>
                    {rows_html}
                </tbody>
            </table>

            {post_html}

        </td>
    </tr>

    <!-- ═══ FOOTER ═══ -->
    <tr>
        <td style="background-color:#0D1F3C;padding:20px 28px;border-top:3px solid {PRIMARY_COLOR};">
            <table width="100%" cellpadding="0" cellspacing="0">
                <tr>
                    <td style="vertical-align:middle;">
                        <span style="font-size:13px;font-weight:700;color:#FFFFFF;">SalesUp Polska SA</span>
                        <br>
                        <span style="font-size:11px;color:#5C7A99;">Raport wygenerowany automatycznie</span>
                    </td>
                    <td style="text-align:right;vertical-align:middle;">
                        <span style="font-size:11px;color:#5C7A99;">&copy; 2026 Wszystkie prawa zastrzeżone</span>
                    </td>
                </tr>
            </table>
        </td>
    </tr>

</table>
</td></tr></table>

</body>
</html>"""
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
    if report_end_date is None:
        report_end_date = get_week_end_date(tydzien)
    if format_data is None:
        format_data = {}

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

    for metryka, wartosc in data.items():
        metryka_format_info = format_data.get(metryka, "")

        if isinstance(metryka_format_info, dict):
            format_type = metryka_format_info.get('format', "")
            decimal_places = metryka_format_info.get('decimal_places', 2)
            metryka_format_spec = parse_format_type(format_type)
            metryka_format_spec['decimal_places'] = decimal_places
        else:
            metryka_format_spec = parse_format_type(metryka_format_info)

        if metryka_format_spec.get('type') != 'auto':
            wartosc_formatted = apply_format_to_value(wartosc, metryka_format_spec)
        else:
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
