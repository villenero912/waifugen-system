# 📚 Recursos Completos para Generación de Imágenes LoRA

## 🎯 Resumen del Proyecto

Este proyecto contiene todos los recursos necesarios para generar **160 imágenes realistas** (32 personajes × 5 plataformas) optimizadas para entrenamiento de modelos LoRA.

### 📊 Estadísticas
- **32 Personajes** diversos (edades 19-65, múltiples nacionalidades)
- **5 Plataformas** por personaje (Instagram, Facebook, TikTok, YouTube, Discord)
- **160 Imágenes** totales para dataset LoRA
- **Consistencia** mantenida mediante uso de misma semilla por personaje

## 📁 Estructura de Archivos

```
lora_training/
├── prompts/
│   ├── complete_lora_prompts.md      # Todos los prompts completos
│   └── lora_config.json              # Configuración JSON estructurada
├── scripts/
│   ├── generate_lora_images.py       # Script Python principal
│   └── generate_with_sd_api.sh       # Script Bash para API SD
├── documentation/
│   └── generation_guide.md           # Guía detallada de generación
└── README.md                         # Este archivo
```

## 🚀 Cómo Empezar

### Opción 1: Stable Diffusion WebUI (Más fácil)

1. Abre **complete_lora_prompts.md**
2. Copia los prompts uno por uno
3. Usa la **misma semilla** para todas las plataformas de un personaje
4. Genera y guarda en la carpeta correspondiente

### Opción 2: Generación Automática (Python)

```bash
# Instalar dependencias
pip install requests

# Ejecutar script
python scripts/generate_lora_images.py

# Esto generará el archivo lora_generation_tasks.json
# con todas las tareas organizadas
```

### Opción 3: API de Stable Diffusion

```bash
# Hacer ejecutable el script
chmod +x scripts/generate_with_sd_api.sh

# Verificar que API esté corriendo (por defecto: http://127.0.0.1:7860)
./scripts/generate_with_sd_api.sh test

# Generar todo el dataset
./scripts/generate_with_sd_api.sh generate
```

## 🌱 Clave: Uso de Semillas

### Principio Fundamental
```
MISMA SEMILLA para todas las plataformas de un personaje
SEMILLA DIFERENTE para cada personaje
```

### Ejemplo Práctico

| Personaje | Semilla | Instagram | Facebook | TikTok | YouTube | Discord |
|-----------|---------|-----------|----------|--------|---------|---------|
| Miyuki_Sakura | 1001 | 1001 | 1001 | 1001 | 1001 | 1001 |
| Haruto_Tanaka | 1002 | 1002 | 1002 | 1002 | 1002 | 1002 |
| Luna_Tsukino | 1027 | 1027 | 1027 | 1027 | 1027 | 1027 |

### Por Qué Esto Funciona

1. **Consistencia Facial**: La IA mantiene rasgos faciales similares
2. **Variedad de Contexto**: Diferentes fondos, iluminaciones y estilos
3. **Aprendizaje Eficiente**: LoRA aprende a reconocer el personaje

## ⚙️ Configuración Recomendada

### Stable Diffusion
```json
{
  "width": 1024,
  "height": 1024,
  "steps": 50,
  "cfg_scale": 8,
  "sampler": "DPM++ 2M Karras",
  "model": "realisticVision_v51.safetensors"
}
```

### Modelos Recomendados
1. **realisticVision_v51** - ⭐ Mejor para retratos
2. **Juggernaut_XL** - Buena consistencia
3. **AbsoluteReality** - Muy detallado
4. **EpicRealism** - Equilibrio realismo/detalle

## 📱 Configuración por Plataforma

| Plataforma | Resolución | Formato | Keywords Clave |
|------------|------------|---------|----------------|
| Instagram | 1024×1024 | 1:1 | aesthetic feed, lifestyle |
| Facebook | 1080×1350 | 4:5 | friendly, family-friendly |
| TikTok | 1080×1920 | 9:16 | ring light, high energy |
| YouTube | 1920×1080 | 16:9 | cinematic, thumbnail |
| Discord | 1024×1024 | 1:1 | gaming, RGB neon |

## 📋 Lista de Personajes (32 Total)

### Personajes Japoneses (26)
1. Miyuki_Sakura (23) 🌸
2. Haruto_Tanaka (28) 👔
3. Yuki_Watanabe (21) 🎀
4. Kenji_Morimoto (30) 🎖️
5. Aiko_Hayashi (26) 💼
6. Takeshi_Oda (25) 🧢
7. Sakura_Ito (24) 🌺
8. Ryo_Nakamura (27) 🎸
9. Mei_Fujiwara (22) 🧸
10. Hiroshi_Yamamoto (35) 📚
11. Yuna_Shimizu (27) 💎
12. Kenta_Fukuda (24) 🏀
13. Akira_Kojima (29) 🖤
14. Ren_Ohashi (32) 👓
15. Hana_Nakamura (20) 🌼
16. Daiki_Sato (23) ⛹️
17. Mika_Kobayashi (25) 💅
18. Takumi_Endou (31) 🪖
19. Rio_Mizuno (23) 🏖️
20. Jin_Kawasaki (26) 🤖
21. Chiyo_Sasaki (65) 👘
22. Kai_Morita (33) 🔥
23. Aya_Tomita (19) 😴
24. Shota_Hayashi (22) 🧥
25. Natsuki_Taniguchi (28) 🏎️
26. Minato_Sakamoto (34) 📖

### Personajes Especiales (6)
27. Luna_Tsukino (21) ✨ - Elfa fantástica
28. Kaito_Shirakawa (25) 🌅 - Estilo romántico
29. Zara_Chen (22) 🇨🇳 - China
30. Victor_Williams (30) 🇺🇸 - Afroamericano
31. Sofia_Rossi (24) 🇮🇹 - Italiana
32. Mateo_Garcia (27) 🇲🇽 - Hispano

## 🔧 Solución de Problemas

### ❓ Problema: Rostros inconsistentes
**Solución**: Verifica usar exactamente la misma semilla

### ❓ Problema: Baja calidad
**Solución**: Aumenta steps a 50-70, cfg_scale a 7-9

### ❓ Problema: LoRA no reconoce personaje
**Solución**: Añade más imágenes (mínimo 10-20 recomendado)

### ❓ Problema: Artefactos en ojos
**Solución**: Añade "sharp focus on eyes" al prompt

## 📈 Optimización para LoRA

### Configuración de Entrenamiento
```yaml
learning_rate: 0.0001-0.0002
batch_size: 4-8
max_train_steps: 1000-3000
network_dim: 16-32
alpha: 1.0
```

### Consejos Profesionales
1. ✅ Usa imágenes de alta resolución (512×512 mínimo)
2. ✅ Mantén consistencia en iluminación por personaje
3. ✅ Evita variaciones extremas en pose/ángulo
4. ✅ Etiqueta correctamente cada imagen
5. ✅ Usa imágenes de regularización si hay overfitting

## 📞 Recursos Adicionales

- **Guía Completa**: `documentation/generation_guide.md`
- **Prompts Completos**: `prompts/complete_lora_prompts.md`
- **Configuración JSON**: `prompts/lora_config.json`
- **Script Python**: `scripts/generate_lora_images.py`
- **Script Bash**: `scripts/generate_with_sd_api.sh`

---

**⚠️ Nota**: Este dataset es SFW (Safe For Work). Todos los personajes son adultos claramente identificados por edad.

**🎉 ¡Listo para generar!** Empieza con los prompts en `complete_lora_prompts.md` o usa los scripts automatizados.
