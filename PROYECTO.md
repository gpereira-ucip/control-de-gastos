# Control Mensual — app de gastos e ingresos de Gonzalo

Proyecto de **Gonzalo Gabriel Pereira**. App personal para registrar gastos e ingresos del hogar y del consultorio, en **un solo archivo HTML** que se abre en el navegador (compu y celular), en español rioplatense, montos en pesos (ARS).

Objetivo: que sea la mejor app de finanzas personales posible, profesional y cómoda de usar todos los días.

## Estado actual

- **Versión:** 1.1 (10 nov 2026) · esquema de datos 1
- **Qué hace hoy:** resumen con ahorro proyectado y % de los ingresos; gastos fijos con checklist de pagado, categoría, día de vencimiento y monto real vs estimado; ingresos con cobrado/pendiente; movimientos (gastos variables) con fecha y categoría; cierre de mes con historial, gráfico de evolución y detalle por categoría; respaldo/restauración JSON, exportación CSV, modo claro/oscuro, menú de opciones; pantalla «Novedades» con aviso (punto en el botón de menú) al actualizar; versión visible al pie del menú; datos con `schemaVersion` y migraciones automáticas (también al restaurar respaldos viejos), con copia interna previa a cada migración.
- **Archivos en este artifact:** `index.html` (la app completa, todo el código), `PROYECTO.md` (este documento: memoria del proyecto) y `tests.py` (pruebas Playwright: `python3 tests.py index.html capturas`).
- **Datos y migraciones (desde v1.1):** clave `control-mensual:meta` = `{schemaVersion, appVersion, vistoNovedades[]}`. Esquema 0 = datos v1.0 sin meta. Para cambiar la estructura: subir `SCHEMA_VERSION` y agregar `MIGRATIONS[n](d)` que reciba `{config,current,history}` del esquema n-1. Antes de migrar se guarda `control-mensual:pre-migracion-esquema-<n>` con los textos originales. Si los datos son de un esquema más nuevo que la app, no se sobrescriben.
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
- [ ] 3. Guardado en IndexedDB con respaldo en localStorage (más espacio, necesario para adjuntos), migrando los datos actuales sin pérdida.
- [ ] 4. Aviso «hace X días que no descargás un respaldo» con acceso directo.
- [ ] 5. Respaldo alternativo para cuando la descarga está bloqueada: «Copiar respaldo» y «Pegar respaldo» (texto).
- [ ] 6. «Deshacer» en el aviso inferior al borrar un gasto, ingreso, movimiento o mes.
- [ ] 7. Validación de montos y campos con mensajes en línea (vacíos, negativos, cifras absurdas).
- [ ] 8. Accesibilidad: foco visible, aria-labels, contraste AA, navegación con teclado y Escape en las hojas.
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
- Nota para la próxima corrida: el ítem 3 (IndexedDB) es grande; conviene hacerlo como migración de esquema 2 manteniendo una copia espejo en localStorage, y ampliar `tests.py` con su prueba de migración.

## Registro de cambios
- 2026-11-10 — v1.1: ítems 1 (VERSION + Novedades con aviso), 2 (schemaVersion + migraciones, copia pre-migración, respaldos versionados y migrados al restaurar) y 9 (`tests.py`: flujo en 390x844 y 1280x900, claro/oscuro, sin scroll horizontal, tildar pago, cargar movimiento, cerrar mes, migración desde datos v1.0, primera instalación). Todas las pruebas OK.
- 2026-11-09 — Se crea este documento con la hoja de ruta de 100 mejoras y la tarea diaria de la mañana.
- 2026-11-06 — v1.0: rediseño completo (resumen, categorías, vencimientos, movimientos, historial con gráfico, respaldo, CSV, tema oscuro).
