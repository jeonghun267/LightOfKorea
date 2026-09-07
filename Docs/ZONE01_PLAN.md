# 빛의 대한민국 : 달빛에서 네온까지

ZONE 1 ‘달빛의 한국’ 설계 · 2026-09-07

> 후속 구현이 진행되었습니다. 아래는 원래 설계이며, 실제 생성·검증 상태는 [WORK_STATUS.md](WORK_STATUS.md)를 기준으로 확인합니다.

## 이번 단계의 결과

현재 프로젝트 검사, 폴더 구조 준비, 에셋 및 제어 구조 설계, 구현 순서 확정까지 진행한다. 아래 에셋은 **제작 명세**이며 아직 생성된 Unreal 에셋이 아니다. 전체 전시 완성 상태는 PARTIAL이다.

## 1. 현재 프로젝트 검사

| 항목 | 확인 결과 | 다음 제작 단계의 조치 |
|---|---|---|
| 엔진 | `.uproject`는 5.7, 설치 엔진 Build.version 및 실행 로그는 **5.7.4** | 설치 버전 유지 |
| 콘텐츠 | `Content/Main.umap`만 존재 | 별도 LOK 경로에 제작 |
| 필수 플러그인 | Niagara, MovieRenderPipeline, PythonScriptPlugin, EditorScriptingUtilities 모두 최근 실행 로그에서 Mount 확인 | 추가 설치 불필요 |
| 보조 플러그인 | SequencerScripting, ModelingToolsEditorMode, GeometryScripting도 Mount 확인 | 사용 가능한 기능만 활용 |
| DX12 / SM6 | Config 및 실제 실행 로그에서 확인 | 유지 |
| Lumen GI / Reflection | 각각 `r.DynamicGlobalIlluminationMethod=1`, `r.ReflectionMethod=1` | 장면에서 시각 검증 |
| VSM / Mesh Distance Fields | 활성화 | 유지 |
| TSR | 프로젝트 Config에 명시 없음 | 제작 단계에 AA Method 확인 후 TSR 명시 |
| Ray Tracing | `r.RayTracing=True` | 소프트웨어 Lumen을 기준으로 별도 동작 검증. 지원 활성화만으로 실제 사용 여부를 단정하지 않음 |
| Exposure / Bloom | 자동 노출 False, Bloom False, Lens Flare True | Zone의 Post Process에서 노출 고정·약한 Bloom·Lens Flare 억제 |
| nDisplay / DMX | 템플릿에서 이미 활성화. WindowsEngine.ini에 DisplayCluster 엔진 클래스 지정 | 현재는 확장 기능을 제작하지 않음. 일반 Preview 실행 시 이 설정의 영향 확인 후 필요한 부분만 조정 |
| 시작 맵 | EditorStartupMap은 Main, GameDefaultMap은 프로젝트 Config에 명시 없음 | Master 맵이 검증된 뒤 시작 맵 지정 |
| Config 중복 | 노출 범위, Local Exposure, EditorStartupMap, DX12 키 중복 | 설정 수정 시 유효값을 보존하며 중복 정리 |
| Git | 현재 저장소 아님 | Git 도입 시 캐시 제외 및 에셋 LFS 검토 |

근거: `LightOfKorea.uproject`, `Config/DefaultEngine.ini`, `Config/Windows/WindowsEngine.ini`, `Saved/Logs/LightOfKorea.log`, 설치 엔진 `Engine/Build/Build.version`. 로그 확인은 기존 실행 기록 기준이며 이번 작업에서 Editor 실행을 검증한 것은 아니다. Config 변경은 아직 수행하지 않았다.

## 2. 공간과 시각 방향

- 어두운 전시장으로 시작한다. 40m 폭 × 60m 깊이의 가상 공간을 초기 기준으로 하고, 실제 전시장 치수는 추후 보정한다. Unreal 단위는 cm이다.
- 전방 +X, 좌우 Y, 높이 Z. 중앙 달의 초기 중심은 (2000, 0, 1400), 직경 20m. 바닥 위 4m부터 달이 떠 있는 구도다.
- 관람 카메라는 X=-2200 부근, 높이 160cm에서 시작한다. 60초 동안 전진 및 완만한 측면 이동으로 구도를 바꾼다. 렌즈는 28mm에서 출발한다.
- 중앙의 달, 중경의 한옥, 양측 빛의 숲, 전경 바닥 파동으로 깊이를 만든다. 달 표면은 밝은 회백색, 그림자는 먹색, 보조광은 낮은 채도의 청색으로 제한한다.
- 한옥은 Cube 기둥·보·분절한 지붕과 끝이 올라가는 처마로 표현한다. 빛의 숲은 Cylinder 인스턴스 24~40개부터 시작한다.
- 달항아리의 정서는 둥근 볼륨, 백자 같은 미세한 표면과 여백에 반영한다. 별도 항아리 모델은 첫 제작 범위에 넣지 않는다.
- 바닥과 향후 벽의 빛은 World Position 기반 좌표계를 공유한다. 카메라 화면 좌표에 효과를 고정하지 않는다.

