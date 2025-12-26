"""
URDF Kitchen Studio - プロジェクト管理
プロジェクトファイル（project.uks）と
ディレクトリ構造の管理
"""

import json
import os
from pathlib import Path
from typing import Optional, Dict, Any
from datetime import datetime


class URDFProject:
    """URDF Kitchen Studio プロジェクト管理"""
    
    # プロジェクトファイル名
    PROJECT_FILE = "project.uks"
    
    # ディレクトリ構成 (ROS標準形式)
    DIRS = {
        "meshes": "meshes",
        "urdf": "urdf",
    }
    
    def __init__(self, project_path: str):
        """
        プロジェクトを初期化
        
        Args:
            project_path: プロジェクトルートディレクトリパス
        """
        self.project_path = Path(project_path)
        self.project_file = self.project_path / self.PROJECT_FILE
        self.data = {}
        self._load_or_create()
    
    def _load_or_create(self):
        """プロジェクトファイルを読み込む、または新規作成"""
        if self.project_file.exists():
            self._load()
        else:
            self._create_new()
    
    def _create_new(self):
        """新規プロジェクトを作成"""
        # ディレクトリ構造を作成
        for dir_name in self.DIRS.values():
            dir_path = self.project_path / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
        
        # デフォルトデータ
        self.data = {
            "version": "1.0",
            "name": self.project_path.name,
            "created": datetime.now().isoformat(),
            "modified": datetime.now().isoformat(),
            "meshes_dir": str(self.project_path / self.DIRS["meshes"]),
            "urdf_dir": str(self.project_path / self.DIRS["urdf"]),
            "parts": {},  # {"part_name": {"stl_file": "...", "xml_file": "..."}}
            "assembly": {
                "nodes": {},
                "connections": {},
            },
            "dirty_flags": {
                "meshes": False,
                "parts": False,
                "assembly": False,
            }
        }
        self._save()
    
    def _load(self):
        """プロジェクトファイルを読み込む"""
        try:
            with open(self.project_file, 'r', encoding='utf-8') as f:
                self.data = json.load(f)
        except Exception as e:
            print(f"Error loading project file: {e}")
            self.data = {}
    
    def _save(self):
        """プロジェクトファイルを保存"""
        try:
            self.data["modified"] = datetime.now().isoformat()
            with open(self.project_file, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Error saving project file: {e}")
    
    def save(self):
        """プロジェクトを保存"""
        self._save()
    
    def get_meshes_dir(self) -> Path:
        """meshesディレクトリパスを取得 (STLファイル保存先)"""
        return Path(self.data.get("meshes_dir", self.project_path / self.DIRS["meshes"]))
    
    def get_urdf_dir(self) -> Path:
        """urdfディレクトリパスを取得 (URDF、パーツXML保存先)"""
        return Path(self.data.get("urdf_dir", self.project_path / self.DIRS["urdf"]))
    
    # 後方互換性のためのエイリアス
    def get_stl_dir(self) -> Path:
        """STL ディレクトリパスを取得 (meshesディレクトリを返す)"""
        return self.get_meshes_dir()
    
    def get_parts_dir(self) -> Path:
        """パーツディレクトリパスを取得 (urdfディレクトリを返す)"""
        return self.get_urdf_dir()
    
    def get_assembly_dir(self) -> Path:
        """アセンブリディレクトリパスを取得 (urdfディレクトリを返す)"""
        return self.get_urdf_dir()
    
    def get_export_dir(self) -> Path:
        """エクスポートディレクトリパスを取得 (urdfディレクトリを返す)"""
        return self.get_urdf_dir()
    
    def add_part(self, part_name: str, stl_file: str, xml_file: Optional[str] = None):
        """パーツ情報を追加"""
        if "parts" not in self.data:
            self.data["parts"] = {}
        
        self.data["parts"][part_name] = {
            "stl_file": stl_file,
            "xml_file": xml_file or "",
            "created": datetime.now().isoformat(),
        }
        self._save()
    
    def remove_part(self, part_name: str):
        """パーツ情報を削除"""
        if "parts" in self.data and part_name in self.data["parts"]:
            del self.data["parts"][part_name]
            self._save()
    
    def get_parts(self) -> Dict[str, Any]:
        """全パーツ情報を取得"""
        return self.data.get("parts", {})
    
    def set_dirty_flag(self, target: str, dirty: bool = True):
        """更新フラグを設定
        
        Args:
            target: "stl", "parts", "assembly"
            dirty: True = 更新あり, False = 更新なし
        """
        if "dirty_flags" not in self.data:
            self.data["dirty_flags"] = {}
        
        self.data["dirty_flags"][target] = dirty
        self._save()
    
    def get_dirty_flags(self) -> Dict[str, bool]:
        """更新フラグを取得"""
        return self.data.get("dirty_flags", {})
    
    def is_dirty(self, target: str) -> bool:
        """指定ターゲットが更新フラグ立っているか"""
        flags = self.get_dirty_flags()
        return flags.get(target, False)
    
    def get_name(self) -> str:
        """プロジェクト名を取得"""
        return self.data.get("name", "Untitled Project")
    
    def get_created(self) -> str:
        """作成日時を取得"""
        return self.data.get("created", "")
    
    def get_modified(self) -> str:
        """修正日時を取得"""
        return self.data.get("modified", "")
