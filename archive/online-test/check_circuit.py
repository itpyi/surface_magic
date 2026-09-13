import src.magic as magic
import stim
import sys
import os

def check_dem_dist_errors(dem):
    """
    一步到位检查 Distance=1 (纯L0) 和 Distance=2 (仅相差L0) 的错误。
    修复了 L0 L0 互相抵消导致的误报问题，并过滤掉无意义的 ^ 符号。
    """
    import re
    
    # 存储格式: normalized_detectors -> has_logical_flip
    # normalized_detectors 是一个排序后的 detector tuple (如 ('D0', 'D1'))
    # has_logical_flip 是布尔值，True 表示 L0 出现奇数次
    error_map = {}
    
    # 1. 解析 DEM
    for line in str(dem).splitlines():
        line = line.strip()
        if line.startswith("error("):
            m = re.match(r"error\([^\)]+\)\s+(.*)", line)
            if m:
                raw_items = m.group(1).split()
                
                detectors = []
                l0_count = 0
                
                for item in raw_items:
                    if item == "^":
                        continue # 忽略格式符
                    elif item == "L0":
                        l0_count += 1
                    elif item.startswith("D"):
                        detectors.append(item)
                
                # 标准化 detector 组合
                det_key = tuple(sorted(detectors))
                #如果在二进制下，L0 出现偶数次等于没出现
                is_logical_flipped = (l0_count % 2 == 1)
                
                # 我们只关心存在的错误形式
                # 如果同一个 detector 组合既以 "flipped" 出现，又以 "not flipped" 出现，
                # 说明存在 distance 2 的错误。
                
                # 记录该 detector 组合目前见过的逻辑状态
                if det_key not in error_map:
                    error_map[det_key] = set()
                error_map[det_key].add(is_logical_flipped)
    d1_errors = []
    d2_pairs = []
    for detectors, states in error_map.items():
        # 检查 Distance = 1:
        # 如果 detectors 为空 (没有触发探测器)，且状态为 True (有逻辑翻转)
        if len(detectors) == 0 and True in states:
            d1_errors.append("Pure L0 error (undetected)")
            
        # 检查 Distance = 2:
        # 如果同一个 detector 组合，既有 True (翻转) 又有 False (未翻转) 的情况
        if True in states and False in states:
            d2_pairs.append((detectors, tuple(list(detectors) + ["L0"])))
    return d1_errors, d2_pairs

T_SC_PRE=0 # >=0
T_LAT_SURG=3 # should be at least 3
T_BEFORE_GROW=1 # should be at least 1 to read out the combined X check

if __name__ == "__main__":
    # 1. 生成线路
    print("Generating circuit...")
    circuit = magic.magic_preparation(
        T=6,
        T_lat_surg=T_LAT_SURG,
        t_round=8,
        error_rate=0.001
    )

    dgm = str(circuit.diagram('timeline-svg'))
    with open('magic_preparation_circuit.svg', 'w') as f:
        f.write(dgm)
    print(">> Circuit diagram saved to magic_preparation_circuit.svg")

    # 2. 构造 DEM 并检查是否有不确定的 detectors/observables
    print("Constructing Detector Error Model (DEM)...")
    try:
        # decompose_errors=True 有助于将复合错误拆分，使分析更准确
        dem = circuit.detector_error_model(decompose_errors=True)
        print(">> Success: DEM constructed.")
    except Exception as e:
        print(f">> Error: Failed to construct DEM. The circuit may have non-deterministic detectors or observables without noise.")
        print(f"Details: {e}")
        sys.exit(1)

    # 3. 检查 Distance <= 1 (是否存在纯 L0 错误)
    print("Checking for Distance 1 or 2 errors...")
    d1_errors, d2_pairs = check_dem_dist_errors(dem)

    # 5. 输出最终结果
    if d1_errors or d2_pairs:
        print(">> FAIL: Potential logical errors found (Distance < 3).")
        # 1. 确保目录存在
        save_dir = '../debug'
        os.makedirs(save_dir, exist_ok=True)
        
        # 2. 构造带参数的文件名 (例如: dem_fail_Pre0_Lat3_Bef1_Ps0_Main5.dem)
        file_name = (
            f"dem_fail_"
            f"Pre{T_SC_PRE}_"
            f"Lat{T_LAT_SURG}_"
            f"Bef{T_BEFORE_GROW}_"
            f".dem"
        )
        
        save_path = os.path.join(save_dir, file_name)
        
        # 3. 保存文件
        dem.to_file(save_path)
        print(f">> Debug: Failed DEM saved to: {save_path}")

        if d1_errors:
            print(f"\n[Distance 1 Errors Found] ({len(d1_errors)} items):")
            for err in d1_errors:
                print(f"  {err}")
        
        if d2_pairs:
            print(f"\n[Distance 2 Error Pairs Found] ({len(d2_pairs)} pairs):")
            for pair in d2_pairs:
                print(f"  {pair[0]} <---> {pair[1]}")
    else:
        print("\n>> PASSED: No distance 1 or 2 errors found. Distance >= 3.")