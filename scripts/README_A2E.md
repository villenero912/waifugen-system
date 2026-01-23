# A2E Pro - Quick Start

## 🚀 Uso Rápido

### 1. Ver Créditos
```bash
python scripts/a2e_helpers.py credits
```

### 2. Generar Reel de Prueba
```bash
# Con Miyuki Sakura (default)
python scripts/a2e_helpers.py test

# Con otro personaje
python scripts/a2e_helpers.py test --character airi_neo
python scripts/a2e_helpers.py test --character hana_nakamura
python scripts/a2e_helpers.py test --character aiko_hayashi
```

### 3. Generar 4 Reels en Batch (Producción)
```bash
python scripts/a2e_helpers.py batch
```

### 4. Reporte Diario
```bash
python scripts/a2e_helpers.py report
```

---

## 📊 Output Esperado

### Credits
```
💳 Verificando créditos A2E...

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  Plan: PRO
  Total: 3,600 créditos
  Usados: 1,200 créditos
  Restantes: 2,400 créditos
  Uso: 33.3%
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

📹 Reels posibles (Seedance 720p): 40
```

### Batch Generation
```
🎯 Generación en Batch: 4 Reels Diarios

✅ Créditos suficientes (2,400)

📋 Configuración de reels:

   1. Morning              | miyuki_sakura   | 60 créditos
   2. Afternoon            | hana_nakamura   | 60 créditos
   3. Evening              | airi_neo        | 60 créditos
   4. Night (Premium)      | aiko_hayashi    | 75 créditos

   TOTAL: 255 créditos

📊 Resultados:

   1. ✅ Morning: Job abc123...
   2. ✅ Afternoon: Job def456...
   3. ✅ Evening: Job ghi789...
   4. ✅ Night (Premium): Job jkl012...

✅ Exitosos: 4/4
💰 Créditos usados: ~255
💡 Ahorro con batch: ~18 créditos (15%)
```

---

## 💰 Costos

- **Reel individual:** 60-75 créditos (~$0.66-0.83)
- **4 reels/día:** 255 créditos (~$2.81)
- **Mes completo:** 7,650 créditos (~$84)
- **Con optimizaciones:** ~$42/mes (50% ahorro)

---

## ⚠️ Troubleshooting

### Error: A2E_API_KEY not set
```bash
# Windows PowerShell
$env:A2E_API_KEY="tu_api_key"

# Linux/Mac
export A2E_API_KEY="tu_api_key"

# O crear .env
echo "A2E_API_KEY=tu_api_key" >> .env
```

### Error: Créditos insuficientes
```bash
# Opción 1: Comprar topup
# https://a2e.ai/billing

# Opción 2: Reducir a 3 reels
# (comentar 1 slot en batch)

# Opción 3: Usar modelo económico
# wan_2.5_480p = 35 créditos
```

---

## 📞 Ayuda

```bash
python scripts/a2e_helpers.py --help
```
