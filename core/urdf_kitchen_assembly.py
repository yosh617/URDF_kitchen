"""
URDF Kitchen Studio - Assembly 計算処理
既存 urdf_kitchen_Assembler.py から URDF 生成・プロジェクト保存読み込み処理を抽出
"""

import os
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional, Any
from pathlib import Path
import numpy as np


class URDFGenerator:
    """URDF ファイル生成エンジン"""
    
    def __init__(self, robot_name: str = "robot"):
        """初期化
        
        Args:
            robot_name: ロボット名（クリーンな名前、_description無し）
        """
        self.robot_name = robot_name
        self.materials = {}  # 色定義のキャッシュ
    
    def generate_urdf(self,
                     nodes: List[Any],
                     base_link_name: str = "base_link",
                     mesh_dir_name: str = "meshes") -> str:
        """URDF XML を生成
        
        Args:
            nodes: ノードリスト（NodeGraphQt の Node オブジェクト）
            base_link_name: ベースリンクの名前
            mesh_dir_name: メッシュディレクトリ名（package:// パスに使用）
        
        Returns:
            URDF XML 文字列
        """
        lines = []
        
        # ヘッダー
        lines.append('<?xml version="1.0"?>')
        lines.append(f'<robot name="{self.robot_name}">\n')
        
        # マテリアル定義
        self._collect_materials(nodes)
        lines.append(self._generate_materials_xml())
        
        # base_link
        base_node = self._find_node_by_name(nodes, base_link_name)
        if base_node:
            lines.append(self._generate_base_link_xml())
            
            # ツリー構造を順番に出力
            visited = set()
            self._generate_tree_xml(lines, base_node, None, visited, mesh_dir_name)
        
        lines.append('</robot>')
        
        return '\n'.join(lines)
    
    def _collect_materials(self, nodes: List[Any]):
        """ノードから色定義を収集
        
        Args:
            nodes: ノードリスト
        """
        self.materials.clear()
        
        for node in nodes:
            if hasattr(node, 'node_color'):
                rgb = node.node_color
                if len(rgb) >= 3:
                    hex_color = '#{:02x}{:02x}{:02x}'.format(
                        int(rgb[0] * 255),
                        int(rgb[1] * 255),
                        int(rgb[2] * 255)
                    )
                    self.materials[hex_color] = rgb
    
    def _generate_materials_xml(self) -> str:
        """マテリアル定義の XML を生成
        
        Returns:
            マテリアル XML 文字列
        """
        lines = ['<!-- material color setting -->']
        
        for hex_color, rgb in self.materials.items():
            lines.append(f'<material name="{hex_color}">')
            lines.append(f'  <color rgba="{rgb[0]:.3f} {rgb[1]:.3f} {rgb[2]:.3f} 1.0"/>')
            lines.append('</material>')
        
        lines.append('')
        return '\n'.join(lines)
    
    def _generate_base_link_xml(self) -> str:
        """base_link の XML を生成
        
        Returns:
            base_link XML 文字列
        """
        return '''  <link name="base_link">
    <inertial>
      <origin xyz="0 0 0" rpy="0 0 0"/>
      <mass value="0.0"/>
      <inertia ixx="0.01" ixy="0.0" ixz="0.0" iyy="0.0" iyz="0.0" izz="0.0"/>
    </inertial>
  </link>
'''
    
    def _generate_tree_xml(self,
                           lines: List[str],
                           node: Any,
                           parent_node: Optional[Any],
                           visited: set,
                           mesh_dir_name: str):
        """再帰的にツリー構造を XML 化
        
        Args:
            lines: 出力先のリスト
            node: 現在のノード
            parent_node: 親ノード（None の場合は base_link）
            visited: 訪問済みノード集合
            mesh_dir_name: メッシュディレクトリ名
        """
        if node in visited:
            return
        visited.add(node)
        
        # Massless Decoration ノードはスキップ
        is_decoration = hasattr(node, 'massless_decoration') and node.massless_decoration
        if is_decoration:
            return
        
        # base_link は既に出力済み
        if node.name() != "base_link":
            # ジョイント出力
            if parent_node is not None:
                lines.append(self._generate_joint_xml(parent_node, node))
            
            # リンク出力
            lines.append(self._generate_link_xml(node, mesh_dir_name))
        
        # 子ノードを処理
        if hasattr(node, 'output_ports'):
            for port in node.output_ports():
                for connected_port in port.connected_ports():
                    child_node = connected_port.node()
                    self._generate_tree_xml(lines, child_node, node, visited, mesh_dir_name)
    
    def _generate_joint_xml(self, parent_node: Any, child_node: Any) -> str:
        """ジョイントの XML を生成
        
        Args:
            parent_node: 親ノード
            child_node: 子ノード
        
        Returns:
            ジョイント XML 文字列
        """
        # 接続ポートから位置を取得
        origin_xyz = [0.0, 0.0, 0.0]
        origin_rpy = [0.0, 0.0, 0.0]
        
        if hasattr(parent_node, 'output_ports'):
            for port in parent_node.output_ports():
                for connected_port in port.connected_ports():
                    if connected_port.node() == child_node:
                        if hasattr(port, 'get_position'):
                            origin_xyz = port.get_position()
                        if hasattr(port, 'get_orientation'):
                            origin_rpy = port.get_orientation()
                        break
        
        # ジョイントタイプ（ノードの属性から取得、デフォルトは fixed）
        joint_type = "fixed"
        if hasattr(child_node, 'joint_type'):
            joint_type = child_node.joint_type
        
        joint_name = f"{parent_node.name()}_to_{child_node.name()}"
        
        xml = f'''  <joint name="{joint_name}" type="{joint_type}">
    <origin xyz="{origin_xyz[0]:.6f} {origin_xyz[1]:.6f} {origin_xyz[2]:.6f}" rpy="{origin_rpy[0]:.6f} {origin_rpy[1]:.6f} {origin_rpy[2]:.6f}"/>
    <parent link="{parent_node.name()}"/>
    <child link="{child_node.name()}"/>'''
        
        # 回転・移動ジョイントの場合は軸と制限を追加
        if joint_type in ["revolute", "prismatic", "continuous"]:
            # ジョイント軸（デフォルトは Z軸）
            axis = getattr(child_node, 'joint_axis', [0, 0, 1])
            xml += f'\n    <axis xyz="{axis[0]} {axis[1]} {axis[2]}"/>'
            
            # 制限値
            if joint_type != "continuous":
                lower = getattr(child_node, 'joint_lower', -3.14)
                upper = getattr(child_node, 'joint_upper', 3.14)
                effort = getattr(child_node, 'joint_effort', 100.0)
                velocity = getattr(child_node, 'joint_velocity', 1.0)
                xml += f'\n    <limit lower="{lower}" upper="{upper}" effort="{effort}" velocity="{velocity}"/>'
        
        xml += '\n  </joint>\n'
        return xml
    
    def _generate_link_xml(self, node: Any, mesh_dir_name: str) -> str:
        """リンクの XML を生成
        
        Args:
            node: ノードオブジェクト
            mesh_dir_name: メッシュディレクトリ名
        
        Returns:
            リンク XML 文字列
        """
        lines = [f'  <link name="{node.name()}">']
        
        # 慣性パラメータ
        if hasattr(node, 'mass_value') and hasattr(node, 'inertia'):
            lines.append('    <inertial>')
            
            # 重心（ノードに com 属性があれば使用、デフォルトは原点）
            com = getattr(node, 'center_of_mass', [0, 0, 0])
            lines.append(f'      <origin xyz="{com[0]:.6f} {com[1]:.6f} {com[2]:.6f}" rpy="0 0 0"/>')
            
            lines.append(f'      <mass value="{node.mass_value:.6f}"/>')
            
            # 慣性テンソル
            inertia = node.inertia
            lines.append('      <inertia')
            for key, value in inertia.items():
                lines.append(f'        {key}="{value:.12f}"')
            lines[-1] += '/>'
            
            lines.append('    </inertial>')
        
        # ビジュアル・コリジョン
        if hasattr(node, 'stl_file') and node.stl_file:
            stl_filename = os.path.basename(node.stl_file)
            package_path = f"package://{self.robot_name}_description/{mesh_dir_name}/{stl_filename}"
            
            # メインビジュアル
            lines.append('    <visual>')
            lines.append('      <origin xyz="0 0 0" rpy="0 0 0"/>')
            lines.append('      <geometry>')
            lines.append(f'        <mesh filename="{package_path}"/>')
            lines.append('      </geometry>')
            
            # 色（ノードに node_color 属性があれば追加）
            if hasattr(node, 'node_color'):
                rgb = node.node_color
                hex_color = '#{:02x}{:02x}{:02x}'.format(
                    int(rgb[0] * 255),
                    int(rgb[1] * 255),
                    int(rgb[2] * 255)
                )
                lines.append(f'      <material name="{hex_color}"/>')
            
            lines.append('    </visual>')
            
            # コリジョン
            lines.append('    <collision>')
            lines.append('      <origin xyz="0 0 0" rpy="0 0 0"/>')
            lines.append('      <geometry>')
            lines.append(f'        <mesh filename="{package_path}"/>')
            lines.append('      </geometry>')
            lines.append('    </collision>')
        
        lines.append('  </link>\n')
        return '\n'.join(lines)
    
    def _find_node_by_name(self, nodes: List[Any], name: str) -> Optional[Any]:
        """名前でノードを検索
        
        Args:
            nodes: ノードリスト
            name: ノード名
        
        Returns:
            見つかったノード、見つからない場合は None
        """
        for node in nodes:
            if hasattr(node, 'name') and callable(node.name):
                if node.name() == name:
                    return node
        return None
    
    def save_urdf_file(self, urdf_xml: str, output_path: str) -> bool:
        """URDF を ファイルに保存
        
        Args:
            urdf_xml: URDF XML 文字列
            output_path: 保存先パス
        
        Returns:
            成功時 True、失敗時 False
        """
        try:
            # ディレクトリが存在しない場合は作成
            os.makedirs(os.path.dirname(output_path), exist_ok=True)
            
            with open(output_path, 'w', encoding='utf-8') as f:
                f.write(urdf_xml)
            
            print(f"URDF saved to: {output_path}")
            return True
        except Exception as e:
            print(f"Error saving URDF: {e}")
            return False


