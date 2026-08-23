import sys, os, random, datetime, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db as D, partners as PT

random.seed(41)
con = D.init(); PT.con = con; PT.init_tables(con)

if con.execute("SELECT COUNT(*) c FROM agents WHERE deleted=0").fetchone()["c"]:
    print("already seeded"); sys.exit()

govs = [dict(r) for r in con.execute("SELECT id,name_ar FROM geo_governorates")]
gmap = {g["name_ar"]: g["id"] for g in govs}
def dis_of(gid):
    r = con.execute("SELECT id,name_ar FROM geo_districts WHERE gov_id=? ORDER BY RANDOM() LIMIT 1",(gid,)).fetchone()
    return (r["id"], r["name_ar"]) if r else (None, None)

# ---- 1. give every account a real Yemeni location ----
main_govs = ["أمانة العاصمة","عدن","تعز","الحديدة","حضرموت","إب","ذمار","حجه","المكلا" ]
pool = [gmap[g] for g in main_govs if g in gmap] or [g["id"] for g in govs[:6]]
n_loc = 0
for a in con.execute("SELECT id FROM accounts WHERE deleted=0"):
    gid = random.choice(pool)
    did, _ = dis_of(gid)
    uz = con.execute("SELECT id FROM geo_uzlah WHERE district_id=? ORDER BY RANDOM() LIMIT 1",(did,)).fetchone()
    vil = con.execute("SELECT id FROM geo_villages WHERE uzlah_id=? ORDER BY RANDOM() LIMIT 1",
                      (uz["id"],)).fetchone() if uz else None
    con.execute("UPDATE accounts SET gov_id=?, district_id=?, village_id=? WHERE id=?",
                (gid, did, vil["id"] if vil else None, a["id"]))
    n_loc += 1

# ---- 2. quarters + streets (user-managed levels) ----
QUARTERS = ["حارة الجراف","حارة السنينة","حارة القاع","حارة شملان","حارة بئر العزب","حارة التحرير",
            "حارة الصافية","حارة حدة","حارة المعلا","حارة كريتر","حارة الشيخ عثمان","حارة المنصورة"]
STREETS = ["شارع الزبيري","شارع حدة","شارع الستين","شارع الرباط","شارع تعز","شارع الجزائر",
           "شارع القيادة","شارع جمال","شارع الملكة أروى","شارع المطار","شارع الخمسين","شارع صنعاء"]
qids = []
for q in QUARTERS:
    gid = random.choice(pool); did, _ = dis_of(gid)
    qids.append(con.execute("""INSERT INTO geo_quarters(district_id,name_ar,name_en,created_at)
        VALUES(?,?,?,?)""", (did, q, "", D.now())).lastrowid)
for s in STREETS:
    con.execute("""INSERT INTO geo_streets(quarter_id,district_id,name_ar,name_en,created_at)
        VALUES(?,?,?,?,?)""", (random.choice(qids), None, s, "", D.now()))

# ---- 3. partners ----
PARTNERS = [
 ("وكالة الأمين للتوزيع","agent","أمانة العاصمة","tiered",0,420000),
 ("مؤسسة عدن الحديثة للتجارة","distributor","عدن","tiered",0,380000),
 ("وكالة تعز التجارية","agent","تعز","percent",5.0,260000),
 ("شركة الحديدة للتوزيع","distributor","الحديدة","percent",4.0,210000),
 ("مؤسسة حضرموت للتقنية","agent","حضرموت","tiered",0,340000),
 ("وكالة إب المركزية","agent","إب","percent",4.5,180000),
 ("مندوب ذمار — أحمد الشرعبي","rep","ذمار","percent",3.0,90000),
 ("مندوب حجة — سالم الأهدل","rep","حجه","percent",3.0,70000),
 ("مندوب المكلا — عمر باوزير","rep","حضرموت","flat",500,110000),
 ("وسيط المناقصات الحكومية","broker","أمانة العاصمة","percent",2.0,150000),
]
TIERS_JSON = json.dumps(PT.DEFAULT_TIERS)
aids = []
for i,(nm, ty, gov, model, rate, target) in enumerate(PARTNERS):
    gid = gmap.get(gov, pool[0]); did, _ = dis_of(gid)
    aid = con.execute("""INSERT INTO agents(code,name,type,phone,email,gov_id,district_id,
        commission_model,commission_rate,tiers,target,credit_limit,status,rating,
        joined_at,created_at,updated_at,deleted,address)
        VALUES(?,?,?,?,?,?,?,?,?,?,?,?,'Active',?,?,?,?,0,?)""",
        (f"AG-{1001+i}", nm, ty, f"+967-7{random.randint(0,7)}-{random.randint(1000000,9999999)}",
         f"agent{i}@partners.ye", gid, did, model, rate,
         TIERS_JSON if model=="tiered" else None, target,
         random.choice([0,5000,10000,20000]), round(random.uniform(3.2,4.9),1),
         (datetime.date.today()-datetime.timedelta(days=random.randint(120,1500))).isoformat(),
         D.now(), D.now(), gov)).lastrowid
    aids.append(aid)

