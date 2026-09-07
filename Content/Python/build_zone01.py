"""Build Zone 01 in Unreal Editor. No external assets; no project setting edits.

Run with Unreal's Python commandlet or Editor Python. Owned objects are reused.
Rendering and runtime behavior require separate validation after asset creation.
"""
import json
import gc
import math
import traceback
from pathlib import Path
import unreal as u

BASE = "/Game/LOK"
ZONE = BASE + "/Maps/Zone01/LV_Zone01_Moonlight"
MASTER = BASE + "/Maps/Master/LV_LOK_Master"
OWNER = "LOK.Zone01.v1"
EAL = u.EditorAssetLibrary
MAT = u.MaterialEditingLibrary
TOOLS = u.AssetToolsHelpers.get_asset_tools()
ACTORS = u.get_editor_subsystem(u.EditorActorSubsystem)
LEVELS = u.get_editor_subsystem(u.LevelEditorSubsystem)
CREATED = []


def struct(cls, **properties):
    result = cls()
    for key, value in properties.items():
        result.set_editor_property(key, value)
    return result


def log(message):
    u.log("[LOK][INFO] " + message)


def owned(asset):
    return EAL.get_metadata_tag(asset, "LOK.Generated") == OWNER


def mark(asset):
    EAL.set_metadata_tag(asset, "LOK.Generated", OWNER)


def save(asset):
    mark(asset)
    if not EAL.save_loaded_asset(asset, only_if_is_dirty=False):
        raise RuntimeError("Save failed: " + asset.get_path_name())


def asset(path, cls, factory):
    if EAL.does_asset_exist(path):
        result = EAL.load_asset(path)
        if not isinstance(result, cls) or not owned(result):
            raise RuntimeError("Unowned or incompatible asset: " + path)
        return result, False
    folder, name = path.rsplit("/", 1)
    result = TOOLS.create_asset(name, folder, cls, factory)
    if not result:
        raise RuntimeError("Asset creation failed: " + path)
    mark(result)
    CREATED.append(path)
    return result, True


def expression(material, cls, **properties):
    node = MAT.create_material_expression(material, cls)
    for key, value in properties.items():
        node.set_editor_property(key, value)
    return node


def connect(source, target, pin, output=""):
    if not MAT.connect_material_expressions(source, output, target, pin):
        raise RuntimeError("Material connection failed: " + pin)


def scalar(material, value):
    return expression(material, u.MaterialExpressionConstant, r=float(value))


def color(material, rgb):
    return expression(material, u.MaterialExpressionConstant3Vector,
                      constant=u.LinearColor(*rgb, 1))


def output(material, node, prop):
    if not MAT.connect_material_property(node, "", prop):
        raise RuntimeError("Material output connection failed")


def mpc_node(material, collection, name):
    return expression(material, u.MaterialExpressionCollectionParameter,
                      collection=collection, parameter_name=name)


def multiply(material, *nodes):
    result = nodes[0]
    for other in nodes[1:]:
        node = expression(material, u.MaterialExpressionMultiply)
        connect(result, node, "A")
        connect(other, node, "B")
        result = node
    return result


def custom(material, code, inputs, output_type=u.CustomMaterialOutputType.CMOT_FLOAT3):
    node = expression(material, u.MaterialExpressionCustom, code=code,
                      output_type=output_type,
                      inputs=[struct(u.CustomInput, input_name=n) for n in inputs])
    for name, source in inputs.items():
        connect(source, node, name)
    return node


def finish_material(material):
    MAT.layout_material_expressions(material)
    MAT.recompile_material(material)
    save(material)


