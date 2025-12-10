import os
import asyncio
import random
import string
from datetime import datetime
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError, ChannelPrivateError
from telethon.tl.types import InputMessagesFilterEmpty
import json

# -------------------------
# AYARLAR
# -------------------------
API_ID = 30647156
API_HASH = "11d0174f807a8974a955520b8c968b4d"
BOT_TOKEN = os.environ.get("BOT_TOKEN", "8525996238:AAHTU2kLioYCPkwk-2QliVnQRzWcZ8jxzto")
ADMIN_ID = int(os.environ.get("ADMIN_ID", "8102629232"))

VIP_FILE = "vip_users.json"
vip_users = {}
active_sessions = {}

# -------------------------
# VIP SİSTEMİ
# -------------------------
def load_vip():
    global vip_users
    if os.path.exists(VIP_FILE):
        with open(VIP_FILE, 'r') as f:
            vip_users = json.load(f)

def save_vip():
    with open(VIP_FILE, 'w') as f:
        json.dump(vip_users, f)

def gen_code():
    return ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))

def create_vip():
    code = gen_code()
    vip_users[code] = {
        "active": False,
        "user": None,
        "transfer_limit": 7000,
        "used": 0,
        "created": datetime.now().isoformat()
    }
    save_vip()
    return code

def activate_vip(uid, code):
    if code not in vip_users:
        return False, "❌ Geçersiz kod!"
    if vip_users[code]["active"]:
        return False, "❌ Kod kullanılmış!"
    vip_users[code]["active"] = True
    vip_users[code]["user"] = uid
    save_vip()
    return True, f"✅ VIP Aktif!\n\n⚡ 7000 mesaj transfer hakkı tanımlandı!"

def check_vip(uid):
    for code, data in vip_users.items():
        if data.get("user") == uid and data["active"]:
            remaining = data["transfer_limit"] - data["used"]
            return True, remaining
    return False, 0

def use_quota(uid, count):
    for code, data in vip_users.items():
        if data.get("user") == uid and data["active"]:
            data["used"] += count
            save_vip()
            return True
    return False

load_vip()
bot = TelegramClient('bot', API_ID, API_HASH).start(bot_token=BOT_TOKEN)

print("✅ Bot aktif!")

# -------------------------
# ULTRA HIZLI TRANSFER
# -------------------------
async def turbo_transfer(client, source, target, limit, progress_callback):
    """
    Gizli iletim kapalı kanallarda bile çalışan turbo transfer
    Forward önce denenir, olmazsa kopyalama yapılır
    """
    try:
        source_entity = await client.get_entity(source)
        target_entity = await client.get_entity(target)
    except Exception as e:
        return {"error": f"Kanal bulunamadı: {e}"}
    
    success = 0
    failed = 0
    batch_size = 100
    
    try:
        # Mesajları batch'ler halinde al (daha hızlı)
        all_messages = []
        async for msg in client.iter_messages(source_entity, limit=limit):
            if msg.media or msg.text:
                all_messages.append(msg)
        
        total = len(all_messages)
        await progress_callback(f"📥 {total} mesaj bulundu! Transfer başlıyor...", 0, total)
        
        # Toplu forward dene (en hızlı yöntem)
        for i in range(0, len(all_messages), batch_size):
            batch = all_messages[i:i+batch_size]
            msg_ids = [m.id for m in batch]
            
            try:
                # Toplu forward (süper hızlı)
                await client.forward_messages(target_entity, msg_ids, source_entity)
                success += len(batch)
                await progress_callback(None, success, total)
                await asyncio.sleep(1)  # Rate limit önleme
                
            except Exception as forward_error:
                # Forward başarısız, tek tek kopyala
                for msg in batch:
                    try:
                        if msg.media:
                            # Medyayı direkt kopyala (caption olmadan)
                            await client.send_file(
                                target_entity,
                                msg.media,
                                caption=None  # Caption yok!
                            )
                        elif msg.text:
                            await client.send_message(target_entity, msg.text)
                        
                        success += 1
                        await progress_callback(None, success, total)
                        
                    except FloodWaitError as e:
                        await asyncio.sleep(e.seconds + 2)
                    except Exception:
                        failed += 1
                        continue
        
        return {
            "success": success,
            "failed": failed,
            "total": total
        }
        
    except Exception as e:
        return {"error": str(e)}

# -------------------------
# KOMUTLAR
# -------------------------
@bot.on(events.NewMessage(pattern='/start'))
async def start(event):
    await event.respond(
        "⚡ **TURBO TRANSFER BOT**\n\n"
        "🚀 Gizli kanallarda bile 7000 mesaj transfer!\n"
        "💎 Medya kopyalama - caption yok!\n\n"
        "**Komutlar:**\n"
        "/activate [kod] - VIP aktif et\n"
        "/transfer - Transfer başlat\n"
        "/hak - Kalan hakkını gör\n\n"
        "⚡ **Özellikler:**\n"
        "• Toplu forward (100x hızlı)\n"
        "• Gizli kanal desteği\n"
        "• Caption otomatik kaldırma\n"
        "• 7000 mesaj/transfer"
    )

