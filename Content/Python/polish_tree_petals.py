"""Apply only the requested tree particle appearance; preserve all other scene data."""
import json,traceback
from pathlib import Path
import unreal as u
import build_zone01 as b
import petal_clusters as petals

def main():
    assert b.LEVELS.load_level(b.ZONE)
    actors=b.ACTORS.get_all_level_actors()
    garden=next(a for a in actors if a.get_actor_label()=='LuminousGarden')
    assert b.OWNER in [str(t) for t in garden.tags]
    import polish_zone01 as hero
    import hero_geometry as geo
    hero.COL=u.load_asset(b.BASE+'/Materials/MPC/MPC_LOK_Global')
    bark=u.load_asset(b.BASE+'/Materials/Hero/M_Hero_BarkFlow')
    mesh=u.load_asset(b.BASE+'/Meshes/Hero/SM_HeroTrees_Curved')
    if b.EAL.get_metadata_tag(mesh,'LOK.TreeSilhouetteRevision')!='1':
        assert b.owned(bark) and b.owned(mesh)
        b.EAL.set_metadata_tag(bark,'LOK.HeroRevision','tree-update')
        bark=hero.material('M_Hero_BarkFlow',hero.bark,True)
        b.EAL.set_metadata_tag(mesh,'LOK.HeroRevision','tree-update')
        mesh=hero.mesh_asset('SM_HeroTrees_Curved',geo.trees()[0],bark)
        b.EAL.set_metadata_tag(mesh,'LOK.TreeSilhouetteRevision','1');b.save(mesh)
    report=petals.apply(garden)
    # A second application must yield the same instance distribution, with no duplication.
    again=petals.apply(garden)
    assert report==again
    report['repeat_application']='PASS'
    report['actor_count']=len(actors)
    report['tree_thickness']='trunk +22-24%, branches about +25%; taper and paths retained'
    if not b.LEVELS.save_current_level():raise RuntimeError('Could not save Zone01 petal changes')
    report['status']='SAVED'
    Path(u.Paths.project_saved_dir(),'LOK','tree_petals.json').write_text(json.dumps(report,indent=2))
    b.log('Tree petal appearance saved: '+str(report['instances'])+' instances')

if __name__ in ('__main__','<run_path>'):
    try:main()
    except Exception:u.log_error('[LOK][PETALS] '+traceback.format_exc())
    finally:u.SystemLibrary.quit_editor()
