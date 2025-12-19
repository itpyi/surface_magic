import stim
import src.magic as magic# 假设这是你自定义的库
import sinter
import numpy as np
from typing import List

# Constants
T_SC_PRE = 1
T_LAT_SURG = 3
T_BEFORE_GROW = 1
# T_PS_GROW = 2
T_MAINTAIN = 0
ERROR_RATE = 0.001

if __name__ == "__main__":
    tasks = []
    
    # 遍历参数 T_MAINTAIN (从 0 到 10)
    for t_ps_grow in range(0, 10):
        # 1. 生成 Circuit (使用当前的 t_maintain)
        circuit = magic.magic_preparation(
            T_sc_pre=T_SC_PRE,
            T_lat_surg=T_LAT_SURG,
            T_before_grow=T_BEFORE_GROW,
            T_ps_grow=t_ps_grow,
            T_maintain=T_MAINTAIN,  # 注意这里使用循环变量
            error_rate=ERROR_RATE
        )

        # 2. 从该 Circuit 生成 Mask
        psmask = sinter.post_selection_mask_from_4th_coord(circuit)

        # 3. 添加到任务列表
        tasks.append(
            sinter.Task(
                circuit=circuit,
                postselection_mask=psmask,
                json_metadata={'T_PS_GROW': t_ps_grow, 'p': ERROR_RATE}
            )
        )

    print(f"Starting simulation for {len(tasks)} tasks...")

    # 开始运行
    collected_stats: List[sinter.TaskStats] = sinter.collect(
        num_workers=16,
        tasks=tasks,
        decoders=['pymatching'],
        max_shots=100_000_000,
        max_errors=5000,
        print_progress=True, # 在服务器上建议开启，可以看到大概进度
    )

    # 保存结果到 CSV
    output_file = "sinter_results_sweep_ps.csv"
    with open(output_file, 'w') as f:
        print(sinter.CSV_HEADER, file=f)
        for sample in collected_stats:
            print(sample.to_csv_line(), file=f)

    print(f"Results saved to {output_file}")
