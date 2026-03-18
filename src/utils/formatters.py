"""Number and value formatting utility functions"""


def format_number_value(value, metryka_name=""):
    """Formatuje liczbę z separatorami tysięcy i przecinkiem jako separator dziesiętny (format polski)
    
    Args:
        value: Wartość do sformatowania (int, float lub string)
        metryka_name: Nazwa metryki - używana do określenia jednostek (zł, %)
        
    Returns:
        str: Sformatowana wartość z jednostkami
    """
    if value is None or value == "":
        return ""
    
    if isinstance(value, str):
        return value
    
    try:
        value = float(value)
        
        # Określ suffix i czy to procent
        suffix = ""
        is_percent = False
        
        metryka_lower = metryka_name.lower()
        
        # Metryki ze złotówkami - użyj set dla szybszego sprawdzania
        currency_metrics = {"wartość sztywna", "target obrót", "wartość akc"}
        if any(metric in metryka_lower for metric in currency_metrics):
            suffix = " zł"
        
        # Metryki z procentami - te należy pomnożyć przez 100
        percent_metrics = {"% dziewiątek", "realizacja godzin", "realizacja obrót", "realizacja akc"}
        if any(metric in metryka_lower for metric in percent_metrics):
            is_percent = True
            suffix = " %"
            # Pomnóż przez 100
            value = value * 100
        
        # Formatuj liczbę
        if is_percent:
            # Procenty - wyświetl bez miejsc dziesiętnych jeśli liczba całkowita
            if value == int(value):
                formatted = f"{int(value)}"
            else:
                formatted = f"{value:.2f}".replace('.', ',')
        else:
            # Zwykłe liczby - ze spacjami jako separatory tysięcy
            if value == int(value):
                formatted = f"{int(value):,}".replace(',', ' ')
            else:
                formatted = f"{value:,.2f}".replace(',', ' ').replace('.', ',')
        
        return formatted + suffix
    except Exception:
        return str(value)
