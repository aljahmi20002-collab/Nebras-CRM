/* NebrasCRM Customer Portal — bilingual self-service area */
const P = {
  token: localStorage.getItem("ptok") || "", me: null,
  lang: localStorage.getItem("lang") || "ar",
  theme: localStorage.getItem("theme") || "dark",
  tab: "home",
};
const TT = {
  ar: {portal:"بوابة العملاء",welcome:"مرحباً",home:"الرئيسية",tickets:"تذاكر الدعم",invoices:"الفواتير",
    quotes:"عروض الأسعار",profile:"الحساب",login:"تسجيل الدخول",email:"البريد الإلكتروني",password:"كلمة المرور",
    logout:"خروج",openTickets:"تذاكر مفتوحة",totalTickets:"إجمالي التذاكر",outstanding:"مستحقات غير مدفوعة",
    paid:"مدفوع",openQuotes:"عروض قيد الانتظار",newTicket:"تذكرة جديدة",subject:"الموضوع",desc:"الوصف",
    priority:"الأولوية",category:"الفئة",submit:"إرسال",cancel:"إلغاء",status:"الحالة",created:"تاريخ الإنشاء",
    due:"الاستحقاق",amount:"المبلغ",remaining:"المتبقي",validUntil:"صالح حتى",accept:"قبول العرض",
    reject:"رفض العرض",noData:"لا توجد بيانات",reply:"اكتب ردك...",send:"إرسال",conversation:"المحادثة",
    you:"أنت",support:"فريق الدعم",back:"رجوع",account:"الشركة",name:"الاسم",phone:"الهاتف",title:"المسمى",
    changePw:"تغيير كلمة المرور",current:"كلمة المرور الحالية",newPw:"كلمة المرور الجديدة",save:"حفظ",
    saved:"تم الحفظ",sent:"تم الإرسال",decided:"تم تسجيل قرارك",item:"البند",qty:"الكمية",price:"السعر",
    total:"الإجمالي",staffLogin:"دخول الموظفين",demo:"حساب تجريبي (اضغط للتعبئة)",confirmQ:"هل أنت متأكد؟",
    ticketMsg:"سيتم إشعار فريق الدعم فوراً",payNow:"ادفع الآن",payments:"سجل المدفوعات",ref:"المرجع",method:"الطريقة",paidOn:"تاريخ الدفع",noBalance:"مدفوعة بالكامل",shop:"المنتجات",orders:"طلباتي",loyalty:"الولاء",statement:"كشف الحساب",documents:"المستندات",cart:"السلة",addCart:"أضف للسلة",yourPrice:"سعرك",listPrice:"السعر",placeOrder:"إرسال الطلب",qty:"الكمية",total:"الإجمالي",emptyCart:"السلة فارغة",orderSent:"تم إرسال طلبك",tier:"الفئة",points:"النقاط",available:"المتاح",breakdown:"تفصيل النقاط",nextTier:"الفئة التالية",perks:"المزايا",rule:"القاعدة",basis:"الأساس",discountL:"خصم فئتك",inStock:"متوفر",outStock:"غير متوفر",debit:"مدين",credit:"دائن",running:"الرصيد",balanceL:"الرصيد المستحق",docType:"النوع",view:"عرض",print:"طباعة",searchP:"ابحث عن منتج...",category:"الفئة",clearCart:"إفراغ",myDiscount:"خصمك"},
  en: {portal:"Customer Portal",welcome:"Welcome",home:"Home",tickets:"Support Tickets",invoices:"Invoices",
    quotes:"Quotes",profile:"Profile",login:"Sign in",email:"Email",password:"Password",
    logout:"Logout",openTickets:"Open Tickets",totalTickets:"Total Tickets",outstanding:"Outstanding Balance",
    paid:"Paid to Date",openQuotes:"Pending Quotes",newTicket:"New Ticket",subject:"Subject",desc:"Description",
    priority:"Priority",category:"Category",submit:"Submit",cancel:"Cancel",status:"Status",created:"Created",
    due:"Due",amount:"Amount",remaining:"Remaining",validUntil:"Valid until",accept:"Accept Quote",
    reject:"Reject Quote",noData:"Nothing here yet",reply:"Write a reply...",send:"Send",conversation:"Conversation",
    you:"You",support:"Support Team",back:"Back",account:"Account",name:"Name",phone:"Phone",title:"Job Title",
    changePw:"Change Password",current:"Current password",newPw:"New password",save:"Save",
    saved:"Saved",sent:"Sent",decided:"Your decision was recorded",item:"Item",qty:"Qty",price:"Price",
    total:"Total",staffLogin:"Staff login",demo:"Demo account (click to fill)",confirmQ:"Are you sure?",
    ticketMsg:"Our support team will be notified immediately",payNow:"Pay now",payments:"Payment history",ref:"Reference",method:"Method",paidOn:"Paid on",noBalance:"Fully paid",shop:"Products",orders:"My Orders",loyalty:"Loyalty",statement:"Statement",documents:"Documents",cart:"Cart",addCart:"Add to cart",yourPrice:"Your price",listPrice:"List",placeOrder:"Place order",qty:"Qty",total:"Total",emptyCart:"Cart is empty",orderSent:"Order submitted",tier:"Tier",points:"Points",available:"Available",breakdown:"Points breakdown",nextTier:"Next tier",perks:"Perks",rule:"Rule",basis:"Basis",discountL:"Your tier discount",inStock:"In stock",outStock:"Out of stock",debit:"Debit",credit:"Credit",running:"Balance",balanceL:"Outstanding",docType:"Type",view:"View",print:"Print",searchP:"Search products...",category:"Category",clearCart:"Clear",myDiscount:"Your discount"},
};
const x = k => TT[P.lang][k] || k;

