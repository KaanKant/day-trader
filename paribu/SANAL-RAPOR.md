# Paribu sanal işlem

Son güncelleme: 2026-11-06 13:04 UTC (kapanmış günlük mum: 2026-11-05). Başlangıç: 2026-11-02.
**Sanal hesap. Gerçek emir verilmez.** Ücret %0.28 + kayma %0.05 her işlemde düşülür.

| Kural | Değer (USDT) | Başlangıçtan | Coinde olan pay | Bugünkü işlem |
|---|---|---|---|---|
| sma50_btc_vol | 200.00 | +0.0% | %0 | 0 |
| donchian_vol | 200.00 | +0.0% | %0 | 0 |
| al_tut | 194.72 | -2.6% | %100 | 0 |

### Vadeli (sanal, long + short)

Kaldıraç 1x, komisyon %0.05 + kayma %0.05, funding günlük %0.03 varsayımı (long öder, short alır). Fiyat: Paribu spot (vadeli fiyatına çok yakın).

| Hesap | Başlangıç | Değer (USDT) | Başlangıçtan | Long | Short | Tasfiye | Bugünkü işlem |
|---|---|---|---|---|---|---|---|
| sma50_btc_vol_1x | 2026-11-05 | 199.80 | -0.1% | - | BTC, ETH, SOL, XRP, DOGE, ADA, AVAX, LINK, TRX | - | 9 |

| Hesap | Coin | İşlem | Fiyat | Büyüklük (USDT) | Ücret | Binance vadeli emri (canlıda gidecek) |
|---|---|---|---|---|---|---|
| sma50_btc_vol_1x | BTC | short | 75986 | 22.22 | 0.02 | `{"symbol":"BTCUSDT","side":"SELL","type":"MARKET","quantity":"0.000292","reduceOnly":false}` |
| sma50_btc_vol_1x | ETH | short | 2237.73 | 22.22 | 0.02 | `{"symbol":"ETHUSDT","side":"SELL","type":"MARKET","quantity":"0.009931","reduceOnly":false}` |
| sma50_btc_vol_1x | SOL | short | 90.14 | 22.22 | 0.02 | `{"symbol":"SOLUSDT","side":"SELL","type":"MARKET","quantity":"0.246530","reduceOnly":false}` |
| sma50_btc_vol_1x | XRP | short | 1.19 | 22.22 | 0.02 | `{"symbol":"XRPUSDT","side":"SELL","type":"MARKET","quantity":"18.674136","reduceOnly":false}` |
| sma50_btc_vol_1x | DOGE | short | 0.072 | 22.22 | 0.02 | `{"symbol":"DOGEUSDT","side":"SELL","type":"MARKET","quantity":"308.641975","reduceOnly":false}` |
| sma50_btc_vol_1x | ADA | short | 0.1858 | 21.99 | 0.02 | `{"symbol":"ADAUSDT","side":"SELL","type":"MARKET","quantity":"118.356800","reduceOnly":false}` |
| sma50_btc_vol_1x | AVAX | short | 8.43 | 22.22 | 0.02 | `{"symbol":"AVAXUSDT","side":"SELL","type":"MARKET","quantity":"2.636088","reduceOnly":false}` |
| sma50_btc_vol_1x | LINK | short | 10.881 | 18.36 | 0.02 | `{"symbol":"LINKUSDT","side":"SELL","type":"MARKET","quantity":"1.687569","reduceOnly":false}` |
| sma50_btc_vol_1x | TRX | short | 0.3182 | 22.22 | 0.02 | `{"symbol":"TRXUSDT","side":"SELL","type":"MARKET","quantity":"69.837279","reduceOnly":false}` |

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
| 2026-11-05 | 200 | 200 | 194 |
| 2026-11-04 | 200 | 200 | 206 |
| 2026-11-03 | 200 | 200 | 200 |
| 2026-11-02 | 200 | 200 | 199 |

Kurallar: `sma50_btc_vol` = coin 50 günlük ortalamanın, BTC de kendi ortalamasının üstündeyse al; pay oynaklığa göre küçülür. `donchian_vol` = 20 günün zirvesini kırınca al, 10 günün dibini kırınca sat; pay oynaklığa göre. `al_tut` = karşılaştırma için baştan sona elde tut. Ayrıntı: PORTFOY-RAPORU.md.
