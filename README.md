# Slot Data Analisis

スロットデータを収集して分析するツール
- パチスロ（主にジャグラー系など）の日次データを収集 → 前処理 → DBへ蓄積 → 集計/可視化 →（将来）予測までを一気通貫で行うためのデータ分析プロジェクトです。
- Streamlitで「立ち回り目線」のダッシュボードを作成
- Supabase(PostgreSQL)を中核DBとして運用
- GitHub Actionsで定期更新

---

## できること(概要)

- スクレイピング（Python）
  - 動的サイトも想定（Playwright / undetected-chromedriver 等）
  - 県 → ホール → 機種 → 台番 → 日付のような階層データ取得
  - 取得結果を CSV保存（生データ） し、再現性を確保
 
- 前処理 → DB登録
  - 不要列・記号除去、型変換、正規化
  - 一意制約で重複を防止し、追記運用しやすくする
  - Supabase(PostgreSQL)を基本。必要に応じてローカルSQLiteも併用可
 
- 分析・可視化（Streamlit）
  - ホール / 機種 / 台番でフィルタ
  - 末尾日（day_last: 1日/7日/末尾3など）の傾向集計
  - RB/BB確率、合算、メダル率、勝率などの指標を表示
  - 期間集計（例：過去◯ヶ月）や、単日×複数日の並列表現
 
- 自動化（GitHub Actions）
  - 毎日/毎朝などの定期実行でデータ更新
  - 成果物の整理（artifact削除等）・ログ保存
 
- （将来）予測
  - XGBoost等で「翌日のRB確率」推定、など
 
---

## アーキテクチャ（データフロー）

1. **Scraper**：サイトから日次データ取得  
2. **Raw CSV**：加工しない生データとして保存  
3. **Preprocess**：クレンジング・型変換・正規化  
4. **DB（Supabase/PostgreSQL）**：テーブルに登録、集計用Viewも用意  
5. **Analysis/UI（Streamlit）**：フィルタ → 集計 → グラフ/表で表示  
6. **Automation（GitHub Actions）**：定期実行で 1〜5 を回す

---

## 技術スタック

- **Python**：スクレイピング / 前処理 / 分析
- **Playwright / undetected-chromedriver**：動的サイト対策（必要に応じて）
- **pandas**：前処理・集計
- **Supabase (PostgreSQL)**：DB、将来的にAuth/Storage/Functionsも拡張可
- **Streamlit + Altair**：UI・可視化
- **GitHub Actions**：定期実行、CI補助

---

## フォルダ構成

```
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
```

## Git 基本コマンド

1. 初期設定（最初だけ）

```bash
git config --global user.name "あなたの名前"
git config --global user.email "you@example.com"
```

2. リポジトリの作成と GitHub から取得

```bash
git init
git clone https://github.com/user/repo.git
```

3. ブランチ操作（超重要）

```bash
git branch     # ローカル
git branch -r  # リモート
git branch -a  # 両方
```

```bash
git checkout -b new-branch  # ブランチ作成
git checkout main           # ブランチ切り替え
```

```bash
git branch -d branch-name             # ローカル安全削除
git branch -D branch-name             # ローカル強制削除
git push origin --delete branch-name  # リモート削除
```

1. 変更の確認・コミット・プッシュ

```bash
git status                      # 状態確認
git diff                        # 差分確認
git diff --staged               # 差分確認
git add file.py                 # ファイルをステージング
git add .                       # ファイルをステージングで全部追加
git commit -m "message"         # コミット
git push                        # リモートにプッシュ
git push -u origin branch-name  # 初めてリモートにプッシュ
```

1. pull と fetch（リモート更新取得）
```bash
git pull
git fetch
git fetch --prune # リモートで消されたブランチを削除
```

1. マージと rebase
```bash
# ブランチをマージ（一般的)
git checkout develop
git merge feature/new-feature
# リベース（きれいな履歴にしたい時）
git checkout feature/new-feature
git rebase develop
```

1. 直前のコミット修正・取り消し
```bash
git commit --amend       # 直前のコミットメッセージ修正
git reset --soft HEAD~1  # 直前のコミットを取り消してステージに戻す
git reset --hard HEAD~1  # コミット＆変更ごと消す（危険）
```

1. リモート設定
```bash
git remote -v # リモート一覧
git remote add origin https://github.com/user/repo.git # origin を追加
```

1. その他便利コマンド
■ ログ確認（きれい）
```bash
git log --oneline --graph --decorate --all # ログ確認（きれい）
git reset HEAD file.py   # ステージング取り消し：
git checkout -- file.py  # 作業内容を完全に捨てる：
```

1.  実務フローのまとめ（黄金パターン）
■ ログ確認（きれい）
```bash
# 1. main から新ブランチ作成
git checkout main
git pull
git checkout -b feature/add-x

# 2. 作業 → add → commit → push
git add .
git commit -m "Add X feature"
git push -u origin feature/add-x

# 3. GitHub で PR 作成
# 4. レビュー後 develop にマージ
# 5. ステージング確認 → main にマージ
```
