# NebrasCRM — إصدار Docker مع MySQL 8.4

**تاريخ التجهيز:** 28 أغسطس 2026 — مراجعة R2  
**قاعدة البيانات:** الصورة الرسمية `mysql:8.4` (MySQL 8 LTS)

هذه حزمة مصدر نظيفة لتشغيل NebrasCRM عبر Docker Compose مع MySQL 8.4. لا تحتوي الحزمة على أسرار محلية أو قاعدة SQLite أو بيانات Docker سابقة.

## تحديث R2

يعالج هذا التحديث خطأ MySQL 8 رقم `1170` عند إنشاء فهرس POS على `created_at`. أصبح العمود الجديد `VARCHAR(40)`، وتنفَّذ ترقية تلقائية وآمنة للعمود القديم من `TEXT` قبل إنشاء الفهرس؛ لا يلزم حذف قاعدة البيانات لتطبيق الإصلاح.

## التشغيل السريع

### Linux / WSL / Git Bash

```bash
cd crm
bash ./compose-up.sh
```

ينشئ المشغّل تلقائياً ملف `.env.docker` خاصاً على جهازك، بكلمات مرور ومفاتيح عشوائية، ثم يبني صورة التطبيق ويشغّلها.

### Windows (Command Prompt أو PowerShell)

```bat
cd crm
compose-up.bat
```

إذا كان `python3` متاحاً، ينشئ المشغّل الإعدادات العشوائية تلقائياً. وإلا فسوف ينشئ `.env.docker` من القالب؛ افتحه واستبدل كل قيمة تبدأ بـ `replace-with-` ثم شغّل الأمر مرة أخرى.

## أول تسجيل دخول

لا تستخدم قاعدة MySQL الجديدة حساباً تجريبياً ثابتاً. عند التشغيل الأول فقط، يُنشأ مدير النظام من القيم الخاصة داخل:

```text
crm/.env.docker
```

استخدم:

```text
CRM_BOOTSTRAP_ADMIN_EMAIL
CRM_BOOTSTRAP_ADMIN_PASSWORD
```

للدخول إلى:

```text
http://localhost:8008/app
```

بعد الدخول، يمكن إضافة السجلات التجريبية من **إعدادات النظام → إضافة بيانات تجريبية**.

## إعادة ضبط بيانات الاختبار

> هذا يحذف **مجلد بيانات MySQL الخاص بـ Docker فقط**، ولا يحذف ملفات المصدر أو `crm.db` الموجود خارج Docker.

```bash
cd crm
bash ./compose-up.sh --reset-data
```

في Windows:

```bat
cd crm
compose-up.bat --reset-data
```

### إصلاح ملف إعدادات ناقص

إذا ظهر الخطأ `MYSQL_PASSWORD is missing` وكانت البيانات تجريبية، احذف ملف الإعدادات المحلي القديم ليُنشأ من جديد ثم نفّذ إعادة الضبط:

```bash
rm -f .env.docker && bash ./compose-up.sh --reset-data
```

في Windows:

```bat
del .env.docker && compose-up.bat --reset-data
```

## التحقق والسجلات

```bash
docker compose --env-file .env.docker -f docker-compose.yml ps
docker compose --env-file .env.docker -f docker-compose.yml logs -f app
docker compose --env-file .env.docker -f docker-compose.yml logs --tail=200 mysql
```

عند استخدام أوامر Docker المباشرة، يجب دائماً تمرير `--env-file .env.docker`؛ وذلك لأن Docker Compose يعالج متغيرات `${...}` قبل تطبيق `env_file` الخاص بالخدمة.

## ما الذي تم التحقق منه قبل الحزم؟

- فحص بنية ملفات Python وShell.
- نجاح **20 اختبار انحدار ودخان**، بما في ذلك الصلاحيات، POS، الفواتير، الطباعة، Resend، وترقية مخطط POS الخاصة بـ MySQL/MariaDB/PostgreSQL.
- التحقق من YAML لعقد Compose: تطبيق + MySQL 8.4، health checks، شبكة قاعدة البيانات الخاصة، ومتغيرات bootstrap.
- التحقق من أن سياق بناء Docker يستبعد `.env*` وملفات قواعد البيانات المحلية، ويُبقي بيانات GeoNames المطلوبة.
- تم اختبار إنشاء أول مدير وتسجيل دخوله على قاعدة جديدة بإعدادات production.

لم يُنشأ Docker image فعلياً داخل بيئة المراجعة لأن Docker daemon غير متاح فيها. ستُبنى الصورة تلقائياً على جهازك عند تشغيل `compose-up.sh` أو `compose-up.bat`.

## مهم للأمان

- لا ترفع `.env.docker` إلى Git ولا ترسله لأي شخص؛ يحتوي كلمات مرور ومفاتيح دخول.
- استبدل إعدادات النطاقات وResend قبل الاستخدام الإنتاجي.
- انتظر دقيقة إلى دقيقتين في أول تشغيل حتى تصبح حاوية `mysql` بحالة `healthy` ويكتمل تجهيز التطبيق.
