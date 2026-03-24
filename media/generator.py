import os
import subprocess
from PIL import Image, ImageDraw
from gtts import gTTS

def create_image(image_path, source_name):
    try:
        img = Image.open(image_path).convert("RGBA")
        base = Image.new('RGBA', img.size, (255,255,255,0))
        draw = ImageDraw.Draw(img)
        # Adding branding logic
        draw.text((20, 20), source_name, fill=(255, 255, 255, 180))
        draw.text((20, img.height - 50), "World News 🌍", fill=(255, 255, 255, 200))
        out_path = f"proc_{os.path.basename(image_path)}"
        img.convert("RGB").save(out_path)
        return out_path
    except Exception as e:
        print(f"Pillow Error: {e}")
        return image_path

def create_video(image_path, text_ar):
    tts_audio = "temp.mp3"
    vid_out = "temp.mp4"
    try:
        # TTS Voiceover (Arabic)
        tts = gTTS(text=text_ar[:400], lang='ar')
        tts.save(tts_audio)
        
        # FFmpeg assembly: Combine image, audio, add 15s cap, and cinematic zoom
        subprocess.run([
            "ffmpeg", "-y", "-loop", "1",
            "-i", image_path,
            "-i", tts_audio,
            "-c:v", "libx264", "-t", "15",
            "-pix_fmt", "yuv420p",
            "-vf", "zoompan=z='min(zoom+0.0015,1.5)':d=450",
            "-shortest", 
            vid_out
        ], check=True)
        return vid_out
    except Exception as e:
        print(f"FFmpeg Error: {e}")
        return None
    finally:
        if os.path.exists(tts_audio):
            os.remove(tts_audio)
