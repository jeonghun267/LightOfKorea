"""Niagara authoring and GPU placements use the full Editor with Slate and RHI."""
import traceback
import unreal as u
try:
    import build_zone01_niagara
    build_zone01_niagara.main()
except Exception:
    u.log_error("[LOK][ERROR] "+traceback.format_exc())
finally:
    u.SystemLibrary.quit_editor()
