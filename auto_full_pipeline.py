"""Prompt SAM 3 with each task's classes and import every returned mask to CVAT.

The Colab service contract is documented in SAM3_COLAB_SETUP.md. This runner
does not invent a center click or silently export an empty annotation file.
"""

from __future__ import annotations

import io
import json
import os
import sys
import tempfile
import time
import zipfile
from pathlib import Path
from typing import Any

import requests
from PIL import Image
from cvat_sdk import Client, models


ROOT = Path(__file__).resolve().parent
CVAT_URL = os.getenv("CVAT_URL", "http://localhost:8080").rstrip("/")
CVAT_USERNAME = os.getenv("CVAT_USERNAME", "admin")
CVAT_PASSWORD = os.getenv("CVAT_PASSWORD", "")
SAM3_URL = os.getenv("SAM3_URL", "").rstrip("/")
SAM3_PREDICT_URL = f"{SAM3_URL}/predict" if SAM3_URL else ""
REQUEST_TIMEOUT = int(os.getenv("SAM3_TIMEOUT", "180"))
MIN_SCORE = float(os.getenv("SAM3_MIN_SCORE", "0.30"))


def load_manifest() -> dict[str, dict[str, Any]]:
    manifest = json.loads((ROOT / "data/manifest.json").read_text(encoding="utf-8"))
    result = {}
    for name, meta in manifest["tasks"].items():
        folder = ROOT / "data" / meta["path"]
        classes = json.loads((folder / "classes.json").read_text(encoding="utf-8"))
        result[name] = {
            "folder": folder,
            "type": meta["type"],
            "classes": classes["classes"],
            "format": "Segmentation mask 1.1" if meta["type"] == "semantic" else "COCO 1.0",
        }
    return result


TASKS = load_manifest()


def require_runtime_config() -> None:
    missing = [name for name, value in (
        ("SAM3_URL", SAM3_URL), ("CVAT_PASSWORD", CVAT_PASSWORD)
    ) if not value]
    if missing:
        raise SystemExit("Thiếu cấu hình: " + ", ".join(missing) +
                         ". Xem SAM3_COLAB_SETUP.md để lấy URL endpoint và đặt biến môi trường.")
    response = requests.get(f"{SAM3_URL}/health", timeout=15)
    response.raise_for_status()
    payload = response.json()
    if payload.get("model") != "sam3" or payload.get("ready") is not True:
        raise RuntimeError(f"Endpoint không xác nhận SAM 3 sẵn sàng: {payload}")


def list_images(folder: Path) -> list[Path]:
    paths = sorted(p for p in (folder / "images").iterdir()
                   if p.is_file() and p.suffix.lower() in {".jpg", ".jpeg", ".png"})
    if not paths:
        raise RuntimeError(f"Không tìm thấy ảnh tại {folder / 'images'}")
    return paths


def task_labels(task: Any, expected: list[str]) -> dict[str, int]:
    actual = {label.name: label.id for label in task.get_labels()}
    absent = [name for name in expected if name not in actual]
    if absent:
        raise RuntimeError(f"Task CVAT #{task.id} thiếu label {absent}; không tự đổi schema task đã tồn tại.")
    return actual


def polygon_shapes(result: dict[str, Any], frame: int, label_ids: dict[str, int],
                   group_start: int) -> tuple[list[Any], int]:
    shapes = []
    group = group_start
    for item in result.get("masks", []):
        label = item.get("label")
        score = float(item.get("score", 0))
        if label not in label_ids or score < MIN_SCORE:
            continue
        polygons = item.get("polygons") or []
        usable = []
        for polygon in polygons:
            points = [float(coord) for coord in polygon]
            if len(points) >= 6 and len(points) % 2 == 0:
                usable.append(points)
        if not usable:
            continue
        # One SAM mask may have disconnected visible pieces; share a CVAT group
        # so it remains one physical instance.
        for points in usable:
            shapes.append(models.LabeledShapeRequest(
                frame=frame,
                label_id=label_ids[label],
                type="polygon",
                points=points,
                group=group,
                occluded=False,
                z_order=0,
                source="auto",
            ))
        group += 1
    return shapes, group


def predict(image_bytes: bytes, filename: str, task_type: str,
            class_names: list[str]) -> dict[str, Any]:
    response = requests.post(
        SAM3_PREDICT_URL,
        files={"file": (filename, image_bytes, "image/jpeg")},
        data={"prompts": json.dumps(class_names), "task_type": task_type,
              "min_score": str(MIN_SCORE)},
        timeout=REQUEST_TIMEOUT,
    )
    response.raise_for_status()
    result = response.json()
    if result.get("model") != "sam3":
        raise RuntimeError(f"Endpoint trả model không đúng: {result.get('model')!r}")
    if result.get("width") is None or result.get("height") is None:
        raise RuntimeError("SAM 3 response thiếu kích thước ảnh")
    return result


