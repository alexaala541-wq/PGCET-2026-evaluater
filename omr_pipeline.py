import os
import cv2
import json
import numpy as np
from pathlib import Path
import sys
import contextlib
import warnings

# Suppress all library warnings
warnings.filterwarnings("ignore")

try:
    import easyocr
except ImportError:
    easyocr = None

try:
    from ultralytics import YOLO
except ImportError:
    YOLO = None

try:
    import torch
    CUDA_AVAILABLE = torch.cuda.is_available()
except ImportError:
    CUDA_AVAILABLE = False

try:
    from sklearn.cluster import KMeans
    SKLEARN_AVAILABLE = True
except ImportError:
    SKLEARN_AVAILABLE = False


class OMRPipeline:
    """
    OMR Answer Sheet Pipeline.
    - Step 1: OCR to find column Q-number anchor X positions (with proportional fallback)
    - Step 2: YOLOv8 to detect all filled (dark) circles
    - Step 3: KMeans clustering on YOLO detections to find 25 row Y-centers and 4 option X-centers per column
    - Step 4: Match each detection to Q number (1-100) and option (1-4)
    - Step 5: Output answers in Q1. 3 format
    """

    def __init__(self, model_path="best.pt", use_gpu=False, verbose=False):
        self.model_path = model_path
        self.use_gpu = use_gpu
        self.verbose = verbose
        self.model = None
        self.ocr_reader = None

        @contextlib.contextmanager
        def suppress_output(active):
            if active:
                with open(os.devnull, 'w') as fnull:
                    old_stdout = sys.stdout
                    old_stderr = sys.stderr
                    sys.stdout = fnull
                    sys.stderr = fnull
                    try:
                        yield
                    finally:
                        sys.stdout = old_stdout
                        sys.stderr = old_stderr
            else:
                yield

        if os.path.exists(model_path):
            if YOLO is not None:
                if self.verbose:
                    print(f"Loading YOLOv8 model from {model_path}...")
                with suppress_output(not self.verbose):
                    self.model = YOLO(model_path)
            else:
                if self.verbose:
                    print("WARNING: 'ultralytics' not installed.")
        else:
            if self.verbose:
                print(f"INFO: Model not found at '{model_path}'.")

        if easyocr is not None:
            if self.verbose:
                print("Initializing EasyOCR (for column calibration only)...")
            with suppress_output(not self.verbose):
                self.ocr_reader = easyocr.Reader(['en'], gpu=use_gpu)
        else:
            if self.verbose:
                print("INFO: EasyOCR not installed. Using proportional column positions.")

    # ─────────────────────────────────────────────
    #  STEP 1: OCR-based column X calibration
    # ─────────────────────────────────────────────
    def get_column_anchors(self, image_path, img_w, img_h):
        """
        Returns 4 X-coordinates (one per column) for where Q-number text sits.
        Falls back to proportional defaults from measured diagnostics if OCR fails.
        """
        # Proportional defaults measured from 627-wide reference image
        default_x = [
            int(img_w * 0.024),   # col1 ~ 15px
            int(img_w * 0.260),   # col2 ~ 163px
            int(img_w * 0.530),   # col3 ~ 332px
            int(img_w * 0.772),   # col4 ~ 484px
        ]

        if self.ocr_reader is None:
            if self.verbose:
                print(f"Using default column anchors: {default_x}")
            return default_x

        try:
            img = cv2.imread(image_path)
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ocr_results = self.ocr_reader.readtext(gray)

            buckets = [[], [], [], []]
            for bbox, text, conf in ocr_results:
                digits = "".join(c for c in text if c.isdigit())
                if not digits:
                    continue
                val = int(digits)
                pts = np.array(bbox, dtype=np.int32)
                cx = int(np.mean(pts[:, 0]))

                if 10 <= val <= 25:
                    buckets[0].append(cx)
                elif 26 <= val <= 50:
                    buckets[1].append(cx)
                elif 51 <= val <= 75:
                    buckets[2].append(cx)
                elif 76 <= val <= 100:
                    buckets[3].append(cx)

            col_x = []
            for i, xs in enumerate(buckets):
                if len(xs) >= 2:
                    col_x.append(int(np.median(xs)))
                else:
                    col_x.append(default_x[i])

            # Sanity: must be strictly increasing and reasonable
            valid = all(col_x[i] < col_x[i+1] for i in range(3))
            if not valid:
                if self.verbose:
                    print("OCR column anchors failed sanity. Using defaults.")
                return default_x

            if self.verbose:
                print(f"OCR column anchors: {col_x}")
            return col_x

        except Exception as e:
            if self.verbose:
                print(f"OCR calibration error ({e}). Using defaults.")
            return default_x

    # ─────────────────────────────────────────────
    #  STEP 2: YOLOv8 circle detection
    # ─────────────────────────────────────────────
    # ─────────────────────────────────────────────
    #  STEP 1b: Crop to question-only ROI
    # ─────────────────────────────────────────────
    def crop_to_grid(self, img):
        """
        Removes header rows (Q NO/ANSWERS column titles, watermark) and
        footer rows (Examination Authority etc.) so only Q1-Q100 rows remain.
        Dynamically adjusts crop margins based on image aspect ratio to support
        pre-cropped tight OMR grids.
        """
        h, w = img.shape[:2]
        aspect = h / w
        if aspect > 1.25:
            # Full page format
            y_top = int(h * 0.050)
            y_bot = int(h * 0.985)
        else:
            # Already cropped tightly to the grid
            y_top = int(h * 0.010)
            y_bot = int(h * 0.995)
            
        cropped = img[y_top:y_bot, 0:w]
        if self.verbose:
            print(f"ROI crop (aspect {aspect:.2f}): rows {y_top}–{y_bot} of {h}")
        return cropped, y_top

    def detect_circles(self, img_array):
        if self.model is None:
            if self.verbose:
                print("ERROR: YOLOv8 model not loaded.")
            return []

        device = 'cuda' if self.use_gpu else 'cpu'
        if self.verbose:
            print("Running YOLOv8 inference...")
        # Pass numpy array directly (already cropped)
        results = self.model.predict(source=img_array, conf=0.35, device=device, verbose=False)

        circles = []
        for result in results:
            for box in result.boxes:
                xyxy = box.xyxy[0].cpu().numpy()
                x0, y0, x1, y1 = map(int, xyxy)
                cx = (x0 + x1) // 2
                cy = (y0 + y1) // 2
                conf = float(box.conf[0].cpu().numpy())
                circles.append({'center': (cx, cy), 'bbox': [x0, y0, x1, y1], 'conf': conf})

        if not circles:
            return []

        # 1. Filter out anomaly sizes using median dimensions
        widths = [c['bbox'][2] - c['bbox'][0] for c in circles]
        heights = [c['bbox'][3] - c['bbox'][1] for c in circles]
        med_w = np.median(widths)
        med_h = np.median(heights)

        filtered_circles = []
        for c in circles:
            w = c['bbox'][2] - c['bbox'][0]
            h = c['bbox'][3] - c['bbox'][1]
            if (0.4 * med_w <= w <= 2.2 * med_w) and (0.4 * med_h <= h <= 2.2 * med_h):
                filtered_circles.append(c)
            else:
                if self.verbose:
                    print(f"Filtered out anomaly circle of size {w}x{h} (median: {med_w:.1f}x{med_h:.1f}) at {c['center']}")

        # 2. Simple Non-Maximum Suppression (NMS) for overlapping boxes
        filtered_circles.sort(key=lambda x: x['conf'], reverse=True)
        nms_circles = []
        for c in filtered_circles:
            cx, cy = c['center']
            keep = True
            for kept in nms_circles:
                kx, ky = kept['center']
                dist = np.sqrt((cx - kx)**2 + (cy - ky)**2)
                if dist < 12.0:
                    keep = False
                    if self.verbose:
                        print(f"NMS filtered duplicate circle at {c['center']} (dist: {dist:.1f}px to {kept['center']})")
                    break
            if keep:
                nms_circles.append(c)

        if self.verbose:
            print(f"YOLOv8 detected {len(circles)} raw circles, {len(nms_circles)} after filtering/NMS.")
        return nms_circles

    # ─────────────────────────────────────────────
    #  STEP 3: KMeans grid calibration
    # ─────────────────────────────────────────────
    def build_column_boundaries(self, col_q_x, col_option_x, img_w):
        """
        Midpoint boundaries between the end of one column (Option 4) and
        the start of the next column (Q-label anchor X).
        """
        bounds = [0]
        for i in range(3):
            col_end = col_option_x[i][-1]  # Option 4 X position of column i
            next_col_start = col_q_x[i + 1] # Anchor X position of column i + 1
            bounds.append((col_end + next_col_start) // 2)
        bounds.append(img_w + 100)
        return bounds

    def cluster_row_y(self, circles, img_h, n_rows=25):
        """
        KMeans on all circle Y positions to find 25 row Y-centers.
        Falls back to proportional if too few circles.
        """
        if not SKLEARN_AVAILABLE:
            top = int(img_h * 0.055)
            bottom = int(img_h * 0.97)
            return [int(top + i * (bottom - top) / (n_rows - 1)) for i in range(n_rows)]

        ys = np.array([c['center'][1] for c in circles], dtype=np.float32).reshape(-1, 1)
        k = min(n_rows, len(circles))
        km = KMeans(n_clusters=k, n_init=10, random_state=42)
        km.fit(ys)
        centers = sorted(km.cluster_centers_.flatten())

        # If we found fewer than n_rows clusters, extrapolate missing rows
        if len(centers) < n_rows:
            step = np.median(np.diff(centers)) if len(centers) > 1 else 24.0
            while len(centers) < n_rows:
                centers.append(centers[-1] + step)
            while len(centers) > n_rows:
                centers.pop()

        centers = [int(y) for y in sorted(centers)]
        
        # Apply robust linear smoothing to guarantee perfect grid alignment
        if len(centers) == n_rows:
            xs = np.arange(n_rows)
            a, b = np.polyfit(xs, centers, 1)
            centers = [int(round(a * r + b)) for r in range(n_rows)]

        if self.verbose:
            print(f"Row Y-centers ({len(centers)}): {centers}")
        return centers

    def get_option_x_positions(self, col_q_x, img_w, scale=None):
        """
        Calculates the 4 option X coordinates for each column using the
        physically calibrated proportional offsets from the column anchor Q-label:
        [29, 55, 80, 105] (scaled by image width ratio).
        """
        if scale is None:
            scale = img_w / 627.0
        option_offsets = [int(29 * scale), int(55 * scale), int(80 * scale), int(105 * scale)]
        
        col_option_x = []
        for col_idx, anchor in enumerate(col_q_x):
            opts = [anchor + opt for opt in option_offsets]
            if self.verbose:
                print(f"Col {col_idx+1} option X positions: {opts}")
            col_option_x.append(opts)
            
        return col_option_x

    # ─────────────────────────────────────────────
    #  STEP 4: Match circles to Q answers
    # ─────────────────────────────────────────────
    def match_answers(self, circles, col_q_x, col_option_x, row_ys, img_w):
        bounds = self.build_column_boundaries(col_q_x, col_option_x, img_w)

        # Tolerances
        y_spacing = np.median(np.diff(row_ys)) if len(row_ys) > 1 else 24.0
        y_tol = y_spacing * 0.48

        answers_raw = {}  # {q_num: [opts]}

        for circle in circles:
            cx, cy = circle['center']

            # Find column
            col = None
            for c in range(4):
                if bounds[c] <= cx < bounds[c + 1]:
                    col = c
                    break
            if col is None:
                continue

            # Find row (nearest row Y within tolerance)
            row = None
            best_dy = float('inf')
            for r, ry in enumerate(row_ys):
                dy = abs(cy - ry)
                if dy < best_dy and dy < y_tol:
                    best_dy = dy
                    row = r
            if row is None:
                continue

            # Find option (nearest option X within tolerance)
            opts_x = col_option_x[col]
            scale = img_w / 627.0
            x_spacing = 25.0 * scale
            x_tol = x_spacing * 0.48

            opt = None
            best_dx = float('inf')
            for o, ox in enumerate(opts_x):
                dx = abs(cx - ox)
                if dx < best_dx and dx < x_tol:
                    best_dx = dx
                    opt = o + 1  # 1-indexed
            if opt is None:
                continue

            q_num = col * 25 + row + 1
            if q_num not in answers_raw:
                answers_raw[q_num] = []
            if opt not in answers_raw[q_num]:
                answers_raw[q_num].append(opt)

        # Format final answers dict
        final = {}
        for q in range(1, 101):
            marked = sorted(answers_raw.get(q, []))
            if len(marked) == 0:
                final[q] = "None"
            elif len(marked) == 1:
                final[q] = str(marked[0])
            else:
                final[q] = "".join(str(m) for m in marked) + " (Multiple)"
        return final

    # ─────────────────────────────────────────────
    #  STEP 5: Visualize
    # ─────────────────────────────────────────────
    def visualize(self, image_path, circles, col_q_x, col_option_x, row_ys, answers, output_path):
        img = cv2.imread(image_path)
        if img is None:
            return

        # Draw expected bubble grid (grey = empty, red = filled)
        for col_idx, opts in enumerate(col_option_x):
            for r, ry in enumerate(row_ys):
                q_num = col_idx * 25 + r + 1
                ans = answers.get(q_num, "None")
                for o_idx, ox in enumerate(opts):
                    opt_str = str(o_idx + 1)
                    is_marked = ans not in ("None",) and opt_str in ans.replace(" (Multiple)", "")
                    color = (0, 0, 220) if is_marked else (160, 160, 160)
                    cv2.circle(img, (ox, ry), 9, color, 2 if is_marked else 1)
                    cv2.putText(img, opt_str, (ox - 3, ry + 4),
                                cv2.FONT_HERSHEY_SIMPLEX, 0.25, color, 1)

        # Draw Q-number labels with answer overlay
        for col_idx, qx in enumerate(col_q_x):
            for r, ry in enumerate(row_ys):
                q_num = col_idx * 25 + r + 1
                ans = answers.get(q_num, "None")
                txt_color = (0, 130, 0) if ans != "None" else (100, 100, 100)
                label = f"Q{q_num}:{ans}" if ans != "None" else f"Q{q_num}"
                cv2.putText(img, label, (max(0, qx - 30), ry + 4),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.27, txt_color, 1)

        # Draw YOLO raw detections (thin red)
        for c in circles:
            x0, y0, x1, y1 = c['bbox']
            cv2.rectangle(img, (x0, y0), (x1, y1), (0, 0, 200), 1)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        cv2.imwrite(output_path, img)
        if self.verbose:
            print(f"Annotated image saved → {output_path}")

    # ─────────────────────────────────────────────
    #  MAIN
    # ─────────────────────────────────────────────
    def process_sheet(self, image_path, output_dir="output_runs"):
        if not os.path.exists(image_path):
            if self.verbose:
                print(f"ERROR: Image not found: {image_path}")
            return None

        img = cv2.imread(image_path)
        img_h, img_w = img.shape[:2]
        img_name = Path(image_path).stem
        if self.verbose:
            print(f"\nProcessing: {image_path}  [{img_w}x{img_h}]")

        # 1. Crop out header and footer — keep only Q1-Q100 grid rows
        cropped, y_offset = self.crop_to_grid(img)
        crop_h, crop_w = cropped.shape[:2]

        # 2. Column anchors via OCR on FULL image (Q numbers are in header zone too)
        col_q_x = self.get_column_anchors(image_path, img_w, img_h)

        # 3. Detect circles via YOLO on CROPPED image
        if self.model is None:
            if self.verbose:
                print("No YOLO model. Cannot extract answers.")
            return None
        circles_crop = self.detect_circles(cropped)
        if not circles_crop:
            if self.verbose:
                print("No circles detected in grid area. Cannot extract answers.")
            return None

        # 4. Shift circle coordinates back to full-image Y space for visualization
        circles = []
        for c in circles_crop:
            cx, cy = c['center']
            x0, y0, x1, y1 = c['bbox']
            circles.append({
                'center': (cx, cy + y_offset),
                'bbox': [x0, y0 + y_offset, x1, y1 + y_offset],
                'conf': c['conf']
            })

        # 5. Calibrate grid from anchors and detections
        row_ys = self.cluster_row_y(circles, img_h, n_rows=25)
        
        # Try dynamic geometric alignment using robust template matching on detected circles
        geom_scale = img_w / 627.0
        if len(circles) >= 15:
            try:
                # Vectorized grid search for best horizontal shift (dx) and scale
                circles_x = np.array([c['center'][0] for c in circles], dtype=np.float32)
                
                # Reference option positions
                x_ref = np.array([
                    44, 70, 95, 120,
                    192, 218, 243, 268,
                    361, 387, 412, 437,
                    513, 539, 564, 589
                ], dtype=np.float32)
                
                prop_scale = img_w / 627.0
                best_score = float('inf')
                best_dx = 0.0
                best_scale = prop_scale
                
                # Search scales around proportional scale (within 15%) and dx in a wide range
                scales = np.linspace(0.85 * prop_scale, 1.15 * prop_scale, 61)
                dxs = np.linspace(-150.0, 150.0, 301)
                
                for s in scales:
                    expected_cols = x_ref * s
                    for dx in dxs:
                        shifted_opts = expected_cols + dx
                        # Calculate distances
                        dists = np.abs(circles_x[:, None] - shifted_opts[None, :])
                        min_dists = np.min(dists, axis=1)
                        # Clip to be robust to outliers (e.g. max 12px error contribution)
                        score = np.sum(np.minimum(min_dists, 12.0))
                        if score < best_score:
                            best_score = score
                            best_dx = dx
                            best_scale = s
                            
                geom_scale = best_scale
                ref_anchors = [15, 163, 332, 484]
                col_q_x = [int(best_dx + a * geom_scale) for a in ref_anchors]
                if self.verbose:
                    print(f"Geometric calibration (template matching) succeeded. Shift: {best_dx:.2f}px, scale: {geom_scale:.4f}, anchors: {col_q_x}")
            except Exception as geom_err:
                if self.verbose:
                    print(f"Geometric calibration error: {geom_err}")

        col_option_x = self.get_option_x_positions(col_q_x, img_w, scale=geom_scale)
        bounds = self.build_column_boundaries(col_q_x, col_option_x, img_w)

        # 6. Match to answers
        answers = self.match_answers(circles, col_q_x, col_option_x, row_ys, img_w)

        # 7. Save annotated image
        viz_path = os.path.join(output_dir, f"{img_name}_annotated.jpeg")
        self.visualize(image_path, circles, col_q_x, col_option_x, row_ys, answers, viz_path)

        # 8. Save JSON
        os.makedirs(output_dir, exist_ok=True)
        json_path = os.path.join(output_dir, f"{img_name}_answers.json")
        with open(json_path, 'w') as f:
            json.dump({str(k): v for k, v in answers.items()}, f, indent=4)
        if self.verbose:
            print(f"JSON saved → {json_path}")

        # 9. Console output — Q1-Q100 only
        if self.verbose:
            print("\n=== Extracted Answers (Q1 - Q100) ===")
        for q in range(1, 101):
            ans = answers.get(q, "None")
            print(f"Q{q}. {ans}")

        return answers


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="OMR Sheet Reader - YOLOv8 + KMeans Grid Calibration")
    parser.add_argument("--image", type=str, required=True, help="Path to OMR sheet image")
    parser.add_argument("--model", type=str, default="best.pt", help="Path to YOLOv8 best.pt weights")
    parser.add_argument("--output", type=str, default="output_runs", help="Output directory")
    parser.add_argument("--gpu", action="store_true", help="Force GPU")
    parser.add_argument("--verbose", action="store_true", help="Print detailed processing logs")
    args, _ = parser.parse_known_args()

    # Auto-find model
    model_path = args.model
    if not os.path.exists(model_path):
        fallback = r"C:\Users\vjaga\Downloads\omr test\best.pt"
        if os.path.exists(fallback):
            if args.verbose:
                print(f"Using model: {fallback}")
            model_path = fallback

    use_gpu = CUDA_AVAILABLE or args.gpu
    pipeline = OMRPipeline(model_path=model_path, use_gpu=use_gpu, verbose=args.verbose)
    pipeline.process_sheet(args.image, output_dir=args.output)
