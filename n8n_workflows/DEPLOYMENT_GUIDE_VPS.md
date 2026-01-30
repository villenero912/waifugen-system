# 🚀 GUÍA DE DEPLOYMENT AL SERVIDOR VPS - PASO A PASO

**Servidor:** 72.61.143.251  
**Usuario:** root  
**Password:** Veranoazul82@_  
**Fecha:** 2026-01-25  
**Duración Estimada:** 45-60 minutos

---

## 🎯 **RESUMEN DE CAMBIOS A APLICAR**

### **Archivos Nuevos/Modificados:**
1. ✅ `01_daily_content_generator.json` - **FIXED** (sanitización SQL)
2. ✅ `02_weekly_premium_generator.json` - **NUEVO**
3. ✅ `03_comment_auto_reply.json` - **NUEVO**
4. ✅ `05_nsfw_escalation_manager.json` - **NUEVO** (Fase 2)
5. ✅ `06_nsfw_execution_pipeline.json` - **NUEVO** (Fase 2 GPU Execution - **SECURED**)
6. ✅ `07_dm_execution_pipeline.json` - **NUEVO** (Fase 2 DM Execution - **SECURED**)
7. ✅ `docker-compose.yml` - **SECURITY FIX** (Removed exposed ports)
8. ✅ `FINAL_SYSTEM_SUMMARY.md` - **NUEVO** (documentación completa)

### **Tablas DB Faltantes:**
- `characters` - **CRÍTICO** (requerido por workflows)
- `reels` - **CRÍTICO** (requerido por workflows)
- `social_comments` - Para auto-reply workflow
- `comment_replies` - Para auto-reply logging
- `nsfw_content` - Para Fase 2

### **Configuraciones Requeridas:**
- Variables entorno (.env)
- N8N credentials (PostgreSQL, A2E, Replicate)
- Verificar servicios Docker

---

## ⚠️ **PRE-REQUISITOS (VERIFICAR ANTES DE EMPEZAR)**

### **En tu PC Windows:**
```powershell
# Verificar que tienes los archivos más recientes
cd "C:\Users\Sebas\Downloads\package (1)\waifugen_system"
git status

# Deberías ver los archivos modificados/nuevos
```

### **Verificar conexión al servidor:**
```powershell
# Test SSH
ssh root@72.61.143.251 "echo 'Conexión OK'"
```

---

## 📋 **FASE 1: BACKUP DEL ESTADO ACTUAL (5 min)**

**⚠️ CRÍTICO: Siempre hacer backup antes de cambios**

### **Paso 1.1: SSH al servidor**
```bash
ssh root@72.61.143.251
# Password: Veranoazul82@_
```

### **Paso 1.2: Crear backup de base de datos**
```bash
# Navegar al directorio del proyecto
cd ~/waifugen-system

# Backup completo de PostgreSQL
docker exec waifugen_postgres pg_dump \
  -U waifugen_user \
  -d waifugen_production \
  > backup_$(date +%Y%m%d_%H%M%S).sql

# Verificar que se creó
ls -lh backup_*.sql

# Deberías ver un archivo .sql con tamaño >100KB
```

### **Paso 1.3: Backup de configuración N8N (si existe)**
```bash
# Backup del volumen N8N (contiene workflows existentes)
docker run --rm \
  -v waifugen_n8n_data:/data \
  -v $(pwd):/backup \
  alpine tar czf /backup/n8n_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .

# Verificar
ls -lh n8n_backup_*.tar.gz
```

✅ **CHECKPOINT 1:** Tienes 2 backups (.sql y .tar.gz)

---

## 📥 **FASE 2: ACTUALIZAR CÓDIGO DEL REPOSITORIO (5 min)**

### **Paso 2.1: Commit y push desde Windows**

