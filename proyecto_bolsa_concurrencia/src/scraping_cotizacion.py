"""
Módulo: scraping_cotizacion.py

Objetivo:
    - Descargar la tabla de cotizaciones del IGBM desde CincoDías.
    - Guardar los datos crudos en raw/cotizaciones/.
    - Generar datos limpios en processed/cotizaciones_limpias.csv.
    - Registrar logs en logs/cotizaciones.log.
"""

import os
import requests
import pandas as pd
from bs4 import BeautifulSoup
from datetime import datetime
import logging


# ============================================================
# LOGGING
# ============================================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/cotizaciones.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


# ============================================================
# SCRAPING DE COTIZACIONES
# ============================================================

URL = "https://cincodias.elpais.com/mercados/bolsa/igbm/"


def clean_num(texto):
    """Limpia y estandariza números españoles a float de Python."""
    if texto in ("", None, "--", "-"):
        return None
    texto = texto.replace(".", "").replace(",", ".").replace("%", "")
    try:
        return float(texto)
    except:
        return None


def ejecutar_scraping_cotizacion():
    try:
        print("[INFO] Descargando HTML desde CincoDías...")
        logger.info("Iniciando scraping de cotizaciones")

        headers = {
            "User-Agent":
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
        }

        resp = requests.get(URL, headers=headers, timeout=15)
        resp.raise_for_status()
        html = resp.text

        print("[INFO] Parseando HTML...")
        logger.info("HTML descargado")

        soup = BeautifulSoup(html, "html.parser")

        # Buscar tabla
        tabla = None
        for t in soup.find_all("table"):
            if "Principales valores" in t.get_text(" ", strip=True):
                tabla = t
                break

        if tabla is None:
            logger.error("No se encontró la tabla")
            raise RuntimeError("Tabla no localizada")

        filas = []
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        cuerpo = tabla.find("tbody").find_all("tr")
        for tr in cuerpo:
            th = tr.find("th")
            if th is None:
                continue

            a = th.find("a")
            if a is None:
                continue

            name = a.get_text(strip=True)
            link = "https://cincodias.elpais.com" + a.get("href", "").strip()
            tds = tr.find_all("td")

            if len(tds) < 5:
                continue

            filas.append({
                "link": link,
                "name": name,
                "value": tds[0].get_text(strip=True),
                "var": tds[1].get_text(strip=True),
                "datetime": fecha,
                "max": tds[3].get_text(strip=True),
                "min": tds[4].get_text(strip=True)
            })

        logger.info(f"Filas extraídas: {len(filas)}")
        print(f"[INFO] Filas extraídas: {len(filas)}")

        # Guardar RAW
        os.makedirs("raw/cotizaciones", exist_ok=True)
        ruta_raw = f"raw/cotizaciones/cotizacion_{datetime.now().strftime('%Y%m%d')}.csv"
        pd.DataFrame(filas).to_csv(ruta_raw, index=False, encoding="utf-8")
        print(f"[OK] Archivo RAW guardado en: {ruta_raw}")

        # ============================================================
        # PROCESSED (LIMPIEZA)
        # ============================================================
        df_clean = pd.DataFrame(filas)
        df_clean["value"] = df_clean["value"].apply(clean_num)
        df_clean["var"] = df_clean["var"].apply(clean_num)
        df_clean["max"] = df_clean["max"].apply(clean_num)
        df_clean["min"] = df_clean["min"].apply(clean_num)

        os.makedirs("processed", exist_ok=True)
        ruta_clean = "processed/cotizaciones_limpias.csv"
        df_clean.to_csv(ruta_clean, index=False, encoding="utf-8")

        logger.info(f"Archivo limpio PROCESSED guardado en {ruta_clean}")
        print(f"[OK] Archivo limpio guardado en: {ruta_clean}")

    except Exception as e:
        logger.error(f"ERROR en scraping cotizaciones: {e}")
        print(f"[ERROR] {e}")


if __name__ == "__main__":
    ejecutar_scraping_cotizacion()
