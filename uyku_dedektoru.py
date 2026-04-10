import cv2
import mediapipe as mp
import time
import webbrowser
from scipy.spatial import distance

# ============================================================
#  AYARLAR — ihtiyaca göre buradan değiştirin
# ============================================================
EAR_ESIK       = 0.18   # Göz kapalılık eşiği (düşük = daha katı)
KARE_ESIK      = 20     # Kaç kare boyunca kapalı kalırsa uyku sayılsın
UYKU_SURE      = 5.0    # Saniye cinsinden alarm süresi
KAMERA_BEKLE   = 10     # Kamera açılmazsa kaç saniye beklensin
YOUTUBE_URL    = "https://www.youtube.com/watch?v=3NvPuYjwSVI"

SOL_GOZ = [362, 385, 387, 263, 373, 380]
SAG_GOZ = [33,  160, 158, 133, 153, 144]
# ============================================================

def ear_hesapla(noktalar):
    A = distance.euclidean(noktalar[1], noktalar[5])
    B = distance.euclidean(noktalar[2], noktalar[4])
    C = distance.euclidean(noktalar[0], noktalar[3])
    if C == 0:
        return 0.0
    return (A + B) / (2.0 * C)
# Baş eğikliği için referans noktalar
BURUN_UCU   = 1
ALIN_MERKEZ = 10

def bas_egikligi_al(lm, genislik, yukseklik):
    """Başın dikey eğimini hesaplar. Öne eğildikçe değer artar."""
    burun = nokta_al(lm, BURUN_UCU,   genislik, yukseklik)
    alin  = nokta_al(lm, ALIN_MERKEZ, genislik, yukseklik)
    # Dikey mesafe / yatay mesafe oranı — kafa öne eğilince artar
    dikey  = burun[1] - alin[1]
    yatay  = abs(burun[0] - alin[0]) + 1e-6
    return dikey / yatay

def dinamik_esik(lm, genislik, yukseklik):
    """Kafa öne eğikse eşiği düşür, dik duruyorsa normal eşik."""
    egim = bas_egikligi_al(lm, genislik, yukseklik)
    # Egim genellikle 2-4 arası dik, 5+ öne eğik
    if egim > 5.0:
        return EAR_ESIK - 0.05   # Öne eğik: daha hoşgörülü
    elif egim > 4.0:
        return EAR_ESIK - 0.03
    else:
        return EAR_ESIK          # Dik: normal eşik
def nokta_al(landmark, indeks, genislik, yukseklik):
    n = landmark[indeks]
    return (n.x * genislik, n.y * yukseklik)

# ── Kamera aç, açılmazsa bekle ──────────────────────────────
print("Kamera baslatiliyor...")
kamera = cv2.VideoCapture(0)

kamera_baslangic = time.time()
while not kamera.isOpened():
    gecen = time.time() - kamera_baslangic
    kalan = int(KAMERA_BEKLE - gecen)
    print(f"Kamera acilmadi, bekleniyor... ({kalan}s)")
    time.sleep(1)
    kamera = cv2.VideoCapture(0)
    if gecen >= KAMERA_BEKLE:
        print("HATA: Kamera acilamadi. Lutfen kameranizin bagli ve acik oldugundan emin olun.")
        exit(1)

print("Kamera basariyla acildi.")

# ── İlk kareyi test et ──────────────────────────────────────
ret, _ = kamera.read()
if not ret:
    print("HATA: Kameradan goruntu alinamadi. Baska bir uygulama kameranizi kullaniyor olabilir.")
    kamera.release()
    exit(1)

# ── MediaPipe ───────────────────────────────────────────────
mp_face    = mp.solutions.face_mesh
face_mesh  = mp_face.FaceMesh(max_num_faces=1, refine_landmarks=True,
                               min_detection_confidence=0.7,
                               min_tracking_confidence=0.7)

# ── Durum değişkenleri ──────────────────────────────────────
goz_kapali_baslangic = None
kapali_kare_sayisi   = 0
alarm_calindi        = False

print("Sistem calisıyor. Cıkmak icin kamera penceresine tıklayıp Q veya ESC'ye basin.")

while True:
    ret, kare = kamera.read()

    # Kare alınamazsa kamera bağlantısı kopmuş demek
    if not ret:
        print("UYARI: Kamera baglantisi kesildi, yeniden baglanmaya calisiliyor...")
        kamera.release()
        time.sleep(2)
        kamera = cv2.VideoCapture(0)
        if not kamera.isOpened():
            print("HATA: Kamera yeniden baglanamaadi. Program kapatiliyor.")
            break
        continue

    kare     = cv2.flip(kare, 1)
    rgb      = cv2.cvtColor(kare, cv2.COLOR_BGR2RGB)
    sonuc    = face_mesh.process(rgb)
    y, x     = kare.shape[:2]

    if sonuc.multi_face_landmarks:
        lm = sonuc.multi_face_landmarks[0].landmark

        sol_k = [nokta_al(lm, i, x, y) for i in SOL_GOZ]
        sag_k = [nokta_al(lm, i, x, y) for i in SAG_GOZ]

        sol_ear = ear_hesapla(sol_k)
        sag_ear = ear_hesapla(sag_k)
        ear     = (sol_ear + sag_ear) / 2.0

        # ── Durum rengi: yeşil=açık, turuncu=şüpheli, kırmızı=kapalı
        if ear >= EAR_ESIK:
            renk = (0, 220, 0)
            durum = "Acik"
        elif ear >= EAR_ESIK - 0.03:
            renk = (0, 165, 255)
            durum = "Supheli"
        else:
            renk = (0, 0, 220)
            durum = "Kapali"

        cv2.putText(kare, f"EAR: {ear:.2f}  Goz: {durum}", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, renk, 2)

        # ── Kapalı göz sayacı (kare bazlı — aşağı bakma sorununu çözer)
        esik = dinamik_esik(lm, x, y)
        if ear < esik:
            kapali_kare_sayisi += 1
        else:
            kapali_kare_sayisi   = 0
            goz_kapali_baslangic = None
            alarm_calindi        = False

        # ── Yeterli kare kapalıysa zamanlayıcıyı başlat
        if kapali_kare_sayisi >= KARE_ESIK:
            if goz_kapali_baslangic is None:
                goz_kapali_baslangic = time.time()
            gecen = time.time() - goz_kapali_baslangic

            cv2.putText(kare, f"Uyku riski! {gecen:.1f}s / {UYKU_SURE}s", (10, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.65, (0, 100, 255), 2)

            if gecen >= UYKU_SURE and not alarm_calindi:
                print("ALARM: Uyku tespit edildi! YouTube aciliyor...")
                webbrowser.open(YOUTUBE_URL)
                alarm_calindi = True

            if alarm_calindi:
                cv2.putText(kare, "UYAN!", (x // 2 - 90, y // 2),
                            cv2.FONT_HERSHEY_SIMPLEX, 2.5, (0, 0, 255), 5)
    else:
        # Yüz bulunamadı
        cv2.putText(kare, "Yuz algilanamadi", (10, 30),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.65, (100, 100, 100), 2)

    cv2.imshow("Uyku Dedektoru", kare)

    key = cv2.waitKey(1) & 0xFF
    if key == ord('q') or key == 27:  # Q veya ESC
        print("Program kapatiliyor.")
        break

kamera.release()
cv2.destroyAllWindows()