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
    calcular_tasa_crecimiento_promedio_mensual
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

# Función de ETL
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
        facturacion_mensual = df.groupby('Mes')['Imp. Total'].sum().reset_index()
        facturacion_mensual['Mes'] = facturacion_mensual['Mes'].dt.to_timestamp()
        facturacion_mensual['Mes'] = facturacion_mensual['Mes'].dt.strftime('%Y-%m')
        facturacion_mensual['Acumulado'] = facturacion_mensual['Imp. Total'].cumsum()
 
        return df, facturacion_mensual
    else:
        # Devuelve DataFrames vacíos si no se subió ningún archivo
        return pd.DataFrame(), pd.DataFrame()

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

        1. Ingresa con Clave Fiscal en [ARCA]:(https://auth.afip.gob.ar/contribuyente_/login.xhtml)
        2. Descarga tu archivo de facturación en formato CSV desde el servicio Mis Comprobantes -> Emitidos
        3. Selecciona el rango de los últimos 12 meses. Ejemplo: 01/01/2024 - 31/12/2024
        4. Sube el archivo CSV
        5. Ingresa el nombre del contribuyente y la categoría actual
        6. Aplica Enter y obtén instantáneamente un análisis detallado de tu situación fiscal
        """)

    # =============================================================================
    # Sección 3: Ingreso de datos
    # =============================================================================
    st.subheader("Ingreso de datos: ")

    # Usamos st.columns para crear tres columnas
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        contribuyente = st.text_input("Nombre del Contribuyente", "")

    with col2:
        categorias = {
            'A': 7813063.45, 'B': 11447046.44, 'C': 16050091.57, 'D': 19926340.10, 
            'E': 23439190.34, 'F': 29374695.90, 'G': 35128502.31, 'H': 53298417.30, 
            'I': 59657887.55, 'J': 68318880.36, 'K': 82370281.28
        }
        categoria_actual = st.selectbox("Selecciona tu categoría actual", options=list(categorias.keys()))

    with col3:
        uploaded_file = st.file_uploader("Sube tu archivo CSV de los últimos 12 meses", type="csv")

    with col4:
        uploaded_file_2 = st.file_uploader("Sube tu archivo CSV del periodo anterior", type="csv")

    # Procesamos los csv
    df_actual, facturacion_mensual_actual = procesar_csv(uploaded_file)
    df_anterior, facturacion_mensual_anterior= procesar_csv(uploaded_file_2)

    # Verificamos si los archivos CSV han sido cargados
    if uploaded_file is not None and uploaded_file_2 is not None:

        # =============================================================================
        # Sección 4: Cálculo de Métricas y KPIs
        # =============================================================================        

        if not facturacion_mensual_actual.empty:
            facturacion_total_actual, facturacion_promedio_mensual_actual, tasa_crecimiento_promedio_actual = calcular_kpis(facturacion_mensual_actual)
            facturacion_acumulada_actual = facturacion_mensual_actual['Acumulado'].iloc[-1]  # Último valor de la columna 'Acumulado'
        else:
            facturacion_total_actual, facturacion_promedio_mensual_actual, tasa_crecimiento_promedio_actual = 0, 0, 0
            facturacion_acumulada_actual = 0

        if not facturacion_mensual_anterior.empty:
            facturacion_total_anterior, facturacion_promedio_mensual_anterior, tasa_crecimiento_promedio_anterior = calcular_kpis(facturacion_mensual_anterior)
        else:
            facturacion_total_anterior, facturacion_promedio_mensual_anterior, tasa_crecimiento_promedio_anterior = 0, 0, 0

        # Obtenemos el límite de la categoría actual
        limite_categoria_actual = categorias[categoria_actual]

        # Calculamos la facturación disponible
        facturacion_disponible = max(0, limite_categoria_actual - facturacion_acumulada_actual)
        exceso_facturacion = max(0, facturacion_acumulada_actual - limite_categoria_actual)


        # =============================================================================
        # Sección 5: Métricas de Facturación
        # =============================================================================

        st.subheader("Métricas de Facturación")

        col1, col2, col3, col4 = st.columns(4)

        # Tarjeta 1: Facturación Total
        with col1:
            ui.metric_card(
                title="Facturación Total",
                content=f"${facturacion_total_actual:,.2f}",
                description="Total facturado en el período",
                key="card4"
            )

        # Tarjeta 2: Facturación Promedio Mensual
        with col2:
            ui.metric_card(
                title="Facturación Promedio Mensual",
                content=f"${facturacion_promedio_mensual_actual:,.2f}",
                description="Promedio de facturación mensual",
                key="card5"
            )

        # Tarjeta 3: Tasa de Crecimiento Promedio Mensual
        with col3:
            ui.metric_card(
                title="Tasa de Crecimiento Promedio Mensual",
                content=f"{tasa_crecimiento_promedio_actual:.2f}%",
                description="Crecimiento promedio mensual en 12 meses",
                key="card6"
            )   

        # Tarjeta 4: Margen de facturación
        with col4:
            ui.metric_card(
                title="Margen de facturación",
                content=f"${facturacion_disponible:,.2f}",
                description=f"Margen disponible a facturar para la categoría {categoria_actual}",
                key="card7"
            )

        # =============================================================================
        # Sección 6: Gráfico facturación anual + Alerta y margen de facturación
        # =============================================================================

        with st.container(border=True):
            bar_height = 0.3  # Puedes ajustar este valor para hacer la barra más plana

            fig_acumulado = px.bar(x=[facturacion_acumulada_actual], 
                                y=['Facturación Acumulada'], 
                                orientation='h',
                                title=f'Facturación Acumulada vs Límite de Categoría {categoria_actual}',
                                labels={'x': 'Monto', 'y': ''},
                                text=[f"${facturacion_acumulada_actual:,.2f}"],
                                height=300)  # Altura del gráfico

            # Ajustamos el ancho de la barra
            fig_acumulado.update_traces(marker=dict(line=dict(width=0)),  # Sin borde en la barra
                                        width=bar_height)  # Ajustamos la altura de la barra

            # Añadimos la línea vertical para el límite de categoría
            fig_acumulado.add_vline(x=limite_categoria_actual, line_dash="dash", line_color="red", 
                                    annotation_text=f"Límite Categoría {categoria_actual}", 
                                    annotation_position="top right")

            # Personalizamos el diseño del gráfico
            fig_acumulado.update_layout(
                showlegend=False,  # Ocultamos la leyenda
                xaxis=dict(title='Monto'),  # Título del eje X
                yaxis=dict(showticklabels=False),  # Ocultamos las etiquetas del eje Y
                plot_bgcolor='rgba(0,0,0,0)',  # Fondo transparente
                margin=dict(l=20, r=20, t=40, b=20)  # Ajustamos los márgenes
            )

            # Mostramos el gráfico en Streamlit
            st.plotly_chart(fig_acumulado)

        # =============================================================================
        # Sección 7: Gráfico de Facturación mensual + Tabla
        # =============================================================================

        with st.container(border=True):
            col1, col2= st.columns([3,1])
            with col1:     
                # Creamos el gráfico de facturación mensual con Plotly
                fig_mensual = px.bar(facturacion_mensual_actual, x='Mes', y='Imp. Total', 
                                        title=f'Facturación Mensual - {contribuyente}',
                                        labels={'Imp. Total': 'Facturación Mensual', 'Mes': 'Fecha'})
                st.plotly_chart(fig_mensual)

                # Calculamos el período
                fecha_inicio = facturacion_mensual_actual['Mes'].min()
                fecha_fin = facturacion_mensual_actual['Mes'].max()
                periodo = f"{fecha_inicio} a {fecha_fin}"

            with col2:
                # Mostrar la facturación mensual
                st.write("Facturación mensual (agrupada por mes):")
                st.write(facturacion_mensual_actual)

                # Verificamos si hay exceso de facturación
                if facturacion_acumulada_actual > limite_categoria_actual:
                    # Ordenamos las categorías por su límite de facturación
                    categorias_ordenadas = sorted(categorias.items(), key=lambda x: x[1])
                    
                    # Encontramos la categoría más alta que no sea excedida por la facturación acumulada
                    categoria_encuadre = None
                    for cat, limite in categorias_ordenadas:
                        if facturacion_acumulada_actual <= limite:
                            categoria_encuadre = cat
                            break
                    
                    # Si no se encuentra una categoría válida, el contribuyente excede todas las categorías
                    if categoria_encuadre:
                        st.error(f"**Alerta! Exceso de facturación.** Con la facturación actual, queda encuadrado en la **Categoría {categoria_encuadre}**.")
                    else:
                        st.error("**Alerta! Exceso de facturación.** No hay una categoría superior disponible.")
            

        # =============================================================================
        # Sección 8: Cuadro de facturación agrupada por cliente + Gráfico
        # =============================================================================

        st.subheader("Facturación por cliente")

        # Cantidad de clientes
        num_receptores_unicos = df_actual['Denominación Receptor'].nunique()
        st.write(f"Número de clientes únicos en el año: {num_receptores_unicos}")

        col1, col2 = st.columns([1,1.5])
        
        with col1:
            # Agrupación por cliente y recuento de facturas
            facturacion_cliente = df_actual.groupby('Denominación Receptor')['Imp. Total'].sum().reset_index()
            cantidad_facturas = df_actual.groupby('Denominación Receptor').size().reset_index(name='Cantidad de Facturas')
            facturacion_cliente = pd.merge(facturacion_cliente, cantidad_facturas, on='Denominación Receptor')

            # Crear la columna "Promedio por Factura"
            facturacion_cliente["Promedio por Factura"] = (facturacion_cliente["Imp. Total"] / facturacion_cliente["Cantidad de Facturas"]).round(2)

            # Mostrar la facturación por cliente
            st.write(facturacion_cliente)

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
        # Sección 8.1: Detalle de Facturas por Cliente
        # =============================================================================
        with st.expander("ℹ️ Detalle de Facturas por Cliente"):

            # Crear una lista de clientes únicos para el selectbox
            clientes_unicos = df_actual['Denominación Receptor'].unique().tolist()
            clientes_unicos.sort()  # Ordenar alfabéticamente

            # Agregar un selectbox para seleccionar el cliente
            cliente_seleccionado = st.selectbox(
                "Selecciona un cliente para ver sus facturas:",
                options=clientes_unicos,
                index=0  # Selecciona el primer cliente por defecto
            )

            # Filtrar el DataFrame por el cliente seleccionado
            facturas_cliente = df_actual[df_actual['Denominación Receptor'] == cliente_seleccionado]

            # Mostrar el DataFrame filtrado
            st.write(f"Facturas del cliente: **{cliente_seleccionado}**")
            st.dataframe(facturas_cliente)

            # Opcional: Mostrar un resumen de las facturas del cliente
            st.write(f"**Resumen de Facturas para {cliente_seleccionado}:**")
            st.write(f"- Total Facturado: ${facturas_cliente['Imp. Total'].sum():,.2f}")
            st.write(f"- Cantidad de Facturas: {len(facturas_cliente)}")        

        # =============================================================================
        # Sección 9: Detalle de Notas de Crédito 
        # =============================================================================

        # Filtrar solo las Notas de Crédito C (tipo '13')
        notas_de_credito = df_actual[df_actual['Tipo de Comprobante'] == 13]

        # Mostrar solo las Notas de Crédito C
        with st.expander("ℹ️ Detalle Notas de Crédito C"):
            st.write("Notas de Crédito C (tipo '13'):")
            st.write(notas_de_credito)
            total_notas_de_credito = notas_de_credito['Imp. Total'].sum()
            st.write(f"Total notas de credito: $ {total_notas_de_credito:,.2f}")

        # =============================================================================
        # Sección 10: Ingreso de KPIs objetivo
        # =============================================================================
        st.divider()
        st.subheader("Objetivos de Facturación")

        with st.expander("**Configurar Objetivos de Facturación**", expanded=False):
        
            # Input para que el usuario ingrese el porcentaje objetivo
            porcentaje_objetivo = st.number_input(
                "Porcentaje de crecimiento objetivo (%)",
                min_value=0.0,  # El porcentaje no puede ser negativo
                max_value=1000.0,  # Límite máximo del 1000% para evitar valores absurdos
                value=10.0,  # Valor predeterminado del 10%
                step=1.0,  # Incrementos de 1%
                format="%.2f"  # Formato con dos decimales
            )    
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Calcular el objetivo de facturación total basado en el porcentaje ingresado
                objetivo_facturacion_total = facturacion_total_anterior * (1 + porcentaje_objetivo / 100)

                # Mostrar el valor objetivo en formato de moneda
                st.write(f"**Objetivo de Facturación Total:** ${objetivo_facturacion_total:,.2f}")
                
            with col2:
                # Objetivo de Facturación Mensual Promedio: 10% más que el promedio del año anterior
                objetivo_facturacion_mensual = objetivo_facturacion_total / 12

                st.write(f"**Objetivo de Facturación Mensual Promedio:** ${objetivo_facturacion_mensual:,.2f}")
            
            with col3:
                # Checkbox para elegir entre calcular automáticamente o ingresar manualmente la tasa de crecimiento
                calcular_tasa_automaticamente = st.checkbox("Calcular tasa automáticamente", value=True)

                if calcular_tasa_automaticamente:
                    # Calcular la tasa de crecimiento mensual con crecimiento compuesto
                    objetivo_tasa_crecimiento_promedio = ((objetivo_facturacion_total / facturacion_total_anterior) ** (1 / 12)) - 1
                    st.write(f"**Objetivo de Tasa de Crecimiento Promedio Mensual:** {objetivo_tasa_crecimiento_promedio * 100:.2f}%")
                else:
                    # Permitir al usuario ingresar manualmente la tasa de crecimiento mensual
                    objetivo_tasa_crecimiento_promedio = st.number_input(
                        "Objetivo de Tasa de Crecimiento Mensual (%)",
                        min_value=-100.0,
                        max_value=1000.0,
                        value=5.0,  
                        step=1.0,
                        format="%.2f"
                    )

                
            st.info("Estos objetivos se utilizarán para comparar con los resultados actuales.")

        # Calcular cumplimiento de objetivos
        cumplimiento_facturacion_total = (facturacion_total_actual / objetivo_facturacion_total) * 100
        cumplimiento_facturacion_mensual = (facturacion_promedio_mensual_actual / objetivo_facturacion_mensual)  * 100
        cumplimiento_tasa_crecimiento_promedio = (tasa_crecimiento_promedio_actual / objetivo_tasa_crecimiento_promedio) * 100 if objetivo_tasa_crecimiento_promedio != 0 else 0

        # Función para determinar el color según el cumplimiento
        def get_color(cumplimiento):
            if cumplimiento >= 100:
                return "green"
            elif cumplimiento >= 85:
                return "orange"
            else:
                return "red"

        st.divider()

        # =============================================================================
        # Sección 11: Facturación Actual vs Objetivos
        # =============================================================================
        st.subheader("Comparación de Facturación Actual vs Objetivos")

        # Usamos st.columns para crear tres columnas
        col1, col2, col3 = st.columns(3)

        # Tarjeta 1: Facturación Total
        with col1:
            ui.metric_card(
                title="Facturación Total",
                content=f"${facturacion_total_actual:,.2f}",
                description=f"Objetivo: ${objetivo_facturacion_total:,.2f} ({cumplimiento_facturacion_total:.1f}%)",  # Aquí se usa el cálculo corregido
                key="card1",
            )

        # Tarjeta 2: Facturación Promedio Mensual
        with col2:
            ui.metric_card(
                title="Facturación Promedio Mensual",
                content=f"${facturacion_promedio_mensual_actual:,.2f}",
                description=f"Objetivo: ${objetivo_facturacion_mensual:,.2f} ({cumplimiento_facturacion_mensual:.1f}%)",  # Cálculo corregido
                key="card2",
            )

        # Tarjeta 3: Tasa de Crecimiento 
        with col3:
            ui.metric_card(
                title="Tasa de Crecimiento Promedio Mensual",
                content=f"{tasa_crecimiento_promedio_actual:.2f}%",
                description=f"Objetivo: {objetivo_tasa_crecimiento_promedio:.2f}% ({cumplimiento_tasa_crecimiento_promedio:.1f}%)",  # Cálculo corregido
                key="card3",
            )

        with st.container(border=True):

            col1, col2 = st.columns([3,1])
            # Datos para los gráficos
            df_comparacion_montos = pd.DataFrame({
                'KPI': ['Facturación Total', 'Facturación Mensual Promedio'],
                'Actual': [facturacion_total_actual, facturacion_promedio_mensual_actual],
                'Objetivo': [objetivo_facturacion_total, objetivo_facturacion_mensual]
            })

            df_comparacion_tasa = pd.DataFrame({
                'KPI': ['Tasa de Crecimiento Promedio Mensual (%)'],
                'Actual': [tasa_crecimiento_promedio_actual],
                'Objetivo': [objetivo_tasa_crecimiento_promedio]
            })

            # Gráfico para montos (USD)
            fig_comparacion_montos = px.bar(
                df_comparacion_montos, 
                x='KPI', 
                y=['Actual', 'Objetivo'],
                barmode='group',
                title='Facturación Actual vs Objetivos (Montos)',
                labels={'value': 'Pesos', 'variable': ''},
                text_auto=",.2f"  # Formato numérico
            )

            # Gráfico para tasa de crecimiento (%)
            fig_comparacion_tasa = px.bar(
                df_comparacion_tasa, 
                x='KPI', 
                y=['Actual', 'Objetivo'],
                barmode='group',
                title='Tasa de Crecimiento vs Objetivo',
                labels={'value': '%', 'variable': ''},
                text_auto=".2f"  # Formato porcentual
            )

            # Mostrar ambos gráficos
            with col1:
                st.plotly_chart(fig_comparacion_montos)
            with col2:
                st.plotly_chart(fig_comparacion_tasa)

        # =============================================================================
        # Sección 12: Gráfico de comparación mensual (Estacionalidad)
        # =============================================================================
        st.divider()
        st.subheader("Comparación Mensual: Año Actual vs Año Anterior")

        # Verificar si hay datos para ambos años
        if not facturacion_mensual_actual.empty and not facturacion_mensual_anterior.empty:
            # Agregar columna identificadora de año
            facturacion_mensual_actual['Año'] = 'Año Actual'
            facturacion_mensual_anterior['Año'] = 'Año Anterior'
            
            # Unir los DataFrames
            facturacion_comparativa = pd.concat([facturacion_mensual_actual, facturacion_mensual_anterior])

            # Asegurar que la columna 'Mes' es de tipo string
            facturacion_comparativa['Mes'] = facturacion_comparativa['Mes'].astype(str)

            # Convertir 'Mes' de '2024-01' a 'Enero'
            facturacion_comparativa['Mes'] = pd.to_datetime(facturacion_comparativa['Mes'], format="%Y-%m").dt.strftime("%B")

            # Ordenar los meses en español correctamente
            meses_orden = [
                "enero", "febrero", "marzo", "abril", "mayo", "junio",
                "julio", "agosto", "septiembre", "octubre", "noviembre", "diciembre"
            ]

            facturacion_comparativa['Mes'] = pd.Categorical(
                facturacion_comparativa['Mes'].str.lower(), 
                categories=meses_orden, 
                ordered=True
            )

            # Crear gráfico con líneas sobrepuestas
            fig_comparacion_mensual = px.line(
                facturacion_comparativa,
                x='Mes',
                y='Imp. Total',
                color='Año',  # Diferenciar líneas por año
                labels={'Imp. Total': 'Facturación Mensual', 'Mes': 'Mes'},
                markers=True,  # Añadir marcadores para cada punto
                line_shape='linear'  # Líneas rectas entre puntos
            )

            # Personalizar el gráfico
            fig_comparacion_mensual.update_layout(
                xaxis_title='Mes',
                yaxis_title='Facturación Mensual',
                legend_title='Año',
                template='plotly_white',  # Estilo limpio del gráfico
                hovermode='x unified'  # Mostrar info de ambas líneas al pasar el mouse
            )

            # Mostrar el gráfico
            st.plotly_chart(fig_comparacion_mensual)
        else:
            st.warning("No hay suficientes datos para comparar la facturación mensual entre años.")


        # =============================================================================
        # Sección 13: Resumen Final
        # =============================================================================

        # Añadimos un resumen de la facturación
        st.subheader(f"Resumen de Facturación del período {periodo}")
        resumen = {
            "Facturación Total": facturacion_mensual_actual['Imp. Total'].sum(),
            "Facturación Máxima Mensual": facturacion_mensual_actual['Imp. Total'].max(),
            "Límite de Categoría Actual": limite_categoria_actual,
            "Exceso de Facturación": exceso_facturacion,
            "Facturación Disponible": facturacion_disponible
        }
        
         # Calculamos el período
        fecha_inicio = facturacion_mensual_actual['Mes'].min()
        fecha_fin = facturacion_mensual_actual['Mes'].max()
        periodo = f"{fecha_inicio} a {fecha_fin}"

        # Creamos un DataFrame para el resumen
        df_resumen = pd.DataFrame({
            'Métrica': [
            "Facturación Total",
            "Facturación Máxima Mensual",
            "Límite de Categoría Actual",
            "Exceso de Facturación",
            "Facturación Disponible"
        ],
        'Valor': [
            f"${facturacion_mensual_actual['Imp. Total'].sum():,.2f}",
            f"${facturacion_mensual_actual['Imp. Total'].max():,.2f}",
            f"${limite_categoria_actual:,.2f}",
            f"${exceso_facturacion:,.2f}",
            f"${facturacion_disponible:,.2f}"
        ]
        })


        # Mostramos la tabla de resumen
        st.table(df_resumen)

        # Añadir KPIs comparativos como tabla
        st.subheader("Comparativa con Objetivos")

        # Función para determinar el estado basado en el cumplimiento
        def get_estado(cumplimiento):
            if cumplimiento >= 100:
                return "✅ Cumplido"
            elif cumplimiento >= 85:
                return "⚠️ Cerca"
            else:
                return "❌ No cumplido"


        # Creamos un DataFrame para la comparativa
        df_comparativa = pd.DataFrame({
            'Métrica': [
                "Facturación Total",
                "Facturación Promedio Mensual",
                "Tasa de Crecimiento Promedio Mensual"
                ],
            'Valor Actual': [
                f"${facturacion_total_actual:,.2f}",
                f"${facturacion_promedio_mensual_actual:,.2f}",
                f"{tasa_crecimiento_promedio_actual:.2f}%"
            ],
            'Objetivo': [
                f"${objetivo_facturacion_total:,.2f}",
                f"${objetivo_facturacion_mensual:,.2f}",
                f"{objetivo_tasa_crecimiento_promedio:.2f}%"
            ],
            'Cumplimiento': [
                f"{cumplimiento_facturacion_total:.2f}%",
                f"{cumplimiento_facturacion_mensual:.2f}%",
                f"{cumplimiento_tasa_crecimiento_promedio:.2f}%"
            ],
            'Estado': [
                get_estado(cumplimiento_facturacion_total),
                get_estado(cumplimiento_facturacion_mensual),
                get_estado(cumplimiento_tasa_crecimiento_promedio)
            ]
        })

        # Mostramos la tabla de comparativa
        st.table(df_comparativa)

        # =============================================================================
        # Sección 14: Análisis de Brecha
        # =============================================================================

        # Opcionalmente, podemos añadir un análisis de brecha
        st.subheader("Análisis de Brecha")

        # Calcular las brechas absolutas
        brecha_facturacion_total = objetivo_facturacion_total - facturacion_total_actual
        brecha_facturacion_mensual = objetivo_facturacion_mensual - facturacion_promedio_mensual_actual
        brecha_tasa_crecimiento_promedio = objetivo_tasa_crecimiento_promedio - tasa_crecimiento_promedio_actual

        # Crear DataFrame para el análisis de brecha
        df_brecha = pd.DataFrame({
            'Métrica': [
            "Brecha Facturación Total",
            "Brecha Facturación Mensual",
            "Brecha Tasa de Crecimiento Promedio Mensual"
        ],
            'Valor': [
            f"${brecha_facturacion_total:,.2f}",
            f"${brecha_facturacion_mensual:,.2f}",
            f"{brecha_tasa_crecimiento_promedio:.2f}%"
        ],
            'Interpretación': [
            "Faltante para alcanzar el objetivo" if brecha_facturacion_total > 0 else "Superávit sobre el objetivo",
            "Faltante mensual promedio" if brecha_facturacion_mensual > 0 else "Superávit mensual promedio", 
            "Crecimiento adicional necesario" if brecha_tasa_crecimiento_promedio > 0 else "Crecimiento por encima del objetivo"
        ]
        })

        # Mostrar la tabla de brechas
        st.table(df_brecha)

    else:
        st.warning("Por favor, sube los archivos CSV para ver la información.")

if __name__ == "__main__":
    main()
