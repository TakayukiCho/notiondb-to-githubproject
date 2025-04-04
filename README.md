# NotionDB to GitHub Projects

NotionデータベースからGitHub Projectsにデータを移行するためのPythonツールです。

## 概要

このツールは以下の機能を提供します：

- Notionデータベースからタスクデータのエクスポート
- GitHub ProjectsへのDraftアイテムとしての直接インポート（リポジトリ不要）
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
GITHUB_PROJECT_NUMBER=your_project_number
```

### 各種APIキー・IDの取得方法

#### Notion API Key
1. [Notion Developers](https://www.notion.so/my-integrations) にアクセスします
2. 右上の「+ New integration」をクリックします
3. 統合の名前（例：「GitHub Projects Export」）を入力し、関連するワークスペースを選択します
4. 「Submit」をクリックします
5. 作成された統合の画面に表示される「Internal Integration Token」がAPIキーです

#### Notion Database ID
1. NotionでデータベースのページをWebブラウザで開きます
2. URLの `https://www.notion.so/` に続く部分を確認します
   - 例：`https://www.notion.so/myworkspace/83c75a51b3fe4a1aad9f0cbe6d75c89e?v=...`
   - この場合、Database IDは `83c75a51b3fe4a1aad9f0cbe6d75c89e` です
3. ※注意：Notionの統合をそのデータベースに追加する権限設定も必要です
   - データベースページの右上「...」→「Add connections」から、作成した統合を追加します

#### GitHub Token
1. [GitHub Personal Access Tokens](https://github.com/settings/tokens) にアクセスします
2. 「Generate new token」をクリックします（Classic or Fine-grained）
3. トークンの名前を入力します（例：「Notion to GitHub Projects」）
4. 少なくとも以下のスコープを選択します：
   - `project`（全て）
5. 「Generate token」をクリックします
6. 表示されたトークンを保存します（この画面を閉じると二度と表示されません）

#### GitHub Owner
- 個人アカウントの場合：あなたのGitHubのユーザー名
- 組織の場合：組織の名前

#### GitHub Project Number
1. GitHubでプロジェクトを開きます
2. URLの `https://github.com/users/[username]/projects/` または `https://github.com/orgs/[orgname]/projects/` の後にある数字がプロジェクト番号です
   - 例：`https://github.com/users/username/projects/42` の場合、プロジェクト番号は `42` です

## 特徴

- **リポジトリ不要**: タスクはDraftアイテムとして直接GitHub Projectsに追加されます。あとで必要に応じてリポジトリに紐付けることができます。
- **柔軟なマッピング**: Notionのステータス、タグ、担当者、期日をGitHub Projectsのフィールドに柔軟にマッピングできます。
- **バッチ処理**: 一度に複数のNotionタスクを移行できます。

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

MITライセンス
