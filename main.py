from telethon import TelegramClient, events
from telethon.tl.functions.messages import GetHistoryRequest
from telethon.tl.types import InputPeerChannel, MessageMediaPhoto, MessageMediaDocument
from telethon.sessions import StringSession
from telethon.errors import FloodWaitError
import asyncio
import os
from datetime import datetime

# Yapılandırma - Ortam değişkenlerinden al
api_id = int(os.environ.get('36435345', '0'))
api_hash = os.environ.get('28cfcf7036020a54feadb2d8b29d94d0', '')

# Userbot modu - kendi hesabınızla giriş yapın
# İlk çalıştırmada telefon numarası ve doğrulama kodu istenecek
SESSION_NAME = 'userbot_session'

# Telegram Client oluştur (userbot olarak)
client = TelegramClient(SESSION_NAME, api_id, api_hash)

# Bot komutlarını dinleyecek kullanıcı ID'leri (güvenlik için)
# Kendi Telegram ID'nizi buraya ekleyin
ALLOWED_USERS = [8102629232] 


def is_authorized(user_id):
    """Kullanıcı yetkisi kontrolü"""
    return len(ALLOWED_USERS) == 0 or user_id in ALLOWED_USERS


@client.on(events.NewMessage(pattern='/start'))
async def start(event):
    """Bot başlatma komutu"""
    if not is_authorized(event.sender_id):
        await event.respond("❌ Bu botu kullanma yetkiniz yok!")
        return

    help_text = """
🤖 **Telegram Userbot'a Hoş Geldiniz!**

⚡ **Bu bir USERBOT'tur** - Kendi hesabınızla çalışır, tüm kanallara erişebilir!

📋 **Kullanılabilir Komutlar:**

📝 **Metin Kopyalama:**
`/copy [mesaj_linki]` - Kopyalama korumalı metni alır
`/forward [mesaj_linki]` - İletim kapalı mesajı alır

📥 **Medya İndirme:**
`/getmedia [mesaj_linki]` - İletim kapalı gruptan medya indirir
`/getphoto [mesaj_linki]` - Fotoğraf indirir
`/getvideo [mesaj_linki]` - Video indirir
`/getdoc [mesaj_linki]` - Doküman indirir

📊 **Toplu İşlemler:**
`/getall [kanal/grup_linki] [adet]` - Son N mesajı alır (max 100)
`/getallmedia [kanal/grup_linki] [adet]` - Son N medyayı indirir

🔄 **Transfer İşlemi:**
`/transfer [kaynak] [hedef] [adet]` - Kaynak kanaldan hedef gruba foto/video aktarır (max 200)

ℹ️ **Not:** Komutları kendinize (Saved Messages) veya herhangi bir sohbete yazabilirsiniz.
Örnek link: `https://t.me/kanal_adi/12345`
"""
    await event.respond(help_text)


async def get_message_from_link(link):
    """Mesaj linkinden mesaj objesini alır"""
    try:
        # Link temizle
        link = link.strip()

        # ? işaretinden sonrasını temizle (örn: ?single gibi parametreler)
        if '?' in link:
            link = link.split('?')[0]

        # Link formatı: https://t.me/username/message_id veya https://t.me/c/channel_id/message_id
        parts = link.rstrip('/').split('/')

        # Mesaj ID'sini al
        message_id = int(parts[-1])

        if 't.me/c/' in link:
            # Özel kanal/grup (örn: https://t.me/c/1234567890/123)
            channel_id = int(parts[-2])
            entity = await client.get_entity(int(f'-100{channel_id}'))
        else:
            # Public kanal/grup (örn: https://t.me/kanaladi/123)
            username = parts[-2]
            if username.startswith('@'):
                username = username[1:]
            entity = await client.get_entity(username)

        # Mesajı al
        message = await client.get_messages(entity, ids=message_id)

        if message is None:
            print(f"Mesaj bulunamadı: {link}")
            return None

        return message
    except FloodWaitError as e:
        print(f"⏳ Rate limit! {e.seconds} saniye bekleniyor...")
        await asyncio.sleep(e.seconds + 5)
        return await get_message_from_link(link)
    except ValueError as e:
        print(f"Link format hatası: {e}")
        return None
    except Exception as e:
        print(f"Mesaj alma hatası: {e}")
        return None


