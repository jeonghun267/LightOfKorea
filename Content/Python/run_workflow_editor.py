"""Use an RHI-enabled editor when checking maps that contain GPU Niagara."""
import traceback
import unreal as u
try:
    command=u.SystemLibrary.get_command_line()
    if "-LOKTask=check" in command:
        import check_zone01_idempotency
        check_zone01_idempotency.main()
    elif "-LOKTask=build" in command:
        import build_zone01
        build_zone01.main()
    elif "-LOKTask=validate" in command:
        import validate_zone01
        validate_zone01.main()
    else:
        raise RuntimeError("Specify -LOKTask=build, validate, or check")
except Exception:
    u.log_error("[LOK][ERROR] "+traceback.format_exc())
finally:
    u.SystemLibrary.quit_editor()
