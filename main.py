import os
import asyncio
import random
import string
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
import json

# -------------------------
# AYARLAR
# -------------------------
API_ID = 30647156
API_HASH = "11d0174f807a8974a955520b8c968b4d"
BOT_TOKEN = "8525996238:AAHTU2kLioYCPkwk-2QliVnQRzWcZ8jxzto"  # @BotFather'dan aldığın token
ADMIN_ID = 8102629232  # SENİN TELEGRAM ID'N (@userinfobot'tan öğren)

VIP_FILE = "vip_users.json"
vip_users = {}

# -------------------------
# VIP SİSTEMİ
# -------------------------
def load_vip():
    global vip_users
    try:
        if os.path.exists(VIP_FILE):
            with open(VIP_FILE, 'r', encoding='utf-8') as f:
                vip_users = json.load(f)
                print(f"📂 VIP dosyası yüklendi: {len(vip_users)} kayıt")
        else:
            vip_users = {}
            print("📂 Yeni VIP dosyası oluşturulacak")
    except Exception as e:
        print(f"⚠️ VIP dosyası yüklenemedi: {e}")
        vip_users = {}

def save_vip():
    try:
        with open(VIP_FILE, 'w', encoding='utf-8') as f:
            json.dump(vip_users, f, indent=2, ensure_ascii=False)
        print(f"💾 VIP dosyası kaydedildi: {len(vip_users)} kayıt")
    except Exception as e:
        print(f"⚠️ VIP dosyası kaydedilemedi: {e}")

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def create_vip():
    code = gen_code()
    vip_users[code] = {
        "active": False,
        "user_id": None,
        "transfer_limit": 7000,
        "used": 0,
        "created": datetime.now().isoformat()
    }
    save_vip()
    print(f"🔑 Yeni VIP kodu oluşturuldu: {code}")
    return code

def activate_vip(user_id, code):
    code = code.upper().strip()
    print(f"🔍 VIP aktivasyon denemesi - User: {user_id}, Code: {code}")
    
    if code not in vip_users:
        print(f"❌ Kod bulunamadı: {code}")
        print(f"📋 Mevcut kodlar: {list(vip_users.keys())}")
        return False, "❌ Geçersiz kod!"
    
    if vip_users[code]["active"]:
        print(f"⚠️ Kod zaten kullanılmış: {code}")
        return False, "❌ Bu kod daha önce kullanılmış!"
    
    vip_users[code]["active"] = True
    vip_users[code]["user_id"] = user_id
    vip_users[code]["activated_at"] = datetime.now().isoformat()
    save_vip()
    
    print(f"✅ VIP aktif edildi - User: {user_id}, Code: {code}")
    return True, f"✅ VIP Aktif Edildi!\n\n⚡ 7000 mesaj transfer hakkınız tanımlandı!"

def check_vip(user_id):
    print(f"🔍 VIP kontrolü - User: {user_id}")
    
    for code, data in vip_users.items():
        if data.get("user_id") == user_id and data.get("active"):
            remaining = data["transfer_limit"] - data["used"]
            print(f"✅ VIP bulundu - Kalan: {remaining}")
            return True, remaining
    
    print(f"❌ VIP bulunamadı")
    return False, 0

def use_quota(user_id, count):
    for code, data in vip_users.items():
        if data.get("user_id") == user_id and data.get("active"):
            data["used"] += count
            save_vip()
            print(f"📊 Kota kullanıldı - User: {user_id}, Kullanılan: {count}")
            return True
    return False

def is_admin(user_id):
    """Admin kontrolü"""
    return user_id == ADMIN_ID