@client.on(events.NewMessage(pattern='/copy'))
async def copy_protected_text(event):
    """Kopyalama korumalı metni kopyalar"""
    if not is_authorized(event.sender_id):
        await event.respond("❌ Yetkiniz yok!")
        return

    try:
        args = event.message.text.split(' ', 1)
        if len(args) < 2:
            await event.respond("❌ Kullanım: /copy [mesaj_linki]")
            return

        link = args[1]
        msg = await get_message_from_link(link)

        if msg and msg.text:
            await event.respond(f"📄 **Kopyalanan Metin:**\n\n{msg.text}")
        else:
            await event.respond("❌ Metin bulunamadı!")
    except Exception as e:
        await event.respond(f"❌ Hata: {str(e)}")


@client.on(events.NewMessage(pattern='/forward'))
async def forward_protected_message(event):
    """İletim kapalı mesajı alır"""
    if not is_authorized(event.sender_id):
        await event.respond("❌ Yetkiniz yok!")
        return

    try:
        args = event.message.text.split(' ', 1)
        if len(args) < 2:
            await event.respond("❌ Kullanım: /forward [mesaj_linki]")
            return

        link = args[1]
        msg = await get_message_from_link(link)

        if msg:
            content = f"📩 **İletilen Mesaj:**\n\n"
            if msg.text:
                content += msg.text

            await event.respond(content)

            # Medya varsa onu da gönder
            if msg.media:
                await client.send_file(event.chat_id, msg.media)
        else:
            await event.respond("❌ Mesaj bulunamadı!")
    except Exception as e:
        await event.respond(f"❌ Hata: {str(e)}")


@client.on(events.NewMessage(pattern='/getmedia'))
async def get_protected_media(event):
    """İletim kapalı medyayı indirir"""
    if not is_authorized(event.sender_id):
        await event.respond("❌ Yetkiniz yok!")
        return

    try:
        args = event.message.text.split(' ', 1)
        if len(args) < 2:
            await event.respond("❌ Kullanım: /getmedia [mesaj_linki]")
            return

        link = args[1].strip()
        status_msg = await event.respond("⏳ Mesaj alınıyor...")

        msg = await get_message_from_link(link)

        if msg is None:
            await status_msg.edit(
                "❌ Mesaj bulunamadı! Bot'un kanala/gruba üye olduğundan emin olun."
            )
            return

        if not hasattr(msg, 'media') or msg.media is None:
            await status_msg.edit("❌ Bu mesajda medya yok!")
            return

        await status_msg.edit("⏳ Medya indiriliyor...")

        # Medyayı indir ve gönder
        file_path = await client.download_media(msg.media)

        if file_path is None:
            await status_msg.edit("❌ Medya indirilemedi!")
            return

        await client.send_file(event.chat_id,
                               file_path,
                               caption="✅ Medya başarıyla alındı!")
        await status_msg.delete()

        # İndirilen dosyayı sil
        if os.path.exists(file_path):
            os.remove(file_path)
    except Exception as e:
        await event.respond(f"❌ Hata: {str(e)}")


@client.on(events.NewMessage(pattern='/getphoto'))
async def get_photo(event):
    """Fotoğraf indirir"""
    if not is_authorized(event.sender_id):
        return

    try:
        args = event.message.text.split(' ', 1)
        if len(args) < 2:
            await event.respond("❌ Kullanım: /getphoto [mesaj_linki]")
            return

        link = args[1]
        msg = await get_message_from_link(link)

        if msg and isinstance(msg.media, MessageMediaPhoto):
            await event.respond("📸 Fotoğraf indiriliyor...")
            file_path = await client.download_media(msg.media)
            await client.send_file(event.chat_id, file_path)
            if os.path.exists(file_path):
                os.remove(file_path)
        else:
            await event.respond("❌ Fotoğraf bulunamadı!")
    except Exception as e:
        await event.respond(f"❌ Hata: {str(e)}")


@client.on(events.NewMessage(pattern='/getvideo'))
async def get_video(event):
    """Video indirir"""
    if not is_authorized(event.sender_id):
        return

    try:
        args = event.message.text.split(' ', 1)
        if len(args) < 2:
            await event.respond("❌ Kullanım: /getvideo [mesaj_linki]")
            return

        link = args[1]
        msg = await get_message_from_link(link)

        if msg and isinstance(msg.media, MessageMediaDocument):
            if msg.media.document.mime_type.startswith('video/'):
                await event.respond("🎥 Video indiriliyor...")
                file_path = await client.download_media(msg.media)
                await client.send_file(event.chat_id, file_path)
                if os.path.exists(file_path):
                    os.remove(file_path)
            else:
                await event.respond("❌ Bu bir video değil!")
        else:
            await event.respond("❌ Video bulunamadı!")
    except Exception as e:
        await event.respond(f"❌ Hata: {str(e)}")


