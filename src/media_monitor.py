"""
Monitoreo de apariciones en medios de comunicación.

Fuentes usadas:
  1. Google News RSS (gratis, sin límite, cubre toda América Latina)
  2. Google Custom Search API (100 consultas/día gratis, opcional)
  3. RSS feeds de medios específicos (gratis, sin límite)

Busca menciones de "Centro de Políticas Migratorias" publicadas en las últimas 24 hs.
"""
import os
import logging
from datetime import datetime, timedelta, timezone
from urllib.parse import quote

import feedparser
import requests
from duckduckgo_search import DDGS
from utils import truncate, deduplicate_by_url

logger = logging.getLogger(__name__)

# Términos a buscar (se busca cada uno por separado)
TERMINOS_BUSQUEDA = [
    "Centro de Políticas Migratorias",
    "Centro de Politicas Migratorias",
    "Juan Pablo Ramaciotti",
    "Olaya Grau",
]

# Google News RSS — busca en TODA la web en español, sin API key
# Una entrada por cada término × región
GOOGLE_NEWS_FEEDS = [
    # Término 1 — toda América Latina (when:7d fuerza resultados de los últimos 7 días)
    {"url": "https://news.google.com/rss/search?q=%22Centro+de+Pol%C3%ADticas+Migratorias%22+when%3A7d&hl=es-419&gl=US&ceid=US:es-419", "medio": "Google News",           "tipo": "Digital"},
    {"url": "https://news.google.com/rss/search?q=%22Centro+de+Pol%C3%ADticas+Migratorias%22+when%3A7d&hl=es-CL&gl=CL&ceid=CL:es",     "medio": "Google News Chile",     "tipo": "Digital"},
    {"url": "https://news.google.com/rss/search?q=%22Centro+de+Pol%C3%ADticas+Migratorias%22+when%3A7d&hl=es-AR&gl=AR&ceid=AR:es",     "medio": "Google News Argentina", "tipo": "Digital"},
    # Término 2 — sin tilde
    {"url": "https://news.google.com/rss/search?q=%22Centro+de+Politicas+Migratorias%22+when%3A7d&hl=es-419&gl=US&ceid=US:es-419",     "medio": "Google News",           "tipo": "Digital"},
    {"url": "https://news.google.com/rss/search?q=%22Centro+de+Politicas+Migratorias%22+when%3A7d&hl=es-CL&gl=CL&ceid=CL:es",         "medio": "Google News Chile",     "tipo": "Digital"},
    # Término 3 — Juan Pablo Ramaciotti
    {"url": "https://news.google.com/rss/search?q=%22Juan+Pablo+Ramaciotti%22+when%3A7d&hl=es-419&gl=US&ceid=US:es-419",               "medio": "Google News",           "tipo": "Digital"},
    {"url": "https://news.google.com/rss/search?q=%22Juan+Pablo+Ramaciotti%22+when%3A7d&hl=es-CL&gl=CL&ceid=CL:es",                   "medio": "Google News Chile",     "tipo": "Digital"},
    # Término 4 — Olaya Grau
    {"url": "https://news.google.com/rss/search?q=%22Olaya+Grau%22+when%3A7d&hl=es-419&gl=US&ceid=US:es-419",                         "medio": "Google News",           "tipo": "Digital"},
    {"url": "https://news.google.com/rss/search?q=%22Olaya+Grau%22+when%3A7d&hl=es-CL&gl=CL&ceid=CL:es",                              "medio": "Google News Chile",     "tipo": "Digital"},
]

# RSS feeds de medios especializados en migración y derechos humanos
RSS_FEEDS_ESPECIALIZADOS = [
    {"url": "https://www.acnur.org/es/rss.xml",      "medio": "ACNUR",      "tipo": "Digital"},
    {"url": "https://chequeado.com/feed/",            "medio": "Chequeado",  "tipo": "Digital"},
    {"url": "https://www.infomigrants.net/es/rss",    "medio": "InfoMigrants","tipo": "Digital"},
]


