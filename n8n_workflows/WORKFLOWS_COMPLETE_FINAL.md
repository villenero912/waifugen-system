# 🎯 WORKFLOWS N8N - SISTEMA COMPLETO WAIFUGEN

**Versión:** 4.0 FINAL DEFINITIVA  
**Incluye:** Fetiches, Ingeniería Social, LoRA Training GPU, Fase 1+2  
**Basado en:** TODOS los archivos JSON/YAML del proyecto

---

## 📋 RESUMEN EJECUTIVO

### TOTAL: 7 WORKFLOWS

**FASE 1 (Inmediato):**
1. ✅ Daily SFW Content (4 reels/día, $0.33/día)
2. ✅ Weekly Premium (1 reel/semana, $0.12)
3. ✅ Comment Auto-Reply
4. ✅ Analytics & Revenue

**FASE 2 (50K+ followers):**
5. ⏸️ NSFW Escalation + Fetish (383 prompts)
6. ⏸️ DM Automation & Social Engineering
7. ⏸️ LoRA Training Manager (GPU RunPod)

---

## 🔥 WORKFLOW 1: DAILY SFW CONTENT GENERATOR

### CONFIGURACIÓN:

```json
{
  "name": "Daily SFW Content - Phase 1",
  "trigger": {
    "type": "cron",
    "schedule": "0 0,4,10,13 * * *",
    "timezone": "Asia/Tokyo"
  },
  "daily_slots": [
    {
      "time_jst": "08:00",
      "time_utc": "00:00",
      "character_id": 1,
      "character": "miyuki_sakura",
      "trigger_word": "miysak_v1",
      "platform": "tiktok",
      "aspect_ratio": "9:16",
      "theme": "Morning motivation",
      "style": "energetic_upbeat",
      "music_genre": "upbeat",
      "energy": "high"
    },
    {
      "time_jst": "12:00",
      "time_utc": "04:00",
      "character_id": 16,
      "character": "hana_nakamura",
      "trigger_word": "hannak_v1",
      "platform": "instagram",
      "aspect_ratio": "9:16",
      "theme": "Midday inspiration",
      "style": "emotional_soft",
      "music_genre": "lofi",
      "energy": "medium"
    },
    {
      "time_jst": "18:00",
      "time_utc": "10:00",
      "character_id": 10,
      "character": "airi_neo",
      "trigger_word": "airneo_v1",
      "platform": "youtube",
      "aspect_ratio": "9:16",
      "theme": "Evening entertainment",
      "style": "cyber_energetic",
      "music_genre": "electronic",
      "energy": "high"
    },
    {
      "time_jst": "21:00",
      "time_utc": "13:00",
      "character_id": 5,
      "character": "aiko_hayashi",
      "trigger_word": "aikoch_v1",
      "platform": "tiktok",
      "aspect_ratio": "9:16",
      "theme": "Night reflection",
      "style": "professional_elegant",
      "music_genre": "chill",
      "energy": "low"
    }
  ],
  "production": {
    "model": "seedance_1.5_pro",
    "resolution": "720p",
    "duration": 15,
    "fps": 30,
    "credits_per_reel": 15,
    "daily_credits": 60,
    "daily_cost": 0.33
  },
  "nsfw_level": 0,
  "compliance": {
    "platforms": ["tiktok", "instagram", "youtube", "facebook"],
    "restrictions": [
      "no_suggestive_content",
      "no_revealing_clothing",
      "no_bedroom_settings",
      "family_friendly_captions"
    ]
  }
}
```

### FLUJO N8N:

```
[Cron Trigger 4x/día]
    ↓
[Determine Current Slot] (JS: compare UTC time)
    ↓
[Get Character from Slot] (JS: extract character config)
    ↓
[Generate Video Prompt] (Ollama)
    Prompt: "{theme} themed reel featuring {character}, {style} mood, {trigger_word}, 9:16 vertical, SFW level 0, bright cheerful, no NSFW"
    ↓
[Generate Voice Script] (Ollama)
    Prompt: "10-second {style} voice script for {character}, {theme}, first person, 25 words max"
    ↓
[Parallel Execution]
    ├─→ [Generate Video A2E] (seedance_1.5_pro, 720p, 15s, 15 credits)
    ├─→ [Generate Voice Piper] (en_US-amy-medium)
    └─→ [Get Music Pixabay] (genre: {music_genre}) 
          IF fail → [Generate Music Replicate] (MusicGen, 15s)
    ↓
[FFmpeg Montage]
    Command: "ffmpeg -i video.mp4 -i voice.wav -i music.mp3 -filter_complex '[1:a]volume=1.0[voice];[2:a]volume=0.3[music];[voice][music]amix=inputs=2[audio]' -map 0:v -map '[audio]' -c:v libx264 -preset medium -crf 23 -c:a aac -b:a 128k -ar 44100 -shortest output.mp4"
    ↓
[Save to PostgreSQL]
    Table: reels
    Fields: character_id, prompt, voice_script, theme, mood, platform, duration, video_path, nsfw_level=0, status='ready_to_publish'
    ↓
[Telegram Notification]
    Message: "✅ Reel {character} generado\nTema: {theme}\nPlataforma: {platform}\nPath: /tmp/reel_*.mp4"
```

**Costo:** $0.33/día = $9.90/mes (Plan Pro completo)

---

## 🌟 WORKFLOW 2: WEEKLY PREMIUM CONTENT

### CONFIGURACIÓN:

```json
{
  "name": "Weekly Premium Content - Featured",
  "trigger": {
    "type": "cron",
    "schedule": "0 12 * * 0",
    "timezone": "Asia/Tokyo"
  },
  "rotation": {
    "week_1": "miyuki_sakura",
    "week_2": "hana_nakamura",
    "week_3": "airi_neo",
    "week_4": "aiko_hayashi",
    "cycle": "repeat"
  },
  "production": {
    "model": "wan_2.5",
    "resolution": "1080p",
    "duration": 15,
    "credits_per_reel": 90,
    "weekly_cost": 0.12
  },
  "platforms": ["tiktok", "instagram", "youtube"],
  "theme": "Weekly highlight - Premium quality"
}
```

**Costo:** ~$0.50/mes (usando buffer mensual de 1800 créditos)

---

## 💬 WORKFLOW 3: COMMENT AUTO-REPLY

### CONFIGURACIÓN:

```json
{
  "name": "Comment Auto-Reply with Ollama",
  "trigger": {
    "type": "polling",
    "interval": "every_5_minutes"
  },
  "platforms": ["tiktok", "instagram", "youtube"],
  "flow": [
    "Scrape new comments (APIs)",
    "Detect language (Ollama)",
    "Analyze sentiment (Ollama: positive/neutral/negative)",
    "Route to character (based on video)",
    "Generate reply (Ollama with character context)",
    "Post reply (API)",
    "Log to PostgreSQL"
  ],
  "character_contexts": {
    "miyuki_sakura": {
      "personality": "sweet, encouraging, cute",
      "signature_phrases": ["Thank you so much! 💕", "You're so sweet!", "Stay positive!"],
      "emoji_usage": "high (💕🌸✨😊)"
    },
    "airi_neo": {
      "personality": "futuristic, energetic, tech-savvy",
      "signature_phrases": ["That's awesome!", "Let's go!", "Future is now!"],
      "emoji_usage": "medium (⚡🤖💫)"
    }
  }
}
```

---

## 📊 WORKFLOW 4: ANALYTICS & REVENUE TRACKING

### CONFIGURACIÓ N:

```json
{
  "name": "Analytics Dashboard & Alerts",
  "trigger": {
    "type": "cron",
    "schedule": "59 23 * * *",
    "timezone": "Asia/Tokyo"
  },
  "metrics_collected": {
    "production": {
      "reels_generated": "COUNT(*) FROM reels WHERE created_at >= NOW() - INTERVAL '1 day'",
      "credits_consumed": "SUM(credits_used)",
      "cost_per_reel": "AVG(cost)",
      "failed_generations": "COUNT(*) WHERE status = 'failed'"
    },
    "engagement": {
      "total_views": "SUM(views)",
      "total_likes": "SUM(likes)",
      "total_comments": "SUM(comments)",
      "engagement_rate": "(likes + comments) / views * 100"
    },
    "growth": {
      "followers_gained": "tiktok + instagram + youtube",
      "milestone_progress": "current_followers / 50000 * 100"
    }
  },
  "alerts": {
    "credits_warning": "IF daily_credits > 70 THEN notify",
    "milestone_reached": "IF followers >= 50000 THEN trigger_nsfw_escalation",
    "quality_drop": "IF face_consistency < 0.95 THEN notify"
  },
  "output": {
    "grafana_push": true,
    "telegram_daily_summary": true,
    "postgresql_storage": true
  }
}
```

