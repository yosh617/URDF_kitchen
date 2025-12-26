"""
URDF Kitchen Studio - ホーム画面
プロジェクト選択・新規作成のランディングUI
"""

import json
import sys
from pathlib import Path
from typing import Optional

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel,
    QListWidget, QListWidgetItem, QFileDialog, QSplitter,
    QFrame, QSpacerItem, QSizePolicy, QComboBox
)
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtGui import QFont, QIcon

# パス設定（ワークスペース内のモジュールを読み込み）
sys.path.insert(0, str(Path(__file__).parent.parent))

from models.project import URDFProject
from utils.event_bus import event_bus
from utils.translator import translator, tr, TranslationManager


class HomeScreenWidget(QWidget):
    """ホーム画面UI
    
    Signals:
        project_selected: プロジェクトが選択されたとき (project_path: str)
    """
    
    project_selected = Signal(str)  # プロジェクトパス
    
    def __init__(self):
        """ホーム画面の初期化"""
        super().__init__()
        self.recent_projects_file = Path.home() / ".urdf_kitchen" / "recent_projects.json"
        self.recent_projects = self._load_recent_projects()
        self._setup_ui()
        self._load_recent_projects_list()
    
    def _setup_ui(self):
        """UI を構築"""
        self.setWindowTitle(tr("app_title"))
        self.setMinimumSize(900, 600)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # ===== 言語選択ボタン（右上） =====
        header_layout = QHBoxLayout()
        header_layout.addStretch()
        
        self.language_label = QLabel("Language:")
        self.language_combo = QComboBox()
        self.language_combo.addItem("日本語 (Japanese)", "ja")
        self.language_combo.addItem("English", "en")
        
        # 現在の言語を選択
        current_lang = translator.get_language()
        for i in range(self.language_combo.count()):
            if self.language_combo.itemData(i) == current_lang:
                self.language_combo.setCurrentIndex(i)
                break
        
        self.language_combo.currentIndexChanged.connect(self._on_language_changed)
        
        header_layout.addWidget(self.language_label)
        header_layout.addWidget(self.language_combo)
        main_layout.addLayout(header_layout)
        
        # ===== タイトル =====
        self.title_label = QLabel(tr("app_title"))
        title_font = QFont()
        title_font.setPointSize(28)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.title_label)
        
        self.subtitle_label = QLabel(tr("app_subtitle"))
        subtitle_font = QFont()
        subtitle_font.setPointSize(12)
        self.subtitle_label.setFont(subtitle_font)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        main_layout.addWidget(self.subtitle_label)
        
        main_layout.addSpacing(30)
        
        # ===== コンテンツエリア：左右分割 =====
        content_splitter = QSplitter(Qt.Orientation.Horizontal)
        content_splitter.setChildrenCollapsible(False)
        
        # ----- 左パネル:プロジェクト操作 -----
        left_panel = QFrame()
        left_layout = QVBoxLayout()
        left_layout.setSpacing(10)
        
        self.operations_label = QLabel(tr("project"))
        operations_font = QFont()
        operations_font.setPointSize(14)
        operations_font.setBold(True)
        self.operations_label.setFont(operations_font)
        left_layout.addWidget(self.operations_label)
        
        # 新規作成ボタン
        self.new_project_btn = QPushButton(tr("new_project"))
        self.new_project_btn.setMinimumHeight(50)
        self.new_project_btn.setFont(QFont("", 11))
        self.new_project_btn.clicked.connect(self._on_new_project)
        left_layout.addWidget(self.new_project_btn)
        
        # 既存プロジェクト読み込みボタン
        self.open_project_btn = QPushButton(tr("open_project"))
        self.open_project_btn.setMinimumHeight(50)
        self.open_project_btn.setFont(QFont("", 11))
        self.open_project_btn.clicked.connect(self._on_open_project)
        left_layout.addWidget(self.open_project_btn)
        
        left_layout.addSpacing(20)
        
        self.recent_label = QLabel(tr("recent_projects"))
        recent_font = QFont()
        recent_font.setPointSize(12)
        recent_font.setBold(True)
        self.recent_label.setFont(recent_font)
        left_layout.addWidget(self.recent_label)
        
        # 最近使用したプロジェクトリスト
        self.recent_list = QListWidget()
        self.recent_list.itemClicked.connect(self._on_recent_project_selected)
        left_layout.addWidget(self.recent_list)
        
        left_panel.setLayout(left_layout)
        
        # ----- 右パネル：情報表示 -----
        right_panel = QFrame()
        right_layout = QVBoxLayout()
        right_layout.setSpacing(10)
        
        self.info_label = QLabel(tr("start_guide"))
        info_font = QFont()
        info_font.setPointSize(14)
        info_font.setBold(True)
        self.info_label.setFont(info_font)
        right_layout.addWidget(self.info_label)
        
        guide_text_content = (
            f"{tr('welcome')}\n\n"
            f"{tr('workflow')}\n"
            f"{tr('workflow_step1')}\n"
            f"{tr('workflow_step2')}\n"
            f"{tr('workflow_step3')}\n"
            f"{tr('workflow_step4')}\n\n"
            f"{tr('recommendation')}\n"
            f"{tr('sample_hint')}"
        )
        
        self.guide_text = QLabel(guide_text_content)
        self.guide_text.setFont(QFont("", 10))
        self.guide_text.setWordWrap(True)
        self.guide_text.setAlignment(Qt.AlignmentFlag.AlignTop | Qt.AlignmentFlag.AlignLeft)
        right_layout.addWidget(self.guide_text)
        
        # サンプルプロジェクト読み込みボタン
        self.sample_project_btn = QPushButton(tr("sample_project"))
        self.sample_project_btn.setMinimumHeight(40)
        self.sample_project_btn.setFont(QFont("", 10))
        self.sample_project_btn.clicked.connect(self._on_open_sample_project)
        right_layout.addWidget(self.sample_project_btn)
        
        right_layout.addStretch()
        right_panel.setLayout(right_layout)
        
        # Splitter に追加
        content_splitter.addWidget(left_panel)
        content_splitter.addWidget(right_panel)
        content_splitter.setSizes([400, 400])
        
        main_layout.addWidget(content_splitter)
        
        # ===== フッター =====
        footer_layout = QHBoxLayout()
        footer_layout.addStretch()
        
        self.version_label = QLabel(f"URDF Kitchen Studio {tr('version')}")
        self.version_label.setFont(QFont("", 9))
        footer_layout.addWidget(self.version_label)
        
        main_layout.addLayout(footer_layout)
        
        self.setLayout(main_layout)
        
        # 翻訳マネージャーのシグナル接続
        event_bus.language_changed.connect(self._on_language_changed_signal)
    
    def _load_recent_projects(self) -> list:
        """最近使用したプロジェクト一覧を読み込む"""
        try:
            if self.recent_projects_file.exists():
                with open(self.recent_projects_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    return data.get("recent", [])
        except:
            pass
        return []
    
    def _save_recent_projects(self):
        """最近使用したプロジェクト一覧を保存"""
        try:
            self.recent_projects_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.recent_projects_file, 'w', encoding='utf-8') as f:
                json.dump({"recent": self.recent_projects[:10]}, f, indent=2, ensure_ascii=False)
        except:
            pass
    
    def _load_recent_projects_list(self):
        """最近使用したプロジェクトリストを表目に反映"""
        self.recent_list.clear()
        for project_path in self.recent_projects:
            if Path(project_path).exists():
                project_name = Path(project_path).name
                item = QListWidgetItem(f"{project_name}\n{project_path}")
                item.setData(Qt.ItemDataRole.UserRole, project_path)
                self.recent_list.addItem(item)
    
    def _add_recent_project(self, project_path: str):
        """プロジェクトを最近使用済みに追加"""
        # 既に存在する場合は削除（重複を避ける）
        if project_path in self.recent_projects:
            self.recent_projects.remove(project_path)
        
        # リストの先頭に追加
        self.recent_projects.insert(0, project_path)
        
        # 上位10項目のみ保持
        self.recent_projects = self.recent_projects[:10]
        
        self._save_recent_projects()
        self._load_recent_projects_list()
    
    def _on_new_project(self):
        """新規プロジェクト作成"""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setWindowTitle(tr("select_save_dir"))
        
        if dialog.exec():
            project_path = dialog.selectedFiles()[0]
            project_path = str(Path(project_path))
            
            # プロジェクトを作成
            try:
                project = URDFProject(project_path)
                project.save()
                
                self._add_recent_project(project_path)
                event_bus.project_created.emit(project_path)
                event_bus.status_message.emit(tr("project_created"), 3000)
                self.project_selected.emit(project_path)
            except Exception as e:
                print(f"Error creating project: {e}")
                event_bus.error_message.emit(f"{tr('error_create_project')}: {e}")
    
    def _on_open_project(self):
        """既存プロジェクトを開く"""
        dialog = QFileDialog()
        dialog.setFileMode(QFileDialog.FileMode.Directory)
        dialog.setOption(QFileDialog.Option.ShowDirsOnly, True)
        dialog.setWindowTitle(tr("select_project_folder"))
        
        if dialog.exec():
            project_path = dialog.selectedFiles()[0]
            project_path = str(Path(project_path))
            
            # プロジェクトファイルの存在確認
            project_file = Path(project_path) / URDFProject.PROJECT_FILE
            if not project_file.exists():
                event_bus.error_message.emit(tr("not_valid_project"))
                return
            
            try:
                self._add_recent_project(project_path)
                event_bus.project_opened.emit(project_path)
                event_bus.status_message.emit(tr("project_opened"), 3000)
                self.project_selected.emit(project_path)
            except Exception as e:
                print(f"Error opening project: {e}")
                event_bus.error_message.emit(f"{tr('error_open_project')}: {e}")
    
    def _on_open_sample_project(self):
        """サンプルプロジェクト(roborecipe2)を開く"""
        # ワークスペース内の roborecipe2_description を探す
        sample_path = Path(__file__).parent.parent / "roborecipe2_description"
        
        if not sample_path.exists():
            event_bus.error_message.emit(tr("error_sample_not_found"))
            return
        
        project_path = str(sample_path)
        
        try:
            self._add_recent_project(project_path)
            event_bus.project_opened.emit(project_path)
            event_bus.status_message.emit(tr("project_opened"), 3000)
            self.project_selected.emit(project_path)
        except Exception as e:
            print(f"Error opening sample project: {e}")
            event_bus.error_message.emit(f"{tr('error_open_project')}: {e}")
    
    def _on_recent_project_selected(self, item: QListWidgetItem):
        """最近使用したプロジェクトが選択された"""
        project_path = item.data(Qt.ItemDataRole.UserRole)
        
        if not Path(project_path).exists():
            event_bus.error_message.emit(tr("error_project_not_found"))
            return
        
        try:
            self._add_recent_project(project_path)
            event_bus.project_opened.emit(project_path)
            event_bus.status_message.emit(tr("project_opened"), 3000)
            self.project_selected.emit(project_path)
        except Exception as e:
            print(f"Error opening project: {e}")
            event_bus.error_message.emit(f"{tr('error_open_project')}: {e}")
    
    def _on_language_changed(self, index: int):
        """言語が変更された"""
        lang_code = self.language_combo.itemData(index)
        trans_mgr = TranslationManager.instance()
        if lang_code and lang_code != trans_mgr.get_language():
            trans_mgr.set_language(lang_code)
            event_bus.language_changed.emit(lang_code)
            event_bus.status_message.emit(tr("language_changed"), 3000)
            
            # UIを更新
            self._update_ui_translations()
    
    def _on_language_changed_signal(self, language: str):
        """言語変更シグナルを受信（現在は未実装、今後の複数パネル対応用）"""
        pass
    
    def _update_ui_translations(self):
        """UI要素の翻訳を更新"""
        # タイトル
        self.title_label.setText(tr("app_title"))
        self.subtitle_label.setText(tr("app_subtitle"))
        
        # 左パネル
        self.operations_label.setText(tr("project"))
        self.new_project_btn.setText(tr("new_project"))
        self.open_project_btn.setText(tr("open_project"))
        self.recent_label.setText(tr("recent_projects"))
        
        # 右パネル
        self.info_label.setText(tr("start_guide"))
        guide_text_content = (
            f"{tr('welcome')}\n\n"
            f"{tr('workflow')}\n"
            f"{tr('workflow_step1')}\n"
            f"{tr('workflow_step2')}\n"
            f"{tr('workflow_step3')}\n"
            f"{tr('workflow_step4')}\n\n"
            f"{tr('recommendation')}\n"
            f"{tr('sample_hint')}"
        )
        self.guide_text.setText(guide_text_content)
        self.sample_project_btn.setText(tr("sample_project"))
        self.version_label.setText(f"URDF Kitchen Studio {tr('version')}")
