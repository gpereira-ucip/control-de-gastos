#!/usr/bin/env python3
"""Pruebas de Control Mensual (Playwright).

Uso:  python3 tests.py [ruta/index.html] [carpeta_capturas]
Abre el archivo local (file://), en 390x844 y 1280x900, claro y oscuro, y verifica:
  - sin errores de consola ni de página
  - sin scroll horizontal (scrollWidth == ancho)
  - recorrer pestañas, tildar un pago, cargar un movimiento, cerrar un mes
  - migración: datos con formato v1.0 (sin esquema) se leen sin perder nada
  - novedades / versión
  - (v1.3) doble copia IndexedDB + localStorage: espejo, recuperación si se borra localStorage,
    gana la copia más nueva, datos v1.2 (solo localStorage) pasan a IndexedDB sin pérdida
  - (v1.4) aviso de respaldo: aparece con datos viejos sin respaldo, «Descargar» lo apaga y anota la fecha,
    «Más tarde» lo pospone 3 días, vuelve a los 7 días, no aparece en instalación nueva
  - (v1.5) respaldo como texto: «Copiar respaldo» copia al portapapeles y anota la fecha; «Pegar respaldo»
    restaura (con texto alrededor), migra uno v1.0, rechaza texto incompleto/ajeno con mensaje en línea
    sin tocar los datos, guarda 'pre-restauracion' antes de reemplazar; 390/1280 claro/oscuro
  - (v1.6) «Deshacer» en el aviso al eliminar gasto fijo, ingreso, movimiento o mes del historial: vuelve
    a su lugar con su estado (pagado/real), queda en IndexedDB, vence a los 6 s; 390/1280 claro/oscuro
  - (v1.7) validación en línea: lector de montos (miles, centavos, 1500.50, negativos, letras, 12,500, cifras
    absurdas), errores por campo sin guardar (gasto, ingreso, movimiento, nombre del mes), se limpian al
    escribir, avisos de cifras raras con «Guardar/Agregar igual»; 390 claro y 1280 oscuro
  - (v1.8) accesibilidad: contraste AA de todo texto visible (4 pestañas, historial abierto, menú, vencimientos),
    botones con nombre, campos con etiqueta, filas y meses con Tab + Enter/Espacio, foco visible, hojas como
    diálogo (fondo inerte, Tab no se escapa, Escape cierra y el foco vuelve), tildar con teclado conserva el
    foco, Ctrl+Z deshace; 390/1280 claro/oscuro
  - (v1.9) redibujo fino: al tildar gasto o ingreso la fila es el mismo nodo, no se mueve el scroll ni la fila,
    la barra «Pagado» es el mismo nodo (anima); filtro «Pendientes» quita solo esa fila; borrar un movimiento
    conserva los nodos de los demás; lo escrito en «Registrar gasto» sobrevive a un redibujo y se vacía al
    agregar; cambiar de pestaña sigue andando; 390/1280 claro/oscuro
  - (v2.0) calendario del mes en «Gastos fijos»: la lista sigue siendo la vista por defecto; grilla que arranca
    en lunes, con los días del mes; puntos por estado (pagado, pendiente, vence pronto, vencido) calculados con
    la fecha de hoy; día 31 en un mes de 30 cae el último día; tocar un día muestra sus gastos y se pueden tildar
    ahí (mismo nodo, guardado); «Sin día de vencimiento» lista los que no tienen día; flechas del teclado;
    nombres para lectores de pantalla; contraste AA; datos sin cambios; 390/1280 claro/oscuro
  - (v2.1) aviso de vencimientos en Resumen (fecha fija con el reloj de Playwright): vencido, hoy y próximos 3
    días, sin pagados ni lejanos ni sin día; título y total; orden; «Pagado» desde el aviso guarda y se deshace;
    «Ver en el calendario» abre el día de hoy; no aparece en otro mes; día 31 en mes de 30 vence el 30 (también
    la etiqueta de la fila); contraste AA; 390/1280 claro/oscuro
  - (v2.2) exportar vencimientos a .ics (fecha fija): botón en el calendario y en el menú; hoja con aviso y
    «Qué gastos»; vista previa que cambia; descarga con un VEVENT por gasto sin pagar (todo el día, UID estable,
    31→30, DTEND al día siguiente), VALARM según el aviso elegido (y ninguno en «Sin aviso» o pagados), CRLF,
    líneas de ≤75 octetos, texto escapado; «Todos» suma los pagados; la elección queda en meta.ics y se
    recuerda al recargar; sin días → mensaje sin descarga; datos sin cambios; contraste AA; 390/1280 claro/oscuro
  - (v2.3) «Agregar a Google Calendar» en la hoja de cada gasto fijo (fecha fija): enlace a calendar.google.com
    (action=TEMPLATE, todo el día, 31→30, título con monto real o estimado, detalles con categoría, estado y nota),
    abre en pestaña nueva; usa lo escrito sin guardar; sin día → oculto con indicación; gasto nuevo; datos sin
    cambios; contraste AA; 390/1280 claro/oscuro
  - (v2.4) avisos del navegador (Notification simulada, fecha fija): enlace en el aviso de vencimientos y opción en
    el menú; activar pide permiso, guarda meta.notif y muestra la notificación (título y total); una sola por día
    (al recargar no repite; al día siguiente sí; al volver a la app con visibilitychange); permiso negado → mensaje
    en línea; bloqueadas o sin soporte → sin enlace e instrucciones; «Probar» y «Desactivar»; otro mes sin aviso;
    datos sin cambios; contraste AA; 390/1280 claro/oscuro
  - (v2.5) anticipación del aviso (1, 3, 5 o 7 días; fecha fija): por defecto 3; opción en el menú, enlace en el
    aviso y en la hoja de notificaciones; vista previa que cambia al elegir (también con flechas del teclado);
    «Guardar» deja meta.aviso y cambia el aviso, el estado «pronto» del calendario, el texto de las notificaciones
    y lo que notifica; «Cancelar» no cambia nada; se recuerda al recargar; meta sin la preferencia o con un valor
    inválido usa 3; otro mes lo explica; datos sin cambios; contraste AA; 390/1280 claro/oscuro
  - (v2.6) frecuencia de cada gasto (esquema 2; fecha fija): datos del esquema 1 migran a «mensual» sin perder nada
    (copia pre-migración, totales iguales); hoja con Frecuencia y «Se paga en» (oculto si es mensual), texto con los
    meses y el próximo pago, «Estimado por pago», sin «Real este mes» si no toca; un trimestral que no toca no suma,
    no está en el Resumen, el calendario ni el aviso, y se ve aparte en Gastos fijos con «Próximo: enero 2027»; uno
    bimestral que toca lleva su etiqueta y avisa; Google Calendar apunta al próximo pago; se recuerda al recargar;
    al cerrar el mes cambia lo que toca; respaldo del esquema 1 restaurado migra; contraste AA; 390/1280 claro/oscuro
Sale con código 1 si algo falla. Ampliar en cada corrida con lo nuevo.
"""
import json, os, sys, pathlib
from playwright.sync_api import sync_playwright

HTML = pathlib.Path(sys.argv[1] if len(sys.argv) > 1 else 'index.html').resolve()
SHOTS = pathlib.Path(sys.argv[2] if len(sys.argv) > 2 else 'capturas'); SHOTS.mkdir(exist_ok=True)
URL = HTML.as_uri()
P = 'control-mensual:'
fails = []

def check(cond, msg):
    print(('  OK  ' if cond else '  FALLA ') + msg)
    if not cond: fails.append(msg)

# Datos con el formato de la v1.0 (sin 'meta' ni schemaVersion)
V10 = {
    'config': {'ingresos': [{'id': 'i1', 'nombre': 'Sanatorio', 'estimado': 1000000, 'nota': ''}],
               'gastos': [{'id': 'g1', 'nombre': 'Luz', 'estimado': 50000, 'categoria': 'servicios', 'vence': 10, 'nota': 'n'},
                          {'id': 'g2', 'nombre': 'Expensas', 'estimado': 200000, 'nota': ''}]},  # sin categoría a propósito
    'current': {'mesLabel': 'Octubre 2026', 'gastos': {'g1': {'real': 61000, 'pagado': True}, 'g2': {'real': '', 'pagado': False}},
                'ingresos': {'i1': {'real': '', 'cobrado': True}},
                'movimientos': [{'id': 'm1', 'desc': 'Súper', 'monto': 35000, 'categoria': 'comida', 'fecha': '2026-10-05', 'ts': 1}]},
    'history': [{'mesLabel': 'Septiembre 2026', 'ingresos': 900000, 'gastos': 700000, 'ahorro': 200000, 'guardado': '2026-10-01'}],
}

def new_page(b, w, h, theme=None, seed=None, fecha=None, init=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1)
    if init: ctx.add_init_script(init)
    if fecha: ctx.clock.set_fixed_time(fecha)  # 'AAAA-MM-DDTHH:MM:SS' (hora local)
    # Google Fonts es el único recurso externo permitido (con respaldo del sistema): sin red, se responde vacío.
    ctx.route(lambda u: not u.startswith('file:'), lambda r: r.fulfill(status=200, body='', content_type='text/css'))
    page = ctx.new_page()
    errs = []
    page.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.on('dialog', lambda d: (errs.append('dialog nativo: ' + d.message), d.dismiss()))
    page.goto(URL)
    page.wait_for_selector('.hero')  # que termine la primera carga antes de sembrar datos
    if seed is not None or theme:
        page.evaluate("""([seed, theme, P]) => new Promise(res => { localStorage.clear();
            if (seed) for (const [k, v] of Object.entries(seed)) localStorage.setItem(P + k, JSON.stringify(v));
            if (theme) localStorage.setItem(P + 'theme', theme);
            try { if (typeof store !== 'undefined' && store.idb) store.idb.close(); } catch (e) {}  // si no, el borrado queda bloqueado y la base vieja puede ganarle a la semilla
            const rq = indexedDB.deleteDatabase('control-mensual'); rq.onsuccess = rq.onerror = rq.onblocked = () => res(true); })""", [seed, theme, P])
        page.reload()
    page.wait_for_selector('.hero')
    return ctx, page, errs

def no_hscroll(page, w, label):
    sw = page.evaluate('document.documentElement.scrollWidth')
    check(sw == w, f'{label}: sin scroll horizontal (scrollWidth {sw} == {w})')

def flujo(b, w, h, theme):
    label = f'{w}x{h} {theme}'
    print(f'\n== Flujo {label}')
    ctx, page, errs = new_page(b, w, h, theme=theme, seed={})
    page.screenshot(path=str(SHOTS / f'resumen-{w}-{theme}.png'), full_page=True)
    no_hscroll(page, w, label)
    for tab in ['fijos', 'movimientos', 'historial', 'resumen']:
        page.click(f'.nav [data-tab={tab}]'); page.wait_for_timeout(150)
        no_hscroll(page, w, f'{label} pestaña {tab}')
    # tildar un pago
    page.click('.nav [data-tab=fijos]')
    before = page.locator('.row.is-done').count()
    page.locator('[data-act=toggle-gasto]').first.click(); page.wait_for_timeout(100)
    check(page.locator('.row.is-done').count() == before + 1, f'{label}: tildar pagado')
    # cargar movimiento
    page.click('.nav [data-tab=movimientos]')
    page.fill('#mov-form [name=desc]', 'Farmacia'); page.fill('#mov-form [name=monto]', '12.500')
    page.click('#mov-form button')
    page.wait_for_timeout(150)
    check(page.locator('.row-title', has_text='Farmacia').count() == 1, f'{label}: cargar movimiento')
    movs = page.evaluate(f"JSON.parse(localStorage.getItem('{P}current')).movimientos")
    check(any(m['monto'] == 12500 for m in movs), f'{label}: movimiento guardado con monto 12500')
    # novedades desde el menú
    page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet')
    check(page.evaluate('VERSION') in page.locator('.ver-foot').inner_text(), f'{label}: versión visible en el menú')
    page.click('[data-run=novedades]'); page.wait_for_selector('.nov'); page.wait_for_timeout(500)
    page.screenshot(path=str(SHOTS / f'novedades-{w}-{theme}.png'))
    page.keyboard.press('Escape'); page.wait_for_timeout(100)
    # cerrar mes
    if w <= 720: page.click('#close-mobile')
    else: page.click('.appbar [data-act=cerrar-mes]')
    page.wait_for_selector('.sheet'); page.click('.sheet button[type=submit]'); page.wait_for_timeout(200)
    hist = page.evaluate(f"JSON.parse(localStorage.getItem('{P}history'))")
    check(len(hist) == 1, f'{label}: cerrar mes guarda en historial')
    page.click('.nav [data-tab=historial]'); page.wait_for_timeout(150)
    page.screenshot(path=str(SHOTS / f'historial-{w}-{theme}.png'), full_page=True)
    check(not errs, f'{label}: sin errores de consola {errs}')
    ctx.close()

def migracion(b):
    print('\n== Migración desde v1.0')
    ctx, page, errs = new_page(b, 390, 844, seed=V10)
    get = lambda k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    meta, cfg, cur, hist = get('meta'), get('config'), get('current'), get('history')
    check(meta and meta.get('schemaVersion', 0) >= 1, f'meta.schemaVersion grabado ({meta})')
    check(page.evaluate(f"!!localStorage.getItem('{P}pre-migracion-esquema-0')"), 'copia pre-migración guardada')
    check([g['id'] for g in cfg['gastos']] == ['g1', 'g2'], 'gastos conservados')
    check(cfg['gastos'][1].get('categoria') == 'hogar', 'categoría completada por migración (Expensas → hogar)')
    check(cur['mesLabel'] == 'Octubre 2026', 'mes actual conservado')
    check(cur['gastos']['g1'] == {'real': 61000, 'pagado': True}, 'monto real y pagado conservados')
    check(cur['ingresos']['i1']['cobrado'] is True, 'cobrado conservado')
    check(len(cur['movimientos']) == 1 and cur['movimientos'][0]['monto'] == 35000, 'movimientos conservados')
    check(len(hist) == 1 and hist[0]['ahorro'] == 200000, 'historial conservado')
    check(page.locator('.appbar .dot').count() == 1, 'aviso de novedades al actualizar')
    check('Octubre 2026' in page.inner_text('#mes-label'), 'la app muestra el mes migrado')
    # segunda apertura: no duplica ni rompe
    page.reload(); page.wait_for_selector('.hero')
    check(get('current') == cur, 'reabrir no cambia los datos')
    # abrir novedades apaga el aviso
    page.click('.appbar [data-act=menu]'); page.click('[data-run=novedades]'); page.wait_for_timeout(150)
    page.keyboard.press('Escape'); page.wait_for_timeout(100)
    check(page.locator('.appbar .dot').count() == 0, 'aviso de novedades se apaga al verlas')
    page.reload(); page.wait_for_selector('.hero')
    check(page.locator('.appbar .dot').count() == 0, 'aviso no vuelve tras recargar')
    # restaurar un respaldo v1.0 (sin schemaVersion)
    bk = pathlib.Path(SHOTS / 'respaldo-v10.json'); bk.write_text(json.dumps({'version': 2, **V10}), encoding='utf-8')
    page.set_input_files('#file-import', str(bk)); page.wait_for_timeout(300)
    check(get('config')['gastos'][1].get('categoria') == 'hogar', 'restaurar respaldo viejo lo migra')
    check(not errs, f'migración sin errores {errs}')
    ctx.close()

