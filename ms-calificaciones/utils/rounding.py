from decimal import Decimal

def redondeo(valor):
    dec = valor if isinstance(valor, Decimal) else Decimal(str(valor))
    entero = int(dec.to_integral_value(rounding='ROUND_FLOOR'))
    fraccion = dec - Decimal(entero)

    if fraccion >= Decimal('0.5'):
        return int(dec.to_integral_value(rounding='ROUND_CEILING'))
    return entero