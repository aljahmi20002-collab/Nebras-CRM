"""AI & predictive layer.

Design decision: every model here is a TRANSPARENT, data-driven estimator computed
from the tenant's own CRM history — no external API key required, works offline,
and every prediction ships with the factors that produced it ("why"). An optional
LLM can be plugged in for free-text generation (see llm_complete), but the system
degrades gracefully to high-quality templates when no key is configured.

That matters: a black-box score a rep cannot explain is a score a rep will not trust.
"""
import os, json, math, datetime, statistics, re, urllib.request
from typing import Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel

con = None


def _f(v):
    try: return float(v or 0)
    except (TypeError, ValueError): return 0.0


def today(): return datetime.date.today()


def dsince(s):
    if not s: return None
    try: return (today() - datetime.date.fromisoformat(str(s)[:10])).days
    except Exception: return None


# ---------------------------------------------------------------- LLM (optional)
def llm_ready():
    import mailer as M
    return bool(M.cfg("openai_key", ""))


def llm_complete(prompt, system="You are a concise bilingual (Arabic/English) CRM assistant.",
                 max_tokens=700):
    """Optional LLM call. Returns None when not configured so callers fall back."""
    import mailer as M
    key = M.cfg("openai_key", "")
    if not key:
        return None
    try:
        body = json.dumps({
            "model": M.cfg("openai_model", "gpt-4o-mini"),
            "messages": [{"role": "system", "content": system},
                         {"role": "user", "content": prompt}],
            "max_tokens": max_tokens, "temperature": 0.6,
        }).encode()
        req = urllib.request.Request(
            M.cfg("openai_base", "https://api.openai.com/v1") + "/chat/completions",
            data=body, headers={"Content-Type": "application/json",
                                "Authorization": "Bearer " + key})
        with urllib.request.urlopen(req, timeout=30) as r:
            d = json.load(r)
        return d["choices"][0]["message"]["content"].strip()
    except Exception as e:
        return f"__ERROR__{e}"


# ---------------------------------------------------------------- lead scoring
def score_lead(lead):
    """0-100 readiness-to-buy with explainable factors."""
    f, score = [], 0.0
    def add(pts, label_ar, label_en, detail=""):
        nonlocal score
        score += pts
        f.append({"points": round(pts, 1), "ar": label_ar, "en": label_en, "detail": detail})

    st = (lead.get("status") or "")
    add({"Qualified": 25, "Contacted": 15, "New": 6, "Unqualified": -20,
         "Converted": 30}.get(st, 0), "حالة العميل", "Lead status", st)
    rt = (lead.get("rating") or "")
    add({"Hot": 20, "Warm": 10, "Cold": 0}.get(rt, 0), "التقييم", "Rating", rt)
    src = (lead.get("source") or "")
    add({"Referral": 15, "Partner": 12, "Web": 10, "Campaign": 8,
         "Trade Show": 7, "Cold Call": 3}.get(src, 4), "جودة المصدر", "Source quality", src)

    rev = _f(lead.get("annual_revenue"))
    add(min(15, rev / 200000 * 15), "الحجم المالي", "Company size", f"{rev:,.0f}")

    completeness = sum(1 for k in ("email", "phone", "company", "industry", "city")
                       if lead.get(k)) / 5
    add(completeness * 10, "اكتمال البيانات", "Data completeness", f"{completeness*100:.0f}%")

    acts = con.execute("""SELECT COUNT(*) n FROM activities WHERE deleted=0
        AND related_to LIKE ?""", (f'%leads#{lead["id"]}%',)).fetchone()["n"]
    add(min(12, acts * 4), "التفاعل المسجّل", "Logged engagement", f"{acts}")

    mails = con.execute("""SELECT COUNT(*) n FROM emails WHERE module='leads'
        AND record_id=?""", (lead["id"],)).fetchone()["n"]
    add(min(8, mails * 3), "مراسلات", "Emails exchanged", f"{mails}")

    age = dsince(lead.get("created_at"))
    if age is not None:
        if age <= 7:    add(10, "حداثة العميل", "Freshness", f"{age}d")
        elif age <= 30: add(6, "حداثة العميل", "Freshness", f"{age}d")
        elif age <= 90: add(0, "حداثة العميل", "Freshness", f"{age}d")
        else:           add(-10, "تقادم بلا حراك", "Stale lead", f"{age}d")

    score = max(0, min(100, score))
    band = ("Hot" if score >= 70 else "Warm" if score >= 45 else
            "Cool" if score >= 25 else "Cold")
    band_ar = {"Hot": "جاهز للشراء", "Warm": "واعد", "Cool": "يحتاج رعاية", "Cold": "بارد"}[band]
    f.sort(key=lambda x: -abs(x["points"]))
    return {"score": round(score, 1), "band": band, "band_ar": band_ar, "factors": f}


