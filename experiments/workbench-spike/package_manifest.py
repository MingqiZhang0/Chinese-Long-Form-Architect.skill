"""Hash the actual package bytes; never invent a clean-machine certification."""
import hashlib,json,sys
from pathlib import Path
root=Path(sys.argv[1]).resolve()
files=[{'path':p.relative_to(root).as_posix(),'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'size':p.stat().st_size} for p in sorted(root.rglob('*')) if p.is_file() and p.name!='package-manifest.json']
manifest={'format':'spike-package-1','rid':'win-x64','app':'spike-1','engine':'spike-1','protocol':'1.0.0','net_runtime':'10.0.11','avalonia':'12.1.3','python':'3.14.2','pyinstaller':'6.16.0','clean_machine_verified':False,'files':files}
(root/'package-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n',encoding='utf-8')
print(json.dumps({'files':len(files),'bytes':sum(x['size'] for x in files)}))
