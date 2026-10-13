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