# ---------------------------------------------------------------- deal win prob
def _hist_stage_rates():
    rows = con.execute("""SELECT stage, COUNT(*) n,
        SUM(CASE WHEN stage='Closed Won' THEN 1 ELSE 0 END) w FROM deals
        WHERE deleted=0 GROUP BY stage""").fetchall()
    won = con.execute("SELECT COUNT(*) n FROM deals WHERE deleted=0 AND stage='Closed Won'").fetchone()["n"]
    lost = con.execute("SELECT COUNT(*) n FROM deals WHERE deleted=0 AND stage='Closed Lost'").fetchone()["n"]
    base = won / (won + lost) * 100 if (won + lost) else 50
    return base


def predict_deal(deal):
    base = {"Qualification": 20, "Needs Analysis": 35, "Proposal": 55,
            "Negotiation": 72, "Closed Won": 100, "Closed Lost": 0}.get(deal.get("stage"), 30)
    f, adj = [], 0.0
    def add(pts, ar, en, detail=""):
        nonlocal adj
        adj += pts
        f.append({"points": round(pts, 1), "ar": ar, "en": en, "detail": detail})

    if deal.get("stage") in ("Closed Won", "Closed Lost"):
        return {"probability": base, "factors": [], "band": deal["stage"],
                "expected_value": _f(deal.get("amount")) if base == 100 else 0,
                "risk": [], "closed": True}

    # historical win rate vs this competitor
    if deal.get("competitor_id"):
        r = con.execute("""SELECT
            SUM(CASE WHEN stage='Closed Won' THEN 1 ELSE 0 END) w,
            SUM(CASE WHEN stage='Closed Lost' THEN 1 ELSE 0 END) l
            FROM deals WHERE deleted=0 AND CAST(competitor_id AS INTEGER)=?""",
            (deal["competitor_id"],)).fetchone()
        w, l = (r["w"] or 0), (r["l"] or 0)
        if w + l >= 2:
            wr = w / (w + l) * 100
            add((wr - 50) * 0.28, "سجلنا أمام هذا المنافس", "Head-to-head record",
                f"{wr:.0f}% ({w}W/{l}L)")

    # owner track record
    if deal.get("owner_id"):
        r = con.execute("""SELECT SUM(CASE WHEN stage='Closed Won' THEN 1 ELSE 0 END) w,
            SUM(CASE WHEN stage='Closed Lost' THEN 1 ELSE 0 END) l FROM deals
            WHERE deleted=0 AND owner_id=?""", (deal["owner_id"],)).fetchone()
        w, l = (r["w"] or 0), (r["l"] or 0)
        if w + l >= 3:
            wr = w / (w + l) * 100
            add((wr - 50) * 0.16, "أداء المسؤول", "Owner track record", f"{wr:.0f}%")

    # deal size vs our typical won deal
    avg = _f(con.execute("""SELECT AVG(amount) FROM deals WHERE deleted=0
        AND stage='Closed Won'""").fetchone()[0])
    amt = _f(deal.get("amount"))
    if avg and amt:
        ratio = amt / avg
        if ratio > 2.5:   add(-9, "صفقة أكبر من المعتاد", "Unusually large", f"{ratio:.1f}×")
        elif ratio < 0.4: add(5, "صفقة صغيرة سريعة الإغلاق", "Small quick deal", f"{ratio:.1f}×")

    # stalling
    idle = dsince(deal.get("updated_at"))
    if idle is not None:
        if idle > 45:   add(-14, "ركود بلا تحديث", "Stalled", f"{idle}d")
        elif idle > 21: add(-7, "بطء في الحركة", "Slowing", f"{idle}d")
        elif idle <= 7: add(5, "حركة نشطة", "Active momentum", f"{idle}d")

    # closing date sanity
    cd = deal.get("closing_date")
    if cd:
        dleft = -(dsince(cd) or 0)
        if dleft < 0:    add(-12, "تجاوز تاريخ الإغلاق", "Past close date", f"{-dleft}d late")
        elif dleft <= 14: add(6, "قرب الإغلاق", "Closing soon", f"{dleft}d")

    # engagement
    acts = con.execute("""SELECT COUNT(*) n FROM activities WHERE deleted=0
        AND related_to LIKE ?""", (f'%deals#{deal["id"]}%',)).fetchone()["n"]
    add(min(10, acts * 3), "الأنشطة المسجلة", "Activities logged", f"{acts}")

    if deal.get("next_step"): add(4, "خطوة تالية محددة", "Next step defined", "")
    else: add(-5, "لا خطوة تالية", "No next step", "")

    # customer health
    if deal.get("account_id"):
        a = con.execute("""SELECT list_tag, segment FROM accounts
            WHERE id=CAST(? AS INTEGER)""", (deal["account_id"],)).fetchone()
        if a:
            if a["list_tag"] == "Blacklist": add(-40, "عميل في القائمة السوداء", "Blacklisted", "")
            elif a["list_tag"] in ("VIP", "Loyal"): add(9, "عميل مميز/وفي", "VIP or loyal", a["list_tag"])
            if a["segment"] == "Platinum": add(6, "شريحة بلاتينية", "Platinum segment", "")
            elif a["segment"] == "Dormant": add(-8, "عميل راكد", "Dormant account", "")
        overdue = con.execute("""SELECT COUNT(*) n FROM invoices WHERE deleted=0
            AND CAST(account_id AS INTEGER)=? AND status='Overdue'""",
            (deal["account_id"],)).fetchone()["n"]
        if overdue: add(-10, "فواتير متأخرة على العميل", "Overdue invoices", f"{overdue}")

    prob = max(1, min(97, base + adj))
    risks = [x for x in f if x["points"] <= -7]
    f.sort(key=lambda x: -abs(x["points"]))
    band = "High" if prob >= 65 else "Medium" if prob >= 35 else "Low"
    return {"probability": round(prob, 1), "base": base, "adjustment": round(adj, 1),
            "factors": f, "risks": risks, "band": band,
            "expected_value": round(amt * prob / 100, 2), "closed": False}


