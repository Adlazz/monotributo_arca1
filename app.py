import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import streamlit_shadcn_ui as ui
from local_components import card_container
import locale
from calculos import (
    calcular_facturacion_total,
    calcular_facturacion_promedio_mensual,
    calcular_tasa_crecimiento_promedio_mensual,
    calcular_margen_disponible,
    calcular_exceso_facturacion,
    calcular_promedio_mensual_disponible,
    calcular_reduccion_necesaria,
    determinar_categoria_encuadre,
    analizar_categoria_siguiente
)

# Establecer el idioma español para la conversión de fechas
try:
    # Attempt Windows locale setting
    locale.setlocale(locale.LC_TIME, 'Spanish_Spain.1252')
except locale.Error:
    try:
        # Fallback to Linux locale setting
        locale.setlocale(locale.LC_TIME, 'es_ES.UTF-8')
    except locale.Error:
        # Use system default if specified locales are unavailable
        locale.setlocale(locale.LC_TIME, '')

# Función para determinar la fecha de próxima recategorización
def obtener_proxima_recategorizacion(fecha_actual):
    """
    Determina la próxima fecha de recategorización según el mes actual.
    Recategorización SEMESTRAL en ARCA:
    - ENERO: evalúa período Jul-Dic del año anterior
    - JULIO: evalúa período Ene-Jun del año actual

    Por lo tanto:
    - Si estamos en Jul-Dic: próxima recategorización = Enero del año siguiente
    - Si estamos en Ene-Jun: próxima recategorización = Julio del año actual
    """
    mes_actual = fecha_actual.month
    año_actual = fecha_actual.year

    if mes_actual >= 7:  # Julio a Diciembre
        # Próxima recategorización: Enero del próximo año
        return datetime(año_actual + 1, 1, 1).date()
    else:  # Enero a Junio
        # Próxima recategorización: Julio del año actual
        return datetime(año_actual, 7, 1).date()

# Función de ETL mejorada para período móvil de recategorización
def procesar_csv(uploaded_file):
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file, sep=';', encoding='utf-8', decimal=',', thousands='.')
        df.columns = [col.strip() for col in df.columns]
        columnas_requeridas = [
            'Fecha de Emisión', 'Tipo de Comprobante', 'Punto de Venta',
            'Número Desde', 'Número Hasta', 'Nro. Doc. Receptor', 'Denominación Receptor', 'Imp. Total']
        df = df[columnas_requeridas]
        df['Nro. Doc. Receptor'] = df['Nro. Doc. Receptor'].astype(str)
        df['Fecha de Emisión'] = pd.to_datetime(df['Fecha de Emisión'], format='%Y-%m-%d').dt.date
        df['Imp. Total'] = df.apply(lambda row: -row['Imp. Total'] if row['Tipo de Comprobante'] == 13 else row['Imp. Total'], axis=1)
        df['Mes'] = pd.to_datetime(df['Fecha de Emisión']).dt.to_period('M')

        # Facturación mensual agrupada
        facturacion_mensual = df.groupby('Mes')['Imp. Total'].sum().reset_index()
        facturacion_mensual['Mes_Period'] = facturacion_mensual['Mes']  # Guardar Period
        facturacion_mensual['Mes'] = facturacion_mensual['Mes'].dt.to_timestamp()
        facturacion_mensual['Mes_Str'] = facturacion_mensual['Mes'].dt.strftime('%Y-%m')
        facturacion_mensual['Acumulado'] = facturacion_mensual['Imp. Total'].cumsum()

        # Determinar fecha de última factura cargada
        fecha_max = df['Fecha de Emisión'].max()
        fecha_min = df['Fecha de Emisión'].min()

        # Calcular próxima recategorización
        proxima_recategorizacion = obtener_proxima_recategorizacion(fecha_max)

        # Calcular meses entre fecha_max y proxima_recategorizacion
        # Restamos 1 porque no contamos el mes actual completo
        meses_restantes = (proxima_recategorizacion.year - fecha_max.year) * 12 + \
                         (proxima_recategorizacion.month - fecha_max.month) - 1
        meses_restantes = max(0, meses_restantes)  # No puede ser negativo

        # Para el análisis, separar en histórico y actual (opcional)
        num_meses = len(facturacion_mensual)
        if num_meses >= 6:
            # Si hay 6 o más meses, separar en histórico (primeros) y actual (últimos)
            mitad = num_meses // 2
            facturacion_historica = facturacion_mensual.iloc[:mitad].copy()
            facturacion_actual = facturacion_mensual.iloc[mitad:].copy()
        else:
            # Si hay menos de 6 meses, todo es período actual
            facturacion_historica = pd.DataFrame()
            facturacion_actual = facturacion_mensual.copy()

        return df, facturacion_mensual, facturacion_historica, facturacion_actual, fecha_min, fecha_max, proxima_recategorizacion, meses_restantes
    else:
        # Devuelve DataFrames vacíos si no se subió ningún archivo
        return pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), pd.DataFrame(), None, None, None, 0

