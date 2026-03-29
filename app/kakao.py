"""Kakao i 오픈빌더 스킬 서버 유틸리티."""


def extract_image_url(payload: dict) -> str | None:
    """
    Kakao 스킬 서버 페이로드에서 이미지 URL 추출.

    Kakao 오픈빌더는 사용자가 업로드한 이미지를 action.params 아래에
    imageUrl 키를 포함한 딕셔너리 형태로 전달합니다.
    파라미터 이름은 오픈빌더 설정에 따라 달라질 수 있어 순회하여 탐색합니다.
    """
    try:
        params = payload.get("action", {}).get("params", {})
        for value in params.values():
            if isinstance(value, dict) and "imageUrl" in value:
                return value["imageUrl"]
    except (AttributeError, TypeError):
        pass
    return None


def build_simple_text_response(text: str) -> dict:
    """Kakao i 오픈빌더 2.0 simpleText 응답 포맷 생성."""
    return {
        "version": "2.0",
        "template": {
            "outputs": [
                {
                    "simpleText": {
                        "text": text
                    }
                }
            ]
        }
    }
