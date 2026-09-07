"""Visual-only, owned Zone01 pass. Keeps native playback and Niagara assets intact."""
import json, math, random, traceback, hashlib
from pathlib import Path
import unreal as u
import build_zone01 as b
import hero_geometry as geo

COL=None
REV='hero-3'
PREVIEW_ONLY='-LOKHeroPreviewOnly' in u.SystemLibrary.get_command_line()
CAPTURE=PREVIEW_ONLY or '-LOKHeroCapture' in u.SystemLibrary.get_command_line()

def material(name,build,two_sided=False,translucent=False):
    mat,fresh=b.asset(b.BASE+'/Materials/Hero/'+name,u.Material,u.MaterialFactoryNew())
    if fresh or b.EAL.get_metadata_tag(mat,'LOK.HeroRevision')!=REV:
        b.MAT.delete_all_material_expressions(mat)
        mat.set_editor_property('two_sided',two_sided)
        mat.set_editor_property('used_with_instanced_static_meshes',True)
        if translucent:mat.set_editor_property('blend_mode',u.BlendMode.BLEND_TRANSLUCENT)
        build(mat)
        b.EAL.set_metadata_tag(mat,'LOK.HeroRevision',REV);b.finish_material(mat)
    return mat

def gain(mat,key):return b.multiply(mat,b.mpc_node(mat,COL,key),b.mpc_node(mat,COL,'TransitionAlpha'))
def time(mat):return b.mpc_node(mat,COL,'ExhibitTime')
def world(mat):return b.expression(mat,u.MaterialExpressionWorldPosition)
def uv(mat):return b.expression(mat,u.MaterialExpressionTextureCoordinate)
def out(mat,node,prop):b.output(mat,node,getattr(u.MaterialProperty,'MP_'+prop))
def fcustom(mat,code,inputs):return b.custom(mat,code,inputs,u.CustomMaterialOutputType.CMOT_FLOAT1)

def ceramic(mat):
    fine=b.expression(mat,u.MaterialExpressionNoise,scale=.23,levels=2,quality=1,output_min=0.,output_max=1.)
    base=b.custom(mat,r'''
        float2 p=float2(P.y/2450,(P.z-140)/2249);
        float ink=0;
        for(int k=0;k<3;k++) {
            float v=saturate((p.y-.15-k*.06)/(.72-k*.13));
            float bx=-.38+.19*k+(.2+.10*k)*v+.08*sin(v*5+k);
            float branch=exp(-pow((p.x-bx)/(.003+.009*(1-v)),2));
            ink=max(ink,branch*step(.14+k*.06,p.y)*step(p.y,.85-k*.08));
            for(int j=0;j<5;j++) {
                float t=.29+j*.11;
                float stemX=-.38+.19*k+(.2+.10*k)*t+.08*sin(t*5+k);
                float2 c=float2(stemX+sin(j*3.1+k)*.075,.15+k*.06+t*(.72-k*.13));
                float2 d=p-c;float a=atan2(d.y,d.x);
                float radius=.018+.007*cos(5*a+j);
                float blossom=1-smoothstep(radius-.004,radius+.003,length(d));
                ink=max(ink,blossom*.65);
            }
        }
        float reveal=.72+.18*sin(T*.065+p.y*4);
        ink*=reveal;
        float cloud=sin(p.x*19+sin(p.y*11)+T*.018)*sin(p.y*21+p.x*3);
        float3 ivory=float3(.68,.655,.59)*(1+cloud*.035+(N-.5)*.028);
        return lerp(ivory,float3(.05,.07,.11),saturate(ink*.78));
    ''',{'P':world(mat),'T':time(mat),'N':fine})
    out(mat,base,'BASE_COLOR')
    out(mat,fcustom(mat,'return .42+(N-.5)*.035;',{'N':fine}),'ROUGHNESS')
    out(mat,b.scalar(mat,.22),'SPECULAR')
    out(mat,b.custom(mat,'return normalize(float3((N-.5)*.009,(N-.5)*.007,1));',{'N':fine}),'NORMAL')
    fresnel=b.expression(mat,u.MaterialExpressionFresnel,exponent=5.,base_reflect_fraction=.0)
    out(mat,b.multiply(mat,fresnel,b.color(mat,(.18,.23,.32)),gain(mat,'MoonGlow')),'EMISSIVE_COLOR')