IDB_READ = """(k) => new Promise(res => { const rq = indexedDB.open('control-mensual');
  rq.onsuccess = () => { const db = rq.result; try { const g = db.transaction('kv').objectStore('kv').get(k);
    g.onsuccess = () => { db.close(); res(g.result ?? null); }; g.onerror = () => { db.close(); res(null); }; }
    catch (e) { db.close(); res(null); } }; rq.onerror = () => res(null); })"""
IDB_WRITE = """([k, v]) => new Promise(res => { const rq = indexedDB.open('control-mensual');
  rq.onsuccess = () => { const db = rq.result; const tx = db.transaction('kv', 'readwrite'); tx.objectStore('kv').put(v, k);
    tx.oncomplete = () => { db.close(); res(true); }; }; })"""

def doble_copia(b):
    print('\n== Doble copia IndexedDB + localStorage (v1.3)')
    # 1) Datos de la v1.2 (solo localStorage, esquema 1) pasan a IndexedDB sin pérdida
    V12 = json.loads(json.dumps(V10)); V12['meta'] = {'schemaVersion': 1, 'appVersion': '1.2', 'vistoNovedades': ['1.2']}
    V12['config']['gastos'][1]['categoria'] = 'hogar'
    ctx, page, errs = new_page(b, 390, 844, seed=V12)
    idb_cur = page.evaluate(IDB_READ, 'current')
    check(idb_cur and json.loads(idb_cur)['movimientos'][0]['monto'] == 35000, 'datos v1.2 copiados a IndexedDB')
    check(json.loads(page.evaluate(IDB_READ, 'history'))[0]['ahorro'] == 200000, 'historial copiado a IndexedDB')
    check(page.evaluate(IDB_READ, 'rev') == page.evaluate(f"localStorage.getItem('{P}rev')"), 'marca rev igual en las dos copias')
    page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet')
    check('Doble copia activa' in page.inner_text('.store-status'), 'menú muestra doble copia activa')
    page.screenshot(path=str(SHOTS / 'menu-doble-copia.png'))
    page.keyboard.press('Escape'); page.wait_for_timeout(100)
    # 2) Un cambio se escribe en las dos
    page.click('.nav [data-tab=movimientos]')
    page.fill('#mov-form [name=desc]', 'Verdulería'); page.fill('#mov-form [name=monto]', '4.321'); page.fill('#mov-form [name=fecha]', '2026-10-15')
    page.click('#mov-form button'); page.wait_for_timeout(200)
    check(any(m['monto'] == 4321 for m in json.loads(page.evaluate(IDB_READ, 'current'))['movimientos']), 'movimiento nuevo también en IndexedDB')
    # 3) Se borra localStorage: al reabrir se recupera todo desde IndexedDB
    page.evaluate('localStorage.clear()'); page.reload(); page.wait_for_selector('.hero'); page.wait_for_timeout(200)
    cur = page.evaluate(f"JSON.parse(localStorage.getItem('{P}current'))")
    check(cur and len(cur['movimientos']) == 2 and cur['mesLabel'] == 'Octubre 2026', 'recuperación desde IndexedDB tras borrar localStorage')
    check('Recuperamos' in page.inner_text('#toast'), 'aviso de recuperación')
    check(page.evaluate(f"JSON.parse(localStorage.getItem('{P}history'))")[0]['ahorro'] == 200000, 'historial recuperado')
    # 4) Si IndexedDB tiene una versión más nueva (p. ej. localStorage lleno), gana IndexedDB
    newer = json.loads(page.evaluate(IDB_READ, 'current')); newer['mesLabel'] = 'Noviembre 2026'
    page.evaluate(IDB_WRITE, ['current', json.dumps(newer)])
    page.evaluate(IDB_WRITE, ['rev', str(10**13)])
    page.reload(); page.wait_for_selector('.hero'); page.wait_for_timeout(200)
    check('Noviembre 2026' in page.inner_text('#mes-label'), 'gana la copia más nueva (IndexedDB)')
    # 5) Empate o localStorage más nuevo: gana localStorage
    page.evaluate(f"""() => {{ const c = JSON.parse(localStorage.getItem('{P}current')); c.mesLabel = 'Diciembre 2026';
        localStorage.setItem('{P}current', JSON.stringify(c)); localStorage.setItem('{P}rev', String(2*10**13)); }}""")
    page.reload(); page.wait_for_selector('.hero'); page.wait_for_timeout(200)
    check('Diciembre 2026' in page.inner_text('#mes-label'), 'gana la copia más nueva (localStorage)')
    check(json.loads(page.evaluate(IDB_READ, 'current'))['mesLabel'] == 'Diciembre 2026', 'IndexedDB se resincroniza')
    check(not errs, f'doble copia sin errores {errs}')
    ctx.close()
    # 6) Navegador sin IndexedDB: sigue andando solo con localStorage
    ctx = b.new_context(viewport={'width': 390, 'height': 844})
    ctx.route(lambda u: not u.startswith('file:'), lambda r: r.fulfill(status=200, body='', content_type='text/css'))
    ctx.add_init_script("Object.defineProperty(window, 'indexedDB', {get(){ return undefined; }})")
    page = ctx.new_page(); errs = []
    page.on('pageerror', lambda e: errs.append(str(e)))
    page.on('console', lambda m: errs.append(m.text) if m.type == 'error' else None)
    page.goto(URL); page.wait_for_selector('.hero')
    page.click('.nav [data-tab=fijos]'); page.locator('[data-act=toggle-gasto]').first.click(); page.wait_for_timeout(100)
    page.reload(); page.wait_for_selector('.hero'); page.click('.nav [data-tab=fijos]')
    check(page.locator('.row.is-done').count() >= 1, 'sin IndexedDB: guarda y recarga con localStorage')
    page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet')
    check('Copia única' in page.inner_text('.store-status'), 'sin IndexedDB: el menú lo indica')
    check(not errs, f'sin IndexedDB: sin errores {errs}')
    ctx.close()

def aviso_respaldo(b):
    print('\n== Aviso de respaldo (v1.4)')
    DIA = 864e5
    for w, h in [(390, 844), (1280, 900)]:
        for theme in ['light', 'dark']:
            label = f'{w} {theme}'
            ctx, page, errs = new_page(b, w, h, theme=theme, seed=V10)
            check(page.locator('#aviso-respaldo').count() == 1, f'{label}: aviso visible con datos y sin respaldo')
            check('Todavía no' in page.inner_text('#aviso-respaldo'), f'{label}: texto «todavía no descargaste»')
            no_hscroll(page, w, f'{label} con aviso')
            page.screenshot(path=str(SHOTS / f'aviso-respaldo-{w}-{theme}.png'))
            cur = page.evaluate(f"JSON.parse(localStorage.getItem('{P}current'))")
            check(cur['gastos']['g1'] == {'real': 61000, 'pagado': True}, f'{label}: datos conservados')
            if w == 390 and theme == 'light':
                with page.expect_download() as d:
                    page.click('[data-act=respaldo-ya]')
                check(d.value.suggested_filename.startswith('control-mensual-respaldo-'), 'descarga el respaldo desde el aviso')
                page.wait_for_timeout(200)
                check(page.locator('#aviso-respaldo').count() == 0, 'el aviso desaparece tras descargar')
                meta = page.evaluate(f"JSON.parse(localStorage.getItem('{P}meta'))")
                ult = meta['respaldo']['ultimo']
                check(isinstance(ult, (int, float)) and ult > 0, 'fecha del último respaldo guardada')
                page.reload(); page.wait_for_selector('.hero')
                check(page.locator('#aviso-respaldo').count() == 0, 'no vuelve al recargar')
                page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet')
                check('Último: hoy' in page.inner_text('[data-run=backup]'), 'menú muestra «Último: hoy»')
                page.keyboard.press('Escape')
                # simular último respaldo hace 9 días (en las dos copias)
                page.evaluate(SET_META_ULTIMO, [P, 9 * DIA])
                page.reload(); page.wait_for_selector('.hero')
                txt = page.inner_text('#aviso-respaldo') if page.locator('#aviso-respaldo').count() else ''
                check('Hace 9 días' in txt, f'a los 9 días vuelve: «Hace 9 días…» ({txt[:40]!r})')
                page.click('[data-act=respaldo-luego]'); page.wait_for_timeout(200)
                check(page.locator('#aviso-respaldo').count() == 0, '«Más tarde» oculta el aviso')
                meta = page.evaluate(f"JSON.parse(localStorage.getItem('{P}meta'))")
                pos = meta['respaldo'].get('pospuesto') or 0
                now = page.evaluate('Date.now()')
                check(2.9 * DIA < pos - now <= 3 * DIA + 1000, 'pospuesto 3 días')
                page.reload(); page.wait_for_selector('.hero')
                check(page.locator('#aviso-respaldo').count() == 0, 'sigue pospuesto al recargar')
            check(not errs, f'{label}: sin errores {errs}')
            ctx.close()

SET_META_ULTIMO = """([P, hace]) => new Promise(res => {
  const m = JSON.parse(localStorage.getItem(P + 'meta')); m.respaldo.ultimo = Date.now() - hace; const t = JSON.stringify(m);
  localStorage.setItem(P + 'meta', t);
  const rq = indexedDB.open('control-mensual');
  rq.onsuccess = () => { const db = rq.result; const tx = db.transaction('kv', 'readwrite'); tx.objectStore('kv').put(t, 'meta');
    tx.oncomplete = () => { db.close(); res(1); }; }; })"""

