"""Back up project settings and collect read-only crash/dependency evidence."""
import datetime
import hashlib
import json
from pathlib import Path
import re
import shutil
import subprocess
import xml.etree.ElementTree as ET

ROOT=Path(__file__).resolve().parents[2]
ENGINE=Path("C:/Program Files/Epic Games/UE_5.7/Engine")
OUT=ROOT/"Saved/Diagnostics/RemoteControlIsolation"

def digest(path):
    h=hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda:stream.read(1024*1024),b""):
            h.update(block)
    return h.hexdigest()

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    stamp=datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    backup=ROOT/"Saved/Backups"/("RemoteControlIsolation_"+stamp)
    previous=OUT/"inspection.json"
    if previous.exists():
        backup=Path(json.loads(previous.read_text(encoding="utf-8"))["backup"])
    else:
        backup.mkdir(parents=True,exist_ok=False)
        shutil.copy2(ROOT/"LightOfKorea.uproject",backup/"LightOfKorea.uproject")
        shutil.copytree(ROOT/"Config",backup/"Config")
    originals=[ROOT/"LightOfKorea.uproject",*sorted((ROOT/"Config").rglob("*"))]
    settings={str(p.relative_to(ROOT)):digest(p) for p in originals if p.is_file()}
    content={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/"Content").rglob("*")) if p.is_file()}
    baseline=OUT/"before_hashes.json"
    current={"settings":settings,"content":content}
    if baseline.exists():
        if json.loads(baseline.read_text(encoding="utf-8"))!=current:
            raise RuntimeError("Files changed since backup; preserve original baseline and inspect the changes")
    else:
        baseline.write_text(json.dumps(current,indent=2),encoding="utf-8")
    plugin_paths=subprocess.run(["rg","--files",str(ENGINE/"Plugins"),"-g","*.uplugin"],capture_output=True,text=True,check=True).stdout.splitlines()
    plugins={}
    errors=[]
    for value in plugin_paths:
        path=Path(value)
        try:
            source=path.read_text(encoding="utf-8-sig")
            # Unreal descriptors permit JSON comments and trailing commas.
            source=re.sub(r'("(?:\\.|[^"\\])*")|(/\*.*?\*/|//[^\r\n]*)',lambda m:m.group(1) or "",source,flags=re.S)
            source=re.sub(r',\s*([}\]])',r'\1',source)
            data=json.loads(source)
            plugins[path.stem]={"path":str(path),"default":data.get("EnabledByDefault"),
                "dependencies":[p for p in data.get("Plugins",[]) if p.get("Enabled",False)],
                "modules":[m["Name"] for m in data.get("Modules",[])]}
        except Exception as exc:
            errors.append({"path":str(path),"error":str(exc)})
    # Use a known pre-change startup log as actual activation evidence.
    startup=ROOT/"Saved/Logs/LOK_show_run.log"
    mounted=set(re.findall(r"Mounting (?:Engine|Project) plugin (\w+)",startup.read_text(encoding="utf-8",errors="replace")))
    targets={"RemoteControl","RemoteControlWebInterface"}
    dependents=[]
    for name,data in plugins.items():
        deps=[d for d in data["dependencies"] if d["Name"] in targets]
        if deps:
            dependents.append({"plugin":name,"currently_mounted":name in mounted,"dependencies":deps,"descriptor":data["path"]})
    # Transitive reverse dependency closure, including plugins not currently active.
    closure=set(targets)
    changed=True
    while changed:
        changed=False
        for name,data in plugins.items():
            if name not in closure and any(d["Name"] in closure and not d.get("Optional",False) for d in data["dependencies"]):
                closure.add(name)
                changed=True
    dependency_report={"descriptors_checked":len(plugins),"parse_errors":errors,
        "targets":{n:plugins[n] for n in targets},"direct_dependents":dependents,
        "active_transitive_dependents":sorted((closure-targets)&mounted),
        "nDisplay":plugins["nDisplay"],"RemoteControlInterception":plugins["RemoteControlInterception"],
        "mounted_plugins":sorted(mounted),"activation_log":str(startup)}
    (OUT/"dependencies.json").write_text(json.dumps(dependency_report,indent=2),encoding="utf-8")
    crashes=[]
    for path in (ROOT/"Saved/Crashes").glob("*/CrashContext.runtime-xml"):
        xml=ET.parse(path).getroot()
        error=xml.findtext(".//ErrorMessage","")
        stack=xml.findtext(".//CallStack","")+xml.findtext(".//PCallStack","")
        logs=list(path.parent.glob("*.log"))
        text="\n".join(p.read_text(encoding="utf-8",errors="replace") for p in logs)
        relevant="RemoteControl" in stack+text and ("0x0000000000000030" in error+text or "0x30" in error+text)
        crashes.append({"path":str(path),"modified":datetime.datetime.fromtimestamp(path.stat().st_mtime).isoformat(),
            "error":error,"remote_control_0x30":relevant,"logs":[str(p) for p in logs]})
        if relevant and logs:
            source=max(logs,key=lambda p:p.stat().st_mtime)
            lines=source.read_text(encoding="utf-8",errors="replace").splitlines()
            error_lines=[line for line in lines if "Error:" in line or "Fatal error" in line or "Unhandled Exception" in line]
            tail=error_lines[-50:]
            (OUT/"crash_last_50_errors.txt").write_text("\n".join(tail)+"\n",encoding="utf-8")
            (OUT/"crash_excerpt_source.json").write_text(json.dumps({"source":str(source),"lines":len(tail),"selection":"Last 50 error-tagged lines in the matching crash log"},indent=2),encoding="utf-8")
            shutil.copy2(path,OUT/"CrashContext_RemoteControl.runtime-xml")
    report={"backup":str(backup),"backed_up_files":len(settings),"content_files_hashed":len(content),
            "active_transitive_dependents":dependency_report["active_transitive_dependents"],
            "crashes":sorted(crashes,key=lambda c:c["modified"],reverse=True),"descriptor_parse_errors":len(errors)}
    (OUT/"inspection.json").write_text(json.dumps(report,indent=2),encoding="utf-8")
    print(json.dumps({k:v for k,v in report.items() if k!="crashes"}))
    print(json.dumps([{**c,"error":c["error"].splitlines()[0]} for c in report["crashes"][:3]]))

if __name__=="__main__":
    main()
