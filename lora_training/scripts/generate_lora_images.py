#!/usr/bin/env python3
"""
Script de Generación Batch para Imágenes LoRA
32 Personajes × 5 Plataformas = 160 Imágenes

Uso con Stable Diffusion API:
1. Instala la librería: pip install stable-diffusion-api-client
2. O usa con AUTOMATIC1111 WebUI via API

Este script genera imágenes realistas con configuración optimizada
para entrenamiento de modelos LoRA.

Configuración de Semilla:
- La misma semilla para todas las variantes de un personaje
- Semilla aleatoria para cada nuevo personaje
- Esto mantiene consistencia facial mientras varía el contexto
"""

import os
import json
import random
from datetime import datetime

# Configuración Base para Stable Diffusion
BASE_CONFIG = {
    "width": 1024,
    "height": 1024,
    "steps": 50,           # Mayor calidad = más pasos
    "cfg_scale": 8,        # Adherencia al prompt
    "sampler": "DPM++ 2M Karras",
    "model": "realisticVision_v51.safetensors",  # Modelo para fotos realistas
    "clip_skip": 2,
    "denoising_strength": 0.35,
}

# Configuraciones por Plataforma
PLATFORM_CONFIGS = {
    "Instagram": {
        "width": 1024,
        "height": 1024,
        "aspect_ratio": "1:1",
        "style": "Instagram lifestyle photography, aesthetic feed, high-end filters"
    },
    "Facebook": {
        "width": 1080,
        "height": 1350,
        "aspect_ratio": "4:5",
        "style": "Facebook profile style, friendly and approachable, family-friendly setting"
    },
    "TikTok": {
        "width": 1080,
        "height": 1920,
        "aspect_ratio": "9:16",
        "style": "TikTok vertical video frame, ring light illumination, high energy, content creator aesthetic"
    },
    "YouTube": {
        "width": 1920,
        "height": 1080,
        "aspect_ratio": "16:9",
        "style": "YouTube thumbnail style, expressive face, high contrast, professional studio lighting"
    },
    "Discord": {
        "width": 1024,
        "height": 1024,
        "aspect_ratio": "1:1 (close-up)",
        "style": "Discord avatar PFP style, close-up headshot, gaming setup background"
    }
}

