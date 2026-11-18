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
    page.fill('#mov-form [name=desc]', 'Verdulería'); page.fill('#mov-form [name=monto]', '4.321')
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
                page.fill('#mov-form [name=desc]', 'Kiosco'); page.fill('#mov-form [name=monto]', '999')
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
    primera_vez(b)
    b.close()

print('\nRESULTADO:', 'TODO OK' if not fails else f'{len(fails)} FALLAS')
sys.exit(1 if fails else 0)
