---
id: js-plantilla-001
lenguaje: javascript
framework: playwright
runner: "@playwright/test"
tipo: ui
patron: pom
categoria: plantilla
version: 1.1
---

# Plantilla de proyecto base: Playwright + POM en JavaScript

Esta plantilla se usa SOLO cuando el proyecto empieza desde cero (ver `comportamiento-asistente.md`, Función 4).

## Modo demo: funciona al ejecutarla

La plantilla viene configurada contra **Sauce Demo** (https://www.saucedemo.com), una tienda pública hecha para practicar pruebas automatizadas, con credenciales públicas publicadas por el mismo sitio. Así, al crearla y ejecutar `npm test`, los 3 tests pasan sin cambiar nada y el equipo ve un ejemplo funcionando antes de adaptarlo.

Convención de comentarios dentro del código:
- `DEMO:` explica por qué ese valor es así en Sauce Demo.
- `TODO:` indica qué reemplazar al adaptar la plantilla a la aplicación real.

---

## 1. Estructura de carpetas

```
mi-proyecto-pruebas/
├── .env.example              Plantilla de variables de entorno (se sube a Git)
├── .env                      Variables reales (NO se sube a Git; copia de .env.example)
├── .gitignore
├── package.json
├── playwright.config.js      Configuración de Playwright
└── tests/
    ├── pages/                Page Objects: una clase por página
    │   ├── LoginPage.js
    │   └── HomePage.js
    ├── components/           Partes reutilizables (header, menú, modales)
    │   └── HeaderComponent.js
    ├── fixtures/             Inyecta los Page Objects en los tests
    │   └── pages.js
    ├── data/                 Datos de prueba
    │   └── usuarios.js
    └── specs/                Los tests
        └── login.spec.js
```

---

## 2. Archivo `package.json`

```json
{
  "name": "plantilla-playwright-pom",
  "version": "1.0.0",
  "description": "Plantilla base de pruebas con Playwright + POM",
  "scripts": {
    "test": "playwright test",
    "test:ui": "playwright test --ui",
    "test:debug": "playwright test --debug",
    "report": "playwright show-report"
  },
  "devDependencies": {
    "@playwright/test": "^1.63.0",
    "dotenv": "^18.0.5"
  }
}
```

Comandos para instalar todo:

```bash
# Instala Playwright y dotenv según el package.json
npm install

# Descarga los navegadores que usa Playwright
npx playwright install
```

---

## 3. Archivo `.env.example`

```bash
# ============================================================
# VARIABLES DE ENTORNO DE EJEMPLO
# 1. Copia este archivo y renómbralo a .env
# 2. Reemplaza los valores por los de tu aplicación
# 3. NUNCA subas el archivo .env a Git (tiene datos sensibles)
# ============================================================

# DEMO: Sauce Demo es una tienda pública hecha para practicar pruebas.
# TODO: reemplaza por la URL de tu aplicación (sin "/" al final).
BASE_URL=https://www.saucedemo.com

# DEMO: estas credenciales son públicas, las publica el mismo sitio de práctica.
# TODO: reemplaza por un usuario de PRUEBAS de tu app (nunca uno real).
TEST_USER=standard_user
TEST_PASSWORD=secret_sauce
```

---

## 4. Archivo `.gitignore`

```bash
# Dependencias
node_modules/

# Variables con datos sensibles
.env

# Resultados generados por Playwright
test-results/
playwright-report/
blob-report/
playwright/.cache/
playwright/.auth/
```

---

## 5. Archivo `playwright.config.js`

```javascript
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
    baseURL: process.env.BASE_URL,

    // Atributo que usa getByTestId() para buscar elementos.
    // DEMO: Sauce Demo usa data-test="...".
    // TODO: si tu app usa data-testid="..." (el estándar de Playwright), borra esta línea.
    testIdAttribute: 'data-test',

    // Guarda el trace (grabación paso a paso) cuando un test se reintenta.
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
```

---

## 6. Archivo `tests/pages/LoginPage.js`

```javascript
// ============================================================
// PAGE OBJECT: LOGIN
// Un Page Object representa UNA página de la aplicación.
// Aquí van: locators (cómo encontrar elementos) y acciones.
// Aquí NO van: aserciones (expect). Esas van en el test (Regla 1).
// ============================================================

class LoginPage {
  /** @param {import('@playwright/test').Page} page */
  constructor(page) {
    this.page = page;

    // ---------- LOCATORS ----------
    // Prioridad: getByRole > getByLabel > getByPlaceholder > getByText > getByTestId > CSS (Regla 2)
    // Tip: usa "npx playwright codegen <url>" para encontrar el locator correcto.

    // DEMO: los campos de Sauce Demo no tienen label, por eso se usa el placeholder.
    // TODO: en tu app, si el campo tiene label, prefiere getByLabel('Texto del label').
    this.usuarioInput = page.getByPlaceholder('Username');
    this.claveInput = page.getByPlaceholder('Password');

    // TODO: reemplaza 'Login' por el texto real del botón de tu app.
    this.ingresarButton = page.getByRole('button', { name: 'Login' });

    // Mensaje de error que aparece con credenciales inválidas.
    // DEMO: en Sauce Demo es <h3 data-test="error">.
    // TODO: ajusta al locator del mensaje de error de tu app.
    this.mensajeError = page.getByTestId('error');
  }

  // ---------- ACCIONES ----------
  // Nombra los métodos según lo que hace el usuario, no según el clic (Regla 4).
  // Bien: login()  |  Mal: clickBoton()

  // Abre la página de login. La ruta se suma a BASE_URL del .env.
  async abrir() {
    // DEMO: en Sauce Demo el login está en la raíz '/'.
    // TODO: cambia por la ruta real de tu página de login (por ejemplo '/login').
    await this.page.goto('/');
  }

  // Llena el formulario y envía. No valida nada: eso lo hace el test.
  async login(usuario, clave) {
    await this.usuarioInput.fill(usuario);
    await this.claveInput.fill(clave);
    await this.ingresarButton.click();
  }
}

module.exports = { LoginPage };
```

---

## 7. Archivo `tests/components/HeaderComponent.js`

```javascript
// ============================================================
// COMPONENTE: HEADER
// Un componente es una parte que se repite en varias páginas
// (header, menú lateral, modal). Va en su propia clase y las
// páginas lo "usan". Así no se repite código (Regla 5).
// ============================================================

class HeaderComponent {
  /** @param {import('@playwright/test').Page} page */
  constructor(page) {
    // TODO: si tu app tiene elementos repetidos (por ejemplo, dos botones "Menú"),
    // busca primero el contenedor del header y luego los elementos DENTRO de él:
    //   this.contenedor = page.getByRole('banner');
    //   this.menuButton = this.contenedor.getByRole('button', { name: 'Menú' });
    // Así evitas el error "strict mode violation".

    // DEMO: botón de menú (hamburguesa) de Sauce Demo.
    // TODO: reemplaza 'Open Menu' por el nombre real del botón de tu app.
    this.menuButton = page.getByRole('button', { name: 'Open Menu' });

    // DEMO: opción "Logout" dentro del menú lateral de Sauce Demo.
    // TODO: reemplaza 'Logout' por el texto real de tu app.
    this.cerrarSesionLink = page.getByRole('link', { name: 'Logout' });
  }

  async cerrarSesion() {
    await this.menuButton.click();
    // No hace falta esperar a que el menú se abra:
    // Playwright espera solo a que el link esté listo antes del clic (Regla 3).
    await this.cerrarSesionLink.click();
  }
}

module.exports = { HeaderComponent };
```

---

## 8. Archivo `tests/pages/HomePage.js`

```javascript
// ============================================================
// PAGE OBJECT: HOME (página principal después del login)
// Ejemplo de una página que USA un componente (el header).
// DEMO: en Sauce Demo es la página de productos.
// ============================================================

const { HeaderComponent } = require('../components/HeaderComponent');

class HomePage {
  /** @param {import('@playwright/test').Page} page */
  constructor(page) {
    this.page = page;

    // Se compone el header dentro de la página.
    // En el test se usa así: homePage.header.menuButton
    this.header = new HeaderComponent(page);

    // DEMO: título "Products" de Sauce Demo (<span data-test="title">).
    // TODO: reemplaza por un elemento que solo aparezca en tu página principal.
    this.titulo = page.getByTestId('title');
  }

  async abrir() {
    // TODO: cambia por la ruta real de tu página principal.
    await this.page.goto('/inventory.html');
  }
}

module.exports = { HomePage };
```

---

## 9. Archivo `tests/fixtures/pages.js`

```javascript
// ============================================================
// FIXTURES
// Crea los Page Objects automáticamente para cada test.
// Así en el test no hay que escribir "new LoginPage(page)".
// Cada test recibe sus propias instancias (tests independientes).
// ============================================================

const base = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');
const { HomePage } = require('../pages/HomePage');

const test = base.test.extend({
  loginPage: async ({ page }, use) => {
    await use(new LoginPage(page));
  },

  homePage: async ({ page }, use) => {
    await use(new HomePage(page));
  },

  // TODO: cada Page Object nuevo que crees, regístralo aquí con el mismo formato.
});

// Los tests deben importar test y expect DESDE ESTE ARCHIVO, no desde '@playwright/test'.
module.exports = { test, expect: base.expect };
```

---

## 10. Archivo `tests/data/usuarios.js`

```javascript
// ============================================================
// DATOS DE PRUEBA
// Los datos sensibles (usuario y clave de prueba) vienen
// del .env. Aquí NUNCA se escriben contraseñas reales (Regla 7).
// ============================================================

const usuarios = {
  // Usuario válido: los valores vienen del archivo .env
  valido: {
    usuario: process.env.TEST_USER,
    clave: process.env.TEST_PASSWORD,
  },

  // Usuario inválido: estos datos NO son sensibles, se pueden escribir aquí.
  invalido: {
    usuario: 'usuario_que_no_existe',
    clave: 'clave_incorrecta',
  },
};

module.exports = { usuarios };
```

---

## 11. Archivo `tests/specs/login.spec.js`

```javascript
// ============================================================
// TESTS DE LOGIN
// El test describe QUÉ se valida. El Page Object sabe CÓMO hacerlo.
// Estructura de cada test:
//   1. Preparar (abrir la página)
//   2. Actuar  (usar métodos del Page Object)
//   3. Validar (expect, siempre con await)
// ============================================================

// IMPORTANTE: importar desde los fixtures, no desde '@playwright/test'.
const { test, expect } = require('../fixtures/pages');
const { usuarios } = require('../data/usuarios');

test.describe('Login', () => {

  test('permite ingresar con credenciales válidas', async ({ loginPage, homePage }) => {
    // 1. Preparar
    await loginPage.abrir();

    // 2. Actuar
    await loginPage.login(usuarios.valido.usuario, usuarios.valido.clave);

    // 3. Validar
    // Aserción web-first: reintenta sola hasta que se cumpla (Regla 3). Siempre con await.
    // TODO: reemplaza 'Products' por el título real de tu página principal.
    await expect(homePage.titulo).toHaveText('Products');
  });

  test('muestra error con credenciales inválidas', async ({ loginPage }) => {
    await loginPage.abrir();
    await loginPage.login(usuarios.invalido.usuario, usuarios.invalido.clave);

    // toContainText valida solo una parte del mensaje: es más estable si el texto cambia un poco.
    // TODO: reemplaza por el mensaje de error real de tu app.
    await expect(loginPage.mensajeError).toContainText('Username and password do not match');
  });

  test('permite cerrar sesión desde el header', async ({ loginPage, homePage }) => {
    // Cada test hace su propio login: no depende de que otro test lo haya hecho (Regla 6).
    await loginPage.abrir();
    await loginPage.login(usuarios.valido.usuario, usuarios.valido.clave);

    // Se usa el componente header a través de la página.
    await homePage.header.cerrarSesion();

    // Si cerró sesión, vuelve a aparecer el botón de login.
    await expect(loginPage.ingresarButton).toBeVisible();
  });

  // TODO: agrega aquí más casos de login (campos vacíos, usuario bloqueado, etc.).
  // Un caso = un test. Sin if/else dentro de los tests (Regla 8).
});
```

---

## 12. Pasos para ejecutar y luego adaptar

El asistente debe indicar estos pasos al terminar:

**Primero, ver la demo funcionando:**
1. Ejecutar `npm install` y luego `npx playwright install`.
2. Copiar `.env.example` y renombrarlo a `.env` (sin cambiar nada todavía).
3. Ejecutar `npm test`. Deben pasar los 3 tests.
4. Ejecutar `npm run report` para ver el reporte, o `npm run test:ui` para ver los tests paso a paso.

**Después, adaptarla a la aplicación real:**
5. Cambiar en `.env` la URL y el usuario de pruebas por los de la aplicación.
6. Reemplazar todos los `TODO:` (en VS Code: buscar "TODO" con `Ctrl+Shift+F`).
7. Borrar los comentarios `DEMO:` cuando ya no apliquen.
8. Siguiente mejora recomendada: configurar `storageState` para no repetir el login por UI en cada test (Regla 6).
