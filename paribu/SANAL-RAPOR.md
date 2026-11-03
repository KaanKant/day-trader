# Paribu sanal işlem

Son güncelleme: 2026-11-03 12:13 UTC (kapanmış günlük mum: 2026-11-02). Başlangıç: 2026-11-02.
**Sanal hesap. Gerçek emir verilmez.** Ücret %0.28 + kayma %0.05 her işlemde düşülür.

| Kural | Değer (USDT) | Başlangıçtan | Coinde olan pay | Bugünkü işlem |
|---|---|---|---|---|
| sma50_btc_vol | 200.00 | +0.0% | %0 | 0 |
| donchian_vol | 200.00 | +0.0% | %0 | 0 |
| al_tut | 199.34 | -0.3% | %100 | 9 |

## Bugünkü işlemler

| Kural | Coin | Yön | Fiyat | USDT | Ücret | Paribu emri (canlıda gidecek) |
|---|---|---|---|---|---|---|
| al_tut | BTC | al | 77086 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"btc_usdt"}` |
| al_tut | ETH | al | 2267.15 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"eth_usdt"}` |
| al_tut | SOL | al | 92.54 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"sol_usdt"}` |
| al_tut | XRP | al | 1.2601 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"xrp_usdt"}` |
| al_tut | DOGE | al | 0.0745 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"doge_usdt"}` |
| al_tut | ADA | al | 0.1894 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"ada_usdt"}` |
| al_tut | AVAX | al | 8.52 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"avax_usdt"}` |
| al_tut | LINK | al | 11.14 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"link_usdt"}` |
| al_tut | TRX | al | 0.3225 | 22.22 | 0.06 | `{"trade":"buy","type":"market","total":"22.22","market":"trx_usdt"}` |

## Pozisyonlar

| Kural | BTC | ETH | SOL | XRP | DOGE | ADA | AVAX | LINK | TRX |
|---|---|---|---|---|---|---|---|---|---|
| sma50_btc_vol | - | - | - | - | - | - | - | - | - |
| donchian_vol | - | - | - | - | - | - | - | - | - |
| al_tut | %100 | %100 | %100 | %100 | %100 | %100 | %100 | %100 | %100 |

## Son 30 gün (USDT)

| Gün | sma50_btc_vol | donchian_vol | al_tut |
|---|---|---|---|
| 2026-11-02 | 200 | 200 | 199 |

Kurallar: `sma50_btc_vol` = coin 50 günlük ortalamanın, BTC de kendi ortalamasının üstündeyse al; pay oynaklığa göre küçülür. `donchian_vol` = 20 günün zirvesini kırınca al, 10 günün dibini kırınca sat; pay oynaklığa göre. `al_tut` = karşılaştırma için baştan sona elde tut. Ayrıntı: PORTFOY-RAPORU.md.
