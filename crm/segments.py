"""Customer classification + stagnation analytics.

Two engines:
  1. RFM-style activity scoring -> Platinum / Gold / Silver / Bronze / Dormant
  2. Stagnation reports -> dead stock and inactive customers
Plus curated lists: VIP, Loyal, Early Adopter, Distinguished, Watchlist, Blacklist.
"""
import datetime
from fastapi import Depends, HTTPException
from pydantic import BaseModel

from authz import record_or_404

con = None

SEGMENTS = {
    "Platinum": {"en": "Platinum", "ar": "بلاتيني", "color": "#a855f7", "min": 80},
    "Gold":     {"en": "Gold", "ar": "ذهبي", "color": "#f59e0b", "min": 60},
    "Silver":   {"en": "Silver", "ar": "فضي", "color": "#94a3b8", "min": 40},
    "Bronze":   {"en": "Bronze", "ar": "برونزي", "color": "#b45309", "min": 20},
    "Dormant":  {"en": "Dormant", "ar": "راكد", "color": "#64748b", "min": 0},
}

LISTS = {
    "VIP":            {"en": "VIP", "ar": "كبار العملاء", "icon": "👑", "color": "#a855f7"},
    "Loyal":          {"en": "Loyal", "ar": "الأوفياء", "icon": "🤝", "color": "#22c55e"},
    "Early Adopter":  {"en": "Early Adopter", "ar": "المبادرون", "icon": "🚀", "color": "#06b6d4"},
    "Distinguished":  {"en": "Distinguished", "ar": "المميزون", "icon": "⭐", "color": "#f59e0b"},
    "Watchlist":      {"en": "Watchlist", "ar": "قائمة المراقبة", "icon": "👁️", "color": "#f97316"},
    "Blacklist":      {"en": "Blacklist", "ar": "القائمة السوداء", "icon": "⛔", "color": "#ef4444"},
}


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def today():
    return datetime.date.today()


def days_since(s):
    if not s:
        return None
    try:
        return (today() - datetime.date.fromisoformat(str(s)[:10])).days
    except Exception:
        return None


def score_accounts():
    """RFM scoring. Returns list of dicts with score + suggested segment."""
    rows = con.execute("""
        SELECT a.id, a.name, a.segment, a.list_tag, a.created_at,
               (SELECT COUNT(*) FROM deals d WHERE d.deleted=0
                 AND CAST(d.account_id AS INTEGER)=a.id AND d.stage='Closed Won') won_deals,
               (SELECT COALESCE(SUM(d.amount),0) FROM deals d WHERE d.deleted=0
                 AND CAST(d.account_id AS INTEGER)=a.id AND d.stage='Closed Won') revenue,
               (SELECT COALESCE(SUM(i.paid_amount),0) FROM invoices i WHERE i.deleted=0
                 AND CAST(i.account_id AS INTEGER)=a.id) paid,
               (SELECT COALESCE(SUM(COALESCE(i.amount,0)-COALESCE(i.paid_amount,0)),0)
                 FROM invoices i WHERE i.deleted=0 AND CAST(i.account_id AS INTEGER)=a.id
                 AND i.status NOT IN ('Paid','Cancelled')) outstanding,
               (SELECT MAX(i.invoice_date) FROM invoices i WHERE i.deleted=0
                 AND CAST(i.account_id AS INTEGER)=a.id) last_invoice,
               (SELECT MAX(d.closing_date) FROM deals d WHERE d.deleted=0
                 AND CAST(d.account_id AS INTEGER)=a.id AND d.stage='Closed Won') last_deal,
               (SELECT COUNT(*) FROM tickets t WHERE t.deleted=0
                 AND CAST(t.account_id AS INTEGER)=a.id) tickets,
               (SELECT COUNT(*) FROM invoices i WHERE i.deleted=0
                 AND CAST(i.account_id AS INTEGER)=a.id AND i.status='Overdue') overdue
        FROM accounts a WHERE a.deleted=0""").fetchall()

    data = [dict(r) for r in rows]
    max_rev = max([_f(d["revenue"]) for d in data] or [1]) or 1
    max_freq = max([d["won_deals"] or 0 for d in data] or [1]) or 1

    for d in data:
        last = max([x for x in (d["last_invoice"], d["last_deal"]) if x], default=None)
        rec = days_since(last)
        d["last_activity"] = last
        d["days_inactive"] = rec

        # Recency 0-40
        if rec is None:
            r_s = 0
        elif rec <= 30:  r_s = 40
        elif rec <= 90:  r_s = 30
        elif rec <= 180: r_s = 20
        elif rec <= 365: r_s = 10
        else:            r_s = 0
        # Frequency 0-25
        f_s = min(25, (d["won_deals"] or 0) / max_freq * 25)
        # Monetary 0-35
        m_s = min(35, _f(d["revenue"]) / max_rev * 35)

        score = round(r_s + f_s + m_s, 1)
        if (d["overdue"] or 0) > 0:
            score = max(0, score - 8)
        d["score"] = score
        d["r_score"], d["f_score"], d["m_score"] = r_s, round(f_s, 1), round(m_s, 1)

        if _f(d["revenue"]) == 0 and not d["won_deals"]:
            seg = "Dormant" if (rec is None or rec > 180) else "Bronze"
        else:
            seg = next(k for k, v in sorted(SEGMENTS.items(), key=lambda x: -x[1]["min"])
                       if score >= v["min"])
        d["suggested"] = seg
    data.sort(key=lambda x: -x["score"])
    return data


