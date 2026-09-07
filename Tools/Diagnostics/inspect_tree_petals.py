import json
from pathlib import Path
import unreal as u
u.get_editor_subsystem(u.LevelEditorSubsystem).load_level('/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight')
a=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='LuminousGarden')
r=[]
for c in a.get_components_by_class(u.InstancedStaticMeshComponent):
    if 'Blossoms' not in c.get_name():continue
    r.append({'name':c.get_name(),'count':c.get_instance_count(),'mesh':c.static_mesh.get_path_name(),
      'material':c.get_material(0).get_path_name(),'seed':c.get_editor_property('instancing_random_seed'),
      'first':str(c.get_instance_transform(0))})
Path(u.Paths.project_saved_dir(),'LOK','petal_reload_probe.json').write_text(json.dumps(r,indent=2))
u.SystemLibrary.quit_editor()
