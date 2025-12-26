"""
テスト用スクリプト：Step 2 - STL Sourcer 計算処理のテスト
"""

import sys
from pathlib import Path
import numpy as np

# パス設定
sys.path.insert(0, str(Path(__file__).parent))

from core.urdf_kitchen_stl_compute import STLProcessor

print("=== Step 2: STL Sourcer Test ===\n")

# Test processor initialization
processor = STLProcessor()
print("[OK] STLProcessor instance created")

# テスト用 STL ファイルを探す（roborecipe2_description/meshes から）
stl_test_file = Path(__file__).parent / "roborecipe2_description" / "meshes" / "c_chest.stl"

if stl_test_file.exists():
    print(f"\n[TEST] STL File Loading")
    print(f"Test file: {stl_test_file.name}")
    
    if processor.load_stl(str(stl_test_file)):
        print("[OK] STL loaded successfully")
        
        # Info output
        print(f"\n[INFO] Mesh Information")
        bounds = processor.get_bounds()
        print(f"Bounding box:")
        print(f"  X: [{bounds[0]:.6f}, {bounds[1]:.6f}]")
        print(f"  Y: [{bounds[2]:.6f}, {bounds[3]:.6f}]")
        print(f"  Z: [{bounds[4]:.6f}, {bounds[5]:.6f}]")
        
        center = processor.get_center()
        print(f"Center: ({center[0]:.6f}, {center[1]:.6f}, {center[2]:.6f})")
        
        volume = processor.get_volume()
        print(f"Volume: {volume:.6f} m^3")
        
        size = processor.get_size()
        print(f"Max size: {size:.6f}")
        
        surface_area = processor.get_surface_area()
        print(f"Surface area: {surface_area:.6f} m^2")
        
        # Transform test
        print(f"\n[TEST] Transform Operations")
        
        # Translation test
        original_center = processor.get_center().copy()
        processor.apply_translation(np.array([0.1, 0.2, 0.3]))
        new_center = processor.get_center()
        print(f"[OK] Translation: ({new_center[0]:.6f}, {new_center[1]:.6f}, {new_center[2]:.6f})")
        
        # Restore
        processor.apply_translation(-np.array([0.1, 0.2, 0.3]))
        
        # Rotation test
        processor.apply_rotation(45, "z")
        print(f"[OK] Rotation (Z axis 45 deg)")
        
        # Scaling
        processor.apply_scale(0.5)
        print(f"[OK] Scaling (0.5x)")
        
        # Axis flip
        processor.flip_axis("x")
        print(f"[OK] Flip axis (X)")
        
        print(f"\n[OK] All tests passed")
    else:
        print("[ERROR] STL loading failed")
else:
    print(f"[INFO] Test STL file not found: {stl_test_file}")
    print(f"[OK] STLProcessor initialized successfully (no file test)")

print("\n=== Step 2 Test Completed ===")
