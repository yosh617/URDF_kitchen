"""
Step 5-7 のテストスクリプト
UI実装の動作確認（手動テスト用）
"""

import os
import sys

# プロジェクトのルートディレクトリをパスに追加
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

print("=" * 60)
print("Step 5-7: UI実装テスト")
print("=" * 60)

print("\n[INFO] アプリケーションを起動します...")
print("[INFO] 以下の機能を手動でテストしてください:\n")

print("【Step 5: STL Sourcer UI】")
print("  1. STLファイルを開く")
print("  2. 座標変換（移動・回転・スケール）を適用")
print("  3. 軸反転を試す")
print("  4. STLファイルを保存\n")

print("【Step 6: Parts Editor UI】")
print("  1. STLを読み込み")
print("  2. 接続点を追加・編集")
print("  3. 物理パラメータ（体積・密度・質量）を計算")
print("  4. 重心を計算")
print("  5. 慣性テンソルを計算")
print("  6. パーツXMLを保存\n")

print("【Step 7: Assembler UI】")
print("  1. パーツノードを追加")
print("  2. base_linkを追加")
print("  3. ノード間を接続")
print("  4. 各ノードにSTL/XMLを割り当て")
print("  5. 3Dプレビューを確認")
print("  6. URDFをエクスポート")
print("  7. プロジェクトを保存・読み込み\n")

print("=" * 60)
print("アプリケーション起動中...")
print("=" * 60 + "\n")

# メインアプリケーションを起動
from urdf_kitchen_main import main

if __name__ == "__main__":
    main()