@bot.on(events.NewMessage(pattern='/olustur'))
async def create(event):
    if event.sender_id != ADMIN_ID:
        return
    code = create_vip()
    await event.respond(
        f"✅ **VIP Kod Oluşturuldu!**\n\n"
        f"🔑 `{code}`\n\n"
        f"⚡ 7000 mesaj transfer hakkı\n"
        f"📌 Kullanım: /activate {code}"
    )

@bot.on(events.NewMessage(pattern='/activate'))
async def activate(event):
    try:
        code = event.text.split()[1].upper()
    except:
        await event.respond("❌ Kullanım: /activate KOD")
        return
    
    success, msg = activate_vip(event.sender_id, code)
    await event.respond(msg)

@bot.on(events.NewMessage(pattern='/hak'))
async def check(event):
    has_vip, remaining = check_vip(event.sender_id)
    if not has_vip:
        await event.respond("❌ VIP üyeliğiniz yok!")
        return
    
    await event.respond(
        f"💎 **VIP Durumunuz**\n\n"
        f"⚡ Kalan Hak: {remaining} mesaj\n"
        f"🚀 Transfer Limiti: 7000/transfer"
    )

@bot.on(events.NewMessage(pattern='/transfer'))
async def transfer(event):
    has_vip, remaining = check_vip(event.sender_id)
    if not has_vip:
        await event.respond("❌ VIP gerekli! /activate komutuyla aktif edin.")
        return
    
    await event.respond(
        "🚀 **TURBO TRANSFER**\n\n"
        "📝 Bilgileri sırayla gönderin:\n\n"
        "1️⃣ **Session String**\n"
        "2️⃣ **Kaynak Kanal** (@username veya ID)\n"
        "3️⃣ **Hedef Kanal** (@username veya ID)\n"
        "4️⃣ **Mesaj Sayısı** (Max: 7000)\n\n"
        "⏱️ 60 saniye içinde gönderin!"
    )
    
    user_id = event.sender_id
    
    try:
        # Session al
        session_event = await bot.wait_for(
            events.NewMessage(from_users=user_id),
            timeout=60
        )
        session = session_event.text.strip()
        
        # Kaynak al
        source_event = await bot.wait_for(
            events.NewMessage(from_users=user_id),
            timeout=60
        )
        source = source_event.text.strip()
        
        # Hedef al
        target_event = await bot.wait_for(
            events.NewMessage(from_users=user_id),
            timeout=60
        )
        target = target_event.text.strip()
        
        # Limit al
        limit_event = await bot.wait_for(
            events.NewMessage(from_users=user_id),
            timeout=60
        )
        limit = int(limit_event.text.strip())
        
        if limit > 7000:
            limit = 7000
            await event.respond("⚠️ Limit 7000'e çekildi.")
        
        if limit > remaining:
            await event.respond(f"❌ Hakkınız yetersiz! Kalan: {remaining}")
            return
            
    except asyncio.TimeoutError:
        await event.respond("⏱️ Zaman aşımı!")
        return
    except:
        await event.respond("❌ Geçersiz girdi!")
        return
    
    # Transfer başlat
    status = await event.respond("🔄 Bağlanılıyor...")
    
    try:
        client = TelegramClient(StringSession(session), API_ID, API_HASH)
        await client.start()
        
        await status.edit("✅ Hesaba giriş yapıldı!")
        
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
                    f"✅ Başarılı transferler"
                )
                last_update = current
        
        # Transfer yap
        result = await turbo_transfer(client, source, target, limit, update_progress)
        
        if "error" in result:
            await status.edit(f"❌ Hata: {result['error']}")
        else:
            # Kotayı güncelle
            use_quota(user_id, result["success"])
            new_remaining = remaining - result["success"]
            
            await status.edit(
                f"🏁 **TRANSFER TAMAMLANDI!**\n\n"
                f"✅ Başarılı: {result['success']}\n"
                f"❌ Başarısız: {result['failed']}\n"
                f"📊 Toplam: {result['total']}\n\n"
                f"💎 Kalan Hak: {new_remaining} mesaj"
            )
        
        await client.disconnect()
        
    except Exception as e:
        await status.edit(f"❌ Transfer hatası: {e}")

# -------------------------
# BOT ÇALIŞTIR
# -------------------------
print("🤖 Bot çalışıyor...")
bot.run_until_disconnected()
