"""
Funciones de utilidad compartidas por todos los módulos.
"""
from datetime import datetime
import logging

# Configuración de logs para ver qué hace el agente
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)


def get_today() -> str:
    """Retorna la fecha de hoy en formato YYYY-MM-DD."""
    return datetime.now().strftime("%Y-%m-%d")


def get_now() -> str:
    """Retorna fecha y hora actual en formato YYYY-MM-DD HH:MM."""
    return datetime.now().strftime("%Y-%m-%d %H:%M")


def truncate(text: str, max_chars: int = 200) -> str:
    """Corta un texto largo y agrega '...' al final si es necesario."""
    if not text:
        return ""
    text = text.strip()
    return text[:max_chars] + "..." if len(text) > max_chars else text


def deduplicate_by_url(items: list) -> list:
    """Elimina duplicados de una lista de dicts basándose en la clave 'url'."""
    seen = set()
    unique = []
    for item in items:
        url = item.get("url", "")
        if url and url not in seen:
            seen.add(url)
            unique.append(item)
        elif not url:
            # Si no tiene URL, lo incluimos igual (mención sin link)
            unique.append(item)
    return unique