def bark(mat):
    out(mat,b.color(mat,(.038,.049,.065)),'BASE_COLOR');out(mat,b.scalar(mat,.74),'ROUGHNESS')
    flow=b.custom(mat,r'''float h=UV.y;float phase=frac(T*.075-h*.8);
        float pulse=exp(-pow((phase-.5)/.07,2));
        float vein=pow(saturate(.5+.5*cos(UV.x*6.283*5+sin(h*20))),22);
        return float3(.15,.34,.45)*vein*(.20+pulse*.85);''',{'UV':uv(mat),'T':time(mat)})
    out(mat,b.multiply(mat,flow,gain(mat,'ForestGlow')),'EMISSIVE_COLOR')

def roof(mat):
    out(mat,b.color(mat,(.016,.025,.041)),'BASE_COLOR');out(mat,b.scalar(mat,.40),'ROUGHNESS')
    out(mat,b.custom(mat,'float t=sin(UV.x*6.283*64);return normalize(float3(t*.065,0,1));',{'UV':uv(mat)}),'NORMAL')

def floor(mat):
    out(mat,b.color(mat,(.035,.052,.075)),'BASE_COLOR');out(mat,b.scalar(mat,.09),'ROUGHNESS');out(mat,b.scalar(mat,.72),'METALLIC')
    out(mat,b.custom(mat,'float a=sin(P.x*.013+P.y*.003+T*.12)*.018;float c=cos(P.y*.011+T*.10)*.018;return normalize(float3(a,c,1));',{'P':world(mat),'T':time(mat)}),'NORMAL')
    ripple=b.custom(mat,r'''float d=length((P.xy-float2(-600,0))*float2(1,.95));
        float phase=d*.022-T*.32;
        float ring=pow(saturate(.5+.5*cos(phase)),70)*exp(-d/1500);
        float axis=exp(-pow(abs(P.y)/14,2))*.025*smoothstep(-1800,1000,P.x);
        return float3(.12,.25,.37)*(ring*.48+axis);''',{'P':world(mat),'T':time(mat)})
    out(mat,b.multiply(mat,ripple,gain(mat,'GroundGlow'),b.mpc_node(mat,COL,'RippleStrength')),'EMISSIVE_COLOR')

def streak(mat):
    mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    mask=fcustom(mat,r'''float ends=pow(saturate(sin(UV.x*3.14159)),2);
        float edge=pow(saturate(1-abs(UV.y-.5)*2),3);
        float fade=pow(.5+.5*sin(T*.23+C.y*.013+C.x*.007),2);
        return ends*edge*fade*.23;''',{'UV':uv(mat),'T':time(mat),'C':b.expression(mat,u.MaterialExpressionObjectPositionWS)})
    out(mat,mask,'OPACITY');out(mat,b.multiply(mat,b.color(mat,(.10,.23,.34)),gain(mat,'ForestGlow')),'EMISSIVE_COLOR')

def sky(mat):
    mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    out(mat,b.custom(mat,'float t=saturate((P.z+1000)/15000);return lerp(float3(.008,.016,.035),float3(.0015,.003,.009),t);',{'P':world(mat)}),'EMISSIVE_COLOR')

def mist(mat):
    mat.set_editor_property('shading_model',u.MaterialShadingModel.MSM_UNLIT)
    mask=fcustom(mat,r'''float2 p=UV-.5;float edge=pow(saturate(1-dot(p*2,p*2)),2);
        float cloud=.5+.22*sin(P.y*.004+T*.04+sin(P.z*.03))+.16*cos(P.y*.009-T*.02);
        return edge*cloud*.18;''',{'UV':uv(mat),'P':world(mat),'T':time(mat)})
    out(mat,mask,'OPACITY');out(mat,b.color(mat,(.11,.17,.25)),'EMISSIVE_COLOR')

def light_function(mat):
    mat.set_editor_property('material_domain',u.MaterialDomain.MD_LIGHT_FUNCTION)
    out(mat,b.multiply(mat,gain(mat,'MoonGlow'),b.scalar(mat,1/.7)),'EMISSIVE_COLOR')

def flat(base,emission,rough=.6):
    def build(mat):
        out(mat,b.color(mat,base),'BASE_COLOR');out(mat,b.scalar(mat,rough),'ROUGHNESS')
        out(mat,b.multiply(mat,b.color(mat,emission),gain(mat,'ForestGlow')),'EMISSIVE_COLOR')
    return build

