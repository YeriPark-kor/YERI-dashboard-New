# -*- coding: utf-8 -*-
"""
update_data.py
매일 아침 GitHub 로봇이 실행해서 data.json 파일을 새로 만드는 프로그램입니다.
대시보드(index.html)는 이 data.json을 읽어서 화면을 그립니다.

가져오는 것: 환율, WTI, Brent(2년치), 국내/글로벌 종목 시세, CNN 공포탐욕지수
(두바이유, MOPJ 납사, 스프레드는 제외하기로 했어요)

어떤 항목이 실패해도 전체가 멈추지 않고, 실패한 항목은 어제 값을 그대로 둡니다.
"""
import json
import sys
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

CNN_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"


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


def fear_greed_label(score):
    if score < 25:
        return "극단적 공포"
    if score < 45:
        return "공포"
    if score < 55:
        return "중립"
    if score < 75:
        return "탐욕"
    return "극단적 탐욕"


def fetch_fear_greed_from_cnn():
    """CNN에서 공포탐욕지수(현재값, 비교값, 1년 추이)를 가져와요."""
    req = urllib.request.Request(
        CNN_URL,
        headers={
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
            ),
            "Accept": "application/json",
            "Origin": "https://edition.cnn.com",
            "Referer": "https://edition.cnn.com/",
        },
    )
    with urllib.request.urlopen(req, timeout=20) as res:
        raw = json.load(res)

    now = raw["fear_and_greed"]
    score = round(float(now["score"]))

    prev = {}
    for key, src in [
        ("close", "previous_close"),
        ("week", "previous_1_week"),
        ("month", "previous_1_month"),
        ("year", "previous_1_year"),
    ]:
        if now.get(src) is not None:
            prev[key] = round(float(now[src]))

    points = raw.get("fear_and_greed_historical", {}).get("data", [])[-365:]
    history = {
        "labels": [
            datetime.fromtimestamp(p["x"] / 1000, timezone.utc).strftime("%Y-%m-%d")
            for p in points
        ],
        "values": [round(float(p["y"])) for p in points],
    }

    return {
        "score": score,
        "label": fear_greed_label(score),
        "prev": prev,
        "history": history,
        "asof": str(now.get("timestamp", TODAY))[:10],
        "source": "cnn",
        "fetched": TODAY,
    }


def fear_greed_from_manual():
    """CNN이 막혔을 때를 위한 대비책: manual.json의 fear_greed 값을 써요."""
    raw = load_json("manual.json", {})
    m = raw.get("fear_greed") if isinstance(raw, dict) else None
    if isinstance(m, dict) and m.get("score") is not None:
        score = round(float(m["score"]))
        result = {
            "score": score,
            "label": fear_greed_label(score),
            "asof": m.get("asof", TODAY),
            "source": "manual",
            "fetched": TODAY,
        }
        if isinstance(m.get("prev"), dict):
            result["prev"] = m["prev"]
        return result
    return None


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

    # 공포탐욕지수: CNN -> manual.json -> 어제 값 순서로 시도
    try:
        data["fear_greed"] = fetch_fear_greed_from_cnn()
        print("공포탐욕지수 OK (CNN):", data["fear_greed"]["score"])
    except Exception as e:
        problems.append(f"CNN 공포탐욕지수 실패: {e}")
        manual = fear_greed_from_manual()
        if manual:
            data["fear_greed"] = manual
            print("공포탐욕지수: manual.json 값 사용")
        elif old.get("fear_greed"):
            kept = dict(old["fear_greed"])
            # 옛 값이라는 표시를 위해 fetched를 옛 날짜로 둬요 (화면에 경고가 떠요)
            kept.setdefault("fetched", old.get("updated"))
            data["fear_greed"] = kept
            print("공포탐욕지수: 어제 값 유지")

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
