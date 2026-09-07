"""Apply the bounded timing pass then render in the same dedicated editor."""
import traceback
import unreal as u
try:
    import polish_zone01_timing
    polish_zone01_timing.main()
    import polish_jar_surface
    polish_jar_surface.main()
    import render_zone01
except Exception:
    u.log_error('[LOK][TIMING REVIEW] '+traceback.format_exc())
    u.SystemLibrary.quit_editor()
