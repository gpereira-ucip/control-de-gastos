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

def new_page(b, w, h, theme=None, seed=None):
    ctx = b.new_context(viewport={'width': w, 'height': h}, device_scale_factor=1)
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
    check(page.locator('.ver-foot').inner_text().find('1.') >= 0, f'{label}: versión visible en el menú')
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
    primera_vez(b)
    b.close()

print('\nRESULTADO:', 'TODO OK' if not fails else f'{len(fails)} FALLAS')
sys.exit(1 if fails else 0)
