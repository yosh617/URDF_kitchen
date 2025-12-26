"""
URDF Kitchen Studio - Parts Editor 計算処理
既存 urdf_kitchen_PartsEditor.py から計算部分を抽出
"""

import numpy as np
import vtk
import xml.etree.ElementTree as ET
from typing import Dict, List, Tuple, Optional
from pathlib import Path


class PartsCalculator:
    """パーツ定義の計算エンジン（物理パラメータ、慣性テンソル、重心計算）"""
    
    def __init__(self):
        """初期化"""
        self.polydata = None
        self.volume = 0.0
        self.density = 1.0  # デフォルト密度 (kg/m^3)
        self.mass = 0.0
        self.center_of_mass = np.array([0.0, 0.0, 0.0])
        self.inertia_tensor = np.eye(3)
    
    # ========== 物理パラメータ計算 ==========
    
    def set_polydata(self, polydata):
        """VTK PolyData を設定
        
        Args:
            polydata: vtk.vtkPolyData オブジェクト
        """
        self.polydata = polydata
        self._calculate_volume()
    
    def _calculate_volume(self):
        """体積を計算"""
        if self.polydata is None:
            self.volume = 0.0
            return
        
        mass_properties = vtk.vtkMassProperties()
        mass_properties.SetInputData(self.polydata)
        self.volume = mass_properties.GetVolume()
    
    def calculate_from_two_params(self, 
                                   volume: Optional[float] = None,
                                   density: Optional[float] = None,
                                   mass: Optional[float] = None) -> Dict[str, float]:
        """2つのパラメータから残りを計算
        
        Args:
            volume: 体積 (m^3)
            density: 密度 (kg/m^3)
            mass: 質量 (kg)
        
        Returns:
            全パラメータの辞書 {"volume": ..., "density": ..., "mass": ...}
        """
        result = {}
        
        # 体積が指定されていない場合は STL から計算
        if volume is None and self.polydata is not None:
            volume = self.volume
        
        # 2つの値から3つ目を計算
        if volume is not None and density is not None:
            result["volume"] = volume
            result["density"] = density
            result["mass"] = volume * density
        elif volume is not None and mass is not None:
            result["volume"] = volume
            result["mass"] = mass
            result["density"] = mass / volume if volume > 0 else 0.0
        elif density is not None and mass is not None:
            result["density"] = density
            result["mass"] = mass
            result["volume"] = mass / density if density > 0 else 0.0
        else:
            # 値が不足している場合はデフォルト値を使用
            result["volume"] = volume or self.volume
            result["density"] = density or self.density
            result["mass"] = mass or (result["volume"] * result["density"])
        
        # 内部状態を更新
        self.volume = result.get("volume", self.volume)
        self.density = result.get("density", self.density)
        self.mass = result.get("mass", self.mass)
        
        return result
    
    def calculate_center_of_mass(self, manual_com: Optional[List[float]] = None) -> np.ndarray:
        """重心を計算
        
        Args:
            manual_com: 手動指定の重心座標 [x, y, z]。None の場合は STL から計算
        
        Returns:
            重心座標 np.array([x, y, z])
        """
        if manual_com is not None:
            self.center_of_mass = np.array(manual_com)
        elif self.polydata is not None:
            com_filter = vtk.vtkCenterOfMass()
            com_filter.SetInputData(self.polydata)
            com_filter.SetUseScalarsAsWeights(False)
            com_filter.Update()
            self.center_of_mass = np.array(com_filter.GetCenter())
        else:
            self.center_of_mass = np.array([0.0, 0.0, 0.0])
        
        return self.center_of_mass
    
    def calculate_inertia_tensor(self, 
                                  mass: Optional[float] = None,
                                  center_of_mass: Optional[np.ndarray] = None) -> np.ndarray:
        """慣性テンソルを計算
        
        Args:
            mass: 質量。None の場合は内部状態を使用
            center_of_mass: 重心座標。None の場合は内部状態を使用
        
        Returns:
            3x3 慣性テンソル行列
        """
        if self.polydata is None:
            return np.eye(3)
        
        if mass is None:
            mass = self.mass
        if center_of_mass is None:
            center_of_mass = self.center_of_mass
        
        # ポリゴンの各頂点から慣性を計算
        points = self.polydata.GetPoints()
        num_points = points.GetNumberOfPoints()
        
        if num_points == 0:
            return np.eye(3)
        
        # 各点の質量（均等分布と仮定）
        point_mass = mass / num_points
        
        # 慣性テンソルの初期化
        inertia = np.zeros((3, 3))
        
        for i in range(num_points):
            point = np.array(points.GetPoint(i))
            # 重心からの相対位置
            r = point - center_of_mass
            
            # 慣性テンソルの成分計算
            r_squared = np.dot(r, r)
            inertia += point_mass * (r_squared * np.eye(3) - np.outer(r, r))
        
        self.inertia_tensor = inertia
        return inertia
    
    def get_bounding_box_inertia(self, mass: float) -> np.ndarray:
        """バウンディングボックスを使った簡易慣性計算（高速）
        
        Args:
            mass: 質量
        
        Returns:
            3x3 慣性テンソル（対角行列）
        """
        if self.polydata is None:
            return np.eye(3)
        
        bounds = self.polydata.GetBounds()
        dx = bounds[1] - bounds[0]
        dy = bounds[3] - bounds[2]
        dz = bounds[5] - bounds[4]
        
        # 直方体の慣性モーメント
        ixx = (1.0/12.0) * mass * (dy**2 + dz**2)
        iyy = (1.0/12.0) * mass * (dx**2 + dz**2)
        izz = (1.0/12.0) * mass * (dx**2 + dy**2)
        
        inertia = np.diag([ixx, iyy, izz])
        return inertia