# Prompts por Personaje (estructura simplificada)
# Cada personaje tiene 5 variantes (una por plataforma)
PERSON_PROMPTS = {
    "Miyuki_Sakura": {
        "age": 23,
        "gender": "woman",
        "seed_base": 1001,  # Semilla base para este personaje
        "description": "young Japanese woman, long flowing black hair with subtle purple highlights, warm brown eyes",
        "outfit": "cream-colored oversized knit sweater"
    },
    "Haruto_Tanaka": {
        "age": 28,
        "gender": "man",
        "seed_base": 1002,
        "description": "Japanese man, short neatly styled black hair, dark brown eyes",
        "outfit": "tailored navy blue suit with white dress shirt"
    },
    "Yuki_Watanabe": {
        "age": 21,
        "gender": "woman",
        "seed_base": 1003,
        "description": "Japanese woman, shoulder-length pastel pink hair, large expressive hazel eyes",
        "outfit": "oversized white graphic t-shirt"
    },
    "Kenji_Morimoto": {
        "age": 30,
        "gender": "man",
        "seed_base": 1004,
        "description": "Japanese man, short buzz cut black hair, piercing dark eyes",
        "outfit": "black tactical military uniform with patches"
    },
    "Aiko_Hayashi": {
        "age": 26,
        "gender": "woman",
        "seed_base": 1005,
        "description": "Japanese woman, long straight black hair, deep brown eyes with golden flecks",
        "outfit": "black silk blazer with pearl earrings"
    },
    "Takeshi_Oda": {
        "age": 25,
        "gender": "man",
        "seed_base": 1006,
        "description": "Japanese man, messy dyed blonde highlights on dark hair, dark brown eyes",
        "outfit": "casual black hoodie with gold chain"
    },
    "Sakura_Ito": {
        "age": 24,
        "gender": "woman",
        "seed_base": 1007,
        "description": "Japanese woman, long wavy cherry blossom pink hair, large sparkling violet eyes",
        "outfit": "white lace floral dress with pearl accents"
    },
    "Ryo_Nakamura": {
        "age": 27,
        "gender": "man",
        "seed_base": 1008,
        "description": "Japanese man, undercut hairstyle one side shaved, sharp intense dark eyes",
        "outfit": "black leather jacket over white t-shirt"
    },
    "Mei_Fujiwara": {
        "age": 22,
        "gender": "woman",
        "seed_base": 1009,
        "description": "Japanese woman, short bob cut hair with blunt bangs, large sparkly black eyes",
        "outfit": "cute pink oversized sweater with bear design"
    },
    "Hiroshi_Yamamoto": {
        "age": 35,
        "gender": "man",
        "seed_base": 1010,
        "description": "Japanese man, short salt and pepper hair, kind gentle eyes",
        "outfit": "cozy light gray wool sweater over collared shirt"
    },
    "Yuna_Shimizu": {
        "age": 27,
        "gender": "woman",
        "seed_base": 1011,
        "description": "Japanese woman, long straight black hair, intense focused dark brown eyes",
        "outfit": "tailored black blazer with white silk blouse"
    },
    "Kenta_Fukuda": {
        "age": 24,
        "gender": "man",
        "seed_base": 1012,
        "description": "Japanese man, short spiky black hair, bright energetic smile",
        "outfit": "tight fitted athletic tank top"
    },
    "Akira_Kojima": {
        "age": 29,
        "gender": "woman",
        "seed_base": 1013,
        "description": "Japanese woman, short asymmetric bob cut dyed silver grey, sharp intense dark eyes",
        "outfit": "black leather biker jacket with silver studs"
    },
    "Ren_Ohashi": {
        "age": 32,
        "gender": "man",
        "seed_base": 1014,
        "description": "Japanese man, medium length black hair, thin round glasses",
        "outfit": "cream colored turtleneck sweater"
    },
    "Hana_Nakamura": {
        "age": 20,
        "gender": "woman",
        "seed_base": 1015,
        "description": "Japanese woman, long natural black hair, large innocent brown eyes",
        "outfit": "simple white cotton dress with small blue flowers"
    },
    "Daiki_Sato": {
        "age": 23,
        "gender": "man",
        "seed_base": 1016,
        "description": "Japanese man, short spiky bleached blonde hair, bright confident smirk",
        "outfit": "high school basketball jersey number 23"
    },
    "Mika_Kobayashi": {
        "age": 25,
        "gender": "woman",
        "seed_base": 1017,
        "description": "Japanese woman, long silky straight hair with honey blonde highlights, large elegant brown eyes",
        "outfit": "luxurious white satin slip dress"
    },
    "Takumi_Endou": {
        "age": 31,
        "gender": "man",
        "seed_base": 1018,
        "description": "Japanese man, short military crew cut, piercing intense dark eyes",
        "outfit": "black tactical vest over olive green shirt"
    },
    "Rio_Mizuno": {
        "age": 23,
        "gender": "woman",
        "seed_base": 1019,
        "description": "Japanese woman, sun-bleached beach wavy hair, large bright friendly eyes",
        "outfit": "colorful tropical patterned bikini top with sarong"
    },
    "Jin_Kawasaki": {
        "age": 26,
        "gender": "man",
        "seed_base": 1020,
        "description": "Japanese man, shaved sides with long slicked back dyed silver hair, intense yellow eyes",
        "outfit": "high-tech tactical jacket with glowing circuit patterns"
    },
    "Chiyo_Sasaki": {
        "age": 65,
        "gender": "woman",
        "seed_base": 1021,
        "description": "Japanese woman, traditional updo with ornamental hair pins, gentle wise kind eyes",
        "outfit": "formal navy blue silk kimono with subtle pattern"
    },
    "Kai_Morita": {
        "age": 33,
        "gender": "man",
        "seed_base": 1022,
        "description": "Japanese man, long tangled black hair tied back, thick unkempt beard",
        "outfit": "torn white tank top"
    },
    "Aya_Tomita": {
        "age": 19,
        "gender": "woman",
        "seed_base": 1023,
        "description": "Japanese woman, messy bedhead brown hair, large sleepy droopy eyes",
        "outfit": "oversized big bear onesie pajamas"
    },
    "Shota_Hayashi": {
        "age": 22,
        "gender": "man",
        "seed_base": 1024,
        "description": "Japanese man, trendy two-block haircut with shaved sides, relaxed smirk expression",
        "outfit": "designer oversized beige trench coat"
    },
    "Natsuki_Taniguchi": {
        "age": 28,
        "gender": "woman",
        "seed_base": 1025,
        "description": "Japanese woman, short sharp bob cut with undercut, intense sharp eyes",
        "outfit": "fitted black leather racing suit with sponsor patches"
    },
    "Minato_Sakamoto": {
        "age": 34,
        "gender": "man",
        "seed_base": 1026,
        "description": "Japanese man, neat professional short black hair, thoughtful intelligent expression",
        "outfit": "tailored navy suit with subtle pinstripe"
    },
    "Luna_Tsukino": {
        "age": 21,
        "gender": "woman",
        "seed_base": 1027,
        "description": "Japanese woman, long flowing silver hair, large luminous purple eyes",
        "outfit": "flowing white fantasy gown with silver embroidery"
    },
    "Kaito_Shirakawa": {
        "age": 25,
        "gender": "man",
        "seed_base": 1028,
        "description": "Japanese man, medium-length wavy dark brown hair, hazel eyes with golden flecks",
        "outfit": "crisp white linen shirt"
    },
    "Zara_Chen": {
        "age": 22,
        "gender": "woman",
        "seed_base": 1029,
        "description": "Chinese woman, sleek straight jet black hair, sharp intense dark eyes",
        "outfit": "luxurious black silk slip dress with lace trim"
    },
    "Victor_Williams": {
        "age": 30,
        "gender": "man",
        "seed_base": 1030,
        "description": "African American man, short tapered natural black hair, rich brown eyes",
        "outfit": "tailored charcoal three-piece suit with burgundy silk tie"
    },
    "Sofia_Rossi": {
        "age": 24,
        "gender": "woman",
        "seed_base": 1031,
        "description": "Italian woman, long flowing auburn hair, large expressive green eyes",
        "outfit": "vintage-inspired white lace crop top with puff sleeves"
    },
    "Mateo_Garcia": {
        "age": 27,
        "gender": "man",
        "seed_base": 1032,
        "description": "Hispanic man, medium-length textured brown hair, warm inviting brown eyes",
        "outfit": "crisp white t-shirt under burnt orange casual blazer"
    }
}

