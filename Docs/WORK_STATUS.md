# 현재 작업 상태

2026-09-07. UE 5.7.4 / 영화·TV 템플릿. 아래 최신 상태가 이전 기록보다 우선한다.

## 최신: Hero visual pass

### 추가: 단계별 Reveal / 공간 파동 / 유약·먹 표면

- `polish_zone01_timing.py`: 윤곽 1~5초, 표면 5~12초, 문양 10~15초, Halo 15~19초, 주변 입자 19초 이후. 22초 첫 바닥 파동, 46초 약한 두 번째 파동. 원점 (-600,0), 속도 440cm/s를 나무/입자/한옥 반응에 공유한다.
- 기존 MPC에 Surface/Pattern/Halo Reveal 3개 scalar 추가. 기존 Sequencer 밝기 곡선과 Niagara lifetime section 시작 시각만 보정하며, 카메라 키와 Actor transform 일치 및 2회 반복 binding/track 동일 확인. 메시는 변경하지 않는다.
- 추가 표면 요청으로 Moon 및 기존 Key/Fill 조명만 channel 1에 연결했다. Key/Fill은 1800/1100의 최종 강도로 5~12초에 등장하며, 두 조명의 안개 기여·주변 투영 그림자를 끄고 간접광은 0.05로 제한했다. 맵 변경은 이 조명 설정이며, 모델/카메라/나무 인스턴스 배치는 그대로다.
- `polish_jar_surface.py`: 자체 생성 atlas로 유약의 색·roughness·미세 normal, 먹 매화 문양을 분리한다. 전체 Emissive 대신 월드 좌표에서 계산한 윤곽 발광만 사용. 중앙 하이라이트를 줄여 표면 디테일을 보존한다. 제작 프롬프트와 재현 절차는 `Docs/ZONE01_TIMING.md`.
- 최신 glaze-3은 잘못된 음영 패치를 방지하기 위해 항아리 몸체의 월드 공간 근사 normal에 미세 유약 굴곡을 더한다. 조명 세기를 실제 렌더로 보정했으며, `HeroReview/Zone01_20260907_181938/Zone01.1650.png`에서 표면 질감·문양·밝기 보존을 확인했다. 참조 이미지의 모든 공간 디테일을 완전히 재현했다는 의미는 아니다.
- 백업: `Saved/Backups/TimingPolish_20260907_174959`. `timing_polish.json`, `jar_surface.json`에 저장 결과. native 65초 PIE에서 카메라 이동·Niagara4·최종 프레임 도달 PASS; 실제 MPC 단계별 값도 기록(`runtime_zone01.json`). 이후 등불 재질의 초반 밝기만 추가 제한했다.
- 이전 전체 hero 생성기를 다시 실행하면 타이밍 보정 이전 조명 키로 돌아갈 수 있으므로 이 추가 보정에는 위 전용 스크립트를 사용한다. 최신 저장된 맵을 열어 감상할 때 제작 스크립트를 실행할 필요는 없다.
- 최종 검증 PASS: 65초 native PIE에서 60초 종료 후에도 마지막 MPC·조명 값을 유지하도록 Keep State 보정 확인. MPC/조명 샘플 값 189회 비교 PASS, 1,800프레임 렌더 PASS. `timing_verification.json`에 변경 범위 검증, `TimingReview/Zone01_Reveal_60s.webp`에 60초 미리보기, `TimingReview/Timing_ContactSheet.jpg`에 시간대별 실제 렌더를 저장했다. 기존 메시·Blueprint·Niagara·Config 파일 SHA256 동일. 1920×1080 최종 55초 표면 렌더는 위 `181938` 경로다.

### 추가: 나무의 빛/꽃잎 보정

