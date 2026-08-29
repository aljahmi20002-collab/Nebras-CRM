"""Loyalty engine for customers and partners.

Fairness is the design goal ("بعدالة وإنصاف"), so the engine is built on
three principles:

 1. NORMALISED, NOT ABSOLUTE — a small shop in a village and a bank in Sanaa are
    not judged on raw revenue alone. Points come from *relative* performance:
    growth vs the member's own history, consistency, and share of their own
    potential — so a small loyal buyer can outrank a big erratic one.
 2. EFFORT COUNTS, NOT JUST MONEY — engagement (orders placed, visits, on-time
    payment, low returns) earns points independently of deal size.
 3. TRANSPARENT & AUDITABLE — every point is written as a ledger row with the
    rule that produced it, so a member can be shown exactly why they got a tier.
    Nothing is a black box, and points expire on a published schedule.
"""
import datetime, json, math
from typing import Optional
from fastapi import Depends, HTTPException
from pydantic import BaseModel

con = None

TIERS = [
    {"code": "diamond",  "en": "Diamond",  "ar": "ماسي",  "min": 5000, "color": "#22d3ee",
     "discount": 15, "perks_ar": "خصم 15% · أولوية دعم · مدير حساب مخصص · دفع آجل 60 يوم"},
    {"code": "platinum", "en": "Platinum", "ar": "بلاتيني", "min": 2500, "color": "#a855f7",
     "discount": 10, "perks_ar": "خصم 10% · أولوية دعم · دفع آجل 45 يوم"},
    {"code": "gold",     "en": "Gold",     "ar": "ذهبي",  "min": 1200, "color": "#f59e0b",
     "discount": 7,  "perks_ar": "خصم 7% · دعم سريع · دفع آجل 30 يوم"},
    {"code": "silver",   "en": "Silver",   "ar": "فضي",   "min": 500,  "color": "#94a3b8",
     "discount": 4,  "perks_ar": "خصم 4% · عروض موسمية"},
    {"code": "bronze",   "en": "Bronze",   "ar": "برونزي", "min": 100, "color": "#b45309",
     "discount": 2,  "perks_ar": "خصم 2%"},
    {"code": "member",   "en": "Member",   "ar": "عضو",   "min": 0,    "color": "#64748b",
     "discount": 0,  "perks_ar": "الانضمام للبرنامج"},
]

# Every rule is published — this table IS the program's terms.
RULES = {
    "purchase":     {"ar": "نقاط الشراء", "en": "Purchase points",
                     "desc_ar": "نقطة واحدة لكل 100 من قيمة الشراء", "cap": 2000},
    "frequency":    {"ar": "تكرار التعامل", "en": "Frequency",
                     "desc_ar": "50 نقطة لكل عملية شراء منفصلة (يكافئ الاستمرارية لا الحجم)", "cap": 1500},
    "growth":       {"ar": "النمو الذاتي", "en": "Self growth",
                     "desc_ar": "حتى 800 نقطة عند تجاوز أداء الفترة السابقة", "cap": 800},
    "consistency":  {"ar": "الانتظام", "en": "Consistency",
                     "desc_ar": "150 نقطة لكل شهر متتالٍ من النشاط", "cap": 900},
    "payment":      {"ar": "الالتزام بالسداد", "en": "On-time payment",
                     "desc_ar": "200 نقطة لكل فاتورة سُددت في موعدها", "cap": 1200},
    "tenure":       {"ar": "أقدمية التعامل", "en": "Tenure",
                     "desc_ar": "120 نقطة لكل سنة شراكة", "cap": 720},
    "engagement":   {"ar": "التفاعل", "en": "Engagement",
                     "desc_ar": "20 نقطة لكل نشاط أو زيارة موثقة", "cap": 400},
    "coverage":     {"ar": "التغطية الجغرافية", "en": "Territory coverage",
                     "desc_ar": "للوكلاء: 80 نقطة لكل مديرية مغطاة فعلياً", "cap": 600},
    "referral":     {"ar": "الترشيحات", "en": "Referrals",
                     "desc_ar": "300 نقطة لكل عميل جديد بترشيح", "cap": 900},
    "penalty_late": {"ar": "خصم التأخر", "en": "Late payment penalty",
                     "desc_ar": "خصم 150 نقطة لكل فاتورة متأخرة", "cap": -1000},
    "penalty_churn": {"ar": "خصم الركود", "en": "Inactivity decay",
                      "desc_ar": "خصم 10 نقاط لكل شهر ركود بعد 3 أشهر", "cap": -600},
}

POINT_EXPIRY_MONTHS = 24


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def today():
    return datetime.date.today()


