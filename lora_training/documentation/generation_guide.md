# Guía Completa para Generación de Imágenes LoRA

## 📋 Resumen del Proyecto

- **32 Personajes** × **5 Plataformas** = **160 Imágenes** totales
- Imágenes realistas optimizadas para entrenamiento de modelos LoRA
- Consistencia mantenida mediante uso de **misma semilla por personaje**

## 🎯 Objetivos de Cada Plataforma

| Plataforma | Formato | Resolución | Propósito |
|------------|---------|------------|-----------|
| **Instagram** | 1:1 | 1024×1024 | Feed aesthetic, fotos lifestyle |
| **Facebook** | 4:5 | 1080×1350 | Perfiles, contenido accesible |
| **TikTok** | 9:16 | 1080×1920 | Videos verticales, contenido dinámico |
| **YouTube** | 16:9 | 1920×1080 | Thumbnails, thumbnails cinematográficos |
| **Discord** | 1:1 | 1024×1024 | Avatares, gaming aesthetic |

## ⚙️ Configuración Técnica Recomendada

### Stable Diffusion (AUTOMATIC1111 / ComfyUI)

```json
{
  "width": 1024,
  "height": 1024,
  "steps": 50,
  "cfg_scale": 7-9,
  "sampler": "DPM++ 2M Karras",
  "model": "realisticVision_v51.safetensors",
  "clip_skip": 2,
  "denoising_strength": 0.35,
  "seed": [misma para todas las variantes de un personaje]
}
```

### Modelos Recomendados para Fotos Realistas

1. **realisticVision_v51** - Excelente para retratos realistas
2. **Juggernaut_XL** - Buena consistencia facial
3. **AbsoluteReality** - Muy detallado para rostros
4. **EpicRealism** - Equilibrio entre realismo y detalle

## 🌱 Estrategia de Semillas

### Principio Clave
> **"Misma semilla para un personaje, varía la semilla entre personajes"**

### Por Qué Esto Funciona

1. **Consistencia Facial**: La misma semilla genera estructuras faciales similares
2. **Variedad de Contexto**: Cambiar prompts mantiene variedad en la ropa, fondo, iluminación
3. **Datos Ricos para LoRA**: El modelo aprende los rasgos distintivos del personaje

### Ejemplo de Uso

```python
# Personaje: Miyuki_Sakura
# Semilla base: 1001
Miyuki_Sakura_Instagram = seed(1001)
Miyuki_Sakura_Facebook = seed(1001)
Miyuki_Sakura_TikTok = seed(1001)
Miyuki_Sakura_YouTube = seed(1001)
Miyuki_Sakura_Discord = seed(1001)

# Personaje: Haruto_Tanaka
# Semilla base: 1002
Haruto_Tanaka_Instagram = seed(1002)
# ...etc
```

## 📁 Estructura de Archivos Generada

```
lora_training/
├── prompts/
│   └── complete_lora_prompts.md    # Todos los prompts completos
├── scripts/
│   └── generate_lora_images.py     # Script principal de generación
├── images/
│   ├── Instagram/                  # 32 imágenes (1 por personaje)
│   ├── Facebook/                   # 32 imágenes (1 por personaje)
│   ├── TikTok/                     # 32 imágenes (1 por personaje)
│   ├── YouTube/                    # 32 imágenes (1 por personaje)
│   └── Discord/                    # 32 imágenes (1 por personaje)
└── documentation/
    └── generation_guide.md         # Esta guía
```

## 🚀 Métodos de Generación

### Método 1: Stable Diffusion WebUI (AUTOMATIC1111)

1. Carga el archivo `generate_lora_images.py`
2. Genera cada prompt usando la API de WebUI
3. Guarda las imágenes en la estructura de carpetas

### Método 2: ComfyUI

1. Importa el JSON de tareas generado
2. Ejecuta el workflow batch
3. Las imágenes se guardan automáticamente

### Método 3: API de Stability AI / Replicate

```python
import replicate

output = replicate.run(
    "stability-ai/sdxl:...",
    input={
        "prompt": "tu prompt aquí",
        "width": 1024,
        "height": 1024,
        "num_inference_steps": 50,
        "guidance_scale": 8.0,
        "seed": 1001
    }
)
```

