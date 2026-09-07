"""GPU lens comparison at a fixed existing Sequencer time; never saves assets."""
import unreal as u
import json, time, traceback
from pathlib import Path
S={'ticks':0,'started':time.time(),'shots':[]}
OUT=Path(u.Paths.project_saved_dir())/'LOK/HeroReview'
OUT.mkdir(parents=True,exist_ok=True)

def finish():
    u.unregister_slate_post_tick_callback(S['handle']);u.SystemLibrary.quit_editor()

def tick(delta):
    try:
        S['ticks']+=1;n=S['ticks']
        if n in (240,380,520):
            lens={240:24,380:28,520:35}[n]
            S['camera'].get_cine_camera_component().set_editor_property('current_focal_length',float(lens))
        if n in (310,450,590):
            lens={310:24,450:28,590:35}[n];path=OUT/('Hero_%smm_55s.png'%lens)
            u.AutomationLibrary.take_high_res_screenshot(1600,900,str(path),camera=S['camera'])
            S['shots'].append(str(path))
        if n>630 and all(Path(p).exists() and Path(p).stat().st_mtime>S['started'] for p in S['shots']) and len(S['shots'])==3:
            (OUT/'lens_review.json').write_text(json.dumps({'status':'CAPTURED','shots':S['shots'],'camera':str(S['camera'].get_actor_transform())},indent=2))
            finish()
        if n>1500:raise RuntimeError('Hero capture timeout')
    except Exception:u.log_error(traceback.format_exc());finish()

try:
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if '-LOKHeroPreviewOnly' not in u.SystemLibrary.get_command_line() and '-LOKHeroCapture' not in u.SystemLibrary.get_command_line():
        assert levels.load_level('/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight')
    actors=u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
    S['camera']=next(a for a in actors if a.get_actor_label()=='CAM_Zone01_Main')
    seq=u.load_asset('/Game/LOK/Sequences/Zone01/LS_Zone01_Opening')
    u.LevelSequenceEditorBlueprintLibrary.open_level_sequence(seq)
    u.LevelSequenceEditorBlueprintLibrary.set_current_time(1650)
    u.EditorLevelLibrary.set_level_viewport_camera_info(S['camera'].get_actor_location(),S['camera'].get_actor_rotation())
    S['handle']=u.register_slate_post_tick_callback(tick)
except Exception:u.log_error(traceback.format_exc());u.SystemLibrary.quit_editor()
