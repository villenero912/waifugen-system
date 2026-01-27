# 📂 Dataset de Entrenamiento LoRA: Aiko Hayashi
**ID:** aiko_hayashi
**Trigger Word:** `aikoch_v1`
**Total Imágenes Objetivo:** 20 (Diferentes ángulos/estilos para máxima consistencia)

## 🎯 Configuración de Prompts para Dataset

| ID | Tipo de Plano | Descripción del Prompt | Outfit |
|:---|:---|:---|:---|
| AIKO_01 | Close-up | `aikoch_v1, japanese woman, glasses, stern looking at camera, close-up face, professional office lighting, sharp focus on eyes` | Office Suit |
| AIKO_02 | Medium Shot | `aikoch_v1, japanese woman, wearing a tight pencil skirt and white shirt, standing in a corporate office, city view background, high-end professional aesthetic` | Office Suit |
| AIKO_03 | Full Body | `aikoch_v1, japanese woman, walking through a luxury library, holding a folder, sophisticated style, full body shot, cinematic lighting` | Business Casual |
| AIKO_04 | Side Profile | `aikoch_v1, japanese woman, looking out a window at sunset, profile view, detailed skin textures, soft warm lighting, elegant mood` | Evening Gown |
| AIKO_05 | Sitting Pose | `aikoch_v1, japanese woman, sitting behind a large mahogany desk, crossing legs, black stockings, heels visible, boss persona, authoritative look` | Pencil Skirt |
| AIKO_06 | Emotional | `aikoch_v1, japanese woman, gentle smile, looking away, hair tied in a professional bun, soft library background, cozy atmosphere` | Silk Blouse |
| AIKO_07 | NSFW Level 2 | `aikoch_v1, japanese woman, wearing only a white silk shirt partially unbuttoned, flirty look over glasses, bedroom at night, dim moody lighting` | Teasing |
| AIKO_08 | NSFW Level 4 | `aikoch_v1, japanese woman, black lace lingerie under a blazer, office setting at night, seductive expression, professional yet intimate` | Lingerie/Suit |
| AIKO_09 | Outdoor | `aikoch_v1, japanese woman, standing in a traditional japanese garden, wearing a minimalist black dress, natural sunlight, depth of field` | Summer Dress |
| AIKO_10 | Action | `aikoch_v1, japanese woman, adjusting her glasses, intense focus, office background, modern desk with computer monitors, tech-professional vibe` | Casual Career |

## 🛠️ Instrucciones de Generación para el Dataset

1. **Semilla Única:** Usa la semilla `5588` para todas las imágenes de este set para forzar la consistencia facial.
2. **Modelo Base:** Se recomienda usar **Realistic Vision v5.1** o **Juggernaut XL**.
3. **Resolución:** Generar en 1024x1024 para modelos SDXL o 512x512 (con Hi-Res Fix) para SD1.5.
4. **Etiquetado:** Cada imagen debe acompañarse de un archivo `.txt` con el mismo nombre conteniendo los tags separados por comas (incluyendo `aikoch_v1`).

---
**Estado del Dataset:** *Pendiente de Generación Automatizada via GPU Bridge.*