### Método 4: Generación Manual (Copy-Paste)

Usa el archivo `complete_lora_prompts.md` para copiar cada prompt manualmente en tu herramienta favorita.

## 📝 Prompts Negativos Estandarizados

Para todas las imágenes, usa este prompt negativo:

```
blurry, low quality, distorted features, bad anatomy, extra limbs, 
deformed face, ugly, disfigured, poorly drawn face, mutation, mutated, 
worst quality, low quality, normal quality, jpeg artifacts, signature, 
watermark, username, artist name, text, watermark, nsfw
```

## 🎨 Estilos Visuales por Plataforma

### Instagram
- **Keywords**: aesthetic feed, high-end filters, trendy outfit
- **Iluminación**: Soft natural lighting, bokeh background
- **Mood**: Lifestyle photography, aspirational

### Facebook  
- **Keywords**: friendly and approachable, family-friendly
- **Iluminación**: Clear lighting
- **Mood**: Casual everyday look, accessible

### TikTok
- **Keywords**: ring light illumination, high energy, motion blur
- **Iluminación**: Ring light central
- **Mood**: Content creator aesthetic, trendy streetwear

### YouTube
- **Keywords**: expressive face, high contrast, cinematic frame
- **Iluminación**: Professional studio lighting
- **Mood**: Thumbnail ready, vibrant colors

### Discord
- **Keywords**: close-up headshot, gaming setup background
- **Iluminación**: RGB neon accents
- **Mood**: Expressive personality, sharp focus

## ✅ Checklist de Calidad

Antes de usar las imágenes para entrenar LoRA:

- [ ] **Consistencia Facial**: Verifica que cada personaje se vea reconocible
- [ ] **Calidad de Imagen**: Sin artefactos, blur excesivo, o distorsiones
- [ ] **Consistencia de Etiquetas**: Cada imagen tiene el tag del personaje correcto
- [ ] **Variedad Visual**: Hay diferencia entre plataformas del mismo personaje
- [ ] **Formato Consistente**: Todas las imágenes tienen la misma resolución por plataforma
- [ ] **Cantidad Mínima**: Mínimo 10-20 imágenes por personaje para LoRA (aquí: 5 por personaje)

## 🔧 Solución de Problemas

### Problema: Rostros inconsistentes entre plataformas
**Solución**: Verifica que estés usando exactamente la misma semilla

### Problema: Imágenes de baja calidad
**Solución**: Aumenta los steps a 50-70 y usa cfg_scale 7-9

### Problema: El modelo no reconoce al personaje
**Solución**: Aumenta el número de imágenes por personaje (a más imágenes, mejor aprendizaje)

### Problema: Artefactos en los ojos
**Solución**: Añade "sharp focus on eyes" al prompt y usa pasos adicionales

## 📊 Estadísticas del Dataset

| Característica | Valor |
|----------------|-------|
| Total Personajes | 32 |
| Total Imágenes | 160 |
| Rango de Edades | 19-65 años |
| Nacionalidades | Japonés, Chino, Italiano, Hispano, Afroamericano |
| Plataformas | 5 (Instagram, Facebook, TikTok, YouTube, Discord) |

## 🎓 Notas sobre Entrenamiento LoRA

### Configuraciones de Entrenamiento Recomendadas

```yaml
learning_rate: 0.0001-0.0002
batch_size: 4-8
max_train_steps: 1000-3000
network_dim: 16-32  # Para personajes específicos
alpha: 1.0
```

### Consejos para Mejor Resultados

1. **Usa imágenes de alta resolución** (mínimo 512×512, ideal 1024×1024)
2. **Mantén consistencia en iluminación** dentro de cada personaje
3. **Evita variaciones extremas** en pose y ángulo
4. **Etiquetado correcto**: Usa el nombre del personaje en los prompts
5. **Regularización**: Si el modelo overfittea, añade imágenes de regularization

## 📞 Soporte

Para problemas o preguntas sobre la generación:
1. Revisa la sección de solución de problemas
2. Consulta la documentación de Stable Diffusion
3. Ajusta parámetros según tu hardware específico

---

**Nota**: Este dataset está diseñado para uso SFW (Safe For Work). Todos los personajes son adultos o claramente identificados por edad.
