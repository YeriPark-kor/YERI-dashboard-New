<!DOCTYPE html>
<html lang="ko" class="dark">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>YERI's Today - Executive Dashboard</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: {
              50: '#f0fdf4',
              500: '#22c55e',
              600: '#16a34a',
              900: '#14532d',
            }
          }
        }
      }
    }
  </script>
  <style>
    @import url('https://cdn.jsdelivr.net/gh/orioncactus/pretendard/dist/web/static/pretendard.css');
    body { font-family: 'Pretendard', sans-serif; }
  </style>
</head>
<body class="bg-slate-900 text-slate-100 min-h-screen pb-12">

  <!-- Header -->
  <header class="border-b border-slate-800 bg-slate-900/80 backdrop-blur sticky top-0 z-50">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
      <div class="flex items-center gap-3">
        <span class="text-2xl">📊</span>
        <h1 class="text-xl font-bold tracking-tight bg-gradient-to-r from-emerald-400 to-teal-200 bg-clip-text text-transparent">
          YERI's Today
        </h1>
        <span class="text-xs px-2 py-0.5 rounded-full bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">Executive Briefing</span>
      </div>
      <div class="text-xs text-slate-400 flex items-center gap-2">
        <span>최종 갱신:</span>
        <span id="last-updated" class="font-mono text-slate-200">-</span>
      </div>
    </div>
  </header>

  <main class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 pt-8 space-y-8">

    <!-- Key Takeaways & Market Briefing -->
    <section class="grid grid-cols-1 md:grid-cols-2 gap-6">
      <!-- Key Takeaways -->
      <div class="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/50 shadow-xl backdrop-blur-sm">
        <h2 class="text-lg font-semibold text-emerald-400 mb-4 flex items-center gap-2">
          <span>📌</span> Today's Key Takeaways (마케팅 및 사업 전략)
        </h2>
        <ul class="space-y-3 text-slate-300 text-sm leading-relaxed">
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 font-bold">•</span>
            <span><strong>유가 변동성 대응 마케팅:</strong> WTI·브렌트유 등락에 따른 원가 압박 요인을 선제 분석하고, 주요 고객사 대상 판가 연동 구조 및 재고 최적화 커뮤니케이션 강화</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 font-bold">•</span>
            <span><strong>스페셜티 포트폴리오 소통:</strong> 범용 석유화학 시황 둔화 국면 타개를 위한 고부가 친환경 소재 및 친환경 플라스틱 라인업의 차별적 가치 집중 홍보</span>
          </li>
          <li class="flex items-start gap-2">
            <span class="text-emerald-400 font-bold">•</span>
            <span><strong>실시간 대시보드 기반 민첩성:</strong> 환율, 유가, 공포탐욕지수 등 매크로 지표 변동에 맞춰 영업 전략 및 타겟 마켓 세분화 대응 속도 극대화</span>
          </li>
        </ul>
      </div>

      <!-- 데일리 마켓 브리핑 인사이트 -->
      <div class="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/50 shadow-xl backdrop-blur-sm">
        <h2 class="text-lg font-semibold text-blue-400 mb-4 flex items-center gap-2">
          <span>📑</span> 데일리 석유화학 & 원자재 마켓 브리핑 인사이트
        </h2>
        <blockquote class="border-l-4 border-blue-500 pl-4 py-1 text-slate-300 italic text-sm leading-relaxed mb-3">
          "매크로 불확실성 속 기초소재 원가 방어와 고부가 스페셜티 전환의 기로"
        </blockquote>
        <p class="text-slate-300 text-sm leading-relaxed">
          최근 글로벌 에너지 시장은 WTI 및 브렌트유의 변동성이 확대되면서 석유화학 업계의 기초 원가(나프타 등) 부담을 가중시키고 있습니다. 범용 제품 중심의 스프레드가 제한적인 상황에서, 단기적인 시황 방어와 함께 장기적인 스페셜티·친환경 소재 포트폴리오 전환의 실행력이 어느 때보다 중요해졌습니다. 특히 주요 고객사들과의 소통 과정에서 원가 연동 구조의 투명성을 높이고, 고부가 가치 제품군의 경쟁 우위를 데이터 기반으로 입증하는 마케팅 전략이 핵심 경쟁력이 될 것입니다.
        </p>
      </div>
    </section>

    <!-- Macro Indicators Summary (FX, WTI, Brent, Fear & Greed) -->
    <section class="grid grid-cols-2 md:grid-cols-4 gap-4">
      <div class="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4">
        <div class="text-xs text-slate-400 mb-1">원/달러 환율 (KRW)</div>
        <div id="fx-val" class="text-2xl font-bold font-mono text-slate-100">-</div>
      </div>
      <div class="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4">
        <div class="text-xs text-slate-400 mb-1">WTI유 ($/bbl)</div>
        <div class="flex items-baseline justify-between">
          <span id="wti-price" class="text-2xl font-bold font-mono text-slate-100">-</span>
          <span id="wti-change" class="text-sm font-semibold font-mono">-</span>
        </div>
      </div>
      <div class="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4">
        <div class="text-xs text-slate-400 mb-1">Brent유 ($/bbl)</div>
        <div class="flex items-baseline justify-between">
          <span id="brent-price" class="text-2xl font-bold font-mono text-slate-100">-</span>
          <span id="brent-change" class="text-sm font-semibold font-mono">-</span>
        </div>
      </div>
      <div class="bg-slate-800/40 border border-slate-700/40 rounded-xl p-4">
        <div class="text-xs text-slate-400 mb-1">Fear & Greed 지수</div>
        <div class="flex items-baseline justify-between">
          <span id="fg-score" class="text-2xl font-bold font-mono text-emerald-400">-</span>
          <span id="fg-label" class="text-xs font-medium text-slate-300">-</span>
        </div>
      </div>
    </section>

    <!-- Stock Heatmap Section -->
    <section class="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/50 shadow-xl">
      <h2 class="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
        <span>📈</span> 주요 종목 시세 (Heatmap)
      </h2>
      <div class="grid grid-cols-1 md:grid-cols-2 gap-6">
        <div>
          <h3 class="text-sm font-medium text-slate-400 mb-3">국내 주식 & 지수</h3>
          <div id="domestic-stocks" class="grid grid-cols-2 sm:grid-cols-4 gap-3"></div>
        </div>
        <div>
          <h3 class="text-sm font-medium text-slate-400 mb-3">글로벌 테크 & 에너지</h3>
          <div id="global-stocks" class="grid grid-cols-2 sm:grid-cols-4 gap-3"></div>
        </div>
      </div>
    </section>

    <!-- News & English Topics -->
    <section class="grid grid-cols-1 lg:grid-cols-3 gap-6">
      <!-- News TOP 10 -->
      <div class="lg:col-span-2 bg-slate-800/60 rounded-2xl p-6 border border-slate-700/50 shadow-xl">
        <h2 class="text-lg font-semibold text-slate-200 mb-4 flex items-center gap-2">
          <span>📰</span> 글로벌 & 석유화학 주요 뉴스
        </h2>
        <div id="news-list" class="space-y-3"></div>
      </div>

      <!-- Business English -->
      <div class="bg-slate-800/60 rounded-2xl p-6 border border-slate-700/50 shadow-xl">
        <h2 class="text-lg font-semibold text-amber-400 mb-4 flex items-center gap-2">
          <span>💡</span> Business English 10
        </h2>
        <div id="english-list" class="space-y-4 max-h-[500px] overflow-y-auto pr-2"></div>
      </div>
    </section>

  </main>

  <script>
    async function loadDashboardData() {
      try {
        const res = await fetch('data.json');
        if (!res.ok) throw new Error('Data load failed');
        const data = await res.json();

        // 1. Updated Time & FX
        document.getElementById('last-updated').innerText = data.updated || '-';
        document.getElementById('fx-val').innerText = data.fx ? `${data.fx.toLocaleString()} 원` : '-';

        // 2. Oil Metrics
        if (data.metrics) {
          if (data.metrics.wti) {
            document.getElementById('wti-price').innerText = `$${data.metrics.wti.price}`;
            const wtiChg = document.getElementById('wti-change');
            wtiChg.innerText = `${data.metrics.wti.change >= 0 ? '+' : ''}${data.metrics.wti.change}%`;
            wtiChg.className = `text-sm font-semibold font-mono ${data.metrics.wti.change >= 0 ? 'text-red-400' : 'text-blue-400'}`;
          }
          if (data.metrics.brent) {
            document.getElementById('brent-price').innerText = `$${data.metrics.brent.price}`;
            const brentChg = document.getElementById('brent-change');
            brentChg.innerText = `${data.metrics.brent.change >= 0 ? '+' : ''}${data.metrics.brent.change}%`;
            brentChg.className = `text-sm font-semibold font-mono ${data.metrics.brent.change >= 0 ? 'text-red-400' : 'text-blue-400'}`;
          }
        }

        // 3. Fear & Greed
        if (data.fear_greed) {
          document.getElementById('fg-score').innerText = data.fear_greed.score || '-';
          document.getElementById('fg-label').innerText = data.fear_greed.label || '';
        }

        // 4. Stock Heatmaps
        const renderStocks = (containerId, stocks) => {
          const container = document.getElementById(containerId);
          if (!container || !stocks) return;
          container.innerHTML = stocks.map(s => {
            const isUp = s.change && s.change.startsWith('+');
            const bgClass = isUp ? 'bg-red-500/10 border-red-500/20' : 'bg-blue-500/10 border-blue-500/20';
            const textClass = isUp ? 'text-red-400' : 'text-blue-400';
            return `
              <div class="${bgClass} border rounded-xl p-3 flex flex-col justify-between">
                <span class="text-xs text-slate-400 font-medium truncate">${s.name}</span>
                <span class="text-sm font-bold font-mono text-slate-200 mt-1">${s.val}</span>
                <span class="text-xs font-semibold font-mono ${textClass} mt-0.5">${s.change}</span>
              </div>
            `;
          }).join('');
        };

        if (data.stocks) {
          renderStocks('domestic-stocks', data.stocks.domestic);
          renderStocks('global-stocks', data.stocks.global);
        }

        // 5. News List
        const newsContainer = document.getElementById('news-list');
        if (newsContainer && data.news && data.news.items) {
          newsContainer.innerHTML = data.news.items.map(n => `
            <a href="${n.link}" target="_blank" class="block p-3 rounded-xl bg-slate-700/30 hover:bg-slate-700/60 transition border border-slate-700/40">
              <div class="flex items-center justify-between gap-2">
                <span class="text-xs px-2 py-0.5 rounded bg-slate-600/50 text-emerald-300 font-medium">${n.tag || '뉴스'}</span>
                <span class="text-xs text-slate-400">${n.source || ''}</span>
              </div>
              <h3 class="text-sm font-medium text-slate-200 mt-1 hover:text-emerald-400 transition leading-snug">${n.title}</h3>
            </a>
          `).join('');
        }

        // 6. Business English
        const englishContainer = document.getElementById('english-list');
        if (englishContainer && data.english && data.english.items) {
          englishContainer.innerHTML = data.english.items.map((item, idx) => `
            <div class="p-3 rounded-xl bg-slate-700/30 border border-slate-700/40 space-y-1">
              <div class="flex items-center justify-between">
                <span class="font-bold text-amber-300 text-sm">${idx + 1}. ${item.term}</span>
                <span class="text-xs text-slate-400">[${item.pron}]</span>
              </div>
              <p class="text-xs font-medium text-emerald-400">${item.meaning}</p>
              <p class="text-xs text-slate-300 italic">"${item.example}"</p>
              <p class="text-xs text-slate-400">${item.example_ko}</p>
            </div>
          `).join('');
        }

      } catch (err) {
        console.error('대시보드 데이터 연동 오류:', err);
      }
    }

    document.addEventListener('DOMContentLoaded', loadDashboardData);
  </script>
</body>
</html>
