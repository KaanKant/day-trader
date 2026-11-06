#!/usr/bin/env python3
"""
Paribu sanal işlem botu
=======================
Günde bir kez, günlük mum kapandıktan sonra çalışır (00:15 UTC = 03:15 TSİ):
  1. Binance'ten kapanmış günlük mumları alır, her kural için hedef payları hesaplar
     (portfoy.py'deki Karar sınıfı: backtest ile birebir aynı kararlar).
  2. Paribu'nun herkese açık fiyatından (GET /market/ticker, *_usdt) sanal alım satım yapar.
     Ücret ve kayma düşülür.
  3. Durumu paribu/durum/sanal.json'a, raporu paribu/SANAL-RAPOR.md'ye yazar.
     TELEGRAM_BOT_TOKEN ve TELEGRAM_CHAT_ID tanımlıysa özeti Telegram'a gönderir.

Her işlem, canlı modda Paribu'ya gidecek emrin gövdesiyle (POST /order) birlikte kaydedilir.
Bu bot GERÇEK EMİR VERMEZ: API anahtarı kullanmaz, Paribu'ya sadece fiyat sorar.

  python3 paribu/sanal.py            # günlük çalıştırma
  python3 paribu/sanal.py --kuru     # hiçbir dosyaya yazmadan ne yapacağını göster
"""
from __future__ import annotations

import argparse
import json
import os
import sys
import urllib.request
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import backtest as bt  # noqa: E402
import portfoy as pf  # noqa: E402
import vadeli as vd  # noqa: E402
import veri  # noqa: E402

KOK = Path(__file__).resolve().parent
AYAR = KOK / "sanal_ayarlar.json"
DURUM = KOK / "durum" / "sanal.json"
RAPOR = KOK / "SANAL-RAPOR.md"
TICKER = "https://api.paribu.com/market/ticker"


def ayarlar(yol=AYAR):
    return json.loads(Path(yol).read_text(encoding="utf-8"))


def durum_oku(yol=DURUM):
    p = Path(yol)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}


def paribu_fiyatlari(coinler, getir=veri._get):
    """{coin: son fiyat (USDT)} - Paribu *_usdt paritelerinden."""
    data = getir(TICKER) or []
    if isinstance(data, dict):            # zarf içinde gelirse
        data = data.get("payload") or data.get("data") or []
    son = {str(x.get("market", "")).lower(): x.get("last") for x in data if isinstance(x, dict)}
    out = {}
    for c in coinler:
        v = son.get("%s_usdt" % c.lower())
        try:
            if v is not None and float(v) > 0:
                out[c] = float(v)
        except (TypeError, ValueError):
            pass
    return out


def yeni_hesap(coinler, usdt):
    pay = usdt / len(coinler)
    return {"kasa": {c: {"usdt": pay, "adet": 0.0, "pay": 0.0} for c in coinler},
            "baslangic_usdt": usdt, "gecmis": []}


def kasa_degeri(k, fiyat):
    return k["usdt"] + k["adet"] * fiyat


def islem_yap(k, hedef, fiyat, ucret, kayma, min_usdt):
    """Kasayı hedef paya getirir. İşlem kaydı (dict) ya da None döndürür."""
    V = kasa_degeri(k, fiyat)
    hedef_deger = hedef * V
    simdi_deger = k["adet"] * fiyat
    fark = hedef_deger - simdi_deger
    if hedef == 0 and k["adet"] > 0:
        fark = -simdi_deger                      # çıkışta hepsini sat
    if abs(fark) < min_usdt:                     # Paribu en küçük emir tutarının altı: işlem yok
        if hedef == 0:
            k["pay"] = 0.0
        return None
    if fark > 0:
        harcanan = min(fark, k["usdt"])
        adet = harcanan * (1 - ucret) / (fiyat * (1 + kayma))
        k["usdt"] -= harcanan
        k["adet"] += adet
        kayit = {"yon": "al", "usdt": round(harcanan, 4), "adet": adet, "ucret": round(harcanan * ucret, 4)}
        emir = {"trade": "buy", "type": "market", "total": "%.2f" % harcanan}
    else:
        adet = min(-fark / fiyat, k["adet"])
        gelir = adet * fiyat * (1 - kayma) * (1 - ucret)
        k["adet"] -= adet
        if k["adet"] * fiyat < 1e-6:
            k["adet"] = 0.0
        k["usdt"] += gelir
        kayit = {"yon": "sat", "usdt": round(gelir, 4), "adet": adet,
                 "ucret": round(adet * fiyat * (1 - kayma) * ucret, 4)}
        emir = {"trade": "sell", "type": "market", "amount": "%.8f" % adet}
    k["pay"] = hedef
    kayit.update({"fiyat": fiyat, "hedef_pay": round(hedef, 3), "emir": emir})
    return kayit