# ---------------------------------------------------------------- next best action
def next_best_action(module, rid):
    """Concrete, prioritised recommendations grounded in this record's data."""
    acts = []
    def rec(pri, ar, en, why_ar, action=None):
        acts.append({"priority": pri, "ar": ar, "en": en, "why_ar": why_ar, "action": action})

    if module == "deals":
        d = con.execute("SELECT * FROM deals WHERE id=? AND deleted=0", (rid,)).fetchone()
        if not d: raise HTTPException(404, "Not found")
        d = dict(d)
        p = predict_deal(d)
        idle = dsince(d.get("updated_at"))
        if d["stage"] in ("Closed Won", "Closed Lost"):
            rec(3, "سجّل سبب الفوز/الخسارة", "Log win/loss reason",
                "يغذّي دقة التنبؤ لبقية الفريق")
            if d["stage"] == "Closed Won":
                rec(1, "افتح فرصة بيع إضافي", "Open an upsell opportunity",
                    "العملاء الجدد أعلى استجابة خلال 30 يوماً", {"type": "create", "module": "opportunities"})
            return {"prediction": p, "actions": acts}
        if not d.get("next_step"):
            rec(1, "حدّد الخطوة التالية والتاريخ", "Define the next step",
                "الصفقات بلا خطوة تالية تُغلق أقل بنحو 5 نقاط احتمالية")
        if idle and idle > 21:
            rec(1, f"تواصل فوراً — {idle} يوماً بلا تحديث", "Reach out now — deal is stalling",
                "الركود أقوى مؤشر سلبي في النموذج",
                {"type": "activity", "subject": "مكالمة إنعاش للصفقة"})
        if d.get("closing_date") and (dsince(d["closing_date"]) or 0) > 0:
            rec(1, "حدّث تاريخ الإغلاق — تجاوز موعده", "Update the close date",
                "تواريخ متجاوزة تفسد دقة التوقعات")
        acnt = con.execute("SELECT COUNT(*) n FROM activities WHERE deleted=0 AND related_to LIKE ?",
                           (f"%deals#{rid}%",)).fetchone()["n"]
        if acnt == 0:
            rec(2, "سجّل مكالمة أو اجتماع", "Log a call or meeting",
                "لا يوجد أي نشاط مسجل على هذه الصفقة")
        if d["stage"] == "Proposal":
            q = con.execute("""SELECT COUNT(*) n FROM quotes WHERE deleted=0
                AND CAST(deal_id AS INTEGER)=?""", (rid,)).fetchone()["n"]
            if not q:
                rec(1, "أنشئ عرض سعر رسمي", "Create a formal quote",
                    "المرحلة «عرض» بلا عرض سعر مسجل", {"type": "create", "module": "quotes"})
        if d.get("competitor_id"):
            c = con.execute("SELECT name FROM competitors WHERE id=CAST(? AS INTEGER)",
                            (d["competitor_id"],)).fetchone()
            if c: rec(2, f"راجع بطاقة المواجهة ضد {c['name']}", "Review the battlecard",
                      "استخدم نقاط ضعفه المعروفة في العرض",
                      {"type": "battlecard", "id": int(d["competitor_id"])})
        if p["probability"] >= 65 and d["stage"] == "Negotiation":
            rec(1, "اطلب الإغلاق الآن", "Ask for the close",
                f'الاحتمالية {p["probability"]}% وهي الأعلى في مسارها')
        for r in p["risks"]:
            rec(1, f'عالج المخاطرة: {r["ar"]}', f'Mitigate: {r["en"]}', r.get("detail", ""))
        acts.sort(key=lambda x: x["priority"])
        return {"prediction": p, "actions": acts[:8]}

    if module == "leads":
        l = con.execute("SELECT * FROM leads WHERE id=? AND deleted=0", (rid,)).fetchone()
        if not l: raise HTTPException(404, "Not found")
        l = dict(l)
        s = score_lead(l)
        if s["score"] >= 70 and l["status"] != "Converted":
            rec(1, "حوّله الآن — جاهز للشراء", "Convert now — buying-ready",
                f'درجة الجاهزية {s["score"]}', {"type": "convert"})
        if not l.get("email") or not l.get("phone"):
            rec(2, "أكمل بيانات التواصل", "Complete contact details",
                "نقص البيانات يخفض الجاهزية")
        age = dsince(l.get("created_at"))
        if l["status"] == "New" and age and age > 3:
            rec(1, f"لم يُتواصل معه منذ {age} يوماً", "No contact yet",
                "سرعة الاستجابة أهم عامل في تحويل العملاء المحتملين",
                {"type": "activity", "subject": "مكالمة أولى"})
        if l.get("rating") == "Hot" and l["status"] != "Qualified":
            rec(1, "أهّله فوراً", "Qualify immediately", "مُصنّف Hot ولم يُؤهَّل بعد")
        if age and age > 90 and l["status"] in ("New", "Contacted"):
            rec(3, "أرسل حملة إحياء أو أغلقه", "Nurture campaign or disqualify",
                "متقادم بلا حراك — يستنزف المسار")
        acts.sort(key=lambda x: x["priority"])
        return {"score": s, "actions": acts[:8]}

    if module == "accounts":
        a = con.execute("SELECT * FROM accounts WHERE id=? AND deleted=0", (rid,)).fetchone()
        if not a: raise HTTPException(404, "Not found")
        a = dict(a)
        ov = con.execute("""SELECT COUNT(*) n, COALESCE(SUM(amount-COALESCE(paid_amount,0)),0) v
            FROM invoices WHERE deleted=0 AND CAST(account_id AS INTEGER)=?
            AND status='Overdue'""", (rid,)).fetchone()
        if ov["n"]:
            rec(1, f'تحصيل {ov["v"]:,.0f} متأخرة', "Chase overdue invoices", f'{ov["n"]} فاتورة')
        last = con.execute("""SELECT MAX(closing_date) d FROM deals WHERE deleted=0
            AND stage='Closed Won' AND CAST(account_id AS INTEGER)=?""", (rid,)).fetchone()["d"]
        idle = dsince(last)
        if idle and idle > 180:
            rec(1, f"عميل راكد منذ {idle} يوماً — خطة استرجاع", "Win-back campaign",
                "الإيراد معرّض للفقد")
        opn = con.execute("""SELECT COUNT(*) n FROM deals WHERE deleted=0
            AND CAST(account_id AS INTEGER)=? AND stage NOT IN ('Closed Won','Closed Lost')""",
            (rid,)).fetchone()["n"]
        if not opn:
            rec(2, "لا توجد صفقة مفتوحة — ابحث عن فرصة", "No open deal — find an opportunity", "")
        if a.get("segment") == "Platinum" and a.get("list_tag") not in ("VIP", "Loyal"):
            rec(2, "رشّحه لقائمة كبار العملاء", "Nominate for VIP list", "شريحة بلاتينية غير مصنفة")
        tk = con.execute("""SELECT COUNT(*) n FROM tickets WHERE deleted=0
            AND CAST(account_id AS INTEGER)=? AND status!='Closed'""", (rid,)).fetchone()["n"]
        if tk: rec(1, f"{tk} تذكرة مفتوحة — تابع الرضا", "Open tickets — check satisfaction", "")
        acts.sort(key=lambda x: x["priority"])
        return {"actions": acts[:8]}

    raise HTTPException(400, "Unsupported module")


