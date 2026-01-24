# 🔐 GUÍA DE IMPORTACIÓN SEGURA - N8N WORKFLOWS

**Workflow:** Daily Content Generator  
**Archivo:** `01_daily_content_generator.json`  
**Seguridad:** Variables de entorno, sin credenciales hardcodeadas

---

## ✅ CARACTERÍSTICAS DE SEGURIDAD

### 1. Variables de Entorno (NO hardcoded)
- `A2E_API_KEY` → Credencial segura en N8N
- `TELEGRAM_BOT_URL` → Variable de entorno
- `TELEGRAM_ADMIN_CHAT_ID` → Variable de entorno

### 2. Conexiones Docker Internas
- `waifugen_ollama:11434` (red interna)
- `waifugen_piper:10200` (red interna)
- PostgreSQL vía credential manager

### 3. Sin Exposición de Datos
- No logs de credenciales
- Errores no exponen API keys
- Comunicación interna encriptada

---

## 📋 PASO A PASO: IMPORTACIÓN SEGURA

### PASO 1: Acceder a N8N

**En tu navegador:**
```
http://72.61.143.251:5678
```

**Credenciales (configura si es primera vez):**
- Usuario: `admin@waifugen.local`
- Password: (usa una segura, guárdala en Bitwarden)

---

### PASO 2: Configurar Credenciales (ANTES de importar)

#### A. PostgreSQL Credential

1. N8N → **Credentials** → **Add Credential**
2. Tipo: **PostgreSQL**
3. Nombre: `WaifuGen PostgreSQL`
4. Configuración:
   ```
   Host: waifugen_postgres
   Database: waifugen_production
   User: waifugen_user
   Password: [TU_POSTGRES_PASSWORD del .env]
   Port: 5432
   SSL: false
   ```

#### B. A2E API Key Credential

1. N8N → **Credentials** → **Add Credential**
2. Tipo: **Header Auth**
3. Nombre: `A2E API Key`
4. Configuración:
   ```
   Header Name: Authorization
   Header Value: Bearer [TU_A2E_API_KEY]
   ```

---

### PASO 3: Configurar Variables de Entorno

**En el VPS (SSH):**

```bash
cd ~/waifugen-system

# Editar .env
nano .env
```

**Añadir estas líneas:**
```bash
# Telegram Notifications
TELEGRAM_BOT_URL=https://api.telegram.org/bot[TU_BOT_TOKEN]
TELEGRAM_ADMIN_CHAT_ID=[TU_CHAT_ID]

# A2E API
A2E_API_URL=https://api.a2e.ai/v1/generate
```

**Guardar:** Ctrl+O, Enter, Ctrl+X

**Reiniciar N8N:**
```bash
docker compose restart n8n
```

---

### PASO 4: Importar Workflow

1. **Subir archivo al VPS:**

**En PowerShell Windows:**
```powershell
scp "C:\Users\Sebas\Downloads\package (1)\waifugen_system\n8n_workflows\01_daily_content_generator.json" root@72.61.143.251:~/
```

2. **En N8N Web:**
   - Click **"+"** (nuevo workflow)
   - Click **"Import"**
   - Pega el contenido del JSON
   - Click **"Import"**

3. **Verificar conexiones:**
   - Todos los nodos deben estar VERDES
   - Si hay rojos, falta configurar credencial

---

### PASO 5: Crear Tabla de Database (Si no existe)

**En SSH del VPS:**

```bash
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production
```

**Ejecutar SQL:**
```sql
CREATE TABLE IF NOT EXISTS characters (
  id SERIAL PRIMARY KEY,
  name VARCHAR(100) NOT NULL,
  trigger_word VARCHAR(50) NOT NULL,
  age INT NOT NULL,
  style TEXT NOT NULL,
  active BOOLEAN DEFAULT true,
  created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE IF NOT EXISTS reels (
  id SERIAL PRIMARY KEY,
  character_id INT REFERENCES characters(id),
  prompt TEXT NOT NULL,
  video_url TEXT,
  voice_url TEXT,
  platform VARCHAR(50) NOT NULL,
  duration INT NOT NULL,
  status VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Insertar personajes de ejemplo
INSERT INTO characters (name, trigger_word, age, style, active) VALUES
('Miyuki Sakura', 'miysak_v1', 22, 'elegant, soft features', true),
('Airi Neo', 'airneo_v1', 24, 'cyborg, cyber-kimono', true),
('Hana Nakamura', 'hannak_v1', 22, 'floral spring aesthetic', true);

\q
```

