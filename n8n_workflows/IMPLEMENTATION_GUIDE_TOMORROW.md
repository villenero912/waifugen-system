# 🚀 GUÍA PASO A PASO - IMPLEMENTACIÓN FINAL (MAÑANA)

**Tiempo estimado total:** 1-2 horas  
**Dificultad:** Media (con esta guía, será fácil)

---

## 📋 CHECKLIST ANTES DE EMPEZAR

Verifica que TODO esté corriendo en el VPS:

```bash
# SSH al VPS
ssh root@72.61.143.251
# Password: Veranoazul82@_

# Verificar servicios
docker compose ps
```

**Deberías ver:**
- ✅ `waifugen_postgres` - Up (healthy)
- ✅ `waifugen_redis` - Up (healthy)
- ✅ `waifugen_ollama` - Up
- ✅ `waifugen_piper` - Up
- ✅ `waifugen_n8n` - Up
- ✅ `waifugen_nginx` - Up 21 hours

**Si algo NO está Up, ejecuta:**
```bash
docker compose restart
```

---

## PASO 1: ACTUALIZAR VPS CON ÚLTIMO CÓDIGO (5 min)

**En SSH del VPS:**

```bash
cd ~/waifugen-system

# Descargar últimos cambios de GitHub
git pull origin master

# Verificar que llegaron los workflows
ls n8n_workflows/

# Deberías ver:
# - 01_daily_professional_reel_final.json
# - SECURITY_DEPLOYMENT_CHECKLIST.md
# - COMPLETE_SYSTEM_ANALYSIS_FINAL.md
# - etc.
```

✅ **Confirmación:** Si ves los archivos, continúa al Paso 2

---

## PASO 2: VERIFICAR Y COMPLETAR TABLAS EN POSTGRESQL (5 min)

**El schema principal YA está creado en `docker/init.sql` con:**
- ✅ 26 tablas (subscribers, revenue, DM automation, analytics, etc.)
- ✅ Triggers automáticos (update_timestamp)
- ✅ Funciones (calculate_subscriber_ltv)
- ✅ Views (engagement_leaderboard, content_ranking)
- ✅ Índices de performance

**SOLO necesitas añadir 2 tablas de Fase 1:**

**En SSH del VPS:**

```bash
# Conectar a PostgreSQL
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production
```

**Ejecuta este SQL (SOLO falta esto):**

```sql
-- Tabla de personajes (Fase 1)
CREATE TABLE IF NOT EXISTS characters (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  trigger_word VARCHAR(50) NOT NULL,
  age INT NOT NULL,
  style TEXT NOT NULL,
  personality TEXT NOT NULL,
  voice_settings JSONB,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla de reels generados (Fase 1)
CREATE TABLE IF NOT EXISTS reels (
  id SERIAL PRIMARY KEY,
  character_id INT REFERENCES characters(id),
  video_prompt TEXT NOT NULL,
  voice_script TEXT NOT NULL,
  theme VARCHAR(100),
  mood VARCHAR(100),
  platform VARCHAR(50) NOT NULL,
  duration INT NOT NULL,
  video_path TEXT,
  nsfw_level INT DEFAULT 0,
  credits_used INT,
  cost_usd DECIMAL(10,4),
  status VARCHAR(50) NOT NULL,
  has_subtitles BOOLEAN DEFAULT false,
  has_music BOOLEAN DEFAULT false,
  production_quality VARCHAR(50),
  created_at TIMESTAMP DEFAULT NOW()
);

-- Insertar 4 personajes Elite de Fase 1
INSERT INTO characters (id, name, trigger_word, age, style, personality, active) VALUES
(1, 'Miyuki Sakura', 'miysak_v1', 22, 'elegant, soft features', 'sweet, encouraging, girlfriend experience', true),
(16, 'Hana Nakamura', 'hannak_v1', 22, 'floral spring aesthetic, ethereal', 'gentle, nurturing, emotional', true),
(10, 'Airi Neo', 'airneo_v1', 24, 'cyborg, cyber-kimono, futuristic', 'energetic, tech-savvy, confident', true),
(5, 'Aiko Hayashi', 'aikoch_v1', 24, 'minimalist, professional, elegant', 'professional, warm, sophisticated', true)
ON CONFLICT (id) DO NOTHING;

-- Verificar personajes
SELECT id, name, trigger_word, active FROM characters;

-- Verificar todas las tablas del sistema
\dt

-- Salir
\q
```

✅ **Confirmación:** 
- Deberías ver 4 personajes: Miyuki, Hana, Airi, Aiko
- Deberías ver +28 tablas (26 de Fase 2 + 2 nuevas)

---

## PASO 3: CONFIGURAR VARIABLES DE ENTORNO (5 min)

**En SSH del VPS:**

```bash
cd ~/waifugen-system

# Editar .env
nano .env
```

**Añade estas líneas AL FINAL del archivo:**

