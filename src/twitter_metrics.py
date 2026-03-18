"""
Métricas de X / Twitter usando twscrape (gratuito, sin API oficial).

Requiere:
  - TWITTER_USERNAME  → nombre de usuario sin @ (ej: cpmigratorias)
  - TWITTER_EMAIL     → email de la cuenta
  - TWITTER_PASSWORD  → contraseña de la cuenta

twscrape usa la API interna de Twitter/X para obtener datos sin costo.
"""
import os
import asyncio
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

logger = logging.getLogger(__name__)

# Ruta donde twscrape guarda la sesión (para no loguearse cada vez)
DB_PATH = str(Path(__file__).parent.parent / "credentials" / "twscrape.db")


async def _fetch_metrics(username: str, email: str, password: str) -> dict:
    """Función async que obtiene los datos de Twitter/X."""
    import twscrape

    api = twscrape.API(DB_PATH)

    # Agregar cuenta solo si no existe ya en la base de datos
    try:
        await api.pool.add_account(
            username=username,
            password=password,
            email=email,
            email_password="",   # No requerido para la mayoría de cuentas
        )
        await api.pool.login_all()
    except Exception as e:
        logger.debug(f"twscrape login: {e} (puede ser normal si ya estaba logueado)")

    # Obtener datos del usuario
    user = await api.user_by_login(username)
    if not user:
        return {"metodo": "Error: usuario no encontrado"}

    seguidores = user.followersCount

    # Obtener tweets de las últimas 24 horas
    corte      = datetime.now(tz=timezone.utc) - timedelta(hours=24)
    tweets_hoy = []

    async for tweet in api.user_tweets(user.id, limit=50):
        if tweet.date < corte:
            break
        # Excluir retweets
        if tweet.retweetedTweet:
            continue
        tweets_hoy.append(tweet)

    likes_total      = sum(t.likeCount      for t in tweets_hoy)
    retweets_total   = sum(t.retweetCount   for t in tweets_hoy)
    respuestas_total = sum(t.replyCount     for t in tweets_hoy)
    tweet_urls       = [
        f"https://twitter.com/{username}/status/{t.id}" for t in tweets_hoy
    ]

    return {
        "seguidores":       seguidores,
        "tweets_nuevos":    len(tweets_hoy),
        "likes_total":      likes_total,
        "retweets_total":   retweets_total,
        "respuestas_total": respuestas_total,
        "impresiones":      "N/D",
        "tweet_urls":       " | ".join(tweet_urls),
        "metodo":           "twscrape",
    }


class TwitterMetrics:
    """Obtiene tweets y métricas de la cuenta del CPM en X/Twitter."""

    def __init__(self):
        self.username = os.environ.get("TWITTER_USERNAME", "cpmigratorias")
        self.email    = os.environ.get("TWITTER_EMAIL", "")
        self.password = os.environ.get("TWITTER_PASSWORD", "")

    def get_daily_metrics(self) -> dict:
        if not self.email or not self.password:
            logger.warning("Twitter/X: credenciales no configuradas.")
            return {"metodo": "Sin credenciales"}

        try:
            return asyncio.run(
                _fetch_metrics(self.username, self.email, self.password)
            )
        except Exception as e:
            logger.error(f"Twitter/X: error al obtener métricas: {e}")
            return {"metodo": f"Error: {e}"}