def build_materials():
    collection, fresh = asset(BASE + "/Materials/MPC/MPC_LOK_Global",
                              u.MaterialParameterCollection, u.MaterialParameterCollectionFactoryNew())
    if fresh:
        defaults = {"GlobalIntensity": 1, "ScenePhase": 1, "MoonGlow": 0.7,
                    "GroundGlow": 0.5, "ParticleIntensity": 1, "TransitionAlpha": 1,
                    "ExhibitTime": 50, "RippleStartTime": 45, "RippleStrength": 1,
                    "ForestGlow": 0.65}
        collection.set_editor_property("scalar_parameters", [
            struct(u.CollectionScalarParameter, parameter_name=k, default_value=v) for k, v in defaults.items()])
        collection.set_editor_property("vector_parameters", [
            struct(u.CollectionVectorParameter, parameter_name=k, default_value=u.LinearColor(*v))
            for k, v in {"PrimaryLight": (0.82, 0.88, 1, 1),
                         "SecondaryLight": (0.12, 0.22, 0.4, 1),
                         "InteractionPosition": (-450, 0, 0, 0)}.items()])
        save(collection)
    materials = {}
    for key, name in [("moon", "M_Moon_Procedural"), ("ground", "M_Ground_Moonlight"),
                      ("hanok", "M_Hanok_Silhouette"), ("forest", "M_LightForest"),
                      ("trim", "M_Exhibit_Trim")]:
        material, fresh = asset(BASE + "/Materials/Master/" + name, u.Material, u.MaterialFactoryNew())
        if fresh or (key in ("moon","ground") and EAL.get_metadata_tag(material,"LOK.SurfaceRevision") != "5"):
            if not fresh:
                MAT.delete_all_material_expressions(material)
            world = expression(material, u.MaterialExpressionWorldPosition)
            global_gain = multiply(material,
                mpc_node(material, collection, "GlobalIntensity"),
                mpc_node(material, collection, "TransitionAlpha"))
            if key == "moon":
                material.set_editor_property("blend_mode",u.BlendMode.BLEND_MASKED)
                center=expression(material,u.MaterialExpressionObjectPositionWS)
                mask=custom(material,"return step(P.z-C.z,800);",{"P":world,"C":center},u.CustomMaterialOutputType.CMOT_FLOAT1)
                output(material,mask,u.MaterialProperty.MP_OPACITY_MASK)
                low = expression(material, u.MaterialExpressionNoise, scale=0.0008, levels=3,
                                 quality=1, output_min=0.0, output_max=1.0)
                high = expression(material, u.MaterialExpressionNoise, scale=0.012, levels=2,
                                  quality=1, output_min=0.0, output_max=1.0)
                # Noise's unconnected position input uses the surface world position.
                surface = custom(material,
                    "float n=saturate(L*.9+H*.1); return lerp(float3(.26,.29,.31),float3(.73,.74,.68),smoothstep(.15,.82,n));",
                    {"L": low, "H": high})
                output(material, surface, u.MaterialProperty.MP_BASE_COLOR)
                output(material, custom(material, "return lerp(.65,.95,H);", {"H": high},
                       u.CustomMaterialOutputType.CMOT_FLOAT1), u.MaterialProperty.MP_ROUGHNESS)
                output(material, multiply(material, surface, global_gain,
                    mpc_node(material, collection, "MoonGlow")), u.MaterialProperty.MP_EMISSIVE_COLOR)
                normal = custom(material, "return normalize(float3((L-.5)*.08,(H-.5)*.08,1));", {"L": low, "H": high})
                output(material, normal, u.MaterialProperty.MP_NORMAL)
            elif key == "ground":
                output(material, color(material, (.025, .032, .05)), u.MaterialProperty.MP_BASE_COLOR)
                output(material, scalar(material, .10), u.MaterialProperty.MP_ROUGHNESS)
                output(material, scalar(material, .65), u.MaterialProperty.MP_METALLIC)
                ripple = custom(material,
                    "float d=length(P.xy-float2(-850,0)); float age=max(0,T-45); float r=fmod(age*80,1000); "
                    "float a=exp(-pow((d-r)/10,2)); float b=exp(-pow((d-r-260)/9,2))*.65; "
                    "float c=exp(-pow((d-r-530)/8,2))*.35; "
                    "float fade=saturate(age)*saturate((2200-d)/600); return float3(.22,.55,1.1)*(a+b+c)*fade;",
                    {"P": world, "C": mpc_node(material, collection, "InteractionPosition"),
                     "T": mpc_node(material, collection, "ExhibitTime")})
                output(material, multiply(material, ripple, global_gain,
                    mpc_node(material, collection, "GroundGlow"),
                    mpc_node(material, collection, "RippleStrength")), u.MaterialProperty.MP_EMISSIVE_COLOR)
            elif key == "hanok":
                output(material, color(material, (.008, .012, .019)), u.MaterialProperty.MP_BASE_COLOR)
                output(material, scalar(material, .82), u.MaterialProperty.MP_ROUGHNESS)
            elif key == "forest":
                output(material, color(material, (.017, .028, .04)), u.MaterialProperty.MP_BASE_COLOR)
                output(material, scalar(material, .38), u.MaterialProperty.MP_ROUGHNESS)
                glow = custom(material,
                    "float v=pow(saturate(P.z/900),3); return lerp(float3(.025,.055,.10),float3(.20,.39,.57),v);",
                    {"P": world})
                output(material, multiply(material, glow, global_gain,
                    mpc_node(material, collection, "ForestGlow")), u.MaterialProperty.MP_EMISSIVE_COLOR)
            else:
                output(material, color(material, (.012, .018, .025)), u.MaterialProperty.MP_BASE_COLOR)
                output(material, scalar(material, .65), u.MaterialProperty.MP_ROUGHNESS)
            EAL.set_metadata_tag(material,"LOK.SurfaceRevision","5")
            finish_material(material)
        if key=="forest" and not material.get_editor_property("used_with_instanced_static_meshes"):
            material.set_editor_property("used_with_instanced_static_meshes",True)
            MAT.recompile_material(material)
            save(material)
        instance, fresh = asset(BASE + "/Materials/Instances/MI_Zone01_" + key.title(),
                                u.MaterialInstanceConstant, u.MaterialInstanceConstantFactoryNew())
        if fresh:
            MAT.set_material_instance_parent(instance, material)
            save(instance)
        materials[key] = instance
    return collection, materials