def mesh_asset(name,data,mat):
    path=b.BASE+'/Meshes/Hero/'+name
    if b.EAL.does_asset_exist(path):
        sm=u.load_asset(path)
        if not b.owned(sm):raise RuntimeError('Unowned '+path)
        if b.EAL.get_metadata_tag(sm,'LOK.HeroRevision')==REV:return sm
    else:sm=None
    buf=b.struct(u.GeometryScriptSimpleMeshBuffers,
      vertices=[u.Vector(*p) for p in data.vertices],normals=[u.Vector(*n) for n in data.normals()],
      uv0=[u.Vector2D(*p) for p in data.uv],triangles=[u.IntVector(*t) for t in data.triangles])
    dynamic=u.DynamicMesh();u.GeometryScript_MeshEdits.append_buffers_to_mesh(dynamic,buf)
    if sm is None:
        result=u.GeometryScript_NewAssetUtils.create_new_static_mesh_asset_from_mesh(dynamic,path,
          b.struct(u.GeometryScriptCreateNewStaticMeshAssetOptions,enable_recompute_tangents=True,enable_collision=False))
        sm=result[0]
    else:
        u.GeometryScript_AssetUtils.copy_mesh_to_static_mesh(dynamic,sm,
          b.struct(u.GeometryScriptCopyMeshToAssetOptions,enable_recompute_tangents=True),u.GeometryScriptMeshWriteLOD())
    if not sm:raise RuntimeError('Mesh creation failed '+path)
    sm.set_material(0,mat);b.EAL.set_metadata_tag(sm,'LOK.HeroRevision',REV);b.save(sm)
    return sm

def place(name,mesh,mat,p=(0,0,0),scale=(1,1,1)):
    actor=b.actor(name,u.StaticMeshActor,p)
    comp=actor.static_mesh_component;comp.set_mobility(u.ComponentMobility.MOVABLE)
    comp.set_static_mesh(mesh);comp.set_material(0,mat);actor.set_actor_scale3d(u.Vector(*scale))
    return actor

def hide(actor):
    actor.set_actor_hidden_in_game(True)
    for comp in actor.get_components_by_class(u.PrimitiveComponent):comp.set_visibility(False,True)

def sequence_signature(seq):
    rate=seq.get_display_rate()
    return {'end':seq.get_playback_end(),'rate':(rate.numerator,rate.denominator),
      'bindings':[(u.GuidLibrary.conv_guid_to_string(x.get_id()),str(x.get_name()),[t.get_class().get_name() for t in x.get_tracks()]) for x in seq.get_bindings()],
      'tracks':[t.get_class().get_name() for t in seq.get_tracks()]}

def particle_depth_material():
    # Preserve all Niagara emitters/modules; depth differences are sprite shading.
    mat=u.load_asset(b.BASE+'/Materials/Master/M_Particle_Soft')
    if not b.owned(mat):raise RuntimeError('Unowned particle material')
    if b.EAL.get_metadata_tag(mat,'LOK.HeroDepth')=='1':return
    b.MAT.delete_all_material_expressions(mat)
    pos=b.expression(mat,u.MaterialExpressionParticlePositionWS)
    pc=b.expression(mat,u.MaterialExpressionParticleColor)
    mask=fcustom(mat,r'''float fg=1-smoothstep(-300,300,P.x);float bg=smoothstep(1800,2400,P.x);
        float seed=frac(sin(dot(floor(P.xy*.1),float2(12.9898,78.233)))*43758.5453);
        float density=lerp(.78,.30,fg)*(1-bg*.20);
        return pow(saturate(1-length(UV-.5)*2),3)*step(seed,density)*lerp(.34,.58,fg)*(1-bg*.5);''',{'UV':uv(mat),'P':pos})
    alpha=b.expression(mat,u.MaterialExpressionMultiply);b.connect(mask,alpha,'A');b.connect(pc,alpha,'B','A')
    fade=b.expression(mat,u.MaterialExpressionDepthFade,fade_distance_default=45.)
    b.connect(b.multiply(mat,alpha,b.mpc_node(mat,COL,'ParticleIntensity')),fade,'Opacity');out(mat,fade,'OPACITY')
    shade=b.custom(mat,'float bg=smoothstep(1800,2400,P.x);return lerp(float3(.31,.40,.48),float3(.11,.17,.26),bg);',{'P':pos})
    out(mat,b.multiply(mat,shade,gain(mat,'ParticleIntensity')),'EMISSIVE_COLOR')
    drift=b.custom(mat,r'''float fg=1-smoothstep(-300,300,P.x);float bg=smoothstep(1800,2400,P.x);
        float size=lerp(1.,1.8,fg)*(1-bg*.35);float speed=lerp(.18,.34,fg)*(1-bg*.6);
        return (W-P)*(size-1)+float3(sin(T*speed+P.y*.013)*22,cos(T*speed*.7+P.x*.011)*29,sin(T*speed*1.2+P.z*.009)*18);''',{'P':pos,'W':world(mat),'T':time(mat)})
    out(mat,drift,'WORLD_POSITION_OFFSET')
    b.EAL.set_metadata_tag(mat,'LOK.HeroDepth','1')
    if PREVIEW_ONLY:b.MAT.recompile_material(mat)
    else:b.finish_material(mat)

