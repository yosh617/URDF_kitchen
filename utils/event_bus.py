"""
URDF Kitchen Studio - イベントバス
タブ間・モード間のシグナル通信を管理
既存 urdf_kitchen.py の FileEventBus を拡張
"""

from PySide6.QtCore import QObject, Signal
from typing import Any


class URDFEventBus(QObject):
    """イベントバス：全アプリケーション内のシグナル通信を統一管理"""
    
    # ===== ファイル・プロジェクト関連 =====
    project_created = Signal(str)  # プロジェクトパス
    project_opened = Signal(str)   # プロジェクトパス
    project_saved = Signal(str)    # プロジェクトパス
    project_closed = Signal()
    
    # ===== STL 関連 =====
    stl_loaded = Signal(str, str)  # (ファイルパス, パーツ名)
    stl_transformed = Signal(str)  # パーツ名
    stl_saved = Signal(str, str)   # (パーツ名, ファイルパス)
    
    # ===== パーツ関連 =====
    part_created = Signal(str)     # パーツ名
    part_modified = Signal(str)    # パーツ名
    part_deleted = Signal(str)     # パーツ名
    part_xml_saved = Signal(str)   # パーツ名
    
    # ===== アセンブリ・ノード関連 =====
    node_added = Signal(str, str)           # (ノードID, ノード型)
    node_removed = Signal(str)              # ノードID
    node_selected = Signal(str)             # ノードID
    node_properties_changed = Signal(str)   # ノードID
    connection_created = Signal(str, str)   # (ノード1, ノード2)
    connection_removed = Signal(str, str)   # (ノード1, ノード2)
    
    # ===== URDF 関連 =====
    urdf_generated = Signal(str)   # URDF ファイルパス
    urdf_exported = Signal(str)    # エクスポートパス
    
    # ===== UI・モード関連 =====
    mode_changed = Signal(str)     # モード名（"stl_editor", "parts_editor", "assembly"）
    status_message = Signal(str, int)      # (メッセージ, 継続時間ms)
    error_message = Signal(str)    # エラーメッセージ
    warning_message = Signal(str)  # 警告メッセージ
    
    # ===== 同期・更新 =====
    rebuild_required = Signal()    # 再構築が必要
    data_sync_requested = Signal(str)  # 同期対象のタイプ
    
    # ===== 設定 =====
    language_changed = Signal(str)  # 言語が変更された ("ja" / "en")
    
    # Singleton インスタンス
    _instance = None
    
    def __new__(cls):
        """Singleton パターン"""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self):
        """初期化（既に初期化済みなら実行しない）"""
        if not hasattr(self, '_initialized'):
            super().__init__()
            self._initialized = True
    
    @staticmethod
    def instance() -> 'URDFEventBus':
        """シングルトンインスタンスを取得"""
        if URDFEventBus._instance is None:
            URDFEventBus()
        return URDFEventBus._instance


# グローバルインスタンスへのショートカット
event_bus = URDFEventBus.instance()