```bash
# A2E API
A2E_API_URL=https://api.a2e.ai/v1/generate

# Telegram Notifications (SUSTITUYE con tus valores reales)
TELEGRAM_BOT_URL=https://api.telegram.org/bot[TU_BOT_TOKEN_AQUI]
TELEGRAM_ADMIN_CHAT_ID=[TU_CHAT_ID_AQUI]

# Pixabay Music
PIXABAY_API_KEY=[TU_PIXABAY_KEY_AQUI]
```

**Guardar:**
- Presiona `Ctrl + O`
- Presiona `Enter`
- Presiona `Ctrl + X`

**Reiniciar N8N para cargar variables:**
```bash
docker compose restart n8n

# Esperar 10 segundos
sleep 10

# Verificar que está corriendo
docker compose ps n8n
```

✅ **Confirmación:** N8N debe estar "Up"

---

## PASO 4: ABRIR N8N EN NAVEGADOR (2 min)

**En tu PC Windows, abre navegador:**

```
http://72.61.143.251:5678
```

**Primera vez:**
- Te pedirá crear cuenta
- Usuario: `admin@waifugen.local`
- Password: `[ELIGE UNA SEGURA Y GUÁRDALA EN BITWARDEN]`
- Email: `admin@waifugen.local`

**Ya configurado antes:**
- Haz login con tus credenciales

✅ **Confirmación:** Deberías ver el dashboard de N8N

---

## PASO 5: CONFIGURAR CREDENTIALS EN N8N (15 min)

**En N8N Web UI:**

### 5A. PostgreSQL Credential

1. Click **"Credentials"** (menú izquierdo)
2. Click **"Add Credential"**
3. Busca y selecciona **"Postgres"**
4. Rellena:
   - **Name:** `WaifuGen PostgreSQL`
   - **Host:** `waifugen_postgres`
   - **Database:** `waifugen_production`
   - **User:** `waifugen_user`
   - **Password:** `[TU_PASSWORD del .env]`
   - **Port:** `5432`
   - **SSL:** `Disable`
5. Click **"Test"** (debe decir "Connection successful")
6. Click **"Save"**

### 5B. A2E API Key Credential

1. Click **"Add Credential"** de nuevo
2. Selecciona **"Header Auth"**
3. Rellena:
   - **Name:** `A2E API Key`
   - **Header Name:** `Authorization`
   - **Header Value:** `Bearer [TU_A2E_API_KEY]`
4. Click **"Save"**

### 5C. Replicate API Token Credential

1. Click **"Add Credential"** de nuevo
2. Selecciona **"Header Auth"**
3. Rellena:
   - **Name:** `Replicate API Token`
   - **Header Name:** `Authorization`
   - **Header Value:** `Token [TU_REPLICATE_TOKEN]`
4. Click **"Save"**

✅ **Confirmación:** Deberías tener 3 credentials guardadas

---

## PASO 6: IMPORTAR WORKFLOW EN N8N (5 min)

**En N8N Web UI:**

### 6A. Copiar JSON del Workflow

**En tu PC Windows, PowerShell:**

```powershell
# Leer el archivo workflow
Get-Content "C:\Users\Sebas\Downloads\package (1)\waifugen_system\n8n_workflows\01_daily_professional_reel_final.json" | Set-Clipboard

Write-Host "✓ JSON copiado al portapapeles"
```

### 6B. Importar en N8N

1. En N8N, click **"Workflows"** (menú izquierdo)
2. Click **"Add Workflow"** (+)
3. Click **"⋮"** (3 puntos arriba a la derecha)
4. Click **"Import from File"**
5. Pega el JSON (Ctrl + V)
6. Click **"Import"**

✅ **Confirmación:** El workflow debería aparecer con 13 nodos conectados

---

## PASO 7: VERIFICAR CONEXIONES DEL WORKFLOW (5 min)

**En el workflow importado, verifica que TODO esté VERDE:**

### Nodos que DEBEN estar verdes (✓):
1. Trigger 4x Daily (JST) - ✓
2. Determine Content Slot - ✓
3. Get Character from PostgreSQL - ⚠️ (podría ser rojo si credential mal configurada)
4. Generate Video Prompt (Ollama) - ✓
5. Generate Voice Script (Ollama) - ✓
6. Generate Video (A2E Pro) - ⚠️ (rojo si credential falta)
7. Generate Voice (Piper TTS) - ✓
8. Search Music (Pixabay) - ✓
9. Check Pixabay Results - ✓
10. Download Music (Pixabay) - ✓
11. Generate Music (Replicate) - ⚠️ (rojo si credential falta)
12. **Sanitize Text (Security)** - ✓
13. FFmpeg Professional Montage (Secured) - ✓
14. Save Reel to PostgreSQL - ⚠️ (rojo si credential mal)
15. Telegram Notification - ✓

**Si algo está ROJO:**
- Click en el nodo rojo
- Verifica que la credential esté seleccionada
- Si no aparece, selecciona la credential del dropdown

✅ **Confirmación:** TODOS los nodos están VERDES

---