## 3. Content 구조

```text
Content/
├─ Python/
└─ LOK/
   ├─ Maps/
   │  ├─ Master/                 LV_LOK_Master
   │  └─ Zone01/                 LV_Zone01_Moonlight
   ├─ Blueprints/
   │  ├─ Core/                   전시 Controller, GameMode, Zone 인터페이스
   │  ├─ Environment/            한옥, 빛의 나무
   │  ├─ Interaction/            입력 소스 변환
   │  └─ Zones/Zone01/           Zone Root, Moon
   ├─ Materials/
   │  ├─ Master/
   │  ├─ Instances/
   │  ├─ Functions/
   │  └─ MPC/
   ├─ Niagara/Zone01/
   ├─ Sequences/Zone01/
   ├─ Audio/
   ├─ Cameras/
   └─ Dev/                       검증용 에셋, MRQ 프리셋
```

Master는 비 World Partition 맵으로 만들고 Zone01을 스트리밍 서브레벨로 연결한다. 초기에는 항상 로드하고 Root가 전시 활성 상태를 관리한다. 다음 Zone부터 필요에 따라 로드/언로드한다. 카메라는 Preview 전용으로 분리한다.

## 4. Blueprint 목록과 책임

| 에셋 | 주요 책임 |
|---|---|
| `BP_LOK_ExhibitController` | Zone 등록·활성화, 전시 시작/정지/리셋, 모드 관리. 개별 달·한옥의 구현은 갖지 않음 |
| `BPI_LOK_Zone` | Activate / Deactivate / Reset / SetPhase 인터페이스 |
| `BP_Zone01_Root` | Zone의 Actor 참조, Niagara 사용자 값 전달, Sequence 선택 및 상태 복원 |
| `BP_Zone01_Moon` | Sphere, 달 MI, 크기 및 로컬 표면 설정 |
| `BP_HanokSilhouette` | Cube 조합의 기둥·보·분절 지붕·처마. Construction 재실행 시 중복 없는 생성 |
| `BP_LightTree` | Cylinder 형태와 재질 파라미터 원형. 다수 배치는 Root의 ISM/HISM으로 처리 |
| `BP_LOK_InteractionManager` | Simulated 입력의 위치·강도·유효 상태를 통일. 미래 센서의 좌표 변환 접점 |
| `GM_LOK_Exhibit` | Cinematic Preview에서 불필요한 기본 Pawn·HUD 생성을 방지 |

Controller 변수: `CurrentZone=1`, `CurrentPhase=0`(0~1), `AutoPlay=true`, `InteractionEnabled=false`, `MasterIntensity=1`, `TransitionDuration=5`. 추가로 `PreviewMode`, Zone 등록 목록, 실행 중 Sequence Player 참조를 가진다.

Controller 함수: `InitializeExhibit`, `ActivateZone(ZoneIndex)`, `DeactivateZone(ZoneIndex)`, `SetPhase(Value)`, `FadeIn(Duration)`, `FadeOut(Duration)`, `ResetExhibit`. Zone 준비 완료 이후 재생하며 중복 Initialize/Play를 방지한다.

Root 변수: `IsActive`, `ZoneIntensity`, `MoonIntensity`, `ParticleIntensity`. 함수: `ActivateZone01`, `DeactivateZone01`, `ResetZone01`. 비활성화 시 발광뿐 아니라 광원, Niagara Spawn, Audio도 함께 정지한다.

Interaction 변수: `InteractionPosition`, `InteractionStrength`, `HasValidTarget`, `InputSource=Simulated`. 함수: `SetInteractionPosition`, `SetInteractionStrength`, `ClearInteraction`. 실제 입력 사용 여부와 미리 작성한 시뮬레이션 큐는 분리해, InteractionEnabled=false에서도 오프닝 파동은 재생한다.

제어 흐름: Controller → Zone 인터페이스 → Zone Root → 로컬 광원/Niagara/Audio. Interaction Manager → MPC 위치·강도 → Material, 그리고 Root를 통해 Niagara 사용자 파라미터로 전달한다. MPC가 Niagara에 자동 연결된다고 가정하지 않는다.

## 5. Material과 공통 파라미터

