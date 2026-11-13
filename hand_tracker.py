"""El takibi ve parmak sayma modülü (MediaPipe Tasks - HandLandmarker)."""

import math
import os
import time
import urllib.request
from collections import Counter, deque

import cv2
import mediapipe as mp
from mediapipe.tasks.python import BaseOptions, vision

MODEL_URL = (
    "https://storage.googleapis.com/mediapipe-models/hand_landmarker/"
    "hand_landmarker/float16/latest/hand_landmarker.task"
)
MODEL_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "models", "hand_landmarker.task")

# 21 eklem noktası arasındaki bağlantılar (kemikler)
HAND_CONNECTIONS = [
    (0, 1), (1, 2), (2, 3), (3, 4),          # başparmak
    (0, 5), (5, 6), (6, 7), (7, 8),          # işaret
    (5, 9), (9, 10), (10, 11), (11, 12),     # orta
    (9, 13), (13, 14), (14, 15), (15, 16),   # yüzük
    (13, 17), (0, 17), (17, 18), (18, 19), (19, 20),  # serçe + avuç
]

# Parmak uçları ve bir alt eklemleri (PIP)
FINGER_TIPS = [8, 12, 16, 20]
FINGER_PIPS = [6, 10, 14, 18]
FINGERTIP_IDS = [4, 8, 12, 16, 20]


def ensure_model(path: str = MODEL_PATH) -> str:
    """Model dosyası yoksa indirir."""
    if not os.path.exists(path):
        os.makedirs(os.path.dirname(path), exist_ok=True)
        print("Model indiriliyor (ilk çalıştırmada bir kez)...")
        urllib.request.urlretrieve(MODEL_URL, path)
        print("Model indirildi:", path)
    return path


def _dist(a, b) -> float:
    return math.hypot(a[0] - b[0], a[1] - b[1])


def count_fingers(pts) -> int:
    """Açık parmak sayısını hesaplar.

    pts: 21 noktanın (x, y) piksel koordinatları.
    Mesafe tabanlı kurallar kullanıldığı için el döndürülse de çalışır.
    """
    wrist = pts[0]
    count = 0

    # İşaret, orta, yüzük, serçe: uç bileğe PIP ekleminden daha uzaksa açıktır
    for tip, pip in zip(FINGER_TIPS, FINGER_PIPS):
        if _dist(pts[tip], wrist) > _dist(pts[pip], wrist):
            count += 1

    # Başparmak: uç, serçe kökünden (17) IP ekleminden (3) daha uzaksa
    # ve işaret parmağı kökünden (5) yeterince uzaktaysa açıktır
    palm = _dist(pts[0], pts[9]) or 1.0
    if (_dist(pts[4], pts[17]) > _dist(pts[3], pts[17])
            and _dist(pts[4], pts[5]) > 0.45 * palm):
        count += 1

    return count


class HandTracker:
    def __init__(self, max_hands=2, detection_conf=0.6, tracking_conf=0.5, smooth_frames=5):
        options = vision.HandLandmarkerOptions(
            base_options=BaseOptions(model_asset_path=ensure_model()),
            running_mode=vision.RunningMode.VIDEO,
            num_hands=max_hands,
            min_hand_detection_confidence=detection_conf,
            min_hand_presence_confidence=detection_conf,
            min_tracking_confidence=tracking_conf,
        )
        self.landmarker = vision.HandLandmarker.create_from_options(options)
        self._last_ts = -1
        # Sayının titrememesi için son birkaç karenin çoğunluk oyu
        self._history = {"Left": deque(maxlen=smooth_frames), "Right": deque(maxlen=smooth_frames)}

    def process(self, frame_bgr):
        """Kareyi işler; her el için {'label', 'points', 'fingers'} listesi döndürür."""
        h, w = frame_bgr.shape[:2]
        rgb = cv2.cvtColor(frame_bgr, cv2.COLOR_BGR2RGB)
        image = mp.Image(image_format=mp.ImageFormat.SRGB, data=rgb)

        ts = int(time.monotonic() * 1000)
        if ts <= self._last_ts:  # zaman damgası kesinlikle artmalı
            ts = self._last_ts + 1
        self._last_ts = ts

        result = self.landmarker.detect_for_video(image, ts)

        hands = []
        seen = set()
        for landmarks, handedness in zip(result.hand_landmarks, result.handedness):
            # Mediapipe'ın etiketi, aynalanmış (cv2.flip) görüntüde ters çıkıyor;
            # gerçek eli göstermesi için çeviriyoruz.
            label = "Left" if handedness[0].category_name == "Right" else "Right"
            pts = [(int(lm.x * w), int(lm.y * h)) for lm in landmarks]
            raw = count_fingers(pts)

            hist = self._history.setdefault(label, deque(maxlen=5))
            hist.append(raw)
            fingers = Counter(hist).most_common(1)[0][0]
            seen.add(label)

            hands.append({"label": label, "points": pts, "fingers": fingers})

        # Kaybolan elin geçmişini temizle
        for label, hist in self._history.items():
            if label not in seen:
                hist.clear()
        return hands

    @staticmethod
    def draw(frame, hand, yazi):
        """Eklem noktalarını çizer; elin üstüne 'Sağ: 3' etiketini yazı katmanına ekler."""
        pts = hand["points"]
        for a, b in HAND_CONNECTIONS:
            cv2.line(frame, pts[a], pts[b], (255, 255, 255), 2, cv2.LINE_AA)
        for i, p in enumerate(pts):
            color = (0, 0, 255) if i in FINGERTIP_IDS else (0, 200, 0)
            cv2.circle(frame, p, 6 if i in FINGERTIP_IDS else 4, color, -1, cv2.LINE_AA)

        name = "Sağ" if hand["label"] == "Right" else "Sol"
        x = min(p[0] for p in pts)
        y = max(min(p[1] for p in pts) - 40, 5)
        yazi.ekle(f"{name}: {hand['fingers']}", (x, y), 28, (0, 255, 255))

    def close(self):
        self.landmarker.close()