def respaldo_texto(b):
    print('\n== Respaldo como texto (v1.5)')
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    for w, h in [(390, 844), (1280, 900)]:
        for theme in ['light', 'dark']:
            label = f'{w} {theme}'
            ctx, page, errs = new_page(b, w, h, theme=theme, seed=V10)
            ctx.grant_permissions(['clipboard-read', 'clipboard-write'])
            check(page.locator('[data-act=respaldo-copiar]').count() == 1, f'{label}: el aviso ofrece copiar como texto')
            page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet')
            check(page.locator('[data-run=copiar]').count() == 1 and page.locator('[data-run=pegar]').count() == 1, f'{label}: menú con Copiar y Pegar respaldo')
            page.screenshot(path=str(SHOTS / f'menu-texto-{w}-{theme}.png'))
            page.click('[data-run=copiar]'); page.wait_for_selector('.sheet textarea')
            no_hscroll(page, w, f'{label} hoja copiar')
            page.screenshot(path=str(SHOTS / f'copiar-{w}-{theme}.png'))
            page.click('.sheet button[type=submit]'); page.wait_for_timeout(300)
            clip = page.evaluate('navigator.clipboard.readText()')
            d = json.loads(clip)
            check(d['current']['gastos']['g1'] == {'real': 61000, 'pagado': True} and d['schemaVersion'] >= 1, f'{label}: portapapeles con el respaldo completo')
            check(page.locator('.sheet').count() == 0 and 'copiado' in page.inner_text('#toast'), f'{label}: hoja se cierra y avisa')
            meta = get(page, 'meta')
            check((meta['respaldo'].get('ultimo') or 0) > 0 and page.locator('#aviso-respaldo').count() == 0, f'{label}: copiar cuenta como respaldo y apaga el aviso')
            # pegar texto inválido: mensaje en línea y datos intactos
            antes = get(page, 'current')
            page.click('.appbar [data-act=menu]'); page.click('[data-run=pegar]'); page.wait_for_selector('.sheet textarea')
            page.fill('.sheet textarea', clip[:len(clip)//2]); page.click('.sheet button[type=submit]'); page.wait_for_timeout(200)
            check(page.locator('.sheet .form-err').count() == 1 and 'incompleto' in page.inner_text('.sheet .form-err'), f'{label}: texto cortado → «incompleto»')
            page.fill('.sheet textarea', 'hola, esto no es nada'); page.click('.sheet button[type=submit]'); page.wait_for_timeout(200)
            check('no parece un respaldo' in page.inner_text('.sheet .form-err'), f'{label}: texto ajeno → mensaje claro')
            page.fill('.sheet textarea', '{"config":{},"current":{},"schemaVersion":99}'); page.click('.sheet button[type=submit]'); page.wait_for_timeout(200)
            check('más nueva' in page.inner_text('.sheet .form-err'), f'{label}: esquema futuro rechazado')
            check(get(page, 'current') == antes, f'{label}: errores no tocan los datos')
            no_hscroll(page, w, f'{label} hoja pegar con error')
            page.screenshot(path=str(SHOTS / f'pegar-error-{w}-{theme}.png'))
            if w == 390 and theme == 'light':
                # «Pegar» desde el portapapeles llena el recuadro
                page.evaluate('navigator.clipboard.writeText("x")'); page.fill('.sheet textarea', '')
                page.evaluate(f'navigator.clipboard.writeText({json.dumps(clip)})')
                page.click('.sheet .actions button[type=button]'); page.wait_for_timeout(200)
                check(page.input_value('.sheet textarea') == clip, 'botón Pegar trae el portapapeles')
                page.keyboard.press('Escape'); page.wait_for_timeout(100)
                # cambiar datos y restaurar desde el texto (con texto alrededor, como en un mail)
                page.click('.nav [data-tab=movimientos]')
                page.fill('#mov-form [name=desc]', 'Kiosco'); page.fill('#mov-form [name=monto]', '999'); page.fill('#mov-form [name=fecha]', '2026-10-15')
                page.click('#mov-form button'); page.wait_for_timeout(200)
                check(len(get(page, 'current')['movimientos']) == 2, 'cambio local antes de restaurar')
                page.click('.appbar [data-act=menu]'); page.click('[data-run=pegar]'); page.wait_for_selector('.sheet textarea')
                page.fill('.sheet textarea', 'Respaldo del martes:\n' + clip + '\n-- enviado desde mi celular')
                page.click('.sheet button[type=submit]'); page.wait_for_timeout(300)
                cur = get(page, 'current')
                check(len(cur['movimientos']) == 1 and cur['mesLabel'] == 'Octubre 2026', 'pegar restaura los datos copiados')
                pre = json.loads(page.evaluate(f"localStorage.getItem('{P}pre-restauracion')") or '{}')
                check(len(pre.get('current', {}).get('movimientos', [])) == 2, 'copia interna pre-restauración con lo anterior')
                check(json.loads(page.evaluate(IDB_READ, 'current'))['movimientos'] == cur['movimientos'], 'restauración escrita también en IndexedDB')
                # pegar un respaldo v1.0 (sin esquema) lo migra
                page.click('.appbar [data-act=menu]'); page.click('[data-run=pegar]'); page.wait_for_selector('.sheet textarea')
                page.fill('.sheet textarea', json.dumps({'version': 2, **V10})); page.click('.sheet button[type=submit]'); page.wait_for_timeout(300)
                check(get(page, 'config')['gastos'][1].get('categoria') == 'hogar', 'pegar respaldo v1.0 lo migra')
                page.reload(); page.wait_for_selector('.hero')
                check(get(page, 'history')[0]['ahorro'] == 200000, 'datos restaurados persisten al recargar')
            else:
                page.keyboard.press('Escape')
            check(not errs, f'{label}: sin errores {errs}')
            ctx.close()
    # sin acceso al portapapeles: muestra cómo copiar a mano
    ctx, page, errs = new_page(b, 390, 844, seed=V10)
    page.evaluate("Object.defineProperty(navigator, 'clipboard', {get(){ return undefined; }}); document.execCommand = () => false;")
    page.click('.appbar [data-act=menu]'); page.click('[data-run=copiar]'); page.wait_for_selector('.sheet textarea')
    page.click('.sheet button[type=submit]'); page.wait_for_timeout(200)
    check(page.locator('.sheet .form-err').count() == 1 and 'Seleccionar todo' in page.inner_text('.sheet .form-err'), 'sin portapapeles: indica copiar a mano y no cierra')
    check(not (get(page, 'meta')['respaldo'].get('ultimo')), 'sin copiar no se anota respaldo')
    page.screenshot(path=str(SHOTS / 'copiar-sin-portapapeles.png'))
    check(not errs, f'sin portapapeles: sin errores {errs}')
    ctx.close()

def deshacer(b):
    print('\n== Deshacer al eliminar (v1.6)')
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark')]:
        label = f'{w} {theme}'
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=V10)
        cur0, cfg0, hist0 = get(page, 'current'), get(page, 'config'), get(page, 'history')
        # movimiento
        page.click('.nav [data-tab=movimientos]'); page.wait_for_timeout(150)
        page.click('[data-act=del-mov][data-id=m1]'); page.wait_for_timeout(200)
        check(get(page, 'current')['movimientos'] == [], f'{label}: movimiento eliminado')
        check(page.locator('#toast.show #toast-undo').count() == 1, f'{label}: aviso con «Deshacer»')
        no_hscroll(page, w, label + ' con aviso')
        page.screenshot(path=str(SHOTS / f'deshacer-{w}-{theme}.png'))
        page.click('#toast-undo'); page.wait_for_timeout(250)
        check(get(page, 'current')['movimientos'] == cur0['movimientos'], f'{label}: movimiento recuperado igual')
        check(page.locator('.row-title', has_text='Súper').count() == 1, f'{label}: movimiento visible otra vez')
        check('recuperado' in page.inner_text('#toast') and page.locator('#toast-undo').count() == 0, f'{label}: confirma sin otro «Deshacer»')
        check(json.loads(page.evaluate(IDB_READ, 'current'))['movimientos'] == cur0['movimientos'], f'{label}: recuperado también en IndexedDB')
        # gasto fijo (el primero, pagado y con monto real)
        page.click('.nav [data-tab=fijos]'); page.wait_for_timeout(150)
        page.click('.row-main[data-act=edit-gasto][data-id=g1]'); page.wait_for_selector('.sheet')
        page.click('.sheet .btn.danger'); page.wait_for_timeout(250)
        check([g['id'] for g in get(page, 'config')['gastos']] == ['g2'] and 'g1' not in get(page, 'current')['gastos'], f'{label}: gasto eliminado')
        page.click('#toast-undo'); page.wait_for_timeout(250)
        check(get(page, 'config')['gastos'] == cfg0['gastos'], f'{label}: gasto recuperado en su lugar')
        check(get(page, 'current')['gastos']['g1'] == cur0['gastos']['g1'], f'{label}: gasto conserva pagado y monto real')
        # ingreso (está en el Resumen)
        page.click('.nav [data-tab=resumen]'); page.wait_for_timeout(150)
        page.click('.row-main[data-act=edit-ingreso][data-id=i1]'); page.wait_for_selector('.sheet')
        page.click('.sheet .btn.danger'); page.wait_for_timeout(250)
        check(get(page, 'config')['ingresos'] == [], f'{label}: ingreso eliminado')
        page.click('#toast-undo'); page.wait_for_timeout(250)
        check(get(page, 'config')['ingresos'] == cfg0['ingresos'] and get(page, 'current')['ingresos'] == cur0['ingresos'], f'{label}: ingreso recuperado con cobrado')
        # mes del historial
        page.click('.nav [data-tab=historial]'); page.wait_for_timeout(150)
        page.click('[data-act=hist-toggle][data-i="0"]'); page.click('[data-act=hist-del][data-i="0"]'); page.wait_for_selector('.sheet')
        check('Deshacer' in page.inner_text('.sheet'), f'{label}: la hoja ya no dice «No se puede deshacer»')
        page.click('.sheet .btn.danger'); page.wait_for_timeout(250)
        check(get(page, 'history') == [], f'{label}: mes eliminado')
        page.click('#toast-undo'); page.wait_for_timeout(250)
        check(get(page, 'history') == hist0, f'{label}: mes recuperado')
        page.reload(); page.wait_for_selector('.hero')
        check(get(page, 'current') == cur0 and get(page, 'config') == cfg0 and get(page, 'history') == hist0, f'{label}: tras recargar, todo igual que al principio')
        # vence: pasado el tiempo el borrado queda firme
        page.click('.nav [data-tab=movimientos]'); page.wait_for_timeout(150)
        page.click('[data-act=del-mov][data-id=m1]'); page.wait_for_timeout(6500)
        check(page.locator('#toast.show').count() == 0 and get(page, 'current')['movimientos'] == [], f'{label}: a los 6 s el aviso se va y el borrado queda')
        check(page.evaluate("getComputedStyle(document.getElementById('toast')).pointerEvents") == 'none', f'{label}: aviso oculto no tapa toques')
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()

def validacion(b):
    print('\n== Validación en línea (v1.7)')
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    casos = {'12.500': 12500, '12.500,50': 12500.5, '1500.50': 1500.5, '1.250.000': 1250000, '$ 3.000': 3000,
             '1,5': 1.5, '': '', ',50': 0.5, '1,250,000': 1250000, '7.': 7}
    errores = ['-500', 'abc', '12,500', '1,234', '12.50.0', '1.2345', '5-3', '99999999999', '1,5,0', '12,345.6']
    ctx, page, errs = new_page(b, 390, 844, seed={})
    for t, v in casos.items():
        r = page.evaluate('t => leerMonto(t)', t)
        check(r.get('n') == v and 'error' not in r, f'leerMonto({t!r}) = {v!r} (dio {r})')
    for t in errores:
        r = page.evaluate('t => leerMonto(t)', t)
        check('error' in r, f'leerMonto({t!r}) da error ({r.get("error")})')
    check(page.evaluate("parseMonto('-500')") == '', 'parseMonto ignora negativos')
    ctx.close()
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark')]:
        label = f'{w} {theme}'
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=V10)
        cfg0, cur0 = get(page, 'config'), get(page, 'current')
        # Gasto fijo nuevo con todo mal
        page.click('.nav [data-tab=fijos]'); page.wait_for_timeout(150)
        page.click('[data-act=add-gasto]'); page.wait_for_selector('.sheet')
        page.fill('.sheet [name=vence]', '40'); page.fill('.sheet [name=estimado]', '-500'); page.fill('.sheet [name=real]', 'abc')
        page.click('.sheet button[type=submit]'); page.wait_for_timeout(200)
        check(page.locator('.sheet').count() == 1, f'{label}: con errores la hoja queda abierta')
        for n in ['nombre', 'vence', 'estimado', 'real']:
            check(page.locator(f'.sheet [name={n}][aria-invalid=true]').count() == 1, f'{label}: error marcado en {n}')
        check(page.locator('.sheet .f-msg:not(.warn)').count() == 4, f'{label}: 4 mensajes en línea')
        check('negativo' in page.inner_text('.sheet'), f'{label}: dice que no puede ser negativo')
        check(get(page, 'config') == cfg0, f'{label}: nada guardado con errores')
        no_hscroll(page, w, label + ' hoja con errores')
        page.screenshot(path=str(SHOTS / f'validacion-gasto-{w}-{theme}.png'))
        page.fill('.sheet [name=nombre]', 'Internet'); page.wait_for_timeout(50)
        check(page.locator('.sheet [name=nombre][aria-invalid]').count() == 0 and page.locator('.sheet .f-msg').count() == 3, f'{label}: al escribir se limpia el error del campo')
        page.fill('.sheet [name=vence]', '15'); page.fill('.sheet [name=estimado]', '20.000'); page.fill('.sheet [name=real]', '250000')
        page.click('.sheet button[type=submit]'); page.wait_for_timeout(200)
        check(page.locator('.sheet .f-msg.warn').count() == 1 and page.locator('.sheet button[type=submit]').inner_text() == 'Agregar igual', f'{label}: aviso de 10 veces el estimado con «Agregar igual»')
        check(len(get(page, 'config')['gastos']) == 2, f'{label}: el aviso no guarda todavía')
        page.screenshot(path=str(SHOTS / f'validacion-aviso-{w}-{theme}.png'))
        page.click('.sheet button[type=submit]'); page.wait_for_timeout(250)
        cfg = get(page, 'config'); g = cfg['gastos'][-1]
        check(page.locator('.sheet').count() == 0 and g['nombre'] == 'Internet' and g['vence'] == 15 and g['estimado'] == 20000, f'{label}: «Guardar igual» guarda el gasto')
        check(get(page, 'current')['gastos'][g['id']]['real'] == 250000, f'{label}: monto real guardado')
        # Editar: cambiar el monto quita el aviso y vuelve el botón
        page.click(f'.row-main[data-act=edit-gasto][data-id="{g["id"]}"]'); page.wait_for_selector('.sheet')
        page.click('.sheet button[type=submit]'); page.wait_for_timeout(150)
        check(page.locator('.sheet .f-msg.warn').count() == 1, f'{label}: aviso al editar')
        page.fill('.sheet [name=real]', '21.000'); page.wait_for_timeout(50)
        check(page.locator('.sheet .f-msg').count() == 0 and page.locator('.sheet button[type=submit]').inner_text() == 'Guardar', f'{label}: al corregir se va el aviso')
        page.click('.sheet button[type=submit]'); page.wait_for_timeout(200)
        check(page.locator('.sheet').count() == 0 and get(page, 'current')['gastos'][g['id']]['real'] == 21000, f'{label}: guarda directo sin aviso')
        # Ingreso sin nombre
        page.click('.nav [data-tab=resumen]'); page.wait_for_timeout(150)
        page.click('.row-main[data-act=edit-ingreso][data-id=i1]'); page.wait_for_selector('.sheet')
        page.fill('.sheet [name=nombre]', ''); page.fill('.sheet [name=estimado]', '1.2345')
        page.click('.sheet button[type=submit]'); page.wait_for_timeout(150)
        check(page.locator('.sheet [aria-invalid=true]').count() == 2, f'{label}: ingreso sin nombre y monto mal escrito')
        check(get(page, 'config')['ingresos'] == cfg0['ingresos'], f'{label}: ingreso sin cambios')
        page.keyboard.press('Escape'); page.wait_for_timeout(100)
        # Movimientos
        page.click('.nav [data-tab=movimientos]'); page.wait_for_timeout(150)
        page.click('#mov-form button'); page.wait_for_timeout(150)
        check(page.locator('#mov-form [aria-invalid=true]').count() == 2, f'{label}: movimiento vacío marca descripción y monto')
        page.fill('#mov-form [name=desc]', 'Kiosco'); page.fill('#mov-form [name=monto]', '0')
        page.click('#mov-form button'); page.wait_for_timeout(150)
        check('mayor a' in page.inner_text('#mov-form'), f'{label}: monto 0 no se acepta')
        page.fill('#mov-form [name=monto]', '12,500'); page.click('#mov-form button'); page.wait_for_timeout(150)
        check('12.500' in page.inner_text('#mov-form'), f'{label}: sugiere 12.500 para «12,500»')
        no_hscroll(page, w, label + ' movimiento con error')
        page.screenshot(path=str(SHOTS / f'validacion-mov-{w}-{theme}.png'))
        check(len(get(page, 'current')['movimientos']) == 1, f'{label}: nada registrado con errores')
        # Fecha de otro mes (los datos son de Octubre 2026) + monto mayor a los ingresos
        page.fill('#mov-form [name=monto]', '2000000'); page.fill('#mov-form [name=fecha]', '2026-11-03')
        page.click('#mov-form button'); page.wait_for_timeout(150)
        check(page.locator('#mov-form .f-msg.warn').count() == 2 and page.inner_text('#mov-form button') == 'Agregar igual', f'{label}: avisos de fecha de otro mes y monto mayor a ingresos')
        page.screenshot(path=str(SHOTS / f'validacion-mov-aviso-{w}-{theme}.png'))
        page.click('#mov-form button'); page.wait_for_timeout(200)
        movs = get(page, 'current')['movimientos']
        check(len(movs) == 2 and movs[-1]['monto'] == 2000000 and movs[-1]['fecha'] == '2026-11-03', f'{label}: «Agregar igual» registra')
        page.fill('#mov-form [name=desc]', 'Pan'); page.fill('#mov-form [name=monto]', '1500.50'); page.fill('#mov-form [name=fecha]', '2026-10-20')
        page.click('#mov-form button'); page.wait_for_timeout(200)
        check(get(page, 'current')['movimientos'][-1]['monto'] == 1500.5, f'{label}: 1500.50 se registra directo como 1500,5')
        # Nombre del mes vacío
        page.evaluate('sheetRename()'); page.wait_for_selector('.sheet')
        page.fill('.sheet [name=mes]', ''); page.click('.sheet button[type=submit]'); page.wait_for_timeout(150)
        check(page.locator('.sheet [name=mes][aria-invalid=true]').count() == 1 and get(page, 'current')['mesLabel'] == 'Octubre 2026', f'{label}: nombre del mes vacío no se guarda')
        page.keyboard.press('Escape')
        check(json.loads(page.evaluate(IDB_READ, 'current'))['movimientos'] == get(page, 'current')['movimientos'], f'{label}: IndexedDB al día')
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()

