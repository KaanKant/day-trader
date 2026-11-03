#!/usr/bin/env python3
"""
Paribu strateji testi
=====================
Kod yazıp para bağlamadan önce soruyu veriyle sorar: "Bu strateji geçmişte,
ücretler düşüldükten sonra para kazandırır mıydı?"

Stratejiler
  al_tut            : ilk gün al, sonuna kadar tut (karşılaştırma tabanı)
  sma_N             : günlük kapanış N günlük ortalamanın üstündeyse ertesi gün tut, değilse nakit
  donchian_G_C      : kapanış son G günün zirvesini kırınca al, son C günün dibini kırınca sat
  kirilim_K[_R][_t] : gün içi kırılım (15 dk mum, UTC 00:00 gün başı).
                      İlk K mum açılış aralığı. Fiyat aralığın tepesini kırınca al,
                      zarar kes aralığın dibi, hedef R katı risk (yoksa gün sonu kapanış).
                      _t: sadece günlük trend yukarıyken (önceki kapanış > 50 gün ortalaması)

Maliyet: her yönde ücret + kayma. Aynı mumda hem stop hem hedef görülürse stop sayılır.
Her strateji tüm dönemde ve iki yarıda ayrı ayrı test edilir (tutarlılık kontrolü).

Kullanım:
  python3 paribu/backtest.py                 # veriyi indirir, rapor yazar
  python3 paribu/backtest.py --ucret 0.1     # her yönde %0.1 ücretle
"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import veri  # noqa: E402

KOK = Path(__file__).resolve().parent
COINLER = ["BTC", "ETH", "SOL", "XRP", "BNB", "DOGE", "ADA", "AVAX", "LINK", "TRX"]
GUN_MS = 86_400_000


# ------------------------------------------------------------------ yardımcılar
def max_dusus(egri):
    """En büyük tepe-dip düşüş (%), negatif sayı."""
    tepe, en = egri[0] if egri else 1.0, 0.0
    for x in egri:
        tepe = max(tepe, x)
        en = min(en, x / tepe - 1)
    return en * 100


def sonuc(egri, islemler, gun_sayisi):
    son = egri[-1] if egri else 1.0
    yil = max(gun_sayisi / 365.0, 1e-9)
    net = [x for x in islemler]
    return {
        "getiri": (son - 1) * 100,
        "yillik": ((son ** (1 / yil)) - 1) * 100 if son > 0 else -100.0,
        "dusus": max_dusus(egri),
        "islem": len(net),
        "kazanan": (sum(1 for x in net if x > 0) * 100 / len(net)) if net else 0.0,
        "ort_islem": statistics.mean(net) * 100 if net else 0.0,
    }


# ------------------------------------------------------------------ günlük stratejiler
def al_tut(gunluk, maliyet):
    """İlk günün açılışında al, son günün kapanışında sat."""
    if not gunluk:
        return sonuc([1.0], [], 0)
    o0 = gunluk[0]["o"]
    egri = [1.0] + [(1 - maliyet) * g["c"] / o0 for g in gunluk]
    son = egri[-1] * (1 - maliyet)
    egri.append(son)
    return sonuc(egri, [son - 1], len(gunluk))


def pozisyonlu(gunluk, sinyal, maliyet):
    """sinyal[i]: i. günün KAPANIŞINDA verilen karar (True = elde tut).
    Pozisyon i+1. günün açılışında alınır/bırakılır; getiri açılıştan açılışa."""
    e, egri, islemler = 1.0, [1.0], []
    poz, giris_e = False, None
    for j in range(1, len(gunluk)):
        hedef = sinyal[j - 1]
        if hedef and not poz:
            e *= (1 - maliyet)
            poz, giris_e = True, e / (1 - maliyet)
        elif not hedef and poz:
            e *= (1 - maliyet)
            islemler.append(e / giris_e - 1)
            poz = False
        if poz:
            sonraki = gunluk[j + 1]["o"] if j + 1 < len(gunluk) else gunluk[j]["c"]
            e *= sonraki / gunluk[j]["o"]
        egri.append(e)
    if poz:
        e *= (1 - maliyet)
        islemler.append(e / giris_e - 1)
        egri.append(e)
    return sonuc(egri, islemler, len(gunluk))


def sma_sinyal(gunluk, n):
    c = [g["c"] for g in gunluk]
    out = []
    for i in range(len(c)):
        if i + 1 < n:
            out.append(False)
        else:
            out.append(c[i] > sum(c[i + 1 - n:i + 1]) / n)
    return out


def donchian_sinyal(gunluk, giris, cikis):
    out, poz = [], False
    for i in range(len(gunluk)):
        if i < max(giris, cikis):
            out.append(False)
            continue
        tepe = max(g["h"] for g in gunluk[i - giris:i])
        dip = min(g["l"] for g in gunluk[i - cikis:i])
        c = gunluk[i]["c"]
        if not poz and c > tepe:
            poz = True
        elif poz and c < dip:
            poz = False
        out.append(poz)
    return out


# ------------------------------------------------------------------ gün içi kırılım
def gunlere_bol(mumlar):
    gunler = {}
    for m in mumlar:
        gunler.setdefault(m["t"] // GUN_MS, []).append(m)
    return gunler


def trend_yukari(gunluk, n=50):
    """{gün_no: önceki günün kapanışı > n günlük ortalama} - aynı günün verisi kullanılmaz."""
    out, c = {}, [g["c"] for g in gunluk]
    for i in range(n, len(gunluk)):
        out[gunluk[i]["t"] // GUN_MS] = c[i - 1] > sum(c[i - n:i]) / n
    return out


def kirilim(mumlar15, maliyet, k=4, r=None, trend=None):
    """Günde en fazla bir işlem. Giriş: aralık tepesi kırılınca (boşlukla açılırsa açılış)."""
    gunler = gunlere_bol(mumlar15)
    e, egri, islemler = 1.0, [1.0], []
    for gun in sorted(gunler):
        bar = gunler[gun]
        if len(bar) < 90:                     # eksik gün (bakım/veri boşluğu)
            continue
        if trend is not None and not trend.get(gun, False):
            continue
        aralik = bar[:k]
        tepe = max(m["h"] for m in aralik)
        dip = min(m["l"] for m in aralik)
        if tepe <= dip:
            continue
        giris = None
        for i in range(k, len(bar)):
            m = bar[i]
            if giris is None:
                if m["h"] > tepe:
                    giris = max(m["o"], tepe)
                    stop = dip
                    hedef = giris + r * (giris - stop) if r else None
                    # Giriş mumu içinde stop da görüldüyse (sert dönüş): stop say
                    if m["l"] <= stop and m["o"] > stop:
                        cikis = stop
                        break
                    if hedef and m["c"] >= hedef:
                        cikis = hedef
                        break
                continue
            if m["l"] <= stop:
                cikis = min(stop, m["o"])     # boşlukla açılırsa açılıştan
                break
            if hedef and m["h"] >= hedef:
                cikis = max(hedef, m["o"])
                break
        else:
            cikis = bar[-1]["c"] if giris is not None else None
        if giris is None:
            continue
        net = (cikis / giris) * (1 - maliyet) ** 2 - 1
        islemler.append(net)
        e *= (1 + net)
        egri.append(e)
    gun_sayisi = (mumlar15[-1]["t"] - mumlar15[0]["t"]) / GUN_MS if mumlar15 else 0
    return sonuc(egri, islemler, gun_sayisi)


# ------------------------------------------------------------------ çalıştırma
def stratejiler(gunluk, mum15, maliyet, trend_kaynak=None):
    s = {"al_tut": al_tut(gunluk, maliyet)}
    for n in (20, 50, 100, 200):
        s["sma_%d" % n] = pozisyonlu(gunluk, sma_sinyal(gunluk, n), maliyet)
    for g, c in ((20, 10), (55, 20)):
        s["donchian_%d_%d" % (g, c)] = pozisyonlu(gunluk, donchian_sinyal(gunluk, g, c), maliyet)
    if mum15:
        tr = trend_yukari(trend_kaynak or gunluk)
        for k in (4, 8):
            s["kirilim_%d" % k] = kirilim(mum15, maliyet, k)
            s["kirilim_%d_2R" % k] = kirilim(mum15, maliyet, k, r=2)
            s["kirilim_%d_t" % k] = kirilim(mum15, maliyet, k, trend=tr)
            s["kirilim_%d_2R_t" % k] = kirilim(mum15, maliyet, k, r=2, trend=tr)
    return s


def yarilar(gunluk, mum15):
    """Veriyi zaman olarak ikiye böler (her biri kendi içinde baştan test edilir)."""
    if not gunluk:
        return []
    orta = gunluk[len(gunluk) // 2]["t"]
    g1 = [g for g in gunluk if g["t"] < orta]
    g2 = [g for g in gunluk if g["t"] >= orta]
    # Gün içi veri daha kısa: kendi ortasından böl, trend filtresi için tüm günlük veri kalır
    if mum15:
        o15 = mum15[len(mum15) // 2]["t"] // GUN_MS * GUN_MS
        m1 = [m for m in mum15 if m["t"] < o15]
        m2 = [m for m in mum15 if m["t"] >= o15]
    else:
        m1 = m2 = []
    return [(g1, m1), (g2, m2)]


def tablo(sonuclar, baslik):
    L = ["### " + baslik, "",
         "| Strateji | Medyan getiri | Ortalama getiri | Kâr eden coin | Medyan yıllık | Medyan max düşüş | İşlem/coin | Kazanan % | İşlem başı ort. |",
         "|---|---|---|---|---|---|---|---|---|"]
    isimler = sorted({s for r in sonuclar.values() for s in r},
                     key=lambda s: -statistics.median(sonuclar[c][s]["getiri"] for c in sonuclar if s in sonuclar[c]))
    for s in isimler:
        rr = [sonuclar[c][s] for c in sonuclar if s in sonuclar[c]]
        L.append("| %s | %+.0f%% | %+.0f%% | %d/%d | %+.0f%% | %.0f%% | %.0f | %.0f | %+.2f%% |" % (
            s, statistics.median(r["getiri"] for r in rr), statistics.mean(r["getiri"] for r in rr),
            sum(1 for r in rr if r["getiri"] > 0), len(rr),
            statistics.median(r["yillik"] for r in rr), statistics.median(r["dusus"] for r in rr),
            statistics.mean(r["islem"] for r in rr), statistics.mean(r["kazanan"] for r in rr),
            statistics.mean(r["ort_islem"] for r in rr)))
    return L + [""]


def tarih(ms):
    return datetime.fromtimestamp(ms / 1000, timezone.utc).strftime("%Y-%m-%d")


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--ucret", type=float, default=0.25, help="her yönde ücret, yüzde (varsayılan 0.25)")
    ap.add_argument("--kayma", type=float, default=0.05, help="her yönde kayma, yüzde (varsayılan 0.05)")
    ap.add_argument("--gunluk-yil", type=int, default=6)
    ap.add_argument("--gunici-gun", type=int, default=730)
    ap.add_argument("--coinler", default=",".join(COINLER))
    ap.add_argument("--cikti", default=str(KOK / "BACKTEST-RAPORU.md"))
    a = ap.parse_args(argv)
    maliyet = (a.ucret + a.kayma) / 100

    coinler = [c.strip().upper() for c in a.coinler.split(",") if c.strip()]
    try:
        uygun = veri.paribu_uygun(coinler, veri.paribu_marketleri())
        not_paribu = "Paribu market listesi okundu."
        coinler = [c for c in coinler if c in uygun]
    except veri.VeriHatasi as e:
        uygun, not_paribu = {}, "Paribu market listesi okunamadı (%s), tüm coinler test edildi." % e
    simdi = datetime.now(timezone.utc)

    tum, yari = {}, [{}, {}]
    donem = {}
    for c in coinler:
        sym = c + "USDT"
        try:
            gunluk = veri.mumlar(sym, "1d", simdi - timedelta(days=365 * a.gunluk_yil))
            mum15 = veri.mumlar(sym, "15m", simdi - timedelta(days=a.gunici_gun))
        except veri.VeriHatasi as e:
            print("%s atlandı: %s" % (c, e))
            continue
        if len(gunluk) < 250:
            print("%s atlandı: günlük veri az (%d gün)" % (c, len(gunluk)))
            continue
        donem[c] = (tarih(gunluk[0]["t"]), tarih(gunluk[-1]["t"]),
                    tarih(mum15[0]["t"]) if mum15 else "-", tarih(mum15[-1]["t"]) if mum15 else "-")
        tum[c] = stratejiler(gunluk, mum15, maliyet)
        for i, (g, m) in enumerate(yarilar(gunluk, mum15)):
            # Trend filtresi tüm günlük veriden hesaplanır; sadece önceki günlere bakar, sızıntı yok
            yari[i][c] = stratejiler(g, m, maliyet, trend_kaynak=gunluk)
        print("%s tamam: %d gün, %d adet 15 dk mum" % (c, len(gunluk), len(mum15)))

    if not tum:
        print("Hiç veri alınamadı.")
        return 1

    L = ["# Paribu strateji testi", "",
         "Tarih: %s UTC" % simdi.strftime("%Y-%m-%d %H:%M"),
         "Maliyet: her yönde ücret %%%.2f + kayma %%%.2f (gidiş-dönüş ~%%%.2f)" % (a.ucret, a.kayma, 2 * (a.ucret + a.kayma)),
         "Veri: Binance USDT pariteleri (Paribu'da mum verisi yok). " + not_paribu,
         "Coinler: " + ", ".join("%s (%s)" % (c, "/".join(uygun.get(c, ["?"]))) for c in tum), ""]
    L.append("Dönemler: " + "; ".join("%s günlük %s→%s, 15dk %s→%s" % ((c,) + donem[c]) for c in list(donem)[:1]))
    L.append("")
    L += tablo(tum, "Tüm dönem")
    L += tablo(yari[0], "1. yarı (eski)")
    L += tablo(yari[1], "2. yarı (yeni)")
    L += ["### Coin bazında (tüm dönem, toplam getiri %)", "",
          "| Strateji | " + " | ".join(tum) + " |", "|---|" + "---|" * len(tum)]
    for s in sorted(next(iter(tum.values()))):
        L.append("| %s | " % s + " | ".join("%+.0f" % tum[c][s]["getiri"] if s in tum[c] else "-" for c in tum) + " |")
    L += ["", "Notlar:",
          "- Getiriler USDT cinsinden. TL paritelerinde kurdaki değişim ayrıca eklenir; stratejinin kendi başarısını görmek için USDT kullanıldı.",
          "- kirilim_*: 15 dk mumlar, gün başı UTC 00:00 (TSİ 03:00). Aynı mumda stop ve hedef görülürse stop varsayıldı.",
          "- Geçmiş sonuç geleceği garanti etmez. Bir stratejiyi ancak iki yarıda da tutarlıysa ciddiye alıyoruz."]
    Path(a.cikti).write_text("\n".join(L) + "\n", encoding="utf-8")
    Path(a.cikti).with_suffix(".json").write_text(json.dumps({"tum": tum, "yari1": yari[0], "yari2": yari[1]},
                                                             indent=1), encoding="utf-8")
    print("\n".join(L))
    return 0


if __name__ == "__main__":
    sys.exit(main())
