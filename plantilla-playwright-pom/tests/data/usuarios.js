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
