import sys, os, random, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db as D

random.seed(11)
con = D.init()

if con.execute("SELECT COUNT(*) c FROM competitors WHERE deleted=0").fetchone()["c"]:
    print("intel already seeded"); sys.exit()

uids = [r["id"] for r in con.execute("SELECT id FROM users WHERE role!='readonly'")]
def d(n): return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()
def ins(t, **kw):
    kw.update(created_at=D.now(), updated_at=D.now(), deleted=0)
    kw.setdefault("owner_id", random.choice(uids)); kw.setdefault("created_by", 1)
    k = list(kw)
    return con.execute(f'INSERT INTO "{t}" ({",".join(chr(34)+x+chr(34) for x in k)}) '
                       f'VALUES ({",".join("?"*len(k))})', [kw[x] for x in k]).lastrowid

COMPETITORS = [
 dict(name="Zoho CRM", tier="Primary", segment="All", hq_country="India", website="zoho.com/crm",
      founded=1996, employees=15000, annual_revenue=1000000000, market_share=4.8,
      pricing_model="Subscription", threat_score=9,
      strengths="تسعير منخفض جداً · منظومة تطبيقات متكاملة (60+ تطبيق) · تعريب ممتاز · حضور قوي في الشرق الأوسط",
      weaknesses="واجهة مزدحمة · جودة الدعم متفاوتة · التخصيص العميق يتطلب خبرة · أداء بطيء مع البيانات الضخمة",
      strategy="نتفوق بواجهة أبسط وأداء أسرع وتخصيص بلا كود. نستهدف عملاءهم المحبطين من الدعم ونقدّم ترحيلاً مجانياً للبيانات."),
 dict(name="Salesforce", tier="Primary", segment="Enterprise", hq_country="USA", website="salesforce.com",
      founded=1999, employees=79000, annual_revenue=34900000000, market_share=21.7,
      pricing_model="Subscription", threat_score=10,
      strengths="قائد السوق بلا منازع · منصة AppExchange · قدرات مؤسسية عميقة · ثقة العلامة التجارية",
      weaknesses="تكلفة إجمالية باهظة · يحتاج مستشارين للتنفيذ · تعقيد مفرط للشركات المتوسطة · رسوم إضافية لكل شيء",
      strategy="نستهدف الشركات المتوسطة التي تجد Salesforce مبالغاً فيه. رسالتنا: 80% من القدرات بـ 25% من التكلفة وبدون مستشارين."),
 dict(name="HubSpot CRM", tier="Primary", segment="Mid-Market", hq_country="USA", website="hubspot.com",
      founded=2006, employees=8200, annual_revenue=2600000000, market_share=5.3,
      pricing_model="Freemium", threat_score=8,
      strengths="نسخة مجانية سخية · تجربة استخدام ممتازة · تسويق داخلي قوي · سهولة التبني",
      weaknesses="التكلفة تقفز بحدة عند النمو · ضعف في إدارة المخزون والفوترة · تخصيص محدود",
      strategy="نبرز التكلفة الحقيقية عند التوسع، ونتفوق بوحدات المخزون والفواتير التي يفتقدونها."),
 dict(name="Microsoft Dynamics 365", tier="Primary", segment="Enterprise", hq_country="USA",
      website="dynamics.microsoft.com", founded=2001, employees=221000, annual_revenue=6800000000,
      market_share=5.7, pricing_model="Subscription", threat_score=9,
      strengths="تكامل عميق مع Office و Teams · قوة مؤسسية · اتفاقيات مشتريات حكومية",
      weaknesses="منحنى تعلّم حاد · تكلفة ترخيص مركّبة · يحتاج شريك تنفيذ · بطء في التحديثات",
      strategy="نستهدف من لا يملك بيئة مايكروسوفت كاملة. نؤكد على سرعة التنفيذ: أسابيع بدل أشهر."),
 dict(name="Pipedrive", tier="Secondary", segment="SMB", hq_country="Estonia", website="pipedrive.com",
      founded=2010, employees=1000, annual_revenue=120000000, market_share=1.9,
      pricing_model="Subscription", threat_score=6,
      strengths="بساطة شديدة · خط مبيعات بصري ممتاز · سعر معقول للفرق الصغيرة",
      weaknesses="محدود خارج المبيعات · لا يوجد دعم أو تسويق حقيقي · لا يصلح للمؤسسات",
      strategy="نفوز عندما ينمو العميل ويحتاج الدعم والتسويق والمخزون في نظام واحد."),
 dict(name="Freshsales (Freshworks)", tier="Secondary", segment="Mid-Market", hq_country="USA",
      website="freshworks.com", founded=2010, employees=4700, annual_revenue=596000000,
      market_share=1.4, pricing_model="Subscription", threat_score=6,
      strengths="واجهة نظيفة · ذكاء اصطناعي مدمج · تسعير تنافسي · دعم جيد",
      weaknesses="حضور ضعيف في الشرق الأوسط · تعريب ناقص · منظومة شركاء صغيرة",
      strategy="نتفوق بالتعريب الكامل ودعم RTL الأصلي والحضور المحلي."),
 dict(name="Odoo CRM", tier="Secondary", segment="SMB", hq_country="Belgium", website="odoo.com",
      founded=2005, employees=5500, annual_revenue=600000000, market_share=2.1,
      pricing_model="Hybrid", threat_score=7,
      strengths="مفتوح المصدر · ERP متكامل · تكلفة منخفضة · مرونة عالية",
      weaknesses="يحتاج خبرة تقنية · تكاليف تخصيص خفية · واجهة CRM أضعف من ERP",
      strategy="نستهدف من يريد CRM جاهزاً بلا فريق تقني. رسالتنا: تشغيل في يوم بدل مشروع تنفيذ."),
 dict(name="Bitrix24", tier="Emerging", segment="SMB", hq_country="Russia", website="bitrix24.com",
      founded=1998, employees=800, annual_revenue=100000000, market_share=1.2,
      pricing_model="Freemium", threat_score=5,
      strengths="مجاني لعدد كبير من المستخدمين · أدوات تعاون مدمجة · سعر منخفض",
      weaknesses="واجهة مربكة · أداء غير مستقر · مخاوف جيوسياسية لدى بعض العملاء",
      strategy="نؤكد على الموثوقية والاستضافة الإقليمية وحوكمة البيانات."),
]
cids = {}
for c in COMPETITORS:
    cids[c["name"]] = ins("competitors", **c)

