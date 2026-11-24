// ============================================================
// CONFIGURACIÓN DE PLAYWRIGHT
// Aquí se define dónde están los tests, la URL base,
// los navegadores y qué guardar cuando una prueba falla.
// ============================================================

// Carga las variables del archivo .env (BASE_URL, TEST_USER, etc.)
require('dotenv').config({ quiet: true });

const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // Carpeta donde Playwright busca los archivos .spec.js
  testDir: './tests/specs',

  // Ejecuta los tests en paralelo. Por eso cada test debe ser independiente (Regla 6).
  fullyParallel: true,

  // En CI, falla si alguien dejó un test.only olvidado.
  forbidOnly: !!process.env.CI,

  // Reintentos solo en CI como red de seguridad.
  // OJO: no se usan para esconder pruebas inestables; esas se corrigen.
  retries: process.env.CI ? 2 : 0,

  // Genera un reporte HTML. Se abre con: npm run report
  reporter: 'html',

  use: {
    // La URL viene del .env. Así en los tests se usa goto('/ruta') y no la URL completa (Regla 7).
    // DEMO: si no hay .env, se usa Sauce Demo para que la plantilla funcione tal cual.
    // TODO: cuando uses tu app, define BASE_URL en el .env (no cambies este valor por defecto).
    baseURL: process.env.BASE_URL || 'https://www.saucedemo.com',

    // Atributo que usa getByTestId() para buscar elementos.
    // DEMO: Sauce Demo usa data-test="...".
    // TODO: si tu app usa data-testid="..." (el estándar de Playwright), borra esta línea.
    testIdAttribute: 'data-test',

    // Guarda el trace (grabación paso a paso) cuando un test se reintenta.
    // SEGURIDAD: el trace y el reporte HTML guardan el texto escrito en cada campo,
    // incluida la clave de prueba. No compartas ni publiques playwright-report/ ni
    // test-results/ si usan credenciales que no sean públicas (ya están en .gitignore).
    trace: 'on-first-retry',

    // Toma captura de pantalla solo si el test falla.
    screenshot: 'only-on-failure',
  },

  // Navegadores donde se ejecutan los tests.
  // TODO: agrega firefox o webkit si tu equipo lo necesita.
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
});