def calcular_kpis(facturacion_mensual):
    facturacion_total = calcular_facturacion_total(facturacion_mensual)
    facturacion_promedio_mensual = calcular_facturacion_promedio_mensual(facturacion_mensual)
    tasa_crecimiento_promedio = calcular_tasa_crecimiento_promedio_mensual(facturacion_mensual)
    return facturacion_total, facturacion_promedio_mensual, tasa_crecimiento_promedio

def main():
    # =============================================================================
    # Sección 1: Configuración inicial
    # =============================================================================
    st.set_page_config(layout="wide", page_title="Análisis de Monotributo", page_icon=":bar_chart:")
    st.title('📊 Análisis de Monotributo')
    st.markdown("##")

    # =============================================================================
    # Sección 2: Guía de uso
    # =============================================================================
    with st.expander("ℹ️ Guía de Uso"):
        st.markdown("""
        ### 📥 Cómo Usar

        1. Ingresa con Clave Fiscal en [ARCA](https://auth.afip.gob.ar/contribuyente_/login.xhtml)
        2. Descarga tu archivo de facturación en formato CSV desde el servicio Mis Comprobantes -> Emitidos
        3. **Importante**: Descarga el período de **12 meses** para la recategorización
           - **Ejemplo: Estás en Marzo 2026 (próxima recategorización: Julio 2026)**
             - Descarga desde **01/07/2025** hasta **31/03/2026** (9 meses cargados)
             - La app calculará: faltan **3 meses** hasta **Julio 2026** (Abril, Mayo, Junio)
             - Podrás facturar los meses restantes sin exceder el límite anual
           - **Ejemplo: Estás en Octubre 2025 (próxima recategorización: Enero 2026)**
             - Descarga desde **01/07/2025** hasta **31/10/2025** (4 meses cargados)
             - La app calculará: faltan **2 meses** hasta **Enero 2026** (Noviembre, Diciembre)
        4. Sube el archivo CSV
        5. Ingresa el nombre del contribuyente y la categoría actual
        6. Obtén un análisis detallado del margen disponible hasta la próxima recategorización

        **Nota**: La recategorización en ARCA se realiza **SEMESTRALMENTE** en Enero y Julio, considerando **12 MESES** de facturación.

        **Períodos de recategorización (12 meses):**
        - **Recategorización de ENERO**: evalúa facturación de **Enero (año anterior) - Diciembre (año anterior)** = 12 meses
        - **Recategorización de JULIO**: evalúa facturación de **Julio (año anterior) - Junio (año actual)** = 12 meses

        **Clave:** Siempre cargar desde el **inicio del período anual** (Julio o Enero) hasta la fecha actual.
        """)

    # =============================================================================
    # Sección 3: Ingreso de datos
    # =============================================================================
    st.subheader("Ingreso de datos: ")

    # Usamos st.columns para crear tres columnas
    col1, col2, col3 = st.columns(3)

    with col1:
        contribuyente = st.text_input("Nombre del Contribuyente", "")

    with col2:
        # Montos vigentes desde abril 2026 (ARCA/ex-AFIP)
        categorias = {
            'A': 10277988.13, 'B': 15058447.71, 'C': 21113696.52, 'D': 26212853.42,
            'E': 30833964.37, 'F': 38642048.36, 'G': 46288359.82, 'H': 70185003.97,
            'I': 78570820.99, 'J': 89946653.09, 'K': 108357084.05
        }
        categoria_actual = st.selectbox("Selecciona tu categoría actual", options=list(categorias.keys()))

    with col3:
        uploaded_file = st.file_uploader("Sube tu archivo CSV del período anual (desde Julio o Enero)", type="csv")

    # Procesamos el CSV con período móvil de recategorización
    df_completo, facturacion_mensual_completa, facturacion_historica, facturacion_actual, fecha_inicio_periodo, fecha_fin_periodo, fecha_recategorizacion, meses_faltantes = procesar_csv(uploaded_file)

    # Verificamos si el archivo CSV ha sido cargado
    if uploaded_file is not None:

        # =============================================================================
        # Sección 4: Cálculo de Métricas y KPIs para Período de Recategorización
        # =============================================================================

        # Obtenemos el límite de la categoría actual
        limite_categoria_actual = categorias[categoria_actual]

        # Cálculos del período completo (12 meses)
        if not facturacion_mensual_completa.empty:
            facturacion_total_12_meses = calcular_facturacion_total(facturacion_mensual_completa)
            facturacion_acumulada_total = facturacion_mensual_completa['Acumulado'].iloc[-1]
        else:
            facturacion_total_12_meses = 0
            facturacion_acumulada_total = 0

        # Cálculos del período histórico (primeros 6 meses)
        if not facturacion_historica.empty:
            facturacion_periodo_historico = calcular_facturacion_total(facturacion_historica)
        else:
            facturacion_periodo_historico = 0

        # Cálculos del período actual (últimos meses cargados)
        if not facturacion_actual.empty:
            facturacion_periodo_actual = calcular_facturacion_total(facturacion_actual)
            facturacion_promedio_mensual_actual = calcular_facturacion_promedio_mensual(facturacion_actual)
            meses_transcurridos = len(facturacion_actual)
        else:
            facturacion_periodo_actual = 0
            facturacion_promedio_mensual_actual = 0
            meses_transcurridos = 0

        # Total de meses cargados
        meses_cargados = len(facturacion_mensual_completa) if not facturacion_mensual_completa.empty else 0

        # Usar los meses restantes calculados por la función (hasta próxima recategorización)
        meses_restantes = max(0, meses_faltantes)

        # Calcular margen disponible y exceso
        margen_disponible = calcular_margen_disponible(facturacion_acumulada_total, limite_categoria_actual)
        exceso_facturacion = calcular_exceso_facturacion(facturacion_acumulada_total, limite_categoria_actual)

        # Promedio mensual disponible para los meses restantes
        promedio_mensual_disponible = calcular_promedio_mensual_disponible(margen_disponible, meses_restantes) if meses_restantes > 0 else 0

        # Si hay exceso, calcular reducción necesaria
        reduccion_mensual_necesaria = calcular_reduccion_necesaria(exceso_facturacion, meses_restantes) if meses_restantes > 0 else 0

        # Determinar categoría de encuadre si excede
        categoria_encuadre, limite_encuadre = determinar_categoria_encuadre(facturacion_acumulada_total, categorias)

        # Analizar categoría siguiente
        analisis_siguiente = analizar_categoria_siguiente(facturacion_acumulada_total, categoria_actual, categorias, meses_restantes)


        # =============================================================================
        # Sección 5: Métricas de Recategorización (Período Móvil)
        # =============================================================================

        st.subheader("📊 Análisis de Período de Recategorización")

        # Mostrar información del período y próxima recategorización
        if fecha_recategorizacion:
            nombre_mes_recateorizacion = fecha_recategorizacion.strftime('%B %Y')
            st.caption(f"**Período cargado**: {fecha_inicio_periodo.strftime('%d/%m/%Y')} - {fecha_fin_periodo.strftime('%d/%m/%Y')} ({meses_cargados} meses) | **Próxima recategorización**: {nombre_mes_recateorizacion} | **Categoría Actual**: {categoria_actual} | **Límite**: ${limite_categoria_actual:,.2f}")
        else:
            st.caption(f"Categoría Actual: **{categoria_actual}** | Límite: ${limite_categoria_actual:,.2f}")

        col1, col2, col3, col4 = st.columns(4)

        # Tarjeta 1: Facturación Total Cargada
        with col1:
            ui.metric_card(
                title=f"Facturación Total ({meses_cargados} meses)",
                content=f"${facturacion_total_12_meses:,.2f}",
                description=f"Acumulado desde {fecha_inicio_periodo.strftime('%b %Y')} hasta {fecha_fin_periodo.strftime('%b %Y')}",
                key="card1"
            )

        # Tarjeta 2: Meses Restantes hasta Recategorización
        with col2:
            ui.metric_card(
                title=f"Meses Restantes",
                content=f"{meses_restantes}",
                description=f"Hasta {fecha_recategorizacion.strftime('%B %Y')} (recategorización)",
                key="card2"
            )

        # Tarjeta 3: Margen Disponible
        with col3:
            color_margen = "green" if margen_disponible > 0 else "red"
            ui.metric_card(
                title="Margen Disponible",
                content=f"${margen_disponible:,.2f}",
                description=f"Para categoría {categoria_actual} ({meses_restantes} meses restantes)",
                key="card3"
            )

        # Tarjeta 4: Promedio Mensual Disponible o Reducción Necesaria
        with col4:
            if exceso_facturacion > 0:
                ui.metric_card(
                    title="⚠️ Exceso de Facturación",
                    content=f"${exceso_facturacion:,.2f}",
                    description=f"Debe reducir ${reduccion_mensual_necesaria:,.2f}/mes" if meses_restantes > 0 else "Ya excedió el límite",
                    key="card4"
                )
            else:
                if meses_restantes > 0:
                    ui.metric_card(
                        title="Promedio Mensual Disponible",
                        content=f"${promedio_mensual_disponible:,.2f}",
                        description=f"Puede facturar en promedio los próximos {meses_restantes} meses",
                        key="card4"
                    )
                else:
                    ui.metric_card(
                        title="✅ Período Completo",
                        content=f"${margen_disponible:,.2f}",
                        description="Margen disponible hasta recategorización",
                        key="card4"
                    )

        # =============================================================================
        # Sección 6: Alertas Inteligentes de Recategorización
        # =============================================================================

        st.markdown("---")

        # Alerta si hay exceso de facturación
        if exceso_facturacion > 0:
            st.error(f"""
            ### ⚠️ ALERTA: Exceso de Facturación Detectado

            - **Exceso**: ${exceso_facturacion:,.2f}
            - **Categoría actual**: {categoria_actual} (límite: ${limite_categoria_actual:,.2f})
            - **Nueva categoría de encuadre**: {categoria_encuadre if categoria_encuadre else 'Excede todas las categorías'}
            - **Facturación acumulada**: ${facturacion_acumulada_total:,.2f}
            - **Meses restantes hasta {fecha_recategorizacion.strftime('%B %Y')}**: {meses_restantes}
            """)

            if meses_restantes > 0 and categoria_encuadre:
                st.info(f"💡 **Recomendación**: Para mantenerse en categoría **{categoria_actual}**, debe reducir su facturación promedio a **${reduccion_mensual_necesaria:,.2f}/mes** o menos durante los próximos {meses_restantes} meses. De lo contrario, quedará encuadrado en categoría **{categoria_encuadre}** en {fecha_recategorizacion.strftime('%B %Y')}.")
            elif meses_restantes == 0:
                st.warning(f"⚠️ El período de recategorización está completo. En {fecha_recategorizacion.strftime('%B %Y')} quedará encuadrado en categoría **{categoria_encuadre}**.")
        else:
            # Alerta de proximidad al límite (si está al 80% o más)
            porcentaje_utilizado = (facturacion_acumulada_total / limite_categoria_actual) * 100

            if porcentaje_utilizado >= 80:
                st.warning(f"""
                ### ⚠️ Proximidad al Límite de Categoría

                - Ha utilizado el **{porcentaje_utilizado:.1f}%** del límite de categoría **{categoria_actual}**
                - **Margen disponible**: ${margen_disponible:,.2f}
                - **Meses restantes hasta {fecha_recategorizacion.strftime('%B %Y')}**: {meses_restantes}
                - **Promedio mensual disponible**: ${promedio_mensual_disponible:,.2f}

                💡 **Recomendación**: Monitoree su facturación mensual para no exceder el promedio disponible.
                """)
            else:
                st.success(f"""
                ### ✅ Situación Fiscal Favorable

                - Utilizado: **{porcentaje_utilizado:.1f}%** del límite de categoría **{categoria_actual}**
                - **Margen disponible**: ${margen_disponible:,.2f}
                - **Meses restantes hasta {fecha_recategorizacion.strftime('%B %Y')}**: {meses_restantes}
                - **Promedio mensual disponible**: ${promedio_mensual_disponible:,.2f}

                ✅ Puede continuar facturando dentro de su categoría actual.
                """)

        # Análisis de categoría siguiente
        if analisis_siguiente:
            with st.expander("📈 Análisis de Categoría Siguiente"):
                st.write(f"""
                **Categoría {analisis_siguiente['categoria']}** (límite: ${analisis_siguiente['limite']:,.2f})
                - **Margen disponible**: ${analisis_siguiente['margen_disponible']:,.2f}
                - **Promedio mensual disponible**: ${analisis_siguiente['promedio_mensual']:,.2f} para {meses_restantes} meses
                """)

        # =============================================================================
        # Sección 7: Gráfico de Facturación Acumulada vs Límite
        # =============================================================================

        with st.container(border=True):
            st.subheader("Facturación Acumulada vs Límites de Categoría")

            bar_height = 0.3

            # Determinar color según estado
            color_barra = 'red' if exceso_facturacion > 0 else ('orange' if porcentaje_utilizado >= 80 else 'green')

            fig_acumulado = px.bar(
                x=[facturacion_acumulada_total],
                y=['Facturación Acumulada 12 meses'],
                orientation='h',
                labels={'x': 'Monto (ARS)', 'y': ''},
                text=[f"${facturacion_acumulada_total:,.2f}"],
                height=300,
                color_discrete_sequence=[color_barra]
            )

            fig_acumulado.update_traces(
                marker=dict(line=dict(width=0)),
                width=bar_height
            )

            # Línea del límite categoría actual
            fig_acumulado.add_vline(
                x=limite_categoria_actual,
                line_dash="dash",
                line_color="red",
                annotation_text=f"Límite Cat. {categoria_actual}: ${limite_categoria_actual:,.0f}",
                annotation_position="top right"
            )

            # Línea del límite categoría siguiente (si existe)
            if analisis_siguiente:
                fig_acumulado.add_vline(
                    x=analisis_siguiente['limite'],
                    line_dash="dot",
                    line_color="blue",
                    annotation_text=f"Límite Cat. {analisis_siguiente['categoria']}: ${analisis_siguiente['limite']:,.0f}",
                    annotation_position="bottom right"
                )

            fig_acumulado.update_layout(
                showlegend=False,
                xaxis=dict(title='Monto (ARS)'),
                yaxis=dict(showticklabels=False),
                plot_bgcolor='rgba(0,0,0,0)',
                margin=dict(l=20, r=20, t=40, b=20)
            )

            st.plotly_chart(fig_acumulado, use_container_width=True)

        # =============================================================================
        # Sección 8: Gráfico de Facturación Mensual
        # =============================================================================

        st.markdown("---")
        st.subheader("📊 Facturación Mensual del Período")

        with st.container(border=True):
            col1, col2 = st.columns([3, 1])

            with col1:
                # Gráfico de facturación mensual del período completo
                if not facturacion_mensual_completa.empty:
                    # Formato del período para el título
                    periodo_titulo = f"{fecha_inicio_periodo.strftime('%b %Y')} - {fecha_fin_periodo.strftime('%b %Y')}"

                    # Crear el gráfico usando Mes_Str para el eje X
                    fig_mensual = px.bar(
                        facturacion_mensual_completa,
                        x='Mes_Str',
                        y='Imp. Total',
                        title=f'Facturación Mensual - {contribuyente} ({periodo_titulo})',
                        labels={'Imp. Total': 'Facturación Mensual (ARS)', 'Mes_Str': 'Mes'},
                        color='Imp. Total',
                        color_continuous_scale='Blues'
                    )

                    fig_mensual.update_layout(
                        xaxis_tickangle=-45,
                        showlegend=False,
                        height=400
                    )

                    st.plotly_chart(fig_mensual, use_container_width=True)

            with col2:
                st.write("**Facturación mensual:**")
                # Mostrar solo las columnas relevantes
                st.dataframe(
                    facturacion_mensual_completa[['Mes_Str', 'Imp. Total']].rename(columns={'Mes_Str': 'Mes'}).style.format({'Imp. Total': '${:,.2f}'}),
                    hide_index=True,
                    height=350
                )
            

        # =============================================================================
        # Sección 9: Cuadro de facturación agrupada por cliente + Gráfico
        # =============================================================================

        st.markdown("---")
        st.subheader("📊 Facturación por Cliente")

        # Cantidad de clientes
        num_receptores_unicos = df_completo['Denominación Receptor'].nunique()
        st.write(f"Número de clientes únicos en el período: **{num_receptores_unicos}**")

        col1, col2 = st.columns([1, 1.5])

        with col1:
            # Agrupación por cliente y recuento de facturas
            facturacion_cliente = df_completo.groupby('Denominación Receptor')['Imp. Total'].sum().reset_index()
            cantidad_facturas = df_completo.groupby('Denominación Receptor').size().reset_index(name='Cantidad de Facturas')
            facturacion_cliente = pd.merge(facturacion_cliente, cantidad_facturas, on='Denominación Receptor')

            # Crear la columna "Promedio por Factura"
            facturacion_cliente["Promedio por Factura"] = (facturacion_cliente["Imp. Total"] / facturacion_cliente["Cantidad de Facturas"]).round(2)

            # Mostrar la facturación por cliente con formato
            st.dataframe(
                facturacion_cliente.style.format({
                    'Imp. Total': '${:,.2f}',
                    'Promedio por Factura': '${:,.2f}'
                }),
                hide_index=True
            )

        with col2:
            # Gráfico Top 10 clientes

            # Ordenar el DataFrame por 'Imp. Total' de mayor a menor y tomar el top 10
            top_10_clientes = facturacion_cliente.sort_values(by='Imp. Total', ascending=False).head(10)

            # Calcular el porcentaje que representa cada cliente respecto al total
            total_facturado = top_10_clientes['Imp. Total'].sum()
            top_10_clientes['Porcentaje'] = (top_10_clientes['Imp. Total'] / total_facturado) * 100

            # Crear el gráfico de barras con Plotly
            fig = px.bar(
                top_10_clientes,
                x='Denominación Receptor',
                y='Imp. Total',
                text=top_10_clientes['Porcentaje'].round(2).astype(str) + '%',  # Mostrar el porcentaje en las barras
                labels={'Imp. Total': 'Importe Total', 'Denominación Receptor': 'Cliente'},
                title='Top 10 Clientes por Facturación',
                hover_data={'Porcentaje': ':.2f%'},  # Mostrar el porcentaje en el hover
            )

            # Personalizar el gráfico
            fig.update_traces(textposition='outside')  # Mover el texto fuera de las barras
            fig.update_layout(
                xaxis_title='Cliente',
                yaxis_title='Importe Total',
                showlegend=False,  # No mostrar leyenda adicional
                template='plotly_white',  # Estilo del gráfico
            )

            # Mostrar el gráfico
            st.plotly_chart(fig)      

        # =============================================================================
        # Sección 10: Detalle de Facturas por Cliente
        # =============================================================================
        with st.expander("ℹ️ Detalle de Facturas por Cliente"):

            # Crear una lista de clientes únicos para el selectbox
            clientes_unicos = df_completo['Denominación Receptor'].unique().tolist()
            clientes_unicos.sort()  # Ordenar alfabéticamente

            # Agregar un selectbox para seleccionar el cliente
            cliente_seleccionado = st.selectbox(
                "Selecciona un cliente para ver sus facturas:",
                options=clientes_unicos,
                index=0  # Selecciona el primer cliente por defecto
            )

            # Filtrar el DataFrame por el cliente seleccionado
            facturas_cliente = df_completo[df_completo['Denominación Receptor'] == cliente_seleccionado]

            # Mostrar el DataFrame filtrado
            st.write(f"Facturas del cliente: **{cliente_seleccionado}**")
            st.dataframe(facturas_cliente)

            # Opcional: Mostrar un resumen de las facturas del cliente
            st.write(f"**Resumen de Facturas para {cliente_seleccionado}:**")
            st.write(f"- Total Facturado: ${facturas_cliente['Imp. Total'].sum():,.2f}")
            st.write(f"- Cantidad de Facturas: {len(facturas_cliente)}")

        # =============================================================================
        # Sección 11: Detalle de Notas de Crédito
        # =============================================================================

        # Filtrar solo las Notas de Crédito C (tipo '13')
        notas_de_credito = df_completo[df_completo['Tipo de Comprobante'] == 13]

        # Mostrar solo las Notas de Crédito C
        with st.expander("ℹ️ Detalle Notas de Crédito C"):
            st.write("Notas de Crédito C (tipo '13'):")
            if not notas_de_credito.empty:
                st.dataframe(notas_de_credito)
                total_notas_de_credito = notas_de_credito['Imp. Total'].sum()
                st.write(f"Total notas de crédito: **${total_notas_de_credito:,.2f}**")
            else:
                st.info("No hay notas de crédito en este período.")

        # =============================================================================
        # Sección 12: Resumen Final del Período de Recategorización
        # =============================================================================
        st.markdown("---")
        st.subheader("📋 Resumen del Período de Recategorización")

        # Creamos un DataFrame para el resumen con información dinámica
        periodo = f"{fecha_inicio_periodo.strftime('%d/%m/%Y')} - {fecha_fin_periodo.strftime('%d/%m/%Y')}"

        df_resumen = pd.DataFrame({
            'Métrica': [
                "Período Analizado",
                "Meses Cargados",
                "Próxima Recategorización",
                "Meses Restantes",
                "Categoría Actual",
                "Límite de Categoría",
                "Facturación Total Acumulada",
                "Facturación Máxima Mensual",
                "Margen Disponible",
                "Promedio Mensual Disponible",
                "Exceso de Facturación"
            ],
            'Valor': [
                periodo,
                f"{meses_cargados} meses",
                fecha_recategorizacion.strftime('%B %Y'),
                f"{meses_restantes} meses",
                categoria_actual,
                f"${limite_categoria_actual:,.2f}",
                f"${facturacion_total_12_meses:,.2f}",
                f"${facturacion_mensual_completa['Imp. Total'].max():,.2f}" if not facturacion_mensual_completa.empty else "$0.00",
                f"${margen_disponible:,.2f}",
                f"${promedio_mensual_disponible:,.2f}" if meses_restantes > 0 else "N/A",
                f"${exceso_facturacion:,.2f}" if exceso_facturacion > 0 else "$0.00"
            ]
        })

        # Mostramos la tabla de resumen
        st.table(df_resumen)

        # =============================================================================
        # Sección 13: Gráfico de Barras - Facturación por Mes con Proyección
        # =============================================================================
        st.markdown("---")
        st.subheader("📊 Análisis Visual: Facturación Mensual y Proyección")

        with st.container(border=True):
            # Crear DataFrame para el gráfico
            df_grafico = facturacion_mensual_completa[['Mes_Str', 'Imp. Total']].copy()
            df_grafico['Tipo'] = 'Facturación Real'

            # Si hay margen disponible y meses restantes, mostrar proyección
            if meses_restantes > 0 and promedio_mensual_disponible > 0:
                # Agregar meses proyectados
                import calendar

                meses_proyectados = []
                fecha_temp = fecha_fin_periodo

                for i in range(meses_restantes):
                    # Avanzar al siguiente mes
                    if fecha_temp.month == 12:
                        fecha_temp = datetime(fecha_temp.year + 1, 1, 1).date()
                    else:
                        fecha_temp = datetime(fecha_temp.year, fecha_temp.month + 1, 1).date()

                    mes_str = fecha_temp.strftime('%Y-%m')
                    meses_proyectados.append({
                        'Mes_Str': mes_str,
                        'Imp. Total': promedio_mensual_disponible,
                        'Tipo': 'Proyección (Promedio Disponible)'
                    })

                df_proyeccion = pd.DataFrame(meses_proyectados)
                df_grafico = pd.concat([df_grafico, df_proyeccion], ignore_index=True)

            # Crear gráfico de barras
            fig_barras = px.bar(
                df_grafico,
                x='Mes_Str',
                y='Imp. Total',
                color='Tipo',
                title=f'Facturación Mensual y Proyección hasta {fecha_recategorizacion.strftime("%B %Y")}',
                labels={'Imp. Total': 'Monto (ARS)', 'Mes_Str': 'Mes'},
                color_discrete_map={
                    'Facturación Real': '#1f77b4',
                    'Proyección (Promedio Disponible)': '#ff7f0e'
                },
                barmode='group'
            )

            # Agregar línea horizontal del límite promedio
            if meses_restantes > 0:
                fig_barras.add_hline(
                    y=promedio_mensual_disponible,
                    line_dash="dash",
                    line_color="red",
                    annotation_text=f"Promedio Mensual Disponible: ${promedio_mensual_disponible:,.0f}",
                    annotation_position="right"
                )

            fig_barras.update_layout(
                xaxis_tickangle=-45,
                height=500,
                showlegend=True,
                legend=dict(
                    orientation="h",
                    yanchor="bottom",
                    y=1.02,
                    xanchor="right",
                    x=1
                )
            )

            st.plotly_chart(fig_barras, use_container_width=True)

            # Explicación
            if meses_restantes > 0:
                st.info(f"""
                📊 **Interpretación del gráfico:**
                - **Barras azules**: Facturación real de los meses cargados ({meses_cargados} meses)
                - **Barras naranjas**: Proyección del promedio mensual disponible para los próximos {meses_restantes} meses
                - **Línea roja punteada**: Límite promedio que puedes facturar por mes sin exceder tu categoría

                💡 Si las barras naranjas están por debajo o al nivel de la línea roja, estás dentro del margen seguro.
                """)

    else:
        st.warning("Por favor, sube el archivo CSV con 12 meses de facturación para ver el análisis.")

if __name__ == "__main__":
    main()
