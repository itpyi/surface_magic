import stim
import src.magic as magic# 假设这是你自定义的库
import sinter
import numpy as np
from typing import List
import math



if __name__ == "__main__":
    
    # 遍历参数 T_BEFORE_GROW (从 1 到 10)
    for logerr in np.linspace(-4, -3, 10):
        err = 10**logerr
        for t in [1,2]:
            # 1. 生成 Circuit (使用当前的 t_maintain)
            circuit = magic.magic_preparation(
                T=1,
                T_lat_surg=3,
                t_round=t,
                error_rate=err
            )

            # 2. Generate dem
            dem = circuit.detector_error_model()

            # 3. Print the DEM
            dem_filename = f"ip_decoder/dem/dem_T{t}_err{logerr:.2f}.dem"
            with open(dem_filename, "w") as f:
                f.write(str(dem))  