# ---- 4. attach deals & accounts to partners ----
n_d = 0
for dl in con.execute("SELECT id FROM deals WHERE deleted=0"):
    if random.random() < 0.62:
        con.execute("UPDATE deals SET agent_id=? WHERE id=?", (random.choice(aids), dl["id"]))
        n_d += 1
for a in con.execute("SELECT id FROM accounts WHERE deleted=0"):
    if random.random() < 0.5:
        con.execute("UPDATE accounts SET agent_id=? WHERE id=?", (random.choice(aids), a["id"]))

# ---- 5. territories ----
n_t = 0
used = set()
for aid, (nm, ty, gov, *_ ) in zip(aids, PARTNERS):
    gid = gmap.get(gov)
    if not gid or gid in used or ty == "broker": continue
    con.execute("""INSERT INTO territories(agent_id,gov_id,exclusive,created_at)
                   VALUES(?,?,1,?)""", (aid, gid, D.now()))
    used.add(gid); n_t += 1

# ---- 6. consigned stock ----
prods = [r["id"] for r in con.execute("SELECT id FROM products WHERE deleted=0 LIMIT 8")]
for aid in aids[:6]:
    for p in random.sample(prods, random.randint(2,4)):
        cons = random.randint(10,120); sold = random.randint(0,cons)
        con.execute("""INSERT INTO agent_stock(agent_id,product_id,qty,consigned,sold,updated_at)
            VALUES(?,?,?,?,?,?)""", (aid, p, cons-sold, cons, sold, D.now()))

con.commit()

# ---- 7. accrue commissions then simulate payouts/advances ----
import importlib
posted = total = 0
done = set()
for d in con.execute("""SELECT id,name,amount,agent_id,closing_date FROM deals
    WHERE deleted=0 AND stage='Closed Won' AND agent_id IS NOT NULL"""):
    ag = con.execute("SELECT * FROM agents WHERE id=CAST(? AS INTEGER)",(d["agent_id"],)).fetchone()
    if not ag: continue
    ag = dict(ag)
    vol = con.execute("""SELECT COALESCE(SUM(amount),0) v FROM deals WHERE deleted=0
        AND stage='Closed Won' AND CAST(agent_id AS INTEGER)=?""",(ag["id"],)).fetchone()["v"]
    amt, rate = PT.compute_commission(ag, float(d["amount"] or 0), float(vol))
    if amt<=0: continue
    con.execute("""INSERT INTO agent_txn(agent_id,kind,amount,ref_module,ref_id,note,period,
        created_by,created_at) VALUES(?,'commission',?,'deals',?,?,?,1,?)""",
        (ag["id"], amt, d["id"], f'{d["name"]} @ {rate}%' if rate else d["name"],
         (d["closing_date"] or "")[:7], D.now()))
    posted+=1; total+=amt
# payouts (never more than owed) + a few advances/bonuses
for aid in aids:
    bal = PT.balance(aid)["balance"]
    if bal > 1000:
        pay = round(bal * random.uniform(0.3,0.7), 2)
        con.execute("""INSERT INTO agent_txn(agent_id,kind,amount,note,period,created_by,created_at)
            VALUES(?,'payout',?,'صرف دفعة مستحقات',?,1,?)""",
            (aid, pay, datetime.date.today().strftime("%Y-%m"), D.now()))
    if random.random()<0.4:
        con.execute("""INSERT INTO agent_txn(agent_id,kind,amount,note,period,created_by,created_at)
            VALUES(?,'bonus',?,'مكافأة تجاوز الهدف',?,1,?)""",
            (aid, random.choice([500,1000,1500]), datetime.date.today().strftime("%Y-%m"), D.now()))
    if random.random()<0.3:
        con.execute("""INSERT INTO agent_txn(agent_id,kind,amount,note,period,created_by,created_at)
            VALUES(?,'advance',?,'سلفة على الحساب',?,1,?)""",
            (aid, random.choice([1000,2000,3000]), datetime.date.today().strftime("%Y-%m"), D.now()))
con.commit()
print(f"located {n_loc} accounts | {len(QUARTERS)} quarters, {len(STREETS)} streets | "
      f"{len(aids)} partners | {n_d} deals linked | {n_t} territories | "
      f"{posted} commissions ({total:,.0f})")