---

## 🔞 WORKFLOW 5: NSFW ESCALATION + FETISH CONTENT

**TRIGGER:** 50,000 followers alcanzados

### CONFIGURACIÓN COMPLETA:

```json
{
  "name": "NSFW Escalation Manager - Phase 2",
  "trigger": {
    "type": "milestone",
    "condition": "followers >= 50000"
  },
  "escalation_timeline": {
    "week_1": {
      "level": 0,
      "content": "SFW viral",
      "platforms": ["tiktok", "instagram", "youtube"]
    },
    "week_2-3": {
      "level": 2,
      "content": "Suggestive (cosplay, bikini, workout)",
      "platforms": ["discord", "twitter", "reddit", "telegram"],
      "pricing": "free",
      "goal": "Discord community building"
    },
    "week_4-6": {
      "level": 4,
      "content": "Softcore (lingerie, boudoir)",
      "platforms": ["onlyfans_basic", "fansly_basic", "patreon"],
      "pricing": "$9.99/mes",
      "production": {
        "model": "wan_2.5",
        "resolution": "1080p",
        "credits": 90
      }
    },
    "week_7-10": {
      "level": 6,
      "content": "Mid-tier NSFW (topless, partial nudity)",
      "platforms": ["onlyfans_premium", "fansly_premium"],
      "pricing": "$24.99/mes",
      "production": {
        "model": "wan_2.5",
        "resolution": "1080p",
        "credits": 90
      }
    },
    "week_11+": {
      "level": 8-10,
      "content": "Explicit + Hardcore + Custom",
      "platforms": ["onlyfans_vip", "xvideos", "pornhub", "xhamster"],
      "pricing": "$49.99/mes + PPV ($50-500)",
      "production": {
        "provider": "RunPod GPU",
        "model": "Stable Video Diffusion",
        "resolution": "4K",
        "gpu": "RTX_4090",
        "cost_per_hour": "$0.69"
      }
    }
  },
  "fetish_categories": {
    "glamour_fashion": {
      "tags": ["lingerie", "silk", "luxury", "designer", "elegant", "seductive"],
      "platforms": ["Fantia", "OnlyFans", "Xhamster"],
      "total_prompts": 55,
      "characters": ["Mika Kobayashi", "Zara Chen", "Sofia Rossi"]
    },
    "cosplay_anime": {
      "tags": ["costume", "character", "convention", "vtuber", "gaming"],
      "platforms": ["Fantia", "Twitter", "Pornhub"],
      "total_prompts": 72,
      "characters": ["Luna Tsukino", "Jin Kawasaki"]
    },
    "mature_elegant": {
      "tags": ["traditional", "kimono", "sophisticated", "dignified", "65yo"],
      "platforms": ["Fantia", "OnlyFans"],
      "total_prompts": 66,
      "characters": ["Chiyo Sasaki", "Minato Sakamoto"]
    },
    "athletic_fitness": {
      "tags": ["military", "tactical", "gym", "workout", "muscle"],
      "platforms": ["Fantia", "Pornhub", "OnlyFans"],
      "total_prompts": 84,
      "characters": ["Takumi Endou", "Kai Morita", "Natsuki Taniguchi"]
    },
    "cultural_lifestyle": {
      "tags": ["tropical", "beach", "bikini", "latino", "college", "kawaii"],
      "platforms": ["Fantia", "XVideos", "OnlyFans"],
      "total_prompts": 90,
      "characters": ["Rio Mizuno", "Mateo Garcia", "Aya Tomita"]
    },
    "total_entries": 383
  },
  "platform_specific_prompts": {
    "Fantia": {
      "style": "high quality, studio lighting, gravure idol, 8k",
      "aspect": "16:9",
      "aesthetic": "professional Japanese gravure"
    },
    "Twitter": {
      "style": "amateur, iphone, candid, authentic, grainy",
      "aspect": "1:1 or 16:9",
      "aesthetic": "smartphone selfie"
    },
    "Xhamster": {
      "style": "high contrast, provocative, bold colors, thumbnail optimized",
      "aspect": "16:9",
      "aesthetic": "adult thumbnail clickbait"
    },
    "Pornhub": {
      "style": "professional studio, high production, 4k",
      "aspect": "16:9",
      "aesthetic": "cinematic adult"
    },
    "XVideos": {
      "style": "european artistic, tasteful, cinematic",
      "aspect": "16:9",
      "aesthetic": "artistic european"
    },
    "LINE": {
      "style": "intimate, girlfriend POV, ring light, front camera",
      "aspect": "9:16",
      "aesthetic": "personal selfie"
    },
    "OnlyFans": {
      "style": "premium, ring light, fairy lights, bedroom, teaser",
      "aspect": "various",
      "aesthetic": "professional but personal"
    }
  }
}
```

