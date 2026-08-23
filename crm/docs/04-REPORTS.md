# مرجع التقارير — NebrasCRM

**17 تقريراً** موزعة على 7 مجموعات. كل تقرير قابل للطباعة والتصدير (CSV · Excel · JSON).

---

## 💰 المبيعات — Sales

### 📊 المبيعات حسب المرحلة
`sales_by_stage` · *Sales by Stage*

> توزيع الصفقات وقيمها على مراحل خط المبيعات

| العمود | Column | النوع |
|---|---|---|
| المرحلة | Stage | نص |
| العدد | Count | عدد |
| القيمة | Value | مبلغ |
| المتوسط | Average | مبلغ |
| الاحتمالية % | Probability % | نسبة |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/sales_by_stage.csv` · `.xls` · `.json`

### 🏆 أداء المندوبين
`sales_by_owner` · *Sales by Rep*

> الإيراد المحقق والصفقات لكل مندوب مقابل هدفه

| العمود | Column | النوع |
|---|---|---|
| المندوب | Rep | نص |
| صفقات مكسوبة | Won | عدد |
| مخسورة | Lost | عدد |
| الإيراد | Revenue | مبلغ |
| الهدف | Target | مبلغ |
| الإنجاز % | Achieved % | نسبة |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/sales_by_owner.csv` · `.xls` · `.json`

### ⚖️ تحليل الفوز والخسارة
`win_loss` · *Win/Loss Analysis*

> أسباب كسب وخسارة الصفقات بالقيمة والعدد

| العمود | Column | النوع |
|---|---|---|
| السبب | Reason | نص |
| فوز | Won | عدد |
| خسارة | Lost | عدد |
| قيمة الفوز | Won value | مبلغ |
| قيمة الخسارة | Lost value | مبلغ |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/win_loss.csv` · `.xls` · `.json`

### 🔮 خط المبيعات المتوقع
`pipeline_forecast` · *Pipeline Forecast*

> الصفقات المفتوحة وقيمتها المرجّحة حسب شهر الإغلاق

| العمود | Column | النوع |
|---|---|---|
| الشهر | Month | نص |
| الصفقات | Deals | عدد |
| القيمة الكاملة | Full value | مبلغ |
| القيمة المرجّحة | Weighted | مبلغ |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/pipeline_forecast.csv` · `.xls` · `.json`

### 🎯 فعالية مصادر العملاء
`lead_source` · *Lead Source Effectiveness*

> عدد العملاء المحتملين ونسبة التحويل لكل مصدر

| العمود | Column | النوع |
|---|---|---|
| المصدر | Source | نص |
| العدد | Leads | عدد |
| مؤهل | Qualified | عدد |
| محوّل | Converted | عدد |
| نسبة التحويل % | Conversion % | نسبة |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/lead_source.csv` · `.xls` · `.json`

## 🧾 المالية — Finance

### ⏳ أعمار الذمم المدينة
`ar_aging` · *Accounts Receivable Aging*

> الفواتير غير المسددة موزّعة على فترات التأخير

| العمود | Column | النوع |
|---|---|---|
| العميل | Customer | نص |
| جارية | Current | مبلغ |
| 1-30 يوم | 1-30 | مبلغ |
| 31-60 يوم | 31-60 | مبلغ |
| 61-90 يوم | 61-90 | مبلغ |
| +90 يوم | 90+ | مبلغ |
| الإجمالي | Total | مبلغ |

**فلتر التاريخ:** — غير متاح

**تصدير:** `/api/reports/export/ar_aging.csv` · `.xls` · `.json`

### 💰 الإيرادات الشهرية
`revenue_monthly` · *Monthly Revenue*

> الإيراد المحقق والمحصّل شهرياً

| العمود | Column | النوع |
|---|---|---|
| الشهر | Month | نص |
| الفواتير | Invoices | عدد |
| المفوتر | Billed | مبلغ |
| المحصّل | Collected | مبلغ |
| المتبقي | Outstanding | مبلغ |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/revenue_monthly.csv` · `.xls` · `.json`

### 💳 المدفوعات حسب القناة
`payments_by_channel` · *Payments by Channel*

> المبالغ المحصّلة والرسوم والصافي لكل قناة دفع

| العمود | Column | النوع |
|---|---|---|
| القناة | Channel | نص |
| العمليات | Count | عدد |
| الإجمالي | Gross | مبلغ |
| الرسوم | Fees | مبلغ |
| الصافي | Net | مبلغ |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/payments_by_channel.csv` · `.xls` · `.json`

### 🧾 ملخص الضرائب
`tax_summary` · *Tax Summary*

> الضريبة المحصّلة من بنود الفواتير

| العمود | Column | النوع |
|---|---|---|
| الشهر | Month | نص |
| الفواتير | Invoices | عدد |
| الوعاء | Taxable base | مبلغ |
| الضريبة | Tax | مبلغ |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/tax_summary.csv` · `.xls` · `.json`

