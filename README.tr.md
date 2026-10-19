<h1 align="center">lexdays</h1>

<p align="center">
  <b>Açıklamalı hukuki süre ve iş günü hesaplama.</b><br>
  Her sonuç <i>neden</i> o tarih olduğunu söyler ve uyguladığı kanun maddesini gösterir.
</p>

<p align="center">
  Python · TypeScript · Komut satırı · bağımlılıksız · MIT lisansı<br>
  <a href="README.md">English</a> ·
  <a href="https://dogood-studio.github.io/lexdays/">Canlı demo</a> ·
  <a href="docs/jurisdictions/tr.md">Türkiye kuralları ve tartışmalı noktalar</a> ·
  <a href="docs/RELIABILITY.md">Güvenilirlik raporu</a>
</p>

---

Tatil kütüphaneleri hangi günün tatil olduğunu söyler. Avukatların, hukuk yazılımı geliştirenlerin, muhasebecilerin ve İK ekiplerinin ihtiyacı ise başka: **işlemin yapılabileceği son gün ve bunun gerekçesi.**

```python
>>> import lexdays
>>> r = lexdays.compute("tr/hmk", "2026-07-30", "P2W")   # HMK: tebliğden itibaren 2 hafta
>>> r.deadline
datetime.date(2026, 9, 8)
>>> print(r.explain("tr"))
1. 30.07.2026 Perşembe tarihinden itibaren 2 hafta, son haftada aynı adı taşıyan günde biter: 13.08.2026 Perşembe. [HMK m.92]
2. 13.08.2026 Perşembe, adli tatil (20.07.2026 Pazartesi – 31.08.2026 Pazartesi) içine düşüyor; süre, tatilin bitimini izleyen 01.09.2026 Salı tarihinden itibaren 7 gün uzar: 08.09.2026 Salı. [HMK m.102 ve m.104]
3. 08.09.2026 Salı iş günü; düzeltme gerekmez. [HMK m.93]
4. Süre son günün 23:59 saatinde sona erer. [HMK m.445/4]
Son gün: 08.09.2026 Salı
Bitiş saati: 23:59 (Europe/Istanbul)
```

## Neler yapar?

- **Hukuki süre hesaplama.** HMK, İİK, CMK, İYUK, VUK ve Anayasa Mahkemesi bireysel başvurusu için ayrı kural paketleri vardır. Hepsi şunları hesaba katar:
  - adli tatil (uzama veya erteleme)
  - arife ve 28 Ekim yarım günleri
  - e-tebligatta 5. gün kuralı
  - son günün resmî tatile, Cumartesiye veya bayrama rastlaması
  - ay sonu kuralı (31 Ocak + 1 ay = 28/29 Şubat)
- **Kaynak gösterir.** Her adımda dayandığı kanun maddesi veya karar yazar. Sonuç denetlenebilir ve dilekçeye ya da iç kayda eklenebilir. Açıklama 12 dilde alınabilir: Türkçe, İngilizce, Almanca, Fransızca, İspanyolca, İtalyanca, Portekizce, Felemenkçe, Rusça, Arapça, Çince ve Japonca. Kural notları ve atıf etiketleri İngilizce ve gerektiğinde mahkemenin dilindedir.
- **Tartışmalı noktaları gizlemez.** İçtihadın veya uygulamanın bölündüğü yerler seçenek olarak sunulur ve sonuca açıklayıcı bir not eklenir. Varsayılan, yerleşik yüksek mahkeme içtihadı varsa onu izler; yoksa daha erken, yani güvenli tarihtir. Örnekler:
  - adli tatil sonrası 7 Eylül mü, 8 Eylül mü
  - süre arifede biterse ne olur
  - tatil kuralıyla adli tatile kayan son gün
  - CMK'da adli tatil içinde yapılan tebliğ
- **Tahmin yapmaz.** Takvimin doğrulanmış yılları dışında hesap istenirse yanlış tarih vermek yerine hata verir.
- **İş günü hesabı:** iş günü mü, n iş günü sonrası, iki tarih arası iş günü sayısı, resmî tatil listesi. Bayram tarihleri 2000–2035 için Diyanet takviminden alınmıştır; idari izin ayrı bir tür olarak ele alınır.

## Kurulum