def vadeli_adim(ay, durum, gunlukler, son_i, fiyat, kaynak, gun):
    """Sanal vadeli hesaplar (long + short). Pozisyon dünkü mum boyunca açıktıysa önce o günün
    tasfiye kontrolü ve funding'i uygulanır, sonra bugünün hedefine göre işlem yapılır."""
    v = ay.get("vadeli") or {}
    if not v.get("kurallar"):
        return []
    coinler = ay["coinler"]
    maliyet = (v.get("ucret_pct", 0.05) + v.get("kayma_pct", 0.05)) / 100
    L = float(v.get("kaldirac", 1))
    fund = float(v.get("funding_gunluk_pct", 0.03)) / 100
    hesaplar = durum.setdefault("vadeli", {})
    btc = gunlukler.get("BTC")
    bugun = []
    for kural in v["kurallar"]:
        anahtar = "%s_%gx" % (kural, L)
        h = hesaplar.setdefault(anahtar, {
            "baslangic": gun, "baslangic_usdt": v.get("baslangic_usdt", 200), "gecmis": [],
            "kasa": {c: {"nakit": v.get("baslangic_usdt", 200) / len(coinler), "adet": 0.0, "pay": 0.0,
                         "olu": False} for c in coinler}})
        for c in coinler:
            k = h["kasa"][c]
            if k["olu"]:
                continue
            g = gunlukler[c][son_i]
            if k["adet"] and h.get("son_gun") and h["son_gun"] < gun:
                kotu = g["l"] if k["adet"] > 0 else g["h"]
                if k["nakit"] + k["adet"] * kotu <= vd.BAKIM * abs(k["adet"]) * kotu:
                    kayit = {"gun": gun, "kural": anahtar, "coin": c, "yon": "TASFİYE", "fiyat": kotu,
                             "usdt": 0.0, "ucret": 0.0, "emir": {}}
                    k.update({"nakit": 0.0, "adet": 0.0, "pay": 0.0, "olu": True})
                    bugun.append(kayit)
                    continue
                k["nakit"] -= k["adet"] * g["c"] * fund       # long öder, short alır
            yon = vd.yonler(gunlukler[c], btc, kural, True)[son_i]
            hedef = 0.0
            if yon:
                p = 1.0
                if "_vol" in kural:
                    o = pf.oynaklik(gunlukler[c])[son_i]
                    p = min(1.0, pf.HEDEF_GUNLUK_VOL / o) if o else 1.0
                hedef = yon * p * L
            fark = hedef - k["pay"]
            yon_degisti = (hedef == 0) != (k["pay"] == 0) or hedef * k["pay"] < 0
            if not fark or not (yon_degisti or abs(fark) >= pf.ESIK * L):
                continue
            P = fiyat[c]
            deger = k["nakit"] + k["adet"] * P
            hedef_adet = hedef * deger / P
            d = hedef_adet - k["adet"]
            if abs(d) * P < ay.get("min_islem_usdt", 10) and hedef != 0:
                continue
            u = abs(d) * P * maliyet
            k["nakit"] -= d * P + u
            k["adet"], k["pay"] = hedef_adet, hedef
            ne = "kapat" if hedef == 0 else ("long" if hedef > 0 else "short")
            kayit = {"gun": gun, "kural": anahtar, "coin": c, "yon": ne, "fiyat": P,
                     "usdt": round(abs(d) * P, 4), "ucret": round(u, 4), "fiyat_kaynagi": kaynak[c],
                     "emir": {"symbol": c + "USDT", "side": "BUY" if d > 0 else "SELL", "type": "MARKET",
                              "quantity": "%.6f" % abs(d), "reduceOnly": hedef == 0}}
            bugun.append(kayit)
        h["son_gun"] = gun
        deger = sum(h["kasa"][c]["nakit"] + h["kasa"][c]["adet"] * fiyat[c] for c in coinler)
        h["gecmis"].append({"gun": gun, "deger": round(deger, 2)})
        h["gecmis"] = h["gecmis"][-400:]
    return bugun


