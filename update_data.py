# -*- coding: utf-8 -*-
"""
update_data.py
매일 아침 GitHub 로봇이 실행해서 data.json 파일을 새로 만드는 프로그램입니다.
대시보드(index.html)는 이 data.json을 읽어서 화면을 그립니다.

가져오는 것: 환율, WTI, Brent(2년치), 국내/글로벌 종목 시세,
             영어 표현 10선(Gemini AI가 매일 새로 작성)
(두바이유, MOPJ 납사, 스프레드, 공포탐욕지수는 제외하기로 했어요)

어떤 항목이 실패해도 전체가 멈추지 않고, 실패한 항목은 어제 값을 그대로 둡니다.
"""
import json
import os
import sys
import urllib.error
import urllib.request
from datetime import datetime, timedelta, timezone

import yfinance as yf

# 한국 시간 기준 오늘 날짜
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

# ---------------------------------------------------------------
# 1) 가져올 목록 (화면에 보일 이름, 야후 파이낸스 코드, 표시 형식)
#    종목을 바꾸고 싶으면 이 목록만 고치면 돼요.
# ---------------------------------------------------------------
OIL = {"wti": "CL=F", "brent": "BZ=F"}

DOMESTIC = [
    ("KOSPI", "^KS11", "index"),
    ("KOSDAQ", "^KQ11", "index"),
    ("SK하이닉스", "000660.KS", "won"),
    ("삼성전자", "005930.KS", "won"),
    ("LG화학", "051910.KS", "won"),
    ("금호석유", "011780.KS", "won"),
    ("S-Oil", "010950.KS", "won"),
    ("롯데케미칼", "011170.KS", "won"),
]

GLOBAL = [
    ("S&P 500", "^GSPC", "index"),
    ("NVIDIA", "NVDA", "usd"),
    ("Apple", "AAPL", "usd"),
    ("Microsoft", "MSFT", "usd"),
    ("Alphabet", "GOOGL", "usd"),
    ("ExxonMobil", "XOM", "usd"),
    ("Chevron", "CVX", "usd"),
    ("TSMC", "TSM", "usd"),
]


# ---------------------------------------------------------------
# 2) 도우미 함수들
# ---------------------------------------------------------------
def load_json(path, default):
    """파일을 읽어요. 없거나 깨져 있으면 default를 돌려줘요."""
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default


def get_closes(ticker, period):
    """야후 파이낸스에서 종가(그날의 마지막 가격) 목록을 가져와요."""
    df = yf.Ticker(ticker).history(period=period, auto_adjust=False)
    closes = df["Close"].dropna()
    if len(closes) < 2:
        raise ValueError(f"{ticker}: 데이터가 부족해요")
    return closes


def fetch_oil(ticker):
    """유가 2년치 일별 종가와 최신 가격, 전일 대비 변동률을 만들어요."""
    closes = get_closes(ticker, "2y")
    labels = [d.strftime("%Y-%m-%d") for d in closes.index]
    values = [round(float(v), 2) for v in closes.values]

    # 미국 시간 기준 '아직 끝나지 않은 오늘' 막대는 빼요 (진행 중인 값이라서)
    us_today = (datetime.now(timezone.utc) - timedelta(hours=5)).strftime("%Y-%m-%d")
    while len(labels) > 2 and labels[-1] > us_today:
        labels.pop()
        values.pop()

    price = values[-1]
    change = round((values[-1] / values[-2] - 1) * 100, 2)
    return {"labels": labels, "values": values}, {"price": price, "change": change}


def fetch_quote(ticker):
    """종목의 최신 종가와 전일 대비 변동률(%)을 돌려줘요."""
    closes = get_closes(ticker, "10d")
    last, prev = float(closes.iloc[-1]), float(closes.iloc[-2])
    return last, (last / prev - 1) * 100


def format_value(kind, price):
    if kind == "won":
        return f"{price:,.0f}원"
    if kind == "usd":
        return f"${price:,.2f}"
    return f"{price:,.2f}"


# ---------------------------------------------------------------
# 2-2) Gemini AI 도우미 (영어 표현처럼 AI가 쓰는 글에 사용)
#      API 키는 코드에 적지 않고 GitHub Secrets의 GEMINI_API_KEY에서 읽어요.
# ---------------------------------------------------------------
# 구글이 모델을 자주 교체해서, 앞의 것이 안 되면 다음 것을 시도해요.
# 나중에 모델 이름이 바뀌면 이 목록만 고치면 돼요.
GEMINI_MODELS = [m for m in [os.environ.get("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-3.6-flash"] if m]


def ask_gemini_json(prompt):
    """Gemini에게 질문하고 JSON 형태의 답을 받아요."""
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았어요 (GitHub Secrets 확인)")

    body = json.dumps(
        {
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8},
        }
    ).encode("utf-8")

    last_err = None
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        req = urllib.request.Request(
            url,
            data=body,
            headers={"Content-Type": "application/json", "x-goog-api-key": key},
        )
        try:
            with urllib.request.urlopen(req, timeout=90) as res:
                raw = json.load(res)
            parts = raw["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            if text.startswith("```"):  # 혹시 코드 표시(```)로 감싸서 오면 벗겨내요
                text = text.strip("`")
                if text.lower().startswith("json"):
                    text = text[4:]
            print(f"Gemini 응답 OK (모델: {model})")
            return json.loads(text)
        except urllib.error.HTTPError as e:
            detail = e.read().decode("utf-8", "ignore")[:200]
            last_err = f"{model}: HTTP {e.code} {detail}"
        except Exception as e:
            last_err = f"{model}: {e}"
        print("Gemini 시도 실패:", last_err)
    raise RuntimeError(last_err)


