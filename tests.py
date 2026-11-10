#!/usr/bin/env python3
"""Pruebas de Control Mensual (Playwright).

Uso:  python3 tests.py [ruta/index.html] [carpeta_capturas]
Abre el archivo local (file://), en 390x844 y 1280x900, claro y oscuro, y verifica:
  - sin errores de consola ni de página
  - sin scroll horizontal (scrollWidth == ancho)
  - recorrer pestañas, tildar un pago, cargar un movimiento, cerrar un mes
  - migración: datos con formato v1.0 (sin esquema) se leen sin perder nada
  - novedades / versión
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
    if seed is not None or theme:
        page.evaluate("""([seed, theme, P]) => { localStorage.clear();
            if (seed) for (const [k, v] of Object.entries(seed)) localStorage.setItem(P + k, JSON.stringify(v));
            if (theme) localStorage.setItem(P + 'theme', theme); }""", [seed, theme, P])
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

def primera_vez(b):
    print('\n== Primera vez (sin datos)')
    ctx, page, errs = new_page(b, 390, 844, seed={})
    meta = page.evaluate(f"JSON.parse(localStorage.getItem('{P}meta'))")
    check(meta and meta['schemaVersion'] >= 1, 'meta creado en instalación nueva')
    check(page.locator('.appbar .dot').count() == 0, 'sin aviso de novedades la primera vez')
    check(not page.evaluate(f"Object.keys(localStorage).some(k=>k.includes('pre-migracion'))"), 'sin copia pre-migración innecesaria')
    check(not errs, f'sin errores {errs}')
    ctx.close()

with sync_playwright() as pw:
    exe = '/usr/bin/google-chrome' if os.path.exists('/usr/bin/google-chrome') else None
    b = pw.chromium.launch(executable_path=exe) if exe else pw.chromium.launch()
    for w, h in [(390, 844), (1280, 900)]:
        for theme in ['light', 'dark']:
            flujo(b, w, h, theme)
    migracion(b)
    primera_vez(b)
    b.close()

print('\nRESULTADO:', 'TODO OK' if not fails else f'{len(fails)} FALLAS')
sys.exit(1 if fails else 0)