- `polish_tree_petals.py`가 기존 LuminousGarden의 두 ISM 컴포넌트를 재사용한다. 2,592개 구체를 402개 soft glow/petal 카드, 18개 가지 끝 군집으로 줄였다. compact/medium/airy 3종 군집, small/medium/large 크기 분포 222/141/39.
- 줄기 반경 약 22~24%, 가지 약 25% 증가. 기존 가지 경로와 taper 유지, bark base color와 양면 처리를 조정. Moon Jar/카메라/Sequence/Niagara/BP는 그대로 유지한다.
- PerInstanceRandom + 기존 MPC ExhibitTime으로 drift, flutter, brightness breathing, fade 생애를 표현한다. 실제 Niagara spawn 로직을 추가하지 않고 가시성으로 출현/소멸을 연출한다. 색은 moon white 70%, pale cyan 24%, violet 6%; 작은 soft glow 중심, 꽃잎 일부.
- Blueprint 컴포넌트의 `set_editor_property`는 재구성을 유발해 참조가 무효화될 수 있다. 인스턴스 편집에는 native `set_cast_shadow`, `set_bounds_scale`을 사용하며 seed의 editor setter를 호출하지 않는다. 실제 reload 검사 결과는 `petal_reload_verified.json` 확인.
- 백업 `Saved/Backups/PetalPolish_20260907_172050`. `tree_petals.json`에 적용/반복 결과, `render_petal_clip.json`에 50~58초 영상 결과, `tree_petals_verification.json`에 파일 범위 및 WebP 결과를 기록한다.
- 최종 검증 PASS: 새 Editor 프로세스에서 Plane/재질/402개 인스턴스 재로드 확인. 960×540, 30fps, 240프레임 실제 렌더 완료; 52초/55초 프레임에서 가시성·드리프트 변화를 확인했다. `Saved/LOK/PetalReview/TreePetals_50-58s.webp`에 8초 미리보기 저장. 변경된 기존 에셋은 Zone01 맵·BarkFlow 재질·Curved Trees 메시 3개이며 나머지 기존 에셋 SHA256은 동일하다.

### 앞선 Hero 구성 기록

- Remote Control 크래시 격리 완료. RemoteControl/API 및 Web Interface 비활성, 자동 서버 시작 OFF. 의존성 없는 것을 확인했고 nDisplay의 RemoteControlInterception은 유지했다. `Saved/Diagnostics/RemoteControlIsolation/REPORT.md`에 원인과 마지막 오류 50줄, 검증 근거가 있다.
- 원본 `LV_Zone01_Moonlight`에 hero 구도 저장 완료: 중앙 28mm 카메라, 정면 3m dolly, 매끄러운 비대칭 달항아리 메시, 아이보리/먹·꽃 재질, 곡선 나무 6그루, 꽃 인스턴스 2592개, soft light line 12개, 우측 한옥, 중앙 계단, 반사 바닥, 낮은 안개 3층.
- 기존 Blueprint/Niagara/MPC 11개 파일 SHA256 동일. 변경된 기존 에셋은 Zone01 map, Opening sequence(카메라/안개 시각 값), Particle Soft material의 3개뿐이다. `Saved/LOK/hero_file_scope.json`.
- 저장된 hero-2 장면 native PIE 65초 PASS: 60초 시퀀스 마지막 프레임 도달, 중앙 카메라 이동, Niagara 4종 활성. 이후 hero-3은 한옥 roof geometry/detail와 배경 빛 배치만 추가 조정했다.
- Hero 프레임 1920×1080 MRQ 32 spatial samples 출력 성공. 최종 출력 경로는 `Saved/LOK/render_hero_still.json`의 output을 확인한다. MRQ 성공은 참조 이미지 수준의 완성도를 의미하지 않는다.
- 최종 반복 적용 2회 PASS (Actor ID 158개 및 바인딩 동일), 구조 검증 42/42 PASS. `hero_idempotency.json`, `validation_zone01.json` 참고. `Saved/LOK/HeroReview/REVIEW.md`에 최종 렌더와 검증 범위를 정리했다. 참조 이미지의 수목·건축 세부 묘사를 완전히 재현했다고 주장하지 않는다.
- 백업: `Saved/Backups/HeroPolish_20260907_164501` (Content/LOK와 Python 원본 및 SHA256).
- 실행: 일반 Python으로 `Tools/run_hero_task.py Content/Python/polish_zone01.py` (실제 저장), `... Content/Python/check_hero_idempotency.py` (시각 패스 2회+구조 검증), `... Content/Python/render_zone01.py -LOKHeroStill` (고품질 55초 정지 렌더).
- 기존 animation/interaction을 재구축하지 않는다. `build_zone01.main()`은 Hero 메시가 존재하면 시각 패스로 연결한다. `build_zone01_garden.main()`을 직접 실행하면 예전 prototype 구도가 복원되므로 사용하지 않는다.
- 프로젝트 작업 중 Editor가 맵/Sequence를 열고 있으면 Windows error 32로 저장이 차단된다. 사용자 작업 저장 후 정상 종료를 확인하고 구축한다. Remote Control은 사용하지 않는다.