ENGLISH_FIELDS = ("term", "pron", "meaning", "example", "example_ko")


def make_english(old):
    """컨설팅·임원 보고용 비즈니스 영어 표현 10개를 AI가 새로 만들어요."""
    used = old.get("english_used", [])
    prompt = (
        "당신은 글로벌 전략 컨설팅(McKinsey, BCG, Bain) 출신 비즈니스 영어 코치입니다. "
        "한국의 B2B 소재·석유화학 업계 실무자가 임원 보고와 영문 이메일에서 바로 쓸 수 있는 "
        "컨설팅 비즈니스 영어 표현 10개를 만들어 주세요.\n"
        "조건:\n"
        "1) 실제 컨설팅·임원 보고에서 쓰이는 표현일 것\n"
        "2) 10개가 서로 다른 주제일 것\n"
        "3) 아래 '이미 사용한 표현'과 겹치지 않을 것\n"
        "4) term=영어 표현, pron=한글 발음 표기, meaning=짧은 한국어 뜻, "
        "example=짧은 영어 예문 한 문장, example_ko=그 예문의 한국어 해석\n"
        '반드시 이 JSON 형식으로만 답하세요: {"items":[{"term":"","pron":"","meaning":"","example":"","example_ko":""}]}\n'
        "이미 사용한 표현: " + json.dumps(used, ensure_ascii=False)
    )
    result = ask_gemini_json(prompt)
    items = result.get("items") if isinstance(result, dict) else result

    clean = []
    for it in items or []:
        if isinstance(it, dict) and all(str(it.get(k, "")).strip() for k in ENGLISH_FIELDS):
            clean.append({k: str(it[k]).strip() for k in ENGLISH_FIELDS})
    if len(clean) < 10:
        raise ValueError(f"유효한 표현이 {len(clean)}개뿐이에요")
    clean = clean[:10]

    used_new = ([c["term"] for c in clean] + used)[:100]  # 최근 100개까지만 기억
    return {"date": TODAY, "items": clean}, used_new


# ---------------------------------------------------------------
# 3) 메인: 위의 것들을 차례로 실행해서 data.json을 만들어요
# ---------------------------------------------------------------
def main():
    old = load_json("data.json", {})
    data = {"updated": TODAY, "metrics": {}, "series": {}, "stocks": {}}
    problems = []

    # 환율
    try:
        data["fx"] = round(float(get_closes("KRW=X", "10d").iloc[-1]), 2)
        print("환율 OK:", data["fx"])
    except Exception as e:
        data["fx"] = old.get("fx")
        problems.append(f"환율 실패 (어제 값 유지): {e}")

    # 유가 (WTI, Brent)
    oil_ok = 0
    for key, ticker in OIL.items():
        try:
            series, metric = fetch_oil(ticker)
            data["series"][key] = series
            data["metrics"][key] = metric
            oil_ok += 1
            print(f"{key} OK:", metric)
        except Exception as e:
            if key in old.get("series", {}):
                data["series"][key] = old["series"][key]
            if key in old.get("metrics", {}):
                data["metrics"][key] = old["metrics"][key]
            problems.append(f"{key} 실패 (어제 값 유지): {e}")

    # 히트맵 종목
    for group, items in [("domestic", DOMESTIC), ("global", GLOBAL)]:
        old_by_name = {s.get("name"): s for s in old.get("stocks", {}).get(group, [])}
        rows = []
        for name, ticker, kind in items:
            try:
                price, pct = fetch_quote(ticker)
                rows.append(
                    {"name": name, "val": format_value(kind, price), "change": f"{pct:+.2f}%"}
                )
            except Exception as e:
                problems.append(f"{name} 실패 (어제 값 유지): {e}")
                if name in old_by_name:
                    rows.append(old_by_name[name])
        data["stocks"][group] = rows
    print("종목 OK:", {k: len(v) for k, v in data["stocks"].items()})

    # 영어 표현 10선 (Gemini)
    try:
        data["english"], data["english_used"] = make_english(old)
        print("영어 표현 OK:", data["english"]["items"][0]["term"], "외 9개")
    except Exception as e:
        problems.append(f"영어 표현 실패 (어제 것 유지): {e}")
        if old.get("english"):
            data["english"] = old["english"]
        if old.get("english_used"):
            data["english_used"] = old["english_used"]

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)
    print("data.json 저장 완료:", TODAY)

    if problems:
        print("\n[알림] 일부 항목에 문제가 있었어요:")
        for p in problems:
            print(" -", p)

    # 유가를 하나도 못 가져왔다면 '실패'로 표시해서 Actions 탭에 빨간 X가 뜨게 해요
    if oil_ok == 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
