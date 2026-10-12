import os
import json
from dotenv import load_dotenv
from google import genai

load_dotenv()
API_KEY = os.getenv("GEMINI_API_KEY")
DOSYA_ADI = "urunler.json"

client = genai.Client(api_key=API_KEY)


# 1. FONKSİYON: JSON Dosyasından Verileri Oku
def verileri_yukle():
    """urunler.json dosyasını okur; dosya yoksa veya bozuksa boş liste döner."""
    if not os.path.exists(DOSYA_ADI):
        return []
    try:
        with open(DOSYA_ADI, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return []


# 2. FONKSİYON: JSON Dosyasına Verileri Kaydet
def verileri_kaydet(urunler):
    """Güncel ürün listesini urunler.json dosyasına yazar."""
    try:
        with open(DOSYA_ADI, "w", encoding="utf-8") as f:
            json.dump(urunler, f, ensure_ascii=False, indent=2)
    except IOError as e:
        print(f"[HATA] Dosya kaydedilemedi: {e}")


# 3. FONKSİYON: Gemini API ile Ürün Analizi Yap
def e_ticaret_api_simulasyonu(aciklama):
    """Gemini API kullanarak ürün adı, kategori, SEO etiketleri ve satış açıklaması üretir."""
    prompt = f"""
    Aşağıdaki ürün açıklamasını analiz et ve SADECE saf bir JSON objesi döndür.
    Markdown kod blokları (```json gibi) kullanma.

    İstenen JSON formatı:
    {{
      "urun_adi": "Ürünün kısa ve net adı",
      "kategori": "Ürünün kategorisi",
      "seo_etiketleri": "etiket1, etiket2, etiket3",
      "satis_aciklamasi": "Ürünü tanıtan tam iki cümlelik etkili satış açıklaması."
    }}

    Ürün Açıklaması: {aciklama}
    """
    try:
        response = client.models.generate_content(
            model="gemini-flash-latest",
            contents=prompt
        )
        
        yanit_metni = response.text.strip()
        
        # Olası markdown işaretlerini temizle
        if yanit_metni.startswith("```json"):
            yanit_metni = yanit_metni[7:]
        elif yanit_metni.startswith("```"):
            yanit_metni = yanit_metni[3:]
            
        if yanit_metni.endswith("```"):
            yanit_metni = yanit_metni[:-3]
            
        veri = json.loads(yanit_metni.strip())
        
        # Zorunlu alan kontrolü
        zorunlu_alanlar = ["urun_adi", "kategori", "seo_etiketleri", "satis_aciklamasi"]
        for alan in zorunlu_alanlar:
            if alan not in veri:
                return None
        return veri
    except Exception as e:
        print(f"[API HATASI] Gemini yanıt veremedi: {e}")
        return None


# 4. FONKSİYON: Yeni Ürün Kodu Üret
def yeni_urun_kodu_uret(urunler):
    """URN-0001 formatında bir sonraki ürün kodunu üretir."""
    if not urunler:
        return "URN-0001"
    
    son_numaralar = []
    for u in urunler:
        kod = u.get("urun_kodu", "")
        if kod.startswith("URN-"):
            try:
                son_numaralar.append(int(kod.split("-")[1]))
            except ValueError:
                continue
                
    yeni_no = max(son_numaralar, default=0) + 1
    return f"URN-{yeni_no:04d}"


# 5. FONKSİYON: Stok Durumu Mesajı
def stok_uyarisi_ver(stok):
    """Stok durumuna göre ekrana uyarı basar."""
    if stok == 0:
        return "[UYARI] STOKTA YOK"
    elif 1 <= stok <= 4:
        return f"[UYARI] KRİTİK STOK! Yalnızca {stok} adet kaldı."
    return ""


# 6. FONKSİYON: Yeni Ürün Ekle
def yeni_urun_ekle():
    aciklama = input("Ürün açıklaması: ").strip()
    if not aciklama:
        print("[HATA] Ürün açıklaması boş bırakılamaz.")
        return

    # Fiyat alma ve doğrulama
    try:
        fiyat = float(input("Ürün fiyatı: "))
        if fiyat < 0:
            print("[HATA] Fiyat negatif olamaz.")
            return
    except ValueError:
        print("[HATA] Geçerli bir sayı giriniz.")
        return

    # Stok alma ve doğrulama
    try:
        stok = int(input("Stok miktarı: "))
        if stok < 0:
            print("[HATA] Stok miktarı negatif olamaz.")
            return
    except ValueError:
        print("[HATA] Geçerli bir tam sayı giriniz.")
        return

    print("[API] Ürün bilgileri oluşturuluyor...")
    api_sonuc = e_ticaret_api_simulasyonu(aciklama)

    if not api_sonuc:
        print("[HATA] Yapay zekâ yanıtı alınamadı veya doğrulanamadı. Kayıt iptal edildi.")
        return

    urunler = verileri_yukle()
    yeni_kod = yeni_urun_kodu_uret(urunler)

    yeni_urun = {
        "urun_kodu": yeni_kod,
        "urun_adi": api_sonuc["urun_adi"],
        "kategori": api_sonuc["kategori"],
        "seo_etiketleri": api_sonuc["seo_etiketleri"],
        "satis_aciklamasi": api_sonuc["satis_aciklamasi"],
        "fiyat": fiyat,
        "stok": stok
    }

    urunler.append(yeni_urun)
    verileri_kaydet(urunler)

    print("\n[BAŞARILI] Ürün kaydedildi.")
    print(f"Ürün Kodu : {yeni_kod}")
    print(f"Ürün Adı  : {yeni_urun['urun_adi']}")
    print(f"Kategori  : {yeni_urun['kategori']}")
    print(f"Fiyat     : {yeni_urun['fiyat']} TL")
    print(f"Stok      : {yeni_urun['stok']}")
    print(f"SEO       : {yeni_urun['seo_etiketleri']}")
    
    uyari = stok_uyarisi_ver(stok)
    if uyari:
        print(uyari)


# 7. FONKSİYON: Ürünleri Listele
def urunleri_listele():
    urunler = verileri_yukle()
    if not urunler:
        print("[BİLGİ] Kayıtlı ürün bulunmamaktadır.")
        return

    print("\n--- KAYITLI ÜRÜNLER ---")
    for u in urunler:
        stok = u.get("stok", 0)
        uyari = stok_uyarisi_ver(stok)
        uyari_metni = f" -> {uyari}" if uyari else ""
        print(f"Kod: {u.get('urun_kodu')} | Ad: {u.get('urun_adi')} | Kategori: {u.get('kategori')} | Fiyat: {u.get('fiyat')} TL | Stok: {stok}{uyari_metni}")


# 8. FONKSİYON: Ürün Ara
def urun_ara():
    terim = input("Aranacak ürün adı veya kodu: ").strip().lower()
    if not terim:
        print("[HATA] Arama terimi boş olamaz.")
        return

    urunler = verileri_yukle()
    bulunanlar = [
        u for u in urunler
        if terim in u.get("urun_adi", "").lower() or terim in u.get("urun_kodu", "").lower()
    ]

    if not bulunanlar:
        print("[SONUÇ] Eşleşen ürün bulunamadı.")
        return

    print(f"\n[SONUÇ] {len(bulunanlar)} ürün bulundu:")
    for u in bulunanlar:
        stok = u.get("stok", 0)
        uyari = stok_uyarisi_ver(stok)
        uyari_metni = f" ({uyari})" if uyari else ""
        print(f"- [{u.get('urun_kodu')}] {u.get('urun_adi')} | {u.get('fiyat')} TL | Stok: {stok}{uyari_metni}")


# 9. FONKSİYON: Stok Güncelle
def stok_guncelle():
    kod = input("Ürün kodu: ").strip().upper()
    urunler = verileri_yukle()

    urun = next((u for u in urunler if u.get("urun_kodu") == kod), None)
    if not urun:
        print(f"[HATA] '{kod}' kodlu ürün bulunamadı.")
        return

    try:
        yeni_stok = int(input("Yeni stok miktarı: "))
        if yeni_stok < 0:
            print("[HATA] Stok miktarı negatif olamaz.")
            return
    except ValueError:
        print("[HATA] Geçerli bir tam sayı giriniz.")
        return

    eski_stok = urun.get("stok", 0)
    urun["stok"] = yeni_stok
    verileri_kaydet(urunler)

    print(f"[BAŞARILI] Stok {eski_stok} -> {yeni_stok} olarak güncellendi.")
    uyari = stok_uyarisi_ver(yeni_stok)
    if uyari:
        print(uyari)


# ANA DÖNGÜ (Menü)
def main():
    while True:
        print("\n== E-TICARET YÖNETİM PANELI ==")
        print("1- Yeni Ürün Ekle")
        print("2- Ürünleri Listele")
        print("3- Ürün Ara")
        print("4- Stok Güncelle")
        print("5- Çıkış")
        
        secim = input("Seçiminiz: ").strip()

        if secim == "1":
            yeni_urun_ekle()
        elif secim == "2":
            urunleri_listele()
        elif secim == "3":
            urun_ara()
        elif secim == "4":
            stok_guncelle()
        elif secim == "5":
            print("Programdan çıkılıyor...")
            break
        else:
            print("[HATA] Geçersiz seçim! Lütfen 1-5 arasında bir değer girin.")


if __name__ == "__main__":
    main()