def dsince(s):
    if not s: return None
    try: return (today() - datetime.date.fromisoformat(str(s)[:10])).days
    except Exception: return None


def init_tables(c):
    c.execute("""CREATE TABLE IF NOT EXISTS loyalty_points(
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_type VARCHAR(32), member_id INTEGER,
        rule TEXT, points REAL, basis TEXT, period TEXT,
        expires_at TEXT, created_at TEXT)""")
    c.execute("""CREATE TABLE IF NOT EXISTS loyalty_members(
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_type VARCHAR(32), member_id INTEGER,
        points REAL DEFAULT 0, tier TEXT DEFAULT 'member', lifetime REAL DEFAULT 0,
        redeemed REAL DEFAULT 0, joined_at TEXT, computed_at TEXT,
        UNIQUE(member_type, member_id))""")
    c.execute("""CREATE TABLE IF NOT EXISTS loyalty_redemptions(
        id INTEGER PRIMARY KEY AUTOINCREMENT, member_type VARCHAR(32), member_id INTEGER,
        points REAL, reward TEXT, "value" REAL, status TEXT DEFAULT 'approved',
        note TEXT, created_by INTEGER, created_at TEXT)""")
    c.execute("CREATE INDEX IF NOT EXISTS ix_lp_member ON loyalty_points(member_type,member_id)")
    c.commit()


def tier_for(points):
    for t in TIERS:
        if points >= t["min"]:
            return t
    return TIERS[-1]


def cap(rule, val):
    c = RULES[rule]["cap"]
    return max(c, val) if c < 0 else min(c, val)


# --------------------------------------------------------------------------
def score_customer(aid):
    """Return (breakdown list, total) for one account."""
    b = []
    inv = con.execute("""SELECT COUNT(*) n, COALESCE(SUM(paid_amount),0) paid,
        MIN(invoice_date) first_inv, MAX(invoice_date) last_inv
        FROM invoices WHERE deleted=0 AND CAST(account_id AS INTEGER)=?
        AND status IN ('Paid','Sent','Overdue')""", (aid,)).fetchone()
    won = con.execute("""SELECT COUNT(*) n, COALESCE(SUM(amount),0) v, MAX(closing_date) last
        FROM deals WHERE deleted=0 AND stage='Closed Won'
        AND CAST(account_id AS INTEGER)=?""", (aid,)).fetchone()

    spend = _f(inv["paid"]) + _f(won["v"])
    b.append(("purchase", cap("purchase", spend / 100), f"{spend:,.0f}"))

    orders = (inv["n"] or 0) + (won["n"] or 0)
    b.append(("frequency", cap("frequency", orders * 50), f"{orders}"))

    # growth: last 6 months vs the 6 before
    cut1 = (today() - datetime.timedelta(days=180)).isoformat()
    cut2 = (today() - datetime.timedelta(days=360)).isoformat()
    recent = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0 AND stage='Closed Won'
        AND CAST(account_id AS INTEGER)=? AND closing_date>=?""", (aid, cut1)).fetchone()[0])
    prior = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0 AND stage='Closed Won'
        AND CAST(account_id AS INTEGER)=? AND closing_date>=? AND closing_date<?""",
        (aid, cut2, cut1)).fetchone()[0])
    if prior > 0:
        g = (recent - prior) / prior
        b.append(("growth", cap("growth", max(0, g) * 800), f"{g*100:.0f}%"))
    elif recent > 0:
        b.append(("growth", 400, "new activity"))
    else:
        b.append(("growth", 0, "—"))

    months = con.execute("""SELECT DISTINCT substr(invoice_date,1,7) m FROM invoices
        WHERE deleted=0 AND CAST(account_id AS INTEGER)=? AND invoice_date IS NOT NULL
        ORDER BY m""", (aid,)).fetchall()
    streak = best = 0; prev = None
    for r in months:
        y, mo = (int(x) for x in r["m"].split("-"))
        cur = y * 12 + mo
        streak = streak + 1 if prev is not None and cur == prev + 1 else 1
        best = max(best, streak); prev = cur
    b.append(("consistency", cap("consistency", best * 150), f"{best} mo"))

    ontime = con.execute("""SELECT COUNT(*) n FROM invoices WHERE deleted=0
        AND CAST(account_id AS INTEGER)=? AND status='Paid'
        AND (due_date IS NULL OR due_date>=date('now'))""", (aid,)).fetchone()["n"]
    b.append(("payment", cap("payment", ontime * 200), f"{ontime}"))

    late = con.execute("""SELECT COUNT(*) n FROM invoices WHERE deleted=0
        AND CAST(account_id AS INTEGER)=? AND status='Overdue'""", (aid,)).fetchone()["n"]
    b.append(("penalty_late", cap("penalty_late", -late * 150), f"{late}"))

    acc = con.execute("SELECT created_at FROM accounts WHERE id=?", (aid,)).fetchone()
    first = inv["first_inv"] or (acc["created_at"] if acc else None)
    yrs = (dsince(first) or 0) / 365.0
    b.append(("tenure", cap("tenure", yrs * 120), f"{yrs:.1f}y"))

    acts = con.execute("""SELECT COUNT(*) n FROM activities WHERE deleted=0
        AND related_to LIKE ?""", (f"%accounts#{aid}%",)).fetchone()["n"]
    tks = con.execute("""SELECT COUNT(*) n FROM tickets WHERE deleted=0
        AND CAST(account_id AS INTEGER)=?""", (aid,)).fetchone()["n"]
    b.append(("engagement", cap("engagement", (acts + tks) * 20), f"{acts+tks}"))

    last = max([x for x in (inv["last_inv"], won["last"]) if x], default=None)
    idle = dsince(last)
    if idle and idle > 90:
        b.append(("penalty_churn", cap("penalty_churn", -((idle - 90) / 30) * 10), f"{idle}d"))
    else:
        b.append(("penalty_churn", 0, "active"))

    total = round(sum(x[1] for x in b), 1)
    return b, max(0, total)