| 에셋 | 구현 명세 |
|---|---|
| `M_Moon_Procedural` | Default Lit 계열. 오브젝트 로컬 위치의 저주파·고주파 Noise 2종 이상 혼합. Base Color, Roughness, 절제된 Emissive와 미세 표면 노멀 변화 |
| `MI_Zone01_Moon` | 달 색·Noise Scale·대비·표면 강도. 전체가 하얗게 클리핑되지 않도록 조명과 함께 조정 |
| `M_Ground_Moonlight` / `MI_Zone01_Ground` | 먹색 바닥, Roughness 초기 0.35~0.55, 은은한 반사와 파동 함수 결합 |
| `MF_Ground_Ripple` | World Position XY와 InteractionPosition XY 사이 거리로 이동하는 Ring Mask 생성 |
| `M_Hanok_Silhouette` / `MI_Zone01_Hanok` | 거의 검은 비금속 표면. 형상은 뒤쪽 광원으로 드러냄 |
| `M_LightForest` / `MI_Zone01_LightForest` | 높이별 발광 그라데이션, 인스턴스별 밝기 차이. 개별 Actor Tick 없이 작동 |
| `M_Particle_Soft` | Halo/Ambient/Floor용 부드러운 Sprite와 Depth Fade. 발광/알파는 Niagara 값으로 제어 |
| `M_Fog_Soft` | 낮은 불투명도의 국소 안개 Sprite. 주 안개는 Height Fog가 담당 |
| `MPC_LOK_Global` | 아래 공통 상태 전달 |

MPC Scalar: `GlobalIntensity=1`, `ScenePhase=0`, `MoonGlow=0`, `GroundGlow=0`, `ParticleIntensity=0`, `TransitionAlpha=0`.

MPC Vector: `PrimaryLight=(0.82,0.88,1,1)`, `SecondaryLight=(0.12,0.22,0.40,1)`, `InteractionPosition=(0,0,0,0)`. 색은 초기 선형 값이며 캘리브레이션된 출력 색이 아니다.

재현성 및 독립 연출을 위한 추가 Scalar: `ExhibitTime=0`(초), `RippleStartTime=45`, `RippleStrength=0`, `ForestGlow=0`. InteractionStrength는 RippleStrength에 전달한다.

파동 반경은 `max(0, ExhibitTime-RippleStartTime) × Speed`로 계산하고, Distance와의 차이를 Ring Width로 마스킹한다. 발광은 `Ring × GroundGlow × RippleStrength × GlobalIntensity × TransitionAlpha`. 런타임 Time 노드만 사용하지 않아 Sequencer 탐색·반복·MRQ에서 같은 시간에 같은 모습을 재현한다.

소유권: Cinematic 모드에서는 Sequence가 애니메이션 MPC 값을 쓴다. Controller의 시작/정지/리셋은 재생 경계에서만 값을 설정한다. 향후 Interactive 모드에서는 Sequence의 같은 트랙을 비활성화하고 Manager가 쓴다. 두 시스템이 동일 값을 매 프레임 덮어쓰지 않게 한다.

## 6. Niagara 목록

아래 수치는 최적화 출발점이며 측정 결과가 아니다. 모든 시스템은 유한 수명, Spawn 상한, Fixed Bounds, 종료 시 Spawn 중지와 리셋을 갖는다.

| System / Emitter | 목적 | 초기 최대 생존 입자 | 사용자 파라미터 |
|---|---|---:|---|
| `NS_Zone01_AmbientParticles` / `NE_Zone01_Ambient` | 선택한 공간에 떠다니는 작은 빛 | 1,200 | SpawnRate, Intensity, Extent |
| `NS_Zone01_MoonHalo` / `NE_Zone01_Halo` | 달 외곽의 희박한 빛 고리 | 600 | SpawnRate, Intensity, Radius |
| `NS_Zone01_FloorLight` / `NE_Zone01_Floor` | 파동 주변의 작은 빛 입자 | 400 | SpawnRate, Intensity, InteractionPosition, Strength |
| `NS_Zone01_FogParticles` / `NE_Zone01_Fog` | 한옥 아래의 국소 안개층 | 64 | SpawnRate, Intensity, Extent |

GPU Sprite부터 검토하되 큰 Fog Sprite의 화면 점유율을 먼저 제한한다. Halo Bounds는 달 반경+최대 이동량을 포함하고 Ambient는 배치 공간+수명 동안 이동량을 포함한다. 카메라에 붙여 무한 방출하지 않는다. Sequence의 수명/활성 구간과 사용자 파라미터로 효과를 분리 제어한다. 스크럽 재현성은 고정 Seed, Desired Age 또는 Sim Cache 후보를 설치 버전에서 확인한다.

