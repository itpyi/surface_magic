import stim
import src.magic as magic# 假设这是你自定义的库
import sinter
import numpy as np
from typing import List
import math
from stimbposd import SinterDecoder_BPOSD, sinter_decoders


# Constants
T = 6
# T_BEFORE_GROW = 1 # >=1
ERROR_RATE = 1e-5

if __name__ == "__main__":
    tasks = []
    
    # 遍历参数 T_BEFORE_GROW (从 1 到 10)
    for t in range(1, 10):
        # 1. 生成 Circuit (使用当前的 t_maintain)
        circuit = magic.magic_preparation(
            T=T,
            T_lat_surg=3,
            t_round=t,
            error_rate=ERROR_RATE
        )

        # 2. 从该 Circuit 生成 Mask
        # psmask = sinter.post_selection_mask_from_4th_coord(circuit)

        # 3. 添加到任务列表
        tasks.append(
            sinter.Task(
                circuit=circuit,
                # postselection_mask=psmask,
                json_metadata={'time': t, 'p': ERROR_RATE}
            )
        )

    print(f"Starting simulation for {len(tasks)} tasks...")

    # 开始运行
    collected_stats: List[sinter.TaskStats] = sinter.collect(
        num_workers=16,
        tasks=tasks,
        decoders=['bposd'],
        custom_decoders=sinter_decoders(),
        max_shots=1_000_000,
        max_errors=5000,
        print_progress=True, # 在服务器上建议开启，可以看到大概进度
    )

    # 保存结果到 CSV
    output_file = f"sinter_results_sweep_time_bposd_{ERROR_RATE}.csv"
    with open(output_file, 'w') as f:
        print(sinter.CSV_HEADER, file=f)
        for sample in collected_stats:
            print(sample.to_csv_line(), file=f)

    print(f"Results saved to {output_file}")