def register(app, current_user, require):

    @app.get("/api/segments/meta")
    def meta(user=Depends(current_user)):
        return {"segments": SEGMENTS, "lists": LISTS}

    @app.get("/api/segments/scores")
    def scores(user=Depends(current_user)):
        require(user, "admin", "manager")
        data = score_accounts()
        dist = {}
        for d in data:
            dist[d["suggested"]] = dist.get(d["suggested"], 0) + 1
        lists = [dict(r) for r in con.execute("""
            SELECT COALESCE(a.list_tag,'—') k, COUNT(DISTINCT a.id) n,
                   COALESCE(SUM(CASE WHEN d.stage='Closed Won' THEN d.amount ELSE 0 END),0) v
            FROM accounts a
            LEFT JOIN deals d ON d.deleted=0 AND d.stage='Closed Won'
              AND CAST(d.account_id AS INTEGER)=a.id
            WHERE a.deleted=0
            GROUP BY COALESCE(a.list_tag,'—')""")]
        return {"accounts": data, "distribution": dist, "lists": lists,
                "meta": {"segments": SEGMENTS, "lists": LISTS}}

    @app.post("/api/segments/apply")
    def apply(user=Depends(current_user)):
        """Write the computed segment back onto every account."""
        require(user, "admin", "manager")
        n = 0
        for d in score_accounts():
            if d["segment"] != d["suggested"]:
                con.execute("UPDATE accounts SET segment=?, updated_at=? WHERE id=?",
                            (d["suggested"], datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds"), d["id"]))
                n += 1
        con.commit()
        return {"ok": True, "updated": n}

    class TagBody(BaseModel):
        account_ids: list[int]
        list_tag: str
        reason: str = ""

    @app.post("/api/segments/tag")
    def tag(b: TagBody, user=Depends(current_user)):
        require(user, "admin", "manager")
        if len(b.account_ids) > 200:
            raise HTTPException(400, "At most 200 accounts can be tagged at once")
        if b.list_tag and b.list_tag not in LISTS:
            raise HTTPException(400, "Unknown list")
        if b.list_tag == "Blacklist":
            require(user, "admin", "manager")
            if not b.reason.strip():
                raise HTTPException(400, "A reason is required to blacklist a customer")
        ts = datetime.datetime.now(datetime.UTC).replace(tzinfo=None).isoformat(timespec="seconds")
        for aid in b.account_ids:
            record_or_404(con, "accounts", int(aid), user)
            con.execute("UPDATE accounts SET list_tag=?, blacklist_reason=?, updated_at=? WHERE id=?",
                        (b.list_tag or None, b.reason if b.list_tag == "Blacklist" else None, ts, aid))
            import db as D
            D.log(con, "accounts", aid, "list_tag", {"list": b.list_tag, "reason": b.reason}, user["id"])
        con.commit()
        return {"ok": True, "tagged": len(b.account_ids)}

    @app.get("/api/segments/list/{name}")
    def list_members(name: str, user=Depends(current_user)):
        require(user, "admin", "manager")
        if name not in LISTS:
            raise HTTPException(404, "Unknown list")
        rows = [dict(r) for r in con.execute("""
            SELECT a.*, (SELECT COALESCE(SUM(d.amount),0) FROM deals d WHERE d.deleted=0
                AND d.stage='Closed Won' AND CAST(d.account_id AS INTEGER)=a.id) revenue
            FROM accounts a WHERE a.deleted=0 AND a.list_tag=? ORDER BY revenue DESC""", (name,))]
        return {"list": name, "meta": LISTS[name], "members": rows,
                "total_revenue": sum(_f(r["revenue"]) for r in rows)}

    @app.get("/api/segments/blacklist-check/{account_id}")
    def blacklist_check(account_id: int, user=Depends(current_user)):
        r = record_or_404(con, "accounts", account_id, user)
        return {"blocked": r["list_tag"] == "Blacklist", "name": r["name"],
                "reason": r["blacklist_reason"], "list": r["list_tag"]}

    # ---------------- stagnation ----------------
    @app.get("/api/reports/stagnant-products")
    def stagnant_products(days: int = 90, user=Depends(current_user)):
        """Dead stock: never sold, or not sold within N days, plus capital tied up."""
        require(user, "admin", "manager")
        days = min(3650, max(1, days))
        cutoff = (today() - datetime.timedelta(days=days)).isoformat()
        rows = []
        for p in con.execute("SELECT * FROM products WHERE deleted=0"):
            sold = con.execute("""
                SELECT COALESCE(SUM(li.qty),0) qty, COUNT(*) lines,
                       MAX(i.invoice_date) last_sold,
                       COALESCE(SUM(li.qty*li.price),0) revenue
                FROM line_items li
                JOIN invoices i ON i.id=li.record_id AND i.deleted=0
                     AND i.status NOT IN ('Draft','Cancelled')
                WHERE li.module='invoices' AND li.product_id=?""", (p["id"],)).fetchone()
            quoted = con.execute("""
                SELECT COUNT(*) n FROM line_items li JOIN quotes q ON q.id=li.record_id
                AND q.deleted=0 WHERE li.module='quotes' AND li.product_id=?""",
                (p["id"],)).fetchone()["n"]
            last = sold["last_sold"]
            idle = days_since(last)
            stock = _f(p["qty_in_stock"])
            cost = _f(p["cost"]) or _f(p["unit_price"]) * 0.55
            if last and idle is not None and idle <= days:
                continue  # moving fine
            rows.append({
                "id": p["id"], "name": p["name"], "code": p["code"], "category": p["category"],
                "qty_in_stock": stock, "unit_price": _f(p["unit_price"]), "cost": round(cost, 2),
                "tied_capital": round(stock * cost, 2),
                "units_sold": _f(sold["qty"]), "revenue": _f(sold["revenue"]),
                "times_quoted": quoted,
                "last_sold": last, "days_idle": idle,
                "status": ("Quoted, Never Sold" if (not last and quoted) else
                           "Never Sold" if not last else
                           "Critical" if idle and idle > 365 else "Stagnant"),
                "reorder_level": _f(p["reorder_level"]), "active": p["active"],
            })
        rows.sort(key=lambda x: -x["tied_capital"])
        return {"days": days, "rows": rows,
                "total_tied": round(sum(r["tied_capital"] for r in rows), 2),
                "never_sold": sum(1 for r in rows if "Never Sold" in r["status"]),
                "quoted_not_sold": sum(1 for r in rows if r["status"] == "Quoted, Never Sold"),
                "critical": sum(1 for r in rows if r["status"] == "Critical")}

    @app.get("/api/reports/stagnant-customers")
    def stagnant_customers(days: int = 180, user=Depends(current_user)):
        """Customers who stopped buying — with revenue at risk."""
        require(user, "admin", "manager")
        days = min(3650, max(1, days))
        data = score_accounts()
        rows = []
        for d in data:
            idle = d["days_inactive"]
            if idle is not None and idle <= days:
                continue
            rows.append({
                "id": d["id"], "name": d["name"], "segment": d["segment"],
                "suggested": d["suggested"], "list_tag": d["list_tag"],
                "revenue": _f(d["revenue"]), "won_deals": d["won_deals"],
                "outstanding": _f(d["outstanding"]), "tickets": d["tickets"],
                "last_activity": d["last_activity"], "days_inactive": idle,
                "score": d["score"],
                "risk": "Lost" if (idle is None or idle > 540) else
                        ("High" if idle > 365 else "Medium"),
            })
        rows.sort(key=lambda x: -x["revenue"])
        return {"days": days, "rows": rows,
                "revenue_at_risk": round(sum(r["revenue"] for r in rows), 2),
                "outstanding_at_risk": round(sum(r["outstanding"] for r in rows), 2),
                "never_bought": sum(1 for r in rows if r["revenue"] == 0)}

    # ---------------- opportunity pipeline ----------------
    @app.get("/api/opportunities/analytics")
    def opp_analytics(user=Depends(current_user)):
        require(user, "admin", "manager")
        g = lambda s: con.execute(s).fetchone()[0] or 0
        by_stage = [dict(r) for r in con.execute("""
            SELECT stage k, COUNT(*) n, SUM("value") v FROM opportunities
            WHERE deleted=0 GROUP BY stage""")]
        by_outcome = [dict(r) for r in con.execute("""
            SELECT COALESCE(outcome,'Potential') k, COUNT(*) n, SUM("value") v
            FROM opportunities WHERE deleted=0 GROUP BY COALESCE(outcome,'Potential')""")]
        win_reasons = [dict(r) for r in con.execute("""
            SELECT COALESCE(win_reason,'—') k, COUNT(*) n, SUM("value") v FROM opportunities
            WHERE deleted=0 AND outcome='Won' GROUP BY COALESCE(win_reason,'—') ORDER BY n DESC""")]
        loss_reasons = [dict(r) for r in con.execute("""
            SELECT COALESCE(loss_reason,'—') k, COUNT(*) n, SUM("value") v FROM opportunities
            WHERE deleted=0 AND outcome='Lost' GROUP BY COALESCE(loss_reason,'—') ORDER BY v DESC""")]
        sources = [dict(r) for r in con.execute("""
            SELECT COALESCE(source,'—') k, COUNT(*) n, SUM("value") v,
                   SUM(CASE WHEN outcome='Won' THEN 1 ELSE 0 END) won
            FROM opportunities WHERE deleted=0 GROUP BY COALESCE(source,'—') ORDER BY v DESC""")]
        won = g("SELECT COUNT(*) FROM opportunities WHERE deleted=0 AND outcome='Won'")
        lost = g("SELECT COUNT(*) FROM opportunities WHERE deleted=0 AND outcome='Lost'")
        return {
            "kpi": {
                "potential": g("SELECT COUNT(*) FROM opportunities WHERE deleted=0 AND outcome='Potential'"),
                "potential_value": g("""SELECT SUM("value") FROM opportunities
                                        WHERE deleted=0 AND outcome='Potential'"""),
                "weighted": g("""SELECT SUM("value"*COALESCE(probability,0)/100.0)
                                 FROM opportunities WHERE deleted=0 AND outcome='Potential'"""),
                "won": won, "lost": lost,
                "won_value": g("""SELECT SUM("value") FROM opportunities
                                    WHERE deleted=0 AND outcome='Won'"""),
                "lost_value": g("""SELECT SUM("value") FROM opportunities
                                     WHERE deleted=0 AND outcome='Lost'"""),
                "win_rate": round(won / (won + lost) * 100, 1) if (won + lost) else 0,
            },
            "by_stage": by_stage, "by_outcome": by_outcome,
            "win_reasons": win_reasons, "loss_reasons": loss_reasons, "sources": sources,
        }

    @app.post("/api/opportunities/{oid}/convert")
    def convert_opp(oid: int, user=Depends(current_user)):
        """Won opportunity -> real deal."""
        if user["role"] == "readonly":
            raise HTTPException(403, "Read-only user")
        o = record_or_404(con, "opportunities", oid, user)
        if o["deal_id"]:
            raise HTTPException(400, "Already converted")
        chk = con.execute("SELECT list_tag FROM accounts WHERE id=CAST(? AS INTEGER)",
                          (o["account_id"],)).fetchone()
        if chk and chk["list_tag"] == "Blacklist":
            raise HTTPException(403, "This account is blacklisted — conversion blocked")
        import db as D
        ts = D.now()
        did = con.execute("""INSERT INTO deals(created_at,updated_at,created_by,owner_id,deleted,
            name,account_id,contact_id,amount,stage,probability,closing_date,source,competitor_id)
            VALUES(?,?,?,?,0,?,?,?,?,?,?,?,?,?)""",
            (ts, ts, user["id"], o["owner_id"], o["name"], o["account_id"], o["contact_id"],
             o["value"], "Qualification", o["probability"] or 20,
             o["expected_close"], o["source"], o["competitor_id"])).lastrowid
        con.execute("UPDATE opportunities SET deal_id=?, outcome='Won', stage='Won', actual_close=?, updated_at=? WHERE id=?",
                    (did, today().isoformat(), ts, oid))
        D.log(con, "opportunities", oid, "convert", {"deal": did}, user["id"])
        con.commit()
        return {"deal_id": did}