def blueprint(path, parent=u.Actor):
    if EAL.does_asset_exist(path):
        bp = EAL.load_asset(path)
        if not isinstance(bp, u.Blueprint) or not owned(bp):
            raise RuntimeError("Unowned Blueprint: " + path)
        return bp, False
    bp = u.BlueprintEditorLibrary.create_blueprint_asset_with_parent(path, parent)
    if not bp:
        raise RuntimeError("Blueprint factory failed: " + path)
    mark(bp)
    CREATED.append(path)
    return bp, True


def component(bp, name, cls):
    system = u.get_engine_subsystem(u.SubobjectDataSubsystem)
    handles = system.k2_gather_subobject_data_for_blueprint(bp)
    handle, failure = system.add_new_subobject(struct(u.AddNewSubobjectParams,
        parent_handle=handles[0], new_class=cls, blueprint_context=bp))
    if str(failure):
        raise RuntimeError(str(failure))
    system.rename_subobject(handle, name)
    data = u.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
    return u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data, bp)


def configure_mesh(comp, mesh, material, location=None, scale=(1, 1, 1), rotation=None):
    comp.set_static_mesh(u.load_asset("/Engine/BasicShapes/" + mesh))
    comp.set_material(0, material)
    if location is not None:
        comp.set_editor_property("relative_location", u.Vector(*location))
    comp.set_editor_property("relative_scale3d", u.Vector(*scale))
    if rotation is not None:
        comp.set_editor_property("relative_rotation", u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]))
    comp.set_editor_property("mobility", u.ComponentMobility.MOVABLE)


