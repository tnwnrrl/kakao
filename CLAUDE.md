# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 프로젝트 개요
카카오 채널 챗봇. 입주민이 아파트너 앱 마이페이지 스크린샷을 전송하면 Claude Vision으로 분석하여 "일산 와이시티" 단지 여부, 동·호수, 상태바 시계를 추출하고 10분 이내 촬영 여부를 검증한 뒤 오픈채팅방 링크와 참여코드를 제공한다.

## 개발 명령어

```bash
# 로컬 실행
pip install -r requirements.txt
cp .env.example .env  # 실제 값 입력 후
uvicorn app.main:app --reload --port 8000

# 헬스 체크
curl http://localhost:8000/health

# 웹훅 수동 테스트
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{"action": {"params": {"image": {"imageUrl": "https://실제-이미지-URL"}}}}'

# NAS 배포
./deploy.sh
```

## 환경변수 (.env)
| 변수 | 설명 |
|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `CHAT_ROOM_LINK` | 카카오 오픈채팅방 URL |
| `CHAT_ROOM_CODE` | 채팅방 참여코드 (정기 교체됨) |
| `TIME_TOLERANCE_MINUTES` | 시간 허용 오차 (기본: 10분) |
| `MODEL` | Claude 모델 ID (기본: claude-haiku-4-5-20251001) |

## 아키텍처

### 요청 흐름
```
Kakao 채널 → /webhook (main.py)
  → extract_image_url() (kakao.py)  # 일반/보안 이미지 URL 추출
  → analyze_screenshot() (vision.py) # Claude Vision → VerificationResult
  → 검증 로직 (main.py)             # is_ycity → 동호수 → 상태바 → 시간 10분
  → build_simple_text_response()    # Kakao 2.0 응답 포맷
```

### 핵심 제약
- **Kakao 5초 타임아웃**: `asyncio.wait_for(..., timeout=4.0)`으로 Vision 호출 제한
- **Kakao 보안 CDN**: 이미지 URL 직접 참조 불가 → `httpx`로 다운로드 후 base64 변환
- **12시간제 시계**: 상태바 시간이 AM/PM 없이 표시될 수 있어 `hour+12` 후보도 검증

### 이미지 파라미터 두 가지 형식
- 일반 이미지: `action.params.*.imageUrl` (dict)
- 보안 이미지(secureimage 플러그인): `action.params.*` = JSON 문자열, `secureUrls` 키에 `List(url1, ...)` 형식

### 블록 ID (Kakao i 오픈빌더)
- `IMAGE_AUTH_BLOCK_ID`: 이미지 인증 블록 (재시도 버튼 대상)
- `CONSULT_BLOCK_ID`: "실거주자 아닐 경우" 블록 → "현재는 실거주자만 인증이 가능합니다." 응답

### 엔드포인트
- `POST /webhook` — 메인 인증 처리
- `POST /webhook/non-resident` — 실거주자 아닐 경우 안내
- `GET /health` — 헬스 체크

## 배포 환경
- **NAS**: `192.168.219.187:55` (tnwnrrl), `/volume1/homes/tnwnrrl/kakao`
- **외부 URL**: `https://kakao.mysterydam.com` (Cloudflare Tunnel)
- **Kakao 스킬 URL**: `https://kakao.mysterydam.com/webhook`
- `deploy.sh`: app/ + docker-compose.yml 전송 → `docker restart kakao-auth`
- `.env`를 변경한 경우 반드시 `docker restart kakao-auth` 필요 (환경변수는 컨테이너 시작 시점에 로드)
