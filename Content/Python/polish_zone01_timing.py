"""Polish timing only: preserve meshes, instances, camera and Niagara simulation.

Existing ExhibitTime drives every spatial response; no tick/event controller added.
Run in a dedicated editor via Tools/run_hero_task.py after closing the main editor.
"""
import json, math, traceback
from pathlib import Path
import unreal as u
import build_zone01 as b
import polish_zone01 as hero

REV='timing-1'
COL=None
CURVES={
 'TransitionAlpha':[(0,0),(2,1),(60,1)],
 'MoonGlow':[(0,0),(1,0),(5,.70),(12,.60),(20,.70),(60,.70)],
 'MoonSurfaceReveal':[(0,0),(5,0),(7,.16),(10,.74),(12,1),(60,1)],
 'MoonPatternReveal':[(0,0),(10,0),(12,.15),(15,1),(60,1)],
 'MoonHaloReveal':[(0,0),(15,0),(17,.35),(19,1),(60,1)],
 'ForestGlow':[(0,.0),(22,0),(26,.46),(38,.46),(46,.46),(55,.43),(60,.43)],
 'GroundGlow':[(0,0),(21,0),(22,.15),(24,.85),(39,.72),(45,.72),(48,.82),(60,.72)],
 'ParticleIntensity':[(0,0),(15,0),(19,.70),(24,.72),(38,.62),(60,.58)],
 'ExhibitTime':[(0,0),(60,60)],
 'ScenePhase':[(0,0),(60,1)],
 'RippleStartTime':[(0,22),(60,22)],
 'RippleStrength':[(0,0),(22,0),(23,1),(40,.85),(45,.85),(47,1),(60,.85)]}

# Centimetres / seconds. The same wave reaches each surface and particle.
WAVE=r'''
 float d=length(P.xy-float2(-600,0));
 float arrival=S+d/440.;
 float on=smoothstep(arrival,arrival+2.2,T);
 float hit=exp(-pow((T-arrival-.4)/.75,2));
 float echo=.35*exp(-pow((T-(46.+d/440.)-.4)/.9,2));
'''

def scalar(mat,name):return b.mpc_node(mat,COL,name)
def custom1(mat,code,inputs):return b.custom(mat,code,inputs,u.CustomMaterialOutputType.CMOT_FLOAT1)
def position(mat):return b.expression(mat,u.MaterialExpressionWorldPosition)
def spatial(mat,pos=None,amount=1.):
    return custom1(mat,WAVE+'return (on*.82+hit*.18+echo*.18)*'+str(float(amount))+';',
      {'P':pos or position(mat),'T':scalar(mat,'ExhibitTime'),'S':scalar(mat,'RippleStartTime')})

def wrap(mat,prop,factor):
    prop=getattr(u.MaterialProperty,'MP_'+prop)
    previous=b.MAT.get_material_property_input_node(mat,prop)
    if previous is None:raise RuntimeError('Missing material input '+mat.get_name()+str(prop))
    pin=b.MAT.get_material_property_input_node_output_name(mat,prop)
    node=b.expression(mat,u.MaterialExpressionMultiply)
    b.connect(previous,node,'A',pin);b.connect(factor,node,'B');b.output(mat,node,prop)

def edit(name,fn,folder='Hero'):
    mat=u.load_asset(b.BASE+'/Materials/'+folder+'/'+name)
    if not mat or not b.owned(mat):raise RuntimeError('Unowned/missing '+name)
    if b.EAL.get_metadata_tag(mat,'LOK.TimingRevision')!=REV:
        fn(mat);b.EAL.set_metadata_tag(mat,'LOK.TimingRevision',REV);b.finish_material(mat)
    return mat

