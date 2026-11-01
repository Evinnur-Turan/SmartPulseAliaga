# 🏭 Smart Pulse Aliağa

Aliağa tipi ağır sanayi tesisleri (rafineri, petrokimya, liman terminali) için **Streamlit** tabanlı, yönetici odaklı operasyon paneli. Sentetik veriyle tek dosyada, ek kurulum gerektirmeden çalışır.

> Tüm veriler `pandas` + `numpy` ile üretilmiş **sentetik** veridir; gerçek tesis verisini temsil etmez.

## Özellikler

- **Yönetici özeti:** Üretim hacmi, verimlilik, CO₂, aktif uyarı ve demuraj maruziyeti için trend göstergeli KPI kartları
- **Operasyon:** Günlük/haftalık üretim ve verimlilik grafikleri, ünite bazlı kartlar
- **Karbon ve ESG:** Saatlik CO₂ takibi, emisyon sınırı çizgisi, 24 saatlik gösterge, uyumluluk durumu
- **Demuraj:** Rıhtım doluluğu, işleme hızı ve günlük bedele göre maliyet tahmini; duyarlılık analizi ve tek gemi hesaplayıcısı
- **Sensör telemetrisi:** Sıcaklık, basınç ve CO₂ için normal seviye ve uyarı limiti işaretli grafikler
- **Anomali uyarıları:** Sınır dışı okumalar ve tedarik gecikmeleri için rozetler, bildirim kartları, filtreli tablo, CSV dışa aktarma
- **Sade dil özetleri:** Her grafikte teknik veriyi cümleye çeviren açıklama kutuları ve ipuçları

## Kurulum ve Çalıştırma

Python 3.9+ gerekir.

```bash
pip install streamlit pandas numpy plotly
streamlit run smart_pulse_Aliaga.py
```

Uygulama `http://localhost:8501` adresinde açılır.

## Kullanım

Kenar çubuğundan tarih aralığı, ünite, özet sıklığı, uyarı eşikleri ve liman varsayımları (rıhtım sayısı, doluluk, işleme hızı, demuraj bedeli) ayarlanır. Sayfa yukarıdan aşağıya şöyle akar: **KPI kartları → analiz sekmeleri → uyarılar ve detay tablosu**.

## Hesaplama Notları

- **CO₂ sınırı:** nominal üretim × emisyon faktörü × (1 + sınır payı). Sınır altında kalan ünite-saatlerinin oranı ≥%99 ise *Uyumlu*, %97–99 *İzlemede*, altı *Uyumsuz* sayılır.
- **Demuraj:** Rıhtım doluluğu arttıkça bekleme süresi doğrusal olmayan biçimde artan, basitleştirilmiş bir kuyruk modeli kullanılır. Planlama amaçlıdır; charter party kurallarının yerini tutmaz.

## Gerçek Veriye Bağlama

`generate_telemetry()` ve `generate_vessels()` fonksiyonlarını kendi veri kaynağınızla değiştirin ve şu sütunları koruyun:

- Telemetri: `timestamp, plant, tph, eff, temp_c, press_bar, co2_kgh`
- Gemiler: `vessel, arrival, berth, cargo, cargo_t, pump_tph, laytime_h, arrival_delay_h`

Ünite parametreleri ve limitler `PLANTS` sözlüğündedir.

## Tasarım

Sakin kurumsal tema: slate lacivert `#1E293B`, arka plan `#F8FAFC`, metin `#0F172A`; durum renkleri mat yeşil, amber ve kırmızı.
