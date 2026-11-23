import cv2, os, json, numpy as np

model_path = os.path.join('data', 'models', 'segformer', 'model.onnx')
cfg_path = os.path.join('data', 'models', 'segformer', 'config.json')

with open(cfg_path, 'r') as f:
    cfg = json.load(f)
id2label = {int(k): v for k, v in cfg.get('id2label', {}).items()}

net = cv2.dnn.readNetFromONNX(model_path)

img = cv2.imread(os.path.join('data', 'roomie_default_room.jpg'))
orig_h, orig_w = img.shape[:2]

rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
resized = cv2.resize(rgb, (512, 512)).astype(np.float32) / 255.0
mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
norm = (resized - mean) / std
blob = norm.transpose(2, 0, 1)[np.newaxis, ...]

net.setInput(blob)
logits = net.forward()[0] # (150, 128, 128)

# Upsample logits to original size
logits_full = np.zeros((150, orig_h, orig_w), dtype=np.float32)
for c in range(150):
    logits_full[c] = cv2.resize(logits[c], (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

pred_classes = np.argmax(logits_full, axis=0)

unique, counts = np.unique(pred_classes, return_counts=True)
total_pixels = orig_h * orig_w

print(f'Original image dimensions: {orig_w}x{orig_h}')
print('Detected surfaces and objects:')
for u, count in sorted(zip(unique, counts), key=lambda x: x[1], reverse=True):
    pct = (count / total_pixels) * 100
    if pct > 0.5:
        print(f' - Class {u} ({id2label.get(u, "unknown")}): {pct:.2f}% of room')
