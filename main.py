"""Kamerayla El Takibi - webcam'den el tespiti, eklem çizimi ve parmak sayma.

Tuşlar:
  1 : Parmak sayma
  2 : Ses kontrolü (0 parmak sessiz ... 5 parmak tam ses)
  3 : Taş-Kağıt-Makas (BOŞLUK: tur başlat, R: skoru sıfırla)
  S : Ekran görüntüsü kaydet (screenshots/ klasörüne)
  q / ESC : Çıkış
"""

import os
import time

import cv2

from hand_tracker import HandTracker
from rps_game import RPSGame
from text_utils import TextLayer
from volume_control import VolumeController

MODLAR = {ord("1"): "sayma", ord("2"): "ses", ord("3"): "oyun"}
MOD_ADLARI = {"sayma": "Parmak Sayma", "ses": "Ses Kontrolü", "oyun": "Taş-Kağıt-Makas"}
EKRAN_GORUNTUSU_KLASORU = os.path.join(os.path.dirname(os.path.abspath(__file__)), "screenshots")


def ekran_goruntusu_kaydet(frame, mod):
    """Her mod için screenshots/<mod>.png olarak kaydeder (README bu dosyaları kullanır)."""
    os.makedirs(EKRAN_GORUNTUSU_KLASORU, exist_ok=True)
    yol = os.path.join(EKRAN_GORUNTUSU_KLASORU, f"{mod}.png")
    cv2.imwrite(yol, frame)
    print("Ekran görüntüsü kaydedildi:", yol)


def main(camera_index=0):
    cap = cv2.VideoCapture(camera_index, cv2.CAP_DSHOW)  # Windows'ta hızlı açılış
    if not cap.isOpened():
        cap = cv2.VideoCapture(camera_index)
    if not cap.isOpened():
        print("Kamera açılamadı! Başka bir uygulama kamerayı kullanıyor olabilir.")
        return

    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)

    tracker = HandTracker(max_hands=2)
    yazi = TextLayer()
    ses = VolumeController()
    oyun = RPSGame()
    mod = "sayma"
    prev = time.time()
    kaydedildi_zamani = 0.0

    try:
        while True:
            ok, frame = cap.read()
            if not ok:
                print("Kameradan görüntü alınamadı.")
                break

            frame = cv2.flip(frame, 1)  # ayna görüntüsü, daha doğal
            h, w = frame.shape[:2]
            hands = tracker.process(frame)

            for hand in hands:
                tracker.draw(frame, hand, yazi)

            total = sum(hd["fingers"] for hd in hands)
            # Ses ve oyunda ilk görünen el kullanılır
            ana_parmak = hands[0]["fingers"] if hands else None

            if mod == "ses":
                ses.guncelle(ana_parmak)
                ses.ciz(frame, yazi)
            elif mod == "oyun":
                oyun.guncelle(ana_parmak)
                oyun.ciz(frame, yazi, ana_parmak)

            # Bilgi paneli
            now = time.time()
            fps = 1.0 / max(now - prev, 1e-6)
            prev = now
            cv2.rectangle(frame, (10, 10), (360, 150), (0, 0, 0), -1)
            yazi.ekle(MOD_ADLARI[mod], (22, 18), 26, (0, 255, 255))
            yazi.ekle(f"Parmak: {total}", (22, 52), 48, (0, 255, 0))
            yazi.ekle(f"El: {len(hands)}    FPS: {fps:.0f}", (22, 112), 22, (255, 255, 255))

            # Alt bilgi satırı
            cv2.rectangle(frame, (0, h - 40), (w, h), (0, 0, 0), -1)
            yardim = "1: Sayma    2: Ses    3: Oyun    S: Görüntü kaydet    q: Çıkış"
            if mod == "oyun":
                yardim += "    BOŞLUK: Tur başlat    R: Skoru sıfırla"
            yazi.ekle(yardim, (15, h - 33), 22, (255, 255, 255))

            yazi.ciz(frame)
            # Kaydedilen görüntüde "Kaydedildi" yazısı çıkmasın diye önce kopyasını al
            temiz_kare = frame.copy()
            if now - kaydedildi_zamani < 1.5:
                cv2.putText(frame, "Kaydedildi", (w // 2 - 110, 60), cv2.FONT_HERSHEY_SIMPLEX,
                            1.2, (0, 255, 0), 3, cv2.LINE_AA)
            cv2.imshow("Kamerayla El Takibi", frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (ord("q"), 27):
                break
            if key in (ord("s"), ord("S")):
                ekran_goruntusu_kaydet(temiz_kare, mod)
                kaydedildi_zamani = now
            if key in MODLAR:
                mod = MODLAR[key]
            elif mod == "oyun" and key == ord(" "):
                oyun.baslat()
            elif mod == "oyun" and key in (ord("r"), ord("R")):
                oyun.skoru_sifirla()
    finally:
        tracker.close()
        cap.release()
        cv2.destroyAllWindows()


if __name__ == "__main__":
    main()