def ceramic(mat):
    base=b.MAT.get_material_property_input_node(mat,u.MaterialProperty.MP_BASE_COLOR)
    code=base.get_editor_property('code') if isinstance(base,u.MaterialExpressionCustom) else ''
    if 'ink*=reveal;' not in code:
        raise RuntimeError('Unexpected ceramic graph; refusing to replace surface detail')
    old_inputs=list(base.get_editor_property('inputs'))
    old_nodes=b.MAT.get_inputs_for_material_expression(mat,base)
    base.set_editor_property('inputs',old_inputs+[b.struct(u.CustomInput,input_name='Pattern')])
    base.set_editor_property('code',code.replace('ink*=reveal;','ink*=reveal*Pattern;'))
    for item,node in zip(old_inputs,old_nodes):
        if node:b.connect(node,base,str(item.get_editor_property('input_name')))
    b.connect(scalar(mat,'MoonPatternReveal'),base,'Pattern')
    wrap(mat,'BASE_COLOR',custom1(mat,'return lerp(.018,1.,A);',{'A':scalar(mat,'MoonSurfaceReveal')}))

def keylight(mat):
    b.output(mat,b.multiply(mat,scalar(mat,'MoonSurfaceReveal'),scalar(mat,'TransitionAlpha')),u.MaterialProperty.MP_EMISSIVE_COLOR)

def floor(mat):
    # Keep the existing reflective surface/normal; replace only its decorative ring timing.
    ring=b.custom(mat,r'''
      float d=length(P.xy-float2(-600,0));
      float age=T-S;
      float front=age*440.;
      float a=exp(-pow((d-front)/55.,2));
      float trail=.30*exp(-pow((d-front+170.)/48.,2));
      float envelope=smoothstep(0.,1.1,age)*(1-smoothstep(6600.,7900.,front));
      float f2=(T-46.)*440.;
      float second=.36*exp(-pow((d-f2)/65.,2))*smoothstep(46.,47.1,T);
      float axis=exp(-pow(P.y/19.,2))*.021*smoothstep(23.,32.,T);
      return float3(.50,.66,.80)*((a+trail)*envelope+second+axis);
    ''',{'P':position(mat),'T':scalar(mat,'ExhibitTime'),'S':scalar(mat,'RippleStartTime')})
    b.output(mat,b.multiply(mat,ring,scalar(mat,'GroundGlow'),scalar(mat,'RippleStrength'),scalar(mat,'TransitionAlpha')),u.MaterialProperty.MP_EMISSIVE_COLOR)

def petals(mat):
    # World position, not object position: the two ISM components span all six trees.
    wrap(mat,'OPACITY',spatial(mat))

def lanterns(mat):
    gate=custom1(mat,WAVE+'return .015+.18*Surface+on*.42+hit*.06+echo*.04;',
      {'P':position(mat),'T':scalar(mat,'ExhibitTime'),'S':scalar(mat,'RippleStartTime'),'Surface':scalar(mat,'MoonSurfaceReveal')})
    wrap(mat,'EMISSIVE_COLOR',gate)

def particles(mat):
    pos=b.expression(mat,u.MaterialExpressionParticlePositionWS)
    actor=b.expression(mat,u.MaterialExpressionActorPositionWS)
    gate=custom1(mat,WAVE+r'''
      float halo=step(3000.,A.x)*step(800.,A.z);
      float nearby=(1-smoothstep(1200.,3300.,length(P.xy-float2(3600,0))))*smoothstep(19.,22.,T)*.20;
      return lerp(max(nearby,on*.72+hit*.12+echo*.10),H,halo);
    ''',{'P':pos,'A':actor,'T':scalar(mat,'ExhibitTime'),'S':scalar(mat,'RippleStartTime'),'H':scalar(mat,'MoonHaloReveal')})
    wrap(mat,'OPACITY',gate)

def collection():
    params=list(COL.get_editor_property('scalar_parameters'))
    names={str(p.get_editor_property('parameter_name')) for p in params}
    for name in ('MoonSurfaceReveal','MoonPatternReveal','MoonHaloReveal'):
        if name not in names:params.append(b.struct(u.CollectionScalarParameter,parameter_name=name,default_value=1.))
    if len(params)!=len(names):
        COL.set_editor_property('scalar_parameters',params);b.save(COL)

