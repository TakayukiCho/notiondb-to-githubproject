# NotionDB to GitHub Projects

NotionデータベースからGitHub Projectsにデータを移行するためのPythonツールです。

## 概要

このツールは以下の機能を提供します：

- Notionデータベースからタスクデータのエクスポート
- GitHub Projectsへのタスクのインポート
- 各タスクのステータス、タグ、担当者、期日などのマッピング

## 必要条件

- Python 3.8以上
- Notion API キー
- GitHub パーソナルアクセストークン（プロジェクト管理権限付き）

## インストール

```bash
git clone https://github.com/yourusername/notiondb-to-githubproject.git
cd notiondb-to-githubproject
pip install -r requirements.txt
```

## 設定

1. `.env.example` ファイルを `.env` としてコピーして、以下の項目を設定してください：

```
NOTION_API_KEY=your_notion_api_key
NOTION_DATABASE_ID=your_notion_database_id
GITHUB_TOKEN=your_github_token
GITHUB_OWNER=your_github_username_or_org
GITHUB_REPO=your_repository_name
GITHUB_PROJECT_NUMBER=your_project_number
```

## 使い方

```bash
python main.py
```

詳細なオプションについては、以下のコマンドでヘルプを参照してください：

```bash
python main.py --help
```

## カスタマイズ

`config.py` ファイルを編集することで、NotionとGitHubのフィールドマッピングをカスタマイズできます。

## ライセンス

MITライセンス # notiondb-to-githubproject