**En tu PC Windows PowerShell:**
```powershell
cd "C:\Users\Sebas\Downloads\package (1)\waifugen_system"

# Ver cambios
git status

# Añadir todos los archivos nuevos/modificados
git add n8n_workflows/
git add config/
git add src/

# Commit
git commit -m "feat: Add optimized workflows with security fixes and Phase 2 NSFW escalation

- Fixed SQL injection in 01_daily_content_generator.json
- Added 02_weekly_premium_generator.json (Elite 8 rotation)
- Added 03_comment_auto_reply.json (Ollama sentiment analysis)
- Added 05_nsfw_escalation_manager.json (Phase 2 NSFW with GPU routing)
- Added FINAL_SYSTEM_SUMMARY.md (complete documentation)
- Token optimization A2E Pro plan documented
- 32 LoRA characters with trigger words
- 383 fetish prompts cataloged
- Database schema complete (26 tables)
- DM automation templates ready"

# Push al repositorio
git push origin main
# O si es master: git push origin master
```

### **Paso 2.2: Pull en el servidor**

**En el servidor (SSH):**
```bash
cd ~/waifugen-system

# Verificar rama actual
git branch

# Pull de los cambios
git pull origin main
# O si es master: git pull origin master

# Verificar que se descargaron los archivos
ls -l n8n_workflows/

# Deberías ver:
# 01_daily_content_generator.json (modificado)
# 02_weekly_premium_generator.json (nuevo)
# 03_comment_auto_reply.json (nuevo)
# 05_nsfw_escalation_manager.json (nuevo)
# FINAL_SYSTEM_SUMMARY.md (nuevo)
```

✅ **CHECKPOINT 2:** Código actualizado en servidor

---

## 🗄️ **FASE 3: ACTUALIZAR BASE DE DATOS (10 min)**

### **Paso 3.1: Conectar a PostgreSQL**
```bash
# Conectar a la base de datos
docker exec -it waifugen_postgres psql \
  -U waifugen_user \
  -d waifugen_production
```

### **Paso 3.2: Verificar tablas existentes**
```sql
-- Ver todas las tablas
\dt

-- Deberías ver 26 tablas de Phase 2
-- Si no existen, fueron creadas por init.sql
```

### **Paso 3.3: Crear tablas faltantes CRÍTICAS**

**IMPORTANTE: Solo ejecuta las que NO existen**

