```mermaid
graph TD
U[Usuario/Trigger] --> N8N[N8N - Orquestador]
N8N --> FC[FlowCoordinator]
FC --> E1[/api/generate/talking-avatar/]
FC --> E2[/api/generate/music-video/]
FC --> E3[/api/generate/character-animation/]
FC --> E4[/api/generate/song-generation/]
E5[/api/generate/custom/]
E6[/api/generate/sixth-flow/]
E1 --> FC
E2 --> FC
E3 --> FC
E4 --> FC
E5 --> FC
E6 --> FC
FC --> TG[Telegram gate]
TG -->|approve| GPU[GPU Pipeline (Phase 2)]
GPU --> PUB[Publish mainstream]
GPU --> PREMIUM[Publish premium]
FC --> DB[DB - estado]
N8N --> REST[/rest/workflows?overwrite=true/]
REST --> N8N
NGNX[Nginx - puerta de entrada]
```
