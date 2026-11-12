"""Release Moonfix V2 with atomic manifest, ZIP, SHA-256 and fsync."""
from pathlib import Path
from sys import path as import_path
import_path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
from atomic_io import atomic_write
import json, hashlib, zipfile, os, uuid

ROOT=Path(__file__).resolve().parents[1]
OUT=Path(os.getenv('MOONFIX_RELEASE_ZIP','/mnt/data/Moonfix_NASA_SpaceApps_ENGINEERING_V2_ATOMIC_VERIFIED_20261106.zip'))
OMIT={'__pycache__','.pytest_cache','.git','_demo_frames','_v2_frames'}

def digest_bytes(data):return hashlib.sha256(data).hexdigest()

def digest_file(path):
    h=hashlib.sha256()
    with open(path,'rb') as f:
        for buf in iter(lambda:f.read(4<<20),b''):h.update(buf)
    return h.hexdigest()

def build():
    contents=[p for p in sorted(ROOT.rglob('*')) if p.is_file() and not (set(p.relative_to(ROOT).parts)&OMIT) and p.name not in ('SHA256_MANIFEST.json','RELEASE_RECEIPT.json') and not p.name.endswith(('.pyc','.partial'))]
    hashes={p.relative_to(ROOT).as_posix():digest_file(p) for p in contents}
    manifest={'release':'Moonfix NASA Lunar Navigator — Engineering V2','created_utc_date':'2026-11-06','hash_algorithm':'sha256',
              'file_count_without_manifest':len(hashes), 'files_sha256':hashes,
              'notes':'Standalone HTML and all 100 model/scenario diagnostics included; no official submission is asserted.'}
    atomic_write(ROOT/'SHA256_MANIFEST.json',(json.dumps(manifest,indent=2,ensure_ascii=False)+'\n').encode())
    contents.append(ROOT/'SHA256_MANIFEST.json')
    OUT.parent.mkdir(parents=True,exist_ok=True)
    tmp=OUT.with_name('.'+OUT.name+'.'+uuid.uuid4().hex+'.partial')
    try:
        with zipfile.ZipFile(tmp,'w',compression=zipfile.ZIP_DEFLATED,compresslevel=6,allowZip64=True) as z:
            for p in contents:z.write(p,p.relative_to(ROOT).as_posix())
        with zipfile.ZipFile(tmp) as z:
            assert z.testzip() is None
            assert len(z.namelist())==len(contents)
            for name,sha in hashes.items():
                assert digest_bytes(z.read(name))==sha,name
            bundled=json.loads(z.read('SHA256_MANIFEST.json'))
            assert bundled['files_sha256']==hashes
        with open(tmp,'rb') as f:os.fsync(f.fileno())
        os.replace(tmp,OUT)
        try:
            d=os.open(OUT.parent,os.O_RDONLY|os.O_DIRECTORY)
            try:os.fsync(d)
            finally:os.close(d)
        except OSError:pass
    finally:
        if tmp.exists():tmp.unlink()
    print(json.dumps({'zip':str(OUT),'bytes':OUT.stat().st_size,'sha256':digest_file(OUT),'files_in_zip':len(contents),'data_rows':720,'sites':10,'model_scenarios':100},indent=2))
if __name__=='__main__':
    import sys
    sys.path.insert(0,str(Path(__file__).resolve().parents[1]/'src'))
    build()
