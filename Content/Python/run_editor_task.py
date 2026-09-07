"""Launch the installed UE editor with explicit arguments (run with ordinary Python)."""
import argparse
import json
import os
from pathlib import Path
import subprocess


def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("mode",choices=["show","preview","render","runtime","niagara","build","validate","check"])
    parser.add_argument("--engine",type=Path)
    opts=parser.parse_args()
    project=Path(__file__).resolve().parents[2]
    descriptor=project/"LightOfKorea.uproject"
    version=json.loads(descriptor.read_text(encoding="utf-8-sig"))["EngineAssociation"]
    engine=opts.engine or Path(os.environ["ProgramFiles"])/"Epic Games"/("UE_"+version)
    full_editor=True
    exe=engine/"Engine/Binaries/Win64"/("UnrealEditor.exe" if full_editor else "UnrealEditor-Cmd.exe")
    if not exe.is_file():
        raise FileNotFoundError("Pass --engine with the installed Unreal Engine directory")
    log=project/"Saved/Logs"/("LOK_"+opts.mode+"_run.log")
    args=[str(exe),str(descriptor),"-unattended","-nosplash","-nosound","-nop4","-NoPythonPipInstall",
          "-DDC=InstalledNoZenLocalFallback","-ShaderWorkingDir="+str(project/"Intermediate/Shaders/LOK"),"-abslog="+str(log)]
    if opts.mode=="show":
        args += ["-ExecCmds=py import open_zone01; open_zone01.main()"]
    elif opts.mode in ("preview","render","runtime"):
        args += ["-RenderOffscreen","-ExecCmds=PixelStreaming2.Editor.AutoStreamPIE 0,py import "+opts.mode+"_zone01"]
    elif opts.mode=="niagara":
        args += ["-RenderOffscreen","-EnablePlugins=CascadeToNiagaraConverter","-ExecutePythonScript="+(project/"Content/Python/run_niagara_editor.py").as_posix()]
    else:
        args += ["-RenderOffscreen","-LOKTask="+opts.mode,"-ExecutePythonScript="+(project/"Content/Python/run_workflow_editor.py").as_posix()]
    env=os.environ.copy()
    env["UE-LocalDataCachePath"]=str(project/"DerivedDataCache")
    startup=subprocess.STARTUPINFO()
    startup.dwFlags |= subprocess.STARTF_USESHOWWINDOW
    startup.wShowWindow=3 if opts.mode=="show" else 0
    child=subprocess.Popen(args,cwd=project,env=env,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW,
                           stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
    print(json.dumps({"pid":child.pid,"mode":opts.mode,"log":str(log)}))


if __name__=="__main__":
    try:
        main()
    except Exception as exc:
        print("[LOK][ERROR] "+str(exc))
        raise
