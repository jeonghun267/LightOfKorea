"""Apply visual timing state retention then verify the full native autoplay."""
import traceback
import unreal as u
try:
    import polish_zone01_timing
    polish_zone01_timing.main()
    import runtime_zone01
except Exception:
    u.log_error('[LOK][TIMING PLAYBACK] '+traceback.format_exc())
    u.SystemLibrary.quit_editor()
