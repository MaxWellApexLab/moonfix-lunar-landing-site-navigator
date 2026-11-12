"""Build a complete offline NASA Space Apps 2026 Lunar Landing Site Navigator.

Dataset is the supplied real 72-hour JPL-DE441/LOLA prepared CSV, 10 sites,
not simulated orbital predictions.  Uses official 80m LOLA DEM only for small
local pixel-correct relief tiles; explicitly warns against landing safety use.
Produces self-contained index.html with embedded data and no CDN dependencies.
"""
from __future__ import annotations
from pathlib import Path
import base64,csv,io,json,math,hashlib,sys,os
from collections import defaultdict
from mission_windows import generate
from atomic_io import atomic_write
from PIL import Image
import numpy as np
import rasterio
from rasterio.windows import Window
from pyproj import CRS,Transformer

BASE=Path(__file__).resolve().parents[1]
OUTPUT=Path(os.environ.get('MOONFIX_OUTPUT',str(BASE)))
CSV=Path(os.environ.get('MOONFIX_CSV',str(BASE/'data/real_72h_JPL_LOLA.csv')))
SUMMARY=Path(os.environ.get('MOONFIX_SUMMARY',str(BASE/'data/terrain_summaries.json')))
DEM=Path(os.environ.get('MOONFIX_DEM','/mnt/data/LDEM_80S_80MPP_ADJ.TIF'))
MARGINS=(0.,.5,1.,2.,3.)



def intervals(clear_s,clear_e,margin=0.):
    # Exact within the stated, unverified assumption: straight line between
    # each pair of one-hour Sun/Earth terrain-horizon-clearance measurements.
    result=0.
    for a,b,c,d in zip(clear_s[:-1],clear_s[1:],clear_e[:-1],clear_e[1:]):
        def region(left,right):
            left-=margin;right-=margin
            if left>0 and right>0:return 0.,1.
            if left<=0 and right<=0:return None
            q=-left/(right-left)
            return (0.,q) if left>0 else (q,1.)
        s=region(a,b);e=region(c,d)
        if s is not None and e is not None:
            result+=max(0.,min(s[1],e[1])-max(s[0],e[0]))
    return float(result)


def tile_data(ds,lat,lon):
    moon_geo=CRS.from_proj4('+proj=longlat +a=1737400 +b=1737400 +no_defs')
    x,y=Transformer.from_crs(moon_geo,ds.crs,always_xy=True).transform(lon,lat)
    row,col=ds.index(x,y)
    n=13
    z=ds.read(1,window=Window(col-n,row-n,2*n+1,2*n+1),masked=True).filled(np.nan).astype(float)
    if z.shape!=(27,27) or not np.isfinite(z).all():raise ValueError('Missing LOLA terrain tile')
    q=(z-np.min(z))/(np.ptp(z) or 1)
    # Hillshade is merely a visualization of physical DEM heights, not a
    # calibrated physical illumination forecast. Apply two gradient sources.
    gy,gx=np.gradient(z,80,80)
    normal=np.stack((-gx,-gy,np.ones_like(gx)),axis=-1)
    normal/=np.linalg.norm(normal,axis=-1,keepdims=True)
    light=np.array([-.55,-.4,.73]);light/=np.linalg.norm(light)
    shade=np.clip((normal*light).sum(-1)*.65+.35,0,1)
    low=np.array([29,42,61]);high=np.array([179,200,196])
    color=low[None,None,:]*(1-q[:,:,None])+high[None,None,:]*q[:,:,None]
    arr=np.uint8(np.clip(color*(.5+.5*shade[:,:,None]),0,255))
    im=Image.fromarray(arr,'RGB').resize((270,270),Image.Resampling.BICUBIC)
    buff=io.BytesIO();im.save(buff,format='PNG',optimize=True)
    return 'data:image/png;base64,'+base64.b64encode(buff.getvalue()).decode()


