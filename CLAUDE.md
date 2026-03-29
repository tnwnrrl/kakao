# 일산 와이시티 입주민 인증 챗봇

## 프로젝트 개요
카카오 채널 챗봇으로, 입주민이 아파트너 앱 스크린샷을 전송하면 자동으로 인증하여 단톡방 링크와 입장코드를 제공합니다.

## 인증 조건
1. 스크린샷에 "와이시티" 아파트명 표시
2. 동·호수 정보 확인 가능
3. 상태바 시계와 업로드 시각 차이 **10분 이내**

## 실행 방법
```bash
# 의존성 설치
pip install -r requirements.txt

# 환경변수 설정
cp .env.example .env
# .env 파일에 실제 값 입력

# 서버 실행
uvicorn app.main:app --reload --port 8000
```

## 환경변수 (.env)
| 변수 | 설명 |
|------|------|
| `ANTHROPIC_API_KEY` | Anthropic API 키 |
| `CHAT_ROOM_LINK` | 카카오 오픈채팅방 URL |
| `CHAT_ROOM_CODE` | 채팅방 입장코드 |
| `TIME_TOLERANCE_MINUTES` | 시간 허용 오차 (기본: 10분) |

## 테스트
```bash
# 헬스 체크
curl http://localhost:8000/health

# 이미지 포함 웹훅 테스트
curl -X POST http://localhost:8000/webhook \
  -H "Content-Type: application/json" \
  -d '{
    "action": {
      "params": {
        "image": {
          "imageUrl": "https://실제-이미지-URL"
        }
      }
    }
  }'
```

## Kakao i 오픈빌더 설정
1. https://i.kakao.com 에서 챗봇 생성
2. 스킬 서버 URL: `https://your-server.com/webhook` (HTTPS 필수)
3. 이미지 타입 파라미터 이름: `image`
4. 시나리오 블록에서 스킬 연결
5. 채널 설정에서 이미지 전송 허용

## 주요 제약사항
- Kakao 스킬 서버 응답 제한: **5초** (Claude 호출은 4초 제한 적용)
- HTTPS 필수 (Kakao 요건)
- 배포 시 Nginx + Let's Encrypt 권장

## 파일 구조
```
app/
├── main.py       # FastAPI 앱, 웹훅 엔드포인트, 검증 로직
├── vision.py     # Claude Vision API 연동, 스크린샷 분석
├── kakao.py      # Kakao 응답 빌더, 페이로드 파서
└── config.py     # 환경변수 설정 (Pydantic Settings)
```
