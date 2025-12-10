#!/bin/bash
python bot.py
```

### 2️⃣ Render.com'a Deploy

1. **[render.com](https://render.com)**'a git → Sign Up (GitHub ile giriş yap)

2. **New +** → **Background Worker** seç

3. **Connect Repository** → GitHub repo'nu seç

4. Ayarlar:
   - **Name:** `turbo-transfer-bot`
   - **Environment:** `Python 3`
   - **Build Command:** `pip install -r requirements.txt`
   - **Start Command:** `python bot.py`

5. **Environment Variables** ekle:
```
   BOT_TOKEN = (BotFather'dan aldığın token)
   ADMIN_ID = (Senin Telegram ID'n)
```

6. **Create Background Worker** → Deploy başlayacak!

### 3️⃣ Bot Token Al
```
@BotFather'a git:
/newbot
İsim: Turbo Transfer
Username: turbo_transfer_bot (veya başka)
```
Token'ı kopyala, Render'da BOT_TOKEN'a yapıştır.

### 4️⃣ ID'ni Öğren
```
@userinfobot'a mesaj at
ID'ni kopyala, Render'da ADMIN_ID'ye yapıştır
```

---

## ⚡ ÖZELLİKLER:

✅ **7000 mesaj transfer** (VIP başına)
✅ **Toplu forward** - 100x daha hızlı!
✅ **Gizli kanal desteği** - İletim kapalı bile olsa çalışır
✅ **Caption otomatik kaldırma** - Temiz transfer
✅ **Batch processing** - 100'lük gruplarda transfer
✅ **FloodWait koruması** - Otomatik bekler
✅ **Progress bar** - Canlı ilerleme takibi

## 🎯 KULLANIM:

**Sen (Admin):**
```
/olustur → VIP kodu oluştur
```

**VIP Kullananlar:**
```
/activate ABC123XYZ → Kodu aktif et
/transfer → Transfer başlat
/hak → Kalan mesaj hakkını gör
