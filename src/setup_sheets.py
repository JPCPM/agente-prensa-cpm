"""
Script de configuración inicial de la Google Sheet.
Crea todas las pestañas con sus encabezados.

Ejecutar UNA SOLA VEZ después de crear la planilla:
    python src/setup_sheets.py
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
load_dotenv()

from sheets_client import SheetsClient

if __name__ == "__main__":
    print("Configurando pestañas en Google Sheets...")
    client = SheetsClient()
    client.setup_tabs()
    print("✓ Pestañas creadas correctamente.")
    print("  Podés abrir la planilla y verificar que aparecen:")
    print("  - Menciones_Medios")
    print("  - Instagram_Metricas")
    print("  - LinkedIn_Metricas")
    print("  - Twitter_X_Metricas")
    print("  - Resumen_Diario")
