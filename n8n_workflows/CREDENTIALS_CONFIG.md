# Configuración de Credenciales para n8n

## 1. PostgreSQL - "WaifuGen PostgreSQL"
```
Name: WaifuGen PostgreSQL
Host: postgres
Database: waifugen_prod
User: waifugen_user
Password: WaifuGen2026Secure
Port: 5432
SSL: disabled
```

## 2. Telegram Bot - "Telegram Bot"
```
Name: Telegram Bot
Access Token: YOUR_BOT_TOKEN_FROM_BOTFATHER
```
**⚠️ Reemplazar con tu token real de BotFather**

## 3. A2E API Key - "A2E API Key"
```
Name: A2E API Key
Header Name: Authorization
Header Value: Bearer sk_YOUR_A2E_API_KEY_HERE
```
**⚠️ Reemplazar con tu API key real de A2E**

## 4. Replicate API Token - "Replicate API Token"
```
Name: Replicate API Token
Header Name: Authorization
Header Value: Token r8_YOUR_REPLICATE_TOKEN_HERE
```
**⚠️ Reemplazar con tu token real de Replicate**

---

## Variables de Entorno en n8n

Estas se configuran automáticamente desde el `.env`:
- `TELEGRAM_ADMIN_CHAT_ID` - Tu chat ID de Telegram
- `PIXABAY_API_KEY` - API key de Pixabay (opcional)
- `A2E_API_URL` - URL de la API de A2E (opcional)

---

## Pasos Rápidos

1. Abrir n8n: `http://localhost:5678`
2. Ir a **Credentials** (🔑)
3. Crear cada credencial con los datos de arriba
4. Importar workflow: `01_daily_professional_reel_final.json`