@client.on(events.NewMessage(pattern='/getall'))
async def get_all_messages(event):
    """Belirli sayıda mesaj alır"""
    if not is_authorized(event.sender_id):
        return

    try:
        args = event.message.text.split()
        if len(args) < 3:
            await event.respond("❌ Kullanım: /getall [kanal_linki] [adet]")
            return

        channel_link = args[1]
        limit = min(int(args[2]), 100)

        # Kanal entitysini al
        if 't.me/' in channel_link:
            username = channel_link.split('/')[-1]
            entity = await client.get_entity(username)
        else:
            entity = await client.get_entity(channel_link)

        await event.respond(f"⏳ Son {limit} mesaj alınıyor...")

        messages = await client.get_messages(entity, limit=limit)

        # Mesajları gönder
        for msg in reversed(messages):
            if msg.text:
                await event.respond(
                    f"📝 **Mesaj ID: {msg.id}**\n\n{msg.text[:4000]}")
                await asyncio.sleep(1)  # Rate limit için

        await event.respond(f"✅ Toplam {len(messages)} mesaj alındı!")
    except Exception as e:
        await event.respond(f"❌ Hata: {str(e)}")


@client.on(events.NewMessage(pattern='/getallmedia'))
async def get_all_media(event):
    """Belirli sayıda medya indirir"""
    if not is_authorized(event.sender_id):
        return

    try:
        args = event.message.text.split()
        if len(args) < 3:
            await event.respond("❌ Kullanım: /getallmedia [kanal_linki] [adet]"
                                )
            return

        channel_link = args[1]
        limit = min(int(args[2]), 50)

        if 't.me/' in channel_link:
            username = channel_link.split('/')[-1]
            entity = await client.get_entity(username)
        else:
            entity = await client.get_entity(channel_link)

        await event.respond(f"⏳ Son {limit} medya indiriliyor...")

        messages = await client.get_messages(entity, limit=limit)
        media_count = 0

        for msg in reversed(messages):
            if msg.media:
                try:
                    file_path = await client.download_media(msg.media)
                    if file_path:
                        await client.send_file(event.chat_id,
                                               file_path,
                                               caption=f"Mesaj ID: {msg.id}")
                        if os.path.exists(file_path):
                            os.remove(file_path)
                        media_count += 1
                    await asyncio.sleep(2)
                except Exception as e:
                    print(f"Medya indirme hatası: {e}")
                    continue

        await event.respond(f"✅ Toplam {media_count} medya indirildi!")
    except Exception as e:
        await event.respond(f"❌ Hata: {str(e)}")


