"""매일 data.json을 새로 만드는 스크립트 (GitHub Actions가 자동 실행)"""
import json, pathlib, datetime, urllib.request
import yfinance as yf

ROOT = pathlib.Path(__file__).parent
OUT = ROOT / "data.json"
MANUAL = ROOT / "manual.json"
old = json.loads(OUT.read_text("utf-8")) if OUT.exists() else {}
today = datetime.date.today().isoformat()


def closes(ticker, period):
    df = yf.Ticker(ticker).history(period=period, auto_adjust=False)
    return df["Close"].dropna()


def pct(prev, last):
    return round((last / prev - 1) * 100, 2) if prev else 0.0


# ---------- 1) 유가 (실제 시세) ----------
series, metrics = {}, {}
for key, ticker in {"wti": "CL=F", "brent": "BZ=F"}.items():
    try:
        c = closes(ticker, "2y")
        series[key] = {
            "labels": [d.strftime("%Y-%m-%d") for d in c.index],
            "values": [round(float(v), 2) for v in c.values],
        }
        metrics[key] = {"price": round(float(c.iloc[-1]), 2), "change": pct(c.iloc[-2], c.iloc[-1])}
    except Exception as e:
        print("유가 실패", key, e)
        series[key] = old.get("series", {}).get(key, {"labels": [], "values": []})
        if key in old.get("metrics", {}):
            metrics[key] = old["metrics"][key]

# ---------- 2) 두바이·납사·스프레드 (무료 시세 없음 → manual.json 값을 매일 쌓음) ----------
manual = json.loads(MANUAL.read_text("utf-8"))
for key, value in manual.items():
    hist = old.get("series", {}).get(key, {"labels": [], "values": []})
    labels, values = list(hist["labels"]), list(hist["values"])
    if labels and labels[-1] == today:
        values[-1] = value
    else:
        labels.append(today)
        values.append(value)
    series[key] = {"labels": labels, "values": values}
    prev = values[-2] if len(values) > 1 else value
    metrics[key] = {"price": value, "change": pct(prev, value)}

# ---------- 3) 히트맵 종목 ----------
DOMESTIC = [("KOSPI", "^KS11", "{:,.2f}"), ("KOSDAQ", "^KQ11", "{:,.2f}"),
            ("SK하이닉스", "000660.KS", "{:,.0f}원"), ("삼성전자", "005930.KS", "{:,.0f}원"),
            ("LG화학", "051910.KS", "{:,.0f}원"), ("금호석유", "011780.KS", "{:,.0f}원"),
            ("S-Oil", "010950.KS", "{:,.0f}원"), ("롯데케미칼", "011170.KS", "{:,.0f}원")]
GLOBAL = [("S&P 500", "^GSPC", "{:,.2f}"), ("NVIDIA", "NVDA", "${:,.2f}"),
          ("Apple", "AAPL", "${:,.2f}"), ("Microsoft", "MSFT", "${:,.2f}"),
          ("Alphabet", "GOOGL", "${:,.2f}"), ("ExxonMobil", "XOM", "${:,.2f}"),
          ("Chevron", "CVX", "${:,.2f}"), ("TSMC", "TSM", "${:,.2f}")]


def stock_list(items, old_list):
    result = []
    for i, (name, ticker, fmt) in enumerate(items):
        try:
            c = closes(ticker, "7d")
            last, prev = float(c.iloc[-1]), float(c.iloc[-2])
            result.append({"name": name, "val": fmt.format(last), "change": f"{pct(prev, last):+.2f}%"})
        except Exception as e:
            print("종목 실패", name, e)
            if i < len(old_list):
                result.append(old_list[i])
    return result


stocks = {
    "domestic": stock_list(DOMESTIC, old.get("stocks", {}).get("domestic", [])),
    "global": stock_list(GLOBAL, old.get("stocks", {}).get("global", [])),
}

# ---------- 4) 환율 ----------
try:
    fx = round(float(closes("KRW=X", "7d").iloc[-1]), 2)
except Exception as e:
    print("환율 실패", e)
    fx = old.get("fx")

# ---------- 5) CNN 공포탐욕지수 (비공식 주소라 막히면 어제 값 유지) ----------
LABELS = {"extreme fear": "극단적 공포", "fear": "공포", "neutral": "중립",
          "greed": "탐욕", "extreme greed": "극단적 탐욕"}
fear_greed = old.get("fear_greed")
try:
    req = urllib.request.Request(
        "https://production.dataviz.cnn.io/index/fearandgreed/graphdata",
        headers={"User-Agent": "Mozilla/5.0"})
    fg = json.load(urllib.request.urlopen(req, timeout=20))["fear_and_greed"]
    fear_greed = {"score": round(fg["score"]), "label": LABELS.get(str(fg["rating"]).lower(), fg["rating"])}
except Exception as e:
    print("공포탐욕지수 실패(어제 값 유지)", e)

OUT.write_text(json.dumps({
    "updated": today, "fx": fx, "fear_greed": fear_greed,
    "metrics": metrics, "series": series, "stocks": stocks,
}, ensure_ascii=False, indent=1), encoding="utf-8")
print("완료", today)
