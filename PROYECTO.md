# Control Mensual — app de gastos e ingresos de Gonzalo

Proyecto de **Gonzalo Gabriel Pereira**. App personal para registrar gastos e ingresos del hogar y del consultorio, en **un solo archivo HTML** que se abre en el navegador (compu y celular), en español rioplatense, montos en pesos (ARS).

Objetivo: que sea la mejor app de finanzas personales posible, profesional y cómoda de usar todos los días.

## Estado actual

- **Versión:** 1.8 (20 nov 2026) · esquema de datos 1
- **Qué hace hoy:** resumen con ahorro proyectado y % de los ingresos; gastos fijos con checklist de pagado, categoría, día de vencimiento y monto real vs estimado; ingresos con cobrado/pendiente; movimientos (gastos variables) con fecha y categoría; cierre de mes con historial, gráfico de evolución y detalle por categoría; respaldo/restauración JSON, exportación CSV, modo claro/oscuro, menú de opciones; pantalla «Novedades» con aviso (punto en el botón de menú) al actualizar; versión visible al pie del menú; datos con `schemaVersion` y migraciones automáticas (también al restaurar respaldos viejos), con copia interna previa a cada migración; lista del mes completa como checklist (v1.2); doble copia de los datos en IndexedDB + localStorage con recuperación automática y estado visible en el menú (v1.3); aviso en Resumen «hace X días que no descargás un respaldo» con botón «Descargar respaldo» y «Más tarde» (3 días), y fecha del último respaldo en el menú (v1.4); «Copiar respaldo» y «Pegar respaldo» como texto, con errores en línea y copia interna `pre-restauracion` antes de restaurar (v1.5); «Deshacer» en el aviso inferior al eliminar un gasto fijo, un ingreso, un movimiento o un mes del historial, con 6 segundos para recuperarlo en su lugar y con su estado (v1.6); validación en línea en los formularios (gasto, ingreso, movimiento, nombre del mes): errores por campo y avisos de cifras raras con «Guardar igual» (v1.7); accesibilidad: foco visible, todo usable con teclado (filas y meses con Enter/Espacio), hojas como diálogo con Escape, foco atrapado y devuelto al cerrar, foco conservado al redibujar, Ctrl/Cmd+Z deshace, contraste AA en claro y oscuro, nombres para lectores de pantalla (v1.8).
- **Archivos en este artifact:** `index.html` (la app completa, todo el código), `PROYECTO.md` (este documento: memoria del proyecto) y `tests.py` (pruebas Playwright: `python3 tests.py index.html capturas`).
- **Datos y migraciones (desde v1.1):** clave `control-mensual:meta` = `{schemaVersion, appVersion, vistoNovedades[]}`. Esquema 0 = datos v1.0 sin meta. Para cambiar la estructura: subir `SCHEMA_VERSION` y agregar `MIGRATIONS[n](d)` que reciba `{config,current,history}` del esquema n-1. Antes de migrar se guarda `control-mensual:pre-migracion-esquema-<n>` con los textos originales. Si los datos son de un esquema más nuevo que la app, no se sobrescriben.
- **Almacenamiento (desde v1.3):** cada guardado escribe en localStorage (`control-mensual:<clave>`) y en IndexedDB (base `control-mensual`, almacén `kv`, mismas claves sin prefijo) y deja la marca `rev` (ms) en las dos. Al abrir gana la copia con `rev` mayor (empate o sin marca: localStorage) y la otra se resincroniza. Si localStorage no se pudo escribir completo, su `rev` queda en 0. Sin IndexedDB, la app sigue solo con localStorage. No hizo falta subir el esquema: la estructura de los datos no cambió.
- **Aviso de respaldo (desde v1.4):** en `meta.respaldo = {ultimo, base, pospuesto}` (ms). Aparece si pasaron 7 días desde `ultimo`; si nunca hubo descarga, cuenta desde `base` (0 si ya había datos al actualizar → avisa enseguida; fecha de instalación si es nueva). «Más tarde» fija `pospuesto` = ahora + 3 días. Constantes `RESPALDO_DIAS` y `RESPALDO_POSPONER_DIAS`. No es parte de los datos: no cambia el esquema.
- **Respaldo como texto (desde v1.5):** `respaldoJSON()` arma el mismo contenido que el .json (en una línea para copiar). `leerRespaldo(texto)` tolera texto alrededor y devuelve `{d}` o `{error}`; `aplicarRespaldo(d)` (lo usan archivo y texto) guarda antes `control-mensual:pre-restauracion` con los datos que había, migra y guarda. Copiar con éxito cuenta como respaldo (`marcarRespaldo()`); si el portapapeles falla, indica copiar a mano.
- **Deshacer (desde v1.6):** `toast(msg, fn)` muestra «Deshacer» durante `UNDO_MS` (6 s) y ejecuta `fn` una sola vez; un aviso nuevo reemplaza al anterior y su «Deshacer». Cada borrado guarda el elemento, su posición y su estado del mes (pagado/real o cobrado) y lo devuelve con `reinsertar(arr, idx, item)`. Si entre medio cambió el mes o se restauró un respaldo (otro objeto `config`/`current`/`hist`), no restaura y avisa. Sin cambio de esquema.
- **Validación (desde v1.7):** `leerMonto(texto)` → `{n}` (`''` si vacío) o `{error}`: miles con punto de a 3, centavos con coma y hasta 2 cifras, también `1500.50` (punto + 1-2 cifras = decimal) y `1,250,000`; rechaza negativos, letras, `12,500` (sugiere `12.500`) y más de `MONTO_MAX` (1e10). `parseMonto` usa `leerMonto` (error → `''`). `validarForm(form, errores, avisos)` marca cada campo (`aria-invalid` + `.f-msg`), enfoca el primero y no guarda; los avisos (`.f-msg.warn`) se muestran una vez y el botón pasa a «Guardar/Agregar igual» (firma de los valores en `form.dataset.ok`; cualquier cambio los quita). Avisos actuales: real > 10× estimado; movimiento mayor que los ingresos del mes; fecha de movimiento fuera del mes en curso. Sin cambio de esquema.
- **Accesibilidad (desde v1.8):** `:focus-visible` con contorno `--primary` (los `.inp` mantienen su anillo). Filas (`.row-main`) y meses (`.h-head`) son `role=button tabindex=0`; un `keydown` global los activa con Enter/Espacio. `render()` guarda `claveFoco(activeElement)` (selector por `data-act`/`data-id`/`data-tab`/`data-f`/`data-i`) y lo restaura con `enfocarClave` (sin scroll). `openSheet` crea `role=dialog aria-modal` con título `#sheet-title`, deja `inert` el encabezado y `#app`, atrapa Tab, cierra con Escape (`sheetActual.close()`) y devuelve el foco al control que la abrió (o al menú). `asociarLabels(root)` une cada `<label>` de `.field` con su `.inp`. Contraste claro: `--muted #5B6576`, `--pos #047857`, `--neg #C81E1E`, `--warn #B45309`, `--chip-mix 52%`; `tests.py` trae una auditoría de contraste (`AUDIT_JS`) que recorre todo texto visible. Sin cambio de esquema.
- **Novedades:** agregar cada versión al principio del arreglo `CHANGELOG` y subir `VERSION`.

