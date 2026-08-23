"""Market & Competitive Intelligence analytics.

Turns the competitors / competitor_products / market_research modules into
decision-grade insight: win-loss per competitor, price gap analysis, battlecards,
and market sizing rollups.
"""
import datetime
from fastapi import Depends, HTTPException

con = None  # injected


def _f(v):
    try:
        return float(v or 0)
    except (TypeError, ValueError):
        return 0.0


def register(app, current_user, require):

    @app.get("/api/intel/dashboard")
    def intel_dashboard(user=Depends(current_user)):
        g = lambda s, p=(): con.execute(s, p).fetchone()[0] or 0

        # ---- win/loss against each competitor ----
        rows = con.execute("""
            SELECT c.id, c.name k, c.tier, c.threat_score,
                   COUNT(d.id) total,
                   SUM(CASE WHEN d.stage='Closed Won'  THEN 1 ELSE 0 END) won,
                   SUM(CASE WHEN d.stage='Closed Lost' THEN 1 ELSE 0 END) lost,
                   SUM(CASE WHEN d.stage='Closed Lost' THEN d.amount ELSE 0 END) lost_value,
                   SUM(CASE WHEN d.stage='Closed Won'  THEN d.amount ELSE 0 END) won_value
            FROM competitors c
            LEFT JOIN deals d ON CAST(d.competitor_id AS INTEGER)=c.id AND d.deleted=0
            WHERE c.deleted=0 GROUP BY c.id ORDER BY lost_value DESC""").fetchall()
        winloss = []
        for r in rows:
            d = dict(r)
            closed = (d["won"] or 0) + (d["lost"] or 0)
            d["win_rate"] = round((d["won"] or 0) / closed * 100, 1) if closed else None
            winloss.append(d)

        # ---- why we lose ----
        loss_reasons = [dict(r) for r in con.execute("""
            SELECT COALESCE(loss_reason,'Unspecified') k, COUNT(*) n, SUM(amount) v
            FROM deals WHERE deleted=0 AND stage='Closed Lost' GROUP BY 1 ORDER BY v DESC""")]

        # ---- price positioning ----
        price_gap = []
        for r in con.execute("""
            SELECT cp.name, cp.price, cp.our_price, cp.positioning, cp.category, cp.billing,
                   c.name competitor
            FROM competitor_products cp LEFT JOIN competitors c ON c.id=CAST(cp.competitor_id AS INTEGER)
            WHERE cp.deleted=0 AND cp.price IS NOT NULL"""):
            d = dict(r)
            their, ours = _f(d["price"]), _f(d["our_price"])
            d["gap"] = round(ours - their, 2)
            d["gap_pct"] = round((ours - their) / their * 100, 1) if their else None
            price_gap.append(d)
        price_gap.sort(key=lambda x: abs(x["gap_pct"] or 0), reverse=True)

        positioning = [dict(r) for r in con.execute("""
            SELECT COALESCE(positioning,'Unknown') k, COUNT(*) n FROM competitor_products
            WHERE deleted=0 GROUP BY 1""")]

        tiers = [dict(r) for r in con.execute("""
            SELECT COALESCE(tier,'—') k, COUNT(*) n, AVG(threat_score) avg_threat,
                   SUM(market_share) share FROM competitors WHERE deleted=0 GROUP BY 1""")]

        share = [dict(r) for r in con.execute("""
            SELECT name k, COALESCE(market_share,0) v FROM competitors
            WHERE deleted=0 AND market_share IS NOT NULL ORDER BY v DESC LIMIT 12""")]
        our_share = _f(con.execute(
            "SELECT AVG(our_share) FROM market_research WHERE deleted=0 AND our_share IS NOT NULL"
        ).fetchone()[0])

        studies = [dict(r) for r in con.execute("""
            SELECT COALESCE(status,'—') k, COUNT(*) n FROM market_research
            WHERE deleted=0 GROUP BY 1""")]

        tam = [dict(r) for r in con.execute("""
            SELECT COALESCE(segment,'—') k, SUM(market_size) v, AVG(growth_rate) g
            FROM market_research WHERE deleted=0 AND market_size IS NOT NULL GROUP BY 1 ORDER BY v DESC""")]

        return {
            "kpi": {
                "competitors": g("SELECT COUNT(*) FROM competitors WHERE deleted=0"),
                "primary_threats": g("SELECT COUNT(*) FROM competitors WHERE deleted=0 AND tier='Primary'"),
                "tracked_products": g("SELECT COUNT(*) FROM competitor_products WHERE deleted=0"),
                "studies": g("SELECT COUNT(*) FROM market_research WHERE deleted=0"),
                "active_studies": g("SELECT COUNT(*) FROM market_research WHERE deleted=0 AND status='In Progress'"),
                "tam": g("SELECT SUM(market_size) FROM market_research WHERE deleted=0"),
                "avg_growth": round(_f(g("SELECT AVG(growth_rate) FROM market_research WHERE deleted=0 AND growth_rate IS NOT NULL")), 1),
                "our_share": round(our_share, 1),
                "contested_pipeline": g("""SELECT SUM(amount) FROM deals WHERE deleted=0
                    AND competitor_id IS NOT NULL AND competitor_id!=''
                    AND stage NOT IN ('Closed Won','Closed Lost')"""),
                "lost_to_competitors": g("""SELECT SUM(amount) FROM deals WHERE deleted=0
                    AND stage='Closed Lost' AND competitor_id IS NOT NULL AND competitor_id!=''"""),
            },
            "winloss": winloss, "loss_reasons": loss_reasons, "price_gap": price_gap[:15],
            "positioning": positioning, "tiers": tiers, "share": share,
            "studies": studies, "tam": tam,
        }

    @app.get("/api/intel/battlecard/{cid}")
    def battlecard(cid: int, user=Depends(current_user)):
        """Everything a rep needs when facing this competitor in a live deal."""
        c = con.execute("SELECT * FROM competitors WHERE id=? AND deleted=0", (cid,)).fetchone()
        if not c:
            raise HTTPException(404, "Competitor not found")
        comp = dict(c)

        prods = []
        for r in con.execute("""
            SELECT cp.*, p.name our_product_name, p.unit_price our_list
            FROM competitor_products cp
            LEFT JOIN products p ON p.id=CAST(cp.our_product_id AS INTEGER)
            WHERE cp.deleted=0 AND CAST(cp.competitor_id AS INTEGER)=?""", (cid,)):
            d = dict(r)
            their = _f(d["price"]); ours = _f(d["our_price"]) or _f(d["our_list"])
            d["our_effective"] = ours
            d["gap"] = round(ours - their, 2)
            d["gap_pct"] = round((ours - their) / their * 100, 1) if their else None
            prods.append(d)

        deals = [dict(r) for r in con.execute("""
            SELECT d.id, d.name, d.amount, d.stage, d.closing_date, d.loss_reason, a.name account
            FROM deals d LEFT JOIN accounts a ON a.id=CAST(d.account_id AS INTEGER)
            WHERE d.deleted=0 AND CAST(d.competitor_id AS INTEGER)=?
            ORDER BY d.id DESC LIMIT 50""", (cid,))]
        won = [d for d in deals if d["stage"] == "Closed Won"]
        lost = [d for d in deals if d["stage"] == "Closed Lost"]
        openv = [d for d in deals if d["stage"] not in ("Closed Won", "Closed Lost")]

        reasons = [dict(r) for r in con.execute("""
            SELECT COALESCE(loss_reason,'Unspecified') k, COUNT(*) n FROM deals
            WHERE deleted=0 AND stage='Closed Lost' AND CAST(competitor_id AS INTEGER)=?
            GROUP BY 1 ORDER BY n DESC""", (cid,))]

        studies = [dict(r) for r in con.execute("""
            SELECT id,title,type,status,findings FROM market_research
            WHERE deleted=0 AND type='Competitor Analysis' ORDER BY id DESC LIMIT 5""")]

        closed = len(won) + len(lost)
        return {
            "competitor": comp, "products": prods,
            "stats": {
                "total_deals": len(deals), "won": len(won), "lost": len(lost), "open": len(openv),
                "win_rate": round(len(won) / closed * 100, 1) if closed else None,
                "won_value": sum(_f(d["amount"]) for d in won),
                "lost_value": sum(_f(d["amount"]) for d in lost),
                "open_value": sum(_f(d["amount"]) for d in openv),
                "avg_gap_pct": round(sum(p["gap_pct"] or 0 for p in prods) / len(prods), 1) if prods else None,
            },
            "loss_reasons": reasons, "deals": deals[:15], "studies": studies,
        }

    @app.get("/api/intel/matrix")
    def matrix(user=Depends(current_user)):
        """Feature/price comparison matrix: our products vs each competitor's."""
        ours = [dict(r) for r in con.execute(
            "SELECT id,name,unit_price,category FROM products WHERE deleted=0 ORDER BY name")]
        rows = []
        for p in ours:
            rivals = [dict(r) for r in con.execute("""
                SELECT cp.name, cp.price, cp.our_price, cp.billing, cp.positioning,
                       cp.key_features, cp.gaps, c.name competitor, c.id competitor_id
                FROM competitor_products cp LEFT JOIN competitors c ON c.id=CAST(cp.competitor_id AS INTEGER)
                WHERE cp.deleted=0 AND CAST(cp.our_product_id AS INTEGER)=?""", (p["id"],))]
            if not rivals:
                continue
            prices = [_f(r["price"]) for r in rivals if _f(r["price"])]
            ours_puy = next((_f(r["our_price"]) for r in rivals if _f(r["our_price"])), _f(p["unit_price"]))
            rows.append({
                "product": p["name"], "our_price": ours_puy, "list_price": _f(p["unit_price"]),
                "basis": "Per User / Year", "category": p["category"],
                "rivals": rivals, "rival_count": len(rivals),
                "market_low": min(prices) if prices else None,
                "market_high": max(prices) if prices else None,
                "market_avg": round(sum(prices) / len(prices), 2) if prices else None,
            })
        return {"rows": rows}
