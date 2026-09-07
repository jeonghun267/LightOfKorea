"""Repeat only the visual pass; assert stable actor IDs and sequence structure."""
import json,traceback
from pathlib import Path
import unreal as u
import polish_zone01 as p
import build_zone01 as b

def signature():
    actors=b.ACTORS.get_all_level_actors()
    ids=sorted(str(t) for a in actors for t in a.tags if str(t).startswith('LOK.ID.'))
    return {'actor_ids':ids,'unique':len(ids)==len(set(ids)),
      'sequence':p.sequence_signature(u.load_asset(b.BASE+'/Sequences/Zone01/LS_Zone01_Opening'))}

try:
    p.main();first=signature()
    p.main();second=signature()
    report={'status':'PASS' if first==second and second['unique'] else 'FAIL',
      'runs':2,'actor_count':len(second['actor_ids']),'same_actor_ids_and_bindings':first==second}
    Path(u.Paths.project_saved_dir(),'LOK','hero_idempotency.json').write_text(json.dumps(report,indent=2))
    if report['status']!='PASS':raise RuntimeError('Hero repeat changed structure')
    import validate_zone01
    validate_zone01.main()
except Exception:u.log_error('[LOK][HERO CHECK] '+traceback.format_exc())
finally:u.SystemLibrary.quit_editor()