# -------------------------
# BOT BAŞLAT
# -------------------------
load_vip()
bot = TelegramClient('turbo_bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

print("="*50)
print("✅ BOT AKTİF!")
print(f"👑 Admin ID: {ADMIN_ID}")
print(f"📊 Kayıtlı VIP Sayısı: {len(vip_users)}")
print("="*50)

# -------------------------
# ULTRA HIZLI TRANSFER
# -------------------------
async def turbo_transfer(client, source, target, limit, progress_callback):
    """
    Gizli iletim kapalı kanallarda bile çalışan turbo transfer
    """
    try:
        source_entity = await client.get_entity(source)
        target_entity = await client.get_entity(target)
    except Exception as e:
        return {"error": f"Kanal bulunamadı: {str(e)}"}
    
    success = 0
    failed = 0
    batch_size = 100
    
    try:
        # Mesajları topla
        all_messages = []
        async for msg in client.iter_messages(source_entity, limit=limit):
            if msg.media or msg.text:
                all_messages.append(msg)
        
        total = len(all_messages)
        await progress_callback(f"📥 {total} mesaj bulundu! Transfer başlıyor...", 0, total)
        
        # Toplu forward (en hızlı yöntem)
        for i in range(0, len(all_messages), batch_size):
            batch = all_messages[i:i+batch_size]
            msg_ids = [m.id for m in batch]
            
            try:
                # Toplu forward dene
                await client.forward_messages(target_entity, msg_ids, source_entity)
                success += len(batch)
                await progress_callback(None, success, total)
                await asyncio.sleep(1)
                
            except Exception:
                # Forward başarısız, tek tek kopyala
                for msg in batch:
                    try:
                        if msg.media:
                            # Medyayı caption olmadan gönder
                            await client.send_file(target_entity, msg.media, caption=None)
                        elif msg.text:
                            await client.send_message(target_entity, msg.text)
                        
                        success += 1
                        await progress_callback(None, success, total)
                        
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 2)
                    except Exception:
                        failed += 1
                        continue
        
        return {"success": success, "failed": failed, "total": total}
        
    except Exception as e:
        return {"error": str(e)}

# -------------------------
# KOMUTLAR
# -------------------------
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    user_id = event.sender_id
    is_vip, remaining = check_vip(user_id)
    admin = is_admin(user_id)
    
    msg = "⚡ **TURBO TRANSFER BOT**\n\n"
    
    if admin:
        msg += "👑 **ADMIN PANELİ**\n"
        msg += "/olustur - VIP kodu oluştur\n"
        msg += "/viplist - VIP listesini göster\n\n"
    
    msg += "🚀 7000 mesaj hızlı transfer!\n\n"
    msg += "**Komutlar:**\n"
    msg += "/activate [kod] - VIP aktif et\n"
    msg += "/transfer - Transfer başlat\n"
    msg += "/hak - Kalan hakkını gör\n\n"
    
    if is_vip:
        msg += f"💎 **Durumunuz:** VIP Aktif\n"
        msg += f"⚡ **Kalan Hak:** {remaining} mesaj"
    else:
        msg += "❌ VIP üyeliğiniz yok"
    
    await event.respond(msg)

@bot.on(events.NewMessage(pattern='/olustur'))
async def create(event):
    if not is_admin(event.sender_id):
        await event.respond("❌ Bu komutu sadece admin kullanabilir!")
        return
    
    code = create_vip()
    await event.respond(
        f"✅ **Yeni VIP Kodu Oluşturuldu!**\n\n"
        f"🔑 Kod: `{code}`\n\n"
        f"⚡ 7000 mesaj transfer hakkı\n"
        f"📌 Kullanım: `/activate {code}`"
    )

@bot.on(events.NewMessage(pattern='/viplist'))
async def viplist(event):
    if not is_admin(event.sender_id):
        await event.respond("❌ Bu komutu sadece admin kullanabilir!")
        return
    
    if not vip_users:
        await event.respond("📋 Henüz VIP kullanıcı yok!")
        return
    
    msg = "📋 **VIP LİSTESİ**\n\n"
    for code, data in vip_users.items():
        status = "✅ Aktif" if data["active"] else "⏳ Beklemede"
        user = data.get("user_id", "Yok")
        used = data.get("used", 0)
        limit = data.get("transfer_limit", 7000)
        msg += f"🔑 `{code}`\n"
        msg += f"   {status} | User: {user}\n"
        msg += f"   Kullanım: {used}/{limit}\n\n"
    
    await event.respond(msg)

@bot.on(events.NewMessage(pattern='/activate'))
async def activate(event):
    try:
        parts = event.text.split(maxsplit=1)
        if len(parts) < 2:
            await event.respond("❌ Kullanım: /activate KOD\n\nÖrnek: /activate ABC123XYZ")
            return
        
        code = parts[1].upper().strip()
    except Exception as e:
        await event.respond(f"❌ Hata: {e}\n\nKullanım: /activate KOD")
        return
    
    success, msg = activate_vip(event.sender_id, code)
    await event.respond(msg)

@bot.on(events.NewMessage(pattern='/hak'))
async def check(event):
    has_vip, remaining = check_vip(event.sender_id)
    
    if not has_vip:
        await event.respond(
            "❌ **VIP Üyeliğiniz Yok!**\n\n"
            "VIP almak için:\n"
            "1. Admin'den kod alın\n"
            "2. /activate KOD yazın"
        )
        return
    
    await event.respond(
        f"💎 **VIP DURUMUNUZ**\n\n"
        f"⚡ Kalan Hak: **{remaining}** mesaj\n"
        f"🚀 Transfer Limiti: 7000/işlem\n\n"
        f"Transfer için: /transfer"
    )