our = {r["name"]: r for r in con.execute("SELECT id,name,unit_price FROM products WHERE deleted=0")}
def oid(n): return our[n]["id"] if n in our else None
def oprice(n): return our[n]["unit_price"] if n in our else None

PRODUCTS = [
 ("Zoho CRM Professional","Zoho CRM","CRM",276,"Per User / Year","Mid-Market","NebrasCRM Pro License","Parity",
  "أتمتة سير العمل · تقارير مخصصة · تكامل البريد · تطبيق جوال","ضعف في تحليلات الذكاء الاصطناعي · حدود على استدعاءات API"),
 ("Zoho CRM Enterprise","Zoho CRM","CRM",480,"Per User / Year","Enterprise","NebrasCRM Enterprise","We Win",
  "Zia AI · CommandCenter · وحدات مخصصة","الأداء يتدهور مع أكثر من مليون سجل · تخصيص معقّد"),
 ("Zoho One Suite","Zoho CRM","Suite",444,"Per User / Year","All","NebrasCRM Enterprise","They Win",
  "45+ تطبيق برخصة واحدة · قيمة استثنائية مقابل السعر","تكامل التطبيقات سطحي · جودة متفاوتة بين التطبيقات"),
 ("Salesforce Sales Cloud Enterprise","Salesforce","CRM",1980,"Per User / Year","Enterprise","NebrasCRM Enterprise","We Win",
  "منصة ناضجة · AppExchange · Einstein AI · تقارير قوية","تكلفة باهظة · رسوم على Sandbox و API · يحتاج مستشار"),
 ("Salesforce Service Cloud","Salesforce","Support",1980,"Per User / Year","Enterprise","Premium Support (yr)","We Win",
  "إدارة حالات متقدمة · Omni-channel · قاعدة معرفة","سعر مرتفع جداً · تعقيد الإعداد"),
 ("HubSpot Sales Hub Professional","HubSpot CRM","CRM",1080,"Per User / Year","Mid-Market","NebrasCRM Pro License","We Win",
  "تسلسلات بريدية · أتمتة تسويق ممتازة · تجربة سلسة","التكلفة تتضاعف عند إضافة المقاعد · لا فوترة ولا مخزون"),
 ("HubSpot Starter Suite","HubSpot CRM","Suite",240,"Per User / Year","SMB","NebrasCRM Pro License","They Win",
  "نقطة دخول رخيصة · مجاني للبداية","حدود صارمة على الميزات · علامة HubSpot على الرسائل"),
 ("Dynamics 365 Sales Enterprise","Microsoft Dynamics 365","CRM",1140,"Per User / Year","Enterprise","NebrasCRM Enterprise","We Win",
  "تكامل Teams و Outlook و Power BI · Copilot","يحتاج Power Platform لتخصيص جدي · تعقيد الترخيص"),
 ("Pipedrive Advanced","Pipedrive","CRM",408,"Per User / Year","SMB","NebrasCRM Pro License","We Win",
  "خط مبيعات بصري · بساطة · أتمتة أساسية","لا دعم ولا تسويق ولا فوترة · تقارير محدودة"),
 ("Freshsales Pro","Freshsales (Freshworks)","CRM",468,"Per User / Year","Mid-Market","NebrasCRM Pro License","Parity",
  "Freddy AI · هاتف مدمج · واجهة نظيفة","تعريب ناقص · لا يدعم RTL بالكامل"),
 ("Odoo CRM + Inventory","Odoo CRM","Suite",288,"Per User / Year","SMB","NebrasCRM Enterprise","Parity",
  "ERP كامل · مفتوح المصدر · وحدات لا نهائية","تكاليف التنفيذ تتجاوز الترخيص · يحتاج مطوّر"),
 ("Bitrix24 Professional","Bitrix24","Suite",199,"Flat / Month","SMB","NebrasCRM Pro License","They Win",
  "مستخدمون غير محدودين · تعاون وهاتف مدمج","واجهة مزدحمة · أداء متذبذب"),
 ("Salesforce Revenue Cloud (CPQ)","Salesforce","Quoting",1500,"Per User / Year","Enterprise","NebrasCRM Enterprise","We Win",
  "تسعير وعروض معقدة · اعتمادات متعددة","سعر إضافي فوق Sales Cloud · تنفيذ طويل"),
 ("Zoho Desk","Zoho CRM","Support",480,"Per User / Year","Mid-Market","Premium Support (yr)","Parity",
  "بوابة عملاء · SLA · قاعدة معرفة","يحتاج ترخيصاً منفصلاً عن CRM"),
 ("HubSpot Service Hub","HubSpot CRM","Support",1080,"Per User / Year","Mid-Market","Premium Support (yr)","We Win",
  "تذاكر · استبيانات رضا · بوابة عملاء","سعر مرتفع للقيمة المقدمة"),
]
for nm, comp, cat, price, billing, seg, ourp, pos, feats, gaps in PRODUCTS:
    ins("competitor_products", name=nm, competitor_id=cids[comp], category=cat, price=price,
        billing=billing, target_segment=seg, our_product_id=oid(ourp), our_price=oprice(ourp),
        positioning=pos, key_features=feats, gaps=gaps)

