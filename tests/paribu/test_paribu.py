"""Paribu backtest ve veri katmanı testleri (ağ yok, sahte veri)."""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "paribu"))
import backtest as bt  # noqa: E402
import portfoy as pf  # noqa: E402
import sanal  # noqa: E402
import vadeli  # noqa: E402
import veri  # noqa: E402

GUN = bt.GUN_MS


def gun(i, o, h, l, c):
    return {"t": i * GUN, "o": o, "h": h, "l": l, "c": c, "v": 1}


def gunici(gun_no, fiyatlar):
    """96 adet 15 dk mum; fiyatlar: [(o,h,l,c), ...] eksikler son kapanışla düz devam eder."""
    out, son = [], fiyatlar[-1][3]
    for i in range(96):
        o, h, l, c = fiyatlar[i] if i < len(fiyatlar) else (son, son, son, son)
        out.append({"t": gun_no * GUN + i * 900_000, "o": o, "h": h, "l": l, "c": c, "v": 1})
    return out


class Testler(unittest.TestCase):
    def test_al_tut(self):
        g = [gun(0, 100, 100, 100, 100), gun(1, 100, 120, 100, 120), gun(2, 120, 150, 120, 150)]
        r = bt.al_tut(g, 0.0)
        self.assertAlmostEqual(r["getiri"], 50.0, places=6)
        r = bt.al_tut(g, 0.01)
        self.assertAlmostEqual(r["getiri"], (1.5 * 0.99 * 0.99 - 1) * 100, places=6)

    def test_pozisyonlu_acilistan_acilisa(self):
        # Gün 0 kapanışında sinyal -> gün 1 açılışında al; gün 1 kapanışında çık -> gün 2 açılışında sat
        g = [gun(0, 100, 100, 100, 100), gun(1, 100, 110, 100, 110), gun(2, 110, 110, 110, 110),
             gun(3, 120, 120, 120, 120)]
        r = bt.pozisyonlu(g, [True, False, False, False], 0.0)
        self.assertAlmostEqual(r["getiri"], 10.0, places=6)
        self.assertEqual(r["islem"], 1)

    def test_sma_ileriye_bakmaz(self):
        g = [gun(i, 1, 1, 1, 1) for i in range(5)] + [gun(5, 1, 2, 1, 2)]
        s = bt.sma_sinyal(g, 3)
        self.assertEqual(s[:5], [False] * 5)
        self.assertTrue(s[5])

    def test_kirilim_hedef(self):
        # aralık (ilk 4 mum) 100-102; 5. mum 102'yi kırar; 2R hedef = 102 + 2*2 = 106
        f = [(101, 102, 100, 101)] * 4 + [(101, 103, 101, 103), (103, 107, 103, 106)]
        r = bt.kirilim(gunici(0, f), 0.0, k=4, r=2)
        self.assertEqual(r["islem"], 1)
        self.assertAlmostEqual(r["getiri"], (106 / 102 - 1) * 100, places=6)

    def test_kirilim_stop_ve_bosluk(self):
        # giriş 102, sonra 99'dan açılan mum: stop 100 değil açılış 99 sayılır
        f = [(101, 102, 100, 101)] * 4 + [(101, 103, 101, 102.5), (99, 99, 98, 98)]
        r = bt.kirilim(gunici(0, f), 0.0, k=4)
        self.assertAlmostEqual(r["getiri"], (99 / 102 - 1) * 100, places=6)

    def test_kirilim_gun_sonu_ve_maliyet(self):
        f = [(101, 102, 100, 101)] * 4 + [(101, 103, 101, 103)]
        r = bt.kirilim(gunici(0, f), 0.01, k=4)
        self.assertAlmostEqual(r["getiri"], ((103 / 102) * 0.99 ** 2 - 1) * 100, places=6)

    def test_kirilim_yoksa_islem_yok(self):
        f = [(101, 102, 100, 101)] * 10
        self.assertEqual(bt.kirilim(gunici(0, f), 0.0, k=4)["islem"], 0)

    def test_trend_filtresi_onceki_gunler(self):
        g = [gun(i, 1, 1, 1, 1) for i in range(50)] + [gun(50, 1, 5, 1, 5), gun(51, 5, 5, 5, 5)]
        tr = bt.trend_yukari(g, n=50)
        self.assertFalse(tr[50])     # gün 50'nin kendi kapanışı kullanılmaz
        self.assertTrue(tr[51])

    def test_mumlar_sayfalama_ve_tekil(self):
        cagrilar = []

        def sahte(url):
            cagrilar.append(url)
            bas = int(url.split("startTime=")[1].split("&")[0])
            if bas >= 3 * GUN:
                return []
            return [[bas + i * GUN, "1", "2", "0.5", "1.5", "10"] for i in range(2)]
        m = veri.mumlar("BTCUSDT", "1d", 0, 4 * GUN, bekle=0, getir=sahte)
        self.assertEqual([x["t"] for x in m], [0, GUN, 2 * GUN, 3 * GUN])
        self.assertEqual(len(cagrilar), 2)   # 4. gün bitiş sınırında, üçüncü istek gerekmez

    def test_paribu_uygun(self):
        u = veri.paribu_uygun(["BTC", "XYZ", "ETH"], {"btc_tl", "btc_usdt", "eth_tl"})
        self.assertEqual(u, {"BTC": ["usdt", "tl"], "ETH": ["tl"]})

    def test_max_dusus(self):
        self.assertAlmostEqual(bt.max_dusus([1, 2, 1, 3]), -50.0)


    def test_portfoy_al_tut_ortalama(self):
        a = [gun(i, 100 + 10 * i, 0, 0, 100 + 10 * i) for i in range(5)]   # 100 -> 140
        b = [gun(i, 100, 0, 0, 100) for i in range(5)]                     # yatay
        r = pf.calistir({"BTC": a, "X": b}, "al_tut", 0.0)
        # karar gün 0 kapanışında, alım gün 1 açılışında (110), son kapanış 140; X sabit
        self.assertAlmostEqual(r["getiri"], (140 / 110 - 1) * 50, places=6)

    def test_portfoy_ucret_ve_hizalama(self):
        a = [gun(i, 100, 0, 0, 100) for i in range(4)]
        r = pf.calistir({"BTC": a}, "al_tut", 0.01)
        self.assertAlmostEqual(r["getiri"], (0.99 * 0.99 - 1) * 100, places=6)
        h = pf.hizala({"A": [gun(0, 1, 1, 1, 1), gun(1, 1, 1, 1, 1)], "B": [gun(1, 1, 1, 1, 1)]})
        self.assertEqual([len(v) for v in h.values()], [1, 1])

    def test_portfoy_btc_rejimi_nakitte_tutar(self):
        # BTC sürekli düşüyor -> rejim kapalı -> X yükselse de alınmaz
        btc = [gun(i, 100 - i * 0.5, 0, 0, 100 - i * 0.5) for i in range(80)]
        x = [gun(i, 100 + i, 0, 0, 100 + i) for i in range(80)]
        r = pf.calistir({"BTC": btc, "X": x}, "sma50_btc", 0.0)
        self.assertAlmostEqual(r["getiri"], 0.0, places=6)
        self.assertGreater(pf.calistir({"BTC": btc, "X": x}, "sma50", 0.0)["getiri"], 0)


    def _ay(self):
        return {"kurallar": ["al_tut", "sma50"], "coinler": ["BTC", "ETH"], "baslangic_usdt": 1000,
                "ucret_pct": 0.0, "kayma_pct": 0.0, "min_islem_usdt": 10}

    def test_sanal_ilk_gun_al_tut_alir_ayni_gun_tekrar_islemez(self):
        btc = [gun(i, 100, 100, 100, 100) for i in range(60)]
        eth = [gun(i, 10 + i, 10 + i, 10 + i, 10 + i) for i in range(60)]
        mum = lambda c: {"BTC": btc, "ETH": eth}[c]
        fiyat = lambda cs: {"BTC": 100.0, "ETH": 70.0}
        d, rapor, tg = sanal.calistir(self._ay(), {}, mum, fiyat, log=lambda *a: None)
        at = d["hesaplar"]["al_tut"]["kasa"]
        self.assertAlmostEqual(at["BTC"]["adet"], 5.0)            # 500 USDT / 100
        self.assertAlmostEqual(at["ETH"]["adet"], 500 / 70)
        sm = d["hesaplar"]["sma50"]["kasa"]
        self.assertEqual(sm["BTC"]["adet"], 0.0)                  # yatay: ortalamanın üstünde değil
        self.assertGreater(sm["ETH"]["adet"], 0)                  # yükselen: al
        emirler = [x["emir"] for x in d["islemler"]]
        self.assertIn({"trade": "buy", "type": "market", "total": "500.00", "market": "btc_usdt"}, emirler)
        self.assertIsNone(sanal.calistir(self._ay(), d, mum, fiyat, log=lambda *a: None))

    def test_sanal_sinyal_bitince_satar_ve_ucret_duser(self):
        eth = [gun(i, 10 + i, 0, 0, 10 + i) for i in range(60)]
        btc = [gun(i, 100, 0, 0, 100) for i in range(61)]
        ay = self._ay()
        ay["ucret_pct"] = 1.0
        d, _, _ = sanal.calistir(ay, {}, lambda c: {"BTC": btc[:60], "ETH": eth}[c],
                                 lambda cs: {"BTC": 100.0, "ETH": 70.0}, log=lambda *a: None)
        eth2 = eth + [gun(60, 20, 0, 0, 20)]                      # sert düşüş: ortalamanın altı
        d2, _, _ = sanal.calistir(ay, d, lambda c: {"BTC": btc, "ETH": eth2}[c],
                                  lambda cs: {"BTC": 100.0, "ETH": 20.0}, log=lambda *a: None)
        k = d2["hesaplar"]["sma50"]["kasa"]["ETH"]
        self.assertEqual(k["adet"], 0.0)
        self.assertAlmostEqual(k["usdt"], 500 * 0.99 / 70 * 20 * 0.99, places=6)
        satis = [x for x in d2["islemler"] if x["yon"] == "sat"]
        self.assertTrue(satis[0]["emir"]["amount"])

    def test_sanal_paribu_fiyat_yoksa_kapanis(self):
        btc = [gun(i, 100, 0, 0, 100) for i in range(60)]
        d, rapor, _ = sanal.calistir(self._ay(), {}, lambda c: btc, lambda cs: {}, log=lambda *a: None)
        self.assertTrue(any("Paribu fiyatı alınamadı" in x for x in rapor))

    def test_paribu_fiyatlari_ayristirma(self):
        f = sanal.paribu_fiyatlari(["BTC", "ETH"], getir=lambda u: [
            {"market": "btc_usdt", "last": "95000.5"}, {"market": "eth_tl", "last": "1"}])
        self.assertEqual(f, {"BTC": 95000.5})


    # ---------------------------------------------------------------- vadeli
    def _sifir_funding(self, g):
        return {"BTC": {x["t"] // GUN: 0.0 for x in g}}

    def test_vadeli_1x_al_tut_spotla_ayni(self):
        g = [gun(i, 100 + 10 * i, 100 + 10 * i, 100 + 10 * i, 100 + 10 * i) for i in range(5)]
        r = vadeli.calistir({"BTC": g}, self._sifir_funding(g), "al_tut", False, 1, 0.0)
        self.assertAlmostEqual(r["getiri"], (140 / 110 - 1) * 100, places=6)
        self.assertEqual(r["tasfiye"], 0)

    def test_vadeli_3x_sert_dususte_tasfiye(self):
        g = [gun(0, 100, 100, 100, 100), gun(1, 100, 100, 100, 100), gun(2, 100, 100, 60, 90),
             gun(3, 90, 90, 90, 90)]
        r = vadeli.calistir({"BTC": g}, self._sifir_funding(g), "al_tut", False, 3, 0.0)
        self.assertEqual(r["tasfiye"], 1)
        self.assertAlmostEqual(r["getiri"], -100.0, places=6)
        r1 = vadeli.calistir({"BTC": g}, self._sifir_funding(g), "al_tut", False, 1, 0.0)
        self.assertEqual(r1["tasfiye"], 0)             # 1x: %40 iğne tasfiye etmez

    def test_vadeli_short_dususten_kazanir(self):
        g = [gun(i, 200 - 2 * i, 200 - 2 * i, 200 - 2 * i, 200 - 2 * i) for i in range(70)]
        f = self._sifir_funding(g)
        ls = vadeli.calistir({"BTC": g}, f, "sma50_btc_vol", True, 1, 0.0)
        lo = vadeli.calistir({"BTC": g}, f, "sma50_btc_vol", False, 1, 0.0)
        self.assertGreater(ls["getiri"], 0)
        self.assertGreater(ls["short_kar"], 0)
        self.assertAlmostEqual(lo["getiri"], 0.0, places=6)

    def test_vadeli_funding_long_oder(self):
        g = [gun(i, 100, 100, 100, 100) for i in range(4)]
        f = {"BTC": {x["t"] // GUN: 0.01 for x in g}}
        r = vadeli.calistir({"BTC": g}, f, "al_tut", False, 1, 0.0)
        self.assertLess(r["getiri"], 0)
        self.assertGreater(r["funding"], 0)

    def test_funding_zip_okuma(self):
        import io as _io
        import zipfile as _zf
        b = _io.BytesIO()
        with _zf.ZipFile(b, "w") as z:
            z.writestr("x.csv", "calc_time,funding_interval_hours,last_funding_rate\n"
                                "%d,8,0.0001\n%d,8,0.0002\n" % (GUN, GUN + 8 * 3600000))
        from datetime import datetime as _dt, timezone as _tz
        d = vadeli.funding_gunluk("BTCUSDT", _dt(2026, 1, 1, tzinfo=_tz.utc), _dt(2026, 1, 2, tzinfo=_tz.utc),
                                  getir=lambda u: b.getvalue(), bekle=0)
        self.assertAlmostEqual(d[1], 0.0003)


if __name__ == "__main__":
    unittest.main()
