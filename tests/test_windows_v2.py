"""Scientific and browser regression for Moonfix V2 window explorer."""
import csv, json, math, os, shutil, sys
from pathlib import Path
from playwright.sync_api import sync_playwright
from scipy.interpolate import PchipInterpolator
import numpy as np

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'src'))
from mission_windows import event_windows, generate, validation_cv, summarize_runs


def test_exact_linear_crossing_and_simultaneous_intersection():
    s=np.ones(72)*(-1);e=np.ones(72)*(-1)
    s[0],s[1]= -1.,3.
    e[0],e[1]=3.,-1.
    assert event_windows(s,e,0,'linear')==[(0.25,0.75)]
    assert event_windows(s,e,0,'pchip')[0][0]>0
    pchip=event_windows(s,e,0,'pchip')
    assert len(pchip)==1 and 0<pchip[0][0]<pchip[0][1]<1


def test_reject_broken_data_and_method():
    for args in [([0]*71,[0]*72,0,'linear'),([0]*72,[float('nan')]*72,0,'linear'),([0]*72,[0]*72,0,'cubic')]:
        try:event_windows(*args)
        except ValueError:pass
        else:raise AssertionError('Must reject bad input')


def test_exact_pchip_root_vs_independent_dense_grid_all_sites_margins():
    data=json.loads((ROOT/'data.json').read_text())
    for site in data['sites']:
        s=np.array([r['sunEl']-r['sunH'] for r in site['rows']]);e=np.array([r['earthEl']-r['earthH'] for r in site['rows']])
        x=np.arange(72); fine=np.linspace(0,71,71*600+1)
        fs=PchipInterpolator(x,s);fe=PchipInterpolator(x,e)
        for m in [0.,.5,1.,2.,3.]:
            exact=sum(b-a for a,b in event_windows(s,e,m,'pchip'))
            good=(fs(fine)>m)&(fe(fine)>m)
            dense=float(np.sum((good[:-1].astype(float)+good[1:].astype(float)))/2/600)
            assert abs(exact-dense)<1/600+1e-9,(site['id'],m,exact,dense)
            metric=site['windows']['margins'][str(int(m)) if m.is_integer() else str(m)]
            assert abs(exact-metric['pchip']['total_hours'])<2e-6
            assert metric['sampled_joint_good']==site['counts'][str(int(m)) if m.is_integer() else str(m)]
            assert abs(sum(r['duration_h'] for r in metric['pchip']['runs'])-exact)<2e-6
            assert all(0<=r['start_h']<r['end_h']<=71 for r in metric['pchip']['runs'])
            assert all(r['right_boundary_truncated']==(r['end_h']>=71-1e-8) for r in metric['pchip']['runs'])


def test_linear_matches_original_builder_and_all_methods_consistent():
    d=json.loads((ROOT/'data.json').read_text())
    for site in d['sites']:
        s=[r['sunEl']-r['sunH'] for r in site['rows']];e=[r['earthEl']-r['earthH'] for r in site['rows']]
        for m in [0.,.5,1.,2.,3.]:
            k=str(int(m)) if m.is_integer() else str(m)
            linear=sum(b-a for a,b in event_windows(s,e,m,'linear'))
            assert abs(linear-site['estimatedHours'][k])<.00006
            assert abs(linear-site['windows']['margins'][k]['linear']['total_hours'])<1e-6
            assert site['windows']['margins'][k]['linear']['total_hours'] >= -1e-8
            assert site['windows']['margins'][k]['linear']['total_hours'] <= 71+1e-8


def test_cv_is_withheld_observed_hours_not_false_uncertainty():
    d=json.loads((ROOT/'data.json').read_text())
    for site in d['sites']:
        assert site['windows']['sun_alternate_hour_pchip_cv']['withheld_hour_samples']==70
        assert site['windows']['earth_alternate_hour_pchip_cv']['withheld_hour_samples']==70
        assert site['windows']['sun_alternate_hour_pchip_cv']['abs_error_p95_deg']>=0


def test_window_data_export_file_matches_embedded_data():
    data=json.loads((ROOT/'data.json').read_text());audit=json.loads((ROOT/'data/window_audit.json').read_text())
    assert len(audit['sites'])==10
    rows=list(csv.DictReader((ROOT/'data/window_runs.csv').open()))
    assert len(rows)==sum(len(s['windows']['margins'][str(int(m)) if m.is_integer() else str(m)][method]['runs']) for s in data['sites'] for m in [0.,.5,1.,2.,3.] for method in ['linear','pchip'])
    for site in data['sites']:
        assert site['windows']==audit['sites'][site['id']]
        for m in [0.,.5,1.,2.,3.]:
            k=str(int(m)) if m.is_integer() else str(m)
            for method in ['linear','pchip']:
                runs=site['windows']['margins'][k][method]['runs']
                filtered=[r for r in rows if r['site']==site['id'] and float(r['margin_deg'])==m and r['method']==method]
                assert len(runs)==len(filtered)


def test_browser_window_controls_and_csv_download(tmp_path):
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=os.getenv('MOONFIX_CHROME') or shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
        page=b.new_page(accept_downloads=True,viewport={'width':1440,'height':900})
        errs=[];page.on('pageerror',lambda e:errs.append(str(e)))
        page.set_content((ROOT/'index.html').read_text(),wait_until='load')
        assert '44.03 h' in page.locator('#windowSummary').inner_text()
        assert page.locator('#windowTimeline .window-run').count()==2
        assert page.locator('#windowRuns .window-jump').count()==1
        page.locator('#windowRuns .window-jump').click()
        assert page.locator('#timeSlider').input_value()!='12'
        with page.expect_download() as dl:
            page.locator('#downloadWindows').click()
        file=dl.value
        assert 'South_84E40_1deg_windows.csv' in file.suggested_filename
        dest=tmp_path/file.suggested_filename;file.save_as(dest)
        saved=list(csv.DictReader(dest.open()))
        assert len(saved)==2 and set(r['method'] for r in saved)=={'linear','pchip'}
        page.locator('#siteChoice').select_option(label='South · 84E90')
        assert 'No joint-clear intervals' in page.locator('#windowRuns').inner_text()
        assert page.locator('#windowTimeline .window-run').count()==0
        page.locator('#siteChoice').select_option(label='South · 83E60')
        page.locator('#marginButtons button[data-margin="2"]').click()
        assert page.locator('#windowTimeline .window-run').count()==0
        page.locator('#marginButtons button[data-margin="1"]').click()
        assert '16.72 h' in page.locator('#windowSummary').inner_text()
        assert not errs,errs
        b.close()


def test_mobile_window_panel_reflows():
    with sync_playwright() as p:
        b=p.chromium.launch(executable_path=os.getenv('MOONFIX_CHROME') or shutil.which('chromium') or None,headless=True,args=['--no-sandbox'])
        page=b.new_page(viewport={'width':390,'height':844})
        page.set_content((ROOT/'index.html').read_text(),wait_until='load')
        assert page.locator('#windowSummary .window-metric').count()==4
        assert page.locator('#windowRuns .window-jump').count()==1
        # Main content should never overflow its *own* document width.
        assert page.evaluate('document.querySelector(".window-panel").scrollWidth <= document.querySelector(".window-panel").clientWidth + 2')
        b.close()