/* Theme-aware colour: hex palettes coming from the API were chosen for the dark
   canvas. On the light canvas we darken anything too pale to keep text legible. */
function TC(c){
  if(!c||typeof c!=="string"||c[0]!=="#") return c;
  if((localStorage.getItem("theme")||"dark")!=="light") return c;
  let h=c.slice(1);
  if(h.length===3) h=h.split("").map(x=>x+x).join("");
  if(h.length<6) return c;
  let r=parseInt(h.slice(0,2),16),g=parseInt(h.slice(2,4),16),b=parseInt(h.slice(4,6),16);
  const lum=(0.2126*r+0.7152*g+0.0722*b)/255;
  if(lum<=0.42) return c;                       // already dark enough
  const k=Math.max(0.40,0.42/lum);              // scale down toward target luminance
  const f=v=>Math.round(Math.max(0,Math.min(255,v*k))).toString(16).padStart(2,"0");
  return "#"+f(r)+f(g)+f(b);
}
const es = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const money = v => (v == null || v === "") ? "—" : new Intl.NumberFormat(P.lang==="ar"?"ar-EG":"en-US",
  {style:"currency",currency:"USD",maximumFractionDigits:0}).format(v);
const CLR = {"Open":"var(--info)","In Progress":"var(--warn)","Waiting on Customer":"var(--purple)",
  "Escalated":"var(--danger)","Closed":"var(--mut)","Paid":"var(--ok)","Overdue":"var(--danger)",
  "Draft":"var(--mut)","Sent":"var(--info)","Accepted":"var(--ok)","Rejected":"var(--danger)",
  "Cancelled":"var(--mut)","Expired":"var(--mut)","Urgent":"var(--danger)","High":"var(--warn)",
  "Medium":"var(--info)","Low":"var(--mut)"};
const bg = v => v==null||v===""?"—":`<span class="badge" style="color:${CLR[v]||"var(--mut)"};background:${CLR[v]||"var(--mut)"}22;border-color:${CLR[v]||"var(--mut)"}55">${es(v)}</span>`;

async function pa(path, opts = {}) {
  const r = await fetch("/portal/api" + path, {...opts, headers:{"Content-Type":"application/json",
    ...(P.token?{Authorization:"Bearer "+P.token}:{}), ...(opts.headers||{})}});
  if (r.status === 401) { plogout(); throw new Error("auth"); }
  if (!r.ok) { const e = await r.json().catch(()=>({detail:"Error"})); tst(e.detail||"Error"); throw new Error(e.detail); }
  return r.json();
}
function tst(m){const d=document.createElement("div");d.className="toast";d.textContent=m;document.body.append(d);setTimeout(()=>d.remove(),2600);}
function plogout(){localStorage.removeItem("ptok");P.token="";P.me=null;draw();}

async function pboot(){
  if (P.token && !P.me) { try { P.me = await pa("/me"); } catch { return draw(); } }
  draw();
}
function applyShell(){
  const rtl = P.lang==="ar";
  document.documentElement.lang = P.lang;
  document.documentElement.dir = rtl?"rtl":"ltr";
  document.body.dir = rtl?"rtl":"ltr";
  document.body.classList.toggle("light", P.theme==="light");
  const mt=document.querySelector('meta[name="theme-color"]');
  if(mt) mt.setAttribute("content", P.theme==="light"?"#EEF2F8":"#2B4ACB");
}
function draw(){
  applyShell();
  P.me ? shell() : plogin();
}

