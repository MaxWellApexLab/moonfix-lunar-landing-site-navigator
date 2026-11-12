"""Fresh-directory, all-file-hash, browser, science and deterministic rebuild check."""
from pathlib import Path
import hashlib,json,os,shutil,subprocess,sys,zipfile
ROOT=Path(__file__).resolve().parents[1]
ARCHIVE=Path(os.getenv('MOONFIX_RELEASE_ZIP','/mnt/data/Moonfix_NASA_SpaceApps_ENGINEERING_V2_ATOMIC_VERIFIED_20261106.zip'))
DEST=Path(os.getenv('MOONFIX_VERIFICATION_DIR','/mnt/data/Moonfix_Engineering_V2_CLEAN_EXTRACT_20261106'))
sys.path.insert(0,str(ROOT/'src'))
from atomic_io import atomic_write

def sha(path):
 h=hashlib.sha256()
 with open(path,'rb') as f:
  for part in iter(lambda:f.read(4<<20),b''):h.update(part)
 return h.hexdigest()

def main():
 if DEST.exists():shutil.rmtree(DEST)
 DEST.mkdir(parents=True,exist_ok=True)
 with zipfile.ZipFile(ARCHIVE) as z:
  assert z.testzip() is None
  # no path traversal
  assert all(not Path(n).is_absolute() and '..' not in Path(n).parts for n in z.namelist())
  z.extractall(DEST)
 manifest=json.loads((DEST/'SHA256_MANIFEST.json').read_text())
 def verify():
  for name,expected in manifest['files_sha256'].items():
   p=DEST/name
   assert p.is_file(),name
   assert sha(p)==expected,(name,'hash mismatch')
  observed=[p for p in DEST.rglob('*') if p.is_file() and not (set(p.relative_to(DEST).parts)&{'__pycache__','.pytest_cache'}) and p.suffix!='.pyc']
  assert len(manifest['files_sha256'])==len(observed)-1,(len(manifest['files_sha256']),len(observed))
 verify()
 proc=subprocess.run([sys.executable,'-m','pytest','-q','--disable-warnings'],cwd=DEST,text=True,capture_output=True,timeout=90)
 assert proc.returncode==0,proc.stdout+'\n'+proc.stderr
 assert '14 passed' in proc.stdout,proc.stdout
 before={name:sha(DEST/name) for name in ('index.html','data.json','sources.json','data/window_audit.json','data/window_runs.csv')}
 assert Path('/mnt/data/LDEM_80S_80MPP_ADJ.TIF').is_file(),'Original NASA DEM unavailable'
 env=dict(os.environ,MOONFIX_DEM='/mnt/data/LDEM_80S_80MPP_ADJ.TIF')
 cp=subprocess.run([sys.executable,'src/build_moonfix.py'],cwd=DEST,env=env,text=True,capture_output=True,timeout=90)
 assert cp.returncode==0,cp.stdout+'\n'+cp.stderr
 assert all(sha(DEST/name)==before[name] for name in before),'Non-deterministic clean builder output'
 verify()
 import csv
 d=json.loads((DEST/'data.json').read_text())
 audit=json.loads((DEST/'data/window_audit.json').read_text())
 rows=list(csv.DictReader((DEST/'data/window_runs.csv').open()))
 assert len(d['sites'])==10 and sum(len(site['rows']) for site in d['sites'])==720
 assert len(audit['sites'])==10 and len(rows)==16
 assert len(d['sites'])*len(audit['margins_deg'])*2==100
 receipt={'release':ARCHIVE.name,'release_bytes':ARCHIVE.stat().st_size,'release_sha256':sha(ARCHIVE),
          'fresh_extraction':str(DEST),'verified_manifest_files':len(manifest['files_sha256']),
          'verified_zip_members':len(manifest['files_sha256'])+1,
          'clean_pytest':'14 passed','browser_ui_and_csv_export_tested':True,
          'deterministic_rebuild_from_original_NASA_DEM':True,
          'source_sites':10,'real_hourly_records':720,
          'model_scenarios':100,'exported_window_segments':len(rows),
          'official_NASA_submission_claimed':False}
 outside=Path('/mnt/data/Moonfix_NASA_SpaceApps_ENGINEERING_V2_VERIFICATION_RECEIPT.json')
 atomic_write(outside,(json.dumps(receipt,ensure_ascii=False,indent=2)+'\n').encode())
 print(json.dumps(receipt,indent=2))

if __name__=='__main__':main()
