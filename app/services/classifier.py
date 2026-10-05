"""Module 2 – AI food classification (pretrained CLIP, zero-shot).

CLIP compares an image with text descriptions and scores how well they match.
With one pretrained model and no extra training we get:
  * a food / not-food check
  * dish recognition over our own label list (incl. Indian dishes)
  * a visual freshness vs spoilage score
  * a rough quantity estimate (single plate ... large vessels)

The model (~600 MB) is downloaded once from Hugging Face and then runs locally.
"""
import logging
import threading
import time

import numpy as np
import torch
from PIL import Image

from app.config import get_settings
from app.services.food_catalog import (
    CATEGORIES, DISH_TEMPLATES, DISHES, FOOD_PROMPTS, FRESH_PROMPTS, FRESHNESS_DISTRACTORS,
    NOT_FOOD_PROMPTS, QUANTITY_BUCKETS, SPOILED_PROMPTS,
)

log = logging.getLogger(__name__)

NOT_FOOD_REJECT = 0.85  # reject uploads this confidently not food


class FoodAnalyzer:
    def __init__(self, model_name: str, device: str = "cpu"):
        self.model_name = model_name
        self.device = device
        self.status = "not_loaded"  # not_loaded | loading | ready | error
        self.error: str | None = None
        self._lock = threading.Lock()

    # ---------- loading ----------
    def load(self) -> None:
        with self._lock:
            if self.status == "ready":
                return
            self.status = "loading"
            try:
                from transformers import CLIPModel, CLIPProcessor

                start = time.perf_counter()
                self.processor = CLIPProcessor.from_pretrained(self.model_name)
                self.model = CLIPModel.from_pretrained(self.model_name).to(self.device).eval()
                self.logit_scale = self.model.logit_scale.exp().item()
                self._build_text_embeddings()
                self.status, self.error = "ready", None
                log.info("Loaded %s in %.1fs", self.model_name, time.perf_counter() - start)
            except Exception as exc:  # keep the app usable without AI
                self.status, self.error = "error", str(exc)
                log.exception("Failed to load %s", self.model_name)
                raise

    @torch.no_grad()
    def _embed_text(self, prompts: list[str]) -> torch.Tensor:
        inputs = self.processor(text=prompts, return_tensors="pt", padding=True).to(self.device)
        features = self.model.get_text_features(**inputs).pooler_output
        return features / features.norm(dim=-1, keepdim=True)

    def _ensemble(self, prompts: list[str]) -> torch.Tensor:
        """Average several prompts into one normalised class embedding."""
        mean = self._embed_text(prompts).mean(dim=0)
        return mean / mean.norm()

    def _build_text_embeddings(self) -> None:
        self.dish_emb = torch.stack([
            self._ensemble([t.format(desc) for t in DISH_TEMPLATES]) for _, _, desc, _ in DISHES
        ])
        self.food_check_emb = self._embed_text(FOOD_PROMPTS + NOT_FOOD_PROMPTS)
        # index 0 = fresh, 1 = spoiled, rest = distractors
        self.fresh_emb = torch.stack([
            self._ensemble(FRESH_PROMPTS),
            self._ensemble(SPOILED_PROMPTS),
            *[self._ensemble(group) for group in FRESHNESS_DISTRACTORS],
        ])
        self.quantity_emb = self._embed_text([q[0] for q in QUANTITY_BUCKETS])

    # ---------- inference ----------
    @torch.no_grad()
    def _embed_image(self, image_rgb: np.ndarray) -> torch.Tensor:
        inputs = self.processor(images=Image.fromarray(image_rgb), return_tensors="pt").to(self.device)
        features = self.model.get_image_features(**inputs).pooler_output
        return (features / features.norm(dim=-1, keepdim=True))[0]

    def _probs(self, image_emb: torch.Tensor, text_emb: torch.Tensor) -> np.ndarray:
        logits = self.logit_scale * image_emb @ text_emb.T
        return logits.softmax(dim=-1).cpu().numpy()

    def analyze(self, image_rgb: np.ndarray) -> dict:
        """Analyse an RGB uint8 image. Loads the model on first use."""
        if self.status != "ready":
            self.load()
        start = time.perf_counter()
        img = self._embed_image(image_rgb)

        food_check = self._probs(img, self.food_check_emb)
        food_probability = float(food_check[:len(FOOD_PROMPTS)].sum())

        dish_probs = self._probs(img, self.dish_emb)
        order = np.argsort(dish_probs)[::-1]
        top = [
            {"key": DISHES[i][0], "name": DISHES[i][1], "category": DISHES[i][3],
             "confidence": round(float(dish_probs[i]), 3)}
            for i in order[:3]
        ]

        # Category = the category with the highest total probability over its dishes
        category_probs: dict[str, float] = {}
        for p, (_, _, _, cat) in zip(dish_probs, DISHES):
            category_probs[cat] = category_probs.get(cat, 0.0) + float(p)
        category = max(category_probs, key=category_probs.get)

        fresh_probs = self._probs(img, self.fresh_emb)
        spoiled = float(fresh_probs[1])
        q_probs = self._probs(img, self.quantity_emb)
        q = QUANTITY_BUCKETS[int(q_probs.argmax())]

        return {
            "model": self.model_name,
            "is_food": food_probability >= 0.5,
            "food_probability": round(food_probability, 3),
            "dish": top[0],
            "top_predictions": top,
            "category": {
                "key": category,
                "name": CATEGORIES[category]["name"],
                "confidence": round(category_probs[category], 3),
                "non_veg": CATEGORIES[category]["non_veg"],
            },
            "freshness": {
                "spoiled_probability": round(spoiled, 3),
                "label": "looks spoiled" if spoiled >= 0.5 else "looks fresh",
            },
            "quantity_estimate": {
                "label": q[1], "min_servings": q[2], "max_servings": q[3],
                "confidence": round(float(q_probs.max()), 3),
            },
            "inference_ms": round((time.perf_counter() - start) * 1000),
        }


_analyzer: FoodAnalyzer | None = None


def get_analyzer() -> FoodAnalyzer:
    global _analyzer
    if _analyzer is None:
        settings = get_settings()
        _analyzer = FoodAnalyzer(settings.ai_model, settings.ai_device)
    return _analyzer
