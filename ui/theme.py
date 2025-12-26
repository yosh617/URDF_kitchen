"""
URDF Kitchen Studio - ダークテーマ定義
既存 urdf_kitchen.py のテーマを統一化・一元管理
"""

from PySide6.QtGui import QColor, QFont
from PySide6.QtWidgets import QApplication


class URDFKitchenTheme:
    """ダークテーマ設定（SolidWorks風CAD）"""
    
    # 背景色
    BG_MAIN = "#2b2b2b"           # メイン背景
    BG_DARK = "#1e1e1e"           # より暗い背景
    BG_LIGHT = "#3d3d3d"          # より明るい背景
    
    # テキスト色
    TEXT_PRIMARY = "#f0f0f0"       # メインテキスト
    TEXT_SECONDARY = "#a0a0a0"     # セカンダリテキスト
    TEXT_DISABLED = "#606060"      # 無効テキスト
    
    # ハイライト・アクセント
    ACCENT_BLUE = "#0078d4"        # Windows系ブルー
    ACCENT_ORANGE = "#ff9800"      # 選択時オレンジ
    ACCENT_GREEN = "#4caf50"       # 成功時グリーン
    ACCENT_RED = "#f44336"         # エラー時レッド
    
    # ボーダー
    BORDER_COLOR = "#505050"
    BORDER_LIGHT = "#707070"
    
    # パネル
    PANEL_BG = "#323232"
    PANEL_BORDER = "#464646"
    
    @staticmethod
    def apply_dark_theme(app: QApplication):
        """アプリケーション全体にダークテーマを適用"""
        stylesheet = """
        QMainWindow {
            background-color: """ + URDFKitchenTheme.BG_MAIN + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
        }
        
        QWidget {
            background-color: """ + URDFKitchenTheme.BG_MAIN + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
        }
        
        QMenuBar {
            background-color: """ + URDFKitchenTheme.PANEL_BG + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border-bottom: 1px solid """ + URDFKitchenTheme.PANEL_BORDER + """;
        }
        
        QMenuBar::item:selected {
            background-color: """ + URDFKitchenTheme.BG_LIGHT + """;
        }
        
        QMenu {
            background-color: """ + URDFKitchenTheme.PANEL_BG + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border: 1px solid """ + URDFKitchenTheme.PANEL_BORDER + """;
        }
        
        QMenu::item:selected {
            background-color: """ + URDFKitchenTheme.ACCENT_BLUE + """;
        }
        
        QTabWidget::pane {
            border: 1px solid """ + URDFKitchenTheme.PANEL_BORDER + """;
        }
        
        QTabBar::tab {
            background-color: """ + URDFKitchenTheme.PANEL_BG + """;
            color: """ + URDFKitchenTheme.TEXT_SECONDARY + """;
            padding: 6px 20px;
            border: 1px solid """ + URDFKitchenTheme.PANEL_BORDER + """;
            border-bottom: none;
        }
        
        QTabBar::tab:selected {
            background-color: """ + URDFKitchenTheme.BG_MAIN + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border-bottom: 2px solid """ + URDFKitchenTheme.ACCENT_BLUE + """;
        }
        
        QDockWidget {
            background-color: """ + URDFKitchenTheme.BG_MAIN + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border: 1px solid """ + URDFKitchenTheme.PANEL_BORDER + """;
        }
        
        QDockWidget::title {
            background-color: """ + URDFKitchenTheme.PANEL_BG + """;
            padding: 5px;
        }
        
        QPushButton {
            background-color: """ + URDFKitchenTheme.PANEL_BG + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border: 1px solid """ + URDFKitchenTheme.BORDER_COLOR + """;
            padding: 6px 12px;
            border-radius: 3px;
        }
        
        QPushButton:hover {
            background-color: """ + URDFKitchenTheme.BG_LIGHT + """;
        }
        
        QPushButton:pressed {
            background-color: """ + URDFKitchenTheme.ACCENT_BLUE + """;
        }
        
        QLineEdit, QTextEdit, QPlainTextEdit {
            background-color: """ + URDFKitchenTheme.BG_DARK + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border: 1px solid """ + URDFKitchenTheme.BORDER_COLOR + """;
            padding: 4px;
            border-radius: 2px;
        }
        
        QLineEdit:focus, QTextEdit:focus, QPlainTextEdit:focus {
            border: 1px solid """ + URDFKitchenTheme.ACCENT_BLUE + """;
        }
        
        QComboBox {
            background-color: """ + URDFKitchenTheme.BG_DARK + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border: 1px solid """ + URDFKitchenTheme.BORDER_COLOR + """;
            padding: 4px;
        }
        
        QComboBox::drop-down {
            border: none;
        }
        
        QComboBox QAbstractItemView {
            background-color: """ + URDFKitchenTheme.PANEL_BG + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            selection-background-color: """ + URDFKitchenTheme.ACCENT_BLUE + """;
        }
        
        QTreeWidget, QListWidget, QTableWidget {
            background-color: """ + URDFKitchenTheme.BG_DARK + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border: 1px solid """ + URDFKitchenTheme.BORDER_COLOR + """;
            gridline-color: """ + URDFKitchenTheme.BORDER_COLOR + """;
        }
        
        QTreeWidget::item:selected, QListWidget::item:selected, QTableWidget::item:selected {
            background-color: """ + URDFKitchenTheme.ACCENT_BLUE + """;
        }
        
        QScrollBar:vertical {
            background-color: """ + URDFKitchenTheme.BG_DARK + """;
            width: 12px;
            border: none;
        }
        
        QScrollBar::handle:vertical {
            background-color: """ + URDFKitchenTheme.BORDER_LIGHT + """;
            min-height: 20px;
            border-radius: 6px;
        }
        
        QScrollBar::handle:vertical:hover {
            background-color: """ + URDFKitchenTheme.ACCENT_BLUE + """;
        }
        
        QStatusBar {
            background-color: """ + URDFKitchenTheme.PANEL_BG + """;
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border-top: 1px solid """ + URDFKitchenTheme.PANEL_BORDER + """;
        }
        
        QLabel {
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
        }
        
        QGroupBox {
            color: """ + URDFKitchenTheme.TEXT_PRIMARY + """;
            border: 1px solid """ + URDFKitchenTheme.BORDER_COLOR + """;
            border-radius: 4px;
            margin-top: 8px;
            padding-top: 8px;
        }
        
        QGroupBox::title {
            subcontrol-origin: margin;
            subcontrol-position: top left;
            padding: 0 4px;
        }
        """
        app.setStyleSheet(stylesheet)
