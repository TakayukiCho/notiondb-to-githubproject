"""
GitHub APIクライアント

GitHub APIを使ってGitHub Projectsにタスクをインポートします。
"""

import logging
from typing import Dict, List, Any, Optional, Tuple
import requests
import json
import config
from github import Github
from github.GithubException import GithubException

class GitHubClient:
    """
    GitHub APIと通信するためのクライアントクラス
    
    このクラスはGitHubのAPIを使用してタスクをGitHub Projectに追加する機能を提供します。
    GitHub GraphQL APIを使用して直接プロジェクトにDraftアイテムを追加します。
    """
    
    def __init__(self, token: Optional[str] = None, owner: Optional[str] = None, 
                 project_number: Optional[str] = None):
        """
        GitHubClientの初期化
        
        Args:
            token: GitHub APIトークン。指定しない場合は環境変数から取得
            owner: GitHubの所有者名（ユーザー名または組織名）。指定しない場合は環境変数から取得
            project_number: GitHub Projectの番号。指定しない場合は環境変数から取得
        """
        self.token = token or config.GITHUB_TOKEN
        self.owner = owner or config.GITHUB_OWNER
        self.project_number = project_number or config.GITHUB_PROJECT_NUMBER
        
        if not self.token:
            raise ValueError("GitHub Tokenが設定されていません。.envファイルを確認してください。")
        
        if not self.owner:
            raise ValueError("GitHub Ownerが設定されていません。.envファイルを確認してください。")
        
        if not self.project_number:
            raise ValueError("GitHub Project Numberが設定されていません。.envファイルを確認してください。")
        
        # GraphQLのエンドポイント
        self.graphql_url = "https://api.github.com/graphql"
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        # プロジェクトIDとプロジェクトフィールドのキャッシュ
        self._project_id = None
        self._field_ids = {}
        
        self.logger = logging.getLogger(__name__)
    
    def get_project_id(self) -> str:
        """
        プロジェクトのIDを取得します。
        
        GitHub Projectsはプロジェクト番号と内部IDの両方を持っています。
        GraphQL APIを使用するにはプロジェクトの内部IDが必要です。
        
        Returns:
            プロジェクトのID
        """
        if self._project_id:
            return self._project_id
            
        # ユーザープロジェクトかOrganizationプロジェクトかを判定
        # ユーザープロジェクトの場合
        query = """
        query($owner: String!, $project_number: Int!) {
            user(login: $owner) {
                projectV2(number: $project_number) {
                    id
                }
            }
        }
        """
        
        variables = {
            "owner": self.owner,
            "project_number": int(self.project_number)
        }
        
        response = requests.post(
            self.graphql_url, 
            headers=self.headers, 
            json={"query": query, "variables": variables}
        )
        
        data = response.json()
        
        # ユーザープロジェクトの場合
        if "data" in data and data["data"]["user"] and data["data"]["user"]["projectV2"]:
            project_id = data["data"]["user"]["projectV2"]["id"]
            self._project_id = project_id
            return project_id
        
        # Organizationプロジェクトの場合
        query = """
        query($owner: String!, $project_number: Int!) {
            organization(login: $owner) {
                projectV2(number: $project_number) {
                    id
                }
            }
        }
        """
        
        response = requests.post(
            self.graphql_url, 
            headers=self.headers, 
            json={"query": query, "variables": variables}
        )
        
        data = response.json()
        if "errors" in data or not data["data"]["organization"] or not data["data"]["organization"]["projectV2"]:
            error_message = data.get("errors", [{"message": "プロジェクトが見つかりません"}])[0]["message"]
            self.logger.error(f"プロジェクトIDの取得に失敗しました: {error_message}")
            raise ValueError(f"プロジェクトIDの取得に失敗しました: {error_message}")
            
        project_id = data["data"]["organization"]["projectV2"]["id"]
        self._project_id = project_id
        return project_id
    
    def get_field_ids(self) -> Dict[str, str]:
        """
        プロジェクトのフィールドIDを取得します。
        
        GitHub Projectsのフィールドは内部IDを持っています。
        GraphQL APIを使用するにはフィールドの内部IDが必要です。
        
        Returns:
            フィールド名からフィールドIDへのマッピング辞書
        """
        if self._field_ids:
            return self._field_ids
            
        project_id = self.get_project_id()
        
        query = """
        query($project_id: ID!) {
            node(id: $project_id) {
                ... on ProjectV2 {
                    fields(first: 20) {
                        nodes {
                            ... on ProjectV2Field {
                                id
                                name
                            }
                            ... on ProjectV2IterationField {
                                id
                                name
                            }
                            ... on ProjectV2SingleSelectField {
                                id
                                name
                                options {
                                    id
                                    name
                                }
                            }
                        }
                    }
                }
            }
        }
        """
        
        variables = {
            "project_id": project_id
        }
        
        response = requests.post(
            self.graphql_url, 
            headers=self.headers, 
            json={"query": query, "variables": variables}
        )
        
        data = response.json()
        if "errors" in data:
            error_message = data["errors"][0]["message"]
            self.logger.error(f"フィールドIDの取得に失敗しました: {error_message}")
            raise ValueError(f"フィールドIDの取得に失敗しました: {error_message}")
            
        field_mappings = {}
        fields = data["data"]["node"]["fields"]["nodes"]
        
        for field in fields:
            field_name = field["name"]
            field_id = field["id"]
            field_mappings[field_name] = field_id
            
            # ステータスフィールドの場合は、各オプションのIDも保存
            if "options" in field:
                for option in field["options"]:
                    option_name = option["name"]
                    option_id = option["id"]
                    field_mappings[f"{field_name}:{option_name}"] = option_id
        
        self._field_ids = field_mappings
        return field_mappings
    
    def create_draft_item(self, task_data: Dict[str, Any]) -> str:
        """
        GitHub ProjectsにDraftアイテムを直接作成します。
        
        Args:
            task_data: タスクデータ
            
        Returns:
            作成されたDraftアイテムのID
        """
        title = task_data.get('title', 'No Title')
        project_id = self.get_project_id()
        
        # Draftアイテムを作成するGraphQLミューテーション
        query = """
        mutation($project_id: ID!, $title: String!) {
            addProjectV2DraftItem(input: {
                projectId: $project_id,
                title: $title
            }) {
                projectItem {
                    id
                }
            }
        }
        """
        
        variables = {
            "project_id": project_id,
            "title": title
        }
        
        try:
            response = requests.post(
                self.graphql_url, 
                headers=self.headers, 
                json={"query": query, "variables": variables}
            )
            
            data = response.json()
            if "errors" in data:
                error_message = data["errors"][0]["message"]
                self.logger.error(f"Draftアイテム作成に失敗しました: {title}, エラー: {error_message}")
                raise ValueError(f"Draftアイテム作成に失敗しました: {error_message}")
            
            item_id = data["data"]["addProjectV2DraftItem"]["projectItem"]["id"]
            return item_id
            
        except Exception as e:
            self.logger.error(f"Draftアイテム作成に失敗しました: {title}, エラー: {str(e)}")
            raise
    
    def update_item_field(self, item_id: str, field_name: str, field_value: Any) -> bool:
        """
        プロジェクトのアイテムフィールドを更新します。
        
        Args:
            item_id: アイテムのID
            field_name: フィールド名
            field_value: フィールド値
            
        Returns:
            更新に成功したかどうか
        """
        field_ids = self.get_field_ids()
        
        if field_name not in field_ids:
            self.logger.warning(f"フィールド '{field_name}' が見つかりません")
            return False
        
        field_id = field_ids[field_name]
        project_id = self.get_project_id()
        
        # フィールドタイプに応じたミューテーションを選択
        if field_name == "Status":
            # ステータスフィールドの場合
            status_option_key = f"Status:{field_value}"
            if status_option_key not in field_ids:
                self.logger.warning(f"ステータスオプション '{field_value}' が見つかりません")
                return False
                
            option_id = field_ids[status_option_key]
            
            query = """
            mutation($project_id: ID!, $item_id: ID!, $field_id: ID!, $option_id: String!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $project_id,
                    itemId: $item_id,
                    fieldId: $field_id,
                    value: {
                        singleSelectOptionId: $option_id
                    }
                }) {
                    clientMutationId
                }
            }
            """
            
            variables = {
                "project_id": project_id,
                "item_id": item_id,
                "field_id": field_id,
                "option_id": option_id
            }
        
        elif field_name == "Due Date":
            # 期日フィールドの場合
            query = """
            mutation($project_id: ID!, $item_id: ID!, $field_id: ID!, $date_value: Date!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $project_id,
                    itemId: $item_id,
                    fieldId: $field_id,
                    value: {
                        date: $date_value
                    }
                }) {
                    clientMutationId
                }
            }
            """
            
            variables = {
                "project_id": project_id,
                "item_id": item_id,
                "field_id": field_id,
                "date_value": field_value
            }
            
        else:
            # その他のテキストフィールドの場合
            query = """
            mutation($project_id: ID!, $item_id: ID!, $field_id: ID!, $text_value: String!) {
                updateProjectV2ItemFieldValue(input: {
                    projectId: $project_id,
                    itemId: $item_id,
                    fieldId: $field_id,
                    value: {
                        text: $text_value
                    }
                }) {
                    clientMutationId
                }
            }
            """
            
            variables = {
                "project_id": project_id,
                "item_id": item_id,
                "field_id": field_id,
                "text_value": str(field_value)
            }
        
        response = requests.post(
            self.graphql_url, 
            headers=self.headers, 
            json={"query": query, "variables": variables}
        )
        
        data = response.json()
        if "errors" in data:
            error_message = data["errors"][0]["message"]
            self.logger.error(f"フィールド更新に失敗しました: {error_message}")
            return False
            
        return True
    
    def update_item_body(self, item_id: str, body: str) -> bool:
        """
        プロジェクトのアイテムの説明を更新します。
        
        Args:
            item_id: アイテムのID
            body: 説明文
            
        Returns:
            更新に成功したかどうか
        """
        project_id = self.get_project_id()
        
        query = """
        mutation($project_id: ID!, $item_id: ID!, $body: String!) {
            updateProjectV2ItemFieldValue(input: {
                projectId: $project_id,
                itemId: $item_id,
                fieldId: "PVTF_NOTE",
                value: {
                    text: $body
                }
            }) {
                clientMutationId
            }
        }
        """
        
        variables = {
            "project_id": project_id,
            "item_id": item_id,
            "body": body
        }
        
        response = requests.post(
            self.graphql_url, 
            headers=self.headers, 
            json={"query": query, "variables": variables}
        )
        
        data = response.json()
        if "errors" in data:
            error_message = data["errors"][0]["message"]
            self.logger.error(f"説明更新に失敗しました: {error_message}")
            return False
            
        return True
    
    def import_task(self, task_data: Dict[str, Any]) -> Tuple[bool, Optional[str]]:
        """
        タスクをGitHub Projectsにインポートします。
        
        Args:
            task_data: タスクデータ
            
        Returns:
            (成功したかどうか, エラーメッセージ)
        """
        try:
            # 1. Draftアイテムを作成
            item_id = self.create_draft_item(task_data)
            
            # 2. 説明を設定
            body = task_data.get('description', '')
            
            # タスクのソースとしてNotionのURLを追加
            if 'url' in task_data:
                body += f"\n\n*From Notion: {task_data['url']}*"
                
            if body:
                self.update_item_body(item_id, body)
            
            # 3. ステータスを設定（あれば）
            if 'status' in task_data and task_data['status']:
                self.update_item_field(item_id, "Status", task_data['status'])
            
            # 4. 期日を設定（あれば）
            if 'due_date' in task_data and task_data['due_date']:
                self.update_item_field(item_id, "Due Date", task_data['due_date'])
            
            # 5. アサインの追加（あれば）- カスタムフィールドとして設定する必要があります
            if 'assignees' in task_data and task_data['assignees'] and len(task_data['assignees']) > 0:
                assignee_text = ", ".join(task_data['assignees'])
                self.update_item_field(item_id, "Assignees", assignee_text)
            
            # 6. ラベルの追加（あれば）- カスタムフィールドとして設定する必要があります
            if 'tags' in task_data and task_data['tags'] and len(task_data['tags']) > 0:
                labels_text = ", ".join(task_data['tags'])
                self.update_item_field(item_id, "Labels", labels_text)
            
            return (True, None)
            
        except Exception as e:
            error_message = f"タスクのインポートに失敗しました: {str(e)}"
            self.logger.error(error_message)
            return (False, error_message) 