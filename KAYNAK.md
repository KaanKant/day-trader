# Kaynak ve inceleme notu

Bu depo [jakeschincariol/day-trader-skill](https://github.com/Jakeschincariol/day-trader-skill)
deposunun **3d0f4ef** (2026-10-20) sürümünün kopyasıdır (MIT lisansı, bkz. LICENSE).

Kopyalanmadan önce kod okunarak incelendi (2026-11-03):
- Kod sadece herkese açık veri kaynaklarına bağlanıyor (Yahoo Finance, SEC EDGAR,
  Stooq, ABD Meclis bildirimleri, Nasdaq sembol listesi). Başka bir sunucuya veri gitmiyor.
- Gizli/şifreli kod, eval/exec, görünmez karakter yok. Dış kütüphane kurulmuyor.
- `ticket.py` hiçbir aracı kuruma bağlanmaz; emri broker'ın MCP aracı gönderir.
  O aracın izni her zaman "Needs approval" olmalı, asla "Always allow" değil.
- Küçük not: `trader-pelosi/ptr.py` Meclis dizinindeki DocID'yi doğrulamadan dosya
  adında kullanıyor (risk çok düşük).

Orijinal depodaki güncellemeler buraya otomatik gelmez. Güncelleme alınacaksa önce
aynı inceleme tekrarlanır.
