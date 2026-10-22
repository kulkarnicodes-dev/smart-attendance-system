"""Download the two OpenCV Zoo face models (~40 MB total). Run once:  python scripts/download_models.py"""
import sys
import urllib.request
from pathlib import Path

DEST = Path(__file__).resolve().parent.parent / "models"
DEST.mkdir(exist_ok=True)
FILES = {
    "face_detection_yunet_2023mar.onnx":
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_detection_yunet/face_detection_yunet_2023mar.onnx",
    "face_recognition_sface_2021dec.onnx":
        "https://github.com/opencv/opencv_zoo/raw/main/models/face_recognition_sface/face_recognition_sface_2021dec.onnx",
}

for name, url in FILES.items():
    target = DEST / name
    if target.exists() and target.stat().st_size > 100_000:
        print(f"[skip] {name} already present")
        continue
    print(f"[download] {name} ...")
    try:
        urllib.request.urlretrieve(url, target)
        print(f"[ok] {target.stat().st_size // 1024} KB")
    except Exception as e:
        print(f"[error] {e}\nDownload manually from:\n  {url}\nand put it in: {DEST}")
        sys.exit(1)
print("All models ready.")
