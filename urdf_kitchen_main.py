"""
URDF Kitchen Studio - メインエントリポイント
アプリケーションの起動・ウィンドウ管理・モード切り替え
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
    QStatusBar, QTabWidget, QLabel, QMenuBar, QMenu
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont, QAction

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

from ui.theme import URDFKitchenTheme
from ui.home_screen import HomeScreenWidget
from ui.sourcer_ui import STLSourcerWidget
from ui.editor_ui import PartsEditorWidget
from ui.assembler_ui import AssemblerWidget
from models.project import URDFProject
from utils.event_bus import event_bus
from utils.translator import tr, TranslationManager
from utils.workflow import workflow_manager


class URDFKitchenStudio(QMainWindow):
    """URDF Kitchen Studio メインウィンドウ
    
    ホーム画面から各モード（STL Editor, Parts Editor, Assembly）へ遷移
    """
    
    def __init__(self):
        """メインウィンドウの初期化"""
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        
        # ウィンドウサイズを画面に合わせて調整
        self.setMinimumSize(900, 700)
        self.resize(1400, 850)
        
        self.translator = TranslationManager.instance()
        self.current_project: URDFProject = None
        
        # ===== UI 構築 =====
        self._setup_ui()
        
        # ===== シグナル接続 =====
        self._connect_signals()
        
        # ===== テーマ適用 =====
        URDFKitchenTheme.apply_dark_theme(self)
        
        # ===== ホーム画面を表示 =====
        self.show_home_screen()
    
    def _setup_ui(self):
        """UI を構築"""
        # ===== セントラルウィジェット =====
        central_widget = QWidget()
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # ===== スタック（画面遷移） =====
        self.stacked = QStackedWidget()
        
        # ホーム画面
        self.home_screen = HomeScreenWidget()
        self.stacked.addWidget(self.home_screen)
        
        # ワークスペース（タブ化された各モード）
        self.workspace_widget = self._create_workspace()
        self.stacked.addWidget(self.workspace_widget)
        
        layout.addWidget(self.stacked)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # ===== メニューバー =====
        self._create_menu_bar()
        
        # ===== ステータスバー =====
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(tr("status_ready"))
    
    def _create_workspace(self) -> QWidget:
        """ワークスペース作成（3つのモードをタブで切り替え）"""
        workspace = QWidget()
        layout = QVBoxLayout(workspace)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # タブウィジェット
        self.mode_tabs = QTabWidget()
        self.mode_tabs.setTabPosition(QTabWidget.North)
        
        # 各モードのウィジェット
        self.stl_sourcer = STLSourcerWidget()
        self.parts_editor = PartsEditorWidget()
        self.assembler = AssemblerWidget()
        
        # タブに追加
        self.mode_tabs.addTab(self.stl_sourcer, "STL Editor")
        self.mode_tabs.addTab(self.parts_editor, "Parts Editor")
        self.mode_tabs.addTab(self.assembler, "Assembly")
        
        layout.addWidget(self.mode_tabs)
        
        return workspace
    
    def _create_menu_bar(self):
        """メニューバー作成"""
        menubar = self.menuBar()
        
        # ファイルメニュー
        file_menu = menubar.addMenu(tr("project"))
        
        home_action = QAction(tr("home_screen_loaded"), self)
        home_action.triggered.connect(self.show_home_screen)
        file_menu.addAction(home_action)
        
        file_menu.addSeparator()
        
        exit_action = QAction("Exit", self)
        exit_action.triggered.connect(self.close)
        file_menu.addAction(exit_action)
        
        # 言語メニュー
        # lang_menu = menubar.addMenu("🌐 Language")
        # ja_action = QAction("🇯🇵 日本語", self)
        # ja_action.triggered.connect(lambda: self._change_language("ja"))
        # lang_menu.addAction(ja_action)
        # en_action = QAction("🇺🇸 English", self)
        # en_action.triggered.connect(lambda: self._change_language("en"))
        # lang_menu.addAction(en_action)
    
    
    def show_home_screen(self):
        """ホーム画面を表示"""
        self.stacked.setCurrentIndex(0)
        self.status_bar.showMessage(tr("home_screen_loaded"))
    
    def _change_language(self, lang: str):
        """言語を変更"""
        self.translator.set_language(lang)
        event_bus.language_changed.emit(lang)
        self.status_bar.showMessage(tr("language_changed"))
    
    def _connect_signals(self):
        """シグナルを接続"""
        # ホーム画面
        self.home_screen.project_selected.connect(self._on_project_selected)
        
        # イベントバス
        event_bus.status_message.connect(self._on_status_message)
        event_bus.error_message.connect(self._on_error_message)
        event_bus.project_closed.connect(self._on_project_closed)
        event_bus.language_changed.connect(self._update_translations)        
        # ワークフロー管理
        workflow_manager.stl_completed.connect(self._on_stl_completed)
        workflow_manager.part_completed.connect(self._on_part_completed)    
    def _on_project_selected(self, project_path: str):
        """プロジェクトが選択された"""
        try:
            # プロジェクトを読み込む
            self.current_project = URDFProject(project_path)
            
            # 各モードにプロジェクト情報を設定
            self._configure_modes_with_project()
            
            # ワークスペースに切り替え
            self.stacked.setCurrentIndex(1)
            
            # ステータス更新
            self.status_bar.showMessage(
                f"{tr('project_opened')}: {self.current_project.data.get('name', 'Untitled')}",
                5000
            )
            
            # タイトル更新
            self.setWindowTitle(f"URDF Kitchen Studio - {self.current_project.data.get('name', 'Untitled')}")
            
        except Exception as e:
            event_bus.error_message.emit(f"Failed to open project: {e}")
            print(f"Error loading project: {e}")
    
    def _configure_modes_with_project(self):
        """各モードにプロジェクト設定を適用"""
        if not self.current_project:
            return
        
        # STL Sourcerに設定
        self.stl_sourcer.project = self.current_project
        self.stl_sourcer.default_save_dir = self.current_project.get_stl_dir()
        
        # Parts Editorに設定
        self.parts_editor.project = self.current_project
        self.parts_editor.stl_dir = self.current_project.get_stl_dir()
        self.parts_editor.parts_dir = self.current_project.get_parts_dir()
        
        # Assemblerに設定
        self.assembler.project = self.current_project
        self.assembler.parts_dir = self.current_project.get_parts_dir()
        self.assembler.export_dir = self.current_project.get_export_dir()
        
        # プロジェクトデータを各モードに反映
        self._load_project_data_to_modes()
    
    def _load_project_data_to_modes(self):
        """プロジェクトデータを各モードに読み込む"""
        if not self.current_project:
            return
        
        try:
            # Parts Editorにパーツリスト反映
            parts = self.current_project.get_parts()
            if parts and hasattr(self.parts_editor, 'load_parts_list'):
                self.parts_editor.load_parts_list(parts)
            
            # Assemblerにアセンブリデータ反映
            assembly_data = self.current_project.data.get('assembly', {})
            if assembly_data and hasattr(self.assembler, 'load_assembly_data'):
                self.assembler.load_assembly_data(assembly_data)
        except Exception as e:
            event_bus.error_message.emit(f"{tr('error_open_project')}: {e}")
    
    def _show_workspace(self, project_path: str):
        """ワークスペースを表示
        
        Args:
            project_path: プロジェクトパス
        """
        # TODO: Step 5-7 で実装
        # ここでは、プロジェクトを開いたことを示すための簡易実装
        workspace = QWidget()
        layout = QVBoxLayout()
        
        label = QLabel(
            f"プロジェクト: {Path(project_path).name}\n\n"
            "STL Editor / Parts Editor / Assembly\n"
            "（Step 5-7 で実装予定）"
        )
        label.setFont(QFont("", 14))
        label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(label)
        
        workspace.setLayout(layout)
        self.workspace_widget = workspace
        self.stacked.removeWidget(self.stacked.widget(1))
        self.stacked.addWidget(workspace)
        self.stacked.setCurrentWidget(workspace)
    
    def _on_project_closed(self):
        """プロジェクトが閉じられた"""
        # プロジェクトデータを保存
        if self.current_project:
            self._save_all_modes_data()
            self.current_project.save()
        
        # プロジェクトクリア
        self.current_project = None
        
        # 各モードをリセット
        if hasattr(self.stl_sourcer, 'reset'):
            self.stl_sourcer.reset()
        if hasattr(self.parts_editor, 'reset'):
            self.parts_editor.reset()
        if hasattr(self.assembler, 'reset'):
            self.assembler.reset()
        
        # ホーム画面に戻る
        self.show_home_screen()
        self.setWindowTitle("URDF Kitchen Studio")
    
    def _save_all_modes_data(self):
        """全モードのデータをプロジェクトに保存"""
        if not self.current_project:
            return
        
        # Parts Editorのパーツデータを保存
        if hasattr(self.parts_editor, 'get_current_parts_data'):
            parts_data = self.parts_editor.get_current_parts_data()
            if parts_data:
                for part_name, part_info in parts_data.items():
                    self.current_project.add_part(
                        part_name,
                        part_info.get('stl_file', ''),
                        part_info.get('xml_file', '')
                    )
        
        # Assemblerのアセンブリデータを保存
        if hasattr(self.assembler, 'get_assembly_data'):
            assembly_data = self.assembler.get_assembly_data()
            if assembly_data:
                self.current_project.data['assembly'] = assembly_data
    
    def show_home_screen(self):
        """ホーム画面を表示"""
        self.stacked.setCurrentWidget(self.home_screen)
        self.setWindowTitle(f"{tr('app_title')} - {tr('project')}")
        event_bus.status_message.emit(tr("home_screen_loaded"), 3000)
    
    def _on_status_message(self, message: str, duration: int):
        """ステータスメッセージを表示
        
        Args:
            message: メッセージ
            duration: 表示時間（ミリ秒）
        """
        self.status_bar.showMessage(message, duration)
    
    def _on_error_message(self, message: str):
        """エラーメッセージを表示
        
        Args:
            message: エラーメッセージ
        """
        self.status_bar.showMessage(f"エラー: {message}", 5000)
        print(f"ERROR: {message}")
    
    def _update_translations(self):
        """言語変更時に呼ばれる翻訳更新"""
        # タイトル更新
        if self.current_project:
            project_name = self.current_project.data.get('name', 'Untitled')
            self.setWindowTitle(f"URDF Kitchen Studio - {project_name}")
        else:
            self.setWindowTitle("URDF Kitchen Studio")
        
        # ステータスバー更新
        if self.stacked.currentIndex() == 0:
            self.status_bar.showMessage(tr("status_ready"))
        
        # タブのタイトル更新
        self.mode_tabs.setTabText(0, tr("stl_editor"))
        self.mode_tabs.setTabText(1, tr("parts_editor"))
        self.mode_tabs.setTabText(2, tr("assembler"))
    
    def _change_language(self, lang_code: str):
        """言語を変更"""
        trans_mgr = TranslationManager.instance()
        trans_mgr.set_language(lang_code)
        event_bus.language_changed.emit(lang_code)
        self._update_translations()
        self.status_bar.showMessage(
            f"{tr('language')}: {'日本語' if lang_code == 'ja' else 'English'}",
            3000
        )
    
    def closeEvent(self, event):
        """アプリケーション終了時のクリーンアップ"""
        # 各ウィジェットのクリーンアップを呼び出す
        if hasattr(self, 'stl_sourcer'):
            self.stl_sourcer.close()
        if hasattr(self, 'parts_editor'):
            self.parts_editor.close()
        if hasattr(self, 'assembler'):
            self.assembler.close()
        event.accept()
    
    def _on_stl_completed(self, stl_path: str):
        """現在のSTLがParts Editorで使えるように自動読み込み"""
        # Parts Editorタブに切り替え
        self.mode_tabs.setCurrentIndex(1)
        
        # STLを自動読み込み
        if hasattr(self.parts_editor, 'load_stl_file'):
            self.parts_editor.load_stl_file(stl_path)
        
        self.status_bar.showMessage(
            f"STLファイルをParts Editorに読み込みました: {Path(stl_path).name}",
            5000
        )
    
    def _on_part_completed(self, stl_path: str, xml_path: str):
        """パーツがAssemblerで使えるように自動登録"""
        # Assemblerタブに切り替え
        self.mode_tabs.setCurrentIndex(2)
        
        # パーツをプロジェクトに追加
        if self.current_project:
            part_name = Path(stl_path).stem
            self.current_project.add_part(part_name, stl_path, xml_path)
        
        self.status_bar.showMessage(
            f"パーツをAssemblerに追加しました: {Path(stl_path).stem}",
            5000
        )


def main():
    """メイン関数"""
    # Qt フォント警告を抑制
    import os
    os.environ['QT_LOGGING_RULES'] = 'qt.qpa.fonts=false'
    
    app = QApplication(sys.argv)
    app.setApplicationName("URDF Kitchen Studio")
    app.setApplicationVersion("0.1.0")
    
    # デフォルトフォントを設定してフォントエラーを回避
    from PySide6.QtGui import QFont
    font = QFont("Yu Gothic UI", 9)  # Windowsの標準フォント
    app.setFont(font)
    
    # メインウィンドウを作成・表示
    window = URDFKitchenStudio()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
