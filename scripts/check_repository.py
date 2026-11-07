"""Small staged-source hygiene check. Not a full historical secret scanner."""
import re
import subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
paths=subprocess.check_output(['git','ls-files'],cwd=ROOT,text=True).splitlines()
errors=[]
for relative in paths:
    p=ROOT/relative
    if relative.startswith(('.venv/','.state/')) or p.suffix in ('.sqlite3','.pem','.key','.mp4','.zip'):
        errors.append(f'Forbidden source artifact: {relative}')
    if p.name.startswith('.env') and p.name!='.env.example': errors.append(f'Environment file tracked: {relative}')
    if p.stat().st_size>1024*1024: errors.append(f'Oversized tracked artifact: {relative}')
    if p.suffix in ('.py','.md','.js','.html','.css','.json','.toml','.yml') or p.name=='.env.example':
        text=p.read_text()
        patterns=(r'-----BEGIN [A-Z ]*PRIVATE KEY-----',r'gh[pousr]_[A-Za-z0-9]{30,}',r'sk-[A-Za-z0-9]{30,}')
        if any(re.search(pattern,text) for pattern in patterns): errors.append(f'Potential credential in {relative}')
if not paths: errors.append('No tracked source files to check.')
if errors: raise SystemExit('\n'.join(errors))
print(f'PASS: {len(paths)} tracked files; no matches in this limited hygiene check.')
