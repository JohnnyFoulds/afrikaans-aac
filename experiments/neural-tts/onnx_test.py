"""
ONNX inference test for Simba-TTS-afr using onnxruntime directly.
ORTModelForTextToWaveform is not available in optimum 2.2.0, so we use
the onnxruntime InferenceSession API directly.
"""
import onnxruntime as ort
import numpy as np
from transformers import AutoTokenizer
import scipy.io.wavfile

tokenizer = AutoTokenizer.from_pretrained("UBC-NLP/Simba-TTS-afr")
sess = ort.InferenceSession("experiments/neural-tts/simba-tts-afr-onnx/model.onnx")

text = "Goeie môre, hoe gaan dit?"
inputs = tokenizer(text, return_tensors="np")

ort_inputs = {
    "input_ids": inputs["input_ids"].astype(np.int64),
    "attention_mask": inputs["attention_mask"].astype(np.int64),
}

outputs = sess.run(None, ort_inputs)
waveform = outputs[0]  # shape: [1, T] or [T]
audio = waveform.squeeze().astype(np.float32)
scipy.io.wavfile.write("experiments/neural-tts/onnx_test.wav", rate=16000, data=audio)
print(f"ONNX inference OK, wrote onnx_test.wav ({len(audio)/16000:.1f}s)")
print(f"Waveform shape: {waveform.shape}, dtype: {waveform.dtype}")
