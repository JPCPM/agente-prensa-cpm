# Agente de Prensa - Centro de Políticas Migratorias

Agente que actualiza automáticamente una Google Sheet cada mañana con:
- Apariciones del CPM en medios digitales
- Publicaciones y métricas de Instagram, LinkedIn y X/Twitter

---

## GUÍA DE CONFIGURACIÓN PASO A PASO

> No necesitás saber programar para seguir estos pasos.

---

## PASO 1 — Crear cuenta en GitHub

1. Ir a **https://github.com/signup**
2. Completar email, contraseña y nombre de usuario
3. Verificar el email
4. Una vez dentro, hacer clic en **"New repository"** (botón verde)
5. Nombre: `agente-prensa-cpm`
6. Visibilidad: **Public** (gratis e ilimitado)
7. Click en **"Create repository"**

---

## PASO 2 — Subir el código a GitHub

Abrí una terminal (en Windows: botón derecho en la carpeta → "Abrir en Terminal") y ejecutá:

```bash
cd "C:/Users/jpram/OneDrive/Documents/Agente prensa"
git init
git add .
git commit -m "Primer commit: agente de prensa CPM"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/agente-prensa-cpm.git
git push -u origin main
```

> Reemplazá `TU_USUARIO` por tu nombre de usuario de GitHub.

---

## PASO 3 — Obtener las credenciales de Google Cloud

### 3.1 — Encontrar la Service Account

1. Ir a **https://console.cloud.google.com**
2. En el menú izquierdo → **"IAM y administración"** → **"Cuentas de servicio"**
3. Si ves una cuenta listada, hacé clic en ella
4. Ir a la pestaña **"Claves"**
5. Click **"Agregar clave"** → **"Crear clave nueva"** → **JSON** → **Crear**
6. Se descargará un archivo `.json` — **guardalo en un lugar seguro**

> Si no ves ninguna cuenta de servicio, avisame y te ayudo a crearla desde cero.

### 3.2 — Copiar el contenido del JSON

1. Abrí el archivo `.json` con el Bloc de notas
2. Copiá TODO el contenido (Ctrl+A, Ctrl+C)
3. Lo vas a necesitar en el Paso 5

---

## PASO 4 — Crear la Google Sheet

1. Ir a **https://sheets.google.com**
2. Crear una hoja de cálculo nueva → nombrarla **"Agente Prensa CPM"**
3. Copiar el **ID** de la URL:
   - La URL se ve así: `https://docs.google.com/spreadsheets/d/`**`ESTE_ES_EL_ID`**`/edit`
   - Copiar solo la parte en negrita
4. **Compartir la hoja** con el email de la Service Account (se ve en el JSON como `"client_email"`)
   - Click en "Compartir" → pegar el email → rol: **"Editor"** → Enviar

---

## PASO 5 — Configurar los Secrets en GitHub

En tu repositorio de GitHub:
1. Ir a **Settings** → **Secrets and variables** → **Actions**
2. Click **"New repository secret"** para cada uno:

| Nombre del secret         | Valor                                               |
|--------------------------|-----------------------------------------------------|
| `GOOGLE_SHEET_ID`        | El ID de la planilla (Paso 4)                       |
| `GOOGLE_CREDENTIALS_JSON`| Todo el contenido del archivo JSON (Paso 3.2)       |
| `TWITTER_BEARER_TOKEN`   | (ver Paso 6)                                        |
| `TWITTER_USERNAME`       | Usuario de X sin @ (ej: `CPMigratorias`)            |
| `INSTAGRAM_ACCESS_TOKEN` | (ver Paso 7)                                        |
| `INSTAGRAM_USER_ID`      | (ver Paso 7)                                        |
| `LINKEDIN_ACCESS_TOKEN`  | (ver Paso 8)                                        |
| `LINKEDIN_ORGANIZATION_ID`| (ver Paso 8)                                       |
| `GOOGLE_CSE_API_KEY`     | (ver Paso 9 — opcional)                             |
| `GOOGLE_CSE_ID`          | (ver Paso 9 — opcional)                             |

---

## PASO 6 — Configurar X / Twitter API

**Tiempo estimado: 20 minutos**

1. Ir a **https://developer.twitter.com/en/portal/dashboard**
2. Iniciar sesión con la cuenta del CPM
3. Click **"Create Project"** → Nombre: "CPM Monitor"
4. Elegir **"Read-only"** (solo lectura)
5. Ir a **"Keys and Tokens"** → copiar el **Bearer Token**
6. Guardarlo como secret `TWITTER_BEARER_TOKEN` en GitHub

