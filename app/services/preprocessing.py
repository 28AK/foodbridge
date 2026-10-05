"""Module 1 – Food image preprocessing (OpenCV).

Pipeline for every donor photo:
  1. Decode + fix phone-camera EXIF rotation
  2. Resize so the longest side is at most 1024 px
  3. Measure quality: brightness, contrast, sharpness (blur)
  4. Enhance only when needed:
       - dark photo     -> denoise + gamma brighten + CLAHE
       - over-exposed   -> gamma darken
       - low contrast   -> CLAHE (on the L channel of LAB, so colours stay natural)
  5. Center-crop + resize to 224x224 RGB for the CNN classifier
"""
import io
import math
from dataclasses import dataclass

import cv2
import numpy as np
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_SIDE = 1024
MIN_SIDE = 64
MODEL_SIZE = 224

DARK_THRESHOLD = 90         # mean grey level (0-255) below which a photo counts as dark
BRIGHT_THRESHOLD = 200      # above this it counts as over-exposed
TARGET_BRIGHTNESS = 130
LOW_CONTRAST = 40           # std-dev of grey levels
BLUR_THRESHOLD = 100.0      # variance of Laplacian; lower = blurrier


@dataclass
class PreprocessResult:
    original: np.ndarray     # BGR, resized for storage
    processed: np.ndarray    # BGR, enhanced
    model_input: np.ndarray  # RGB uint8, MODEL_SIZE x MODEL_SIZE
    report: dict


def decode_image(data: bytes) -> np.ndarray:
    """Decode image bytes to a BGR array, honouring EXIF orientation."""
    try:
        with Image.open(io.BytesIO(data)) as im:
            rgb = np.asarray(ImageOps.exif_transpose(im).convert("RGB"))
    except (UnidentifiedImageError, OSError, Image.DecompressionBombError) as exc:
        raise ValueError("Uploaded file is not a valid image") from exc
    if min(rgb.shape[:2]) < MIN_SIDE:
        raise ValueError(f"Image is too small (minimum {MIN_SIDE}x{MIN_SIDE} px)")
    return cv2.cvtColor(rgb, cv2.COLOR_RGB2BGR)


def resize_max_side(img: np.ndarray, max_side: int = MAX_SIDE) -> np.ndarray:
    h, w = img.shape[:2]
    scale = max_side / max(h, w)
    if scale >= 1:
        return img
    return cv2.resize(img, (round(w * scale), round(h * scale)), interpolation=cv2.INTER_AREA)


def measure_quality(img: np.ndarray) -> dict:
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    return {
        "brightness": round(float(gray.mean()), 1),
        "contrast": round(float(gray.std()), 1),
        "sharpness": round(float(cv2.Laplacian(gray, cv2.CV_64F).var()), 1),
    }


def gamma_for(brightness: float, target: float = TARGET_BRIGHTNESS) -> float:
    """Gamma that maps the current mean brightness towards the target."""
    mean = min(max(brightness, 1.0), 254.0) / 255.0
    gamma = math.log(target / 255.0) / math.log(mean)
    return min(max(gamma, 0.4), 2.5)


def adjust_gamma(img: np.ndarray, gamma: float) -> np.ndarray:
    table = ((np.arange(256) / 255.0) ** gamma * 255).clip(0, 255).astype(np.uint8)
    return cv2.LUT(img, table)


def apply_clahe(img: np.ndarray, clip_limit: float = 2.0) -> np.ndarray:
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    l, a, b = cv2.split(lab)
    l = cv2.createCLAHE(clipLimit=clip_limit, tileGridSize=(8, 8)).apply(l)
    return cv2.cvtColor(cv2.merge((l, a, b)), cv2.COLOR_LAB2BGR)


def to_model_input(img: np.ndarray, size: int = MODEL_SIZE) -> np.ndarray:
    """Center-crop to a square and resize to size x size, returned as RGB."""
    h, w = img.shape[:2]
    side = min(h, w)
    top, left = (h - side) // 2, (w - side) // 2
    square = cv2.resize(img[top:top + side, left:left + side], (size, size),
                        interpolation=cv2.INTER_AREA)
    return cv2.cvtColor(square, cv2.COLOR_BGR2RGB)


def preprocess(data: bytes) -> PreprocessResult:
    decoded = decode_image(data)
    original = resize_max_side(decoded)
    before = measure_quality(original)
    brightness = before["brightness"]

    img = original
    steps = []
    if brightness < DARK_THRESHOLD:
        # Low-light photos are noisy; denoise before brightening amplifies the noise
        img = cv2.fastNlMeansDenoisingColored(img, None, 5, 5, 7, 21)
        steps.append("denoise")
    if brightness < DARK_THRESHOLD or brightness > BRIGHT_THRESHOLD:
        gamma = gamma_for(brightness)
        img = adjust_gamma(img, gamma)
        steps.append(f"gamma_correction({gamma:.2f})")
    if brightness < DARK_THRESHOLD or before["contrast"] < LOW_CONTRAST:
        img = apply_clahe(img)
        steps.append("clahe_contrast")

    after = measure_quality(img)
    warnings = []
    if before["sharpness"] < BLUR_THRESHOLD:
        warnings.append("Photo looks blurry – a sharper photo improves AI accuracy")
    if after["brightness"] < 60:
        warnings.append("Photo is still very dark – try taking it in better light")

    report = {
        "original_size": [decoded.shape[1], decoded.shape[0]],
        "stored_size": [original.shape[1], original.shape[0]],
        "model_input_size": [MODEL_SIZE, MODEL_SIZE],
        "before": before,
        "after": after,
        "steps": steps,
        "enhanced": bool(steps),
        "warnings": warnings,
    }
    return PreprocessResult(original, img, to_model_input(img), report)


def encode_images(result: PreprocessResult) -> dict[str, bytes]:
    """JPEG-encode the three pipeline stages; returns {stage: jpeg bytes}."""
    stages = {
        "original": result.original,
        "processed": result.processed,
        "model_input": cv2.cvtColor(result.model_input, cv2.COLOR_RGB2BGR),
    }
    encoded = {}
    for name, image in stages.items():
        ok, buf = cv2.imencode(".jpg", image, [cv2.IMWRITE_JPEG_QUALITY, 85])
        if not ok:
            raise ValueError(f"Could not encode {name} image")
        encoded[name] = buf.tobytes()
    return encoded
