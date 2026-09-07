"""Launch an isolated full editor with the project plugin settings as saved."""
import json
import os
from pathlib import Path
import subprocess

root=Path(__file__).resolve().parents[2]
version=json.loads((root/"LightOfKorea.uproject").read_text(encoding="utf-8-sig"))["EngineAssociation"]
engine=Path(os.environ["ProgramFiles"])/"Epic Games"/("UE_"+version)
script=root/"Tools/Diagnostics/editor_remote_isolation_check.py"
log=root/"Saved/Logs/LOK_remote_isolation_check.log"
args=[str(engine/"Engine/Binaries/Win64/UnrealEditor.exe"),str(root/"LightOfKorea.uproject"),
      "-unattended","-RenderOffscreen","-nosplash","-nosound","-nop4","-NoPythonPipInstall",
      "-DDC=InstalledNoZenLocalFallback","-ShaderWorkingDir="+str(root/"Intermediate/Shaders/LOK"),
      "-abslog="+str(log),"-ExecCmds=py import runpy; runpy.run_path("+repr(script.as_posix())+")"]
env=os.environ.copy()
env["UE-LocalDataCachePath"]=str(root/"DerivedDataCache")
startup=subprocess.STARTUPINFO()
startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW
startup.wShowWindow=0
process=subprocess.Popen(args,cwd=root,env=env,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW,
                         stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({"pid":process.pid,"log":str(log)}))
