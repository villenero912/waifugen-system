
# 🌏 Estrategia de Automatización Global y Proxies (Fase 2)

## 1. Análisis de Viabilidad por Plataforma

Dado que plataformas como **XVideos, XHamster** y plataformas asiáticas (**Fantia, DMM, Twitter JP**) no ofrecen APIs públicas de subida, la automatización se realizará mediante **Browser Automation (Playwright)**.

| Plataforma | Método de Subida | Requisito de Proxy | Viabilidad Auto |
|:---|:---|:---|:---|
| **XVideos / XHamster** | Playwright (Stealth) | Residencial / Datacenter | Alta |
| **Fantia / DMM (Asia)** | Playwright + Cookie Auth | **Residencial JP (Obligatorio)** | Media-Alta |
| **OnlyFans / Fansly** | Playwright (Subida Manual simulada) | Residencial (Localización cuenta) | Alta |
| **Twitter / X (JP Market)** | API / Playwright | Residencial JP | Muy Alta |

## 2. Estrategia de Proxies por Región

Para el mercado asiático y la evasión de bloqueos en plataformas de adultos, implementaremos una **Ruta Híbrida**:

### 🇯🇵 Mercado Asiático (Hana Nakamura / Miyuki Sakura)
- **Proveedor:** IPRoyal (Residencial).
- **Configuración:** Forzar nodos en **Tokio/Osaka (JP)**.
- **Técnica:** "Session Persistence". Se mantiene la misma IP residencial durante toda la sesión de subida para evitar bloqueos por cambio de geolocalización.
- **Fingerprinting:** Uso de `playwright-extra-stealth` para evitar que las plataformas detecten que es un bot.

### 🌐 Mercado Global (Aurelia Viral / Aiko Hayashi)
- **Proveedor:** IPRoyal / Proxy-Cheap.
- **Configuración:** Rotación por país según el objetivo (US, DE, FR).
- **Técnica:** Rotación cada 10 minutos para subir múltiples clips en diferentes "shards" de la plataforma.

## 3. Arquitectura del "Stealth Uploader" (Fase 2)

He diseñado la estructura para el nuevo módulo de subida automática sin API:

```python
# Módulo: src/social/stealth_uploader.py

class StealthUploader:
    def __init__(self, platform, proxy_config):
        self.platform = platform
        self.proxy = proxy_config # Residencial JP para Fantia
        
    async def upload_video(self, video_path, metadata):
        # 1. Iniciar navegador con Proxy Residencial
        # 2. Inyectar Cookies de Sesión (para saltar 2FA)
        # 3. Simular movimiento humano (Mouse/Keyboard)
        # 4. Subir archivo y completar metadatos
        # 5. Confirmar publicación
```

## 4. Limitaciones y Riesgos
- **Subida Manual vs Auto:** Las plataformas de adultos son agresivas detectando bots. Se recomienda una estrategia de **"Semi-Automática"**: n8n prepara la subida, abre el navegador con el proxy adecuado, y el usuario solo da el "click final" de publicar, o se programa con delays humanos aleatorios (15-45 mins).
- **Velocidad:** Las IPs residenciales son lentas para subir videos 4K. El sistema fragmentará las subidas o usará proxies "Static Residential" (ISP) si el volumen de Fase 2 es muy alto.

## 5. Próximos Pasos en el Sistema
1. **Configurar IPRoyal JP:** Activar el filtrado por código de país `JP` en `proxy_manager.py`.
2. **Crear Scripts de Playwright:** Uno por cada plataforma objetivo (empezando por XVideos/Fansly).
3. **Gestión de Cookies:** Sistema de encriptación para guardar sesiones de login de las waifus y no loguear cada vez (reduce el riesgo de baneo).
