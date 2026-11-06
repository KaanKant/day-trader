#!/usr/bin/env python3
"""
Vadeli işlem (perpetual futures) testi - long/short ve kaldıraç
================================================================
Soru: Paribu botundaki trend kuralları vadeli işlemde short da açabilseydi ve
kaldıraç kullansaydı, geçmişte ne olurdu? İşlem yapmaz, sadece geçmişi hesaplar.

Model (her coine ayrı, "izole teminatlı" bir kasa):
  - Fiyat: Binance spot günlük mumları (perp fiyatı spotla çok yakın; vadeli API'si
    GitHub sunucularından erişime kapalı).
  - Pozisyon adet olarak tutulur; kâr/zarar fiyatla birlikte değişir. Pozisyon sadece
    sinyal değişince ya da oynaklık payı %20'den fazla kayınca ayarlanır.
  - Komisyon + kayma her işlemde pozisyon büyüklüğü üzerinden (teminat değil).
  - Funding: Binance'in geçmiş funding kayıtları (data.binance.vision). Kayıt
    bulunamayan aylar için 8 saatte %0.01 varsayılır (long öder, short alır).
  - Tasfiye: gün içindeki en kötü fiyatta (long için dip, short için tepe) kasa
    değeri bakım teminatının (%0.5) altına inerse kasa sıfırlanır ve o coin
    dönem sonuna kadar işlem yapmaz.
  - Karar günün kapanışında, işlem ertesi günün açılışında.

  python3 paribu/vadeli.py
"""
from __future__ import annotations

import argparse
import csv
import io
import statistics
import sys
import time
import zipfile
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backtest as bt  # noqa: E402
import portfoy as pf  # noqa: E402
import veri  # noqa: E402

KOK = Path(__file__).resolve().parent
FUNDING_URL = ("https://data.binance.vision/data/futures/um/monthly/fundingRate/"
               "{s}/{s}-fundingRate-{y:04d}-{m:02d}.zip")
VARSAYILAN_FUNDING_GUN = 0.0003      # 8 saatte %0.01 x 3
BAKIM = 0.005


# ------------------------------------------------------------------ funding verisi
def _zip_getir(url, timeout=30):
    import urllib.error
    import urllib.request
    req = urllib.request.Request(url, headers={"User-Agent": veri.UA})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.read()
    except (urllib.error.URLError, OSError):
        return None


def funding_gunluk(sembol, bas, bit, getir=_zip_getir, bekle=0.05):
    """{gün_no: o günün toplam funding oranı} - Binance arşivinden aylık zip'ler."""
    out = {}
    y, m = bas.year, bas.month
    while (y, m) <= (bit.year, bit.month):
        ham = getir(FUNDING_URL.format(s=sembol, y=y, m=m))
        if ham:
            try:
                with zipfile.ZipFile(io.BytesIO(ham)) as z:
                    for ad in z.namelist():
                        if not ad.endswith(".csv"):
                            continue
                        metin = z.read(ad).decode("utf-8", "replace")
                        for satir in csv.reader(io.StringIO(metin)):
                            if not satir or not satir[0].strip().isdigit():
                                continue          # başlık satırı
                            ts, oran = int(satir[0]), float(satir[-1])
                            g = ts // bt.GUN_MS
                            out[g] = out.get(g, 0.0) + oran
            except (zipfile.BadZipFile, ValueError):
                pass
        m += 1
        if m == 13:
            y, m = y + 1, 1
        time.sleep(bekle)
    return out


# ------------------------------------------------------------------ yön sinyalleri
def yonler(gunluk, btc, kural, short):
    """Her gün kapanışında hedef yön: +1 long, -1 short, 0 nakit."""
    T = len(gunluk)
    c = [g["c"] for g in gunluk]
    if kural.startswith("al_tut"):
        return [1] * T
    if kural.startswith("sma50"):
        ust = bt.sma_sinyal(gunluk, 50)
        alt = [i >= 49 and not ust[i] for i in range(T)]
        if "_btc" in kural and btc:
            bu = bt.sma_sinyal(btc, 50)
            ba = [i >= 49 and not bu[i] for i in range(T)]
            return [1 if (ust[i] and bu[i]) else (-1 if (short and alt[i] and ba[i]) else 0) for i in range(T)]
        return [1 if ust[i] else (-1 if (short and alt[i]) else 0) for i in range(T)]
    if kural.startswith("donchian"):
        out, poz = [], 0
        for i in range(T):
            if i < 20:
                out.append(0)
                continue
            tepe20 = max(g["h"] for g in gunluk[i - 20:i])
            dip20 = min(g["l"] for g in gunluk[i - 20:i])
            tepe10 = max(g["h"] for g in gunluk[i - 10:i])
            dip10 = min(g["l"] for g in gunluk[i - 10:i])
            if poz == 1 and c[i] < dip10:
                poz = 0
            elif poz == -1 and c[i] > tepe10:
                poz = 0
            if poz == 0:
                if c[i] > tepe20:
                    poz = 1
                elif short and c[i] < dip20:
                    poz = -1
            out.append(poz)
        return out
    raise ValueError(kural)


