# Control Mensual — app de gastos e ingresos de Gonzalo

Proyecto de **Gonzalo Gabriel Pereira**. App personal para registrar gastos e ingresos del hogar y del consultorio, en **un solo archivo HTML** que se abre en el navegador (compu y celular), en español rioplatense, montos en pesos (ARS).

Objetivo: que sea la mejor app de finanzas personales posible, profesional y cómoda de usar todos los días.

## Estado actual

- **Versión:** 2.5 (26 nov 2026) · esquema de datos 1
- **Qué hace hoy:** resumen con ahorro proyectado y % de los ingresos; gastos fijos con checklist de pagado, categoría, día de vencimiento y monto real vs estimado; ingresos con cobrado/pendiente; movimientos (gastos variables) con fecha y categoría; cierre de mes con historial, gráfico de evolución y detalle por categoría; respaldo/restauración JSON, exportación CSV, modo claro/oscuro, menú de opciones; pantalla «Novedades» con aviso (punto en el botón de menú) al actualizar; versión visible al pie del menú; datos con `schemaVersion` y migraciones automáticas (también al restaurar respaldos viejos), con copia interna previa a cada migración; lista del mes completa como checklist (v1.2); doble copia de los datos en IndexedDB + localStorage con recuperación automática y estado visible en el menú (v1.3); aviso en Resumen «hace X días que no descargás un respaldo» con botón «Descargar respaldo» y «Más tarde» (3 días), y fecha del último respaldo en el menú (v1.4); «Copiar respaldo» y «Pegar respaldo» como texto, con errores en línea y copia interna `pre-restauracion` antes de restaurar (v1.5); «Deshacer» en el aviso inferior al eliminar un gasto fijo, un ingreso, un movimiento o un mes del historial, con 6 segundos para recuperarlo en su lugar y con su estado (v1.6); validación en línea en los formularios (gasto, ingreso, movimiento, nombre del mes): errores por campo y avisos de cifras raras con «Guardar igual» (v1.7); accesibilidad: foco visible, todo usable con teclado (filas y meses con Enter/Espacio), hojas como diálogo con Escape, foco atrapado y devuelto al cerrar, foco conservado al redibujar, Ctrl/Cmd+Z deshace, contraste AA en claro y oscuro, nombres para lectores de pantalla (v1.8); redibujo fino: solo cambia lo distinto, sin saltos ni parpadeo, barra y anillo animados, lo escrito en «Registrar gasto» no se pierde (v1.9); «Calendario» en Gastos fijos: grilla del mes (lunes a domingo) con puntos por estado de cada vencimiento y lo que falta pagar por día, tocar un día muestra y deja tildar sus gastos, lista de gastos sin día, flechas del teclado (v2.0); aviso de vencimientos arriba del Resumen (vencido, hoy, mañana o en 2–3 días) con total a pagar, «Pagado» por gasto con Deshacer y «Ver en el calendario» (v2.1); «Agregar al calendario»: descarga los vencimientos del mes en un .ics con aviso elegible (mismo día, 1/2/3 días o 1 semana antes, o sin aviso), solo sin pagar o todos, con vista previa; desde el calendario y el menú (v2.2); «Agregar a Google Calendar» en la hoja de cada gasto fijo: abre Google Calendar con el vencimiento del mes (día, monto, categoría, estado y nota) listo para guardar, con lo escrito en la hoja (v2.3); «Avisos del navegador»: con permiso, al abrir la app (o volver a ella) llega una notificación por día si hay algo vencido, que vence hoy o en los próximos 3 días, con filas y total; se activan desde el menú o desde el aviso de vencimientos, con «Probar» y «Desactivar», e instrucciones si están bloqueadas o el navegador no las permite (v2.4); «Anticipación del aviso»: 1, 3, 5 o 7 días (3 por defecto) para el aviso del Resumen, las notificaciones y el «vence pronto» del calendario, con vista previa de lo que verías hoy; desde el menú, el aviso y la hoja de notificaciones (v2.5).
- **Archivos en este artifact:** `index.html` (la app completa, todo el código), `PROYECTO.md` (este documento: memoria del proyecto) y `tests.py` (pruebas Playwright: `python3 tests.py index.html capturas`).
- **Datos y migraciones (desde v1.1):** clave `control-mensual:meta` = `{schemaVersion, appVersion, vistoNovedades[]}`. Esquema 0 = datos v1.0 sin meta. Para cambiar la estructura: subir `SCHEMA_VERSION` y agregar `MIGRATIONS[n](d)` que reciba `{config,current,history}` del esquema n-1. Antes de migrar se guarda `control-mensual:pre-migracion-esquema-<n>` con los textos originales. Si los datos son de un esquema más nuevo que la app, no se sobrescriben.
- **Almacenamiento (desde v1.3):** cada guardado escribe en localStorage (`control-mensual:<clave>`) y en IndexedDB (base `control-mensual`, almacén `kv`, mismas claves sin prefijo) y deja la marca `rev` (ms) en las dos. Al abrir gana la copia con `rev` mayor (empate o sin marca: localStorage) y la otra se resincroniza. Si localStorage no se pudo escribir completo, su `rev` queda en 0. Sin IndexedDB, la app sigue solo con localStorage. No hizo falta subir el esquema: la estructura de los datos no cambió.
- **Aviso de respaldo (desde v1.4):** en `meta.respaldo = {ultimo, base, pospuesto}` (ms). Aparece si pasaron 7 días desde `ultimo`; si nunca hubo descarga, cuenta desde `base` (0 si ya había datos al actualizar → avisa enseguida; fecha de instalación si es nueva). «Más tarde» fija `pospuesto` = ahora + 3 días. Constantes `RESPALDO_DIAS` y `RESPALDO_POSPONER_DIAS`. No es parte de los datos: no cambia el esquema.
- **Respaldo como texto (desde v1.5):** `respaldoJSON()` arma el mismo contenido que el .json (en una línea para copiar). `leerRespaldo(texto)` tolera texto alrededor y devuelve `{d}` o `{error}`; `aplicarRespaldo(d)` (lo usan archivo y texto) guarda antes `control-mensual:pre-restauracion` con los datos que había, migra y guarda. Copiar con éxito cuenta como respaldo (`marcarRespaldo()`); si el portapapeles falla, indica copiar a mano.
- **Deshacer (desde v1.6):** `toast(msg, fn)` muestra «Deshacer» durante `UNDO_MS` (6 s) y ejecuta `fn` una sola vez; un aviso nuevo reemplaza al anterior y su «Deshacer». Cada borrado guarda el elemento, su posición y su estado del mes (pagado/real o cobrado) y lo devuelve con `reinsertar(arr, idx, item)`. Si entre medio cambió el mes o se restauró un respaldo (otro objeto `config`/`current`/`hist`), no restaura y avisa. Sin cambio de esquema.
- **Validación (desde v1.7):** `leerMonto(texto)` → `{n}` (`''` si vacío) o `{error}`: miles con punto de a 3, centavos con coma y hasta 2 cifras, también `1500.50` (punto + 1-2 cifras = decimal) y `1,250,000`; rechaza negativos, letras, `12,500` (sugiere `12.500`) y más de `MONTO_MAX` (1e10). `parseMonto` usa `leerMonto` (error → `''`). `validarForm(form, errores, avisos)` marca cada campo (`aria-invalid` + `.f-msg`), enfoca el primero y no guarda; los avisos (`.f-msg.warn`) se muestran una vez y el botón pasa a «Guardar/Agregar igual» (firma de los valores en `form.dataset.ok`; cualquier cambio los quita). Avisos actuales: real > 10× estimado; movimiento mayor que los ingresos del mes; fecha de movimiento fuera del mes en curso. Sin cambio de esquema.
- **Accesibilidad (desde v1.8):** `:focus-visible` con contorno `--primary` (los `.inp` mantienen su anillo). Filas (`.row-main`) y meses (`.h-head`) son `role=button tabindex=0`; un `keydown` global los activa con Enter/Espacio. `render()` guarda `claveFoco(activeElement)` (selector por `data-act`/`data-id`/`data-tab`/`data-f`/`data-i`) y lo restaura con `enfocarClave` (sin scroll). `openSheet` crea `role=dialog aria-modal` con título `#sheet-title`, deja `inert` el encabezado y `#app`, atrapa Tab, cierra con Escape (`sheetActual.close()`) y devuelve el foco al control que la abrió (o al menú). `asociarLabels(root)` une cada `<label>` de `.field` con su `.inp`. Contraste claro: `--muted #5B6576`, `--pos #047857`, `--neg #C81E1E`, `--warn #B45309`, `--chip-mix 52%`; `tests.py` trae una auditoría de contraste (`AUDIT_JS`) que recorre todo texto visible. Sin cambio de esquema.
- **Redibujo fino (desde v1.9):** `render()` arma la pantalla en un `<main>` aparte y `morphHijos(app, nuevo)` sincroniza atributos, textos e hijos (la primera vez, `replaceChildren`). Filas con `data-key` (`g-<id>`, `i-<id>`, `m-<id>`, `d-<fecha>`, `h-<mes>-<guardado>`) se reconocen aunque cambie el orden o se borren otras; el resto se empareja por posición y etiqueta. Los campos conservan lo escrito (el valor no es atributo): para vaciar un formulario usar `form.reset()` (así lo hace «Registrar gasto»). No se borran los `id` `campo-N` de `asociarLabels`. El foco solo se restaura con `claveFoco` si el elemento enfocado desapareció. Se arregló una carrera: el foco automático de las hojas (50 ms, compu) ya no le saca el foco a un campo que el usuario ya eligió. Sin cambio de esquema.
- **Calendario (desde v2.0):** `ui.vistaFijos` (`lista` por defecto | `cal`, solo en memoria) y `ui.diaCal` (día elegido; por defecto hoy si el mes es el actual, si no el primer día con vencimientos). `vencimientosDelMes()` agrupa `config.gastos` por `vence` (redondeado; si pasa el último día del mes cae en el último; vacío o <1 va a «Sin día»). `estadoVence(x, dia, m, y)` → `ok`/`vencido`/`hoy`/`pronto` (≤3 días)/`pend`, usando la fecha de hoy solo si `mesLabel` es el mes en curso (si el nombre no se entiende, se usa el mes de hoy). Las celdas son `button.cal-d[data-act=cal-dia][data-i=<día>]` con `aria-label` completo; las flechas mueven el día (±1, ±7). Las filas de abajo son `gastoRow` (se tildan y editan igual). Sin cambio de esquema.
- **Aviso de vencimientos (desde v2.1):** `vencimientosAviso()` → `[{x, dia, diff, monto}]` de gastos sin pagar con día, solo si `mesLabel` es el mes en curso, con `diff ≤ VENCE_PRONTO_DIAS` (3; el ítem 16 lo hará configurable), día topado al último del mes; orden por `diff` y luego monto. `vencAviso()` dibuja `#aviso-vence` (clase `danger` si hay vencidos, si no ámbar) antes del aviso de respaldo; filas `data-key=va-<id>`; `data-act=aviso-pagar` tilda con toast «Deshacer»; `data-act=ver-cal` abre Gastos fijos › Calendario en hoy. `venceTag` ahora también topa el día al último del mes. Ícono `bell`. Sin cambio de esquema. `tests.py` fija la fecha con `ctx.clock.set_fixed_time` (`new_page(..., fecha=)`).
- **Exportar a calendario (desde v2.2):** `sheetICS()` (botón `data-act=ics` en el encabezado del calendario y `MENU.ics`). `armarICS({alarma, todos})` → `{texto, n, nombre}`: un VEVENT de día completo por gasto con día (de `vencimientosDelMes`, topado al último día) en el mes de `mesCal()`, `UID:cm-<id>-<AAAAMM>@control-mensual` (estable: reimportar actualiza en los calendarios que lo respetan), SUMMARY «Vence X · $monto» (✓ si pagado), DESCRIPTION con monto (real o «estimado»), categoría, estado y nota; VALARM solo en los no pagados según `ICS_ALARMAS` (relativo a medianoche: `-PT15H` = 9:00 del día anterior). CRLF, `icsEsc` (\\ ; , saltos) e `icsFold` (75 octetos UTF-8). Archivo `vencimientos-AAAA-MM.ics`. Preferencia en `meta.ics = {alarma, todos}` (no son datos: sin cambio de esquema); se carga en `ui.ics`. Si no hay nada para exportar, la hoja lo dice y no descarga.
- **Google Calendar por gasto (desde v2.3):** `gcalURL({nombre,dia,monto,estimado,categoria,nota,pagado})` arma `https://calendar.google.com/calendar/render?action=TEMPLATE&text=…&dates=AAAAMMDD/AAAAMMDD+1&details=…` (evento de día completo en el mes de `mesCal()`, día topado al último del mes; `encodeURIComponent`). En `sheetGasto` el bloque `#gcal` (enlace `a.btn-gcal`, `target=_blank rel=noopener`, y un `<p>` con la fecha) se recalcula en cada `input`/`change` con `gcalDesdeForm` (usa los valores escritos aunque no estén guardados; monto real si hay, si no estimado). Sin día válido, el enlace queda `hidden` y el texto pide completar el día. Evento único del mes (sin repetición, porque el monto cambia). Sin cambio de esquema.
- **Avisos del navegador (desde v2.4):** `meta.notif = {activo, ultimo:'AAAA-MM-DD'|null}` (no son datos: sin cambio de esquema), en `ui.notif`. `notifRevisar(forzar)` corre al terminar la carga y en `visibilitychange` (visible): si `activo`, permiso `granted` y `vencimientosAviso()` no está vacío, y `ultimo` no es hoy, anota hoy y muestra la notificación (`tag: control-mensual-vencimientos`, título `vencTitulo(l)` —el mismo del aviso— y cuerpo con hasta 4 filas «Nombre · Vence… · $» + «Total a pagar»). `mostrarNotif` usa `registration.showNotification` si hay service worker (https; Android no acepta `new Notification`) y si no `new Notification` (tocarla enfoca y va al Resumen); `sw.js` tiene `notificationclick` que enfoca o abre la app. `sheetNotif()` (menú `notif` y enlace `data-act=notif` en `#aviso-vence`, que solo aparece si hay soporte, no está bloqueado y no están activos) tiene 4 estados: sin soporte, bloqueadas, activos (Desactivar/Probar/Listo) y desactivados (Activar avisos → `Notification.requestPermission`, promesa o callback). En `tests.py`, `NOTIF_MOCK` simula `Notification` con estado en `window.name` (usar localStorage o sessionStorage en el simulacro hacía fallar al azar la semilla); `new_page(..., init=)` agrega scripts de inicio y ahora cierra la base interna antes de borrarla.
- **Anticipación del aviso (desde v2.5):** `meta.aviso = {dias}` (no son datos: sin cambio de esquema), en `ui.avisoDias`; valores válidos `AVISO_DIAS_OPC` = [1,3,5,7], cualquier otro (o ausente) usa `VENCE_PRONTO_DIAS` (3) vía `avisoDias()`. `vencimientosAviso(dias=avisoDias())` (la vista previa le pasa otro valor), `estadoVence` usa `avisoDias()` para `pronto`. `sheetAnticipo()` (menú `anticipo`, `data-act=anticipo` en `#aviso-vence` con el texto «Avisar N días antes · cambiar», y `data-run=anticipo` en la hoja de notificaciones): `fieldset.ant-opts` con radios `name=dias` (flechas del teclado nativas), `#ant-prev` = `antPrevia(d)` (otro mes: lo explica). Ícono `clock`.
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
- [x] 10. (v1.9) Render más fino: actualizar solo lo que cambia, sin saltos de scroll al tildar.

