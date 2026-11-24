# Prueba de automatización (punta a punta)

Comprueba que el RAG le sirve a un QA que automatiza con Playwright + POM:
revisa código mal y bien hecho, diagnostica errores **reales** de Playwright (provocados en
una copia temporal de `plantilla-playwright-pom`), arma un proyecto con `plantilla_proyecto`
y hace preguntas sencillas a `buscar_conocimiento`.

Necesita: Node + npm, internet (para `npm install`) y los navegadores de Playwright.
Usa una base vectorial temporal: no toca la base del usuario.

## Cómo ejecutarlo (un solo comando, desde `rag-qa-playwright`)

```bash
PYTHONIOENCODING=utf-8 ~/.venvs/rag-qa-playwright/Scripts/python.exe pruebas_automatizacion/probar_automatizacion.py
```

En PowerShell: `$env:PYTHONIOENCODING='utf-8'; & "$env:USERPROFILE\.venvs\rag-qa-playwright\Scripts\python.exe" pruebas_automatizacion/probar_automatizacion.py`

Cada caso imprime ✅ o ❌ con una explicación y al final el total. Termina con código 0 solo
si todos los casos pasan.
