name: Daily Market Data Update

on:
  schedule:
    - cron: '0 23 * * *' # UTC 기준 23시 (한국 시간 아침 8시 자동 실행)
  workflow_dispatch: # 수동으로 언제든 실행 가능

permissions:
  contents: write

jobs:
  update-data:
    runs-on: ubuntu-latest
    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: '3.10'

      - name: Install dependencies
        run: |
          pip install yfinance pytz

      - name: Run update script
        run: |
          python update_data.py

      - name: Commit and push if changes exist
        run: |
          git config --global user.name "GitHub Actions Bot"
          git config --global user.email "actions@github.com"
          git add data.json
          git diff --quiet && git diff --staged --quiet || (git commit -m "Auto-update market data.json [skip ci]" && git push)
