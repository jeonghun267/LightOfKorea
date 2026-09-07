"""Read-only editor load verification. Do not save or alter content."""
import json
import time
import traceback
from pathlib import Path
import unreal as u

ROOT=Path(u.Paths.convert_relative_path_to_full(u.Paths.project_dir()))
OUT=ROOT/"Saved/Diagnostics/RemoteControlIsolation"
S={"ticks":0,"start":time.perf_counter()}

def finish(error=None):
    report={"status":"FAIL" if error else "PASS","error":error,"warmup_ticks":S["ticks"],
            "elapsed_seconds":round(time.perf_counter()-S["start"],2),**S.get("result",{})}
    (OUT/"editor_load_check.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    u.log("[LOK-ISOLATION] "+json.dumps(report))
    if "handle" in S:
        u.unregister_slate_post_tick_callback(S["handle"])
    u.SystemLibrary.quit_editor()

def tick(delta):
    try:
        S["ticks"]+=1
        if S["ticks"]>=120:
            finish()
    except Exception:
        finish(traceback.format_exc())

def main():
    try:
        levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
        if not levels.load_level("/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight"):
            raise RuntimeError("Zone01 map load failed")
        world=levels.get_current_level().get_outer()
        actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
        names=[a.get_actor_label() for a in actors]
        required=["Moon","HanokSilhouette","CAM_Zone01_Main","ExhibitController"]
        if any(name not in names for name in required):
            raise RuntimeError("Required existing actors missing")
        niagara=sum(isinstance(a,u.NiagaraActor) for a in actors)
        if niagara!=4:
            raise RuntimeError("Expected four existing Niagara actors")
        sequence=u.load_asset("/Game/LOK/Sequences/Zone01/LS_Zone01_Opening")
        if not isinstance(sequence,u.LevelSequence) or sequence.get_playback_end()!=1800:
            raise RuntimeError("Existing opening sequence did not load")
        S["result"]={"map":world.get_path_name(),"actor_count":len(actors),"niagara_actors":niagara,
            "sequence_frames":sequence.get_playback_end(),"content_saved":False,
            "cvars":{name:u.SystemLibrary.get_console_variable_int_value(name) for name in
                ["r.DynamicGlobalIlluminationMethod","r.ReflectionMethod","r.RayTracing","r.Lumen.HardwareRayTracing"]}}
        S["handle"]=u.register_slate_post_tick_callback(tick)
        u.log("[LOK-ISOLATION] Map loaded, waiting for 120 editor ticks without any content save")
    except Exception:
        finish(traceback.format_exc())

main()