def calistir(ay, durum, mum_getir=None, fiyat_getir=None, simdi=None, log=print):
    """Bir günlük adım. (yeni_durum, rapor_satirlari, telegram_metni) ya da None (bugün işlendi)."""
    simdi = simdi or datetime.now(timezone.utc)
    coinler = ay["coinler"]
    ucret, kayma = ay["ucret_pct"] / 100, ay["kayma_pct"] / 100
    mum_getir = mum_getir or (lambda c: veri.mumlar(c + "USDT", "1d", simdi - timedelta(days=220)))
    fiyat_getir = fiyat_getir or (lambda cs: paribu_fiyatlari(cs))

    gunlukler = {}
    for c in coinler + (["BTC"] if "BTC" not in coinler else []):
        gunlukler[c] = mum_getir(c)
    gunlukler = pf.hizala({c: v for c, v in gunlukler.items() if v})
    son_i = len(gunlukler["BTC"]) - 1
    gun = bt.tarih(gunlukler["BTC"][son_i]["t"])
    sadece_vadeli = False
    if durum.get("son_gun") == gun:
        v = ay.get("vadeli") or {}
        yeni = ["%s_%gx" % (k, float(v.get("kaldirac", 1))) for k in v.get("kurallar", [])]
        if not any(a not in (durum.get("vadeli") or {}) for a in yeni):
            log("%s mumu zaten işlendi, yeni işlem yok." % gun)
            return None
        sadece_vadeli = True                    # spot işlendi; sadece yeni vadeli hesap açılır

    fiyat = fiyat_getir(coinler)
    kaynak = {}
    for c in coinler:
        if c in fiyat:
            kaynak[c] = "paribu"
        else:                                   # Paribu fiyatı yoksa son kapanış (rapora not düşülür)
            fiyat[c] = gunlukler[c][son_i]["c"]
            kaynak[c] = "binance-kapanis"

    durum = json.loads(json.dumps(durum)) if durum else {}
    durum.setdefault("baslangic", gun)
    hesaplar = durum.setdefault("hesaplar", {})
    islemler = durum.setdefault("islemler", [])
    bugun = []
    for kural in ([] if sadece_vadeli else ay["kurallar"]):
        h = hesaplar.setdefault(kural, yeni_hesap(coinler, ay["baslangic_usdt"]))
        for c in coinler:                       # sonradan eklenen coin: boş kasa
            h["kasa"].setdefault(c, {"usdt": 0.0, "adet": 0.0, "pay": 0.0})
        karar = pf.Karar({c: gunlukler[c] for c in gunlukler if c in coinler or c == "BTC"}, kural)
        for c in coinler:
            k = h["kasa"][c]
            hedef = karar.hedef(c, son_i)
            if not pf.degisir_mi(k["pay"], hedef):
                continue
            kayit = islem_yap(k, hedef, fiyat[c], ucret, kayma, ay.get("min_islem_usdt", 10))
            if kayit:
                kayit.update({"gun": gun, "kural": kural, "coin": c, "fiyat_kaynagi": kaynak[c]})
                kayit["emir"]["market"] = "%s_usdt" % c.lower()
                islemler.append(kayit)
                bugun.append(kayit)
        deger = sum(kasa_degeri(h["kasa"][c], fiyat[c]) for c in coinler)
        h["gecmis"].append({"gun": gun, "deger": round(deger, 2)})
        h["gecmis"] = h["gecmis"][-400:]
    vbugun = vadeli_adim(ay, durum, gunlukler, son_i, fiyat, kaynak, gun)
    durum["vadeli_islemler"] = (durum.get("vadeli_islemler", []) + vbugun)[-1000:]
    durum["islemler"] = islemler[-1000:]
    durum["son_gun"] = gun
    durum["son_calisma"] = simdi.strftime("%Y-%m-%d %H:%M UTC")
    rapor, tg = rapor_yaz(ay, durum, fiyat, kaynak, bugun, gun)
    vr, vtg = vadeli_rapor(ay, durum, fiyat, vbugun)
    rapor[rapor.index("## Bugünkü işlemler") - 1:rapor.index("## Bugünkü işlemler") - 1] = vr
    tg = tg + ("\n" + vtg if vtg else "")
    return durum, rapor, tg


