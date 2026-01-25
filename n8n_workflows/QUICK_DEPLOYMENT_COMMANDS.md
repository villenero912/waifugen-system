# ⚡ QUICK COMMAND REFERENCE - DEPLOYMENT VPS

**USAR ESTA GUÍA:** Copia y pega los comandos en orden  
**GUÍA COMPLETA:** Ver `DEPLOYMENT_GUIDE_VPS.md`

---

## 🔧 **SETUP EN PC WINDOWS (PowerShell)**

```powershell
# 1. Ir al directorio del proyecto
cd "C:\Users\Sebas\Downloads\package (1)\waifugen_system"

# 2. Ver cambios
git status

# 3. Add, commit, push
git add .
git commit -m "feat: Production deployment with security fixes and Phase 2 workflows"
git push origin main
```

---

## 🖥️ **DEPLOYMENT EN SERVIDOR (SSH)**

### **PASO 1: Conectar y backup**
```bash
ssh root@72.61.143.251
cd ~/waifugen-system

# Backup DB
docker exec waifugen_postgres pg_dump -U waifugen_user -d waifugen_production > backup_$(date +%Y%m%d_%H%M%S).sql

# Backup N8N
docker run --rm -v waifugen_n8n_data:/data -v $(pwd):/backup alpine tar czf /backup/n8n_backup_$(date +%Y%m%d_%H%M%S).tar.gz -C /data .
```

### **PASO 2: Pull código**
```bash
git pull origin main
ls -l n8n_workflows/  # Verificar archivos nuevos
```

### **PASO 3: Actualizar DB**
```bash
# Conectar a PostgreSQL
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production
```

**En PostgreSQL, pega TODO este bloque:**
```sql
-- Tabla characters
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

-- Tabla reels
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

-- Tabla social_comments
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

-- Tabla comment_replies
CREATE TABLE IF NOT EXISTS comment_replies (
  id SERIAL PRIMARY KEY,
  comment_id INT REFERENCES social_comments(id),
  character_id INT REFERENCES characters(id),
  reply_text TEXT NOT NULL,
  sentiment VARCHAR(20),
  platform VARCHAR(50) NOT NULL,
  created_at TIMESTAMP DEFAULT NOW()
);

-- Tabla nsfw_content
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

-- Insertar personajes Elite 8
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

-- Verificar
SELECT id, name, trigger_word FROM characters ORDER BY id;
\dt
\q
```

### **PASO 4: Configurar .env**
```bash
cp .env .env.backup_$(date +%Y%m%d_%H%M%S)
nano .env
```

**Añadir al final:**
```bash
# A2E API
A2E_API_URL=https://api.a2e.ai/v1/generate
A2E_API_KEY=tu_api_key_aqui

# Telegram
TELEGRAM_BOT_URL=https://api.telegram.org/bot<TOKEN>
TELEGRAM_ADMIN_CHAT_ID=tu_chat_id

# Pixabay (opcional)
PIXABAY_API_KEY=tu_key_aqui

# Replicate (opcional)
REPLICATE_API_TOKEN=tu_token_aqui

# RunPod (Fase 2)
RUNPOD_API_KEY=configurar_despues
```

**Guardar:** Ctrl+O, Enter, Ctrl+X

### **PASO 5: Reiniciar servicios**
```bash
docker-compose restart n8n
sleep 10
docker-compose ps  # Verificar todos "Up"
```

---

## 🌐 **CONFIGURAR N8N (Navegador)**

**Abrir:** http://72.61.143.251:5678

### **Credentials a crear:**

1. **PostgreSQL:**
   - Name: `WaifuGen PostgreSQL`
   - Host: `waifugen_postgres`
   - Database: `waifugen_production`
   - User: `waifugen_user`
   - Password: `[TU_PASSWORD]`
   - Port: `5432`
   - SSL: Disable

2. **A2E API Key:**
   - Type: Header Auth
   - Name: `A2E API Key`
   - Header Name: `Authorization`
   - Header Value: `Bearer [TU_A2E_API_KEY]`

3. **Replicate Token:**
   - Type: Header Auth
   - Name: `Replicate API Token`
   - Header Name: `Authorization`
   - Header Value: `Token [TU_REPLICATE_TOKEN]`

---

## 📥 **IMPORTAR WORKFLOWS**

**Para cada workflow, en servidor SSH:**

```bash
# Workflow 01
cat ~/waifugen-system/n8n_workflows/01_daily_content_generator.json

# Workflow 02
cat ~/waifugen-system/n8n_workflows/02_weekly_premium_generator.json

# Workflow 03
cat ~/waifugen-system/n8n_workflows/03_comment_auto_reply.json

# Workflow 05 (NO ACTIVAR - Fase 2)
cat ~/waifugen-system/n8n_workflows/05_nsfw_escalation_manager.json
```

**En N8N:** Workflows → Add → Import from File → Pegar JSON → Save

---

## ✅ **TESTING**

### **Test Workflow 01:**
```
N8N → Abrir "01 - Daily Content Generator"
→ Test Workflow → Execute Workflow
→ Esperar 2-5 min
→ Todas las flechas VERDES ✅
```

### **Verificar en DB:**
```bash
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production -c "SELECT id, character_id, platform, status FROM reels ORDER BY created_at DESC LIMIT 3;"
```

---

## 🚀 **ACTIVAR PRODUCCIÓN**

**Solo si test pasó:**

```
N8N → Workflows
→ Workflow 01 → Toggle "Active"
→ Workflow 02 → Toggle "Active"
→ Workflow 03 → Toggle "Active"
→ Workflow 05 → DEJAR "Inactive" (Fase 2)
```

---

## 📊 **MONITOREO**

### **Ver ejecuciones:**
```
N8N → Executions
```

### **Ver reels del día:**
```bash
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production -c "
SELECT c.name, r.platform, r.duration, r.created_at 
FROM reels r 
JOIN characters c ON r.character_id = c.id 
WHERE DATE(r.created_at) = CURRENT_DATE 
ORDER BY r.created_at DESC;
"
```

### **Logs N8N:**
```bash
docker-compose logs -f --tail=100 n8n
```

---

## 🆘 **ROLLBACK**

### **Si algo falla:**
```bash
# Restaurar DB
cat backup_TIMESTAMP.sql | docker exec -i waifugen_postgres psql -U waifugen_user -d waifugen_production

# Restaurar N8N
docker run --rm -v waifugen_n8n_data:/data -v $(pwd):/backup alpine tar xzf /backup/n8n_backup_TIMESTAMP.tar.gz -C /data

# Reiniciar todo
docker-compose restart
```

---

## ⏰ **HORARIO DE EJECUCIÓN (JST)**

- **08:00** - Miyuki Sakura (TikTok)
- **12:00** - Hana Nakamura (Instagram)
- **18:00** - Airi Neo (YouTube)
- **21:00** - Aiko Hayashi (TikTok)

**Producción:** 4 reels/día × 15s = 60 créditos = $0.33/día

---

## ✅ **CHECKLIST RÁPIDO**

- [ ] Git push desde Windows
- [ ] SSH al servidor + backup
- [ ] Git pull
- [ ] Crear 5 tablas + 8 personajes
- [ ] Configurar .env
- [ ] Restart N8N
- [ ] Crear 3 credentials
- [ ] Importar 4 workflows
- [ ] Test workflow 01
- [ ] Activar 3 workflows (01, 02, 03)
- [ ] Verificar primera ejecución

**Tiempo total:** 45-60 minutos

---

**🎉 ¡Listo para deployment!**