function plogin(){
  const ar=P.lang==="ar";
  const T=ar?{h:"بوابة العملاء",h2:"خدمة ذاتية على مدار الساعة",
    p:"تابع فواتيرك وطلباتك وتذاكر الدعم، واطلب منتجاتك بأسعارك الخاصة، وتابع نقاط ولائك — في أي وقت.",
    f:[["كتالوج بأسعارك الخاصة","خصم تلقائي حسب فئة ولائك"],
       ["فواتير ودفع إلكتروني","36 قناة دفع تشمل محافظ الجوال"],
       ["تذاكر دعم بمحادثة مباشرة","تواصل فوري مع فريق الدعم"],
       ["كشف حساب ومستندات","فواتيرك وعروض أسعارك قابلة للطباعة"]],
    welcome:"أهلاً بك 👋",sub:"سجّل الدخول لبوابة العملاء",
    demo:"حسابات تجريبية — اضغط للدخول",signing:"جارٍ الدخول...",
    staff:"دخول الموظفين",part:"بوابة الشركاء",home:"الرئيسية"}
  :{h:"Customer Portal",h2:"self-service, around the clock",
    p:"Track invoices, orders and support tickets, order at your own pricing, and follow your loyalty points — anytime.",
    f:[["Catalogue at your pricing","Automatic discount from your loyalty tier"],
       ["Invoices and online payment","36 channels including mobile wallets"],
       ["Support tickets with live chat","Talk to the support team directly"],
       ["Statement and documents","Printable invoices and quotes"]],
    welcome:"Welcome 👋",sub:"Sign in to the customer portal",
    demo:"Demo accounts — click to sign in",signing:"Signing in...",
    staff:"Staff login",part:"Partner portal",home:"Home"};
  const DEMO=[["ahmed.saleh@example.com",ar?"عميل":"Customer"],
              ["fatima.ali@example.com",ar?"عميل":"Customer"],
              ["noor.hassan@example.com",ar?"عميل":"Customer"],
              ["huda.saeed@example.com",ar?"عميل":"Customer"]];
  document.body.innerHTML=`
    <div class="auth-bg"><i style="background:#22c55e"></i><i></i><i style="background:#06b6d4"></i></div>
    <div class="auth-grid"></div>
    <div class="auth">
      <div class="auth-art">
        <a href="/" class="logo" style="font-size:21px"><span class="mark"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</a>
        <div><h2>${T.h}<br><span class="gr">${T.h2}</span></h2>
          <p style="margin-top:14px">${T.p}</p></div>
        <div class="auth-feats">${T.f.map(([a,b])=>`<div><span class="tick">✓</span>
          <span><b>${es(a)}</b><br>${es(b)}</span></div>`).join("")}</div>
      </div>
      <div class="auth-side"><form class="auth-card" id="pf">
        <div class="logo"><span class="mark"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</div>
        <div class="auth-sub">🛍️ ${T.h}</div>
        <div style="font-size:19px;font-weight:800">${T.welcome}</div>
        <div class="auth-sub" style="margin:5px 0 20px">${T.sub}</div>
        <div id="perr"></div>
        <div class="ifield"><span class="ico">✉️</span>
          <input id="pe" type="email" placeholder="${x("email")}" value="ahmed.saleh@example.com" required></div>
        <div class="ifield"><span class="ico">🔒</span>
          <input id="pp" type="password" placeholder="${x("password")}" value="portal123" required>
          <button type="button" class="eye" id="pey">👁️</button></div>
        <button class="btn-auth" id="psb">${x("login")} →</button>
        <div class="divider">${T.demo}</div>
        <div class="demo-grid">${DEMO.map(([e,r])=>`<button type="button" data-e="${e}">
          <b>${es(r)}</b><small>${e}</small></button>`).join("")}</div>
        <div class="auth-links">
          <a href="/">${T.home}</a><a href="/app">${T.staff}</a><a href="/agent">${T.part}</a>
          <a id="pl">${ar?"English":"العربية"}</a>
          <a id="pth">${P.theme==="dark"?"☀️":"🌙"}</a></div>
      </form></div>
    </div>`;
  pey.onclick=()=>{pp.type=pp.type==="password"?"text":"password";pey.textContent=pp.type==="password"?"👁️":"🙈";};
  pl.onclick=()=>{P.lang=P.lang==="ar"?"en":"ar";localStorage.setItem("lang",P.lang);draw();};
  pth.onclick=()=>{P.theme=P.theme==="dark"?"light":"dark";localStorage.setItem("theme",P.theme);draw();};
  document.querySelectorAll(".demo-grid button").forEach(b=>b.onclick=()=>{
    pe.value=b.dataset.e;pp.value="portal123";pf.requestSubmit();});
  pf.onsubmit=async e=>{e.preventDefault();
    const btn=document.getElementById("psb");btn.disabled=true;btn.textContent=T.signing;perr.innerHTML="";
    try{const r=await fetch("/portal/api/login",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email:pe.value,password:pp.value})});
      const j=await r.json(); if(!r.ok) throw new Error(j.detail||"Error");
      P.token=j.token;localStorage.setItem("ptok",j.token);P.me=await pa("/me");P.tab="home";draw();
    }catch(err){perr.innerHTML=`<div class="auth-err">⚠ ${es(err.message)}</div>`;
      btn.disabled=false;btn.textContent=x("login")+" →";}};
}

function shell(){
  applyShell();
  const tabs=[["home","🏠 "+x("home")],["shop","🛍️ "+x("shop")],["orders","🛒 "+x("orders")],
              ["tickets","🎫 "+x("tickets")],["invoices","🧾 "+x("invoices")],["quotes","📄 "+x("quotes")],
              ["statement","📒 "+x("statement")],["documents","📁 "+x("documents")],
              ["loyalty","🏆 "+x("loyalty")],["profile","👤 "+x("profile")]];
  document.body.innerHTML=`<div class="ptop"><div class="in">
      <div class="logo" style="font-size:18px"><span class="mark" style="width:28px;height:28px"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</div>
      <span class="mut" style="font-size:12px">${x("portal")}</span>
      <div class="spacer" style="flex:1"></div>
      <div style="text-align:end;line-height:1.3"><div style="font-weight:700;font-size:13px">${es(P.me.name)}</div>
        <div class="mut" style="font-size:11px">${es(P.me.account||"")}</div></div>
      <button class="icbtn" id="th">${P.theme==="dark"?"☀️":"🌙"}</button>
      <button class="btn sm" id="lg">${P.lang==="ar"?"EN":"ع"}</button>
      <button class="btn sm" id="lo">${x("logout")}</button></div></div>
    <div class="pshell"><div class="ptabs">${tabs.map(([k,l])=>`<button data-t="${k}" class="${P.tab===k?"on":""}">${l}</button>`).join("")}</div>
    <div id="pc"><div class="empty">…</div></div></div>`;
  th.onclick=()=>{P.theme=P.theme==="dark"?"light":"dark";localStorage.setItem("theme",P.theme);draw();};
  lg.onclick=()=>{P.lang=P.lang==="ar"?"en":"ar";localStorage.setItem("lang",P.lang);draw();};
  lo.onclick=plogout;
  document.querySelectorAll(".ptabs button").forEach(b=>b.onclick=()=>{P.tab=b.dataset.t;shell();});
  ({home:tHome,shop:tShop,orders:tOrders,tickets:tTickets,invoices:tInvoices,quotes:tQuotes,
    statement:tStatement,documents:tDocuments,loyalty:tLoyalty,profile:tProfile}[P.tab])();
}

