// ============================================================
// DATOS DE PRUEBA
// Los datos sensibles (usuario y clave de prueba) vienen
// del .env. Aquí NUNCA se escriben contraseñas reales (Regla 7).
// ============================================================

// DEMO: credenciales PÚBLICAS de Sauce Demo (las publica el mismo sitio).
// Solo se usan si no hay .env, para que la plantilla funcione tal cual.
// TODO: con tu app, pon el usuario y la clave en el .env y deja vacíos estos
// valores por defecto ('') para que nunca quede una clave real en el código.
const USUARIO_DEMO = 'standard_user';
const CLAVE_DEMO = 'secret_sauce';

const usuarios = {
  // Usuario válido: los valores vienen del archivo .env (o los DEMO si no existe).
  valido: {
    usuario: process.env.TEST_USER || USUARIO_DEMO,
    clave: process.env.TEST_PASSWORD || CLAVE_DEMO,
  },

  // Usuario inválido: estos datos NO son sensibles, se pueden escribir aquí.
  invalido: {
    usuario: 'usuario_que_no_existe',
    clave: 'clave_incorrecta',
  },
};

module.exports = { usuarios };
