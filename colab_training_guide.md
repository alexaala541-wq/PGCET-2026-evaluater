# Google Colab YOLOv8 OMR Training Guide

This guide contains copy-pasteable cells for Google Colab to train a high-accuracy YOLOv8 model on your custom OMR dataset.

---

### Step 1: Open Google Colab
1. Go to [Google Colab](https://colab.research.google.com/).
2. Click **New Notebook**.
3. In the menu, go to **Runtime > Change runtime type**, select **T4 GPU** (or any available GPU), and click **Save**. This ensures your model trains in seconds.

---

### Step 2: Copy and Run the Cells

#### Cell 1: Mount Google Drive
This connects your Google Drive containing the zipped dataset (`omr reader.yolov8.zip`) to the Colab environment.

```python
from google.colab import drive
drive.mount('/content/drive')
```

---

#### Cell 2: Unzip the OMR Dataset
This unzips the dataset folder directly to the local Colab temporary storage (`/content/dataset`) for faster file access during training.

```python
import zipfile
import os

# Update this path if your zip file is located in a specific folder on Drive
zip_path = '/content/drive/MyDrive/omr reader.yolov8.zip'
extract_path = '/content/dataset'

os.makedirs(extract_path, exist_ok=True)
if os.path.exists(zip_path):
    print("Extracting dataset...")
    with zipfile.ZipFile(zip_path, 'r') as zip_ref:
        zip_ref.extractall(extract_path)
    print("Dataset extracted successfully to:", extract_path)
else:
    print(f"ERROR: Could not find zip file at {zip_path}. Please check your file name and location in Google Drive.")
```

---

#### Cell 3: Install Ultralytics (YOLOv8)
Install the official Ultralytics package and check the hardware environment to confirm GPU access.

```python
!pip install ultralytics

import ultralytics
# Print environment information and confirm CUDA (GPU) is available
ultralytics.checks()
```

---

#### Cell 4: Update data.yaml Paths
This automatically updates the dataset paths in `data.yaml` to point to the local folders inside Colab, preventing path-not-found errors during training.

```python
import yaml

yaml_path = '/content/dataset/data.yaml'

with open(yaml_path, 'r') as f:
    data = yaml.safe_load(f)

# Update paths to point to absolute Colab directory
data['path'] = '/content/dataset'
data['train'] = 'train/images'
data['val'] = 'valid/images'
data['test'] = 'test/images'

# Write updated config back
with open(yaml_path, 'w') as f:
    yaml.dump(data, f, default_flow_style=False)

print("Updated data.yaml configuration:")
print(yaml.dump(data, default_flow_style=False))
```

---

#### Cell 5: Train YOLOv8 Model (Highest Accuracy & Efficiency)
We use the YOLOv8 Small (`yolov8s.pt`) model. It provides a sweet spot between speed and accuracy, and is less prone to overfitting on a small dataset (32 images) compared to larger models.

**Key Hyperparameters for High Accuracy:**
- `imgsz=640`: Maintains high resolution to see detail in OMR bubbles.
- `epochs=100`: Gives the model plenty of iterations to converge on a tiny dataset.
- `batch=8`: Suitable batch size for a small dataset.
- `device=0`: Uses the T4 GPU.
- `augment=True`: Activates built-in augmentations (flips, scales, color shifts) to prevent overfitting.

```python
from ultralytics import YOLO

# Load a pre-trained YOLOv8 small model
model = YOLO('yolov8s.pt')

# Train the model
results = model.train(
    data='/content/dataset/data.yaml',
    epochs=100,
    imgsz=640,
    batch=8,
    device=0,        # Use GPU
    workers=2,       # Parallel data loading
    augment=True,    # Enabled data augmentation
    project='omr_training',
    name='yolov8s_omr',
    exist_ok=True
)
```

---

#### Cell 6: Evaluate Model Performance
Validate the model on the validation subset and plot accuracy metrics over training epochs.

```python
import os
import matplotlib.pyplot as plt
import matplotlib.image as mpimg

# Validate on validation set
metrics = model.val()
print("\n=== Validation Metrics ===")
print("mAP50-95:", metrics.box.map)
print("mAP50 (IOU=0.5):", metrics.box.map50)
print("Precision:", metrics.box.mp)
print("Recall:", metrics.box.mr)

# Plot training results curve
results_png = '/content/omr_training/yolov8s_omr/results.png'
if os.path.exists(results_png):
    plt.figure(figsize=(10, 10))
    img = mpimg.imread(results_png)
    plt.imshow(img)
    plt.axis('off')
    plt.show()
else:
    print("Results plot not found. Check training output directory.")
```

---

#### Cell 7: Save Trained Weights back to Google Drive
This copies your trained weights file (`best.pt`) back to Google Drive under a folder named `omr_reader_model/`, so you can download it for local use.

```python
import shutil

src_weights = '/content/omr_training/yolov8s_omr/weights/best.pt'
dst_dir = '/content/drive/MyDrive/omr_reader_model/'
os.makedirs(dst_dir, exist_ok=True)
dst_weights = os.path.join(dst_dir, 'best.pt')

if os.path.exists(src_weights):
    shutil.copy(src_weights, dst_weights)
    print("Success! Trained weights saved to Google Drive at:")
    print(dst_weights)
else:
    print("ERROR: Trained weights file not found. Did training complete successfully?")
```

---

#### Cell 8: Test the Model on Random Test Images
This cell allows you to visually check how well the model is performing on your test images. You can control how many images to test by setting `num_images_to_test`.

```python
# Set the number of random test images you want to visualize
num_images_to_test = 5 

import glob
import random
import matplotlib.pyplot as plt
import cv2
import os

# Locate images in the test set directory
test_images = (glob.glob('/content/dataset/test/images/*.jpeg') + 
               glob.glob('/content/dataset/test/images/*.jpg') + 
               glob.glob('/content/dataset/test/images/*.png'))

if not test_images:
    print("No test images found in '/content/dataset/test/images/'")
else:
    # Safely limit count to the number of available test images
    num_to_draw = min(num_images_to_test, len(test_images))
    selected_images = random.sample(test_images, num_to_draw)
    print(f"Visualizing {num_to_draw} random test images...")
    
    for idx, img_path in enumerate(selected_images):
        # Run inference using the trained model
        test_results = model.predict(source=img_path, conf=0.4, verbose=False)
        
        for result in test_results:
            # Get annotated image with drawn bounding boxes (BGR)
            annotated_img_bgr = result.plot()
            # Convert BGR to RGB for matplotlib display
            annotated_img_rgb = cv2.cvtColor(annotated_img_bgr, cv2.COLOR_BGR2RGB)
            
            # Render the image
            plt.figure(figsize=(10, 10))
            plt.title(f"Test Image {idx+1}: {os.path.basename(img_path)}")
            plt.imshow(annotated_img_rgb)
            plt.axis('off')
            plt.show()
```
