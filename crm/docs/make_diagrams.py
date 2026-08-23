#!/usr/bin/env python3
"""Generate NebrasCRM architecture diagrams as standalone SVG.

Hand-built SVG (no graphviz dependency) so the diagrams stay in the repo,
render anywhere, and can be regenerated after an architecture change.
Arabic labels are converted to outline paths via the brand text engine, so
they display correctly in every viewer regardless of installed fonts.
"""
import os, sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "brand"))
import textpath as TP

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "diagrams")
os.makedirs(OUT, exist_ok=True)

C = {
    "ink": "#0F1420", "panel": "#151C2C", "line": "#2A3550",
    "txt": "#E8EDF7", "mut": "#8B98B4",
    "indigo": "#4F7CFF", "violet": "#7C3AED", "gold": "#FFC53D",
    "cyan": "#06B6D4", "green": "#22C55E", "orange": "#F97316",
    "red": "#EF4444",
}


def T(text, size, x, y, fill="#E8EDF7", anchor="middle", weight="bold"):
    g, w = TP.text_svg_group(text, size, weight, fill, x, y, anchor)
    return g


def box(x, y, w, h, fill, stroke, r=12, op=1.0):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{r}" fill="{fill}" '
            f'fill-opacity="{op}" stroke="{stroke}" stroke-width="1.5"/>')


def arrow(x1, y1, x2, y2, color="#8B98B4", dash=""):
    d = f' stroke-dasharray="{dash}"' if dash else ""
    return (f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
            f'stroke-width="2"{d} marker-end="url(#ar)"/>')


def head(w, h, title_ar):
    return f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}">
<defs>
  <marker id="ar" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="7" markerHeight="7"
          orient="auto-start-reverse"><path d="M0 0 L10 5 L0 10 z" fill="#8B98B4"/></marker>
  <linearGradient id="hdr" x1="0" y1="0" x2="1" y2="0">
    <stop offset="0" stop-color="{C['indigo']}"/><stop offset="1" stop-color="{C['violet']}"/></linearGradient>