def generate_full_prompt(person_data, platform, platform_config):
    """Genera el prompt completo combinando todos los elementos"""
    
    # Construir prompt base
    prompt_parts = [
        f"Portrait photography of a {person_data['description']}",
        f"{person_data['age']} years old",
        f"wearing {person_data['outfit']}",
        "professional headshot style",
        "clean minimalist background",
        "Fujifilm XT-4 photography, sharp focus on eyes",
        "shallow depth of field, bokeh effect, 85mm portrait lens",
        "4K resolution, highly detailed skin texture",
        "professional color grading, photorealistic",
        "high quality, SFW",
        platform_config["style"]
    ]
    
    return ", ".join(prompt_parts)

def generate_negative_prompt():
    """Prompt negativo estándar para evitar defectos"""
    return "blurry, low quality, distorted features, bad anatomy, extra limbs, deformed face, ugly, disfigured, poorly drawn face, mutation, mutated, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, text, watermark"

def create_generation_task(person_name, person_data, platform, seed):
    """Crea una tarea de generación con todos los parámetros"""
    
    platform_config = PLATFORM_CONFIGS[platform]
    
    return {
        "prompt": generate_full_prompt(person_data, platform, platform_config),
        "negative_prompt": generate_negative_prompt(),
        "seed": seed,
        "width": platform_config["width"],
        "height": platform_config["height"],
        "steps": BASE_CONFIG["steps"],
        "cfg_scale": BASE_CONFIG["cfg_scale"],
        "sampler": BASE_CONFIG["sampler"],
        "model": BASE_CONFIG["model"],
        "output_filename": f"{person_name}_{platform.lower()}_{seed}",
        "person_name": person_name,
        "platform": platform
    }

def generate_all_tasks():
    """Genera todas las tareas de generación para 32 personajes × 5 plataformas"""
    
    all_tasks = []
    
    for person_name, person_data in PERSON_PROMPTS.items():
        base_seed = person_data["seed_base"]
        
        for platform in PLATFORM_CONFIGS.keys():
            # Usar la misma semilla base para todas las plataformas del personaje
            # Esto mantiene consistencia facial
            task = create_generation_task(person_name, person_data, platform, base_seed)
            all_tasks.append(task)
    
    return all_tasks

def save_tasks_json(tasks, filename="lora_generation_tasks.json"):
    """Guarda todas las tareas en un archivo JSON"""
    
    output = {
        "generated_at": datetime.now().isoformat(),
        "total_characters": len(PERSON_PROMPTS),
        "total_platforms": len(PLATFORM_CONFIGS),
        "total_images": len(tasks),
        "base_config": BASE_CONFIG,
        "platform_configs": PLATFORM_CONFIGS,
        "tasks": tasks
    }
    
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(output, f, indent=2, ensure_ascii=False)
    
    print(f"✓ Guardados {len(tasks)} tareas en {filename}")
    return output

def print_summary():
    """Imprime resumen de todas las imágenes a generar"""
    
    tasks = generate_all_tasks()
    total = len(tasks)
    
    print("\n" + "="*60)
    print("📊 RESUMEN DE GENERACIÓN LoRA")
    print("="*60)
    print(f"Total de personajes: {len(PERSON_PROMPTS)}")
    print(f"Total de plataformas: {len(PLATFORM_CONFIGS)}")
    print(f"Total de imágenes a generar: {total}")
    print("\n📋 Personajes:")
    for name in sorted(PERSON_PROMPTS.keys()):
        print(f"  • {name}")
    print("\n📱 Plataformas:")
    for platform in PLATFORM_CONFIGS.keys():
        config = PLATFORM_CONFIGS[platform]
        print(f"  • {platform} ({config['aspect_ratio']})")
    print("\n🔧 Configuración:")
    print(f"  • Pasos: {BASE_CONFIG['steps']}")
    print(f"  • CFG Scale: {BASE_CONFIG['cfg_scale']}")
    print(f"  • Resolución: {BASE_CONFIG['width']}x{BASE_CONFIG['height']}")
    print("="*60)

if __name__ == "__main__":
    print_summary()
    tasks = generate_all_tasks()
    save_tasks_json(tasks)
