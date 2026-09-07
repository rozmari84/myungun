"""
동서양 철학자 명언 크롤러 (lxml/wikiquote 라이브러리 없이 requests만 사용)
- 영어 위키인용집(en.wikiquote.org)의 MediaWiki API로 문서 원문(wikitext)을 받아
  '* ' 로 시작하는 명언 줄만 뽑아 data/quotes.json 으로 저장한다.

사용법:
    pip install -r requirements.txt
    python crawl_quotes.py
"""

import json
import re
import time
import hashlib
from pathlib import Path

import requests

API_URL = "https://en.wikiquote.org/w/api.php"

# 위키인용집(영문판) 기준 문서 제목. 필요하면 자유롭게 추가/삭제하세요.
PHILOSOPHERS = {
    "서양": [
        "Socrates",
        "Plato",
        "Aristotle",
        "Marcus Aurelius",
        "Seneca the Younger",
        "Epictetus",
        "René Descartes",
        "Baruch Spinoza",
        "Immanuel Kant",
        "Friedrich Nietzsche",
        "Arthur Schopenhauer",
        "Søren Kierkegaard",
        "Jean-Paul Sartre",
        "Albert Camus",
        "Bertrand Russell",
        "Blaise Pascal",
        "Voltaire",
        "John Locke",
    ],
    "동양": [
        "Confucius",
        "Laozi",
        "Zhuangzi",
        "Mencius",
        "Sun Tzu",
        "Gautama Buddha",
        "Wang Yangming",
        "Han Fei",
        "Xunzi",
    ],
}

# 명언이 아닐 확률이 높은 섹션(주석 처리된 인용, 남이 한 말, 관련 항목 등)은 건너뜀
EXCLUDE_SECTION_KEYWORDS = [
    "about",
    "see also",
    "external links",
    "misattributed",
    "disputed",
    "quotes about",
    "sourced",  # 이건 살리는 경우도 있지만 애매하면 제외 목록에 둠
]

MAX_QUOTES_PER_PERSON = 15
OUTPUT_PATH = Path(__file__).parent / "data" / "quotes.json"


def make_id(philosopher: str, quote: str) -> str:
    raw = f"{philosopher}::{quote}".encode("utf-8")
    return hashlib.sha1(raw).hexdigest()[:12]


def fetch_wikitext(title: str) -> str:
    params = {
        "action": "query",
        "prop": "revisions",
        "titles": title,
        "rvslots": "main",
        "rvprop": "content",
        "format": "json",
        "formatversion": "2",
    }
    resp = requests.get(API_URL, params=params, timeout=15, headers={"User-Agent": "philosophy-quote-bot/1.0"})
    resp.raise_for_status()
    data = resp.json()
    pages = data.get("query", {}).get("pages", [])
    if not pages or "revisions" not in pages[0]:
        return ""
    return pages[0]["revisions"][0]["slots"]["main"]["content"]


def clean_wikitext(text: str) -> str:
    # 각주/참조 제거
    text = re.sub(r"<ref[^>]*/?>.*?(</ref>|$)", "", text, flags=re.DOTALL)
    text = re.sub(r"<ref[^>]*/>", "", text)
    # 템플릿 {{...}} 제거 (중첩 없이 단순 처리)
    text = re.sub(r"\{\{[^{}]*\}\}", "", text)
    # 링크 [[a|b]] -> b, [[a]] -> a
    text = re.sub(r"\[\[[^\]|]*\|([^\]]*)\]\]", r"\1", text)
    text = re.sub(r"\[\[([^\]]*)\]\]", r"\1", text)
    # 외부 링크 [http... text] -> text
    text = re.sub(r"\[https?://\S+\s+([^\]]*)\]", r"\1", text)
    text = re.sub(r"\[https?://\S+\]", "", text)
    # 볼드/이탤릭 마크업 제거
    text = text.replace("'''", "").replace("''", "")
    # HTML 태그 제거
    text = re.sub(r"<[^>]+>", "", text)
    return text.strip()


def parse_quotes(wikitext: str) -> list[str]:
    quotes = []
    current_section = ""
    for raw_line in wikitext.splitlines():
        line = raw_line.strip()

        if line.startswith("=="):
            current_section = line.strip("= ").lower()
            continue

        if any(kw in current_section for kw in EXCLUDE_SECTION_KEYWORDS):
            continue

        # 최상위 글머리 기호(* )만 채택. '**'(하위 항목, 보통 출처)는 제외.
        if line.startswith("* ") and not line.startswith("**"):
            content = clean_wikitext(line[2:])
            if content:
                quotes.append(content)

    return quotes


def crawl() -> list[dict]:
    collected = []
    seen_texts = set()

    for tradition, names in PHILOSOPHERS.items():
        for name in names:
            print(f"[크롤링 중] {tradition} - {name}")
            try:
                wikitext = fetch_wikitext(name)
                raw_quotes = parse_quotes(wikitext)
            except Exception as e:
                print(f"  -> 실패: {e}")
                continue

            count_for_person = 0
            for q in raw_quotes:
                if count_for_person >= MAX_QUOTES_PER_PERSON:
                    break
                if not q or len(q) < 15 or len(q) > 400:
                    continue
                if q in seen_texts:
                    continue
                seen_texts.add(q)
                count_for_person += 1

                collected.append(
                    {
                        "id": make_id(name, q),
                        "philosopher": name,
                        "tradition": tradition,
                        "quote": q,
                    }
                )

            print(f"  -> {count_for_person}개 수집")
            time.sleep(0.5)  # 위키인용집 서버 배려용 딜레이

    return collected


def main():
    quotes = crawl()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(quotes, f, ensure_ascii=False, indent=2)

    print(f"\n총 {len(quotes)}개의 명언을 수집해서 {OUTPUT_PATH} 에 저장했습니다.")


if __name__ == "__main__":
    main()
