"""
Monitoreo de apariciones en medios de comunicación.

Fuentes usadas:
  1. RSS feeds de medios argentinos (gratis, sin límite)
  2. Google Custom Search API (100 consultas/día gratis)

Busca menciones de "Centro de Políticas Migratorias" publicadas en las últimas 24 hs.
"""
import os
import logging
from datetime import datetime, timedelta, timezone

import feedparser
import requests
from utils import truncate, deduplicate_by_url

logger = logging.getLogger(__name__)

# Término a buscar en todos los medios
TERMINO_BUSQUEDA = "Centro de Políticas Migratorias"

# Feeds RSS de medios argentinos relevantes
RSS_FEEDS = [
    # Nacionales generalistas
    {"url": "https://www.clarin.com/rss/",                         "medio": "Clarín",        "tipo": "Digital"},
    {"url": "https://www.lanacion.com.ar/arc/outboundfeeds/rss/",  "medio": "La Nación",     "tipo": "Digital"},
    {"url": "https://www.infobae.com/feeds/rss/",                  "medio": "Infobae",       "tipo": "Digital"},
    {"url": "https://www.pagina12.com.ar/rss/portada",             "medio": "Página 12",     "tipo": "Digital"},
    {"url": "https://www.ambito.com/rss.xml",                      "medio": "Ámbito",        "tipo": "Digital"},
    {"url": "https://www.telam.com.ar/rss/",                       "medio": "Télam",         "tipo": "Digital"},
    {"url": "https://www.cronista.com/rss/",                       "medio": "El Cronista",   "tipo": "Digital"},
    {"url": "https://chequeado.com/feed/",                         "medio": "Chequeado",     "tipo": "Digital"},
    # Medios especializados en migración / derechos humanos
    {"url": "https://www.acnur.org/es/rss.xml",                    "medio": "ACNUR",         "tipo": "Digital"},
    {"url": "https://agenciadenoticias.io/feed/",                  "medio": "AgenciaN",      "tipo": "Digital"},
]


class MediaMonitor:
    """Busca menciones del CPM en medios digitales e impresos."""

    def __init__(self):
        self.google_api_key = os.environ.get("GOOGLE_CSE_API_KEY", "")
        self.google_cse_id  = os.environ.get("GOOGLE_CSE_ID", "")

    # ------------------------------------------------------------------
    # RSS Feeds
    # ------------------------------------------------------------------
    def buscar_en_rss(self) -> list:
        """Parsea los feeds RSS y filtra entradas que mencionen al CPM."""
        resultados = []
        termino    = TERMINO_BUSQUEDA.lower()
        corte      = datetime.now(tz=timezone.utc) - timedelta(hours=24)

        for feed_info in RSS_FEEDS:
            try:
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries:
                    titulo  = entry.get("title", "")
                    resumen = entry.get("summary", "")
                    texto   = (titulo + " " + resumen).lower()

                    if termino not in texto:
                        continue

                    # Filtro de fecha (si el feed la provee)
                    fecha_entry = entry.get("published_parsed")
                    if fecha_entry:
                        fecha_dt = datetime(*fecha_entry[:6], tzinfo=timezone.utc)
                        if fecha_dt < corte:
                            continue

                    resultados.append({
                        "titulo":     titulo,
                        "medio":      feed_info["medio"],
                        "tipo_medio": feed_info["tipo"],
                        "url":        entry.get("link", ""),
                        "resumen":    truncate(resumen),
                        "fuente":     "RSS",
                    })
            except Exception as e:
                logger.warning(f"Error al procesar RSS de {feed_info['medio']}: {e}")

        logger.info(f"RSS: {len(resultados)} menciones encontradas.")
        return resultados

    # ------------------------------------------------------------------
    # Google Custom Search API
    # ------------------------------------------------------------------
    def buscar_en_google_cse(self) -> list:
        """
        Busca menciones recientes usando la API de Google Custom Search.
        Requiere GOOGLE_CSE_API_KEY y GOOGLE_CSE_ID en las variables de entorno.
        """
        if not self.google_api_key or not self.google_cse_id:
            logger.info("Google CSE no configurado, se omite esta fuente.")
            return []

        resultados = []
        try:
            params = {
                "key":         self.google_api_key,
                "cx":          self.google_cse_id,
                "q":           f'"{TERMINO_BUSQUEDA}"',
                "dateRestrict": "d1",   # últimas 24 horas
                "num":         10,
                "lr":          "lang_es",
            }
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=15,
            )
            resp.raise_for_status()
            items = resp.json().get("items", [])

            for item in items:
                resultados.append({
                    "titulo":     item.get("title", ""),
                    "medio":      item.get("displayLink", ""),
                    "tipo_medio": "Digital",
                    "url":        item.get("link", ""),
                    "resumen":    truncate(item.get("snippet", "")),
                    "fuente":     "GoogleCSE",
                })
        except Exception as e:
            logger.error(f"Error en Google CSE: {e}")

        logger.info(f"Google CSE: {len(resultados)} menciones encontradas.")
        return resultados

    # ------------------------------------------------------------------
    # Método principal
    # ------------------------------------------------------------------
    def buscar_todas_las_fuentes(self) -> list:
        """
        Combina todos los resultados y elimina duplicados por URL.
        Retorna la lista final de menciones para registrar en Sheets.
        """
        menciones = []
        menciones += self.buscar_en_rss()
        menciones += self.buscar_en_google_cse()

        menciones_unicas = deduplicate_by_url(menciones)
        logger.info(f"Total menciones únicas: {len(menciones_unicas)}")
        return menciones_unicas
