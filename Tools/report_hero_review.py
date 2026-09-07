"""Write a review record from saved test/render evidence."""
import json
from pathlib import Path
root=Path(__file__).resolve().parents[1]
saved=root/'Saved/LOK'
def read(name):return json.loads((saved/name).read_text(encoding='utf-8-sig'))
build=read('hero_build.json');scope=read('hero_file_scope.json')
runtime=read('runtime_zone01.json');checks=read('validation_zone01.json')
repeat=read('hero_idempotency.json');render=read('render_hero_still.json')
image=next(Path(render['output']).glob('*.png'))
passed=sum(x['status']=='PASS' for x in checks['checks'])
text=f'''# ZONE01 — 달항아리 중심 구도 수정본

원본 `{build['map']}`에 저장한 시각 개선본이다. 24·28·35mm를 같은 시간에서 비교하고, 바닥·계단·항아리를 함께 담는 중앙 28mm 구도를 채택했다.

![Unreal Engine 실제 렌더](<{image.as_posix()}>)

## 반영한 내용

- 카메라: Y=0 정면 축, 60초 동안 3m 전진. 기존 카메라 바인딩·컷·재생 길이 유지.
- 달항아리: 43,200 triangle 연속 곡면, 좁은 굽·넓은 몸통·짧은 목·두께 있는 매끄러운 입구, 미세 비대칭. 아이보리 도자기와 시간에 따라 변하는 먹/꽃 문양. 전체 발광 대신 조명과 제한된 rim emission.
- 나무: 6그루의 곡선·테이퍼 가지, 선택적인 뿌리→가지 light flow, 꽃 인스턴스 2,592개. 구형 부품으로 만든 기존 입구와 직선 숲은 숨김 처리.
- 세로 빛: 12개로 축소. 고정 seed로 위치·폭·길이를 달리하고 부드러운 양끝 및 시간 fade 적용.
- 한옥: 오른쪽 긴 용마루·네 면의 지붕 경사·들린 처마·기둥·보강 보, 후경 낮은 곡선 지붕선.
- 바닥/공간: glossy ripple 바닥, 중앙 계단의 ivory 선, low mist 3층과 volumetric fog, Deep Navy 배경. 청록/보라는 보조색으로 완화.
- 입자: 기존 Niagara 4개를 유지하면서 Particle Soft 재질에서 전경/중경/후경의 크기·밝기·흐름·밀도를 구분.

## 검증 근거

- 구조 검사: {passed}/{len(checks['checks'])} PASS.
- 시각 패스 2회 반복: {repeat['status']}, Actor ID와 Sequence 바인딩 동일, Actor ID {repeat['actor_count']}개 중복 없음.
- Native PIE 65초: {runtime['status']}, 60초 시퀀스 끝 도달, 카메라 이동, Niagara 4개 활성. 이 검사는 hero-2에 수행했으며 이후 변경은 roof detail와 배경 light 배치이다.
- 기존 Blueprint/Niagara/MPC 11개 파일: {scope['status']}, SHA256 동일. 기존 에셋 중 변경은 map, sequence 시각 값, particle material 3개.
- 최신 정지 프레임 MRQ: {render['status']}, 1920×1080, 32 spatial samples. 전체 60초 최종 버전 영상 출력이나 전시장 장비 성능 테스트는 수행하지 않았다.

구도와 형상의 개선 결과이며, 레퍼런스의 복잡한 건축·수목 디테일까지 완성한 것으로 평가하지 않는다. 외부 Marketplace 모델을 사용하지 않고 프로젝트 내에서 생성한 메시와 재질을 사용했다.

## 복구와 재실행

백업: `Saved/Backups/HeroPolish_20260907_164501`.

일반 Python에서 `Tools/run_hero_task.py Content/Python/polish_zone01.py`로 다시 적용한다. 기존 원형 제작기 `build_zone01_garden.py`를 직접 실행하면 이전 블록아웃이 복원되므로 사용하지 않는다.

Remote Control 크래시 격리 결과와 마지막 오류 50줄: [진단 보고서](../../Diagnostics/RemoteControlIsolation/REPORT.md). RemoteControl API/Web Interface는 계속 비활성이다.
'''
out=saved/'HeroReview/REVIEW.md';out.write_text(text,encoding='utf-8')
print(json.dumps({'report':str(out),'image':str(image)},ensure_ascii=False))
