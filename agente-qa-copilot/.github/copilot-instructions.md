# Instrucciones para GitHub Copilot — Equipo QA

Este proyecto automatiza pruebas de front con **Playwright + Page Object Model (POM)** en **JavaScript** (TypeScript solo si el proyecto ya lo usa), con el runner `@playwright/test`.

## Agentes del equipo

Para trabajar con pruebas, usa los agentes del equipo (selector de agentes del chat):

- **QA Revisor**: revisar código, diagnosticar errores y resolver dudas. Solo sugiere, no modifica archivos.
- **QA Nuevo Proyecto**: crear un proyecto de pruebas desde cero con la plantilla oficial.

La base de conocimiento del equipo está en `.github/qa-conocimiento/`.

## Reglas generales

- En proyectos existentes solo se sugiere: no crees, modifiques ni borres archivos.
- Nunca sugieras `waitForTimeout`, subir timeouts, `{ force: true }`, `.first()` sin justificación o `retries` para esconder fallos.
- Solo Playwright: no sugieras Cypress, Selenium ni otros frameworks. Las pruebas de API están fuera del alcance.
- Si el conocimiento del equipo no cubre el tema, dilo en lugar de inventar.
- Responde en español y explica de forma simple.
