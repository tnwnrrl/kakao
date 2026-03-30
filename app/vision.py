"""Claude Vision API를 이용한 아파트너 앱 스크린샷 분석."""
import base64
import json
import logging
import re

import anthropic
import httpx
from pydantic import BaseModel

from .config import settings

logger = logging.getLogger(__name__)


EXTRACTION_PROMPT = """이 스크린샷은 아파트너 앱의 마이페이지 화면입니다.
마이페이지 상단에는 아파트 단지명과 동호수가 표시됩니다. 예: "일산와이시티 103동 4705호"

다음 정보를 추출하여 JSON 형식으로만 응답하세요. 다른 텍스트는 포함하지 마세요.

추출 항목:
1. is_ycity: 화면에 "와이시티", "Y-CITY", "와이 시티", "일산와이시티" 등이 아파트 단지명으로 표시되어 있으면 true
2. building: 동 번호 (숫자만, 예: "103"). 확인 불가면 null
3. unit: 호수 (숫자만, 예: "4705"). 확인 불가면 null
4. status_bar_time: 핸드폰 화면 상단 상태바에 표시된 시계 시간 (HH:MM 24시간 형식).
   오전/오후가 표시된 경우 24시간으로 변환. 확인 불가면 null
5. confidence: 아파트너 앱 마이페이지 화면이 명확하면 "high", 흐리거나 잘린 경우 "low",
   아파트너 앱 마이페이지 화면이 아닌 경우 "unclear"

응답 형식 (JSON만):
{
  "is_ycity": true,
  "building": "103",
  "unit": "4705",
  "status_bar_time": "16:30",
  "confidence": "high"
}"""


class VerificationResult(BaseModel):
    is_ycity: bool
    building: str | None
    unit: str | None
    status_bar_time: str | None
    confidence: str


def analyze_screenshot(image_url: str) -> VerificationResult:
    """
    아파트너 앱 스크린샷을 Claude Vision으로 분석하여 인증 정보를 추출합니다.

    Args:
        image_url: Kakao CDN에서 제공하는 이미지 URL

    Returns:
        VerificationResult: 추출된 아파트 정보 및 신뢰도
    """
    client = anthropic.Anthropic(api_key=settings.anthropic_api_key)

    # Kakao 보안 CDN URL은 직접 접근 불가 → base64로 변환
    logger.info("Downloading image: %s", image_url[:80])
    img_response = httpx.get(image_url, timeout=10)
    img_response.raise_for_status()
    img_data = base64.standard_b64encode(img_response.content).decode("utf-8")
    media_type = img_response.headers.get("content-type", "image/jpeg").split(";")[0]
    logger.info("Image downloaded: %d bytes, media_type=%s", len(img_response.content), media_type)

    logger.info("Calling Anthropic API with model=%s", settings.model)
    response = client.messages.create(
        model=settings.model,
        max_tokens=256,
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": img_data,
                        },
                    },
                    {
                        "type": "text",
                        "text": EXTRACTION_PROMPT,
                    },
                ],
            }
        ],
    )

    raw = response.content[0].text.strip()
    input_tokens = response.usage.input_tokens
    output_tokens = response.usage.output_tokens
    cost_usd = (input_tokens * 0.80 + output_tokens * 4.0) / 1_000_000
    cost_krw = cost_usd * 1350
    logger.info(
        "tokens: input=%d output=%d | cost=₩%.2f ($%.5f) | model=%s",
        input_tokens, output_tokens, cost_krw, cost_usd, settings.model,
    )
    logger.info("Anthropic response: %s", raw[:200])

    # JSON 블록이 마크다운으로 감싸진 경우 제거
    json_match = re.search(r"\{.*\}", raw, re.DOTALL)
    if json_match:
        raw = json_match.group()

    data = json.loads(raw)
    return VerificationResult(**data)