# ------------------------------------------------------------------ simülasyon
def calistir(gunlukler, funding, kural, short, kaldirac, maliyet):
    coinler = list(gunlukler)
    T = len(next(iter(gunlukler.values())))
    btc = gunlukler.get("BTC")
    yon = {c: yonler(gunlukler[c], btc, kural, short) for c in coinler}
    vol = {c: pf.oynaklik(gunlukler[c]) for c in coinler} if "_vol" in kural else None

    n = len(coinler)
    nakit = {c: 1.0 / n for c in coinler}     # kasa değeri = nakit + adet * fiyat
    adet = {c: 0.0 for c in coinler}
    pay = {c: 0.0 for c in coinler}           # işaretli: + long, - short (kaldıraç dahil)
    olu = set()
    egri, tasfiye, fund_top, ucret_top, short_kar = [1.0], 0, 0.0, 0.0, 0.0
    for j in range(1, T):
        gun_no = gunlukler[coinler[0]][j]["t"] // bt.GUN_MS
        for c in coinler:
            if c in olu:
                continue
            g = gunlukler[c][j]
            o = g["o"]
            deger = nakit[c] + adet[c] * o
            # --- hedef pay
            y = yon[c][j - 1]
            hedef = 0.0
            if y:
                p = 1.0
                if vol is not None:
                    v = vol[c][j - 1]
                    p = min(1.0, pf.HEDEF_GUNLUK_VOL / v) if v else 1.0
                hedef = y * p * kaldirac
            fark = hedef - pay[c]
            yon_degisti = (hedef == 0) != (pay[c] == 0) or (hedef * pay[c] < 0)
            if fark and (yon_degisti or abs(fark) >= pf.ESIK * kaldirac):
                hedef_adet = hedef * deger / o
                d = hedef_adet - adet[c]
                u = abs(d) * o * maliyet
                nakit[c] -= d * o + u
                adet[c] = hedef_adet
                pay[c] = hedef
                ucret_top += u
            if adet[c] == 0:
                continue
            # --- gün içi tasfiye kontrolü (en kötü fiyat)
            kotu = g["l"] if adet[c] > 0 else g["h"]
            kotu_deger = nakit[c] + adet[c] * kotu
            if kotu_deger <= BAKIM * abs(adet[c]) * kotu:
                tasfiye += 1
                nakit[c], adet[c], pay[c] = 0.0, 0.0, 0.0
                olu.add(c)
                continue
            # --- funding (kapanış fiyatıyla; long öder, short alır; oran negatifse tersi)
            f = funding.get(c, {}).get(gun_no, VARSAYILAN_FUNDING_GUN)
            od = adet[c] * g["c"] * f
            nakit[c] -= od
            fund_top += od
            # --- short'tan gelen günlük kâr/zarar (açılıştan ertesi açılışa)
            sonraki = gunlukler[c][j + 1]["o"] if j + 1 < T else g["c"]
            if adet[c] < 0:
                short_kar += adet[c] * (sonraki - o)
        egri.append(sum(nakit[c] + adet[c] * (gunlukler[c][j + 1]["o"] if j + 1 < T else gunlukler[c][j]["c"])
                        for c in coinler))
    son_fiyat = {c: gunlukler[c][-1]["c"] for c in coinler}
    son = sum(nakit[c] + adet[c] * son_fiyat[c] - abs(adet[c]) * son_fiyat[c] * maliyet for c in coinler)
    egri.append(son)
    yil = T / 365.0
    yillik = (son ** (1 / yil) - 1) * 100 if son > 0 else -100.0
    dusus = bt.max_dusus([max(x, 1e-9) for x in egri])
    return {"getiri": (son - 1) * 100, "yillik": yillik, "dusus": dusus,
            "calmar": yillik / abs(dusus) if dusus else 0.0, "tasfiye": tasfiye,
            "funding": fund_top * 100, "ucret": ucret_top * 100, "short_kar": short_kar * 100}


SENARYOLAR = []
for _k in ("sma50_btc_vol", "donchian_vol"):
    for _s in (False, True):
        for _L in (1, 2, 3):
            SENARYOLAR.append((_k, _s, _L))
for _L in (1, 2, 3):
    SENARYOLAR.append(("al_tut", False, _L))


def ad(k, s, L):
    return "%s %s %dx" % (k, "long+short" if s else "sadece long", L)


