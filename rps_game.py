"""Taş-Kağıt-Makas oyunu (bilgisayara karşı).

Taş = 0 parmak (yumruk), Makas = 2 parmak, Kağıt = 4-5 parmak (açık el)
BOŞLUK: yeni tur başlatır (3-2-1 geri sayım), R: skoru sıfırlar.
"""

import random
import time

HAMLELER = ["Taş", "Kağıt", "Makas"]
YENER = {"Taş": "Makas", "Makas": "Kağıt", "Kağıt": "Taş"}  # anahtar, değeri yener


def parmaktan_hamle(parmak):
    if parmak is None:
        return None
    if parmak == 0:
        return "Taş"
    if parmak == 2:
        return "Makas"
    if parmak >= 4:
        return "Kağıt"
    return None  # 1 veya 3 parmak: anlaşılmadı


class RPSGame:
    GERI_SAYIM = 3.0   # saniye
    SONUC_SURESI = 3.0  # sonucun ekranda kalma süresi

    def __init__(self):
        self.durum = "bekle"  # bekle / geri_sayim / sonuc
        self.zaman = 0.0
        self.oyuncu_skor = 0
        self.bilgisayar_skor = 0
        self.oyuncu_hamle = None
        self.bilgisayar_hamle = None
        self.sonuc = ""

    def baslat(self):
        if self.durum != "geri_sayim":
            self.durum = "geri_sayim"
            self.zaman = time.time()

    def skoru_sifirla(self):
        self.oyuncu_skor = self.bilgisayar_skor = 0

    def guncelle(self, parmak):
        simdi = time.time()
        if self.durum == "geri_sayim" and simdi - self.zaman >= self.GERI_SAYIM:
            self.oyuncu_hamle = parmaktan_hamle(parmak)
            self.bilgisayar_hamle = random.choice(HAMLELER)
            if self.oyuncu_hamle is None:
                self.sonuc = "ANLAŞILMADI"
            elif self.oyuncu_hamle == self.bilgisayar_hamle:
                self.sonuc = "BERABERE"
            elif YENER[self.oyuncu_hamle] == self.bilgisayar_hamle:
                self.sonuc = "KAZANDIN!"
                self.oyuncu_skor += 1
            else:
                self.sonuc = "KAYBETTİN"
                self.bilgisayar_skor += 1
            self.durum = "sonuc"
            self.zaman = simdi
        elif self.durum == "sonuc" and simdi - self.zaman >= self.SONUC_SURESI:
            self.durum = "bekle"

    def ciz(self, frame, yazi, parmak):
        h, w = frame.shape[:2]
        orta = w // 2

        yazi.ekle(f"Sen {self.oyuncu_skor} - {self.bilgisayar_skor} Bilgisayar",
                  (w - 20, 20), 32, (255, 255, 255), "ra")

        if self.durum == "bekle":
            yazi.ekle("Başlamak için BOŞLUK tuşuna bas", (orta, h // 2), 40, (0, 255, 255), "mm")
            yazi.ekle("Taş = yumruk   Makas = 2 parmak   Kağıt = açık el",
                      (orta, h // 2 + 50), 26, (255, 255, 255), "mm")

        elif self.durum == "geri_sayim":
            kalan = self.GERI_SAYIM - (time.time() - self.zaman)
            yazi.ekle(str(int(kalan) + 1), (orta, h // 2), 160, (0, 255, 255), "mm")
            hamle = parmaktan_hamle(parmak) or "?"
            yazi.ekle(f"Senin hamlen: {hamle}", (orta, h // 2 + 120), 34, (255, 255, 255), "mm")

        elif self.durum == "sonuc":
            renk = {"KAZANDIN!": (0, 255, 0), "KAYBETTİN": (0, 0, 255)}.get(self.sonuc, (0, 255, 255))
            yazi.ekle(self.sonuc, (orta, h // 2 - 40), 80, renk, "mm")
            oyuncu = self.oyuncu_hamle or "?"
            yazi.ekle(f"Sen: {oyuncu}    Bilgisayar: {self.bilgisayar_hamle}",
                      (orta, h // 2 + 40), 38, (255, 255, 255), "mm")
            if self.oyuncu_hamle is None:
                yazi.ekle("Yumruk, 2 parmak veya açık el göster", (orta, h // 2 + 90),
                          26, (200, 200, 200), "mm")
