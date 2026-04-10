# uyku_dedektoru

# 😴 Uyku Dedektörü — Drowsiness Detection System

Bir süre önce sosyal medyada kayan bir videoda, birinin bilgisayar kamerasına bağlanarak uyku tespiti yapan küçük bir proje yaptığını gördüm. Videoyu kim paylaştı tam hatırlamıyorum ama fikir aklımda kaldı. Ben de görüntü işleme konusunda hiçbir deneyimim olmadan Claude Code kullanarak bu projeyi sıfırdan yazmaya karar verdim.

Bilgisayar kamerası aracılığıyla gerçek zamanlı göz takibi yaparak uyku belirtilerini tespit eden ve YouTube üzerinden alarm veren bir Python uygulaması. 

---

## 🧠 Nasıl Çalışır?

### EAR (Eye Aspect Ratio) Algoritması

Sistem, gözün açıklığını ölçmek için **EAR (Göz En-Boy Oranı)** algoritmasını kullanır. Her göz için MediaPipe tarafından tespit edilen 6 anahtar nokta kullanılarak şu formül uygulanır:

```
EAR = (‖p2−p6‖ + ‖p3−p5‖) / (2 × ‖p1−p4‖)
```

- Göz **açıkken** EAR ≈ 0.25–0.35
- Göz **kapanırken** EAR ≈ 0.15'in altına düşer
- İki gözün EAR ortalaması alınarak kararlılık artırılır

### Baş Eğikliği Düzeltmesi

Klavye kullanımı gibi durumlarda kafa öne eğildiğinde gözler açık olsa bile EAR düşebilir. Bu sorunu çözmek için sistem, MediaPipe'ın **burun ucu** ve **alın merkezi** noktalarını kullanarak kafanın dikey eğimini hesaplar ve EAR eşiğini dinamik olarak ayarlar:

- Kafa **dik** duruyorsa → normal eşik (0.18)
- Kafa **öne eğikse** → eşik otomatik düşürülür (0.13–0.15)

### Kare Bazlı Sayaç

Anlık EAR dalgalanmalarından kaynaklanan yanlış alarmları önlemek için sistem **kare sayacı** kullanır. Göz yalnızca tek bir karedeyse kapalı sayılmaz; belirlenen kare sayısı (varsayılan: 20 kare) boyunca sürekli kapalı kalması gerekir.

### Alarm Mekanizması

```
Kamera görüntüsü
       ↓
MediaPipe ile 468 yüz noktası tespiti
       ↓
Sol + Sağ göz EAR hesapla → Ortalama al
       ↓
Baş eğikliğine göre dinamik eşik belirle
       ↓
EAR < Eşik mi? → Kare sayacını artır
       ↓
20 kare boyunca kapalı mı? → Zamanlayıcı başlat
       ↓
4 saniye geçti mi? → YouTube alarmı aç!
```

---

## 🛠️ Kullanılan Teknolojiler

| Kütüphane | Sürüm | Kullanım Amacı |
|---|---|---|
| Python | 3.8+ | Ana programlama dili |
| OpenCV (`opencv-python`) | 4.x | Kamera erişimi, görüntü işleme, ekran çıktısı |
| MediaPipe | 0.10.9 | Yüz mesh tespiti (468 nokta), göz landmark'ları |
| SciPy | 1.x | Euclidean mesafe hesabı (EAR formülü) |
| webbrowser | Standart kütüphane | YouTube'u varsayılan tarayıcıda açma |

> ⚠️ MediaPipe sürümü önemlidir. **0.10.9** kullanmanız önerilir. Daha yeni sürümlerde `mp.solutions` API'si kaldırılmıştır.

---

## 📦 Kurulum

### Gereksinimler

- Python 3.8 veya üzeri
- Çalışan bir webcam
- İnternet bağlantısı (YouTube alarmı için)

### Adım Adım

**1. Repoyu klonla:**
```bash
git clone https://github.com/kullanici-adi/uyku-dedektoru.git
cd uyku-dedektoru
```

**2. Gerekli kütüphaneleri kur:**
```bash
pip install opencv-python mediapipe==0.10.9 scipy
```

**3. Çalıştır:**
```bash
python uyku_dedektoru.py
```

---

## ⚙️ Ayarlar

`uyku_dedektoru.py` dosyasının üstündeki **AYARLAR** bölümünden tüm parametreler kolayca değiştirilebilir:

```python
EAR_ESIK     = 0.18   # Göz kapalılık eşiği — düşürürseniz daha az hassas olur
KARE_ESIK    = 20     # Kaç kare boyunca kapalı kalırsa uyku sayılsın
UYKU_SURE    = 4.0    # Alarmdan kaç saniye önce beklenir
KAMERA_BEKLE = 10     # Kamera açılmazsa kaç saniye beklenir
YOUTUBE_URL  = "..."  # Alarm olarak açılacak YouTube videosu
```

### EAR Eşiği Kalibrasyonu

Her yüz ve ışık koşulu farklıdır. Programı çalıştırınca ekranda **EAR** değerini canlı görebilirsiniz:

- Gözleriniz açıkken EAR değerinizi not edin
- Gözlerinizi kapatınca düşen değeri not edin
- `EAR_ESIK` değerini bu iki değerin ortasına ayarlayın

---

## 🖥️ Ekran Görüntüsü Açıklaması

Çalışırken kamera penceresinde şunlar görünür:

- **Yeşil yazı** → Göz açık, normal durum
- **Turuncu yazı** → Şüpheli (göz yarı kapalı)
- **Mavi yazı** → Göz kapalı, sayaç çalışıyor
- **Kırmızı "UYAN!"** → Alarm tetiklendi

---

## ❗ Bilinen Sınırlılıklar

- Düşük ışık koşullarında yüz tespiti zorlaşabilir
- Gözlük kullananlar için EAR eşiğinin manuel kalibrasyonu gerekebilir
- Çok hızlı baş hareketlerinde kısa süreli yanlış alarm olabilir
- YouTube alarmı için internet bağlantısı gereklidir

---

## 🤝 Katkıda Bulunma

Pull request ve issue açmaya hoş geldiniz! Özellikle şu konularda katkı bekliyoruz:

- Farklı ışık koşullarında EAR kalibrasyonu
- Ses alarmı alternatifi (internet gerektirmeyen)
- GUI arayüzü eklenmesi

---

## 💡 İlham

Bu projeyi yapmamı sağlayan sosyal medyada gördüğüm bir videoydu. Kim paylaştığını hatırlamıyorum ama o video olmasaydı böyle bir şey denemezdim. Fikri ilk atan kim idiyse, teşekkürler. 🙏

Kodu sıfırdan yazdım, görüntü işleme konusunda önceden hiçbir bilgim yoktu. Bu yüzden bu repo aynı zamanda "hiç bilmediğin bir alanda vibe coding ile ne kadar ileri gidebilirsin?" sorusunun da cevabı.
