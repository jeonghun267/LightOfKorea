"""Launch a bounded local Unreal Python task, without Remote Control."""
import json, os, subprocess, sys
from pathlib import Path
root=Path(__file__).resolve().parents[1]
version=json.loads((root/'LightOfKorea.uproject').read_text(encoding='utf-8-sig'))['EngineAssociation']
engine=Path(os.environ['ProgramFiles'])/'Epic Games'/('UE_'+version)
script=(root/sys.argv[1]).resolve()
assert script.is_relative_to(root) and script.is_file()
log=root/'Saved/Logs'/('LOK_'+script.stem+'.log')
args=[str(engine/'Engine/Binaries/Win64/UnrealEditor.exe'),str(root/'LightOfKorea.uproject'),
 '-unattended','-RenderOffscreen','-nosplash','-nosound','-nop4','-NoPythonPipInstall',
 '-DDC=InstalledNoZenLocalFallback','-ShaderWorkingDir='+str(root/'Intermediate/Shaders/LOK'),
 '-abslog='+str(log),'-ExecCmds=py import runpy; runpy.run_path('+repr(script.as_posix())+')']
env=os.environ.copy();env['UE-LocalDataCachePath']=str(root/'DerivedDataCache')
args.extend(sys.argv[2:])
startup=subprocess.STARTUPINFO();startup.dwFlags|=subprocess.STARTF_USESHOWWINDOW;startup.wShowWindow=0
p=subprocess.Popen(args,cwd=root,env=env,startupinfo=startup,creationflags=subprocess.CREATE_NO_WINDOW,
 stdout=subprocess.DEVNULL,stderr=subprocess.DEVNULL)
print(json.dumps({'pid':p.pid,'log':str(log)}))