## 7. 조명·안개·카메라·60초 Sequencer

Directional Light 1개로 달빛 방향을 만들고 Sky Light 1개로 검은 영역의 형태를 최소한 보존한다. 한옥 뒤 Rect Light 1~2개, 숲의 공유 Accent Light 2~4개부터 시작한다. 나무마다 동적 광원을 만들지 않는다. Exponential Height Fog 1개에서 Volumetric Fog를 활성화하고 과도한 회색 막을 피한다.

Unbound Post Process는 고정 노출, 약한 Bloom, 낮은 Vignette, Chromatic Aberration 0, 최소 Lens Flare를 기준으로 한다. 초기 전체 샷은 깊은 초점을 유지한다. 카메라 전용 후처리에 전시 핵심 룩을 넣지 않는다.

`CAM_Zone01_Main`과 `LS_Zone01_Opening`: 60초, 30fps, 프레임 범위 [0, 1800). 한 대의 연속 카메라 이동으로 진입→달 공개→한옥 측면→전체 구도를 연결하며 Ease In/Out과 충돌 없는 경로를 확인한다.

| 시간 | 연출 | 주요 트랙 |
|---|---|---|
| 0~5초 | 암전에서 어두운 바닥과 공간이 드러남 | TransitionAlpha 0→1, Camera Transform |
| 5~15초 | 달 표면과 방향광이 서서히 드러남 | MoonGlow, 달 보조광 Intensity |
| 15~25초 | Halo와 공중 입자 등장 | Niagara 수명/활성, SpawnRate·Intensity |
| 25~35초 | 한옥 실루엣과 안개 레이어 공개 | Rim Light Intensity, Fog Density |
| 35~45초 | 양측 빛의 숲 활성화 | ForestGlow, 공유 Accent Light |
| 45~55초 | 시뮬레이션 위치에서 바닥 파동 확산 | InteractionPosition, RippleStrength, ExhibitTime, FloorLight |
| 55~60초 | 달·한옥·숲·파동 전체 구도 유지 | 느린 Camera Transform, 안정된 조명 |

Camera Cuts는 전체 재생 구간을 덮는다. 전시 암전은 MPC 발광과 실제 광원/안개를 함께 제어하고, Preview에는 필요시 Fade Track을 더한다. 마지막은 구도를 유지하며 자동 루프를 기본으로 강제하지 않는다. 반복 재생 시 별도 Fade Out 후 정지·초기값 복원·Niagara Reset·0초 이동·재생 순서를 사용해 갑작스러운 카메라 복귀를 숨긴다.

시퀀스 바인딩은 로드된 Zone Actor 기준으로 생성한다. Editor 단독 Zone 재생과 Master에서의 재생을 각각 검사한다. MRQ용 Master Sequence가 필요하면 Camera Cuts 및 서브시퀀스 연결을 검증한 뒤 추가한다.

## 8. 자동화 설계

현재 생성: `Content/Python/build_project_structure.py`. 폴더만 생성하며 일반 Python 및 Unreal Python에서 실행할 수 있다. 3회 연속 실행해 중복/삭제 없이 같은 구조를 유지하는지 확인한다.

후속 구현:

- `build_zone01.py`: 기능 노출 검사 → 기존 에셋 클래스·소유권 검사 → Material/MPC → 맵·Actor → 카메라·Sequence → 저장. 기능별 결과 기록.
- `validate_zone01.py`: 필수 에셋의 존재뿐 아니라 클래스, 컴파일 오류, Actor 참조, Sequence 시간·바인딩·키, Niagara Emitter/Renderer/수명/Bounds를 확인. 시각·성능 검증은 별도 미검증 상태로 기록.

에셋 생성은 Unreal Editor API로만 수행한다. 생성한 에셋은 `LOK.Generated` 메타데이터, Actor는 고유 태그와 안정적인 ID로 식별한다. 이름만 같은 사용자 에셋이나 클래스가 다른 충돌은 오류로 보고한다. 재실행 시 추적 중인 대상만 갱신하며 무조건 삭제/재생성하지 않는다. 랜덤 배치 Seed를 고정한다. 저장 전 검증하고 오류 시 기존 정상 에셋을 지우지 않는다. 로그 접두사는 `[LOK][INFO/WARNING/ERROR]`이며 모든 진입점에 try-except를 둔다. 경로는 Unreal Project Directory를 기준으로 계산한다.

