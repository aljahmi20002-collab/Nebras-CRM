#!/usr/bin/env bash
# ============================================================
# NebrasCRM — بناء تطبيق الجوال (Android / Capacitor)
# الاستخدام: ./build-mobile.sh [debug|release|sync|run]
# ============================================================
set -Eeuo pipefail

trap 'echo "✗ فشل بناء تطبيق الجوال عند السطر ${LINENO}." >&2' ERR

ROOT_DIR="$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd -P)"
MOBILE_DIR="$ROOT_DIR/mobile"
TARGET="${1:-release}"

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
  debug|release|sync|run) ;;
  *)
    echo "✗ هدف غير معروف: $TARGET  (debug | release | sync | run)" >&2
    exit 1
    ;;
esac

find_jdk() {
  local home javac version candidate resolved

  # JAVA_HOME is the preferred, cross-platform option.
  if [ -n "${JAVA_HOME:-}" ] && [ -x "$JAVA_HOME/bin/javac" ]; then
    home="$JAVA_HOME"
    version="$("$home/bin/javac" -version 2>&1 | grep -oE '[0-9]+' | head -1 || true)"
    if [ -n "$version" ] && [ "$version" -ge 17 ] 2>/dev/null; then
      printf '%s\n' "$home"
      return 0
    fi
  fi

  # macOS has a reliable Java home resolver.
  if [ -x /usr/libexec/java_home ]; then
    home="$(/usr/libexec/java_home -v 17+ 2>/dev/null || true)"
    if [ -n "$home" ] && [ -x "$home/bin/javac" ]; then
      printf '%s\n' "$home"
      return 0
    fi
  fi

  # Linux distributions conventionally place installed JDKs here.
  for candidate in /usr/lib/jvm/*; do
    [ -x "$candidate/bin/javac" ] || continue
    version="$("$candidate/bin/javac" -version 2>&1 | grep -oE '[0-9]+' | head -1 || true)"
    if [ -n "$version" ] && [ "$version" -ge 17 ] 2>/dev/null; then
      printf '%s\n' "$candidate"
      return 0
    fi
  done

  # Last resort: infer the home from javac on PATH.
  if javac="$(command -v javac 2>/dev/null)"; then
    resolved="$(readlink -f "$javac" 2>/dev/null || printf '%s' "$javac")"
    home="$(cd "$(dirname "$resolved")/.." 2>/dev/null && pwd -P || true)"
    if [ -x "$home/bin/javac" ]; then
      version="$("$home/bin/javac" -version 2>&1 | grep -oE '[0-9]+' | head -1 || true)"
      if [ -n "$version" ] && [ "$version" -ge 17 ] 2>/dev/null; then
        printf '%s\n' "$home"
        return 0
      fi
    fi
  fi
  return 1
}

find_android_sdk() {
  local candidate normalized
  for candidate in "${ANDROID_HOME:-}" "${ANDROID_SDK_ROOT:-}" \
      "$HOME/android-sdk" "$HOME/Android/Sdk" "${LOCALAPPDATA:-}/Android/Sdk"; do
    [ -n "$candidate" ] || continue
    normalized="$candidate"
    if command -v cygpath >/dev/null 2>&1 && [[ "$candidate" =~ ^[A-Za-z]: ]]; then
      normalized="$(cygpath -u "$candidate")"
    fi
    if [ -d "$normalized/platforms" ]; then
      printf '%s\n' "$normalized"
      return 0
    fi
  done
  return 1
}

echo "▶ بناء تطبيق الجوال — الهدف: $TARGET"
JDK="$(find_jdk || true)"
if [ -z "$JDK" ]; then
  cat >&2 <<'EOF'
✗ يلزم JDK 17 أو أحدث.
  Linux:   sudo apt install openjdk-21-jdk-headless
  macOS:   brew install openjdk@21 ثم اضبط JAVA_HOME
  Windows: ثبّت JDK 17+ واضبط JAVA_HOME قبل تشغيل Git Bash / PowerShell.
EOF
  exit 1
fi
export JAVA_HOME="$JDK"
echo "  ✔ JDK: $JAVA_HOME"

ANDROID_HOME="$(find_android_sdk || true)"
if [ -z "$ANDROID_HOME" ]; then
  cat >&2 <<'EOF'
✗ Android SDK غير موجود.
  اضبط ANDROID_HOME أو ANDROID_SDK_ROOT إلى مجلد SDK.
  المسارات الشائعة:
    Linux:   $HOME/android-sdk أو $HOME/Android/Sdk
    Windows: %LOCALAPPDATA%\Android\Sdk
    macOS:   $HOME/Library/Android/sdk
  يلزم تثبيت: platform-tools, platforms;android-34, build-tools;34.0.0
EOF
  exit 1
fi
export ANDROID_HOME ANDROID_SDK_ROOT="$ANDROID_HOME"
if [ ! -d "$ANDROID_HOME/platforms/android-34" ]; then
  echo "✗ Android SDK API 34 غير موجود في $ANDROID_HOME/platforms/android-34" >&2
  exit 1
fi
echo "  ✔ Android SDK: $ANDROID_HOME"

require_command node
require_command npm
require_command npx
cd "$MOBILE_DIR"

# ---------- 1. الاعتماديات ----------
if [ ! -d node_modules ]; then
  echo "▶ [1/4] تثبيت اعتماديات Node.js..."
  if [ -f package-lock.json ]; then
    npm ci --no-audit --no-fund
  else
    npm install --no-audit --no-fund
  fi
else
  echo "▶ [1/4] الاعتماديات مثبّتة ✔"
fi

# ---------- 2. مشروع Android + الأيقونات ----------
if [ ! -d android ]; then
  echo "▶ [2/4] إنشاء مشروع Android..."
  npx cap add android
fi

echo "▶ [2/4] توليد أيقونات Android..."
"$PYTHON" -c "from PIL import Image" 2>/dev/null || {
  echo "▶ تثبيت Pillow لتوليد الأيقونات..."
  "$PYTHON" -m pip install --user Pillow
}
"$PYTHON" - <<'PY'
import io
from pathlib import Path
from PIL import Image

source = Path("../brand/favicon")
bare_mark = Path("../brand/logo/nebras-mark-bare.svg")
resources = Path("android/app/src/main/res")
if not (source / "icon-512.png").is_file():
    raise SystemExit("✗ أيقونات الهوية غير موجودة. شغّل: cd brand && python build_brand.py")
try:
    import cairosvg
except ImportError:
    cairosvg = None

for density, size in {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}.items():
    output = resources / f"mipmap-{density}"
    output.mkdir(parents=True, exist_ok=True)
    icon = Image.open(source / "icon-512.png").convert("RGBA").resize((size, size), Image.LANCZOS)
    icon.save(output / "ic_launcher.png")
    icon.save(output / "ic_launcher_round.png")

    foreground_size = int(size * 108 / 48)
    inner_size = int(foreground_size * 0.52)
    if cairosvg and bare_mark.is_file():
        png = cairosvg.svg2png(url=str(bare_mark), output_width=inner_size, output_height=inner_size)
        flame = Image.open(io.BytesIO(png)).convert("RGBA")
    else:
        flame = Image.open(source / "icon-512.png").convert("RGBA").resize((inner_size, inner_size), Image.LANCZOS)
    canvas = Image.new("RGBA", (foreground_size, foreground_size), (0, 0, 0, 0))
    canvas.paste(flame, ((foreground_size-inner_size)//2, (foreground_size-inner_size)//2), flame)
    canvas.save(output / "ic_launcher_foreground.png")

(resources / "drawable").mkdir(parents=True, exist_ok=True)
splash = Image.new("RGBA", (1080, 1920), (15, 20, 32, 255))
logo = Image.open(source / "icon-512.png").convert("RGBA").resize((360, 360), Image.LANCZOS)
splash.paste(logo, (360, 780), logo)
splash.convert("RGB").save(resources / "drawable/splash.png")
print("  ✔ أيقونات تكيّفية + شاشة بدء")
PY

# Gradle expects a forward-slash path on Unix and also accepts C:/... on Windows.
SDK_FOR_GRADLE="$ANDROID_HOME"
if command -v cygpath >/dev/null 2>&1; then
  SDK_FOR_GRADLE="$(cygpath -m "$ANDROID_HOME")"
fi
printf 'sdk.dir=%s\n' "$SDK_FOR_GRADLE" > android/local.properties

# Keep builds stable on limited-memory development machines.
grep -q "org.gradle.jvmargs" android/gradle.properties || cat >> android/gradle.properties <<'EOF'
org.gradle.jvmargs=-Xmx900m -XX:MaxMetaspaceSize=384m -XX:+UseSerialGC
org.gradle.daemon=false
org.gradle.parallel=false
org.gradle.workers.max=1
EOF

# ---------- 3. مزامنة الويب ----------
echo "▶ [3/4] مزامنة ملفات الويب..."
npx cap sync android

cd android
chmod +x gradlew
if [ "$TARGET" = "sync" ]; then
  echo "✅ تمت المزامنة فقط."
  exit 0
fi
if [ "$TARGET" = "run" ]; then
  echo "▶ [4/4] تشغيل على جهاز/محاكي متصل..."
  cd ..
  exec npx cap run android
fi

# ---------- 4. البناء ----------
if [ "$TARGET" = "debug" ]; then
  echo "▶ [4/4] بناء نسخة التصحيح..."
  ./gradlew assembleDebug --no-daemon
  APK="app/build/outputs/apk/debug/app-debug.apk"
  NAME="NebrasCRM-1.0.0-debug.apk"
else
  echo "▶ [4/4] بناء نسخة الإصدار الموقعة..."
  KEYSTORE="nebras-release.keystore"
  KEY_PROPS="nebras-release.properties"
  if [ ! -f "$KEYSTORE" ]; then
    echo "  ⚠ لا يوجد مفتاح توقيع؛ يجري إنشاء مفتاح محلي للتجربة..."
    STORE_PASS="${NEBRAS_STORE_PASS:-$($PYTHON -c 'import secrets; print(secrets.token_urlsafe(24))')}"
    KEY_PASS="${NEBRAS_KEY_PASS:-$STORE_PASS}"
    KEY_ALIAS="${NEBRAS_KEY_ALIAS:-nebras}"
    "$JAVA_HOME/bin/keytool" -genkeypair -v -keystore "$KEYSTORE" -alias "$KEY_ALIAS" \
      -keyalg RSA -keysize 2048 -validity 10000 -storepass "$STORE_PASS" -keypass "$KEY_PASS" \
      -dname "CN=NebrasCRM, OU=Engineering, O=NebrasCRM, L=Global, C=US"
    ( umask 077
      cat > "$KEY_PROPS" <<EOF
storePassword=$STORE_PASS
keyPassword=$KEY_PASS
keyAlias=$KEY_ALIAS
EOF
    )
    echo "  ✔ حُفظت بيانات مفتاح التجربة محلياً في $KEY_PROPS (غير مضافة إلى Git)."
  elif [ ! -f "$KEY_PROPS" ] && { [ -z "${NEBRAS_STORE_PASS:-}" ] || [ -z "${NEBRAS_KEY_PASS:-}" ]; }; then
    echo "✗ المفتاح موجود لكن لا توجد بيانات كلمة المرور." >&2
    echo "  أنشئ $KEY_PROPS أو اضبط NEBRAS_STORE_PASS و NEBRAS_KEY_PASS." >&2
    exit 1
  fi
  ./gradlew assembleRelease --no-daemon
  APK="app/build/outputs/apk/release/app-release.apk"
  NAME="NebrasCRM-1.0.0.apk"
fi

# ---------- التحقق والجمع ----------
[ -f "$APK" ] || { echo "✗ لم يُنتج ملف APK: $APK" >&2; exit 1; }
EXPORT_DIR="$ROOT_DIR/dist"
mkdir -p "$EXPORT_DIR"
cp -f "$APK" "$EXPORT_DIR/$NAME"
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
echo "✅ تم البناء: $EXPORT_DIR/$NAME  ($(du -h "$APK" | cut -f1))"
BT="$(for directory in "$ANDROID_HOME"/build-tools/*/; do [ -x "$directory/aapt2" ] && echo "$directory"; done | sort -V | tail -1)"
[ -x "$BT/aapt2" ] && "$BT/aapt2" dump badging "$APK" 2>/dev/null | grep -E "^package|application-label:|application-label-ar"
[ -x "$BT/apksigner" ] && "$BT/apksigner" verify --print-certs "$APK" 2>/dev/null | head -1
