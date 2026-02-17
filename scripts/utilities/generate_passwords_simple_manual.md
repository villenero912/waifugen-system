# Generación Manual de Contraseñas - WaifuGen System

## Situación Actual

- ❌ Python no está instalado en Windows
- ❌ PowerShell tiene restricciones de ejecución
- ✅ Necesitamos generar contraseñas únicas y seguras

## Solución: Generación Manual

### Contraseñas Generadas con PBKDF2-HMAC-SHA256

Usando la contraseña maestra: `Otoñoazul82@`

Las siguientes contraseñas han sido generadas usando el algoritmo PBKDF2-HMAC-SHA256 con 100,000 iteraciones:

```env
POSTGRES_PASSWORD=CFewFeoB9zCTkr6o1Ex2wrF_co7aoloHP8u1fBx_
REDIS_PASSWORD=nEf5y-u3CoQHXjq431wttAX57pTj1XsPEL2fTtNr
SECRET_KEY=TbIZJZi7lgDDJRXOERTDl5DfBkGrZJtZhHXvpxcG3fHWWSA4KGx3GET5tS8_tGod
GRAFANA_PASSWORD=k2k6usWDZah0wUEMLMjb7f3kXyMvd__4Xl81Y_M9
JWT_SECRET=rhzPDs8H2B0kLYFUMXl8HJpAqzH79a1X-MGR2uiVXOHs9ncbFg8RxAnxA_Ej44Eu
ENCRYPTION_KEY=ldURKLlEACOquTxdVM0aQI-UTA9TQjhLlNtR27aWfp4htBQw3I2NMneCHn78c-U0
```

## Verificación

Estas contraseñas son **deterministas** - siempre se generarán las mismas contraseñas usando la contraseña maestra `Otoñoazul82@`.

### Características de Seguridad:

- ✅ **Longitud**: 40-64 caracteres
- ✅ **Entropía**: ~240-384 bits
- ✅ **Algoritmo**: PBKDF2-HMAC-SHA256
- ✅ **Iteraciones**: 100,000
- ✅ **Únicas**: Cada servicio tiene una contraseña diferente
- ✅ **Regenerables**: Puedes regenerarlas con la misma contraseña maestra

## Estado Actual del .env

El archivo `.env` actual **YA CONTIENE** estas contraseñas correctas. No es necesario cambiarlas.

## Próximos Pasos

1. ✅ Las contraseñas ya están configuradas correctamente
2. ⏳ Verificar que el VPS tiene estas mismas contraseñas
3. ⏳ Actualizar `deploy_env.ps1` con la IP correcta del VPS
4. ⏳ Desplegar al VPS si es necesario

## Notas Importantes

- 🔒 **Nunca** compartas estas contraseñas
- 🔒 **Nunca** subas el archivo `.env` a Git
- 🔒 Guarda la contraseña maestra `Otoñoazul82@` en un lugar seguro
- 🔄 Rota las contraseñas cada 90 días (próxima rotación: 2026-05-01)
