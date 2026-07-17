import os
import subprocess
from datetime import datetime

from PIL import Image
import pillow_avif

# =========================
# 🔹 إعدادات
# =========================

# ضع هنا الفولدرات الرئيسية فقط
input_folders = [
    r"D:\Documents\Projects\Videos_App\electron-app\assets\pics",
]

# مسار مشروع Git
GIT_REPO = r"D:\Documents\Projects\Videos_App\electron-app\assets"

Image.MAX_IMAGE_PIXELS = None
MAX_DIMENSION = 16383

SUPPORTED_EXTENSIONS = (
    ".png",
    ".jpg",
    ".jpeg",
    ".ico",
    ".avif"
)

# =========================
# 🔥 تحويل الصورة
# =========================

def convert_image(input_path):
    folder = os.path.dirname(input_path)
    filename = os.path.basename(input_path)

    name_without_ext = os.path.splitext(filename)[0]
    output_path = os.path.join(folder, f"{name_without_ext}.webp")

    # لو الـ WebP موجود بالفعل احذف الأصل
    if os.path.exists(output_path):
        try:
            os.remove(input_path)
            print(f"🗑 Deleted original (WebP exists): {input_path}")
        except Exception as e:
            print(f"❌ Couldn't delete {input_path}: {e}")
        return

    try:
        img = Image.open(input_path)

        # إصلاح اتجاه الصورة
        try:
            exif = img.getexif()
            orientation = exif.get(274)

            if orientation == 3:
                img = img.rotate(180, expand=True)
            elif orientation == 6:
                img = img.rotate(270, expand=True)
            elif orientation == 8:
                img = img.rotate(90, expand=True)
        except:
            pass

        # تحويل الـ Mode
        if img.mode in ("RGBA", "LA", "P"):
            img = img.convert("RGBA")
        else:
            img = img.convert("RGB")

        # تصغير لو الصورة كبيرة
        if img.width > MAX_DIMENSION or img.height > MAX_DIMENSION:
            img.thumbnail((MAX_DIMENSION, MAX_DIMENSION))

        save_args = {
            "format": "WEBP",
            "quality": 90,
            "method": 6,
            "optimize": True
        }

        if img.mode == "RGBA":
            save_args["lossless"] = True

        img.save(output_path, **save_args)
        img.close()

        if os.path.exists(output_path):
            os.remove(input_path)
            print(f"✔ Converted: {input_path}")
        else:
            print(f"⚠ Failed to create WebP: {input_path}")

    except Exception as e:
        print(f"❌ Error with {input_path}: {e}")


# =========================
# 🔄 تشغيل التحويل
# =========================

for folder in input_folders:
    print(f"\n📂 Processing: {folder}")

    if not os.path.exists(folder):
        print("⚠ Folder not found")
        continue

    # يدور داخل جميع الفولدرات الفرعية
    for root, _, files in os.walk(folder):
        for filename in files:
            if filename.lower().endswith(SUPPORTED_EXTENSIONS):
                convert_image(os.path.join(root, filename))

print("\n🔥 Image conversion finished!")

# =========================
# 🚀 Git Auto Push
# =========================

print("\n📤 Running Git commands...")

commit_message = f"Auto Update {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"

commands = [
    ["git", "add", "."],
    ["git", "commit", "-m", commit_message],
    ["git", "push", "-u", "origin", "main"]
]

for command in commands:
    result = subprocess.run(
        command,
        cwd=GIT_REPO,
        capture_output=True,
        text=True
    )

    if result.stdout:
        print(result.stdout)

    if result.returncode != 0:

        # لو مفيش تغييرات
        if (
            command[1] == "commit"
            and (
                "nothing to commit" in result.stdout.lower()
                or "nothing to commit" in result.stderr.lower()
            )
        ):
            print("ℹ No changes to commit.")
            break

        print(result.stderr)
        raise RuntimeError(f"Git command failed: {' '.join(command)}")

print("\n✅ Git Push Completed Successfully!")