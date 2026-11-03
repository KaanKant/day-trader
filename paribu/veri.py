"""
Veri katmanı
============
- Mum verisi: Binance'in herkese açık piyasa verisi (data-api.binance.vision).
  Paribu API'sinde geçmiş mum verisi olmadığı için sinyal ve test verisi buradan gelir.
- Paribu market listesi: https://api.paribu.com/initials/config?scope=markets (herkese açık).

Sadece standart Python kütüphaneleri kullanılır. Anahtar gerekmez.
"""
from __future__ import annotations

import json
import time
import urllib.error
import urllib.request
from datetime import datetime, timezone

BINANCE = "https://data-api.binance.vision/api/v3/klines"
PARIBU_CONFIG = "https://api.paribu.com/initials/config?scope=markets"
UA = "paribu-trader/0.1 (+https://github.com/KaanKant/day-trader)"

ARALIK_MS = {"15m": 15 * 60_000, "1h": 3_600_000, "4h": 4 * 3_600_000, "1d": 86_400_000}


class VeriHatasi(Exception):
    pass


def _get(url, timeout=30, deneme=3):
    son = None
    for i in range(deneme):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept": "application/json"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return json.loads(r.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            son = "HTTP %d" % e.code
            if e.code == 429 or e.code >= 500:
                time.sleep(2 * (i + 1))
                continue
            break
        except (urllib.error.URLError, OSError, ValueError) as e:
            son = str(e)
            time.sleep(2 * (i + 1))
    raise VeriHatasi("%s alınamadı: %s" % (url.split("?")[0], son))


def mumlar(sembol, aralik, baslangic, bitis=None, bekle=0.15, getir=_get):
    """Binance mumları: [{"t": açılış ms, "o","h","l","c","v"}], eskiden yeniye.

    sembol: "BTCUSDT"  aralik: "15m" | "1h" | "4h" | "1d"
    baslangic / bitis: datetime (UTC) ya da ms.
    """
    adim = ARALIK_MS[aralik]
    bas = baslangic if isinstance(baslangic, int) else int(baslangic.timestamp() * 1000)
    son = bitis if isinstance(bitis, int) else int((bitis or datetime.now(timezone.utc)).timestamp() * 1000)
    out = []
    while bas < son:
        url = "%s?symbol=%s&interval=%s&startTime=%d&endTime=%d&limit=1000" % (
            BINANCE, sembol, aralik, bas, son)
        satirlar = getir(url)
        if not satirlar:
            break
        for k in satirlar:
            out.append({"t": int(k[0]), "o": float(k[1]), "h": float(k[2]),
                        "l": float(k[3]), "c": float(k[4]), "v": float(k[5])})
        yeni = int(satirlar[-1][0]) + adim
        if yeni <= bas:
            break
        bas = yeni
        time.sleep(bekle)
    # Henüz kapanmamış son mumu at
    simdi = int(time.time() * 1000)
    while out and out[-1]["t"] + adim > simdi:
        out.pop()
    # tekrar eden mum olmasın
    tekil, gorulen = [], set()
    for m in out:
        if m["t"] not in gorulen:
            gorulen.add(m["t"])
            tekil.append(m)
    return tekil


def paribu_marketleri(getir=_get):
    """Paribu'da işlem gören market id'leri: {"btc_tl", "btc_usdt", ...}"""
    data = getir(PARIBU_CONFIG)
    markets = ((data or {}).get("payload") or {}).get("markets") or {}
    return set(markets)


def paribu_uygun(coinler, marketler):
    """Paribu'da TL ya da USDT paritesi olan coinler, hangi paritelerin olduğuyla."""
    out = {}
    for c in coinler:
        k = c.lower()
        p = [q for q in ("usdt", "tl") if "%s_%s" % (k, q) in marketler]
        if p:
            out[c] = p
    return out
