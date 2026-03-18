"""
Agente de Prensa - Centro de Políticas Migratorias
====================================================
Punto de entrada principal. Orquesta todos los módulos y actualiza la Google Sheet.

Ejecución local:
    python src/main.py

Ejecución automática:
    GitHub Actions lo ejecuta todos los días a las 8:00 AM (hora argentina).
"""
import sys
import logging
from pathlib import Path

# Permite importar los otros módulos desde src/
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()  # Carga el archivo .env en desarrollo local

from sheets_client import SheetsClient
from media_monitor import MediaMonitor
from instagram_metrics import InstagramMetrics
from linkedin_metrics import LinkedInMetrics
from twitter_metrics import TwitterMetrics
from utils import get_today

logger = logging.getLogger(__name__)


def run():
    logger.info("=" * 60)
    logger.info(f"Agente de Prensa CPM - Inicio: {get_today()}")
    logger.info("=" * 60)

    sheets  = SheetsClient()
    estado  = "OK"
    notas   = []

    # ── 1. Monitoreo de medios ────────────────────────────────────────
    menciones = []
    try:
        monitor   = MediaMonitor()
        menciones = monitor.buscar_todas_las_fuentes()
        sheets.append_menciones(menciones)
    except Exception as e:
        estado = "ERROR"
        notas.append(f"Medios: {e}")
        logger.error(f"Medios: {e}")

    # ── 2. Instagram ──────────────────────────────────────────────────
    ig_data = {}
    try:
        ig_data = InstagramMetrics().get_daily_metrics()
        sheets.append_instagram(ig_data)
    except Exception as e:
        notas.append(f"Instagram: {e}")
        logger.error(f"Instagram: {e}")

    # ── 3. LinkedIn ───────────────────────────────────────────────────
    li_data = {}
    try:
        li_data = LinkedInMetrics().get_daily_metrics()
        sheets.append_linkedin(li_data)
    except Exception as e:
        notas.append(f"LinkedIn: {e}")
        logger.error(f"LinkedIn: {e}")

    # ── 4. Twitter / X ────────────────────────────────────────────────
    tw_data = {}
    try:
        tw_data = TwitterMetrics().get_daily_metrics()
        sheets.append_twitter(tw_data)
    except Exception as e:
        notas.append(f"Twitter: {e}")
        logger.error(f"Twitter: {e}")

    # ── 5. Resumen del día ────────────────────────────────────────────
    try:
        sheets.update_resumen(
            menciones = menciones,
            ig        = ig_data,
            li        = li_data,
            tw        = tw_data,
            estado    = estado,
            notas     = " | ".join(notas) if notas else "",
        )
    except Exception as e:
        logger.error(f"Resumen: {e}")

    logger.info("=" * 60)
    logger.info(f"Agente finalizado. Estado: {estado}")
    if notas:
        logger.warning(f"Advertencias: {' | '.join(notas)}")
    logger.info("=" * 60)


if __name__ == "__main__":
    run()
