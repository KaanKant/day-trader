# Vadeli işlem testi (long/short, kaldıraç)

Tarih: 2026-11-06 12:50 UTC | Komisyon %0.05 + kayma %0.05, pozisyon büyüklüğü üzerinden
Coinler (sermaye eşit bölündü, her coin ayrı teminatlı): BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK, TRX
Dönem: 2020-11-08 → 2026-11-05 (2189 gün). Yarılar: 2023-11-07'e kadar / sonrası.
Gerçek funding kaydı olan günler: ortalama %100 (kalanı için 8 saatte %0.01 varsayıldı).

### Tüm dönem

| Senaryo | Toplam getiri | Yıllık | En büyük düşüş | Yıllık / düşüş | Tasfiye olan coin | Short'un katkısı | Ödenen funding | Ödenen ücret |
|---|---|---|---|---|---|---|---|---|
| sma50_btc_vol sadece long 1x | +1166% | +52.7% | -50% | 1.06 | 0 | +0% | +239% | 96% |
| sma50_btc_vol sadece long 2x | +4160% | +86.9% | -78% | 1.12 | 1 | +0% | +2025% | 758% |
| sma50_btc_vol sadece long 3x | +3449% | +81.3% | -95% | 0.86 | 2 | +0% | +6596% | 1993% |
| sma50_btc_vol long+short 1x | +2362% | +70.6% | -50% | 1.41 | 0 | +503% | +400% | 279% |
| sma50_btc_vol long+short 2x | +9030% | +112.3% | -87% | 1.29 | 1 | -6040% | +4826% | 2692% |
| sma50_btc_vol long+short 3x | +4729% | +90.9% | -99% | 0.92 | 3 | -43564% | +19144% | 7479% |
| donchian_vol sadece long 1x | +445% | +32.7% | -37% | 0.89 | 0 | +0% | +107% | 21% |
| donchian_vol sadece long 2x | +1146% | +52.3% | -64% | 0.82 | 0 | +0% | +448% | 92% |
| donchian_vol sadece long 3x | +1537% | +59.4% | -83% | 0.72 | 1 | +0% | +867% | 179% |
| donchian_vol long+short 1x | +272% | +24.5% | -49% | 0.50 | 0 | -78% | +99% | 33% |
| donchian_vol long+short 2x | +291% | +25.5% | -87% | 0.29 | 0 | -431% | +329% | 100% |
| donchian_vol long+short 3x | -67% | -16.8% | -99% | -0.17 | 2 | -1068% | +427% | 110% |
| al_tut sadece long 1x | +42% | +6.0% | -100% | 0.06 | 8 | +0% | +521% | 0% |
| al_tut sadece long 2x | +172% | +18.2% | -100% | 0.18 | 8 | +0% | +793% | 0% |
| al_tut sadece long 3x | +302% | +26.1% | -100% | 0.26 | 8 | +0% | +1110% | 0% |

### 1. yarı (eski)

| Senaryo | Toplam getiri | Yıllık | En büyük düşüş | Yıllık / düşüş | Tasfiye olan coin | Short'un katkısı | Ödenen funding | Ödenen ücret |
|---|---|---|---|---|---|---|---|---|
| sma50_btc_vol sadece long 1x | +566% | +88.3% | -30% | 2.96 | 0 | +0% | +67% | 19% |
| sma50_btc_vol sadece long 2x | +2194% | +184.4% | -53% | 3.45 | 0 | +0% | +298% | 98% |
| sma50_btc_vol sadece long 3x | +4202% | +250.8% | -72% | 3.49 | 0 | +0% | +787% | 254% |
| sma50_btc_vol long+short 1x | +1242% | +137.8% | -35% | 3.92 | 0 | +527% | +100% | 49% |
| sma50_btc_vol long+short 2x | +7758% | +328.9% | -59% | 5.53 | 0 | +3571% | +554% | 319% |
| sma50_btc_vol long+short 3x | +19766% | +484.4% | -76% | 6.34 | 0 | +9389% | +1503% | 889% |
| donchian_vol sadece long 1x | +221% | +47.6% | -37% | 1.30 | 0 | +0% | +45% | 6% |
| donchian_vol sadece long 2x | +469% | +78.6% | -64% | 1.24 | 0 | +0% | +141% | 21% |
| donchian_vol sadece long 3x | +497% | +81.5% | -83% | 0.99 | 0 | +0% | +288% | 42% |
| donchian_vol long+short 1x | +199% | +44.1% | -40% | 1.10 | 0 | +23% | +48% | 11% |
| donchian_vol long+short 2x | +364% | +66.9% | -68% | 0.99 | 0 | +58% | +136% | 30% |
| donchian_vol long+short 3x | +234% | +49.6% | -86% | 0.58 | 0 | -111% | +201% | 39% |
| al_tut sadece long 1x | -63% | -28.6% | -100% | -0.29 | 8 | +0% | +529% | 0% |
| al_tut sadece long 2x | -38% | -14.8% | -100% | -0.15 | 8 | +0% | +810% | 0% |
| al_tut sadece long 3x | -13% | -4.4% | -100% | -0.04 | 8 | +0% | +1135% | 0% |

