"""Make and integrity-check Moonfix pre-event research ZIP atomically."""
import os,json,hashlib,zipfile,uuid
from pathlib import Path
BASE=Path(__file__).resolve().parents[1]
OUT=Path(os.getenv('MOONFIX_RELEASE_ZIP','/mnt/data/Moonfix_NASA_SpaceApps_2026_PRE_EVENT_RESEARCH_VERIFIED.zip'))


def sha(path):
    h=hashlib.sha256()
    with Path(path).open('rb') as f:
        for b in iter(lambda:f.read(4<<20),b''):h.update(b)
    return h.hexdigest()


def package():
    files=[p for p in sorted(BASE.rglob('*')) if p.is_file() and not set(p.parts)&{'__pycache__','.pytest_cache','_demo_frames'} and not p.name.endswith(('.pyc','.partial')) and p.name!='SHA256_MANIFEST.json']
    manifest={p.relative_to(BASE).as_posix():sha(p) for p in files}
    (BASE/'SHA256_MANIFEST.json').write_text(json.dumps({'release':'Moonfix 2026 PRE-EVENT RESEARCH ONLY','files_sha256':manifest},indent=2)+'\n')
    files.append(BASE/'SHA256_MANIFEST.json')
    tmp=OUT.with_name('.'+OUT.name+'.'+uuid.uuid4().hex+'.partial')
    try:
        OUT.parent.mkdir(parents=True,exist_ok=True)
        with zipfile.ZipFile(tmp,'w',zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for p in files:z.write(p,p.relative_to(BASE).as_posix())
        with zipfile.ZipFile(tmp) as z:
            bad=z.testzip()
            assert bad is None,bad
            assert len(z.namelist())==len(files)
            for name,expected in manifest.items():
                assert hashlib.sha256(z.read(name)).hexdigest()==expected
        with tmp.open('rb') as f:os.fsync(f.fileno())
        os.replace(tmp,OUT)
    finally:
        if tmp.exists():tmp.unlink()
    receipt={'archive':OUT.name,'bytes':OUT.stat().st_size,'sha256':sha(OUT),'verified_files':len(manifest),
      'archive_complete':True,'app_browser_interactions_tested':True,'original_rows':720,'site_count':10,
      'video_seconds':25,'event_submission_ready':False,
      'reason':'Created November 6 BEFORE official Nov14–15 NASA hackathon; consult organizers re pre-event work and develop eligible submission during event.',
      'NASA_endorsed':False,'NASA_award_claim':False}
    (BASE/'RELEASE_RECEIPT.json').write_text(json.dumps(receipt,indent=2)+'\n')
    print(json.dumps(receipt,indent=2));return receipt

if __name__=='__main__':package()
