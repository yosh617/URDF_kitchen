"""
URDF Kitchen Studio - Assembler UI
ノードグラフベースのロボットアセンブリインターフェース
"""

from PySide6 import QtWidgets, QtCore, QtGui
from PySide6.QtGui import QAction
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor
import vtk
import os
from pathlib import Path
from typing import Dict, List, Optional, Any

from NodeGraphQt import NodeGraph, BaseNode
from core.urdf_kitchen_assembly import URDFGenerator, ProjectPersistence
from utils.event_bus import URDFEventBus
from utils.translator import tr


class PartNode(BaseNode):
    """パーツノード（NodeGraphQt用）"""
    
    __identifier__ = 'urdf.kitchen'
    NODE_NAME = 'Part'
    
    def __init__(self):
        super().__init__()
        self.stl_file = None
        self.xml_file = None
        self.mass_value = 1.0
        self.inertia = {
            "ixx": 0.01, "ixy": 0.0, "ixz": 0.0,
            "iyy": 0.01, "iyz": 0.0, "izz": 0.01
        }
        self.node_color = (0.8, 0.2, 0.2)
        self.center_of_mass = [0, 0, 0]
        self.massless_decoration = False
        
        # ポート作成
        self.add_input('parent')
        self.add_output('child')


class AssemblerWidget(QtWidgets.QWidget):
    """Assembler メインウィジェット"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.event_bus = URDFEventBus()
        self.urdf_generator = URDFGenerator()
        self.project_persistence = ProjectPersistence()
        
        self.robot_name = "robot"
        self.current_project_file = None
        self.meshes_dir = None
        self.has_unsaved_changes = False
        
        # プロジェクト管理
        self.project = None
        self.parts_dir = None
        self.export_dir = None
        
        self.init_ui()
        self.connect_signals()
    
    def init_ui(self):
        """UI初期化"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # ツールバー
        toolbar = self.create_toolbar()
        layout.addWidget(toolbar)
        
        # メインスプリッター
        splitter = QtWidgets.QSplitter(QtCore.Qt.Horizontal)
        
        # 左側：ノードグラフ（60%）
        self.node_graph_widget = self.create_node_graph()
        splitter.addWidget(self.node_graph_widget)
        
        # 右側：3Dプレビュー + プロパティ（40%）
        right_panel = self.create_right_panel()
        splitter.addWidget(right_panel)
        
        splitter.setStretchFactor(0, 6)
        splitter.setStretchFactor(1, 4)
        
        layout.addWidget(splitter)
        
        # ステータスバー
        self.status_bar = QtWidgets.QStatusBar()
        layout.addWidget(self.status_bar)
        self.update_status(tr("ready"))
    
    def create_toolbar(self) -> QtWidgets.QToolBar:
        """ツールバー作成"""
        toolbar = QtWidgets.QToolBar()
        toolbar.setIconSize(QtCore.QSize(24, 24))
        
        # ロボット名
        toolbar.addWidget(QtWidgets.QLabel(tr("robot_name") + ":"))
        self.robot_name_edit = QtWidgets.QLineEdit(self.robot_name)
        self.robot_name_edit.setMaximumWidth(200)
        self.robot_name_edit.textChanged.connect(self.on_robot_name_changed)
        toolbar.addWidget(self.robot_name_edit)
        
        toolbar.addSeparator()
        
        # プロジェクト操作
        new_action = QAction(tr("new_project"), self)
        new_action.setToolTip(tr("create_new_project"))
        new_action.triggered.connect(self.new_project)
        toolbar.addAction(new_action)
        
        open_action = QAction(tr("open_project"), self)
        open_action.setToolTip(tr("open_existing_project"))
        open_action.triggered.connect(self.open_project)
        toolbar.addAction(open_action)
        
        save_action = QAction(tr("save_project"), self)
        save_action.setToolTip(tr("save_current_project"))
        save_action.triggered.connect(self.save_project)
        toolbar.addAction(save_action)
        
        toolbar.addSeparator()
        
        # ノード操作
        add_part_action = QAction(tr("add_part"), self)
        add_part_action.setToolTip(tr("add_part_node"))
        add_part_action.triggered.connect(self.add_part_node)
        toolbar.addAction(add_part_action)
        
        add_base_action = QAction(tr("add_base_link"), self)
        add_base_action.setToolTip(tr("add_base_link_node"))
        add_base_action.triggered.connect(self.add_base_link)
        toolbar.addAction(add_base_action)
        
        toolbar.addSeparator()
        
        # URDF生成
        export_urdf_action = QAction(tr("export_urdf"), self)
        export_urdf_action.setToolTip(tr("generate_urdf_file"))
        export_urdf_action.triggered.connect(self.export_urdf)
        toolbar.addAction(export_urdf_action)
        
        return toolbar
    
    def create_node_graph(self) -> QtWidgets.QWidget:
        """ノードグラフウィジェット作成"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # NodeGraphQt インスタンス
        self.graph = NodeGraph()
        self.graph.register_node(PartNode)
        
        # グラフウィジェット
        graph_widget = self.graph.widget
        layout.addWidget(graph_widget)
        
        return container
    
    def create_right_panel(self) -> QtWidgets.QWidget:
        """右側パネル（3Dプレビュー + プロパティ）"""
        panel = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # タブウィジェット
        tabs = QtWidgets.QTabWidget()
        
        # 3Dプレビュータブ
        preview_tab = self.create_3d_preview()
        tabs.addTab(preview_tab, tr("3d_preview"))
        
        # ノードプロパティタブ
        properties_tab = self.create_properties_panel()
        tabs.addTab(properties_tab, tr("node_properties"))
        
        # ツリービュータブ
        tree_tab = self.create_tree_view()
        tabs.addTab(tree_tab, tr("tree_view"))
        
        layout.addWidget(tabs)
        
        return panel
    
    def create_3d_preview(self) -> QtWidgets.QWidget:
        """3Dプレビュー作成"""
        container = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(container)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # VTK Widget
        self.vtk_render_widget = QVTKRenderWindowInteractor(container)
        
        # VTK セットアップ
        self.renderer = vtk.vtkRenderer()
        self.renderer.SetBackground(0.1, 0.1, 0.1)
        
        self.vtk_render_widget.GetRenderWindow().AddRenderer(self.renderer)
        self.interactor = self.vtk_render_widget.GetRenderWindow().GetInteractor()
        
        style = vtk.vtkInteractorStyleTrackballCamera()
        self.interactor.SetInteractorStyle(style)
        
        # 軸
        self.axes_actor = vtk.vtkAxesActor()
        self.axes_widget = vtk.vtkOrientationMarkerWidget()
        self.axes_widget.SetOrientationMarker(self.axes_actor)
        self.axes_widget.SetInteractor(self.interactor)
        self.axes_widget.SetViewport(0.0, 0.0, 0.15, 0.15)
        self.axes_widget.SetEnabled(1)
        self.axes_widget.InteractiveOn()
        
        # 原点座標軸
        self.origin_axes_actors = []
        self.add_origin_axes()
        
        # 平面アクター
        self.plane_actors = {'xy': None, 'xz': None, 'yz': None}
        
        layout.addWidget(self.vtk_render_widget)
        
        # コントロールボタン
        btn_layout = QtWidgets.QHBoxLayout()
        
        reset_btn = QtWidgets.QPushButton(tr("reset_view"))
        reset_btn.clicked.connect(self.reset_3d_view)
        btn_layout.addWidget(reset_btn)
        
        refresh_btn = QtWidgets.QPushButton(tr("refresh_preview"))
        refresh_btn.clicked.connect(self.refresh_3d_preview)
        btn_layout.addWidget(refresh_btn)
        
        # 軸表示切り替えチェックボックス
        self.axes_checkbox = QtWidgets.QCheckBox(tr("show_axes"))
        self.axes_checkbox.setChecked(True)
        self.axes_checkbox.toggled.connect(self.toggle_axes)
        btn_layout.addWidget(self.axes_checkbox)
        
        # 透明度スライダー
        btn_layout.addWidget(QtWidgets.QLabel(tr("opacity") + ":"))
        self.opacity_slider = QtWidgets.QSlider(QtCore.Qt.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(100)
        self.opacity_slider.setMaximumWidth(100)
        self.opacity_slider.valueChanged.connect(self.update_opacity)
        btn_layout.addWidget(self.opacity_slider)
        
        btn_layout.addStretch()
        
        # 平面表示
        plane_layout = QtWidgets.QHBoxLayout()
        plane_layout.addWidget(QtWidgets.QLabel(tr("show_grid") + ":"))
        
        self.xy_plane_check = QtWidgets.QCheckBox("XY")
        self.xy_plane_check.toggled.connect(lambda: self.toggle_plane('xy'))
        plane_layout.addWidget(self.xy_plane_check)
        
        self.xz_plane_check = QtWidgets.QCheckBox("XZ")
        self.xz_plane_check.toggled.connect(lambda: self.toggle_plane('xz'))
        plane_layout.addWidget(self.xz_plane_check)
        
        self.yz_plane_check = QtWidgets.QCheckBox("YZ")
        self.yz_plane_check.toggled.connect(lambda: self.toggle_plane('yz'))
        plane_layout.addWidget(self.yz_plane_check)
        
        plane_layout.addStretch()
        
        layout.addLayout(btn_layout)
        layout.addLayout(plane_layout)
        
        self.interactor.Initialize()
        
        return container
    
    def create_properties_panel(self) -> QtWidgets.QWidget:
        """ノードプロパティパネル"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        # 選択ノード情報
        info_group = QtWidgets.QGroupBox(tr("selected_node"))
        info_layout = QtWidgets.QFormLayout(info_group)
        
        self.node_name_label = QtWidgets.QLabel("-")
        self.node_type_label = QtWidgets.QLabel("-")
        self.stl_file_label = QtWidgets.QLabel("-")
        self.xml_file_label = QtWidgets.QLabel("-")
        
        info_layout.addRow(tr("name") + ":", self.node_name_label)
        info_layout.addRow(tr("type") + ":", self.node_type_label)
        info_layout.addRow("STL:", self.stl_file_label)
        info_layout.addRow("XML:", self.xml_file_label)
        
        layout.addWidget(info_group)
        
        # ノード編集
        edit_group = QtWidgets.QGroupBox(tr("edit_node"))
        edit_layout = QtWidgets.QVBoxLayout(edit_group)
        
        load_stl_btn = QtWidgets.QPushButton(tr("load_stl"))
        load_stl_btn.clicked.connect(self.load_stl_for_node)
        edit_layout.addWidget(load_stl_btn)
        
        load_xml_btn = QtWidgets.QPushButton(tr("load_part_xml"))
        load_xml_btn.clicked.connect(self.load_xml_for_node)
        edit_layout.addWidget(load_xml_btn)
        
        # 質量
        mass_layout = QtWidgets.QHBoxLayout()
        mass_layout.addWidget(QtWidgets.QLabel(tr("mass") + ":"))
        self.mass_spin = QtWidgets.QDoubleSpinBox()
        self.mass_spin.setRange(0.001, 10000)
        self.mass_spin.setDecimals(6)
        self.mass_spin.setValue(1.0)
        self.mass_spin.valueChanged.connect(self.update_node_mass)
        mass_layout.addWidget(self.mass_spin)
        edit_layout.addLayout(mass_layout)
        
        # Massless decoration
        self.massless_check = QtWidgets.QCheckBox(tr("massless_decoration"))
        self.massless_check.stateChanged.connect(self.update_node_massless)
        edit_layout.addWidget(self.massless_check)
        
        layout.addWidget(edit_group)
        layout.addStretch()
        
        return widget
    
    def create_tree_view(self) -> QtWidgets.QWidget:
        """ツリービュー"""
        widget = QtWidgets.QWidget()
        layout = QtWidgets.QVBoxLayout(widget)
        
        self.tree_text = QtWidgets.QTextEdit()
        self.tree_text.setReadOnly(True)
        self.tree_text.setFontFamily("Courier New")
        layout.addWidget(self.tree_text)
        
        refresh_btn = QtWidgets.QPushButton(tr("refresh_tree"))
        refresh_btn.clicked.connect(self.refresh_tree_view)
        layout.addWidget(refresh_btn)
        
        return widget
    
    # ========== イベントハンドラ ==========
    
    def on_robot_name_changed(self, text: str):
        """ロボット名変更"""
        self.robot_name = text
        self.has_unsaved_changes = True
    
    def new_project(self):
        """新規プロジェクト"""
        if self.has_unsaved_changes:
            reply = QtWidgets.QMessageBox.question(
                self,
                tr("unsaved_changes"),
                tr("save_before_new"),
                QtWidgets.QMessageBox.Save | 
                QtWidgets.QMessageBox.Discard | 
                QtWidgets.QMessageBox.Cancel
            )
            
            if reply == QtWidgets.QMessageBox.Save:
                self.save_project()
            elif reply == QtWidgets.QMessageBox.Cancel:
                return
        
        # グラフクリア
        self.graph.clear_session()
        self.robot_name = "robot"
        self.robot_name_edit.setText(self.robot_name)
        self.current_project_file = None
        self.has_unsaved_changes = False
        self.update_status(tr("new_project_created"))
    
    def open_project(self):
        """プロジェクト読み込み"""
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            tr("open_project"),
            "",
            "Project Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            data = self.project_persistence.load_project(file_path)
            if data:
                self.load_project_data(data)
                self.current_project_file = file_path
                self.has_unsaved_changes = False
                self.update_status(f"{tr('project_loaded')}: {Path(file_path).name}")
    
    def load_project_data(self, data: dict):
        """プロジェクトデータを読み込み"""
        # グラフクリア
        self.graph.clear_session()
        
        # ロボット名
        self.robot_name = data.get("robot_name", "robot")
        self.robot_name_edit.setText(self.robot_name)
        
        # meshes ディレクトリ
        self.meshes_dir = data.get("meshes_dir")
        self.project_persistence.meshes_dir = self.meshes_dir
        
        # ノード作成
        nodes_dict = {}
        for node_data in data.get("nodes", []):
            node = self.create_node_from_data(node_data)
            if node:
                nodes_dict[node_data["name"]] = node
        
        # 接続
        for from_node, from_port, to_node, to_port in data.get("connections", []):
            if from_node in nodes_dict and to_node in nodes_dict:
                from_node_obj = nodes_dict[from_node]
                to_node_obj = nodes_dict[to_node]
                
                # ポート接続（NodeGraphQt API使用）
                try:
                    from_port_obj = from_node_obj.output(0)  # 簡易実装
                    to_port_obj = to_node_obj.input(0)
                    from_port_obj.connect_to(to_port_obj)
                except Exception as e:
                    print(f"Connection error: {e}")
    
    def create_node_from_data(self, data: dict) -> Optional[PartNode]:
        """データからノード作成"""
        try:
            node = self.graph.create_node(
                'urdf.kitchen.PartNode',
                name=data.get("name", "part"),
                pos=data.get("position", [0, 0])
            )
            
            if "stl_file" in data:
                node.stl_file = data["stl_file"]
            if "mass" in data:
                node.mass_value = data["mass"]
            if "inertia" in data:
                node.inertia = data["inertia"]
            if "color" in data:
                node.node_color = data["color"]
            if "massless_decoration" in data:
                node.massless_decoration = data["massless_decoration"]
            
            return node
        except Exception as e:
            print(f"Error creating node: {e}")
            return None
    
    def save_project(self):
        """プロジェクト保存"""
        if self.current_project_file:
            file_path = self.current_project_file
        else:
            file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
                self,
                tr("save_project"),
                "",
                "Project Files (*.xml);;All Files (*)"
            )
        
        if file_path:
            # ノードと接続を収集
            nodes = self.graph.all_nodes()
            connections = []
            
            for node in nodes:
                for output_port in node.output_ports():
                    for connected_port in output_port.connected_ports():
                        connections.append((
                            node.name(),
                            output_port.name(),
                            connected_port.node().name(),
                            connected_port.name()
                        ))
            
            success = self.project_persistence.save_project(
                file_path=file_path,
                robot_name=self.robot_name,
                nodes=nodes,
                connections=connections
            )
            
            if success:
                self.current_project_file = file_path
                self.has_unsaved_changes = False
                self.update_status(f"{tr('project_saved')}: {Path(file_path).name}")
    
    def add_part_node(self):
        """パーツノード追加"""
        node = self.graph.create_node('urdf.kitchen.PartNode', name='part')
        self.has_unsaved_changes = True
        self.update_status(tr("part_node_added"))
    
    def add_base_link(self):
        """base_linkノード追加"""
        node = self.graph.create_node('urdf.kitchen.PartNode', name='base_link')
        node.mass_value = 0.0
        self.has_unsaved_changes = True
        self.update_status(tr("base_link_added"))
    
    def export_urdf(self):
        """URDF出力"""
        file_path, _ = QtWidgets.QFileDialog.getSaveFileName(
            self,
            tr("export_urdf"),
            f"{self.robot_name}.urdf",
            "URDF Files (*.urdf);;All Files (*)"
        )
        
        if file_path:
            nodes = self.graph.all_nodes()
            
            self.urdf_generator.robot_name = self.robot_name
            urdf_xml = self.urdf_generator.generate_urdf(
                nodes=nodes,
                base_link_name="base_link",
                mesh_dir_name="meshes"
            )
            
            success = self.urdf_generator.save_urdf_file(urdf_xml, file_path)
            if success:
                self.update_status(f"{tr('urdf_exported')}: {Path(file_path).name}")
                QtWidgets.QMessageBox.information(
                    self,
                    tr("success"),
                    f"{tr('urdf_exported_to')}:\n{file_path}"
                )
    
    def load_stl_for_node(self):
        """選択ノードにSTLを読み込み"""
        selected = self.graph.selected_nodes()
        if not selected:
            QtWidgets.QMessageBox.warning(
                self,
                tr("error"),
                tr("select_node_first")
            )
            return
        
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            tr("load_stl"),
            "",
            "STL Files (*.stl);;All Files (*)"
        )
        
        if file_path:
            node = selected[0]
            node.stl_file = file_path
            self.stl_file_label.setText(Path(file_path).name)
            self.has_unsaved_changes = True
    
    def load_xml_for_node(self):
        """選択ノードにXMLを読み込み"""
        selected = self.graph.selected_nodes()
        if not selected:
            QtWidgets.QMessageBox.warning(
                self,
                tr("error"),
                tr("select_node_first")
            )
            return
        
        file_path, _ = QtWidgets.QFileDialog.getOpenFileName(
            self,
            tr("load_part_xml"),
            "",
            "XML Files (*.xml);;All Files (*)"
        )
        
        if file_path:
            node = selected[0]
            node.xml_file = file_path
            self.xml_file_label.setText(Path(file_path).name)
            
            # XMLから質量・慣性を読み込み（簡易実装）
            # 実際には XMLGenerator.load_xml() を使用
            self.has_unsaved_changes = True
    
    def update_node_mass(self, value: float):
        """ノード質量更新"""
        selected = self.graph.selected_nodes()
        if selected:
            selected[0].mass_value = value
            self.has_unsaved_changes = True
    
    def update_node_massless(self, state: int):
        """Massless decoration更新"""
        selected = self.graph.selected_nodes()
        if selected:
            selected[0].massless_decoration = (state == QtCore.Qt.Checked)
            self.has_unsaved_changes = True
    
    def add_origin_axes(self):
        """原点に大きな座標軸を追加"""
        # 既存の軸アクターを削除
        for actor in self.origin_axes_actors:
            self.renderer.RemoveActor(actor)
        self.origin_axes_actors.clear()
        
        origin = [0, 0, 0]
        
        # シーン全体のサイズを推定
        axis_length = 1.0  # デフォルト
        
        # レンダラー内のすべてのアクターからバウンディングボックスを計算
        actors = self.renderer.GetActors()
        actors.InitTraversal()
        all_bounds = []
        for _ in range(actors.GetNumberOfItems()):
            actor = actors.GetNextActor()
            if actor and actor not in self.origin_axes_actors:
                bounds = actor.GetBounds()
                if bounds[0] != bounds[1]:  # 有効なboundsがある
                    all_bounds.append(bounds)
        
        if all_bounds:
            # 全体のバウンディングボックスを計算
            min_x = min(b[0] for b in all_bounds)
            max_x = max(b[1] for b in all_bounds)
            min_y = min(b[2] for b in all_bounds)
            max_y = max(b[3] for b in all_bounds)
            min_z = min(b[4] for b in all_bounds)
            max_z = max(b[5] for b in all_bounds)
            
            max_dim = max(max_x - min_x, max_y - min_y, max_z - min_z)
            axis_length = max_dim * 2.0
        
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
        opacity = value / 100.0
        # すべてのノードのSTアクターの透明度を更新
        for actor in self.renderer.GetActors():
            # 原点座標軸と平面以外のアクターのみ更新
            if actor not in self.origin_axes_actors and actor not in self.plane_actors.values():
                actor.GetProperty().SetOpacity(opacity)
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
    
    def reset_3d_view(self):
        """3Dビューリセット"""
        self.renderer.ResetCamera()
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def refresh_3d_preview(self):
        """3Dプレビュー更新"""
        # 全アクター削除
        self.renderer.RemoveAllViewProps()
        
        # 原点座標軸を再追加
        self.add_origin_axes()
        
        # 全ノードのSTLを読み込んで表示
        nodes = self.graph.all_nodes()
        for node in nodes:
            if hasattr(node, 'stl_file') and node.stl_file and os.path.exists(node.stl_file):
                reader = vtk.vtkSTLReader()
                reader.SetFileName(node.stl_file)
                reader.Update()
                
                mapper = vtk.vtkPolyDataMapper()
                mapper.SetInputConnection(reader.GetOutputPort())
                
                actor = vtk.vtkActor()
                actor.SetMapper(mapper)
                
                if hasattr(node, 'node_color'):
                    actor.GetProperty().SetColor(node.node_color)
                else:
                    actor.GetProperty().SetColor(0.7, 0.7, 0.8)
                
                self.renderer.AddActor(actor)
        
        self.renderer.ResetCamera()
        self.vtk_render_widget.GetRenderWindow().Render()
    
    def refresh_tree_view(self):
        """ツリービュー更新"""
        # base_linkからツリー構造を生成
        base_node = None
        for node in self.graph.all_nodes():
            if node.name() == "base_link":
                base_node = node
                break
        
        if base_node:
            tree_text = self.generate_tree_text(base_node, 0, set())
            self.tree_text.setPlainText(tree_text)
        else:
            self.tree_text.setPlainText(tr("no_base_link"))
    
    def generate_tree_text(self, node, level: int, visited: set) -> str:
        """ツリーテキスト生成"""
        if node in visited:
            return ""
        visited.add(node)
        
        text = "  " * level + f"├─ {node.name()}\n"
        
        # 子ノード
        for output_port in node.output_ports():
            for connected_port in output_port.connected_ports():
                child_node = connected_port.node()
                text += self.generate_tree_text(child_node, level + 1, visited)
        
        return text
    
    def update_status(self, message: str):
        """ステータスバー更新"""
        self.status_bar.showMessage(message, 5000)
    
    def connect_signals(self):
        """シグナル接続"""
        self.event_bus.language_changed.connect(self.update_translations)
        
        # ノード選択イベント
        self.graph.node_selected.connect(self.on_node_selected_event)
    
    def on_node_selected_event(self, node):
        """ノード選択時"""
        if node:
            self.node_name_label.setText(node.name())
            self.node_type_label.setText(node.__class__.__name__)
            
            if hasattr(node, 'stl_file') and node.stl_file:
                self.stl_file_label.setText(Path(node.stl_file).name)
            else:
                self.stl_file_label.setText("-")
            
            if hasattr(node, 'xml_file') and node.xml_file:
                self.xml_file_label.setText(Path(node.xml_file).name)
            else:
                self.xml_file_label.setText("-")
            
            if hasattr(node, 'mass_value'):
                self.mass_spin.setValue(node.mass_value)
            
            if hasattr(node, 'massless_decoration'):
                self.massless_check.setChecked(node.massless_decoration)
    
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
        # ノードグラフをクリア
        if hasattr(self, 'node_graph'):
            self.node_graph.clear_session()
        
        # 3Dビューをクリア
        if hasattr(self, 'renderer'):
            self.renderer.RemoveAllViewProps()
            if hasattr(self, 'vtk_render_widget'):
                self.vtk_render_widget.GetRenderWindow().Render()
        
        self.robot_name = "robot"
        self.current_project_file = None
        self.has_unsaved_changes = False
    
    def load_assembly_data(self, assembly_data: Dict[str, Any]):
        """アセンブリデータを読み込む"""
        # ノードグラフにデータを復元
        # TODO: 実装詳細
        pass
    
    def get_assembly_data(self) -> Dict[str, Any]:
        """アセンブリデータを取得"""
        # ノードグラフのデータをエクスポート
        # TODO: 実装詳細
        return {}
    
    def reset(self):
        """モードをリセット"""
        # ノードグラフをクリア
        if hasattr(self, 'node_graph'):
            self.node_graph.clear_session()
        
        # 3Dビューをクリア
        if hasattr(self, 'renderer'):
            self.renderer.RemoveAllViewProps()
            if hasattr(self, 'vtk_render_widget'):
                self.vtk_render_widget.GetRenderWindow().Render()
    
    def load_assembly_data(self, assembly_data: Dict[str, Any]):
        """アセンブリデータを読み込む"""
        # ノードグラフにデータを復元
        # TODO: 実装詳細
        pass
    
    def get_assembly_data(self) -> Dict[str, Any]:
        """アセンブリデータを取得"""
        # ノードグラフのデータをエクスポート
        # TODO: 実装詳細
        return {}
