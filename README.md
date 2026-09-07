# 매일 아침 철학 명언 텔레그램 봇

매일 한국시간 오전 5시 30분, 동서양 철학자의 명언을 하나씩 골라 텔레그램으로 보내줍니다.
같은 명언은 모든 명언을 다 보낼 때까지 다시 나오지 않습니다.

## 1. 텔레그램 봇 준비

1. 텔레그램에서 **@BotFather** 검색 → `/newbot` 명령으로 봇 생성 → **토큰(TELEGRAM_BOT_TOKEN)** 발급받기
2. 만든 봇과 대화를 한 번 시작(아무 메시지나 전송)
3. 아래 주소에 방금 받은 토큰을 넣어 브라우저로 접속해서 **chat id(TELEGRAM_CHAT_ID)** 확인
   `https://api.telegram.org/bot<토큰>/getUpdates`
   → 응답 JSON에서 `"chat":{"id": 123456789, ...}` 부분의 숫자가 chat id

## 2. 명언 데이터 만들기 (최초 1회, 또는 갱신하고 싶을 때)

```bash
pip install -r requirements.txt
python crawl_quotes.py
```

(`requests`만 사용하며 위키인용집 API를 직접 호출하는 방식이라, 별도 컴파일 도구 없이
Windows/Mac/Linux 어디서든 바로 설치·실행됩니다.)

`data/quotes.json` 파일이 생성됩니다. 이 파일은 GitHub 저장소에 커밋해서 올려두세요.
(매일 아침 발송할 때는 크롤링을 다시 하지 않고, 이미 만들어둔 이 파일에서 고릅니다.
 크롤링을 매일 새벽에 돌리면 사이트 접속 실패 등으로 발송이 안 될 위험이 있어서
 "한 번 모아두고 매일 그 안에서 고르는" 방식으로 설계했습니다.)

## 3. GitHub 저장소 설정

1. 이 폴더 전체를 새 GitHub 저장소에 push
2. 저장소 **Settings → Secrets and variables → Actions** 에서 다음 2개 등록
   - `TELEGRAM_BOT_TOKEN`
   - `TELEGRAM_CHAT_ID`
3. **Actions** 탭에서 `Daily Philosophy Quote` 워크플로가 보이면 준비 완료
   (`workflow_dispatch`가 있어서 "Run workflow" 버튼으로 지금 바로 테스트 전송도 가능)

이후로는 매일 한국시간 05:30(±몇 분, 무료 요금제 특성상 약간 지연 가능)에 자동으로
명언이 텔레그램으로 전송됩니다.

## 4. 명언 목록을 더 추가하고 싶다면

`crawl_quotes.py` 상단의 `PHILOSOPHERS` 딕셔너리에 위키인용집(wikiquote.org) 영문판
문서 제목을 추가한 뒤 `python crawl_quotes.py` 를 다시 실행하면 됩니다.
(기존에 이미 보낸 명언 기록(`data/sent.json`)은 그대로 유지되므로 새로 추가된
명언부터 순환에 섞여 들어갑니다.)
