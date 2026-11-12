# SAM 3 auto-label pipeline (all nine Day 03 tasks)

`auto_full_pipeline.py` sends each image and the task's own class list to SAM 3 using text prompts. SAM 3 returns one or more masks per class; the runner converts the contours to CVAT polygons, writes them to the matching frame/label, then exports the task's required CVAT format. It checks the exported ZIP and stops a task if the annotations are empty.

SAM 3 is used here because it can find and segment instances from text concepts. SAM 2's automatic mask generator proposes unlabeled regions, so it would need a separate detector/classifier to produce the nine task schemas.

## 1. Start SAM 3 in Colab

Use a GPU runtime. The official SAM 3 repo currently requires Python 3.12+, PyTorch 2.7+, a CUDA 12.6+ GPU, and checkpoint access granted through Hugging Face. If Colab's runtime does not meet those requirements or the checkpoint request is pending, this service cannot start.

Run these Colab cells:

```python
!git clone https://github.com/facebookresearch/sam3.git /content/sam3
%cd /content/sam3
!pip install -e .
!pip install flask pyngrok opencv-python-headless
```

Sign in to Hugging Face in a private cell (do not commit or share the token):

```python
from huggingface_hub import login
login()  # paste a token only after SAM 3 checkpoint access has been granted
```

Upload this repository's `sam3_colab_server.py` to `/content/sam3_colab_server.py` in Colab. Start an Ngrok tunnel:

```python
from getpass import getpass
from pyngrok import ngrok
ngrok.set_auth_token(getpass("Ngrok auth token: "))
public_url = ngrok.connect(7860, "http").public_url
print(public_url)
```

Start the server in another cell and leave that cell running:

```python
!python /content/sam3_colab_server.py
```

The server loads the official image model and exposes `/health` and `/predict`. The Ngrok URL changes when the tunnel/runtime restarts; use the new URL in the local setup each time.

## 2. Run the local CVAT importer

From the project root on Windows PowerShell, set credentials and the current Ngrok URL for this terminal session:

```powershell
$env:SAM3_URL = "https://YOUR-CURRENT-NGROK-URL"
$env:CVAT_URL = "http://localhost:8080"
$env:CVAT_USERNAME = "admin"
$env:CVAT_PASSWORD = "YOUR-CVAT-PASSWORD"
python -m pip install -r requirements-autolabel.txt
python auto_full_pipeline.py
```

The runner processes `easy_semantic`, `medium_instance`, `hard_panoptic`, then all six checkpoints from `data/manifest.json`. It uses each task's `classes.json`, not the first label for every result. Export formats are selected from task type: semantic uses Segmentation mask 1.1; instance and panoptic use COCO 1.0.

The runner intentionally stops if an existing task has annotation data, a task has missing labels or the wrong image count, the SAM endpoint is unavailable, CVAT does not confirm saved shapes, or the export has no masks. This prevents a rerun from silently duplicating annotations or replacing a usable ZIP with an empty one. If the task has stale annotations, review/delete them in CVAT first, then rerun. Check every generated mask in CVAT before submission; SAM predictions are drafts and can miss objects, leak into the background, or confuse road/sidewalk and thin structures.

## Endpoint response contract

`POST /predict` receives multipart `file`, JSON-array `prompts`, `task_type`, and `min_score`. It returns the model name, image dimensions, and polygons associated with the exact class prompt. The client checks this response and checks the exported ZIP before writing the final `submissions/<task>.zip`.