class ProjectPersistence:
    """プロジェクトファイルの保存・読み込み"""
    
    def __init__(self):
        """初期化"""
        self.project_dir = None
        self.meshes_dir = None
    
    def save_project(self,
                    file_path: str,
                    robot_name: str,
                    nodes: List[Any],
                    connections: List[Tuple[str, str, str, str]]) -> bool:
        """プロジェクトを XML ファイルに保存
        
        Args:
            file_path: 保存先パス
            robot_name: ロボット名
            nodes: ノードリスト
            connections: 接続リスト [(from_node, from_port, to_node, to_port), ...]
        
        Returns:
            成功時 True、失敗時 False
        """
        try:
            self.project_dir = os.path.dirname(os.path.abspath(file_path))
            
            # XML ツリー作成
            root = ET.Element("project")
            
            # ロボット名
            ET.SubElement(root, "robot_name").text = robot_name
            
            # meshes ディレクトリ（相対パス）
            if self.meshes_dir:
                try:
                    meshes_rel = os.path.relpath(self.meshes_dir, self.project_dir)
                    ET.SubElement(root, "meshes_directory").text = meshes_rel
                except ValueError:
                    ET.SubElement(root, "meshes_directory").text = self.meshes_dir
            
            # ノード情報
            nodes_elem = ET.SubElement(root, "nodes")
            for node in nodes:
                node_elem = self._serialize_node(node)
                nodes_elem.append(node_elem)
            
            # 接続情報
            connections_elem = ET.SubElement(root, "connections")
            for from_node, from_port, to_node, to_port in connections:
                conn_elem = ET.SubElement(connections_elem, "connection")
                ET.SubElement(conn_elem, "from_node").text = from_node
                ET.SubElement(conn_elem, "from_port").text = from_port
                ET.SubElement(conn_elem, "to_node").text = to_node
                ET.SubElement(conn_elem, "to_port").text = to_port
            
            # ファイル保存
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(file_path, encoding='utf-8', xml_declaration=True)
            
            print(f"Project saved to: {file_path}")
            return True
            
        except Exception as e:
            print(f"Error saving project: {e}")
            return False
    
    def load_project(self, file_path: str) -> Optional[Dict]:
        """プロジェクトを XML ファイルから読み込み
        
        Args:
            file_path: プロジェクトファイルパス
        
        Returns:
            プロジェクトデータの辞書、失敗時 None
        """
        try:
            self.project_dir = os.path.dirname(os.path.abspath(file_path))
            
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            data = {
                "robot_name": "",
                "meshes_dir": None,
                "nodes": [],
                "connections": []
            }
            
            # ロボット名
            robot_name_elem = root.find("robot_name")
            if robot_name_elem is not None:
                data["robot_name"] = robot_name_elem.text or ""
            
            # meshes ディレクトリ
            meshes_elem = root.find("meshes_directory")
            if meshes_elem is not None and meshes_elem.text:
                meshes_path = os.path.normpath(os.path.join(self.project_dir, meshes_elem.text))
                if os.path.exists(meshes_path):
                    data["meshes_dir"] = meshes_path
                    self.meshes_dir = meshes_path
            
            # ノード
            nodes_elem = root.find("nodes")
            if nodes_elem is not None:
                for node_elem in nodes_elem.findall("node"):
                    node_data = self._deserialize_node(node_elem)
                    if node_data:
                        data["nodes"].append(node_data)
            
            # 接続
            connections_elem = root.find("connections")
            if connections_elem is not None:
                for conn_elem in connections_elem.findall("connection"):
                    from_node = conn_elem.find("from_node").text
                    from_port = conn_elem.find("from_port").text
                    to_node = conn_elem.find("to_node").text
                    to_port = conn_elem.find("to_port").text
                    data["connections"].append((from_node, from_port, to_node, to_port))
            
            print(f"Project loaded from: {file_path}")
            return data
            
        except Exception as e:
            print(f"Error loading project: {e}")
            return None
    
    def _serialize_node(self, node: Any) -> ET.Element:
        """ノードを XML 要素にシリアライズ
        
        Args:
            node: ノードオブジェクト
        
        Returns:
            XML Element
        """
        elem = ET.Element("node")
        
        # 基本属性
        ET.SubElement(elem, "name").text = node.name() if hasattr(node, 'name') and callable(node.name) else str(node)
        ET.SubElement(elem, "type").text = node.__class__.__name__
        
        # 位置
        if hasattr(node, 'pos'):
            pos = node.pos()
            ET.SubElement(elem, "position").set("x", str(pos[0]))
            elem.find("position").set("y", str(pos[1]))
        
        # STL ファイル
        if hasattr(node, 'stl_file') and node.stl_file:
            # 相対パスに変換
            try:
                stl_rel = os.path.relpath(node.stl_file, self.project_dir)
                ET.SubElement(elem, "stl_file").text = stl_rel
            except ValueError:
                ET.SubElement(elem, "stl_file").text = node.stl_file
        
        # 物理パラメータ
        if hasattr(node, 'mass_value'):
            ET.SubElement(elem, "mass").text = str(node.mass_value)
        
        if hasattr(node, 'inertia'):
            inertia_elem = ET.SubElement(elem, "inertia")
            for key, value in node.inertia.items():
                inertia_elem.set(key, str(value))
        
        # 色
        if hasattr(node, 'node_color'):
            color_elem = ET.SubElement(elem, "color")
            rgb = node.node_color
            color_elem.set("r", f"{rgb[0]:.3f}")
            color_elem.set("g", f"{rgb[1]:.3f}")
            color_elem.set("b", f"{rgb[2]:.3f}")
        
        # Massless decoration フラグ
        if hasattr(node, 'massless_decoration'):
            ET.SubElement(elem, "massless_decoration").text = str(node.massless_decoration)
        
        return elem
    
    def _deserialize_node(self, elem: ET.Element) -> Optional[Dict]:
        """XML 要素からノードデータを復元
        
        Args:
            elem: XML Element
        
        Returns:
            ノードデータの辞書、失敗時 None
        """
        try:
            data = {}
            
            # 基本属性
            name_elem = elem.find("name")
            if name_elem is not None:
                data["name"] = name_elem.text
            
            type_elem = elem.find("type")
            if type_elem is not None:
                data["type"] = type_elem.text
            
            # 位置
            pos_elem = elem.find("position")
            if pos_elem is not None:
                data["position"] = (
                    float(pos_elem.get("x", "0")),
                    float(pos_elem.get("y", "0"))
                )
            
            # STL ファイル
            stl_elem = elem.find("stl_file")
            if stl_elem is not None and stl_elem.text:
                stl_path = os.path.normpath(os.path.join(self.project_dir, stl_elem.text))
                if os.path.exists(stl_path):
                    data["stl_file"] = stl_path
            
            # 物理パラメータ
            mass_elem = elem.find("mass")
            if mass_elem is not None:
                data["mass"] = float(mass_elem.text or "0.0")
            
            inertia_elem = elem.find("inertia")
            if inertia_elem is not None:
                data["inertia"] = {
                    key: float(value)
                    for key, value in inertia_elem.attrib.items()
                }
            
            # 色
            color_elem = elem.find("color")
            if color_elem is not None:
                data["color"] = (
                    float(color_elem.get("r", "1.0")),
                    float(color_elem.get("g", "1.0")),
                    float(color_elem.get("b", "1.0"))
                )
            
            # Massless decoration
            md_elem = elem.find("massless_decoration")
            if md_elem is not None:
                data["massless_decoration"] = md_elem.text.lower() == "true"
            
            return data
            
        except Exception as e:
            print(f"Error deserializing node: {e}")
            return None
