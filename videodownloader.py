import telebot
import instaloader
import os
from telebot import types
from moviepy import VideoFileClip
import uuid
import shutil

BOT_TOKEN = "6714295341:AAH_WVqB8UW95ZgeRT40aogK4ZmE7Nn_Cgo"

bot = telebot.TeleBot(BOT_TOKEN)

loader = instaloader.Instaloader(
    download_comments=False,
    download_geotags=False,
    download_pictures=False,
    download_video_thumbnails=False,
    save_metadata=False,
)

video_file = None
folder_name = None


@bot.message_handler(commands=["start"])
def start(message):
    bot.send_message(message.chat.id, "Assalom aleykum hush kelibsiz✅")


def clean_folder(path):
    """Fayllarni tozalash uchun yordamchi funksiya"""
    try:
        if os.path.exists(path):
            shutil.rmtree(path, ignore_errors=True)
    except:
        pass


@bot.message_handler(func=lambda message: True)
def get_instagram_video(message):
    global video_file, folder_name
    url = message.text.strip()
    video_file = None
    folder_name = None

    try:
        shortcode = url.split("/")[-2]
        folder_name = shortcode
    except IndexError:
        bot.reply_to(message, "❌ Link noto'g'ri!")
        return

    loader_message = bot.send_message(message.chat.id, "⏳ Video yuklanmoqda...")

    try:
        post = instaloader.Post.from_shortcode(loader.context, shortcode)
        loader.download_post(post, target=shortcode)

        for file in os.listdir(shortcode):
            if file.endswith(".mp4"):
                video_file = os.path.join(shortcode, file)
                break

        if not video_file:
            raise Exception("Video topilmadi")

        with open(video_file, "rb") as video:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton(
                "🎧 Audioni yuklab olish", callback_data="get_audio"
            )
            markup.add(btn1)
            bot.send_video(message.chat.id, video, reply_markup=markup)

        bot.delete_message(message.chat.id, loader_message.message_id)

    except instaloader.exceptions.QueryReturnedNotFoundException:
        bot.reply_to(message, "❌ Instagram bu postni bloklagan yoki topilmadi!")

    except instaloader.exceptions.TwoFactorAuthRequiredException:
        bot.reply_to(message, "❌ Instagram login talab qilmoqda!")

    except Exception as e:
        if "403" in str(e):
            bot.reply_to(
                message, "❌ Instagram 403 xato berdi. Postni yuklab bo'lmadi."
            )
        else:
            bot.reply_to(message, f"❌ Xatolik: {e}")

    finally:
        clean_folder(folder_name)


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    global video_file, folder_name

    if call.data == "get_audio":
        try:
            wait = bot.send_message(call.message.chat.id, "⏳ Audio tayyorlanmoqda...")

            video = VideoFileClip(video_file)
            audio = video.audio
            audio_name = f"{uuid.uuid4()}.mp3"
            audio.write_audiofile(audio_name)
            video.close()

            with open(audio_name, "rb") as audio_:
                bot.send_audio(call.message.chat.id, audio_)

            os.remove(audio_name)

            bot.delete_message(call.message.chat.id, wait.message_id)

        except Exception as e:
            bot.reply_to(call.message, f"❌ Audio yuklashda xatolik: {e}")

        finally:
            clean_folder(folder_name)


bot.infinity_polling()
