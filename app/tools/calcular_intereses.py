from __future__ import annotations

from langchain_core.tools import tool


@tool
def calcular_intereses(
    monto: float,
    tasa_anual: float,
    plazo_meses: int,
    incluir_tabla: bool = False,
) -> dict:
    """Calcula la cuota mensual, el total de intereses y la amortización de un préstamo o financiamiento.

    Usa el sistema de cuota fija (sistema francés). Es un cálculo local, no
    consulta la base de datos. Úsala cuando el usuario pregunte cuánto
    pagaría de cuota por un préstamo, tarjeta u otro financiamiento, cuánto
    interés total pagaría, o pida el detalle de cómo se amortiza una deuda
    mes a mes.

    Args:
        monto: monto del préstamo o saldo a financiar.
        tasa_anual: tasa de interés anual nominal, en porcentaje (ej. 18 para 18%).
        plazo_meses: número de cuotas mensuales.
        incluir_tabla: si es True, incluye el detalle mes a mes (cuota, interés, capital, saldo). Por defecto False.
    """
    if monto <= 0:
        return {"error": "El monto debe ser mayor a 0."}
    if tasa_anual < 0:
        return {"error": "La tasa anual no puede ser negativa."}
    if plazo_meses < 1:
        return {"error": "El plazo debe ser de al menos 1 mes."}

    tasa_mensual = tasa_anual / 100 / 12

    if tasa_mensual == 0:
        cuota = monto / plazo_meses
    else:
        factor = (1 + tasa_mensual) ** plazo_meses
        cuota = monto * (tasa_mensual * factor) / (factor - 1)

    saldo = monto
    tabla = []
    for periodo in range(1, plazo_meses + 1):
        interes_periodo = saldo * tasa_mensual
        capital_periodo = cuota - interes_periodo
        saldo = max(saldo - capital_periodo, 0)
        tabla.append(
            {
                "periodo": periodo,
                "cuota": round(cuota, 2),
                "interes": round(interes_periodo, 2),
                "capital": round(capital_periodo, 2),
                "saldo": round(saldo, 2),
            }
        )

    total_interes = sum(fila["interes"] for fila in tabla)

    resultado = {
        "cuota_mensual": round(cuota, 2),
        "total_pagado": round(cuota * plazo_meses, 2),
        "total_interes": round(total_interes, 2),
    }
    if incluir_tabla:
        resultado["tabla_amortizacion"] = tabla

    return resultado
