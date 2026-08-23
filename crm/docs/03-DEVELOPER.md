# دليل المطوّر — NebrasCRM
**البنية · التوسعة · الـAPI · قواعد المساهمة**

---

## 1. تجهيز بيئة التطوير

```bash
# المتطلبات: Python 3.11+
cd crm
pip install fastapi uvicorn pydantic
python3 -m uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

**بيانات تجريبية** (أول مرة فقط، بالترتيب):
```bash
python3 seed.py          # مستخدمون · عملاء · صفقات · فواتير
python3 seed_intel.py    # منافسون · دراسات سوق
python3 seed_extra.py    # فرص · مخزون راكد · قوائم
python3 seed_geo.py      # مواقع · وكلاء · عمولات
python3 seed_portal.py   # حسابات بوابة العملاء
```

**اختياري:** `cairosvg Pillow fontTools arabic-reshaper python-bidi brotli` لإعادة توليد الهوية والمخططات.

---

## 2. بنية المشروع

```
crm/
├── main.py              التطبيق · المصادقة · CRUD العام · التحليلات
├── schema.py            ★ تعريف الوحدات — نقطة التوسعة الأساسية
├── db.py                الاتصال · الترحيل · سجل التدقيق
│
├── ai.py                7 محركات تنبؤ
├── reports.py           17 تقريراً + إعدادات النظام
├── payments.py          دفتر المدفوعات · روابط · ويب هوك
├── gateways.py          36 قناة دفع (تعريفية)
├── loyalty.py           محرك الولاء
├── segments.py          RFM · القوائم · الرواكد
├── partners.py          الوكلاء · العمولات
├── geo.py               الخريطة الإدارية
├── intel.py             ذكاء السوق
├── mailer.py            البريد والقوالب
├── platform_ext.py      360° · حقول مخصصة · API عام
├── portal.py            بوابة العملاء
├── agentportal.py       بوابة الشركاء
│
├── static/              الواجهات (SPA بلا إطار عمل)
│   ├── app.js           تطبيق الموظفين
│   ├── portal.js        بوابة العملاء
│   ├── agent.js         بوابة الشركاء
│   ├── styles.css       التصميم + الخط المضمّن + الطباعة
│   ├── sw.js            Service Worker (العمل دون اتصال)
│   └── pwa.js           تثبيت التطبيق · المزامنة
│
├── brand/               الهوية البصرية (مولَّدة برمجياً)
├── desktop/             تطبيق Electron
├── mobile/              تطبيق Capacitor
└── docs/                هذه الوثائق
```

---

## 3. المبدأ الحاكم: مدفوع بالميتاداتا

### إضافة وحدة كاملة

أضف قاموساً واحداً في `schema.py`:

```python
"contracts": {
    "label_en": "Contracts", "label_ar": "العقود",
    "icon": "📜", "group": "sales", "title": "name",
    "kanban": "status",                    # اختياري: يفعّل عرض كانبان
    "fields": [
        F("name", "Contract", "العقد", required=True),
        F("account_id", "Account", "الشركة", "lookup", target="accounts"),
        F("value", "Value", "القيمة", "currency"),
        F("status", "Status", "الحالة", "select",
          options=["Draft", "Active", "Expired"], default="Draft"),
        F("start_date", "Start", "البداية", "date"),
        F("owner_id", "Owner", "المسؤول", "user"),
    ],
    "list": ["name", "account_id", "value", "status", "owner_id"],
},
```

أعد التشغيل، فتحصل **تلقائياً** على:
جدول قاعدة بيانات · 6 نقاط API · شاشة قائمة · نموذج إضافة وتعديل · فلاتر · بحث ·
استيراد وتصدير CSV · خيارات في منشئ التقارير واللوحات.

**دون كتابة سطر واجهة واحد.**

### أنواع الحقول

| النوع | السلوك |
|---|---|
| `text` `textarea` `email` `phone` `url` | نص |
| `number` `currency` | رقم (يُخزَّن REAL) |
| `date` | تاريخ ISO |
| `select` | قائمة من `options` |
| `lookup` | ربط بوحدة أخرى عبر `target` |
| `user` | ربط بمستخدم النظام |

---

## 4. الـAPI — 188 نقطة نهاية

| المجموعة | العدد | البادئة |
|---|---|---|
| الأعمال (CRUD + تحليلات) | 102 | `/api/...` |
| بوابة العملاء | 19 | `/portal/api/...` |
| صفحات وملفات ثابتة | 17 | `/`, `/app`, `/brand/...` |
| بوابة الشركاء | 14 | `/agent/api/...` |
| الإدارة والإعدادات | 11 | `/api/admin`, `/api/settings` |
| الذكاء الاصطناعي | 11 | `/api/ai/...` |
| التقارير | 5 | `/api/reports/...` |
| الدفع | 4 | `/pay/...` |
| ويب هوكس واردة | 3 | `/api/hooks/...` |
| API عام بمفتاح | 2 | `/api/v1/...` |

**توثيق تفاعلي كامل:** `http://localhost:8000/docs`