### FLUJO NSFW:

```
[Milestone Detected: 50K followers]
    ↓
[Activate NSFW Mode]
    ↓
[Week-based Content Generator]
    ├─→ Week 2-3: Level 2 (Discord, Twitter)
    ├─→ Week 4-6: Level 4 (OnlyFans Basic)
    ├─→ Week 7-10: Level 6 (OnlyFans Premium)
    └─→ Week 11+: Level 8-10 (VIP + PPV)
    ↓
[For Each Level]
    ├─→ [Select Fetish Category] (glamour, cosplay, mature, athletic, cultural)
    ├─→ [Select Platform] (Fantia, OnlyFans, Pornhub, etc.)
    ├─→ [Load Platform-Specific Prompts] (383 total)
    ├─→ [Generate Prompt with Ollama]
          "Generate NSFW level {level} content prompt featuring {character}, {fetish_tags}, {platform_aesthetic}, {aspect_ratio}"
    ├─→ [Production Decision]
    │     IF level <= 6:
    │       → A2E wan_2.5, 1080p, 90 créditos
    │     IF level >= 8:
    │       → RunPod GPU, Stable Video Diffusion, 4K
    ├─→ [Generate Content]
    ├─→ [Apply Platform Compliance]
    ├─→ [Watermark if Required]
    └─→ [Publish to Platform]
    ↓
[Track Revenue]
    ├─→ Basic tier: $9.99/mes × subs
    ├─→ Premium tier: $24.99/mes × subs
    ├─→ VIP tier: $49.99/mes × subs
    └─→ PPV: $50-500 per custom
```

---

## 💌 WORKFLOW 6: DM AUTOMATION & SOCIAL ENGINEERING

### CONFIGURACIÓN:

```json
{
  "name": "DM Automation - Social Engineering",
  "triggers": {
    "new_subscriber": {
      "template": "welcome",
      "delay": "immediate"
    },
    "7_days_inactive": {
      "template": "engagement",
      "delay": "7 days since last_activity"
    },
    "basic_30days": {
      "template": "upsell",
      "delay": "30 days on basic_tier"
    },
    "vip_subscriber": {
      "template": "custom_offer",
      "delay": "immediate"
    }
  },
  "templates_by_character": {
    "miyuki_sakura": {
      "persona": "younger_sister",
      "welcome": "Hi! Thank you so much for subscribing! 💕 I'm so happy to have you here. Make sure to check out my exclusive content section! Let me know if you have any questions~ 🥰",
      "engagement": "Hey! I noticed you haven't been around lately... 😔 Is everything okay? I miss seeing you in the chat! Let me know if you need anything 💕",
      "upsell": "Hey! You've been such a great supporter 🥰 Have you checked out my Premium tier? You get custom videos and more exclusive content! It would mean so much if you upgraded 💕",
      "custom_offer": "Hi! As a VIP, you can request custom content just for you 🎥 Tell me your fantasy and I'll make it real~ Prices start at $50 for photos, $100 for videos 😘"
    },
    "aurelia_viral": {
      "persona": "provocative_seductive",
      "welcome": "Welcome babe 😈 Thanks for joining my exclusive club. You're in for a treat... check out what I have waiting for you 🔥",
      "engagement": "Hey stranger 👀 Where have you been? I've got some new content you DON'T want to miss... come back and play with me 💋",
      "upsell": "You've been enjoying the basic tier... but trust me, Premium is where the REAL fun happens 🔥 Upgrade and see what you've been missing 😏",
      "custom_offer": "VIP access unlocked 🔓 I'm taking custom requests this week. Tell me EXACTLY what you want to see and I'll make your fantasy come true 💦 Starting at $100"
    }
  },
  "upsell_psychology": {
    "scarcity": "Only 5 VIP spots left this month!",
    "urgency": "20% off Premium if you upgrade in the next 24h!",
    "fomo": "VIP members just got exclusive access to...",
    "social_proof": "Over 500 fans already upgraded to Premium!",
    "reciprocity": "Here's a free preview of Premium tier as a thank you 💕"
  },
  "ab_testing": {
    "enabled": true,
    "variants": ["friendly", "seductive", "cute", "professional"],
    "metric": "conversion_rate",
    "sample_size": 100,
    "winner_threshold": "95% confidence"
  }
}
```

