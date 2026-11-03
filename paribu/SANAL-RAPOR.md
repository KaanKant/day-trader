# Paribu sanal işlem

Son güncelleme: 2026-11-03 12:09 UTC (kapanmış günlük mum: 2026-11-02). Başlangıç: 2026-11-02.
**Sanal hesap. Gerçek emir verilmez.** Ücret %0.28 + kayma %0.05 her işlemde düşülür.

| Kural | Değer (USDT) | Başlangıçtan | Coinde olan pay | Bugünkü işlem |
|---|---|---|---|---|
| sma50_btc_vol | 1000.00 | +0.0% | %0 | 0 |
| donchian_vol | 1000.00 | +0.0% | %0 | 0 |
| al_tut | 996.70 | -0.3% | %100 | 9 |

## Bugünkü işlemler

| Kural | Coin | Yön | Fiyat | USDT | Ücret | Paribu emri (canlıda gidecek) |
|---|---|---|---|---|---|---|
| al_tut | BTC | al | 77068.3 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"btc_usdt"}` |
| al_tut | ETH | al | 2266.47 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"eth_usdt"}` |
| al_tut | SOL | al | 92.51 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"sol_usdt"}` |
| al_tut | XRP | al | 1.2584 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"xrp_usdt"}` |
| al_tut | DOGE | al | 0.0745 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"doge_usdt"}` |
| al_tut | ADA | al | 0.1894 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"ada_usdt"}` |
| al_tut | AVAX | al | 8.52 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"avax_usdt"}` |
| al_tut | LINK | al | 11.151 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"link_usdt"}` |
| al_tut | TRX | al | 0.3224 | 111.11 | 0.31 | `{"trade":"buy","type":"market","total":"111.11","market":"trx_usdt"}` |

## Pozisyonlar

| Kural | BTC | ETH | SOL | XRP | DOGE | ADA | AVAX | LINK | TRX |
|---|---|---|---|---|---|---|---|---|---|
| sma50_btc_vol | - | - | - | - | - | - | - | - | - |
| donchian_vol | - | - | - | - | - | - | - | - | - |
| al_tut | %100 | %100 | %100 | %100 | %100 | %100 | %100 | %100 | %100 |

## Son 30 gün (USDT)

| Gün | sma50_btc_vol | donchian_vol | al_tut |
|---|---|---|---|
| 2026-11-02 | 1000 | 1000 | 997 |

Kurallar: `sma50_btc_vol` = coin 50 günlük ortalamanın, BTC de kendi ortalamasının üstündeyse al; pay oynaklığa göre küçülür. `donchian_vol` = 20 günün zirvesini kırınca al, 10 günün dibini kırınca sat; pay oynaklığa göre. `al_tut` = karşılaştırma için baştan sona elde tut. Ayrıntı: PORTFOY-RAPORU.md.
