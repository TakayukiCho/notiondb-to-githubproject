"""
設定ファイル

NotionとGitHubのAPIトークンや、フィールドのマッピングを管理します。
"""

import os
import json
from dotenv import load_dotenv

# .envファイルから環境変数を読み込む
load_dotenv()

# Notion API設定
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

# GitHub API設定
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")
GITHUB_OWNER = os.getenv("GITHUB_OWNER")
GITHUB_PROJECT_NUMBER = os.getenv("GITHUB_PROJECT_NUMBER")

# Notionのフィールド名をGitHubの対応するフィールド名にマッピング
# これらはユーザーが必要に応じて変更できる
FIELD_MAPPING = {
    "Name": "title",  # Notionのタイトルフィールド → GitHubのタイトル
    "Status": "status", # Notionのステータス → GitHubのステータス
    "Tags": "labels",  # Notionのタグ → GitHubのラベル
    "Person": "assignees", # Notionの担当者 → GitHubのアサイン
    "Due Date": "due_date", # Notionの期日 → GitHubの期日
    "Parent task": "parent" # Notionの親タスク → GitHubの親タスク
}

# Notionのステータス名をGitHubのステータス名にマッピング
try:
    STATUS_MAPPING = json.loads(os.getenv("STATUS_MAPPING", "{}"))
except json.JSONDecodeError:
    STATUS_MAPPING = {
        "In progress": "In Progress",  # 大文字小文字を一致させる
        "Done": "Done",
        "Backlog": "No Status"
    }

# NotionのタグをGitHubのラベルにマッピング
try:
    TAG_MAPPING = json.loads(os.getenv("TAG_MAPPING", "{}"))
except json.JSONDecodeError:
    TAG_MAPPING = {
        "管理画面/edge": "admin",
        "アクション": "action",
        "ドキュメント": "documentation",
        "SDK/計測": "sdk"
    }

# GitHub Projectsのカスタムフィールド名
GITHUB_PROJECT_FIELDS = {
    "status": "Status",
    "title": "Title",
    "labels": "Labels",
    "assignees": "Assignees",
    "due_date": "Due Date"
} 