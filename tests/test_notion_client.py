"""
NotionClientのテスト

Notionクライアントの機能をモックデータを使用してテストします。
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock
import sys

# テスト対象のモジュールをインポートするためにパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from notion_api_client import NotionClient
import config

class TestNotionClient(unittest.TestCase):
    """NotionClientクラスのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # 環境変数の設定
        self.original_notion_api_key = config.NOTION_API_KEY
        self.original_notion_database_id = config.NOTION_DATABASE_ID
        
        config.NOTION_API_KEY = "test_api_key"
        config.NOTION_DATABASE_ID = "test_database_id"
        
        # モックデータの読み込み
        with open(os.path.join(os.path.dirname(__file__), 'mock_data/notion_database.json'), 'r') as f:
            self.mock_data = json.load(f)
    
    def tearDown(self):
        """テストの後処理"""
        # 環境変数を元に戻す
        config.NOTION_API_KEY = self.original_notion_api_key
        config.NOTION_DATABASE_ID = self.original_notion_database_id
    
    @patch('notion_api_client.NotionSDKClient')
    def test_init(self, mock_notion_client):
        """初期化のテスト"""
        # NotionClientのインスタンス化
        client = NotionClient()
        
        # APIキーとデータベースIDの設定が正しいか確認
        self.assertEqual(client.api_key, "test_api_key")
        self.assertEqual(client.database_id, "test_database_id")
        
        # Notion SDKクライアントが正しく初期化されたか確認
        mock_notion_client.assert_called_once_with(auth="test_api_key")
    
    @patch('notion_api_client.NotionSDKClient')
    def test_get_database_schema(self, mock_notion_client):
        """データベーススキーマ取得のテスト"""
        # モックの設定
        mock_instance = mock_notion_client.return_value
        mock_instance.databases.retrieve.return_value = {
            "properties": {
                "Name": {"type": "title"},
                "Status": {"type": "status"},
                "Tags": {"type": "multi_select"},
                "Person": {"type": "people"},
                "Due Date": {"type": "date"}
            }
        }
        
        # NotionClientのインスタンス化
        client = NotionClient()
        
        # スキーマを取得
        schema = client.get_database_schema()
        
        # 正しいスキーマが取得できたか確認
        self.assertEqual(schema["Name"]["type"], "title")
        self.assertEqual(schema["Status"]["type"], "status")
        self.assertEqual(schema["Tags"]["type"], "multi_select")
        self.assertEqual(schema["Person"]["type"], "people")
        self.assertEqual(schema["Due Date"]["type"], "date")
        
        # Notion APIが正しく呼び出されたか確認
        mock_instance.databases.retrieve.assert_called_once_with("test_database_id")
    
    @patch('notion_api_client.NotionSDKClient')
    def test_get_all_tasks(self, mock_notion_client):
        """タスク取得のテスト"""
        # モックの設定
        mock_instance = mock_notion_client.return_value
        mock_instance.databases.query.return_value = self.mock_data
        
        # NotionClientのインスタンス化
        client = NotionClient()
        
        # タスクを取得
        tasks = client.get_all_tasks()
        
        # 正しい数のタスクが取得できたか確認
        self.assertEqual(len(tasks), 3)
        
        # タスクの内容が正しく解析されたか確認
        self.assertEqual(tasks[0]["title"], "[edge上mtg] OptinOptoutのあるべきを考える")
        self.assertEqual(tasks[0]["status"], "In Progress")  # マッピング後のステータス
        self.assertEqual(tasks[0]["tags"], ["sdk"])  # マッピング後のタグ
        self.assertEqual(tasks[0]["assignees"], ["Takayuki Cho"])
        self.assertEqual(tasks[0]["due_date"], "2024-12-05")
        
        # 2つ目のタスクも確認
        self.assertEqual(tasks[1]["title"], "条件判定期間・集計タイミングの仕様：サポサイ作成&管理画面注記")
        self.assertEqual(tasks[1]["assignees"], ["Minami Oki", "Toi"])
        
        # Notion APIが正しく呼び出されたか確認
        mock_instance.databases.query.assert_called_once_with(database_id="test_database_id", page_size=100)
    
    @patch('notion_api_client.NotionSDKClient')
    def test_parse_page(self, mock_notion_client):
        """ページ解析のテスト"""
        # NotionClientのインスタンス化
        client = NotionClient()
        
        # モックページデータ
        page_data = self.mock_data["results"][0]
        
        # ページを解析
        task = client._parse_page(page_data)
        
        # 解析結果が正しいか確認
        self.assertEqual(task["notion_id"], "notion_page_id_1")
        self.assertEqual(task["url"], "https://www.notion.so/page1")
        self.assertEqual(task["title"], "[edge上mtg] OptinOptoutのあるべきを考える")
        self.assertEqual(task["status"], "In Progress")  # マッピング後のステータス
        self.assertEqual(task["tags"], ["sdk"])  # マッピング後のタグ
        self.assertEqual(task["assignees"], ["Takayuki Cho"])
        self.assertEqual(task["due_date"], "2024-12-05")

if __name__ == '__main__':
    unittest.main() 