"""
Módulo: scraping_finanzas.py

Objetivo:
    - Scraping financiero de 8 empresas del IGBM.
    - Guardar RAW en SQLite.
    - Generar processed/finanzas_limpias.csv.
    - Concurrencia con hilos (Tema 7).
    - Logging en logs/finanzas.log.
"""

import os
import threading
import sqlite3
from datetime import datetime
import requests
from bs4 import BeautifulSoup
import pandas as pd
import logging


# ============================================================
# LOGGING
# ============================================================

os.makedirs("logs", exist_ok=True)

logging.basicConfig(
    filename="logs/finanzas.log",
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

logger = logging.getLogger(__name__)


# ============================================================
# EMPRESAS
# ============================================================

EMPRESAS = [
    {"name": "BBVA", "ticker": "BBVA", "url": "https://cincodias.elpais.com/mercados/empresas/bbva/"},
    {"name": "CaixaBank", "ticker": "CABK", "url": "https://cincodias.elpais.com/mercados/empresas/caixabank/"},
    {"name": "Iberdrola", "ticker": "IBE", "url": "https://cincodias.elpais.com/mercados/empresas/iberdrola/"},
    {"name": "Endesa", "ticker": "ELE", "url": "https://cincodias.elpais.com/mercados/empresas/endesa/"},
    {"name": "Repsol", "ticker": "REP", "url": "https://cincodias.elpais.com/mercados/empresas/repsol/"},
    {"name": "Telefónica", "ticker": "TEF", "url": "https://cincodias.elpais.com/mercados/empresas/telefonica/"},
    {"name": "Inditex", "ticker": "ITX", "url": "https://cincodias.elpais.com/mercados/empresas/inditex/"},
    {"name": "AENA", "ticker": "AENA", "url": "https://cincodias.elpais.com/mercados/empresas/aena/"},
]


# ============================================================
# UTILS
# ============================================================

def asegurar_db():
    os.makedirs("raw/finanzas", exist_ok=True)
    return "raw/finanzas/finanzas_empresas.db"


def convertir_num(texto):
    if texto in ("", None, "-", "--"):
        return None
    texto = texto.replace(".", "").replace(",", ".")
    try:
        return float(texto)
    except:
        return None


# ============================================================
# BASE DE DATOS
# ============================================================

def inicializar_bd():
    ruta = asegurar_db()
    conn = sqlite3.connect(ruta)
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS empresas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT,
            ticker TEXT UNIQUE,
            url TEXT
        );
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS finanzas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            empresa_id INTEGER,
            fecha_registro TEXT,
            per REAL,
            bpa REAL,
            ebitda REAL,
            beneficio REAL,
            deuda REAL,
            FOREIGN KEY (empresa_id) REFERENCES empresas(id)
        );
    """)

    for emp in EMPRESAS:
        cur.execute("""
            INSERT OR IGNORE INTO empresas (nombre, ticker, url)
            VALUES (?, ?, ?)
        """, (emp["name"], emp["ticker"], emp["url"]))

    conn.commit()
    cur.execute("SELECT id, ticker FROM empresas;")
    mapa = {t: i for i, t in cur.fetchall()}

    conn.close()
    return mapa


# ============================================================
# SCRAPING
# ============================================================

def descargar_html(url):
    headers = {
        "User-Agent":
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15)"
    }
    resp = requests.get(url, headers=headers, timeout=12)
    resp.raise_for_status()
    return resp.text


def extraer_finanzas(html):
    soup = BeautifulSoup(html, "html.parser")

    tablas = soup.find_all("table")
    per = bpa = ebitda = beneficio = deuda = None

    for tabla in tablas:
        for fila in tabla.find_all("tr"):
            c = fila.find_all(["td", "th"])
            if len(c) < 2:
                continue

            clave = c[0].get_text(strip=True).lower()
            valor = convertir_num(c[1].get_text(strip=True))

            if "per" in clave:
                per = valor
            elif "bpa" in clave:
                bpa = valor
            elif "ebitda" in clave:
                ebitda = valor
            elif "benef" in clave:
                beneficio = valor
            elif "deuda" in clave:
                deuda = valor

    return {
        "per": per,
        "bpa": bpa,
        "ebitda": ebitda,
        "beneficio": beneficio,
        "deuda": deuda
    }


# ============================================================
# PROCESAMIENTO POR HILO
# ============================================================

def procesar_empresa(emp, mapa_ids, lock, sem):
    sem.acquire()
    try:
        nombre = emp["name"]
        ticker = emp["ticker"]
        url = emp["url"]

        print(f"[INFO] Procesando {nombre}...")
        logger.info(f"Procesando {nombre}")

        html = descargar_html(url)
        datos = extraer_finanzas(html)

        empresa_id = mapa_ids[ticker]

        conn = sqlite3.connect(asegurar_db())
        cur = conn.cursor()
        fecha = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with lock:
            cur.execute("""
                INSERT INTO finanzas (empresa_id, fecha_registro, per, bpa, ebitda, beneficio, deuda)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                empresa_id, fecha,
                datos["per"], datos["bpa"],
                datos["ebitda"], datos["beneficio"], datos["deuda"]
            ))
            conn.commit()

        conn.close()

        print(f"[OK] Guardado en BD para {nombre}")
        logger.info(f"Datos guardados para {nombre}")
    except Exception as e:
        print(f"[ERROR] Fallo procesando {emp['name']}: {e}")
        logger.error(f"Error con {emp['name']}: {e}")
    finally:
        sem.release()


# ============================================================
# EJECUCIÓN PRINCIPAL
# ============================================================

def ejecutar_scraping_finanzas(max_hilos_concurrentes=3):
    print("[INFO] Inicializando BD...")
    mapa = inicializar_bd()
    print("[INFO] Mapa IDs:", mapa)

    lock = threading.Lock()
    sem = threading.Semaphore(max_hilos_concurrentes)
    hilos = []

    for emp in EMPRESAS:
        th = threading.Thread(
            target=procesar_empresa,
            args=(emp, mapa, lock, sem),
            daemon=True
        )
        hilos.append(th)
        th.start()

    for h in hilos:
        h.join()

    print("[INFO] Scraping financiero completado.")

    # ============================================================
    # PROCESSED: Generar CSV limpio
    # ============================================================

    conn = sqlite3.connect("raw/finanzas/finanzas_empresas.db")
    df_fin = pd.read_sql_query("""
        SELECT empresas.nombre, empresas.ticker,
               finanzas.per, finanzas.bpa, finanzas.ebitda,
               finanzas.beneficio, finanzas.deuda,
               finanzas.fecha_registro
        FROM finanzas
        JOIN empresas ON empresas.id = finanzas.empresa_id
    """, conn)
    conn.close()

    os.makedirs("processed", exist_ok=True)
    ruta_clean = "processed/finanzas_limpias.csv"
    df_fin.to_csv(ruta_clean, index=False, encoding="utf-8")

    print(f"[OK] Archivo limpio guardado en {ruta_clean}")
    logger.info("Archivo PROCESSED generado")


if __name__ == "__main__":
    ejecutar_scraping_finanzas()
