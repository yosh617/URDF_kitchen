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
            
            # 共通UI
            "file_operations": "ファイル操作",
            "open_stl": "STLを開く",
            "save_stl": "STLを保存",
            "save_as": "名前を付けて保存",
            "load_stl": "STLを読み込み",
            "load_part_xml": "パーツXMLを読み込み",
            "save_part_xml": "パーツXMLを保存",
            "loaded": "読み込み完了",
            "saved": "保存完了",
            "error": "エラー",
            "success": "成功",
            "ready": "準備完了",
            "name": "名前",
            "type": "タイプ",
            "mass": "質量",
            
            # STL Sourcer
            "reset_view": "ビューをリセット",
            "reset_camera_view": "カメラビューをリセット",
            "wireframe": "ワイヤーフレーム",
            "toggle_wireframe": "ワイヤーフレーム切替",
            "show_axes": "軸を表示",
            "toggle_axes": "軸表示切替",
            "opacity": "透明度",
            "show_grid": "グリッド表示",
            "show_xy_plane": "XY平面",
            "show_xz_plane": "XZ平面",
            "show_yz_plane": "YZ平面",
            "no_stl_loaded": "STL未読込",
            "translation_rotation": "移動・回転",
            "translation": "移動",
            "rotation_deg": "回転（度）",
            "apply": "適用",
            "scale": "スケール",
            "flip_axes": "軸反転",
            "stl_info": "STL情報",
            "vertices": "頂点数",
            "faces": "面数",
            "volume": "体積",
            "surface_area": "表面積",
            "bounds": "バウンディングボックス",
            "reset_all": "すべてリセット",
            "center_origin": "原点に中心化",
            "failed_to_load_stl": "STLの読み込みに失敗しました",
            "error_loading_stl": "STL読み込みエラー",
            "failed_to_save_stl": "STLの保存に失敗しました",
            "error_saving_stl": "STL保存エラー",
            "stl_saved_successfully": "STLファイルを保存しました",
            "unsaved_changes": "未保存の変更",
            "save_before_close": "変更を保存しますか？",
            
            # Parts Editor
            "connection_points": "接続点",
            "physical_properties": "物理パラメータ",
            "inertia_tensor": "慣性テンソル",
            "show_connection_points": "接続点を表示",
            "add_point": "接続点を追加",
            "remove_point": "接続点を削除",
            "point_coordinates": "接続点座標",
            "point_name": "接続点名",
            "update_point": "接続点を更新",
            "properties_info": "2つのパラメータを入力すると、残りが自動計算されます",
            "parameters": "パラメータ",
            "auto_from_stl": "STLから自動",
            "density": "密度",
            "calculate_properties": "パラメータを計算",
            "center_of_mass": "重心",
            "calculate_from_stl": "STLから計算",
            "inertia_info": "慣性テンソルを計算します（精密計算またはバウンディングボックス近似）",
            "calculate_precise": "精密計算",
            "calculate_bbox": "バウンディングボックス近似",
            "load_stl_first": "先にSTLを読み込んでください",
            "point_already_exists": "その名前の接続点は既に存在します",
            "part_xml_loaded": "パーツXMLを読み込みました",
            "part_xml_saved": "パーツXMLを保存しました",
            
            # Assembler
            "robot_name": "ロボット名",
            "create_new_project": "新規プロジェクトを作成",
            "open_existing_project": "既存プロジェクトを開く",
            "save_current_project": "現在のプロジェクトを保存",
            "add_part": "パーツを追加",
            "add_part_node": "パーツノードを追加",
            "add_base_link": "ベースリンクを追加",
            "add_base_link_node": "ベースリンクノードを追加",
            "export_urdf": "URDFをエクスポート",
            "generate_urdf_file": "URDFファイルを生成",
            "3d_preview": "3Dプレビュー",
            "node_properties": "ノードプロパティ",
            "tree_view": "ツリービュー",
            "selected_node": "選択ノード",
            "edit_node": "ノードを編集",
            "massless_decoration": "質量なし装飾",
            "refresh_tree": "ツリーを更新",
            "new_project_created": "新規プロジェクトを作成しました",
            "project_loaded": "プロジェクトを読み込みました",
            "project_saved": "プロジェクトを保存しました",
            "part_node_added": "パーツノードを追加しました",
            "base_link_added": "ベースリンクを追加しました",
            "urdf_exported": "URDFをエクスポートしました",
            "urdf_exported_to": "URDFをエクスポートしました",
            "select_node_first": "先にノードを選択してください",
            
            # ワークフロー
            "send_to_parts_editor": "Parts Editorに送る",
            "send_to_assembler": "Assemblerに送る",
            "warning": "警告",
            "save_changes_before_closing": "変更を保存してから閉じますか？",
            "file_loaded": "ファイルを読み込みました",
            "file_saved": "ファイルを保存しました",
            
            # モードタブ
            "stl_editor": "STL Editor",
            "parts_editor": "Parts Editor",
            "assembler": "Assembler",
            
            # 言語
            "language": "言語",
            "app_subtitle": "URDF生成支援ツール",
            "home": "ホーム",
            "save_before_new": "変更を保存してから新規作成しますか？",
            "no_base_link": "base_linkが見つかりません",
            "refresh_preview": "プレビューを更新",
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
            
            # Common UI
            "file_operations": "File Operations",
            "open_stl": "Open STL",
            "save_stl": "Save STL",
            "save_as": "Save As",
            "load_stl": "Load STL",
            "load_part_xml": "Load Part XML",
            "save_part_xml": "Save Part XML",
            "loaded": "Loaded",
            "saved": "Saved",
            "error": "Error",
            "success": "Success",
            "ready": "Ready",
            "name": "Name",
            "type": "Type",
            "mass": "Mass",
            
            # STL Sourcer
            "reset_view": "Reset View",
            "reset_camera_view": "Reset Camera View",
            "wireframe": "Wireframe",
            "toggle_wireframe": "Toggle Wireframe",
            "show_axes": "Show Axes",
            "toggle_axes": "Toggle Axes",
            "opacity": "Opacity",
            "show_grid": "Show Grid",
            "show_xy_plane": "XY Plane",
            "show_xz_plane": "XZ Plane",
            "show_yz_plane": "YZ Plane",
            "no_stl_loaded": "No STL Loaded",
            "translation_rotation": "Translation & Rotation",
            "translation": "Translation",
            "rotation_deg": "Rotation (degrees)",
            "apply": "Apply",
            "scale": "Scale",
            "flip_axes": "Flip Axes",
            "stl_info": "STL Information",
            "vertices": "Vertices",
            "faces": "Faces",
            "volume": "Volume",
            "surface_area": "Surface Area",
            "bounds": "Bounding Box",
            "reset_all": "Reset All",
            "center_origin": "Center to Origin",
            "failed_to_load_stl": "Failed to load STL",
            "error_loading_stl": "Error loading STL",
            "failed_to_save_stl": "Failed to save STL",
            "error_saving_stl": "Error saving STL",
            "stl_saved_successfully": "STL file saved successfully",
            "unsaved_changes": "Unsaved Changes",
            "save_before_close": "Save changes before closing?",
            
            # Parts Editor
            "connection_points": "Connection Points",
            "physical_properties": "Physical Properties",
            "inertia_tensor": "Inertia Tensor",
            "show_connection_points": "Show Connection Points",
            "add_point": "Add Point",
            "remove_point": "Remove Point",
            "point_coordinates": "Point Coordinates",
            "point_name": "Point Name",
            "update_point": "Update Point",
            "properties_info": "Enter two parameters to auto-calculate the third",
            "parameters": "Parameters",
            "auto_from_stl": "Auto from STL",
            "density": "Density",
            "calculate_properties": "Calculate Properties",
            "center_of_mass": "Center of Mass",
            "calculate_from_stl": "Calculate from STL",
            "inertia_info": "Calculate inertia tensor (precise or bounding box approximation)",
            "calculate_precise": "Precise Calculation",
            "calculate_bbox": "Bounding Box Approximation",
            "load_stl_first": "Please load STL first",
            "point_already_exists": "Point with that name already exists",
            "part_xml_loaded": "Part XML loaded",
            "part_xml_saved": "Part XML saved",
            
            # Assembler
            "robot_name": "Robot Name",
            "create_new_project": "Create New Project",
            "open_existing_project": "Open Existing Project",
            "save_current_project": "Save Current Project",
            "add_part": "Add Part",
            "add_part_node": "Add Part Node",
            "add_base_link": "Add Base Link",
            "add_base_link_node": "Add Base Link Node",
            "export_urdf": "Export URDF",
            "generate_urdf_file": "Generate URDF File",
            "3d_preview": "3D Preview",
            "node_properties": "Node Properties",
            "tree_view": "Tree View",
            "selected_node": "Selected Node",
            "edit_node": "Edit Node",
            "massless_decoration": "Massless Decoration",
            "refresh_tree": "Refresh Tree",
            "new_project_created": "New project created",
            "project_loaded": "Project loaded",
            "project_saved": "Project saved",
            "part_node_added": "Part node added",
            "base_link_added": "Base link added",
            "urdf_exported": "URDF exported",
            "urdf_exported_to": "URDF exported to",
            "select_node_first": "Please select a node first",
            
            # Workflow
            "send_to_parts_editor": "Send to Parts Editor",
            "send_to_assembler": "Send to Assembler",
            "warning": "Warning",
            "save_changes_before_closing": "Save changes before closing?",
            "file_loaded": "File loaded",
            "file_saved": "File saved",
            
            # Mode Tabs
            "stl_editor": "STL Editor",
            "parts_editor": "Parts Editor",
            "assembler": "Assembler",
            
            # Language
            "language": "Language",
            "home": "Home",
            "massless_decoration": "Massless Decoration",
            "refresh_tree": "Refresh Tree",
            "new_project_created": "New project created",
            "project_loaded": "Project loaded",
            "project_saved": "Project saved",
            "part_node_added": "Part node added",
            "base_link_added": "Base link added",
            "urdf_exported": "URDF exported",
            "urdf_exported_to": "URDF exported to",
            "select_node_first": "Please select a node first",
            "save_before_new": "Save changes before creating new project?",
            "no_base_link": "No base_link found",
            "refresh_preview": "Refresh Preview",
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
