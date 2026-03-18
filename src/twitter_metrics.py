"""
Métricas de X / Twitter usando la API oficial v2 (plan gratuito).

Requiere:
  - TWITTER_BEARER_TOKEN  → token de solo lectura
  - TWITTER_USERNAME      → nombre de usuario sin @ (ej: "CPMigratorias")

Plan gratuito incluye:
  ✓ Tweets propios de las últimas 24h
  ✓ Cantidad de seguidores
  ✓ Likes y retweets
  ✗ Impresiones (requiere plan de pago)

Para obtener el token ver README.md → Sección "Configurar Twitter/X API".
"""
import os
import logging
from datetime import datetime, timedelta, timezone

import tweepy
from utils import get_today

logger = logging.getLogger(__name__)


class TwitterMetrics:
    """Obtiene tweets y métricas de la cuenta del CPM en X/Twitter."""

    def __init__(self):
        bearer_token       = os.environ.get("TWITTER_BEARER_TOKEN", "")
        self.username      = os.environ.get("TWITTER_USERNAME", "")
        self.client        = tweepy.Client(bearer_token=bearer_token) if bearer_token else None

    def get_daily_metrics(self) -> dict:
        """
        Retorna un dict con las métricas del día:
          - seguidores, tweets_nuevos, likes_total, retweets_total,
            respuestas_total, impresiones, tweet_urls, metodo
        """
        if not self.client or not self.username:
            logger.warning("Twitter/X: credenciales no configuradas.")
            return {"metodo": "Sin credenciales"}

        try:
            # 1. Obtener el ID del usuario a partir del username
            user_resp = self.client.get_user(
                username=self.username,
                user_fields=["public_metrics"],
            )
            user       = user_resp.data
            user_id    = user.id
            seguidores = user.public_metrics.get("followers_count", "")

            # 2. Obtener tweets de las últimas 24 horas
            corte      = datetime.now(tz=timezone.utc) - timedelta(hours=24)
            tweets_resp = self.client.get_users_tweets(
                id            = user_id,
                start_time    = corte,
                tweet_fields  = ["public_metrics", "created_at"],
                max_results   = 100,
                exclude       = ["retweets", "replies"],   # solo tweets originales
            )

            tweets = tweets_resp.data or []

            likes_total      = 0
            retweets_total   = 0
            respuestas_total = 0
            tweet_urls       = []

            for tweet in tweets:
                m = tweet.public_metrics
                likes_total      += m.get("like_count",   0)
                retweets_total   += m.get("retweet_count", 0)
                respuestas_total += m.get("reply_count",  0)
                tweet_urls.append(
                    f"https://twitter.com/{self.username}/status/{tweet.id}"
                )

            return {
                "seguidores":      seguidores,
                "tweets_nuevos":   len(tweets),
                "likes_total":     likes_total,
                "retweets_total":  retweets_total,
                "respuestas_total": respuestas_total,
                "impresiones":     "N/D (plan gratuito)",
                "tweet_urls":      " | ".join(tweet_urls),
                "metodo":          "Twitter API v2 (plan gratuito)",
            }

        except Exception as e:
            logger.error(f"Twitter/X: error al obtener métricas: {e}")
            return {"metodo": f"Error: {e}"}