@bot.on(events.NewMessage(pattern='/transfer'))
async def transfer(event):
    has_vip, remaining = check_vip(event.sender_id)
    
    if not has_vip:
        await event.respond(
            "❌ **VIP Gerekli!**\n\n"
            "Transfer yapmak için VIP üyeliğiniz olmalı.\n"
            "VIP kodu için admin ile iletişime geçin."
        )
        return
    
    await event.respond(
        f"🚀 **TURBO TRANSFER**\n\n"
        f"💎 Kalan Hakkınız: {remaining} mesaj\n\n"
        f"📝 **Bilgileri sırayla gönderin:**\n\n"
        f"1️⃣ Session String\n"
        f"2️⃣ Kaynak Kanal (@username veya ID)\n"
        f"3️⃣ Hedef Kanal (@username veya ID)\n"
        f"4️⃣ Mesaj Sayısı (Max: 7000)\n\n"
        f"⏱️ Her adım için 60 saniye süreniz var!"
    )
    
    user_id = event.sender_id
    
    try:
        # Session
        session_event = await bot.wait_for(events.NewMessage(from_users=user_id), timeout=60)
        session = session_event.text.strip()
        await session_event.respond("✅ Session alındı!")
        
        # Kaynak
        source_event = await bot.wait_for(events.NewMessage(from_users=user_id), timeout=60)
        source = source_event.text.strip()
        await source_event.respond("✅ Kaynak kanal alındı!")
        
        # Hedef
        target_event = await bot.wait_for(events.NewMessage(from_users=user_id), timeout=60)
        target = target_event.text.strip()
        await target_event.respond("✅ Hedef kanal alındı!")
        
        # Limit
        limit_event = await bot.wait_for(events.NewMessage(from_users=user_id), timeout=60)
        limit = int(limit_event.text.strip())
        
        if limit > 7000:
            limit = 7000
            await limit_event.respond("⚠️ Limit 7000'e çekildi.")
        else:
            await limit_event.respond(f"✅ Limit: {limit} mesaj")
        
        if limit > remaining:
            await event.respond(f"❌ Hakkınız yetersiz!\n\nİstenen: {limit}\nMevcut: {remaining}")
            return
            
    except asyncio.TimeoutError:
        await event.respond("⏱️ Zaman aşımı! İşlem iptal edildi.")
        return
    except ValueError:
        await event.respond("❌ Mesaj sayısı sayı olmalı! (Örn: 500)")
        return
    except Exception as e:
        await event.respond(f"❌ Hata: {e}")
        return
    
    # Transfer başlat
    status = await event.respond("🔄 **Bağlanılıyor...**")
    
    try:
        client = TelegramClient(StringSession(session), API_ID, API_HASH)
        await client.start()
        
        await status.edit("✅ **Hesaba giriş yapıldı!**\n\n🔍 Kanallar kontrol ediliyor...")
        
        # Progress callback
        last_update = 0
        async def update_progress(text, current, total):
            nonlocal last_update
            if text:
                await status.edit(text)
            elif current - last_update >= 50 or current == total:
                percent = int((current / total) * 100)
                await status.edit(
                    f"⚡ **Transfer Devam Ediyor**\n\n"
                    f"📊 {current}/{total} ({percent}%)\n"
                    f"✅ Başarılı transfer"
                )
                last_update = current
        
        # Transfer yap
        result = await turbo_transfer(client, source, target, limit, update_progress)
        
        if "error" in result:
            await status.edit(f"❌ **Transfer Hatası**\n\n{result['error']}")
        else:
            # Kotayı güncelle
            use_quota(user_id, result["success"])
            new_remaining = remaining - result["success"]
            
            await status.edit(
                f"🏁 **TRANSFER TAMAMLANDI!**\n\n"
                f"✅ Başarılı: **{result['success']}**\n"
                f"❌ Başarısız: **{result['failed']}**\n"
                f"📊 Toplam: **{result['total']}**\n\n"
                f"💎 Kalan Hakkınız: **{new_remaining}** mesaj"
            )
        
        await client.disconnect()
        
    except Exception as e:
        await status.edit(f"❌ **Transfer Hatası**\n\n{str(e)}")

# -------------------------
# BOT ÇALIŞTIR
# -------------------------
print("🤖 Bot komutları dinleniyor...")
bot.run_until_disconnected()
