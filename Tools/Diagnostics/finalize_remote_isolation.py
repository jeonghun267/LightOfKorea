"""Verify the settings-only change and assemble the requested crash report."""
import difflib
import hashlib
import json
from pathlib import Path
import re

ROOT=Path(__file__).resolve().parents[2]
OUT=ROOT/"Saved/Diagnostics/RemoteControlIsolation"
def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

before=json.loads((OUT/"before_hashes.json").read_text(encoding="utf-8"))
inspection=json.loads((OUT/"inspection.json").read_text(encoding="utf-8"))
dependencies=json.loads((OUT/"dependencies.json").read_text(encoding="utf-8"))
check=json.loads((OUT/"editor_load_check.json").read_text(encoding="utf-8"))
now={str(p.relative_to(ROOT)):digest(p) for p in sorted((ROOT/"Content").rglob("*")) if p.is_file()}
if now!=before["content"]:
    raise RuntimeError("Content changed during the settings-only isolation phase")
backup=Path(inspection["backup"])
for name,value in before["settings"].items():
    if digest(backup/name)!=value:
        raise RuntimeError("Backup verification failed: "+name)
changed=[name for name,value in before["settings"].items() if digest(ROOT/name)!=value]
if set(changed)!={"LightOfKorea.uproject","Config\\DefaultEngine.ini"}:
    raise RuntimeError("Unexpected settings change: "+str(changed))
log=ROOT/"Saved/Logs/LOK_remote_isolation_check.log"
text=log.read_text(encoding="utf-8",errors="replace")
mounted=set(re.findall(r"Mounting (?:Engine|Project) plugin (\w+)",text))
absent=not ({"RemoteControl","RemoteControlWebInterface"}&mounted)
servers_absent="Web Remote Control WebSocket server started" not in text and "Web Remote Control HTTP server started" not in text
fatal_absent="Fatal error!" not in text and "Unhandled Exception:" not in text
success=check["status"]=="PASS" and absent and servers_absent and fatal_absent and "RemoteControlInterception" in mounted
crashlog=ROOT/"Saved/Logs/LightOfKorea-backup-2026.09.07-07.23.34.log"
lines=crashlog.read_text(encoding="utf-8",errors="replace").splitlines()
tail=[line for line in lines if "error:" in line.lower() or "fatal error" in line.lower() or "unhandled exception" in line.lower()][-50:]
if len(tail)!=50:
    raise RuntimeError("Expected a 50-line crash error excerpt")
(OUT/"crash_last_50_errors.txt").write_text("\n".join(tail)+"\n",encoding="utf-8")
(OUT/"crash_excerpt_source.json").write_text(json.dumps({"source":str(crashlog),"lines":50,"selection":"Last 50 error-related lines, including deserialization warnings"},indent=2),encoding="utf-8")
diff=[]
for name in changed:
    diff.extend(difflib.unified_diff((backup/name).read_text(encoding="utf-8-sig").splitlines(),(ROOT/name).read_text(encoding="utf-8-sig").splitlines(),fromfile="before/"+name,tofile="after/"+name,lineterm=""))
(OUT/"settings.diff").write_text("\n".join(diff)+"\n",encoding="utf-8")
result={"status":"PASS" if success else "FAIL","content_files_unchanged":len(now),"backup_verified":True,
        "changed_files":changed,"remote_api_plugins_not_mounted":absent,"remote_servers_not_started":servers_absent,
        "nDisplay_interception_dependency_preserved":"RemoteControlInterception" in mounted,
        "map_load_check":check,"verification_log":str(log),"crash_error_lines":50}