## Reglas de trabajo (mandan sobre todo lo demás)

1. **Nunca perder datos del usuario.** Las claves de guardado son `control-mensual:config`, `control-mensual:current`, `control-mensual:history` (y `control-mensual:theme`). Si cambia la estructura de datos, agregá una migración versionada (`schemaVersion`) que convierta lo viejo; nunca borres ni renombres claves sin migrar. Probá siempre abriendo la versión nueva con datos de la versión anterior.
2. **Un solo HTML** que funcione abierto como archivo local (file://) en Chrome, Safari de iPhone y Android. Sin servidor. Solo se permite Google Fonts como recurso externo, con fuentes del sistema de respaldo; cualquier librería de CDN es opcional y la app tiene que seguir funcionando si no carga.
3. Sin `alert`, `confirm` ni `prompt`: usar las hojas (sheets) propias de la app.
4. Mantener la estética actual (Manrope, tarjeta oscura de resumen, verde azulado como color principal, claro/oscuro, mobile first con barra inferior). Se puede pulir, no reemplazar.
5. **No inventar datos financieros, impositivos ni legales** (tasas de percepción, índices de inflación, tipos de cambio, escalas de Ganancias): siempre los carga el usuario o se muestran como dato a completar.
6. Implementar con parches de Python con reemplazos exactos de cadenas (assert count == 1).
7. El archivo que se entrega se llama siempre **`CONTROL_DE_GASTOS.html`** (el mismo nombre, para que el navegador conserve los datos guardados). La versión va adentro: constante `VERSION` y pantalla de Novedades.
8. Limitaciones conocidas: una página abierta no puede mandar notificaciones con la app cerrada; los avisos son al abrirla, por calendario (.ics / Google Calendar) o, si se aloja como PWA, con notificaciones del navegador. Los adjuntos van en IndexedDB del navegador (no se sincronizan entre dispositivos salvo con respaldo).

## Hoja de ruta: 100 mejoras

Orden de trabajo: de arriba hacia abajo. Cada corrida hace 1 a 3 ítems según su tamaño y los marca [x] con la versión.

### Fase 0 — Bases sólidas
- [x] 1. (v1.1) Constante `VERSION` y pantalla «Novedades» en el menú (qué cambió en cada versión).
- [x] 2. (v1.1) `schemaVersion` y sistema de migraciones de datos entre versiones.
- [x] 3. (v1.3) Guardado en IndexedDB con respaldo en localStorage (más espacio, necesario para adjuntos), migrando los datos actuales sin pérdida.
- [x] 4. (v1.4) Aviso «hace X días que no descargás un respaldo» con acceso directo.
- [x] 5. (v1.5) Respaldo alternativo para cuando la descarga está bloqueada: «Copiar respaldo» y «Pegar respaldo» (texto).
- [x] 6. (v1.6) «Deshacer» en el aviso inferior al borrar un gasto, ingreso, movimiento o mes.
- [x] 7. (v1.7) Validación de montos y campos con mensajes en línea (vacíos, negativos, cifras absurdas).
- [x] 8. (v1.8) Accesibilidad: foco visible, aria-labels, contraste AA, navegación con teclado y Escape en las hojas.
- [x] 9. (v1.1) Guardar en este artifact un script de pruebas `tests.py` (Playwright) reutilizable por cada corrida.
- [ ] 10. Render más fino: actualizar solo lo que cambia, sin saltos de scroll al tildar.

### Fase 1 — Vencimientos y alertas
- [ ] 11. Vista «Calendario del mes» con los vencimientos marcados por día.
- [ ] 12. Banner en Resumen: «Hoy vence…», «Vence en 2 días», «Vencido».
- [ ] 13. Exportar vencimientos del mes a calendario (.ics) con alarma configurable.
- [ ] 14. Botón «Agregar a Google Calendar» por gasto (enlace con fecha, monto y nota).
- [ ] 15. Notificación del navegador al abrir la app si hay vencimientos próximos (con permiso).
- [ ] 16. Anticipación del aviso configurable (1, 3, 5 o 7 días).
- [ ] 17. Frecuencia de cada gasto: mensual, bimestral, trimestral, semestral, anual.
- [ ] 18. Gastos anuales (seguro, patente, matrícula) con provisión mensual sugerida.
- [ ] 19. Marca «débito automático»: se considera pagado al pasar la fecha (con confirmación).
- [ ] 20. Ordenar gastos fijos por vencimiento, monto, nombre o categoría; reordenar a mano.
- [ ] 21. Recordatorio de cierre de mes en los últimos días.
- [ ] 22. Fecha de pago registrada al tildar «pagado» (y pagos parciales).

### Fase 2 — Facturas y comprobantes
- [ ] 23. Adjuntar comprobante (foto o PDF) a cada pago fijo del mes.
- [ ] 24. Visor de comprobantes dentro de la app (imagen con zoom y PDF).
- [ ] 25. Compresión automática de fotos antes de guardarlas.
- [ ] 26. Sección «Archivo»: todos los comprobantes ordenados por servicio, año y mes, con buscador.
- [ ] 27. Datos de la factura: período, consumo (kWh, m³), número de cliente, vencimientos.
- [ ] 28. Gráfico de consumo y costo por servicio a lo largo de los meses.
- [ ] 29. Alerta de aumento: «la luz subió 35 % respecto del mes pasado».
- [ ] 30. Adjuntar ticket a los movimientos variables.
- [ ] 31. Indicador de espacio usado y limpieza de adjuntos viejos.
- [ ] 32. Respaldo completo con adjuntos incluidos.
- [ ] 33. Arrastrar y soltar archivos sobre un gasto en la compu.
- [ ] 34. Nombre de descarga ordenado: «2026-11 Luz.pdf».
- [ ] 35. Ficha del proveedor: número de cliente, enlace de pago y teléfono, a mano al pagar.
- [ ] 36. Lectura sugerida de monto y vencimiento desde PDFs con texto (siempre confirmable por el usuario; opcional si la librería no carga).

### Fase 3 — Ingresos y recibos de sueldo
- [ ] 37. Sección «Recibos de sueldo» por empleador, con adjunto de cada mes.
- [ ] 38. Campos del recibo: bruto, neto, descuentos (jubilación, obra social, sindicato, Ganancias) y adicionales (guardias, horas extra).
- [ ] 39. Gráfico de evolución del neto por empleador.
- [ ] 40. Aviso si el neto cobrado es menor que el esperado o que el mes anterior.
- [ ] 41. Aguinaldo (SAC) de junio y diciembre como ingreso esperado configurable.
- [ ] 42. Ingresos variables: guardias extra, honorarios y otros ingresos sueltos.
- [ ] 43. Fecha de cobro esperada y aviso si pasó y no está marcado como cobrado.
- [ ] 44. Porcentaje de descuentos (bruto vs neto) por recibo.
- [ ] 45. Cobros del consultorio: particulares y obras sociales, con pendientes de cobro.
- [ ] 46. Separar «Hogar» y «Consultorio» como dos ámbitos con su propio resumen.
- [ ] 47. Resultado del consultorio (ingresos − gastos del consultorio) por mes.
- [ ] 48. Resumen anual de ingresos y gastos del consultorio para el contador (exportable).

### Fase 4 — Análisis y presupuesto
- [ ] 49. Presupuesto por categoría con barras de progreso.
- [ ] 50. Aviso al llegar al 80 % y al 100 % del presupuesto de una categoría.
- [ ] 51. Comparación con el mes anterior por categoría (sube/baja).
- [ ] 52. Tendencia del ahorro de los últimos 12 meses.
- [ ] 53. Proyección de fin de mes según el ritmo de gasto variable.
- [ ] 54. Estimado sugerido: promedio de los últimos 3 meses reales.
- [ ] 55. Ajuste por inflación: subir los estimados un % en bloque.
- [ ] 56. Ver montos en valores reales con un índice que carga el usuario.
- [ ] 57. Top 5 gastos del mes.
- [ ] 58. Gasto diario promedio y «disponible por día» hasta fin de mes.
- [ ] 59. Informe mensual con vista para imprimir o guardar como PDF.
- [ ] 60. Resumen anual: totales, mejor y peor mes, por categoría.
- [ ] 61. Buscador y filtros de movimientos (texto, categoría, rango de fechas, monto).
- [ ] 62. Etiquetas libres (#vacaciones, #regalos) para cruzar categorías.

### Fase 5 — Tarjeta, cuotas y monedas
- [ ] 63. Tarjeta de crédito como medio de pago: lo comprado con tarjeta va al resumen del mes siguiente (evita contar dos veces).
- [ ] 64. Fechas de cierre y vencimiento de cada tarjeta.
- [ ] 65. Compras en cuotas: cuota actual, cuánto falta y cuándo termina.
- [ ] 66. Proyección de cuotas comprometidas para los próximos 6 meses.
- [ ] 67. Medios de pago: efectivo, débito, transferencia, varias tarjetas.
- [ ] 68. Gastos en dólares con tipo de cambio cargado por el usuario.
- [ ] 69. Conciliación del resumen: cargar el total de la tarjeta y ver la diferencia con lo registrado.
- [ ] 70. Pago mínimo vs total: aviso si se pagó menos que el total.
- [ ] 71. Préstamos y deudas con saldo y cuotas.
- [ ] 72. Totales por moneda en el resumen.

### Fase 6 — Ahorro y objetivos
- [ ] 73. Metas de ahorro (vacaciones, auto…) con progreso y fecha objetivo.
- [ ] 74. Fondo de emergencia: cuántos meses de gastos cubre.
- [ ] 75. Registro de ahorros (pesos, dólares, plazo fijo) con saldos cargados a mano.
- [ ] 76. Patrimonio simple: suma de cuentas y ahorros.
- [ ] 77. Sugerencia al cerrar el mes: «podés apartar $X para tu meta».
- [ ] 78. Gastos escolares: matrícula, cuotas y materiales con su calendario.
- [ ] 79. Gastos compartidos en pareja: quién pagó qué y saldo entre ambos.
- [ ] 80. Simulador «¿y si…?»: efecto en el ahorro de un aumento o un gasto nuevo.

### Fase 7 — Experiencia de app
- [ ] 81. Botón flotante «+» para cargar un gasto desde cualquier pestaña.
- [ ] 82. Carga rápida: teclado numérico grande, categorías recientes y montos frecuentes.
- [ ] 83. Plantillas de movimientos frecuentes (súper, nafta, farmacia).
- [ ] 84. Deslizar una fila en el celular para pagar o editar.
- [ ] 85. Modo «ocultar montos» para usar la app en público.
- [ ] 86. Bloqueo con PIN (privacidad local básica).
- [ ] 87. Categorías personalizables: crear, renombrar, color e ícono.
- [ ] 88. Íconos por categoría en filas y gráficos.
- [ ] 89. Selector de mes para ver y corregir meses anteriores (no solo el historial resumido).
- [ ] 90. Pantalla de bienvenida la primera vez, con guía rápida.
- [ ] 91. Animaciones sutiles y estados vacíos ilustrados.
- [ ] 92. Preparar como PWA instalable (manifest e íconos) para cuando se aloje en una web.

### Fase 8 — Datos e integraciones
- [ ] 93. Importar movimientos desde un CSV del home banking, con vista previa.
- [ ] 94. Reglas de categorización automática por descripción.
- [ ] 95. Exportar a Excel con varias hojas (mes, historial, categorías).
- [ ] 96. Historial de cambios por ítem (qué se modificó y cuándo).
- [ ] 97. Estructura lista para sincronizar celular y compu cuando se aloje (diseño documentado aquí).
- [ ] 98. Modo familiar (varios usuarios) — depende del 97.
- [ ] 99. Pantalla «Acerca de»: versión, autor (Gonzalo Gabriel Pereira) y guía de uso.
- [ ] 100. Auditoría final: rendimiento con 3 años de datos, accesibilidad, pruebas en iPhone/Android y pulido general.

## Pendientes / problemas abiertos
- (ninguno)
- Nota: los comprobantes (Fase 2) deberían guardarse solo en IndexedDB (no en el espejo de localStorage, que tiene ~5 MB); usar `idbPut` con claves propias (p. ej. `adj:<id>`).

## Registro de cambios
- 2026-11-10 — v1.1: ítems 1 (VERSION + Novedades con aviso), 2 (schemaVersion + migraciones, copia pre-migración, respaldos versionados y migrados al restaurar) y 9 (`tests.py`: flujo en 390x844 y 1280x900, claro/oscuro, sin scroll horizontal, tildar pago, cargar movimiento, cerrar mes, migración desde datos v1.0, primera instalación). Todas las pruebas OK.
- 2026-11-09 — Se crea este documento con la hoja de ruta de 100 mejoras y la tarea diaria de la mañana.
- 2026-11-06 — v1.0: rediseño completo (resumen, categorías, vencimientos, movimientos, historial con gráfico, respaldo, CSV, tema oscuro).


## Instalación en el teléfono (14/11/2026)
- `manifest.json`, `icon-192.png`, `icon-512.png` y `sw.js` permiten instalar la app con su ícono desde la dirección de GitHub Pages. No los borres ni quites las etiquetas `<link rel="manifest">`, ícono y el registro de `sw.js` del `<head>` de index.html.
- `sw.js` no guarda caché a propósito: así Gonzalo ve siempre la última mejora diaria.


## Publicación (14/11/2026)
- La dirección https://gpereira-ucip.github.io/control-de-gastos/ se publica desde la rama gh-pages. El workflow `.github/workflows/publicar.yml` copia main a gh-pages solo en cada push: no lo borres ni toques gh-pages a mano.

- 14/11/2026 · v1.2 (pedido de Gonzalo): en Resumen, «Gastos del mes» muestra todos los gastos fijos (sin «Ver todos») y lo tildado queda tildado en su lugar; sigue apareciendo en «Pagados».
- 16/11/2026 · v1.3: ítem 3. Doble copia IndexedDB + localStorage con marca `rev`, recuperación automática si se borra una copia (con aviso), estado en el menú de Opciones. `tests.py` amplía: datos v1.2 pasan a IndexedDB, escritura en ambas, recuperación tras borrar localStorage, gana la copia más nueva en los dos sentidos, navegador sin IndexedDB; además espera la primera carga antes de sembrar datos (evitaba una falla intermitente). TODO OK.
- 17/11/2026 · v1.4: ítem 4. Aviso de respaldo en Resumen (7 días sin descargar o nunca en este dispositivo) con «Descargar respaldo» y «Más tarde» (3 días); el menú muestra «Último: hoy / ayer / hace X días». Sin cambio de esquema. `tests.py` amplía: aviso con datos viejos, descarga lo apaga y guarda la fecha, vuelve a los 9 días, «Más tarde» pospone 3 días, no aparece en instalación nueva; 390/1280 claro/oscuro sin scroll horizontal. TODO OK.
- 20/11/2026 · v1.7: ítem 7. Validación en línea con mensajes por campo (nombre vacío, día 1–31, montos negativos, con letras, mal puntuados o absurdos) y avisos confirmables («Guardar igual») para cifras raras y fechas de otro mes; el formulario de movimientos ya no avisa con el cartel de abajo sino en el campo. Sin cambio de esquema. `tests.py` amplía: 20 casos del lector de montos, errores en gasto/ingreso/movimiento/mes sin guardar nada, se limpian al escribir, avisos y «Guardar/Agregar igual», 1500.50, IndexedDB al día; 390 claro y 1280 oscuro sin scroll horizontal (las pruebas viejas que cargan movimientos en «Octubre 2026» ahora ponen fecha de octubre). TODO OK.
- 19/11/2026 · v1.6: ítem 6. «Deshacer» en el aviso al eliminar gasto fijo, ingreso, movimiento o mes del historial (la hoja de eliminar mes ya no dice «No se puede deshacer»); el aviso con botón recibe toques solo mientras se ve. Sin cambio de esquema. `tests.py` amplía: cada borrado y su deshacer en 390 claro y 1280 oscuro, posición y estado (pagado, real, cobrado) conservados, IndexedDB al día, recarga igual al inicio, a los 6 s el borrado queda firme. TODO OK.
- 18/11/2026 · v1.5: ítem 5. «Copiar respaldo» (portapapeles, con respaldo a selección manual) y «Pegar respaldo» (botón Pegar + recuadro, mensajes en línea para texto incompleto, ajeno o de esquema futuro), enlace «Copialo como texto» en el aviso de respaldo, copia `pre-restauracion` también al restaurar desde archivo. Sin cambio de esquema. `tests.py` amplía: copiar al portapapeles y anotar fecha, errores sin tocar datos, restaurar con texto alrededor, migrar respaldo v1.0 pegado, IndexedDB al día, sin portapapeles; 390/1280 claro/oscuro. TODO OK.
- 20/11/2026 · v1.8: ítem 8. Accesibilidad: foco visible, filas/meses/tildes con teclado (Enter, Espacio), hojas como diálogo (Escape, Tab no se escapa, fondo inerte, foco vuelve al origen), foco conservado al tildar, Ctrl/Cmd+Z para deshacer, `aria-pressed`/`aria-current`/`aria-expanded`, etiquetas unidas a campos, gráficos con descripción, contraste AA en modo claro (grises, verdes, rojos, ámbar y chips de categoría), `prefers-reduced-motion`. Sin cambio de esquema. `tests.py` amplía: auditoría de contraste de todo texto visible en 4 pestañas + historial + menú, botones con nombre y campos con etiqueta, recorrido con teclado completo; 390/1280 claro/oscuro. TODO OK.
