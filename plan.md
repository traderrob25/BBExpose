# Project Plan: Hexada Scanner Web 🚀

## Estado Actual
El proyecto está construido y funcionalmente desplegado en Vercel. Contiene dos herramientas principales:
1.  **Bollinger Scanner:** API en Python interactuando con React Front-End.
2.  **Asimetrías Dashboard:** Panel interactivo en React para la calificación de acciones basada en Asimetrías Estructurales y Filtros Cuantitativos (Deep Value).

## Mejoras Implementadas Recientemente
*   [x] Integración de la lógica de analistas (Prompt 1) en el `AsymmetryDashboard.tsx`.
*   [x] Adición de métricas cuantitativas: `sector`, `pbRatio`, `targetPrice`, y `analystScore`.
*   [x] Creación de sistema de pestañas (Tabs) para agrupar por escenarios (>$50 Sólidas vs <$50 Rápidas).
*   [x] Incorporación de Checkboxes para filtrar por: P/B < 1.0, Upside > 30% y Strong Buy (Score <= 2.0).

## Próximos Pasos (Hoja de Ruta)

### Fase 1: Integración de Datos Dinámicos
- [ ] Construir un endpoint en `api/index.py` que obtenga las métricas de Asimetrías (Target Price, PB Ratio, Analyst Score) dinámicamente desde Yahoo Finance u otra API (reemplazando los datos *hard-coded* en `sampleStocks`).
- [ ] Vincular la barra de búsqueda para golpear esta nueva API usando SWR (o similar) para caching.

### Fase 2: Robustecimiento de Reportes
- [ ] Mejorar el UI/UX de la exportación a CSV para segmentar según la pestaña activa ("Escenario A" vs "Escenario B").
- [ ] Configurar Alertas por Correo (vía webhook/Resend) cuando una acción cruce umbrales específicos de Deep Value (ej. si una acción en watchlist de repente tiene Upside > 40%).

### Fase 3: AI Insights (Integración con LLM)
- [ ] Integrar el Agente (Anthropic/Groq APIs recomendables) al Dashboard para que devuelva un análisis automatizado en un popup cuando el usuario hace click en *Ver Detalle* de una acción (ej. "Analiza por qué esta acción tiene 4 asimetrías").

## Consideraciones de Seguridad
*   **Gestión de APIs:** Verificar siempre en `.env` (o panel de Vercel) y JAMÁS hacer commit de llaves a GitHub. El proyecto ya ha sido limpiado de tokens hard-coded.
*   **Rate Limiting:** Asegurarse de que el bot de Yfinance no envíe llamadas abusivas en paralelo, usar siempre caché temporal (Next.js Cache o en memoria limitadas).
