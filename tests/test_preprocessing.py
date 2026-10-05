import cv2
import numpy as np
import pytest

from app.services.preprocessing import MODEL_SIZE, gamma_for, preprocess


def encode(img: np.ndarray) -> bytes:
    ok, buf = cv2.imencode(".jpg", img)
    assert ok
    return buf.tobytes()


def textured_image(h=600, w=800, scale=1.0) -> np.ndarray:
    rng = np.random.default_rng(0)
    img = rng.integers(40, 220, size=(h, w, 3)).astype(np.float32)
    img = cv2.GaussianBlur(img, (0, 0), 3)
    return (img * scale).clip(0, 255).astype(np.uint8)


def test_dark_image_is_brightened():
    result = preprocess(encode(textured_image(scale=0.25)))
    r = result.report
    assert r["before"]["brightness"] < 90
    assert r["after"]["brightness"] > r["before"]["brightness"] + 30
    assert "denoise" in r["steps"] and "clahe_contrast" in r["steps"]
    assert r["enhanced"]


def test_well_lit_high_contrast_image_left_alone():
    img = np.zeros((400, 400, 3), np.uint8)
    img[:, :200] = 30
    img[:, 200:] = 230
    result = preprocess(encode(img))
    assert result.report["steps"] == []
    assert not result.report["enhanced"]


def test_large_image_resized_and_model_input_shape():
    result = preprocess(encode(textured_image(h=2000, w=3000)))
    assert max(result.original.shape[:2]) == 1024
    assert result.report["original_size"] == [3000, 2000]
    assert result.model_input.shape == (MODEL_SIZE, MODEL_SIZE, 3)


def test_invalid_bytes_rejected():
    with pytest.raises(ValueError):
        preprocess(b"definitely not an image")


def test_tiny_image_rejected():
    with pytest.raises(ValueError):
        preprocess(encode(np.zeros((20, 20, 3), np.uint8)))


def test_gamma_direction():
    assert gamma_for(50) < 1 < gamma_for(230)
