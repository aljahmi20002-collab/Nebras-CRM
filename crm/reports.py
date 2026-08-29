"""Reporting centre — every report is printable, exportable and permission-aware.

Design: reports are declared as metadata (source query + columns + filters), so the
UI, the CSV/Excel exporter and the print view are all generated from one definition.
Adding a report is a dict entry, not three new code paths that drift apart.
"""
import io, csv, json, datetime
from typing import Optional
from fastapi import Depends, HTTPException, Response
from fastapi.responses import StreamingResponse
from pydantic import BaseModel

con = None


def _f(v):
    try: return float(v or 0)
    except (TypeError, ValueError): return 0.0


def today():
    return datetime.date.today()


# ---------------------------------------------------------------- catalogue
# Each report: sql + columns [(key, ar, en, type)] ; type drives formatting.
REPORTS = {
    # ---------------- SALES ----------------
    "sales_by_stage": {
        "ar": "المبيعات حسب المرحلة", "en": "Sales by Stage", "group": "sales", "icon": "📊",
        "desc_ar": "توزيع الصفقات وقيمها على مراحل خط المبيعات",
        "sql": """SELECT stage k, COUNT(*) n, COALESCE(SUM(amount),0) v,
                         COALESCE(AVG(amount),0) avg_v, COALESCE(AVG(probability),0) prob
                  FROM deals WHERE deleted=0 {date} GROUP BY stage ORDER BY v DESC""",
        "date_col": "closing_date",
        "cols": [("k", "المرحلة", "Stage", "text"), ("n", "العدد", "Count", "int"),
                 ("v", "القيمة", "Value", "money"), ("avg_v", "المتوسط", "Average", "money"),
                 ("prob", "الاحتمالية %", "Probability %", "pct")],
    },
    "sales_by_owner": {
        "ar": "أداء المندوبين", "en": "Sales by Rep", "group": "sales", "icon": "🏆",
        "desc_ar": "الإيراد المحقق والصفقات لكل مندوب مقابل هدفه",
        "sql": """SELECT u.name k, u.target target,
                    COUNT(CASE WHEN d.stage='Closed Won' THEN 1 END) n,
                    COALESCE(SUM(CASE WHEN d.stage='Closed Won' THEN d.amount END),0) v,
                    COUNT(CASE WHEN d.stage='Closed Lost' THEN 1 END) lost
                  FROM users u LEFT JOIN deals d ON d.owner_id=u.id AND d.deleted=0 {date}
                  WHERE u.active=1 GROUP BY u.id,u.name,u.target ORDER BY v DESC""",
        "date_col": "d.closing_date",
        "cols": [("k", "المندوب", "Rep", "text"), ("n", "صفقات مكسوبة", "Won", "int"),
                 ("lost", "مخسورة", "Lost", "int"), ("v", "الإيراد", "Revenue", "money"),
                 ("target", "الهدف", "Target", "money"), ("ach", "الإنجاز %", "Achieved %", "pct")],
        "derive": lambda r: {**r, "ach": round(_f(r["v"]) / _f(r["target"]) * 100, 1) if _f(r["target"]) else 0},
    },
    "win_loss": {
        "ar": "تحليل الفوز والخسارة", "en": "Win/Loss Analysis", "group": "sales", "icon": "⚖️",
        "desc_ar": "أسباب كسب وخسارة الصفقات بالقيمة والعدد",
        "sql": """SELECT COALESCE(loss_reason,'غير محدد') k,
                    COUNT(CASE WHEN stage='Closed Won' THEN 1 END) won,
                    COUNT(CASE WHEN stage='Closed Lost' THEN 1 END) lost,
                    COALESCE(SUM(CASE WHEN stage='Closed Lost' THEN amount END),0) lost_v,
                    COALESCE(SUM(CASE WHEN stage='Closed Won' THEN amount END),0) won_v
                  FROM deals WHERE deleted=0 AND stage IN ('Closed Won','Closed Lost') {date}
                  GROUP BY COALESCE(loss_reason,'غير محدد') ORDER BY lost DESC""",
        "date_col": "closing_date",
        "cols": [("k", "السبب", "Reason", "text"), ("won", "فوز", "Won", "int"),
                 ("lost", "خسارة", "Lost", "int"), ("won_v", "قيمة الفوز", "Won value", "money"),
                 ("lost_v", "قيمة الخسارة", "Lost value", "money")],
    },
    "pipeline_forecast": {
        "ar": "خط المبيعات المتوقع", "en": "Pipeline Forecast", "group": "sales", "icon": "🔮",
        "desc_ar": "الصفقات المفتوحة وقيمتها المرجّحة حسب شهر الإغلاق",
        "sql": """SELECT substr(closing_date,1,7) k, COUNT(*) n,
                    COALESCE(SUM(amount),0) v,
                    COALESCE(SUM(amount*COALESCE(probability,0)/100.0),0) weighted
                  FROM deals WHERE deleted=0 AND stage NOT IN ('Closed Won','Closed Lost')
                    AND closing_date IS NOT NULL {date} GROUP BY substr(closing_date,1,7) ORDER BY k""",
        "date_col": "closing_date",
        "cols": [("k", "الشهر", "Month", "text"), ("n", "الصفقات", "Deals", "int"),
                 ("v", "القيمة الكاملة", "Full value", "money"),
                 ("weighted", "القيمة المرجّحة", "Weighted", "money")],
    },
    "lead_source": {
        "ar": "فعالية مصادر العملاء", "en": "Lead Source Effectiveness", "group": "sales", "icon": "🎯",
        "desc_ar": "عدد العملاء المحتملين ونسبة التحويل لكل مصدر",
        "sql": """SELECT COALESCE(source,'غير محدد') k, COUNT(*) n,
                    COUNT(CASE WHEN status='Converted' THEN 1 END) conv,
                    COUNT(CASE WHEN status='Qualified' THEN 1 END) qual
                  FROM leads WHERE deleted=0 {date} GROUP BY COALESCE(source,'غير محدد') ORDER BY n DESC""",
        "date_col": "created_at",
        "cols": [("k", "المصدر", "Source", "text"), ("n", "العدد", "Leads", "int"),
                 ("qual", "مؤهل", "Qualified", "int"), ("conv", "محوّل", "Converted", "int"),
                 ("rate", "نسبة التحويل %", "Conversion %", "pct")],
        "derive": lambda r: {**r, "rate": round(r["conv"] / r["n"] * 100, 1) if r["n"] else 0},
    },

    # ---------------- FINANCE ----------------
    "ar_aging": {
        "ar": "أعمار الذمم المدينة", "en": "Accounts Receivable Aging", "group": "finance", "icon": "⏳",
        "desc_ar": "الفواتير غير المسددة موزّعة على فترات التأخير",
        "custom": "ar_aging",
        "cols": [("k", "العميل", "Customer", "text"),
                 ("cur", "جارية", "Current", "money"), ("d30", "1-30 يوم", "1-30", "money"),
                 ("d60", "31-60 يوم", "31-60", "money"), ("d90", "61-90 يوم", "61-90", "money"),
                 ("d90p", "+90 يوم", "90+", "money"), ("total", "الإجمالي", "Total", "money")],
    },
    "revenue_monthly": {
        "ar": "الإيرادات الشهرية", "en": "Monthly Revenue", "group": "finance", "icon": "💰",
        "desc_ar": "الإيراد المحقق والمحصّل شهرياً",
        "sql": """SELECT substr(invoice_date,1,7) k, COUNT(*) n,
                    COALESCE(SUM(amount),0) billed,
                    COALESCE(SUM(paid_amount),0) collected,
                    COALESCE(SUM(amount)-SUM(paid_amount),0) outstanding
                  FROM invoices WHERE deleted=0 AND status!='Cancelled'
                    AND invoice_date IS NOT NULL {date} GROUP BY substr(invoice_date,1,7) ORDER BY k DESC""",
        "date_col": "invoice_date",
        "cols": [("k", "الشهر", "Month", "text"), ("n", "الفواتير", "Invoices", "int"),
                 ("billed", "المفوتر", "Billed", "money"),
                 ("collected", "المحصّل", "Collected", "money"),
                 ("outstanding", "المتبقي", "Outstanding", "money")],
    },
    "payments_by_channel": {
        "ar": "المدفوعات حسب القناة", "en": "Payments by Channel", "group": "finance", "icon": "💳",
        "desc_ar": "المبالغ المحصّلة والرسوم والصافي لكل قناة دفع",
        "sql": """SELECT COALESCE(method,channel,'غير محدد') k, COUNT(*) n,
                    COALESCE(SUM(amount),0) v, COALESCE(SUM(fee),0) fees,
                    COALESCE(SUM(net),0) net
                  FROM payments WHERE status='paid' {date} GROUP BY COALESCE(method,channel,'غير محدد') ORDER BY v DESC""",
        "date_col": "paid_at",
        "cols": [("k", "القناة", "Channel", "text"), ("n", "العمليات", "Count", "int"),
                 ("v", "الإجمالي", "Gross", "money"), ("fees", "الرسوم", "Fees", "money"),
                 ("net", "الصافي", "Net", "money")],
    },
    "tax_summary": {
        "ar": "ملخص الضرائب", "en": "Tax Summary", "group": "finance", "icon": "🧾",
        "desc_ar": "الضريبة المحصّلة من بنود الفواتير",
        "sql": """SELECT substr(i.invoice_date,1,7) k, COUNT(DISTINCT i.id) n,
                    COALESCE(SUM(li.qty*li.price*(1-li.discount/100.0)),0) base,
                    COALESCE(SUM(li.qty*li.price*(1-li.discount/100.0)*li.tax/100.0),0) tax
                  FROM invoices i JOIN line_items li ON li.module='invoices' AND li.record_id=i.id
                  WHERE i.deleted=0 AND i.status!='Cancelled' AND i.invoice_date IS NOT NULL {date}
                  GROUP BY substr(i.invoice_date,1,7) ORDER BY k DESC""",
        "date_col": "i.invoice_date",
        "cols": [("k", "الشهر", "Month", "text"), ("n", "الفواتير", "Invoices", "int"),
                 ("base", "الوعاء", "Taxable base", "money"), ("tax", "الضريبة", "Tax", "money")],
    },

    # ---------------- CUSTOMERS ----------------
    "customer_ranking": {
        "ar": "ترتيب العملاء بالإيراد", "en": "Top Customers", "group": "customers", "icon": "👑",
        "desc_ar": "أعلى العملاء إيراداً مع مستحقاتهم وشريحتهم",
        "sql": """SELECT a.name k, a.segment seg, a.list_tag tag,
                    COALESCE((SELECT SUM(d.amount) FROM deals d WHERE d.deleted=0
                      AND d.stage='Closed Won' AND CAST(d.account_id AS INTEGER)=a.id),0) v,
                    COALESCE((SELECT SUM(COALESCE(i.amount,0)-COALESCE(i.paid_amount,0))
                      FROM invoices i WHERE i.deleted=0 AND CAST(i.account_id AS INTEGER)=a.id
                      AND i.status NOT IN ('Paid','Cancelled')),0) due
                  FROM accounts a WHERE a.deleted=0 ORDER BY v DESC LIMIT 100""",
        "cols": [("k", "العميل", "Customer", "text"), ("seg", "الشريحة", "Segment", "text"),
                 ("tag", "القائمة", "List", "text"), ("v", "الإيراد", "Revenue", "money"),
                 ("due", "مستحقات", "Outstanding", "money")],
    },
    "customer_segments": {
        "ar": "توزيع شرائح العملاء", "en": "Customer Segments", "group": "customers", "icon": "🏅",
        "desc_ar": "عدد العملاء وإيرادهم لكل شريحة نشاط",
        "sql": """SELECT COALESCE(a.segment,'غير مصنّف') k, COUNT(DISTINCT a.id) n,
                    COALESCE(SUM(CASE WHEN d.stage='Closed Won' THEN d.amount ELSE 0 END),0) v
                  FROM accounts a
                  LEFT JOIN deals d ON d.deleted=0 AND d.stage='Closed Won'
                    AND CAST(d.account_id AS INTEGER)=a.id
                  WHERE a.deleted=0
                  GROUP BY COALESCE(a.segment,'غير مصنّف') ORDER BY v DESC""",
        "cols": [("k", "الشريحة", "Segment", "text"), ("n", "العملاء", "Customers", "int"),
                 ("v", "الإيراد", "Revenue", "money")],
    },
    "geo_performance": {
        "ar": "الأداء حسب الدولة", "en": "Performance by Country", "group": "customers", "icon": "🗺️",
        "desc_ar": "العملاء والإيراد موزّعون حسب الدولة",
        "sql": """SELECT g.name_ar k, COUNT(DISTINCT a.id) n,
                    COALESCE(SUM(CASE WHEN d.stage='Closed Won' THEN d.amount ELSE 0 END),0) v
                  FROM geo_governorates g
                  LEFT JOIN accounts a ON CAST(a.gov_id AS INTEGER)=g.id AND a.deleted=0
                  LEFT JOIN deals d ON d.deleted=0 AND d.stage='Closed Won'
                    AND CAST(d.account_id AS INTEGER)=a.id
                  GROUP BY g.id,g.name_ar HAVING COUNT(a.id)>0 ORDER BY v DESC""",
        "cols": [("k", "الدولة", "Country", "text"), ("n", "العملاء", "Customers", "int"),
                 ("v", "الإيراد", "Revenue", "money")],
    },

    # ---------------- INVENTORY ----------------
    "product_performance": {
        "ar": "أداء المنتجات", "en": "Product Performance", "group": "inventory", "icon": "📦",
        "desc_ar": "الكميات المباعة والإيراد لكل منتج",
        "sql": """SELECT p.name k, p.category cat, p.qty_in_stock stock,
                    COALESCE(SUM(CASE WHEN i.id IS NOT NULL THEN li.qty ELSE 0 END),0) sold,
                    COALESCE(SUM(CASE WHEN i.id IS NOT NULL THEN li.qty*li.price ELSE 0 END),0) v
                  FROM products p
                  LEFT JOIN line_items li ON li.product_id=p.id AND li.module='invoices'
                  LEFT JOIN invoices i ON i.id=li.record_id AND i.deleted=0
                     AND i.status NOT IN ('Draft','Cancelled')
                  WHERE p.deleted=0
                  GROUP BY p.id,p.name,p.category,p.qty_in_stock ORDER BY v DESC""",
        "cols": [("k", "المنتج", "Product", "text"), ("cat", "الفئة", "Category", "text"),
                 ("sold", "المباع", "Sold", "int"), ("stock", "المخزون", "Stock", "int"),
                 ("v", "الإيراد", "Revenue", "money")],
    },
    "stock_valuation": {
        "ar": "تقييم المخزون", "en": "Stock Valuation", "group": "inventory", "icon": "🏷️",
        "desc_ar": "قيمة المخزون بالتكلفة وسعر البيع",
        "sql": """SELECT name k, category cat, qty_in_stock qty,
                    COALESCE(cost,0) cost, COALESCE(unit_price,0) price,
                    COALESCE(qty_in_stock*cost,0) cost_val,
                    COALESCE(qty_in_stock*unit_price,0) retail_val
                  FROM products WHERE deleted=0 AND qty_in_stock>0 ORDER BY cost_val DESC""",
        "cols": [("k", "المنتج", "Product", "text"), ("cat", "الفئة", "Category", "text"),
                 ("qty", "الكمية", "Qty", "int"), ("cost", "التكلفة", "Cost", "money"),
                 ("cost_val", "قيمة التكلفة", "Cost value", "money"),
                 ("retail_val", "قيمة البيع", "Retail value", "money")],
    },

    # ---------------- SUPPORT ----------------
    "ticket_summary": {
        "ar": "ملخص تذاكر الدعم", "en": "Support Tickets Summary", "group": "support", "icon": "🎫",
        "desc_ar": "التذاكر حسب الحالة والأولوية",
        "sql": """SELECT status k, COUNT(*) n,
                    COUNT(CASE WHEN priority IN ('High','Urgent') THEN 1 END) urgent,
                    COUNT(CASE WHEN due_date < date('now') AND status!='Closed' THEN 1 END) overdue
                  FROM tickets WHERE deleted=0 {date} GROUP BY status ORDER BY n DESC""",
        "date_col": "created_at",
        "cols": [("k", "الحالة", "Status", "text"), ("n", "العدد", "Count", "int"),
                 ("urgent", "عاجلة", "Urgent", "int"), ("overdue", "متأخرة", "Overdue", "int")],
    },
    "agent_commissions": {
        "ar": "عمولات الوكلاء", "en": "Partner Commissions", "group": "partners", "icon": "🤝",
        "desc_ar": "المستحق والمصروف والرصيد لكل شريك",
        "sql": """SELECT a.name k, a.type typ,
                    COALESCE(SUM(CASE WHEN t.kind IN ('commission','bonus','adjustment')
                      THEN t.amount END),0) earned,
                    COALESCE(SUM(CASE WHEN t.kind IN ('payout','deduction','advance','penalty')
                      THEN t.amount END),0) paid
                  FROM agents a LEFT JOIN agent_txn t ON t.agent_id=a.id
                  WHERE a.deleted=0 GROUP BY a.id,a.name,a.type ORDER BY earned DESC""",
        "cols": [("k", "الشريك", "Partner", "text"), ("typ", "النوع", "Type", "text"),
                 ("earned", "المستحق", "Earned", "money"), ("paid", "المصروف", "Paid", "money"),
                 ("bal", "الرصيد", "Balance", "money")],
        "derive": lambda r: {**r, "bal": round(_f(r["earned"]) - _f(r["paid"]), 2)},
    },
    "activity_log": {
        "ar": "سجل نشاط المستخدمين", "en": "User Activity Log", "group": "system", "icon": "📋",
        "desc_ar": "عدد العمليات لكل مستخدم حسب النوع",
        "sql": """SELECT COALESCE(u.name,'النظام') k, COUNT(*) n,
                    COUNT(CASE WHEN a.action='create' THEN 1 END) created,
                    COUNT(CASE WHEN a.action='update' THEN 1 END) updated,
                    COUNT(CASE WHEN a.action='delete' THEN 1 END) deleted
                  FROM audit a LEFT JOIN users u ON u.id=a.user_id
                  WHERE 1=1 {date} GROUP BY a.user_id,u.name ORDER BY n DESC""",
        "date_col": "a.created_at",
        "cols": [("k", "المستخدم", "User", "text"), ("n", "الإجمالي", "Total", "int"),
                 ("created", "إضافة", "Created", "int"), ("updated", "تعديل", "Updated", "int"),
                 ("deleted", "حذف", "Deleted", "int")],
        "admin_only": True,
    },
}

