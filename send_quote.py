"""
오늘의 철학 명언을 텔레그램으로 전송한다.
- data/quotes.json : crawl_quotes.py 로 미리 만들어둔 명언 목록
- data/sent.json    : 이미 보낸 명언의 id 기록 (중복 방지용)

전부 다 보내면 sent.json 을 초기화하고 처음부터 다시 순환한다.

필요한 환경변수:
    TELEGRAM_BOT_TOKEN  - BotFather에게서 받은 봇 토큰
    TELEGRAM_CHAT_ID    - 명언을 받을 채팅 ID (본인 계정 또는 채널)
"""

import json
import os
import random
import sys
from pathlib import Path

import requests

BASE_DIR = Path(__file__).parent
QUOTES_PATH = BASE_DIR / "data" / "quotes.json"
SENT_PATH = BASE_DIR / "data" / "sent.json"


def load_json(path: Path, default):
    if not path.exists():
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def pick_quote(quotes: list[dict], sent_ids: list[str]) -> tuple[dict, list[str]]:
    sent_set = set(sent_ids)
    unsent = [q for q in quotes if q["id"] not in sent_set]

    # 전부 다 보냈으면 한 바퀴 다 돈 것 -> 초기화하고 다시 시작
    if not unsent:
        sent_ids = []
        unsent = quotes

    chosen = random.choice(unsent)
    sent_ids = sent_ids + [chosen["id"]]
    return chosen, sent_ids


def translate_to_korean(text: str) -> str | None:
    """구글 번역 비공식 엔드포인트로 영어 -> 한글 번역. 실패하면 None 반환."""
    try:
        resp = requests.get(
            "https://translate.googleapis.com/translate_a/single",
            params={
                "client": "gtx",
                "sl": "en",
                "tl": "ko",
                "dt": "t",
                "q": text,
            },
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        # data[0] 은 [번역조각, 원문조각, ...] 형태의 리스트들의 리스트
        translated = "".join(chunk[0] for chunk in data[0] if chunk[0])
        return translated.strip() or None
    except Exception as e:
        print(f"번역 실패 (원문만 전송): {e}")
        return None


def format_message(q: dict) -> str:
    translated = translate_to_korean(q["quote"])

    body = f"“{q['quote']}”"
    if translated:
        body += f"\n\n({translated})"

    return (
        f"🌅 오늘의 철학 한마디 ({q['tradition']} 철학)\n\n"
        f"{body}\n\n"
        f"— {q['philosopher']}"
    )


def send_telegram(token: str, chat_id: str, text: str):
    url = f"https://api.telegram.org/bot{token}/sendMessage"
    resp = requests.post(url, data={"chat_id": chat_id, "text": text}, timeout=10)
    resp.raise_for_status()
    return resp.json()


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    chat_id = os.environ.get("TELEGRAM_CHAT_ID")

    if not token or not chat_id:
        print("TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID 환경변수가 필요합니다.")
        sys.exit(1)

    quotes = load_json(QUOTES_PATH, [])
    if not quotes:
        print(f"{QUOTES_PATH} 가 비어있습니다. crawl_quotes.py 를 먼저 실행하세요.")
        sys.exit(1)

    sent_ids = load_json(SENT_PATH, [])

    chosen, sent_ids = pick_quote(quotes, sent_ids)
    message = format_message(chosen)

    send_telegram(token, chat_id, message)
    save_json(SENT_PATH, sent_ids)

    print("전송 완료:")
    print(message)


if __name__ == "__main__":
    main()
