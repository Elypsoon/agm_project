from decimal import Decimal


def redondeo(valor):
    """Redondea un promedio en escala 0-100 a un entero en escala 0-10.

    Reglas institucionales:
    - Promedio (en escala 0-10) < 6: función piso SIEMPRE.
    - Promedio (en escala 0-10) >= 6: función piso si la fracción < 0.5,
      función techo si la fracción >= 0.5.
    """
    dec = valor if isinstance(valor, Decimal) else Decimal(str(valor))

    # Convertir de escala 0-100 a 0-10
    en_diez = dec / Decimal('10')

    entero = int(en_diez.to_integral_value(rounding='ROUND_FLOOR'))
    fraccion = en_diez - Decimal(entero)

    if en_diez < Decimal('6'):
        # Reprobado: siempre piso
        return entero
    else:
        # Aprobado: techo si fracción >= 0.5, piso si no
        if fraccion >= Decimal('0.5'):
            return int(en_diez.to_integral_value(rounding='ROUND_CEILING'))
        return entero
