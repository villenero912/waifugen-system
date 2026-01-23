#!/bin/bash
# =====================================================
# Script de Generación Batch - Stable Diffusion API
# 32 Personajes × 5 Plataformas = 160 Imágenes
# =====================================================

# Colores para输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}🚀 Iniciando generación de imágenes LoRA...${NC}"
echo -e "${YELLOW}📊 Total: 32 personajes × 5 plataformas = 160 imágenes${NC}"
echo ""

# Configuración
API_URL="http://127.0.0.1:7860"
OUTPUT_DIR="./lora_images"
TEMP_DIR="./temp_prompts"
mkdir -p "$OUTPUT_DIR"
mkdir -p "$TEMP_DIR"

# Semillas por personaje (32 personajes)
declare -A SEEDS=(
    ["Miyuki_Sakura"]=1001
    ["Haruto_Tanaka"]=1002
    ["Yuki_Watanabe"]=1003
    ["Kenji_Morimoto"]=1004
    ["Aiko_Hayashi"]=1005
    ["Takeshi_Oda"]=1006
    ["Sakura_Ito"]=1007
    ["Ryo_Nakamura"]=1008
    ["Mei_Fujiwara"]=1009
    ["Hiroshi_Yamamoto"]=1010
    ["Yuna_Shimizu"]=1011
    ["Kenta_Fukuda"]=1012
    ["Akira_Kojima"]=1013
    ["Ren_Ohashi"]=1014
    ["Hana_Nakamura"]=1015
    ["Daiki_Sato"]=1016
    ["Mika_Kobayashi"]=1017
    ["Takumi_Endou"]=1018
    ["Rio_Mizuno"]=1019
    ["Jin_Kawasaki"]=1020
    ["Chiyo_Sasaki"]=1021
    ["Kai_Morita"]=1022
    ["Aya_Tomita"]=1023
    ["Shota_Hayashi"]=1024
    ["Natsuki_Taniguchi"]=1025
    ["Minato_Sakamoto"]=1026
    ["Luna_Tsukino"]=1027
    ["Kaito_Shirakawa"]=1028
    ["Zara_Chen"]=1029
    ["Victor_Williams"]=1030
    ["Sofia_Rossi"]=1031
    ["Mateo_Garcia"]=1032
)

# Plataformas con resoluciones
PLATFORMS=("Instagram" "Facebook" "TikTok" "YouTube" "Discord")

generate_image() {
    local character=$1
    local platform=$2
    local seed=$3
    local prompt=$4
    
    local width=$([[ "$platform" == "Instagram" || "$platform" == "Discord" ]] && echo "1024" || \
                 ([[ "$platform" == "Facebook" ]] && echo "1080" || \
                 ([[ "$platform" == "TikTok" ]] && echo "1080" || \
                 echo "1924")))
    
    local height=$([[ "$platform" == "Instagram" || "$platform" == "Discord" ]] && echo "1024" || \
                  ([[ "$platform" == "Facebook" ]] && echo "1350" || \
                  ([[ "$platform" == "TikTok" ]] && echo "1920" || \
                  echo "1080")))
    
    local output_file="${OUTPUT_DIR}/${platform}/${character}_${platform,,}.png"
    mkdir -p "$(dirname "$output_file")"
    
    echo -e "${YELLOW}Generando:${NC} ${character} - ${platform} (seed: ${seed})"
    
    # Llamada a la API de Stable Diffusion
    curl -s "${API_URL}/sdapi/v1/txt2img" \
        -H "Content-Type: application/json" \
        -d "{
            \"prompt\": \"${prompt}\",
            \"negative_prompt\": \"blurry, low quality, distorted features, bad anatomy, extra limbs, deformed face, ugly, disfigured, poorly drawn face, mutation, mutated, worst quality, low quality, normal quality, jpeg artifacts, signature, watermark, username, artist name, text, watermark\",
            \"seed\": ${seed},
            \"width\": ${width},
            \"height\": ${height},
            \"steps\": 50,
            \"cfg_scale\": 8,
            \"sampler_name\": \"DPM++ 2M Karras\"
        }" > "${TEMP_DIR}/${character}_${platform}.json"
    
    # Extraer y guardar imagen
    if grep -q "images" "${TEMP_DIR}/${character}_${platform}.json"; then
        local base64_data=$(grep -o '"images":\[[^]]*\]' "${TEMP_DIR}/${character}_${platform}.json" | sed 's/"images":\[\(.*\)\]/\1/' | tr -d '"')
        echo "$base64_data" | base64 -d > "$output_file"
        echo -e "${GREEN}✓ Guardado:${NC} ${output_file}"
    else
        echo -e "${RED}✗ Error generando:${NC} ${character} - ${platform}"
    fi
}

# Persona base (ejemplo - usar prompts completos del archivo MD)
generate_all() {
    local count=0
    local total=$(( ${#SEEDS[@]} * 5 ))
    
    for character in "${!SEEDS[@]}"; do
        seed=${SEEDS[$character]}
        
        for platform in "${PLATFORMS[@]}"; do
            count=$((count + 1))
            echo -e "${GREEN}[${count}/${total}]${NC} Procesando: ${character} - ${platform}"
            
            # Aquí iría el prompt completo
            # Para uso real, carga desde el archivo de prompts
            prompt="Portrait photography of ${character}, professional headshot style, clean minimalist background, Fujifilm XT-4 photography, sharp focus on eyes, shallow depth of field, 85mm portrait lens, 4K resolution, highly detailed skin texture, photorealistic, high quality, SFW"
            
            generate_image "$character" "$platform" "$seed" "$prompt"
            
            # Pequeña pausa para no saturar la API
            sleep 0.5
        done
    done
}

# Mostrar ayuda
show_help() {
    echo "Uso: $0 [opción]"
    echo ""
    echo "Opciones:"
    echo "  generate   - Generar todas las imágenes"
    echo "  test       - Generar imagen de prueba"
    echo "  help       - Mostrar esta ayuda"
    echo ""
    echo "Ejemplo:"
    echo "  $0 generate"
}

# Generar imagen de prueba
test_generation() {
    echo -e "${YELLOW}🧪 Generando imagen de prueba...${NC}"
    
    curl -s "${API_URL}/sdapi/v1/txt2img" \
        -H "Content-Type: application/json" \
        -d '{
            "prompt": "Portrait photography of Miyuki_Sakura, young Japanese woman with long black hair, warm brown eyes, wearing cream knit sweater, professional headshot style, Fujifilm XT-4 photography, sharp focus on eyes, 4K resolution, photorealistic, SFW",
            "negative_prompt": "blurry, low quality, distorted features, bad anatomy",
            "seed": 1001,
            "width": 1024,
            "height": 1024,
            "steps": 50,
            "cfg_scale": 8,
            "sampler_name": "DPM++ 2M Karras"
        }' > "${TEMP_DIR}/test_output.json"
    
    if grep -q "images" "${TEMP_DIR}/test_output.json"; then
        echo -e "${GREEN}✓ Imagen de prueba generada exitosamente${NC}"
    else
        echo -e "${RED}✗ Error en la generación de prueba${NC}"
    fi
}

# Procesar argumentos
case "${1:-help}" in
    generate)
        generate_all
        ;;
    test)
        test_generation
        ;;
    help|--help|-h)
        show_help
        ;;
    *)
        show_help
        ;;
esac

echo ""
echo -e "${GREEN}✨ Proceso completado${NC}"