### CRUD العام (يعمل لكل وحدة)

```http
GET    /api/{module}?q=&page=1&per_page=25&sort=id&dir=desc&filters=[]&mine=0
GET    /api/{module}/{id}
POST   /api/{module}
PUT    /api/{module}/{id}
DELETE /api/{module}/{id}          # حذف ناعم
POST   /api/{module}/bulk          # {ids, action: delete|update, field, value}
GET    /api/{module}/export/csv?token=...
POST   /api/{module}/import        # multipart CSV
```

### المصادقة

```bash
TOKEN=$(curl -s -XPOST localhost:8000/api/auth/login \
  -H 'Content-Type: application/json' \
  -d '{"email":"admin@nebrascrm.io","password":"admin123"}' | jq -r .token)

curl -H "Authorization: Bearer $TOKEN" localhost:8000/api/deals
```

### API عام بمفتاح (للتكاملات)

```bash
# أنشئ مفتاحاً من: التكاملات ← مفاتيح API
curl -H "X-API-Key: nx_xxxxx" localhost:8000/api/v1/leads?limit=50
curl -XPOST -H "X-API-Key: nx_xxxxx" -H 'Content-Type: application/json' \
     -d '{"name":"عميل جديد","email":"x@y.com"}' localhost:8000/api/v1/leads
```

### ويب هوكس واردة

| المسار | الوظيفة |
|---|---|
| `POST /api/hooks/whatsapp` | رسالة واردة ← تُطابق بجهة الاتصال أو تُنشئ عميلاً محتملاً |
| `POST /api/hooks/leadform` | نموذج ويب ← عميل محتمل + حساب درجة الجاهزية فوراً |
| `POST /api/hooks/order` | طلب متجر ← شركة + فاتورة |
| `POST /pay/webhook` | إشعار الدفع — موقّع بـ HMAC-SHA256، **آمن ضد التكرار** |

---

## 5. إضافة تقرير جديد

في `reports.py` أضف مدخلاً لقاموس `REPORTS`:

```python
"my_report": {
    "ar": "تقريري", "en": "My Report", "group": "sales", "icon": "📊",
    "desc_ar": "وصف يظهر على البطاقة",
    "sql": """SELECT x k, COUNT(*) n, SUM(amount) v
              FROM deals WHERE deleted=0 {date} GROUP BY x""",
    "date_col": "closing_date",              # يفعّل فلتر التاريخ
    "cols": [("k", "المفتاح", "Key", "text"),
             ("n", "العدد", "Count", "int"),
             ("v", "القيمة", "Value", "money")],
    "derive": lambda r: {**r, "extra": ...},  # اختياري: حقول محسوبة
    "admin_only": False,
},
```

تحصل تلقائياً على: بطاقة في مركز التقارير · جدول بصف إجمالي · فلترة بالتاريخ ·
طباعة A4 · تصدير CSV و Excel و JSON.

**أنواع الأعمدة:** `text` · `int` · `money` · `pct` — تحدد التنسيق والتجميع.

---

## 6. إضافة قناة دفع

في `gateways.py`:

```python
CH("mypay", "MyPay", "ماي باي", "wallet", country="YE", icon="📱",
   fields=["msisdn", "otp"], prefix=["77"], fee_pct=1.5,
   currency=["YER", "USD"], instant=True),
```

يظهر تلقائياً في صفحة الدفع بحقوله الصحيحة، ويدخل في محرك الرسوم وتقرير القنوات.

**`instant=False`** يجعل القناة تُسجَّل «بانتظار التسوية» فلا تُضاف للفاتورة قبل تأكيد الموظف —
هذا هو السلوك الصحيح للحوالات.

---

## 7. الأمن — قواعد إلزامية

### القاعدة الأولى
> كل قيد يُفرض على **الخادم**. إخفاء زر في الواجهة ليس حماية.

### عند إضافة نقطة نهاية

```python
@app.post("/api/something")
def do_something(body: dict, user=Depends(current_user)):
    require(user, "admin", "manager")     # تحقق الدور
    if user["role"] == "readonly":        # أو: منع القراءة فقط
        raise HTTPException(403, "Read-only user")
    ...
    D.log(con, "module", rid, "action", changes, user["id"])   # سجّل دائماً
    con.commit()
```

