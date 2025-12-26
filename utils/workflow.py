"""
URDF Kitchen Studio - ワークフロー管理
STL Sourcer → Parts Editor → Assembler の連携
"""

from pathlib import Path
from typing import Optional, Dict, Any
from PySide6.QtCore import QObject, Signal


class WorkflowManager(QObject):
    """ワークフロー管理クラス
    
    各モード間のデータフローを管理し、自動連携を実現
    """
    
    # シグナル定義
    stl_completed = Signal(str)  # STLファイルパス
    part_completed = Signal(str, str)  # STLファイルパス, XMLファイルパス
    assembly_updated = Signal(dict)  # アセンブリデータ
    
    def __init__(self):
        super().__init__()
        self._current_stl = None
        self._current_xml = None
        self._current_part_name = None
    
    def set_stl_completed(self, stl_path: str):
        """STL Sourcerでの作業完了を通知
        
        Args:
            stl_path: 完成したSTLファイルのパス
        """
        self._current_stl = stl_path
        self._current_part_name = Path(stl_path).stem
        self.stl_completed.emit(stl_path)
    
    def set_part_completed(self, stl_path: str, xml_path: str):
        """Parts Editorでの作業完了を通知
        
        Args:
            stl_path: STLファイルのパス
            xml_path: 生成されたXMLファイルのパス
        """
        self._current_stl = stl_path
        self._current_xml = xml_path
        self._current_part_name = Path(stl_path).stem
        self.part_completed.emit(stl_path, xml_path)
    
    def get_current_stl(self) -> Optional[str]:
        """現在のSTLファイルパスを取得"""
        return self._current_stl
    
    def get_current_xml(self) -> Optional[str]:
        """現在のXMLファイルパスを取得"""
        return self._current_xml
    
    def get_current_part_name(self) -> Optional[str]:
        """現在のパーツ名を取得"""
        return self._current_part_name
    
    def reset(self):
        """ワークフロー状態をリセット"""
        self._current_stl = None
        self._current_xml = None
        self._current_part_name = None


# グローバルインスタンス
workflow_manager = WorkflowManager()