AUDIT_JS = r"""() => {
  const cv=document.createElement('canvas'); cv.width=cv.height=1; const cx=cv.getContext('2d',{willReadFrequently:true});
  const rgba=s=>{ cx.clearRect(0,0,1,1); cx.fillStyle='#000'; cx.fillStyle=s; cx.fillRect(0,0,1,1); const d=cx.getImageData(0,0,1,1).data; return [d[0],d[1],d[2],d[3]/255]; };
  const over=(t,b)=>{ const a=t[3]; return [t[0]*a+b[0]*(1-a),t[1]*a+b[1]*(1-a),t[2]*a+b[2]*(1-a),1]; };
  const lum=c=>{ const f=v=>{v/=255;return v<=.03928?v/12.92:Math.pow((v+.055)/1.055,2.4)}; return .2126*f(c[0])+.7152*f(c[1])+.0722*f(c[2]); };
  const ratio=(a,b)=>{ const x=lum(a),y=lum(b); return (Math.max(x,y)+.05)/(Math.min(x,y)+.05); };
  const bgOf=el=>{ const layers=[]; let e=el;
    while(e && e.nodeType===1){ const cs=getComputedStyle(e);
      if(cs.backgroundImage && cs.backgroundImage!=='none' && /gradient/.test(cs.backgroundImage)){ // hero: usar el color más claro del degradado
        const cols=cs.backgroundImage.match(/(rgba?\([^)]*\)|color\([^)]*\)|#[0-9a-f]{3,8})/gi)||[]; let best=null;
        cols.forEach(c=>{ const v=rgba(c); if(!best||lum(v)>lum(best)) best=v; }); if(best){ layers.push([...best.slice(0,3),1]); break; } }
      const c=rgba(cs.backgroundColor); if(c[3]>0){ layers.push(c); if(c[3]>=1) break; }
      e=e.parentElement; }
    let base=[255,255,255,1]; if(!layers.length || layers[layers.length-1][3]<1){ base=rgba(getComputedStyle(document.body).backgroundColor); }
    for(let i=layers.length-1;i>=0;i--) base=over(layers[i],base); return base; };
  const out=[];
  const walker=document.createTreeWalker(document.body,NodeFilter.SHOW_TEXT);
  const seen=new Set();
  while(walker.nextNode()){ const n=walker.currentNode; if(!n.textContent.trim()) continue; const el=n.parentElement; if(seen.has(el)) continue; seen.add(el);
    if(el.closest('svg')||el.closest('[aria-hidden=true]')) continue;
    const r=el.getBoundingClientRect(); if(!r.width||!r.height) continue;
    const cs=getComputedStyle(el); if(cs.visibility==='hidden') continue;
    let op=1; for(let e=el;e&&e.nodeType===1;e=e.parentElement) op*=Number(getComputedStyle(e).opacity);
    if(op<0.05) continue;
    const bg=bgOf(el); let fg=rgba(cs.color); fg=over([fg[0],fg[1],fg[2],fg[3]*op],bg);
    const size=parseFloat(cs.fontSize), bold=Number(cs.fontWeight)>=700;
    const large= size>=24 || (bold && size>=18.66);
    const need= large?3:4.5; const rr=ratio(fg,bg);
    if(rr<need) out.push({t:n.textContent.trim().slice(0,30), cls:el.className, r:Math.round(rr*100)/100, need});
  }
  return out;
}"""

A11Y_SEED = {
    'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 1000000, 'nota': ''}],
               'gastos': [{'id': 'g1', 'nombre': 'Luz', 'estimado': 50000, 'categoria': 'servicios', 'vence': 1, 'nota': 'n'},
                          {'id': 'g2', 'nombre': 'Nafta', 'estimado': 20000, 'categoria': 'transporte', 'vence': 21, 'nota': ''},
                          {'id': 'g3', 'nombre': 'Super', 'estimado': 20000, 'categoria': 'comida', 'vence': 5, 'nota': ''}]},
    'current': {'mesLabel': 'Noviembre 2026', 'gastos': {'g1': {'real': 61000, 'pagado': True}, 'g2': {'real': '', 'pagado': False}, 'g3': {'real': '', 'pagado': False}},
                'ingresos': {'i1': {'real': '', 'cobrado': True}},
                'movimientos': [{'id': 'm1', 'desc': 'Kiosco', 'monto': 3500, 'categoria': 'ocio', 'fecha': '2026-11-05', 'ts': 1}]},
    'history': [{'mesLabel': 'Octubre 2026', 'ingresos': 900000, 'gastos': 700000, 'ahorro': 200000, 'guardado': '2026-10-01',
                 'detalle': {'porCat': {'servicios': 300000, 'comida': 400000}}}],
}

def foco(page):
    return page.evaluate("""() => { const a=document.activeElement; if(!a||a===document.body) return null;
        return {act:a.dataset?.act||null, id:a.dataset?.id||null, tag:a.tagName, inSheet:!!a.closest('.sheet'),
                outline:getComputedStyle(a).outlineStyle, ow:parseFloat(getComputedStyle(a).outlineWidth)} }""")

def tab_hasta(page, cond, maxn=60):
    for _ in range(maxn):
        page.keyboard.press('Tab'); f = foco(page)
        if f and cond(f): return f
    return None

