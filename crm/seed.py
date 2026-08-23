import random, datetime, os, sys
sys.path.insert(0, os.path.dirname(__file__))
import db as D
from main import hash_pw
from schema import MODULES, DEAL_STAGES

random.seed(7)
con = D.init()

if con.execute("SELECT COUNT(*) c FROM users").fetchone()["c"]:
    print("already seeded"); sys.exit()

USERS = [
    ("admin@nebrascrm.io", "admin123", "Omar Al-Hadhrami", "admin", 500000),
    ("manager@nebrascrm.io", "manager123", "Layla Nasser", "manager", 400000),
    ("sara@nebrascrm.io", "sara123", "Sara Kamal", "agent", 250000),
    ("yousef@nebrascrm.io", "yousef123", "Yousef Ahmed", "agent", 250000),
    ("viewer@nebrascrm.io", "viewer123", "Guest Viewer", "readonly", 0),
]
for e, p, n, r, t in USERS:
    con.execute("INSERT INTO users(email,password,name,role,active,target,created_at) VALUES(?,?,?,?,1,?,?)",
                (e, hash_pw(p), n, r, t, D.now()))
uids = [r["id"] for r in con.execute("SELECT id FROM users WHERE role!='readonly'")]

COMPANIES = ["Yemen Soft", "Al-Amal Bank", "Sabafon", "Hadhramout Trading", "Aden Logistics", "Tihama Industries",
 "Arabian Tech", "Gulf Medical", "Sanaa Constructions", "Red Sea Shipping", "Zain Telecom", "Mareb Energy",
 "Cedar Analytics", "NileWorks", "Levant Foods", "Falcon Motors", "Oryx Digital", "Nafis Retail"]
NAMES = ["Ahmed Saleh","Fatima Ali","Khalid Mansour","Noor Hassan","Ibrahim Qasim","Huda Saeed","Tariq Amin",
 "Rania Zaid","Mohammed Anwar","Salma Fares","Waleed Bakr","Amina Yahya","Nasser Jaber","Dina Rashid",
 "Faisal Omar","Maha Sultan","Bilal Nour","Lina Haddad","Ziad Mustafa","Hanan Adel","Samir Aziz","Rasha Nabil"]
INDUSTRIES = ["Technology","Banking","Telecom","Retail","Healthcare","Construction","Logistics","Energy","Education"]
CITIES = [("Sanaa","Yemen"),("Aden","Yemen"),("Dubai","UAE"),("Riyadh","Saudi Arabia"),("Cairo","Egypt"),("Amman","Jordan")]
SOURCES = ["Web","Referral","Cold Call","Campaign","Partner","Trade Show","Other"]

def d(days): return (datetime.date.today() + datetime.timedelta(days=days)).isoformat()
def ins(t, **kw):
    kw.update(created_at=D.now(), updated_at=D.now(), deleted=0)
    kw.setdefault("owner_id", random.choice(uids)); kw.setdefault("created_by", 1)
    k = list(kw)
    return con.execute(f'INSERT INTO "{t}" ({",".join(chr(34)+x+chr(34) for x in k)}) '
                       f'VALUES ({",".join("?"*len(k))})', [kw[x] for x in k]).lastrowid

# campaigns
camps = []
for i, (nm, ty) in enumerate([("Q1 Digital Push","Email"),("Ramadan Promo","Social"),("Enterprise Webinar","Webinar"),
                              ("Gitex Expo","Event"),("Outbound Blitz","Telemarketing")]):
    b = random.randint(5000, 60000)
    camps.append(ins("campaigns", name=nm, type=ty, status=random.choice(["Planning","Active","Completed"]),
        start_date=d(-random.randint(30,180)), end_date=d(random.randint(5,90)), budget=b,
        actual_cost=round(b*random.uniform(.4,1.1)), expected_revenue=b*random.randint(3,8),
        leads_generated=random.randint(20,300), description=f"{nm} marketing campaign."))

# accounts
accs = []
for c in COMPANIES:
    accs.append(ins("accounts", name=c, industry=random.choice(INDUSTRIES),
        type=random.choice(["Customer","Prospect","Partner","Reseller"]),
        phone=f"+967-1-{random.randint(200000,999999)}", website=f"www.{c.split()[0].lower()}.com",
        annual_revenue=random.randint(200,9000)*1000, employees=random.randint(10,3000),
        billing_address=f"{random.choice(CITIES)[0]}, HQ Tower"))

# contacts
cts = []
for n in NAMES:
    cts.append(ins("contacts", name=n, account_id=random.choice(accs),
        title=random.choice(["CEO","CTO","Procurement Manager","IT Director","Finance Head","Operations Lead"]),
        email=n.lower().replace(" ",".")+"@example.com", phone=f"+967-77-{random.randint(1000000,9999999)}",
        mobile=f"+967-73-{random.randint(1000000,9999999)}",
        department=random.choice(["IT","Finance","Sales","Operations","HR"])))

# leads
for i in range(45):
    n = random.choice(NAMES); city, country = random.choice(CITIES)
    ins("leads", name=n, company=random.choice(COMPANIES), email=f"lead{i}@example.com",
        phone=f"+967-71-{random.randint(1000000,9999999)}",
        status=random.choices(["New","Contacted","Qualified","Unqualified"], [4,3,2,1])[0],
        source=random.choice(SOURCES), rating=random.choice(["Hot","Warm","Cold"]),
        industry=random.choice(INDUSTRIES), annual_revenue=random.randint(50,2000)*1000,
        city=city, country=country, description="Inbound lead from marketing funnel.")