## PASO 8: TEST MANUAL DEL WORKFLOW (10 min)

**En N8N:**

1. Click **"Test Workflow"** (botón play arriba a la derecha)
2. Click **"Execute Workflow"**

**Lo que DEBERÍA pasar (tarda ~2-5 min):**

```
✓ Trigger ejecutado
✓ Slot determinado (08:00 = Miyuki Sakura)
✓ Character obtenido desde PostgreSQL
✓ Video prompt generado (Ollama)
✓ Voice script generado (Ollama)
✓ Video generación iniciada (A2E) - ESTO TARDA 1-3 MIN
✓ Voice generada (Piper)
✓ Música descargada (Pixabay o Replicate)
✓ Texto sanitizado
✓ FFmpeg montaje ejecutado
✓ Guardado en PostgreSQL
✓ Telegram notificación enviada
```

**SI TODO FUNCIONA:**
- ✅ Verás TODAS las flechas verdes
- ✅ Deberías recibir notificación en Telegram
- ✅ En PostgreSQL habrá 1 registro nuevo en tabla `reels`

**SI ALGO FALLA:**
- ❌ Click en el nodo que falló
- ❌ Lee el error en el panel derecho
- ❌ Corrígelo según el error (credential, variable de entorno, etc.)

---

## PASO 9: ACTIVAR WORKFLOW AUTOMÁTICO (2 min)

**SOLO SI EL TEST FUNCIONÓ:**

1. En N8N, click **"Inactive"** (toggle arriba)
2. Cambiará a **"Active"** (verde)

**¡LISTO!**

El workflow ahora correrá automáticamente:
- **08:00 JST** (00:00 UTC) - Miyuki Sakura en TikTok
- **12:00 JST** (04:00 UTC) - Hana Nakamura en Instagram
- **18:00 JST** (10:00 UTC) - Airi Neo en YouTube
- **21:00 JST** (13:00 UTC) - Aiko Hayashi en TikTok

✅ **Confirmación:** Toggle está en "Active" (verde)

---

## PASO 10: MONITOREAR PRIMERA EJECUCIÓN AUTOMÁTICA (Esperar hasta próxima hora programada)

**Ver ejecuciones:**

1. En N8N, click **"Executions"** (menú izquierdo)
2. Espera hasta la próxima hora programada (00:00, 04:00, 10:00, o 13:00 UTC)
3. Debería aparecer una nueva ejecución

**Ver reels generados en PostgreSQL:**

**En SSH del VPS:**
```bash
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production -c "SELECT id, character_id, theme, platform, status, created_at FROM reels ORDER BY created_at DESC LIMIT 10;"
```

✅ **Confirmación:** Ves nuevos reels en la tabla

---

## 🎉 ¡SISTEMA 100% FUNCIONAL!

**Si llegaste aquí, tienes:**
- ✅ 4 reels generados automáticamente cada día
- ✅ Con subtítulos profesionales
- ✅ Con música de fondo
- ✅ Con efectos de color grading
- ✅ 100% automático
- ✅ Gastando exactamente 60 créditos/día ($9.90/mes)

---

## 🚨 TROUBLESHOOTING

### Problema: "Cannot connect to PostgreSQL"
**Solución:**
```bash
docker compose restart postgres
docker compose logs postgres
```

### Problema: "A2E API authentication failed"
**Solución:**
- Verifica A2E API Key en N8N Credentials
- Debe tener formato: `Bearer sk-...`

### Problema: "Ollama timeout"
**Solución:**
```bash
docker compose restart ollama
docker compose logs ollama
```

### Problema: "Piper TTS not responding"
**Solución:**
```bash
docker compose restart piper
curl http://localhost:10200/api/tts -X POST -d '{"text":"test","model":"en_US-amy-medium"}'
```

### Problema: "FFmpeg command failed"
**Solución:**
- Verifica que N8N container tenga FFmpeg instalado:
```bash
docker exec -it waifugen_n8n ffmpeg -version
```

---

## 📞 SI NECESITAS AYUDA MAÑANA

**Documenta el error:**
1. Captura de pantalla del nodo que falla
2. Copia el mensaje de error completo
3. Muéstramelo y te ayudo a corregirlo

---

## ✅ RESUMEN DE PASOS

1. ✅ Actualizar VPS (git pull)
2. ✅ Crear tablas PostgreSQL + insertar 4 personajes
3. ✅ Añadir variables de entorno (.env)
4. ✅ Abrir N8N (http://72.61.143.251:5678)
5. ✅ Crear 3 credentials (PostgreSQL, A2E, Replicate)
6. ✅ Importar workflow JSON
7. ✅ Verificar conexiones (todo verde)
8. ✅ Test manual (ejecutar 1 vez)
9. ✅ Activar workflow (si test OK)
10. ✅ Monitorear primera ejecución automática

**Tiempo total:** 1-2 horas (con calma)

---

**¡MAÑANA SERÁ FÁCIL CON ESTA GUÍA!** 🚀
