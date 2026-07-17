import os
import json
import subprocess
import sys

# ==========================================
# Cloudflare R2 Settings
# ==========================================

ACCESS_KEY = "87b544de19d87b53cfea237da86acc8f"
SECRET_KEY = "212690252d8ff96dc541bdd9274c03841a16bf73b3b22f220e72e1cf593d51e8"

ENDPOINT = "https://2e0617ddc730d7a1ad448073368451a3.r2.cloudflarestorage.com"
BUCKET = "videos"

REGION = "auto"
OUTPUT = "json"

# ==========================================
# Choose Content-Disposition
# ==========================================

print("=" * 60)
print(" Cloudflare R2 Metadata Updater")
print("=" * 60)
print()
print("Choose Content-Disposition:")
print("  ATC = attachment (Force Download)")
print("  INL = inline (Open In Browser)")
print()

while True:
    choice = input("Choose (ATC/INL): ").strip().lower()

    if choice == "atc":
        CONTENT_DISPOSITION = "attachment"
        break

    elif choice == "inl":
        CONTENT_DISPOSITION = "inline"
        break

    else:
        print("Invalid choice.\n")

print(f"\nSelected: {CONTENT_DISPOSITION}\n")

# ==========================================

env = os.environ.copy()

env["AWS_ACCESS_KEY_ID"] = ACCESS_KEY
env["AWS_SECRET_ACCESS_KEY"] = SECRET_KEY
env["AWS_DEFAULT_REGION"] = REGION
env["AWS_DEFAULT_OUTPUT"] = OUTPUT


def run(cmd):
    return subprocess.run(
        cmd, env=env, capture_output=True, text=True, encoding="utf-8", errors="replace"
    )


print("Reading bucket...")

result = run(
    ["aws", "s3", "ls", f"s3://{BUCKET}", "--recursive", "--endpoint-url", ENDPOINT]
)

if result.returncode != 0:
    print(result.stderr)
    input("\nPress Enter to exit...")
    sys.exit()

if not result.stdout:
    print("No output received from AWS CLI.")
    print(result.stderr)
    input("\nPress Enter to exit...")
    sys.exit()

files = []

for line in result.stdout.splitlines():

    parts = line.split(maxsplit=3)

    if len(parts) != 4:
        continue

    key = parts[3]

    if key.endswith("/"):
        continue

    files.append(key)

print(f"\nFound {len(files)} files.\n")

for index, file in enumerate(files, start=1):

    print(f"[{index}/{len(files)}] {file}")

    # اقرأ الـ Metadata الحالية
    head = run(
        [
            "aws",
            "s3api",
            "head-object",
            "--bucket",
            BUCKET,
            "--key",
            file,
            "--endpoint-url",
            ENDPOINT,
        ]
    )

    if head.returncode != 0:
        print("   ❌ Failed to read metadata")
        print(head.stderr)
        continue

    try:
        metadata = json.loads(head.stdout)
    except Exception:
        print("   ❌ Invalid response")
        continue

    current = metadata.get("ContentDisposition", "")
    content_type = metadata.get("ContentType", "")

    if (
    current.lower() == CONTENT_DISPOSITION.lower()
    and content_type == "video/mp4"
    ):
        print("   ⏭ Skipped")
        continue

    update_cmd = [
        "aws",
        "s3",
        "cp",
        f"s3://{BUCKET}/{file}",
        f"s3://{BUCKET}/{file}",
        "--metadata-directive",
        "REPLACE",
        "--content-disposition",
        CONTENT_DISPOSITION,
    ]

    # الحفاظ على Content-Type الأصلي
    if content_type:
        update_cmd.extend(["--content-type", content_type])

    update_cmd.extend(["--endpoint-url", ENDPOINT])

    update = run(update_cmd)

    if update.returncode != 0:
        print("   ❌ Failed")
        print(update.stderr)
    else:
        print("   ✔ Updated")
print()
print("=" * 60)
print(" Finished")
print("=" * 60)

input("\nPress Enter to close...")