def tablo(sonuc, baslik):
    L = ["### " + baslik, "",
         "| Senaryo | Toplam getiri | Yıllık | En büyük düşüş | Yıllık / düşüş | Tasfiye olan coin | Short'un katkısı | Ödenen funding | Ödenen ücret |",
         "|---|---|---|---|---|---|---|---|---|"]
    for key in SENARYOLAR:
        r = sonuc[key]
        L.append("| %s | %+.0f%% | %+.1f%% | %.0f%% | %.2f | %d | %+.0f%% | %+.0f%% | %.0f%% |" % (
            ad(*key), r["getiri"], r["yillik"], r["dusus"], r["calmar"], r["tasfiye"],
            r["short_kar"], r["funding"], r["ucret"]))
    return L + [""]


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ucret", type=float, default=0.05, help="vadeli taker komisyonu, yüzde (Binance standart %0.05)")
    ap.add_argument("--kayma", type=float, default=0.05)
    ap.add_argument("--yil", type=int, default=6)
    ap.add_argument("--coinler", default=",".join(c for c in bt.COINLER if c != "BNB"))
    ap.add_argument("--cikti", default=str(KOK / "VADELI-RAPORU.md"))
    a = ap.parse_args(argv)
    maliyet = (a.ucret + a.kayma) / 100
    simdi = datetime.now(timezone.utc)
    bas = simdi - timedelta(days=365 * a.yil)

    coinler = [c.strip().upper() for c in a.coinler.split(",") if c.strip()]
    if "BTC" not in coinler:
        coinler.insert(0, "BTC")
    gunlukler, funding, gercek = {}, {}, {}
    for c in coinler:
        try:
            gunlukler[c] = veri.mumlar(c + "USDT", "1d", bas)
        except veri.VeriHatasi as e:
            print("%s atlandı: %s" % (c, e))
            continue
        funding[c] = funding_gunluk(c + "USDT", bas, simdi)
        gercek[c] = len(funding[c])
        print("%s: %d gün fiyat, %d gün funding kaydı" % (c, len(gunlukler[c]), gercek[c]))
    gunlukler = pf.hizala({c: v for c, v in gunlukler.items() if len(v) > 300})
    T = len(next(iter(gunlukler.values())))
    orta = T // 2
    yarim = [{c: v[:orta] for c, v in gunlukler.items()}, {c: v[orta:] for c, v in gunlukler.items()}]

    tum = {k: calistir(gunlukler, funding, k[0], k[1], k[2], maliyet) for k in SENARYOLAR}
    y = [{k: calistir(h, funding, k[0], k[1], k[2], maliyet) for k in SENARYOLAR} for h in yarim]
    ilk = next(iter(gunlukler.values()))
    kapsama = statistics.mean(min(1.0, gercek.get(c, 0) / T) for c in gunlukler) * 100
    L = ["# Vadeli işlem testi (long/short, kaldıraç)", "",
         "Tarih: %s UTC | Komisyon %%%.2f + kayma %%%.2f, pozisyon büyüklüğü üzerinden" % (
             simdi.strftime("%Y-%m-%d %H:%M"), a.ucret, a.kayma),
         "Coinler (sermaye eşit bölündü, her coin ayrı teminatlı): " + ", ".join(gunlukler),
         "Dönem: %s → %s (%d gün). Yarılar: %s'e kadar / sonrası." % (
             bt.tarih(ilk[0]["t"]), bt.tarih(ilk[-1]["t"]), T, bt.tarih(ilk[orta]["t"])),
         "Gerçek funding kaydı olan günler: ortalama %%%.0f (kalanı için 8 saatte %%0.01 varsayıldı)." % kapsama, ""]
    L += tablo(tum, "Tüm dönem")
    L += tablo(y[0], "1. yarı (eski)")
    L += tablo(y[1], "2. yarı (yeni)")
    L += ["Notlar:",
          "- Tasfiye olan coin: o coinin teminatı tamamen gitti ve dönem sonuna kadar işlem yapmadı.",
          "- Short'un katkısı: short pozisyonlardan gelen fiyat kâr/zararı, başlangıç sermayesinin yüzdesi olarak (ücret ve funding hariç).",
          "- Ödenen funding eksiyse funding'den net kazanılmıştır (short pozisyonlar pozitif funding'de para alır).",
          "- Spot Paribu botuyla karşılaştırma için PORTFOY-RAPORU.md (sadece long, 1x, %0.28 ücret).",
          "- Geçmiş sonuç geleceği garanti etmez. Tasfiye modeli günlük mumla yapıldı; gerçekte gün içi iğneler daha sık tasfiye yaratabilir."]
    Path(a.cikti).write_text("\n".join(L) + "\n", encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
