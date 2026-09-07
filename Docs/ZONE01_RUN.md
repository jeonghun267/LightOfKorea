# ZONE 01 실행 안내

현재 결과는 ‘달빛의 한국’ 60초 오프닝 프로토타입이다. 외부 Marketplace 에셋 없이 기본 오브젝트, Blueprint, Material, Niagara, Sequencer로 구성했다.

## Unreal에서 감상

1. `LightOfKorea.uproject`를 설치된 Unreal Engine 5.7로 연다.
2. Content Browser에서 `/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight`를 연다.
3. **Play**를 누르면 전시 카메라와 60초 오프닝이 자동 재생된다. 처음에는 어둡게 시작한다.
4. **Esc**로 종료한다. 반복 감상하려면 다시 Play를 누른다.

Master 맵 `/Game/LOK/Maps/Master/LV_LOK_Master`에도 Zone01이 Always Loaded로 연결되어 있다. 기본 시작 맵과 프로젝트 렌더링 설정은 그대로 유지했다.

## 타임라인

| 시간 | 연출 |
|---|---|
| 1–5초 | 달항아리 윤곽 등장 |
| 5–12초 | 유약 표면과 전용 조명 등장 |
| 10–15초 | 먹 매화 문양 Reveal |
| 15–22초 | Halo, 이어서 달 주변 입자 등장 |
| 22–38초 | 중앙 바닥 Ripple이 앞→뒤로 퍼지며 나무·한옥·입자 반응 |
| 46–60초 | 약한 두 번째 파동과 피날레 |

재생 종료 후 조명·재질·카메라는 마지막 상태를 유지한다. 상세 곡선과 표면 제작 정보는 [타이밍 보정 기록](ZONE01_TIMING.md)을 참고한다.

## 결과와 검증

- `Saved/LOK/Zone01_Opening_60s.webp`: 소리가 없는 가벼운 60초 미리보기. 640×360, 10fps.
- `Saved/LOK/render_zone01.json`: 최신 MRQ 원본 PNG 폴더와 출력 성공 여부. 원본은 1920×1080, 30fps, 1,800프레임.
- `Saved/LOK/runtime_zone01.json`: 실제 PIE 자동 재생, 카메라 이동, Niagara 활성화 기록.
- `Saved/LOK/validation_zone01.json`: 구조 검사와 별도 실행 근거.
- `Saved/LOK/idempotency_zone01.json`: 생성 스크립트 재실행 시 중복 생성 여부.

성능 기록은 820×550 PIE 뷰포트에서 다른 Editor가 열린 상태의 에디터 프레임 간격이다. 실제 전시장 GPU, 출력 해상도, 프로젝터 수에 대한 성능 보증으로 사용하면 안 된다. MRQ 출력 시간 역시 실시간 FPS와 다르다.

## 자동화 재현

일반 Python으로 `Content/Python/run_editor_task.py`에 아래 모드를 전달한다. 런처는 `.uproject`의 EngineAssociation으로 엔진 경로를 찾으며, 다른 경로라면 `--engine`을 지정한다.

| 모드 | 용도 |
|---|---|
| `build` | 생성 소유권이 있는 Zone01 에셋 구축·갱신 |
| `niagara` | Niagara/입자 Material/Sequence 수명 트랙 구축·갱신 |
| `check` | 구축 3회 반복과 구조 검사 |
| `validate` | 저장된 에셋 구조 검사 |
| `runtime` | 별도 Editor에서 65초 PIE 자동 재생 검사 |
| `render` | 별도 Editor에서 전체 60초 MRQ PNG 출력 |
| `preview` | 55초 지점 정지 화면 출력 |

`build`와 `niagara`는 순차 실행한다. 생성 맵을 사용자 Editor에서 편집 중이면 먼저 저장하고 닫아 디스크 갱신과 충돌하지 않게 한다. 검사·출력은 별도 프로세스에서 실행하며 기존 사용자 Editor를 종료하지 않는다.

MRQ 출력 완료 후 Pillow가 있는 일반 Python으로 `Content/Python/make_zone01_review.py`를 실행하면 WebP 미리보기를 만든다.

## 다음 제작 범위

국악·환경음 및 오디오 믹싱, 현장 해상도에서 성능 측정, 프로젝션 벽·바닥 규격 적용, 센서 입력과 다중 Zone Controller는 아직 구현하지 않았다. nDisplay/DMX 구성과 ZONE 2–5는 현재 범위에 포함하지 않는다.
