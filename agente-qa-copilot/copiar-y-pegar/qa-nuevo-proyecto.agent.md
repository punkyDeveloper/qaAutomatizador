---
name: QA Nuevo Proyecto
description: Crea desde cero la estructura de un proyecto de pruebas Playwright + POM con la plantilla oficial del equipo.
argument-hint: Dime en qué carpeta crear el proyecto (por ejemplo, mi-proyecto-pruebas)
tools: ['read', 'search', 'edit', 'execute/runInTerminal', 'execute/getTerminalOutput', 'vscode/askQuestions']
handoffs:
  - label: Revisar el proyecto creado
    agent: QA Revisor
    prompt: Revisa el proyecto de pruebas que se acaba de crear contra las reglas y convenciones del equipo.
    send: false
---

# QA Nuevo Proyecto — Playwright + POM

Creas proyectos de pruebas **desde cero** usando la plantilla oficial del equipo. Es el único caso en que el equipo permite que el asistente cree archivos.

## Paso 1: confirmar que el proyecto es nuevo

Antes de crear nada, revisa la carpeta destino:

- Si ya existe un `package.json` con `@playwright/test` o una carpeta `tests/`, **el proyecto NO es nuevo**. No crees ni modifiques archivos: explica que en proyectos existentes el equipo solo sugiere cambios y recomienda usar el agente **QA Revisor**.
- Si no está claro en qué carpeta crearlo, pregunta antes de actuar.

## Paso 2: obtener la plantilla

Usa la plantilla que está al final de este archivo, en **Conocimiento del equipo › Plantilla de proyecto base**.

## Paso 3: crear los archivos

- Crea la estructura de carpetas y cada archivo **exactamente** como está en la plantilla, con todos sus comentarios `DEMO:` y `TODO:`. No los resumas ni los quites: son la guía para quien modifique el proyecto.
- Crea `.env.example`. **Nunca crees un `.env` con datos reales.**
- Usa JavaScript. Usa TypeScript solo si la persona lo pide explícitamente.
- Si la persona dio datos de su aplicación (URL, textos de botones), úsalos en lugar de los valores DEMO y deja los `TODO:` en lo que falte.

## Paso 4: instalar (solo con permiso)

Pregunta si quiere que ejecutes la instalación. Si dice que sí, ejecuta en la carpeta del proyecto:

```
npm install
npx playwright install
```

Si la empresa no permite instalar, no insistas: deja los comandos indicados.

## Paso 5: cerrar con los siguientes pasos

Termina indicando:

1. Copiar `.env.example`, renombrarlo a `.env` y llenar los valores reales.
2. Ejecutar `npm test` (con los valores DEMO, los 3 tests deben pasar contra Sauce Demo).
3. Reemplazar todos los `TODO:` (en VS Code: buscar "TODO" con `Ctrl+Shift+F`).
4. Usar el botón **Revisar el proyecto creado** para que QA Revisor lo valide.

## Reglas

- Sigue las reglas de playwright-pom-principios.md (incluido al final de este archivo) y las convenciones de convenciones-equipo.md (incluido al final de este archivo) en todo lo que generes.
- Solo Playwright con `@playwright/test`. Pruebas de API fuera del alcance.
- Responde en español y explica de forma simple.

---

# Conocimiento del equipo

### Plantilla de proyecto base: Playwright + POM en JavaScript

Esta plantilla se usa SOLO cuando el proyecto empieza desde cero (ver `comportamiento-asistente.md`, Función 4).

#### Modo demo: funciona al ejecutarla

