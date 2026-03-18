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
    """
    Métricas de Twitter/X.
    Como la API gratuita no permite lectura, el agente crea la fila
    con la fecha del día y deja los campos para carga manual.
    """

    def __init__(self):
        self.username = os.environ.get("TWITTER_USERNAME", "cpmigratorias")

    def get_daily_metrics(self) -> dict:
        """
        Retorna una fila con la fecha y campos vacíos para carga manual.
        El usuario completa los datos desde el perfil de @cpmigratorias.
        """
        logger.info(
            "Twitter/X: generando fila para carga manual. "
            f"Completar en la planilla los datos de @{self.username}."
        )
        return {
            "seguidores":       "→ COMPLETAR MANUALMENTE",
            "tweets_nuevos":    "→ COMPLETAR MANUALMENTE",
            "likes_total":      "→ COMPLETAR MANUALMENTE",
            "retweets_total":   "→ COMPLETAR MANUALMENTE",
            "respuestas_total": "→ COMPLETAR MANUALMENTE",
            "impresiones":      "N/D",
            "tweet_urls":       f"https://twitter.com/{self.username}",
            "metodo":           "Carga manual — ver perfil @cpmigratorias",
        }
