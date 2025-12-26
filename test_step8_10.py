"""
URDF Kitchen Studio - Step 8-10 統合テスト
プロジェクト管理、ワークフロー統合、UI改善の確認
"""

import sys
from pathlib import Path

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

def test_step_8_10():
    """Step 8-10 のテスト"""
    print("=" * 60)
    print("Step 8-10: プロジェクト管理・ワークフロー統合テスト")
    print("=" * 60)
    print()
    
    # インポートテスト
    print("[1/5] インポート確認...")
    try:
        from urdf_kitchen_main import URDFKitchenStudio
        from models.project import URDFProject
        from utils.workflow import workflow_manager
        from utils.translator import tr, TranslationManager
        print("✓ 全モジュールのインポート成功")
    except Exception as e:
        print(f"✗ インポートエラー: {e}")
        return False
    
    # プロジェクトモデルテスト
    print("\n[2/5] プロジェクトモデル確認...")
    try:
        import tempfile
        import shutil
        
        # 一時ディレクトリでプロジェクト作成
        with tempfile.TemporaryDirectory() as tmpdir:
            test_project_path = Path(tmpdir) / "test_project"
            test_project_path.mkdir()
            
            project = URDFProject(str(test_project_path))
            
            # 基本機能確認
            assert project.project_file.exists(), "プロジェクトファイルが作成されていない"
            assert project.get_stl_dir().exists(), "STLディレクトリが作成されていない"
            assert project.get_parts_dir().exists(), "パーツディレクトリが作成されていない"
            
            # パーツ追加テスト
            project.add_part("test_part", "test.stl", "test.xml")
            parts = project.get_parts()
            assert "test_part" in parts, "パーツが追加されていない"
            
            print("✓ プロジェクトモデル正常動作")
    except Exception as e:
        print(f"✗ プロジェクトモデルエラー: {e}")
        return False
    
    # ワークフローマネージャーテスト
    print("\n[3/5] ワークフローマネージャー確認...")
    try:
        # シグナル接続テスト
        signal_received = []
        
        def on_stl_completed(path):
            signal_received.append(('stl', path))
        
        def on_part_completed(stl_path, xml_path):
            signal_received.append(('part', stl_path, xml_path))
        
        workflow_manager.stl_completed.connect(on_stl_completed)
        workflow_manager.part_completed.connect(on_part_completed)
        
        # テスト実行
        workflow_manager.set_stl_completed("test.stl")
        workflow_manager.set_part_completed("test.stl", "test.xml")
        
        assert len(signal_received) == 2, "シグナルが正しく発火していない"
        assert signal_received[0][0] == 'stl', "STL完了シグナルが発火していない"
        assert signal_received[1][0] == 'part', "パーツ完了シグナルが発火していない"
        
        print("✓ ワークフローマネージャー正常動作")
    except Exception as e:
        print(f"✗ ワークフローマネージャーエラー: {e}")
        return False
    
    # 翻訳システムテスト
    print("\n[4/5] 翻訳システム確認...")
    try:
        # インスタンス取得
        trans_mgr = TranslationManager.instance()
        
        # 日本語
        trans_mgr.set_language("ja")
        assert tr("app_title") == "URDF Kitchen Studio", "日本語翻訳エラー"
        assert tr("send_to_parts_editor") == "Parts Editorに送る", "新規翻訳キーエラー"
        
        # 英語
        trans_mgr.set_language("en")
        assert tr("app_title") == "URDF Kitchen Studio", "英語翻訳エラー"
        assert tr("send_to_parts_editor") == "Send to Parts Editor", "新規翻訳キー（英語）エラー"
        
        # 日本語に戻す
        trans_mgr.set_language("ja")
        
        print("✓ 翻訳システム正常動作")
    except Exception as e:
        print(f"✗ 翻訳システムエラー: {e}")
        return False
    
    # GUIアプリケーション起動テスト
    print("\n[5/5] GUIアプリケーション起動確認...")
    print("[INFO] GUIウィンドウが開きます。動作確認後、ウィンドウを閉じてください。")
    print()
    print("【確認項目】")
    print("  □ ホーム画面が正しく表示される")
    print("  □ 言語選択（日本語/英語）が機能する")
    print("  □ 新規プロジェクト作成ボタンが表示される")
    print("  □ サンプルプロジェクトボタンが表示される")
    print("  □ プロジェクトを開くと3つのタブ（STL Editor, Parts Editor, Assembler）に切り替わる")
    print("  □ 各タブにワークフロー連携ボタン（📤 〜に送る）が表示される")
    print("  □ メニューバーに言語切り替えメニューがある")
    print()
    print("=" * 60)
    
    try:
        from PySide6.QtWidgets import QApplication
        
        app = QApplication(sys.argv)
        app.setApplicationName("URDF Kitchen Studio - Test")
        
        # メインウィンドウ作成
        window = URDFKitchenStudio()
        window.show()
        
        # アプリケーション実行
        sys.exit(app.exec())
        
    except Exception as e:
        print(f"✗ GUI起動エラー: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    test_step_8_10()
