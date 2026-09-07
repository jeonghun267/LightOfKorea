"""Render a saved Zone01 preview using an offscreen Unreal Editor viewport."""
import traceback
import time
from pathlib import Path
import unreal as u

STATE = {"ticks": 0, "requested": False, "started": time.time()}
OUT = Path(u.Paths.convert_relative_path_to_full(u.Paths.project_saved_dir())) / "LOK" / "Zone01_Preview_55s.png"


def finish():
    u.unregister_slate_post_tick_callback(STATE["handle"])
    u.SystemLibrary.quit_editor()


def tick(delta):
    try:
        STATE["ticks"] += 1
        if STATE["ticks"] == 240:
            u.AutomationLibrary.take_high_res_screenshot(1600, 900, str(OUT), camera=STATE["camera"])
            STATE["requested"] = True
            u.log("[LOK][INFO] Preview screenshot requested")
        if STATE["requested"] and OUT.exists() and OUT.stat().st_mtime >= STATE["started"] and STATE["ticks"] > 270:
            u.log("[LOK][INFO] Preview saved: " + str(OUT))
            finish()
        elif STATE["ticks"] > 1200:
            raise RuntimeError("Preview screenshot timeout")
    except Exception:
        u.log_error("[LOK][ERROR] " + traceback.format_exc())
        finish()


def main():
    try:
        OUT.parent.mkdir(parents=True, exist_ok=True)
        levels = u.get_editor_subsystem(u.LevelEditorSubsystem)
        if not levels.load_level("/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight"):
            raise RuntimeError("Zone map load failed")
        actors = u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
        STATE["camera"] = next(a for a in actors if a.get_actor_label() == "CAM_Zone01_Main")
        sequence=u.load_asset("/Game/LOK/Sequences/Zone01/LS_Zone01_Opening")
        if not u.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence):
            raise RuntimeError("Could not open the opening sequence for visual evaluation")
        u.LevelSequenceEditorBlueprintLibrary.set_current_time(1650)
        cam = STATE["camera"]
        u.EditorLevelLibrary.set_level_viewport_camera_info(cam.get_actor_location(), cam.get_actor_rotation())
        STATE["handle"] = u.register_slate_post_tick_callback(tick)
        u.log("[LOK][INFO] Waiting for scene rendering to warm up")
    except Exception:
        u.log_error("[LOK][ERROR] " + traceback.format_exc())
        u.SystemLibrary.quit_editor()
        raise


main()
