"""Real Chromium UI + real Tank Royale. Not a physical-smartphone test."""
from __future__ import annotations
import json
import os
from pathlib import Path
import sys
import threading
sys.path.insert(0, str(Path(__file__).resolve().parents[2] / 'scripts'))
import serve_mobile_spike as app
from playwright.sync_api import sync_playwright, expect


def main():
    output = app.mobile.ROOT / '.local/mobile-browser'
    output.mkdir(parents=True, exist_ok=True)
    evidence = {'environment': 'chromium-emulation-not-physical-phone', 'viewports': [], 'battles': []}
    server = app.LabServer(0)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        with sync_playwright() as p:
            options = {'headless': True}
            if os.getenv('CHROMIUM_EXECUTABLE'):
                options['executable_path'] = os.environ['CHROMIUM_EXECUTABLE']
            browser = p.chromium.launch(**options)
            for width, height, touch in [(360, 800, True), (390, 844, True), (1280, 900, False)]:
                context = browser.new_context(viewport={'width': width, 'height': height},
                                              is_mobile=touch, has_touch=touch)
                page = context.new_page()
                errors=[]
                page.on('pageerror', lambda error: errors.append(str(error)))
                page.goto(f'http://127.0.0.1:{server.server_port}')
                expect(page.get_by_role('status')).to_contain_text('Laboratório pronto')
                assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'), 'Horizontal overflow'
                assert page.locator('#codigo').evaluate('e => parseFloat(getComputedStyle(e).fontSize)') >= 16
                for button in page.locator('button').all():
                    assert button.bounding_box()['height'] >= 44
                source = app.mobile.LANG.EXAMPLES['sentinela'] + '# rascunho\n'
                page.get_by_label('Código da estratégia').fill(source)
                page.get_by_role('button', name='Salvar rascunho').click()
                page.reload()
                expect(page.get_by_label('Código da estratégia')).to_have_value(source)
                page.get_by_label('Código da estratégia').fill('System.exit(0)')
                page.get_by_role('button', name='Verificar código').click()
                expect(page.get_by_role('status')).to_contain_text('Linha 1')
                expect(page.get_by_label('Código da estratégia')).to_have_value('System.exit(0)')
                page.get_by_label('Código da estratégia').fill(app.mobile.LANG.EXAMPLES['explorador'])
                page.get_by_role('button', name='Verificar código').click()
                expect(page.get_by_role('status')).to_contain_text('Código válido')
                if width == 390:
                    for strategy in ('sentinela', 'explorador'):
                        page.get_by_label('Código da estratégia').fill(app.mobile.LANG.EXAMPLES[strategy])
                        with page.expect_response(lambda r: r.url.endswith('/api/train'), timeout=240000) as received:
                            page.get_by_role('button', name='Testar no motor real').click()
                        response=received.value
                        data=response.json()
                        assert response.status == 200, data
                        app.mobile.validate_result(data['results'], app.mobile.LANG.compile_program(app.mobile.LANG.EXAMPLES[strategy])['program_sha256'])
                        expect(page.get_by_role('status')).to_contain_text('Batalha concluída', timeout=10000)
                        page.get_by_role('button', name='Reproduzir replay').click()
                        page.wait_for_timeout(350)
                        page.get_by_role('button', name='Pausar replay').click()
                        page.screenshot(path=str(output / f'mobile-{strategy}.png'), full_page=True)
                        evidence['battles'].append({'strategy': strategy, 'run_id': data['run_id'],
                            'results': data['results'], 'replay': {k:v for k,v in data['replay'].items() if k!='frames'}})
                    first,second=evidence['battles']
                    assert first['results']['program_sha256'] != second['results']['program_sha256']
                    assert second['replay']['mean_abs_speed'] > first['replay']['mean_abs_speed'] + 1, evidence
                assert not errors, errors
                page.screenshot(path=str(output/f'viewport-{width}.png'), full_page=True)
                evidence['viewports'].append({'width':width,'height':height,'touch_emulation':touch,
                    'horizontal_overflow':False,'draft_recovered':True,'invalid_code_preserved':True,'javascript_errors':errors})
                context.close()
            browser.close()
        evidence['status']='PASS'
        (output/'browser-evidence.json').write_text(json.dumps(evidence,indent=2),encoding='utf-8')
        print('PASS: Chromium, três viewports, rascunho, erros recuperáveis e duas batalhas reais.')
    finally:
        server.shutdown();server.server_close();thread.join()

if __name__=='__main__': main()
