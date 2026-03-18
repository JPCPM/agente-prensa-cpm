"""
Métricas de LinkedIn usando la API oficial de LinkedIn (Community Management API).

Requiere:
  - LINKEDIN_ACCESS_TOKEN      → token OAuth 2.0
  - LINKEDIN_ORGANIZATION_ID   → ID numérico de la página de la organización

IMPORTANTE: La API oficial de LinkedIn para páginas requiere solicitar acceso
en https://developer.linkedin.com. Ver README.md para instrucciones completas.

Si aún no tenés el acceso aprobado, el módulo devuelve datos vacíos con una nota.
"""
import os
import logging
from datetime import datetime, timedelta, timezone

import requests
from utils import get_today, truncate

logger = logging.getLogger(__name__)

LINKEDIN_BASE = "https://api.linkedin.com/v2"


class LinkedInMetrics:
    """Obtiene publicaciones y métricas de la página de LinkedIn del CPM."""

    def __init__(self):
        self.token   = os.environ.get("LINKEDIN_ACCESS_TOKEN", "")
        self.org_id  = os.environ.get("LINKEDIN_ORGANIZATION_ID", "")

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.token}",
            "X-Restli-Protocol-Version": "2.0.0",
        }

    def get_daily_metrics(self) -> dict:
        """
        Retorna un dict con las métricas del día:
          - seguidores, publicaciones_nuevas, reacciones_total,
            comentarios_total, impresiones, post_urls, metodo
        """
        if not self.token or not self.org_id:
            logger.warning("LinkedIn: credenciales no configuradas.")
            return {
                "metodo": (
                    "Sin credenciales. "
                    "Ver README → 'Configurar LinkedIn API'."
                )
            }

        try:
            org_urn = f"urn:li:organization:{self.org_id}"

            # 1. Seguidores
            stats_url = (
                f"{LINKEDIN_BASE}/networkSizes/{org_urn}"
                f"?edgeType=CompanyFollowedByMember"
            )
            stats_resp = requests.get(stats_url, headers=self._headers(), timeout=15)
            stats_resp.raise_for_status()
            seguidores = stats_resp.json().get("firstDegreeSize", "")

            # 2. Posts de las últimas 24 horas
            corte = int((datetime.now(tz=timezone.utc) - timedelta(hours=24)).timestamp() * 1000)
            posts_url = (
                f"{LINKEDIN_BASE}/ugcPosts"
                f"?q=authors&authors=List({org_urn})"
                f"&count=20&sortBy=LAST_MODIFIED"
            )
            posts_resp = requests.get(posts_url, headers=self._headers(), timeout=15)
            posts_resp.raise_for_status()
            posts = posts_resp.json().get("elements", [])

            posts_hoy        = [p for p in posts if p.get("created", {}).get("time", 0) >= corte]
            reacciones_total = 0
            comentarios_total = 0
            post_urls        = []
            impresiones      = 0

            for post in posts_hoy:
                post_id = post.get("id", "")
                # Estadísticas de cada post
                try:
                    soc_url = (
                        f"{LINKEDIN_BASE}/socialMetadata/{post_id}"
                        f"?projection=(totalShareStatistics)"
                    )
                    soc_resp = requests.get(soc_url, headers=self._headers(), timeout=10)
                    soc_resp.raise_for_status()
                    soc = soc_resp.json().get("totalShareStatistics", {})
                    reacciones_total  += soc.get("likeCount",        0)
                    comentarios_total += soc.get("commentCount",     0)
                    impresiones       += soc.get("impressionCount",  0)
                except Exception:
                    pass

                # URL del post
                share_url = post.get("specificContent", {}).get(
                    "com.linkedin.ugc.ShareContent", {}
                ).get("shareCommentary", {}).get("text", "")
                if post_id:
                    post_urls.append(f"https://www.linkedin.com/feed/update/{post_id}/")

            return {
                "seguidores":           seguidores,
                "publicaciones_nuevas": len(posts_hoy),
                "reacciones_total":     reacciones_total,
                "comentarios_total":    comentarios_total,
                "impresiones":          impresiones,
                "post_urls":            " | ".join(post_urls),
                "metodo":               "LinkedIn API v2",
            }

        except Exception as e:
            logger.error(f"LinkedIn: error al obtener métricas: {e}")
            return {"metodo": f"Error: {e}"}