class XMLGenerator:
    """パーツ定義 XML の生成・読み込み"""
    
    def __init__(self):
        """初期化"""
        pass
    
    def create_part_xml(self,
                       stl_file: str,
                       points: Dict[str, List[float]],
                       properties: Dict[str, float],
                       color: Optional[Tuple[float, float, float, float]] = None) -> ET.Element:
        """パーツ定義 XML を生成
        
        Args:
            stl_file: STL ファイルパス
            points: 接続点の辞書 {"point1": [x, y, z], "point2": [...], ...}
            properties: 物理パラメータ {"mass": ..., "volume": ..., "density": ..., ...}
            color: RGBA色 (r, g, b, a) (0.0-1.0)
        
        Returns:
            XML Element
        """
        root = ET.Element("part")
        
        # STL ファイル
        stl_elem = ET.SubElement(root, "stl")
        stl_elem.set("file", stl_file)
        
        # 接続点
        points_elem = ET.SubElement(root, "points")
        for point_name, coords in points.items():
            point_elem = ET.SubElement(points_elem, "point")
            point_elem.set("name", point_name)
            point_elem.set("x", f"{coords[0]:.6f}")
            point_elem.set("y", f"{coords[1]:.6f}")
            point_elem.set("z", f"{coords[2]:.6f}")
        
        # 物理パラメータ
        props_elem = ET.SubElement(root, "properties")
        
        if "mass" in properties:
            mass_elem = ET.SubElement(props_elem, "mass")
            mass_elem.text = f"{properties['mass']:.12f}"
        
        if "volume" in properties:
            vol_elem = ET.SubElement(props_elem, "volume")
            vol_elem.text = f"{properties['volume']:.12f}"
        
        if "density" in properties:
            dens_elem = ET.SubElement(props_elem, "density")
            dens_elem.text = f"{properties['density']:.12f}"
        
        if "center_of_mass" in properties:
            com = properties["center_of_mass"]
            com_elem = ET.SubElement(props_elem, "center_of_mass")
            com_elem.set("x", f"{com[0]:.6f}")
            com_elem.set("y", f"{com[1]:.6f}")
            com_elem.set("z", f"{com[2]:.6f}")
        
        if "inertia" in properties:
            inertia = properties["inertia"]
            inertia_elem = ET.SubElement(props_elem, "inertia")
            inertia_elem.set("ixx", f"{inertia[0, 0]:.12f}")
            inertia_elem.set("ixy", f"{inertia[0, 1]:.12f}")
            inertia_elem.set("ixz", f"{inertia[0, 2]:.12f}")
            inertia_elem.set("iyy", f"{inertia[1, 1]:.12f}")
            inertia_elem.set("iyz", f"{inertia[1, 2]:.12f}")
            inertia_elem.set("izz", f"{inertia[2, 2]:.12f}")
        
        # 色
        if color is not None:
            color_elem = ET.SubElement(root, "color")
            color_elem.set("r", f"{color[0]:.3f}")
            color_elem.set("g", f"{color[1]:.3f}")
            color_elem.set("b", f"{color[2]:.3f}")
            color_elem.set("a", f"{color[3]:.3f}")
        
        return root
    
    def save_xml(self, root: ET.Element, file_path: str) -> bool:
        """XML をファイルに保存
        
        Args:
            root: XML Element
            file_path: 保存先パス
        
        Returns:
            成功時 True、失敗時 False
        """
        try:
            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(file_path, encoding="utf-8", xml_declaration=True)
            return True
        except Exception as e:
            print(f"Error saving XML: {e}")
            return False
    
    def load_xml(self, file_path: str) -> Optional[Dict]:
        """XML ファイルを読み込み
        
        Args:
            file_path: XML ファイルパス
        
        Returns:
            パースしたデータの辞書、失敗時 None
        """
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            
            data = {
                "stl_file": "",
                "points": {},
                "properties": {},
                "color": None
            }
            
            # STL ファイル
            stl_elem = root.find("stl")
            if stl_elem is not None:
                data["stl_file"] = stl_elem.get("file", "")
            
            # 接続点
            points_elem = root.find("points")
            if points_elem is not None:
                for point_elem in points_elem.findall("point"):
                    name = point_elem.get("name", "")
                    x = float(point_elem.get("x", "0.0"))
                    y = float(point_elem.get("y", "0.0"))
                    z = float(point_elem.get("z", "0.0"))
                    data["points"][name] = [x, y, z]
            
            # 物理パラメータ
            props_elem = root.find("properties")
            if props_elem is not None:
                mass_elem = props_elem.find("mass")
                if mass_elem is not None:
                    data["properties"]["mass"] = float(mass_elem.text or "0.0")
                
                vol_elem = props_elem.find("volume")
                if vol_elem is not None:
                    data["properties"]["volume"] = float(vol_elem.text or "0.0")
                
                dens_elem = props_elem.find("density")
                if dens_elem is not None:
                    data["properties"]["density"] = float(dens_elem.text or "0.0")
                
                com_elem = props_elem.find("center_of_mass")
                if com_elem is not None:
                    data["properties"]["center_of_mass"] = [
                        float(com_elem.get("x", "0.0")),
                        float(com_elem.get("y", "0.0")),
                        float(com_elem.get("z", "0.0"))
                    ]
                
                inertia_elem = props_elem.find("inertia")
                if inertia_elem is not None:
                    data["properties"]["inertia"] = np.array([
                        [float(inertia_elem.get("ixx", "0.0")), 
                         float(inertia_elem.get("ixy", "0.0")), 
                         float(inertia_elem.get("ixz", "0.0"))],
                        [float(inertia_elem.get("ixy", "0.0")), 
                         float(inertia_elem.get("iyy", "0.0")), 
                         float(inertia_elem.get("iyz", "0.0"))],
                        [float(inertia_elem.get("ixz", "0.0")), 
                         float(inertia_elem.get("iyz", "0.0")), 
                         float(inertia_elem.get("izz", "0.0"))]
                    ])
            
            # 色
            color_elem = root.find("color")
            if color_elem is not None:
                data["color"] = (
                    float(color_elem.get("r", "1.0")),
                    float(color_elem.get("g", "1.0")),
                    float(color_elem.get("b", "1.0")),
                    float(color_elem.get("a", "1.0"))
                )
            
            return data
        except Exception as e:
            print(f"Error loading XML: {e}")
            return None
