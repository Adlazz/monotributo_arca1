def calcular_facturacion_total(facturacion_mensual):
    """Calcula la facturación total del período"""
    return facturacion_mensual['Imp. Total'].sum()

def calcular_facturacion_promedio_mensual(facturacion_mensual):
    """Calcula el promedio mensual de facturación"""
    return facturacion_mensual['Imp. Total'].mean()

def calcular_tasa_crecimiento_promedio_mensual(facturacion_mensual):
    """Calcula la tasa de crecimiento promedio mensual"""
    if facturacion_mensual.empty or 'Imp. Total' not in facturacion_mensual.columns:
        return None
    if len(facturacion_mensual) < 2:
        return None
    valor_inicial = facturacion_mensual['Imp. Total'].iloc[0]
    valor_final = facturacion_mensual['Imp. Total'].iloc[-1]
    n = len(facturacion_mensual)
    tasa_crecimiento_promedio = ((valor_final / valor_inicial) ** (1/n) - 1) * 100
    return tasa_crecimiento_promedio

def calcular_margen_disponible(facturacion_acumulada, limite_categoria):
    """Calcula el margen disponible hasta el límite de la categoría"""
    return max(0, limite_categoria - facturacion_acumulada)

def calcular_exceso_facturacion(facturacion_acumulada, limite_categoria):
    """Calcula el exceso de facturación sobre el límite de la categoría"""
    return max(0, facturacion_acumulada - limite_categoria)

def calcular_promedio_mensual_disponible(margen_disponible, meses_restantes):
    """Calcula el promedio mensual disponible para facturar en los meses restantes"""
    if meses_restantes <= 0:
        return 0
    return margen_disponible / meses_restantes

def calcular_reduccion_necesaria(exceso, meses_restantes):
    """Calcula la reducción mensual necesaria si hay exceso de facturación"""
    if meses_restantes <= 0:
        return 0
    return exceso / meses_restantes

def determinar_categoria_encuadre(facturacion_acumulada, categorias):
    """Determina en qué categoría quedaría encuadrado según la facturación acumulada"""
    categorias_ordenadas = sorted(categorias.items(), key=lambda x: x[1])

    for cat, limite in categorias_ordenadas:
        if facturacion_acumulada <= limite:
            return cat, limite

    return None, None  # Excede todas las categorías

def analizar_categoria_siguiente(facturacion_acumulada, categoria_actual, categorias, meses_restantes):
    """Analiza el margen disponible en la categoría siguiente"""
    categorias_ordenadas = sorted(categorias.items(), key=lambda x: x[1])

    # Encontrar la posición de la categoría actual
    posicion_actual = None
    for idx, (cat, _) in enumerate(categorias_ordenadas):
        if cat == categoria_actual:
            posicion_actual = idx
            break

    # Si hay una categoría siguiente
    if posicion_actual is not None and posicion_actual < len(categorias_ordenadas) - 1:
        categoria_siguiente = categorias_ordenadas[posicion_actual + 1][0]
        limite_siguiente = categorias_ordenadas[posicion_actual + 1][1]

        margen_siguiente = calcular_margen_disponible(facturacion_acumulada, limite_siguiente)
        promedio_siguiente = calcular_promedio_mensual_disponible(margen_siguiente, meses_restantes)

        return {
            'categoria': categoria_siguiente,
            'limite': limite_siguiente,
            'margen_disponible': margen_siguiente,
            'promedio_mensual': promedio_siguiente
        }

    return None

