# Hexada Scanner Web 📊

Hexada Scanner Web es la interfaz principal del sistema de análisis de la suite Hexada. Se divide en dos potentes motores: el Scanner de Bollinger (Scalping) y el Dashboard de Asimetrías Estructurales (Deep Value Investment).

## Módulos Principales

### 1. Bollinger Band Scalper (`page.tsx`)
Un scanner conectado a una API serverless en Python que consume datos en tiempo real de Yahoo Finance. Detecta confluencias de sobrecompra/sobreventa en múltiples temporalidades (Semanal, Mensual, Diario, 1h, 15m).

### 2. Asymmetry Dashboard (`AsymmetryDashboard.tsx`)
Un panel diseñado para la metodología de inversión "Deep Value". 
El Dashboard evalúa acciones con base en:
*   **7 Asimetrías Estructurales:** (Información, Tiempo, Acceso, Liquidez, Estructura, Incentivos, Descentralización).
*   **Filtros de Analista Cuantitativo:** 
    *   `P/B Ratio < 1.0` (Para buscar acciones debajo de su valor contable).
    *   `Upside > 30%` (Filtro Anti-Value-Trap, asegura que el Precio Objetivo justifique el riesgo).
    *   `Analyst Score <= 2.0` (Confirmación de convicción Institucional "Strong Buy" / "Buy").

## Tecnologías y Seguridad 🔒

Este proyecto ha sido estructurado considerando las mejores prácticas:
*   **Frontend:** React, Next.js (App Router), TailwindCSS.
*   **Backend / Serverless:** Python (`api/index.py`) encapsulado en Vercel Serverless Functions.
*   **Manejo de Secretos:** Integrado 100% mediante Vercel Environment Variables. Ninguna API Key (como Anthropic o Groq en otros submódulos) está expuesta en el código cliente.
*   **Seguridad UI:** Sanitización automática de inputs por defecto gracias a la arquitectura de componentes de React.

## Cómo Ejecutar en Local

1. Instala las dependencias:
```bash
npm install
```

2. Corre el servidor de desarrollo (que levanta simultáneamente React y el Proxy para Python):
```bash
npm run dev
```

3. Abre `http://localhost:3000` en tu navegador.

## Despliegue en Producción (Vercel)
Este proyecto está conectado via Continuous Deployment (CD) a la rama `main` en GitHub.
Cada `git push origin main` detona un build automático donde:
1. Se validan los scripts de TypeScript.
2. Vercel instala las dependencias de Python (dictadas en `requirements.txt`).
3. Se publican los Serverless Endpoints.
