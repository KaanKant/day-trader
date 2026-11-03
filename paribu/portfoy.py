#!/usr/bin/env python3
"""
Portföy testi
=============
Sermaye coinlere eşit bölünür (her coine bir "kasa"). Her kasa kendi sinyaline göre
coinde ya da nakitte durur. Soru: hepsi birlikteyken toplam düşüş ve getiri ne olur?

Kurallar
  al_tut         : her kasa baştan sona coinde
  sma50          : kapanış 50 günlük ortalamanın üstündeyse coinde
  donchian       : 20 günün zirvesini kırınca al, 10 günün dibini kırınca sat
  *_btc          : ayrıca BTC kapanışı kendi 50 günlük ortalamasının üstünde olmalı (piyasa rejimi)
  *_vol          : coindeki pay, son 20 günlük oynaklığa göre küçültülür (yıllık %60 hedef, en fazla %100)

Karar günün kapanışında verilir, işlem ertesi günün açılışında yapılır. Ücret pay
değişimi kadar ödenir. Oynaklık ayarında küçük değişiklikler (<%20) yapılmaz.

  python3 paribu/portfoy.py --ucret 0.28
"""
from __future__ import annotations

import argparse
import math
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backtest as bt  # noqa: E402
import veri  # noqa: E402

KOK = Path(__file__).resolve().parent
HEDEF_GUNLUK_VOL = 0.60 / math.sqrt(365)
ESIK = 0.20


def hizala(gunlukler):
    """Tüm coinlerde ortak olan günler: {coin: [mum,...]} aynı uzunlukta."""
    ortak = set.intersection(*[{g["t"] for g in v} for v in gunlukler.values()])
    return {c: [g for g in v if g["t"] in ortak] for c, v in gunlukler.items()}


def oynaklik(gunluk, n=20):
    out = [None] * len(gunluk)
    for i in range(n, len(gunluk)):
        r = [math.log(gunluk[k]["c"] / gunluk[k - 1]["c"]) for k in range(i - n + 1, i + 1)]
        out[i] = statistics.pstdev(r)
    return out


def sinyaller(gunluk, kural):
    if kural.startswith("al_tut"):
        return [True] * len(gunluk)
    if kural.startswith("sma50"):
        return bt.sma_sinyal(gunluk, 50)
    if kural.startswith("donchian"):
        return bt.donchian_sinyal(gunluk, 20, 10)
    raise ValueError(kural)


def calistir(gunlukler, kural, maliyet):
    coinler = list(gunlukler)
    T = len(next(iter(gunlukler.values())))
    btc = gunlukler.get("BTC")
    btc_ok = bt.sma_sinyal(btc, 50) if (btc and "_btc" in kural) else [True] * T
    sinyal = {c: sinyaller(gunlukler[c], kural) for c in coinler}
    vol = {c: oynaklik(gunlukler[c]) for c in coinler} if "_vol" in kural else None

    kasa = {c: 1.0 / len(coinler) for c in coinler}
    pay = {c: 0.0 for c in coinler}
    egri, ucret, islem, piyasada = [1.0], 0.0, 0, []
    for j in range(1, T):
        for c in coinler:
            g = gunlukler[c]
            hedef = 1.0 if (sinyal[c][j - 1] and btc_ok[j - 1]) else 0.0
            if hedef and vol is not None:
                v = vol[c][j - 1]
                hedef = min(1.0, HEDEF_GUNLUK_VOL / v) if v else 1.0
            fark = abs(hedef - pay[c])
            # Oynaklık ayarında küçük düzeltme yapma; giriş/çıkış her zaman yapılır
            if fark > 0 and (hedef == 0 or pay[c] == 0 or fark >= ESIK):
                if pay[c] == 0 and hedef > 0:
                    islem += 1
                u = kasa[c] * fark * maliyet
                kasa[c] -= u
                ucret += u
                pay[c] = hedef
            sonraki = g[j + 1]["o"] if j + 1 < T else g[j]["c"]
            kasa[c] *= 1 + pay[c] * (sonraki / g[j]["o"] - 1)
        egri.append(sum(kasa.values()))
        piyasada.append(statistics.mean(pay.values()))
    # sonda her şey satılır
    son = sum(k * (1 - p * maliyet) for k, p in ((kasa[c], pay[c]) for c in coinler))
    egri.append(son)
    yil = T / 365.0
    yillik = (son ** (1 / yil) - 1) * 100 if son > 0 else -100.0
    dusus = bt.max_dusus(egri)
    return {"getiri": (son - 1) * 100, "yillik": yillik, "dusus": dusus,
            "calmar": yillik / abs(dusus) if dusus else 0.0,
            "piyasada": statistics.mean(piyasada) * 100 if piyasada else 0.0,
            "islem_yil": islem / yil, "ucret": ucret * 100}


