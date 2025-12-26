"""
URDF Kitchen Studio - 翻訳・国際化システム
日本語と英語の切り替え
"""

from typing import Dict, Optional


class TranslationManager:
    """翻訳マネージャー（シングルトン）"""
    
    # 翻訳辞書
    TRANSLATIONS = {
        "ja": {
            # アプリケーション
            "app_title": "URDF Kitchen Studio",
            "version": "v0.1.0",
            
            # ホーム画面
            "project": "プロジェクト",
            "new_project": "新規プロジェクトを作成",
            "open_project": "既存プロジェクトを開く",
            "recent_projects": "最近使用したプロジェクト",
            "start_guide": "開始ガイド",
            "welcome": "URDF Kitchen Studio へようこそ！",
            "workflow": "【ワークフロー】",
            "workflow_step1": "1. STL Editor: STL メッシュの座標系定義",
            "workflow_step2": "2. Parts Editor: 接続点・物理パラメータ設定",
            "workflow_step3": "3. Assembly: ロボット構造の組立",
            "workflow_step4": "4. URDF Export: URDF ファイル出力",
            "recommendation": "【推奨】",
            "sample_hint": "はじめてのプロジェクトは \"サンプルプロジェクトを開く\" をお試しください。",
            "sample_project": "サンプルプロジェクト(roborecipe2)を開く",
            
            # ダイアログ
            "select_save_dir": "新規プロジェクトの保存先を選択",
            "select_project_folder": "プロジェクトフォルダを選択",
            "not_valid_project": "このフォルダは URDF Kitchen Studio プロジェクトではありません",
            "error_create_project": "プロジェクト作成失敗",
            "error_open_project": "プロジェクト読み込み失敗",
            "error_project_not_found": "プロジェクトが見つかりません",
            "error_sample_not_found": "サンプルプロジェクトが見つかりません",
            
            # メッセージ
            "home_screen_loaded": "ホーム画面に戻りました",
            "project_created": "プロジェクトを作成しました",
            "project_opened": "プロジェクトを開きました",
            "language_changed": "言語を変更しました",
            
            # ステータス
            "status_ready": "準備完了",
        },
        "en": {
            # Application
            "app_title": "URDF Kitchen Studio",
            "app_subtitle": "SolidWorks-like Mechanical CAD Robot Design Tool",
            "version": "v0.1.0",
            
            # Home Screen
            "project": "Project",
            "new_project": "Create New Project",
            "open_project": "Open Existing Project",
            "recent_projects": "Recent Projects",
            "start_guide": "Getting Started",
            "welcome": "Welcome to URDF Kitchen Studio!",
            "workflow": "[Workflow]",
            "workflow_step1": "1. STL Editor: Define coordinate system of STL meshes",
            "workflow_step2": "2. Parts Editor: Set connection points & physical parameters",
            "workflow_step3": "3. Assembly: Assemble robot structure",
            "workflow_step4": "4. URDF Export: Export URDF file",
            "recommendation": "[Recommendation]",
            "sample_hint": "For your first project, try \"Open Sample Project\".",
            "sample_project": "Open Sample Project (roborecipe2)",
            
            # Dialogs
            "select_save_dir": "Select Save Directory for New Project",
            "select_project_folder": "Select Project Folder",
            "not_valid_project": "This folder is not a URDF Kitchen Studio project",
            "error_create_project": "Failed to create project",
            "error_open_project": "Failed to open project",
            "error_project_not_found": "Project not found",
            "error_sample_not_found": "Sample project not found",
            
            # Messages
            "home_screen_loaded": "Returned to home screen",
            "project_created": "Project created",
            "project_opened": "Project opened",
            "language_changed": "Language changed",
            
            # Status
            "status_ready": "Ready",
        }
    }
    
    _instance = None
    
    def __new__(cls):
        """Singleton パターン"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化"""
        if not hasattr(self, '_initialized'):
            self.current_language = "ja"
            self._initialized = True
    
    @staticmethod
    def instance() -> 'TranslationManager':
        """シングルトンインスタンスを取得"""
        if TranslationManager._instance is None:
            TranslationManager()
        return TranslationManager._instance
    
    def set_language(self, language: str):
        """言語を設定
        
        Args:
            language: "ja" または "en"
        """
        if language in self.TRANSLATIONS:
            self.current_language = language
    
    def get_language(self) -> str:
        """現在の言語を取得"""
        return self.current_language
    
    def translate(self, key: str, default: Optional[str] = None) -> str:
        """翻訳を取得
        
        Args:
            key: 翻訳キー
            default: キーが見つからない場合のデフォルト値
        
        Returns:
            翻訳文字列
        """
        lang = self.current_language
        translation = self.TRANSLATIONS.get(lang, {}).get(key)
        
        if translation is None:
            # フォールバック：キーが見つからない場合は英語を試す
            translation = self.TRANSLATIONS.get("en", {}).get(key)
        
        if translation is None:
            # それでも見つからない場合はデフォルト値またはキーを返す
            translation = default or key
        
        return translation


# グローバルインスタンスへのショートカット
translator = TranslationManager.instance()


def tr(key: str, default: Optional[str] = None) -> str:
    """翻訳関数（簡潔版）
    
    Args:
        key: 翻訳キー
        default: デフォルト値
    
    Returns:
        翻訳文字列
    """
    return translator.translate(key, default)
