from decimal import Decimal


def redondeo(valor):
    """Redondea una calificación promedio en escala 0-100 a un entero oficial en escala 0-10.

    Aplica las reglas oficiales de redondeo institucional:
      1. Se escala el valor de la base 100 a base 10 (dividiendo entre 10).
      2. Si el promedio resultante en escala 0-10 es menor a 6.0 (reprobatorio),
         se aplica redondeo hacia abajo (función piso) incondicionalmente.
         (Ej. 5.99 -> 5).
      3. Si el promedio resultante en escala 0-10 es mayor o igual a 6.0, se
         aplica redondeo estándar: fracción menor a 0.5 redondea hacia abajo (piso),
         y fracción mayor o igual a 0.5 redondea hacia arriba (techo).
         (Ej. 8.50 -> 9, 8.49 -> 8).

    Args:
        valor: Nota promedio en escala de 0.00 a 100.00. Puede ser de tipo
            Decimal, float, int o str.

    Returns:
        int: Calificación final redondeada en escala de 0 a 10.
    """
    dec = valor if isinstance(valor, Decimal) else Decimal(str(valor))

    # Convertir de escala 0-100 a escala 0-10
    en_diez = dec / Decimal('10')

    entero = int(en_diez.to_integral_value(rounding='ROUND_FLOOR'))
    fraccion = en_diez - Decimal(entero)

    if en_diez < Decimal('6'):
        # Reprobado: siempre piso (truncamiento)
        return entero
    else:
        # Aprobado: redondeo estándar con punto medio hacia arriba
        if fraccion >= Decimal('0.5'):
            return int(en_diez.to_integral_value(rounding='ROUND_CEILING'))
        return entero

