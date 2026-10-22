"""Face detection (OpenCV YuNet) + face embeddings (OpenCV SFace) + cosine matching.

Only 128-d embeddings are stored - raw face photos are never saved.
"""
import base64
import json
import threading
from typing import List, Optional, Tuple

import cv2
import numpy as np

from .config import settings

DET_MODEL = settings.MODEL_DIR / "face_detection_yunet_2023mar.onnx"
REC_MODEL = settings.MODEL_DIR / "face_recognition_sface_2021dec.onnx"
MAX_WIDTH = 640


class ModelsMissing(RuntimeError):
    pass


class FaceEngine:
    def __init__(self):
        self._lock = threading.Lock()
        self.detector = None
        self.recognizer = None
        self._gallery: Optional[List[Tuple[int, np.ndarray]]] = None

    def _load(self):
        if self.detector is not None:
            return
        if not DET_MODEL.exists() or not REC_MODEL.exists():
            raise ModelsMissing("Face models not found. Run:  python scripts/download_models.py")
        self.detector = cv2.FaceDetectorYN.create(
            str(DET_MODEL), "", (320, 320), settings.DETECT_THRESHOLD, 0.3, 5000)
        self.recognizer = cv2.FaceRecognizerSF.create(str(REC_MODEL), "")

    @staticmethod
    def decode(image_b64: str) -> np.ndarray:
        if "," in image_b64:
            image_b64 = image_b64.split(",", 1)[1]
        data = np.frombuffer(base64.b64decode(image_b64), np.uint8)
        img = cv2.imdecode(data, cv2.IMREAD_COLOR)
        if img is None:
            raise ValueError("Invalid image")
        h, w = img.shape[:2]
        if w > MAX_WIDTH:
            img = cv2.resize(img, (MAX_WIDTH, int(h * MAX_WIDTH / w)))
        return img

    def detect(self, img: np.ndarray) -> np.ndarray:
        self._load()
        h, w = img.shape[:2]
        with self._lock:
            self.detector.setInputSize((w, h))
            _, faces = self.detector.detect(img)
        return faces if faces is not None else np.empty((0, 15))

    def embed(self, img: np.ndarray, face_row: np.ndarray) -> np.ndarray:
        self._load()
        with self._lock:
            aligned = self.recognizer.alignCrop(img, face_row)
            feat = self.recognizer.feature(aligned).flatten().astype(np.float32)
        return feat / (np.linalg.norm(feat) + 1e-9)

    def invalidate(self):
        self._gallery = None

    def load_gallery(self, students) -> None:
        gallery = []
        for s in students:
            try:
                embs = np.array(json.loads(s.face_reference or "[]"), dtype=np.float32)
            except Exception:
                continue
            if embs.ndim == 2 and len(embs):
                gallery.append((s.id, embs))
        self._gallery = gallery

    def has_gallery(self) -> bool:
        return self._gallery is not None

    def best(self, emb: np.ndarray, exclude: Optional[int] = None) -> Tuple[Optional[int], float]:
        """Best candidate regardless of threshold (caller decides: match / uncertain / unknown)."""
        best_id, best = None, -1.0
        for pk, embs in self._gallery or []:
            if pk == exclude:
                continue
            score = float(np.max(embs @ emb))
            if score > best:
                best, best_id = score, pk
        return best_id, max(best, 0.0)

    def match(self, emb: np.ndarray) -> Tuple[Optional[int], float]:
        best_id, best = None, -1.0
        for pk, embs in self._gallery or []:
            score = float(np.max(embs @ emb))
            if score > best:
                best, best_id = score, pk
        if best_id is not None and best >= settings.MATCH_THRESHOLD:
            return best_id, best
        return None, max(best, 0.0)


engine = FaceEngine()
