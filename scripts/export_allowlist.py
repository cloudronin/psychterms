"""Audit prospective public files without uploading or publishing anything."""
from pathlib import Path
import json,re,subprocess
from core import ROOT
ALLOW_FILES={'README.md','PROJECT-PLAN.md','LICENSE','LICENSE-DATA','NOTICE.md','CONTRIBUTING.md','.gitignore','package.json','package-lock.json','requirements-dev.txt'}
ALLOW_DIRS={'scripts','schema','data','docs','tests','site','.github','reports'}
EXCLUDED={'node_modules','.git','.private','.cache','__pycache__','.astro','dist','dist-data','.venv'}
def public_paths():
 for p in ROOT.rglob('*'):
  rel=p.relative_to(ROOT)
  if not p.is_file() or any(part in EXCLUDED for part in rel.parts) or rel.as_posix().startswith('site/public/downloads/'):continue
  if len(rel.parts)==1 and rel.name not in ALLOW_FILES:raise ValueError('Unexpected root file: '+str(rel))
  if len(rel.parts)>1 and rel.parts[0] not in ALLOW_DIRS:raise ValueError('Unexpected directory: '+str(rel))
  if p.suffix in {'.key','.pem','.pdf','.bin'} or p.is_symlink():raise ValueError('Unexpected private or binary file: '+str(rel))
  try:text=p.read_text()
  except UnicodeError:raise ValueError('Unexpected binary: '+str(rel))
  if re.search(r'/Users/[A-Za-z0-9_.-]+/|(?<![A-Za-z0-9_-])sk-[A-Za-z0-9_-]{20,}|BEGIN (?:RSA |OPENSSH )?PRIVATE KEY',text):raise ValueError('Private path or secret-like material: '+str(rel))
  yield rel.as_posix()
if __name__=='__main__':
 paths=sorted(public_paths());print(json.dumps({'allowlisted_files':len(paths),'private_files_exported':0,'uploaded':False,'paths':paths},indent=2))
