import unreal as u
import json
from pathlib import Path
r={}
for cls,names in {
 'GeometryScript_MeshEdits':['append_buffers_to_mesh'],
 'GeometryScript_AssetUtils':['copy_mesh_to_static_mesh'],
 'GeometryScript_MeshNormals':['set_per_vertex_normals','recompute_normals'],
 'GeometryScriptSimpleMeshBuffers':[],
 'GeometryScriptCopyMeshToAssetOptions':[],
 'StaticMeshFactoryNew':[],
}.items():
    obj=getattr(u,cls,None)
    r[cls]=str(obj.__doc__) if obj else 'MISSING'
    if obj:
        for n in names:r[cls+'.'+n]=str(getattr(obj,n,None).__doc__)
Path(u.Paths.project_saved_dir(),'LOK','hero_api.json').write_text(json.dumps(r,indent=2))
u.SystemLibrary.quit_editor()