## 이하 이전 단계 기록 (최신 상태 아님)

## 최신 사용자 수정 (16시대)

- 사용자는 현재 Main 맵만 보고 있었음. 생성 맵은 별도 Zone01. 원격 콘솔 실행은 비활성이라 변경하지 않았고, Remote Control의 제한된 LoadMap API를 확인 중이다. 원격 API는 로컬 30010에서 응답한다.
- 두 번째 사용자 이미지가 새 시각 기준: 거대한 달항아리, 발광 나무, 우측 한옥, 반사 바닥과 안개. `Docs/ZONE01_VISUAL_TARGET.md` 참고. 기존 단순 달/기둥 장면은 기능 초안이며 목표 품질 완료가 아니다.
- `build_zone01_garden.py`를 추가해 기본 메시 인스턴스로 나무/꽃잎/암석/등불/달항아리 입구를 만드는 중. `build_zone01.main()`에서 통합 실행한다. 최신 변경의 시각 확인은 아직 진행 중.
- 기존 구도의 60초 MRQ: 1920×1080/30fps/1800 PNG 성공. `render_zone01.json` 확인. 이 출력은 새 정원 구도보다 이전 버전이다.
- 기존 구도의 native PIE 65초 검사 PASS: 마지막 Sequence frame 1799, 카메라 이동, Niagara4 활성. 820×550 뷰포트에서 평균 에디터 프레임 간격 8.38ms, p95 9.39ms. 전시장/1080p 성능 보증이 아니다.
- Niagara 기본 템플릿 렌더러 + staged 렌더러가 중복되어 기본 재질이 안개를 하얗게 덮었음. `fix_renderers`는 소유 System 하위 Sprite Renderer 모두를 생성 재질로 교체함. 각 System에 Renderer 2개가 남는다. bIsEnabled는 protected여서 수정하지 않음. 최신 교체 실행 성공.
- 새 스크립트: `runtime_zone01.py`, `render_zone01.py`, `make_zone01_review.py`, `open_zone01.py`. WebP 인코딩은 최종 렌더 이후 실행해야 함.

## 생성됨

- `Content/LOK/Maps/Zone01/LV_Zone01_Moonlight.umap`, `Maps/Master/LV_LOK_Master.umap`.
- 달·한옥·빛의 숲 Root·LevelSequenceActor 기반 전시 Controller Blueprint 4종.
- Material 5종, Material Instance 5종, MPC_LOK_Global.
- Cine Camera와 60초/30fps LS_Zone01_Opening. 달광·한옥 Rim·FogDensity·MPC·카메라 키.
- 새 Zone의 PP Bloom override 0.45, 고정 노출, Volumetric Fog.

## 확인됨 / 남은 작업

