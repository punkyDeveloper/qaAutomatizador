---
id: js-errores-001
lenguaje: javascript
framework: playwright
runner: "@playwright/test"
tipo: ui
patron: pom
categoria: errores
version: 1.0
---

# Catálogo de errores comunes de Playwright

Cada error sigue el mismo formato: mensaje en consola, qué significa, causas comunes, dónde buscar y solución.

---

## Cómo leer un error de Playwright (dónde está el problema)

Cuando una prueba falla, la consola muestra:

1. **El mensaje del error** (primera línea): qué falló.
2. **La línea de código marcada con `>`**: la instrucción exacta que falló.
3. **El stack trace** (líneas con `at ...`): la ruta de archivos y líneas. La primera línea que apunte a `tests/pages/` o `tests/specs/` es donde hay que mirar.

```
  Error: locator.click: Timeout 30000ms exceeded.
  ...
    > 18 |     await this.ingresarButton.click();
         |                               ^
      at LoginPage.login (tests/pages/LoginPage.js:18:31)
      at tests/specs/login.spec.js:6:19
```
En este ejemplo el problema está en `LoginPage.js` línea 18, llamado desde `login.spec.js` línea 6.

**Herramientas para investigar:**
- `npx playwright show-report`: abre el reporte con capturas del fallo.
- `npx playwright test --ui`: modo visual para ver la prueba paso a paso.
- `npx playwright test --debug`: ejecuta pausando en cada paso.
- `npx playwright show-trace <archivo-trace.zip>`: muestra el estado de la página en cada acción.
- `npx playwright codegen <url>`: ayuda a encontrar el locator correcto de un elemento.

---

## Error: Timeout en una acción

**Mensaje:**
```
Error: locator.click: Timeout 30000ms exceeded.
Call log:
  - waiting for getByRole('button', { name: 'Ingresar' })
```

**Qué significa:** Playwright esperó a que el elemento estuviera listo (visible, habilitado, estable) y nunca lo estuvo.

**Causas comunes:**
- El locator no coincide con ningún elemento (texto distinto, mayúsculas, tildes).
- El elemento existe pero está oculto o deshabilitado.
- La prueba está en otra página de la que se cree (falló una navegación anterior).
- El elemento está dentro de un iframe.

**Dónde buscar:** el `Call log` dice qué locator esperaba. Revisa ese locator en el Page Object indicado en el stack trace.

**Solución:**
- Verificar el texto exacto con `npx playwright codegen` o el modo `--ui`.
- Si está en un iframe, usar `page.frameLocator(...)`.
- NO subir el timeout ni agregar `waitForTimeout` como solución (viola la Regla 3).

```javascript
// Mal: el texto no coincide con la app ("Iniciar sesión")
this.ingresarButton = page.getByRole('button', { name: 'Ingresar' });

// Bien: texto real verificado con codegen
this.ingresarButton = page.getByRole('button', { name: 'Iniciar sesión' });
```

---

## Error: Strict mode violation (varios elementos)

**Mensaje:**
```
Error: locator.click: Error: strict mode violation:
getByRole('button', { name: 'Guardar' }) resolved to 2 elements
```

**Qué significa:** el locator encontró más de un elemento y Playwright no sabe a cuál hacerle clic.

**Causas comunes:** hay dos botones con el mismo texto (por ejemplo, uno en un formulario y otro en un modal).

**Dónde buscar:** el locator mencionado en el mensaje, dentro del Page Object.

**Solución:** acotar el locator al contenedor correcto. Evitar `.first()` o `.nth()` salvo que el orden sea parte del requisito.

```javascript
// Mal: ambiguo, o "arreglado" con .first() sin saber cuál es
this.guardarButton = page.getByRole('button', { name: 'Guardar' }).first();

// Bien: acotado al contenedor
this.modal = page.getByRole('dialog');
this.guardarButton = this.modal.getByRole('button', { name: 'Guardar' });
```

---

## Error: Aserción fallida por timeout

**Mensaje:**
```
Error: Timed out 5000ms waiting for expect(locator).toHaveText(expected)
Expected string: "Credenciales incorrectas"
Received string: "Usuario o contraseña inválidos"
```

**Qué significa:** la aserción reintentó durante 5 segundos y el valor nunca fue el esperado.

**Causas comunes:**
- El texto esperado está mal escrito o la app cambió el mensaje.
- El elemento nunca apareció (`Received: <element(s) not found>`).

**Dónde buscar:** la línea del `expect` en el archivo `.spec.js`. Compara `Expected` contra `Received`.

**Solución:**
- Si cambió el texto, actualizar el valor esperado en el test.
- Si el texto es dinámico, validar una parte: `toContainText('inválid')` o una expresión regular.
- Si dice `element(s) not found`, revisar el locator en el Page Object.

---

## Error: Cannot navigate to invalid URL

**Mensaje:**
```
Error: page.goto: Protocol error (Page.navigate): Cannot navigate to invalid URL
```

**Qué significa:** se llamó `goto('/login')` con una ruta relativa, pero no hay `baseURL` configurada.

**Causas comunes:** la variable de entorno `BASE_URL` no está definida, o falta el archivo `.env`.

**Dónde buscar:** `playwright.config.js` (propiedad `use.baseURL`) y el archivo `.env`.

**Solución:**
- Crear el `.env` a partir de `.env.example` y definir `BASE_URL`.
- Verificar que el config cargue las variables (por ejemplo con `require('dotenv').config()` al inicio).
- NO quemar la URL completa en el Page Object (viola la Regla 7).

---

## Error: ERR_CONNECTION_REFUSED

**Mensaje:**
```
Error: page.goto: net::ERR_CONNECTION_REFUSED at http://localhost:3000/login
```

