# -*- coding: utf-8 -*-
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from email.utils import parsedate_to_datetime
from datetime import datetime, timedelta, timezone

import yfinance as yf

# 한국 시간 기준 오늘 날짜
KST = timezone(timedelta(hours=9))
TODAY = datetime.now(KST).strftime("%Y-%m-%d")

CNN_URL = "https://production.dataviz.cnn.io/index/fearandgreed/graphdata"

OIL = {"wti": "CL=F", "brent": "BZ=F"}

NEWS_TOPICS = [
    ("석유화학", "납사 에틸렌 석유화학"),
    ("에너지", "국제유가 WTI 브렌트"),
    ("반도체", "SK하이닉스 삼성전자 HBM 반도체"),
    ("글로벌 테크", "엔비디아 AI 인프라 빅테크"),
    ("매크로", "미국 국채금리 연준 증시"),
    ("화학전략", "석유화학 구조조정 스페셜티"),
    ("환율 동향", "원달러 환율"),
    ("ESG/친환경", "탄소국경세 친환경 플라스틱"),
    ("공급망", "중동 해상운임 원유 공급망"),
    ("기업 실적", "LG화학 롯데케미칼 실적"),
]

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

def load_json(path, default):
    try:
        with open(path, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

def get_closes(ticker, period):
    df = yf.Ticker(ticker).history(period=period, auto_adjust=False)
    closes = df["Close"].dropna()
    if len(closes) < 2:
        raise ValueError(f"{ticker}: 데이터가 부족해요")
    return closes

def fetch_oil(ticker):
    closes = get_closes(ticker, "2y")
    labels = [d.strftime("%Y-%m-%d") for d in closes.index]
    values = [round(float(v), 2) for v in closes.values]
    us_today = (datetime.now(timezone.utc) - timedelta(hours=5)).strftime("%Y-%m-%d")
    while len(labels) > 2 and labels[-1] > us_today:
        labels.pop()
        values.pop()
    price = values[-1]
    change = round((values[-1] / values[-2] - 1) * 100, 2)
    return {"labels": labels, "values": values}, {"price": price, "change": change}

def fetch_quote(ticker):
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
    if score < 25: return "극단적 공포"
    if score < 45: return "공포"
    if score < 55: return "중립"
    if score < 75: return "탐욕"
    return "극단적 탐욕"

def fetch_fear_greed_from_cnn():
    req = urllib.request.Request(
        CNN_URL,
        headers={
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36",
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
    for key, src in [("close", "previous_close"), ("week", "previous_1_week"), ("month", "previous_1_month"), ("year", "previous_1_year")]:
        if now.get(src) is not None:
            prev[key] = round(float(now[src]))
    points = raw.get("fear_and_greed_historical", {}).get("data", [])[-365:]
    history = {
        "labels": [datetime.fromtimestamp(p["x"] / 1000, timezone.utc).strftime("%Y-%m-%d") for p in points],
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
    raw = load_json("manual.json", {})
    m = raw.get("fear_greed") if isinstance(raw, dict) else None
    if isinstance(m, dict) and m.get("score") is not None:
        score = round(float(m["score"]))
        result = {"score": score, "label": fear_greed_label(score), "asof": m.get("asof", TODAY), "source": "manual", "fetched": TODAY}
        if isinstance(m.get("prev"), dict): result["prev"] = m["prev"]
        return result
    return None

GEMINI_MODELS = [m for m in [os.environ.get("GEMINI_MODEL"), "gemini-3.8-flash", "gemini-3.6-flash"] if m]

def ask_gemini_json(prompt):
    key = os.environ.get("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY가 설정되지 않았어요")
    body = json.dumps({"contents": [{"parts": [{"text": prompt}]}], "generationConfig": {"responseMimeType": "application/json", "temperature": 0.8}}).encode("utf-8")
    last_err = None
    for model in GEMINI_MODELS:
        url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json", "x-goog-api-key": key})
        try:
            with urllib.request.urlopen(req, timeout=90) as res:
                raw = json.load(res)
            parts = raw["candidates"][0]["content"]["parts"]
            text = "".join(p.get("text", "") for p in parts if not p.get("thought")).strip()
            if text.startswith("```"):
                text = text.strip("`")
                if text.lower().startswith("json"): text = text[4:]
            return json.loads(text)
        except Exception as e:
            last_err = f"{model}: {e}"
    raise RuntimeError(last_err)

ENGLISH_FIELDS = ("term", "pron", "meaning", "example", "example_ko")

def make_english(old):
    used = old.get("english_used", [])
    prompt = (
        "당신은 글로벌 전략 컨설팅 출신 비즈니스 영어 코치입니다. B2B 소재·석유화학 업계 실무자가 임원 보고에서 쓸 수 있는 "
        "컨설팅 비즈니스 영어 표현 10개를 만들어 주세요.\n"
        '반드시 이 JSON 형식으로만 답하세요: {"items":[{"term":"","pron":"","meaning":"","example":"","example_ko":""}]}\n'
        "이미 사용한 표현: " + json.dumps(used, ensure_ascii=False)
    )
    result = ask_gemini_json(prompt)
    items = result.get("items") if isinstance(result, dict) else result
    clean = []
    for it in items or []:
        if isinstance(it, dict) and all(str(it.get(k, "")).strip() for k in ENGLISH_FIELDS):
            clean.append({k: str(it[k]).strip() for k in ENGLISH_FIELDS})
    if len(clean) < 10: raise ValueError("유효 표현 부족")
    clean = clean[:10]
    used_new = ([c["term"] for c in clean] + used)[:100]
    return {"date": TODAY, "items": clean}, used_new

def fetch_news_item(query, used_titles):
    for window in ("2d", "7d"):
        q = urllib.parse.quote(f"{query} when:{window}")
        url = f"[https://news.google.com/rss/search?q=](https://news.google.com/rss/search?q=){q}&hl=ko&gl=KR&ceid=KR:ko"
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/124.0 Safari/537.36"})
        with urllib.request.urlopen(req, timeout=20) as res:
            root = ET.fromstring(res.read())
        for item in root.iter("item"):
            title = (item.findtext("title") or "").strip()
            link = (item.findtext("link") or "").strip()
            src = item.find("source")
            source = (src.text or "").strip() if src is not None and src.text else ""
            if source and title.endswith(" - " + source): title = title[: -len(" - " + source)].strip()
            if not title or not link.startswith("http") or title in used_titles: continue
            pub = ""
            try: pub = parsedate_to_datetime(item.findtext("pubDate")).astimezone(KST).strftime("%Y-%m-%d")
            except Exception: pass
            return {"title": title, "source": source, "link": link, "pub": pub}
    raise ValueError("검색 결과 없음")

def make_news(old):
    old_by_tag = {n.get("tag"): n for n in (old.get("news") or {}).get("items", [])}
    items, used, problems = [], set(), []
    for tag, query in NEWS_TOPICS:
        try:
            art = fetch_news_item(query, used)
            art["tag"] = tag
            used.add(art["title"])
            items.append(art)
        except Exception as e:
            problems.append(f"뉴스[{tag}] 실패: {e}")
            if tag in old_by_tag: items.append(old_by_tag[tag])
    if not items: raise RuntimeError("뉴스 수집 실패")
    return {"date": TODAY, "items": items}, problems

def main():
    old = load_json("data.json", {})
    data = {"updated": TODAY, "metrics": {}, "series": {}, "stocks": {}}
    problems = []

    try:
        data["fx"] = round(float(get_closes("KRW=X", "10d").iloc[-1]), 2)
    except Exception as e:
        data["fx"] = old.get("fx")
        problems.append(f"환율 실패: {e}")

    oil_ok = 0
    for key, ticker in OIL.items():
        try:
            series, metric = fetch_oil(ticker)
            data["series"][key] = series
            data["metrics"][key] = metric
            oil_ok += 1
        except Exception as e:
            if key in old.get("series", {}): data["series"][key] = old["series"][key]
            if key in old.get("metrics", {}): data["metrics"][key] = old["metrics"][key]
            problems.append(f"{key} 실패: {e}")

    for group, items in [("domestic", DOMESTIC), ("global", GLOBAL)]:
        old_by_name = {s.get("name"): s for s in old.get("stocks", {}).get(group, [])}
        rows = []
        for name, ticker, kind in items:
            try:
                price, pct = fetch_quote(ticker)
                rows.append({"name": name, "val": format_value(kind, price), "change": f"{pct:+.2f}%"})
            except Exception as e:
                problems.append(f"{name} 실패: {e}")
                if name in old_by_name: rows.append(old_by_name[name])
        data["stocks"][group] = rows

    try:
        data["fear_greed"] = fetch_fear_greed_from_cnn()
    except Exception as e:
        problems.append(f"CNN 공포탐욕지수 실패: {e}")
        manual = fear_greed_from_manual()
        if manual: data["fear_greed"] = manual
        elif old.get("fear_greed"): data["fear_greed"] = dict(old["fear_greed"])

    try:
        data["english"], data["english_used"] = make_english(old)
    except Exception as e:
        problems.append(f"영어 표현 실패: {e}")
        if old.get("english"): data["english"] = old["english"]
        if old.get("english_used"): data["english_used"] = old["english_used"]

    try:
        data["news"], news_problems = make_news(old)
        problems.extend(news_problems)
    except Exception as e:
        problems.append(f"뉴스 실패: {e}")
        if old.get("news"): data["news"] = old["news"]

    with open("data.json", "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=1)

    if oil_ok == 0:
        sys.exit(1)

if __name__ == "__main__":
    main()