def vadeli_rapor(ay, durum, fiyat, bugun):
    v, hes = ay.get("vadeli") or {}, durum.get("vadeli") or {}
    if not hes:
        return [], ""
    coinler = ay["coinler"]
    L = ["", "### Vadeli (sanal, long + short)", "",
         "Kaldıraç %gx, komisyon %%%.2f + kayma %%%.2f, funding günlük %%%.2f varsayımı (long öder, short alır). "
         "Fiyat: Paribu spot (vadeli fiyatına çok yakın)." % (
             v.get("kaldirac", 1), v.get("ucret_pct", 0.05), v.get("kayma_pct", 0.05), v.get("funding_gunluk_pct", 0.03)),
         "", "| Hesap | Başlangıç | Değer (USDT) | Başlangıçtan | Long | Short | Tasfiye | Bugünkü işlem |",
         "|---|---|---|---|---|---|---|---|"]
    tg = []
    for ad, h in hes.items():
        deger = sum(h["kasa"][c]["nakit"] + h["kasa"][c]["adet"] * fiyat[c] for c in coinler)
        lo = [c for c in coinler if h["kasa"][c]["adet"] > 0]
        sh = [c for c in coinler if h["kasa"][c]["adet"] < 0]
        ol = [c for c in coinler if h["kasa"][c]["olu"]]
        n = sum(1 for x in bugun if x["kural"] == ad)
        deg = (deger / h["baslangic_usdt"] - 1) * 100
        L.append("| %s | %s | %.2f | %+.1f%% | %s | %s | %s | %d |" % (
            ad, h["baslangic"], deger, deg, ", ".join(lo) or "-", ", ".join(sh) or "-", ", ".join(ol) or "-", n))
        tg.append("Vadeli %s: %.0f USDT (%+.1f%%), long: %s, short: %s" % (
            ad, deger, deg, ", ".join(lo) or "-", ", ".join(sh) or "-"))
    if bugun:
        L += ["", "| Hesap | Coin | İşlem | Fiyat | Büyüklük (USDT) | Ücret | Binance vadeli emri (canlıda gidecek) |",
              "|---|---|---|---|---|---|---|"]
        for x in bugun:
            L.append("| %s | %s | %s | %.6g | %.2f | %.2f | `%s` |" % (
                x["kural"], x["coin"], x["yon"], x["fiyat"], x["usdt"], x["ucret"],
                json.dumps(x["emir"], separators=(",", ":"))))
            tg.append("Vadeli %s %s %.0f USDT @ %.6g" % (x["coin"], x["yon"].upper(), x["usdt"], x["fiyat"]))
    return L, "\n".join(tg)