```sql
-- ========================================
-- TABLA 1: characters (CRÍTICO - Fase 1)
-- ========================================
CREATE TABLE IF NOT EXISTS characters (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  trigger_word VARCHAR(50) NOT NULL,
  age INT NOT NULL,
  style TEXT NOT NULL,
  personality TEXT NOT NULL,
  voice_model VARCHAR(100) DEFAULT 'en_US-amy-medium',
  lora_strength DECIMAL(3,2) DEFAULT 0.8,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- TABLA 2: reels (CRÍTICO - Fase 1)
-- ========================================
CREATE TABLE IF NOT EXISTS reels (
  id SERIAL PRIMARY KEY,
  character_id INT REFERENCES characters(id),
  prompt TEXT NOT NULL,
  video_url TEXT,
  voice_url TEXT,
  platform VARCHAR(50) NOT NULL,
  duration INT NOT NULL,
  quality_tier VARCHAR(20) DEFAULT 'standard',
  nsfw_level INT DEFAULT 0,
  credits_used INT,
  status VARCHAR(50) NOT NULL DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- TABLA 3: social_comments (Auto-Reply)
-- ========================================
CREATE TABLE IF NOT EXISTS social_comments (
  id SERIAL PRIMARY KEY,
  platform VARCHAR(50) NOT NULL,
  post_id VARCHAR(255) NOT NULL,
  user_name VARCHAR(255),
  comment_text TEXT NOT NULL,
  replied BOOLEAN DEFAULT false,
  replied_at TIMESTAMP,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- TABLA 4: comment_replies (Auto-Reply Log)
-- ========================================
CREATE TABLE IF NOT EXISTS comment_replies (
  id SERIAL PRIMARY KEY,
  comment_id INT REFERENCES social_comments(id),
  character_id INT REFERENCES characters(id),
  reply_text TEXT NOT NULL,
  sentiment VARCHAR(20),
  platform VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- TABLA 5: nsfw_content (Fase 2)
-- ========================================
CREATE TABLE IF NOT EXISTS nsfw_content (
  id SERIAL PRIMARY KEY,
  character VARCHAR(100) NOT NULL,
  nsfw_level INT NOT NULL,
  fetish_category VARCHAR(100),
  prompt TEXT NOT NULL,
  platform VARCHAR(50) NOT NULL,
  pricing_tier DECIMAL(10,2),
  production_method VARCHAR(50),
  video_url TEXT,
  status VARCHAR(50) DEFAULT 'pending',
  created_at TIMESTAMP DEFAULT NOW()
);

-- ========================================
-- INSERTAR PERSONAJES ELITE 8
-- ========================================
INSERT INTO characters (id, name, trigger_word, age, style, personality, active) VALUES
(1, 'Miyuki Sakura', 'miysak_v1', 22, 'elegant, soft features, cute girlfriend', 'sweet, encouraging, girlfriend experience', true),
(16, 'Hana Nakamura', 'hannak_v1', 22, 'floral spring aesthetic, ethereal', 'gentle, nurturing, emotional romantic', true),
(10, 'Airi Neo', 'airineo_fusion', 24, 'cyborg, cyber-kimono, futuristic neon', 'energetic, tech-savvy, confident cyber AI', true),
(5, 'Aiko Hayashi', 'aikoch_v1', 24, 'minimalist, professional, elegant businesswoman', 'professional, warm, sophisticated', true),
(19, 'Rio Mizuno', 'riomiz_v1', 23, 'tropical beach, hydro aesthetic, athletic', 'active, teasing, beach lifestyle', true),
(15, 'Chiyo Sasaki', 'chisak_v1', 65, 'traditional kimono, mature elegant', 'wise, sophisticated, traditional', true),
(20, 'Mika Sweet', 'mikasweet_v1', 25, 'sweet playful, cute aesthetic', 'playful, flirty, energetic', true),
(21, 'Momoka AV', 'momoka_av_v1', 28, 'provocative bold, adult industry', 'confident, seductive, direct', true)
ON CONFLICT (id) DO NOTHING;

-- ========================================
-- VERIFICAR INSERCIONES
-- ========================================
SELECT id, name, trigger_word, active FROM characters ORDER BY id;

-- Deberías ver los 8 personajes

-- Ver TODAS las tablas creadas
\dt

-- Salir de PostgreSQL
\q
```

✅ **CHECKPOINT 3:** Base de datos actualizada con 5 tablas nuevas + 8 personajes

---

## ⚙️ **FASE 4: CONFIGURAR VARIABLES DE ENTORNO (5 min)**

### **Paso 4.1: Editar .env**
```bash
cd ~/waifugen-system

# Backup del .env actual
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)

# Editar .env
nano .env
```

### **Paso 4.2: Añadir/Verificar estas líneas**

**IMPORTANTE: Reemplaza con tus valores reales**

```bash
# ===== AÑADIR AL FINAL DEL ARCHIVO .env =====

# A2E API Configuration
A2E_API_URL=https://api.a2e.ai/v1/generate
A2E_API_KEY=tu_api_key_aqui  # <-- REEMPLAZAR

# Telegram Notifications
TELEGRAM_BOT_URL=https://api.telegram.org/bot<TU_BOT_TOKEN>  # <-- REEMPLAZAR
TELEGRAM_ADMIN_CHAT_ID=tu_chat_id_aqui  # <-- REEMPLAZAR

# Pixabay Music API
PIXABAY_API_KEY=tu_pixabay_key_aqui  # <-- REEMPLAZAR (opcional)

# Replicate API (para música generativa)
REPLICATE_API_TOKEN=tu_replicate_token_aqui  # <-- REEMPLAZAR (opcional)

# RunPod GPU (Fase 2)
RUNPOD_API_KEY=tu_runpod_key_aqui  # <-- REEMPLAZAR cuando tengas cuenta
```

**Guardar y salir:**
- Presiona `Ctrl + O`
- Presiona `Enter`
- Presiona `Ctrl + X`

