# Slot Data Analisis

スロットデータを収集して分析するツール

## やること

- Web サイトから必要なデータをスクレイピングする。
- クラウド上で自動実行できるようにする。
- クラウドデータベースを使ってデータを保存する。
- Web アプリを使って分析データをデプロイする。

## アプリ構成

- Python
- Github Actions
- Supabase
- Streamlit

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

4. 変更の確認・コミット・プッシュ

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

5. pull と fetch（リモート更新取得）
```bash
git pull
git fetch
```

6. マージと rebase
```bash
# ブランチをマージ（一般的)
git checkout develop
git merge feature/new-feature
# リベース（きれいな履歴にしたい時）
git checkout feature/new-feature
git rebase develop
```

7. 直前のコミット修正・取り消し
```bash
git commit --amend       # 直前のコミットメッセージ修正
git reset --soft HEAD~1  # 直前のコミットを取り消してステージに戻す
git reset --hard HEAD~1  # コミット＆変更ごと消す（危険）
```

8. リモート設定
```bash
git remote -v # リモート一覧
git remote add origin https://github.com/user/repo.git # origin を追加
```

9. その他便利コマンド
■ ログ確認（きれい）
```bash
git log --oneline --graph --decorate --all # ログ確認（きれい）
git reset HEAD file.py   # ステージング取り消し：
git checkout -- file.py  # 作業内容を完全に捨てる：
```

10. 実務フローのまとめ（黄金パターン）
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

