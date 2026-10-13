---
id: js-ui-pom-001
lenguaje: javascript
framework: playwright
runner: "@playwright/test"
tipo: ui
patron: pom
categoria: ejemplos
version: 1.0
---

# Playwright + POM en JavaScript

## Configuración base
La URL base va en la configuración, nunca quemada en los tests. Se lee del archivo `.env` con la librería dotenv.

```javascript
// playwright.config.js
require('dotenv').config({ quiet: true }); // carga BASE_URL desde el archivo .env
const { defineConfig } = require('@playwright/test');

module.exports = defineConfig({
  testDir: './tests/specs',
  use: {
    baseURL: process.env.BASE_URL,
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
});
```

## Page Object correcto
```javascript
// tests/pages/LoginPage.js
class LoginPage {
  /** @param {import('@playwright/test').Page} page */
  constructor(page) {
    this.page = page;
    this.usuarioInput = page.getByLabel('Usuario');
    this.claveInput = page.getByLabel('Contraseña');
    this.ingresarButton = page.getByRole('button', { name: 'Ingresar' });
    this.mensajeError = page.getByRole('alert');
  }

  async abrir() {
    await this.page.goto('/login');
  }

  async login(usuario, clave) {
    await this.usuarioInput.fill(usuario);
    await this.claveInput.fill(clave);
    await this.ingresarButton.click();
  }
}

module.exports = { LoginPage };
```
El comentario `@param` con JSDoc da autocompletado en VS Code sin necesidad de TypeScript.

## Fixture para inyectar Page Objects
```javascript
// tests/fixtures/pages.js
const base = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');

const test = base.test.extend({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },
});

module.exports = { test, expect: base.expect };
```

## Test correcto
```javascript
// tests/specs/login.spec.js
const { test, expect } = require('../fixtures/pages');

test('muestra error con credenciales inválidas', async ({ loginPage }) => {
  await loginPage.abrir();
  await loginPage.login('usuario_invalido', 'clave_invalida');
  await expect(loginPage.mensajeError).toHaveText('Credenciales incorrectas');
});
```

## Anti-patrón (NO hacer)
```javascript
test('login', async ({ page }) => {
  await page.goto('https://mi-app.com/login');                          // URL quemada
  await page.fill('#root > div > form > input:nth-child(1)', 'admin');  // selector frágil
  await page.fill('.css-8x7y2', 'admin123');                            // clase generada + clave quemada
  await page.click('xpath=/html/body/div/form/button');                 // XPath absoluto
  await page.waitForTimeout(3000);                                      // espera fija
  const visible = await page.isVisible('.dashboard');
  expect(visible).toBe(true);                                           // aserción sin reintento
});
```
Problemas: locators en el test, selectores frágiles, datos y URL quemados, espera fija, aserción no web-first.

## Variante TypeScript (opcional)
Si alguien usa TypeScript, la estructura es idéntica. Solo cambian la extensión (`.ts`), los imports (`import { Page, Locator } from '@playwright/test'`) y los tipos declarados en las propiedades del Page Object. Las reglas son las mismas.