---

### PASO 6: Test del Workflow

**En N8N:**

1. Click en el workflow importado
2. Click **"Test Workflow"** (botón play arriba a la derecha)
3. Click **"Execute Workflow"**

**Resultado esperado:**
- ✅ Character seleccionado
- ✅ Prompt generado con Ollama
- ✅ Llamada a A2E iniciada
- ✅ Voz generada con Piper
- ✅ Guardado en PostgreSQL
- ✅ Notificación Telegram enviada

---

### PASO 7: Activar Workflow

**Solo SI el test funciona:**

1. Click **"Active"** (toggle arriba)
2. El workflow ahora correrá automáticamente 4x/día

**Horarios (UTC):**
- 00:00 (madrugada)
- 06:00 (mañana)
- 12:00 (mediodía)
- 18:00 (tarde)

---

## 🔒 CHECKLIST DE SEGURIDAD

Antes de activar en producción, verifica:

- [ ] ✅ Credenciales PostgreSQL configuradas (NO en workflow JSON)
- [ ] ✅ A2E API Key configurada (credential manager)
- [ ] ✅ Variables de entorno en `.env` (Telegram)
- [ ] ✅ Red Docker interna (no expuesta a internet)
- [ ] ✅ N8N accesible solo desde VPS o VPN
- [ ] ✅ Backup de `.env` en Bitwarden
- [ ] ✅ Test ejecutado exitosamente

---

## 🚨 PROBLEMAS COMUNES

### Error: "Cannot connect to PostgreSQL"
**Solución:**
```bash
docker compose ps postgres
```
Verifica que esté "Up" y "healthy"

### Error: "A2E API authentication failed"
**Solución:**
Verifica que la credencial "A2E API Key" tenga:
- Header: `Authorization`
- Value: `Bearer [TU_KEY_REAL]`

### Error: "Ollama not responding"
**Solución:**
```bash
docker compose logs ollama
docker compose restart ollama
```

### Error: "Piper TTS timeout"
**Solución:**
```bash
docker compose ps piper
docker compose restart piper
```

---

## 📊 MONITOREO

**Ver ejecuciones:**
- N8N → **Executions** (panel izquierdo)
- Última ejecución, estado, errores

**Ver logs en VPS:**
```bash
docker compose logs -f n8n
```

**Ver reels generados:**
```bash
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production -c "SELECT id, character_id, platform, status, created_at FROM reels ORDER BY created_at DESC LIMIT 10;"
```

---

## ✅ CONFIRMACIÓN DE DESPLIEGUE

**Workflow desplegado correctamente si:**
- ✅ Aparece en lista de workflows
- ✅ Toggle "Active" está ON (verde)
- ✅ Test manual funciona
- ✅ Ejecuciones automáticas aparecen en log
- ✅ Datos se guardan en PostgreSQL
- ✅ Notificaciones Telegram llegan

---

## 📝 NOTAS IMPORTANTES

**Este workflow NO hace:**
- ❌ Montaje final (eso lo hace `generate_complete_reel.py`)
- ❌ Publicación automática (necesita APIs de redes)
- ❌ Descarga de música (Replicate pendiente)

**Este workflow SÍ hace:**
- ✅ Selecciona personaje aleatorio
- ✅ Genera prompt con IA
- ✅ Inicia generación de video (A2E)
- ✅ Genera voz (Piper)
- ✅ Guarda en database
- ✅ Notifica progreso

**Siguiente paso:** Crear workflow #2 "Video Finalization" para montaje FFmpeg.

---

**¿TODO CLARO? Empieza con PASO 1** 🚀
