"""SAM 3 text-prompt HTTP service intended to run in a Google Colab GPU runtime."""

from __future__ import annotations

import io
import json
import os
import threading
from contextlib import nullcontext

import cv2
import numpy as np
import torch
from flask import Flask, jsonify, request
from PIL import Image
from sam3.model_builder import build_sam3_image_model
from sam3.model.sam3_image_processor import Sam3Processor


DEVICE = "cuda" if torch.cuda.is_available() else "cpu"
MODEL = build_sam3_image_model(device=DEVICE)
PROCESSOR = Sam3Processor(MODEL, confidence_threshold=0.25)
if DEVICE == "cuda":
    major, _ = torch.cuda.get_device_capability()
    AUTOCAST_DTYPE = torch.bfloat16 if major >= 8 else torch.float16
    torch.backends.cuda.matmul.allow_tf32 = True
    torch.backends.cudnn.allow_tf32 = True
else:
    AUTOCAST_DTYPE = None
INFERENCE_LOCK = threading.Lock()
APP = Flask(__name__)


def to_numpy(value):
    if hasattr(value, "detach"):
        value = value.detach().float().cpu().numpy()
    return np.asarray(value)


def mask_polygons(mask: np.ndarray, width: int, height: int,
                  thin_class: bool = False) -> list[list[float]]:
    binary = (mask > 0).astype(np.uint8)
    min_area = 2 if thin_class else max(4, int(width * height * 0.000015))
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    polygons = []
    for contour in contours:
        if cv2.contourArea(contour) < min_area:
            continue
        perimeter = cv2.arcLength(contour, True)
        approx = cv2.approxPolyDP(contour, max(0.35, perimeter * 0.0008), True)
        points = approx.reshape(-1, 2)
        if len(points) < 3:
            continue
        flat = []
        for x, y in points:
            flat.extend([float(np.clip(x, 0, width - 1)), float(np.clip(y, 0, height - 1))])
        polygons.append(flat)
    return polygons


@APP.get("/health")
def health():
    return jsonify({"model": "sam3", "ready": True, "device": DEVICE})


@APP.post("/predict")
def predict():
    uploaded = request.files.get("file")
    if uploaded is None:
        return jsonify({"error": "multipart field 'file' is required"}), 400
    try:
        prompts = json.loads(request.form.get("prompts", "[]"))
    except json.JSONDecodeError:
        return jsonify({"error": "'prompts' must be a JSON array"}), 400
    if not isinstance(prompts, list) or not prompts or not all(isinstance(x, str) and x.strip() for x in prompts):
        return jsonify({"error": "'prompts' must contain non-empty class names"}), 400
    task_type = request.form.get("task_type", "instance")
    if task_type not in {"semantic", "instance", "panoptic"}:
        return jsonify({"error": "unsupported task_type"}), 400
    min_score = float(request.form.get("min_score", "0.30"))

    try:
        image = Image.open(io.BytesIO(uploaded.read())).convert("RGB")
        width, height = image.size
        # SAM 3 caches image features in state, so encode each frame once and
        # evaluate the task's class prompts against the same image state.
        amp = (torch.autocast("cuda", dtype=AUTOCAST_DTYPE)
               if DEVICE == "cuda" else nullcontext())
        with INFERENCE_LOCK, torch.inference_mode(), amp:
            state = PROCESSOR.set_image(image)
            detections = []
            for prompt in prompts:
                output = PROCESSOR.set_text_prompt(state=state, prompt=prompt)
                masks = to_numpy(output["masks"])
                scores = to_numpy(output["scores"]).reshape(-1)
                if masks.ndim == 4:
                    masks = masks[:, 0]
                elif masks.ndim == 2:
                    masks = masks[None, ...]
                if masks.ndim != 3:
                    continue
                for idx, raw_mask in enumerate(masks):
                    score = float(scores[idx]) if idx < len(scores) else 1.0
                    if score < min_score:
                        continue
                    binary = (raw_mask > 0.5).astype(np.uint8)
                    if binary.shape != (height, width):
                        binary = cv2.resize(binary, (width, height), interpolation=cv2.INTER_NEAREST)
                    polygons = mask_polygons(binary, width, height,
                                             thin_class=prompt.lower() in {"pole", "traffic sign", "traffic light"})
                    if polygons:
                        detections.append({"label": prompt, "score": score,
                                           "polygons": polygons, "_mask": binary})

        # SAM may return duplicate masks for one concept. Suppress near-identical
        # masks per class while retaining separate adjacent instances.
        kept = []
        for det in sorted(detections, key=lambda row: row["score"], reverse=True):
            duplicate = False
            for prior in kept:
                if prior["label"] != det["label"]:
                    continue
                a, b = prior["_mask"].astype(bool), det["_mask"].astype(bool)
                union = np.logical_or(a, b).sum()
                if union and np.logical_and(a, b).sum() / union >= 0.88:
                    duplicate = True
                    break
            if not duplicate:
                kept.append(det)

        # Semantic and panoptic output must not leave same-pixel class overlaps.
        # In panoptic mode thing masks claim pixels before stuff masks; within
        # each group, higher-confidence regions claim first. Instance masks
        # remain independent so each object is represented separately.
        if task_type in {"semantic", "panoptic"}:
            occupied = np.zeros((height, width), dtype=bool)
            stuff = {"road", "sidewalk", "building", "vegetation", "sky"}
            ordered = sorted(kept, key=lambda det: (
                1 if task_type == "panoptic" and det["label"] in stuff else 0,
                -det["score"],
            ))
            for det in ordered:
                mask = det["_mask"].astype(bool) & ~occupied
                occupied |= mask
                det["polygons"] = mask_polygons(mask.astype(np.uint8), width, height,
                                                thin_class=det["label"].lower() in {"pole", "traffic sign", "traffic light"})

        masks_out = [{"label": item["label"], "score": item["score"], "polygons": item["polygons"]}
                     for item in kept if item["polygons"]]
        return jsonify({"model": "sam3", "width": width, "height": height,
                        "masks": masks_out})
    except Exception as exc:
        APP.logger.exception("SAM 3 inference failed")
        return jsonify({"error": str(exc)}), 500


if __name__ == "__main__":
    APP.run(host="0.0.0.0", port=int(os.getenv("PORT", "7860")), threaded=False)