@client.on(events.NewMessage(pattern='/transfer'))
async def transfer_media_to_group(event):
    """Kaynak kanaldan hedef gruba tüm medyaları (foto/video) aktarır"""
    if not is_authorized(event.sender_id):
        await event.respond("❌ Yetkiniz yok!")
        return

    try:
        args = event.message.text.split()
        if len(args) < 4:
            await event.respond(
                "❌ **Kullanım:** `/transfer [kaynak_link] [hedef_link] [adet]`\n\n"
                "**Örnek:**\n"
                "`/transfer https://t.me/kaynakkanal https://t.me/hedefgrup 50`\n\n"
                "**Not:** Sadece fotoğraf ve videolar aktarılır, mesajlar aktarılmaz."
            )
            return

        source_link = args[1].strip()
        target_link = args[2].strip()
        limit = min(int(args[3]), 200)  # Maximum 200 medya

        status_msg = await event.respond(
            f"⏳ Transfer başlatılıyor...\n\n📤 Kaynak: {source_link}\n📥 Hedef: {target_link}\n📊 Adet: {limit}"
        )

        # Kaynak entity'sini al
        if 't.me/c/' in source_link:
            parts = source_link.rstrip('/').split('/')
            channel_id = int(parts[-1])
            source_entity = await client.get_entity(int(f'-100{channel_id}'))
        elif 't.me/' in source_link:
            username = source_link.rstrip('/').split('/')[-1]
            if username.startswith('@'):
                username = username[1:]
            source_entity = await client.get_entity(username)
        else:
            source_entity = await client.get_entity(source_link)

        # Hedef entity'sini al
        if 't.me/c/' in target_link:
            parts = target_link.rstrip('/').split('/')
            channel_id = int(parts[-1])
            target_entity = await client.get_entity(int(f'-100{channel_id}'))
        elif 't.me/' in target_link:
            username = target_link.rstrip('/').split('/')[-1]
            if username.startswith('@'):
                username = username[1:]
            target_entity = await client.get_entity(username)
        else:
            target_entity = await client.get_entity(target_link)

        await status_msg.edit(f"⏳ Kaynak kanaldan {limit} mesaj alınıyor...")

        # Mesajları al
        messages = await client.get_messages(source_entity, limit=limit)

        photo_count = 0
        video_count = 0
        error_count = 0

        for i, msg in enumerate(reversed(messages)):
            if msg.media:
                is_photo = isinstance(msg.media, MessageMediaPhoto)
                is_video = isinstance(
                    msg.media, MessageMediaDocument) and hasattr(
                        msg.media, 'document'
                    ) and msg.media.document.mime_type.startswith('video/')

                if is_photo or is_video:
                    try:
                        # Medyayı indir
                        file_path = await client.download_media(msg.media)

                        if file_path:
                            # Hedef gruba gönder
                            await client.send_file(
                                target_entity,
                                file_path,
                                caption=msg.text if msg.text else None)

                            # Dosyayı sil
                            if os.path.exists(file_path):
                                os.remove(file_path)

                            if is_photo:
                                photo_count += 1
                            else:
                                video_count += 1

                            # Her 10 medyada bir durum güncelle
                            if (photo_count + video_count) % 10 == 0:
                                await status_msg.edit(
                                    f"⏳ Transfer devam ediyor...\n\n"
                                    f"📸 Fotoğraf: {photo_count}\n"
                                    f"🎥 Video: {video_count}\n"
                                    f"❌ Hata: {error_count}")

                            await asyncio.sleep(2)  # Rate limit için bekle
                    except Exception as e:
                        print(f"Transfer hatası: {e}")
                        error_count += 1
                        continue

        await status_msg.edit(
            f"✅ **Transfer tamamlandı!**\n\n"
            f"📸 Fotoğraf: {photo_count}\n"
            f"🎥 Video: {video_count}\n"
            f"❌ Hata: {error_count}\n"
            f"📊 Toplam: {photo_count + video_count} medya aktarıldı!")
    except Exception as e:
        await event.respond(f"❌ Transfer hatası: {str(e)}")


async def main():
    """Userbot'u başlat"""
    print("=" * 50)
    print("🤖 USERBOT BAŞLATILIYOR")
    print("=" * 50)

    # API bilgilerini kontrol et
    if not api_id or not api_hash:
        print(
            "\n❌ HATA: TELEGRAM_API_ID ve TELEGRAM_API_HASH ortam değişkenleri ayarlanmamış!"
        )
        print("Lütfen Secrets bölümünden bu değerleri ekleyin.")
        return

    # Session dosyası var mı kontrol et
    session_file = f"{SESSION_NAME}.session"
    if not os.path.exists(session_file):
        print("\n❌ Session dosyası bulunamadı!")
        print("Lütfen önce Shell'de şu komutu çalıştırın:")
        print("   python auth.py")
        print("\nTelefon numaranızı ve doğrulama kodunu girdikten sonra")
        print("bu uygulamayı tekrar başlatın.")
        return

    try:
        # Bağlantıyı başlat (mevcut session ile)
        await client.connect()

        # Oturum açık mı kontrol et
        if not await client.is_user_authorized():
            print("\n❌ Oturum geçersiz veya süresi dolmuş!")
            print("Lütfen Shell'de şu komutu çalıştırın:")
            print("   python auth.py")
            await client.disconnect()
            return

        me = await client.get_me()
        print(f"\n✅ Giriş başarılı!")
        print(f"👤 Hesap: {me.first_name} {me.last_name or ''}")
        print(f"📱 Telefon: +{me.phone}")
        print(f"🆔 ID: {me.id}")
        print("\n" + "=" * 50)
        print("✨ USERBOT HAZIR!")
        print("Kendinize mesaj atarak komutları kullanabilirsiniz.")
        print("=" * 50 + "\n")

        await client.run_until_disconnected()

    except Exception as e:
        print(f"\n❌ Bağlantı hatası: {e}")
        print("Lütfen Shell'de 'python auth.py' komutunu çalıştırın.")


if __name__ == '__main__':
    asyncio.run(main())