### عزل بيانات البوابات
كل استعلام في `portal.py` و`agentportal.py` **مقيّد على مستوى SQL** بحساب العميل أو الشريك.
لا تعتمد أبداً على الفلترة في الواجهة.

```python
def _scope(u):
    return "CAST(account_id AS INTEGER)=?", [int(u["account_id"])]
```

### ما لا يجب فعله
- ❌ لا تضع طلبات المصادقة في طابور العمل دون اتصال
- ❌ لا ترسل كلمات المرور أو المفاتيح للمتصفح (تُعرض كـ `••••`)
- ❌ لا تبني SQL بدمج نصي من مدخلات المستخدم — استخدم المعاملات دائماً
- ❌ لا تحذف السجلات فعلياً — استخدم `deleted=1`

---

## 8. الواجهة الأمامية

### لا إطار عمل — لماذا؟
لا خطوة بناء، ولا اعتماديات تتقادم، وملف واحد يُقرأ من أوله لآخره.
النظام كله يُخدَّم كملفات ثابتة.

### القواعد
- **الترجمة:** كل نص في قاموس `T` بمفتاحين `ar`/`en` — لا نصوص مكتوبة مباشرة
- **الاتجاه والثيم:** استدعِ `applyShell()` في أي دالة تعيد بناء `document.body`
- **الألوان:** استخدم متغيرات CSS (`var(--pri)`) لا قيماً ثابتة
- **ألوان من الخادم:** مرّرها عبر `TC()` لتُعتَّم تلقائياً في الثيم النهاري
- **التهريب:** كل قيمة من الخادم تمر بـ `esc()` قبل الإدراج في HTML

```javascript
// نمط الشاشة القياسي
async function viewMyScreen(){
  const d = await api("/my/endpoint");
  main.innerHTML = `<div class="h1">${t("myTitle")}</div>
    <div class="card">${d.rows.map(r=>`
      <div>${esc(r.name)}</div>`).join("")}</div>`;
  // اربط الأحداث بعد الإدراج
}
```

---

## 9. الاختبار

لا توجد حزمة اختبار آلية بعد. الأسلوب المتبع هو التحقق عبر الـAPI مباشرة:

```bash
# فحص شامل سريع
TOKEN=$(curl -s -XPOST localhost:8000/api/auth/login -H 'Content-Type: application/json' \
  -d '{"email":"admin@nebrascrm.io","password":"admin123"}' | python3 -c 'import sys,json;print(json.load(sys.stdin)["token"])')

for ep in /api/analytics/dashboard /api/ai/digest /api/reports/catalogue /api/meta; do
  echo -n "$ep = "; curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $TOKEN" localhost:8000$ep
done
```

**اختبارات يجب إجراؤها عند أي تعديل حساس:**
- عزل البوابات: رمز عميل على بوابة الشركاء ← يجب 401
- الصلاحيات: مستخدم «قراءة فقط» يحاول الكتابة ← يجب 403
- عزل المندوب: مندوب يعدّل سجل زميله ← يجب 403
- الحمايات المالية: صرف يتجاوز الرصيد ← يجب 400

---

## 10. إعادة توليد الأصول

```bash
cd brand  && python3 build_brand.py     # الشعار · الأيقونات · بطاقات التواصل
cd docs   && python3 make_diagrams.py   # المخططات المعمارية
```

**ملاحظة مهمة عن النصوص في SVG:**
محرّكات SVG لا تُشكّل العربية، ولا يمكن الاعتماد على وجود الخط في جهاز القارئ.
لذا `brand/textpath.py` يُشكّل النص ثم **يحوّل كل حرف إلى مسار متجه**،
مع **اختيار الخط لكل حرف على حدة** (الكوفي للعربية، Montserrat للاتينية) —
لأن اختيار خط واحد للنص المختلط يُسقط بصمت كل حرف لا يحويه الخط.

---

## 11. المساهمة

| المبدأ | التطبيق |
|---|---|
| **الميتاداتا أولاً** | قبل كتابة كود، اسأل: هل يمكن تعريفه بدل برمجته؟ |
| **الخادم يحمي** | كل تحقق على الخادم، والواجهة تحسين تجربة فقط |
| **ثنائية اللغة إلزامية** | أي نص جديد يحتاج `ar` و`en` |
| **سجّل كل تغيير** | `D.log()` في كل عملية كتابة |
| **حذف ناعم** | لا `DELETE FROM` على بيانات الأعمال |
| **اشرح القرار** | إن كان الحل غير بديهي، علّق على **السبب** لا على ما يفعله الكود |