GROUPS = {
    "sales": {"ar": "المبيعات", "en": "Sales", "icon": "💰"},
    "finance": {"ar": "المالية", "en": "Finance", "icon": "🧾"},
    "customers": {"ar": "العملاء", "en": "Customers", "icon": "👥"},
    "inventory": {"ar": "المخزون", "en": "Inventory", "icon": "📦"},
    "support": {"ar": "الدعم", "en": "Support", "icon": "🎫"},
    "partners": {"ar": "الشركاء", "en": "Partners", "icon": "🤝"},
    "system": {"ar": "النظام", "en": "System", "icon": "⚙️"},
}


def ar_aging():
    """Receivables bucketed by how overdue they are."""
    rows = {}
    t = today()
    for r in con.execute("""SELECT i.id, i.amount, i.paid_amount, i.due_date,
                              COALESCE(a.name,'—') acc
                            FROM invoices i
                            LEFT JOIN accounts a ON a.id=CAST(i.account_id AS INTEGER)
                            WHERE i.deleted=0 AND i.status NOT IN ('Paid','Cancelled')"""):
        bal = _f(r["amount"]) - _f(r["paid_amount"])
        if bal <= 0.01:
            continue
        d = rows.setdefault(r["acc"], {"k": r["acc"], "cur": 0.0, "d30": 0.0,
                                       "d60": 0.0, "d90": 0.0, "d90p": 0.0, "total": 0.0})
        days = 0
        if r["due_date"]:
            try:
                days = (t - datetime.date.fromisoformat(str(r["due_date"])[:10])).days
            except Exception:
                days = 0
        bucket = ("cur" if days <= 0 else "d30" if days <= 30 else
                  "d60" if days <= 60 else "d90" if days <= 90 else "d90p")
        d[bucket] += bal
        d["total"] += bal
    out = sorted(rows.values(), key=lambda x: -x["total"])
    return [{k: (round(v, 2) if isinstance(v, float) else v) for k, v in r.items()} for r in out]