def accesibilidad(b):
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark'), (390, 844, 'dark'), (1280, 900, 'light')]:
        label = f'a11y {w} {theme}'
        print(f'\n== Accesibilidad (v1.8) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=A11Y_SEED)
        malos = set()
        for tab in ['resumen', 'fijos', 'movimientos', 'historial']:
            page.click(f'.nav [data-tab={tab}]'); page.wait_for_timeout(120)
            if tab == 'historial': page.click('.h-head'); page.wait_for_timeout(120)
            for o in page.evaluate(AUDIT_JS): malos.add(f"{o['t']} ({o['r']}<{o['need']})")
            sin_nombre = page.evaluate("""() => [...document.querySelectorAll('button,[role=button]')].filter(e=>e.offsetParent!==null)
                .filter(e=>!(e.getAttribute('aria-label')||e.textContent).trim()).map(e=>e.outerHTML.slice(0,60))""")
            check(not sin_nombre, f'{label} {tab}: todos los botones tienen nombre {sin_nombre}')
            sin_label = page.evaluate("""() => [...document.querySelectorAll('.inp')].filter(e=>!e.labels?.length && !e.getAttribute('aria-label')).map(e=>e.name)""")
            check(not sin_label, f'{label} {tab}: todos los campos tienen etiqueta {sin_label}')
        page.click('.appbar [data-act=menu]'); page.wait_for_timeout(250)
        for o in page.evaluate(AUDIT_JS): malos.add(f"{o['t']} ({o['r']}<{o['need']})")
        page.keyboard.press('Escape'); page.wait_for_timeout(100)
        check(not malos, f'{label}: contraste AA en todos los textos {sorted(malos)}')
        check(page.locator('.sheet').count() == 0, f'{label}: Escape cierra el menú')
        check((foco(page) or {}).get('act') == 'menu', f'{label}: el foco vuelve al botón de menú')

        # Teclado en Resumen: Tab hasta la fila de «Nafta», Enter abre la hoja de edición
        page.click('.nav [data-tab=resumen]'); page.wait_for_timeout(120)
        page.evaluate("document.activeElement.blur()")
        f = tab_hasta(page, lambda f: f['act'] == 'edit-gasto' and f['id'] == 'g2')
        check(f is not None, f'{label}: Tab llega a la fila de un gasto')
        check(f and f['outline'] != 'none' and f['ow'] >= 2, f'{label}: el foco se ve (contorno {f and f["outline"]})')
        page.screenshot(path=str(SHOTS / f'a11y-foco-{w}-{theme}.png'))
        page.keyboard.press('Enter'); page.wait_for_timeout(200)
        dlg = page.locator('.sheet[role=dialog][aria-modal=true]')
        check(dlg.count() == 1 and dlg.get_attribute('aria-labelledby') == 'sheet-title', f'{label}: Enter abre la hoja como diálogo con título')
        check((foco(page) or {}).get('inSheet'), f'{label}: el foco entra en la hoja')
        check(page.evaluate("document.getElementById('app').inert && document.querySelector('.appbar').inert"), f'{label}: el fondo queda inerte')
        dentro = True
        for _ in range(14):
            page.keyboard.press('Tab'); dentro = dentro and bool((foco(page) or {}).get('inSheet'))
        for _ in range(3):
            page.keyboard.press('Shift+Tab'); dentro = dentro and bool((foco(page) or {}).get('inSheet'))
        check(dentro, f'{label}: Tab y Shift+Tab no se escapan de la hoja')
        page.screenshot(path=str(SHOTS / f'a11y-hoja-{w}-{theme}.png'))
        page.keyboard.press('Escape'); page.wait_for_timeout(120)
        f = foco(page)
        check(page.locator('.sheet').count() == 0 and f and f['act'] == 'edit-gasto' and f['id'] == 'g2', f'{label}: Escape cierra y el foco vuelve a la fila {f}')
        check(not page.evaluate("document.getElementById('app').inert"), f'{label}: el fondo vuelve a estar activo')

        # Espacio en el check: tilda y el foco queda en el mismo gasto
        page.keyboard.press('Shift+Tab'); f = foco(page)
        check(f and f['act'] == 'toggle-gasto' and f['id'] == 'g2', f'{label}: Shift+Tab va al tilde del gasto')
        page.keyboard.press('Space'); page.wait_for_timeout(200)
        f = foco(page)
        check(get(page, 'current')['gastos']['g2']['pagado'] is True, f'{label}: Espacio tilda el pago')
        check(f and f['act'] == 'toggle-gasto' and f['id'] == 'g2', f'{label}: el foco sigue en el mismo tilde tras redibujar')
        check(page.get_attribute('[data-act=toggle-gasto][data-id=g2]', 'aria-pressed') == 'true', f'{label}: aria-pressed indica pagado')
        page.keyboard.press('Enter'); page.wait_for_timeout(200)
        check(get(page, 'current')['gastos']['g2']['pagado'] is False, f'{label}: Enter lo destilda')

        # Historial: Enter despliega el mes y aria-expanded lo indica
        page.click('.nav [data-tab=historial]'); page.wait_for_timeout(120)
        if page.get_attribute('.h-head', 'aria-expanded') == 'true': page.click('.h-head'); page.wait_for_timeout(120)
        check(page.get_attribute('.h-head', 'aria-expanded') == 'false', f'{label}: el mes arranca plegado')
        page.focus('.h-head'); page.keyboard.press('Enter'); page.wait_for_timeout(120)
        check(page.get_attribute('.h-head', 'aria-expanded') == 'true' and page.locator('.h-detail').count() == 1, f'{label}: Enter despliega el mes')
        check((foco(page) or {}).get('act') == 'hist-toggle', f'{label}: el foco queda en el mes')
        page.keyboard.press(' '); page.wait_for_timeout(120)
        check(page.get_attribute('.h-head', 'aria-expanded') == 'false', f'{label}: Espacio lo pliega')
        check(page.get_attribute('.nav [data-tab=historial]', 'aria-current') == 'page', f'{label}: la pestaña activa se anuncia')

        # Ctrl+Z deshace un borrado mientras se ve el aviso
        page.click('.nav [data-tab=movimientos]'); page.wait_for_timeout(120)
        page.focus('[data-act=del-mov][data-id=m1]'); page.keyboard.press('Enter'); page.wait_for_timeout(200)
        check(len(get(page, 'current')['movimientos']) == 0, f'{label}: se elimina el movimiento con el teclado')
        page.keyboard.press('Control+z'); page.wait_for_timeout(250)
        check([m['id'] for m in get(page, 'current')['movimientos']] == ['m1'], f'{label}: Ctrl+Z lo recupera')
        page.wait_for_timeout(2400)
        check(page.locator('#toast-undo').count() == 0, f'{label}: el «Deshacer» oculto no queda en el recorrido del teclado')

        # Etiquetas: tocar «Monto» enfoca su campo
        page.click('#mov-form label:has-text("Monto")')
        check(page.evaluate("document.activeElement.name") == 'monto', f'{label}: la etiqueta «Monto» enfoca su campo')
        no_hscroll(page, w, label)
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()

def redibujo(b):
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    gs = [{'id': f'g{i}', 'nombre': f'Gasto {i}', 'estimado': 10000 + i, 'categoria': 'servicios', 'vence': (i % 28) + 1, 'nota': ''} for i in range(25)]
    seed = {'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 1000000, 'nota': ''}], 'gastos': gs},
            'current': {'mesLabel': 'Octubre 2026', 'gastos': {x['id']: {'real': '', 'pagado': False} for x in gs},
                        'ingresos': {'i1': {'real': '', 'cobrado': False}},
                        'movimientos': [{'id': f'm{i}', 'desc': f'Compra {i}', 'monto': 1000 * i, 'categoria': 'comida', 'fecha': '2026-10-0' + str(i), 'ts': i} for i in range(1, 5)]},
            'history': []}
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark'), (390, 844, 'dark'), (1280, 900, 'light')]:
        label = f'redibujo {w} {theme}'
        print(f'\n== Redibujo fino (v1.9) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=seed)
        for tab in ['resumen', 'fijos']:
            page.click(f'.nav [data-tab={tab}]'); page.wait_for_timeout(500)
            sel = '[data-act=toggle-gasto][data-id=g12]'
            page.evaluate(f"document.querySelector('{sel}').scrollIntoView({{block:'center'}})"); page.wait_for_timeout(150)
            check(page.evaluate('scrollY') > 200, f'{label} {tab}: la prueba arranca con la página scrolleada')
            antes = page.evaluate(f"""() => {{ const b=document.querySelector('{sel}'); b.closest('.row').__marca=1;
                document.querySelector('.hero .bar i').__marca=1; return [scrollY, b.getBoundingClientRect().top]; }}""")
            page.click(sel); page.wait_for_timeout(250)
            despues = page.evaluate(f"""() => {{ const b=document.querySelector('{sel}');
                return [scrollY, b.getBoundingClientRect().top, !!b.closest('.row').__marca, !!document.querySelector('.hero .bar i').__marca,
                        b.closest('.row').classList.contains('is-done'), document.activeElement===b]; }}""")
            check(get(page, 'current')['gastos']['g12']['pagado'] is True, f'{label} {tab}: se tilda')
            check(despues[0] == antes[0] and abs(despues[1] - antes[1]) < 1, f'{label} {tab}: sin salto de scroll ({antes[:2]} → {despues[:2]})')
            check(despues[2] and despues[3], f'{label} {tab}: la fila y la barra son los mismos nodos')
            check(despues[4] and despues[5], f'{label} {tab}: la fila se ve pagada y el foco sigue en el tilde')
            page.click(sel); page.wait_for_timeout(200)
        page.screenshot(path=str(SHOTS / f'redibujo-{w}-{theme}.png'))
        # Ingresos
        page.click('.nav [data-tab=resumen]'); page.wait_for_timeout(200)
        page.evaluate("document.querySelector('[data-key=i-i1]').__marca=1")
        page.click('[data-act=toggle-ingreso][data-id=i1]'); page.wait_for_timeout(200)
        check(page.evaluate("!!document.querySelector('[data-key=i-i1]').__marca && document.querySelector('[data-key=i-i1]').classList.contains('is-done')"), f'{label}: cobrar un ingreso conserva la fila')
        # Filtro «Pendientes»: tildar quita solo esa fila
        page.click('.nav [data-tab=fijos]'); page.wait_for_timeout(150)
        page.click('[data-act=filtro][data-f=pend]'); page.wait_for_timeout(150)
        page.evaluate("document.querySelector('[data-key=g-g6]').__marca=1")
        n0 = page.locator('#app .row').count()
        page.click('[data-act=toggle-gasto][data-id=g5]'); page.wait_for_timeout(200)
        check(page.locator('#app .row').count() == n0 - 1 and page.locator('[data-key=g-g5]').count() == 0, f'{label}: en «Pendientes» se va solo la fila tildada')
        check(page.evaluate("!!document.querySelector('[data-key=g-g6]').__marca"), f'{label}: las demás filas no se rehacen')
        page.click('[data-act=filtro][data-f=todos]'); page.wait_for_timeout(150)
        # Movimientos: borrar uno conserva los demás; lo escrito sobrevive; agregar vacía el formulario
        page.click('.nav [data-tab=movimientos]'); page.wait_for_timeout(200)
        page.evaluate("document.querySelector('[data-key=m-m1]').__marca=1; document.querySelector('[data-key=m-m4]').__marca=1")
        page.click('[data-act=del-mov][data-id=m2]'); page.wait_for_timeout(200)
        check(page.locator('[data-key=m-m2]').count() == 0 and page.evaluate("!!document.querySelector('[data-key=m-m1]').__marca && !!document.querySelector('[data-key=m-m4]').__marca"),
              f'{label}: borrar un movimiento conserva los nodos de los otros')
        page.fill('#mov-form [name=desc]', 'Farmacia'); page.fill('#mov-form [name=monto]', '4.200')
        page.evaluate("async () => { current.gastos.g1.pagado = true; await saveAll(); render(); }"); page.wait_for_timeout(150)
        check(page.input_value('#mov-form [name=desc]') == 'Farmacia' and page.input_value('#mov-form [name=monto]') == '4.200', f'{label}: lo escrito sobrevive a un redibujo')
        page.fill('#mov-form [name=fecha]', '2026-10-09'); page.click('#mov-form button'); page.wait_for_timeout(250)
        movs = get(page, 'current')['movimientos']
        check(any(m['desc'] == 'Farmacia' and m['monto'] == 4200 for m in movs), f'{label}: el movimiento se registra')
        hoy = page.evaluate('todayISO()')
        check(page.input_value('#mov-form [name=desc]') == '' and page.input_value('#mov-form [name=monto]') == '' and page.input_value('#mov-form [name=fecha]') == hoy,
              f'{label}: al agregar, el formulario se vacía y la fecha vuelve a hoy')
        check(page.evaluate("document.activeElement.name") == 'desc', f'{label}: el foco vuelve a «Descripción»')
        # Pestañas siguen andando
        for tab in ['historial', 'fijos', 'resumen']:
            page.click(f'.nav [data-tab={tab}]'); page.wait_for_timeout(120)
            check(page.get_attribute(f'.nav [data-tab={tab}]', 'aria-current') == 'page', f'{label}: pestaña {tab}')
        check(page.locator('#app .row').count() == 26, f'{label}: Resumen completo tras cambiar de pestañas')
        no_hscroll(page, w, label)
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()

def calendario(b):
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    import datetime
    hoy = datetime.date.today()
    MES = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    import calendar as pycal
    n = pycal.monthrange(hoy.year, hoy.month)[1]
    d_venc = 1 if hoy.day > 1 else None                 # día ya pasado (si hoy no es 1)
    d_fut = min(n, hoy.day + 10) if hoy.day + 10 <= n else None
    gs = [{'id': 'ga', 'nombre': 'Luz de prueba', 'estimado': 40000, 'categoria': 'servicios', 'vence': hoy.day, 'nota': ''},
          {'id': 'gb', 'nombre': 'Gas de prueba', 'estimado': 30000, 'categoria': 'servicios', 'vence': hoy.day, 'nota': ''},
          {'id': 'gc', 'nombre': 'Cuota de prueba', 'estimado': 90000, 'categoria': 'educacion', 'vence': 31, 'nota': ''},
          {'id': 'gd', 'nombre': 'Sin fecha de prueba', 'estimado': 15000, 'categoria': 'hogar', 'vence': '', 'nota': ''}]
    if d_venc: gs.append({'id': 'ge', 'nombre': 'Atrasado de prueba', 'estimado': 20000, 'categoria': 'hogar', 'vence': d_venc, 'nota': ''})
    est = {x['id']: {'real': '', 'pagado': False} for x in gs}; est['gb']['pagado'] = True
    seed = {'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 900000, 'nota': ''}], 'gastos': gs},
            'current': {'mesLabel': f'{MES[hoy.month-1]} {hoy.year}', 'gastos': est, 'ingresos': {'i1': {'real': '', 'cobrado': False}}, 'movimientos': []},
            'history': []}
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark'), (390, 844, 'dark'), (1280, 900, 'light')]:
        label = f'calendario {w} {theme}'
        print(f'\n== Calendario del mes (v2.0) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=seed)
        antes = get(page, 'config')
        page.click('.nav [data-tab=fijos]'); page.wait_for_timeout(150)
        check(page.get_attribute('[data-act=vista][data-f=lista]', 'aria-pressed') == 'true' and page.locator('.cal').count() == 0, f'{label}: la lista es la vista por defecto')
        page.click('[data-act=vista][data-f=cal]'); page.wait_for_timeout(200)
        check(page.locator('.cal-d').count() == n, f'{label}: {n} días en la grilla')
        primero = page.evaluate("[...document.querySelector('.cal').children].findIndex(e=>e.classList.contains('cal-d'))")
        check(primero == datetime.date(hoy.year, hoy.month, 1).weekday(), f'{label}: la semana arranca en lunes (día 1 en columna {primero})')
        dh = f'.cal-d[data-i="{hoy.day}"]'
        check(page.get_attribute(dh, 'aria-pressed') == 'true' and 'hoy' in page.get_attribute(dh, 'class'), f'{label}: hoy está elegido y marcado')
        check(page.locator(f'{dh} .cal-dots i').count() == 2 and page.locator(f'{dh} .cal-dots i.ok').count() == 1 and page.locator(f'{dh} .cal-dots i.hoy').count() == 1,
              f'{label}: hoy tiene un punto pagado y uno «vence hoy»')
        check(page.inner_text(f'{dh} .cal-amt') == '$40k', f'{label}: el día muestra lo que falta pagar')
        check(page.locator('[data-key=g-ga]').count() == 1 and page.locator('[data-key=g-gb]').count() == 1, f'{label}: debajo se ven los gastos de hoy')
        check(page.locator(f'.cal-d[data-i="{n}"] .cal-dots i').count() == 1, f'{label}: el día 31 cae en el último día del mes ({n})')
        if d_venc and d_venc != hoy.day:
            check(page.locator(f'.cal-d[data-i="{d_venc}"] .cal-dots i.vencido').count() == 1 and 'e-vencido' in page.get_attribute(f'.cal-d[data-i="{d_venc}"]', 'class'), f'{label}: lo atrasado se ve vencido')
        lbl = page.get_attribute(dh, 'aria-label')
        check('Luz de prueba vence hoy' in lbl and 'Gas de prueba pagado' in lbl and 'hoy' in lbl, f'{label}: el día tiene nombre para lectores de pantalla ({lbl})')
        check(page.locator('.day-h', has_text='Sin día de vencimiento').count() == 1 and page.locator('[data-key=g-gd]').count() == 1, f'{label}: «Sin día de vencimiento» lista el gasto sin día')
        page.screenshot(path=str(SHOTS / f'calendario-{w}-{theme}.png'), full_page=True)
        # Tildar desde el calendario: mismo nodo, se guarda, el día pasa a pagado
        page.evaluate("document.querySelector('[data-key=g-ga]').__marca=1")
        page.click('[data-act=toggle-gasto][data-id=ga]'); page.wait_for_timeout(200)
        check(get(page, 'current')['gastos']['ga']['pagado'] is True, f'{label}: tildar desde el calendario guarda')
        check(page.evaluate("!!document.querySelector('[data-key=g-ga]').__marca"), f'{label}: la fila es el mismo nodo')
        check(page.inner_text(f'{dh} .cal-amt') == '✓' and page.locator(f'{dh} .cal-dots i.ok').count() == 2, f'{label}: el día queda como pagado')
        # Elegir otro día
        page.click(f'.cal-d[data-i="{n}"]'); page.wait_for_timeout(150)
        check(page.get_attribute(f'.cal-d[data-i="{n}"]', 'aria-pressed') == 'true' and page.locator('[data-key=g-gc]').count() == 1 and page.locator('[data-key=g-ga]').count() == 0,
              f'{label}: tocar el día {n} muestra su gasto')
        vacio = next(d for d in range(1, n + 1) if d not in (hoy.day, n, d_venc))
        page.click(f'.cal-d[data-i="{vacio}"]'); page.wait_for_timeout(150)
        check(page.locator('#app .empty', has_text='Nada vence este día').count() == 1, f'{label}: día sin vencimientos')
        # Teclado: flechas
        page.focus(f'.cal-d[data-i="{vacio}"]')
        page.keyboard.press('ArrowRight' if vacio < n else 'ArrowLeft'); page.wait_for_timeout(120)
        esp = vacio + 1 if vacio < n else vacio - 1
        check(page.evaluate('document.activeElement.dataset.i') == str(esp) and page.get_attribute(f'.cal-d[data-i="{esp}"]', 'aria-pressed') == 'true', f'{label}: la flecha mueve al día siguiente')
        if esp + 7 <= n:
            page.keyboard.press('ArrowDown'); page.wait_for_timeout(120)
            check(page.evaluate('document.activeElement.dataset.i') == str(esp + 7), f'{label}: flecha abajo salta una semana')
        # Editar desde el calendario abre la hoja
        page.click(f'.cal-d[data-i="{hoy.day}"]'); page.wait_for_timeout(120)
        page.click('[data-key=g-ga] .row-main'); page.wait_for_selector('.sheet')
        check(page.locator('.sheet [name=vence]').count() == 1, f'{label}: tocar el gasto abre su hoja')
        page.keyboard.press('Escape'); page.wait_for_timeout(150)
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA en el calendario {[(o["t"], o["r"]) for o in malos]}')
        # Volver a la lista y pestañas
        page.click('[data-act=vista][data-f=lista]'); page.wait_for_timeout(150)
        check(page.locator('.cal').count() == 0 and page.locator('#app .row').count() == len(gs), f'{label}: vuelve a la lista')
        check(get(page, 'config') == antes, f'{label}: la configuración no cambia')
        no_hscroll(page, w, label)
        page.click('[data-act=vista][data-f=cal]'); page.wait_for_timeout(150); no_hscroll(page, w, label + ' (calendario)')
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()

def aviso_vence(b):
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    def datos(mes, gs, pagados=()):
        est = {x['id']: {'real': '', 'pagado': x['id'] in pagados} for x in gs}
        return {'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 900000, 'nota': ''}], 'gastos': gs},
                'current': {'mesLabel': mes, 'gastos': est, 'ingresos': {'i1': {'real': '', 'cobrado': False}}, 'movimientos': []}, 'history': []}
    g = lambda i, n, m, v: {'id': i, 'nombre': n, 'estimado': m, 'categoria': 'servicios', 'vence': v, 'nota': ''}
    gs = [g('gx', 'Lejano de prueba', 10000, 25), g('gc', 'Cuota de prueba', 30000, 17), g('gb', 'Luz de prueba', 20000, 15),
          g('ga', 'Atrasado de prueba', 11000, 10), g('gd', 'Pagado de prueba', 50000, 16), g('gf', 'Sin día de prueba', 9000, '')]
    seed = datos('Noviembre 2026', gs, pagados=('gd',))
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark'), (390, 844, 'dark'), (1280, 900, 'light')]:
        label = f'aviso vence {w} {theme}'
        print(f'\n== Aviso de vencimientos (v2.1) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=seed, fecha='2026-11-15T10:00:00')
        antes = get(page, 'config')
        av = page.locator('#aviso-vence')
        check(av.count() == 1, f'{label}: aparece el aviso en Resumen')
        check(page.evaluate("document.querySelector('#aviso-vence').previousElementSibling.matches('.nav')"), f'{label}: está arriba de todo (debajo de las pestañas)')
        check(av.locator('b').first.inner_text() == 'Atrasado de prueba está vencido', f'{label}: título por lo vencido')
        txt = av.inner_text().replace('\xa0', ' ')
        check('1 vence hoy y 1 vence en los próximos días' in txt and '$ 61.000' in txt, f'{label}: resumen y total ({txt[:120]!r})')
        orden = page.evaluate("[...document.querySelectorAll('#aviso-vence .va-row')].map(e=>e.dataset.key)")
        check(orden == ['va-ga', 'va-gb', 'va-gc'], f'{label}: vencido, hoy y en 2 días, sin pagados, lejanos ni sin día ({orden})')
        tags = page.evaluate("[...document.querySelectorAll('#aviso-vence .va-row .tag')].map(e=>e.textContent)")
        check(tags == ['Vencido · día 10', 'Vence hoy', 'Vence en 2 días'], f'{label}: etiquetas ({tags})')
        check('danger' in av.get_attribute('class'), f'{label}: con algo vencido el aviso es rojo')
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA con el aviso {[(o["t"], o["r"]) for o in malos]}')
        no_hscroll(page, w, label)
        page.screenshot(path=str(SHOTS / f'aviso-vence-{w}-{theme}.png'))
        # Pagar desde el aviso y deshacer
        page.click('[data-act=aviso-pagar][data-id=ga]'); page.wait_for_timeout(200)
        check(get(page, 'current')['gastos']['ga']['pagado'] is True, f'{label}: «Pagado» desde el aviso guarda')
        check(page.locator('[data-key=va-ga]').count() == 0 and av.locator('b').first.inner_text() == 'Hoy vence Luz de prueba', f'{label}: sale del aviso y cambia el título')
        check('danger' not in av.get_attribute('class'), f'{label}: sin vencidos el aviso es ámbar')
        check(page.get_attribute('[data-act=toggle-gasto][data-id=ga]', 'aria-pressed') == 'true', f'{label}: la fila del checklist también queda tildada')
        page.click('#toast-undo'); page.wait_for_timeout(200)
        check(get(page, 'current')['gastos']['ga']['pagado'] is False and page.locator('[data-key=va-ga]').count() == 1, f'{label}: «Deshacer» lo devuelve')
        # Ver en el calendario
        page.click('#aviso-vence [data-act=ver-cal]'); page.wait_for_timeout(200)
        check(page.locator('.nav [data-tab=fijos]').get_attribute('aria-current') == 'page' and page.locator('.cal').count() == 1, f'{label}: «Ver en el calendario» abre el calendario')
        check(page.get_attribute('.cal-d[data-i="15"]', 'aria-pressed') == 'true', f'{label}: con el día de hoy elegido')
        check(get(page, 'config') == antes, f'{label}: la configuración no cambia')
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()
    print('\n== Aviso de vencimientos: otros casos')
    # Otro mes: sin aviso
    ctx, page, errs = new_page(b, 390, 844, seed=datos('Octubre 2026', gs), fecha='2026-11-15T10:00:00')
    check(page.locator('#aviso-vence').count() == 0, 'mes que no es el actual: sin aviso')
    check(not errs, f'sin errores {errs}'); ctx.close()
    # Solo próximos, uno solo
    ctx, page, errs = new_page(b, 390, 844, seed=datos('Noviembre 2026', [g('gc', 'Cuota de prueba', 30000, 17), g('gx', 'Lejano de prueba', 10000, 25)]), fecha='2026-11-15T10:00:00')
    check(page.inner_text('#aviso-vence b') == 'Cuota de prueba: vence en 2 días', 'uno solo en 2 días: título «vence en 2 días»')
    page.click('[data-act=aviso-pagar][data-id=gc]'); page.wait_for_timeout(200)
    check(page.locator('#aviso-vence').count() == 0, 'pagado lo único: el aviso desaparece')
    check(not errs, f'sin errores {errs}'); ctx.close()
    # Mañana
    ctx, page, errs = new_page(b, 390, 844, seed=datos('Noviembre 2026', [g('gc', 'Cuota de prueba', 30000, 16)]), fecha='2026-11-15T10:00:00')
    check(page.inner_text('#aviso-vence b') == 'Cuota de prueba: vence mañana', 'vence mañana')
    ctx.close()
    # Día 31 en un mes de 30: vence hoy el 30
    ctx, page, errs = new_page(b, 1280, 900, seed=datos('Noviembre 2026', [g('gc', 'Cuota de prueba', 30000, 31), g('gy', 'Agua de prueba', 30000, 30)]), fecha='2026-11-30T10:00:00')
    check(page.inner_text('#aviso-vence b') == 'Hoy vencen 2 gastos', 'día 31 en un mes de 30 vence hoy (30)')
    check(page.locator('[data-key=g-gc] .tag', has_text='Vence hoy').count() == 1, 'la etiqueta de la fila también dice «Vence hoy»')
    check(not errs, f'sin errores {errs}'); ctx.close()
    # Todo pagado o sin gastos: sin aviso
    ctx, page, errs = new_page(b, 390, 844, seed=datos('Noviembre 2026', [g('gc', 'Cuota de prueba', 30000, 10)], pagados=('gc',)), fecha='2026-11-15T10:00:00')
    check(page.locator('#aviso-vence').count() == 0, 'todo pagado: sin aviso'); ctx.close()

def ics(b):
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    g = lambda i, n, m, v, c='servicios', nota='': {'id': i, 'nombre': n, 'estimado': m, 'categoria': c, 'vence': v, 'nota': nota}
    gs = [g('ga', 'Luz de prueba', 20000, 15), g('gb', 'Colegio, cuota; prueba', 90000, 31, 'educacion', 'Nota larga de prueba con acentos: año, cañería, música y más texto para pasar los 75 octetos de una línea'),
          g('gc', 'Pagado de prueba', 50000, 5), g('gd', 'Sin día de prueba', 9000, '')]
    est = {x['id']: {'real': '', 'pagado': x['id'] == 'gc'} for x in gs}; est['ga']['real'] = 23500
    seed = {'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 900000, 'nota': ''}], 'gastos': gs},
            'current': {'mesLabel': 'Noviembre 2026', 'gastos': est, 'ingresos': {'i1': {'real': '', 'cobrado': False}}, 'movimientos': []}, 'history': []}
    def bajar(page):
        with page.expect_download() as dl:
            page.click('.sheet .actions button[type=submit]')
        d = dl.value; raw = open(d.path(), 'rb').read()
        return d.suggested_filename, raw
    def eventos(txt):
        un = txt.replace('\r\n ', '')
        return [e.split('END:VEVENT')[0] for e in un.split('BEGIN:VEVENT')[1:]]
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark')]:
        label = f'ics {w} {theme}'
        print(f'\n== Agregar al calendario (v2.2) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=seed, fecha='2026-11-10T10:00:00')
        antes = (get(page, 'config'), get(page, 'current'))
        page.click('.nav [data-tab=fijos]'); page.click('[data-act=vista][data-f=cal]'); page.wait_for_timeout(150)
        check(page.locator('#app [data-act=ics]').count() == 1, f'{label}: botón «Agregar al calendario» en el calendario')
        no_hscroll(page, w, label + ' calendario')
        page.screenshot(path=str(SHOTS / f'ics-cal-{w}-{theme}.png'))
        page.click('#app [data-act=ics]'); page.wait_for_selector('.sheet'); page.wait_for_timeout(450)
        check(page.inner_text('#sheet-title') == 'Agregar al calendario', f'{label}: se abre la hoja')
        check('Noviembre 2026' in page.inner_text('.sheet .sheet-note') and 'undefined' not in page.inner_text('.sheet'), f'{label}: la hoja nombra el mes')
        check(page.input_value('.sheet [name=alarma]') == '1d' and page.input_value('.sheet [name=todos]') == '0', f'{label}: por defecto 1 día antes y solo sin pagar')
        check(page.locator('.ics-row').count() == 2 and 'Falta pagar $' in page.inner_text('.ics-h'), f'{label}: vista previa con 2 sin pagar')
        page.screenshot(path=str(SHOTS / f'ics-hoja-{w}-{theme}.png'))
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA en la hoja {[(o["t"], o["r"]) for o in malos]}')
        page.select_option('.sheet [name=todos]', '1'); page.wait_for_timeout(80)
        check(page.locator('.ics-row').count() == 3 and page.locator('.ics-row.pagado').count() == 1, f'{label}: «Todos» suma el pagado en la vista previa')
        page.select_option('.sheet [name=todos]', '0'); page.wait_for_timeout(80)
        nombre, raw = bajar(page)
        txt = raw.decode('utf-8')
        check(nombre == 'vencimientos-2026-11.ics', f'{label}: nombre del archivo ({nombre})')
        check(txt.startswith('BEGIN:VCALENDAR\r\n') and txt.endswith('END:VCALENDAR\r\n') and '\n' not in txt.replace('\r\n', ''), f'{label}: formato con CRLF')
        check(max(len(l.encode()) for l in txt.split('\r\n')) <= 75, f'{label}: ninguna línea pasa los 75 octetos')
        ev = eventos(txt)
        check(len(ev) == 2, f'{label}: 2 eventos (sin el pagado ni el que no tiene día)')
        luz = next((e for e in ev if 'Luz de prueba' in e), ''); col = next((e for e in ev if 'Colegio' in e), '')
        check('DTSTART;VALUE=DATE:20261115' in luz and 'DTEND;VALUE=DATE:20261116' in luz, f'{label}: Luz el 15, todo el día')
        check('DTSTART;VALUE=DATE:20261130' in col and 'DTEND;VALUE=DATE:20261201' in col, f'{label}: el 31 cae el 30 de noviembre')
        check('UID:cm-ga-202611@control-mensual' in luz, f'{label}: UID estable por gasto y mes')
        check('23.500' in luz and 'TRIGGER:-PT15H' in luz and luz.count('BEGIN:VALARM') == 1, f'{label}: monto real y aviso 1 día antes a las 9')
        check(r'Colegio\, cuota\; prueba' in col and 'Nota: Nota larga' in col and '(estimado)' in col, f'{label}: texto escapado, nota y «estimado»')
        check(get(page, 'meta').get('ics') == {'alarma': '1d', 'todos': False}, f'{label}: preferencia guardada')
        page.wait_for_timeout(100)
        check('Descargado: 2 vencimientos' in page.inner_text('#toast'), f'{label}: aviso de descarga')
        # Desde el menú: sin aviso + todos
        page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet')
        page.click('.sheet [data-run=ics]'); page.wait_for_selector('.sheet [name=alarma]')
        page.select_option('.sheet [name=alarma]', 'no'); page.select_option('.sheet [name=todos]', '1')
        _, raw2 = bajar(page); ev2 = eventos(raw2.decode('utf-8'))
        check(len(ev2) == 3 and not any('VALARM' in e for e in ev2) and any('✓ Vence Pagado de prueba' in e for e in ev2), f'{label}: «Sin aviso» y «Todos» (pagado con ✓)')
        page.reload(); page.wait_for_selector('.hero')
        page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet'); page.click('.sheet [data-run=ics]'); page.wait_for_selector('.sheet [name=alarma]')
        check(page.input_value('.sheet [name=alarma]') == 'no' and page.input_value('.sheet [name=todos]') == '1', f'{label}: recuerda la elección al recargar')
        page.select_option('.sheet [name=alarma]', '7d'); page.select_option('.sheet [name=todos]', '0')
        _, raw3 = bajar(page); ev3 = eventos(raw3.decode('utf-8'))
        check(len(ev3) == 2 and all('TRIGGER:-P6DT15H' in e for e in ev3), f'{label}: aviso 1 semana antes')
        check((get(page, 'config'), get(page, 'current')) == antes, f'{label}: los datos no cambian')
        no_hscroll(page, w, label)
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()
    print('\n== Agregar al calendario: todo pagado')
    s2 = json.loads(json.dumps(seed)); 
    for k in s2['current']['gastos']: s2['current']['gastos'][k]['pagado'] = True
    ctx, page, errs = new_page(b, 390, 844, seed=s2, fecha='2026-11-10T10:00:00')
    page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet'); page.click('.sheet [data-run=ics]'); page.wait_for_selector('.sheet [name=alarma]')
    check('No queda nada por pagar' in page.inner_text('.ics-prev'), 'todo pagado: mensaje en la vista previa')
    descargas = []; page.on('download', lambda d: descargas.append(d))
    page.click('.sheet .actions button[type=submit]'); page.wait_for_timeout(300)
    check(not descargas and page.locator('.sheet').count() == 1, 'todo pagado: no descarga y la hoja sigue abierta')
    check(not errs, f'sin errores {errs}')
    ctx.close()

def gcal(b):
    from urllib.parse import urlparse, parse_qs
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    g = lambda i, n, m, v, c='servicios', nota='': {'id': i, 'nombre': n, 'estimado': m, 'categoria': c, 'vence': v, 'nota': nota}
    gs = [g('ga', 'Luz de prueba', 20000, 15, nota='Cliente de prueba 123'), g('gb', 'Colegio & cuota', 90000, 31, 'educacion'), g('gd', 'Sin día de prueba', 9000, '')]
    est = {x['id']: {'real': '', 'pagado': False} for x in gs}; est['ga']['real'] = 23500
    seed = {'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 900000, 'nota': ''}], 'gastos': gs},
            'current': {'mesLabel': 'Noviembre 2026', 'gastos': est, 'ingresos': {'i1': {'real': '', 'cobrado': False}}, 'movimientos': []}, 'history': []}
    def q(page):
        u = urlparse(page.get_attribute('.sheet .btn-gcal', 'href') or '')
        return u, {k: v[0] for k, v in parse_qs(u.query).items()}
    def abrir(page, id):
        page.click(f'.row-main[data-act=edit-gasto][data-id={id}]'); page.wait_for_selector('.sheet #gcal'); page.wait_for_timeout(400)
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark')]:
        label = f'gcal {w} {theme}'
        print(f'\n== Agregar a Google Calendar (v2.3) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=seed, fecha='2026-11-10T10:00:00')
        antes = (get(page, 'config'), get(page, 'current'))
        page.click('.nav [data-tab=fijos]'); page.wait_for_timeout(150)
        abrir(page, 'ga')
        a = page.locator('.sheet .btn-gcal')
        check(a.is_visible() and 'Agregar a Google Calendar' in a.inner_text(), f'{label}: botón visible en la hoja del gasto')
        check(a.get_attribute('target') == '_blank' and 'noopener' in (a.get_attribute('rel') or ''), f'{label}: abre en pestaña nueva (noopener)')
        u, p = q(page)
        check(u.scheme == 'https' and u.netloc == 'calendar.google.com' and u.path == '/calendar/render' and p.get('action') == 'TEMPLATE', f'{label}: enlace de Google Calendar ({u.geturl()[:60]})')
        check(p.get('dates') == '20261115/20261116', f'{label}: día 15, todo el día ({p.get("dates")})')
        check(p.get('text', '').replace('\xa0', ' ') == 'Vence Luz de prueba · $ 23.500', f'{label}: título con monto real ({p.get("text")!r})')
        det = p.get('details', '')
        check('Categoría: ' in det and 'Estado: sin pagar' in det and 'Nota: Cliente de prueba 123' in det and '(estimado)' not in det, f'{label}: detalles ({det!r})')
        check('15 de noviembre 2026' in page.inner_text('#gcal p'), f'{label}: indica la fecha')
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA en la hoja {[(o["t"], o["r"]) for o in malos]}')
        no_hscroll(page, w, label + ' hoja')
        page.locator('.sheet #gcal').scroll_into_view_if_needed()
        page.screenshot(path=str(SHOTS / f'gcal-{w}-{theme}.png'))
        # Usa lo escrito sin guardar
        page.fill('.sheet [name=vence]', '31'); page.fill('.sheet [name=real]', ''); page.fill('.sheet [name=nota]', 'Otra nota')
        u, p = q(page)
        check(p.get('dates') == '20261130/20261201', f'{label}: 31 cae el 30 de noviembre ({p.get("dates")})')
        check(p.get('text', '').replace('\xa0', ' ') == 'Vence Luz de prueba · $ 20.000' and '(estimado)' in p.get('details', '') and 'Otra nota' in p.get('details', ''), f'{label}: usa estimado y nota escritos')
        page.fill('.sheet [name=vence]', '')
        check(not a.is_visible() and 'Poné el día de vencimiento' in page.inner_text('#gcal p'), f'{label}: sin día, el botón se oculta y lo indica')
        page.fill('.sheet [name=vence]', '15')
        if w == 1280:
            with ctx.expect_page() as np:
                a.click()
            nueva = np.value
            check(nueva.url.startswith('https://calendar.google.com/calendar/render?action=TEMPLATE'), f'{label}: al tocar abre Google Calendar en otra pestaña')
            nueva.close()
        page.keyboard.press('Escape'); page.wait_for_timeout(200)
        check((get(page, 'config'), get(page, 'current')) == antes, f'{label}: los datos no cambian si no se guarda')
        abrir(page, 'gd')
        check(not page.locator('.sheet .btn-gcal').is_visible(), f'{label}: gasto sin día: sin botón')
        page.keyboard.press('Escape'); page.wait_for_timeout(200)
        abrir(page, 'gb'); u, p = q(page)
        check(p.get('text') and '&' in p['text'] and p.get('dates') == '20261130/20261201', f'{label}: caracteres especiales y 31→30')
        page.keyboard.press('Escape'); page.wait_for_timeout(200)
        # Gasto nuevo
        page.click('[data-act=add-gasto]') if page.locator('[data-act=add-gasto]').count() else None
        if page.locator('.sheet #gcal').count():
            page.wait_for_timeout(400)
            check(not page.locator('.sheet .btn-gcal').is_visible(), f'{label}: gasto nuevo sin día: sin botón')
            page.fill('.sheet [name=nombre]', 'Nuevo de prueba'); page.fill('.sheet [name=vence]', '3'); page.fill('.sheet [name=estimado]', '1.000')
            u, p = q(page)
            check(p.get('dates') == '20261103/20261104' and 'Nuevo de prueba' in p.get('text', ''), f'{label}: gasto nuevo con día genera enlace')
            page.keyboard.press('Escape'); page.wait_for_timeout(200)
        else:
            check(False, f'{label}: no encontré el botón para agregar gasto')
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()

# Notification simulada: estado en window.name (sobrevive a recargas y no toca el almacenamiento): 'perm', 'resp' y 'notifs'.
NOTIF_MOCK = """(() => { if (%s) { delete window.Notification; return; }
  const st = () => { try { return JSON.parse(window.name || '{}'); } catch (e) { return {}; } };
  const ss = {getItem: k => st()[k] ?? null, setItem: (k, v) => { const o = st(); o[k] = v; window.name = JSON.stringify(o); }}; if (!ss.getItem('perm')) ss.setItem('perm', '%s');
  class N { constructor(t, o) { const l = JSON.parse(ss.getItem('notifs') || '[]'); l.push({t, body: o && o.body, tag: o && o.tag}); ss.setItem('notifs', JSON.stringify(l)); this.onclick = null; window.__ultima = this; }
    close() {} static get permission() { return ss.getItem('perm'); }
    static requestPermission() { const r = ss.getItem('resp') || 'granted'; ss.setItem('perm', r); return Promise.resolve(r); } }
  window.Notification = N; })();"""

def notif(b):
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    notifs = lambda page: page.evaluate("JSON.parse(JSON.parse(window.name||'{}').notifs||'[]')")
    g = lambda i, n, m, v: {'id': i, 'nombre': n, 'estimado': m, 'categoria': 'servicios', 'vence': v, 'nota': ''}
    gs = [g('ga', 'Atrasado de prueba', 11000, 10), g('gb', 'Luz de prueba', 20000, 15), g('gx', 'Lejano de prueba', 10000, 25)]
    def datos(mes='Noviembre 2026', meta=None):
        d = {'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 900000, 'nota': ''}], 'gastos': gs},
             'current': {'mesLabel': mes, 'gastos': {x['id']: {'real': '', 'pagado': False} for x in gs}, 'ingresos': {'i1': {'real': '', 'cobrado': False}}, 'movimientos': []},
             'history': []}
        if meta is not None: d['meta'] = {'schemaVersion': 1, 'appVersion': '2.4', 'vistoNovedades': ['2.4'], 'respaldo': {'ultimo': 1795000000000, 'base': 0, 'pospuesto': None}, **meta}
        return d
    F = '2026-11-15T10:00:00'
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark'), (390, 844, 'dark'), (1280, 900, 'light')]:
        label = f'notif {w} {theme}'
        print(f'\n== Avisos del navegador (v2.4) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=datos(), fecha=F, init=NOTIF_MOCK % ('false', 'default'))
        page.evaluate("(() => { const o = JSON.parse(window.name||'{}'); delete o.notifs; window.name = JSON.stringify(o); })()")
        antes = (get(page, 'config'), get(page, 'current'))
        link = page.locator('#aviso-vence [data-act=notif]')
        check(link.count() == 1 and link.inner_text() == 'Avisarme con una notificación', f'{label}: enlace en el aviso de vencimientos')
        check(notifs(page) == [], f'{label}: sin activar no se notifica')
        no_hscroll(page, w, label)
        page.screenshot(path=str(SHOTS / f'notif-aviso-{w}-{theme}.png'))
        link.click(); page.wait_for_selector('.sheet .notif-estado'); page.wait_for_timeout(400)
        check('Desactivados' in page.inner_text('.notif-estado'), f'{label}: la hoja dice que están desactivados')
        check('Atrasado de prueba está vencido' in page.inner_text('.sheet'), f'{label}: cuenta lo de hoy')
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA en la hoja {[(o["t"], o["r"]) for o in malos]}')
        no_hscroll(page, w, label + ' hoja')
        page.screenshot(path=str(SHOTS / f'notif-hoja-{w}-{theme}.png'))
        page.click('.sheet .actions button:has-text("Activar avisos")'); page.wait_for_timeout(400)
        n = notifs(page)
        check(len(n) == 1 and n[0]['t'] == 'Atrasado de prueba está vencido', f'{label}: al activar llega la notificación ({n})')
        body = (n[0]['body'] if n else '').replace('\xa0', ' ')
        check('Atrasado de prueba · Vencido · día 10' in body and 'Luz de prueba · Vence hoy' in body and 'Total a pagar: $ 31.000' in body and 'Lejano' not in body, f'{label}: cuerpo con filas y total ({body!r})')
        m = get(page, 'meta')
        check(m.get('notif') == {'activo': True, 'ultimo': '2026-11-15'}, f'{label}: meta.notif guardado ({m.get("notif")})')
        check(page.locator('.sheet').count() == 0 and page.locator('#aviso-vence [data-act=notif]').count() == 0, f'{label}: se cierra la hoja y el enlace desaparece')
        check('Avisos activados' in page.inner_text('#toast'), f'{label}: aviso «Avisos activados»')
        page.evaluate("window.__ultima.onclick && window.__ultima.onclick()")
        check(page.locator('.nav [data-tab=resumen]').get_attribute('aria-current') == 'page', f'{label}: tocar la notificación lleva al Resumen')
        page.reload(); page.wait_for_selector('.hero'); page.wait_for_timeout(300)
        check(len(notifs(page)) == 1, f'{label}: al recargar el mismo día no repite')
        page.evaluate("ui.notif.ultimo='2026-11-14'; document.dispatchEvent(new Event('visibilitychange'))"); page.wait_for_timeout(300)
        check(len(notifs(page)) == 2, f'{label}: al volver a la app otro día avisa de nuevo')
        # Menú y hoja activa
        page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet .menu-item[data-run=notif]')
        check('Activas' in page.inner_text('.menu-item[data-run=notif]'), f'{label}: el menú muestra el estado')
        page.click('.menu-item[data-run=notif]'); page.wait_for_selector('.sheet .notif-estado.on'); page.wait_for_timeout(400)
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA en la hoja activa {[(o["t"], o["r"]) for o in malos]}')
        page.screenshot(path=str(SHOTS / f'notif-activa-{w}-{theme}.png'))
        page.click('.sheet .actions button:has-text("Probar")'); page.wait_for_timeout(300)
        check(len(notifs(page)) == 3 and page.locator('.sheet').count() == 1, f'{label}: «Probar» muestra una y deja la hoja abierta')
        page.click('.sheet .actions button:has-text("Desactivar")'); page.wait_for_timeout(300)
        check(get(page, 'meta')['notif']['activo'] is False and page.locator('#aviso-vence [data-act=notif]').count() == 1, f'{label}: «Desactivar» guarda y vuelve el enlace')
        page.evaluate("ui.notif.ultimo=null; document.dispatchEvent(new Event('visibilitychange'))"); page.wait_for_timeout(300)
        check(len(notifs(page)) == 3, f'{label}: desactivados no avisa')
        check((get(page, 'config'), get(page, 'current')) == antes, f'{label}: los datos no cambian')
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()
    print('\n== Avisos del navegador: otros casos')
    # Día siguiente con avisos activos: avisa al abrir, una vez
    ctx, page, errs = new_page(b, 390, 844, seed=datos(meta={'notif': {'activo': True, 'ultimo': '2026-11-14'}}), fecha=F, init=NOTIF_MOCK % ('false', 'granted'))
    page.wait_for_timeout(300)
    check(len(notifs(page)) >= 1 and notifs(page)[-1]['t'] == 'Atrasado de prueba está vencido', 'activos: al abrir otro día avisa')
    check(get(page, 'meta')['notif']['ultimo'] == '2026-11-15' and get(page, 'meta')['schemaVersion'] == 2, 'anota el día y conserva meta')
    check(not errs, f'sin errores {errs}'); ctx.close()
    # Otro mes: no avisa
    ctx, page, errs = new_page(b, 390, 844, seed=datos('Octubre 2026', meta={'notif': {'activo': True, 'ultimo': None}}), fecha=F, init=NOTIF_MOCK % ('false', 'granted'))
    page.wait_for_timeout(300)
    check(notifs(page) == [], 'mes que no es el actual: sin notificación')
    ctx.close()
    # Activos pero el navegador revocó el permiso: no avisa ni ofrece enlace
    ctx, page, errs = new_page(b, 390, 844, seed=datos(meta={'notif': {'activo': True, 'ultimo': None}}), fecha=F, init=NOTIF_MOCK % ('false', 'denied'))
    page.wait_for_timeout(300)
    check(notifs(page) == [] and page.locator('#aviso-vence [data-act=notif]').count() == 0, 'bloqueadas: sin notificación y sin enlace')
    page.click('.appbar [data-act=menu]'); page.wait_for_selector('.menu-item[data-run=notif]')
    check('Bloqueadas' in page.inner_text('.menu-item[data-run=notif]'), 'menú: «Bloqueadas»')
    page.click('.menu-item[data-run=notif]'); page.wait_for_selector('.sheet .notif-estado')
    check('Permisos' in page.inner_text('.sheet') and page.locator('.sheet [data-run=ics]').count() == 1, 'bloqueadas: explica cómo habilitarlas y ofrece el calendario')
    page.click('.sheet [data-run=ics]'); page.wait_for_timeout(200)
    check('calendario' in page.inner_text('#sheet-title').lower(), 'el enlace abre «Agregar al calendario»')
    check(not errs, f'sin errores {errs}'); ctx.close()
    # Permiso negado al pedirlo: mensaje en línea, no activa
    ctx, page, errs = new_page(b, 390, 844, seed=datos(), fecha=F, init=NOTIF_MOCK % ('false', 'default'))
    page.evaluate("(() => { const o = JSON.parse(window.name||'{}'); o.resp = 'denied'; window.name = JSON.stringify(o); })()")
    page.click('#aviso-vence [data-act=notif]'); page.wait_for_selector('.sheet .notif-estado')
    page.click('.sheet .actions button:has-text("Activar avisos")'); page.wait_for_timeout(300)
    check(page.locator('.sheet .form-err').count() == 1 and 'bloqueó' in page.inner_text('.sheet .form-err'), 'permiso negado: mensaje en la hoja')
    check(not (get(page, 'meta') or {}).get('notif', {}).get('activo') and notifs(page) == [], 'permiso negado: no se activa ni notifica')
    check(not errs, f'sin errores {errs}'); ctx.close()
    # Sin soporte (p. ej. Safari de iPhone como página)
    ctx, page, errs = new_page(b, 390, 844, seed=datos(), fecha=F, init=NOTIF_MOCK % ('true', 'default'))
    check(page.locator('#aviso-vence').count() == 1 and page.locator('#aviso-vence [data-act=notif]').count() == 0, 'sin soporte: aviso sin enlace')
    page.click('.appbar [data-act=menu]'); page.wait_for_selector('.menu-item[data-run=notif]')
    page.click('.menu-item[data-run=notif]'); page.wait_for_selector('.sheet .notif-estado')
    check('no permite' in page.inner_text('.sheet') and 'pantalla de inicio' in page.inner_text('.sheet'), 'sin soporte: lo explica')
    no_hscroll(page, 390, 'notif sin soporte')
    check(not errs, f'sin errores {errs}'); ctx.close()

def anticipo(b):
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    g = lambda i, n, m, v: {'id': i, 'nombre': n, 'estimado': m, 'categoria': 'servicios', 'vence': v, 'nota': ''}
    gs = [g('ga', 'Atrasado de prueba', 11000, 10), g('gb', 'Luz de prueba', 20000, 15), g('gc', 'Cuota de prueba', 30000, 17),
          g('gd', 'Gas de prueba', 4000, 19), g('ge', 'Club de prueba', 5000, 21), g('gx', 'Lejano de prueba', 10000, 25)]
    def datos(mes='Noviembre 2026', meta=None):
        d = {'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 900000, 'nota': ''}], 'gastos': gs},
             'current': {'mesLabel': mes, 'gastos': {x['id']: {'real': '', 'pagado': False} for x in gs}, 'ingresos': {'i1': {'real': '', 'cobrado': False}}, 'movimientos': []},
             'history': []}
        if meta is not None: d['meta'] = {'schemaVersion': 1, 'appVersion': '2.4', 'vistoNovedades': ['2.4'], 'respaldo': {'ultimo': 1795000000000, 'base': 0, 'pospuesto': None}, **meta}
        return d
    filas = lambda page: page.evaluate("[...document.querySelectorAll('#aviso-vence .va-row')].map(e=>e.dataset.key.slice(3))")
    pronto = lambda page, d: page.locator(f'.cal-d[data-i="{d}"] .cal-dots i.pronto').count() > 0
    F = '2026-11-15T10:00:00'
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark'), (390, 844, 'dark'), (1280, 900, 'light')]:
        label = f'anticipo {w} {theme}'
        print(f'\n== Anticipación del aviso (v2.5) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=datos(meta={}), fecha=F)
        antes = (get(page, 'config'), get(page, 'current'))
        check(filas(page) == ['ga', 'gb', 'gc'], f'{label}: por defecto avisa 3 días antes ({filas(page)})')
        link = page.locator('#aviso-vence [data-act=anticipo]')
        check(link.count() == 1 and link.inner_text() == 'Avisar 3 días antes · cambiar', f'{label}: enlace en el aviso')
        page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet .menu-item[data-run=anticipo]')
        check('Te avisa 3 días antes del vencimiento' in page.inner_text('.menu-item[data-run=anticipo]'), f'{label}: opción en el menú con el valor')
        page.click('.menu-item[data-run=anticipo]'); page.wait_for_selector('.sheet .ant-opts'); page.wait_for_timeout(300)
        check(page.evaluate("document.querySelector('.sheet [name=dias]:checked').value") == '3', f'{label}: la hoja marca 3')
        prev = page.inner_text('#ant-prev').replace('\xa0', ' ')
        check('3 gastos' in prev and '$ 61.000' in prev, f'{label}: vista previa con 3 días ({prev[:80]!r})')
        page.click('.ant-opt:has(input[value="7"])'); page.wait_for_timeout(150)
        prev = page.inner_text('#ant-prev').replace('\xa0', ' ')
        check('Con 7 días' in prev and '5 gastos' in prev and '$ 70.000' in prev and 'Club de prueba · Vence en 6 días' in prev and 'Lejano' not in prev, f'{label}: vista previa cambia a 7 ({prev[:140]!r})')
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA en la hoja {[(o["t"], o["r"]) for o in malos]}')
        no_hscroll(page, w, label + ' hoja')
        page.screenshot(path=str(SHOTS / f'anticipo-hoja-{w}-{theme}.png'))
        page.click('.sheet .actions button:has-text("Guardar")'); page.wait_for_timeout(300)
        check(get(page, 'meta').get('aviso') == {'dias': 7}, f'{label}: guarda meta.aviso ({get(page, "meta").get("aviso")})')
        check(page.locator('.sheet').count() == 0 and 'te avisamos 7 días antes' in page.inner_text('#toast'), f'{label}: cierra y avisa')
        check(filas(page) == ['ga', 'gb', 'gc', 'gd', 'ge'], f'{label}: el aviso suma lo de 4 y 6 días ({filas(page)})')
        check(link.inner_text() == 'Avisar 7 días antes · cambiar', f'{label}: el enlace muestra 7')
        no_hscroll(page, w, label)
        page.screenshot(path=str(SHOTS / f'anticipo-aviso-{w}-{theme}.png'))
        page.click('#aviso-vence [data-act=ver-cal]'); page.wait_for_timeout(200)
        check(pronto(page, 21) and not pronto(page, 25), f'{label}: en el calendario el 21 «vence pronto» y el 25 no')
        page.reload(); page.wait_for_selector('.hero'); page.wait_for_timeout(200)
        check(filas(page) == ['ga', 'gb', 'gc', 'gd', 'ge'], f'{label}: se recuerda al recargar')
        # Cambiar a 1 desde el aviso, con el teclado
        page.click('#aviso-vence [data-act=anticipo]'); page.wait_for_selector('.sheet .ant-opts'); page.wait_for_timeout(300)
        page.focus('.sheet [name=dias]:checked'); page.keyboard.press('ArrowLeft'); page.keyboard.press('ArrowLeft'); page.keyboard.press('ArrowLeft'); page.wait_for_timeout(150)
        check(page.evaluate("document.querySelector('.sheet [name=dias]:checked').value") == '1' and 'Con 1 día' in page.inner_text('#ant-prev'), f'{label}: con flechas se elige 1 y cambia la vista previa')
        page.keyboard.press('Enter'); page.wait_for_timeout(300)
        check(get(page, 'meta')['aviso'] == {'dias': 1} and filas(page) == ['ga', 'gb'], f'{label}: con 1 día solo vencido y hoy ({filas(page)})')
        # Cancelar no cambia
        page.click('#aviso-vence [data-act=anticipo]'); page.wait_for_selector('.sheet .ant-opts'); page.wait_for_timeout(300)
        page.click('.ant-opt:has(input[value="5"])'); page.click('.sheet .actions button:has-text("Cancelar")'); page.wait_for_timeout(200)
        check(get(page, 'meta')['aviso'] == {'dias': 1} and filas(page) == ['ga', 'gb'], f'{label}: «Cancelar» no cambia nada')
        check((get(page, 'config'), get(page, 'current')) == antes, f'{label}: los datos no cambian')
        check(not errs, f'{label}: sin errores {errs}')
        ctx.close()
    print('\n== Anticipación del aviso: otros casos')
    ctx, page, errs = new_page(b, 390, 844, seed=datos(meta={'aviso': {'dias': 4}}), fecha=F)
    check(filas(page) == ['ga', 'gb', 'gc'], 'valor inválido guardado (4): usa 3')
    check(not errs, f'sin errores {errs}'); ctx.close()
    ctx, page, errs = new_page(b, 390, 844, seed=datos(meta={'aviso': {'dias': 5}}), fecha=F)
    check(filas(page) == ['ga', 'gb', 'gc', 'gd'], 'guardado 5: suma lo de 4 días, no lo de 6')
    check(not errs, f'sin errores {errs}'); ctx.close()
    # Notificaciones con 7 días: texto de la hoja, enlace y contenido
    ctx, page, errs = new_page(b, 390, 844, seed=datos(meta={'aviso': {'dias': 7}, 'notif': {'activo': True, 'ultimo': None}}), fecha=F, init=NOTIF_MOCK % ('false', 'granted'))
    n = page.evaluate("JSON.parse(JSON.parse(window.name||'{}').notifs||'[]')")
    body = (n[-1]['body'] if n else '').replace('\xa0', ' ')
    check('Gas de prueba · Vence en 4 días' in body and 'y 1 más' in body and 'Total a pagar: $ 70.000' in body, f'la notificación usa 7 días ({body!r})')
    page.click('.appbar [data-act=menu]'); page.wait_for_selector('.sheet .menu-item[data-run=notif]')
    page.click('.menu-item[data-run=notif]'); page.wait_for_selector('.sheet .notif-estado'); page.wait_for_timeout(300)
    check('los próximos 7 días' in page.inner_text('.sheet'), 'la hoja de avisos del navegador dice 7 días')
    page.click('.sheet [data-run=anticipo]'); page.wait_for_selector('.sheet .ant-opts')
    check(page.inner_text('#sheet-title') == 'Anticipación del aviso', 'desde la hoja de avisos se abre la anticipación')
    check(not errs, f'sin errores {errs}'); ctx.close()
    # Otro mes: la vista previa lo explica
    ctx, page, errs = new_page(b, 390, 844, seed=datos(mes='Octubre 2026', meta={}), fecha=F)
    page.click('.appbar [data-act=menu]'); page.click('.menu-item[data-run=anticipo]'); page.wait_for_selector('#ant-prev')
    check('solo en el mes en curso' in page.inner_text('#ant-prev'), 'otro mes: la vista previa explica que el aviso es del mes en curso')
    check(not errs, f'sin errores {errs}'); ctx.close()

def frecuencia(b):
    get = lambda page, k: page.evaluate(f"JSON.parse(localStorage.getItem('{P}{k}'))")
    g = lambda i, n, m, v: {'id': i, 'nombre': n, 'estimado': m, 'categoria': 'servicios', 'vence': v, 'nota': ''}
    gs = [g('ga', 'Luz de prueba', 20000, 20), g('gb', 'Seguro de prueba', 60000, 17), g('gc', 'Agua de prueba', 9000, 16)]
    seed = {'config': {'ingresos': [{'id': 'i1', 'nombre': 'Empleo A', 'estimado': 900000, 'nota': ''}], 'gastos': gs},
            'current': {'mesLabel': 'Noviembre 2026', 'gastos': {x['id']: {'real': '', 'pagado': False} for x in gs}, 'ingresos': {'i1': {'real': '', 'cobrado': False}}, 'movimientos': []},
            'history': [], 'meta': {'schemaVersion': 1, 'appVersion': '2.5', 'vistoNovedades': ['2.5'], 'respaldo': {'ultimo': 1795000000000, 'base': 0, 'pospuesto': None}}}
    F = '2026-11-15T10:00:00'
    aviso = lambda page: page.evaluate("[...document.querySelectorAll('#aviso-vence .va-row')].map(e=>e.dataset.key.slice(3))")
    def editar(page, id, frec, mes=None):
        page.click('.nav [data-tab=fijos]'); page.wait_for_timeout(150)
        page.click(f'.row-main[data-act=edit-gasto][data-id={id}]'); page.wait_for_selector('.sheet [name=frecuencia]')
        page.select_option('.sheet [name=frecuencia]', frec)
        if mes is not None: page.select_option('.sheet [name=mesPago]', str(mes))
        page.wait_for_timeout(150)
    for w, h, theme in [(390, 844, 'light'), (1280, 900, 'dark')]:
        label = f'frecuencia {w} {theme}'
        print(f'\n== Frecuencia de cada gasto (v2.6) {label}')
        ctx, page, errs = new_page(b, w, h, theme=theme, seed=seed, fecha=F)
        cfg = get(page, 'config')
        check(all(x['frecuencia'] == 'mensual' and x['mesPago'] is None for x in cfg['gastos']) and [x['id'] for x in cfg['gastos']] == ['ga', 'gb', 'gc']
              and all(cfg['gastos'][k]['estimado'] == gs[k]['estimado'] and cfg['gastos'][k]['vence'] == gs[k]['vence'] for k in range(3)), f'{label}: esquema 1 migra a mensual sin perder nada')
        check(get(page, 'meta')['schemaVersion'] == 2 and get(page, 'pre-migracion-esquema-1') is not None, f'{label}: esquema 2 y copia pre-migración')
        check(page.evaluate('totals().fijos') == 89000 and page.evaluate('totals().nFijos') == 3, f'{label}: totales iguales tras migrar')
        # Hoja: mensual oculta «Se paga en»
        editar(page, 'gb', 'mensual')
        check(page.locator('#f-mespago').is_hidden() and page.inner_text('#lbl-est') == 'Estimado mensual', f'{label}: mensual sin «Se paga en»')
        page.select_option('.sheet [name=frecuencia]', 'trimestral'); page.select_option('.sheet [name=mesPago]', '0'); page.wait_for_timeout(150)
        hint = page.inner_text('#frec-hint')
        check(page.locator('#f-mespago').is_visible() and 'enero, abril, julio y octubre' in hint and 'enero 2027' in hint, f'{label}: el texto explica meses y próximo pago ({hint!r})')
        check(page.inner_text('#lbl-est') == 'Estimado por pago' and page.locator('#f-real').is_hidden(), f'{label}: «Estimado por pago» y sin «Real este mes» si no toca')
        u = page.get_attribute('.sheet .btn-gcal', 'href') or ''
        check('dates=20270117%2F20270118' in u, f'{label}: Google Calendar apunta al próximo pago (enero)')
        page.screenshot(path=str(SHOTS / f'frec-hoja-{w}-{theme}.png'))
        page.click('.sheet button[type=submit]'); page.wait_for_timeout(300)
        x = [x for x in get(page, 'config')['gastos'] if x['id'] == 'gb'][0]
        check(x['frecuencia'] == 'trimestral' and x['mesPago'] == 0, f'{label}: se guarda frecuencia y mes ({x})')
        # Lista: aparte, con próximo
        fuera = page.locator('.row.is-off[data-key=g-gb]')
        check(fuera.count() == 1 and 'Próximo: enero 2027' in fuera.inner_text() and 'Trimestral' in fuera.inner_text() and fuera.locator('button.check').count() == 0, f'{label}: en Gastos fijos se ve aparte, sin tilde y con el próximo pago')
        check('no se pagan en noviembre' in page.inner_text('.fuera-h').lower(), f'{label}: título de la sección aparte')
        check(page.evaluate('totals().fijos') == 29000 and page.evaluate('totals().nFijos') == 2, f'{label}: no suma este mes')
        # bimestral que toca (septiembre → noviembre)
        editar(page, 'gc', 'bimestral', 8)
        check('Este mes (noviembre) toca' in page.inner_text('#frec-hint') and page.locator('#f-real').is_visible(), f'{label}: bimestral desde septiembre toca en noviembre')
        page.click('.sheet button[type=submit]'); page.wait_for_timeout(300)
        check('Bimestral' in page.inner_text('[data-key=g-gc]') and page.locator('.row.is-off[data-key=g-gc]').count() == 0, f'{label}: el que toca lleva la etiqueta y se tilda normal')
        page.screenshot(path=str(SHOTS / f'frec-lista-{w}-{theme}.png'), full_page=True)
        no_hscroll(page, w, label)
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA en Gastos fijos {malos[:3]}')
        # Calendario sin el trimestral
        page.click('[data-act=vista][data-f=cal]'); page.wait_for_timeout(200)
        check(page.locator('.cal-d[data-i="17"] .cal-dots i').count() == 0 and page.locator('.cal-d[data-i="16"] .cal-dots i').count() == 1, f'{label}: el calendario no muestra lo que no toca')
        page.click('[data-act=vista][data-f=lista]')
        # Resumen
        page.click('.nav [data-tab=resumen]'); page.wait_for_timeout(200)
        check(page.locator('.grid [data-key=g-gb]').count() == 0 and '1 gasto no se paga este mes' in page.inner_text('.fuera-nota'), f'{label}: Resumen sin el trimestral y con la nota')
        check(aviso(page) == ['gc'], f'{label}: el aviso no incluye lo que no toca (el 17) y sí el bimestral del 16 ({aviso(page)})')
        malos = page.evaluate(AUDIT_JS)
        check(not malos, f'{label}: contraste AA en Resumen {malos[:3]}')
        page.screenshot(path=str(SHOTS / f'frec-resumen-{w}-{theme}.png'), full_page=True)
        # Recargar
        page.reload(); page.wait_for_selector('.hero')
        check(page.evaluate('totals().fijos') == 29000 and page.locator('.grid [data-key=g-gb]').count() == 0, f'{label}: se recuerda al recargar')
        check(not errs, f'{label}: sin errores {errs}'); ctx.close()
    # Diciembre: no tocan el trimestral (ene/abr/jul/oct) ni el bimestral (sep/nov/ene…); al cerrar, en enero tocan los tres
    print('\n== Frecuencia: cierre de mes y respaldo')
    s2 = json.loads(json.dumps(seed)); s2['meta']['schemaVersion'] = 2
    s2['config']['gastos'][1].update(frecuencia='trimestral', mesPago=0); s2['config']['gastos'][2].update(frecuencia='bimestral', mesPago=8)
    s2['config']['gastos'][0].update(frecuencia='mensual', mesPago=None)
    s2['current']['mesLabel'] = 'Diciembre 2026'
    ctx, page, errs = new_page(b, 390, 844, seed=s2, fecha='2026-12-10T10:00:00')
    check(page.evaluate('totals().nFijos') == 1, 'diciembre: solo toca el mensual')
    page.click('#close-mobile'); page.wait_for_selector('.sheet'); page.click('.sheet button[type=submit]'); page.wait_for_timeout(300)
    check(get(page, 'current')['mesLabel'] == 'Enero 2027' and page.evaluate('totals().nFijos') == 3, 'enero: tocan el mensual, el trimestral y el bimestral')
    check(get(page, 'history')[0]['gastos'] == 20000, 'el historial de diciembre solo sumó lo que tocaba')
    # Restaurar un respaldo del esquema 1 (pegado)
    rsp = json.dumps({'version': 2, 'schemaVersion': 1, 'config': seed['config'], 'current': seed['current'], 'history': []})
    page.click('.appbar [data-act=menu]'); page.click('.menu-item[data-run=pegar]'); page.wait_for_selector('.sheet textarea')
    page.fill('.sheet textarea', rsp); page.click('.sheet button[type=submit]'); page.wait_for_timeout(400)
    check(all(x['frecuencia'] == 'mensual' for x in get(page, 'config')['gastos']), 'respaldo del esquema 1 restaurado queda mensual')
    check(not errs, f'sin errores {errs}'); ctx.close()

def primera_vez(b):
    print('\n== Primera vez (sin datos)')
    ctx, page, errs = new_page(b, 390, 844, seed={})
    meta = page.evaluate(f"JSON.parse(localStorage.getItem('{P}meta'))")
    check(meta and meta['schemaVersion'] >= 1, 'meta creado en instalación nueva')
    check(page.locator('.appbar .dot').count() == 0, 'sin aviso de novedades la primera vez')
    check(not page.evaluate(f"Object.keys(localStorage).some(k=>k.includes('pre-migracion'))"), 'sin copia pre-migración innecesaria')
    check(page.locator('#aviso-respaldo').count() == 0, 'sin aviso de respaldo en instalación nueva')
    check(not errs, f'sin errores {errs}')
    ctx.close()

with sync_playwright() as pw:
    exe = '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None
    b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
    for w, h in [(390, 844), (1280, 900)]:
        for theme in ['light', 'dark']:
            flujo(b, w, h, theme)
    migracion(b)
    doble_copia(b)
    aviso_respaldo(b)
    respaldo_texto(b)
    deshacer(b)
    validacion(b)
    accesibilidad(b)
    redibujo(b)
    calendario(b)
    aviso_vence(b)
    ics(b)
    gcal(b)
    notif(b)
    anticipo(b)
    frecuencia(b)
    primera_vez(b)
    b.close()

print('\nRESULTADO:', 'TODO OK' if not fails else f'{len(fails)} FALLAS')
sys.exit(1 if fails else 0)
