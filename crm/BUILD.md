# دليل البناء — NebrasCRM
**كيف تولّد نسخة سطح المكتب وتطبيق الجوال**

---

## ⚡ الطريقة السريعة

```bash
cd crm

./build-desktop.sh linux     # AppImage + deb
./build-desktop.sh run       # تشغيل مباشر للتجربة

./build-mobile.sh release    # APK موقّع
./build-mobile.sh debug      # APK تصحيح
```

المخرجات تُجمع تلقائياً في **`dist/`** مع ملف بصمات `SHA256SUMS.txt`.

> السكربتان يتوليان كل شيء: توليد الأيقونات من الهوية البصرية، تثبيت الاعتماديات،
> ضبط الإعدادات، البناء، ثم التحقق من صحة المخرج.

---

## ⚠️ ملاحظة مهمة قبل البدء

مجلدات `node_modules/` و`dist/` و`build/` **لا تُحفظ** مع المشروع (وهذا مقصود — حجمها مئات الميجابايت
وقابلة لإعادة التوليد). لذلك عند فتح المشروع على جهاز جديد:

- **لن تجد ملفات APK أو AppImage جاهزة** — شغّل سكربت البناء لتوليدها
- التحميل الأول يستغرق وقتاً (Electron ~106MB، اعتماديات Gradle)
- ما بعده يكون أسرع بكثير لأن الحزم تُخزَّن مؤقتاً

**الكود المصدري وملفات الهوية محفوظة بالكامل** — وهي كل ما يلزم لإعادة البناء.

---

## 🖥️ نسخة سطح المكتب (Electron)

### المتطلبات
| الأداة | الإصدار | التحقق |
|---|---|---|
| Node.js | 18+ | `node --version` |
| Python + Pillow | 3.9+ | لتوليد الأيقونات |

### الأوامر

```bash
./build-desktop.sh run      # تشغيل للتجربة (بدون حزم)
./build-desktop.sh linux    # AppImage + deb
./build-desktop.sh win      # مثبّت NSIS
./build-desktop.sh mac      # DMG
```

### ماذا يفعل السكربت
1. **يولّد الأيقونات** من `brand/favicon/` → `icon.ico` (7 مقاسات) · `icon.icns` (11 نوعاً) · أيقونات Linux · أيقونة شريط المهام
2. **يثبّت الاعتماديات** إن لم تكن موجودة
3. **يحزم** عبر electron-builder وينسخ الناتج إلى `dist/`

### ⚠️ قيد مهم على البناء عبر المنصات
| تبني على | تستطيع إنتاج |
|---|---|
| **Linux** | ✅ AppImage · deb · rpm |
| **Windows** | ✅ exe · ⚠️ AppImage جزئياً |
| **macOS** | ✅ DMG · exe · AppImage |

**لا يمكن بناء DMG لماك إلا على جهاز ماك** — قيد من Apple لا من المشروع.
للبناء الآلي لكل المنصات استخدم GitHub Actions بثلاثة أنظمة تشغيل.

### التشغيل بعد البناء
```bash
# Linux — بلا تثبيت
chmod +x dist/NebrasCRM-1.0.0-x86_64.AppImage
./dist/NebrasCRM-1.0.0-x86_64.AppImage

# Debian / Ubuntu
sudo dpkg -i dist/NebrasCRM-1.0.0-amd64.deb
```

عند أول تشغيل: القائمة **ملف ← الإعدادات** لضبط عنوان الخادم (افتراضياً `http://localhost:8008`).

---

## 📱 تطبيق الجوال (Capacitor + Android)

### المتطلبات
| الأداة | الإصدار | ملاحظة |
|---|---|---|
| Node.js | 18+ | |
| **JDK** | **17 أو أحدث** | JDK 11 **لا يكفي** |
| Android SDK | API 34 | مع build-tools 34 |

### تثبيت JDK
```bash
sudo apt install openjdk-21-jdk-headless      # Debian / Ubuntu
```

### تثبيت Android SDK (بلا Android Studio)
```bash
mkdir -p ~/android-sdk/cmdline-tools && cd ~/android-sdk/cmdline-tools
curl -O https://dl.google.com/android/repository/commandlinetools-linux-11076708_latest.zip
unzip commandlinetools-linux-*.zip && mv cmdline-tools latest

yes | ~/android-sdk/cmdline-tools/latest/bin/sdkmanager \
      --sdk_root=$HOME/android-sdk --licenses

~/android-sdk/cmdline-tools/latest/bin/sdkmanager --sdk_root=$HOME/android-sdk \
  "platform-tools" "platforms;android-34" "build-tools;34.0.0"
```

> إن كان لديك **Android Studio** فالـSDK مثبّت مسبقاً — فقط اضبط:
> `export ANDROID_HOME=$HOME/Android/Sdk`

### الأوامر

