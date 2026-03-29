"""Kakao i 오픈빌더 스킬 서버 유틸리티."""
import json
import re


def extract_image_url(payload: dict) -> str | None:
    """
    Kakao 스킬 서버 페이로드에서 이미지 URL 추출.

    일반 이미지: action.params.*.imageUrl (dict)
    보안 이미지(sys.plugin.secureimage): action.params.*.secureUrls (JSON 문자열)
        형식: {"secureUrls": "List(url1, url2, ...)", ...}
    """
    try:
        params = payload.get("action", {}).get("params", {})
        for value in params.values():
            # 일반 이미지
            if isinstance(value, dict) and "imageUrl" in value:
                return value["imageUrl"]
            # 보안 이미지 플러그인 (JSON 문자열)
            if isinstance(value, str):
                try:
                    data = json.loads(value)
                    secure_urls = data.get("secureUrls", "")
                    # "List(url1, url2, ...)" 형식에서 첫 번째 URL 추출
                    match = re.search(r"List\((.+?)\)", secure_urls)
                    if match:
                        return match.group(1).split(",")[0].strip()
                except (json.JSONDecodeError, AttributeError):
                    pass
    except (AttributeError, TypeError):
        pass
    return None


def build_simple_text_response(text: str, retry_block_id: str | None = None) -> dict:
    """Kakao i 오픈빌더 2.0 simpleText 응답 포맷 생성."""
    template: dict = {
        "outputs": [
            {
                "simpleText": {
                    "text": text
                }
            }
        ]
    }
    if retry_block_id:
        template["quickReplies"] = [
            {
                "label": "다시 시도",
                "action": "block",
                "blockId": retry_block_id,
            }
        ]
    return {"version": "2.0", "template": template}
