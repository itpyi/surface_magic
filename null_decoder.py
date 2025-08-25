# null_decoder.py
import numpy as np
import stim
import sinter

class NullDecoder(sinter.Decoder):
    def compile_decoder_for_dem(self, dem: stim.DetectorErrorModel):
        num_obs = dem.num_logical_observables
        def decode_batch(dets: np.ndarray) -> np.ndarray:
            return np.zeros((dets.shape[0], num_obs), dtype=np.uint8)
        return decode_batch