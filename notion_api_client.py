"""
Notion APIクライアント

NotionのAPIを使ってデータベースからタスク情報を取得します。
"""

import logging
from typing import Dict, List, Any, Optional
from notion_client import Client as NotionSDKClient
from datetime import datetime
import config

class NotionClient:
    """
    Notion APIと通信するためのクライアントクラス
    
    このクラスはNotionのAPIを使用してデータベースからタスク情報を取得し、
    GitHub Projectに適したフォーマットに変換する機能を提供します。
    """
    
    def __init__(self, api_key: Optional[str] = None, database_id: Optional[str] = None):
        """
        NotionClientの初期化
        
        Args:
            api_key: Notion APIキー。指定しない場合は環境変数から取得
            database_id: Notionデータベースのコピー。指定しない場合は環境変数から取得
        """
        self.api_key = api_key or config.NOTION_API_KEY
        self.database_id = database_id or config.NOTION_DATABASE_ID
        
        if not self.api_key:
            raise ValueError("Notion API Keyが設定されていません。.envファイルを確認してください。")
        
        if not self.database_id:
            raise ValueError("Notion Database IDが設定されていません。.envファイルを確認してください。")
        
        self.client = NotionSDKClient(auth=self.api_key)
        self.logger = logging.getLogger(__name__)
    
    def get_database_schema(self) -> Dict[str, Any]:
        """
        データベースのスキーマ情報を取得します。
        
        Returns:
            データベースのプロパティ情報を含む辞書
        """
        try:
            database = self.client.databases.retrieve(self.database_id)
            return database.get('properties', {})
        except Exception as e:
            self.logger.error(f"データベーススキーマの取得に失敗しました: {e}")
            raise
    
    def get_all_tasks(self) -> List[Dict[str, Any]]:
        """
        データベースから全てのタスクを取得します。
        
        Returns:
            タスク情報を含む辞書のリスト
        """
        try:
            # 全ページを取得するための再帰関数
            def fetch_pages(cursor=None, results=None):
                if results is None:
                    results = []
                
                query_params = {
                    "database_id": self.database_id,
                    "page_size": 100  # 最大ページサイズ
                }
                
                if cursor:
                    query_params["start_cursor"] = cursor
                
                response = self.client.databases.query(**query_params)
                results.extend(response.get("results", []))
                
                # 次のページがあれば続けて取得
                if response.get("has_more", False):
                    return fetch_pages(response.get("next_cursor"), results)
                
                return results
            
            all_pages = fetch_pages()
            return [self._parse_page(page) for page in all_pages]
        
        except Exception as e:
            self.logger.error(f"タスクの取得に失敗しました: {e}")
            raise
    
    def _parse_page(self, page: Dict[str, Any]) -> Dict[str, Any]:
        """
        Notionのページデータをパースして必要な情報を抽出します。
        
        Args:
            page: Notionページのデータ
            
        Returns:
            パースされたタスク情報
        """
        properties = page.get('properties', {})
        task_data = {
            'notion_id': page.get('id'),
            'url': page.get('url')
        }
        
        # 各プロパティをパース
        for prop_name, prop_data in properties.items():
            prop_type = prop_data.get('type')
            
            if prop_type == 'title':
                # タイトルフィールド
                title_objects = prop_data.get('title', [])
                title_text = "".join([obj.get('plain_text', '') for obj in title_objects])
                task_data['title'] = title_text
            
            elif prop_type == 'status':
                # ステータスフィールド
                status_value = prop_data.get('status', {}).get('name', '')
                # GitHubのステータスにマッピング
                task_data['status'] = config.STATUS_MAPPING.get(status_value, status_value)
            
            elif prop_type == 'multi_select':
                # マルチセレクト（タグなど）
                multi_select_values = []
                for option in prop_data.get('multi_select', []):
                    value = option.get('name', '')
                    # GitHubのラベルにマッピング
                    mapped_value = config.TAG_MAPPING.get(value, value)
                    multi_select_values.append(mapped_value)
                task_data['tags'] = multi_select_values
            
            elif prop_type == 'people':
                # 担当者
                assignees = []
                for person in prop_data.get('people', []):
                    name = person.get('name', '')
                    if name:
                        assignees.append(name)
                task_data['assignees'] = assignees
            
            elif prop_type == 'date':
                # 期日
                date_data = prop_data.get('date', {})
                start_date = date_data.get('start')
                if start_date:
                    # ISO 8601形式の日付をGitHubの形式に変換
                    try:
                        dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
                        task_data['due_date'] = dt.strftime('%Y-%m-%d')
                    except ValueError:
                        self.logger.warning(f"日付の解析に失敗しました: {start_date}")
            
            elif prop_type == 'rich_text':
                # リッチテキスト（説明など）
                rich_text_objects = prop_data.get('rich_text', [])
                rich_text = "".join([obj.get('plain_text', '') for obj in rich_text_objects])
                if rich_text:
                    task_data['description'] = rich_text
        
        return task_data 