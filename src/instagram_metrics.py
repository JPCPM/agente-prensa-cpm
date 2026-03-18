"""
Métricas de Instagram usando la Meta Graph API (oficial y gratuita).

Requiere:
  - INSTAGRAM_ACCESS_TOKEN  → token de larga duración (válido 60 días)
  - INSTAGRAM_USER_ID       → ID numérico de la cuenta profesional

Para obtenerlos ver README.md → Sección "Configurar Instagram API".
"""
import os
import logging
from datetime import datetime, timedelta, timezone

import requests
from utils import get_today

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.instagram.com/v19.0"


class InstagramMetrics:
    """Obtiene publicaciones y métricas de la cuenta de Instagram del CPM."""

    def __init__(self):
        self.token   = os.environ.get("INSTAGRAM_ACCESS_TOKEN", "")
        self.user_id = os.environ.get("INSTAGRAM_USER_ID", "")

    def _get(self, endpoint: str, params: dict) -> dict:
        params["access_token"] = self.token
        resp = requests.get(f"{GRAPH_BASE}/{endpoint}", params=params, timeout=15)
        resp.raise_for_status()
        return resp.json()

    def get_daily_metrics(self) -> dict:
        """
        Retorna un dict con las métricas del día:
          - seguidores, publicaciones_nuevas, likes_total,
            comentarios_total, alcance_estimado, post_urls, metodo
        """
        if not self.token or not self.user_id:
            logger.warning("Instagram: credenciales no configuradas.")
            return {"metodo": "Sin credenciales"}

        try:
            # 1. Datos básicos de la cuenta
            perfil = self._get(
                self.user_id,
                {"fields": "followers_count,media_count"},
            )
            seguidores = perfil.get("followers_count", "")

            # 2. Posts de las últimas 24 horas
            media = self._get(
                f"{self.user_id}/media",
                {
                    "fields": "id,timestamp,like_count,comments_count,permalink",
                    "limit":  20,
                },
            )
            posts = media.get("data", [])

            corte      = datetime.now(tz=timezone.utc) - timedelta(hours=24)
            posts_hoy  = []
            for post in posts:
                ts = post.get("timestamp", "")
                if ts:
                    fecha_post = datetime.fromisoformat(ts.replace("Z", "+00:00"))
                    if fecha_post >= corte:
                        posts_hoy.append(post)

            likes_total      = sum(p.get("like_count", 0)     for p in posts_hoy)
            comentarios_total = sum(p.get("comments_count", 0) for p in posts_hoy)
            post_urls        = " | ".join(p.get("permalink", "") for p in posts_hoy)

            # 3. Alcance (solo disponible en cuentas Business/Creator)
            alcance = ""
            try:
                insights = self._get(
                    f"{self.user_id}/insights",
                    {
                        "metric": "reach",
                        "period": "day",
                    },
                )
                datos = insights.get("data", [])
                if datos:
                    alcance = datos[0].get("values", [{}])[-1].get("value", "")
            except Exception:
                alcance = "N/D"

            return {
                "seguidores":          seguidores,
                "publicaciones_nuevas": len(posts_hoy),
                "likes_total":         likes_total,
                "comentarios_total":   comentarios_total,
                "alcance_estimado":    alcance,
                "post_urls":           post_urls,
                "metodo":              "Meta Graph API v19",
            }

        except Exception as e:
            logger.error(f"Instagram: error al obtener métricas: {e}")
            return {"metodo": f"Error: {e}"}
