"""Ekrana Türkçe karakterli (ş, ğ, ı, İ, ö, ü, ç) yazı yazmak için yardımcı.

cv2.putText Türkçe harfleri çizemediği için Pillow kullanıyoruz.
Her karede yazılar önce listeye eklenir, sonra tek seferde çizilir (hızlı olsun diye).
"""

import os

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

FONT_ADAYLARI = [
    r"C:\Windows\Fonts\segoeuib.ttf",  # Segoe UI Kalın
    r"C:\Windows\Fonts\arialbd.ttf",   # Arial Kalın
    r"C:\Windows\Fonts\arial.ttf",
]


class TextLayer:
    def __init__(self):
        self._yazilar = []
        self._fontlar = {}
        self._font_yolu = next((p for p in FONT_ADAYLARI if os.path.exists(p)), None)

    def _font(self, boyut):
        if boyut not in self._fontlar:
            if self._font_yolu:
                self._fontlar[boyut] = ImageFont.truetype(self._font_yolu, boyut)
            else:
                self._fontlar[boyut] = ImageFont.load_default()
        return self._fontlar[boyut]

    def ekle(self, metin, konum, boyut=28, renk=(255, 255, 255), hiza="la"):
        """renk BGR (opencv gibi). hiza: 'la' sol-üst, 'mm' tam orta, 'ra' sağ-üst."""
        self._yazilar.append((metin, konum, boyut, renk, hiza))

    def ciz(self, frame):
        if not self._yazilar:
            return frame
        img = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        d = ImageDraw.Draw(img)
        for metin, konum, boyut, (b, g, r), hiza in self._yazilar:
            d.text(konum, metin, font=self._font(boyut), fill=(r, g, b), anchor=hiza,
                   stroke_width=max(1, boyut // 14), stroke_fill=(0, 0, 0))
        self._yazilar.clear()
        frame[:] = cv2.cvtColor(np.array(img), cv2.COLOR_RGB2BGR)
        return frame
