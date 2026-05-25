name: Crawl Missing Items

on:
  workflow_dispatch:  # 수동 실행만

jobs:
  crawl-missing:
    runs-on: ubuntu-latest
    
    permissions:
      contents: write

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install requests beautifulsoup4

      - name: Run missing item crawler
        run: python crawl_missing.py

      - name: Commit and push updated items.json
        run: |
          git config --global user.name "github-actions[bot]"
          git config --global user.email "github-actions[bot]@users.noreply.github.com"
          git add items.json
          git diff --staged --quiet || git commit -m "Add missing items [$(date '+%Y-%m-%d')]"
          git push
