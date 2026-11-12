"""Crash-resistant, single-file atomic publication helper for generated artifacts."""
from pathlib import Path
import os, uuid

def atomic_write(path, data):
    path=Path(path);path.parent.mkdir(parents=True,exist_ok=True)
    tmp=path.with_name('.'+path.name+'.'+uuid.uuid4().hex+'.partial')
    try:
        with open(tmp,'wb') as f:
            f.write(data);f.flush();os.fsync(f.fileno())
        os.replace(tmp,path)
        try:
            d=os.open(path.parent,os.O_RDONLY | getattr(os,'O_DIRECTORY',0))
            try:os.fsync(d)
            finally:os.close(d)
        except OSError:pass
    finally:
        if tmp.exists():tmp.unlink()