# deals
for i in range(60):
    st = random.choices(DEAL_STAGES, [3,3,3,2,4,2])[0]
    prob = {"Qualification":20,"Needs Analysis":40,"Proposal":60,"Negotiation":80,"Closed Won":100,"Closed Lost":0}[st]
    a = random.choice(accs)
    closed = st.startswith("Closed")
    ins("deals", name=f"{random.choice(COMPANIES)} — {random.choice(['License Renewal','Platform Rollout','Support Contract','Hardware Supply','Consulting Engagement'])}",
        account_id=a, contact_id=random.choice(cts), amount=random.randint(5,250)*1000,
        stage=st, probability=prob, closing_date=d(-random.randint(1,240) if closed else random.randint(3,120)),
        source=random.choice(SOURCES), campaign_id=random.choice(camps),
        next_step=random.choice(["Send proposal","Schedule demo","Await approval","Negotiate terms"]))

# activities
for i in range(50):
    ins("activities", subject=random.choice(["Follow-up call","Product demo","Contract review","Discovery meeting",
        "Send pricing","Quarterly check-in","Onboarding session"]),
        type=random.choice(["Task","Call","Meeting","Email"]),
        status=random.choices(["Not Started","In Progress","Completed","Deferred"],[4,3,4,1])[0],
        priority=random.choice(["Low","Medium","High","Urgent"]),
        due_date=d(random.randint(-20,40)), related_to=f"deals#{random.randint(1,60)}")

# tickets
for i in range(35):
    ins("tickets", subject=random.choice(["Login failure","Invoice discrepancy","API timeout","Feature request",
        "Data migration help","Performance degradation","Permission issue"]),
        account_id=random.choice(accs), contact_id=random.choice(cts),
        status=random.choices(["Open","In Progress","Waiting on Customer","Escalated","Closed"],[4,3,2,1,4])[0],
        priority=random.choice(["Low","Medium","High","Urgent"]),
        channel=random.choice(["Email","Phone","Web","Chat","Social"]),
        category=random.choice(["Technical","Billing","Account","Feature"]),
        due_date=d(random.randint(-10,20)), description="Customer reported an issue requiring investigation.")

# products
prods=[]
for nm, cat, pr in [("NebrasCRM Pro License","Software",1200),("NebrasCRM Enterprise","Software",4800),
    ("Implementation Services","Services",15000),("Premium Support (yr)","Services",6000),
    ("Data Migration Pack","Services",3500),("Server Appliance X1","Hardware",8900),
    ("Training Workshop","Services",2200),("API Gateway Add-on","Software",990)]:
    prods.append(ins("products", name=nm, code=f"P-{random.randint(1000,9999)}", category=cat,
        unit_price=pr, cost=round(pr*.55), qty_in_stock=random.randint(0,200),
        reorder_level=20, tax_rate=15, active="Yes"))

# quotes & invoices
for i in range(18):
    a = random.choice(accs); amt = random.randint(3,90)*1000
    ins("quotes", subject=f"Quote #Q-{2000+i}", account_id=a, deal_id=random.randint(1,60),
        status=random.choice(["Draft","Sent","Accepted","Rejected"]), valid_until=d(random.randint(5,60)),
        amount=amt, terms="Payment within 30 days. Prices exclude VAT.")
for i in range(22):
    amt = random.randint(3,90)*1000
    stt = random.choices(["Draft","Sent","Paid","Overdue"],[1,3,4,2])[0]
    ins("invoices", subject=f"Invoice #INV-{5000+i}", account_id=random.choice(accs), status=stt,
        invoice_date=d(-random.randint(1,120)), due_date=d(random.randint(-30,45)), amount=amt,
        paid_amount=amt if stt=="Paid" else 0)

for nm in ["Tech Distributors Ltd","Global Hardware Co","CloudHost MENA","Office Supplies Yemen"]:
    ins("vendors", name=nm, email=nm.split()[0].lower()+"@vendor.com",
        phone=f"+967-1-{random.randint(200000,999999)}", category=random.choice(["Hardware","Cloud","Office"]),
        website="www."+nm.split()[0].lower()+".com")

con.execute("""INSERT INTO workflows(name,module,trigger,field,operator,value,action,action_value,active,created_at)
    VALUES('Big Deal Alert','deals','save','amount','gt','100000','notify','A deal above 100K was saved',1,?)""",(D.now(),))
con.execute("""INSERT INTO workflows(name,module,trigger,field,operator,value,action,action_value,active,created_at)
    VALUES('Hot Lead Task','leads','save','rating','eq','Hot','create_task','Call hot lead within 24h',1,?)""",(D.now(),))
con.execute("""INSERT INTO workflows(name,module,trigger,field,operator,value,action,action_value,active,created_at)
    VALUES('Urgent Ticket Escalation','tickets','save','priority','eq','Urgent','notify','Urgent ticket requires attention',1,?)""",(D.now(),))
con.commit()
print("seeded ok")