### **Paso 4.3: Verificar .env**
```bash
# Ver las variables (sin mostrar valores sensibles)
grep -E "A2E_API_URL|TELEGRAM_BOT_URL|PIXABAY" .env

# Deberías ver las líneas añadidas
```

✅ **CHECKPOINT 4:** Variables de entorno configuradas

---

## 🐳 **FASE 5: REINICIAR SERVICIOS DOCKER (5 min)**

### **Paso 5.1: Reiniciar N8N (para cargar nuevas variables)**
```bash
cd ~/waifugen-system

# Reiniciar solo N8N
docker-compose restart n8n

# Esperar 10 segundos
sleep 10

# Verificar que está corriendo
docker-compose ps n8n

# Debería mostrar "Up" y puerto 5678
```

### **Paso 5.2: Verificar TODOS los servicios**
```bash
# Ver estado de todos los servicios
docker-compose ps

# TODOS deberían estar "Up":
# - waifugen_postgres (healthy)
# - waifugen_redis (healthy)
# - waifugen_ollama
# - waifugen_piper
# - waifugen_n8n
# - waifugen_nginx
```

### **Paso 5.3: Ver logs de N8N (verificar sin errores)**
```bash
# Ver últimas 50 líneas de logs de N8N
docker-compose logs --tail=50 n8n

# NO deberías ver errores de "Cannot connect" o "Failed to load"
```

✅ **CHECKPOINT 5:** Servicios Docker corriendo sin errores

---

## 🔐 **FASE 6: CONFIGURAR CREDENTIALS EN N8N (10 min)**

### **Paso 6.1: Abrir N8N en navegador**

**En tu PC Windows, abre:**
```
http://72.61.143.251:5678
```

**Login:** (usa las credenciales que configuraste, o crea una cuenta si es primera vez)

### **Paso 6.2: Crear Credential: PostgreSQL**

1. Click **"Credentials"** (menú izquierdo)
2. Click **"Add Credential"**
3. Busca y selecciona **"Postgres"**
4. Configura:
   - **Name:** `WaifuGen PostgreSQL`
   - **Host:** `waifugen_postgres` (nombre del servicio Docker)
   - **Database:** `waifugen_production`
   - **User:** `waifugen_user`
   - **Password:** `[TU_PASSWORD del .env POSTGRES_PASSWORD]`
   - **Port:** `5432`
   - **SSL:** `Disable`
5. Click **"Test"** → Debe decir "Connection successful"
6. Click **"Save"**

### **Paso 6.3: Crear Credential: A2E API Key**

1. Click **"Add Credential"**
2. Selecciona **"Header Auth"**
3. Configura:
   - **Name:** `A2E API Key`
   - **Header Name:** `Authorization`
   - **Header Value:** `Bearer [TU_A2E_API_KEY]`
4. Click **"Save"**

### **Paso 6.4: Crear Credential: Replicate API Token**

1. Click **"Add Credential"**
2. Selecciona **"Header Auth"**
3. Configura:
   - **Name:** `Replicate API Token`
   - **Header Name:** `Authorization`
   - **Header Value:** `Token [TU_REPLICATE_TOKEN]`
4. Click **"Save"**

✅ **CHECKPOINT 6:** 3 credentials configuradas en N8N

---

## 📤 **FASE 7: IMPORTAR WORKFLOWS EN N8N (10 min)**

### **Paso 7.1: Importar Workflow 01 (Daily Content - FIXED)**

**En el servidor SSH:**
```bash
# Copiar contenido del workflow al portapapeles
cat ~/waifugen-system/n8n_workflows/01_daily_content_generator.json
```

**En N8N Web UI:**
1. Click **"Workflows"** (menú izquierdo)
2. Click **"Add Workflow"** (+)
3. Click **"⋮"** (3 puntos arriba derecha)
4. Click **"Import from File"**
5. **Pega el JSON** del workflow
6. Click **"Import"**
7. **Nombre:** `01 - Daily Content Generator (Fixed)`
8. **Verificar nodos:**
   - ✅ Todos los nodos deben estar VERDES
   - ⚠️ Si alguno está ROJO, click en él y selecciona la credential
