"""
Módulo: main.py

Objetivo:
    - Orquestar todo el pipeline:
        1. scraping cotizaciones
        2. scraping finanzas
        3. análisis
    - Registrar logs en logs/main.log
"""

import os
import logging

from scraping_cotizacion import ejecutar_scraping_cotizacion
from scraping_finanzas import ejecutar_scraping_finanzas
from analisis import ejecutar_analisis


# ============================================================
# LOGGING
# ============================================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/main.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)

logger = logging.getLogger(__name__)


# ============================================================
# MAIN
# ============================================================

def main():
    logger.info("=== INICIANDO PIPELINE COMPLETO ===")
    print("==============================================")
    print("      PROYECTO MERCADO BURSÁTIL — MAIN        ")
    print("==============================================")

    print("\n[FASE 1] COTIZACIONES")
    logger.info("Ejecutando scraping de cotizaciones")
    ejecutar_scraping_cotizacion()

    print("\n[FASE 2] FINANZAS (CONCURRENCIA)")
    logger.info("Ejecutando scraping financiero concurrente")
    ejecutar_scraping_finanzas(3)

    print("\n[FASE 3] ANÁLISIS")
    logger.info("Ejecutando análisis de datos")
    ruta = ejecutar_analisis()

    logger.info(f"Pipeline completado. Resultados en: {ruta}")
    print("\n==============================================")
    print(" PROCESO COMPLETADO")
    print(f" RESULTADOS EN: {ruta}")
    print("==============================================")


if __name__ == "__main__":
    main()
