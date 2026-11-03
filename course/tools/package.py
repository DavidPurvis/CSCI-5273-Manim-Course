"""Archive the prepared source with explicit acceptance status; excludes build and environments."""
from pathlib import Path
import json,zipfile
from course.tools.preparation import ROOT,audit,timeline_findings
from dataclasses import asdict


def main():
    findings=audit()+timeline_findings()
    from course.tools.release_status import refresh
    status=refresh()
    target=ROOT.parent/'CSCI-5273-Course-Source.zip'
    pending=target.with_suffix('.zip.part')
    with zipfile.ZipFile(pending,'w',zipfile.ZIP_DEFLATED,compresslevel=1) as z:
        for p in sorted(ROOT.rglob('*')):
            if not p.is_file():continue
            rel=p.relative_to(ROOT)
            if any(x in ('.venv','.venv-speech','build','media','__pycache__','.pytest_cache','.heard') for x in rel.parts):continue
            z.write(p,'source/'+rel.as_posix())
    with zipfile.ZipFile(pending) as z:
        failed=z.testzip()
        if failed:raise RuntimeError(f'Archive integrity failed: {failed}')
    pending.replace(target)
    print(target)
    print(f"{len(findings)} input findings remain; release_verified={status['release_verified']}")

if __name__=='__main__':main()
