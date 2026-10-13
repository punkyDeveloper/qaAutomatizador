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
