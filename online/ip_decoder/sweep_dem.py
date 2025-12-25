import stim
import pymatching
import numpy as np

# 这里定义你需要运行的p值列表，请根据实际文件名修改
p_list = np.linspace(-2.5, -3.0, 6)  # 对应于 dem_T1_err-3.0.dem 到 dem_T1_err-2.5.dem
num_shots = 1_000_000

error_list = []
shot_list = []

for p in p_list:
    # 1. 读取 detector error model
    file_path = f"ip_decoder/dem/dem_T7_err{p}.dem"
    dem = stim.DetectorErrorModel.from_file(file_path)

    # 2. 配置 sampler 和 decoder
    sampler = dem.compile_sampler()
    matcher = pymatching.Matching.from_detector_error_model(dem)

    # 3. 使用 stim 运行 sampling
    # separate_observables=True 会分别返回 detectors (用于解码) 和 observables (用于验证)
    detectors, actual_observables, _ = sampler.sample(shots=num_shots)

    # 4. 使用 pymatching 解码
    predicted_observables = matcher.decode_batch(detectors)

    # 5. 统计错误
    # 如果预测的 observable 与实际采样的 observable 不一致，则视为发生逻辑错误
    # axis=1 用于处理多 observable 的情况，只要有一个 observable 错即为错
    num_errors = np.sum(np.any(predicted_observables != actual_observables, axis=1))

    error_list.append(num_errors)
    shot_list.append(num_shots)

print("Error List:", error_list)
print("Total Shots:", shot_list)

