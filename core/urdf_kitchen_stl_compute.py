"""
URDF Kitchen Studio - STL Sourcer 計算処理
既存 urdf_kitchen_StlSourcer.py から計算部分を抽出
"""

import numpy as np
import vtk
from typing import List, Tuple, Optional


class STLProcessor:
    """STL メッシュ処理の計算エンジン"""
    
    def __init__(self):
        """初期化"""
        self.polydata = None
        self.bounds = None
        self.volume = 0.0
        self.center = None
    
    # ========== ファイル I/O ==========
    
    def load_stl(self, file_path: str) -> bool:
        """STL ファイルを読み込む
        
        Args:
            file_path: STL ファイルのパス
        
        Returns:
            成功時 True、失敗時 False
        """
        try:
            reader = vtk.vtkSTLReader()
            reader.SetFileName(file_path)
            reader.Update()
            
            # メッシュのクリーンアップ
            clean = vtk.vtkCleanPolyData()
            clean.SetInputConnection(reader.GetOutputPort())
            clean.SetTolerance(1e-5)
            clean.ConvertPolysToLinesOff()
            clean.ConvertStripsToPolysOff()
            clean.PointMergingOn()
            clean.Update()
            
            # デシメーション（簡略化）
            remover = vtk.vtkDecimatePro()
            remover.SetInputConnection(clean.GetOutputPort())
            remover.SetTargetReduction(0.0)
            remover.PreserveTopologyOn()
            remover.Update()
            
            # 三角形フィルター
            triangulate = vtk.vtkTriangleFilter()
            triangulate.SetInputConnection(remover.GetOutputPort())
            triangulate.Update()
            
            self.polydata = triangulate.GetOutput()
            self.bounds = self.polydata.GetBounds()
            
            # 体積計算
            mass_properties = vtk.vtkMassProperties()
            mass_properties.SetInputData(self.polydata)
            self.volume = mass_properties.GetVolume()
            
            # 中心計算
            self.center = self._calculate_center()
            
            return True
        except Exception as e:
            print(f"Error loading STL: {e}")
            return False
    
    def save_stl(self, file_path: str) -> bool:
        """STL ファイルを保存
        
        Args:
            file_path: 保存先ファイルパス
        
        Returns:
            成功時 True、失敗時 False
        """
        if self.polydata is None:
            print("No polydata to save")
            return False
        
        try:
            writer = vtk.vtkSTLWriter()
            writer.SetFileName(file_path)
            writer.SetInputData(self.polydata)
            writer.Write()
            return True
        except Exception as e:
            print(f"Error saving STL: {e}")
            return False
    
    # ========== 計算・変換処理 ==========
    
    def _calculate_center(self) -> np.ndarray:
        """ポリゴンの中心座標を計算"""
        if self.polydata is None:
            return np.array([0, 0, 0])
        
        bounds = self.polydata.GetBounds()
        center = np.array([
            (bounds[0] + bounds[1]) / 2,
            (bounds[2] + bounds[3]) / 2,
            (bounds[4] + bounds[5]) / 2
        ])
        return center
    
    def get_bounds(self) -> Tuple[float, float, float, float, float, float]:
        """バウンディングボックスを取得
        
        Returns:
            (xmin, xmax, ymin, ymax, zmin, zmax)
        """
        if self.bounds is None:
            return (0, 0, 0, 0, 0, 0)
        return self.bounds
    
    def get_center(self) -> np.ndarray:
        """中心座標を取得"""
        if self.center is None:
            self.center = self._calculate_center()
        return self.center
    
    def get_volume(self) -> float:
        """体積を取得（m^3）"""
        return self.volume
    
    def get_size(self) -> float:
        """最大サイズを取得"""
        if self.bounds is None:
            return 0.0
        
        size = max([
            self.bounds[1] - self.bounds[0],
            self.bounds[3] - self.bounds[2],
            self.bounds[5] - self.bounds[4]
        ])
        return size
    
    # ========== 座標変換 ==========
    
    def transform_to_origin(self, origin: List[float]) -> bool:
        """STL を指定原点に移動
        
        Args:
            origin: 移動先原点 [x, y, z]
        
        Returns:
            成功時 True、失敗時 False
        """
        if self.polydata is None:
            return False
        
        try:
            current_center = self.get_center()
            translation = np.array(origin) - current_center
            
            return self.apply_translation(translation)
        except Exception as e:
            print(f"Error transforming to origin: {e}")
            return False
    
    def apply_translation(self, translation: np.ndarray) -> bool:
        """並進変換を適用
        
        Args:
            translation: [tx, ty, tz]
        
        Returns:
            成功時 True、失敗時 False
        """
        if self.polydata is None:
            return False
        
        try:
            transform = vtk.vtkTransform()
            transform.Translate(translation[0], translation[1], translation[2])
            
            filter_obj = vtk.vtkTransformPolyDataFilter()
            filter_obj.SetTransform(transform)
            filter_obj.SetInputData(self.polydata)
            filter_obj.Update()
            
            self.polydata = filter_obj.GetOutput()
            self.bounds = self.polydata.GetBounds()
            self.center = self._calculate_center()
            
            return True
        except Exception as e:
            print(f"Error applying translation: {e}")
            return False
    
    def apply_rotation(self, angle: float, axis: str) -> bool:
        """回転変換を適用
        
        Args:
            angle: 回転角度（度）
            axis: 回転軸 ("x", "y", "z")
        
        Returns:
            成功時 True、失敗時 False
        """
        if self.polydata is None:
            return False
        
        try:
            center = self.get_center()
            
            transform = vtk.vtkTransform()
            transform.PostMultiply()
            
            # 中心を原点に移動
            transform.Translate(-center[0], -center[1], -center[2])
            
            # 回転
            if axis.lower() == "x":
                transform.RotateX(angle)
            elif axis.lower() == "y":
                transform.RotateY(angle)
            elif axis.lower() == "z":
                transform.RotateZ(angle)
            else:
                print(f"Invalid axis: {axis}")
                return False
            
            # 元の位置に戻す
            transform.Translate(center[0], center[1], center[2])
            
            filter_obj = vtk.vtkTransformPolyDataFilter()
            filter_obj.SetTransform(transform)
            filter_obj.SetInputData(self.polydata)
            filter_obj.Update()
            
            self.polydata = filter_obj.GetOutput()
            self.bounds = self.polydata.GetBounds()
            self.center = self._calculate_center()
            
            return True
        except Exception as e:
            print(f"Error applying rotation: {e}")
            return False
    
    def apply_scale(self, scale: float) -> bool:
        """スケーリングを適用
        
        Args:
            scale: スケール値（1.0 = 原寸）
        
        Returns:
            成功時 True、失敗時 False
        """
        if self.polydata is None:
            return False
        
        try:
            center = self.get_center()
            
            transform = vtk.vtkTransform()
            transform.PostMultiply()
            
            # 中心を原点に移動
            transform.Translate(-center[0], -center[1], -center[2])
            
            # スケーリング
            transform.Scale(scale, scale, scale)
            
            # 元の位置に戻す
            transform.Translate(center[0], center[1], center[2])
            
            filter_obj = vtk.vtkTransformPolyDataFilter()
            filter_obj.SetTransform(transform)
            filter_obj.SetInputData(self.polydata)
            filter_obj.Update()
            
            self.polydata = filter_obj.GetOutput()
            self.bounds = self.polydata.GetBounds()
            self.volume *= (scale ** 3)  # 体積もスケール
            self.center = self._calculate_center()
            
            return True
        except Exception as e:
            print(f"Error applying scale: {e}")
            return False
    
    def apply_arbitrary_transform(self, matrix: np.ndarray) -> bool:
        """任意の 4x4 変換行列を適用
        
        Args:
            matrix: 4x4 変換行列
        
        Returns:
            成功時 True、失敗時 False
        """
        if self.polydata is None:
            return False
        
        try:
            transform = vtk.vtkTransform()
            vtk_matrix = transform.GetMatrix()
            
            for i in range(4):
                for j in range(4):
                    vtk_matrix.SetElement(i, j, matrix[i, j])
            
            filter_obj = vtk.vtkTransformPolyDataFilter()
            filter_obj.SetTransform(transform)
            filter_obj.SetInputData(self.polydata)
            filter_obj.Update()
            
            self.polydata = filter_obj.GetOutput()
            self.bounds = self.polydata.GetBounds()
            self.center = self._calculate_center()
            
            return True
        except Exception as e:
            print(f"Error applying arbitrary transform: {e}")
            return False
    
    # ========== 反転処理 ==========
    
    def flip_axis(self, axis: str) -> bool:
        """指定軸を反転
        
        Args:
            axis: 反転軸 ("x", "y", "z")
        
        Returns:
            成功時 True、失敗時 False
        """
        if self.polydata is None:
            return False
        
        try:
            center = self.get_center()
            
            transform = vtk.vtkTransform()
            transform.PostMultiply()
            
            # 中心を原点に移動
            transform.Translate(-center[0], -center[1], -center[2])
            
            # 反転
            if axis.lower() == "x":
                transform.Scale(-1, 1, 1)
            elif axis.lower() == "y":
                transform.Scale(1, -1, 1)
            elif axis.lower() == "z":
                transform.Scale(1, 1, -1)
            else:
                print(f"Invalid axis: {axis}")
                return False
            
            # 元の位置に戻す
            transform.Translate(center[0], center[1], center[2])
            
            filter_obj = vtk.vtkTransformPolyDataFilter()
            filter_obj.SetTransform(transform)
            filter_obj.SetInputData(self.polydata)
            filter_obj.Update()
            
            self.polydata = filter_obj.GetOutput()
            self.bounds = self.polydata.GetBounds()
            self.center = self._calculate_center()
            
            return True
        except Exception as e:
            print(f"Error flipping axis: {e}")
            return False
    
    # ========== 法線・表面情報 ==========
    
    def get_surface_area(self) -> float:
        """表面積を計算
        
        Returns:
            表面積（m^2）
        """
        if self.polydata is None:
            return 0.0
        
        try:
            mass_properties = vtk.vtkMassProperties()
            mass_properties.SetInputData(self.polydata)
            return mass_properties.GetSurfaceArea()
        except:
            return 0.0
    
    def get_normal_vector(self) -> Optional[np.ndarray]:
        """主要な法線ベクトルを計算
        
        Returns:
            法線ベクトル、計算失敗時 None
        """
        if self.polydata is None:
            return None
        
        try:
            # 法線の計算
            normals = vtk.vtkPolyDataNormals()
            normals.SetInputData(self.polydata)
            normals.Update()
            
            polydata_with_normals = normals.GetOutput()
            normal_array = polydata_with_normals.GetCellData().GetNormals()
            
            if normal_array is None or normal_array.GetNumberOfTuples() == 0:
                return None
            
            # 最初のセルの法線を取得
            normal = np.array([
                normal_array.GetValue(0),
                normal_array.GetValue(1),
                normal_array.GetValue(2)
            ])
            
            return normal / np.linalg.norm(normal)
        except Exception as e:
            print(f"Error computing normal: {e}")
            return None
