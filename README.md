# Slot Data Analisis

スロットデータを収集して分析するツール

## やること

- Webサイトから必要なデータをスクレイピングする。
- クラウド上で自動実行できるようにする。
- クラウドデータベースを使ってデータを保存する。
- Webアプリを使って分析データをデプロイする。

## アプリ構成

- Python
- Github Actions
- Supabase
- Streamlit

## フォルダ構成

<pre>

C:.
│  .gitignore
│  README.md
│  requirements.txt
│  secret.json
│  
├─.venv
├─data
│  ├─csv
│  │      halls.csv
│  ├─db
│  │      minrepo_02.db
│  └─log
│          minrepo.log
├─notebooks
├─scraper
│  │  config.py
│  │  df_clean.py
│  │  df_to_db.py
│  │  halls.yaml
│  │  logger_steup.py
│  │  scraper.py
│  │  scraping_date_page.py
│  │  scraping_hall_page.py
│  │  scraping_model_page.py
│  │  utils.py
│  │  
│  └─__pycache__
│
├─trash
│
└─utils
        create_databese.py
</pre>