def build_blueprints(materials):
    moon, fresh = blueprint(BASE + "/Blueprints/Zones/Zone01/BP_Zone01_Moon")
    if fresh:
        configure_mesh(component(moon, "MoonSurface", u.StaticMeshComponent), "Sphere", materials["moon"], scale=(20,20,20))
        u.BlueprintEditorLibrary.compile_blueprint(moon)
        save(moon)
    hanok, fresh = blueprint(BASE + "/Blueprints/Environment/BP_HanokSilhouette")
    if fresh:
        # Local X is depth, local Y is the facade. Raised eaves are segmented cubes.
        for i, y in enumerate([-420, -140, 140, 420]):
            configure_mesh(component(hanok, "Column%02d" % i, u.StaticMeshComponent), "Cube", materials["hanok"], (0,y,170), (.25,.25,3.4))
        configure_mesh(component(hanok, "Beam", u.StaticMeshComponent), "Cube", materials["hanok"], (0,0,325), (.5,9.2,.4))
        configure_mesh(component(hanok, "Plinth", u.StaticMeshComponent), "Cube", materials["hanok"], (0,0,12), (5.3,10.4,.24))
        for side in [-1,1]:
            for i in range(7):
                y = side * (i + .5) * 82
                z = 455 - 100 * math.sin((i+.5)/7*math.pi/2) + max(0, i-4)**2*12
                roll = side * (-16 if i < 4 else (i-3)*12)
                configure_mesh(component(hanok, "Roof%s_%d" % ("L" if side<0 else "R", i), u.StaticMeshComponent),
                               "Cube", materials["hanok"], (0,y,z), (5.8,.89,.22), (0,0,roll))
        u.BlueprintEditorLibrary.compile_blueprint(hanok)
        save(hanok)
    if EAL.get_metadata_tag(hanok,"LOK.RoofRotationRevision") != "3":
        subsystem=u.get_engine_subsystem(u.SubobjectDataSubsystem)
        for handle in subsystem.k2_gather_subobject_data_for_blueprint(hanok):
            data=u.SubobjectDataBlueprintFunctionLibrary.get_data(handle)
            obj=u.SubobjectDataBlueprintFunctionLibrary.get_object_for_blueprint(data,hanok)
            if isinstance(obj,u.StaticMeshComponent) and obj.get_name().startswith("Roof"):
                name=obj.get_name()
                side=-1 if name.startswith("RoofL") else 1
                index=int(name.split("_")[1])
                t0,t1=index/7,(index+1)/7
                z0=455-180*t0+115*t0**4
                z1=455-180*t1+115*t1**4
                slope=(z1-z0)/82
                roll=-side*math.degrees(math.atan(slope))
                obj.set_editor_property("relative_location",u.Vector(0,side*(index+.5)*82,(z0+z1)/2))
                obj.set_editor_property("relative_scale3d",u.Vector(5.8,(math.hypot(82,z1-z0)+4)/100,.32))
                obj.set_editor_property("relative_rotation",u.Rotator(pitch=0,yaw=0,roll=roll))
        EAL.set_metadata_tag(hanok,"LOK.RoofRotationRevision","3")
        u.BlueprintEditorLibrary.compile_blueprint(hanok)
        save(hanok)
    root, fresh = blueprint(BASE + "/Blueprints/Zones/Zone01/BP_Zone01_Root")
    if fresh:
        forest = component(root, "LightForest", u.InstancedStaticMeshComponent)
        configure_mesh(forest, "Cylinder", materials["forest"])
        for side in [-1, 1]:
            for i in range(16):
                x = -1200 + (i % 8)*520
                y = side * (1400 + (i//8)*530 + math.sin(i*1.7)*100)
                height = 450 + (i*137 % 560)
                forest.add_instance(u.Transform(location=u.Vector(x,y,height/2), scale=u.Vector(.065,.065,height/100)))
        u.BlueprintEditorLibrary.compile_blueprint(root)
        save(root)
    controller, fresh = blueprint(BASE + "/Blueprints/Core/BP_LOK_ExhibitController", u.LevelSequenceActor)
    if fresh:
        # Native LevelSequenceActor playback is functional in PIE and packaged runtime.
        # Full multi-zone Blueprint function API is a subsequent implementation step.
        u.BlueprintEditorLibrary.compile_blueprint(controller)
        save(controller)
    return {"moon": moon, "hanok": hanok, "root": root, "controller": controller}


def load_or_create_map(path):
    if LEVELS.get_current_level().get_outer().get_path_name().split(".")[0] == path:
        current=LEVELS.get_current_level().get_outer()
        if not owned(current):
            raise RuntimeError("Refusing unowned current map: "+path)
        return current
    if EAL.does_asset_exist(path):
        existing = EAL.load_asset(path)
        if not owned(existing):
            raise RuntimeError("Refusing unowned map: " + path)
        del existing
        gc.collect()
        if not LEVELS.load_level(path):
            raise RuntimeError("Cannot load map: " + path)
    else:
        if not LEVELS.new_level(path):
            raise RuntimeError("Cannot create map: " + path)
        CREATED.append(path)
    world = LEVELS.get_current_level().get_outer()
    mark(world)
    if not LEVELS.save_current_level():
        raise RuntimeError("Cannot persist map ownership: " + path)
    return world


def actor(key, cls, location=(0,0,0), rotation=(0,0,0)):
    tag = "LOK.ID." + key
    matches = [a for a in ACTORS.get_all_level_actors() if tag in [str(t) for t in a.tags]]
    if len(matches)>1:
        raise RuntimeError("Duplicate generated Actor: " + key)
    if matches:
        result = matches[0]
    else:
        result = ACTORS.spawn_actor_from_class(cls, u.Vector(*location), u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]))
        if not result:
            raise RuntimeError("Spawn failed: " + key)
        result.tags = [OWNER, tag]
    result.set_actor_label(key)
    result.set_actor_location(u.Vector(*location), False, False)
    result.set_actor_rotation(u.Rotator(pitch=rotation[0],yaw=rotation[1],roll=rotation[2]), False)
    result.set_folder_path("LOK/Zone01")
    return result