def light_keys(seq,actor,name,keys):
    binding=next((v for v in seq.get_bindings() if str(v.get_name())=='LOK_Timing_'+name),None)
    if binding is None:
        binding=seq.add_possessable(actor.get_component_by_class(u.LightComponent))
        binding.set_name('LOK_Timing_'+name)
        track=binding.add_track(u.MovieSceneFloatTrack);track.set_property_name_and_path('Intensity','Intensity')
        track.add_section().set_range(0,1800)
    channel=binding.get_tracks()[0].get_sections()[0].get_all_channels()[0]
    for key in list(channel.get_keys()):channel.remove_key(key)
    for t,v in keys:channel.add_key(u.FrameNumber(round(t*30)),float(v),interpolation=u.MovieSceneKeyInterpolation.LINEAR)

def sequence(seq,actors):
    sections=[s for t in seq.get_tracks() if isinstance(t,u.MovieSceneMaterialParameterCollectionTrack) for s in t.get_sections()]
    if len(sections)!=1:raise RuntimeError('Expected one existing MPC section')
    sec=sections[0]
    sec.set_completion_mode(u.MovieSceneCompletionMode.KEEP_STATE)
    # Monotonic piecewise-linear keys avoid automatic tangent brightness overshoot.
    for name,keys in CURVES.items():
        sec.remove_scalar_parameter(name)
        for t,v in keys:sec.add_scalar_parameter_key(name,u.FrameNumber(round(t*30)),float(v),u.MovieSceneKeyInterpolation.LINEAR)
    for bind in seq.get_bindings():
        for track in bind.get_tracks():
            if isinstance(track,u.MovieSceneFloatTrack) and str(track.get_property_name())=='Intensity':
                # Existing directional and Hanok rim bindings retain their IDs/tracks.
                if str(bind.get_name()).startswith('LOK_Timing_'):continue
                for section in track.get_sections():
                    for ch in section.get_all_channels():
                        old=[k.get_value() for k in ch.get_keys()]
                        if max(old,default=0)<=1:
                            keys=[(0,0),(5,0),(8,.08),(12,.65),(60,.65)]
                        else:
                            arrival=22+math.hypot(1650+600,1100)/440
                            keys=[(0,0),(arrival,0),(arrival+1,75),(arrival+3,58),(60,58)]
                        for k in list(ch.get_keys()):ch.remove_key(k)
                        for t,v in keys:ch.add_key(u.FrameNumber(round(t*30)),float(v),interpolation=u.MovieSceneKeyInterpolation.LINEAR)
            if isinstance(track,u.MovieSceneNiagaraSystemTrack):
                name=str(bind.get_name())
                start=15 if 'MoonHalo' in name else 19 if 'AmbientParticles' in name else 22 if 'FloorLight' in name else 24
                for section in track.get_sections():section.set_range(start*30,1800)
    # The warm pavilion and side fill now follow the same travelling floor wave.
    for name,level in [('Hero_PavilionWarm',32.),('Forest_Accent_-1',7.),('Forest_Accent_1',7.)]:
        p=actors[name].get_actor_location();arrival=22+math.hypot(p.x+600,p.y)/440
        echo=46+math.hypot(p.x+600,p.y)/440
        light_keys(seq,actors[name],name,[(0,0),(arrival,0),(arrival+1,level),(arrival+3,level*.80),
          (echo,level*.80),(echo+1,level*.92),(echo+3,level*.80),(60,level*.80)])
    # Large 18m rect sources require actual illumination once full-face rim leakage is removed.
    # Sequencer explicitly fades these lights; no full-face emissive is needed.
    for name,level in [('Hero_JarKey',1800.),('Hero_JarFill',1100.)]:
        light_keys(seq,actors[name],name,[(0,0),(5,0),(8,level*.32),(12,level),(60,level)])
    # Preserve the final hero state after native autoplay finishes, rather than restoring
    # the old MPC defaults (ExhibitTime=50, ForestGlow=.65) and pre-sequence light levels.
    for track in list(seq.get_tracks())+[t for binding in seq.get_bindings() for t in binding.get_tracks()]:
        if isinstance(track,(u.MovieSceneFloatTrack,u.MovieScene3DTransformTrack,u.MovieSceneCameraCutTrack)):
            for section in track.get_sections():section.set_completion_mode(u.MovieSceneCompletionMode.KEEP_STATE)
    b.EAL.set_metadata_tag(seq,'LOK.TimingRevision',REV);b.save(seq)