def verify_export(path: Path, expected_images: int, export_format: str) -> dict[str, int]:
    with zipfile.ZipFile(path) as archive:
        files = archive.namelist()
        if export_format == "COCO 1.0":
            json_files = [n for n in files if n.endswith("instances_default.json")]
            if len(json_files) != 1:
                raise RuntimeError(f"Export COCO sai cấu trúc: {json_files}")
            coco = json.loads(archive.read(json_files[0]))
            n_images, n_annotations = len(coco.get("images", [])), len(coco.get("annotations", []))
            if n_images != expected_images or n_annotations == 0:
                raise RuntimeError(f"Export COCO không hợp lệ: images={n_images}/{expected_images}, annotations={n_annotations}")
            return {"images": n_images, "annotations": n_annotations}

        masks = [n for n in files if n.startswith("SegmentationClass/") and n.lower().endswith(".png")]
        if len(masks) != expected_images:
            raise RuntimeError(f"Export semantic có {len(masks)} class mask; cần {expected_images}")
        for name in masks:
            with Image.open(io.BytesIO(archive.read(name))) as mask:
                mask.verify()
        return {"images": len(masks), "annotations": len(masks)}


def create_or_get_task(client: Client, name: str, cfg: dict[str, Any],
                       image_paths: list[Path]) -> Any:
    existing = {task.name: task for task in client.tasks.list()}
    if name in existing:
        task = client.tasks.retrieve(existing[name].id)
        if int(getattr(task, "size", 0) or 0) != len(image_paths):
            raise RuntimeError(f"Task {name} hiện có {getattr(task, 'size', 0)} frame, cần {len(image_paths)}; kiểm thứ tự/ảnh trước khi chạy.")
        return task
    labels = [models.LabelRequest(name=label) for label in cfg["classes"]]
    created = client.tasks.create(models.TaskWriteRequest(name=name, labels=labels))
    task = client.tasks.retrieve(created.id)
    task.upload_data(resources=[str(p) for p in image_paths])
    # Wait until CVAT reports all uploaded frames before reading any frame.
    deadline = time.time() + 180
    while int(getattr(task, "size", 0) or 0) != len(image_paths) and time.time() < deadline:
        time.sleep(2)
        task = client.tasks.retrieve(task.id)
    if int(getattr(task, "size", 0) or 0) != len(image_paths):
        raise RuntimeError(f"CVAT chưa nạp đủ ảnh cho {name}")
    return task


def process_task(client: Client, name: str, cfg: dict[str, Any]) -> None:
    image_paths = list_images(cfg["folder"])
    task = create_or_get_task(client, name, cfg, image_paths)
    labels = task_labels(task, cfg["classes"])
    existing = task.get_annotations()
    existing_count = len(existing.shapes) + len(existing.tracks) + len(existing.tags)
    if existing_count:
        raise RuntimeError(f"Task {name} đã có {existing_count} annotation; dừng để tránh nhân đôi. Xóa annotation cũ trong CVAT rồi chạy lại.")

    all_shapes = []
    next_group = 1
    for frame in range(len(image_paths)):
        frame_stream = task.get_frame(frame)
        image_bytes = frame_stream.getvalue() if hasattr(frame_stream, "getvalue") else frame_stream.read()
        with Image.open(io.BytesIO(image_bytes)) as image:
            width, height = image.size
        result = predict(image_bytes, image_paths[frame].name, cfg["type"], cfg["classes"])
        if result["width"] != width or result["height"] != height:
            raise RuntimeError(f"SAM3/CVAT frame size mismatch at {name} frame {frame}")
        shapes, next_group = polygon_shapes(result, frame, labels, next_group)
        print(f"  frame {frame + 1}/{len(image_paths)}: SAM3 returned {len(result.get('masks', []))} masks, accepted {len(shapes)} polygons")
        all_shapes.extend(shapes)

    if not all_shapes:
        raise RuntimeError(f"SAM 3 không trả polygon dùng được cho {name}; không ghi/export ZIP rỗng")

    client.api_client.tasks_api.partial_update_annotations(
        id=task.id,
        action="create",
        patched_labeled_data_request=models.PatchedLabeledDataRequest(shapes=all_shapes),
    )
    saved = task.get_annotations()
    if not saved.shapes:
        raise RuntimeError(f"CVAT không xác nhận annotation đã lưu cho {name}; bỏ qua export")

    out = ROOT / "submissions" / f"{name}.zip"
    out.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(prefix=f"{name}-", suffix=".zip", dir=out.parent, delete=False) as handle:
        temp_zip = Path(handle.name)
    try:
        task.export_dataset(format_name=cfg["format"], filename=str(temp_zip))
        info = verify_export(temp_zip, len(image_paths), cfg["format"])
        temp_zip.replace(out)
    except Exception:
        temp_zip.unlink(missing_ok=True)
        raise
    print(f"  saved shapes={len(saved.shapes)}; verified ZIP={out.name} {info}")


def main() -> int:
    require_runtime_config()
    client = Client(CVAT_URL)
    client.login((CVAT_USERNAME, CVAT_PASSWORD))
    failures = []
    for name, cfg in TASKS.items():
        print(f"\n=== {name} ({cfg['type']}, {cfg['format']}) ===")
        try:
            process_task(client, name, cfg)
        except Exception as exc:
            failures.append((name, str(exc)))
            print(f"ERROR {name}: {exc}", file=sys.stderr)
    print("\n=== TỔNG KẾT ===")
    if failures:
        for name, error in failures:
            print(f"FAIL {name}: {error}")
        print(f"Thành công {len(TASKS) - len(failures)}/{len(TASKS)} task; không coi các task lỗi là đã export.")
        return 1
    print(f"Đã gán nhãn và xác minh export đủ {len(TASKS)} task.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