Python은 Editor 제작 자동화 전용이고 재생 로직은 Blueprint·Material·Niagara·Sequencer에 남긴다. 런타임에서 Python에 의존하지 않는 것은 Epic의 [Python Editor Scripting 범위](https://dev.epicgames.com/documentation/en-us/unreal-engine/scripting-the-unreal-editor-using-python?application_version=5.7)에 따른다. Blueprint 실행 그래프와 Niagara 모듈 그래프의 임의 생성이 Python으로 모두 가능하다고 전제하지 않는다. 설치 버전의 API/Factory를 먼저 검사하고, 지원되지 않는 부분은 Editor에서 원형 에셋을 만든 뒤 자동 배치·파라미터화한다. 빈 에셋만 생성하고 구현 PASS로 처리하지 않는다.

## 9. 구현 순서와 단계별 통과 조건

1. **설정·공통 구조:** 플러그인 기능 노출 확인, 필요한 렌더 설정 조정, Master/Zone 맵, Controller/Root/MPC 제작. Master에서 Zone 로드와 Reset이 한 번씩 정상 작동해야 한다.
2. **Moon → Lighting → Fog:** 달 Noise 2종, 바닥, 고정 노출, 방향광, Volumetric Fog. 정지 구도에서 달 표면·실루엣 대비·밤 분위기를 먼저 통과시킨다.
3. **Hanok → Light Forest:** 기본 Cube/Cylinder 조합과 인스턴싱. 원거리에서 처마선이 읽히고 재구축 시 Actor/컴포넌트가 늘지 않아야 한다.
4. **Niagara 4종:** 분리 시스템, 유한 Spawn, User 파라미터, Bounds. 카메라 이동 시 잘림과 과도한 반투명 중첩이 없어야 한다.
5. **Ground Ripple:** 공통 좌표계와 시간, Simulated 위치 입력. 45초부터 파동이 나오고 스크럽/Reset으로 같은 상태가 재현돼야 한다.
6. **Cine Camera → Opening Sequence:** 60초 타임라인, 연속 이동, 광원/안개/입자 변화. Play·Sequencer Preview·Master 재생을 검사한다.
7. **검증·출력:** 자동화 3회 반복, Blueprint/Niagara 컴파일, 시각 QA, 1080p 성능 측정. 이후 3840×2160/30fps PNG 또는 EXR MRQ 프리셋과 짧은 샘플 렌더를 검증한다.

성능은 1080p Desktop에서 60fps(16.7ms) 권장, 안정적 30fps(33.3ms) 이상을 목표로 한다. 최종 구간과 파동/안개 중첩 구간을 포함해 `stat unit`, `stat gpu`, `ProfileGPU`로 측정하고 해상도·품질·하드웨어·워밍업 조건을 남긴다. 4K MRQ는 실시간 프레임 목표와 별도로 검증한다. Lumen 하드웨어 의존 여부는 [Epic Lumen 기술 문서](https://dev.epicgames.com/documentation/en-us/unreal-engine/lumen-technical-details-in-unreal-engine?application_version=5.7)를 참고해 실제 설정과 실행 결과로 판단한다.

Audio는 후순위로 두고 Root에 볼륨/활성화 제어 접점만 준비한다. 외부 음원 없이 MetaSounds Drone/Filtered Noise를 검토한다. Walkthrough, 실제 센서, Zone02~05, nDisplay/DMX 콘텐츠는 Zone01 검증 이후 확장한다.

## 10. 완료 조건 추적

현재 아래 14개는 모두 **미검증**이다. 설계나 폴더 생성은 장면 완성의 PASS 근거가 아니다.

| 번호 | 조건 | 최종 증거 |
|---|---|---|
| 1 | Level 오류 없이 열림 | Editor 로드와 로그 |
| 2 | Play/Preview에서 달 표시 | 두 모드 캡처 |
| 3 | 달 표면 단색 아님 | Material 그래프 및 근접 캡처 |
| 4 | Volumetric Fog 동작 | 설정과 화면 |
| 5 | Ambient Niagara 동작 | 재생 화면, 컴파일 결과 |
| 6 | 한옥 실루엣 가독성 | 중경 캡처 |
| 7 | 빛의 숲 가시성 | 35~45초 캡처 |
| 8 | 바닥 Ripple 존재 | 45~55초 재생 |
| 9 | Cine Camera 존재 | 클래스·바인딩 검사 |
| 10 | 45~60초 Sequence | 재생 범위 검사 |
| 11 | 조명·입자 시간 변화 | 키 검사 및 영상 |
| 12 | 야간 전시 분위기 | 고정 노출 전체 구도 검토 |
| 13 | 외부 Marketplace 의존 없음 | 에셋 참조 및 실행 검사 |
| 14 | Zone 확장 구조 유지 | 인터페이스·Controller 책임 검사 |