---

## 🎨 WORKFLOW 7: LORA TRAINING MANAGER (GPU)

**TRIGGER:** Fase 2 activada + GPU budget available

### CONFIGURACIÓN:

```json
{
  "name": "LoRA Training Orchestrator - RunPod GPU",
  "purpose": "Train custom LoRAs for 32 characters × 5 platforms = 160 images",
  "trigger": {
    "type": "manual",
    "condition": "phase2_active AND gpu_budget_available"
  },
  "dataset": {
    "total_characters": 32,
    "total_platforms": 5,
    "total_images": 160,
    "platforms": {
      "Instagram": {"aspect_ratio": "1:1", "resolution": "1024x1024"},
      "Facebook": {"aspect_ratio": "4:5", "resolution": "1080x1350"},
      "TikTok": {"aspect_ratio": "9:16", "resolution": "1080x1920"},
      "YouTube": {"aspect_ratio": "16:9", "resolution": "1920x1080"},
      "Discord": {"aspect_ratio": "1:1", "resolution": "1024x1024"}
    }
  },
  "training_config": {
    "provider": "RunPod",
    "gpu": "RTX_4090",
    "hourly_rate": "$0.69",
    "estimated_time_per_lora": "2-3 hours",
    "model_base": "realisticVision_v51.safetensors",
    "steps": 50,
    "cfg_scale": 8,
    "sampler": "DPM++ 2M Karras",
    "clip_skip": 2,
    "batch_size": 4
  },
  "workflow": [
    "Generate 160 base images (32 characters × 5 platforms) using A2E",
    "Upload to RunPod storage",
    "Launch RunPod GPU instance (RTX 4090)",
    "Run LoRA training script (Kohya_ss)",
    "Train for 2-3 hours per character",
    "Download trained .safetensors files",
    "Test LoRA quality (face consistency check)",
    "Deploy to production if quality > 0.95",
    "Shutdown GPU instance"
  ],
  "cost_estimate": {
    "total_characters": 32,
    "hours_per_character": 2.5,
    "total_hours": 80,
    "cost_per_hour": 0.69,
    "total_cost": "$55.20",
    "frequency": "once_per_quarter",
    "annual_cost": "$220.80"
  },
  "usage": {
    "phase2_nsfw": "Custom NSFW content with perfect face consistency",
    "fetish_categories": "Personalized content for specific fetishes",
    "custom_requests": "High-quality PPV custom content ($100-500)"
  }
}
```

---

## 💰 COSTOS TOTALES

### FASE 1 (Actual):
- A2E Pro: $9.90/mes
- VPS: $3-5/mes
- Música: $0-2/mes
- **Total: $13-15/mes**

### FASE 2 (50K+ followers):
- A2E Max: $49/mes
- RunPod GPU: $27.60/mes (10h)
- APIs NSFW: $10-20/mes
- LoRA Training: $55/quarter (~$18/mes)
- **Total: $104.60-114.60/mes**

### ROI FASE 2 (1,000 subs):
- **Ingresos:** $14,000-17,000/mes
- **Costos:** $115/mes
- **Neto:** $13,885-16,885/mes
- **ROI:** 12,000%+

---

## ✅ RESUMEN FINAL

**7 WORKFLOWS LISTOS:**
1. ✅ Daily SFW (4 reels/día)
2. ✅ Weekly Premium (1 reel/semana)
3. ✅ Comment Auto-Reply
4. ✅ Analytics
5. ⏸️ NSFW Escalation + 383 Fetish Prompts
6. ⏸️ DM Automation + Social Engineering
7. ⏸️ LoRA Training (GPU RunPod)

**PRÓXIMO PASO:** Crear los 4 workflows de Fase 1 en formato JSON para N8N

¿Procedo a crear los JSONs finales?