async function tHome(){
  const s=await pa("/summary");
  const ts=await pa("/tickets");
  const iv=await pa("/invoices");
  const k=(l,v,c)=>`<div class="kpi" style="--pri:${c}"><div class="l">${l}</div><div class="v">${v}</div></div>`;
  pc.innerHTML=`<div class="card" style="margin-bottom:14px;background:linear-gradient(135deg,var(--pri)22,transparent)">
      <div style="font-size:19px;font-weight:800">${x("welcome")}، ${es(P.me.name)} 👋</div>
      <div class="mut">${es(P.me.account||"")}</div></div>
    <div class="kpis" style="margin-bottom:16px">
      ${k(x("openTickets"),s.open_tickets,"var(--info)")}
      ${k(x("outstanding"),money(s.outstanding),"var(--danger)")}
      ${k(x("paid"),money(s.paid),"var(--ok)")}
      ${k(x("openQuotes"),s.open_quotes,"var(--warn)")}
      ${k(x("totalTickets"),s.total_tickets,"var(--purple)")}</div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(320px,1fr))">
      <div class="card"><b>🎫 ${x("tickets")}</b><div style="height:8px"></div>
        ${ts.slice(0,5).map(t=>`<div class="row" style="padding:8px 0;border-bottom:1px solid var(--line);cursor:pointer" data-t="${t.id}">
          <span style="flex:1">${es(t.subject)}</span>${bg(t.status)}</div>`).join("")||`<div class="empty">${x("noData")}</div>`}</div>
      <div class="card"><b>🧾 ${x("invoices")}</b><div style="height:8px"></div>
        ${iv.slice(0,5).map(i=>`<div class="row" style="padding:8px 0;border-bottom:1px solid var(--line)">
          <span style="flex:1">${es(i.subject)}</span><b>${money(i.amount)}</b>${bg(i.status)}</div>`).join("")||`<div class="empty">${x("noData")}</div>`}</div>
    </div>`;
  pc.querySelectorAll("[data-t]").forEach(d=>d.onclick=()=>{P.tab="tickets";shell();setTimeout(()=>openTicket(+d.dataset.t),80);});
}

