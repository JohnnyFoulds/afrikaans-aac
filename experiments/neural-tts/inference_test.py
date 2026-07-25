from transformers import VitsModel, AutoTokenizer
import torch, scipy.io.wavfile, numpy as np
import os

os.makedirs("experiments/neural-tts", exist_ok=True)

model = VitsModel.from_pretrained("UBC-NLP/Simba-TTS-afr")
tokenizer = AutoTokenizer.from_pretrained("UBC-NLP/Simba-TTS-afr")

test_phrases = [
    "Goeie môre, hoe gaan dit met jou?",
    "Ek wil graag water hê.",
    "Dankie vir jou hulp.",
    "Ek is honger.",
    "Bel asseblief die dokter.",
]

model.eval()
for phrase in test_phrases:
    inputs = tokenizer(phrase, return_tensors="pt")
    with torch.no_grad():
        output = model(**inputs).waveform
    audio = output.squeeze().numpy()
    filename = f"experiments/neural-tts/{phrase[:20].replace(' ','_').replace(',','').replace('?','').replace('.','')}.wav"
    scipy.io.wavfile.write(filename, rate=model.config.sampling_rate, data=audio.astype(np.float32))
    print(f"Wrote {filename} ({len(audio)/model.config.sampling_rate:.1f}s)")

print(f"Sampling rate: {model.config.sampling_rate} Hz")
print("Inference test complete.")