class MediaMonitor:
    """Busca menciones del CPM en medios de toda América Latina."""

    def __init__(self):
        self.google_api_key = os.environ.get("GOOGLE_CSE_API_KEY", "")
        self.google_cse_id  = os.environ.get("GOOGLE_CSE_ID", "")

    # ------------------------------------------------------------------
    # Google News RSS (principal — toda América Latina, sin API key)
    # ------------------------------------------------------------------
    def buscar_en_google_news(self) -> list:
        """
        Busca menciones del CPM en Google News.
        Cubre medios de toda América Latina en español.
        No requiere API key ni tiene límite de uso.
        """
        resultados = []
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36"
        }
        for feed_info in GOOGLE_NEWS_FEEDS:
            try:
                resp = requests.get(feed_info["url"], headers=headers, timeout=15)
                feed = feedparser.parse(resp.content)
                for entry in feed.entries:
                    titulo  = entry.get("title", "")
                    resumen = entry.get("summary", "")

                    # Detectar el medio real desde el título de Google News
                    # (Google News incluye "- Nombre del Medio" al final del título)
                    medio_real = feed_info["medio"]
                    if " - " in titulo:
                        medio_real = titulo.split(" - ")[-1].strip()
                        titulo     = " - ".join(titulo.split(" - ")[:-1]).strip()

                    resultados.append({
                        "titulo":     titulo,
                        "medio":      medio_real,
                        "tipo_medio": "Digital",
                        "url":        entry.get("link", ""),
                        "resumen":    truncate(resumen),
                        "fuente":     "Google News RSS",
                    })
            except Exception as e:
                logger.warning(f"Error en Google News RSS ({feed_info['medio']}): {e}")

        logger.info(f"Google News RSS: {len(resultados)} menciones encontradas.")
        return resultados

    # ------------------------------------------------------------------
    # RSS de medios especializados
    # ------------------------------------------------------------------
    def buscar_en_rss_especializados(self) -> list:
        """Parsea RSS de medios especializados en migración y DDHH."""
        resultados = []
        terminos   = [t.lower() for t in TERMINOS_BUSQUEDA]
        corte      = datetime.now(tz=timezone.utc) - timedelta(hours=48)

        for feed_info in RSS_FEEDS_ESPECIALIZADOS:
            try:
                feed = feedparser.parse(feed_info["url"])
                for entry in feed.entries:
                    titulo  = entry.get("title", "")
                    resumen = entry.get("summary", "")
                    texto   = (titulo + " " + resumen).lower()

                    if not any(t in texto for t in terminos):
                        continue

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
                        "fuente":     "RSS especializado",
                    })
            except Exception as e:
                logger.warning(f"Error en RSS de {feed_info['medio']}: {e}")

        logger.info(f"RSS especializados: {len(resultados)} menciones encontradas.")
        return resultados

    # ------------------------------------------------------------------
    # DuckDuckGo (búsqueda en toda la web, gratis, sin API key)
    # ------------------------------------------------------------------
    def buscar_en_duckduckgo(self) -> list:
        """
        Busca menciones del CPM en toda la web usando DuckDuckGo.
        Gratis, sin API key, cubre todos los medios de América Latina.
        """
        resultados = []
        try:
            with DDGS() as ddgs:
                for termino in TERMINOS_BUSQUEDA:
                    try:
                        results = list(ddgs.text(
                            f'"{termino}"',
                            region="wt-wt",
                            timelimit="w",
                            max_results=10,
                        ))
                        for r in results:
                            titulo  = r.get("title", "")
                            cuerpo  = r.get("body", "")
                            texto   = (titulo + " " + cuerpo).lower()

                            # Filtrar: solo incluir si el resultado realmente contiene el término
                            if termino.lower() not in texto:
                                continue

                            url   = r.get("href", "")
                            medio = url.split("/")[2].replace("www.", "") if url else "Desconocido"
                            resultados.append({
                                "titulo":     titulo,
                                "medio":      medio,
                                "tipo_medio": "Digital",
                                "url":        url,
                                "resumen":    truncate(cuerpo),
                                "fuente":     "DuckDuckGo",
                            })
                    except Exception as e:
                        logger.warning(f"DuckDuckGo error buscando '{termino}': {e}")
        except Exception as e:
            logger.error(f"Error en DuckDuckGo: {e}")

        logger.info(f"DuckDuckGo: {len(resultados)} menciones encontradas.")
        return resultados

    # ------------------------------------------------------------------
    # Google Custom Search API (opcional, refuerzo adicional)
    # ------------------------------------------------------------------
    def buscar_en_google_cse(self) -> list:
        """
        Búsqueda adicional usando Google Custom Search API.
        Solo se ejecuta si están configuradas las credenciales.
        """
        if not self.google_api_key or not self.google_cse_id:
            logger.info("Google CSE no configurado, se omite esta fuente.")
            return []

        resultados = []
        try:
            query = " OR ".join(f'"{t}"' for t in TERMINOS_BUSQUEDA)
            params = {
                "key":          self.google_api_key,
                "cx":           self.google_cse_id,
                "q":            query,
                "dateRestrict": "d1",
                "num":          10,
                "lr":           "lang_es",
            }
            resp = requests.get(
                "https://www.googleapis.com/customsearch/v1",
                params=params,
                timeout=15,
            )
            if resp.status_code != 200:
                raise Exception(f"Error {resp.status_code}: {resp.json().get('error', {}).get('message', 'sin detalle')}")
            resp.raise_for_status()
            items = resp.json().get("items", [])

            for item in items:
                resultados.append({
                    "titulo":     item.get("title", ""),
                    "medio":      item.get("displayLink", ""),
                    "tipo_medio": "Digital",
                    "url":        item.get("link", ""),
                    "resumen":    truncate(item.get("snippet", "")),
                    "fuente":     "Google CSE",
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
        Combina todas las fuentes y elimina duplicados por URL.
        """
        menciones  = []
        menciones += self.buscar_en_google_news()
        menciones += self.buscar_en_duckduckgo()
        menciones += self.buscar_en_rss_especializados()
        menciones += self.buscar_en_google_cse()

        menciones_unicas = deduplicate_by_url(menciones)
        logger.info(f"Total menciones únicas: {len(menciones_unicas)}")
        return menciones_unicas
