#!/usr/bin/env bash
# ============================================================
# NebrasCRM — بناء نسخة سطح المكتب
# الاستخدام: ./build-desktop.sh [linux|win|mac|run]
# ============================================================
set -Eeuo pipefail

trap 'echo "✗ فشل بناء تطبيق سطح المكتب عند السطر ${LINENO}." >&2' ERR

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
DESKTOP_DIR="$ROOT_DIR/desktop"
TARGET="${1:-linux}"

find_python() {
  local candidate
  for candidate in "${PYTHON_BIN:-}" python3 python py; do
    [ -n "$candidate" ] || continue
    if command -v "$candidate" >/dev/null 2>&1; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done
  return 1
}

require_command() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "✗ الأداة المطلوبة غير موجودة: $1" >&2
    exit 1
  }
}

PYTHON="$(find_python)" || {
  echo "✗ لم يُعثر على Python 3. ثبّت Python 3.10 أو أحدث، أو اضبط PYTHON_BIN." >&2
  exit 1
}

case "$TARGET" in
  linux|win|mac|run) ;;
  *)
    echo "✗ هدف غير معروف: $TARGET  (linux | win | mac | run)" >&2
    exit 1
    ;;
esac

if [ "$TARGET" = "mac" ] && [ "$(uname -s)" != "Darwin" ]; then
  echo "✗ بناء DMG يتطلب macOS. شغّل هذا الأمر على جهاز Mac أو GitHub Actions macOS." >&2
  exit 1
fi

require_command node
require_command npm
require_command npx

echo "▶ بناء نسخة سطح المكتب — الهدف: $TARGET"
cd "$DESKTOP_DIR"

# ---------- 1. توليد الأيقونات من الهوية البصرية ----------
echo "▶ [1/3] توليد أيقونات التطبيق..."
"$PYTHON" -c "from PIL import Image" 2>/dev/null || {
  echo "▶ تثبيت Pillow لتوليد الأيقونات..."
  "$PYTHON" -m pip install --user Pillow
}
mkdir -p build/icons
"$PYTHON" - <<'PY'
import os
import struct
from pathlib import Path
from PIL import Image

brand = Path("../brand/favicon")
required = [brand / "icon-512.png", brand / "icon-32.png", brand / "icon-256.png"]
missing = [str(path) for path in required if not path.is_file()]
if missing:
    raise SystemExit("✗ أيقونات الهوية غير موجودة: " + ", ".join(missing) +
                     ". شغّل: cd brand && python build_brand.py")

Path("build/icons").mkdir(parents=True, exist_ok=True)
Image.open(brand / "icon-512.png").save("build/icon.png")
Image.open(brand / "icon-32.png").resize((32, 32), Image.LANCZOS).save("build/tray.png")
Image.open(brand / "icon-256.png").convert("RGBA").save(
    "build/icon.ico", format="ICO",
    sizes=[(16, 16), (24, 24), (32, 32), (48, 48), (64, 64), (128, 128), (256, 256)],
)

for size in (16, 32, 48, 64, 128, 256, 512):
    source = brand / f"icon-{size}.png"
    if not source.is_file():
        source = brand / "icon-512.png"
    Image.open(source).resize((size, size), Image.LANCZOS).save(f"build/icons/{size}x{size}.png")

# macOS .icns container; it is generated on every host so packaging remains deterministic.
def write_icns(output, entries):
    body = b"".join(kind + struct.pack(">I", len(data) + 8) + data for kind, data in entries)
    Path(output).write_bytes(b"icns" + struct.pack(">I", len(body) + 8) + body)

icns_types = [
    (b"icp4", 16), (b"icp5", 32), (b"icp6", 64), (b"ic07", 128), (b"ic08", 256),
    (b"ic09", 512), (b"ic10", 1024), (b"ic11", 32), (b"ic12", 64),
    (b"ic13", 256), (b"ic14", 512),
]
entries = []
for kind, size in icns_types:
    source = brand / f"icon-{size}.png"
    if source.is_file():
        data = source.read_bytes()
    else:
        temp = Path(f"build/.icon-{size}.png")
        Image.open(brand / "icon-512.png").resize((size, size), Image.LANCZOS).save(temp)
        data = temp.read_bytes()
        temp.unlink(missing_ok=True)
    entries.append((kind, data))
write_icns("build/icon.icns", entries)
print("  ✔ ico + icns + png + tray")
PY

# ---------- 2. تثبيت الاعتماديات ----------
if [ ! -d node_modules ]; then
  echo "▶ [2/3] تثبيت اعتماديات Node.js (قد يستغرق دقائق)..."
  if [ -f package-lock.json ]; then
    npm ci --no-audit --no-fund
  else
    npm install --no-audit --no-fund
  fi
else
  echo "▶ [2/3] الاعتماديات مثبّتة ✔"
fi

# ---------- 3. التشغيل أو الحزم ----------
if [ "$TARGET" = "run" ]; then
  echo "▶ [3/3] تشغيل التطبيق التجريبي..."
  exec npm start
fi

# Avoid copying stale artifacts from a previous platform/architecture build.
rm -rf dist
case "$TARGET" in
  linux)
    echo "▶ [3/3] حزم AppImage + deb..."
    npx electron-builder --linux AppImage deb --publish never
    ;;
  win)
    echo "▶ [3/3] حزم Windows (NSIS + portable)..."
    npx electron-builder --win --publish never
    ;;
  mac)
    echo "▶ [3/3] حزم DMG + zip..."
    npx electron-builder --mac --publish never
    ;;
esac

# ---------- جمع المخرجات والتحقق ----------
EXPORT_DIR="$ROOT_DIR/dist"
mkdir -p "$EXPORT_DIR"
artifact_count=0
while IFS= read -r -d '' artifact; do
  cp -f "$artifact" "$EXPORT_DIR/"
  artifact_count=$((artifact_count + 1))
done < <(find dist -maxdepth 1 -type f \( \
  -name "*.AppImage" -o -name "*.deb" -o -name "*.rpm" -o -name "*.exe" \
  -o -name "*.dmg" -o -name "*.zip" \) -print0)

if [ "$artifact_count" -eq 0 ]; then
  echo "✗ لم ينتج electron-builder أي ملف قابل للتوزيع." >&2
  exit 1
fi

(
  cd "$EXPORT_DIR"
  checksum_tmp="$(mktemp .SHA256SUMS.XXXXXX)"
  while IFS= read -r -d '' file; do
    if command -v sha256sum >/dev/null 2>&1; then
      sha256sum "$file"
    elif command -v shasum >/dev/null 2>&1; then
      shasum -a 256 "$file"
    else
      echo "⚠ sha256sum/shasum غير متاح؛ لم تُنشأ بصمات الملفات." >&2
      break
    fi
  done < <(find . -maxdepth 1 -type f ! -name SHA256SUMS.txt -print0) > "$checksum_tmp"
  mv -f "$checksum_tmp" SHA256SUMS.txt
)

echo
echo "✅ تم البناء. المخرجات في $EXPORT_DIR:"
find "$EXPORT_DIR" -maxdepth 1 -type f -print | sort
