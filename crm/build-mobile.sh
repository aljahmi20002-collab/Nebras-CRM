#!/usr/bin/env bash
# ============================================================
#  NebrasCRM — بناء تطبيق الجوال (أندرويد)
#  الاستخدام:  ./build-mobile.sh [debug|release|sync|run]
# ============================================================
set -e
cd "$(dirname "$0")/mobile"

TARGET="${1:-release}"
echo "▶ بناء تطبيق الجوال — الهدف: $TARGET"

# ---------- 0. التحقق من الأدوات ----------
find_jdk() {
  local v p ver
  for v in 21 17; do
    p="/usr/lib/jvm/java-$v-openjdk-amd64"
    [ -d "$p" ] && { echo "$p"; return; }
  done
  # أي JDK 17+ متاح
  for p in /usr/lib/jvm/*/; do
    if [ -x "$p/bin/javac" ]; then
      ver=$("$p/bin/javac" -version 2>&1 | grep -oE '[0-9]+' | head -1)
      if [ -n "$ver" ] && [ "$ver" -ge 17 ] 2>/dev/null; then echo "${p%/}"; return; fi
    fi
  done
}
JDK="$(find_jdk || true)"
if [ -z "$JDK" ]; then
  echo "✗ يلزم JDK 17 أو أحدث. ثبّته بـ:"
  echo "    sudo apt install openjdk-21-jdk-headless"
  exit 1
fi
export JAVA_HOME="$JDK"
echo "  ✔ JDK: $JAVA_HOME"

export ANDROID_HOME="${ANDROID_HOME:-$HOME/android-sdk}"
export ANDROID_SDK_ROOT="$ANDROID_HOME"
if [ ! -d "$ANDROID_HOME/platforms" ]; then
  echo "✗ Android SDK غير موجود في $ANDROID_HOME"
  echo "  ثبّته بـ:"
  echo "    mkdir -p ~/android-sdk/cmdline-tools && cd ~/android-sdk/cmdline-tools"
  echo "    curl -O https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip"
  echo "    unzip commandlinetools-linux-*.zip && mv cmdline-tools latest"
  echo "    yes | ~/android-sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=\$HOME/android-sdk --licenses"
  echo "    ~/android-sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=\$HOME/android-sdk \\"
  echo "        'platform-tools' 'platforms;android-34' 'build-tools;34.0.0'"
  exit 1
fi
echo "  ✔ Android SDK: $ANDROID_HOME"

# ---------- 1. الاعتماديات ----------
if [ ! -d node_modules ]; then
  echo "▶ [1/4] تثبيت الاعتماديات..."
  npm install --no-audit --no-fund
else
  echo "▶ [1/4] الاعتماديات مثبّتة ✔"
fi

# ---------- 2. مشروع أندرويد + الأيقونات ----------
if [ ! -d android ]; then
  echo "▶ [2/4] إنشاء مشروع أندرويد..."
  npx cap add android
fi

echo "▶ [2/4] توليد أيقونات أندرويد..."
python3 - <<'PY'
import os, io
from PIL import Image
SRC="../brand/favicon"; BARE="../brand/logo/nebras-mark-bare.svg"
res="android/app/src/main/res"
if not os.path.exists(f"{SRC}/icon-512.png"):
    raise SystemExit("✗ شغّل أولاً: cd brand && python3 build_brand.py")
try:
    import cairosvg
except ImportError:
    cairosvg=None

for d,size in {"mdpi":48,"hdpi":72,"xhdpi":96,"xxhdpi":144,"xxxhdpi":192}.items():
    out=f"{res}/mipmap-{d}"; os.makedirs(out, exist_ok=True)
    im=Image.open(f"{SRC}/icon-512.png").convert("RGBA").resize((size,size), Image.LANCZOS)
    im.save(f"{out}/ic_launcher.png"); im.save(f"{out}/ic_launcher_round.png")
    # الأيقونة التكيّفية: الشعلة داخل منطقة آمنة فلا يقصّها أي قناع
    fg=int(size*108/48); inner=int(fg*0.52)
    if cairosvg:
        png=cairosvg.svg2png(url=BARE, output_width=inner, output_height=inner)
        flame=Image.open(io.BytesIO(png)).convert("RGBA")
    else:
        flame=Image.open(f"{SRC}/icon-512.png").convert("RGBA").resize((inner,inner), Image.LANCZOS)
    canvas=Image.new("RGBA",(fg,fg),(0,0,0,0))
    canvas.paste(flame,((fg-inner)//2,(fg-inner)//2),flame)
    canvas.save(f"{out}/ic_launcher_foreground.png")

os.makedirs(f"{res}/drawable", exist_ok=True)
bg=Image.new("RGBA",(1080,1920),(15,20,32,255))
lo=Image.open(f"{SRC}/icon-512.png").convert("RGBA").resize((360,360), Image.LANCZOS)
bg.paste(lo,(360,780),lo); bg.convert("RGB").save(f"{res}/drawable/splash.png")
print("  ✔ أيقونات تكيّفية + شاشة بدء")
PY

echo "sdk.dir=$ANDROID_HOME" > android/local.properties

# ضبط الذاكرة — Gradle يُقتل على الأجهزة محدودة الذاكرة
grep -q "org.gradle.jvmargs" android/gradle.properties || cat >> android/gradle.properties <<'EOF'
org.gradle.jvmargs=-Xmx900m -XX:MaxMetaspaceSize=384m -XX:+UseSerialGC
org.gradle.daemon=false
org.gradle.parallel=false
org.gradle.workers.max=1
EOF

# ---------- 3. مزامنة الويب ----------
echo "▶ [3/4] مزامنة ملفات الويب..."
npx cap sync android

# ---------- 4. البناء ----------
cd android && chmod +x gradlew
case "$TARGET" in
  sync) echo "✅ تمت المزامنة فقط."; exit 0 ;;
  run)  echo "▶ [4/4] تشغيل على جهاز/محاكي متصل..."; cd .. && npx cap run android; exit 0 ;;
  debug)
    echo "▶ [4/4] بناء نسخة التصحيح..."
    ./gradlew assembleDebug --no-daemon
    APK="app/build/outputs/apk/debug/app-debug.apk"; NAME="NebrasCRM-1.0.0-debug.apk" ;;
  release)
    echo "▶ [4/4] بناء نسخة الإصدار الموقّعة..."
    if [ ! -f nebras-release.keystore ]; then
      echo "  ⚠ لا يوجد مفتاح توقيع — يجري إنشاء واحد للتجربة..."
      "$JAVA_HOME/bin/keytool" -genkeypair -v -keystore nebras-release.keystore \
        -alias nebras -keyalg RSA -keysize 2048 -validity 10000 \
        -storepass nebras2026 -keypass nebras2026 \
        -dname "CN=NebrasCRM, OU=Engineering, O=NebrasCRM, L=Sanaa, C=YE"
    fi
    ./gradlew assembleRelease --no-daemon
    APK="app/build/outputs/apk/release/app-release.apk"; NAME="NebrasCRM-1.0.0.apk" ;;
  *) echo "✗ هدف غير معروف: $TARGET  (debug | release | sync | run)"; exit 1 ;;
esac

# ---------- التحقق والجمع ----------
[ -f "$APK" ] || { echo "✗ لم يُنتج ملف APK"; exit 1; }
mkdir -p ../../dist && cp "$APK" "../../dist/$NAME"
( cd ../../dist && sha256sum * > SHA256SUMS.txt 2>/dev/null || true )

echo
echo "✅ تم البناء: dist/$NAME  ($(du -h "$APK" | cut -f1))"
BT="$(for d in "$ANDROID_HOME"/build-tools/*/; do [ -x "$d/aapt2" ] && echo "$d"; done | sort -V | tail -1)"
[ -x "$BT/aapt2" ] && "$BT/aapt2" dump badging "$APK" 2>/dev/null | grep -E "^package|application-label:|application-label-ar"
[ -x "$BT/apksigner" ] && "$BT/apksigner" verify --print-certs "$APK" 2>/dev/null | head -1
