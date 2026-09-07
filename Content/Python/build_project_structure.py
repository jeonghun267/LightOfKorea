"""Create LOK directories only; never create or modify Unreal binary assets."""

import logging
from pathlib import Path


LOGGER = logging.getLogger("LOK.structure")
if not LOGGER.handlers:
    handler = logging.StreamHandler()
    handler.setFormatter(logging.Formatter("[LOK][%(levelname)s] %(message)s"))
    LOGGER.addHandler(handler)
LOGGER.setLevel(logging.INFO)
LOGGER.propagate = False

DIRECTORIES = (
    "Python",
    "LOK/Maps/Master", "LOK/Maps/Zone01",
    "LOK/Blueprints/Core", "LOK/Blueprints/Environment",
    "LOK/Blueprints/Interaction", "LOK/Blueprints/Zones/Zone01",
    "LOK/Materials/Master", "LOK/Materials/Instances",
    "LOK/Materials/Functions", "LOK/Materials/MPC",
    "LOK/Niagara/Zone01", "LOK/Sequences/Zone01",
    "LOK/Audio", "LOK/Cameras", "LOK/Dev",
)


def project_directory():
    try:
        import unreal
    except ModuleNotFoundError as exc:
        if exc.name != "unreal":
            raise
        return Path(__file__).resolve().parents[2]
    return Path(unreal.Paths.convert_relative_path_to_full(
        unreal.Paths.project_dir())).resolve()


def main():
    try:
        project = project_directory()
        if not (project / "LightOfKorea.uproject").is_file():
            raise RuntimeError("Expected the LightOfKorea project directory")
        content = (project / "Content").resolve()
        content.relative_to(project)
        targets = []
        for relative in DIRECTORIES:
            target = (content / relative).resolve()
            target.relative_to(content)
            if target.exists() and not target.is_dir():
                raise RuntimeError("Directory conflicts with file: " + relative)
            targets.append(target)
        created = 0
        for target in targets:
            if not target.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                created += 1
        missing = [str(p.relative_to(content)) for p in targets if not p.is_dir()]
        if missing:
            raise RuntimeError("Missing directories: " + ", ".join(missing))
        LOGGER.info("PASS: %d required directories; %d newly created. "
                    "This validates folders only, not Zone01 assets.",
                    len(targets), created)
        return {"status": "PASS", "directories": len(targets), "created": created}
    except Exception:
        LOGGER.exception("Structure creation failed; existing assets were not deleted")
        raise


if __name__ == "__main__":
    main()