```bash
pip install lexdays          # Python 3.10+
npm install lexdays          # Node 18+, tarayıcı, Deno, Bun
```

## Örnekler

```python
import lexdays

# İcra: ödeme emrine itiraz, 7 gün. Son gün arife: süre o gün biter (Yargıtay 12. HD)
r = lexdays.compute("tr/iik", "2015-09-16", "P7D")
r.deadline                      # 2015-09-23
[n.code for n in r.notices]     # ['half-day-last-day']

# E-tebligat: ulaşma tarihini girin; tebliğ 5. günün sonunda yapılmış sayılır
lexdays.compute("tr/hmk", "2026-10-13", "P2W", options={"service": "e_notification_delivery"}).deadline
# 2026-11-02

# İdari yargı: 60 günlük dava açma süresi ara vermeye rastlarsa 7 Eylül
lexdays.compute("tr/iyuk", "2026-06-10", "P60D").deadline        # 2026-09-07

# Ceza: adli tatile rastlayan süre 3 gün uzar
lexdays.compute("tr/cmk", "2024-07-13", "P2W").deadline          # 2024-09-03

# Adli tatilde görülen işler (nafaka, işçi alacağı, icra mahkemesi ...): uzama yok
lexdays.compute("tr/hmk", "2019-07-26", "P2W", options={"judicial_recess": "exempt"}).deadline   # 2019-08-09

# İş günü
tr = lexdays.calendar("tr")
tr.add_business_days("2026-05-22", 3)           # 2026-06-01: Kurban Bayramı atlanır
tr.business_days_between("2026-01-01", "2026-12-31")
[h.label("tr") for h in tr.holidays(2026)]
```

Komut satırından:

```bash
lexdays deadline tr/hmk 2026-07-30 2w --lang tr
lexdays deadline tr/iik 2026-05-22 "7 gün" --lang tr --json
lexdays holidays tr 2027 --lang tr
lexdays add tr 2026-05-22 3
```

## Türkiye kural paketleri

| Paket | Kapsam | Önemli seçenekler |
|---|---|---|
| `tr/hmk` | HMK m.92–93, 102–104, 445/4 | `service`, `filing`, `judicial_recess`, `recess_extension_from` (8 / 7 Eylül), `recess_after_holiday_shift`, `half_day_last_day` |
| `tr/iik` | İİK m.19, 8/a (adli tatil yok) | `service`, `filing`, `half_day_last_day` |
| `tr/cmk` | CMK m.39, 331 (3 gün uzama) | `service`, `filing`, `served_in_recess`, `half_day_last_day` |
| `tr/iyuk` | İYUK m.8, 61 (7 Eylül) | `service`, `filing`, `court_break`, `half_day_last_day` |
| `tr/vuk` | VUK m.18, 107/A | `service`, `filing` |
| `tr/aym` | 6216 s.K. m.47/5 (öğrenmeden itibaren 30 gün) | – |

Kuralların dayanakları, kararlar ve tartışmalı noktalar [docs/jurisdictions/tr.md](docs/jurisdictions/tr.md) dosyasındadır. Test vektörlerinin önemli bir bölümü gerçek Yargıtay, Danıştay ve Anayasa Mahkemesi kararlarındaki tarihlerden oluşur. Paket bu kararların hepsinde aynı sonucu verir.

## Global

Aynı motor ABD federal mahkemeleri (FRCP 6), İngiltere ve Galler (CPR 2.8), AB Adalet Divanı ve Almanya (ZPO, 16 eyalet takvimiyle) için de çalışır. Ayrıntılar [README.md](README.md) dosyasındadır.

## Katkı

Özellikle avukatların kural incelemesine ve hata bildirimine ihtiyaç var. Yanlış bulduğunuz bir sonucu dayanağıyla birlikte ["Kural düzeltmesi" issue şablonuyla](https://github.com/DoGood-Studio/lexdays/issues/new/choose) bildirin. Ayrıntılar [CONTRIBUTING.md](CONTRIBUTING.md) dosyasındadır.

## Sorumluluk reddi

lexdays bilgilendirme amaçlı bir araçtır, hukuki danışmanlık değildir. Kanun, içtihat, mahkeme kararları ve yerel uygulama her zaman önceliklidir. Önemli bir süreyi mutlaka kontrol edin.

## Lisans

[MIT](LICENSE)