def rapor_yaz(ay, durum, fiyat, kaynak, bugun, gun):
    coinler = ay["coinler"]
    L = ["# Paribu sanal işlem", "",
         "Son güncelleme: %s (kapanmış günlük mum: %s). Başlangıç: %s." % (
             durum["son_calisma"], gun, durum["baslangic"]),
         "**Sanal hesap. Gerçek emir verilmez.** Ücret %%%.2f + kayma %%%.2f her işlemde düşülür." % (
             ay["ucret_pct"], ay["kayma_pct"]), "",
         "| Kural | Değer (USDT) | Başlangıçtan | Coinde olan pay | Bugünkü işlem |", "|---|---|---|---|---|"]
    tg = ["<b>Paribu sanal - %s</b>" % gun]
    for kural, h in durum["hesaplar"].items():
        deger = sum(kasa_degeri(h["kasa"][c], fiyat[c]) for c in coinler)
        coinde = sum(h["kasa"][c]["adet"] * fiyat[c] for c in coinler)
        n = sum(1 for x in bugun if x["kural"] == kural)
        deg = (deger / h["baslangic_usdt"] - 1) * 100
        L.append("| %s | %.2f | %+.1f%% | %%%.0f | %d |" % (kural, deger, deg, coinde / deger * 100 if deger else 0, n))
        tg.append("%s: %.0f USDT (%+.1f%%), coinde %%%.0f, %d işlem" % (
            kural, deger, deg, coinde / deger * 100 if deger else 0, n))
    L += ["", "## Bugünkü işlemler", ""]
    if bugun:
        L += ["| Kural | Coin | Yön | Fiyat | USDT | Ücret | Paribu emri (canlıda gidecek) |", "|---|---|---|---|---|---|---|"]
        for x in bugun:
            L.append("| %s | %s | %s | %.6g | %.2f | %.2f | `%s` |" % (
                x["kural"], x["coin"], x["yon"], x["fiyat"], x["usdt"], x["ucret"],
                json.dumps(x["emir"], separators=(",", ":"))))
            tg.append("%s %s %s %.0f USDT @ %.6g" % (x["kural"], x["coin"], x["yon"].upper(), x["usdt"], x["fiyat"]))
    else:
        L.append("Bugün işlem yok.")
        tg.append("Bugün işlem yok.")
    L += ["", "## Pozisyonlar", "", "| Kural | " + " | ".join(coinler) + " |", "|---|" + "---|" * len(coinler)]
    for kural, h in durum["hesaplar"].items():
        L.append("| %s | " % kural + " | ".join(
            ("%%%.0f" % (h["kasa"][c]["pay"] * 100)) if h["kasa"][c]["adet"] > 0 else "-" for c in coinler) + " |")
    yedek = [c for c in coinler if kaynak[c] != "paribu"]
    if yedek:
        L += ["", "Not: %s için Paribu fiyatı alınamadı, Binance kapanışı kullanıldı." % ", ".join(yedek)]
        tg.append("Paribu fiyatı yok: " + ", ".join(yedek))
    L += ["", "## Son 30 gün (USDT)", "", "| Gün | " + " | ".join(durum["hesaplar"]) + " |",
          "|---|" + "---|" * len(durum["hesaplar"])]
    gunler = [x["gun"] for x in next(iter(durum["hesaplar"].values()))["gecmis"]][-30:]
    for g in reversed(gunler):
        L.append("| %s | " % g + " | ".join(
            next(("%.0f" % x["deger"] for x in h["gecmis"] if x["gun"] == g), "-")
            for h in durum["hesaplar"].values()) + " |")
    L += ["", "Kurallar: `sma50_btc_vol` = coin 50 günlük ortalamanın, BTC de kendi ortalamasının üstündeyse al; "
          "pay oynaklığa göre küçülür. `donchian_vol` = 20 günün zirvesini kırınca al, 10 günün dibini kırınca sat; "
          "pay oynaklığa göre. `al_tut` = karşılaştırma için baştan sona elde tut. "
          "Ayrıntı: PORTFOY-RAPORU.md."]
    return L, "\n".join(tg)


def telegram(metin):
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN", "").strip(), os.environ.get("TELEGRAM_CHAT_ID", "").strip()
    if not token or not chat:
        return False
    body = json.dumps({"chat_id": chat, "text": metin, "parse_mode": "HTML"}).encode()
    req = urllib.request.Request("https://api.telegram.org/bot%s/sendMessage" % token, data=body,
                                 headers={"Content-Type": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=15) as r:
            return r.status == 200
    except Exception as e:  # noqa: BLE001 - bildirim hatası botu düşürmesin
        print("Telegram gönderilemedi:", e)
        return False


def main(argv=None):
    ap = argparse.ArgumentParser()
    ap.add_argument("--kuru", action="store_true", help="dosyaya yazma, Telegram'a gönderme")
    a = ap.parse_args(argv)
    ay = ayarlar()
    sonuc = calistir(ay, durum_oku())
    if sonuc is None:
        return 0
    durum, rapor, tg = sonuc
    print("\n".join(rapor))
    if a.kuru:
        return 0
    DURUM.parent.mkdir(parents=True, exist_ok=True)
    DURUM.write_text(json.dumps(durum, indent=1, ensure_ascii=False), encoding="utf-8")
    RAPOR.write_text("\n".join(rapor) + "\n", encoding="utf-8")
    telegram(tg)
    return 0


if __name__ == "__main__":
    sys.exit(main())