# ---------------------------------------------------------------- forecasting
def forecast(months=3):
    """Blend of weighted pipeline + trend regression on closed-won history."""
    hist = [dict(r) for r in con.execute("""
        SELECT substr(closing_date,1,7) k, SUM(amount) v, COUNT(*) n FROM deals
        WHERE deleted=0 AND stage='Closed Won' AND closing_date IS NOT NULL
        AND closing_date <= date('now') GROUP BY k ORDER BY k""")]
    vals = [_f(h["v"]) for h in hist][-12:]
    trend = None
    if len(vals) >= 3:
        n = len(vals); xs = list(range(n))
        mx, my = statistics.mean(xs), statistics.mean(vals)
        den = sum((x - mx) ** 2 for x in xs) or 1
        slope = sum((xs[i] - mx) * (vals[i] - my) for i in range(n)) / den
        intercept = my - slope * mx
        trend = {"slope": round(slope, 2), "avg": round(my, 2)}

    out = []
    for i in range(1, months + 1):
        mdate = (today().replace(day=1) + datetime.timedelta(days=32 * i)).replace(day=1)
        key = mdate.strftime("%Y-%m")
        nxt = mdate.replace(day=28) + datetime.timedelta(days=4)
        eom = (nxt - datetime.timedelta(days=nxt.day)).isoformat()
        som = mdate.isoformat()
        # weighted pipeline expected to close in that month
        wp = 0.0; cnt = 0
        for d in con.execute("""SELECT * FROM deals WHERE deleted=0
            AND stage NOT IN ('Closed Won','Closed Lost')
            AND closing_date>=? AND closing_date<=?""", (som, eom)):
            p = predict_deal(dict(d))
            wp += p["expected_value"]; cnt += 1
        tr = None
        if trend:
            tr = max(0, intercept + slope * (len(vals) - 1 + i))
        # blend: pipeline is authoritative near-term, trend anchors long-term
        w = {1: 0.75, 2: 0.6, 3: 0.5}.get(i, 0.4)
        blended = wp * w + (tr or wp) * (1 - w)
        out.append({"month": key, "weighted_pipeline": round(wp, 2), "deals": cnt,
                    "trend": round(tr, 2) if tr is not None else None,
                    "forecast": round(blended, 2),
                    "low": round(blended * 0.7, 2), "high": round(blended * 1.3, 2)})
    quota = _f(con.execute("SELECT SUM(target) FROM users WHERE active=1").fetchone()[0])
    return {"history": hist[-12:], "forecast": out, "trend": trend,
            "total_forecast": round(sum(o["forecast"] for o in out), 2),
            "quota": quota,
            "committed": _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0
                AND stage='Negotiation'""").fetchone()[0])}


# ---------------------------------------------------------------- content gen
def gen_email(kind, ctx):
    """LLM if configured, else a strong bilingual template."""
    name = ctx.get("name", "")
    company = ctx.get("company", "NebrasCRM")
    subject_map = {
        "intro": f"تعارف — {company}",
        "followup": f"متابعة — {ctx.get('subject','')}",
        "proposal": f"عرضنا لكم — {ctx.get('subject','')}",
        "winback": f"نفتقدكم — عرض خاص من {company}",
        "overdue": f"تذكير بفاتورة مستحقة — {ctx.get('subject','')}",
        "thanks": f"شكراً لثقتكم — {company}",
    }
    prompt = (f"Write a short professional bilingual (Arabic first, then English) sales email.\n"
              f"Type: {kind}\nRecipient: {name}\nCompany: {company}\n"
              f"Context: {json.dumps(ctx, ensure_ascii=False)}\n"
              f"Keep under 140 words per language. Warm, specific, one clear call to action.")
    out = llm_complete(prompt)
    if out and not out.startswith("__ERROR__"):
        return {"subject": subject_map.get(kind, company), "body": out, "source": "llm"}

    bodies = {
        "intro": f"""مرحباً {name}،

سعدنا باهتمامكم بـ{company}. نساعد شركات مثلكم على تنظيم مبيعاتها ومتابعة عملائها في نظام واحد.
هل يناسبكم اتصال قصير (15 دقيقة) هذا الأسبوع لأعرض عليكم كيف يمكن أن يخدمكم النظام؟

مع التقدير،
{ctx.get('owner','')}""",
        "followup": f"""مرحباً {name}،

أتابع معكم بخصوص {ctx.get('subject','')}. هل كان لديكم فرصة لمراجعة ما أرسلناه؟
يسعدني الإجابة عن أي استفسار أو ترتيب عرض توضيحي في الوقت المناسب لكم.

مع التقدير،
{ctx.get('owner','')}""",
        "proposal": f"""مرحباً {name}،

نرفق لكم عرضنا بخصوص {ctx.get('subject','')} بقيمة {ctx.get('amount','')}.
العرض صالح حتى {ctx.get('valid_until','—')}، ويسعدنا مناقشة أي تعديل يناسب احتياجكم.

مع التقدير،
{ctx.get('owner','')}""",
        "winback": f"""مرحباً {name}،

مضى وقت منذ آخر تعامل بيننا ونود أن نعرف كيف يمكننا خدمتكم بشكل أفضل.
خصصنا لكم عرضاً خاصاً بصفتكم من عملائنا السابقين — هل نحدد مكالمة قصيرة؟

مع التقدير،
{ctx.get('owner','')}""",
        "overdue": f"""مرحباً {name}،

تذكير ودّي بأن الفاتورة {ctx.get('subject','')} بقيمة {ctx.get('amount','')} مستحقة بتاريخ {ctx.get('due_date','—')}.
إن كان السداد قد تم، فتفضلوا بتجاهل هذه الرسالة مشكورين.

مع التقدير،
{ctx.get('owner','')}""",
        "thanks": f"""مرحباً {name}،

شكراً لثقتكم بنا. يسعدنا أن نكون شركاءكم، وفريقنا جاهز لأي دعم تحتاجونه.

مع التقدير،
{ctx.get('owner','')}""",
    }
    return {"subject": subject_map.get(kind, company),
            "body": bodies.get(kind, bodies["followup"]), "source": "template"}


def summarize(text, bullets=5):
    out = llm_complete(f"Summarise the following meeting/notes into {bullets} concise Arabic "
                       f"bullet points, then list action items with owners if mentioned:\n\n{text}")
    if out and not out.startswith("__ERROR__"):
        return {"summary": out, "source": "llm"}
    # extractive fallback: rank sentences by keyword salience
    sents = [s.strip() for s in re.split(r"[.\n؟!]+", text or "") if len(s.strip()) > 15]
    if not sents:
        return {"summary": "—", "source": "extractive", "actions": []}
    words = re.findall(r"[\w\u0600-\u06FF]{4,}", (text or "").lower())
    freq = {}
    for w in words: freq[w] = freq.get(w, 0) + 1
    scored = sorted(sents, key=lambda s: -sum(
        freq.get(w, 0) for w in re.findall(r"[\w\u0600-\u06FF]{4,}", s.lower())))
    top = scored[:bullets]
    ordered = [s for s in sents if s in top][:bullets]
    cues = ("سنقوم", "يجب", "سأرسل", "نتفق", "موعد", "متابعة", "will ", "action", "next step",
            "todo", "follow up")
    actions = [s for s in sents if any(c in s.lower() for c in cues)][:5]
    return {"summary": "\n".join("• " + s for s in ordered),
            "actions": actions, "source": "extractive"}


# ---------------------------------------------------------------- registration
def register(app, current_user, require):

    @app.get("/api/ai/status")
    def status(user=Depends(current_user)):
        import mailer as M
        return {"llm": llm_ready(), "model": M.cfg("openai_model", "gpt-4o-mini"),
                "engines": ["lead_scoring", "deal_prediction", "forecast",
                            "next_best_action", "email_generation", "summarization",
                            "churn_risk"],
                "note_ar": "كل النماذج التنبؤية تعمل محلياً على بياناتك دون أي مفتاح خارجي. "
                           "المفتاح اختياري ويُستخدم فقط لتوليد النصوص الحرة."}

    @app.get("/api/ai/lead-score/{lid}")
    def lead_score(lid: int, user=Depends(current_user)):
        l = con.execute("SELECT * FROM leads WHERE id=? AND deleted=0", (lid,)).fetchone()
        if not l: raise HTTPException(404, "Not found")
        return score_lead(dict(l))

    @app.get("/api/ai/lead-scores")
    def lead_scores(limit: int = 100, user=Depends(current_user)):
        out = []
        for l in con.execute("""SELECT * FROM leads WHERE deleted=0
                                AND status!='Converted' LIMIT ?""", (limit,)):
            d = dict(l); s = score_lead(d)
            out.append({"id": d["id"], "name": d["name"], "company": d.get("company"),
                        "status": d.get("status"), "owner_id": d.get("owner_id"),
                        "score": s["score"], "band": s["band"], "band_ar": s["band_ar"],
                        "top_factor": s["factors"][0]["ar"] if s["factors"] else ""})
        out.sort(key=lambda x: -x["score"])
        dist = {}
        for o in out: dist[o["band"]] = dist.get(o["band"], 0) + 1
        return {"leads": out, "distribution": dist}

    @app.get("/api/ai/deal/{did}")
    def deal_ai(did: int, user=Depends(current_user)):
        d = con.execute("SELECT * FROM deals WHERE id=? AND deleted=0", (did,)).fetchone()
        if not d: raise HTTPException(404, "Not found")
        return predict_deal(dict(d))

    @app.get("/api/ai/pipeline-health")
    def pipeline_health(user=Depends(current_user)):
        rows, tot_w, at_risk = [], 0.0, []
        for d in con.execute("""SELECT * FROM deals WHERE deleted=0
                                AND stage NOT IN ('Closed Won','Closed Lost')"""):
            dd = dict(d); p = predict_deal(dd)
            tot_w += p["expected_value"]
            item = {"id": dd["id"], "name": dd["name"], "amount": _f(dd["amount"]),
                    "stage": dd["stage"], "probability": p["probability"],
                    "expected": p["expected_value"], "band": p["band"],
                    "risks": [r["ar"] for r in p["risks"]],
                    "owner_id": dd.get("owner_id")}
            rows.append(item)
            if p["risks"] and _f(dd["amount"]) > 0: at_risk.append(item)
        rows.sort(key=lambda x: -x["expected"])
        at_risk.sort(key=lambda x: -x["amount"])
        return {"deals": rows[:60], "weighted_total": round(tot_w, 2),
                "at_risk": at_risk[:20],
                "at_risk_value": round(sum(x["amount"] for x in at_risk), 2),
                "count": len(rows)}

    @app.get("/api/ai/forecast")
    def get_forecast(months: int = 3, user=Depends(current_user)):
        return forecast(min(6, max(1, months)))

    @app.get("/api/ai/next-best-action/{module}/{rid}")
    def nba(module: str, rid: int, user=Depends(current_user)):
        return next_best_action(module, rid)

    class GenBody(BaseModel):
        kind: str = "followup"
        module: Optional[str] = None
        record_id: Optional[int] = None
        extra: dict = {}

    @app.post("/api/ai/generate-email")
    def gen(b: GenBody, user=Depends(current_user)):
        import mailer as M
        ctx = {"owner": user["name"], "company": M.cfg("company_name", "NebrasCRM")}
        ctx.update(b.extra or {})
        if b.module and b.record_id:
            r = con.execute(f'SELECT * FROM "{b.module}" WHERE id=?', (b.record_id,)).fetchone()
            if r:
                d = dict(r)
                ctx.setdefault("name", d.get("name") or d.get("subject") or "")
                ctx.setdefault("subject", d.get("subject") or d.get("name") or "")
                for k in ("amount", "due_date", "valid_until"):
                    if d.get(k) is not None: ctx.setdefault(k, d[k])
                if d.get("account_id"):
                    a = con.execute("SELECT name FROM accounts WHERE id=CAST(? AS INTEGER)",
                                    (d["account_id"],)).fetchone()
                    if a: ctx.setdefault("account", a["name"])
        return gen_email(b.kind, ctx)

    class SumBody(BaseModel):
        text: str
        bullets: int = 5
        module: Optional[str] = None
        record_id: Optional[int] = None
        save_note: bool = False

    @app.post("/api/ai/summarize")
    def do_sum(b: SumBody, user=Depends(current_user)):
        r = summarize(b.text, b.bullets)
        if b.save_note and b.module and b.record_id and user["role"] != "readonly":
            import db as D
            con.execute("INSERT INTO notes(module,record_id,body,user_id,created_at) VALUES(?,?,?,?,?)",
                        (b.module, b.record_id, "🤖 ملخص:\n" + r["summary"], user["id"], D.now()))
            con.commit()
        return r

    @app.get("/api/ai/churn-risk")
    def churn(user=Depends(current_user)):
        out = []
        for a in con.execute("SELECT * FROM accounts WHERE deleted=0"):
            d = dict(a); risk, why = 0, []
            last = con.execute("""SELECT MAX(closing_date) d FROM deals WHERE deleted=0
                AND stage='Closed Won' AND CAST(account_id AS INTEGER)=?""", (d["id"],)).fetchone()["d"]
            idle = dsince(last)
            if idle is None: risk += 25; why.append("لا مشتريات مسجلة")
            elif idle > 365: risk += 40; why.append(f"{idle} يوماً بلا شراء")
            elif idle > 180: risk += 25; why.append(f"{idle} يوماً بلا شراء")
            ov = con.execute("""SELECT COUNT(*) n FROM invoices WHERE deleted=0
                AND CAST(account_id AS INTEGER)=? AND status='Overdue'""", (d["id"],)).fetchone()["n"]
            if ov: risk += 15; why.append(f"{ov} فاتورة متأخرة")
            tk = con.execute("""SELECT COUNT(*) n FROM tickets WHERE deleted=0
                AND CAST(account_id AS INTEGER)=? AND priority IN ('High','Urgent')
                AND status!='Closed'""", (d["id"],)).fetchone()["n"]
            if tk: risk += 20; why.append(f"{tk} تذكرة عاجلة مفتوحة")
            lost = con.execute("""SELECT COUNT(*) n FROM deals WHERE deleted=0
                AND stage='Closed Lost' AND CAST(account_id AS INTEGER)=?""", (d["id"],)).fetchone()["n"]
            if lost >= 2: risk += 12; why.append(f"{lost} صفقات مخسورة")
            if d.get("segment") == "Dormant": risk += 10; why.append("شريحة راكدة")
            rev = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0
                AND stage='Closed Won' AND CAST(account_id AS INTEGER)=?""", (d["id"],)).fetchone()[0])
            risk = min(100, risk)
            if risk >= 30:
                out.append({"id": d["id"], "name": d["name"], "risk": risk,
                            "band": "Critical" if risk >= 70 else "High" if risk >= 50 else "Medium",
                            "revenue_at_risk": rev, "reasons": why,
                            "segment": d.get("segment"), "list_tag": d.get("list_tag")})
        out.sort(key=lambda x: (-x["risk"], -x["revenue_at_risk"]))
        return {"accounts": out, "total_at_risk": round(sum(x["revenue_at_risk"] for x in out), 2)}

    @app.get("/api/ai/digest")
    def digest(user=Depends(current_user)):
        """The 'what should I do today' briefing."""
        uid = user["id"]
        mine = "" if user["role"] in ("admin", "manager") else f" AND owner_id={uid}"
        overdue_tasks = [dict(r) for r in con.execute(f"""
            SELECT id,subject,due_date,priority FROM activities WHERE deleted=0
            AND status!='Completed' AND due_date<date('now'){mine}
            ORDER BY due_date LIMIT 10""")]
        today_tasks = [dict(r) for r in con.execute(f"""
            SELECT id,subject,due_date,priority FROM activities WHERE deleted=0
            AND status!='Completed' AND due_date=date('now'){mine} LIMIT 10""")]
        hot = lead_scores(60, user)["leads"][:5]
        ph = pipeline_health(user)
        closing = [d for d in ph["deals"] if d["band"] == "High"][:5]
        risk = ph["at_risk"][:5]
        ch = churn(user)["accounts"][:5]
        return {"overdue_tasks": overdue_tasks, "today_tasks": today_tasks,
                "hot_leads": hot, "closing_soon": closing, "deals_at_risk": risk,
                "churn_risk": ch,
                "weighted_pipeline": ph["weighted_total"],
                "forecast_month": forecast(1)["forecast"][0] if True else None}
