"""
GitHubClientのテスト

GitHubクライアントの機能をモックデータを使用してテストします。
"""

import unittest
import json
import os
from unittest.mock import patch, MagicMock, Mock
import sys
import requests

# テスト対象のモジュールをインポートするためにパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from github_client import GitHubClient
import config

class TestGitHubClient(unittest.TestCase):
    """GitHubClientクラスのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # 環境変数の設定
        self.original_github_token = config.GITHUB_TOKEN
        self.original_github_owner = config.GITHUB_OWNER
        self.original_github_project_number = config.GITHUB_PROJECT_NUMBER
        
        config.GITHUB_TOKEN = "test_github_token"
        config.GITHUB_OWNER = "test_owner"
        config.GITHUB_PROJECT_NUMBER = "42"
        
        # モックデータの読み込み
        with open(os.path.join(os.path.dirname(__file__), 'mock_data/github_project.json'), 'r') as f:
            self.mock_data = json.load(f)
        
        # テスト用のタスクデータ
        self.test_task = {
            "title": "テストタスク",
            "description": "これはテストタスクの説明です",
            "status": "In Progress",
            "assignees": ["testuser"],
            "tags": ["test", "documentation"],
            "due_date": "2024-12-31",
            "url": "https://www.notion.so/test_page"
        }
    
    def tearDown(self):
        """テストの後処理"""
        # 環境変数を元に戻す
        config.GITHUB_TOKEN = self.original_github_token
        config.GITHUB_OWNER = self.original_github_owner
        config.GITHUB_PROJECT_NUMBER = self.original_github_project_number
    
    @patch('github_client.requests.post')
    def test_init(self, mock_post):
        """初期化のテスト"""
        # GitHubClientのインスタンス化
        client = GitHubClient()
        
        # 設定が正しく行われたか確認
        self.assertEqual(client.token, "test_github_token")
        self.assertEqual(client.owner, "test_owner")
        self.assertEqual(client.project_number, "42")
        
        # ヘッダーが正しく設定されたか確認
        self.assertEqual(client.headers["Authorization"], "Bearer test_github_token")
    
    @patch('github_client.requests.post')
    def test_get_project_id(self, mock_post):
        """プロジェクトID取得のテスト"""
        # モックレスポンスの設定
        mock_response = Mock()
        mock_response.json.return_value = self.mock_data["project_id_response"]
        mock_post.return_value = mock_response
        
        # GitHubClientのインスタンス化
        client = GitHubClient()
        
        # プロジェクトIDを取得
        project_id = client.get_project_id()
        
        # 正しいプロジェクトIDが取得できたか確認
        self.assertEqual(project_id, "PVT_kwDOBDCxpc4AXYZ")
        
        # APIが正しく呼び出されたか確認
        mock_post.assert_called_once()
        args, kwargs = mock_post.call_args
        self.assertEqual(kwargs["headers"]["Authorization"], "Bearer test_github_token")
        self.assertIn("projectV2(number: 42)", kwargs["json"]["query"])
    
    @patch('github_client.requests.post')
    def test_get_field_ids(self, mock_post):
        """フィールドID取得のテスト"""
        # モックレスポンスの設定
        mock_responses = [
            Mock(),  # get_project_id用のレスポンス
            Mock()   # get_field_ids用のレスポンス
        ]
        mock_responses[0].json.return_value = self.mock_data["project_id_response"]
        mock_responses[1].json.return_value = self.mock_data["field_ids_response"]
        mock_post.side_effect = mock_responses
        
        # GitHubClientのインスタンス化
        client = GitHubClient()
        
        # フィールドIDを取得
        field_ids = client.get_field_ids()
        
        # 正しいフィールドIDが取得できたか確認
        self.assertEqual(field_ids["Title"], "PVTF_lADOBDCxpc4AXYZzM4AXYZ")
        self.assertEqual(field_ids["Status"], "PVTSSF_lADOBDCxpc4AXYZzM4AXYZ")
        self.assertEqual(field_ids["Status:In Progress"], "75d0b392")
        self.assertEqual(field_ids["Due Date"], "PVTF_lADOBDCxpc4AXYZzM4AXXZ")
        
        # APIが正しく呼び出されたか確認
        self.assertEqual(mock_post.call_count, 2)
    
    @patch('github_client.requests.post')
    def test_create_draft_item(self, mock_post):
        """Draftアイテム作成のテスト"""
        # モックレスポンスの設定
        mock_responses = [
            Mock(),  # get_project_id用のレスポンス
            Mock()   # create_draft_item用のレスポンス
        ]
        mock_responses[0].json.return_value = self.mock_data["project_id_response"]
        mock_responses[1].json.return_value = {
            "data": {
                "addProjectV2DraftItem": {
                    "projectItem": {
                        "id": "PVTI_lADOBDCxpc4AXYZzM4AXAA"
                    }
                }
            }
        }
        mock_post.side_effect = mock_responses
        
        # GitHubClientのインスタンス化
        client = GitHubClient()
        
        # Draftアイテムを作成
        item_id = client.create_draft_item(self.test_task)
        
        # 正しいアイテムIDが取得できたか確認
        self.assertEqual(item_id, "PVTI_lADOBDCxpc4AXYZzM4AXAA")
        
        # APIが正しく呼び出されたか確認
        self.assertEqual(mock_post.call_count, 2)
        args, kwargs = mock_post.call_args
        self.assertIn("addProjectV2DraftItem", kwargs["json"]["query"])
        self.assertEqual(kwargs["json"]["variables"]["title"], "テストタスク")
    
    @patch('github_client.requests.post')
    def test_update_item_field(self, mock_post):
        """アイテムフィールドの更新テスト"""
        # モックレスポンスの設定
        mock_responses = [
            Mock(),  # get_project_id用のレスポンス
            Mock(),  # get_field_ids用のレスポンス
            Mock()   # update_item_field用のレスポンス
        ]
        mock_responses[0].json.return_value = self.mock_data["project_id_response"]
        mock_responses[1].json.return_value = self.mock_data["field_ids_response"]
        mock_responses[2].json.return_value = self.mock_data["update_field_response"]
        mock_post.side_effect = mock_responses
        
        # GitHubClientのインスタンス化
        client = GitHubClient()
        
        # ステータスフィールドを更新
        success = client.update_item_field(
            "PVTI_lADOBDCxpc4AXYZzM4AXAA", 
            "Status", 
            "In Progress"
        )
        
        # 更新が成功したか確認
        self.assertTrue(success)
        
        # APIが正しく呼び出されたか確認
        self.assertEqual(mock_post.call_count, 3)
        args, kwargs = mock_post.call_args
        self.assertIn("updateProjectV2ItemFieldValue", kwargs["json"]["query"])
        self.assertEqual(kwargs["json"]["variables"]["option_id"], "75d0b392")
    
    @patch('github_client.requests.post')
    def test_update_item_body(self, mock_post):
        """アイテム説明の更新テスト"""
        # モックレスポンスの設定
        mock_responses = [
            Mock(),  # get_project_id用のレスポンス
            Mock()   # update_item_body用のレスポンス
        ]
        mock_responses[0].json.return_value = self.mock_data["project_id_response"]
        mock_responses[1].json.return_value = self.mock_data["update_field_response"]
        mock_post.side_effect = mock_responses
        
        # GitHubClientのインスタンス化
        client = GitHubClient()
        
        # 説明を更新
        success = client.update_item_body(
            "PVTI_lADOBDCxpc4AXYZzM4AXAA", 
            "これはテストの説明です"
        )
        
        # 更新が成功したか確認
        self.assertTrue(success)
        
        # APIが正しく呼び出されたか確認
        self.assertEqual(mock_post.call_count, 2)
        args, kwargs = mock_post.call_args
        self.assertIn("updateProjectV2ItemFieldValue", kwargs["json"]["query"])
        self.assertEqual(kwargs["json"]["variables"]["body"], "これはテストの説明です")
    
    @patch('github_client.GitHubClient.update_item_field')
    @patch('github_client.GitHubClient.update_item_body')
    @patch('github_client.GitHubClient.create_draft_item')
    def test_import_task(self, mock_create_draft, mock_update_body, mock_update_field):
        """タスクインポートのテスト"""
        # モックの設定
        mock_create_draft.return_value = "PVTI_lADOBDCxpc4AXYZzM4AXAA"
        mock_update_body.return_value = True
        mock_update_field.return_value = True
        
        # GitHubClientのインスタンス化
        client = GitHubClient()
        
        # タスクをインポート
        success, error = client.import_task(self.test_task)
        
        # インポートが成功したか確認
        self.assertTrue(success)
        self.assertIsNone(error)
        
        # 必要なメソッドが正しく呼び出されたか確認
        mock_create_draft.assert_called_once_with(self.test_task)
        mock_update_body.assert_called_once()
        
        # 更新対象のフィールドが正しいことを確認
        self.assertEqual(mock_update_field.call_count, 4)  # ステータス、期日、担当者、ラベル

if __name__ == '__main__':
    unittest.main() 