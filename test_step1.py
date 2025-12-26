"""
テスト用スクリプト：Step 1 の動作確認
"""

import sys
from pathlib import Path

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

from models.project import URDFProject
from utils.event_bus import event_bus
from ui.theme import URDFKitchenTheme

print("✓ ui.theme インポート成功")
print("✓ utils.event_bus インポート成功")
print("✓ models.project インポート成功")

# イベントバステスト
print("\n=== イベントバステスト ===")
bus = event_bus
print(f"✓ イベントバス取得: {type(bus)}")

# テストプロジェクト作成
test_project_path = Path(__file__).parent / "test_project"
test_project_path.mkdir(exist_ok=True)

print(f"\n=== プロジェクト管理テスト ===")
project = URDFProject(str(test_project_path))
print(f"✓ プロジェクト作成: {project.get_name()}")
print(f"✓ STL ディレクトリ: {project.get_stl_dir()}")
print(f"✓ パーツディレクトリ: {project.get_parts_dir()}")

# テーマテスト
print(f"\n=== テーマテスト ===")
print(f"✓ 背景色: {URDFKitchenTheme.BG_MAIN}")
print(f"✓ テキスト色: {URDFKitchenTheme.TEXT_PRIMARY}")

print("\n=== すべてのテストが成功しました ===")
print("Step 1 の基盤は問題なく動作しています")