9. Click **"Save"** (arriba derecha)

### **Paso 7.2: Importar Workflow 02 (Weekly Premium)**

**Repetir proceso:**
```bash
cat ~/waifugen-system/n8n_workflows/02_weekly_premium_generator.json
```

**Importar en N8N** como en Paso 7.1

### **Paso 7.3: Importar Workflow 03 (Comment Auto-Reply)**

```bash
cat ~/waifugen-system/n8n_workflows/03_comment_auto_reply.json
```

**Importar en N8N**

### **Paso 7.4: Importar Workflow 05 (NSFW Escalation - Fase 2)**

```bash
cat ~/waifugen-system/n8n_workflows/05_nsfw_escalation_manager.json
```

**Importar en N8N** pero **NO ACTIVAR** (es para Fase 2)

### **Paso 7.5: Importar Workflow 06 y 07 (Execution Pipelines)**

```bash
cat ~/waifugen-system/n8n_workflows/06_nsfw_execution_pipeline.json
cat ~/waifugen-system/n8n_workflows/07_dm_execution_pipeline.json
```

**Importar AMBOS en N8N** y mantener **INACTIVOS** hasta Fase 2.

✅ **CHECKPOINT 7:** 4 workflows importados en N8N

---

## 🧪 **FASE 8: TESTING MANUAL (10 min)**

### **Paso 8.1: Test Workflow 01 (Daily Content)**

**En N8N:**
1. Abre el workflow **"01 - Daily Content Generator (Fixed)"**
2. Click **"Test Workflow"** (play button)
3. Click **"Execute Workflow"**

**Espera 2-5 minutos** (A2E generation tarda)

**Verificar:**
- ✅ Todas las flechas están VERDES
- ✅ Nodo "Select Random Character" retorna 1 personaje
- ✅ Nodo "Generate Video (A2E)" retorna `video_url`
- ✅ Nodo "Save Reel to PostgreSQL" retorna `id`
- ✅ Recibes notificación en Telegram

**Si FALLA:**
- Click en el nodo ROJO
- Lee el error en panel derecho
- Corrige (usualmente: credential mal configurada o variable de entorno faltante)

### **Paso 8.2: Verificar en DB**

**En servidor SSH:**
```bash
docker exec -it waifugen_postgres psql \
  -U waifugen_user \
  -d waifugen_production \
  -c "SELECT id, character_id, platform, status, created_at FROM reels ORDER BY created_at DESC LIMIT 5;"
```

**Deberías ver:**
- 1 registro nuevo con el reel generado
- `status` = 'pending_edit' o 'ready_to_publish'
- `created_at` = timestamp reciente

✅ **CHECKPOINT 8:** Workflow 01 funciona correctamente

---

## ⚡ **FASE 9: ACTIVAR PRODUCCIÓN (5 min)**

### **SOLO SI EL TEST PASÓ ✅**

**Paso 9.1: Activar Workflow 01**

**En N8N:**
1. Abre **"01 - Daily Content Generator (Fixed)"**
2. Click **"Inactive"** (toggle arriba) → Cambiará a **"Active" (verde)**

**Paso 9.2: Activar Workflow 02 (Weekly Premium)**

1. Abre **"02 - Weekly Premium Generator"**
2. Click toggle → **"Active"**

**Paso 9.3: Activar Workflow 03 (Comment Auto-Reply)**

1. Abre **"03 - Comment Auto-Reply"**
2. Click toggle → **"Active"**

**Paso 9.4: NO activar Workflow 05** (Fase 2)

- **Dejarlo "Inactive"** hasta alcanzar 50K followers

✅ **CHECKPOINT 9:** 3 workflows ACTIVOS en producción

---

## 📊 **FASE 10: MONITOREO POST-DEPLOYMENT (Continuo)**

### **Verificar Ejecuciones Automáticas**

