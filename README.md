# 빛의 대한민국 : 달빛에서 네온까지

Unreal Engine 기반 한국형 이머시브 미디어아트 전시 프로젝트입니다. 현재는 ZONE 01 **달빛의 한국**을 구현한 60초 오프닝 프로토타입입니다.

거대한 달항아리, 한옥, 빛의 숲, 반사 바닥과 안개를 중심으로 구성합니다. 기존 Niagara·Material·Sequencer 연출과 함께 가지 끝의 soft glow·꽃잎 군집을 포함합니다. 외부 Marketplace 에셋에 의존하지 않습니다.

달항아리의 유약·먹 매화 표면과 단계별 Reveal, 중앙 Ripple에 이어지는 공간 반응을 적용했습니다. [연출 타이밍과 표면 제작 기록](Docs/ZONE01_TIMING.md)에서 세부 내용을 확인할 수 있습니다.

## 실행

1. Unreal Engine **5.7**을 설치합니다. 제작·검증 버전은 5.7.4입니다.
2. 저장소를 복제하고 `LightOfKorea.uproject`를 엽니다.
3. `/Game/LOK/Maps/Zone01/LV_Zone01_Moonlight` 맵을 엽니다. 기본 시작 맵 `Main`에는 전시가 표시되지 않습니다.
4. **Play**를 누르면 전시 카메라로 60초 오프닝이 재생됩니다. 처음에는 어둡게 시작합니다.
5. 완성 구도는 `LS_Zone01_Opening`의 55초(1650프레임)에서 확인할 수 있습니다.

## 프로젝트 구성

- `Content/LOK`: 맵, Blueprint, Material, Niagara, 메시, Sequencer 에셋
- `Content/Python`: Unreal Editor 제작·시각 보정·검증 자동화
- `Config`: 프로젝트 설정
- `Tools`: 실행 및 진단 도구
- `Docs`: 실행 안내와 작업 기록

현재 저장된 장면은 바로 열어 감상할 수 있습니다. 생성 스크립트를 다시 실행할 필요는 없습니다. 에셋을 갱신할 때는 편집 내용을 저장하고 Editor를 닫아 파일 잠금을 피하세요.

## 검증과 범위

나무 보정 후 맵을 새 프로세스에서 다시 불러와 인스턴스와 재질을 확인했고, 50~58초 구간 240프레임을 렌더했습니다. 해당 보정에서 기존 Blueprint·Niagara·Sequencer 에셋은 유지했습니다. 자세한 제작 및 검증 이력은 [작업 상태](Docs/WORK_STATUS.md), 재생 방법은 [실행 안내](Docs/ZONE01_RUN.md)를 참고하세요.

`Saved`, `Intermediate`, `DerivedDataCache`와 로컬 백업·렌더 출력은 저장소에서 제외합니다. 문서에 등장하는 `Saved/...` 검증 보고서와 미리보기는 제작 환경의 로컬 결과이며 저장소에는 포함되지 않습니다.

Remote Control API와 Web Interface는 크래시 격리 후 비활성화했습니다. ZONE 2–5, 오디오 믹싱, 센서 입력 및 현장 nDisplay/DMX 구성은 아직 구현하지 않았습니다. 실제 전시장 해상도·장비에서 별도 성능 검증이 필요합니다.

## 개발 흐름

- `jeonghun` 브랜치에서 작업하고, 빌드·실행으로 에러가 없는지 확인한 뒤 `main`에 머지합니다.
- `main`은 항상 실행 가능한 상태로 유지합니다.
