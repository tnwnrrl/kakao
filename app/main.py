"""일산 와이시티 입주민 인증 챗봇 - FastAPI 스킬 서버."""
import asyncio
import re
from datetime import datetime, timedelta, timezone

from fastapi import FastAPI, Request

from .config import settings
from .kakao import build_simple_text_response, extract_image_url
from .vision import analyze_screenshot

KST = timezone(timedelta(hours=9))

app = FastAPI(title="와이시티 입주민 인증 챗봇")


def parse_status_bar_time(time_str: str) -> tuple[int, int] | None:
    """HH:MM 또는 H:MM 형식의 상태바 시간 파싱."""
    match = re.match(r"^(\d{1,2}):(\d{2})$", time_str.strip())
    if match:
        hour, minute = int(match.group(1)), int(match.group(2))
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    return None


def is_time_within_window(status_bar_time: str, tolerance_minutes: int = 10) -> bool:
    """
    상태바 시간과 현재 KST 시간의 차이가 허용 범위 이내인지 확인.
    자정 경계(예: 23:58과 00:02)도 올바르게 처리합니다.
    """
    parsed = parse_status_bar_time(status_bar_time)
    if not parsed:
        return False

    sb_hour, sb_minute = parsed
    now = datetime.now(KST)

    # 어제/오늘/내일 기준으로 후보 시각 생성 → 현재 시각과 가장 가까운 후보 선택
    candidates = []
    for delta_days in (-1, 0, 1):
        candidate = datetime(
            now.year, now.month, now.day,
            sb_hour, sb_minute, 0,
            tzinfo=KST,
        ) + timedelta(days=delta_days)
        candidates.append(candidate)

    closest = min(candidates, key=lambda dt: abs((dt - now).total_seconds()))
    diff_seconds = abs((closest - now).total_seconds())
    return diff_seconds <= tolerance_minutes * 60


@app.post("/webhook")
async def kakao_webhook(request: Request):
    payload = await request.json()

    # 1. 이미지 URL 추출
    image_url = extract_image_url(payload)
    if not image_url:
        return build_simple_text_response(
            "📱 아파트너 앱에서 마이페이지로 이동해 주세요.\n\n"
            "마이페이지 상단에 아파트명과 동호수가 표시된 화면을 "
            "스크린샷으로 찍어 전송해 주세요.\n\n"
            "⚠️ 스크린샷은 찍은 직후 10분 이내에 전송해야 합니다."
        )

    # 2. Claude Vision 분석 (Kakao 5초 타임아웃 대응: 4초 제한)
    try:
        result = await asyncio.wait_for(
            asyncio.get_event_loop().run_in_executor(None, analyze_screenshot, image_url),
            timeout=4.0,
        )
    except asyncio.TimeoutError:
        return build_simple_text_response(
            "이미지 분석이 지연되고 있습니다. 잠시 후 다시 시도해 주세요."
        )
    except Exception:
        return build_simple_text_response(
            "이미지 분석 중 오류가 발생했습니다. 잠시 후 다시 시도해 주세요."
        )

    # 3. 검증 단계

    # 3-1. 이미지 인식 가능 여부
    if result.confidence == "unclear":
        return build_simple_text_response(
            "이미지를 인식할 수 없습니다.\n\n"
            "아파트너 앱의 입주민 정보 화면을 전체 화면으로 캡처하여 다시 보내주세요."
        )

    # 3-2. 아파트 이름 확인
    if not result.is_ycity:
        return build_simple_text_response(
            "와이시티 아파트 입주민만 가입 가능합니다.\n\n"
            "아파트너 앱에서 '일산 와이시티' 단지 화면을 캡처해 주세요."
        )

    # 3-3. 동·호수 확인
    if not result.building or not result.unit:
        return build_simple_text_response(
            "동호수 정보를 확인할 수 없습니다.\n\n"
            "동과 호수가 모두 보이도록 캡처하여 다시 보내주세요."
        )

    # 3-4. 상태바 시간 존재 여부
    if not result.status_bar_time:
        return build_simple_text_response(
            "핸드폰 상단 상태바의 시간을 확인할 수 없습니다.\n\n"
            "상태바가 보이도록 전체 화면으로 캡처하여 다시 보내주세요."
        )

    # 3-5. 시간 차이 10분 이내
    if not is_time_within_window(result.status_bar_time, settings.time_tolerance_minutes):
        now_kst = datetime.now(KST).strftime("%H:%M")
        return build_simple_text_response(
            f"스크린샷 시간({result.status_bar_time})과 현재 시간({now_kst})의 차이가 "
            f"10분을 초과합니다.\n\n"
            "지금 바로 스크린샷을 찍어서 다시 보내주세요."
        )

    # 4. 인증 성공
    return build_simple_text_response(
        f"✅ 입주민 인증 완료!\n\n"
        f"🏢 {result.building}동 {result.unit}호\n\n"
        f"아래 링크로 입장해 주세요:\n"
        f"{settings.chat_room_link}\n\n"
        f"입장 코드: {settings.chat_room_code}"
    )


@app.get("/health")
async def health():
    return {"status": "ok"}