async function tTickets(){
  const ts=await pa("/tickets");
  pc.innerHTML=`<div class="row" style="margin-bottom:12px"><div class="h1" style="font-size:19px">🎫 ${x("tickets")}</div>
      <div class="spacer" style="flex:1"></div><button class="btn pri sm" id="nt">+ ${x("newTicket")}</button></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>#</th><th>${x("subject")}</th><th>${x("status")}</th><th>${x("priority")}</th><th>${x("created")}</th></tr></thead><tbody>
      ${ts.map(t=>`<tr data-i="${t.id}"><td class="mut">#${t.id}</td><td><b>${es(t.subject)}</b>
        <div class="mut" style="font-size:11.5px">${es((t.description||"").slice(0,70))}</div></td>
        <td>${bg(t.status)}</td><td>${bg(t.priority)}</td><td class="mut">${(t.created_at||"").slice(0,10)}</td></tr>`).join("")
        ||`<tr><td colspan="5"><div class="empty">${x("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  nt.onclick=newTicket;
  pc.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=()=>openTicket(+tr.dataset.i));
}
function newTicket(){
  const el=md(x("newTicket"),`<form id="ntf">
    <div class="fld"><label>${x("subject")} *</label><input name="subject" required></div>
    <div class="fld"><label>${x("desc")}</label><textarea name="description"></textarea></div>
    <div class="f2"><div class="fld"><label>${x("priority")}</label><select name="priority">
      <option>Low</option><option selected>Medium</option><option>High</option><option>Urgent</option></select></div>
      <div class="fld"><label>${x("category")}</label><select name="category">
      <option>Technical</option><option>Billing</option><option>Account</option><option>Feature</option></select></div></div>
    <div class="mut" style="font-size:12px">💡 ${x("ticketMsg")}</div></form>`,
    [[x("cancel"),cl,""],[x("submit"),async()=>{
      const fd=new FormData(el.querySelector("#ntf"));const b={};fd.forEach((v,k)=>b[k]=v);
      if(!b.subject.trim())return;
      await pa("/tickets",{method:"POST",body:JSON.stringify(b)});tst(x("sent"));cl();tTickets();},"pri"]]);
}
async function openTicket(id){
  const t=await pa("/tickets/"+id);
  const el=md(`#${id} · ${es(t.subject)}`,
    `<div class="row" style="gap:8px;margin-bottom:12px;flex-wrap:wrap">${bg(t.status)}${bg(t.priority)}
      <span class="mut">${es(t.category||"")}</span><div class="spacer" style="flex:1"></div>
      <span class="mut" style="font-size:12px">${(t.created_at||"").slice(0,10)}</span></div>
     <b style="font-size:13px">${x("conversation")}</b><div style="height:10px"></div>
     <div id="thr" style="max-height:320px;overflow:auto;margin-bottom:12px">
      ${(t.messages||[]).map(m=>`<div class="msg ${m.author}">
        <div class="row" style="gap:6px;margin-bottom:3px"><b style="font-size:11.5px">${m.author==="customer"?x("you"):x("support")}</b>
        <span class="mut" style="font-size:10.5px">${(m.created_at||"").replace("T"," ")}</span></div>
        <div style="font-size:13px;white-space:pre-wrap">${es(m.body)}</div></div>`).join("")
        ||`<div class="mut" style="font-size:13px">${es(t.description||"")}</div>`}</div>
     ${t.status!=="Closed"?`<div class="fld"><textarea id="rp" placeholder="${x("reply")}"></textarea></div>
       <button class="btn pri sm" id="sr">${x("send")}</button>`:""}`, []);
  const thr=el.querySelector("#thr"); if(thr) thr.scrollTop=thr.scrollHeight;
  const sr=el.querySelector("#sr");
  if(sr)sr.onclick=async()=>{const b=el.querySelector("#rp").value.trim();if(!b)return;
    await pa(`/tickets/${id}/reply`,{method:"POST",body:JSON.stringify({body:b})});
    tst(x("sent"));cl();openTicket(id);};
}

async function tInvoices(){
  const iv=await pa("/invoices");
  pc.innerHTML=`<div class="h1" style="font-size:19px;margin-bottom:12px">🧾 ${x("invoices")}</div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${x("subject")}</th><th>${x("status")}</th><th>${x("created")}</th><th>${x("due")}</th>
      <th>${x("amount")}</th><th>${x("remaining")}</th><th></th></tr></thead><tbody>
      ${iv.map(i=>{const rem=(i.amount||0)-(i.paid_amount||0);
        return `<tr><td><b>${es(i.subject)}</b></td><td>${bg(i.status)}</td>
        <td class="mut">${i.invoice_date||"—"}</td><td class="mut">${i.due_date||"—"}</td>
        <td><b>${money(i.amount)}</b></td><td style="color:${rem>0?"var(--danger)":"var(--ok)"};font-weight:700">${money(rem)}</td>
        <td>${rem>0.01&&i.status!=="Cancelled"?`<button class="btn pri sm" data-p="${i.id}">💳 ${x("payNow")}</button>`
          :`<span class="mut" style="font-size:11.5px">✓ ${x("noBalance")}</span>`}</td></tr>`;}).join("")
        ||`<tr><td colspan="7"><div class="empty">${x("noData")}</div></td></tr>`}
      </tbody></table></div></div>
      <div class="card" style="margin-top:12px" class="row"><div class="row"><b>${x("outstanding")}</b>
      <div class="spacer" style="flex:1"></div><b style="font-size:17px;color:var(--danger)">
      ${money(iv.reduce((a,i)=>a+((i.amount||0)-(i.paid_amount||0)),0))}</b></div></div>
      <div id="ph" style="margin-top:16px"></div>`;
  pc.querySelectorAll("[data-p]").forEach(b=>b.onclick=async()=>{
    b.disabled=true;
    const r=await pa(`/invoices/${b.dataset.p}/pay`,{method:"POST"});
    location.href=r.url;});
  const ps=await pa("/payments");
  if(ps.length){const pcl=v=>({paid:"var(--ok)",pending:"var(--warn)",failed:"var(--danger)",refunded:"var(--purple)"}[v]||"var(--mut)");
    document.getElementById("ph").innerHTML=`<div class="card" style="padding:0">
      <div style="padding:12px 14px;border-bottom:1px solid var(--line)"><b>${x("payments")}</b></div>
      <div class="wrap-scroll"><table class="tbl"><thead><tr><th>${x("subject")}</th><th>${x("amount")}</th>
      <th>${x("method")}</th><th>${x("status")}</th><th>${x("ref")}</th><th>${x("paidOn")}</th></tr></thead><tbody>
      ${ps.map(p=>`<tr><td>${es(p.invoice_subject)}</td><td><b>${money(p.amount)}</b></td><td>${es(p.method||"—")}</td>
        <td><span class="badge" style="color:${pcl(p.status)};background:${pcl(p.status)}22">${p.status}</span></td>
        <td class="mut" style="font-size:11.5px">${es(p.provider_ref||"—")}</td>
        <td class="mut">${(p.paid_at||"—").replace("T"," ")}</td></tr>`).join("")}
      </tbody></table></div></div>`;}
}

async function tQuotes(){
  const qs=await pa("/quotes");
  pc.innerHTML=`<div class="h1" style="font-size:19px;margin-bottom:12px">📄 ${x("quotes")}</div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(330px,1fr))">
    ${qs.map(q=>`<div class="card"><div class="row"><b style="flex:1">${es(q.subject)}</b>${bg(q.status)}</div>
      <div class="mut" style="font-size:12px;margin:4px 0 10px">${x("validUntil")}: ${q.valid_until||"—"}</div>
      ${q.items.length?`<table class="tbl" style="font-size:12.5px"><thead><tr><th>${x("item")}</th><th>${x("qty")}</th><th>${x("price")}</th></tr></thead>
        <tbody>${q.items.map(i=>`<tr><td>${es(i.name)}</td><td>${i.qty}</td><td>${money(i.price)}</td></tr>`).join("")}</tbody></table>`:""}
      <div class="row" style="margin-top:10px;padding-top:10px;border-top:1px solid var(--line)">
        <b>${x("total")}</b><div class="spacer" style="flex:1"></div><b style="font-size:17px">${money(q.amount)}</b></div>
      ${["Draft","Sent"].includes(q.status)?`<div class="row" style="margin-top:10px">
        <button class="btn sm" style="flex:1;color:var(--ok);border-color:var(--ok)55" data-a="${q.id}">✓ ${x("accept")}</button>
        <button class="btn sm dgr" style="flex:1" data-r="${q.id}">✕ ${x("reject")}</button></div>`:""}
      ${q.terms?`<div class="mut" style="font-size:11.5px;margin-top:8px">${es(q.terms)}</div>`:""}</div>`).join("")
      ||`<div class="empty">${x("noData")}</div>`}</div>`;
  const decide=async(id,d)=>{if(!confirm(x("confirmQ")))return;
    await pa(`/quotes/${id}/decision`,{method:"POST",body:JSON.stringify({decision:d})});tst(x("decided"));tQuotes();};
  pc.querySelectorAll("[data-a]").forEach(b=>b.onclick=()=>decide(b.dataset.a,"Accepted"));
  pc.querySelectorAll("[data-r]").forEach(b=>b.onclick=()=>decide(b.dataset.r,"Rejected"));
}

function tProfile(){
  pc.innerHTML=`<div class="h1" style="font-size:19px;margin-bottom:12px">👤 ${x("profile")}</div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
    <div class="card">${[[x("name"),P.me.name],[x("email"),P.me.email],[x("account"),P.me.account],
      [x("title"),P.me.title],[x("phone"),P.me.phone]].map(([l,v])=>
      `<div style="padding:9px 0;border-bottom:1px solid var(--line)"><div class="mut" style="font-size:11.5px">${l}</div>
       <div>${es(v||"—")}</div></div>`).join("")}</div>
    <div class="card"><b>🔒 ${x("changePw")}</b><div style="height:10px"></div>
      <div class="fld"><label>${x("current")}</label><input type="password" id="cp"></div>
      <div class="fld"><label>${x("newPw")}</label><input type="password" id="np"></div>
      <button class="btn pri sm" id="sp">${x("save")}</button></div></div>`;
  sp.onclick=async()=>{try{await pa("/password",{method:"POST",body:JSON.stringify({current:cp.value,new:np.value})});
    tst(x("saved"));cp.value=np.value="";}catch{}};
}

let stack=[];
function md(title,html,buttons=[]){
  const ov=document.createElement("div");ov.className="ov";
  ov.innerHTML=`<div class="modal"><header><b style="flex:1">${title}</b><button class="icbtn" data-x>✕</button></header>
    <div class="body">${html}</div>${buttons.length?`<footer>${buttons.map((b,i)=>`<button class="btn ${b[2]||""}" data-b="${i}">${b[0]}</button>`).join("")}</footer>`:""}</div>`;
  document.body.append(ov);
  ov.querySelector("[data-x]").onclick=cl;
  ov.onclick=e=>{if(e.target===ov)cl();};
  ov.querySelectorAll("[data-b]").forEach(b=>b.onclick=()=>buttons[+b.dataset.b][1]());
  stack.push(ov);return ov;
}
function cl(){const o=stack.pop();if(o)o.remove();}

/* ---------- catalogue & cart ---------- */
let CART=JSON.parse(localStorage.getItem("cart")||"[]");
const saveCart=()=>localStorage.setItem("cart",JSON.stringify(CART));
async function tShop(){
  const d=await pa("/products");
  const cats={};
  d.products.forEach(p=>{(cats[p.category||"—"]=cats[p.category||"—"]||[]).push(p);});
  pc.innerHTML=`<div class="row" style="margin-bottom:12px;flex-wrap:wrap;gap:8px">
      <b style="font-size:17px">🛍️ ${x("shop")}</b>
      ${d.discount?`<span class="badge" style="color:${TC(d.tier.color)};background:${TC(d.tier.color)}22">
        ${P.lang==="ar"?d.tier.ar:d.tier.en} · ${x("myDiscount")} ${d.discount}%</span>`:""}
      <div class="spacer" style="flex:1"></div>
      <input id="pq" placeholder="${x("searchP")}" style="background:var(--bg2);border:1px solid var(--line);
        border-radius:9px;padding:7px 11px;min-width:180px">
      <button class="btn pri sm" id="ct">🛒 ${x("cart")} <b id="cn">${CART.length}</b></button></div>
    <div id="plist">${Object.entries(cats).map(([c,items])=>`
      <div class="mut" style="font-weight:700;font-size:11.5px;margin:12px 0 6px">${es(c)}</div>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(250px,1fr))">
      ${items.map(p=>`<div class="card pcard" data-n="${es((p.name||"").toLowerCase())}">
        <div class="row"><b style="flex:1;font-size:14px">${es(p.name)}</b>
          ${p.in_stock?`<span class="badge" style="color:var(--ok);background:var(--ok)22">${x("inStock")}</span>`
            :`<span class="badge" style="color:var(--mut);background:var(--mut)22">${x("outStock")}</span>`}</div>
        <div class="mut" style="font-size:11.5px;margin:4px 0">${es(p.code||"")}</div>
        <div class="row" style="margin:8px 0">
          <div><div class="mut" style="font-size:11px">${x("yourPrice")}</div>
            <b style="font-size:17px;color:var(--ok)">${money(p.your_price)}</b></div>
          ${p.discount?`<div style="margin-inline-start:10px"><div class="mut" style="font-size:11px">${x("listPrice")}</div>
            <span class="mut" style="text-decoration:line-through">${money(p.unit_price)}</span></div>`:""}</div>
        <button class="btn sm" style="width:100%" data-add="${p.id}" data-nm="${es(p.name)}"
          data-pr="${p.your_price}">+ ${x("addCart")}</button></div>`).join("")}</div>`).join("")}</div>`;
  pq.oninput=()=>{const q=pq.value.toLowerCase();
    pc.querySelectorAll(".pcard").forEach(c=>c.style.display=(!q||c.dataset.n.includes(q))?"":"none");};
  ct.onclick=showCart;
  pc.querySelectorAll("[data-add]").forEach(b=>b.onclick=()=>{
    const id=+b.dataset.add;const ex=CART.find(i=>i.product_id===id);
    if(ex)ex.qty++;else CART.push({product_id:id,name:b.dataset.nm,price:+b.dataset.pr,qty:1});
    saveCart();document.getElementById("cn").textContent=CART.length;tst("✓ "+b.dataset.nm);});
}
function showCart(){
  const draw=()=>{
    const tot=CART.reduce((a,i)=>a+i.price*i.qty,0);
    return CART.length?`<table class="tbl"><thead><tr><th>${x("subject")}</th><th>${x("qty")}</th>
      <th>${x("amount")}</th><th></th></tr></thead><tbody>
      ${CART.map((i,ix)=>`<tr><td>${es(i.name)}</td>
        <td><input type="number" min="1" value="${i.qty}" data-q="${ix}" style="width:64px;background:var(--bg2);
          border:1px solid var(--line);border-radius:7px;padding:4px"></td>
        <td><b>${money(i.price*i.qty)}</b></td>
        <td><button class="btn sm dgr" data-rm="${ix}">✕</button></td></tr>`).join("")}
      </tbody></table>
      <div class="row" style="margin-top:12px"><b style="font-size:17px">${x("total")}: ${money(tot)}</b></div>
      <div class="fld" style="margin-top:10px"><label>${x("notes")||"Note"}</label><textarea id="onote"></textarea></div>`
      :`<div class="empty">${x("emptyCart")}</div>`;};
  const el=md("🛒 "+x("cart"),draw(),
    [[x("clearCart"),()=>{CART=[];saveCart();cl();},""],
     [x("placeOrder"),async()=>{
       if(!CART.length)return;
       const note=(el.querySelector("#onote")||{}).value||"";
       try{const r=await pa("/orders",{method:"POST",body:JSON.stringify({items:CART,note})});
         CART=[];saveCart();cl();tst(x("orderSent")+" · "+money(r.total));P.tab="orders";shell();}catch{}},"pri"]]);
  const wire=()=>{
    el.querySelectorAll("[data-q]").forEach(i=>i.onchange=()=>{
      CART[+i.dataset.q].qty=Math.max(1,+i.value);saveCart();
      el.querySelector(".body").innerHTML=draw();wire();});
    el.querySelectorAll("[data-rm]").forEach(b=>b.onclick=()=>{
      CART.splice(+b.dataset.rm,1);saveCart();el.querySelector(".body").innerHTML=draw();wire();});};
  wire();
}
async function tOrders(){
  const os=await pa("/orders");
  pc.innerHTML=`<div class="h1" style="font-size:19px;margin-bottom:12px">🛒 ${x("orders")}</div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(320px,1fr))">
    ${os.map(o=>`<div class="card"><div class="row"><b style="flex:1">${es(o.subject)}</b>${bg(o.status)}</div>
      <div class="mut" style="font-size:12px;margin:4px 0 8px">${(o.created_at||"").slice(0,10)}</div>
      ${o.items.length?`<table class="tbl" style="font-size:12.5px"><tbody>
        ${o.items.map(i=>`<tr><td>${es(i.name)}</td><td>×${i.qty}</td><td>${money(i.price)}</td></tr>`).join("")}
        </tbody></table>`:""}
      <div class="row" style="margin-top:8px;padding-top:8px;border-top:1px solid var(--line)">
        <b>${x("total")}</b><div class="spacer" style="flex:1"></div><b>${money(o.amount)}</b></div></div>`).join("")
      ||`<div class="empty">${x("noData")}</div>`}</div>`;
}
async function tStatement(){
  const s=await pa("/statement");
  pc.innerHTML=`<div class="row" style="margin-bottom:12px"><div class="h1" style="font-size:19px">📒 ${x("statement")}</div>
      <div class="spacer" style="flex:1"></div>
      <b style="font-size:18px;color:${s.balance>0?"var(--danger)":"var(--ok)"}">${x("balanceL")}: ${money(s.balance)}</b></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${x("created")}</th><th>${x("subject")}</th><th>${x("debit")}</th><th>${x("credit")}</th>
      <th>${x("running")}</th></tr></thead><tbody>
      ${s.rows.map(r=>`<tr><td class="mut">${r.date||"—"}</td><td>${es(r.ref)}
        ${r.kind==="payment"?'<span class="badge" style="color:var(--ok);background:var(--ok)22">✓</span>':""}</td>
        <td>${r.debit?money(r.debit):"—"}</td>
        <td style="color:var(--ok)">${r.credit?money(r.credit):"—"}</td>
        <td><b>${money(r.running)}</b></td></tr>`).join("")
        ||`<tr><td colspan="5"><div class="empty">${x("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
}
async function tDocuments(){
  const ds=await pa("/documents");
  pc.innerHTML=`<div class="h1" style="font-size:19px;margin-bottom:12px">📁 ${x("documents")}</div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${x("docType")}</th><th>${x("subject")}</th><th>${x("created")}</th><th>${x("amount")}</th>
      <th>${x("status")}</th><th></th></tr></thead><tbody>
      ${ds.map(d=>`<tr><td><span class="badge" style="color:${d.type==="invoice"?"var(--info)":"var(--purple)"};
        background:${d.type==="invoice"?"var(--info)":"var(--purple)"}22">${es(d.type_ar)}</span></td>
        <td><b>${es(d.title)}</b></td><td class="mut">${d.date||"—"}</td>
        <td>${money(d.amount)}</td><td>${bg(d.status)}</td>
        <td><button class="btn sm" data-d="${d.type}:${d.id}">${x("view")}</button></td></tr>`).join("")
        ||`<tr><td colspan="6"><div class="empty">${x("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  pc.querySelectorAll("[data-d]").forEach(b=>b.onclick=async()=>{
    const [k,i]=b.dataset.d.split(":");
    const d=await pa(`/document/${k}/${i}`);
    const tot=d.items.reduce((a,it)=>a+it.qty*it.price*(1-(it.discount||0)/100)*(1+(it.tax||0)/100),0);
    md(es(d.subject),`<div style="background:#fff;color:#111;padding:22px;border-radius:10px" id="doc">
      <div style="display:flex;justify-content:space-between;border-bottom:2px solid #111;padding-bottom:10px">
        <div><b style="font-size:18px">${es(d.company)}</b><div style="font-size:12px">${es(d.type_ar||k)}</div></div>
        <div style="text-align:end;font-size:12px"><div><b>${es(d.subject)}</b></div>
          <div>${es(d.invoice_date||d.valid_until||"")}</div></div></div>
      <div style="margin:12px 0;font-size:12.5px"><b>${es(d.account_name||"")}</b><br>${es(d.contact_name||"")}</div>
      <table style="width:100%;border-collapse:collapse;font-size:12.5px">
        <thead><tr style="background:#f1f5f9"><th style="text-align:start;padding:7px">${x("subject")}</th>
        <th style="padding:7px">${x("qty")}</th><th style="padding:7px">${x("price")||"Price"}</th>
        <th style="padding:7px">${x("total")}</th></tr></thead><tbody>
        ${d.items.map(it=>`<tr><td style="padding:7px;border-bottom:1px solid #e2e8f0">${es(it.name)}</td>
          <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center">${it.qty}</td>
          <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center">${money(it.price)}</td>
          <td style="padding:7px;border-bottom:1px solid #e2e8f0;text-align:center">
            ${money(it.qty*it.price*(1-(it.discount||0)/100)*(1+(it.tax||0)/100))}</td></tr>`).join("")
          ||`<tr><td colspan="4" style="padding:14px;text-align:center;color:#64748b">—</td></tr>`}
        </tbody></table>
      <div style="text-align:end;margin-top:12px;font-size:16px"><b>${x("total")}: ${money(d.amount||tot)}</b></div>
      ${d.terms?`<div style="margin-top:12px;font-size:11.5px;color:#475569">${es(d.terms)}</div>`:""}
      </div>`,[[x("print"),()=>{const w=window.open("","_blank");
        w.document.write(`<html dir="${P.lang==="ar"?"rtl":"ltr"}"><body>${document.getElementById("doc").outerHTML}</body></html>`);
        w.document.close();w.print();},"pri"]]);});
}
async function tLoyalty(){
  const l=await pa("/loyalty");
  pc.innerHTML=`<div class="row" style="gap:12px;flex-wrap:wrap;margin-bottom:14px">
      <div class="kpi" style="--pri:${TC(l.tier.color)};flex:1"><div class="l">${x("tier")}</div>
        <div class="v" style="font-size:19px">${P.lang==="ar"?l.tier.ar:l.tier.en}</div></div>
      <div class="kpi" style="--pri:var(--pri);flex:1"><div class="l">${x("points")}</div>
        <div class="v">${new Intl.NumberFormat().format(Math.round(l.points))}</div></div>
      <div class="kpi" style="--pri:var(--ok);flex:1"><div class="l">${x("available")}</div>
        <div class="v">${new Intl.NumberFormat().format(Math.round(l.available))}</div></div>
      <div class="kpi" style="--pri:var(--warn);flex:1"><div class="l">${x("discountL")}</div>
        <div class="v">${l.tier.discount}%</div></div></div>
    <div class="card" style="margin-bottom:12px;font-size:12.5px">🎁 ${es(l.tier.perks_ar)}</div>
    ${l.next?`<div class="card" style="margin-bottom:12px">
      <div class="row"><span style="font-size:12.5px">${x("nextTier")}:
        <b style="color:${TC(l.next.tier.color)}">${P.lang==="ar"?l.next.tier.ar:l.next.tier.en}</b></span>
        <div class="spacer" style="flex:1"></div>
        <span class="mut" style="font-size:12px">${Math.round(l.next.gap)} ${x("points")}</span></div>
      <div class="barbg" style="margin-top:8px"><div class="barfill" style="width:${l.points/l.next.tier.min*100}%"></div></div></div>`:""}
    <div class="card"><b>${x("breakdown")}</b>
      <div class="wrap-scroll" style="margin-top:8px"><table class="tbl"><thead><tr>
        <th>${x("rule")}</th><th>${x("basis")}</th><th>${x("points")}</th></tr></thead><tbody>
        ${l.breakdown.map(r=>`<tr><td><b>${es(P.lang==="ar"?r.label_ar:r.label_en)}</b>
          <div class="mut" style="font-size:11px">${es(r.desc_ar)}</div></td>
          <td class="mut">${es(r.basis)}</td>
          <td><b style="color:${r.points<0?"var(--danger)":r.points>0?"var(--ok)":"var(--mut)"}">
            ${r.points>0?"+":""}${Math.round(r.points)}</b></td></tr>`).join("")}
      </tbody></table></div></div>`;
}

pboot();