KURALLAR = ["al_tut", "sma50", "sma50_btc", "sma50_vol", "sma50_btc_vol",
            "donchian", "donchian_btc", "donchian_vol", "donchian_btc_vol"]


def tablo(sonuc, baslik):
    L = ["### " + baslik, "",
         "| Kural | Toplam getiri | Yıllık | En büyük düşüş | Yıllık / düşüş | Piyasada (ort. pay) | Yeni giriş / yıl | Ödenen ücret |",
         "|---|---|---|---|---|---|---|---|"]
    for k in sorted(sonuc, key=lambda k: -sonuc[k]["calmar"]):
        r = sonuc[k]
        L.append("| %s | %+.0f%% | %+.1f%% | %.0f%% | %.2f | %%%.0f | %.0f | %%%.1f |" % (
            k, r["getiri"], r["yillik"], r["dusus"], r["calmar"], r["piyasada"], r["islem_yil"], r["ucret"]))
    return L + [""]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ucret", type=float, default=0.28)
    ap.add_argument("--kayma", type=float, default=0.05)
    ap.add_argument("--yil", type=int, default=6)
    ap.add_argument("--coinler", default=",".join(bt.COINLER))
    ap.add_argument("--cikti", default=str(KOK / "PORTFOY-RAPORU.md"))
    a = ap.parse_args(argv)
    maliyet = (a.ucret + a.kayma) / 100
    simdi = datetime.now(timezone.utc)

    coinler = [c.strip().upper() for c in a.coinler.split(",") if c.strip()]
    try:
        uygun = veri.paribu_uygun(coinler, veri.paribu_marketleri())
        coinler = [c for c in coinler if "usdt" in uygun.get(c, [])]
    except veri.VeriHatasi as e:
        print("Paribu listesi okunamadı:", e)
    if "BTC" not in coinler:
        coinler.insert(0, "BTC")
    gunlukler = {}
    for c in coinler:
        try:
            gunlukler[c] = veri.mumlar(c + "USDT", "1d", simdi - timedelta(days=365 * a.yil))
        except veri.VeriHatasi as e:
            print("%s atlandı: %s" % (c, e))
    gunlukler = hizala({c: v for c, v in gunlukler.items() if len(v) > 300})
    T = len(next(iter(gunlukler.values())))
    orta = T // 2
    yarim = [{c: v[:orta] for c, v in gunlukler.items()}, {c: v[orta:] for c, v in gunlukler.items()}]

    tum = {k: calistir(gunlukler, k, maliyet) for k in KURALLAR}
    y = [{k: calistir(h, k, maliyet) for k in KURALLAR} for h in yarim]
    ilk = next(iter(gunlukler.values()))
    L = ["# Portföy testi", "",
         "Tarih: %s UTC | Maliyet: her yönde ücret %%%.2f + kayma %%%.2f" % (simdi.strftime("%Y-%m-%d %H:%M"), a.ucret, a.kayma),
         "Coinler (sermaye eşit bölündü): " + ", ".join(gunlukler),
         "Dönem: %s → %s (%d gün). Yarılar: %s'e kadar / sonrası." % (
             bt.tarih(ilk[0]["t"]), bt.tarih(ilk[-1]["t"]), T, bt.tarih(ilk[orta]["t"])), ""]
    L += tablo(tum, "Tüm dönem")
    L += tablo(y[0], "1. yarı (eski)")
    L += tablo(y[1], "2. yarı (yeni)")
    L += ["Notlar:",
          "- \"Yıllık / düşüş\" (Calmar): yıllık getirinin en büyük düşüşe oranı. Yüksek olan, aldığı riske göre daha çok kazandırmış demek. Tablolar buna göre sıralı.",
          "- Getiriler USDT cinsinden. Coin listesi bugün seçildi (hayatta kalanlar), bu sonuçları olduğundan iyi gösterebilir.",
          "- Geçmiş sonuç geleceği garanti etmez."]
    Path(a.cikti).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
