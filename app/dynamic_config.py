"""런타임에 변경 가능한 설정값 관리 (파일 기반)."""
import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_CONFIG_FILE = Path(__file__).parent / "data" / "dynamic_config.json"


def get_code(default: str) -> str:
    try:
        if _CONFIG_FILE.exists():
            return json.loads(_CONFIG_FILE.read_text(encoding="utf-8")).get("chat_room_code", default)
    except Exception as e:
        logger.warning("dynamic_config read error: %s", e)
    return default


def set_code(code: str) -> None:
    _CONFIG_FILE.parent.mkdir(parents=True, exist_ok=True)
    data = {}
    if _CONFIG_FILE.exists():
        try:
            data = json.loads(_CONFIG_FILE.read_text(encoding="utf-8"))
        except Exception:
            pass
    data["chat_room_code"] = code
    _CONFIG_FILE.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")
    logger.info("dynamic_config updated: chat_room_code=%s", code)
