# Codex 비용·시간 절약 적용

2026-09-07 사용자가 첨부한 Astra 가이드 중 이 Unreal 작업에 적용 가능한 항목만 반영한다.

- 프로젝트 설정: `.codex/config.toml`에 `model_reasoning_effort = "low"`.
- 작업 방식: 루트 `AGENTS.md`의 간결한 응답, 부분 패치, 필요한 구간만 읽기, 중복 검증 억제, 상태 요약 저장.
- 모델은 기존 GPT-6 Astra를 유지한다. 전역 설정·요금제·API 계정·서비스 우선순위를 변경하지 않는다.
- 프로젝트 설정은 신뢰된 프로젝트에서 로드된다. 현재 실행 중인 작업의 명시적 모델/추론 선택은 우선할 수 있으므로 현재 대화의 effort를 변경했다고 보장하지 않는다.
- API 호출 코드가 없는 프로젝트이므로 가격 함수, TPM 제한 코드, Batch/Flex 호출은 추가하지 않는다. 예약 작업 역시 자동 생성하지 않는다.
- `len(prompt)//4`는 한글 토큰의 정확한 계산이 아니며, 가이드의 단가·한도를 구독 과금으로 간주하지 않는다.

공식 근거: [Config basics](https://learn.chatgpt.com/docs/config-file/config-basic), [Configuration reference](https://learn.chatgpt.com/docs/config-file/config-reference), [GPT-6 Astra](https://developers.openai.com/api/docs/models/gpt-6-astra).
