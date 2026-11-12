"""Full source-data, generated-browser and scientific-screening regression checks."""
from pathlib import Path
import csv,json,math,sys,shutil,os
from playwright.sync_api import sync_playwright

ROOT=Path(__file__).resolve().parents[1]
# The source code in this release is moved to src/ and imports no unreleased data.
sys.path.insert(0,str(ROOT/'src'))
from build_moonfix import intervals


def test_all_720_real_hourly_records():
    data=json.loads((ROOT/'data.json').read_text())
    assert len(data['sites'])==10
    assert len({site['id'] for site in data['sites']})==10
    assert sum(len(site['rows']) for site in data['sites'])==720
    for site in data['sites']:
        assert 0<=site['counts']['1']<=72
        assert len({r['time'] for r in site['rows']})==72
        sun=[x['sunEl']-x['sunH'] for x in site['rows']]
        earth=[x['earthEl']-x['earthH'] for x in site['rows']]
        for clearance in (0.,.5,1.,2.,3.):
            label=str(int(clearance)) if clearance.is_integer() else str(clearance)
            observed=sum(a>clearance and b>clearance for a,b in zip(sun,earth))
            assert observed==site['counts'][label]
            assert abs(intervals(sun,earth,clearance)-site['estimatedHours'][label])<1e-4
        assert site['reliefPng'].startswith('data:image/png;base64,')


def test_known_site_metrics_from_provenance():
    records={s['id']:s for s in json.loads((ROOT/'data.json').read_text())['sites']}
    assert records['South_84E40']['counts']['1']==45
    assert records['South_83E60']['counts']['1']==17
    assert abs(records['South_84E40']['slope95']-16.44)<.02
    assert abs(records['South_83E60']['estimatedHours']['1']-16.7186)<.00005


def test_no_network_dependency():
    content=(ROOT/'index.html').read_text()
    assert '__EMBEDDED_DATA__' not in content
    assert len(content)>150000
    assert 'https://cdn' not in content.lower()
    assert 'fetch(' not in content.lower()
    assert 'data:image/png;base64' in content
    assert 'JPL Horizons' in content


def test_credible_lunar_interpolation():
    assert intervals([4.,4.],[4.,4.],1.)==1.
    assert intervals([-2.,2.],[2.,-2.],0.)==0.
    assert abs(intervals([-1.,3.],[3.,-1.],0.)-.5)<1e-9


def test_browser_ui_all_interactions_and_no_js_errors():
    with sync_playwright() as p:
        browser=p.chromium.launch(executable_path=os.getenv('MOONFIX_CHROME') or shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
        page=browser.new_page(viewport={'width':1440,'height':1000})
        errors=[]
        page.on('pageerror',lambda e:errors.append(str(e)))
        page.set_content((ROOT/'index.html').read_text(),wait_until='load')
        assert page.locator('#compareTable tbody tr').count()==10
        assert page.locator('#joint').inner_text()=='45/72'
        assert page.locator('#hours').inner_text().startswith('44.0')
        page.locator('#siteChoice').select_option(label='South · 83E60')
        assert page.locator('#joint').inner_text()=='17/72'
        page.locator('#marginButtons button[data-margin="0"]').click()
        assert int(page.locator('#joint').inner_text().split('/')[0])>=17
        page.locator('#marginButtons button[data-margin="1"]').click()
        page.locator('#dateButtons button[data-day="2"]').click()
        assert page.locator('#hourReadout').inner_text()=='12:00'
        assert 'Nov-16' in page.locator('#epochLabel').inner_text()
        page.locator('#timeSlider').fill('71')
        assert '71' in page.locator('#timeSlider').input_value()
        assert page.locator('#compareTable tbody tr.active').count()==1
        assert page.locator('#polar circle[data-index]').count()==10
        assert not errors,errors
        browser.close()


def test_small_mobile_browser_renders():
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=os.getenv('MOONFIX_CHROME') or shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
        pg=b.new_page(viewport={'width':390,'height':844},device_scale_factor=1)
        errors=[];pg.on('pageerror',lambda e:errors.append(str(e)))
        pg.set_content((ROOT/'index.html').read_text(),wait_until='load')
        assert pg.locator('#joint').inner_text()=='45/72'
        assert pg.locator('#compareTable tbody tr').count()==10
        assert not errors
        b.close()