def main():
    global COL
    if not b.LEVELS.load_level(b.ZONE):raise RuntimeError('Load failed')
    actors={a.get_actor_label():a for a in b.ACTORS.get_all_level_actors()}
    COL=u.load_asset(b.BASE+'/Materials/MPC/MPC_LOK_Global')
    seq=u.load_asset(b.BASE+'/Sequences/Zone01/LS_Zone01_Opening');before=sequence_signature(seq)
    mats={'jar':material('M_Hero_Ceramic',ceramic,True),'bark':material('M_Hero_BarkFlow',bark,True),
      'roof':material('M_Hero_RoofTiles',roof,True),'floor':material('M_Hero_WaterFloor',floor),
      'line':material('M_Hero_SoftRain',streak,True,True),'sky':material('M_Hero_NavyBackdrop',sky,True),
      'blue':material('M_Hero_BlossomPearl',flat((.10,.15,.18),(.16,.31,.39))),
      'violet':material('M_Hero_BlossomViolet',flat((.09,.07,.11),(.22,.16,.29))),
      'stone':material('M_Hero_Stone',flat((.033,.045,.060),(.002,.003,.005))),
      'gold':material('M_Hero_IvoryTrim',flat((.2,.15,.085),(.24,.18,.10))),
      'wood':material('M_Hero_PavilionWood',flat((.052,.029,.018),(.013,.009,.006))),
      'mist':material('M_Hero_LowMist',mist,True,True),
      'keyfade':material('M_Hero_MoonLightFunction',light_function)}
    particle_depth_material()
    jar=mesh_asset('SM_MoonJar_HandThrown',geo.jar(),mats['jar'])
    tree_geometry,blossoms=geo.trees();trees=mesh_asset('SM_HeroTrees_Curved',tree_geometry,mats['bark'])
    roofmesh=mesh_asset('SM_Pavilion_CurvedRoof',geo.pavilion_roof(),mats['roof'])
    wallmesh=mesh_asset('SM_Garden_CurvedRoofline',geo.curved_wall(),mats['roof'])
    rockmesh=mesh_asset('SM_Garden_WeatheredStone',geo.rock(),mats['stone'])
    moon=actors['Moon'];moon.set_actor_location(u.Vector(3600,0,140),False,False)
    comp=moon.get_component_by_class(u.StaticMeshComponent);comp.set_static_mesh(jar);comp.set_material(0,mats['jar'])
    comp.set_editor_property('relative_scale3d',u.Vector(1,1,1));comp.set_editor_property('relative_location',u.Vector(0,0,0))
    for name in ('MoonJar_Neck','MoonJar_Opening','MoonJar_Rim','Zone01_Root'):hide(actors[name])
    garden=actors['LuminousGarden']
    for c in garden.get_components_by_class(u.InstancedStaticMeshComponent):
        name=c.get_name()
        if name.startswith(('GardenWood','LightRain','GardenRocks')):c.set_visibility(False,True)
    import petal_clusters
    petal_report=petal_clusters.apply(garden)
    place('HeroTrees',trees,mats['bark'])
    place('HeroPavilion_Roof',roofmesh,mats['roof'],(2250,1640,0))
    place('Hero_BackRoofline',wallmesh,mats['roof'])
    # Preserve the existing Hanok actor; strengthen its proportions and material.
    hanok=actors['HanokSilhouette'];hanok.set_actor_location(u.Vector(2250,1640,0),False,False)
    hanok.set_actor_rotation(u.Rotator(pitch=0,yaw=0,roll=0),False);hanok.set_actor_scale3d(u.Vector(1.65,1.32,1.65))
    for c in hanok.get_components_by_class(u.StaticMeshComponent):
        c.set_material(0,mats['wood'])
        if c.get_name().startswith('Roof'):c.set_visibility(False,True)
    cube=u.load_asset('/Engine/BasicShapes/Cube');cylinder=u.load_asset('/Engine/BasicShapes/Cylinder')
    for side in (-1,1):
        for j in range(9):
            place('Hero_Rock_%s_%s'%(side,j),rockmesh,mats['stone'],(-500+j*630,side*(1700+(j%3)*90),80+(j%3)*35),(3.5+(j%3),2.1+(j%2),2.4+(j%3)*.7))
        for j in range(3):
            place('Hero_Mountain_%s_%s'%(side,j),rockmesh,mats['stone'],(6500+j*950,side*(2450+j*420),560+j*150),(11+j*2,6+j,15+j*4))
    for row in (-1,1):
        place('PavilionUpperBeam_%s'%row,cube,mats['wood'],(2250+row*290,1640,645),(.38,14.8,.44))
        for j in range(5):
            place('PavilionColumn_%s_%s'%(row,j),cylinder,mats['wood'],(2250+row*290,1640-550+j*275,330),(.28,.28,6.6))
            place('PavilionIvory_%s_%s'%(row,j),cube,mats['gold'],(2250+row*292-16,1640-550+j*275,330),(.018,.08,6.1))
            place('PavilionBracket_%s_%s'%(row,j),cube,mats['wood'],(2250+row*290,1640-550+j*275,666),(.85,.65,.25))
    for j in range(5):
        place('PavilionCrossBeam_%s'%j,cube,mats['wood'],(2250,1640-550+j*275,651),(6.0,.3,.28))
    for side in (-1,1):
        for j in range(12):
            y=side*(770+j*290);z=350+85*math.cos(j/12*math.tau*2.2)+j*7
            place('BackdropWall_%s_%02d'%(side,j),cube,mats['stone'],(4880,y,z/2),(.6,2.95,z/100))
    ground=actors['Ground'];ground.static_mesh_component.set_material(0,mats['floor'])
    for i in range(7):
        a=actors['GardenStep_%02d'%i];a.set_actor_location(u.Vector(2050+i*100,0,10+i*19),False,False)
        a.set_actor_scale3d(u.Vector(1.10,10.2-i*.35,.2));a.static_mesh_component.set_material(0,mats['stone'])
        place('StepIvory_%02d'%i,cube,mats['gold'],(1996+i*100,0,19+i*19),(.025,10.2-i*.35,.022))
    backdrop=place('Hero_NavyCyclorama',u.load_asset('/Engine/BasicShapes/Sphere'),mats['sky'],(0,0,0),(600,600,600))
    backdrop.static_mesh_component.set_editor_property('cast_shadow',False)
    plane=u.load_asset('/Engine/BasicShapes/Plane')
    for i in range(3):
        a=place('Hero_LowMist_%s'%i,plane,mats['mist'],(800+i*1700,0,105+i*20),(3.0+i*.7,60,1))
        a.set_actor_rotation(u.Rotator(pitch=90,yaw=0,roll=0),False)
        a.static_mesh_component.set_editor_property('cast_shadow',False)
    rain_rng=random.Random(401)
    for side in (-1,1):
        for j in range(6):
            pos=(2800+j*520+rain_rng.uniform(-180,180),side*(1850+j*110+rain_rng.uniform(-100,100)),rain_rng.uniform(1050,1700))
            a=place('Hero_SoftRain_%s_%s'%(side,j),plane,mats['line'],pos,(rain_rng.uniform(9,22),rain_rng.uniform(.035,.10),1))
            a.set_actor_rotation(u.Rotator(pitch=90,yaw=0,roll=0),False)
    camera=actors['CAM_Zone01_Main'];camera.get_cine_camera_component().set_editor_property('current_focal_length',28.)
    camera.set_actor_location(u.Vector(-2550,0,185),False,False)
    camera.set_actor_rotation(u.Rotator(pitch=7.6,yaw=0,roll=0),False)
    # Only camera transform key values and fog/light values are visual changes.
    for binding in seq.get_bindings():
        for track in binding.get_tracks():
            if isinstance(track,u.MovieScene3DTransformTrack):
                for section in track.get_sections():
                    for index,channel in enumerate(section.get_all_channels()):
                        for key in channel.get_keys():
                            t=key.get_time().frame_number.value/30
                            values=(-2800+t*5,0,185,0,7.6,0,1,1,1)
                            key.set_value(float(values[index]))
                            key.set_interpolation_mode(u.RichCurveInterpMode.RCIM_LINEAR)
            elif isinstance(track,u.MovieSceneFloatTrack) and str(track.get_property_name())=='FogDensity':
                for section in track.get_sections():
                    for channel in section.get_all_channels():
                        for key in channel.get_keys():
                            t=key.get_time().frame_number.value/30
                            key.set_value(.0032 if t<25 else .0048 if t<35 else .0144)
    after=sequence_signature(seq)
    if after!=before:
        Path(u.Paths.project_saved_dir(),'LOK','hero_structure_difference.json').write_text(json.dumps({'before':before,'after':after},indent=2))
        raise RuntimeError('Functional sequence structure changed')
    fog=actors['MoonlightFog'].get_component_by_class(u.ExponentialHeightFogComponent)
    fog.set_editor_property('fog_inscattering_luminance',u.LinearColor(.025,.047,.088,1))
    fog.set_editor_property('fog_height_falloff',.13)
    fog.set_editor_property('volumetric_fog_scattering_distribution',.25)
    for side in (-1,1):
        light=actors['Forest_Accent_'+str(side)].get_component_by_class(u.PointLightComponent)
        light.set_intensity(12);light.set_light_color(u.LinearColor(.30,.46,.64,1))
    for name,p,target,intensity,color,width,height in [
      ('Hero_JarKey',(800,-1700,2800),(3600,0,1400),950,(.86,.90,1),1800,1800),
      ('Hero_JarFill',(2600,2000,1900),(3600,0,1300),320,(.54,.66,.90),1700,1700),
      ('Hero_PavilionWarm',(1800,1640,620),(2550,1640,240),45,(1,.77,.46),1000,200)]:
        rot=u.MathLibrary.find_look_at_rotation(u.Vector(*p),u.Vector(*target))
        a=b.actor(name,u.RectLight,p,(rot.pitch,rot.yaw,rot.roll));c=a.get_component_by_class(u.RectLightComponent)
        c.set_mobility(u.ComponentMobility.MOVABLE);c.set_intensity(intensity);c.set_light_color(u.LinearColor(*color,1))
        c.set_editor_property('source_width',width);c.set_editor_property('source_height',height);c.set_editor_property('attenuation_radius',6000)
        if name in ('Hero_JarKey','Hero_JarFill'):c.set_light_function_material(mats['keyfade'])
    actors['NS_Zone01_MoonHalo'].set_actor_location(u.Vector(3600,0,1350),False,False)
    actors['NS_Zone01_FogParticles'].set_actor_location(u.Vector(2600,0,115),False,False)
    if not PREVIEW_ONLY:
        b.save(seq)
        if not b.LEVELS.save_current_level():raise RuntimeError('Hero map save failed; another editor may hold the package')
    report={'status':'IN_MEMORY_PREVIEW' if PREVIEW_ONLY else 'BUILT_VISUAL_REVIEW_PENDING','revision':REV,'sequence_structure_unchanged':True,
      'hero_trees':6,'blossoms':petal_report['instances'],'soft_light_lines':12,'focal_length':28,
      'jar_triangles':len(geo.jar().triangles),'map':b.ZONE}
    Path(u.Paths.project_saved_dir(),'LOK','hero_build.json').write_text(json.dumps(report,indent=2))
    b.log('Hero preview prepared' if PREVIEW_ONLY else 'Hero visual pass saved. Render review required.')
    if CAPTURE:__import__('preview_hero')

if __name__=='<run_path>' or __name__=='__main__':
    try:main()
    except Exception:
        u.log_error('[LOK][HERO] '+traceback.format_exc());u.SystemLibrary.quit_editor()
    else:
        if not CAPTURE:u.SystemLibrary.quit_editor()
