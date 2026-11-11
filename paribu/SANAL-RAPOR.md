# Paribu sanal işlem

Son güncelleme: 2026-11-11 06:06 UTC (kapanmış günlük mum: 2026-11-10). Başlangıç: 2026-11-02.
**Sanal hesap. Gerçek emir verilmez.** Ücret %0.28 + kayma %0.05 her işlemde düşülür.

| Kural | Değer (USDT) | Başlangıçtan | Coinde olan pay | Bugünkü işlem |
|---|---|---|---|---|
| sma50_btc_vol | 200.00 | +0.0% | %0 | 0 |
| donchian_vol | 200.00 | +0.0% | %0 | 0 |
| al_tut | 185.07 | -7.5% | %100 | 0 |

### Vadeli (sanal, long + short)

Kaldıraç 1x, komisyon %0.05 + kayma %0.05, funding günlük %0.03 varsayımı (long öder, short alır). Fiyat: Paribu spot (vadeli fiyatına çok yakın).

| Hesap | Başlangıç | Değer (USDT) | Başlangıçtan | Long | Short | Tasfiye | Bugünkü işlem |
|---|---|---|---|---|---|---|---|
| sma50_btc_vol_1x | 2026-11-05 | 209.89 | +4.9% | - | BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK, TRX | - | 0 |

## Bugünkü işlemler

Bugün işlem yok.

## Pozisyonlar

| Kural | BTC | ETH | SOL | XRP | DOGE | ADA | AVAX | LINK | TRX |
|---|---|---|---|---|---|---|---|---|---|
| sma50_btc_vol | - | - | - | - | - | - | - | - | - |
| donchian_vol | - | - | - | - | - | - | - | - | - |
| al_tut | %100 | %100 | %100 | %100 | %100 | %100 | %100 | %100 | %100 |

## Son 30 gün (USDT)

| Gün | sma50_btc_vol | donchian_vol | al_tut |
|---|---|---|---|
| 2026-11-10 | 200 | 200 | 185 |
| 2026-11-09 | 200 | 200 | 189 |
| 2026-11-08 | 200 | 200 | 186 |
| 2026-11-07 | 200 | 200 | 193 |
| 2026-11-06 | 200 | 200 | 194 |
| 2026-11-05 | 200 | 200 | 194 |
| 2026-11-04 | 200 | 200 | 206 |
| 2026-11-03 | 200 | 200 | 200 |
| 2026-11-02 | 200 | 200 | 199 |

Kurallar: `sma50_btc_vol` = coin 50 günlük ortalamanın, BTC de kendi ortalamasının üstündeyse al; pay oynaklığa göre küçülür. `donchian_vol` = 20 günün zirvesini kırınca al, 10 günün dibini kırınca sat; pay oynaklığa göre. `al_tut` = karşılaştırma için baştan sona elde tut. Ayrıntı: PORTFOY-RAPORU.md.