def float_track(sequence, obj, property_name, keys):
    binding = sequence.add_possessable(obj)
    track = binding.add_track(u.MovieSceneFloatTrack)
    track.set_property_name_and_path(property_name, property_name)
    section = track.add_section()
    section.set_range(0, 1800)
    channel = section.get_all_channels()[0]
    for second, value in keys:
        channel.add_key(u.FrameNumber(round(second*30)), value)
    return binding


def build_sequence(camera, lights, fog, collection):
    sequence, fresh = asset(BASE + "/Sequences/Zone01/LS_Zone01_Opening", u.LevelSequence, u.LevelSequenceFactoryNew())
    if fresh:
        sequence.set_display_rate(u.FrameRate(30,1))
        sequence.set_tick_resolution_directly(u.FrameRate(30,1))
        sequence.set_playback_start(0)
        sequence.set_playback_end(1800)
        binding = sequence.add_possessable(camera)
        track = binding.add_track(u.MovieScene3DTransformTrack)
        section = track.add_section()
        section.set_range(0,1800)
        channels = section.get_all_channels()
        for seconds, position, look_at in [
            (0,(-2600,-160,150),(1800,0,800)), (15,(-2270,-90,170),(1800,0,1180)),
            (30,(-1980,100,175),(1800,0,1050)), (45,(-1700,260,185),(1800,0,850)),
            (60,(-1520,330,190),(1800,0,830))]:
            rot = u.MathLibrary.find_look_at_rotation(u.Vector(*position),u.Vector(*look_at))
            values = (*position, rot.roll, rot.pitch, rot.yaw, 1,1,1)
            for channel,value in zip(channels,values):
                channel.add_key(u.FrameNumber(seconds*30),float(value))
        cuts = sequence.add_track(u.MovieSceneCameraCutTrack)
        cut = cuts.add_section()
        cut.set_range(0,1800)
        cut.set_camera_binding_id(struct(u.MovieSceneObjectBindingID,guid=binding.get_id()))
        mtrack = sequence.add_track(u.MovieSceneMaterialParameterCollectionTrack)
        mtrack.set_editor_property("mpc",collection)
        msection = mtrack.add_section()
        msection.set_range(0,1800)
        curves = {"TransitionAlpha": [(0,0),(5,1),(60,1)], "MoonGlow": [(0,0),(5,.03),(15,.7),(60,.7)],
                  "ForestGlow": [(0,0),(35,0),(45,.65),(60,.65)], "GroundGlow": [(0,0),(44,0),(49,.5),(60,.5)],
                  "ParticleIntensity": [(0,0),(15,0),(25,1),(60,1)], "ExhibitTime": [(0,0),(60,60)],
                  "ScenePhase": [(0,0),(60,1)], "RippleStrength": [(0,0),(45,0),(47,1),(60,1)]}
        for name,keys in curves.items():
            for seconds,value in keys:
                msection.add_scalar_parameter_key(name,u.FrameNumber(seconds*30),value,
                    u.MovieSceneKeyInterpolation.LINEAR if name in ["ExhibitTime","ScenePhase"] else u.MovieSceneKeyInterpolation.AUTO)
        float_track(sequence,lights["moon"].get_component_by_class(u.DirectionalLightComponent),"Intensity",[(0,0),(5,.05),(15,.8),(60,.8)])
        float_track(sequence,lights["rim"].get_component_by_class(u.RectLightComponent),"Intensity",[(0,0),(25,0),(35,1200),(60,1200)])
        float_track(sequence,fog.get_component_by_class(u.ExponentialHeightFogComponent),"FogDensity",[(0,.002),(25,.003),(35,.009),(60,.009)])
        save(sequence)
    if EAL.get_metadata_tag(sequence,"LOK.RimRevision")!="3":
        for binding in sequence.get_bindings():
            for track in binding.get_tracks():
                if isinstance(track,u.MovieSceneFloatTrack):
                    for section in track.get_sections():
                        for channel in section.get_all_channels():
                            for key in channel.get_keys():
                                if key.get_value() in (6500,1200):
                                    key.set_value(100)
        EAL.set_metadata_tag(sequence,"LOK.RimRevision","3")
        save(sequence)
    return sequence


