"""Render the full opening through MRQ in a dedicated editor; no config changes."""
import json
import time
import traceback
from pathlib import Path
import unreal as u

STATE={"started":time.time(),"errors":[]}
STILL='-LOKHeroStill' in u.SystemLibrary.get_command_line()
PETALS='-LOKPetalClip' in u.SystemLibrary.get_command_line()
TIMING='-LOKTimingReview' in u.SystemLibrary.get_command_line()
EXPECTED=240 if PETALS else 1 if STILL else 1800
RESOLUTION=(960,540) if PETALS or TIMING else (1920,1080)
ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir()))/"LOK"
OUT=ROOT/("TimingReview" if TIMING else "PetalReview" if PETALS else "HeroReview" if STILL else "Renders")/time.strftime("Zone01_%Y%m%d_%H%M%S")

def finished(executor,success):
    frames=list(OUT.glob("*.png"))
    report={"status":"PASS" if success and len(frames)==EXPECTED else "FAIL",
            "executor_success":success,"frames":len(frames),"expected_frames":EXPECTED,
            "resolution":list(RESOLUTION),"fps":30,"duration_seconds":EXPECTED/30,
            "render_wall_seconds":round(time.time()-STATE["started"],2),
            "output":str(OUT),"errors":STATE["errors"],
            "note":"Offline MRQ render time is not real-time exhibition FPS."}
    (ROOT/("render_timing_review.json" if TIMING else "render_petal_clip.json" if PETALS else "render_hero_still.json" if STILL else "render_zone01.json")).write_text(json.dumps(report,indent=2),encoding="utf-8")
    u.log("[LOK][INFO] MRQ result: "+json.dumps(report))
    u.SystemLibrary.quit_editor()

def failed(executor,pipeline,fatal,message):
    STATE["errors"].append({"fatal":fatal,"message":str(message)})
    u.log_error("[LOK][ERROR] MRQ: "+str(message))

def main():
    try:
        OUT.mkdir(parents=True,exist_ok=True)
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
        levels.load_level("/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight")
        if PETALS:
            import petal_clusters
            garden=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors() if a.get_actor_label()=='LuminousGarden')
            comps=[c for c in garden.get_components_by_class(u.InstancedStaticMeshComponent) if 'Blossoms' in c.get_name()]
            actual=[{'name':c.get_name(),'count':c.get_instance_count(),'mesh':c.static_mesh.get_path_name(),'material':c.get_material(0).get_path_name()} for c in comps]
            assert len(comps)==2 and sum(c.get_instance_count() for c in comps)==len(petal_clusters.layout()[0]),actual
            assert all(c.static_mesh.get_name()=='Plane' and c.get_material(0).get_name()=='M_Tree_SoftPetal' for c in comps),actual
            (ROOT/'petal_reload_verified.json').write_text(json.dumps({'status':'PASS','components':actual},indent=2))
        for actor in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors():
            if actor.get_actor_label()=="ExhibitController":
                settings=actor.get_editor_property("playback_settings")
                settings.set_editor_property("auto_play",False)
                actor.set_editor_property("playback_settings",settings)
        subsystem=u.get_editor_subsystem(u.MoviePipelineQueueSubsystem)
        queue=subsystem.get_queue()
        if queue.get_jobs():
            raise RuntimeError("Dedicated render queue must be empty")
        job=queue.allocate_new_job(u.MoviePipelineExecutorJob)
        job.job_name="Zone01_60s_Review"
        job.map=u.SoftObjectPath("/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight.LV_Zone01_Moonlight")
        job.sequence=u.SoftObjectPath("/Game/LOK/Sequences/Zone01/LS_Zone01_Opening.LS_Zone01_Opening")
        config=job.get_configuration()
        output=config.find_or_add_setting_by_class(u.MoviePipelineOutputSetting)
        output.output_directory=u.DirectoryPath(str(OUT))
        output.output_resolution=u.IntPoint(*RESOLUTION)
        output.file_name_format="Zone01.{frame_number}"
        output.zero_pad_frame_numbers=4
        output.use_custom_frame_rate=True
        output.output_frame_rate=u.FrameRate(30,1)
        output.flush_disk_writes_per_shot=True
        if STILL:
            output.use_custom_playback_range=True
            output.custom_start_frame=1650
            output.custom_end_frame=1651
        elif PETALS:
            output.use_custom_playback_range=True
            output.custom_start_frame=1500
            output.custom_end_frame=1740
        config.find_or_add_setting_by_class(u.MoviePipelineDeferredPassBase)
        config.find_or_add_setting_by_class(u.MoviePipelineImageSequenceOutput_PNG)
        aa=config.find_or_add_setting_by_class(u.MoviePipelineAntiAliasingSetting)
        aa.engine_warm_up_count=120 if STILL else 32
        aa.render_warm_up_count=32 if STILL else 8
        aa.spatial_sample_count=4 if PETALS else 32 if STILL else 1
        aa.temporal_sample_count=1
        if STILL or PETALS:
            aa.override_anti_aliasing=True
            aa.anti_aliasing_method=u.AntiAliasingMethod.AAM_NONE
        game=config.find_or_add_setting_by_class(u.MoviePipelineGameOverrideSetting)
        game.game_mode_override=u.GameModeBase
        STATE["executor"]=u.MoviePipelinePIEExecutor(subsystem)
        STATE["executor"].on_executor_finished_delegate.add_callable_unique(finished)
        STATE["executor"].on_executor_errored_delegate.add_callable_unique(failed)
        subsystem.render_queue_with_executor_instance(STATE["executor"])
        u.log("[LOK][INFO] Rendering %s frames to %s"%(EXPECTED,OUT))
    except Exception:
        u.log_error("[LOK][ERROR] "+traceback.format_exc())
        u.SystemLibrary.quit_editor()

main()