### Fase 1 — Vencimientos y alertas
- [x] 11. (v2.0) Vista «Calendario del mes» con los vencimientos marcados por día.
- [x] 12. (v2.1) Banner en Resumen: «Hoy vence…», «Vence en 2 días», «Vencido».
- [x] 13. (v2.2) Exportar vencimientos del mes a calendario (.ics) con alarma configurable.
- [x] 14. (v2.3) Botón «Agregar a Google Calendar» por gasto (enlace con fecha, monto y nota).
- [x] 15. (v2.4) Notificación del navegador al abrir la app si hay vencimientos próximos (con permiso).
- [x] 16. (v2.5) Anticipación del aviso configurable (1, 3, 5 o 7 días).
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
- 20/11/2026 · v1.9 (corrida extra pedida por Gonzalo): ítem 10. Redibujo por diferencias con filas con clave: al tildar, cobrar o borrar cambia solo lo necesario (mismo nodo, sin salto de scroll, foco en su lugar), barra «Pagado», anillo y donut animados, lo escrito en «Registrar gasto» sobrevive y el formulario se vacía con `reset()` al agregar. Arreglo de la carrera del foco automático en hojas (escribir en otro campo enseguida de abrirla mandaba el texto a «Nombre»). Sin cambio de esquema. `tests.py` amplía: mismo nodo y sin salto en Resumen y Gastos fijos con 25 gastos, ingresos, filtro «Pendientes», borrar movimiento conserva los otros, texto sobrevive al redibujo, formulario vacío y fecha de hoy al agregar, pestañas; 390/1280 claro/oscuro. TODO OK.
- 21/11/2026 · v2.0: ítem 11. «Calendario» en Gastos fijos (selector Lista/Calendario): mes en grilla desde el lunes, cada día con puntos de estado (pendiente, vence pronto/hoy, vencido, pagado) y lo que falta pagar, hoy subrayado, día elegido con sus gastos debajo para tildar o editar, «Sin día de vencimiento» con indicación, flechas del teclado, leyenda. Sin cambio de esquema. `tests.py` amplía: lista por defecto, cantidad de días y arranque en lunes, estados con la fecha de hoy, día 31 en mes de 30, tildar desde el calendario (mismo nodo, guardado), elegir días, flechas, hoja de edición, contraste AA, configuración intacta; la prueba de versión del menú ahora compara con `VERSION`. 390/1280 claro/oscuro. TODO OK.
- 22/11/2026 · v2.1: ítem 12. Aviso de vencimientos en Resumen: título según lo más urgente («X está vencido», «Hoy vence X», «X: vence en 2 días»), resumen del resto y total a pagar, filas con etiqueta (Vencido · día N / Vence hoy / mañana / en N días) y botón «Pagado» (con Deshacer), «Ver en el calendario»; rojo si hay vencidos, ámbar si no; solo en el mes en curso. Día 31 en un mes de 30 cuenta como el 30 también en la etiqueta de la fila. Sin cambio de esquema. `tests.py` amplía (fecha fija): orden y filtros, títulos, total, pagar y deshacer, calendario en hoy, otro mes sin aviso, mañana, 31→30, todo pagado; contraste AA; 390/1280 claro/oscuro. TODO OK.
- 23/11/2026 · v2.2: ítem 13. «Agregar al calendario» (botón en el calendario de Gastos fijos, ícono solo en pantallas angostas, y en el menú): hoja con «Aviso» (sin aviso, mismo día 9 h, 1/2/3 días antes 9 h, 1 semana antes) y «Qué gastos» (sin pagar / todos), vista previa con total; descarga `vencimientos-AAAA-MM.ics` (eventos de día completo, UID estable, aviso solo en los no pagados); recuerda la elección. Sin cambio de esquema. `tests.py` amplía: archivo descargado (CRLF, ≤75 octetos, escapes, 31→30, DTEND, UID, monto real/estimado, alarmas 1 día/1 semana/ninguna, «Todos» con ✓), preferencia guardada y recordada al recargar, todo pagado no descarga, datos intactos, contraste AA; 390 claro y 1280 oscuro. TODO OK.
- 24/11/2026 · v2.3: ítem 14. «Agregar a Google Calendar» en la hoja de cada gasto fijo (y al crear uno): enlace que abre Google Calendar en otra pestaña con el vencimiento del mes en curso ya cargado (todo el día, «Vence X · $monto», detalles con monto real o estimado, categoría, estado y nota); usa lo escrito en la hoja sin guardar; día 31 en mes de 30 cae el 30; sin día se oculta y lo indica. Sin cambio de esquema. `tests.py` amplía: URL (host, action, dates, text, details), 31→30, valores sin guardar, sin día, gasto nuevo, caracteres especiales, abre pestaña nueva, datos intactos, contraste AA; 390 claro y 1280 oscuro. TODO OK.
- 25/11/2026 · v2.4: ítem 15. «Avisos del navegador»: opción en el menú y enlace «Avisarme con una notificación» en el aviso de vencimientos; al activarlos se pide permiso y llega la primera notificación; después, una por día al abrir o volver a la app si hay vencidos, de hoy o de los próximos 3 días (título como el aviso, filas y total), tocarla lleva al Resumen; «Probar» y «Desactivar»; mensajes si el permiso se niega, si están bloqueadas (cómo habilitarlas) o si el navegador no las permite (iPhone: agregar a inicio); siempre recuerda que con la app cerrada no hay aviso y ofrece el .ics. `sw.js` abre la app al tocar la notificación. Sin cambio de esquema. `tests.py` amplía (Notification simulada): activar, contenido, meta.notif, una por día, al volver otro día, otro mes, bloqueadas, sin soporte, permiso negado, Probar/Desactivar, datos intactos, contraste AA; 390/1280 claro/oscuro; arreglo de una carrera al sembrar datos (se cierra la base interna antes de borrarla). TODO OK.
- 26/11/2026 · v2.5: ítem 16. «Anticipación del aviso» (Opciones, enlace «Avisar N días antes · cambiar» en el aviso de vencimientos y «Cambiar anticipación» en Avisos del navegador): 1, 3, 5 o 7 días, con vista previa de lo que verías hoy (cantidad, total y filas); cambia el aviso del Resumen, las notificaciones y el «vence pronto» del calendario; se guarda en `meta.aviso`. Sin cambio de esquema. `tests.py` amplía: 3 por defecto, elegir con toque y con flechas, guardar/cancelar, recargar, calendario, notificación y texto con 7 días, valor inválido → 3, 5 días, otro mes; contraste AA; 390/1280 claro/oscuro. TODO OK.
