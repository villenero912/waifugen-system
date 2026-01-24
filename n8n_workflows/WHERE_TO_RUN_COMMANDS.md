# 🖥️ GUÍA: DÓNDE EJECUTAR CADA COMANDO

**IMPORTANTE:** Hay 2 entornos diferentes

---

## 🪟 WINDOWS (Tu PC Local) - PowerShell

**Estos comandos SÍ funcionan en Windows PowerShell:**

```powershell
# ✅ Conectar por SSH al VPS
ssh root@72.61.143.251

# ✅ Ver archivos locales
Get-Content "C:\Users\Sebas\Downloads\package (1)\waifugen_system\n8n_workflows\01_daily_professional_reel_final.json"

# ✅ Copiar archivo JSON al portapapeles (para importar en N8N)
Get-Content "C:\Users\Sebas\Downloads\package (1)\waifugen_system\n8n_workflows\01_daily_professional_reel_final.json" | Set-Clipboard
```

**Estos comandos NO funcionan en Windows PowerShell:**
```bash
❌ grep        # No existe en Windows
❌ cat         # No existe en Windows (usa Get-Content)
❌ docker      # Solo funciona si Docker Desktop instalado localmente
❌ \dt         # Comando PostgreSQL, solo en VPS
```

---

## 🐧 VPS LINUX (Servidor remoto) - Bash

**Para ejecutar estos comandos, PRIMERO conecta por SSH:**

### PASO 1: Conectar al VPS

**En PowerShell Windows:**
```powershell
ssh root@72.61.143.251
# Password: Veranoazul82@_
```

**Ahora estás DENTRO del VPS (verás el prompt cambiar a `root@vps:~#`)**

---

### PASO 2: Ejecutar comandos Linux

**Ahora SÍ funcionan estos comandos:**

```bash
# ✅ Ver servicios Docker
docker compose ps

# ✅ Ver tablas PostgreSQL
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production -c "\dt"

# ✅ Ver variables entorno
cat ~/waifugen-system/.env | grep A2E

# ✅ Git pull
cd ~/waifugen-system
git pull origin master

# ✅ Ver logs
docker compose logs n8n
```

---

## 📋 WORKFLOW CORRECTO PARA MAÑANA

### EN WINDOWS (PowerShell):

**1. Conectar al VPS:**
```powershell
ssh root@72.61.143.251
# Introduces password: Veranoazul82@_
```

---

### EN VPS (DESPUÉS del SSH):

**2. Actualizar código:**
```bash
cd ~/waifugen-system
git pull origin master
```

**3. Verificar servicios:**
```bash
docker compose ps
```

**4. Verificar tablas PostgreSQL:**
```bash
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production -c "\dt"
```

**5. Ver cuántas tablas hay (debería mostrar ~26 si init.sql se ejecutó):**
```bash
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production -c "\dt" | wc -l
```

**6. Si faltan tablas characters y reels, crearlas:**
```bash
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production
```

**Dentro de PostgreSQL (prompt cambia a `waifugen_production=#`):**
```sql
-- Crear tablas
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

-- Insertar personajes
INSERT INTO characters (id, name, trigger_word, age, style, personality, active) VALUES
(1, 'Miyuki Sakura', 'miysak_v1', 22, 'elegant, soft features', 'sweet, encouraging, girlfriend experience', true),
(16, 'Hana Nakamura', 'hannak_v1', 22, 'floral spring aesthetic, ethereal', 'gentle, nurturing, emotional', true),
(10, 'Airi Neo', 'airneo_v1', 24, 'cyborg, cyber-kimono, futuristic', 'energetic, tech-savvy, confident', true),
(5, 'Aiko Hayashi', 'aikoch_v1', 24, 'minimalist, professional, elegant', 'professional, warm, sophisticated', true)
ON CONFLICT (id) DO NOTHING;

-- Verificar
SELECT * FROM characters;

-- Salir de PostgreSQL
\q
```

**7. Verificar/añadir variables entorno:**
```bash
cd ~/waifugen-system
cat .env | grep -E "(A2E_API_URL|TELEGRAM|PIXABAY)"
```

**Si NO existen, añadirlas:**
```bash
nano .env

# Añadir al final del archivo:
A2E_API_URL=https://api.a2e.ai/v1/generate
TELEGRAM_BOT_URL=https://api.telegram.org/bot[TU_TOKEN]
TELEGRAM_ADMIN_CHAT_ID=[TU_CHAT_ID]
PIXABAY_API_KEY=[TU_KEY]

# Guardar: Ctrl+O, Enter, Ctrl+X
```

**8. Reiniciar N8N:**
```bash
docker compose restart n8n
```

**9. Cerrar SSH:**
```bash
exit
```

---

### EN WINDOWS NAVEGADOR:

**10. Abrir N8N:**
```
http://72.61.143.251:5678
```

**11. Configurar Credentials** (UI de N8N)

**12. Importar Workflow:**
- En PowerShell Windows:
```powershell
Get-Content "C:\Users\Sebas\Downloads\package (1)\waifugen_system\n8n_workflows\01_daily_professional_reel_final.json" | Set-Clipboard
```
- En N8N: Import → Pegar (Ctrl+V)

**13. Test y Activar**

---

## 🚨 ERROR QUE TUVISTE

**Estabas ejecutando en Windows PowerShell:**
```powershell
grep A2E        # ❌ grep no existe en Windows
docker compose  # ❌ docker no instalado localmente
cat .env        # ❌ cat no existe (usar Get-Content)
\dt             # ❌ comando PostgreSQL, solo en VPS
```

**CORRECTO:**
1. Conectar SSH al VPS
2. Ejecutar comandos DENTRO del VPS
3. Salir SSH cuando termines

---

## 💡 RESUMEN VISUAL

```
TU PC WINDOWS                    VPS LINUX (SSH)
================                 =================
PowerShell                       Bash shell
│                                │
├─ ssh root@72.61.143.251  ─────>├─ docker compose ps
│  (conectar)                    ├─ git pull
│                                ├─ cat .env
│                                ├─ nano .env
│                                └─ docker exec
│
├─ Navegador Web ───────────────>  N8N UI
│  http://72.61.143.251:5678     (configurar, importar)
│
└─ Get-Content archivo.json
   Set-Clipboard
   (copiar workflow)
```

---

**¿AHORA QUEDA CLARO?**

Mañana:
1. Abre PowerShell
2. `ssh root@72.61.143.251`
3. Ejecuta comandos del VPS
4. `exit` cuando termines
5. Abre navegador para N8N

🚀