STUDIES = [
 dict(title="حجم سوق CRM في الشرق الأوسط 2026", type="Market Sizing", status="Completed", segment="All",
      region="MENA", market_size=2400000000, growth_rate=14.2, our_share=0.8, budget=25000,
      confidence="High", source="Gartner + IDC + تحليل داخلي", start_date=d(-150), end_date=d(-60),
      findings="سوق CRM في المنطقة يبلغ 2.4 مليار دولار بنمو سنوي 14.2%. السعودية والإمارات تمثلان 61% من الإنفاق. "
               "43% من الشركات المتوسطة ما زالت تستخدم جداول بيانات أو أنظمة قديمة. "
               "أكبر ثلاثة عوائق للتبني: التكلفة (38%)، ضعف التعريب (31%)، تعقيد التنفيذ (24%).",
      recommendations="التركيز على الشركات المتوسطة غير المخدومة برسالة 'تعريب أصلي + تنفيذ في أسبوع'. "
                      "بناء شراكات قنوات في الرياض ودبي. تسعير أقل 40% من Salesforce وأعلى 15% من Zoho لتموضع القيمة."),
 dict(title="تحليل تنافسي شامل: Zoho CRM", type="Competitor Analysis", status="Completed", segment="All",
      region="Global", growth_rate=11.0, budget=8000, confidence="High", source="اختبار مباشر + مقابلات عملاء",
      start_date=d(-95), end_date=d(-40),
      findings="Zoho يهيمن على شريحة السعر المنخفض بمنظومة 45+ تطبيقاً. اختبرنا المنصة بمليون سجل فتدهور زمن الاستجابة "
               "إلى 4.2 ثانية مقابل 0.9 ثانية لدينا. 7 من 12 عميلاً قابلناهم اشتكوا من بطء الدعم الفني.",
      recommendations="مهاجمة نقطتي الأداء والدعم مباشرة في العروض. تقديم ترحيل مجاني للبيانات من Zoho. "
                      "نشر مقارنة أداء موثقة في مواد التسويق."),
 dict(title="دراسة تسعير: استعداد الدفع لدى الشركات المتوسطة", type="Pricing Study", status="Completed",
      segment="Mid-Market", region="GCC", market_size=780000000, growth_rate=16.5, our_share=1.4,
      budget=15000, confidence="Medium", source="استبيان 240 شركة", start_date=d(-70), end_date=d(-20),
      findings="متوسط الاستعداد للدفع 38 دولاراً لكل مستخدم شهرياً. النقطة الحرجة عند 50 دولاراً حيث ينخفض التحويل 62%. "
               "74% يفضلون الدفع السنوي مقابل خصم 15%+. الفوترة والمخزون المدمجان يرفعان الاستعداد للدفع بنسبة 22%.",
      recommendations="تثبيت السعر عند 35-42 دولاراً للمستخدم شهرياً. تقديم خصم سنوي 18%. "
                      "تسويق الفوترة والمخزون كميزة مميزة لا كإضافة."),
 dict(title="مراجعة الفوز والخسارة — الربع الماضي", type="Win/Loss Review", status="Completed",
      segment="All", region="MENA", budget=5000, confidence="High", source="مقابلات 34 صفقة مغلقة",
      start_date=d(-45), end_date=d(-10),
      findings="خسرنا 61% من الصفقات المفقودة بسبب السعر، و24% بسبب فجوات في الميزات. "
               "فزنا أساساً بسبب سرعة التنفيذ (44%) وجودة التعريب (29%). "
               "في الصفقات ضد Salesforce فزنا 58% عندما كان حجم الشركة أقل من 200 موظف.",
      recommendations="إطلاق مستوى تسعير تنافسي للشركات الحساسة للسعر. "
                      "تدريب المندوبين على بطاقات المواجهة. التركيز على الشركات دون 200 موظف ضد Salesforce."),
 dict(title="اتجاهات الذكاء الاصطناعي في CRM 2026", type="Trend Analysis", status="In Progress",
      segment="Enterprise", region="Global", growth_rate=31.0, budget=12000, confidence="Medium",
      source="تقارير محللين + رصد المنافسين", start_date=d(-25), end_date=d(35),
      findings="جميع المنافسين الرئيسيين أطلقوا مساعدات ذكاء اصطناعي: Einstein و Zia و Copilot و Freddy. "
               "68% من المشترين يعتبرون الذكاء الاصطناعي عاملاً مؤثراً في القرار، لكن 41% فقط يستخدمونه فعلياً بعد الشراء.",
      recommendations="أولوية عالية لبناء مساعد ذكي: تسجيل نقاط العملاء المحتملين وتلخيص المحادثات والتنبؤ بالإغلاق."),
 dict(title="رضا العملاء ومعدل الفقد", type="Customer Survey", status="In Progress", segment="All",
      region="MENA", budget=6000, confidence="Medium", source="استبيان NPS", start_date=d(-15), end_date=d(20),
      findings="جارية — النتائج الأولية تشير إلى NPS = 44 مقابل متوسط القطاع 31.",
      recommendations="بانتظار اكتمال البيانات."),
 dict(title="تحليل SWOT لموقعنا التنافسي", type="SWOT", status="Completed", segment="All", region="MENA",
      budget=3000, confidence="High", source="ورشة عمل داخلية", start_date=d(-55), end_date=d(-48),
      findings="القوة: تعريب أصلي · سرعة تنفيذ · سعر متوازن · وحدات متكاملة. "
               "الضعف: علامة تجارية غير معروفة · منظومة شركاء صغيرة · لا ذكاء اصطناعي بعد. "
               "الفرص: 43% من السوق غير مخدوم · تحول رقمي حكومي · استياء من أسعار Salesforce. "
               "التهديدات: Zoho يخفض الأسعار · دخول لاعبين إقليميين · اعتماد المشترين على العلامات العالمية.",
      recommendations="الاستثمار في بناء العلامة وقصص نجاح موثقة. تسريع خارطة طريق الذكاء الاصطناعي. "
                      "برنامج شركاء بعمولة 20%."),
 dict(title="فرصة السوق: القطاع الحكومي", type="Market Sizing", status="Planned", segment="Enterprise",
      region="Yemen & GCC", market_size=310000000, growth_rate=9.5, budget=18000, confidence="Low",
      source="مناقصات منشورة", start_date=d(10), end_date=d(90),
      findings="لم تبدأ بعد.", recommendations="—"),
]
for st in STUDIES:
    ins("market_research", **st)

# link existing closed deals to competitors for win/loss analytics
REASONS = ["Price", "Features", "Relationship", "Timing", "Brand", "Support"]
clist = list(cids.values())
weights = [9, 10, 8, 9, 6, 6, 7, 5]
n = 0
for dl in con.execute("SELECT id,stage FROM deals WHERE deleted=0"):
    if random.random() < 0.72:
        cid = random.choices(clist, weights=weights)[0]
        upd = {"competitor_id": cid}
        if dl["stage"] == "Closed Lost":
            upd["loss_reason"] = random.choices(REASONS, [6, 3, 1, 2, 2, 1])[0]
        elif dl["stage"] == "Closed Won":
            upd["loss_reason"] = random.choices(REASONS, [2, 4, 4, 2, 1, 3])[0]
        con.execute(f'UPDATE deals SET {",".join(k+"=?" for k in upd)} WHERE id=?',
                    list(upd.values()) + [dl["id"]])
        n += 1

con.commit()
print(f"seeded {len(COMPETITORS)} competitors, {len(PRODUCTS)} competitor products, "
      f"{len(STUDIES)} studies, linked {n} deals")
