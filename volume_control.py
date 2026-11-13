"""Parmak sayısıyla Windows ses seviyesini kontrol etme.

0 parmak = sessiz, 1 = %20, 2 = %40, 3 = %60, 4 = %80, 5 = %100

Ek kütüphane gerektirmez: klavyedeki ses aç/kıs tuşlarına basılmış gibi yapar
(Windows'ta her basış sesi %2 değiştirir).
Yanlışlıkla değişmesin diye aynı parmak sayısı kısa bir süre sabit tutulmalı.
"""

import ctypes
import time

import cv2

VK_VOLUME_DOWN = 0xAE
VK_VOLUME_UP = 0xAF
KEYEVENTF_KEYUP = 0x0002


def _tusa_bas(tus, adet):
    user32 = ctypes.windll.user32
    for _ in range(adet):
        user32.keybd_event(tus, 0, 0, 0)
        user32.keybd_event(tus, 0, KEYEVENTF_KEYUP, 0)


class VolumeController:
    BEKLEME = 0.8  # saniye: parmak sayısı bu kadar sabit kalınca ses değişir

    def __init__(self):
        self.uygulanan = None   # en son ayarlanan parmak sayısı
        self.aday = None        # şu an gösterilen parmak sayısı
        self.baslangic = 0.0
        self.ilerleme = 0.0

    def guncelle(self, parmak):
        """parmak: el yoksa None. El görünmüyorsa ses değişmez."""
        simdi = time.time()
        if parmak is None:
            self.aday = None
            self.ilerleme = 0.0
            return
        parmak = min(parmak, 5)
        if parmak != self.aday:
            self.aday = parmak
            self.baslangic = simdi
        self.ilerleme = min((simdi - self.baslangic) / self.BEKLEME, 1.0)
        if self.ilerleme >= 1.0 and parmak != self.uygulanan:
            self.ses_ayarla(parmak * 20)
            self.uygulanan = parmak

    @staticmethod
    def ses_ayarla(yuzde):
        # Önce sesi tamamen kıs (50 x %2), sonra istenen seviyeye kadar aç
        _tusa_bas(VK_VOLUME_DOWN, 50)
        _tusa_bas(VK_VOLUME_UP, yuzde // 2)

    def ciz(self, frame, yazi):
        h, w = frame.shape[:2]
        x1, x2 = w - 90, w - 40
        y1, y2 = 150, h - 120

        # Ses çubuğu
        cv2.rectangle(frame, (x1, y1), (x2, y2), (255, 255, 255), 2)
        if self.uygulanan is not None:
            dolu = int((y2 - y1) * self.uygulanan / 5)
            cv2.rectangle(frame, (x1 + 3, y2 - dolu), (x2 - 3, y2 - 3), (0, 200, 0), -1)
            yazi.ekle(f"%{self.uygulanan * 20}", ((x1 + x2) // 2, y2 + 35), 30, (0, 255, 0), "mm")
        else:
            yazi.ekle("?", ((x1 + x2) // 2, y2 + 35), 30, (200, 200, 200), "mm")
        yazi.ekle("SES", ((x1 + x2) // 2, y1 - 25), 28, (255, 255, 255), "mm")

        # Bekleme göstergesi: yeni bir değer onaylanmak üzereyken
        if self.aday is not None and self.aday != self.uygulanan:
            merkez = ((x1 + x2) // 2 - 110, (y1 + y2) // 2)
            cv2.circle(frame, merkez, 40, (90, 90, 90), 6, cv2.LINE_AA)
            if self.ilerleme > 0.02:
                cv2.ellipse(frame, merkez, (40, 40), -90, 0, int(360 * self.ilerleme),
                            (0, 255, 255), 6, cv2.LINE_AA)
            yazi.ekle(f"%{self.aday * 20}", merkez, 24, (0, 255, 255), "mm")
