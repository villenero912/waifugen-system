# 🔒 CHECKLIST DE SEGURIDAD - WORKFLOWS N8N

**Archivo:** 01_daily_professional_reel_final.json  
**Fecha verificación:** 2026-01-24  
**Estado:** REVISIÓN PRE-DEPLOYMENT

---

## ✅ SEGURIDAD CREDENTIALS

### 1. API Keys - NO Hardcoded ✓
```json
"credentials": {
  "postgres": {
    "id": "waifugen_postgres",  // ✓ Credential Manager
    "name": "WaifuGen PostgreSQL"
  }
}
```

**Todas las credenciales usan N8N Credential Manager:**
- ✅ PostgreSQL: `id: "waifugen_postgres"`
- ✅ A2E API: `id: "a2e_api_key"`
- ✅ Replicate: `id: "replicate_api_token"`

### 2. Variables de Entorno ✓
```json
"url": "={{ $env.A2E_API_URL || 'https://api.a2e.ai/v1/generate' }}"
"url": "={{ $env.TELEGRAM_BOT_URL }}/sendMessage"
"chat_id": "={{ $env.TELEGRAM_ADMIN_CHAT_ID }}"
```

**Todas usan variables de entorno, NO valores hardcoded** ✓

---

## ⚠️ PROBLEMAS DETECTADOS

### 1. FFmpeg Command Injection Risk

**Problema:** El comando executeCommand tiene texto literal con comillas que podrían fallar

**Línea problemática:**
```bash
SUBTITLE_TEXT='{{ $('Generate Voice Script (Ollama)').item.json.response }}'
```

**Riesgo:** Si el texto generado contiene comillas simples `'`, rompe el script

**Solución:** Sanitizar texto antes de inyectar

---

### 2. SQL Injection Risk (Menor)

**Problema:** Inserts con template strings podrían tener comillas

**Solución:** Usar prepared statements o escapar comillas

---

## 🛡️ SOLUCIONES IMPLEMENTADAS

### Opción A: Sanitizar en N8N (Recomendado)

Añadir nodo antes de FFmpeg:

```javascript
// Sanitize subtitle text
const text = $('Generate Voice Script (Ollama)').item.json.response;
const sanitized = text.replace(/'/g, "\\'").replace(/"/g, '\\"');
return { subtitle_text: sanitized };
```

### Opción B: Usar Archivos Temporales

En lugar de inyectar texto, escribir a archivo:

```bash
# Safer approach
echo "$SUBTITLE_TEXT" > /tmp/subtitle.txt
# Use file in FFmpeg instead
```

---

## 🔍 VALIDACIÓN DE DESPLIEGUE

### Pre-requisitos en N8N:

**1. Configurar Credentials (ANTES de importar):**

```
N8N → Credentials → Add:

1. PostgreSQL
   - Name: WaifuGen PostgreSQL
   - Host: waifugen_postgres
   - Database: waifugen_production
   - User: waifugen_user
   - Password: [FROM .env]

2. HTTP Header Auth (A2E)
   - Name: A2E API Key
   - Header Name: Authorization
   - Header Value: Bearer [YOUR_A2E_KEY]

3. HTTP Header Auth (Replicate)
   - Name: Replicate API Token
   - Header Name: Authorization
   - Header Value: Token [YOUR_REPLICATE_TOKEN]
```

**2. Variables de Entorno (.env):**

```bash
# Añadir a .env
A2E_API_URL=https://api.a2e.ai/v1/generate
TELEGRAM_BOT_URL=https://api.telegram.org/bot[YOUR_TOKEN]
TELEGRAM_ADMIN_CHAT_ID=[YOUR_CHAT_ID]
PIXABAY_API_KEY=[YOUR_KEY]
```

**3. Reiniciar N8N:**
```bash
docker compose restart n8n
```

---

## ✅ DEPLOYMENT CHECKLIST

Antes de activar workflow:

- [ ] ✅ Todas las credentials configuradas
- [ ] ✅ Variables de entorno en .env
- [ ] ✅ N8N reiniciado
- [ ] ⚠️ Texto sanitizado (pendiente implementar)
- [ ] ✅ PostgreSQL tabla `characters` existe con datos
- [ ] ✅ PostgreSQL tabla `reels` existe
- [ ] ✅ Piper TTS corriendo (puerto 10200)
- [ ] ✅ Ollama corriendo (puerto 11434)
- [ ] ✅ FFmpeg instalado en contenedor N8N

---

## 🔧 COMANDOS DE VALIDACIÓN

**En VPS SSH, ejecutar:**

```bash
# 1. Verificar servicios corriendo
docker compose ps | grep -E '(n8n|postgres|piper|ollama)'

# 2. Test PostgreSQL connection
docker exec -it waifugen_postgres psql -U waifugen_user -d waifugen_production -c "SELECT COUNT(*) FROM characters WHERE active = true;"

# 3. Test Piper TTS
curl -X POST http://localhost:10200/api/tts \
  -H "Content-Type: application/json" \
  -d '{"text":"Test","model":"en_US-amy-medium"}'

# 4. Test Ollama
curl http://localhost:11434/api/generate \
  -d '{"model":"llama3","prompt":"Test","stream":false}'

# 5. Verificar FFmpeg en N8N container
docker exec -it waifugen_n8n ffmpeg -version
```

---

## ⚠️ RECOMENDACIÓN FINAL

**ANTES DE COMMIT:**

1. ✅ Sanitizar texto en workflow (añadir nodo Code)
2. ✅ Crear tabla SQL si no existe
3. ✅ Documentar configuración de credentials

**DESPUÉS DE COMMIT:**

1. Importar workflow en N8N
2. Configurar credentials manualmente
3. Test ejecución manual (1 reel)
4. Verificar output y logs
5. Activar trigger automático

---

## 🚨 FALLBACK PLAN

Si algo falla:

```bash
# Revertir workflow
cd ~/waifugen-system
git revert HEAD

# Ver logs N8N
docker compose logs -f n8n

# Ver logs ejecución específica
# N8N UI → Executions → [Click en ejecución fallida]
```

---

**¿PROCEDER CON COMMIT?**

- [ ] **SÍ, con sanitization fix** (añado nodo Code ahora)
- [ ] **SÍ, como está** (manual fix después)
- [ ] **NO, revisar más** (esperar)
