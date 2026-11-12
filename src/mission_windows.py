"""Hour-to-hour visibility window *proxies* from 72 observed JPL/LOLA clearance samples.

Produces exact crossing estimates for two *assumed* interpolants: piecewise
linear and shape-preserving PCHIP. This is model sensitivity, not independent
high-frequency ground truth. No extrapolation before t=0 or after t=71 h.
"""
from __future__ import annotations
import csv, json, math
from pathlib import Path
from datetime import datetime, timedelta
from collections import defaultdict
import numpy as np
from scipy.interpolate import PchipInterpolator
from scipy.optimize import brentq
from atomic_io import atomic_write

MARGINS=(0.,0.5,1.,2.,3.)


def crossing_region(left,right,threshold,value_at):
    """Positive part of a monotone interval [0,1], ignoring zero-measure endpoints."""
    a=left-threshold;b=right-threshold
    if a>0 and b>0:return (0.,1.)
    if a<=0 and b<=0:return None
    if a==0:return (0.,1.) if b>0 else None
    if b==0:return (0.,1.) if a>0 else None
    t=brentq(lambda u:value_at(u)-threshold,0.,1.,xtol=1e-13)
    return (0.,float(t)) if a>0 else (float(t),1.)


def merge_runs(segments):
    merged=[]
    for a,b in segments:
        if b-a<=1e-12:continue
        if merged and a-merged[-1][1]<1e-8:
            merged[-1]=(merged[-1][0],max(merged[-1][1],b))
        else:
            merged.append((a,b))
    return merged


def event_windows(sun,earth,margin,method):
    """Return all joint-clear run boundaries in hours since first observed epoch."""
    s=np.asarray(sun,dtype=float);e=np.asarray(earth,dtype=float)
    if s.shape!=(72,) or e.shape!=(72,) or not np.all(np.isfinite(s)) or not np.all(np.isfinite(e)):
        raise ValueError('Exactly 72 finite clearance samples are required for both bodies')
    if method not in ('linear','pchip'):raise ValueError('method must be linear or pchip')
    fs=PchipInterpolator(np.arange(72),s) if method=='pchip' else None
    fe=PchipInterpolator(np.arange(72),e) if method=='pchip' else None
    pieces=[]
    for i in range(71):
        def func(body,full,u):
            if method=='linear':return body[i]+u*(body[i+1]-body[i])
            return float(full(i+u))
        rs=crossing_region(s[i],s[i+1],margin,lambda u:func(s,fs,u))
        re=crossing_region(e[i],e[i+1],margin,lambda u:func(e,fe,u))
        if rs is None or re is None:continue
        a=max(rs[0],re[0])+i;b=min(rs[1],re[1])+i
        if b-a>1e-12:pieces.append((float(a),float(b)))
    return merge_runs(pieces)


def validation_cv(clearance):
    """Alternate-hour withheld *observed sample* interpolation discrepancy."""
    y=np.asarray(clearance,float);x=np.arange(72)
    errors=[]
    for parity in (0,1):
        keep=x[x%2==parity]
        hold=x[(x%2!=parity)&(x>keep[0])&(x<keep[-1])]
        fit=PchipInterpolator(keep,y[keep],extrapolate=False)
        err=fit(hold)-y[hold]
        errors.extend(np.abs(err).tolist())
    return {'withheld_hour_samples':len(errors),
            'abs_error_p95_deg':round(float(np.percentile(errors,95)),6),
            'abs_error_max_deg':round(float(np.max(errors)),6)}


def summarize_runs(runs,start):
    def ts(h):
        d=start+timedelta(hours=h)
        return d.strftime('%Y-%b-%d %H:%M:%S.')+f'{int(d.microsecond/1000):03d} TDB'
    return [{'start_h':round(a,7),'end_h':round(b,7),
             'duration_h':round(b-a,7), 'start_tdb':ts(a),'end_tdb':ts(b),
             'left_boundary_truncated':bool(a<=1e-8),'right_boundary_truncated':bool(b>=71-1e-8)} for a,b in runs]


