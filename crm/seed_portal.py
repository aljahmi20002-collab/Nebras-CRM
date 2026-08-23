import sys,os; sys.path.insert(0,os.path.dirname(os.path.abspath(__file__)))
import db as D, portal as P
con=D.connect(); P.con=con; P.init_tables(con)
n=0
for c in con.execute("SELECT id,name,email FROM contacts WHERE deleted=0 AND email IS NOT NULL LIMIT 6"):
    if con.execute("SELECT 1 FROM portal_users WHERE contact_id=? OR lower(email)=lower(?)",(c["id"],c["email"])).fetchone():
        continue
    con.execute("INSERT INTO portal_users(contact_id,email,password,active,created_at) VALUES(?,?,?,1,?)",
                (c["id"],c["email"],P.phash("portal123"),D.now())); n+=1
    print(" ",c["email"],"/ portal123")
con.commit(); print("portal users added:",n)
