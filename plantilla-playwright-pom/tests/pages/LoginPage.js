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
