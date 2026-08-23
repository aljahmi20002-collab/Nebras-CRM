import sys, os, random, datetime
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import db as D

random.seed(23)
con = D.init()
if con.execute("SELECT COUNT(*) c FROM opportunities WHERE deleted=0").fetchone()["c"]:
    print("already seeded"); sys.exit()

uids = [r["id"] for r in con.execute("SELECT id FROM users WHERE role!='readonly'")]
accs = [r["id"] for r in con.execute("SELECT id FROM accounts WHERE deleted=0")]
cts  = [r["id"] for r in con.execute("SELECT id FROM contacts WHERE deleted=0")]
comps= [r["id"] for r in con.execute("SELECT id FROM competitors WHERE deleted=0")]

def d(n): return (datetime.date.today() + datetime.timedelta(days=n)).isoformat()
def ins(t, **kw):
    kw.update(created_at=D.now(), updated_at=D.now(), deleted=0)
    kw.setdefault("owner_id", random.choice(uids)); kw.setdefault("created_by", 1)
    k = list(kw)
    return con.execute(f'INSERT INTO "{t}" ({",".join(chr(34)+x+chr(34) for x in k)}) '
                       f'VALUES ({",".join("?"*len(k))})', [kw[x] for x in k]).lastrowid

NAMES = ["توسعة المنصة","ترخيص إضافي","تجديد سنوي","مشروع تكامل","بوابة عملاء","وحدة الفوترة",
 "ترقية للنسخة المؤسسية","عقد دعم ممتد","تدريب الفريق","ترحيل بيانات","تطبيق جوال","تكامل ERP"]
STAGES = ["Identified","Qualifying","Evaluating","Proposal","Negotiation","Won","Lost","On Hold"]
PROB = {"Identified":10,"Qualifying":25,"Evaluating":40,"Proposal":60,"Negotiation":80,
        "Won":100,"Lost":0,"On Hold":15}
SRC = ["Inbound","Outbound","Referral","Partner","Campaign","Existing Customer","Tender"]
WIN = ["Price","Features","Relationship","Speed","Support","Brand"]
LOSS= ["Price","Features","Competitor","No Budget","No Decision","Timing","Lost Contact"]

n_opp = 0
for i in range(70):
    st = random.choices(STAGES, [5,5,4,4,3,5,4,2])[0]
    out = "Won" if st == "Won" else ("Lost" if st == "Lost" else "Potential")
    val = random.randint(4, 180) * 1000
    prob = PROB[st]
    closed = out in ("Won", "Lost")
    ins("opportunities",
        name=f"{random.choice(NAMES)} — {random.choice(['سبأفون','يمن سوفت','بنك الأمل','عدن للخدمات اللوجستية','تهامة الصناعية','النسر للتقنية'])}",
        account_id=random.choice(accs), contact_id=random.choice(cts),
        stage=st, outcome=out, value=val, probability=prob,
        weighted_value=round(val*prob/100,2),
        expected_close=d(random.randint(5,150)) if not closed else d(-random.randint(1,120)),
        actual_close=d(-random.randint(1,120)) if closed else None,
        source=random.choice(SRC),
        competitor_id=random.choice(comps) if random.random()<0.55 else None,
        win_reason=random.choice(WIN) if out=="Won" else None,
        loss_reason=random.choices(LOSS,[6,3,4,3,2,2,1])[0] if out=="Lost" else None,
        next_step=random.choice(["إرسال العرض","اجتماع تقني","انتظار الموافقة","عرض توضيحي","مراجعة العقد"]))
    n_opp += 1

# ---- products that never move (dead stock) ----
DEAD = [("راوتر مؤسسي RX-900","Hardware",2400,45),("خادم تخزين S3","Hardware",14000,8),
        ("رخصة تحليلات قديمة","Software",900,120),("كرت شبكة 10G","Hardware",680,90),
        ("طابعة باركود صناعية","Hardware",1900,25),("حزمة تدريب مطبوعة","Services",300,200)]
for nm, cat, pr, qty in DEAD:
    ins("products", name=nm, code=f"D-{random.randint(1000,9999)}", category=cat,
        unit_price=pr, cost=round(pr*0.6), qty_in_stock=qty, reorder_level=10,
        tax_rate=15, active="Yes", description="مخزون بطيء الحركة.")

# ---- dormant customers ----
DORMANT = ["مؤسسة الرواد للتجارة","شركة البحر الأحمر للنقل","مجموعة اليمن الحديثة",
           "مصنع الشرق للبلاستيك","مكتب النور للاستشارات"]
for nm in DORMANT:
    aid = ins("accounts", name=nm, industry=random.choice(["Retail","Logistics","Construction"]),
        type="Customer", phone=f"+967-1-{random.randint(200000,999999)}",
        annual_revenue=random.randint(100,900)*1000, employees=random.randint(15,300),
        segment="Dormant", billing_address="اليمن")
    # an old won deal so they have history but no recent activity
    ins("deals", name=f"{nm} — عقد قديم", account_id=aid, amount=random.randint(8,60)*1000,
        stage="Closed Won", probability=100, closing_date=d(-random.randint(400,900)))

# ---- classification tags ----
rows = con.execute("""SELECT a.id,(SELECT COALESCE(SUM(d.amount),0) FROM deals d
    WHERE d.deleted=0 AND d.stage='Closed Won' AND CAST(d.account_id AS INTEGER)=a.id) rev
    FROM accounts a WHERE a.deleted=0 ORDER BY rev DESC""").fetchall()
tags = (["VIP"]*3 + ["Loyal"]*4 + ["Distinguished"]*3 + ["Early Adopter"]*3 +
        ["Watchlist"]*2 + ["Blacklist"]*2)
for i, r in enumerate(rows):
    if i < len(tags):
        reason = "تعثر سداد متكرر وشيكات مرتجعة" if tags[i] == "Blacklist" else None
        con.execute("UPDATE accounts SET list_tag=?, blacklist_reason=? WHERE id=?",
                    (tags[i], reason, r["id"]))

# ---- extra payments across many channels ----
import gateways as G
paid_ch = ["jawali","jaib","onecash","kuraimi","bindowal","stripe","visa","mastercard",
           "mada","tap","paypal","prepaid_card","scratch_card","stcpay","western_union"]
invs = [r["id"] for r in con.execute(
    "SELECT id FROM invoices WHERE deleted=0 AND status='Paid' LIMIT 14")]
import secrets
for i, inv in enumerate(invs):
    ch = paid_ch[i % len(paid_ch)]
    row = con.execute("SELECT amount FROM invoices WHERE id=?", (inv,)).fetchone()
    amt = float(row["amount"] or 0)
    fee = G.compute_fee(ch, amt)
    con.execute("""INSERT INTO payments(invoice_id,amount,currency,method,status,provider,token,
        created_at,paid_at,channel,fee,net,provider_ref,payer_ref)
        VALUES(?,?,?,?,'paid',?,?,?,?,?,?,?,?,?)""",
        (inv, amt, "USD", G.BY_CODE[ch]["name_en"], ch, secrets.token_urlsafe(18),
         D.now(), D.now(), ch, fee, round(amt-fee,2),
         f"{ch.upper()[:6]}-{secrets.token_hex(4).upper()}", "****1234"))

con.commit()
print(f"seeded {n_opp} opportunities, {len(DEAD)} dead-stock products, "
      f"{len(DORMANT)} dormant accounts, tagged {min(len(tags),len(rows))} lists, "
      f"{len(invs)} multi-channel payments")
