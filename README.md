# Nesine York Knicks — Yahoo → GitHub → ChatGPT

Bu paket, Yahoo Fantasy Basketball lig verilerini her sabah **08:15 Türkiye saati** GitHub Actions ile `public/fantasy-data.json` dosyasına yazar. **09:00 ChatGPT görevinin bu dosyayı okuması ayrıca test edilmelidir.** ChatGPT Tasks'ın her ortamda dış URL okuyabildiği garanti değildir.

## 1. GitHub reposu
1. GitHub'da **yeni PUBLIC repo** oluştur (`nesine-fantasy-live` gibi).
2. Bu paketin **içindeki dosyaları** repoya yükle (`.github/workflows/yahoo-daily.yml` dahil).
3. Repo > Settings > Actions > General > Workflow permissions: **Read and write permissions** seç. (Organizasyon politikası izin vermiyorsa farklı bir yöntem gerekir.)

> **Gizlilik:** PUBLIC repoda yayımlanan JSON, lig kadrolarını, takımları ve işlem geçmişini herkese açar. Yahoo tokenları GitHub Secrets içinde kalır. Gizlilik önemliyse public repo kullanma; private repo + doğrulanmış ChatGPT erişimi gerekecektir.

## 2. Yahoo uygulaması oluştur
1. Yahoo Developer Network üzerinde uygulama oluştur.
2. Fantasy Sports API için **read** yetkisi seç.
3. Redirect URI'yi tam olarak `http://localhost:8765/callback` gir. Yahoo uygulama ayarları bu URI'yi kabul etmiyorsa redirect yapılandırmasını uyarlamak gerekir; bu paketin bootstrap scripti o adresi bekler.
4. `Client ID` ve `Client Secret` değerlerini al.

## 3. İlk OAuth yetkisi — kendi bilgisayarında
Terminalde, bu klasörün içinde:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
export YAHOO_CLIENT_ID='BURAYA_CLIENT_ID'
export YAHOO_CLIENT_SECRET='BURAYA_CLIENT_SECRET'
python scripts/bootstrap_oauth.py
```

Tarayıcıda Yahoo hesabınla onay ver. Terminalde gösterilen **refresh token** değerini kopyala. Tokenı GitHub dosyalarına veya ChatGPT sohbetine yazma.

## 4. GitHub Secrets ve Variables
Repo > Settings > Secrets and variables > Actions:

**Secrets:**
- `YAHOO_CLIENT_ID`
- `YAHOO_CLIENT_SECRET`
- `YAHOO_REFRESH_TOKEN`

**Variables:**
- `YAHOO_LEAGUE_KEY` — Yahoo liginin gerçek key'i; biçim örneği `466.l.12345`. Bu bir örnektir, gerçek key'i Yahoo API/lig sayfasından öğren.

## 5. Çalıştır ve test et
1. Repo > Actions > `Yahoo Fantasy Daily Snapshot` > `Run workflow`.
2. Yeşil sonuç ve `public/fantasy-data.json` dosyasının oluştuğunu doğrula.
3. Dosyanın içindeki `updated_at_utc`, `endpoints`, `errors` ve `team_rosters` alanlarını kontrol et. `team_rosters` boşsa Yahoo yanıt yapısı nedeniyle roster ayrıştırıcısını uyarlamak gerekebilir.
4. Raw dosya adresi:

   `https://raw.githubusercontent.com/GITHUB_KULLANICI_ADIN/REPO_ADIN/main/public/fantasy-data.json`

5. ChatGPT'ye **manuel olarak** bu adresi ver ve 'Dosyanın updated_at_utc alanını ve takım sayısını oku' diye test et. Okuyabiliyorsa mevcut günlük görevin promptuna da ekle. **Manuel sohbette erişim, zamanlanmış görevde erişimi garanti etmez**; bir günlük görev çalışmasını ayrıca doğrula.

## 6. Günlük ChatGPT görevine eklenecek metin

```text
Her sabah Nesine York Knicks 14 takımlı H2H 9-cat Yahoo Fantasy raporunu üretmeden önce şu URL'deki güncel JSON'u oku:
https://raw.githubusercontent.com/GITHUB_KULLANICI_ADIN/REPO_ADIN/main/public/fantasy-data.json
JSON içindeki updated_at_utc zamanını kontrol et; veri 30 saatten eskiyse raporu eski veri uyarısıyla sun. Mevcut kadro, rakip kadroları, waiver/free-agent havuzu ve haftalık eşleşmeleri mümkün olduğunca JSON'dan belirle. İşlem geçmişi ve roster verileri eksikse uydurma. Günlük sakatlık durumlarını güvenilir güncel kaynaklarla doğrula. Rapor: 9-cat eşleşme analizi, ilk 3 waiver fırsatı, drop adayları, sakatlıklar, gerçekçi takas fikirleri. JSON'a erişemiyorsan bunu açıkça belirt; eski kadroyu güncelmiş gibi sunma.
```

## Notlar
- GitHub Actions cron işleri birkaç dakika gecikebilir. ChatGPT görevinin 09:00 çalışması için yaklaşık 45 dakika tampon var.
- Yahoo bazı uç noktalarda erişim/sınırlama hatası verebilir; `errors` alanını incele.
- API yanıtları ham JSON olarak yayımlanır. Gizlilik açısından public repo tercihinin bilincinde ol.
- Yahoo OAuth refresh token rotasyonu yaşanırsa secret güncellenmelidir; script token değerini loglamaz.
- Bu paket çalıştırılmış / Yahoo hesabına bağlanmış değildir; ilk çalıştırmada doğrulama gerekir.
