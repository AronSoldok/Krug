from aiogram import Router, Bot, F
from aiogram.types import Message, ContentType, FSInputFile
from aiogram.filters import CommandStart
from aiogram.enums import ParseMode
from moviepy.editor import VideoFileClip, CompositeVideoClip, ImageClip
from PIL import Image, ImageDraw
import numpy as np
import os
import uuid

router = Router(name='handlers')

@router.message(CommandStart())
async def cmd_start(message: Message):
    await message.answer('Привет! Я <b>конвертирую видео из обычного формата в кружочек</b>. Просто скинь мне видео и будет магия!',
                         parse_mode=ParseMode.HTML)

@router.message(F.content_type == ContentType.VIDEO)
async def handle_video(message: Message, bot: Bot):
    video = message.video
    file_id = video.file_id
    await message.answer('Видео конвертируется, дайте нам пару минут')
    file = await bot.get_file(file_id)
    file_path = file.file_path
    input_video_path = f"{uuid.uuid1()}.mp4"
    await bot.download_file(file_path, input_video_path)

    try:
        # Преобразование видео в кружочек
        output_video_path = f"{uuid.uuid3(uuid.NAMESPACE_DNS, str(uuid.uuid1()))}.mp4"
        duration_warning = convert_video_to_circle(input_video_path, output_video_path)

        # Отправка видеокружка
        video_file = FSInputFile(output_video_path)
        await message.answer_video_note(video_file)
        if duration_warning:
            await message.answer('Предупреждение: Видео было обрезано до 1 минуты, так как исходное видео длилось дольше.')
        await message.answer('Всё готово! Если хотите конвертировать ещё какое-либо видео, просто отправьте его мне')
    except Exception as e:
        await message.answer("Произошла ошибка при обработке видео.")
        print(f"Error: {e}")
    finally:
        # Удаление временных файлов
        if os.path.exists(input_video_path):
            try:
                os.remove(input_video_path)
            except PermissionError:
                pass
        if os.path.exists(output_video_path):
            try:
                os.remove(output_video_path)
            except PermissionError:
                pass

def convert_video_to_circle(input_path, output_path):
    clip = VideoFileClip(input_path)
    w, h = clip.size
    duration_warning = False

    # Проверка формата видео
    if clip.fps > 30:
        clip = clip.set_fps(30)
    if clip.duration > 60:
        clip = clip.subclip(0, 60)
        duration_warning = True
    if w != h:
        size = min(w, h)
        clip = clip.crop(x_center=w/2, y_center=h/2, width=size, height=size)
    if w > 600 or h > 600:
        clip = clip.resize(height=600)

    # Создание маски в форме круга с помощью PIL
    mask_img = Image.new('L', (w, h), 0)
    draw = ImageDraw.Draw(mask_img)
    draw.ellipse((0, 0, w, h), fill=255)
    mask = np.array(mask_img) / 255

    # Преобразование маски в ImageClip
    mask_clip = ImageClip(mask, ismask=True).set_duration(clip.duration)

    # Применение маски к видео
    circle_clip = clip.set_mask(mask_clip)

    # Сохранение видео
    circle_clip.write_videofile(output_path, codec="libx264", audio_codec="aac")

    # Закрытие клипов
    clip.close()
    mask_clip.close()
    circle_clip.close()

    return duration_warning
