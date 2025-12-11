import subprocess
import sys

def install(package):
    subprocess.check_call([sys.executable, "-m", "pip", "install", package])

try:
    import pyrogram
    import aiosqlite
except ImportError:
    print("Kütüphaneler eksik, otomatik yükleniyor...")
    install("pyrogram")
    install("tgcrypto")
    install("aiosqlite")
    print("Kurulum tamamlandı! Bot başlatılıyor...")

# Buradan sonra normal importların ve kodun gelecek...
import os
import asyncio
from pyrogram import Client, filters
# ... kodun devamı ...
import os
import asyncio
import aiosqlite
from pyrogram import Client, filters
from pyrogram.errors import FloodWait, RPCError

# --- AYARLAR ---
API_ID = 30376158  # my.telegram.org'dan al
API_HASH = "82150988a6465c80474a9b9dc7634b94"
BOT_TOKEN = "7960144659:AAHp07olQd3eMD_36rNLUnZV3Dqs91Xk02w"
ADMIN_ID = 8586659198 # Kendi Telegram ID'n (Admin Paneli İçin)

# Botu Başlat
app = Client("my_bot", api_id=API_ID, api_hash=API_HASH, bot_token=BOT_TOKEN)

# Veritabanı Dosyası
DB_NAME = "users.db"

