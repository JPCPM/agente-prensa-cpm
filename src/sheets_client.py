"""
Módulo para leer y escribir datos en Google Sheets.
Usa la Service Account de Google Cloud para autenticarse.
"""
import os
import json
import logging
import gspread
from google.oauth2.service_account import Credentials
from utils import get_today, get_now

logger = logging.getLogger(__name__)

# Permisos necesarios para leer/escribir en Sheets y Drive
SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive",
]

# Nombres de las pestañas en la planilla
TAB_MEDIOS     = "Menciones_Medios"
TAB_INSTAGRAM  = "Instagram_Metricas"
TAB_LINKEDIN   = "LinkedIn_Metricas"
TAB_TWITTER    = "Twitter_X_Metricas"
TAB_RESUMEN    = "Resumen_Diario"


class SheetsClient:
    """Maneja toda la comunicación con Google Sheets."""

    def __init__(self):
        sheet_id     = os.environ["GOOGLE_SHEET_ID"]
        creds_json   = os.environ.get("GOOGLE_CREDENTIALS_JSON")   # GitHub Actions
        creds_path   = os.environ.get("GOOGLE_CREDENTIALS_PATH")   # desarrollo local

        if creds_json:
            # GitHub Actions: las credenciales llegan como string JSON
            info  = json.loads(creds_json)
            creds = Credentials.from_service_account_info(info, scopes=SCOPES)
        elif creds_path:
            # Desarrollo local: se usa el archivo .json
            creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        else:
            raise EnvironmentError(
                "No se encontraron credenciales de Google. "
                "Definí GOOGLE_CREDENTIALS_JSON o GOOGLE_CREDENTIALS_PATH."
            )

        client      = gspread.authorize(creds)
        self.book   = client.open_by_key(sheet_id)
        logger.info("Conexión con Google Sheets establecida.")

    # ------------------------------------------------------------------
    # Menciones en medios
    # ------------------------------------------------------------------
    def append_menciones(self, menciones: list):
        """Agrega filas a la pestaña Menciones_Medios."""
        if not menciones:
            logger.info("No hay menciones nuevas para registrar.")
            return
        ws   = self.book.worksheet(TAB_MEDIOS)
        hoy  = get_today()
        ahora = get_now()
        rows = [
            [
                hoy,
                m.get("titulo", ""),
                m.get("medio", ""),
                m.get("tipo_medio", "Digital"),
                m.get("url", ""),
                m.get("resumen", ""),
                m.get("fuente", ""),
                ahora,
                "FALSE",
            ]
            for m in menciones
        ]
        ws.append_rows(rows, value_input_option="USER_ENTERED")
        logger.info(f"Se registraron {len(rows)} menciones en Sheets.")

    # ------------------------------------------------------------------
    # Instagram
    # ------------------------------------------------------------------
    def append_instagram(self, data: dict):
        """Agrega una fila a la pestaña Instagram_Metricas."""
        ws = self.book.worksheet(TAB_INSTAGRAM)
        ws.append_row(
            [
                get_today(),
                data.get("seguidores", ""),
                data.get("publicaciones_nuevas", ""),
                data.get("likes_total", ""),
                data.get("comentarios_total", ""),
                data.get("alcance_estimado", ""),
                data.get("post_urls", ""),
                data.get("metodo", ""),
            ],
            value_input_option="USER_ENTERED",
        )
        logger.info("Métricas de Instagram registradas.")

    # ------------------------------------------------------------------
    # LinkedIn
    # ------------------------------------------------------------------
    def append_linkedin(self, data: dict):
        """Agrega una fila a la pestaña LinkedIn_Metricas."""
        ws = self.book.worksheet(TAB_LINKEDIN)
        ws.append_row(
            [
                get_today(),
                data.get("seguidores", ""),
                data.get("publicaciones_nuevas", ""),
                data.get("reacciones_total", ""),
                data.get("comentarios_total", ""),
                data.get("impresiones", ""),
                data.get("post_urls", ""),
                data.get("metodo", ""),
            ],
            value_input_option="USER_ENTERED",
        )
        logger.info("Métricas de LinkedIn registradas.")

    # ------------------------------------------------------------------
    # Twitter / X
    # ------------------------------------------------------------------
    def append_twitter(self, data: dict):
        """Agrega una fila a la pestaña Twitter_X_Metricas."""
        ws = self.book.worksheet(TAB_TWITTER)
        ws.append_row(
            [
                get_today(),
                data.get("seguidores", ""),
                data.get("tweets_nuevos", ""),
                data.get("likes_total", ""),
                data.get("retweets_total", ""),
                data.get("respuestas_total", ""),
                data.get("impresiones", "N/D (plan gratuito)"),
                data.get("tweet_urls", ""),
                data.get("metodo", ""),
            ],
            value_input_option="USER_ENTERED",
        )
        logger.info("Métricas de Twitter/X registradas.")

    # ------------------------------------------------------------------
    # Resumen diario
    # ------------------------------------------------------------------
    def update_resumen(
        self,
        menciones: list,
        ig: dict,
        li: dict,
        tw: dict,
        estado: str,
        notas: str,
    ):
        """Agrega una fila de resumen al dashboard diario."""
        ws = self.book.worksheet(TAB_RESUMEN)
        ws.append_row(
            [
                get_today(),
                len(menciones),
                sum(1 for m in menciones if m.get("tipo_medio") == "Digital"),
                ig.get("seguidores", ""),
                ig.get("publicaciones_nuevas", ""),
                li.get("seguidores", ""),
                li.get("publicaciones_nuevas", ""),
                tw.get("seguidores", ""),
                tw.get("tweets_nuevos", ""),
                estado,
                notas,
            ],
            value_input_option="USER_ENTERED",
        )
        logger.info(f"Resumen diario registrado. Estado: {estado}")

    # ------------------------------------------------------------------
    # Crear estructura de pestañas si no existe
    # ------------------------------------------------------------------
    def setup_tabs(self):
        """
        Crea las pestañas con sus encabezados si todavía no existen.
        Solo hay que ejecutar esto UNA vez al configurar la planilla.
        """
        tabs_config = {
            TAB_MEDIOS: [
                "Fecha", "Titulo", "Medio", "Tipo_Medio",
                "URL", "Resumen", "Fuente", "Fecha_Recoleccion", "Duplicado",
            ],
            TAB_INSTAGRAM: [
                "Fecha", "Seguidores", "Publicaciones_Nuevas", "Likes_Total",
                "Comentarios_Total", "Alcance_Estimado", "Post_URLs", "Metodo",
            ],
            TAB_LINKEDIN: [
                "Fecha", "Seguidores", "Publicaciones_Nuevas", "Reacciones_Total",
                "Comentarios_Total", "Impresiones", "Post_URLs", "Metodo",
            ],
            TAB_TWITTER: [
                "Fecha", "Seguidores", "Tweets_Nuevos", "Likes_Total",
                "Retweets_Total", "Respuestas_Total", "Impresiones",
                "Tweet_URLs", "Metodo",
            ],
            TAB_RESUMEN: [
                "Fecha", "Total_Menciones", "Medios_Digitales",
                "IG_Seguidores", "IG_Posts",
                "LI_Seguidores", "LI_Posts",
                "TW_Seguidores", "TW_Tweets",
                "Estado_Ejecucion", "Notas",
            ],
        }

        existing = [ws.title for ws in self.book.worksheets()]

        for tab_name, headers in tabs_config.items():
            if tab_name not in existing:
                ws = self.book.add_worksheet(title=tab_name, rows=1000, cols=len(headers))
                ws.append_row(headers)
                logger.info(f"Pestaña '{tab_name}' creada con encabezados.")
            else:
                logger.info(f"Pestaña '{tab_name}' ya existe, no se modifica.")