def snapshot(seq):
    camera=[]
    for binding in seq.get_bindings():
        for track in binding.get_tracks():
            if isinstance(track,u.MovieScene3DTransformTrack):
                camera.append([[[(k.get_time().frame_number.value,k.get_value()) for k in ch.get_keys()]
                  for ch in s.get_all_channels()] for s in track.get_sections()])
    actors=[]
    for a in b.ACTORS.get_all_level_actors():
        p=a.get_actor_location();r=a.get_actor_rotation();s=a.get_actor_scale3d()
        actors.append((a.get_actor_label(),p.x,p.y,p.z,r.pitch,r.yaw,r.roll,s.x,s.y,s.z))
    return {'camera_keys':camera,'actors':sorted(actors)}

def main():
    global COL
    if not b.LEVELS.load_level(b.ZONE):raise RuntimeError('Map load failed')
    seq=u.load_asset(b.BASE+'/Sequences/Zone01/LS_Zone01_Opening')
    before=snapshot(seq)
    actors={a.get_actor_label():a for a in b.ACTORS.get_all_level_actors()}
    COL=u.load_asset(b.BASE+'/Materials/MPC/MPC_LOK_Global');collection()
    edit('M_Hero_Ceramic',ceramic);edit('M_Hero_MoonLightFunction',keylight)
    edit('M_Hero_WaterFloor',floor)
    for name in ('M_Hero_BarkFlow','M_Hero_SoftRain','M_Hero_IvoryTrim','M_Hero_PavilionWood'):
        edit(name,lambda m:wrap(m,'EMISSIVE_COLOR',spatial(m)))
    edit('M_Tree_SoftPetal',petals);edit('M_Particle_Soft',particles,'Master')
    edit('M_Lantern_Warm',lanterns,'Master')
    # Isolate the existing jar lights so increased illumination cannot bleach the exhibition.
    actors['Moon'].get_component_by_class(u.StaticMeshComponent).set_lighting_channels(True,True,False)
    for name in ('Hero_JarKey','Hero_JarFill'):
        light=actors[name].get_component_by_class(u.RectLightComponent)
        light.set_lighting_channels(False,True,False)
        light.set_volumetric_scattering_intensity(0.)
        light.set_indirect_lighting_intensity(.05)
        light.set_affect_translucent_lighting(False)
        light.set_specular_scale(.35)
        light.set_cast_shadows(False)
        light.set_light_function_material(None)
    sequence(seq,actors)
    after=snapshot(seq)
    if before!=after:raise RuntimeError('Unexpected actor transform or camera change')
    first=hero.sequence_signature(seq)
    sequence(seq,actors)
    if hero.sequence_signature(seq)!=first:raise RuntimeError('Timing repeat added bindings or tracks')
    if not b.LEVELS.save_current_level():raise RuntimeError('Could not save jar-only light channels')
    report={'status':'SAVED','revision':REV,'camera_and_actor_transforms_unchanged':True,'repeat_sequence_structure':'PASS',
      'map_change':'Existing Moon and two jar lights use lighting channel 1; jar light spill/specular limited.',
      'curves':CURVES,'ripple_origin':[-600,0],'ripple_speed_cm_s':440,'first_ripple':22,'echo_ripple':46,
      'tree_arrival_seconds':[round(22+math.hypot(x+600,y)/440,2) for x,y in [(300,2050),(2550,2380),(4700,2900)]]}
    Path(u.Paths.project_saved_dir(),'LOK','timing_polish.json').write_text(json.dumps(report,indent=2))
    b.log('Timing polish saved; actual timeline render review required')

if __name__ in ('__main__','<run_path>'):
    try:main()
    except Exception:
        error=traceback.format_exc();u.log_error('[LOK][TIMING] '+error)
        Path(u.Paths.project_saved_dir(),'LOK','timing_polish.json').write_text(json.dumps({'status':'FAIL','error':error},indent=2))
    finally:u.SystemLibrary.quit_editor()