def build_scene(collection,materials,bps):
    world = load_or_create_map(ZONE)
    root = actor("Zone01_Root", bps["root"].generated_class())
    actor("Moon", bps["moon"].generated_class(),(3000,0,1400))
    actor("HanokSilhouette", bps["hanok"].generated_class(),(1200,1100,0),(0,-12,0))
    ground = actor("Ground",u.StaticMeshActor,(0,0,-20))
    configure_mesh(ground.static_mesh_component,"Cube",materials["ground"],scale=(180,150,.4))
    lights = {}
    lights["moon"] = actor("Moonlight",u.DirectionalLight,(1500,0,1600),(-28,-145,0))
    comp = lights["moon"].get_component_by_class(u.DirectionalLightComponent)
    comp.set_mobility(u.ComponentMobility.MOVABLE)
    comp.set_intensity(.8)
    comp.set_light_color(u.LinearColor(.70,.80,1,1))
    lights["rim"] = actor("Hanok_Rim",u.RectLight,(1650,1100,400),(0,180,0))
    comp=lights["rim"].get_component_by_class(u.RectLightComponent)
    comp.set_mobility(u.ComponentMobility.MOVABLE)
    comp.set_intensity(100)
    comp.set_light_color(u.LinearColor(1,.62,.28,1))
    comp.set_editor_property("source_width",800)
    comp.set_editor_property("source_height",500)
    comp.set_editor_property("attenuation_radius",2200)
    for side in [-1,1]:
        light=actor("Forest_Accent_"+str(side),u.PointLight,(0,side*1350,330))
        comp=light.get_component_by_class(u.PointLightComponent)
        comp.set_mobility(u.ComponentMobility.MOVABLE)
        comp.set_intensity(65)
        comp.set_light_color(u.LinearColor(.18,.38,.6,1))
        comp.set_editor_property("attenuation_radius",1600)
        comp.set_editor_property("cast_shadows",False)
    sky=actor("SkyFill",u.SkyLight,(0,0,1000))
    comp=sky.get_component_by_class(u.SkyLightComponent)
    comp.set_mobility(u.ComponentMobility.MOVABLE)
    comp.set_intensity(.04)
    fog=actor("MoonlightFog",u.ExponentialHeightFog,(0,0,-70))
    comp=fog.get_component_by_class(u.ExponentialHeightFogComponent)
    comp.set_editor_property("enable_volumetric_fog",True)
    comp.set_editor_property("fog_density",.009)
    comp.set_editor_property("fog_height_falloff",.25)
    comp.set_editor_property("fog_inscattering_luminance",u.LinearColor(.018,.03,.055,1))
    comp.set_editor_property("volumetric_fog_scattering_distribution",.3)
    pp=actor("PostProcess_Zone01",u.PostProcessVolume)
    pp.set_editor_property("unbound",True)
    settings=pp.get_editor_property("settings")
    for prop,value in {"override_bloom_intensity":True,"bloom_intensity":.45,
        "override_auto_exposure_method":True,"auto_exposure_method":u.AutoExposureMethod.AEM_MANUAL,
        "override_auto_exposure_bias":True,"auto_exposure_bias":0.0,
        "override_auto_exposure_apply_physical_camera_exposure":True,"auto_exposure_apply_physical_camera_exposure":False,
        "override_vignette_intensity":True,"vignette_intensity":.16,
        "override_scene_fringe_intensity":True,"scene_fringe_intensity":0.0,
        "override_lens_flare_intensity":True,"lens_flare_intensity":0.0,
        "override_motion_blur_amount":True,"motion_blur_amount":0.0}.items():
        settings.set_editor_property(prop,value)
    pp.set_editor_property("settings",settings)
    camera=actor("CAM_Zone01_Main",u.CineCameraActor,(-2200,0,170),(12,0,0))
    cam=camera.get_cine_camera_component()
    filmback=cam.get_editor_property("filmback")
    filmback.set_editor_property("sensor_width",36.0)
    filmback.set_editor_property("sensor_height",20.25)
    cam.set_editor_property("filmback",filmback)
    cam.set_editor_property("current_focal_length",24.0)
    focus=cam.get_editor_property("focus_settings")
    focus.set_editor_property("focus_method",u.CameraFocusMethod.DISABLE)
    cam.set_editor_property("focus_settings",focus)
    sequence=build_sequence(camera,lights,fog,collection)
    controller=actor("ExhibitController",bps["controller"].generated_class())
    controller.set_sequence(sequence)
    playback=controller.get_editor_property("playback_settings")
    playback.set_editor_property("auto_play",True)
    playback.set_editor_property("hide_hud",True)
    playback.set_editor_property("hide_player",True)
    controller.set_editor_property("playback_settings",playback)
    mark(world)
    if not LEVELS.save_current_level():
        raise RuntimeError("Zone map save failed")
    return sequence


