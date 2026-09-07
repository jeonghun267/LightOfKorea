"""Open the generated scene in the user's editor without changing project settings."""
import unreal as u

def main():
    if u.EditorLoadingAndSavingUtils.get_dirty_map_packages():
        raise RuntimeError("Save the currently edited map before opening Zone01")
    levels=u.get_editor_subsystem(u.LevelEditorSubsystem)
    if not levels.load_level("/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight"):
        raise RuntimeError("Zone01 could not be opened")
    sequence=u.load_asset("/Game/LOK/Sequences/Zone01/LS_Zone01_Opening")
    u.LevelSequenceEditorBlueprintLibrary.open_level_sequence(sequence)
    u.LevelSequenceEditorBlueprintLibrary.set_current_time(1650)
    camera=next(a for a in u.get_editor_subsystem(u.EditorActorSubsystem).get_all_level_actors()
                if a.get_actor_label()=="CAM_Zone01_Main")
    levels.pilot_level_actor(camera)
    levels.editor_set_game_view(True)
    u.log("[LOK][INFO] Saved Zone01 hero composition opened at 55s with the central Cine Camera piloted.")
