import os
import cv2
import numpy as np
import easyocr
from ultralytics import YOLO

def run_diagnostics(image_path, model_path):
    print("=== OMR Diagnostics ===")
    print(f"Image: {image_path}")
    print(f"Model: {model_path}")
    
    # 1. Load Image
    img = cv2.imread(image_path)
    if img is None:
        print("ERROR: Could not load image.")
        return
    h, w, c = img.shape
    print(f"Image Shape: {w}x{h} ({c} channels)")
    
    # 2. Run EasyOCR
    print("Running EasyOCR...")
    reader = easyocr.Reader(['en'], gpu=True)
    img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    ocr_results = reader.readtext(img_gray)
    print(f"EasyOCR found {len(ocr_results)} text regions.")
    
    numeric_detections = []
    for bbox, text, conf in ocr_results:
        clean_text = "".join([char for char in text if char.isdigit()])
        if clean_text:
            pts = np.array(bbox, dtype=np.int32)
            cx = int(np.mean(pts[:, 0]))
            cy = int(np.mean(pts[:, 1]))
            numeric_detections.append((int(clean_text), cx, cy, text))
            
    print(f"Numeric OCR Detections ({len(numeric_detections)}):")
    # Print first 20 numeric detections sorted by Y coordinate
    numeric_detections.sort(key=lambda x: x[2])
    for val, cx, cy, raw_text in numeric_detections[:30]:
        print(f"  Text: '{raw_text}' -> Val: {val} at ({cx}, {cy})")
        
    # 3. Run YOLOv8
    print("\nRunning YOLOv8...")
    if os.path.exists(model_path):
        model = YOLO(model_path)
        yolo_results = model.predict(source=image_path, conf=0.3, verbose=False)
        filled_circles = []
        for result in yolo_results:
            for box in result.boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x0, y0, x1, y1 = map(int, xyxy)
                cx = (x0 + x1) // 2
                cy = (y0 + y1) // 2
                filled_circles.append((cx, cy, float(box.conf[0].cpu().numpy())))
                
        print(f"YOLOv8 found {len(filled_circles)} filled circles.")
        filled_circles.sort(key=lambda x: x[1])
        for cx, cy, conf in filled_circles[:20]:
            print(f"  Filled circle at ({cx}, {cy}) with conf {conf:.2f}")
    else:
        print("ERROR: YOLOv8 model weights not found.")

if __name__ == "__main__":
    image_path = r"C:\Users\vjaga\Downloads\d ans.jpeg"
    model_path = r"C:\Users\vjaga\Downloads\omr test\best.pt"
    run_diagnostics(image_path, model_path)