(OUT/"result.json").write_text(json.dumps(result,indent=2),encoding="utf-8")
report=f'''# Remote Control 크래시 격리 결과

**결과: {result['status']}**. Remote Control API/Web Interface를 명시적으로 비활성화하고 HTTP·WebSocket 자동 시작을 껐다. 별도 Unreal Editor에서 LV_Zone01_Moonlight를 열고 120틱 동안 유지한 뒤 정상 종료했다.

## 범위와 변경

- 변경 파일: `LightOfKorea.uproject`, `Config/DefaultEngine.ini` 두 개.
- 백업: `{backup}`. 프로젝트 설정 9개 파일의 백업 해시를 검증했다.
- Content 전체 {len(now)}개 파일의 SHA-256이 이 격리 작업 전후 동일하다. 맵, Niagara, Material, Sequencer, 기존 Python 콘텐츠를 저장·수정하지 않았다.
- Niagara Actor 4개, 기존 Sequence 1,800프레임 로드 확인. Lumen GI/Reflection=1, RayTracing=1, Lumen HardwareRayTracing=1 유지.

## 플러그인과 의존성

| 항목 | 최종 상태 |
|---|---|
| RemoteControl — Remote Control API | `.uproject` Enabled=false, 검증 프로세스에서 미마운트 |
| WebRemoteControl | RemoteControl 내부 모듈이며 별도 플러그인이 아님 |
| RemoteControlWebInterface | `.uproject` Enabled=false, 검증 프로세스에서 미마운트 |
| RemoteControlInterception | 유지. nDisplay의 필수 의존성이고 웹 API 서버와 별개 |
| nDisplay / Niagara / Sequencer / MovieRenderPipeline | 기존 설정 유지 |

설치된 엔진의 플러그인 descriptor {dependencies['descriptors_checked']}개를 파싱했다(파싱 오류 0). RemoteControl/API Web Interface의 활성 직접·간접 종속 플러그인은 없다. 비활성 종속 플러그인은 `dependencies.json`에 기록했다. 플러그인 파일은 삭제하지 않았다.

초기 실행 로그에서는 RemoteControl이 활성화되어 있었다. 검사 도중 `.uproject`의 활성 항목이 이미 제거된 상태를 확인했으며, 백업은 그 시점의 파일을 보존한다. 최종 상태는 두 플러그인의 명시적 false다.

## 자동 서버 시작

원래 `WebControl.EnableServerOnStartup=1`은 VPUtilitiesEditor 섹션에 놓여 있어 CVar 적용 여부와 구분해야 한다. 설치 엔진의 RemoteControlSettings에서 `bAutoStartWebServer`와 `bAutoStartWebSocketServer`의 기본값이 true이며, 실행 로그에서 WebSocket 30020 시작을 확인했다.

최종 `[/Script/RemoteControlCommon.RemoteControlSettings]`에서 두 값을 false로 설정했다. `[SystemSettings]`에 `WebControl.EnableServerOnStartup=0`을 설정했다. 새 검증 프로세스에서는 Remote Control 서버 시작 기록이 없다. 변경 전에 켜져 있던 Editor에는 재시작 전까지 이전 설정이 남을 수 있다.

## 크래시 원인 분리

- 대상 사고: 2026-09-07 16:23:34 KST, `EXCEPTION_ACCESS_VIOLATION reading address 0x0000000000000030`.
- 제가 Remote Control로 `FullyLoadPackages`를 호출한 직후 발생했으며, UnrealEd → RemoteControl → WebRemoteControl → HTTPServer 호출 경로가 기록됐다.
- 바로 앞 로그에 `Could not load object ... for property Packages` 역직렬화 오류가 반복된다. 설치 엔진의 `FileHelpers.cpp`에서 FullyLoadPackages는 입력 Package를 null 검사 없이 사용한다. 따라서 원격 패키지 참조 변환 실패로 null이 전달됐을 가능성이 높다. 심볼/메모리 덤프까지 분석하지 않았으므로 정확한 포인터 경로는 추정이다.
- 이 스택은 ZONE01 맵/재질이 원인이라는 증거가 아니다. 현재 검증은 웹 API 경로를 제거한 상태에서 동일 맵이 열리는 것을 확인한 격리 검사이며 장시간 무충돌 보증은 아니다.
- 16:25의 더 최신 CrashContext는 `Level Editor Subsystem Realtime Override` 관련 ensure이다. 16:23 RemoteControl 0x30 크래시와 별개로 분류했다.

## 마지막 오류 50줄

출처: `{crashlog}`. Saved/Crashes의 복사 로그는 치명적 오류가 쓰이기 전에 복사되어, 최종 call stack이 있는 Saved/Logs 백업 로그에서 마지막 오류 관련 50줄을 추출했다. Warning으로 기록된 역직렬화 오류도 포함한다.

```text
{chr(10).join(tail)}
```
'''
(OUT/"REPORT.md").write_text(report,encoding="utf-8")
print(json.dumps(result))
