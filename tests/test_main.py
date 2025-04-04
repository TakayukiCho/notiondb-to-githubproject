"""
メインスクリプトのテスト

main.pyの機能をテストします。
"""

import unittest
import os
import sys
import json
from unittest.mock import patch, MagicMock, Mock

# テスト対象のモジュールをインポートするためにパスを追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import main
import config
from notion_api_client import NotionClient
from github_client import GitHubClient

class TestMain(unittest.TestCase):
    """メインモジュールのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        # 環境変数の設定
        self.original_notion_api_key = config.NOTION_API_KEY
        self.original_notion_database_id = config.NOTION_DATABASE_ID
        self.original_github_token = config.GITHUB_TOKEN
        self.original_github_owner = config.GITHUB_OWNER
        self.original_github_project_number = config.GITHUB_PROJECT_NUMBER
        
        config.NOTION_API_KEY = "test_api_key"
        config.NOTION_DATABASE_ID = "test_database_id"
        config.GITHUB_TOKEN = "test_github_token"
        config.GITHUB_OWNER = "test_owner"
        config.GITHUB_PROJECT_NUMBER = "42"
        
        # モックデータの読み込み
        with open(os.path.join(os.path.dirname(__file__), 'mock_data/notion_database.json'), 'r') as f:
            self.notion_mock_data = json.load(f)
    
    def tearDown(self):
        """テストの後処理"""
        # 環境変数を元に戻す
        config.NOTION_API_KEY = self.original_notion_api_key
        config.NOTION_DATABASE_ID = self.original_notion_database_id
        config.GITHUB_TOKEN = self.original_github_token
        config.GITHUB_OWNER = self.original_github_owner
        config.GITHUB_PROJECT_NUMBER = self.original_github_project_number
    
    def test_setup_argument_parser(self):
        """引数パーサーのセットアップテスト"""
        parser = main.setup_argument_parser()
        
        # 必要な引数がパーサーに追加されているか確認
        arguments = [action.dest for action in parser._actions]
        self.assertIn('dry_run', arguments)
        self.assertIn('config', arguments)
        self.assertIn('notion_database_id', arguments)
        self.assertIn('github_project_number', arguments)
        self.assertIn('log_level', arguments)
        
        # デフォルト値の確認
        args = parser.parse_args([])
        self.assertFalse(args.dry_run)
        self.assertEqual(args.log_level, 'INFO')
    
    @patch('main.GitHubClient')
    @patch('main.NotionClient')
    def test_migrate_tasks_dry_run(self, mock_notion_client, mock_github_client):
        """ドライランモードでのタスク移行テスト"""
        # モックの設定
        mock_notion_instance = mock_notion_client.return_value
        mock_notion_instance.get_all_tasks.return_value = [
            {'title': 'Task 1', 'status': 'In Progress'},
            {'title': 'Task 2', 'status': 'Done'}
        ]
        
        mock_github_instance = mock_github_client.return_value
        
        # タスク移行の実行
        stats = main.migrate_tasks(mock_notion_instance, mock_github_instance, dry_run=True)
        
        # ドライランの場合、GitHub APIは呼ばれない
        mock_github_instance.import_task.assert_not_called()
        
        # 統計情報の確認
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['success'], 0)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['skipped'], 0)
    
    @patch('main.GitHubClient')
    @patch('main.NotionClient')
    def test_migrate_tasks_success(self, mock_notion_client, mock_github_client):
        """タスク移行成功のテスト"""
        # モックの設定
        mock_notion_instance = mock_notion_client.return_value
        mock_notion_instance.get_all_tasks.return_value = [
            {'title': 'Task 1', 'status': 'In Progress'},
            {'title': 'Task 2', 'status': 'Done'}
        ]
        
        mock_github_instance = mock_github_client.return_value
        mock_github_instance.import_task.return_value = (True, None)
        
        # タスク移行の実行
        stats = main.migrate_tasks(mock_notion_instance, mock_github_instance, dry_run=False)
        
        # GitHub APIが正しく呼ばれたか確認
        self.assertEqual(mock_github_instance.import_task.call_count, 2)
        
        # 統計情報の確認
        self.assertEqual(stats['total'], 2)
        self.assertEqual(stats['success'], 2)
        self.assertEqual(stats['failed'], 0)
        self.assertEqual(stats['skipped'], 0)
    
    @patch('main.GitHubClient')
    @patch('main.NotionClient')
    def test_migrate_tasks_partial_failure(self, mock_notion_client, mock_github_client):
        """タスク移行一部失敗のテスト"""
        # モックの設定
        mock_notion_instance = mock_notion_client.return_value
        mock_notion_instance.get_all_tasks.return_value = [
            {'title': 'Task 1', 'status': 'In Progress'},
            {'title': 'Task 2', 'status': 'Done'},
            {'title': 'Task 3', 'status': 'Backlog'}
        ]
        
        mock_github_instance = mock_github_client.return_value
        mock_github_instance.import_task.side_effect = [
            (True, None),              # 1つ目のタスクは成功
            (False, "エラーが発生しました"),  # 2つ目のタスクは失敗
            (True, None)               # 3つ目のタスクは成功
        ]
        
        # タスク移行の実行
        stats = main.migrate_tasks(mock_notion_instance, mock_github_instance, dry_run=False)
        
        # GitHub APIが正しく呼ばれたか確認
        self.assertEqual(mock_github_instance.import_task.call_count, 3)
        
        # 統計情報の確認
        self.assertEqual(stats['total'], 3)
        self.assertEqual(stats['success'], 2)
        self.assertEqual(stats['failed'], 1)
        self.assertEqual(stats['skipped'], 0)
        self.assertEqual(len(stats['failures']), 1)
        self.assertEqual(stats['failures'][0]['title'], 'Task 2')
        self.assertEqual(stats['failures'][0]['error'], 'エラーが発生しました')
    
    @patch('main.migrate_tasks')
    @patch('main.GitHubClient')
    @patch('main.NotionClient')
    @patch('main.setup_argument_parser')
    def test_main_success(self, mock_parser, mock_notion_client, mock_github_client, mock_migrate):
        """main関数成功のテスト"""
        # モックの設定
        mock_args = MagicMock()
        mock_args.dry_run = False
        mock_args.config = None
        mock_args.notion_database_id = None
        mock_args.github_project_number = None
        mock_args.log_level = 'INFO'
        
        mock_parser.return_value.parse_args.return_value = mock_args
        
        mock_notion_instance = mock_notion_client.return_value
        mock_github_instance = mock_github_client.return_value
        
        mock_migrate.return_value = {
            'total': 3,
            'success': 3,
            'failed': 0,
            'skipped': 0,
            'failures': []
        }
        
        # main関数の実行
        with patch('sys.exit') as mock_exit:
            main.main()
            
            # 正常終了の場合、sys.exitは呼ばれない
            mock_exit.assert_not_called()
        
        # クライアントが正しく初期化されたか確認
        mock_notion_client.assert_called_once()
        mock_github_client.assert_called_once()
        
        # タスク移行が正しく呼ばれたか確認
        mock_migrate.assert_called_once_with(mock_notion_instance, mock_github_instance, False)
    
    @patch('main.migrate_tasks')
    @patch('main.GitHubClient')
    @patch('main.NotionClient')
    @patch('main.setup_argument_parser')
    def test_main_with_failures(self, mock_parser, mock_notion_client, mock_github_client, mock_migrate):
        """main関数失敗のテスト"""
        # モックの設定
        mock_args = MagicMock()
        mock_args.dry_run = False
        mock_args.config = None
        mock_args.notion_database_id = None
        mock_args.github_project_number = None
        mock_args.log_level = 'INFO'
        
        mock_parser.return_value.parse_args.return_value = mock_args
        
        mock_notion_instance = mock_notion_client.return_value
        mock_github_instance = mock_github_client.return_value
        
        mock_migrate.return_value = {
            'total': 3,
            'success': 2,
            'failed': 1,
            'skipped': 0,
            'failures': [
                {'title': 'Task 2', 'error': 'エラーが発生しました'}
            ]
        }
        
        # main関数の実行
        with patch('sys.exit') as mock_exit:
            main.main()
            
            # 失敗が含まれる場合、sys.exit(1)が呼ばれる
            mock_exit.assert_called_once_with(1)
        
        # クライアントが正しく初期化されたか確認
        mock_notion_client.assert_called_once()
        mock_github_client.assert_called_once()
        
        # タスク移行が正しく呼ばれたか確認
        mock_migrate.assert_called_once_with(mock_notion_instance, mock_github_instance, False)

if __name__ == '__main__':
    unittest.main() 