**Qué significa:** la URL es válida pero no hay nada respondiendo en esa dirección.

**Causas comunes:**
- La aplicación no está corriendo.
- El puerto en `BASE_URL` es incorrecto.

**Dónde buscar:** el valor de `BASE_URL` y si la app está levantada.

**Solución:** levantar la aplicación antes de las pruebas, o configurar `webServer` en `playwright.config.js` para que Playwright la inicie automáticamente.

---

## Error: Navegadores no instalados

**Mensaje:**
```
Error: browserType.launch: Executable doesn't exist at ...
Looks like Playwright Test or Playwright was just installed or updated.
Please run the following command to download new browsers:
    npx playwright install
```

**Qué significa:** Playwright está instalado pero no los navegadores que usa.

**Causas comunes:** proyecto recién clonado, actualización de Playwright, o ejecución en un servidor de CI nuevo.

**Solución:** ejecutar `npx playwright install`. En CI usar `npx playwright install --with-deps`.

---

## Error: Elemento bloqueado por otro (intercepts pointer events)

**Mensaje:**
```
<div class="overlay">…</div> intercepts pointer events
retrying click action
```

**Qué significa:** hay otro elemento encima (un modal, un spinner de carga, un banner de cookies) que recibe el clic.

**Causas comunes:** un loader que aún no desaparece, un banner de cookies, un modal abierto.

**Dónde buscar:** la captura del reporte (`npx playwright show-report`) muestra qué cubre el elemento.

**Solución:** esperar a que el bloqueo desaparezca con una aserción, o cerrarlo. NO usar `{ force: true }` como solución general: oculta un problema real que un usuario también tendría.

```javascript
// Mal
await this.ingresarButton.click({ force: true });

// Bien: esperar a que el loader desaparezca
await expect(this.page.getByTestId('loader')).toBeHidden();
await this.ingresarButton.click();
```

---

## Error: Target page, context or browser has been closed

**Mensaje:**
```
Error: locator.fill: Target page, context or browser has been closed
```

**Qué significa:** se intentó usar la página después de que la prueba terminó.

**Causas comunes:** casi siempre es un **`await` faltante**. La prueba termina antes de que la acción se ejecute.

**Dónde buscar:** el método indicado en el stack trace; revisar que cada acción y cada llamada a métodos del Page Object tenga `await`.

**Solución:**
```javascript
// Mal: falta await, el test termina antes
loginPage.login('usuario', 'clave');

// Bien
await loginPage.login('usuario', 'clave');
```

---

## Error: Prueba que pasa aunque debería fallar (await faltante en expect)

**Mensaje:** ninguno. La prueba pasa en verde sin validar nada.

**Qué significa:** un `expect` web-first sin `await` no espera ni falla dentro del test.

**Dónde buscar:** revisar todos los `expect(locator)` del archivo `.spec.js`.

**Solución:**
```javascript
// Mal: nunca valida
expect(loginPage.mensajeError).toBeVisible();

// Bien
await expect(loginPage.mensajeError).toBeVisible();
```
Recomendado: instalar `eslint-plugin-playwright` y activar su regla `playwright/missing-playwright-await` para detectarlo automáticamente.

---

## Error: LoginPage is not a constructor

**Mensaje:**
```
TypeError: LoginPage is not a constructor
```

**Qué significa:** el Page Object no se está importando bien.

**Causas comunes:** el archivo exporta `module.exports = { LoginPage }` pero se importa sin llaves, o al revés.

**Dónde buscar:** el `require` en el fixture o test, y el `module.exports` al final del Page Object.

**Solución:**
```javascript
// Si el Page Object exporta así:
module.exports = { LoginPage };

// Mal
const LoginPage = require('../pages/LoginPage');

// Bien
const { LoginPage } = require('../pages/LoginPage');
```

---

## Error: Test timeout exceeded

**Mensaje:**
```
Test timeout of 30000ms exceeded.
```

**Qué significa:** la prueba completa tardó más de 30 segundos (no una acción, sino todo el test).

**Causas comunes:**
- La prueba hace demasiadas cosas (debería dividirse).
- Login por UI repetido en cada test.
- Una acción quedó esperando hasta el límite.

**Solución:**
- Dividir pruebas largas en varias.
- Usar `storageState` para no loguearse por UI en cada test (Regla 6).
- Revisar el reporte para ver qué paso consumió el tiempo.

---

## Error: No tests found

**Mensaje:**
```
Error: No tests found
```

**Qué significa:** Playwright no encontró archivos de prueba.

**Causas comunes:**
- `testDir` en `playwright.config.js` apunta a otra carpeta.
- Los archivos no terminan en `.spec.js` o `.test.js`.
- Se ejecutó el comando desde otra carpeta.

**Solución:** verificar `testDir`, el nombre de los archivos y ejecutar desde la raíz del proyecto.

---

## Problema: Prueba inestable (flaky): pasa a veces y falla a veces

**Mensaje:** varía; a menudo timeouts que no se repiten siempre.

**Causas comunes:**
- Esperas fijas (`waitForTimeout`) que a veces no alcanzan.
- Aserciones sin reintento (`expect(await locator.isVisible()).toBe(true)`).
- Tests que dependen de datos creados por otros tests.
- Datos compartidos entre pruebas que corren en paralelo.

**Dónde buscar:** ejecutar `npx playwright test <archivo> --repeat-each=10` para reproducirlo, y revisar el trace del intento fallido.

**Solución:**
- Reemplazar esperas fijas por aserciones web-first (Regla 3).
- Hacer cada test independiente con sus propios datos (Regla 6).
- NO usar `retries` para esconder el problema: sirve como red de seguridad, no como solución.