</defs>
<rect width="{w}" height="{h}" fill="{C['ink']}"/>
<rect x="0" y="0" width="{w}" height="52" fill="url(#hdr)"/>
{T(title_ar, 19, w/2, 34, "#FFFFFF")}
'''


# ---------------------------------------------------------------- 1. system architecture
def diagram_architecture():
    W, H = 1180, 800
    s = [head(W, H, "معمارية النظام — NebrasCRM")]

    # clients row
    clients = [("بوابة الموظفين", C["indigo"], 60), ("بوابة العملاء", C["green"], 320),
               ("بوابة الشركاء", C["orange"], 580), ("تطبيق سطح المكتب", C["violet"], 840)]
    for label, col, x in clients:
        s.append(box(x, 80, 240, 62, col, col, 12, 0.16))
        s.append(T(label, 15, x + 120, 118, col))

    s.append(T("طبقة العرض — واجهة SPA بلا إطار عمل", 12, W / 2, 168, C["mut"], weight="regular"))

    # gateway
    s.append(box(60, 190, 1060, 74, C["panel"], C["line"]))
    s.append(T("FastAPI — 188 نقطة نهاية", 16, W / 2, 222, C["txt"]))
    s.append(T("مصادقة · تحديد معدل · ترويسات أمنية · صلاحيات 4 أدوار", 11.5, W / 2, 246,
               C["mut"], weight="regular"))

    for _, _, x in clients:
        s.append(arrow(x + 120, 146, x + 120, 186))

    # three auth realms
    realms = [("SECRET", "الموظفون", C["indigo"], 90), ("PSECRET", "العملاء", C["green"], 470),
              ("ASECRET", "الشركاء", C["orange"], 850)]
    s.append(T("ثلاثة عوالم مصادقة معزولة بمفاتيح تشفير مستقلة", 12, W / 2, 296, C["gold"]))
    for key, label, col, x in realms:
        s.append(box(x, 310, 240, 48, col, col, 10, 0.13))
        s.append(T(f"{label}  ·  {key}", 12.5, x + 120, 340, col))

    # business modules
    s.append(box(60, 386, 1060, 214, C["panel"], C["line"]))
    s.append(T("طبقة الأعمال — 12 وحدة برمجية", 15, W / 2, 414, C["txt"]))
    mods = [
        ("schema.py", "15 وحدة بيانات"), ("ai.py", "7 محركات ذكاء"),
        ("reports.py", "17 تقريراً"), ("payments.py", "36 قناة دفع"),
        ("loyalty.py", "الولاء"), ("segments.py", "RFM والرواكد"),
        ("partners.py", "الوكلاء والعمولات"), ("geo.py", "44 ألف موقع"),
        ("intel.py", "ذكاء السوق"), ("mailer.py", "البريد والقوالب"),
        ("platform_ext.py", "360° وتكاملات"), ("portal.py", "البوابات"),
    ]
    for i, (f, desc) in enumerate(mods):
        cx = 100 + (i % 4) * 258
        cy = 436 + (i // 4) * 54
        s.append(box(cx, cy, 236, 44, C["ink"], C["line"], 9))
        s.append(T(f, 11.5, cx + 118, cy + 19, C["cyan"], weight="regular"))
        s.append(T(desc, 11, cx + 118, cy + 35, C["mut"], weight="regular"))

    s.append(arrow(W / 2, 264, W / 2, 306))
    s.append(arrow(W / 2, 358, W / 2, 382))

    # data + integrations
    s.append(box(60, 626, 500, 120, C["panel"], C["line"]))
    s.append(T("قاعدة البيانات — SQLite (WAL)", 14, 310, 656, C["txt"]))
    s.append(T("48 جدولاً · حذف ناعم · سجل تدقيق كامل", 11.5, 310, 680, C["mut"], weight="regular"))
    s.append(T("ترحيل تلقائي للمخطط عند الإقلاع", 11.5, 310, 700, C["mut"], weight="regular"))
    s.append(T("45 ألف سجل في البيانات التجريبية", 11.5, 310, 720, C["mut"], weight="regular"))

    s.append(box(620, 626, 500, 120, C["panel"], C["line"]))
    s.append(T("التكاملات الخارجية", 14, 870, 656, C["txt"]))
    s.append(T("SMTP · واتساب · نماذج ويب · متاجر إلكترونية", 11.5, 870, 680, C["mut"], weight="regular"))
    s.append(T("بوابات دفع · ERP · Zapier · Power BI", 11.5, 870, 700, C["mut"], weight="regular"))
    s.append(T("‎API عام /api/v1 بمفاتيح X-API-Key", 11.5, 870, 720, C["mut"], weight="regular"))

    s.append(arrow(310, 600, 310, 622))
    s.append(arrow(870, 600, 870, 622))
    s.append("</svg>")
    open(os.path.join(OUT, "01-architecture.svg"), "w", encoding="utf-8").write("\n".join(s))


# ---------------------------------------------------------------- 2. data model
def diagram_data_model():
    W, H = 1180, 760
    s = [head(W, H, "نموذج البيانات — العلاقات الأساسية")]

    ents = {
        "leads":      ("العملاء المحتملون", 60, 100, C["cyan"]),
        "accounts":   ("الشركات", 470, 100, C["indigo"]),
        "contacts":   ("جهات الاتصال", 880, 100, C["indigo"]),
        "opportunities": ("الفرص", 60, 250, C["gold"]),
        "deals":      ("الصفقات", 470, 250, C["gold"]),
        "competitors": ("المنافسون", 880, 250, C["red"]),
        "quotes":     ("عروض الأسعار", 60, 400, C["green"]),
        "invoices":   ("الفواتير", 470, 400, C["green"]),
        "payments":   ("المدفوعات", 880, 400, C["green"]),
        "products":   ("المنتجات", 60, 550, C["violet"]),
        "agents":     ("الوكلاء", 470, 550, C["orange"]),
        "geo":        ("الخريطة الإدارية", 880, 550, C["cyan"]),
    }
    for key, (label, x, y, col) in ents.items():
        s.append(box(x, y, 240, 62, col, col, 11, 0.15))
        s.append(T(label, 14, x + 120, y + 27, col))
        s.append(T(key, 10.5, x + 120, y + 46, C["mut"], weight="regular"))

    links = [
        ("leads", "accounts", "تحويل"), ("accounts", "contacts", "1:N"),
        ("accounts", "deals", "1:N"), ("opportunities", "deals", "تحويل"),
        ("deals", "competitors", "N:1"), ("deals", "quotes", "1:N"),
        ("quotes", "invoices", "1:N"), ("invoices", "payments", "1:N"),
        ("products", "quotes", "بنود"), ("agents", "deals", "عمولة"),
        ("geo", "accounts", "موقع"),
    ]
    for a, b, lbl in links:
        ax, ay = ents[a][1] + 120, ents[a][2] + 31
        bx, by = ents[b][1] + 120, ents[b][2] + 31
        if ay == by:
            x1, x2 = (ax + 120, bx - 120) if ax < bx else (ax - 120, bx + 120)
            s.append(arrow(x1, ay, x2, by))
            s.append(T(lbl, 10.5, (x1 + x2) / 2, ay - 8, C["mut"], weight="regular"))
        else:
            y1, y2 = (ay + 31, by - 31) if ay < by else (ay - 31, by + 31)
            s.append(f'<path d="M{ax} {y1} C {ax} {(y1+y2)/2}, {bx} {(y1+y2)/2}, {bx} {y2}" '
                     f'fill="none" stroke="{C["mut"]}" stroke-width="2" marker-end="url(#ar)"/>')
            s.append(T(lbl, 10.5, (ax + bx) / 2, (y1 + y2) / 2 - 6, C["mut"], weight="regular"))

    s.append(T("كل جدول يحمل: id · created_at · updated_at · owner_id · deleted (حذف ناعم)",
               11.5, W / 2, H - 22, C["gold"], weight="regular"))
    s.append("</svg>")
    open(os.path.join(OUT, "02-data-model.svg"), "w", encoding="utf-8").write("\n".join(s))


# ---------------------------------------------------------------- 3. sales lifecycle
def diagram_lifecycle():
    W, H = 1180, 480
    s = [head(W, H, "دورة حياة البيع — من أول تواصل حتى التحصيل")]
    steps = [
        ("عميل محتمل", "leads", C["cyan"]), ("تأهيل", "qualify", C["cyan"]),
        ("فرصة", "opportunities", C["gold"]), ("صفقة", "deals", C["gold"]),
        ("عرض سعر", "quotes", C["green"]), ("فاتورة", "invoices", C["green"]),
        ("تحصيل", "payments", C["green"]),
    ]
    x = 42
    for i, (label, code, col) in enumerate(steps):
        s.append(box(x, 110, 138, 76, col, col, 12, 0.16))
        s.append(T(label, 14, x + 69, 145, col))
        s.append(T(code, 10, x + 69, 166, C["mut"], weight="regular"))
        if i < len(steps) - 1:
            s.append(arrow(x + 138, 148, x + 158, 148))
        x += 160

    # side effects
    fx = [("🤖 تسجيل الجاهزية", 60), ("⚡ أتمتة المهام", 320), ("🏆 نقاط الولاء", 580),
          ("💰 عمولة الوكيل", 840)]
    s.append(T("ما يجري تلقائياً في الخلفية", 13, W / 2, 240, C["gold"]))
    for label, bx in fx:
        s.append(box(bx, 258, 240, 46, C["panel"], C["line"], 10))
        s.append(T(label, 12, bx + 120, 287, C["txt"], weight="regular"))

    s.append(T("سجل تدقيق يوثّق كل تغيير · إشعارات فورية · بريد بقوالب جاهزة",
               12, W / 2, 356, C["mut"], weight="regular"))
    s.append(box(60, 380, 1060, 60, C["indigo"], C["indigo"], 12, 0.12))
    s.append(T("العميل يتابع كل ذلك بنفسه من بوابة العملاء: الطلبات · الفواتير · الدفع · كشف الحساب",
               12.5, W / 2, 416, C["indigo"]))
    s.append("</svg>")
    open(os.path.join(OUT, "03-sales-lifecycle.svg"), "w", encoding="utf-8").write("\n".join(s))


# ---------------------------------------------------------------- 4. security model
def diagram_security():
    W, H = 1180, 620
    s = [head(W, H, "نموذج الأمن والصلاحيات")]

    layers = [
        ("طبقة الشبكة", "تحديد معدل 240 طلب/دقيقة · ترويسات أمنية · قفل بعد 5 محاولات فاشلة", C["red"]),
        ("طبقة المصادقة", "ثلاثة عوالم منفصلة: موظفون · عملاء · شركاء — مفاتيح تشفير مستقلة", C["orange"]),
        ("طبقة الصلاحيات", "4 أدوار: مدير نظام · مدير مبيعات · مندوب · قراءة فقط", C["gold"]),
        ("طبقة البيانات", "المندوب يرى سجلاته فقط · البوابات مقيّدة بحساب العميل على مستوى SQL", C["green"]),
        ("طبقة التدقيق", "كل إنشاء وتعديل وحذف مسجّل بالقيمة قبل وبعد ومَن نفّذه", C["cyan"]),
    ]
    y = 90
    for name, desc, col in layers:
        s.append(box(90, y, 1000, 74, col, col, 12, 0.12))
        s.append(T(name, 15, 250, y + 32, col))
        s.append(T(desc, 11.5, 700, y + 34, C["mut"], weight="regular"))
        y += 92

    s.append(T("مبدأ التصميم: كل قيد مفروض على الخادم لا على الواجهة — إخفاء زر ليس حماية",
               12.5, W / 2, H - 34, C["gold"]))
    s.append("</svg>")
    open(os.path.join(OUT, "04-security.svg"), "w", encoding="utf-8").write("\n".join(s))


# ---------------------------------------------------------------- 5. deployment
def diagram_deployment():
    W, H = 1180, 560
    s = [head(W, H, "خيارات النشر والتشغيل")]

    s.append(box(430, 90, 320, 96, C["indigo"], C["indigo"], 14, 0.18))
    s.append(T("خادم NebrasCRM", 17, 590, 128, C["indigo"]))
    s.append(T("Python · FastAPI · SQLite", 12, 590, 152, C["mut"], weight="regular"))
    s.append(T("uvicorn main:app --host 0.0.0.0", 10.5, 590, 172, C["mut"], weight="regular"))

    clients = [
        ("متصفح الويب", "أي جهاز — لا تثبيت", C["cyan"], 60, 280),
        ("تطبيق ويب PWA", "قابل للتثبيت · يعمل دون اتصال", C["green"], 330, 280),
        ("سطح المكتب", "ويندوز · ماك · لينكس", C["violet"], 600, 280),
        ("الجوال", "أندرويد APK · iOS", C["orange"], 870, 280),
    ]
    for label, desc, col, x, y in clients:
        s.append(box(x, y, 250, 90, col, col, 12, 0.15))
        s.append(T(label, 14, x + 125, y + 36, col))
        s.append(T(desc, 11, x + 125, y + 60, C["mut"], weight="regular"))
        s.append(f'<path d="M{x+125} {y} C {x+125} {y-40}, 590 {y-40}, 590 190" fill="none" '
                 f'stroke="{C["mut"]}" stroke-width="2" stroke-dasharray="5 4"/>')

    s.append(box(90, 424, 1000, 96, C["panel"], C["line"], 12))
    s.append(T("ملاحظة النشر", 13.5, 590, 452, C["gold"]))
    s.append(T("كل التطبيقات أغلفة حول نفس الخادم — تحديث الخادم يصل الجميع فوراً",
               12, 590, 476, C["txt"], weight="regular"))
    s.append(T("قبل الإنتاج: بدّل المفاتيح السرية · فعّل HTTPS · انقل إلى PostgreSQL للأحمال الكبيرة",
               11.5, 590, 500, C["mut"], weight="regular"))
    s.append("</svg>")
    open(os.path.join(OUT, "05-deployment.svg"), "w", encoding="utf-8").write("\n".join(s))


for fn in (diagram_architecture, diagram_data_model, diagram_lifecycle,
           diagram_security, diagram_deployment):
    fn()
    print("✔", fn.__name__)

# rasterise for docs that cannot embed SVG
try:
    import cairosvg
    for f in sorted(os.listdir(OUT)):
        if f.endswith(".svg"):
            cairosvg.svg2png(url=os.path.join(OUT, f),
                             write_to=os.path.join(OUT, f[:-4] + ".png"),
                             output_width=1400)
    print("✔ PNG versions generated")
except Exception as e:
    print("PNG skipped:", e)
