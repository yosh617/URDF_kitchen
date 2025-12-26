# URDF Kitchen Studio

<img width="600" alt="urdf_kitchen_studio" src="docs/urdf_kitchen_banner202550406.png">

**URDF Kitchen Studio**は、URDFファイルの作成を支援する統合開発環境です。  
3つの専用モード（STL Editor, Parts Editor, Assembler）を切り替えながら、直感的なビジュアル操作でロボットモデルを組み立て、URDFとしてエクスポートできます。

## 主な機能

### 統合3モードワークフロー

1. **STL Editor** - STLメッシュの座標系調整
   - 座標変換（移動・回転・スケール・反転）
   - リアルタイム3Dプレビュー
   - ワイヤーフレーム表示・軸表示

2. **Parts Editor** - パーツ定義と物理パラメータ設定
   - 接続点管理（最大8点）
   - 物理パラメータ自動計算（体積・密度・質量）
   - 重心計算
   - 慣性テンソル計算（精密/バウンディングボックス）

3. **Assembler** - ビジュアルノードグラフでロボット組立
   - ノードグラフベースの直感的な組立
   - リアルタイム3Dプレビュー
   - ツリービュー表示
   - URDF自動生成・エクスポート

### 多言語対応

- 日本語/英語の切り替え対応
- UI全体の即座な言語切り替え

### プロジェクト管理

- プロジェクト単位でのファイル管理
- 自動保存・読み込み
- 最近使用したプロジェクトの履歴

### ワークフロー連携

- STL Editor → Parts Editor → Assembler の自動データ連携
- ワンクリックでモード間のファイル受け渡し

## 必要環境

- **Python**: 3.9, 3.11, 3.12 推奨
  - ⚠️ Python 3.10: 一部ライブラリの互換性問題あり
- **OS**: Windows, macOS, Linux

## インストール

### 1. 依存ライブラリのインストール

```bash
pip install numpy
pip install PySide6
pip install vtk
pip install NodeGraphQt
```

### 2. トラブルシューティング（Python 3.12の場合）

Python 3.12で起動できない場合、NodeGraphQtのインポートエラーが発生することがあります：

```bash
pip install packaging
```

NodeGraphQtの`menu.py`と`viewer.py`を編集：

```python
# 変更前
from distutils.version import LooseVersion

# 変更後
from packaging.version import Version as LooseVersion
```

## 使い方

### アプリケーションの起動

```bash
**python urdf_kitchen_main.py
**```

### 基本ワークフロー

1. **新規プロジェクト作成**
   - ホーム画面から「新規プロジェクトを作成」
   - プロジェクト保存先を選択

2. **STL Editor（オプション）**
   - STLファイルを開く
   - 座標系を調整（必要な場合）
   - 保存して「Parts Editorに送る」

3. **Parts Editor**
   - STLファイルを読み込み
   - 接続点を追加・編集
   - 物理パラメータを設定
   - パーツXMLを保存して「Assemblerに送る」

4. **Assembler**
   - base_linkノードを追加
   - パーツノードを追加
   - ノード間を接続
   - URDFをエクスポート

### サンプルプロジェクト

初めての方は、ホーム画面から「サンプルプロジェクト(roborecipe2)を開く」をお試しください。

## プロジェクト構造

```
robotname_description/
├── project.uks          # プロジェクト設定ファイル
├── meshes/              # STLメッシュファイル
│   └── *.stl
└── urdf/                # URDFおよびパーツXMLファイル
    ├── *.xml            # パーツ定義XMLファイル
    └── *.urdf           # 生成されたURDFファイル
```

## 既知の問題

- **STL Sourcer**: 回転を繰り返すと誤差が蓄積（回転前にリセット推奨）
- ~~**Assembler**: Fixed Jointの回転テスト動作~~ (修正済み 2025/01/03)
- **Massless Decoration**: 親ノードのvisualとして処理（修正済み 2025/01/03)

## チュートリアル

詳細なチュートリアルは以下をご参照ください：

https://qiita.com/Ninagawa123/items/c4643ca92e57c3a45efb

<a href="https://qiita.com/Ninagawa123/items/c4643ca92e57c3a45efb">
  <img src="docs/urdf_kitchen.png" alt="URDF Kitchenロゴ" width="400">
</a>

## 関連リンク

- **URDF Viewer**: https://gkjohnson.github.io/urdf-loaders/javascript/example/bundle/
  - 生成したURDFをブラウザで確認できます

## ライセンス

このプロジェクトはMITライセンスの下で公開されています。

## 謝辞

- VTK: 3D可視化ライブラリ
- NodeGraphQt: ノードグラフUIライブラリ
- PySide6: Qtバインディング

---

**URDF Kitchen Studio** - Make URDF creation as easy as cooking!