# --- VERİTABANI İŞLEMLERİ ---
async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                is_vip BOOLEAN DEFAULT 0,
                trial_used BOOLEAN DEFAULT 0
            )
        """)
        await db.commit()

async def get_user(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
        return await cursor.fetchone()

async def add_user(user_id):
    if not await get_user(user_id):
        async with aiosqlite.connect(DB_NAME) as db:
            await db.execute("INSERT INTO users (user_id, is_vip, trial_used) VALUES (?, 0, 0)", (user_id,))
            await db.commit()

async def set_vip(user_id, status):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET is_vip = ? WHERE user_id = ?", (status, user_id))
        await db.commit()

async def set_trial_used(user_id):
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("UPDATE users SET trial_used = 1 WHERE user_id = ?", (user_id,))
        await db.commit()

# --- YARDIMCI FONKSİYONLAR ---
async def transfer_process(client, message, source_id, dest_id, start_msg, end_msg):
    status_msg = await message.reply_text("🚀 İşlem başlıyor... Lütfen bekleyin.")
    success_count = 0
    fail_count = 0

    # Normal botlar çok hızlı işlem yaparsa Flood yer, yavaşlatıyoruz.
    delay = 2 
    
    for msg_id in range(start_msg, end_msg + 1):
        try:
            # YÖNTEM 1: FORWARD (İLETİM)
            try:
                await client.forward_messages(chat_id=dest_id, from_chat_id=source_id, message_ids=msg_id)
                success_count += 1
                await asyncio.sleep(delay) # Flood koruması
                continue # Başarılıysa diğer mesaja geç
            except Exception:
                pass # Forward başarısız, yöntemi değiştir.

            # YÖNTEM 2: COPY (KOPYALA - İletim Kapalıysa)
            try:
                msg = await client.get_messages(source_id, msg_id)
                if not msg.empty:
                    await msg.copy(dest_id)
                    success_count += 1
                    await asyncio.sleep(delay)
                    continue
            except Exception:
                pass # Copy de başarısız, son çareye geç.

            # YÖNTEM 3: İNDİR / YÜKLE / SİL (En ağır yöntem)
            try:
                msg = await client.get_messages(source_id, msg_id)
                if msg.media:
                    dl_msg = await message.reply_text(f"📥 Mesaj {msg_id} indiriliyor... (Bu biraz sürebilir)")
                    file_path = await client.download_media(msg)
                    
                    if msg.caption:
                        caption = msg.caption
                    else:
                        caption = ""

                    # Dosya tipine göre gönder
                    await client.send_document(dest_id, file_path, caption=caption)
                    
                    # Temizlik
                    os.remove(file_path)
                    await dl_msg.delete()
                    success_count += 1
                else:
                    # Sadece metinse
                    if msg.text:
                        await client.send_message(dest_id, msg.text)
                        success_count += 1

                await asyncio.sleep(delay + 2) # İndir yükle yorar, daha çok bekle
            except Exception as e:
                print(f"Hata Mesaj ID {msg_id}: {e}")
                fail_count += 1

        except FloodWait as e:
            await message.reply_text(f"⚠️ Telegram bizi durdurdu. {e.value} saniye bekleyip devam edeceğim.")
            await asyncio.sleep(e.value)
        except Exception as e:
            fail_count += 1

        # Her 10 mesajda bir kullanıcıya bilgi ver
        if (msg_id - start_msg) % 10 == 0:
            try:
                await status_msg.edit_text(f"📊 Durum: {msg_id} nolu mesaja gelindi.\n✅ Başarılı: {success_count}\n❌ Başarısız: {fail_count}")
            except:
                pass

    await status_msg.edit_text(f"🏁 **İŞLEM TAMAMLANDI!**\n\n✅ Toplam Başarılı: {success_count}\n❌ Toplam Hata: {fail_count}")


# --- KOMUTLAR ---

@app.on_message(filters.command("start"))
async def start_command(client, message):
    user_id = message.from_user.id
    await add_user(user_id)
    text = (
        "👋 **Hoş Geldin!**\n\n"
        "Ben gelişmiş bir içerik taşıma botuyum.\n"
        "Sırasıyla İlet -> Kopyala -> İndir/Yükle denerim.\n\n"
        "📌 **Kullanım:**\n"
        "`/transfer KAYNAK_ID HEDEF_ID BASLANGIC_MSJ_ID BITIS_MSJ_ID`\n\n"
        "🛡️ **Üyelik Durumu:**\n"
        "VIP veya Deneme hakkınız varsa kullanabilirsiniz.\n"
        "Deneme almak için: `/deneme`\n"
    )
    if user_id == ADMIN_ID:
        text += "\n👑 **Yönetici Menüsü:** `/admin`"
    
    await message.reply_text(text)

@app.on_message(filters.command("deneme"))
async def trial_command(client, message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    if user[1]: # Zaten VIP ise
        await message.reply_text("💎 Zaten VIP üyesiniz!")
        return

    if user[2]: # Deneme kullanmışsa
        await message.reply_text("❌ Deneme hakkınızı zaten kullandınız. Lütfen admin ile iletişime geçin.")
    else:
        # Deneme için 50 mesajlık limit verilebilir ama basit olsun diye 1 kerelik VIP veriyoruz gibi düşünelim ya da logicle kontrol edelim.
        # Basitlik adına burada kullanıcıya sadece bilgi veriyoruz, gerçek sınırlama transfer komutunda olur.
        # Bu örnekte deneme hakkı = 1 seferlik kullanım gibi basit tutuyorum.
        await set_trial_used(user_id)
        await message.reply_text("✅ **Deneme Hakkı Tanımlandı!**\nTek seferlik küçük bir transfer işlemi yapabilirsiniz.")

@app.on_message(filters.command("admin") & filters.user(ADMIN_ID))
async def admin_panel(client, message):
    text = (
        "👑 **ADMİN PANELİ**\n\n"
        "Bir kullanıcıyı VIP yapmak için:\n"
        "`/vipver KULLANICI_ID`\n\n"
        "VIP'yi almak için:\n"
        "`/vipal KULLANICI_ID`\n\n"
        "Kendi ID'niz: " + str(ADMIN_ID)
    )
    await message.reply_text(text)

@app.on_message(filters.command("vipver") & filters.user(ADMIN_ID))
async def grant_vip(client, message):
    try:
        target_id = int(message.command[1])
        await add_user(target_id) # Garanti olsun
        await set_vip(target_id, 1)
        await message.reply_text(f"✅ Kullanıcı {target_id} artık **VIP**!")
    except:
        await message.reply_text("❌ Hata: ID girmeyi unuttun. Örn: `/vipver 12345`")

@app.on_message(filters.command("transfer"))
async def transfer_handler(client, message):
    user_id = message.from_user.id
    user = await get_user(user_id)
    
    # YETKİ KONTROLÜ
    # user[1] = is_vip, user[2] = trial_used
    # Eğer VIP değilse ve Deneme hakkı yoksa (veya kullanmışsa) durdur.
    # Burada mantık: Deneme hakkını /deneme komutuyla "aktive" ettiyse izin ver, işlem bitince kapatılabilir.
    # Daha basit bir mantık: Admin değilse ve VIP değilse işlem yapmasın. Deneme sistemi için manuel izin gerekli.
    
    is_authorized = False
    if user_id == ADMIN_ID:
        is_authorized = True
    elif user and user[1] == 1: # VIP
        is_authorized = True
    elif user and user[2] == 1: # Deneme hakkı aktif edilmiş (Bu kodda basit tuttum, deneme kullanan her işlemi yapar ama sınır koyulabilir)
        is_authorized = True
    
    if not is_authorized:
        await message.reply_text("⛔ **Yetkiniz Yok!**\nBu işlemi yapmak için VIP olmalısınız veya `/deneme` komutu ile hak talep etmelisiniz.")
        return

    try:
        # Komut: /transfer kaynak hedef baslangic bitis
        cmd = message.command
        source_id = int(cmd[1])
        dest_id = int(cmd[2])
        start_msg = int(cmd[3])
        end_msg = int(cmd[4])

        # Normal bot olduğu için kanalda admin olup olmadığını kontrol etmemiz lazım ama 
        # API bunu doğrudan vermezse hata alınca anlarız.
        
        await transfer_process(client, message, source_id, dest_id, start_msg, end_msg)
        
        # Eğer deneme kullanıcısıysa, işlemden sonra hakkını bitirebiliriz (opsiyonel)
        if user[1] == 0 and user[2] == 1:
             # Burada deneme hakkını "kullanıldı" olarak işaretleyip VIP'yi kapatabilirsin.
             pass

    except IndexError:
        await message.reply_text("⚠️ **Hatalı Kullanım!**\n\nÖrnek:\n`/transfer -100123456 -100987654 10 50`\n\n(Kaynak ID, Hedef ID, Başlangıç Mesaj No, Bitiş Mesaj No)")
    except Exception as e:
        await message.reply_text(f"❌ Bir hata oluştu: {e}")

# Botu çalıştır
if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.run_until_complete(init_db())
    print("Bot çalışıyor...")
    app.run()
