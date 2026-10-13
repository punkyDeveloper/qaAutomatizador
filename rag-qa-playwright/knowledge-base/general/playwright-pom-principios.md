---
id: gen-ui-pom-001
lenguaje: javascript
framework: playwright
tipo: ui
patron: pom
categoria: buenas-practicas
version: 1.0
---

# Playwright + Page Object Model: principios generales

## Decisión del equipo (Paso 0)
- Las pruebas de front se automatizan con **Playwright**.
- El patrón obligatorio para UI es **Page Object Model (POM)**.
- Aplica a JavaScript (TypeScript opcional).

## Regla 1: Responsabilidad de cada capa
- **Page Object**: contiene locators y acciones de la página. Describe CÓMO interactuar.
- **Test**: contiene el escenario y las aserciones. Describe QUÉ se valida.
- Las aserciones van en el test, no en el Page Object. El Page Object puede exponer locators para que el test los valide.

## Regla 2: Prioridad de locators
Usar en este orden:
1. `getByRole` (rol + nombre accesible)
2. `getByLabel`
3. `getByPlaceholder`
4. `getByText`
5. `getByTestId` (atributo `data-testid`)
6. CSS o XPath solo como último recurso y justificado con comentario.

Evitar: selectores por posición (`nth-child`), clases de estilo generadas (`.css-1x2y3z`), XPath absolutos (`/html/body/div[2]/...`).

## Regla 3: Nada de esperas fijas
- Prohibido `waitForTimeout`, `sleep`, `Thread.sleep`, `time.sleep`.
- Playwright espera automáticamente antes de cada acción (auto-waiting).
- Para validar estados, usar aserciones web-first (`expect(locator).toBeVisible()`), que reintentan solas.

## Regla 4: Métodos con intención de usuario
- Bien: `login(usuario, clave)`, `agregarProductoAlCarrito(nombre)`.
- Mal: `clickBoton1()`, `escribirEnInput()`.

## Regla 5: Componentes reutilizables
Partes compartidas (header, menú, modal, tabla) van en su propia clase de componente y se componen dentro de las páginas. No crear un `BasePage` gigante con todo.

## Regla 6: Tests independientes
- Cada test prepara sus datos y no depende del orden de ejecución.
- La autenticación repetida se resuelve con `storageState` o fixtures, no logueándose por UI en cada test.

## Regla 7: Datos de prueba
- No quemar (hardcodear) datos sensibles ni URLs en los tests.
- URLs base en configuración; credenciales en variables de entorno; datos en fixtures o factories.

## Regla 8: Sin lógica condicional en tests
Un test no debe tener `if/else` para decidir qué validar. Si hay dos caminos, son dos tests.

## Estructura de carpetas recomendada
```
tests/
├── pages/        # Page Objects
├── components/   # Componentes reutilizables
├── fixtures/     # Fixtures y setup
├── data/         # Datos de prueba
└── specs/        # Tests
```

## Checklist de revisión (usado por el RAG para validar código)
- [ ] ¿Los locators están dentro del Page Object y no en el test?
- [ ] ¿Se usan locators por rol, label o test-id antes que CSS/XPath?
- [ ] ¿No hay esperas fijas?
- [ ] ¿Las aserciones están en el test y son web-first?
- [ ] ¿Los métodos del Page Object tienen nombres de intención de usuario?
- [ ] ¿El test es independiente de los demás?
- [ ] ¿No hay credenciales ni URLs quemadas?
- [ ] ¿No hay `if/else` dentro del test?
