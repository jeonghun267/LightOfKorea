"""Compare visual-pass scope against the verified pre-polish backup."""
import hashlib,json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
backup=root/'Saved/Backups/HeroPolish_20260907_164501'
baseline=json.loads((backup/'before_hashes.json').read_text(encoding='utf-8-sig'))
changed=[];protected=[]
for row in baseline:
    path=Path(row['Path']);rel=path.relative_to(root)
    same=path.exists() and hashlib.sha256(path.read_bytes()).hexdigest().upper()==row['SHA256']
    if not same:changed.append(str(rel))
    if any(part in ('Niagara','Blueprints','MPC') for part in rel.parts):
        protected.append({'path':str(rel),'unchanged':same})
report={'status':'PASS' if all(x['unchanged'] for x in protected) else 'REVIEW',
 'protected_assets':protected,'changed_existing_assets':changed,'backup':str(backup)}
out=root/'Saved/LOK/hero_file_scope.json';out.write_text(json.dumps(report,indent=2))
print(json.dumps({'status':report['status'],'protected_count':len(protected),'changed':changed}))