def score_partner(pid):
    b = []
    won = con.execute("""SELECT COUNT(*) n, COALESCE(SUM(amount),0) v, MAX(closing_date) last
        FROM deals WHERE deleted=0 AND stage='Closed Won'
        AND CAST(agent_id AS INTEGER)=?""", (pid,)).fetchone()
    sales = _f(won["v"])
    b.append(("purchase", cap("purchase", sales / 100), f"{sales:,.0f}"))
    b.append(("frequency", cap("frequency", (won["n"] or 0) * 50), f'{won["n"] or 0}'))

    cut1 = (today() - datetime.timedelta(days=180)).isoformat()
    cut2 = (today() - datetime.timedelta(days=360)).isoformat()
    recent = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0 AND stage='Closed Won'
        AND CAST(agent_id AS INTEGER)=? AND closing_date>=?""", (pid, cut1)).fetchone()[0])
    prior = _f(con.execute("""SELECT SUM(amount) FROM deals WHERE deleted=0 AND stage='Closed Won'
        AND CAST(agent_id AS INTEGER)=? AND closing_date>=? AND closing_date<?""",
        (pid, cut2, cut1)).fetchone()[0])
    if prior > 0:
        g = (recent - prior) / prior
        b.append(("growth", cap("growth", max(0, g) * 800), f"{g*100:.0f}%"))
    else:
        b.append(("growth", 400 if recent > 0 else 0, "new" if recent > 0 else "—"))

    months = con.execute("""SELECT DISTINCT substr(closing_date,1,7) m FROM deals
        WHERE deleted=0 AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?
        AND closing_date IS NOT NULL ORDER BY m""", (pid,)).fetchall()
    streak = best = 0; prev = None
    for r in months:
        if not r["m"]: continue
        y, mo = (int(x) for x in r["m"].split("-"))
        cur = y * 12 + mo
        streak = streak + 1 if prev is not None and cur == prev + 1 else 1
        best = max(best, streak); prev = cur
    b.append(("consistency", cap("consistency", best * 150), f"{best} mo"))

    # territory coverage: districts where the agent actually closed business
    covered = con.execute("""SELECT COUNT(DISTINCT a.district_id) n FROM deals d
        JOIN accounts a ON a.id=CAST(d.account_id AS INTEGER)
        WHERE d.deleted=0 AND d.stage='Closed Won' AND CAST(d.agent_id AS INTEGER)=?
        AND a.district_id IS NOT NULL""", (pid,)).fetchone()["n"]
    b.append(("coverage", cap("coverage", covered * 80), f"{covered}"))

    ag = con.execute("SELECT joined_at,target,credit_limit FROM agents WHERE id=?", (pid,)).fetchone()
    yrs = (dsince(ag["joined_at"] if ag else None) or 0) / 365.0
    b.append(("tenure", cap("tenure", yrs * 120), f"{yrs:.1f}y"))

    refs = con.execute("""SELECT COUNT(*) n FROM accounts WHERE deleted=0
        AND CAST(agent_id AS INTEGER)=?""", (pid,)).fetchone()["n"]
    b.append(("referral", cap("referral", refs * 300), f"{refs}"))

    # penalty: unsettled advances beyond credit limit
    adv = _f(con.execute("""SELECT SUM(CASE WHEN kind IN ('commission','bonus','adjustment')
        THEN amount ELSE -amount END) FROM agent_txn WHERE agent_id=?""", (pid,)).fetchone()[0])
    b.append(("penalty_late", cap("penalty_late", -300 if adv < 0 else 0), f"{adv:,.0f}"))

    idle = dsince(won["last"])
    b.append(("penalty_churn",
              cap("penalty_churn", -((idle - 90) / 30) * 10) if idle and idle > 90 else 0,
              f"{idle}d" if idle else "—"))
    total = round(sum(x[1] for x in b), 1)
    return b, max(0, total)


def compute(member_type, member_id):
    b, total = (score_customer if member_type == "customer" else score_partner)(member_id)
    rows = [{"rule": r, "points": round(p, 1), "basis": bs,
             "label_ar": RULES[r]["ar"], "label_en": RULES[r]["en"],
             "desc_ar": RULES[r]["desc_ar"]} for r, p, bs in b]
    return rows, total


def register(app, current_user, require):

    @app.get("/api/loyalty/program")
    def program(user=Depends(current_user)):
        return {"tiers": TIERS, "rules": RULES, "expiry_months": POINT_EXPIRY_MONTHS,
                "principles_ar": [
                    "النقاط تُحسب على الأداء النسبي لا الحجم المطلق، فالعميل الصغير المنتظم قد يتفوق على الكبير المتذبذب.",
                    "الجهد يُكافأ: تكرار التعامل والانتظام والالتزام بالسداد تمنح نقاطاً بغض النظر عن قيمة الصفقة.",
                    "كل نقطة مسجّلة بقاعدتها وسببها، ويمكن عرض تفصيل كامل لأي عضو — لا صندوق أسود.",
                    "لكل قاعدة سقف أقصى يمنع أي عامل واحد من الهيمنة على النتيجة.",
                    f"النقاط تنتهي صلاحيتها بعد {POINT_EXPIRY_MONTHS} شهراً وفق جدول معلن."]}

    @app.get("/api/loyalty/members")
    def members(member_type: str = "customer", user=Depends(current_user)):
        require(user, "admin", "manager")
        if member_type not in ("customer", "partner"):
            raise HTTPException(400, "Unknown member type")
        if member_type == "customer":
            src = [dict(r) for r in con.execute(
                "SELECT id, name FROM accounts WHERE deleted=0")]
        else:
            src = [dict(r) for r in con.execute(
                "SELECT id, name FROM agents WHERE deleted=0")]
        out = []
        for s in src:
            rows, total = compute(member_type, s["id"])
            t = tier_for(total)
            saved = con.execute("""SELECT points,redeemed FROM loyalty_members
                WHERE member_type=? AND member_id=?""", (member_type, s["id"])).fetchone()
            red = _f(saved["redeemed"]) if saved else 0
            out.append({"member_type": member_type, "member_id": s["id"], "name": s["name"],
                        "points": total, "available": round(total - red, 1), "redeemed": red,
                        "tier": t["code"], "tier_ar": t["ar"], "tier_en": t["en"],
                        "color": t["color"], "discount": t["discount"],
                        "positives": round(sum(r["points"] for r in rows if r["points"] > 0), 1),
                        "penalties": round(sum(r["points"] for r in rows if r["points"] < 0), 1)})
        out.sort(key=lambda x: -x["points"])
        dist = {}
        for m in out:
            dist[m["tier"]] = dist.get(m["tier"], 0) + 1
        return {"members": out, "distribution": dist, "tiers": TIERS}

    @app.get("/api/loyalty/member/{member_type}/{mid}")
    def member(member_type: str, mid: int, user=Depends(current_user)):
        require(user, "admin", "manager")
        if member_type not in ("customer", "partner"):
            raise HTTPException(400, "Unknown member type")
        table = "accounts" if member_type == "customer" else "agents"
        if not con.execute(f"SELECT 1 FROM {table} WHERE id=? AND deleted=0", (mid,)).fetchone():
            raise HTTPException(404, "Member not found")
        rows, total = compute(member_type, mid)
        t = tier_for(total)
        nxt = None
        for x in reversed(TIERS):
            if x["min"] > total:
                nxt = {"tier": x, "gap": round(x["min"] - total, 1)}
                break
        nm = con.execute(
            f"SELECT name FROM {'accounts' if member_type=='customer' else 'agents'} WHERE id=?",
            (mid,)).fetchone()
        red = [dict(r) for r in con.execute("""SELECT * FROM loyalty_redemptions
            WHERE member_type=? AND member_id=? ORDER BY id DESC""", (member_type, mid))]
        spent = sum(_f(r["points"]) for r in red if r["status"] == "approved")
        return {"member_type": member_type, "member_id": mid,
                "name": nm["name"] if nm else "—", "points": total,
                "available": round(total - spent, 1), "redeemed": spent,
                "tier": t, "next": nxt, "breakdown": rows, "redemptions": red}

    @app.post("/api/loyalty/recompute")
    def recompute(member_type: str = "customer", user=Depends(current_user)):
        require(user, "admin", "manager")
        if member_type not in ("customer", "partner"):
            raise HTTPException(400, "Unknown member type")
        import db as D
        n = 0
        src = con.execute(
            f"SELECT id FROM {'accounts' if member_type=='customer' else 'agents'} WHERE deleted=0")
        for s in src:
            rows, total = compute(member_type, s["id"])
            t = tier_for(total)
            con.execute("""INSERT INTO loyalty_members(member_type,member_id,points,tier,lifetime,joined_at,computed_at)
                VALUES(?,?,?,?,?,?,?)
                ON CONFLICT(member_type,member_id) DO UPDATE SET
                  points=excluded.points, tier=excluded.tier,
                  lifetime=CASE WHEN loyalty_members.lifetime > excluded.points
                    THEN loyalty_members.lifetime ELSE excluded.points END,
                  computed_at=excluded.computed_at""",
                (member_type, s["id"], total, t["code"], total, D.now(), D.now()))
            con.execute("DELETE FROM loyalty_points WHERE member_type=? AND member_id=?",
                        (member_type, s["id"]))
            exp = (today() + datetime.timedelta(days=30 * POINT_EXPIRY_MONTHS)).isoformat()
            for r in rows:
                if r["points"]:
                    con.execute("""INSERT INTO loyalty_points(member_type,member_id,rule,points,
                        basis,period,expires_at,created_at) VALUES(?,?,?,?,?,?,?,?)""",
                        (member_type, s["id"], r["rule"], r["points"], r["basis"],
                         today().strftime("%Y-%m"), exp, D.now()))
            n += 1
        con.commit()
        return {"ok": True, "computed": n, "member_type": member_type}

    class Redeem(BaseModel):
        member_type: str
        member_id: int
        points: float
        reward: str
        value: float = 0
        note: str = ""

    @app.post("/api/loyalty/redeem")
    def redeem(b: Redeem, user=Depends(current_user)):
        require(user, "admin", "manager")
        if b.member_type not in ("customer", "partner"):
            raise HTTPException(400, "Unknown member type")
        table = "accounts" if b.member_type == "customer" else "agents"
        if not con.execute(f"SELECT 1 FROM {table} WHERE id=? AND deleted=0", (b.member_id,)).fetchone():
            raise HTTPException(404, "Member not found")
        if not b.reward.strip() or len(b.reward) > 500 or b.value < 0:
            raise HTTPException(400, "Invalid redemption")
        rows, total = compute(b.member_type, b.member_id)
        spent = _f(con.execute("""SELECT SUM(points) FROM loyalty_redemptions
            WHERE member_type=? AND member_id=? AND status='approved'""",
            (b.member_type, b.member_id)).fetchone()[0])
        avail = total - spent
        if b.points <= 0: raise HTTPException(400, "Points must be positive")
        if b.points > avail + 0.01:
            raise HTTPException(400, f"Not enough points (available {avail:.0f})")
        import db as D
        rid = con.execute("""INSERT INTO loyalty_redemptions(member_type,member_id,points,reward,
            "value",status,note,created_by,created_at) VALUES(?,?,?,?,?,'approved',?,?,?)""",
            (b.member_type, b.member_id, b.points, b.reward, b.value, b.note,
             user["id"], D.now())).lastrowid
        con.commit()
        return {"id": rid, "remaining": round(avail - b.points, 1)}

    @app.get("/api/loyalty/summary")
    def summary(user=Depends(current_user)):
        require(user, "admin", "manager")
        out = {}
        for mt in ("customer", "partner"):
            data = members(mt, user)
            out[mt] = {"count": len(data["members"]),
                       "points": round(sum(m["points"] for m in data["members"]), 1),
                       "distribution": data["distribution"],
                       "top": data["members"][:8]}
        out["redeemed"] = _f(con.execute(
            "SELECT SUM(points) FROM loyalty_redemptions WHERE status='approved'").fetchone()[0])
        out["tiers"] = TIERS
        return out