```bash
./build-mobile.sh release   # APK موقّع (للتوزيع)
./build-mobile.sh debug     # APK تصحيح
./build-mobile.sh sync      # مزامنة ملفات الويب فقط
./build-mobile.sh run       # تشغيل على جهاز/محاكي متصل
```

### ماذا يفعل السكربت
1. **يتحقق** من JDK 17+ و Android SDK ويرشدك للتثبيت إن نقص شيء
2. **يولّد أيقونات أندرويد** بكل الكثافات + **أيقونة تكيّفية** (الشعلة داخل منطقة آمنة فلا يقصّها أي قناع) + شاشة بدء
3. **يضبط ذاكرة Gradle** — الإعداد الافتراضي يُقتل على الأجهزة محدودة الذاكرة
4. **ينشئ مفتاح توقيع** تلقائياً إن لم يوجد
5. **يبني ويتحقق** من هوية الحزمة وتوقيعها

### التثبيت على الجهاز
```bash
adb install -r dist/NebrasCRM-1.0.0.apk
```
أو انقل الملف للهاتف وثبّته يدوياً (فعّل «تثبيت من مصادر غير معروفة»).

### 🍎 نسخة iOS
```bash
cd mobile && npx cap add ios && npx cap open ios
```
ثم البناء من **Xcode** — يتطلب **جهاز macOS** وحساب مطوّر Apple.

---

## 🔑 مفتاح التوقيع — تحذير جوهري

السكربت ينشئ مفتاحاً تلقائياً **للتجربة فقط**. قبل النشر على Google Play:

```bash
keytool -genkeypair -v -keystore my-release.keystore \
  -alias mykey -keyalg RSA -keysize 2048 -validity 10000
```

عند أول `./build-mobile.sh release` ينشئ السكربت مفتاح تجربة وكلمات مرور عشوائية،
ويحفظها محلياً في `mobile/android/nebras-release.properties` (مستثنى من Git).
للمفتاح الإنتاجي استخدم مفتاحك الخاص ثم مرّر القيم في CI أو جلسة البناء:

```bash
export NEBRAS_STORE_PASS='...'
export NEBRAS_KEY_PASS='...'
export NEBRAS_KEY_ALIAS='mykey'   # اختياري؛ الافتراضي nebras
```

> **⚠️ احفظ المفتاح وملف كلمات المرور في مكان آمن خارج المستودع.**
> فقدان مفتاح الإنتاج يعني **استحالة تحديث التطبيق على Google Play إلى الأبد** — لا يوجد استرجاع.

---

## 🌐 البديل الأسرع: تطبيق الويب التقدمي (PWA)

**بلا أي بناء إطلاقاً:**
1. شغّل الخادم
2. افتح `/app` في المتصفح
3. اختر **«تثبيت التطبيق»** من شريط العنوان أو من الإشعار داخل التطبيق

تحصل على أيقونة على سطح المكتب أو الشاشة الرئيسية، ونافذة مستقلة، وعملاً دون اتصال —
دون Node ولا JDK ولا Android SDK.

**هذا هو المسار الموصى به للتجربة السريعة والانتشار الواسع.**

---

## 🔍 حل المشكلات الشائعة

| العَرَض | السبب والحل |
|---|---|
| `Gradle daemon disappeared` | نقص ذاكرة — السكربت يضبطها تلقائياً؛ إن تكرر أغلق التطبيقات الأخرى |
| `يلزم JDK 17 أو أحدث` | ثبّت `openjdk-21-jdk-headless` |
| `Android SDK غير موجود` | اتبع خطوات التثبيت أعلاه أو اضبط `ANDROID_HOME` |
| `libnss3.so` عند تشغيل Electron | `sudo apt install libnss3 libgtk-3-0 libasound2` |
| التطبيق لا يتصل بالخادم | تأكد أن الخادم يعمل على `0.0.0.0` لا `127.0.0.1`، واضبط العنوان في الإعدادات |
| الجوال لا يرى الخادم المحلي | استخدم `10.0.2.2:8008` للمحاكي، أو عنوان IP للشبكة للجهاز الحقيقي |
| البناء بطيء أول مرة | طبيعي — Electron ~106MB واعتماديات Gradle؛ المرات التالية أسرع |

---

## ✅ التحقق من صحة المخرجات

```bash
cd dist && sha256sum -c SHA256SUMS.txt

# فحص الـAPK
BT=$(for d in $ANDROID_HOME/build-tools/*/; do [ -x "$d/aapt2" ] && echo "$d"; done | sort -V | tail -1)
"$BT/aapt2" dump badging NebrasCRM-1.0.0.apk | grep -E "package|application-label"
"$BT/apksigner" verify --print-certs NebrasCRM-1.0.0.apk
```

**المتوقع:** `io.nebrascrm.app` · التسمية العربية `نبراس` · توقيع بشهادة NebrasCRM.