---

## PASO 7 — Configurar Instagram API

**Tiempo estimado: 30 minutos (+ hasta 1 día de verificación de Meta)**

1. La cuenta de Instagram debe ser **Profesional** (no personal)
   - Instagram → Ajustes → Cuenta → Cambiar a cuenta profesional
2. Ir a **https://developers.facebook.com**
3. **"My Apps"** → **"Create App"** → Tipo: **"Business"**
4. Agregar producto: **"Instagram Graph API"**
5. En el panel, generar un **User Access Token** con permisos:
   - `instagram_basic`, `instagram_manage_insights`
6. Convertirlo a **Long-Lived Token** (válido 60 días):
   ```
   GET https://graph.facebook.com/oauth/access_token
   ?grant_type=fb_exchange_token
   &client_id={APP_ID}
   &client_secret={APP_SECRET}
   &fb_exchange_token={TOKEN_CORTO}
   ```
7. Para obtener el USER_ID:
   ```
   GET https://graph.instagram.com/me?fields=id&access_token={TOKEN}
   ```
8. Guardar como secrets `INSTAGRAM_ACCESS_TOKEN` e `INSTAGRAM_USER_ID`

---

## PASO 8 — Configurar LinkedIn API

**Tiempo estimado: variable (puede requerir aprobación)**

1. Ir a **https://developer.linkedin.com**
2. **"Create app"** → vincular a la página de la organización del CPM
3. Solicitar acceso a **"Community Management API"**
4. Una vez aprobado, generar token OAuth 2.0 con scopes:
   - `r_organization_social`, `r_organization_followers`
5. El **Organization ID** se encuentra en la URL de la página:
   - `https://www.linkedin.com/company/`**`ESTE_ES_EL_ID`**`/`
6. Guardar como `LINKEDIN_ACCESS_TOKEN` y `LINKEDIN_ORGANIZATION_ID`

> **Si LinkedIn demora en aprobar**, el agente igual corre y registra las demás
> fuentes. LinkedIn aparecerá como "Sin credenciales" hasta que se configure.

---

## PASO 9 — Google Custom Search (opcional, mejora el monitoreo de medios)

1. Ir a **https://programmablesearchengine.google.com**
2. **"Agregar"** → en "Sitios para buscar": escribir `*.com.ar` → Crear
3. Copiar el **Search Engine ID**
4. En **https://console.cloud.google.com** → habilitar **"Custom Search API"**
5. Ir a **"Credenciales"** → crear una **API Key**
6. Guardar como `GOOGLE_CSE_API_KEY` y `GOOGLE_CSE_ID`

---

## PASO 10 — Primer test manual

Una vez configurados al menos los secrets de Google Sheets:

1. Ir al repositorio en GitHub → pestaña **"Actions"**
2. Click en **"Actualización Diaria - Agente de Prensa CPM"**
3. Click en **"Run workflow"** → **"Run workflow"**
4. Esperar ~2 minutos y ver el resultado
5. Abrir la Google Sheet y verificar que se crearon las pestañas con datos

---

## ESTRUCTURA DE LA PLANILLA

| Pestaña              | Contenido                                         |
|---------------------|---------------------------------------------------|
| `Menciones_Medios`  | Apariciones en medios digitales (buscadas auto)   |
| `Instagram_Metricas`| Seguidores, posts, likes, comentarios diarios     |
| `LinkedIn_Metricas` | Seguidores, publicaciones, reacciones diarias     |
| `Twitter_X_Metricas`| Seguidores, tweets, likes, retweets diarios       |
| `Resumen_Diario`    | Dashboard con el consolidado del día              |

---

## PREGUNTAS FRECUENTES

**¿Cuándo se ejecuta el agente?**
Todos los días a las 8:00 AM hora argentina. También se puede ejecutar manualmente.

**¿Qué pasa si hay un error un día?**
El agente registra el error en la columna "Notas" del Resumen_Diario y sigue corriendo.
Podés ver el detalle en la pestaña "Actions" de GitHub.

**¿Qué pasa con LinkedIn si no me aprueban el acceso?**
El agente corre igual y registra todo lo demás. LinkedIn queda pendiente hasta que se configure.

**¿Tiene costo?**
No. GitHub Actions, Google Sheets API, Google Custom Search (100/día) y Twitter API (plan gratuito) son todos gratuitos dentro de los límites de uso diario.
