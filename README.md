# 📊 Calculadora de Monotributo ARCA

> **Herramienta gratuita para monotributistas argentinos**: Analizá tu facturación, evitá excederte de categoría y planificá hasta la próxima recategorización.

[![Streamlit](https://img.shields.io/badge/Streamlit-FF4B4B?style=for-the-badge&logo=Streamlit&logoColor=white)](https://streamlit.io/)
[![Python](https://img.shields.io/badge/Python-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg?style=for-the-badge)](https://opensource.org/licenses/MIT)

## 🌐 Probala Online (sin instalar nada)

👉 **[https://monotributoarca1.streamlit.app/](https://monotributoarca1.streamlit.app/)**

---

## 🎯 ¿Para qué sirve?

Si sos **monotributista en Argentina**, esta aplicación te ayuda a:

✅ **Controlar tu facturación** en tiempo real
✅ **Evitar excederte** del límite de tu categoría
✅ **Calcular cuánto podés facturar** hasta la próxima recategorización (Enero o Julio)
✅ **Simular escenarios** de facturación proyectada
✅ **Identificar tus mejores clientes** y concentración de ingresos
✅ **Exportar reportes en PDF** profesionales

---

## 🚀 Funcionalidades

### 📈 Análisis de Recategorización
- Cálculo automático del **período de recategorización semestral** (Enero/Julio)
- **Meses restantes** hasta la próxima evaluación
- **Margen disponible** en tu categoría actual
- **Promedio mensual** que podés facturar sin excederte

### 🎨 Visualizaciones Inteligentes
- Gráfico de facturación acumulada vs límites de categoría
- Facturación mensual con proyección de meses restantes
- Top 10 clientes por facturación
- Análisis de notas de crédito

### ⚠️ Alertas Proactivas
- **Alerta roja**: Si ya excediste tu categoría
- **Alerta naranja**: Si estás al 80%+ del límite
- **Recomendaciones**: Cuánto reducir la facturación mensual si es necesario

### 📄 Exportación
- Reporte completo en **PDF** con todos los análisis

---

## 🛠️ Instalación

### Requisitos previos
- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Paso a paso

1. **Clonar el repositorio**
```bash
git clone https://github.com/Adlazz/monotributo_arca1.git
cd monotributo_arca1
```

2. **Crear entorno virtual (recomendado)**
```bash
python -m venv venv

# En Windows
venv\Scripts\activate

# En macOS/Linux
source venv/bin/activate
```

3. **Instalar dependencias**
```bash
pip install -r requirements.txt
```

4. **Ejecutar la aplicación**
```bash
streamlit run app.py
```

5. **Abrir en el navegador**
```
La app se abrirá automáticamente en http://localhost:8501
```

---

## 📥 Cómo usar

### 1. Descargar tu archivo CSV desde ARCA

1. Ingresá con **Clave Fiscal** en [ARCA](https://auth.afip.gob.ar/contribuyente_/login.xhtml)
2. Andá a **Mis Comprobantes → Emitidos**
3. **Importante**: Descargá el período de **12 meses** para la recategorización:

   **Ejemplo 1**: Estás en **Marzo 2026** (próxima recategorización: Julio 2026)
   - Descargá desde **01/07/2025** hasta **31/03/2026** (9 meses)
   - La app calculará que faltan **3 meses** (Abril, Mayo, Junio)

   **Ejemplo 2**: Estás en **Octubre 2025** (próxima recategorización: Enero 2026)
   - Descargá desde **01/01/2025** hasta **31/10/2025** (10 meses)
   - La app calculará que faltan **2 meses** (Noviembre, Diciembre)

4. Guardá el archivo en formato **CSV**

### 2. Usar la aplicación

1. Subí el archivo CSV
2. Ingresá tu nombre y categoría actual (A-K)
3. ¡Listo! Obtené tu análisis completo

---

## 📊 Capturas de pantalla

### Dashboard principal
![Dashboard](https://via.placeholder.com/800x400?text=Dashboard+Principal)

### Análisis por cliente
![Clientes](https://via.placeholder.com/800x400?text=Analisis+por+Cliente)

### Proyección de facturación
![Proyección](https://via.placeholder.com/800x400?text=Proyeccion+Facturacion)

---

## 🧮 Límites de categorías (vigentes Abril 2026)

| Categoría | Límite Anual de Facturación |
|-----------|------------------------------|
| A         | $10.277.988,13              |
| B         | $15.058.447,71              |
| C         | $21.113.696,52              |
| D         | $26.212.853,42              |
| E         | $30.833.964,37              |
| F         | $38.642.048,36              |
| G         | $46.288.359,82              |
| H         | $70.185.003,97              |
| I         | $78.570.820,99              |
| J         | $89.946.653,09              |
| K         | $108.357.084,05             |

---

## 🎓 Cómo funciona la recategorización

La **recategorización en ARCA** se realiza **SEMESTRALMENTE**:

- **Recategorización de ENERO**: evalúa facturación de **Enero a Diciembre** del año anterior (12 meses)
- **Recategorización de JULIO**: evalúa facturación de **Julio (año anterior) a Junio (año actual)** (12 meses)

**Clave**: Siempre cargar desde el **inicio del período anual** (Julio o Enero) hasta la fecha actual.

---

## 🤝 ¿Sos contador o tenés un estudio contable?

Si manejás múltiples clientes monotributistas y te interesa una **versión enterprise** con:
- Dashboard multi-cliente
- Carga batch de múltiples CSVs
- Alertas automáticas por email
- White-label (tu marca)

**Contactame**: [adrianlazzarini@gmail.com](mailto:adrianlazzarini@gmail.com)

---

## 🛠️ Tecnologías utilizadas

- **[Streamlit](https://streamlit.io/)**: Framework web interactivo
- **[Pandas](https://pandas.pydata.org/)**: Procesamiento de datos
- **[Plotly](https://plotly.com/)**: Visualizaciones interactivas
- **[FPDF2](https://pyfpdf.github.io/fpdf2/)**: Generación de PDFs
- **[Streamlit Shadcn UI](https://github.com/ObservedObserver/streamlit-shadcn-ui)**: Componentes UI modernos

---

## 📝 Estructura del proyecto

```
monotributo_arca1/
├── app.py                 # Aplicación principal Streamlit
├── calculos.py           # Lógica de cálculos de monotributo
├── local_components.py   # Componentes UI personalizados
├── requirements.txt      # Dependencias del proyecto
└── README.md            # Este archivo
```

---

## 🤔 Preguntas frecuentes

### ¿Es gratis?
Sí, 100% gratis y open source.

### ¿Mis datos están seguros?
Sí, todo se procesa **localmente** en tu navegador. No se envía ningún dato a servidores externos.

**Nota**: Si usás la versión online en Streamlit Cloud, los datos se procesan en su servidor pero no se almacenan. Para máxima privacidad, instalá la app localmente.

### ¿Puedo contribuir al proyecto?
¡Por supuesto! Pull requests son bienvenidos. Para cambios grandes, abrí primero un issue para discutir qué te gustaría cambiar.

### ¿Qué pasa si encuentro un bug?
Abrí un [issue en GitHub](https://github.com/Adlazz/monotributo_arca1/issues) con el detalle del problema.

---

## 📹 Video tutorial

¿Preferís ver cómo funciona antes de instalar?

👉 **[Ver tutorial completo en YouTube](#)** (próximamente)

---

## 🗺️ Roadmap

### ✅ Versión actual (v1.0)
- [x] Análisis de facturación mensual
- [x] Cálculo de recategorización semestral
- [x] Exportación a PDF
- [x] Análisis por cliente

### 🔜 Próximas versiones
- [ ] Modo oscuro
- [ ] Integración con API de ARCA (si está disponible)
- [ ] Alertas por email
- [ ] Comparación de períodos históricos
- [ ] Predicción con IA de facturación futura
- [ ] App móvil

---

## 📄 Licencia

[MIT](https://choosealicense.com/licenses/mit/)

---

## ⭐ ¿Te resultó útil?

Si esta herramienta te ayudó, **dejá una estrella ⭐** en GitHub y **compartila** con otros monotributistas.

---

## 👨‍💻 Autor

**Adrian Lazzarini** - [GitHub](https://github.com/Adlazz) | [LinkedIn](https://www.linkedin.com/in/adrian-lazzarini)

---

## 🙏 Agradecimientos

A la comunidad de monotributistas argentinos que inspiran este proyecto.

---

**¿Preguntas? ¿Sugerencias?** Abrí un issue o contactame directamente.
