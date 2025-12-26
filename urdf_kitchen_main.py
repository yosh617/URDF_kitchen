"""
URDF Kitchen Studio - メインエントリポイント
アプリケーションの起動・ウィンドウ管理・モード切り替え
"""

import sys
from pathlib import Path

from PySide6.QtWidgets import (
    QApplication, QMainWindow, QStackedWidget, QVBoxLayout, QWidget,
    QStatusBar, QTabWidget, QLabel
)
from PySide6.QtCore import Qt, QTimer
from PySide6.QtGui import QFont

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

from ui.theme import URDFKitchenTheme
from ui.home_screen import HomeScreenWidget
from models.project import URDFProject
from utils.event_bus import event_bus
from utils.translator import tr


class URDFKitchenStudio(QMainWindow):
    """URDF Kitchen Studio メインウィンドウ
    
    ホーム画面から各モード（STL Editor, Parts Editor, Assembly）へ遷移
    """
    
    def __init__(self):
        """メインウィンドウの初期化"""
        super().__init__()
        self.setWindowTitle(tr("app_title"))
        self.setGeometry(100, 100, 1400, 900)
        
        self.current_project: URDFProject = None
        
        # ===== UI 構築 =====
        self._setup_ui()
        
        # ===== シグナル接続 =====
        self._connect_signals()
        
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
        
        # ワークスペース（プロジェクト開放時）
        # TODO: Step 5-7 で実装（STL Editor, Parts Editor, Assembly）
        self.workspace_widget = QWidget()  # プレースホルダー
        self.stacked.addWidget(self.workspace_widget)
        
        layout.addWidget(self.stacked)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)
        
        # ===== ステータスバー =====
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self.statusBar.showMessage(tr("status_ready"))
        
        # テーマ適用
        URDFKitchenTheme.apply_dark_theme(QApplication.instance())
    
    def _connect_signals(self):
        """シグナルを接続"""
        # ホーム画面
        self.home_screen.project_selected.connect(self._on_project_selected)
        
        # イベントバス
        event_bus.status_message.connect(self._on_status_message)
        event_bus.error_message.connect(self._on_error_message)
        event_bus.project_closed.connect(self._on_project_closed)
    
    def _on_project_selected(self, project_path: str):
        """プロジェクトが選択された"""
        try:
            # プロジェクトを読み込む
            self.current_project = URDFProject(project_path)
            
            # ワークスペースに切り替え
            # TODO: Step 5-7 で実装
            self._show_workspace(project_path)
            
            event_bus.status_message.emit(
                f"プロジェクトを開きました: {self.current_project.get_name()}",
                5000
            )
        except Exception as e:
            print(f"Error loading project: {e}")
            event_bus.error_message.emit(f"プロジェクト読み込み失敗: {e}")
    
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
        self.current_project = None
        self.show_home_screen()
    
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
        self.statusBar.showMessage(message, duration)
    
    def _on_error_message(self, message: str):
        """エラーメッセージを表示
        
        Args:
            message: エラーメッセージ
        """
        self.statusBar.showMessage(f"エラー: {message}", 5000)
        print(f"ERROR: {message}")


def main():
    """メイン関数"""
    # Qt フォント警告を無視
    import os
    os.environ['QT_QPA_FONTDIR'] = ''
    
    app = QApplication(sys.argv)
    app.setApplicationName("URDF Kitchen Studio")
    app.setApplicationVersion("0.1.0")
    
    # メインウィンドウを作成・表示
    window = URDFKitchenStudio()
    window.show()
    
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
