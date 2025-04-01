def calcular_facturacion_total(facturacion_mensual):
    return facturacion_mensual['Imp. Total'].sum()

def calcular_facturacion_promedio_mensual(facturacion_mensual):
    return facturacion_mensual['Imp. Total'].mean()

def calcular_tasa_crecimiento_promedio_mensual(facturacion_mensual):
    if facturacion_mensual.empty or 'Imp. Total' not in facturacion_mensual.columns:
        return None
    if len(facturacion_mensual) < 2:
        return None
    valor_inicial = facturacion_mensual['Imp. Total'].iloc[0]
    valor_final = facturacion_mensual['Imp. Total'].iloc[-1]
    n = len(facturacion_mensual)
    tasa_crecimiento_promedio = ((valor_final / valor_inicial) ** (1/n) - 1) * 100
    return tasa_crecimiento_promedio

