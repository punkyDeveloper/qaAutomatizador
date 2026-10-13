---
id: gen-convenciones-001
lenguaje: javascript
framework: playwright
tipo: ui
patron: pom
categoria: convenciones
version: 1.0
---

# Convenciones del equipo

Estas convenciones complementan las reglas de `playwright-pom-principios.md`. Las reglas dicen qué es una buena prueba; las convenciones dicen cómo nombrar y organizar las cosas para que todo el equipo escriba igual.

Al revisar código, el asistente las cita por su código (por ejemplo, "Convención C2").

---

## C1. Nombres de archivos

| Tipo | Formato | Ejemplos correctos | Ejemplos incorrectos |
|---|---|---|---|
| Page Object | PascalCase + `Page` | `LoginPage.js`, `CarritoPage.js` | `login.js`, `loginPage.js`, `Login.js` |
| Componente | PascalCase + `Component` | `HeaderComponent.js`, `ModalConfirmacionComponent.js` | `header.js`, `Header.js` |
| Test | minúsculas con guiones + `.spec.js` | `login.spec.js`, `carrito-compras.spec.js` | `Login.spec.js`, `carritoCompras.spec.js`, `login.test.js` |
| Datos de prueba | minúsculas | `usuarios.js`, `productos.js` | `Usuarios.js`, `data.js` |

---

## C2. Nombres de locators

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

## C3. Nombres de métodos

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

## C4. Nombres de tests

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

## C5. Organización de los tests

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

## C6. Registro de Page Objects

Cada Page Object nuevo se registra en `tests/fixtures/pages.js`. El nombre del fixture es el de la clase en camelCase.

```javascript
// Clase: CarritoPage  →  fixture: carritoPage
carritoPage: async ({ page }, use) => {
  await use(new CarritoPage(page));
},
```

Los tests importan `test` y `expect` desde `../fixtures/pages`, nunca directamente desde `@playwright/test`.

---

## Checklist de convenciones (usado por el RAG al revisar código)

- [ ] ¿Los archivos siguen el formato de nombres de C1?
- [ ] ¿Los locators tienen nombre en español + sufijo del tipo de elemento (C2)?
- [ ] ¿Los métodos describen la acción del usuario (C3)?
- [ ] ¿Los nombres de tests están en español y dicen qué hace el sistema (C4)?
- [ ] ¿Hay un `test.describe` por archivo con el nombre de la funcionalidad (C5)?
- [ ] ¿Los Page Objects están registrados en los fixtures y los tests importan desde ahí (C6)?