def run_report(code, date_from="", date_to=""):
    rep = REPORTS.get(code)
    if not rep:
        raise HTTPException(404, "Unknown report")
    if rep.get("custom") == "ar_aging":
        rows = ar_aging()
    else:
        clause, params = "", []
        if (date_from or date_to) and rep.get("date_col"):
            c = rep["date_col"]
            if date_from:
                clause += f" AND {c} >= ?"; params.append(date_from)
            if date_to:
                clause += f" AND {c} <= ?"; params.append(date_to)
        sql = rep["sql"].replace("{date}", clause)
        rows = [dict(r) for r in con.execute(sql, params)]
        if rep.get("derive"):
            rows = [rep["derive"](r) for r in rows]
    # totals for numeric columns
    totals = {}
    for key, _ar, _en, typ in rep["cols"]:
        if typ in ("money", "int"):
            totals[key] = round(sum(_f(r.get(key)) for r in rows), 2)
    return {"code": code, "meta": {k: v for k, v in rep.items()
                                   if k not in ("sql", "derive", "custom")},
            "rows": rows, "totals": totals, "count": len(rows),
            "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "period": {"from": date_from, "to": date_to}}


def register(app, current_user, require):

    @app.get("/api/reports/catalogue")
    def catalogue(user=Depends(current_user)):
        require(user, "admin", "manager")
        out = []
        for code, r in REPORTS.items():
            if r.get("admin_only") and user["role"] != "admin":
                continue
            out.append({"code": code, "ar": r["ar"], "en": r["en"], "group": r["group"],
                        "icon": r["icon"], "desc_ar": r.get("desc_ar", ""),
                        "has_date": bool(r.get("date_col")),
                        "cols": [{"key": c[0], "ar": c[1], "en": c[2], "type": c[3]}
                                 for c in r["cols"]]})
        return {"reports": out, "groups": GROUPS}

    @app.get("/api/reports/run/{code}")
    def run(code: str, date_from: str = "", date_to: str = "", user=Depends(current_user)):
        require(user, "admin", "manager")
        rep = REPORTS.get(code)
        if rep and rep.get("admin_only") and user["role"] != "admin":
            raise HTTPException(403, "Admins only")
        return run_report(code, date_from, date_to)

    @app.get("/api/reports/export/{code}.{fmt}")
    def export(code: str, fmt: str, date_from: str = "", date_to: str = "",
               lang: str = "ar", user=Depends(current_user)):
        """CSV / Excel-compatible export authenticated with the bearer header."""
        require(user, "admin", "manager")
        rep = REPORTS.get(code)
        if not rep:
            raise HTTPException(404, "Unknown report")
        if rep.get("admin_only") and user["role"] != "admin":
            raise HTTPException(403, "Admins only")
        data = run_report(code, date_from, date_to)
        cols = rep["cols"]
        head = [(c[1] if lang == "ar" else c[2]) for c in cols]

        if fmt == "csv":
            buf = io.StringIO()
            w = csv.writer(buf)
            w.writerow([rep["ar"] if lang == "ar" else rep["en"]])
            if date_from or date_to:
                w.writerow([f"{date_from or '—'} → {date_to or '—'}"])
            w.writerow([])
            w.writerow(head)
            for r in data["rows"]:
                w.writerow([r.get(c[0], "") for c in cols])
            if data["totals"]:
                w.writerow([])
                w.writerow(["الإجمالي" if lang == "ar" else "TOTAL"] +
                           [data["totals"].get(c[0], "") for c in cols[1:]])
            # BOM so Excel opens Arabic correctly
            out = "\ufeff" + buf.getvalue()
            return StreamingResponse(iter([out]), media_type="text/csv; charset=utf-8",
                headers={"Content-Disposition": f'attachment; filename="{code}.csv"'})

        if fmt == "xls":
            # SpreadsheetML: opens natively in Excel with real columns, no deps
            def esc(v):
                return (str(v).replace("&", "&amp;").replace("<", "&lt;")
                        .replace(">", "&gt;").replace('"', "&quot;"))
            rws = []
            rws.append("<Row>" + "".join(
                f'<Cell ss:StyleID="h"><Data ss:Type="String">{esc(h)}</Data></Cell>'
                for h in head) + "</Row>")
            for r in data["rows"]:
                cells = []
                for key, _a, _e, typ in cols:
                    v = r.get(key, "")
                    if typ in ("money", "int", "pct"):
                        cells.append(f'<Cell><Data ss:Type="Number">{_f(v)}</Data></Cell>')
                    else:
                        cells.append(f'<Cell><Data ss:Type="String">{esc(v)}</Data></Cell>')
                rws.append("<Row>" + "".join(cells) + "</Row>")
            if data["totals"]:
                cells = [f'<Cell ss:StyleID="t"><Data ss:Type="String">'
                         f'{"الإجمالي" if lang=="ar" else "TOTAL"}</Data></Cell>']
                for key, _a, _e, typ in cols[1:]:
                    v = data["totals"].get(key, "")
                    cells.append(f'<Cell ss:StyleID="t"><Data ss:Type="Number">{_f(v)}</Data></Cell>'
                                 if v != "" else '<Cell ss:StyleID="t"/>')
                rws.append("<Row>" + "".join(cells) + "</Row>")
            xml = f'''<?xml version="1.0" encoding="UTF-8"?>
<?mso-application progid="Excel.Sheet"?>
<Workbook xmlns="urn:schemas-microsoft-com:office:spreadsheet"
 xmlns:ss="urn:schemas-microsoft-com:office:spreadsheet">
<Styles>
 <Style ss:ID="h"><Font ss:Bold="1" ss:Color="#FFFFFF"/>
  <Interior ss:Color="#2B4ACB" ss:Pattern="Solid"/></Style>
 <Style ss:ID="t"><Font ss:Bold="1"/>
  <Interior ss:Color="#EEF2F8" ss:Pattern="Solid"/></Style>
</Styles>
<Worksheet ss:Name="{esc((rep['ar'] if lang=='ar' else rep['en'])[:28])}">
<Table>{''.join(rws)}</Table>
</Worksheet></Workbook>'''
            return Response(content=xml.encode("utf-8"),
                media_type="application/vnd.ms-excel",
                headers={"Content-Disposition": f'attachment; filename="{code}.xls"'})

        if fmt == "json":
            return Response(content=json.dumps(data, ensure_ascii=False, indent=2),
                media_type="application/json",
                headers={"Content-Disposition": f'attachment; filename="{code}.json"'})

        raise HTTPException(400, "Unsupported format (csv | xls | json)")

    # ---------------- system settings ----------------
    SETTING_DEFS = [
        ("company_name", "اسم الشركة", "Company name", "text", "general"),
        ("company_phone", "هاتف الشركة", "Company phone", "text", "general"),
        ("company_address", "عنوان الشركة", "Company address", "text", "general"),
        ("tax_number", "الرقم الضريبي", "Tax number", "text", "general"),
        ("base_url", "رابط النظام", "System URL", "text", "general"),
        ("currency", "العملة", "Currency", "select:USD,YER,SAR,AED,EUR", "finance"),
        ("tax_rate", "نسبة الضريبة %", "Default tax %", "number", "finance"),
        ("invoice_prefix", "بادئة الفواتير", "Invoice prefix", "text", "finance"),
        ("payment_terms_days", "مهلة السداد (يوم)", "Payment terms (days)", "number", "finance"),
        ("fiscal_year_start", "بداية السنة المالية", "Fiscal year start", "text", "finance"),
        ("email_provider", "مزود الإرسال", "Email provider", "select:sandbox,resend,smtp", "email"),
        ("resend_api_key", "مفتاح Resend API", "Resend API key", "password", "email"),
        ("resend_from", "عنوان Resend المعتمد", "Verified Resend From address", "text", "email"),
        ("resend_reply_to", "الرد إلى", "Resend reply-to", "text", "email"),
        ("smtp_host", "خادم البريد", "SMTP host", "text", "email"),
        ("smtp_port", "المنفذ", "SMTP port", "number", "email"),
        ("smtp_user", "المستخدم", "SMTP user", "text", "email"),
        ("smtp_pass", "كلمة المرور", "SMTP password", "password", "email"),
        ("smtp_from", "المرسل", "From address", "text", "email"),
        ("smtp_tls", "تشفير TLS", "TLS", "select:1,0", "email"),
        ("pos_require_session", "إلزام فتح وردية في نقطة البيع", "Require POS shift", "select:1,0", "sales"),
        ("pos_allow_negative_stock", "السماح بمخزون سالب في نقطة البيع", "Allow negative POS stock", "select:1,0", "sales"),
        ("openai_key", "مفتاح الذكاء الاصطناعي", "AI API key", "password", "ai"),
        ("openai_model", "النموذج", "Model", "text", "ai"),
        ("lead_auto_assign", "توزيع العملاء تلقائياً", "Auto-assign leads", "select:1,0", "sales"),
        ("deal_stale_days", "أيام ركود الصفقة", "Deal stale after (days)", "number", "sales"),
        ("loyalty_enabled", "تفعيل برنامج الولاء", "Loyalty enabled", "select:1,0", "sales"),
    ]
    SETTING_GROUPS = {
        "general": {"ar": "عام", "en": "General", "icon": "🏢"},
        "finance": {"ar": "المالية", "en": "Finance", "icon": "💰"},
        "email": {"ar": "البريد", "en": "Email", "icon": "✉️"},
        "ai": {"ar": "الذكاء الاصطناعي", "en": "AI", "icon": "🤖"},
        "sales": {"ar": "المبيعات", "en": "Sales", "icon": "📊"},
    }

    @app.get("/api/settings/all")
    def all_settings(user=Depends(current_user)):
        require(user, "admin", "manager")
        cur = {r["key"]: r["value"] for r in con.execute("SELECT \"key\",\"value\" FROM settings")}
        out = []
        for key, ar, en, typ, grp in SETTING_DEFS:
            v = cur.get(key, "")
            if typ == "password" and v:
                v = "••••"
            out.append({"key": key, "ar": ar, "en": en, "type": typ, "group": grp, "value": v})
        return {"settings": out, "groups": SETTING_GROUPS}

    @app.put("/api/settings/all")
    def save_settings(body: dict, user=Depends(current_user)):
        require(user, "admin")
        import db as D
        valid = {k for k, *_ in SETTING_DEFS}
        n = 0
        for k, v in body.items():
            if k not in valid:
                continue
            if v == "••••":          # untouched password field
                continue
            con.execute("""INSERT INTO settings(\"key\",\"value\") VALUES(?,?)
                ON CONFLICT(\"key\") DO UPDATE SET \"value\"=excluded.\"value\"""", (k, str(v)))
            n += 1
        D.log(con, "settings", 0, "update", {"keys": list(body.keys())}, user["id"])
        con.commit()
        return {"ok": True, "updated": n}
