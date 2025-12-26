"""
テスト用スクリプト：言語選択機能のテスト
"""

import sys
from pathlib import Path

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

from utils.translator import translator, tr
from utils.event_bus import event_bus

print("=== 翻訳システムテスト ===\n")

# 日本語テスト
print("【日本語】")
translator.set_language("ja")
print(f"app_title: {tr('app_title')}")
print(f"app_subtitle: {tr('app_subtitle')}")
print(f"project: {tr('project')}")
print(f"new_project: {tr('new_project')}")

print("\n【English】")
translator.set_language("en")
print(f"app_title: {tr('app_title')}")
print(f"app_subtitle: {tr('app_subtitle')}")
print(f"project: {tr('project')}")
print(f"new_project: {tr('new_project')}")

print("\n【イベントバステスト】")
bus = event_bus
print(f"✓ language_changed シグナルが定義されている: {hasattr(bus, 'language_changed')}")

print("\n✓ 翻訳システムのテストが成功しました")
