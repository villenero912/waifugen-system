#!/bin/bash
# ============================================================
# WaifuGen — Pipeline de Producción de Vídeo
# Genera 4 reels diarios para los 8 personajes
# ============================================================
set -euo pipefail

source /app/docker/scripts/load_env.sh

CHARACTER=${1:-"miyuki_sakura"}
MODE=${2:-"phase1"}

echo "🎬 Iniciando producción: $CHARACTER ($MODE)"

case $MODE in
    phase1)
        docker exec waifugen_app python scripts/generate_complete_reel.py \
            --character "$CHARACTER" \
            --duration 15 \
            --platform tiktok
        ;;
    karaoke)
        docker exec waifugen_app python scripts/test_miyuki_jp_karaoke.py \
            --character "$CHARACTER"
        ;;
    batch)
        # 4 reels del día en rotación de personajes
        CHARS=("miyuki_sakura" "hana_nakamura" "airi_neo" "aiko_hayashi")
        for char in "${CHARS[@]}"; do
            echo "  ▶ Generando reel: $char"
            docker exec waifugen_app python scripts/generate_complete_reel.py \
                --character "$char" --duration 15
            sleep 10
        done
        ;;
    *)
        echo "❌ Modo desconocido: $MODE"
        echo "   Uso: ./produce.sh [personaje] [phase1|karaoke|batch]"
        exit 1
        ;;
esac

echo "✅ Producción completada"
