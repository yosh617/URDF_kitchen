"""
URDF Kitchen Studio - Parts Editor UI
パーツ定義（接続点、物理パラメータ、慣性テンソル）インターフェース
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtGui import QAction
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import os
import numpy as np
from pathlib import Path
from typing import Dict, List, Optional, Any

from core.urdf_kitchen_stl_compute import STLProcessor
from core.urdf_kitchen_compute import PartsCalculator, XMLGenerator
from utils.event_bus import URDFEventBus
from utils.translator import tr
from utils.workflow import workflow_manager


class ConnectionPoint:
    """接続点データ"""
    def __init__(self, name: str, position: List[float], color: tuple = (1, 0, 0)):
        self.name = name
        self.position = position  # [x, y, z]
        self.color = color
        self.actor = None


class PartsEditorWidget(QtWidgets.QWidget):
    """Parts Editor メインウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = URDFEventBus()
        self.stl_processor = STLProcessor()
        self.calculator = PartsCalculator()
        self.xml_generator = XMLGenerator()
        
        self.current_stl_file = None
        self.current_xml_file = None
        self.connection_points: Dict[str, ConnectionPoint] = {}
        self.has_unsaved_changes = False
        
        # プロジェクト管理
        self.project = None
        self.stl_dir = None
        self.parts_dir = None
        self.parts_list = {}  # {part_name: {stl_file, xml_file}}
        
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """UI初期化"""
        layout = QtWidgets.QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # 左側：3Dビューア（65%）
        self.vtk_widget = self.create_vtk_viewer()
        
        # 右側：パラメータパネル（35%）
        params_panel = self.create_params_panel()
        
        # スプリッター
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        splitter.addWidget(self.vtk_widget)
        splitter.addWidget(params_panel)
        splitter.setStretchFactor(0, 65)
        splitter.setStretchFactor(1, 35)
        
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
        
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        
        # パラレル投影を設定
        camera = self.renderer.GetActiveCamera()
        camera.SetParallelProjection(True)
        camera.SetParallelScale(5)
        
        # 軸
        self.axes_widget = self.create_axes_widget()
        
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
    
    def create_axes_widget(self):
        """軸ウィジェット作成"""
        axes_actor = vtk.vtkAxesActor()
        axes_widget = vtk.vtkOrientationMarkerWidget()
        axes_widget.SetOrientationMarker(axes_actor)
        axes_widget.SetInteractor(self.interactor)
        axes_widget.SetViewport(0.0, 0.0, 0.2, 0.2)
        axes_widget.SetEnabled(1)
        axes_widget.InteractiveOn()
        return axes_widget
    
    def add_origin_axes(self):
        """原点に大きな座標軸を追加"""
        # 既存の軸アクターを削除
        for actor in self.origin_axes_actors:
            self.renderer.RemoveActor(actor)
        self.origin_axes_actors.clear()
        
        origin = [0, 0, 0]
        
        # モデルのサイズに応じて軸の長さを調整
        if self.stl_processor.polydata is not None:
            bounds = self.stl_processor.polydata.GetBounds()
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
        """平面表示切り替え"""
        if self.plane_actors[plane]:
            # 既存の平面を削除
            self.renderer.RemoveActor(self.plane_actors[plane])
            self.plane_actors[plane] = None
        else:
            # 新しい平面を作成
            plane_source = vtk.vtkPlaneSource()
            plane_source.SetXResolution(10)
            plane_source.SetYResolution(10)
            
            size = 200
            if plane == 'xy':
                plane_source.SetOrigin(-size, -size, 0)
                plane_source.SetPoint1(size, -size, 0)
                plane_source.SetPoint2(-size, size, 0)
                color = (0.3, 0.3, 0.5)
            elif plane == 'xz':
                plane_source.SetOrigin(-size, 0, -size)
                plane_source.SetPoint1(size, 0, -size)
                plane_source.SetPoint2(-size, 0, size)
                color = (0.3, 0.5, 0.3)
            else:  # yz
                plane_source.SetOrigin(0, -size, -size)
                plane_source.SetPoint1(0, size, -size)
                plane_source.SetPoint2(0, -size, size)
                color = (0.5, 0.3, 0.3)
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(plane_source.GetOutputPort())
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(color)
            actor.GetProperty().SetOpacity(0.2)
            
            self.renderer.AddActor(actor)
            self.plane_actors[plane] = actor
            
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
        
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def create_viewer_toolbar(self) -> QtWidgets.QToolBar:
        """ビューアツールバー"""
        toolbar = QtWidgets.QToolBar()
        toolbar.setIconSize(QtCore.QSize(20, 20))
        
        # リセットビュー
        reset_action = QAction(tr("reset_view"), self)
        reset_action.triggered.connect(self.reset_camera)
        toolbar.addAction(reset_action)
        
        toolbar.addSeparator()
        
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
        
        # 接続点表示切り替え
        self.show_points_action = QAction(tr("show_connection_points"), self)
        self.show_points_action.setCheckable(True)
        self.show_points_action.setChecked(True)
        self.show_points_action.triggered.connect(self.toggle_connection_points)
        toolbar.addAction(self.show_points_action)
        
        toolbar.addSeparator()
        
        # 情報
        self.info_label = QtWidgets.QLabel(tr("no_stl_loaded"))
        toolbar.addWidget(self.info_label)
        
        return toolbar
    
    def create_params_panel(self) -> QtWidgets.QWidget:
        """パラメータパネル"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        
        # ファイル操作
        file_group = self.create_file_group()
        layout.addWidget(file_group)
        
        # タブウィジェット
        tabs = QtWidgets.QTabWidget()
        tabs.addTab(self.create_connection_points_tab(), tr("connection_points"))
        tabs.addTab(self.create_properties_tab(), tr("physical_properties"))
        tabs.addTab(self.create_inertia_tab(), tr("inertia_tensor"))
        layout.addWidget(tabs)
        
        layout.addStretch()
        
        # 保存ボタン
        save_btn = QtWidgets.QPushButton(tr("save_part_xml"))
        save_btn.clicked.connect(self.save_part_xml)
        save_btn.setStyleSheet("QPushButton { font-weight: bold; padding: 10px; }")
        layout.addWidget(save_btn)
        
        return panel
    
    def create_file_group(self) -> QtWidgets.QGroupBox:
        """ファイル操作グループ"""
        group = QtWidgets.QGroupBox(tr("file_operations"))
        layout = QtWidgets.QVBoxLayout(group)
        
        # STL読み込み
        load_stl_btn = QtWidgets.QPushButton(tr("load_stl"))
        load_stl_btn.clicked.connect(self.load_stl)
        layout.addWidget(load_stl_btn)
        
        # XML読み込み
        load_xml_btn = QtWidgets.QPushButton(tr("load_part_xml"))
        load_xml_btn.clicked.connect(self.load_part_xml)
        layout.addWidget(load_xml_btn)
        
        return group
    
    def create_connection_points_tab(self) -> QtWidgets.QWidget:
        """接続点タブ"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # リスト
        self.points_list = QtWidgets.QListWidget()
        self.points_list.itemSelectionChanged.connect(self.on_point_selected)
        layout.addWidget(self.points_list)
        
        # 追加・削除ボタン
        btn_layout = QtWidgets.QHBoxLayout()
        add_btn = QtWidgets.QPushButton(tr("add_point"))
        add_btn.clicked.connect(self.add_connection_point)
        btn_layout.addWidget(add_btn)
        
        remove_btn = QtWidgets.QPushButton(tr("remove_point"))
        remove_btn.clicked.connect(self.remove_connection_point)
        btn_layout.addWidget(remove_btn)
        layout.addLayout(btn_layout)
        
        # 座標入力
        coord_group = QtWidgets.QGroupBox(tr("point_coordinates"))
        coord_layout = QtWidgets.QFormLayout(coord_group)
        
        self.point_name_edit = QtWidgets.QLineEdit()
        self.point_x_spin = QtWidgets.QDoubleSpinBox()
        self.point_y_spin = QtWidgets.QDoubleSpinBox()
        self.point_z_spin = QtWidgets.QDoubleSpinBox()
        
        for spin in [self.point_x_spin, self.point_y_spin, self.point_z_spin]:
            spin.setRange(-10000, 10000)
            spin.setDecimals(6)
            spin.setSingleStep(0.01)
        
        coord_layout.addRow(tr("name") + ":", self.point_name_edit)
        coord_layout.addRow("X:", self.point_x_spin)
        coord_layout.addRow("Y:", self.point_y_spin)
        coord_layout.addRow("Z:", self.point_z_spin)
        
        update_btn = QtWidgets.QPushButton(tr("update_point"))
        update_btn.clicked.connect(self.update_connection_point)
        coord_layout.addRow(update_btn)
        
        layout.addWidget(coord_group)
        
        return widget
    
    def create_properties_tab(self) -> QtWidgets.QWidget:
        """物理パラメータタブ"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # 説明
        info = QtWidgets.QLabel(tr("properties_info"))
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # パラメータ入力
        params_group = QtWidgets.QGroupBox(tr("parameters"))
        params_layout = QtWidgets.QFormLayout(params_group)
        
        # 体積
        self.volume_spin = QtWidgets.QDoubleSpinBox()
        self.volume_spin.setRange(0, 1000)
        self.volume_spin.setDecimals(9)
        self.volume_spin.setSingleStep(0.001)
        self.volume_auto_check = QtWidgets.QCheckBox(tr("auto_from_stl"))
        self.volume_auto_check.setChecked(True)
        volume_layout = QtWidgets.QHBoxLayout()
        volume_layout.addWidget(self.volume_spin)
        volume_layout.addWidget(self.volume_auto_check)
        params_layout.addRow(tr("volume") + " (m³):", volume_layout)
        
        # 密度
        self.density_spin = QtWidgets.QDoubleSpinBox()
        self.density_spin.setRange(0.001, 100000)
        self.density_spin.setDecimals(3)
        self.density_spin.setValue(1000.0)  # 水の密度
        params_layout.addRow(tr("density") + " (kg/m³):", self.density_spin)
        
        # 質量
        self.mass_spin = QtWidgets.QDoubleSpinBox()
        self.mass_spin.setRange(0.001, 10000)
        self.mass_spin.setDecimals(6)
        params_layout.addRow(tr("mass") + " (kg):", self.mass_spin)
        
        layout.addWidget(params_group)
        
        # 計算ボタン
        calc_btn = QtWidgets.QPushButton(tr("calculate_properties"))
        calc_btn.clicked.connect(self.calculate_properties)
        layout.addWidget(calc_btn)
        
        # 重心
        com_group = QtWidgets.QGroupBox(tr("center_of_mass"))
        com_layout = QtWidgets.QFormLayout(com_group)
        
        self.com_x_spin = QtWidgets.QDoubleSpinBox()
        self.com_y_spin = QtWidgets.QDoubleSpinBox()
        self.com_z_spin = QtWidgets.QDoubleSpinBox()
        
        for spin in [self.com_x_spin, self.com_y_spin, self.com_z_spin]:
            spin.setRange(-10000, 10000)
            spin.setDecimals(6)
        
        com_layout.addRow("X:", self.com_x_spin)
        com_layout.addRow("Y:", self.com_y_spin)
        com_layout.addRow("Z:", self.com_z_spin)
        
        calc_com_btn = QtWidgets.QPushButton(tr("calculate_from_stl"))
        calc_com_btn.clicked.connect(self.calculate_com)
        com_layout.addRow(calc_com_btn)
        
        layout.addWidget(com_group)
        layout.addStretch()
        
        return widget
    
    def create_inertia_tab(self) -> QtWidgets.QWidget:
        """慣性テンソルタブ"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # 説明
        info = QtWidgets.QLabel(tr("inertia_info"))
        info.setWordWrap(True)
        layout.addWidget(info)
        
        # 慣性テンソル入力
        inertia_group = QtWidgets.QGroupBox(tr("inertia_tensor"))
        inertia_layout = QtWidgets.QGridLayout(inertia_group)
        
        self.ixx_spin = QtWidgets.QDoubleSpinBox()
        self.ixy_spin = QtWidgets.QDoubleSpinBox()
        self.ixz_spin = QtWidgets.QDoubleSpinBox()
        self.iyy_spin = QtWidgets.QDoubleSpinBox()
        self.iyz_spin = QtWidgets.QDoubleSpinBox()
        self.izz_spin = QtWidgets.QDoubleSpinBox()
        
        spins = [self.ixx_spin, self.ixy_spin, self.ixz_spin, 
                 self.iyy_spin, self.iyz_spin, self.izz_spin]
        
        for spin in spins:
            spin.setRange(-10000, 10000)
            spin.setDecimals(12)
            spin.setSingleStep(0.001)
        
        inertia_layout.addWidget(QtWidgets.QLabel("Ixx:"), 0, 0)
        inertia_layout.addWidget(self.ixx_spin, 0, 1)
        inertia_layout.addWidget(QtWidgets.QLabel("Ixy:"), 1, 0)
        inertia_layout.addWidget(self.ixy_spin, 1, 1)
        inertia_layout.addWidget(QtWidgets.QLabel("Ixz:"), 2, 0)
        inertia_layout.addWidget(self.ixz_spin, 2, 1)
        inertia_layout.addWidget(QtWidgets.QLabel("Iyy:"), 3, 0)
        inertia_layout.addWidget(self.iyy_spin, 3, 1)
        inertia_layout.addWidget(QtWidgets.QLabel("Iyz:"), 4, 0)
        inertia_layout.addWidget(self.iyz_spin, 4, 1)
        inertia_layout.addWidget(QtWidgets.QLabel("Izz:"), 5, 0)
        inertia_layout.addWidget(self.izz_spin, 5, 1)
        
        layout.addWidget(inertia_group)
        
        # 計算ボタン
        calc_layout = QtWidgets.QHBoxLayout()
        
        calc_precise_btn = QtWidgets.QPushButton(tr("calculate_precise"))
        calc_precise_btn.clicked.connect(self.calculate_inertia_precise)
        calc_layout.addWidget(calc_precise_btn)
        
        calc_bbox_btn = QtWidgets.QPushButton(tr("calculate_bbox"))
        calc_bbox_btn.clicked.connect(self.calculate_inertia_bbox)
        calc_layout.addWidget(calc_bbox_btn)
        
        layout.addLayout(calc_layout)
        layout.addStretch()
        
        return widget
    
    # ========== イベントハンドラ ==========
    
    def load_stl(self):
        """STL読み込み（ダイアログ表示）"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            tr("load_stl"),
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        
        if file_path:
            self.load_stl_file(file_path)
    
    def load_stl_file(self, file_path: str):
        """STLファイルを読み込む（外部からも呼び出し可能）"""
        try:
            success = self.stl_processor.load_stl(file_path)
            if success:
                self.current_stl_file = file_path
                self.update_3d_view()
                self.event_bus.status_message.emit(
                    f"{tr('file_loaded')}: {Path(file_path).name}",
                    3000
                )
        except Exception as e:
            QtWidgets.QMessageBox.critical(
                self,
                tr("error"),
                f"Failed to load STL: {e}"
            )
        
        if file_path:
            success = self.stl_processor.load_stl(file_path)
            if success:
                self.current_stl_file = file_path
                self.calculator.set_polydata(self.stl_processor.polydata)
                self.update_3d_view()
                self.info_label.setText(f"STL: {Path(file_path).name}")
                
                # 体積を自動計算
                if self.volume_auto_check.isChecked():
                    self.volume_spin.setValue(self.calculator.volume)
    
    def load_part_xml(self):
        """パーツXML読み込み"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            tr("load_part_xml"),
            "",
            "XML Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            data = self.xml_generator.load_xml(file_path)
            if data:
                self.current_xml_file = file_path
                self.load_part_data(data)
                QtWidgets.QMessageBox.information(
                    self,
                    tr("success"),
                    tr("part_xml_loaded")
                )
    
    def load_part_data(self, data: dict):
        """パーツデータをUIに反映"""
        # 接続点
        self.connection_points.clear()
        self.points_list.clear()
        for name, coords in data.get("points", {}).items():
            point = ConnectionPoint(name, coords)
            self.connection_points[name] = point
            self.points_list.addItem(name)
        
        # 物理パラメータ
        props = data.get("properties", {})
        if "volume" in props:
            self.volume_spin.setValue(props["volume"])
        if "density" in props:
            self.density_spin.setValue(props["density"])
        if "mass" in props:
            self.mass_spin.setValue(props["mass"])
        
        # 重心
        if "center_of_mass" in props:
            com = props["center_of_mass"]
            self.com_x_spin.setValue(com[0])
            self.com_y_spin.setValue(com[1])
            self.com_z_spin.setValue(com[2])
        
        # 慣性テンソル
        if "inertia" in props:
            inertia = props["inertia"]
            self.ixx_spin.setValue(inertia[0, 0])
            self.ixy_spin.setValue(inertia[0, 1])
            self.ixz_spin.setValue(inertia[0, 2])
            self.iyy_spin.setValue(inertia[1, 1])
            self.iyz_spin.setValue(inertia[1, 2])
            self.izz_spin.setValue(inertia[2, 2])
        
        self.update_connection_points_display()
    
    def add_connection_point(self):
        """接続点を追加"""
        name, ok = QtWidgets.QInputDialog.getText(
            self,
            tr("add_point"),
            tr("point_name") + ":"
        )
        
        if ok and name:
            if name in self.connection_points:
                QtWidgets.QMessageBox.warning(
                    self,
                    tr("error"),
                    tr("point_already_exists")
                )
                return
            
            point = ConnectionPoint(name, [0.0, 0.0, 0.0])
            self.connection_points[name] = point
            self.points_list.addItem(name)
            self.update_connection_points_display()
            self.has_unsaved_changes = True
    
    def remove_connection_point(self):
        """接続点を削除"""
        current = self.points_list.currentItem()
        if current:
            name = current.text()
            del self.connection_points[name]
            self.points_list.takeItem(self.points_list.row(current))
            self.update_connection_points_display()
            self.has_unsaved_changes = True
    
    def on_point_selected(self):
        """接続点選択時"""
        current = self.points_list.currentItem()
        if current:
            name = current.text()
            point = self.connection_points[name]
            self.point_name_edit.setText(name)
            self.point_x_spin.setValue(point.position[0])
            self.point_y_spin.setValue(point.position[1])
            self.point_z_spin.setValue(point.position[2])
    
    def update_connection_point(self):
        """接続点を更新"""
        current = self.points_list.currentItem()
        if current:
            old_name = current.text()
            new_name = self.point_name_edit.text()
            
            point = self.connection_points[old_name]
            point.position = [
                self.point_x_spin.value(),
                self.point_y_spin.value(),
                self.point_z_spin.value()
            ]
            
            # 名前変更
            if new_name != old_name:
                del self.connection_points[old_name]
                point.name = new_name
                self.connection_points[new_name] = point
                current.setText(new_name)
            
            self.update_connection_points_display()
            self.has_unsaved_changes = True
    
    def calculate_properties(self):
        """物理パラメータ計算"""
        if self.calculator.polydata is None:
            QtWidgets.QMessageBox.warning(
                self,
                tr("error"),
                tr("load_stl_first")
            )
            return
        
        volume = self.volume_spin.value() if not self.volume_auto_check.isChecked() else None
        density = self.density_spin.value()
        mass = self.mass_spin.value()
        
        result = self.calculator.calculate_from_two_params(
            volume=volume,
            density=density,
            mass=mass
        )
        
        self.volume_spin.setValue(result["volume"])
        self.density_spin.setValue(result["density"])
        self.mass_spin.setValue(result["mass"])
        
        self.has_unsaved_changes = True
    
    def calculate_com(self):
        """重心計算"""
        if self.calculator.polydata is None:
            QtWidgets.QMessageBox.warning(
                self,
                tr("error"),
                tr("load_stl_first")
            )
            return
        
        com = self.calculator.calculate_center_of_mass()
        self.com_x_spin.setValue(com[0])
        self.com_y_spin.setValue(com[1])
        self.com_z_spin.setValue(com[2])
        
        self.has_unsaved_changes = True
    
    def calculate_inertia_precise(self):
        """慣性テンソル（精密計算）"""
        if self.calculator.polydata is None:
            QtWidgets.QMessageBox.warning(
                self,
                tr("error"),
                tr("load_stl_first")
            )
            return
        
        mass = self.mass_spin.value()
        com = np.array([
            self.com_x_spin.value(),
            self.com_y_spin.value(),
            self.com_z_spin.value()
        ])
        
        inertia = self.calculator.calculate_inertia_tensor(mass, com)
        self.set_inertia_values(inertia)
        self.has_unsaved_changes = True
    
    def calculate_inertia_bbox(self):
        """慣性テンソル（バウンディングボックス近似）"""
        if self.calculator.polydata is None:
            QtWidgets.QMessageBox.warning(
                self,
                tr("error"),
                tr("load_stl_first")
            )
            return
        
        mass = self.mass_spin.value()
        inertia = self.calculator.get_bounding_box_inertia(mass)
        self.set_inertia_values(inertia)
        self.has_unsaved_changes = True
    
    def set_inertia_values(self, inertia: np.ndarray):
        """慣性テンソル値を設定"""
        self.ixx_spin.setValue(inertia[0, 0])
        self.ixy_spin.setValue(inertia[0, 1])
        self.ixz_spin.setValue(inertia[0, 2])
        self.iyy_spin.setValue(inertia[1, 1])
        self.iyz_spin.setValue(inertia[1, 2])
        self.izz_spin.setValue(inertia[2, 2])
    
    def save_part_xml(self):
        """パーツXMLを保存"""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            tr("save_part_xml"),
            "",
            "XML Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            # データ収集
            points = {
                name: point.position
                for name, point in self.connection_points.items()
            }
            
            inertia = np.array([
                [self.ixx_spin.value(), self.ixy_spin.value(), self.ixz_spin.value()],
                [self.ixy_spin.value(), self.iyy_spin.value(), self.iyz_spin.value()],
                [self.ixz_spin.value(), self.iyz_spin.value(), self.izz_spin.value()]
            ])
            
            properties = {
                "mass": self.mass_spin.value(),
                "volume": self.volume_spin.value(),
                "density": self.density_spin.value(),
                "center_of_mass": [
                    self.com_x_spin.value(),
                    self.com_y_spin.value(),
                    self.com_z_spin.value()
                ],
                "inertia": inertia
            }
            
            stl_file = Path(self.current_stl_file).name if self.current_stl_file else "unknown.stl"
            
            root = self.xml_generator.create_part_xml(
                stl_file=stl_file,
                points=points,
                properties=properties
            )
            
            success = self.xml_generator.save_xml(root, file_path)
            if success:
                self.current_xml_file = file_path
                self.has_unsaved_changes = False
                QtWidgets.QMessageBox.information(
                    self,
                    tr("success"),
                    tr("part_xml_saved")
                )
    
    def reset_camera(self):
        """カメラリセット"""
        self.renderer.ResetCamera()
        self.fit_camera_to_model()
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def fit_camera_to_model(self):
        """STLモデルが画面いっぱいに表示されるようにカメラを調整"""
        if self.stl_processor.polydata is None:
            return
        
        camera = self.renderer.GetActiveCamera()
        bounds = self.stl_processor.polydata.GetBounds()
        
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
        
        # モデルが画面にフィットするようにパラレルスケールを設定
        if aspect_ratio > 1:  # 横長の画面
            camera.SetParallelScale(size / 2)
        else:  # 縦長の画面
            camera.SetParallelScale(size / (2 * aspect_ratio))
        
        self.renderer.ResetCameraClippingRange()
    
    def toggle_connection_points(self, checked: bool):
        """接続点表示切り替え"""
        for point in self.connection_points.values():
            if point.actor:
                point.actor.SetVisibility(1 if checked else 0)
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def update_3d_view(self):
        """3Dビュー更新"""
        if self.stl_processor.polydata is None:
            print("update_3d_view: polydata is None")
            return
        
        print(f"update_3d_view: polydata exists, updating view")
        
        # STLアクター
        if self.stl_actor:
            self.renderer.RemoveActor(self.stl_actor)
        
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputData(self.stl_processor.polydata)
        
        self.stl_actor = vtk.vtkActor()
        self.stl_actor.SetMapper(mapper)
        self.stl_actor.GetProperty().SetColor(0.7, 0.7, 0.8)
        
        # 透明度スライダーの値を適用
        opacity = self.opacity_slider.value() / 100.0
        print(f"Setting opacity to: {opacity} (slider value: {self.opacity_slider.value()})")
        self.stl_actor.GetProperty().SetOpacity(opacity)
        
        self.renderer.AddActor(self.stl_actor)
        print(f"Actor added to renderer")
        
        # 原点座標軸が存在しない場合は再追加
        if not self.origin_axes_actors:
            self.add_origin_axes()
        
        self.renderer.ResetCamera()
        self.fit_camera_to_model()
        self.vtk_render_widget.GetRenderWindow().Render()
        print("View updated and rendered")
    
    def update_connection_points_display(self):
        """接続点表示を更新"""
        # 既存の接続点アクターを削除
        for point in self.connection_points.values():
            if point.actor:
                self.renderer.RemoveActor(point.actor)
                point.actor = None
        
        # 新しい接続点を追加
        for point in self.connection_points.values():
            sphere = vtk.vtkSphereSource()
            sphere.SetCenter(point.position)
            sphere.SetRadius(5.0)  # 可視サイズ
            sphere.SetThetaResolution(16)
            sphere.SetPhiResolution(16)
            
            mapper = vtk.vtkPolyDataMapper()
            mapper.SetInputConnection(sphere.GetOutputPort())
            
            actor = vtk.vtkActor()
            actor.SetMapper(mapper)
            actor.GetProperty().SetColor(point.color)
            
            self.renderer.AddActor(actor)
            point.actor = actor
        
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def connect_signals(self):
        """シグナル接続"""
        self.event_bus.language_changed.connect(self.update_translations)
    
    def update_translations(self):
        """翻訳更新"""
        pass
    
    def closeEvent(self, event):
        """ウィンドウクローズ時のクリーンアップ"""
        if hasattr(self, 'vtk_render_widget'):
            self.vtk_render_widget.Finalize()
        event.accept()
    
    def reset(self):
        """モードをリセット"""
        self.current_stl_file = None
        self.current_xml_file = None
        self.connection_points.clear()
        self.has_unsaved_changes = False
        self.parts_list.clear()
        
        # 3Dビューをクリア
        if hasattr(self, 'renderer'):
            self.renderer.RemoveAllViewProps()
            if hasattr(self, 'vtk_render_widget'):
                self.vtk_render_widget.GetRenderWindow().Render()
    
    def load_parts_list(self, parts: Dict[str, Any]):
        """パーツリストを読み込む"""
        self.parts_list = parts
    
    def get_current_parts_data(self) -> Dict[str, Any]:
        """現在のパーツデータを取得"""
        if self.current_stl_file and self.current_xml_file:
            part_name = Path(self.current_stl_file).stem
            return {
                part_name: {
                    'stl_file': self.current_stl_file,
                    'xml_file': self.current_xml_file
                }
            }
        return {}
    
    def send_to_assembler(self):
        """現在のパーツをAssemblerに送る"""
        if not self.current_stl_file or not self.current_xml_file:
            QtWidgets.QMessageBox.warning(
                self,
                tr("warning"),
                "パーツXMLを保存してからAssemblerに送信してください"
            )
            return
        
        # ワークフローマネージャーに通知
        workflow_manager.set_part_completed(self.current_stl_file, self.current_xml_file)
        
        QtWidgets.QMessageBox.information(
            self,
            tr("success"),
            f"パーツをAssemblerに送信しました:\n{Path(self.current_stl_file).stem}"
        )
