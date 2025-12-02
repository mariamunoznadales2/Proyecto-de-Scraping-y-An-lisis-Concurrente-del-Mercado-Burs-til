"""
Módulo: analisis.py

Objetivo:
    - Unir cotizaciones limpias + finanzas limpias.
    - Procesar el análisis usando MULTITHREADING (Tema 7).
    - Guardar dataset procesado en processed/dataset_unido.csv.
    - Exportar resultados finales también a Excel.
    - Guardar análisis final en analysis/.
    - Registrar logs en logs/analisis.log.
"""

import os
import pandas as pd
import threading
from datetime import datetime
import logging


# ============================================================
# LOGGING
# ============================================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/analisis.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


# ============================================================
# CARGA DE ARCHIVOS
# ============================================================

def obtener_cotizaciones_limpias():
    ruta = "processed/cotizaciones_limpias.csv"
    if not os.path.exists(ruta):
        raise FileNotFoundError("Falta processed/cotizaciones_limpias.csv")
    return pd.read_csv(ruta)


def obtener_finanzas_limpias():
    ruta = "processed/finanzas_limpias.csv"
    if not os.path.exists(ruta):
        raise FileNotFoundError("Falta processed/finanzas_limpias.csv")
    return pd.read_csv(ruta)


# ============================================================
# SUBTAREAS DEL ANÁLISIS (MULTITHREADING)
# ============================================================

def calcular_ratios(df, resultados, lock):
    """
    HILO 1 — Calcula ratios financieros:
        - deuda / ebitda
        - ebitda / beneficio
    """
    temp = df.copy()

    def safe_ratio(a, b):
        if a is None or pd.isna(a):
            return None
        if b is None or pd.isna(b) or b == 0:
            return None
        return a / b

    temp["deuda_ebitda"] = temp.apply(lambda r: safe_ratio(r["deuda"], r["ebitda"]), axis=1)
    temp["ebitda_beneficio"] = temp.apply(lambda r: safe_ratio(r["ebitda"], r["beneficio"]), axis=1)

    with lock:
        resultados["ratios"] = temp[["deuda_ebitda", "ebitda_beneficio"]]


def calcular_senales(df, resultados, lock):
    """
    HILO 2 — Clasifica PER y BPA según reglas realistas adaptadas al dataset.
    """

    temp = df.copy()

    def per_sig(x):
        try:
            if x is None or pd.isna(x):
                return "Desconocido"
            x = float(x)
            if x < 12:
                return "Barata"
            if x < 20:
                return "Media"
            return "Cara"
        except:
            return "Desconocido"

    def bpa_sig(x):
        try:
            if x is None or pd.isna(x):
                return "Desconocido"
            x = float(x)
            if x < 0.5:
                return "Débil"
            if x < 1.5:
                return "Media"
            return "Alta"
        except:
            return "Desconocido"

    temp["per_señal"] = temp["per"].apply(per_sig)
    temp["bpa_señal"] = temp["bpa"].apply(bpa_sig)

    with lock:
        resultados["senales"] = temp[["per_señal", "bpa_señal"]]


def calcular_recomendacion(df, resultados, lock):
    """
    HILO 3 — Reglas de recomendación adaptadas para producir resultados variados.
    """

    temp = df.copy()

    def recomendar(r):
        per = r.get("per_señal", "Desconocido")
        bpa = r.get("bpa_señal", "Desconocido")
        deuda_ebitda = r.get("deuda_ebitda", None)

        deuda_ok = deuda_ebitda is not None and not pd.isna(deuda_ebitda)

        if per in ("Barata", "Media") and bpa in ("Media", "Alta"):
            if not deuda_ok or deuda_ebitda <= 6:
                return "Comprar"

        if per == "Cara" and bpa == "Débil":
            if deuda_ok and deuda_ebitda >= 4:
                return "Vender"
            if not deuda_ok:
                return "Vender"

        return "Mantener"

    temp["recomendacion"] = temp.apply(recomendar, axis=1)

    with lock:
        resultados["recomend"] = temp["recomendacion"]


def procesar_dataset_unido(df, resultados, lock):
    """
    HILO 4 — Guarda un dataset unido previo a las métricas
    """
    os.makedirs("processed", exist_ok=True)
    ruta_unido = "processed/dataset_unido.csv"
    df.to_csv(ruta_unido, index=False)

    with lock:
        resultados["dataset_unido"] = ruta_unido


# ============================================================
# EJECUCIÓN PRINCIPAL (CON SINCRONIZACIÓN CORRECTA)
# ============================================================

def ejecutar_analisis():
    logger.info("Iniciando análisis MULTITHREADING")
    print("[INFO] Iniciando análisis con MULTITHREADING...")

    cot = obtener_cotizaciones_limpias()
    fin = obtener_finanzas_limpias()

    df = pd.merge(
        fin,
        cot[["name", "value", "var", "max", "min"]],
        left_on="nombre",
        right_on="name",
        how="left"
    )

    df.drop(columns=["name"], inplace=True)

    resultados = {}
    lock = threading.Lock()

    h1 = threading.Thread(target=calcular_ratios, args=(df, resultados, lock))
    h2 = threading.Thread(target=calcular_senales, args=(df, resultados, lock))
    h3 = threading.Thread(target=calcular_recomendacion, args=(df, resultados, lock))
    h4 = threading.Thread(target=procesar_dataset_unido, args=(df, resultados, lock))

    h1.start()
    h2.start()
    h1.join()
    h2.join()

    h3.start()
    h4.start()
    h3.join()
    h4.join()

    df_final = df.copy()

    df_final = pd.concat([
        df_final,
        resultados["ratios"],
        resultados["senales"],
        resultados["recomend"]
    ], axis=1)

    os.makedirs("analysis", exist_ok=True)

    ruta_csv = f"analysis/analisis_resultados_{datetime.now().strftime('%Y%m%d')}.csv"
    df_final.to_csv(ruta_csv, index=False, encoding="utf-8")

    ruta_excel = "analysis/analisis_resultados.xlsx"
    df_final.to_excel(ruta_excel, index=False)

    logger.info(f"Análisis MULTITHREADING completado. CSV: {ruta_csv} | Excel: {ruta_excel}")
    print(f"[OK] Análisis MULTITHREADING guardado en {ruta_csv}")
    print(f"[OK] También exportado a Excel en {ruta_excel}")

    return ruta_csv


if __name__ == "__main__":
    ejecutar_analisis()