### 2. yarı (yeni)

| Senaryo | Toplam getiri | Yıllık | En büyük düşüş | Yıllık / düşüş | Tasfiye olan coin | Short'un katkısı | Ödenen funding | Ödenen ücret |
|---|---|---|---|---|---|---|---|---|
| sma50_btc_vol sadece long 1x | +54% | +15.4% | -31% | 0.50 | 0 | +0% | +13% | 8% |
| sma50_btc_vol sadece long 2x | +85% | +22.8% | -50% | 0.46 | 1 | +0% | +27% | 18% |
| sma50_btc_vol sadece long 3x | +96% | +25.1% | -65% | 0.39 | 2 | +0% | +38% | 28% |
| sma50_btc_vol long+short 1x | +55% | +15.8% | -40% | 0.39 | 0 | +10% | +11% | 13% |
| sma50_btc_vol long+short 2x | +88% | +23.5% | -64% | 0.37 | 1 | +17% | +20% | 22% |
| sma50_btc_vol long+short 3x | +120% | +30.1% | -77% | 0.39 | 3 | +41% | +27% | 27% |
| donchian_vol sadece long 1x | +34% | +10.3% | -29% | 0.35 | 0 | +0% | +13% | 4% |
| donchian_vol sadece long 2x | +56% | +16.1% | -51% | 0.32 | 0 | +0% | +29% | 9% |
| donchian_vol sadece long 3x | +69% | +19.0% | -66% | 0.29 | 1 | +0% | +44% | 13% |
| donchian_vol long+short 1x | -4% | -1.3% | -37% | -0.03 | 0 | -36% | +12% | 6% |
| donchian_vol long+short 2x | -23% | -8.3% | -61% | -0.14 | 0 | -80% | +27% | 11% |
| donchian_vol long+short 3x | -40% | -15.6% | -75% | -0.21 | 2 | -117% | +47% | 15% |
| al_tut sadece long 1x | +10% | +3.3% | -74% | 0.04 | 1 | +0% | +37% | 0% |
| al_tut sadece long 2x | +15% | +4.7% | -82% | 0.06 | 6 | +0% | +63% | 0% |
| al_tut sadece long 3x | +55% | +15.8% | -82% | 0.19 | 6 | +0% | +85% | 0% |

Notlar:
- Tasfiye olan coin: o coinin teminatı tamamen gitti ve dönem sonuna kadar işlem yapmadı.
- Short'un katkısı: short pozisyonlardan gelen fiyat kâr/zararı, başlangıç sermayesinin yüzdesi olarak (ücret ve funding hariç).
- Ödenen funding eksiyse funding'den net kazanılmıştır (short pozisyonlar pozitif funding'de para alır).
- Spot Paribu botuyla karşılaştırma için PORTFOY-RAPORU.md (sadece long, 1x, %0.28 ücret).
- Geçmiş sonuç geleceği garanti etmez. Tasfiye modeli günlük mumla yapıldı; gerçekte gün içi iğneler daha sık tasfiye yaratabilir.