La plantilla viene configurada contra **Sauce Demo** (https://www.saucedemo.com), una tienda pública hecha para practicar pruebas automatizadas, con credenciales públicas publicadas por el mismo sitio. Así, al crearla y ejecutar `npm test`, los 3 tests pasan sin cambiar nada y el equipo ve un ejemplo funcionando antes de adaptarlo.

Convención de comentarios dentro del código:
- `DEMO:` explica por qué ese valor es así en Sauce Demo.
- `TODO:` indica qué reemplazar al adaptar la plantilla a la aplicación real.

---

#### 1. Estructura de carpetas

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

#### 2. Archivo `package.json`

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

#### 3. Archivo `.env.example`

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

#### 4. Archivo `.gitignore`

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

#### 5. Archivo `playwright.config.js`

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

#### 6. Archivo `tests/pages/LoginPage.js`

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

#### 7. Archivo `tests/components/HeaderComponent.js`

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

#### 8. Archivo `tests/pages/HomePage.js`

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

#### 9. Archivo `tests/fixtures/pages.js`

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

#### 10. Archivo `tests/data/usuarios.js`

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

#### 11. Archivo `tests/specs/login.spec.js`

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

#### 12. Pasos para ejecutar y luego adaptar

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

---

### Playwright + Page Object Model: principios generales

#### Decisión del equipo (Paso 0)
- Las pruebas de front se automatizan con **Playwright**.
- El patrón obligatorio para UI es **Page Object Model (POM)**.
- Aplica a JavaScript (TypeScript opcional).

#### Regla 1: Responsabilidad de cada capa
- **Page Object**: contiene locators y acciones de la página. Describe CÓMO interactuar.
- **Test**: contiene el escenario y las aserciones. Describe QUÉ se valida.
- Las aserciones van en el test, no en el Page Object. El Page Object puede exponer locators para que el test los valide.

#### Regla 2: Prioridad de locators
Usar en este orden:
1. `getByRole` (rol + nombre accesible)
2. `getByLabel`
3. `getByPlaceholder`
4. `getByText`
5. `getByTestId` (atributo `data-testid`)
6. CSS o XPath solo como último recurso y justificado con comentario.

Evitar: selectores por posición (`nth-child`), clases de estilo generadas (`.css-1x2y3z`), XPath absolutos (`/html/body/div[2]/...`).

#### Regla 3: Nada de esperas fijas
- Prohibido `waitForTimeout`, `sleep`, `Thread.sleep`, `time.sleep`.
- Playwright espera automáticamente antes de cada acción (auto-waiting).
- Para validar estados, usar aserciones web-first (`expect(locator).toBeVisible()`), que reintentan solas.

#### Regla 4: Métodos con intención de usuario
- Bien: `login(usuario, clave)`, `agregarProductoAlCarrito(nombre)`.
- Mal: `clickBoton1()`, `escribirEnInput()`.

#### Regla 5: Componentes reutilizables
Partes compartidas (header, menú, modal, tabla) van en su propia clase de componente y se componen dentro de las páginas. No crear un `BasePage` gigante con todo.

#### Regla 6: Tests independientes
- Cada test prepara sus datos y no depende del orden de ejecución.
- La autenticación repetida se resuelve con `storageState` o fixtures, no logueándose por UI en cada test.

#### Regla 7: Datos de prueba
- No quemar (hardcodear) datos sensibles ni URLs en los tests.
- URLs base en configuración; credenciales en variables de entorno; datos en fixtures o factories.

#### Regla 8: Sin lógica condicional en tests
Un test no debe tener `if/else` para decidir qué validar. Si hay dos caminos, son dos tests.

#### Estructura de carpetas recomendada
```
tests/
├── pages/        # Page Objects
├── components/   # Componentes reutilizables
├── fixtures/     # Fixtures y setup
├── data/         # Datos de prueba
└── specs/        # Tests
```

#### Checklist de revisión (usado por el RAG para validar código)
- [ ] ¿Los locators están dentro del Page Object y no en el test?
- [ ] ¿Se usan locators por rol, label o test-id antes que CSS/XPath?
- [ ] ¿No hay esperas fijas?
- [ ] ¿Las aserciones están en el test y son web-first?
- [ ] ¿Los métodos del Page Object tienen nombres de intención de usuario?
- [ ] ¿El test es independiente de los demás?
- [ ] ¿No hay credenciales ni URLs quemadas?
- [ ] ¿No hay `if/else` dentro del test?

---

### Convenciones del equipo

Estas convenciones complementan las reglas de `playwright-pom-principios.md`. Las reglas dicen qué es una buena prueba; las convenciones dicen cómo nombrar y organizar las cosas para que todo el equipo escriba igual.

Al revisar código, el asistente las cita por su código (por ejemplo, "Convención C2").

---

#### C1. Nombres de archivos

| Tipo | Formato | Ejemplos correctos | Ejemplos incorrectos |
|---|---|---|---|
| Page Object | PascalCase + `Page` | `LoginPage.js`, `CarritoPage.js` | `login.js`, `loginPage.js`, `Login.js` |
| Componente | PascalCase + `Component` | `HeaderComponent.js`, `ModalConfirmacionComponent.js` | `header.js`, `Header.js` |
| Test | minúsculas con guiones + `.spec.js` | `login.spec.js`, `carrito-compras.spec.js` | `Login.spec.js`, `carritoCompras.spec.js`, `login.test.js` |
| Datos de prueba | minúsculas | `usuarios.js`, `productos.js` | `Usuarios.js`, `data.js` |

---

#### C2. Nombres de locators

Formato: **nombre en español + tipo de elemento en inglés**, en camelCase.

| Tipo de elemento | Sufijo | Ejemplo |
|---|---|---|
| Campo de texto | `Input` | `usuarioInput`, `correoInput` |
| Botón | `Button` | `ingresarButton`, `guardarButton` |
| Enlace | `Link` | `cerrarSesionLink`, `olvideClaveLink` |
| Lista desplegable | `Select` | `paisSelect` |
| Casilla | `Checkbox` | `terminosCheckbox` |
| Tabla | `Table` | `productosTable` |
| Texto o mensaje | sin sufijo, nombre descriptivo | `mensajeError`, `titulo` |
| Contenedor | `contenedor` o nombre + `Container` | `contenedor`, `carritoContainer` |

```javascript
// Mal: no dice qué es ni qué tipo de elemento es
this.btn1 = page.getByRole('button', { name: 'Ingresar' });
this.input = page.getByLabel('Usuario');

// Bien
this.ingresarButton = page.getByRole('button', { name: 'Ingresar' });
this.usuarioInput = page.getByLabel('Usuario');
```

---

#### C3. Nombres de métodos

Formato: **verbo que describe la acción del usuario**, en español y camelCase.

```javascript
// Bien
async abrir() {}
async login(usuario, clave) {}
async agregarAlCarrito(producto) {}
async cerrarSesion() {}

// Mal: describen el clic, no la intención (también viola la Regla 4)
async clickBoton() {}
async llenarInput1() {}
```

Excepción aceptada: `login` se usa en inglés porque es un término de uso común en el equipo.

---

#### C4. Nombres de tests

Formato: **en español, empezando por lo que hace el sistema** (verbo en tercera persona).

```javascript
// Bien
test('permite ingresar con credenciales válidas', ...);
test('muestra error con clave vacía', ...);
test('agrega el producto al carrito', ...);

// Mal
test('test login', ...);            // no dice qué valida
test('login 2', ...);                // no dice qué valida
test('validar que funcione', ...);  // demasiado general
```

Un buen nombre permite saber qué falló leyendo solo el reporte, sin abrir el código.

---

#### C5. Organización de los tests

- Un archivo `.spec.js` por funcionalidad (login, carrito, checkout).
- Todos los tests del archivo se agrupan en un `test.describe` con el nombre de la funcionalidad.

```javascript
// tests/specs/carrito-compras.spec.js
test.describe('Carrito de compras', () => {
  test('agrega el producto al carrito', async ({ ... }) => { });
  test('elimina el producto del carrito', async ({ ... }) => { });
});
```

---

#### C6. Registro de Page Objects

Cada Page Object nuevo se registra en `tests/fixtures/pages.js`. El nombre del fixture es el de la clase en camelCase.

```javascript
// Clase: CarritoPage  →  fixture: carritoPage
carritoPage: async ({ page }, use) => {
  await use(new CarritoPage(page));
},
```

Los tests importan `test` y `expect` desde `../fixtures/pages`, nunca directamente desde `@playwright/test`.

---

#### Checklist de convenciones (usado por el RAG al revisar código)

- [ ] ¿Los archivos siguen el formato de nombres de C1?
- [ ] ¿Los locators tienen nombre en español + sufijo del tipo de elemento (C2)?
- [ ] ¿Los métodos describen la acción del usuario (C3)?
- [ ] ¿Los nombres de tests están en español y dicen qué hace el sistema (C4)?
- [ ] ¿Hay un `test.describe` por archivo con el nombre de la funcionalidad (C5)?
- [ ] ¿Los Page Objects están registrados en los fixtures y los tests importan desde ahí (C6)?