- `build_zone01.py`의 엔진 실행 성공. 맵·에셋 저장 완료.
- 기본 프로젝트 Config/Main 맵은 변경하지 않음. RayTracing=1, Lumen HardwareRayTracing=1, nDisplay 활성 기존 상태 유지.
- Niagara 4종은 생성·배치 완료. 설치 엔진의 CascadeToNiagaraConverter는 제작 프로세스에서만 로드한다.
- 전시 Controller는 native Sequence autoplay 기반. 설계한 multi-zone 함수 API는 미구현.
- 첫 화면과 55초 지점의 실제 GPU 렌더 캡처 완료. 전체 재생·성능 검증은 미완료. 사용자가 열어둔 Editor는 종료하지 않음.
- `run_editor_task.py`에서 셰이더 경로를 프로젝트 내부로 지정하도록 해결함. 전역 설정 변경 없음.

## 최신 검증 (15:17 KST)

- Niagara 4종 생성 및 배치 완료. GPU Sprite, 유한 Lifetime 10초, SpawnRate 상한, 저장되는 System Fixed Bounds, 사용자 SpawnRate/Intensity/Radius(달 Halo), Sequence 수명 트랙 포함.
- Master에 Zone01 Always Loaded 연결 저장 완료. Blueprint/맵/재질/카메라/Sequence 등 구조 검사 **35 PASS / 0 FAIL**.
- Niagara가 포함된 최신 장면에서 생성 스크립트 **3회 반복 PASS**. 에셋·Actor ID·바인딩·트랙 수 동일.
- 카메라/한옥의 positional Rotator 문제를 keyword 인자로 수정. 36×20.25mm Filmback, 28mm 렌즈. 한옥 Rim 1200으로 완화.
- 인스턴스 숲 Material usage flag 저장. 기본 Config, `.uproject`, `Main.umap` 수정 없음.
- Map 전환 전 Python World 참조를 해제하도록 수정. GPU Niagara가 있는 맵은 NullRHI 대신 전체 Editor+RenderOffscreen으로 구축/검증한다.
- 최신 근거: `Saved/LOK/validation_zone01.json`, `Saved/LOK/idempotency_zone01.json`, `Saved/Logs/LOK_check_run.log`.
- 전체 상태는 PARTIAL: full multi-zone Controller 함수, 센서 추상화 API, 전체 60초 재생 QA, 성능 측정, MRQ 영상 출력은 남아 있음.
- 55초 캡처: `Saved/LOK/Zone01_Preview_55s.png`. 정지 캡처에서 달 표면·한옥·숲·바닥 파동 확인. 달 상단 여백, 한옥 지붕의 연결, 바닥 광원 밝기는 추가 시각 조정이 필요하며 Niagara 움직임은 정지 캡처만으로 통과 처리하지 않는다.

## 실행 참고

엔진은 `.uproject` EngineAssociation으로 확인한다. Python commandlet은 프로젝트·스크립트 모두 런처에서 절대경로로 해석해 전달한다. Python 내부 경로는 `unreal.Paths`로 계산한다.

권장 실행: 일반 Python에서 `Content/Python/run_editor_task.py`에 `build`, `niagara`, `check`, `validate`, `preview` 중 하나를 전달한다. 설치 엔진 경로를 자동 탐색하고 PID와 로그 경로를 반환한다. 기본 탐색 경로와 다르면 `--engine` 지정.

프로세스 환경의 `UE-LocalDataCachePath`는 프로젝트 DerivedDataCache로 지정한다. Niagara 제작 시에만 `-EnablePlugins=CascadeToNiagaraConverter` 사용. 에셋은 기본 Niagara 모듈로 구성해 converter 런타임 의존을 피한다.

현재 스크립트: `build_project_structure.py`, `build_zone01.py`, `build_zone01_niagara.py`, `validate_zone01.py`, `check_zone01_idempotency.py`, `preview_zone01.py`, `run_editor_task.py`. 상세 API 조사 결과는 `Saved/LOK/api_probe.json`; 파일 전체를 출력하지 말고 필요한 클래스/메서드만 읽는다.

기존 생성 맵 소유권 복구는 1회 완료됨. 앞으로 새 맵은 소유권 태그를 즉시 저장한다. 재실행 시 사용자 에셋 충돌을 무시하지 않는다.
