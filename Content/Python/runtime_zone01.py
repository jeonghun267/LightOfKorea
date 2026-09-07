"""Read-only 65-second PIE autoplay check with measured editor frame intervals."""
import json
import statistics
import time
import traceback
from pathlib import Path
import unreal as u

S={"start":time.perf_counter(),"last":None,"intervals":[],"samples":[],"next_sample":0,"errors":[]}
OUT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir()))/"LOK"/"runtime_zone01.json"
LEVELS=u.get_editor_subsystem(u.LevelEditorSubsystem)

def finish(error=None):
    if error:
        S["errors"].append(error)
    samples=S["samples"]
    intervals=sorted(S["intervals"])
    progressed=any(s["sequence_frame"]>=1770 for s in samples)
    moved=len(samples)>1 and samples[0]["camera_position"]!=samples[-1]["camera_position"]
    activated={name for s in samples for name,v in s["niagara"].items() if v["active"]}
    report={"status":"PASS" if progressed and moved and len(activated)==4 and not S["errors"] else "FAIL",
            "autoplay_reached_final_second":progressed,"camera_moved":moved,
            "niagara_active_systems":sorted(activated),"samples":samples,"errors":S["errors"],
            "performance":{"measurement":"PIE Slate post-tick wall intervals after 5 seconds; shared GPU with user's open editor",
                           "frame_samples":len(intervals),
                           "mean_frame_ms":round(statistics.mean(intervals)*1000,2) if intervals else None,
                           "p95_frame_ms":round(intervals[int((len(intervals)-1)*.95)]*1000,2) if intervals else None,
                           "note":"Not a deployment benchmark or isolated GPU timing; target hardware/resolution must be measured separately."}}
    OUT.write_text(json.dumps(report,indent=2),encoding="utf-8")
    u.log("[LOK][INFO] Runtime check: "+report["status"])
    LEVELS.editor_request_end_play()
    u.unregister_slate_post_tick_callback(S["handle"])
    u.SystemLibrary.quit_editor()

def tick(delta):
    try:
        now=time.perf_counter()
        if now-S["start"]>180:
            raise RuntimeError("PIE runtime timeout")
        world=u.get_editor_subsystem(u.UnrealEditorSubsystem).get_game_world()
        if not world:
            return
        elapsed=u.GameplayStatics.get_time_seconds(world)
        if S["last"] and elapsed>5:
            S["intervals"].append(now-S["last"])
        S["last"]=now
        if elapsed>=S["next_sample"]:
            controllers=u.GameplayStatics.get_all_actors_of_class(world,u.LevelSequenceActor)
            controller=next(a for a in controllers if "LOK.ID.ExhibitController" in [str(t) for t in a.tags])
            player=controller.get_editor_property("sequence_player")
            camera=next(a for a in u.GameplayStatics.get_all_actors_of_class(world,u.CineCameraActor)
                        if "LOK.ID.CAM_Zone01_Main" in [str(t) for t in a.tags])
            niagara={}
            for actor in u.GameplayStatics.get_all_actors_of_class(world,u.NiagaraActor):
                comp=actor.get_component_by_class(u.NiagaraComponent)
                niagara[comp.get_asset().get_name()]={"active":comp.is_active(),
                    "rate":comp.get_variable_float("User.SpawnRate"),
                    "intensity":comp.get_variable_float("User.Intensity")}
            p=camera.get_actor_location()
            pc=u.GameplayStatics.get_player_controller(world,0)
            S["samples"].append({"elapsed":round(elapsed,2),"sequence_frame":player.get_current_time().time.frame_number.value,
                "playing":player.is_playing(),"camera_position":[p.x,p.y,p.z],"niagara":niagara,
                "viewport_size":list(pc.get_viewport_size()) if pc else None})
            collection=u.load_asset('/Game/LOK/Materials/MPC/MPC_LOK_Global')
            if collection and 'MoonPatternReveal' in [str(v.get_editor_property('parameter_name')) for v in collection.get_editor_property('scalar_parameters')]:
                S['samples'][-1]['visual_controls']={name:u.MaterialLibrary.get_scalar_parameter_value(world,collection,name)
                  for name in ('ExhibitTime','MoonSurfaceReveal','MoonPatternReveal','MoonHaloReveal','ForestGlow','GroundGlow','RippleStrength')}
                u.log('[LOK][TIMING VALUES] '+json.dumps(S['samples'][-1]['visual_controls']))
                S['samples'][-1]['jar_light_intensities']={a.get_actor_label():a.get_component_by_class(u.RectLightComponent).get_editor_property('intensity')
                  for a in u.GameplayStatics.get_all_actors_of_class(world,u.RectLight) if a.get_actor_label() in ('Hero_JarKey','Hero_JarFill')}
            S["next_sample"]=elapsed+5 if elapsed<55 else elapsed+1
            u.log("[LOK][INFO] Runtime sample %.1fs frame %s"%(elapsed,S["samples"][-1]["sequence_frame"]))
        if elapsed>=65:
            finish()
    except Exception:
        error=traceback.format_exc()
        u.log_error("[LOK][ERROR] "+error)
        finish(error)

def main():
    LEVELS.load_level("/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight")
    S["handle"]=u.register_slate_post_tick_callback(tick)
    LEVELS.editor_request_begin_play()
    u.log("[LOK][INFO] Starting native autoplay runtime check")

main()
