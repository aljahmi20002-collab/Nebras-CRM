#!/usr/bin/env bash
# ============================================================
#  NebrasCRM — بناء نسخة سطح المكتب
#  الاستخدام:  ./build-desktop.sh [linux|win|mac|run]
# ============================================================
set -e
cd "$(dirname "$0")/desktop"

TARGET="${1:-linux}"
echo "▶ بناء نسخة سطح المكتب — الهدف: $TARGET"

# ---------- 1. توليد الأيقونات من الهوية البصرية ----------
echo "▶ [1/3] توليد أيقونات التطبيق..."
mkdir -p build/icons
python3 - <<'PY'
import os, struct
from PIL import Image
B = "../brand/favicon"
if not os.path.exists(f"{B}/icon-512.png"):
    raise SystemExit("✗ أيقونات الهوية غير موجودة. شغّل أولاً: cd brand && python3 build_brand.py")

Image.open(f"{B}/icon-512.png").save("build/icon.png")
Image.open(f"{B}/icon-32.png").resize((32, 32), Image.LANCZOS).save("build/tray.png")

# Windows .ico — القاعدة أكبر مقاس وإلا حُفظ 16px فقط
Image.open(f"{B}/icon-256.png").convert("RGBA").save(
    "build/icon.ico", format="ICO",
    sizes=[(16,16),(24,24),(32,32),(48,48),(64,64),(128,128),(256,256)])

# Linux
for s in (16, 32, 48, 64, 128, 256, 512):
    Image.open(f"{B}/icon-{s}.png").save(f"build/icons/{s}x{s}.png")

# macOS .icns — نبني الحاوية يدوياً (لا تتوفر أدوات ماك على لينكس)
def icns(out, entries):
    body = b"".join(t + struct.pack(">I", len(d) + 8) + d for t, d in entries)
    open(out, "wb").write(b"icns" + struct.pack(">I", len(body) + 8) + body)

types = [(b"icp4",16),(b"icp5",32),(b"icp6",64),(b"ic07",128),(b"ic08",256),
         (b"ic09",512),(b"ic10",1024),(b"ic11",32),(b"ic12",64),(b"ic13",256),(b"ic14",512)]
ent = []
for t, size in types:
    p = f"{B}/icon-{size}.png"
    if not os.path.exists(p):
        p = f"/tmp/_i{size}.png"
        Image.open(f"{B}/icon-1024.png").resize((size, size), Image.LANCZOS).save(p)
    ent.append((t, open(p, "rb").read()))
icns("build/icon.icns", ent)
print("  ✔ ico + icns + png + tray")
PY

# ---------- 2. تثبيت الاعتماديات ----------
if [ ! -d node_modules ]; then
  echo "▶ [2/3] تثبيت الاعتماديات (قد يستغرق دقائق)..."
  npm install --no-audit --no-fund
else
  echo "▶ [2/3] الاعتماديات مثبّتة ✔"
fi

# ---------- 3. التشغيل أو الحزم ----------
case "$TARGET" in
  run)
    echo "▶ [3/3] تشغيل التطبيق..."
    npm start
    ;;
  linux)
    echo "▶ [3/3] حزم AppImage + deb..."
    npx electron-builder --linux AppImage deb --publish never
    ;;
  win)
    echo "▶ [3/3] حزم مثبّت ويندوز..."
    npx electron-builder --win --publish never
    ;;
  mac)
    echo "▶ [3/3] حزم DMG..."
    npx electron-builder --mac --publish never
    ;;
  *)
    echo "✗ هدف غير معروف: $TARGET  (linux | win | mac | run)"; exit 1 ;;
esac

# ---------- جمع المخرجات ----------
if [ "$TARGET" != "run" ]; then
  mkdir -p ../dist
  find dist -maxdepth 1 -type f \
       \( -name "*.AppImage" -o -name "*.deb" -o -name "*.rpm" \
          -o -name "*.exe" -o -name "*.dmg" -o -name "*.zip" \) \
       -exec cp {} ../dist/ \;
  ( cd ../dist && sha256sum * > SHA256SUMS.txt 2>/dev/null || true )
  echo
  echo "✅ تم البناء. المخرجات في dist/:"
  ls -lh ../dist/ | tail -n +2
fi
