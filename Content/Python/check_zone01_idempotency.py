"""Run the scene builder three times and reject duplicate actors/tracks/assets."""
import json
import traceback
from pathlib import Path
import unreal as u
import build_zone01 as b


def main():
    try:
        samples=[]
        for index in range(3):
            b.main()
            actors=b.ACTORS.get_all_level_actors()
            ids=sorted(str(t) for a in actors for t in a.tags if str(t).startswith("LOK.ID."))
            if len(ids)!=len(set(ids)):
                raise RuntimeError("Duplicate actor IDs")
            sequence=u.load_asset(b.BASE+"/Sequences/Zone01/LS_Zone01_Opening")
            content=Path(u.Paths.project_content_dir())/"LOK"
            samples.append({"actor_ids":ids,"assets":sorted(str(p.relative_to(content)) for p in content.rglob("*") if p.suffix in [".uasset",".umap"]),
                            "bindings":len(sequence.get_bindings()),"tracks":len(sequence.get_tracks())})
            del actors
        if not all(s==samples[0] for s in samples[1:]):
            raise RuntimeError("Scene structure changed across repeated builds")
        out=Path(u.Paths.project_saved_dir())/"LOK"/"idempotency_zone01.json"
        out.write_text(json.dumps({"status":"PASS","runs":3,"samples":samples},ensure_ascii=False,indent=2),encoding="utf-8")
        u.log("[LOK][INFO] Idempotency PASS: 3 runs, stable actors, assets and sequence counts")
        import validate_zone01
        validate_zone01.main()
    except Exception:
        u.log_error("[LOK][ERROR] "+traceback.format_exc())
        raise


if __name__=="__main__":
    main()
