# Türkiye: süre kuralları, dayanaklar ve tartışmalı noktalar

*English summary: how the Turkish rule packs work, the statutes and decisions they rely on, and the points on which case law is divided. Disputed points are options; the default follows settled high-court case law, otherwise the earlier, safer date.*

Bu sayfa `tr/*` kural paketlerinin hangi kurala dayandığını ve içtihadın bölündüğü yerlerde nasıl davrandığını özetler. Paketlerin durumu **beta**dır: kanun metinleri ve kararlar incelenmiştir, ancak henüz uygulamacı avukatlarca gözden geçirilmemiştir. Düzeltme ve görüşler için ["Kural düzeltmesi" şablonunu](https://github.com/DoGood-Studio/lexdays/issues/new/choose) kullanın.

## Ortak kurallar

| Konu | Kural | Dayanak |
|---|---|---|
| Gün olarak süre | Tebliğ günü sayılmaz; son gün = tebliğ + n gün | HMK m.92/1, İİK m.19/1, CMK m.39/1, İYUK m.8/1, VUK m.18/1 |
| Hafta olarak süre | Son haftada tebliğ gününe karşılık gelen gün | HMK m.92/2, CMK m.39/2, İİK m.19/2 (1.6.2024'ten itibaren, 7499 s.K.) |
| Ay / yıl olarak süre | Aynı gün numarası; o gün yoksa ayın son günü (31 Ocak + 1 ay = 28/29 Şubat) | HMK m.92/2, CMK m.39/3, İİK m.19/2, VUK m.18/2 |
| Aradaki tatiller | Süreye dahildir; yalnız son gün kayar | HMK m.93, İYUK m.8/2, VUK m.18/4 |
| Son gün tatil | İlk iş gününe kayar. Cumartesi de tatil sayılır (657 s.K. m.99; Yargıtay HGK E.2024/9-158) | HMK m.93, İİK m.19/3, CMK m.39/4, İYUK m.8/2, VUK m.18/4 |
| Elektronik işlem | Son gün 23.59'a kadar; esas alınan an sisteme kayıt zamanıdır | HMK m.445/4, İİK m.8/a, CMK m.38/A-9; HGK E.2024/9-158 |
| Fizikî işlem | Mesai saati sonunda biter. Saat kanunda sabit değildir (657 s.K. m.100) | Yönetmelik m.5/14 |
| E-tebligat | Tebliğ, ulaşmayı izleyen 5. günün sonunda yapılmış sayılır. 5. gün tatile rastlasa da kaymaz; süre ertesi gün başlar | TK m.7/a; Yargıtay HGK E.2019/623 K.2020/9; AYM Mehmet Özcan |
| İdari izin | Resmî tatil değildir, süreyi uzatmaz | Yargıtay 16. HD E.2016/14817; 7. HD E.2021/454; Danıştay 8. D. E.2007/1550 |

## Adli tatil

| Paket | Kural | Sonuç |
|---|---|---|
| `tr/hmk` | Adli tatile tabi işlerde son gün 20.07–31.08 içine düşerse bir hafta uzar (m.104) | **8 Eylül** (HGK E.2017/20-2873: bir hafta 1 Eylül'den başlar); 8 Eylül tatilse ilk iş günü |
| `tr/cmk` | Adli tatile rastlayan süreler işlemez ve tatil bitiminden itibaren üç gün uzar (m.331/4). Tutuklu işler istisna değildir (CGK E.2019/16-292; AYM Ramazan Seçen) | **3 Eylül**; tatilse ilk iş günü |
| `tr/iyuk` | Son gün (tatil kaydırması sonrasında da) ara vermeye düşerse yedi gün uzar (m.8/3) | **7 Eylül**; tatilse ilk iş günü |
| `tr/iik` | İcra daireleri ve icra mahkemeleri adli tatilde çalışır; HMK m.104 uygulanmaz | Uzama yok (HGK E.2017/(6)8-1853 K.2021/1529) |
| `tr/vuk` | Adli tatil VUK sürelerini etkilemez | Uzama yok. Vergi mahkemesinde dava açma süresi için `tr/iyuk` kullanılır |
| `tr/aym` | Bireysel başvuruda adli tatil uygulanmaz | Uzama yok (AYM Turgut Tayyar 2013/7168) |

Adli tatilde görülen işler (HMK m.103: nafaka, soybağı, işçinin iş sözleşmesinden doğan davaları, çekişmesiz yargı, iflas, icra mahkemesi, kamulaştırma, kadastro, mahkemece ivedi sayılan işler) için `tr/hmk` paketinde `judicial_recess="exempt"` seçilir.

## Tartışmalı noktalar ve paketlerin davranışı

| # | Konu | Varsayılan | Seçenek | Not |
|---|---|---|---|---|
| D-1 | HMK m.104 uzaması: 7 Eylül mü, 8 Eylül mü? | **8 Eylül**: Yargıtay HGK E.2017/20-2873 ve daire kararları bu yöntemle tutarlıdır | `recess_extension_from="end"` → 7 Eylül (daha erken, en temkinli) | Uzama uygulandığında `recess-extension-hgk-method` notu "şüphede 7 Eylül'e kadar işlem yapın" der; 7 Eylül seçilirse `recess-7-september-method` notu eklenir |
| D-2 | Son gün arife veya 28 Ekim | Süre **o gün biter** (Yargıtay 12. HD E.2016/29555; CGK E.2001/5-52; AYM Abdulkadir Önen) | `half_day_last_day="non_working"` → bayram sonrası (azınlık görüşü, kararı yok) | Fizikî işlemde 13.00 kapanışı yaygın kabul görür, kararla teyitli değildir; `half-day-last-day` notu |
| D-5 | Son gün tatil kuralıyla (m.93) adli tatile kayarsa (ör. 19 Temmuz Pazar → 20 Temmuz) | **20 Temmuz** (uzamasız, erken tarih) | `recess_after_holiday_shift="yes"` → 8 Eylül | Doğrudan karar yok; `holiday-shift-into-recess` notu |
| CMK D1 | Adli tatil içinde yapılan tebliğ | Süre işler, tatilde biterse **3 Eylül** (erken tarih) | `served_in_recess="defer_start"` → süre tatil bitiminden itibaren işler (çoğunluk görüşü) | `served-in-recess` notu |
| İYUK D7 | Ara vermeden yararlanmayan tek mahkemeli yerler (m.61/1) | Ara verme uygulanır | `court_break="not_applicable"` | Belirsiz |
| İİK | 1.6.2024 öncesi hafta kuralı | Hafta = 7n gün | – | `week-rule-from-2024` notu: eski sürelerin çoğu "on gün" idi |
| Tümü | 2012 öncesi adli tatil dönemleri | Paketler 20.07–31.08'i 2012'den itibaren uygular | – | 2005–2011: 1 Ağustos–5 Eylül; 2004 ve öncesi: 20 Temmuz–5 Eylül. Eski uzama kuralları doğrulanmadığı için 2012 öncesi tebliğlerde uyarı verilir |

## Takvim verisi (`tr`)

- 2429 sayılı Kanun'daki tatiller ve yürürlük yılları: 1 Mayıs 2009'dan, 15 Temmuz 2017'den itibaren.
- Arife ve 28 Ekim, 13.00'ten itibaren yarım gündür (1981'den beri kanun metninde).
- Ramazan ve Kurban Bayramı tarihleri Diyanet İşleri Başkanlığı'ndan alınmıştır (2000–2035; aynı yıl iki bayramın düştüğü 2000, 2006 ve 2033 dahil). Diyanet 2035 sonrasını yayımlamadığı için kapsam 2035'te biter. Python `holidays` kütüphanesiyle karşılaştırıldığında fark yoktur.
- Cumartesi ve Pazar resmî daireler için çalışılmayan günlerdir (657 s.K. m.99).

## Örnek kararlar (test vektörlerinden)

| Olay | Kütüphanenin sonucu | Karar |
|---|---|---|
| Tebliğ 08.08.2018, 2 hafta | 10.09.2018 (8 Eylül Cumartesi) | Yargıtay 2. HD E.2019/2507 K.2019/8376 |
| Tebliğ 23.06.2016, 15 gün | 08.07.2016 (idari izin, kaymaz) | Yargıtay 16. HD E.2016/14817 K.2017/1983 |
| Ödeme emri 16.09.2015, 7 gün | 23.09.2015 (arife, kaymaz) | Yargıtay 12. HD E.2016/29555 K.2018/2478 |
| E-tebligat ulaşma 30.07.2019, 10 gün | 15.08.2019 | Yargıtay HGK E.2019/623 K.2020/9 |
| Tebliğ 13.07.2024, CMK 2 hafta | 03.09.2024 | Yargıtay 8. CD E.2025/3648 K.2025/5977 |
| Tebliğ 02.08.2012, İYUK 30 gün | 03.09.2012 | Danıştay 15. D. E.2015/4978 K.2015/6823 |
| Öğrenme 01.08.2013, bireysel başvuru | 02.09.2013 | AYM Turgut Tayyar 2013/7168 |

Tam liste: [`vectors/tr/deadline.json`](../../vectors/tr/deadline.json).

## Kapsam dışı

- Maddi hukuk süreleri (zamanaşımı, hak düşürücü süreler) ve TBK m.93.
- GİB'in idari süre uzatmaları (VUK mükerrer m.28, m.17) ve mücbir sebep (m.15). `tr/vuk` her sonuçta bunun için not ekler.
- İİK m.51–54 talikleri.
- Arabuluculuk ve tüketici hakem heyeti süreleri.
