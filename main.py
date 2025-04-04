#!/usr/bin/env python3
"""
NotionDB to GitHub Projects

NotionデータベースからGitHub Projectsにデータを移行するためのツール。
"""

import argparse
import logging
from typing import Dict, List, Any, Optional
import json
import sys
import os
from notion_api_client import NotionClient
from github_client import GitHubClient
import config

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('notiondb_to_github.log')
    ]
)

logger = logging.getLogger(__name__)

def setup_argument_parser() -> argparse.ArgumentParser:
    """
    コマンドライン引数のパーサーを設定します。
    
    Returns:
        引数パーサー
    """
    parser = argparse.ArgumentParser(
        description="NotionデータベースからGitHub Projectsにデータを移行するツール"
    )
    
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="実際にデータをGitHubにインポートせず、処理内容を表示するだけのモード"
    )
    
    parser.add_argument(
        "--config",
        type=str,
        help="カスタム設定ファイルへのパス（.env以外の設定を使用する場合）"
    )
    
    parser.add_argument(
        "--notion-database-id",
        type=str,
        help="Notion Database ID（.envファイルの値を上書きします）"
    )
    
    parser.add_argument(
        "--github-project-number",
        type=str,
        help="GitHub Project Number（.envファイルの値を上書きします）"
    )
    
    parser.add_argument(
        "--log-level",
        choices=["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"],
        default="INFO",
        help="ログレベル（デフォルト: INFO）"
    )
    
    return parser

def migrate_tasks(notion_client: NotionClient, github_client: GitHubClient, dry_run: bool = False) -> Dict[str, Any]:
    """
    NotionのタスクをGitHub Projectsに移行します。
    
    Args:
        notion_client: NotionのAPIクライアント
        github_client: GitHubのAPIクライアント
        dry_run: 実際にGitHubにインポートしない場合はTrue
        
    Returns:
        移行結果の統計情報
    """
    # 統計情報
    stats = {
        "total": 0,
        "success": 0,
        "failed": 0,
        "skipped": 0,
        "failures": []
    }
    
    # Notionからタスクを取得
    logger.info("Notionからタスクを取得しています...")
    tasks = notion_client.get_all_tasks()
    stats["total"] = len(tasks)
    
    logger.info(f"取得したタスク数: {len(tasks)}")
    
    if dry_run:
        logger.info("ドライランモードが有効です。実際のデータ移行は行いません。")
        for i, task in enumerate(tasks, 1):
            logger.info(f"タスク {i}/{len(tasks)}: {task.get('title', 'No Title')}")
            logger.debug(f"タスクデータ: {json.dumps(task, ensure_ascii=False, indent=2)}")
        
        return stats
    
    # GitHub Projectsにタスクをインポート
    logger.info("GitHub Projectsにタスクをインポートしています...")
    
    for i, task in enumerate(tasks, 1):
        task_title = task.get('title', 'No Title')
        logger.info(f"タスク {i}/{len(tasks)} をインポート中: {task_title}")
        
        success, error_message = github_client.import_task(task)
        
        if success:
            logger.info(f"タスク '{task_title}' のインポートに成功しました。")
            stats["success"] += 1
        else:
            logger.error(f"タスク '{task_title}' のインポートに失敗しました: {error_message}")
            stats["failed"] += 1
            stats["failures"].append({
                "title": task_title,
                "error": error_message
            })
    
    return stats

def main():
    """
    メインの実行関数
    """
    parser = setup_argument_parser()
    args = parser.parse_args()
    
    # ログレベルの設定
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    try:
        # カスタム設定ファイルの読み込み
        if args.config:
            if not os.path.exists(args.config):
                logger.error(f"設定ファイル '{args.config}' が見つかりません。")
                sys.exit(1)
            
            logger.info(f"カスタム設定ファイル '{args.config}' を読み込みます。")
            # TODO: カスタム設定ファイルの読み込み処理
        
        # コマンドライン引数による設定の上書き
        if args.notion_database_id:
            config.NOTION_DATABASE_ID = args.notion_database_id
            logger.info(f"Notion Database IDを上書きしました: {args.notion_database_id}")
        
        if args.github_project_number:
            config.GITHUB_PROJECT_NUMBER = args.github_project_number
            logger.info(f"GitHub Project Numberを上書きしました: {args.github_project_number}")
        
        # クライアントの初期化
        notion_client = NotionClient()
        github_client = GitHubClient()
        
        # タスクの移行
        stats = migrate_tasks(notion_client, github_client, args.dry_run)
        
        # 結果の表示
        logger.info("====== 移行結果 ======")
        logger.info(f"合計タスク数: {stats['total']}")
        logger.info(f"成功: {stats['success']}")
        logger.info(f"失敗: {stats['failed']}")
        logger.info(f"スキップ: {stats['skipped']}")
        
        if stats["failures"]:
            logger.info("------ 失敗したタスク ------")
            for failure in stats["failures"]:
                logger.info(f"タイトル: {failure['title']}")
                logger.info(f"エラー: {failure['error']}")
                logger.info("-------------------------")
        
        if stats["failed"] > 0:
            sys.exit(1)
    
    except KeyboardInterrupt:
        logger.info("ユーザーによる中断を検出しました。終了します。")
        sys.exit(130)
    
    except Exception as e:
        logger.exception(f"予期しないエラーが発生しました: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main() 