def generate(source):
    raw=defaultdict(list)
    with Path(source).open(newline='') as f:
        for row in csv.DictReader(f):raw[row['site']].append(row)
    if len(raw)!=10:raise ValueError('Expected exactly 10 sites')
    report={'description':'JPL/LOLA 72 sampled hourly Sun/Earth joint skyline-clearance interpolation model diagnostic',
            'time_scale':'TDB: 71 gaps from 2026-Nov-14 00:00 through 2026-Nov-16 23:00',
            'limits':'PCHIP and linear within-hour proxies; cannot establish true continuous visibility, actual engineering operation, or orbital/terrain uncertainty bounds.',
            'margins_deg':list(MARGINS),'sites':{}}
    flattened=[]
    for site,rows in sorted(raw.items()):
        rows.sort(key=lambda r:datetime.strptime(r['epoch_tdb'],'%Y-%b-%d %H:%M:%S.%f'))
        if len(rows)!=72:raise ValueError(f'{site}: 72 rows required')
        start=datetime.strptime(rows[0]['epoch_tdb'],'%Y-%b-%d %H:%M:%S.%f')
        if any(datetime.strptime(r['epoch_tdb'],'%Y-%b-%d %H:%M:%S.%f')-start !=timedelta(hours=i) for i,r in enumerate(rows)):
            raise ValueError(f'{site}: actual one-hour TDB spacing required')
        s=[float(r['sun_elevation_deg'])-float(r['sun_terrain_horizon_deg']) for r in rows]
        e=[float(r['earth_elevation_deg'])-float(r['earth_terrain_horizon_deg']) for r in rows]
        entry={'sun_alternate_hour_pchip_cv':validation_cv(s),
               'earth_alternate_hour_pchip_cv':validation_cv(e), 'margins':{}}
        for margin in MARGINS:
            metrics={};k=str(int(margin)) if margin.is_integer() else str(margin)
            for method in ('linear','pchip'):
                runs=event_windows(s,e,margin,method)
                summarized=summarize_runs(runs,start)
                metrics[method]={'total_hours':round(sum(b-a for a,b in runs),7),
                                 'longest_run_hours':round(max((b-a for a,b in runs),default=0.),7),
                                 'number_of_runs':len(runs),'runs':summarized}
                for j,segment in enumerate(summarized):
                    flattened.append({'site':site,'margin_deg':margin,'method':method,'run_number':j+1,**segment})
            metrics['pchip_minus_linear_hours']=round(metrics['pchip']['total_hours']-metrics['linear']['total_hours'],7)
            metrics['sampled_joint_good']=sum(a>margin and b>margin for a,b in zip(s,e))
            entry['margins'][k]=metrics
        report['sites'][site]=entry
    return report,flattened


def main():
    root=Path(__file__).resolve().parents[1]
    report,rows=generate(root/'data/real_72h_JPL_LOLA.csv')
    dest=root/'data'
    atomic_write(dest/'window_audit.json',(json.dumps(report,indent=2,ensure_ascii=False)+'\n').encode())
    from io import StringIO
    f=StringIO(newline='')
    fields=['site','margin_deg','method','run_number','start_h','end_h','duration_h','start_tdb','end_tdb','left_boundary_truncated','right_boundary_truncated']
    writer=csv.DictWriter(f,fields,lineterminator='\n');writer.writeheader();writer.writerows(rows)
    atomic_write(dest/'window_runs.csv',f.getvalue().encode())
    print('Exact within-proxy crossing solver: 10 sites × 5 margins × 2 methods; emitted',len(rows),'runs')
    for name in ('South_84E40','South_83E60'):
        metric=report['sites'][name]['margins']['1']
        print(name,'1 degree: linear',metric['linear']['total_hours'],'PCHIP',metric['pchip']['total_hours'],'longest PCHIP',metric['pchip']['longest_run_hours'])

if __name__=='__main__':main()
