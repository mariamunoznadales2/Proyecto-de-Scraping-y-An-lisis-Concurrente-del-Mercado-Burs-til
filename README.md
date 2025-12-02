# Proyecto de Scraping y Análisis Concurrente del Mercado Bursátil

## 1. ¿De qué va este trabajo?

Este proyecto simula un sistema completo que analiza empresas de la bolsa española a partir de información real obtenida de **CincoDías (El País)**.  
El objetivo es:

- Descargar **cotizaciones** del índice IGBM.
- Descargar **datos financieros** de varias empresas del mercado español.
- Combinar ambos conjuntos de datos.
- Realizar un **análisis financiero concurrente** (usando hilos).
- Generar recomendaciones de inversión (Comprar / Mantener / Vender).
- Guardar los resultados en formatos CSV y Excel.

Además, este proyecto sirve como **aplicación práctica de Concurrencia en Python**.

---

## 2. ¿Qué hace el programa?

### ✦ Fase 1 — Scraping de cotizaciones
- Entra en la página del IGBM.
- Localiza la tabla *Principales valores*.
- Extrae precios, variaciones, máximos, mínimos y fecha/hora.
- Convierte el formato español (‘10,50’) a números Python.
- Guarda un CSV → `raw/cotizaciones/`.

(No usa hilos. Es la fase base sobre la que se construyen las demás.)

---

### ✦ Fase 2 — Scraping financiero **CON HILOS**
Para cada empresa seleccionada:

- Descarga su ficha desde CincoDías.
- Encuentra la tabla *Resumen financiero*.
- Extrae:
  - ingresos  
  - EBITDA  
  - beneficio neto  
  - deuda neta  
  - BPA  
  - PER  
- Guarda la información en una **base de datos SQLite**.

Aquí se aplican varios conceptos del Tema 7:
- `threading.Thread` → un hilo por empresa  
- `Semaphore` → limita cuántos hilos trabajan simultáneamente  
- `Lock` → protege la escritura en la BD y evita condiciones de carrera  

Resultado:  
La BD final queda en → `raw/finanzas/finanzas_empresas.db`.

---

### ✦ Fase 3 — Análisis financiero **CON HILOS**

El programa une:

- las cotizaciones del CSV, y  
- los datos financieros de la base de datos.

Luego lanza **varios hilos**, cada uno encargado de una parte del análisis:

1. **Cálculo de ratios financieros**
   - deuda/EBITDA  
   - EBITDA/beneficio  

2. **Clasificación de señales**
   - PER → barato / medio / caro  
   - BPA → bajo / medio / alto  

3. **Recomendación de inversión realista**
   - Si PER es barato y BPA alto → Comprar  
   - Si PER alto y BPA bajo → Vender  
   - En empresas grandes, lo más habitual es Mantener (realismo financiero).

4. **Generación de resultados**
   - `processed/dataset_unido.csv`
   - `analysis/analisis_resultados_YYYYMMDD.csv`
   - `analysis/analisis_resultados.xlsx`

---

## 3. Estructura del proyecto



proyecto_bolsa_concurrencia/

├── src/

│   ├── scraping_cotizacion.py
│   ├── scraping_finanzas.py
│   ├── analisis.py
│   ├── main.py

├── raw/

│   ├── cotizaciones/
│   └── finanzas/          

├── processed/

│   ├── dataset_unido.csv

├── analysis/

│   ├── analisis_resultados_YYYYMMDD.csv
│   └── analisis_resultados.xlsx

├── logs/

│   ├── cotizaciones.log
│   ├── finanzas.log
│   ├── analisis.log


└── README.md



---

## 4. Explicación de cada archivo

### ▶ `scraping_cotizacion.py`
**Función:**  
Descarga y procesa la tabla de cotizaciones del IGBM.

**Tarea principal:**  
Genera un CSV diario con los datos de mercado.

**Relación con Tema 7:**  
Aunque es secuencial, es la base de datos que alimenta la fase concurrente.

---

### ▶ `scraping_finanzas.py`
**Función:**  
Obtiene datos financieros en paralelo usando hilos.

**Conceptos de concurrencia usados:**
- Hilos (`Thread`)
- Semáforo (`Semaphore`) → controla el número de hilos simultáneos
- Lock → evita que dos hilos escriban en la base de datos a la vez

**Salida:**  
Base de datos SQLite con información financiera.

---

### ▶ `analisis.py`
**Función:**  
Une todos los datos y realiza el análisis financiero.

**Trabajos concurrentes:**
- cálculo de ratios  
- clasificación de señales  
- recomendaciones  
- guardado de resultados  

Cada tarea se ejecuta en un hilo independiente.

---

### ▶ `main.py`
**Función:**  
Orquesta todo el proyecto.

Ejecuta automáticamente:
1. Scraping de cotizaciones  
2. Scraping financiero concurrente  
3. Análisis concurrente  
4. Exportación de resultados  

---

## 5. ¿Cómo ejecutar el proyecto?

### 1- Instalar dependencias:


pip install:

 requests 

 beautifulsoup4 

 lxml 

 pandas
 
 openpyxl

### 2- EJECUTAR:

python src/main.py




---


## 6. Ratios y términos financieros utilizados en el análisis

| **Término** | **Qué mide** | **Para qué se utiliza en el análisis** |
|-------------|--------------|-----------------------------------------|
| **PER (Price-to-Earnings Ratio)** | Cuántas veces paga el inversor por cada unidad de beneficio anual de la empresa. | Permite evaluar si una acción está barata, en precio razonable o cara. |
| **BPA / EPS (Beneficio por acción)** | Parte del beneficio neto que corresponde a cada acción. | Mide la rentabilidad generada por acción y compara empresas entre sí. |
| **EBITDA** | Beneficio operativo antes de intereses, impuestos, depreciaciones y amortizaciones. | Indica la capacidad real de generación de caja de la empresa. |
| **Deuda Neta (Net Debt)** | Deuda financiera total menos el efectivo disponible. | Refleja el nivel real de endeudamiento y el riesgo financiero. |
| **Deuda/EBITDA** | Años necesarios para pagar la deuda neta usando el EBITDA. | Ratio clave de solvencia y nivel de apalancamiento financiero. |
| **EBITDA / Beneficio Neto** | Relación entre ingresos operativos y beneficio final. | Detecta empresas con alta carga fiscal, amortizaciones o gastos financieros. |


---

## 7. Criterios del sistema de recomendación de inversión

| **Recomendación** | **Condición** | **Interpretación** |
|-------------------|---------------|--------------------|
| **Comprar** | PER bajo o razonable **y** BPA medio o alto. | La acción parece infravalorada y muestra buena rentabilidad; hay potencial de revalorización. |
| **Vender** | PER alto **y** BPA bajo. | El precio está sobrevalorado respecto a sus beneficios y la empresa genera poca rentabilidad; riesgo de caída. |
| **Mantener** | Cualquier caso no claramente Compra o Venta, especialmente cuando los ratios están en rangos normales. | Típico en grandes empresas del IBEX 35: situación estable sin señales de infravaloración ni de riesgo crítico. |

---

## 8. ¿Qué son los logs y para qué sirven en este proyecto?

Los *logs* son archivos donde el programa va registrando todo lo que ocurre durante la ejecución: acciones, errores, avisos y resultados intermedios.  
Permiten:

- detectar errores sin detener la ejecución,
- entender qué ocurrió en cada fase del proceso,
- depurar problemas de scraping o concurrencia,
- verificar que los hilos han trabajado correctamente,
- mantener un historial de ejecuciones.

En este proyecto se generan **tres logs principales**, cada uno asociado a un módulo del sistema:

### **• `cotizaciones.log`**  
Registra todos los pasos del scraping de cotizaciones del índice IGBM.  
Incluye:  
- descargas de HTML,  
- problemas de conexión,  
- número de empresas detectadas,  
- archivo CSV generado.

### **• `finanzas.log`**  
Registra la ejecución **concurrente** del scraping financiero.  
Incluye:  
- inicio y final de cada hilo,  
- errores individuales por empresa,  
- acceso a la base de datos SQLite,  
- datos extraídos del “Resumen financiero”.

Este log es especialmente útil para comprobar que:  
- los hilos no se pisan entre sí,  
- el semáforo limita la concurrencia correctamente,  
- el `Lock` evita condiciones de carrera al escribir en la BD.

### **• `analisis.log`**  
Registra toda la parte de análisis financiero.  
Incluye:  
- unión de datasets,  
- cálculos de ratios,  
- clasificación de señales,  
- recomendaciones generadas,  
- exportación a CSV y Excel.

---

### ¿Por qué son importantes en un proyecto con concurrencia?

Cuando se usan hilos, varios procesos ocurren al mismo tiempo y el programa puede volverse difícil de seguir.  
Los logs permiten:

- saber qué hilo falló,  
- entender cuándo ocurrió un problema y por qué,  
- reproducir errores,  
- garantizar la integridad de la base de datos,  
- asegurar que el flujo completo funciona sin interferencias.

Gracias a los logs, el proyecto se vuelve **auditado, trazable y mucho más profesional**.

---


## Sistema de recomendación

La lógica financiera no está manipulada para “forzar” compras o ventas.  
Se basa en:

- PER (valoración relativa)
- BPA (rentabilidad por acción)
- Deuda/EBITDA (solvencia)
- Estabilidad sectorial

Dado que las empresas analizadas son grandes compañías del IBEX 35, es **normal y realista** que la recomendación predominante sea **Mantener**, ya que:

- no están infravaloradas de forma extrema
- no están en situación crítica
- no presentan riesgos inmediatos
- sus ratios se encuentran dentro de rangos esperados


---

## Objetivos académicos logrados:

Este proyecto demuestra:

- Scraping web real con HTML dinámico.
- Uso de BeautifulSoup y requests.
- Concurrencia con hilos (Thread).
- Sincronización con Lock y Semaphore.
- Acceso concurrente a SQLite.
- Limpieza y normalización de datos dentro del pipeline.
- Análisis financiero multithreading.
- Exportación a CSV + Excel.
- Registro completo del sistema mediante logs.


 