## 👥 العملاء — Customers

### 👑 ترتيب العملاء بالإيراد
`customer_ranking` · *Top Customers*

> أعلى العملاء إيراداً مع مستحقاتهم وشريحتهم

| العمود | Column | النوع |
|---|---|---|
| العميل | Customer | نص |
| الشريحة | Segment | نص |
| القائمة | List | نص |
| الإيراد | Revenue | مبلغ |
| مستحقات | Outstanding | مبلغ |

**فلتر التاريخ:** — غير متاح

**تصدير:** `/api/reports/export/customer_ranking.csv` · `.xls` · `.json`

### 🏅 توزيع شرائح العملاء
`customer_segments` · *Customer Segments*

> عدد العملاء وإيرادهم لكل شريحة نشاط

| العمود | Column | النوع |
|---|---|---|
| الشريحة | Segment | نص |
| العملاء | Customers | عدد |
| الإيراد | Revenue | مبلغ |

**فلتر التاريخ:** — غير متاح

**تصدير:** `/api/reports/export/customer_segments.csv` · `.xls` · `.json`

### 🗺️ الأداء حسب الدولة
`geo_performance` · *Performance by Country*

> العملاء والإيراد موزّعون حسب الدولة

| العمود | Column | النوع |
|---|---|---|
| الدولة | Country | نص |
| العملاء | Customers | عدد |
| الإيراد | Revenue | مبلغ |

**فلتر التاريخ:** — غير متاح

**تصدير:** `/api/reports/export/geo_performance.csv` · `.xls` · `.json`

## 📦 المخزون — Inventory

### 📦 أداء المنتجات
`product_performance` · *Product Performance*

> الكميات المباعة والإيراد لكل منتج

| العمود | Column | النوع |
|---|---|---|
| المنتج | Product | نص |
| الفئة | Category | نص |
| المباع | Sold | عدد |
| المخزون | Stock | عدد |
| الإيراد | Revenue | مبلغ |

**فلتر التاريخ:** — غير متاح

**تصدير:** `/api/reports/export/product_performance.csv` · `.xls` · `.json`

### 🏷️ تقييم المخزون
`stock_valuation` · *Stock Valuation*

> قيمة المخزون بالتكلفة وسعر البيع

| العمود | Column | النوع |
|---|---|---|
| المنتج | Product | نص |
| الفئة | Category | نص |
| الكمية | Qty | عدد |
| التكلفة | Cost | مبلغ |
| قيمة التكلفة | Cost value | مبلغ |
| قيمة البيع | Retail value | مبلغ |

**فلتر التاريخ:** — غير متاح

**تصدير:** `/api/reports/export/stock_valuation.csv` · `.xls` · `.json`

## 🎫 الدعم — Support

### 🎫 ملخص تذاكر الدعم
`ticket_summary` · *Support Tickets Summary*

> التذاكر حسب الحالة والأولوية

| العمود | Column | النوع |
|---|---|---|
| الحالة | Status | نص |
| العدد | Count | عدد |
| عاجلة | Urgent | عدد |
| متأخرة | Overdue | عدد |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/ticket_summary.csv` · `.xls` · `.json`

## 🤝 الشركاء — Partners

### 🤝 عمولات الوكلاء
`agent_commissions` · *Partner Commissions*

> المستحق والمصروف والرصيد لكل شريك

| العمود | Column | النوع |
|---|---|---|
| الشريك | Partner | نص |
| النوع | Type | نص |
| المستحق | Earned | مبلغ |
| المصروف | Paid | مبلغ |
| الرصيد | Balance | مبلغ |

**فلتر التاريخ:** — غير متاح

**تصدير:** `/api/reports/export/agent_commissions.csv` · `.xls` · `.json`

## ⚙️ النظام — System

### 📋 سجل نشاط المستخدمين
`activity_log` · *User Activity Log*  · **مدير النظام فقط**

> عدد العمليات لكل مستخدم حسب النوع

| العمود | Column | النوع |
|---|---|---|
| المستخدم | User | نص |
| الإجمالي | Total | عدد |
| إضافة | Created | عدد |
| تعديل | Updated | عدد |
| حذف | Deleted | عدد |

**فلتر التاريخ:** ✅ متاح

**تصدير:** `/api/reports/export/activity_log.csv` · `.xls` · `.json`

---

## طريقة الاستخدام

```bash
# تشغيل تقرير
GET /api/reports/run/{code}?date_from=2026-01-01&date_to=2026-12-31

# تصدير (الرمز في الرابط ليعمل من زر تحميل مباشر)
GET /api/reports/export/{code}.csv?date_from=&date_to=&lang=ar&token=...
```

**الاستجابة** تتضمن: `rows` · `totals` (إجمالي كل عمود رقمي) · `count` · `generated_at` · `period`.
