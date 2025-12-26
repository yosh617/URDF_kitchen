"""
URDF Kitchen Studio - STL Sourcer UI
STL ファイルの座標変換・編集インターフェース
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtGui import QAction
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import numpy as np
import os
from pathlib import Path

from core.urdf_kitchen_stl_compute import STLProcessor
from utils.event_bus import URDFEventBus
from utils.translator import tr
from utils.workflow import workflow_manager


class STLSourcerWidget(QtWidgets.QWidget):
    """STL Sourcer メインウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = URDFEventBus()
        self.processor = STLProcessor()
        self.current_file = None
        self.has_unsaved_changes = False
        
        # プロジェクト管理
        self.project = None
        self.default_save_dir = None
        
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """UI初期化"""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 左側：3Dビューア（70%）
        self.vtk_widget = self.create_vtk_viewer()
        
        # 右側：コントロールパネル（30%）
        control_panel = self.create_control_panel()
        
        # スプリッター
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.vtk_widget)
        splitter.addWidget(control_panel)
        splitter.setStretchFactor(0, 7)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
    
    def create_vtk_viewer(self) -> QtWidgets.QWidget:
        """VTK 3Dビューア作成"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # VTK Widget
        self.vtk_render_widget = QVTKRenderWindowInteractor(container)
        
        # VTK セットアップ
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.15, 0.15, 0.15)
        
        self.vtk_render_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_render_widget.GetRenderWindow().GetInteractor()
        
        # インタラクタースタイル
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        
        # パラレル投影を設定
        camera = self.renderer.GetActiveCamera()
        camera.SetParallelProjection(True)
        camera.SetParallelScale(5)
        
        # 軸表示
        self.axes_actor = vtk.vtkAxesActor()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.interactor)
        self.axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        self.axes_widget.SetEnabled(1)
        self.axes_widget.InteractiveOn()
        
        # 原点座標軸
        self.origin_axes_actors = []
        self.add_origin_axes()
        
        # 平面アクター
        self.plane_actors = {'xy': None, 'xz': None, 'yz': None}
        
        # STL アクター
        self.stl_actor = None
        
        layout.addWidget(self.vtk_render_widget)
        
        # ツールバー
        toolbar = self.create_viewer_toolbar()
        layout.insertWidget(0, toolbar)
        
        self.interactor.Initialize()
        
        return container
    
    def create_viewer_toolbar(self) -> QtWidgets.QToolBar:
        """ビューアツールバー作成"""
        toolbar = QtWidgets.QToolBar()
        toolbar.setIconSize(QtCore.QSize(20, 20))
        
        # リセットビュー
        reset_action = QAction(tr("reset_view"), self)
        reset_action.setToolTip(tr("reset_camera_view"))
        reset_action.triggered.connect(self.reset_camera)
        toolbar.addAction(reset_action)
        
        toolbar.addSeparator()
        
        # ワイヤーフレーム切り替え
        self.wireframe_action = QAction(tr("wireframe"), self)
        self.wireframe_action.setCheckable(True)
        self.wireframe_action.setToolTip(tr("toggle_wireframe"))
        self.wireframe_action.triggered.connect(self.toggle_wireframe)
        toolbar.addAction(self.wireframe_action)
        
        # 軸表示切り替え
        self.axes_action = QAction(tr("show_axes"), self)
        self.axes_action.setCheckable(True)
        self.axes_action.setChecked(True)
        self.axes_action.setToolTip(tr("toggle_axes"))
        self.axes_action.triggered.connect(self.toggle_axes)
        toolbar.addAction(self.axes_action)
        
        toolbar.addSeparator()
        
        # 透明度スライダー
        toolbar.addWidget(QtWidgets.QLabel(tr("opacity") + ":"))
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setMaximumWidth(100)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        toolbar.addWidget(self.opacity_slider)
        
        toolbar.addSeparator()
        
        # 平面表示
        self.xy_plane_action = QAction("XY", self)
        self.xy_plane_action.setCheckable(True)
        self.xy_plane_action.setToolTip(tr("show_xy_plane"))
        self.xy_plane_action.triggered.connect(lambda: self.toggle_plane('xy'))
        toolbar.addAction(self.xy_plane_action)
        
        self.xz_plane_action = QAction("XZ", self)
        self.xz_plane_action.setCheckable(True)
        self.xz_plane_action.setToolTip(tr("show_xz_plane"))
        self.xz_plane_action.triggered.connect(lambda: self.toggle_plane('xz'))
        toolbar.addAction(self.xz_plane_action)
        
        self.yz_plane_action = QAction("YZ", self)
        self.yz_plane_action.setCheckable(True)
        self.yz_plane_action.setToolTip(tr("show_yz_plane"))
        self.yz_plane_action.triggered.connect(lambda: self.toggle_plane('yz'))
        toolbar.addAction(self.yz_plane_action)
        
        toolbar.addSeparator()
        
        # 情報表示
        self.info_label = QtWidgets.QLabel(tr("no_stl_loaded"))
        toolbar.addWidget(self.info_label)
        
        return toolbar
    
    def create_control_panel(self) -> QtWidgets.QWidget:
        """コントロールパネル作成"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        
        # ファイル操作
        file_group = self.create_file_group()
        layout.addWidget(file_group)
        
        # 座標変換
        transform_group = self.create_transform_group()
        layout.addWidget(transform_group)
        
        # スケール
        scale_group = self.create_scale_group()
        layout.addWidget(scale_group)
        
        # 反転
        flip_group = self.create_flip_group()
        layout.addWidget(flip_group)
        
        # 情報表示
        info_group = self.create_info_group()
        layout.addWidget(info_group)
        
        layout.addStretch()
        
        # アクションボタン
        action_buttons = self.create_action_buttons()
        layout.addWidget(action_buttons)
        
        return panel
    
    def create_file_group(self) -> QtWidgets.QGroupBox:
        """ファイル操作グループ"""
        group = QtWidgets.QGroupBox(tr("file_operations"))
        layout = QtWidgets.QVBoxLayout(group)
        
        # 開く
        open_btn = QtWidgets.QPushButton(tr("open_stl"))
        open_btn.clicked.connect(self.open_stl_file)
        layout.addWidget(open_btn)
        
        # 保存
        save_btn = QtWidgets.QPushButton(tr("save_stl"))
        save_btn.clicked.connect(self.save_stl_file)
        layout.addWidget(save_btn)
        
        # 名前を付けて保存
        save_as_btn = QtWidgets.QPushButton(tr("save_as"))
        save_as_btn.clicked.connect(self.save_stl_as)
        layout.addWidget(save_as_btn)
        
        return group
    
    def create_transform_group(self) -> QtWidgets.QGroupBox:
        """座標変換グループ"""
        group = QtWidgets.QGroupBox(tr("translation_rotation"))
        layout = QtWidgets.QGridLayout(group)
        
        # 移動
        layout.addWidget(QtWidgets.QLabel(tr("translation")), 0, 0, 1, 3)
        
        self.tx_spin = self.create_double_spinbox(-1000, 1000, 0)
        self.ty_spin = self.create_double_spinbox(-1000, 1000, 0)
        self.tz_spin = self.create_double_spinbox(-1000, 1000, 0)
        
        layout.addWidget(QtWidgets.QLabel("X:"), 1, 0)
        layout.addWidget(self.tx_spin, 1, 1)
        layout.addWidget(QtWidgets.QLabel("Y:"), 2, 0)
        layout.addWidget(self.ty_spin, 2, 1)
        layout.addWidget(QtWidgets.QLabel("Z:"), 3, 0)
        layout.addWidget(self.tz_spin, 3, 1)
        
        # 適用ボタン
        apply_trans_btn = QtWidgets.QPushButton(tr("apply"))
        apply_trans_btn.clicked.connect(self.apply_translation)
        layout.addWidget(apply_trans_btn, 1, 2, 3, 1)
        
        # 回転
        layout.addWidget(QtWidgets.QLabel(tr("rotation_deg")), 4, 0, 1, 3)
        
        self.rx_spin = self.create_double_spinbox(-360, 360, 0)
        self.ry_spin = self.create_double_spinbox(-360, 360, 0)
        self.rz_spin = self.create_double_spinbox(-360, 360, 0)
        
        layout.addWidget(QtWidgets.QLabel("RX:"), 5, 0)
        layout.addWidget(self.rx_spin, 5, 1)
        layout.addWidget(QtWidgets.QLabel("RY:"), 6, 0)
        layout.addWidget(self.ry_spin, 6, 1)
        layout.addWidget(QtWidgets.QLabel("RZ:"), 7, 0)
        layout.addWidget(self.rz_spin, 7, 1)
        
        # 適用ボタン
        apply_rot_btn = QtWidgets.QPushButton(tr("apply"))
        apply_rot_btn.clicked.connect(self.apply_rotation)
        layout.addWidget(apply_rot_btn, 5, 2, 3, 1)
        
        return group
    
    def create_scale_group(self) -> QtWidgets.QGroupBox:
        """スケールグループ"""
        group = QtWidgets.QGroupBox(tr("scale"))
        layout = QtWidgets.QHBoxLayout(group)
        
        self.scale_spin = self.create_double_spinbox(0.001, 1000, 1.0, 3)
        layout.addWidget(self.scale_spin)
        
        apply_btn = QtWidgets.QPushButton(tr("apply"))
        apply_btn.clicked.connect(self.apply_scale)
        layout.addWidget(apply_btn)
        
        return group
    
    def create_flip_group(self) -> QtWidgets.QGroupBox:
        """反転グループ"""
        group = QtWidgets.QGroupBox(tr("flip_axes"))
        layout = QtWidgets.QHBoxLayout(group)
        
        flip_x_btn = QtWidgets.QPushButton("Flip X")
        flip_x_btn.clicked.connect(lambda: self.flip_axis('x'))
        layout.addWidget(flip_x_btn)
        
        flip_y_btn = QtWidgets.QPushButton("Flip Y")
        flip_y_btn.clicked.connect(lambda: self.flip_axis('y'))
        layout.addWidget(flip_y_btn)
        
        flip_z_btn = QtWidgets.QPushButton("Flip Z")
        flip_z_btn.clicked.connect(lambda: self.flip_axis('z'))
        layout.addWidget(flip_z_btn)
        
        return group
    
    def create_info_group(self) -> QtWidgets.QGroupBox:
        """情報表示グループ"""
        group = QtWidgets.QGroupBox(tr("stl_info"))
        layout = QtWidgets.QFormLayout(group)
        
        self.vertices_label = QtWidgets.QLabel("-")
        self.faces_label = QtWidgets.QLabel("-")
        self.volume_label = QtWidgets.QLabel("-")
        self.surface_label = QtWidgets.QLabel("-")
        self.bounds_label = QtWidgets.QLabel("-")
        
        layout.addRow(tr("vertices") + ":", self.vertices_label)
        layout.addRow(tr("faces") + ":", self.faces_label)
        layout.addRow(tr("volume") + ":", self.volume_label)
        layout.addRow(tr("surface_area") + ":", self.surface_label)
        layout.addRow(tr("bounds") + ":", self.bounds_label)
        
        return group
    
    def create_action_buttons(self) -> QtWidgets.QWidget:
        """アクションボタン"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # 基本操作
        basic_layout = QtWidgets.QHBoxLayout()
        reset_btn = QtWidgets.QPushButton(tr("reset_all"))
        reset_btn.clicked.connect(self.reset_transforms)
        basic_layout.addWidget(reset_btn)
        
        center_btn = QtWidgets.QPushButton(tr("center_origin"))
        center_btn.clicked.connect(self.center_to_origin)
        basic_layout.addWidget(center_btn)
        layout.addLayout(basic_layout)
        
        # ワークフロー連携ボタン
        workflow_btn = QtWidgets.QPushButton("📤 " + tr("send_to_parts_editor"))
        workflow_btn.setStyleSheet("QPushButton { background-color: #2a5; color: white; font-weight: bold; padding: 8px; }")
        workflow_btn.clicked.connect(self.send_to_parts_editor)
        layout.addWidget(workflow_btn)
        
        return widget
    
    def create_double_spinbox(self, min_val: float, max_val: float, 
                              default: float, decimals: int = 2) -> QtWidgets.QDoubleSpinBox:
        """ダブルスピンボックス作成"""
        spin = QtWidgets.QDoubleSpinBox()
        spin.setRange(min_val, max_val)
        spin.setValue(default)
        spin.setDecimals(decimals)
        spin.setSingleStep(0.1 if decimals > 0 else 1)
        return spin
    
    # ========== イベントハンドラ ==========
    
    def open_stl_file(self):
        """STLファイルを開く"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            tr("open_stl"),
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        
        if file_path:
            self.load_stl(file_path)
    
    def load_stl(self, file_path: str):
        """STLファイルを読み込み"""
        try:
            print(f"Loading STL: {file_path}")
            success = self.processor.load_stl(file_path)
            if success:
                self.current_file = file_path
                self.has_unsaved_changes = False
                print(f"STL loaded successfully, polydata: {self.processor.polydata}")
                self.update_3d_view()
                self.update_info_display()
                part_name = Path(file_path).stem
                self.info_label.setText(f"{tr('loaded')}: {Path(file_path).name}")
                self.event_bus.stl_loaded.emit(file_path, part_name)
            else:
                print("Failed to load STL")
                QtWidgets.QMessageBox.warning(
                    self,
                    tr("error"),
                    tr("failed_to_load_stl")
                )
        except Exception as e:
            print(f"Exception loading STL: {e}")
            import traceback
            traceback.print_exc()
            QtWidgets.QMessageBox.critical(
                self,
                tr("error"),
                f"{tr('error_loading_stl')}: {str(e)}"
            )
    
    def save_stl_file(self):
        """STLファイルを保存"""
        if not self.current_file:
            self.save_stl_as()
            return
        
        self.save_stl(self.current_file)
    
    def save_stl_as(self):
        """名前を付けて保存"""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            tr("save_as"),
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        
        if file_path:
            self.save_stl(file_path)
    
    def save_stl(self, file_path: str):
        """STLファイルを保存"""
        try:
            success = self.processor.save_stl(file_path)
            if success:
                self.current_file = file_path
                self.has_unsaved_changes = False
                self.info_label.setText(f"{tr('saved')}: {Path(file_path).name}")
                
                # プロジェクトに追加
                if self.project and self.default_save_dir:
                    if Path(file_path).parent == self.default_save_dir:
                        self.project.set_dirty_flag('stl', True)
                        self.project.save()
                
                QtWidgets.QMessageBox.information(
                    self,
                    tr("success"),
                    tr("stl_saved_successfully")
                )
            else:
                QtWidgets.QMessageBox.warning(
                    self,
                    tr("error"),
                    tr("failed_to_save_stl")
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                tr("error"),
                f"{tr('error_saving_stl')}: {str(e)}"
            )
    
    def apply_translation(self):
        """移動を適用"""
        if self.processor.polydata is None:
            return
        
        tx = self.tx_spin.value()
        ty = self.ty_spin.value()
        tz = self.tz_spin.value()
        
        self.processor.apply_translation(tx, ty, tz)
        self.has_unsaved_changes = True
        self.update_3d_view()
        self.update_info_display()
        
        # リセット
        self.tx_spin.setValue(0)
        self.ty_spin.setValue(0)
        self.tz_spin.setValue(0)
    
    def apply_rotation(self):
        """回転を適用"""
        if self.processor.polydata is None:
            return
        
        rx = self.rx_spin.value()
        ry = self.ry_spin.value()
        rz = self.rz_spin.value()
        
        self.processor.apply_rotation(rx, ry, rz)
        self.has_unsaved_changes = True
        self.update_3d_view()
        self.update_info_display()
        
        # リセット
        self.rx_spin.setValue(0)
        self.ry_spin.setValue(0)
        self.rz_spin.setValue(0)
    
    def apply_scale(self):
        """スケールを適用"""
        if self.processor.polydata is None:
            return
        
        scale = self.scale_spin.value()
        self.processor.apply_scale(scale, scale, scale)
        self.has_unsaved_changes = True
        self.update_3d_view()
        self.update_info_display()
        
        # リセット
        self.scale_spin.setValue(1.0)
    
    def flip_axis(self, axis: str):
        """軸反転"""
        if self.processor.polydata is None:
            return
        
        self.processor.flip_axis(axis)
        self.has_unsaved_changes = True
        self.update_3d_view()
        self.update_info_display()
    
    def reset_transforms(self):
        """全変換をリセット"""
        if self.current_file:
            self.load_stl(self.current_file)
    
    def center_to_origin(self):
        """原点に中心を移動"""
        if self.processor.polydata is None:
            return
        
        center = self.processor.get_center()
        self.processor.apply_translation(-center[0], -center[1], -center[2])
        self.has_unsaved_changes = True
        self.update_3d_view()
        self.update_info_display()
    
    def reset_camera(self):
        """カメラをリセット"""
        self.renderer.ResetCamera()
        self.fit_camera_to_model()
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def toggle_wireframe(self, checked: bool):
        """ワイヤーフレーム切り替え"""
        if self.stl_actor:
            if checked:
                self.stl_actor.GetProperty().SetRepresentationToWireframe()
            else:
                self.stl_actor.GetProperty().SetRepresentationToSurface()
            self.vtk_render_widget.GetRenderWindow().Render()
    
    def add_origin_axes(self):
        """原点に大きな座標軸を追加"""
        # 既存の軸アクターを削除
        for actor in self.origin_axes_actors:
            self.renderer.RemoveActor(actor)
        self.origin_axes_actors.clear()
        
        origin = [0, 0, 0]
        
        # モデルのサイズに応じて軸の長さを調整
        if self.processor.polydata is not None:
            bounds = self.processor.polydata.GetBounds()
            max_dim = max(
                bounds[1] - bounds[0],  # X範囲
                bounds[3] - bounds[2],  # Y範囲
                bounds[5] - bounds[4]   # Z範囲
            )
            axis_length = max_dim * 2.0  # モデルの2倍の長さ
            print(f"Model bounds: {bounds}, max_dim: {max_dim}, axis_length: {axis_length}")
        else:
            axis_length = 1.0  # デフォルト
        
        colors = [(1, 0, 0), (0, 1, 0), (0, 0, 1)]  # X:赤、Y:緑、Z:青
        
        for i, color in enumerate(colors):
            for direction in [1, -1]:
                line_source = vtk.vtkLineSource()
                line_source.SetPoint1(*origin)
                end_point = [0, 0, 0]
                end_point[i] = axis_length * direction
                line_source.SetPoint2(*end_point)
                
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(line_source.GetOutputPort())
                
                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                actor.GetProperty().SetColor(color)
                actor.GetProperty().SetLineWidth(3)
                
                self.renderer.AddActor(actor)
                self.origin_axes_actors.append(actor)
        
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def toggle_axes(self, checked: bool):
        """軸表示切り替え"""
        self.axes_widget.SetEnabled(1 if checked else 0)
        # 原点座標軸も切り替え
        for actor in self.origin_axes_actors:
            actor.SetVisibility(1 if checked else 0)
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def update_opacity(self, value: int):
        """透明度更新"""
        if self.stl_actor:
            opacity = value / 100.0
            self.stl_actor.GetProperty().SetOpacity(opacity)
            self.vtk_render_widget.GetRenderWindow().Render()
    
    def toggle_plane(self, plane: str):
        """平面視点切り替え（平面は表示しない）"""
        # カメラ視点をその平面の正面に設定
        camera = self.renderer.GetActiveCamera()
        
        if plane == 'xy':
            # XY平面: Z軸から見る
            camera.SetPosition(0, 0, 1)
            camera.SetFocalPoint(0, 0, 0)
            camera.SetViewUp(0, 1, 0)
        elif plane == 'xz':
            # XZ平面: Y軸から見る
            camera.SetPosition(0, 1, 0)
            camera.SetFocalPoint(0, 0, 0)
            camera.SetViewUp(0, 0, 1)
        else:  # yz
            # YZ平面: X軸から見る
            camera.SetPosition(1, 0, 0)
            camera.SetFocalPoint(0, 0, 0)
            camera.SetViewUp(0, 0, 1)
        
        self.renderer.ResetCamera()
        self.fit_camera_to_model()
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def fit_camera_to_model(self):
        """STLモデルが画面いっぱいに表示されるようにカメラを調整"""
        if self.processor.polydata is None:
            return
        
        camera = self.renderer.GetActiveCamera()
        bounds = self.processor.polydata.GetBounds()
        
        # モデルの中心を計算
        center = [
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2
        ]
        
        # モデルの大きさを計算
        size = max(
            bounds[1] - bounds[0],
            bounds[3] - bounds[2],
            bounds[5] - bounds[4]
        )
        
        # 20%の余裕を追加
        size *= 1.4
        
        # 現在のカメラの方向ベクトルを保持
        current_position = np.array(camera.GetPosition())
        focal_point = np.array(center)
        direction = current_position - focal_point
        
        # 方向ベクトルを正規化
        if np.linalg.norm(direction) > 0:
            direction = direction / np.linalg.norm(direction)
        else:
            direction = np.array([1, 0, 0])  # デフォルト方向
        
        # 新しい位置を計算
        new_position = focal_point + direction * size
        
        # カメラの位置を更新
        camera.SetPosition(new_position)
        camera.SetFocalPoint(*center)
        
        # ビューポートのアスペクト比を取得
        viewport = self.renderer.GetViewport()
        aspect_ratio = (viewport[2] - viewport[0]) / (viewport[3] - viewport[1])
        
        # パラレル投影の場合、パラレルスケールを設定
        if camera.GetParallelProjection():
            if aspect_ratio > 1:  # 横長の画面
                camera.SetParallelScale(size / 2)
            else:  # 縦長の画面
                camera.SetParallelScale(size / (2 * aspect_ratio))
        else:
            # パースペクティブ投影の場合、視野角を調整
            angle = 30  # 視野角（度）
            camera.SetViewAngle(angle)
        
        self.renderer.ResetCameraClippingRange()
    
    def update_3d_view(self):
        """3Dビューを更新"""
        if self.processor.polydata is None:
            print("update_3d_view: polydata is None")
            return
        
        print(f"update_3d_view: polydata exists, updating view")
        
        # 既存アクターを削除
        if self.stl_actor:
            self.renderer.RemoveActor(self.stl_actor)
        
        # 新しいアクターを作成
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.processor.polydata)
        
        self.stl_actor = vtk.vtkActor()
        self.stl_actor.SetMapper(mapper)
        self.stl_actor.GetProperty().SetColor(0.8, 0.8, 0.9)
        
        # 透明度スライダーの値を適用
        opacity = self.opacity_slider.value() / 100.0
        print(f"Setting opacity to: {opacity} (slider value: {self.opacity_slider.value()})")
        self.stl_actor.GetProperty().SetOpacity(opacity)
        
        # ワイヤーフレーム状態を維持
        if self.wireframe_action.isChecked():
            self.stl_actor.GetProperty().SetRepresentationToWireframe()
        
        self.renderer.AddActor(self.stl_actor)
        print(f"Actor added to renderer")
        
        # 原点座標軸が存在しない場合は再追加
        if not self.origin_axes_actors:
            self.add_origin_axes()
        
        self.renderer.ResetCamera()
        self.fit_camera_to_model()
        self.vtk_render_widget.GetRenderWindow().Render()
        print("View updated and rendered")
    
    def update_info_display(self):
        """情報表示を更新"""
        if self.processor.polydata is None:
            return
        
        polydata = self.processor.polydata
        
        # 頂点数
        num_points = polydata.GetNumberOfPoints()
        self.vertices_label.setText(f"{num_points:,}")
        
        # 面数
        num_cells = polydata.GetNumberOfCells()
        self.faces_label.setText(f"{num_cells:,}")
        
        # 体積
        volume = self.processor.get_volume()
        self.volume_label.setText(f"{volume:.6f} m³")
        
        # 表面積
        surface = self.processor.get_surface_area()
        self.surface_label.setText(f"{surface:.6f} m²")
        
        # バウンディングボックス
        bounds = self.processor.get_bounds()
        bounds_text = f"[{bounds[0]:.2f}, {bounds[1]:.2f}]\n"
        bounds_text += f"[{bounds[2]:.2f}, {bounds[3]:.2f}]\n"
        bounds_text += f"[{bounds[4]:.2f}, {bounds[5]:.2f}]"
        self.bounds_label.setText(bounds_text)
    
    def connect_signals(self):
        """シグナル接続"""
        self.event_bus.language_changed.connect(self.update_translations)
    
    def update_translations(self):
        """翻訳を更新"""
        # 必要に応じて UI テキストを再設定
        pass
    
    def closeEvent(self, event):
        """クローズイベント"""
        if self.has_unsaved_changes:
            reply = QtWidgets.QMessageBox.question(
                self,
                tr("unsaved_changes"),
                tr("save_before_close"),
                QtWidgets.QMessageBox.Save | 
                QtWidgets.QMessageBox.Discard | 
                QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_stl_file()
                if hasattr(self, 'vtk_render_widget'):
                    self.vtk_render_widget.Finalize()
                event.accept()
            elif reply == QtWidgets.QMessageBox.Discard:
                if hasattr(self, 'vtk_render_widget'):
                    self.vtk_render_widget.Finalize()
                event.accept()
            else:
                event.ignore()
        else:
            if hasattr(self, 'vtk_render_widget'):
                self.vtk_render_widget.Finalize()
            event.accept()
    
    def reset(self):
        """モードをリセット"""
        self.current_file = None
        self.has_unsaved_changes = False
        self.processor = STLProcessor()
        
        # 3Dビューをクリア
        if self.stl_actor:
            self.renderer.RemoveActor(self.stl_actor)
            self.stl_actor = None
        if hasattr(self, 'vtk_render_widget'):
            self.vtk_render_widget.GetRenderWindow().Render()
        
        # UIをリセット
        if hasattr(self, 'info_label'):
            self.info_label.clear()
    
    def send_to_parts_editor(self):
        """現在のSTLをParts Editorに送る"""
        if not self.current_file:
            QtWidgets.QMessageBox.warning(
                self,
                tr("warning"),
                "STLファイルを保存してからParts Editorに送信してください"
            )
            return
        
        if self.has_unsaved_changes:
            reply = QtWidgets.QMessageBox.question(
                self,
                tr("unsaved_changes"),
                "変更を保存してからParts Editorに送信しますか？",
                QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No
            )
            
            if reply == QtWidgets.QMessageBox.Yes:
                self.save_stl_file()
        
        # ワークフローマネージャーに通知
        workflow_manager.set_stl_completed(self.current_file)
        
        QtWidgets.QMessageBox.information(
            self,
            tr("success"),
            f"STLファイルをParts Editorに送信しました:\n{Path(self.current_file).name}"
        )
