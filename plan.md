# 일산 와이시티 단톡방 입주민 인증 챗봇

## 목적
입주민 확인을 자동화하여 관리자 수동 검증 없이 단톡방 가입을 처리

## 인증 조건
1. 아파트너 앱 화면 스크린샷에 "와이시티" 아파트명 표시
2. 동·호수 정보 확인 가능
3. 핸드폰 상태바 시계와 업로드 시각 차이 10분 이내

## 검증 성공 시
- 카카오 오픈채팅방 링크 + 입장코드 제공

## 흐름
```
사용자 → 카카오 채널 채팅 → 스크린샷 전송
→ Kakao i 오픈빌더 (인증봇) 스킬 서버 webhook 호출
→ FastAPI POST /webhook  (kakao.mysterydam.com)
→ Claude Vision API / claude-opus-4-6 (아파트명/동호수/상태바시간 추출)
→ 검증 로직 (아파트명 + 동호수 + 시간차 ≤ 10분)
→ 카카오 응답 (링크+코드 or 오류 안내)
```

## 기술 스택
- Python FastAPI (스킬 서버)
- Claude Vision API / claude-opus-4-6 (이미지 OCR + 분석)
- Kakao i 오픈빌더 - 인증봇 (챗봇 플랫폼)
- Pydantic Settings (환경변수 관리)
- Docker + Cloudflare Tunnel (HTTPS 노출)

## 프로젝트 구조
```
kakao/
├── app/
│   ├── main.py         # FastAPI 앱 + webhook + 검증 로직
│   ├── vision.py       # Claude Vision API 연동
│   ├── kakao.py        # Kakao 응답 빌더 + 페이로드 파서
│   └── config.py       # Pydantic Settings (환경변수)
├── Dockerfile
├── docker-compose.yml  # kakao-auth(8084) + cloudflared
├── deploy.sh           # rsync → NAS → docker-compose up --build
├── plan.md
├── requirements.txt
├── .env.example
└── CLAUDE.md
```

## 환경변수 (.env)
| 변수 | 설명 |
|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `CHAT_ROOM_LINK` | 카카오 오픈채팅방 URL |
| `CHAT_ROOM_CODE` | 채팅방 입장코드 |
| `TIME_TOLERANCE_MINUTES` | 시간 허용 오차 (기본: 10분) |
| `CLOUDFLARE_TUNNEL_TOKEN` | Cloudflare Tunnel 토큰 |

## 배포 환경
- **NAS**: tnwnrrl.synology.me (192.168.219.187), SSH 포트 55, 유저 tnwnrrl
- **배포 경로**: /volume1/homes/tnwnrrl/kakao/
- **내부 포트**: 8084 → 8000
- **외부 URL**: https://kakao.mysterydam.com
- **Kakao 스킬 URL**: https://kakao.mysterydam.com/webhook

## 배포 명령
```bash
./deploy.sh
```

## 남은 작업
- [ ] Cloudflare Zero Trust에서 `kakao-tunnel` 생성
  - Subdomain: kakao / Domain: mysterydam.com
  - Service: http://kakao-auth:8000
  - 토큰 발급 후 .env에 CLOUDFLARE_TUNNEL_TOKEN 입력
- [ ] .env 파일 작성 (NAS에 직접 업로드)
- [ ] deploy.sh 실행하여 NAS 배포
- [ ] Kakao i 오픈빌더 - 인증봇 스킬 URL 등록
  - URL: https://kakao.mysterydam.com/webhook
  - 이미지 파라미터 `image` 생성
- [ ] 시나리오 블록에 스킬 연결
- [ ] 실제 아파트너 스크린샷으로 E2E 테스트

## Kakao i 오픈빌더 설정 (인증봇)
1. 스킬 > 스킬 목록 > 생성
   - 스킬명: 입주민 인증
   - URL: https://kakao.mysterydam.com/webhook
   - 이미지 파라미터 `image` 추가
2. 시나리오 > 블록에 스킬 연결
3. 채널에서 이미지 전송 허용

## 로컬 실행
```bash
pip install -r requirements.txt
cp .env.example .env  # 값 입력
uvicorn app.main:app --reload --port 8000
```