def build_master():
    # Keep map-local UObject references in a separate scope before switching worlds.
    master=load_or_create_map(MASTER)
    if not u.GameplayStatics.get_streaming_level(master,"LV_Zone01_Moonlight"):
        if not u.EditorLevelUtils.add_level_to_world(master,ZONE,u.LevelStreamingAlwaysLoaded):
            raise RuntimeError("Could not link Zone01 to Master")
    mark(master)
    if not u.EditorLoadingAndSavingUtils.save_map(master,MASTER):
        raise RuntimeError("Master map save failed")


def main():
    try:
        # The visual pass owns the current composition; never restore the old blockout.
        if EAL.does_asset_exist(BASE+'/Meshes/Hero/SM_MoonJar_HandThrown') and EAL.does_asset_exist(ZONE):
            import polish_zone01
            polish_zone01.main()
            return
        CREATED.clear()
        log("Building owned Zone01 assets; existing project rendering settings are preserved.")
        collection,materials=build_materials()
        bps=build_blueprints(materials)
        sequence=build_scene(collection,materials,bps)
        build_master()
        LEVELS.load_level(ZONE)
        import build_zone01_garden
        build_zone01_garden.main()
        report={"status":"PARTIAL", "created":CREATED,
                "map":ZONE,"sequence":sequence.get_path_name(),
                "pending":["Multi-zone controller function API", "Full sequence playback QA", "Performance measurement", "MRQ output"]}
        out=Path(u.Paths.project_saved_dir())/"LOK"/"build_zone01.json"
        out.parent.mkdir(parents=True,exist_ok=True)
        out.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        log("Scene asset build complete. Visual and runtime checks remain.")
    except Exception:
        u.log_error("[LOK][ERROR] " + traceback.format_exc())
        raise


if __name__ == "__main__":
    main()
