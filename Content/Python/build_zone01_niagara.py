"""Author native Niagara assets using the bundled editor converter API.

Commandlet option: -EnablePlugins=CascadeToNiagaraConverter
The converter is an authoring tool; generated systems reference Niagara only.
"""
import traceback
import unreal as u
import build_zone01 as b


def args(path):
    data = u.FXConverterUtilitiesLibrary.create_asset_data(path)
    return b.struct(u.CreateScriptContextArgs, script_asset=data)


def set_input(script, name, value):
    if not script.set_parameter(name, value):
        raise RuntimeError("Niagara input unavailable: " + name)


def dynamic(path, parameters, kind):
    fx = u.FXConverterUtilitiesLibrary
    context = fx.create_script_context(args(path))
    for name, value in parameters.items():
        set_input(context, name, value)
    return fx.create_script_input_dynamic(context, kind)


def material(collection, fog=False):
    name = "M_Fog_Soft" if fog else "M_Particle_Soft"
    mat, fresh = b.asset(b.BASE + "/Materials/Master/" + name,u.Material,u.MaterialFactoryNew())
    if fresh or b.EAL.get_metadata_tag(mat,"LOK.SpriteRevision")!="4":
        if not fresh:
            b.MAT.delete_all_material_expressions(mat)
        mat.set_editor_property("blend_mode",u.BlendMode.BLEND_TRANSLUCENT)
        mat.set_editor_property("shading_model",u.MaterialShadingModel.MSM_UNLIT)
        mat.set_editor_property("two_sided",True)
        mat.set_editor_property("used_with_niagara_sprites",True)
        uv=b.expression(mat,u.MaterialExpressionTextureCoordinate)
        pc=b.expression(mat,u.MaterialExpressionParticleColor)
        position=b.expression(mat,u.MaterialExpressionParticlePositionWS)
        clock=b.mpc_node(mat,collection,"ExhibitTime")
        drift=b.custom(mat,
            "return float3(sin(T*.31+P.y*.013)*28,cos(T*.23+P.x*.011)*35,sin(T*.37+P.z*.009)*24);",
            {"T":clock,"P":position})
        b.output(mat,drift,u.MaterialProperty.MP_WORLD_POSITION_OFFSET)
        radial=b.custom(mat,"float r=length(UV-float2(.5,.5))*2; return pow(saturate(1-r),3);",{"UV":uv},u.CustomMaterialOutputType.CMOT_FLOAT1)
        opacity=b.multiply(mat,radial,b.scalar(mat,.0015 if fog else .7),b.mpc_node(mat,collection,"ParticleIntensity"))
        alpha=b.expression(mat,u.MaterialExpressionMultiply)
        b.connect(opacity,alpha,"A")
        b.connect(pc,alpha,"B",output="A")
        fade=b.expression(mat,u.MaterialExpressionDepthFade,fade_distance_default=120 if fog else 25)
        b.connect(alpha,fade,"Opacity")
        b.output(mat,fade,u.MaterialProperty.MP_OPACITY)
        b.output(mat,b.multiply(mat,pc,b.scalar(mat,.08 if fog else 1),b.mpc_node(mat,collection,"GlobalIntensity"),
            b.mpc_node(mat,collection,"TransitionAlpha")),u.MaterialProperty.MP_EMISSIVE_COLOR)
        b.EAL.set_metadata_tag(mat,"LOK.SpriteRevision","4")
        b.finish_material(mat)
    return mat


def make_system(name,extent,rate,size,mat,halo=False):
    system,fresh=b.asset(b.BASE+"/Niagara/Zone01/"+name,u.NiagaraSystem,u.NiagaraSystemFactoryNew())
    system.set_editor_property("bFixedBounds",True)
    system.set_editor_property("FixedBounds",u.Box(min=u.Vector(*[-v-250 for v in extent]),max=u.Vector(*[v+250 for v in extent])))
    if not fresh:
        fix_renderers(system,mat)
        b.save(system)
        return system
    fx=u.FXConverterUtilitiesLibrary
    ctx=fx.create_system_conversion_context(system)
    try:
        emitter=ctx.add_template_emitter(name.replace("NS_","NE_"),"/Niagara/DefaultAssets/Templates/Emitters/Minimal")
        emitter.set_enabled(True)
        emitter.set_local_space(True)
        emitter.set_sim_target(u.NiagaraSimTarget.GPU_COMPUTE_SIM)
        # Fixed finite lifetime + clamped spawn rate bounds the live count.
        spawn=emitter.find_or_add_module_script("LOK_SpawnRate",args("/Niagara/Modules/Emitter/SpawnRate"),u.ScriptExecutionCategory.EMITTER_UPDATE)
        clamped=dynamic("/Niagara/DynamicInputs/Clamp/ClampFloat",{
            "Float":fx.create_script_input_linked_parameter("User.SpawnRate",u.NiagaraScriptInputType.FLOAT),
            "Min":fx.create_script_input_float(0),"Max":fx.create_script_input_float(rate)},u.NiagaraScriptInputType.FLOAT)
        set_input(spawn,"SpawnRate",clamped)
        emitter.set_parameter_directly("Particles.Lifetime",fx.create_script_input_float(10),u.ScriptExecutionCategory.PARTICLE_SPAWN)
        emitter.set_parameter_directly("Particles.SpriteSize",fx.create_script_input_vec2(u.Vector2D(size,size)),u.ScriptExecutionCategory.PARTICLE_SPAWN)
        tint=dynamic("/Niagara/DynamicInputs/LinearColor/MakeLinearColorFromVectorAndFloat",{
            "Vector (RGB)":fx.create_script_input_vector(u.Vector(.28,.48,.8)),
            "Float (Alpha)":fx.create_script_input_linked_parameter("User.Intensity",u.NiagaraScriptInputType.FLOAT)},u.NiagaraScriptInputType.LINEAR_COLOR)
        emitter.set_parameter_directly("Particles.Color",tint,u.ScriptExecutionCategory.PARTICLE_SPAWN)
        if halo:
            shape=emitter.find_or_add_module_script("LOK_HaloSphere",args("/Niagara/Modules/Spawn/Location/V2/ShapeLocation"),u.ScriptExecutionCategory.PARTICLE_SPAWN)
            set_input(shape,"Shape Primitive",fx.create_script_input_enum("/Niagara/Enums/Location/ENiagara_LocationShapes","Sphere"))
            set_input(shape,"Sphere Radius",fx.create_script_input_linked_parameter("User.Radius",u.NiagaraScriptInputType.FLOAT))
            if not shape.set_parameter("Sphere Surface Distribution",fx.create_script_input_float(1),True,True):
                raise RuntimeError("Could not constrain Halo to sphere surface")
        else:
            vector=dynamic("/Niagara/DynamicInputs/UniformRange/V2/RandomRangeVector",{
                "Minimum":fx.create_script_input_vector(u.Vector(*[-v for v in extent])),
                "Maximum":fx.create_script_input_vector(u.Vector(*extent))},u.NiagaraScriptInputType.VEC3)
            position=dynamic("/Niagara/DynamicInputs/Transforms/ConvertVectorToPosition",{"Input Position":vector},u.NiagaraScriptInputType.POSITION)
            emitter.set_parameter_directly("Particles.Position",position,u.ScriptExecutionCategory.PARTICLE_SPAWN)
        renderers=emitter.get_all_renderers()
        for renderer in renderers:
            if isinstance(renderer,u.NiagaraSpriteRendererProperties):
                renderer.set_editor_property("material",mat)
        if not renderers:
            renderer=u.NiagaraSpriteRendererProperties()
            renderer.set_editor_property("material",mat)
            emitter.add_renderer("LOK_Sprites",renderer)
        ctx.finalize()
        fix_renderers(system,mat)
        b.save(system)
        b.log("Niagara system saved: "+name)
    finally:
        ctx.cleanup()
    return system