def build_data():
    raw=defaultdict(list)
    with CSV.open(newline='') as f:
        for row in csv.DictReader(f):raw[row['site']].append(row)
    previous=json.loads(SUMMARY.read_text())
    byname={s['name']:s for s in previous['sites']}
    if set(raw)!=set(byname) or len(raw)!=10:raise ValueError('Source site mismatch')
    window_report,window_flat=generate(CSV)
    items=[]
    with rasterio.open(DEM) as ds:
        for name,rows in sorted(raw.items()):
            rows=sorted(rows,key=lambda r:r['epoch_tdb'])
            if len(rows)!=72 or len({r['epoch_tdb'] for r in rows})!=72:
                raise ValueError('72 distinct hourly TDB epochs required')
            record=byname[name]
            detail=[]
            for i,row in enumerate(rows):
                if not all(row['site']==name for row in rows):raise ValueError('Bad site')
                detail.append({'time':row['epoch_tdb'],'sunEl':float(row['sun_elevation_deg']),
                    'sunAz':float(row['sun_azimuth_deg']),'sunH':float(row['sun_terrain_horizon_deg']),
                    'earthEl':float(row['earth_elevation_deg']),'earthAz':float(row['earth_azimuth_deg']),
                    'earthH':float(row['earth_terrain_horizon_deg'])})
            cs=[r['sunEl']-r['sunH'] for r in detail]
            ce=[r['earthEl']-r['earthH'] for r in detail]
            counts={str(int(m) if m.is_integer() else m):sum(s>m and e>m for s,e in zip(cs,ce)) for m in MARGINS}
            for key,c in counts.items():
                if c!=record['visibility_by_margin_deg'][str(float(key))]['joint_samples']:
                    raise ValueError('Site %s margin=%s mismatch old physical analysis: %s'%(name,key,c))
            estimated={key:round(intervals(cs,ce,float(key)),4) for key in counts}
            data={'id':name,'lat':float(rows[0]['latitude_deg']),
                'lon':float(rows[0]['longitude_east_deg']),'slope95':round(record['terrain']['slope_p95_deg'],3),
                'slope50':round(record['terrain']['slope_p50_deg'],3),
                'relief':round(record['terrain']['elevation_p95_minus_p05_m'],2),
                'elevation':round(record['terrain']['center_elevation_m'],2),
                'counts':counts,'estimatedHours':estimated,'rows':detail,
                'windows':window_report['sites'][name],
                'reliefPng':tile_data(ds,float(rows[0]['latitude_deg']),float(rows[0]['longitude_east_deg']))}
            items.append(data)
    return {'sites':items,'meta':{
        'label':'NASA Lunar Landing Site Navigator — Moonfix',
        'science':'Real participant-supplied JPL Horizons DE441 hourly geometry and LOLA 80-m terrain-derived skyline samples',
        'start':'2026-Nov-14 00:00 TDB','end':'2026-Nov-16 23:00 TDB',
        'timeScale':'TDB (Barycentric Dynamical Time) — not local NYC clock time',
        'sampling':'72 hourly observations/site; 71 between-hour intervals',
        'limitations':['No time extrapolation outside 2026-Nov-14..16','A sampled visible hour is not guaranteed continuous visibility',
                       'Visibility requires both Sun and Earth above their local terrain skyline, plus a selected safety angle',
                       '80 m LOLA terrain cannot resolve small rocks or certify landing safety',
                       'No spacecraft power storage, link budget, sun tracking, or full lunar orbit/attitude model',
                       'The 71h linear-interpolated value is an assumed model proxy, not direct ephemeris or mission truth'],
        'sourceSha256':{'CSV':hashlib.sha256(CSV.read_bytes()).hexdigest(),
                       'LOLA_Terrain':hashlib.sha256(DEM.read_bytes()).hexdigest(),
                       'Prior_terrain_validation':hashlib.sha256(SUMMARY.read_bytes()).hexdigest()}}}


def main():
    data=build_data()
    html=Path(__file__).with_name('ui_template.html').read_text(encoding='utf-8')
    embedded=json.dumps(data,separators=(',',':'),ensure_ascii=False).replace('</','<\\/')
    html=html.replace('__EMBEDDED_DATA__',embedded)
    OUTPUT.mkdir(parents=True,exist_ok=True)
    atomic_write(OUTPUT/'index.html',html.encode('utf-8'))
    atomic_write(OUTPUT/'sources.json',json.dumps(data['meta'],indent=2).encode())
    atomic_write(OUTPUT/'data.json',json.dumps(data,ensure_ascii=False,indent=2).encode())
    OUTPUT.joinpath('data').mkdir(exist_ok=True)
    atomic_write(OUTPUT/'data/real_72h_JPL_LOLA.csv',CSV.read_bytes())
    atomic_write(OUTPUT/'data/terrain_summaries.json',SUMMARY.read_bytes())
    audit,rows=generate(CSV)
    atomic_write(OUTPUT/'data/window_audit.json',(json.dumps(audit,indent=2,ensure_ascii=False)+'\n').encode())
    buffer=io.StringIO()
    fields=['site','margin_deg','method','run_number','start_h','end_h','duration_h','start_tdb','end_tdb','left_boundary_truncated','right_boundary_truncated']
    csv_writer=csv.DictWriter(buffer,fieldnames=fields,lineterminator='\n')
    csv_writer.writeheader();csv_writer.writerows(rows)
    atomic_write(OUTPUT/'data/window_runs.csv',buffer.getvalue().encode())
    print('Built',OUTPUT/'index.html','bytes', (OUTPUT/'index.html').stat().st_size,
        'sites',len(data['sites']),'rows',sum(len(x['rows']) for x in data['sites']))
    for s in sorted(data['sites'],key=lambda x:-x['counts']['1']):
        print(s['id'],'joint 1deg',s['counts']['1'],'estimated hours 1deg',s['estimatedHours']['1'],'slope P95',s['slope95'])
    return data

if __name__=='__main__':main()
