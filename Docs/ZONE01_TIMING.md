# ZONE01 단계별 Reveal과 공간 반응

기존 60초 전시 Controller, 카메라 키, 모델, 나무 인스턴스 및 Niagara 시뮬레이션을 유지한다. Sequencer의 기존 MPC 곡선과 재질 밝기 게이트를 연결하는 시각 보정이다. 추가 표면 요청에 따라 기존 달항아리 Key/Fill의 밝기와 조명 적용 대상도 조정했다.

| 시간 | 연출 |
|---|---|
| 1–5초 | 달항아리 윤곽의 제한된 Fresnel 발광 |
| 5–12초 | 표면 색과 기존 Key/Fill 조명 등장 |
| 10–15초 | 먹 매화 문양이 표면을 따라 드러남 |
| 15–19초 | 기존 MoonHalo 시스템 등장 |
| 19–22초 | 달 주변 입자의 약한 전조 |
| 22초 | 바닥 중앙축 (-600, 0)에서 첫 Ripple |
| 약 27–38초 | 초속 440cm의 파면을 따라 앞→뒤 나무, 한옥, 입자 활성화 |
| 46초 이후 | 첫 파동보다 약한 두 번째 파동, 기존 밝기 계층 유지 |

나무 세 열의 바닥 기준 도착 시각은 약 27.1 / 31.0 / 35.7초다. 가지와 입자는 각 월드 위치에 따른 공간적 차이를 유지한다. 재질 반응과 한옥·주변 조명 키는 같은 파동 원점과 속도를 사용한다. 새로운 게임 이벤트나 Tick Controller는 추가하지 않는다.

`MoonSurfaceReveal`, `MoonPatternReveal`, `MoonHaloReveal`을 기존 MPC에 추가했다. 기존 `ExhibitTime`, `RippleStartTime`, `RippleStrength`와 함께 모든 시간을 Sequencer에서 재현한다. 밝기 곡선은 선형 키를 사용해 자동 탄젠트의 과도한 밝기 상승을 피한다.

재생 종료 때 과거 기본값(ExhibitTime=50, ForestGlow=0.65)으로 복귀하는 것을 방지하도록 MPC·조명·카메라 섹션은 Keep State를 사용한다. 이는 마지막 hero 구도와 밝기를 유지하기 위한 시각 상태 보정이며 Niagara 시뮬레이션 모듈은 그대로다.

## 재현

Editor를 저장하고 닫은 뒤 일반 Python에서 다음 명령을 순서대로 실행한다. 각 Editor 프로세스가 종료된 후 다음 명령을 실행해야 한다.

```powershell
python Tools/run_hero_task.py Content/Python/polish_zone01_timing.py
python Tools/run_hero_task.py Content/Python/polish_jar_surface.py
python Tools/run_hero_task.py Content/Python/render_zone01.py -LOKTimingReview
```

저장된 프로젝트를 감상할 때는 위 제작 스크립트를 실행할 필요가 없다. 렌더 성공과 시각 검토 결과는 `Saved/LOK/render_timing_review.json` 및 후속 검증 기록을 확인한다. 생성 이미지 자체는 Unreal 장면의 최종 렌더 증거가 아니다.

## 달항아리 표면 텍스처

기본 제공 imagegen 도구로 제작한 단일 atlas를 사용한다. 왼쪽 패널은 유약 질감, 오른쪽 패널은 먹 매화 문양이며, 기존 달항아리 모델에 월드 좌표로 투영한다. 전체 표면 Emissive는 사용하지 않고 월드 좌표 기반 윤곽 발광만 유지한다.

기존 두 달항아리 조명은 channel 1로 분리하고 Moon만 channel 0/1을 받는다. Key/Fill은 5~12초에 Sequencer Intensity로 등장한다. 주변 전시가 밝아지지 않도록 해당 두 조명의 volumetric contribution은 0, indirect intensity는 0.05로 제한한다. 표면을 가리는 주변 모델의 큰 투영 그림자를 피하도록 이 두 조명의 그림자만 끄고 기존 전시장 조명·안개는 유지했다. Lighting Channels는 동적 불투명 표면의 직접 조명에 적용되므로 안개 및 간접광 제한을 별도로 설정했다. [Epic 공식 설명](https://dev.epicgames.com/documentation/unreal-engine/using-lighting-channels-in-unreal-engine)

- 소스: `Content/LOK/Textures/Source/T_MoonJar_GlazeInk_Atlas.png`
- Unreal 에셋: `/Game/LOK/Textures/T_MoonJar_GlazeInk_Atlas`
- 재질: `/Game/LOK/Materials/Hero/M_Hero_Ceramic`

생성 프롬프트:

> Create a production material texture atlas for a Korean moon jar in Unreal Engine. Asset type: flat texture, NOT a picture of a jar or a scene. Output landscape 2:1 image, preferably 2048x1024 or higher. TWO EXACTLY EQUAL SQUARE PANELS side by side, with no gap, no border, no labels, no text. LEFT HALF: an evenly lit flat seamless ivory-white porcelain glaze surface in grayscale, richly detailed with subtle small crystalline cloudy blooms, fine kiln speckling and delicate softly interlocking mineral patterns evocative of the lunar surface. Many small organic pale gray-white patches, restrained contrast, no large black blotches, no lighting gradient or shadows, no cracks, no relief illusion. RIGHT HALF: an exquisite grayscale Korean ink-wash plum blossom painting on pure solid white background. Elegant naturally tapered branching limbs enter from lower left and lower right and spread asymmetrically into central height; exceptionally fine twigs, detailed five-petal plum blossoms, tiny buds, gentle variation in ink density, dry brush texture and soft ink diffusion. White open negative space at center and upper center, leave 8 percent pure white blank margin around every edge so it can be projected softly on curved porcelain. The branches must be slender charcoal-gray; flowers delicate, many small handpainted blooms, not heavy black silhouettes. Purpose: left half sampled as ceramic micro/mid surface texture, right half sampled as a separate animated ink mask. Both panels flat front-on orthographic material data, absolutely no object, jar, environment, human, pedestal, logo, caption, diagram or perspective.
