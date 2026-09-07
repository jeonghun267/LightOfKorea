"""Detailed glaze/ink surface on the existing moon jar, with staged reveal intact."""
import json, traceback
from pathlib import Path
import unreal as u
import build_zone01 as b

REV='glaze-3'

def main():
    root=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
    source=root/'Content/LOK/Textures/Source/T_MoonJar_GlazeInk_Atlas.png'
    destination=b.BASE+'/Textures/T_MoonJar_GlazeInk_Atlas'
    if not b.EAL.does_asset_exist(destination):
        task=b.struct(u.AssetImportTask,filename=str(source),destination_path=b.BASE+'/Textures',
          destination_name='T_MoonJar_GlazeInk_Atlas',automated=True,save=False,replace_existing=False)
        b.TOOLS.import_asset_tasks([task])
        tex=u.load_asset(destination)
        if not tex:raise RuntimeError('Texture import failed')
        b.mark(tex)
        tex.set_editor_property('srgb',False)
        tex.set_editor_property('power_of_two_mode',u.TexturePowerOfTwoSetting.STRETCH_TO_POWER_OF_TWO)
        tex.set_editor_property('address_x',u.TextureAddress.TA_CLAMP)
        tex.set_editor_property('address_y',u.TextureAddress.TA_CLAMP)
        b.save(tex)
    else:
        tex=u.load_asset(destination)
        if not b.owned(tex):raise RuntimeError('Unowned texture')
    mat=u.load_asset(b.BASE+'/Materials/Hero/M_Hero_Ceramic')
    if not b.owned(mat):raise RuntimeError('Unowned jar material')
    if b.EAL.get_metadata_tag(mat,'LOK.GlazeRevision')==REV:return
    collection=u.load_asset(b.BASE+'/Materials/MPC/MPC_LOK_Global')
    if 'MoonPatternReveal' not in [str(p.get_editor_property('parameter_name')) for p in collection.get_editor_property('scalar_parameters')]:
        raise RuntimeError('Run timing polish first')
    b.MAT.delete_all_material_expressions(mat)
    mat.set_editor_property('tangent_space_normal',False)
    P=b.expression(mat,u.MaterialExpressionWorldPosition)
    texobj=b.expression(mat,u.MaterialExpressionTextureObject,texture=tex)
    T=b.mpc_node(mat,collection,'ExhibitTime')
    pattern=b.mpc_node(mat,collection,'MoonPatternReveal')
    surface=b.mpc_node(mat,collection,'MoonSurfaceReveal')
    inputs={'P':P,'Atlas':texobj,'T':T,'Pattern':pattern,'Surface':surface}
    base=b.custom(mat,r'''
      float2 p=float2(P.y/2700.+.5,1-(P.z-140.)/2300.);
      float2 g=frac(p*1.7+float2(.13,.27));
      float detail=Texture2DSample(Atlas,AtlasSampler,float2(.008+g.x*.48,.012+g.y*.976)).r;
      float broad=Texture2DSample(Atlas,AtlasSampler,float2(.008+saturate(p.x)*.48,.012+saturate(p.y)*.976)).r;
      float glaze=saturate((detail-.55)*2.3);
      float3 ivory=lerp(float3(.27,.31,.38),float3(.82,.80,.745),glaze);
      ivory*=.94+(broad-.65)*.20;
      float2 inkUV=float2(.51+saturate(p.x)*.485,saturate(p.y));
      inkUV.y+=sin(T*.065+p.x*3.)*.0025;
      float paint=1-Texture2DSample(Atlas,AtlasSampler,inkUV).r;
      float edge=smoothstep(0.,.075,p.x)*(1-smoothstep(.925,1.,p.x))*smoothstep(0.,.08,p.y)*(1-smoothstep(.94,1.,p.y));
      float sweep=smoothstep(p.y-.12,p.y+.12,Pattern*1.25);
      float ink=saturate(pow(max(0.,paint),.52)*edge*Pattern*sweep*1.25);
      float3 color=lerp(ivory,float3(.045,.070,.115),ink);
      return color*lerp(.018,1.,Surface);
    ''',inputs)
    b.output(mat,base,u.MaterialProperty.MP_BASE_COLOR)
    rough=b.custom(mat,r'''
      float2 g=frac(float2(P.y/2700.+.5,1-(P.z-140.)/2300.)*1.7+float2(.13,.27));
      float h=Texture2DSample(Atlas,AtlasSampler,float2(.008+g.x*.48,.012+g.y*.976)).r;
      return clamp(.43+(1-h)*.19,.43,.58);
    ''',{'P':P,'Atlas':texobj},u.CustomMaterialOutputType.CMOT_FLOAT1)
    b.output(mat,rough,u.MaterialProperty.MP_ROUGHNESS)
    b.output(mat,b.scalar(mat,.15),u.MaterialProperty.MP_SPECULAR)
    normal=b.custom(mat,r'''
      float2 g=frac(float2(P.y/2700.+.5,1-(P.z-140.)/2300.)*1.7+float2(.13,.27));
      float2 q=float2(.008+g.x*.48,.012+g.y*.976);
      float l=Texture2DSample(Atlas,AtlasSampler,q-float2(.00055,0)).r;
      float r=Texture2DSample(Atlas,AtlasSampler,q+float2(.00055,0)).r;
      float a=Texture2DSample(Atlas,AtlasSampler,q-float2(0,.0011)).r;
      float d=Texture2DSample(Atlas,AtlasSampler,q+float2(0,.0011)).r;
      float3 n=normalize(float3((P.x-3600.)/1220.,P.y/1220.,(P.z-1260.)/1170.));
      return normalize(n+float3(0,(l-r)*.035,(a-d)*.035));
    ''',{'P':P,'Atlas':texobj})
    b.output(mat,normal,u.MaterialProperty.MP_NORMAL)
    # Explicit outward normal makes the early rim independent of two-sided mesh normals.
    rim=b.custom(mat,r'''
      float3 n=normalize(float3((P.x-3600.)/1220.,P.y/1220.,(P.z-1260.)/1170.));
      return pow(1-saturate(abs(dot(n,normalize(V)))),5.5);
    ''',{'P':P,'V':b.expression(mat,u.MaterialExpressionCameraVectorWS)},u.CustomMaterialOutputType.CMOT_FLOAT1)
    b.output(mat,b.multiply(mat,rim,b.color(mat,(.45,.55,.70)),b.mpc_node(mat,collection,'MoonGlow'),
      b.mpc_node(mat,collection,'TransitionAlpha')),u.MaterialProperty.MP_EMISSIVE_COLOR)
    b.EAL.set_metadata_tag(mat,'LOK.GlazeRevision',REV)
    b.EAL.set_metadata_tag(mat,'LOK.TimingRevision','timing-1')
    b.finish_material(mat)
    (root/'Saved/LOK/jar_surface.json').write_text(json.dumps({'status':'SAVED','revision':REV,
      'texture':destination,'source':str(source.relative_to(root)),
      'base_color_roughness_micro_normal_separate':True,'full_surface_emission':False,'mesh_unchanged':True},indent=2))
    b.log('Layered glaze/ink surface saved; GPU render review required')

if __name__ in ('__main__','<run_path>'):
    try:main()
    except Exception:
        error=traceback.format_exc();u.log_error('[LOK][JAR SURFACE] '+error)
        Path(u.Paths.project_saved_dir(),'LOK','jar_surface.json').write_text(json.dumps({'status':'FAIL','error':error},indent=2))
    finally:u.SystemLibrary.quit_editor()
