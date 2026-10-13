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
