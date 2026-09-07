"""Validate saved assets and references. Never equate asset presence with visual PASS."""
import json
import traceback
from pathlib import Path
import unreal as u
import build_zone01 as b


def master_reference():
    master=u.EditorLoadingAndSavingUtils.load_map(b.MASTER)
    streaming=u.GameplayStatics.get_streaming_level(master,"LV_Zone01_Moonlight")
    return isinstance(streaming,u.LevelStreamingAlwaysLoaded)


def main():
    try:
        checks=[]
        def check(name,passed,detail=""):
            checks.append({"check":name,"status":"PASS" if passed else "FAIL","detail":str(detail)})
        check("master_streaming_reference",master_reference())
        expected={
            b.ZONE:u.World,b.MASTER:u.World,
            b.BASE+"/Blueprints/Core/BP_LOK_ExhibitController":u.Blueprint,
            b.BASE+"/Blueprints/Zones/Zone01/BP_Zone01_Root":u.Blueprint,
            b.BASE+"/Blueprints/Zones/Zone01/BP_Zone01_Moon":u.Blueprint,
            b.BASE+"/Blueprints/Environment/BP_HanokSilhouette":u.Blueprint,
            b.BASE+"/Materials/MPC/MPC_LOK_Global":u.MaterialParameterCollection,
            b.BASE+"/Sequences/Zone01/LS_Zone01_Opening":u.LevelSequence}
        for path,cls in expected.items():
            obj=u.load_asset(path)
            check("asset:"+path,isinstance(obj,cls))
        if not b.LEVELS.load_level(b.ZONE):
            raise RuntimeError("Zone cannot load")
        actors=b.ACTORS.get_all_level_actors()
        by_name={a.get_actor_label():a for a in actors}
        hero='HeroTrees' in by_name
        for name in ["Moon","Ground","HanokSilhouette","Zone01_Root","MoonlightFog","PostProcess_Zone01","CAM_Zone01_Main","ExhibitController"]:
            check("actor:"+name,name in by_name)
        ids=[str(t) for a in actors for t in a.tags if str(t).startswith("LOK.ID.")]
        check("unique_actor_ids",len(ids)==len(set(ids)),len(ids))
        fog=by_name["MoonlightFog"].get_component_by_class(u.ExponentialHeightFogComponent)
        check("volumetric_fog_enabled",fog.get_editor_property("enable_volumetric_fog"))
        pp=by_name["PostProcess_Zone01"].get_editor_property("settings")
        bloom=pp.get_editor_property("bloom_intensity")
        check("bloom_override_in_requested_range",pp.get_editor_property("override_bloom_intensity") and .3<=bloom<=.6,bloom)
        root=by_name["Zone01_Root"]
        forest=root.get_component_by_class(u.InstancedStaticMeshComponent)
        check("prototype_forest_hidden" if hero else "forest_instances",
              not forest.is_visible() if hero else forest is not None and forest.get_instance_count()==32)
        moon=u.load_asset(b.BASE+("/Materials/Hero/M_Hero_Ceramic" if hero else "/Materials/Master/M_Moon_Procedural"))
        check("procedural_moon_graph",u.MaterialEditingLibrary.get_num_material_expressions(moon)>=12,u.MaterialEditingLibrary.get_num_material_expressions(moon))
        sequence=u.load_asset(b.BASE+"/Sequences/Zone01/LS_Zone01_Opening")
        check("opening_60_seconds",sequence.get_playback_end()==1800 and sequence.get_display_rate().numerator==30)
        camera_bindings=[x for x in sequence.get_bindings() if str(x.get_name())=="CAM_Zone01_Main"]
        check("camera_binding",len(camera_bindings)==1)
        check("camera_cut_track",any(isinstance(t,u.MovieSceneCameraCutTrack) for t in sequence.get_tracks()))
        check("mpc_track",any(isinstance(t,u.MovieSceneMaterialParameterCollectionTrack) for t in sequence.get_tracks()))
        check("native_autoplay",by_name["ExhibitController"].get_editor_property("playback_settings").get_editor_property("auto_play"))
        garden=by_name.get("LuminousGarden")
        check("reference_garden_present",garden is not None)
        if garden:
            components=garden.get_components_by_class(u.InstancedStaticMeshComponent)
            leaves=[c for c in components if "Blossoms" in c.get_name()]
            import petal_clusters
            expected_blossoms=len(petal_clusters.layout()[0]) if hero else 6370
            check("blossom_instances",sum(c.get_instance_count() for c in leaves)==expected_blossoms,sum(c.get_instance_count() for c in leaves))
        neck=by_name.get("MoonJar_Neck")
        if hero:
            check("smooth_jar_mesh",by_name['Moon'].get_component_by_class(u.StaticMeshComponent).static_mesh.get_name()=='SM_MoonJar_HandThrown')
            check("prototype_jar_neck_hidden",neck is not None and not neck.static_mesh_component.is_visible())
            check("soft_light_line_count",len([n for n in by_name if n.startswith('Hero_SoftRain_')])==12)
            check("hero_lens_range",24<=by_name['CAM_Zone01_Main'].get_cine_camera_component().get_editor_property('current_focal_length')<=35)
        else:
            check("jar_neck_at_installation",neck is not None and abs(neck.get_actor_location().z-2235)<1)
        check("hanok_on_right",by_name["HanokSilhouette"].get_actor_location().y>0)
        for name in ["NS_Zone01_AmbientParticles","NS_Zone01_MoonHalo","NS_Zone01_FloorLight","NS_Zone01_FogParticles"]:
            path=b.BASE+"/Niagara/Zone01/"+name
            check("niagara:"+name,u.EditorAssetLibrary.does_asset_exist(path) and isinstance(u.load_asset(path),u.NiagaraSystem))
        for path in expected:
            if expected[path]==u.Blueprint:
                bp=u.load_asset(path)
                u.BlueprintEditorLibrary.compile_blueprint(bp)
                check("blueprint_generated_class:"+bp.get_name(),bp.generated_class() is not None)
        cv={name:u.SystemLibrary.get_console_variable_int_value(name) for name in ["r.DefaultFeature.Bloom","r.RayTracing","r.Lumen.HardwareRayTracing","r.DynamicGlobalIlluminationMethod","r.ReflectionMethod"]}
        evidence={}
        for kind in ["runtime","render"]:
            path=Path(u.Paths.project_saved_dir())/"LOK"/(kind+"_zone01.json")
            evidence[kind]=json.loads(path.read_text(encoding="utf-8")) if path.exists() else {"status":"NOT_RUN"}
        pending=["Target-hardware 1080p projection performance", "Sound design", "Full multi-zone function API"]
        if evidence["runtime"].get("status")!="PASS":
            pending.append("Native autoplay and Niagara runtime activation")
        if evidence["render"].get("status")!="PASS":
            pending.append("Full MRQ output")
        report={"status":"PARTIAL","structure_status":"PASS" if all(c["status"]=="PASS" for c in checks) else "FAIL",
                "checks":checks,"cvars":cv,"separate_execution_evidence":evidence,"remaining":pending}
        target=Path(u.Paths.project_saved_dir())/"LOK"/"validation_zone01.json"
        target.parent.mkdir(parents=True,exist_ok=True)
        target.write_text(json.dumps(report,ensure_ascii=False,indent=2),encoding="utf-8")
        u.log("[LOK][INFO] Validation PARTIAL: %d passed / %d failed / visual-runtime checks pending" % (sum(c["status"]=="PASS" for c in checks),sum(c["status"]=="FAIL" for c in checks)))
        return report
    except Exception:
        u.log_error("[LOK][ERROR] "+traceback.format_exc())
        raise


if __name__=="__main__":
    main()