def fix_renderers(system,mat):
    # Minimal already includes a sprite renderer. Converter get_all_renderers()
    # only lists staged additions, so earlier assets also had the template renderer.
    renderers=[]
    for renderer in u.ObjectIterator(u.NiagaraSpriteRendererProperties):
        outer=renderer.get_outer()
        while outer:
            if outer==system:
                renderers.append(renderer)
                break
            outer=outer.get_outer()
    if not renderers:
        raise RuntimeError("No owned sprite renderers found for "+system.get_name())
    renderers.sort(key=lambda r:r.get_path_name())
    for index,renderer in enumerate(renderers):
        renderer.set_editor_property("material",mat)
    b.log("Renderer material fix: %s, found %d, all use %s"%(system.get_name(),len(renderers),mat.get_name()))


def main():
    try:
        if not hasattr(u,"FXConverterUtilitiesLibrary"):
            raise RuntimeError("Use -EnablePlugins=CascadeToNiagaraConverter for editor authoring")
        collection=u.load_asset(b.BASE+"/Materials/MPC/MPC_LOK_Global")
        soft=material(collection)
        fog=material(collection,True)
        specs=[("NS_Zone01_AmbientParticles",(1700,1300,550),80,5,soft,False,(0,0,650),15),
               ("NS_Zone01_MoonHalo",(1250,1250,1250),45,13,soft,True,(2200,0,1400),15),
               ("NS_Zone01_FloorLight",(1000,900,10),25,8,soft,False,(-100,0,22),45),
               ("NS_Zone01_FogParticles",(650,500,90),4,400,fog,False,(800,-750,120),25)]
        systems=[(spec,make_system(*spec[:6])) for spec in specs]
        b.LEVELS.load_level(b.ZONE)
        sequence=u.load_asset(b.BASE+"/Sequences/Zone01/LS_Zone01_Opening")
        for spec,system in systems:
            name,extent,rate,size,mat,halo,location,start=spec
            a=b.actor(name,u.NiagaraActor,location)
            comp=a.get_component_by_class(u.NiagaraComponent)
            comp.set_asset(system)
            comp.set_variable_float("User.SpawnRate",rate)
            comp.set_variable_float("User.Intensity",1)
            if halo:
                comp.set_variable_float("User.Radius",1080)
            comp.set_system_fixed_bounds(u.Box(min=u.Vector(*[-v-250 for v in extent]),max=u.Vector(*[v+250 for v in extent])))
            # Only create one lifetime binding for each named component.
            binding_name="LOK_FX_"+name
            if not any(str(binding.get_name())==binding_name for binding in sequence.get_bindings()):
                binding=sequence.add_possessable(comp)
                binding.set_name(binding_name)
                track=binding.add_track(u.MovieSceneNiagaraSystemTrack)
                section=track.add_section()
                section.set_range(start*30,1800)
            for binding in sequence.get_bindings():
                if str(binding.get_name())==binding_name:
                    for track in binding.get_tracks():
                        for section in track.get_sections():
                            if isinstance(section,u.MovieSceneNiagaraSystemSpawnSection):
                                section.set_age_update_mode(u.NiagaraAgeUpdateMode.DESIRED_AGE)
        b.save(sequence)
        if not b.LEVELS.save_current_level():
            raise RuntimeError("Could not save Niagara actor placements")
        b.log("Four Niagara systems authored and bound to opening sequence")
    except Exception:
        u.log_error("[LOK][ERROR] "+traceback.format_exc())
        raise


if __name__=="__main__":
    main()
