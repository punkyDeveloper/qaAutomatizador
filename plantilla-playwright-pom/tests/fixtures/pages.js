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