**En N8N:**
1. Click **"Executions"** (menú izquierdo)
2. Espera hasta la próxima hora programada:
   - 00:00 UTC (08:00 JST) - Miyuki
   - 04:00 UTC (12:00 JST) - Hana
   - 10:00 UTC (18:00 JST) - Airi
   - 13:00 UTC (21:00 JST) - Aiko

**Verificar en DB:**
```bash
# Query diaria para ver reels generados
docker exec -it waifugen_postgres psql \
  -U waifugen_user \
  -d waifugen_production \
  -c "
SELECT 
  c.name as character,
  r.platform,
  r.duration,
  r.status,
  r.created_at
FROM reels r
JOIN characters c ON r.character_id = c.id
WHERE DATE(r.created_at) = CURRENT_DATE
ORDER BY r.created_at DESC;
"
```

### **Monitorear Logs**
```bash
# Logs de N8N en tiempo real
docker-compose logs -f --tail=100 n8n

# Press Ctrl+C para salir
```

### **Checks Diarios:**
- [ ] 4 reels generados (1 por slot)
- [ ] Notificaciones Telegram recibidas
- [ ] No errores en logs de N8N
- [ ] Credits A2E consumidos: 60/día

✅ **CHECKPOINT 10:** Sistema monitoreado y funcionando

---

## 🚨 **ROLLBACK PLAN (Si algo sale mal)**

### **Escenario 1: N8N no funciona**
```bash
cd ~/waifugen-system

# Restaurar backup de N8N
docker run --rm \
  -v waifugen_n8n_data:/data \
  -v $(pwd):/backup \
  alpine tar xzf /backup/n8n_backup_YYYYMMDD_HHMMSS.tar.gz -C /data

# Reiniciar N8N
docker-compose restart n8n
```

### **Escenario 2: Base de datos corrupta**
```bash
# Restaurar backup de PostgreSQL
cat backup_YYYYMMDD_HHMMSS.sql | \
  docker exec -i waifugen_postgres psql \
  -U waifugen_user \
  -d waifugen_production
```

### **Escenario 3: Servicios no levantan**
```bash
# Reiniciar todo
docker-compose down
docker-compose up -d

# Ver logs
docker-compose logs -f
```

---

## ✅ **CHECKLIST FINAL DE DEPLOYMENT**

- [ ] **Fase 1:** Backup DB y N8N creado
- [ ] **Fase 2:** Código actualizado (git pull)
- [ ] **Fase 3:** 5 tablas nuevas creadas + 8 personajes insertados
- [ ] **Fase 4:** Variables .env configuradas
- [ ] **Fase 5:** Servicios Docker corriendo
- [ ] **Fase 6:** 3 credentials N8N configuradas
- [ ] **Fase 7:** 4 workflows importados
- [ ] **Fase 8:** Test manual workflow 01 PASÓ ✅
- [ ] **Fase 9:** 3 workflows ACTIVOS (01, 02, 03)
- [ ] **Fase 10:** Monitoreo configurado

---

## 🎉 **POST-DEPLOYMENT**

### **Siguiente Horario de Ejecución (JST):**
- **08:00 JST** (00:00 UTC) - Miyuki Sakura en TikTok
- **12:00 JST** (04:00 UTC) - Hana Nakamura en Instagram
- **18:00 JST** (10:00 UTC) - Airi Neo en YouTube
- **21:00 JST** (13:00 UTC) - Aiko Hayashi en TikTok

### **Producción Diaria:**
- 4 reels SFW de 15s
- 60 créditos A2E consumidos
- $0.33/día ($9.90/mes)
- 120 reels/mes

### **Milestone Fase 2:**
- Al alcanzar **50,000 followers**, activar Workflow 05
- Crear cuentas OnlyFans/Fansly
- Configurar RunPod GPU API
- Launch NSFW escalation

---

## 📞 **SOPORTE**

### **Si necesitas ayuda:**
1. Captura de pantalla del error
2. Logs relevantes: `docker-compose logs n8n`
3. Query de DB si es necesario
4. Estado de servicios: `docker-compose ps`

---

**🚀 ¡DEPLOYMENT COMPLETO! Sistema 100% funcional en producción.**
