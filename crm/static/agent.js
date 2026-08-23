/* NebrasCRM Partner Portal — agents, distributors & sales reps */
const A = {
  token: localStorage.getItem("atok") || "", me: null, sum: null,
  lang: localStorage.getItem("lang") || "ar",
  theme: localStorage.getItem("theme") || "dark",
  tab: "home",
};
const TA = {
 ar:{portal:"بوابة الشركاء",welcome:"مرحباً",home:"الرئيسية",customers:"عملائي",deals:"صفقاتي",
  leads:"العملاء المحتملون",statement:"كشف الحساب",stock:"البضاعة",loyalty:"الولاء",requests:"الطلبات",
  profile:"الحساب",login:"تسجيل الدخول",email:"البريد الإلكتروني",password:"كلمة المرور",logout:"خروج",
  sales:"مبيعاتي",pipeline:"قيد التفاوض",balance:"رصيدي المستحق",target:"الهدف",achievement:"الإنجاز",
  commMonth:"عمولة الشهر",myCustomers:"عملائي",openDeals:"صفقات مفتوحة",rank:"ترتيبي",of:"من",
  credit:"لي",debit:"عليّ",monthly:"المبيعات الشهرية",noData:"لا توجد بيانات",name:"الاسم",
  phone:"الهاتف",revenue:"الإيراد",outstanding:"مستحقات",region:"المنطقة",segment:"الشريحة",
  amount:"القيمة",stage:"المرحلة",closing:"الإغلاق",nextStep:"الخطوة التالية",account:"الشركة",
  newLead:"عميل محتمل جديد",company:"الشركة",city:"المدينة",notes:"ملاحظات",estValue:"القيمة التقديرية",
  submit:"إرسال",cancel:"إلغاء",status:"الحالة",date:"التاريخ",kind:"النوع",running:"الرصيد",
  product:"المنتج",consigned:"مسلَّم",sold:"مباع",remaining:"المتبقي",tier:"الفئة",points:"النقاط",
  available:"المتاح",breakdown:"تفصيل النقاط",nextTier:"الفئة التالية",rules:"قواعد البرنامج",
  requestPayout:"طلب صرف مستحقات",requestStock:"طلب بضاعة",requestSupport:"طلب دعم",
  newRequest:"طلب جديد",pending:"قيد المراجعة",approved:"موافق عليه",rejected:"مرفوض",
  reply:"الرد",subject:"الموضوع",body:"التفاصيل",changePw:"تغيير كلمة المرور",current:"الحالية",
  newPw:"الجديدة",save:"حفظ",saved:"تم الحفظ",sent:"تم الإرسال",code:"الرمز",type:"النوع",
  rate:"نسبة العمولة",joined:"تاريخ الانضمام",territories:"مناطقي",demo:"حساب تجريبي (اضغط للتعبئة)",
  staffLogin:"دخول الموظفين",custLogin:"بوابة العملاء",exclusive:"حصري",perks:"المزايا",
  maxPayout:"الحد الأقصى",basis:"الأساس",rule:"القاعدة"},
 en:{portal:"Partner Portal",welcome:"Welcome",home:"Home",customers:"My Customers",deals:"My Deals",
  leads:"Leads",statement:"Statement",stock:"Stock",loyalty:"Loyalty",requests:"Requests",
  profile:"Profile",login:"Sign in",email:"Email",password:"Password",logout:"Logout",
  sales:"My Sales",pipeline:"Pipeline",balance:"My Balance",target:"Target",achievement:"Achievement",
  commMonth:"This month",myCustomers:"My customers",openDeals:"Open deals",rank:"My rank",of:"of",
  credit:"Credit",debit:"Debit",monthly:"Monthly sales",noData:"No data",name:"Name",
  phone:"Phone",revenue:"Revenue",outstanding:"Outstanding",region:"Region",segment:"Segment",
  amount:"Amount",stage:"Stage",closing:"Closing",nextStep:"Next step",account:"Account",
  newLead:"New lead",company:"Company",city:"City",notes:"Notes",estValue:"Estimated value",
  submit:"Submit",cancel:"Cancel",status:"Status",date:"Date",kind:"Kind",running:"Balance",
  product:"Product",consigned:"Consigned",sold:"Sold",remaining:"Remaining",tier:"Tier",points:"Points",
  available:"Available",breakdown:"Points breakdown",nextTier:"Next tier",rules:"Program rules",
  requestPayout:"Request payout",requestStock:"Request stock",requestSupport:"Support request",
  newRequest:"New request",pending:"Pending",approved:"Approved",rejected:"Rejected",
  reply:"Reply",subject:"Subject",body:"Details",changePw:"Change password",current:"Current",
  newPw:"New",save:"Save",saved:"Saved",sent:"Sent",code:"Code",type:"Type",
  rate:"Commission rate",joined:"Joined",territories:"My territories",demo:"Demo account (click to fill)",
  staffLogin:"Staff login",custLogin:"Customer portal",exclusive:"exclusive",perks:"Perks",
  maxPayout:"Max",basis:"Basis",rule:"Rule"},
};
const y = k => TA[A.lang][k] || k;

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
const es = s => String(s??"").replace(/[&<>"]/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const mny = v => (v==null||v==="")?"—":new Intl.NumberFormat(A.lang==="ar"?"ar-EG":"en-US",
  {style:"currency",currency:"USD",maximumFractionDigits:0}).format(v);
const num = v => new Intl.NumberFormat(A.lang==="ar"?"ar-EG":"en-US").format(Math.round(v||0));
const CL={Open:"var(--info)","Closed Won":"var(--ok)","Closed Lost":"var(--danger)",
 Negotiation:"var(--warn)",Proposal:"var(--info)",Qualification:"var(--mut)",
 pending:"var(--warn)",approved:"var(--ok)",rejected:"var(--danger)",New:"var(--info)",
 Qualified:"var(--ok)",Contacted:"var(--warn)",Hot:"var(--danger)",Warm:"var(--warn)",Cold:"var(--info)"};
const bg = v => v==null||v===""?"—":`<span class="badge" style="color:${CL[v]||"var(--mut)"};background:${CL[v]||"var(--mut)"}22;border-color:${CL[v]||"var(--mut)"}55">${es(v)}</span>`;

async function aa(path, opts={}) {
  const r = await fetch("/agent/api"+path, {...opts, headers:{"Content-Type":"application/json",
    ...(A.token?{Authorization:"Bearer "+A.token}:{}), ...(opts.headers||{})}});
  if (r.status===401){alogout();throw new Error("auth");}
  if(!r.ok){const e=await r.json().catch(()=>({detail:"Error"}));tst(e.detail||"Error");throw new Error(e.detail);}
  return r.json();
}
function tst(m){const d=document.createElement("div");d.className="toast";d.textContent=m;
  document.body.append(d);setTimeout(()=>d.remove(),3000);}
function alogout(){localStorage.removeItem("atok");A.token="";A.me=null;paint();}

async function aboot(){
  if(A.token&&!A.me){try{A.me=await aa("/me");}catch{return paint();}}
  paint();
}
function applyShell(){
  const rtl = A.lang==="ar";
  document.documentElement.lang = A.lang;
  document.documentElement.dir = rtl?"rtl":"ltr";
  document.body.dir = rtl?"rtl":"ltr";
  document.body.classList.toggle("light", A.theme==="light");
  const mt=document.querySelector('meta[name="theme-color"]');
  if(mt) mt.setAttribute("content", A.theme==="light"?"#EEF2F8":"#2B4ACB");
}
function paint(){
  applyShell();
  A.me?shell():alogin();
}
function alogin(){
  const ar=A.lang==="ar";
  const T=ar?{h:"بوابة الشركاء",h2:"وكلاء وموزعون ومندوبون",
    p:"تابع مبيعاتك وعمولاتك ورصيدك المستحق، وقدّم عملاءك من الميدان، واطلب صرف مستحقاتك — من أي مكان.",
    f:[["مبيعاتي وعمولاتي","نسب تصاعدية ولوحة إنجاز الهدف"],
       ["كشف حساب جارٍ","ما لك وما عليك برصيد تراكمي"],
       ["تقديم عميل من الميدان","يصل فوراً لفريق المبيعات"],
       ["طلب صرف وبضاعة","متابعة حالة كل طلب"]],
    welcome:"أهلاً بك 👋",sub:"سجّل الدخول لبوابة الشركاء",
    demo:"حسابات تجريبية — اضغط للدخول",signing:"جارٍ الدخول...",
    staff:"دخول الموظفين",cust:"بوابة العملاء",home:"الرئيسية"}
  :{h:"Partner Portal",h2:"agents, distributors & reps",
    p:"Track your sales, commissions and balance, submit field leads, and request payouts — from anywhere.",
    f:[["My sales and commissions","Tiered rates and a target progress ring"],
       ["Running statement","Credit and debit with a rolling balance"],
       ["Submit a field lead","Reaches the sales team instantly"],
       ["Payout and stock requests","Track the status of every request"]],
    welcome:"Welcome 👋",sub:"Sign in to the partner portal",
    demo:"Demo accounts — click to sign in",signing:"Signing in...",
    staff:"Staff login",cust:"Customer portal",home:"Home"};
  const DEMO=[["agent0@partners.ye",ar?"وكيل":"Agent"],["agent1@partners.ye",ar?"موزع":"Distributor"],
              ["agent6@partners.ye",ar?"مندوب":"Sales rep"],["agent9@partners.ye",ar?"وسيط":"Broker"]];
  document.body.innerHTML=`
    <div class="auth-bg"><i style="background:#f97316"></i><i></i><i style="background:#f59e0b"></i></div>
    <div class="auth-grid"></div>
    <div class="auth">
      <div class="auth-art">
        <a href="/" class="logo" style="font-size:21px"><span class="mark"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</a>
        <div><h2>${T.h}<br><span class="gr">${T.h2}</span></h2>
          <p style="margin-top:14px">${T.p}</p></div>
        <div class="auth-feats">${T.f.map(([p,q])=>`<div><span class="tick">✓</span>
          <span><b>${es(p)}</b><br>${es(q)}</span></div>`).join("")}</div>
      </div>
      <div class="auth-side"><form class="auth-card" id="af">
        <div class="logo"><span class="mark"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</div>
        <div class="auth-sub">🤝 ${T.h}</div>
        <div style="font-size:19px;font-weight:800">${T.welcome}</div>
        <div class="auth-sub" style="margin:5px 0 20px">${T.sub}</div>
        <div id="aerr"></div>
        <div class="ifield"><span class="ico">✉️</span>
          <input id="ae" type="email" placeholder="${y("email")}" value="agent0@partners.ye" required></div>
        <div class="ifield"><span class="ico">🔒</span>
          <input id="ap" type="password" placeholder="${y("password")}" value="agent123" required>
          <button type="button" class="eye" id="aey">👁️</button></div>
        <button class="btn-auth" id="asb">${y("login")} →</button>
        <div class="divider">${T.demo}</div>
        <div class="demo-grid">${DEMO.map(([e,r])=>`<button type="button" data-e="${e}">
          <b>${es(r)}</b><small>${e}</small></button>`).join("")}</div>
        <div class="auth-links">
          <a href="/">${T.home}</a><a href="/app">${T.staff}</a><a href="/portal">${T.cust}</a>
          <a id="al">${ar?"English":"العربية"}</a>
          <a id="ath">${A.theme==="dark"?"☀️":"🌙"}</a></div>
      </form></div>
    </div>`;
  aey.onclick=()=>{ap.type=ap.type==="password"?"text":"password";aey.textContent=ap.type==="password"?"👁️":"🙈";};
  al.onclick=()=>{A.lang=A.lang==="ar"?"en":"ar";localStorage.setItem("lang",A.lang);paint();};
  ath.onclick=()=>{A.theme=A.theme==="dark"?"light":"dark";localStorage.setItem("theme",A.theme);paint();};
  document.querySelectorAll(".demo-grid button").forEach(b=>b.onclick=()=>{
    ae.value=b.dataset.e;ap.value="agent123";af.requestSubmit();});
  af.onsubmit=async e=>{e.preventDefault();
    const btn=document.getElementById("asb");btn.disabled=true;btn.textContent=T.signing;aerr.innerHTML="";
    try{const r=await fetch("/agent/api/login",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email:ae.value,password:ap.value})});
      const j=await r.json(); if(!r.ok) throw new Error(j.detail||"Error");
      A.token=j.token;localStorage.setItem("atok",j.token);A.me=await aa("/me");A.tab="home";paint();
    }catch(err){aerr.innerHTML=`<div class="auth-err">⚠ ${es(err.message)}</div>`;
      btn.disabled=false;btn.textContent=y("login")+" →";}};
}

function shell(){
  applyShell();
  const tabs=[["home","📊 "+y("home")],["customers","🏢 "+y("customers")],["deals","💰 "+y("deals")],
    ["leads","🌱 "+y("leads")],["statement","📒 "+y("statement")],["stock","📦 "+y("stock")],
    ["loyalty","🏆 "+y("loyalty")],["requests","📨 "+y("requests")],["profile","👤 "+y("profile")]];
  document.body.innerHTML=`<div class="atop"><div class="in">
      <div class="logo" style="font-size:18px"><span class="mark" style="width:28px;height:28px"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</div>
      <span class="mut" style="font-size:12px">${y("portal")}</span>
      <div style="flex:1"></div>
      <div style="text-align:end;line-height:1.3"><div style="font-weight:700;font-size:13px">${es(A.me.name)}</div>
        <div class="mut" style="font-size:11px">${es(A.me.code||"")} · ${es(A.me.gov||"")}</div></div>
      <button class="icbtn" id="th">${A.theme==="dark"?"☀️":"🌙"}</button>
      <button class="btn sm" id="lg">${A.lang==="ar"?"EN":"ع"}</button>
      <button class="btn sm" id="lo">${y("logout")}</button></div></div>
    <div class="ashell"><div class="atabs">${tabs.map(([k,l])=>`<button data-t="${k}" class="${A.tab===k?"on":""}">${l}</button>`).join("")}</div>
    <div id="ac"><div class="empty">…</div></div></div>`;
  th.onclick=()=>{A.theme=A.theme==="dark"?"light":"dark";localStorage.setItem("theme",A.theme);paint();};
  lg.onclick=()=>{A.lang=A.lang==="ar"?"en":"ar";localStorage.setItem("lang",A.lang);paint();};
  lo.onclick=alogout;
  document.querySelectorAll(".atabs button").forEach(b=>b.onclick=()=>{A.tab=b.dataset.t;shell();});
  ({home:aHome,customers:aCust,deals:aDeals,leads:aLeads,statement:aStmt,
    stock:aStock,loyalty:aLoy,requests:aReq,profile:aProf}[A.tab])();
}

async function aHome(){
  const s=await aa("/summary"); A.sum=s;
  const k=(l,v,c)=>`<div class="kpi" style="--pri:${c}"><div class="l">${l}</div><div class="v">${v}</div></div>`;
  const mx=Math.max(...s.monthly.map(m=>m.v||0),1);
  ac.innerHTML=`<div class="card" style="margin-bottom:14px;background:linear-gradient(135deg,var(--pri)22,transparent)">
      <div class="row" style="flex-wrap:wrap;gap:16px">
        <div style="flex:1;min-width:200px">
          <div style="font-size:19px;font-weight:800">${y("welcome")}، ${es(A.me.name)} 👋</div>
          <div class="mut">${es(A.me.type||"")} · ${es(A.me.gov||"")} ${A.me.district?"· "+es(A.me.district):""}</div>
          <div class="mut" style="font-size:12px;margin-top:4px">${y("rate")}: <b>${A.me.rate}${A.me.commission_model==="flat"?"":"%"}</b>
            ${s.rank?` · ${y("rank")}: <b>${s.rank}</b> ${y("of")} ${s.peer_count}`:""}</div></div>
        ${s.achievement!=null?`<div class="ring" style="--p:${Math.min(100,s.achievement)}">
          <div><div style="text-align:center"><b style="font-size:17px">${s.achievement}%</b>
          <div class="mut" style="font-size:10px">${y("achievement")}</div></div></div></div>`:""}
      </div></div>
    <div class="kpis" style="margin-bottom:16px">
      ${k(y("sales"),mny(s.sales),"var(--ok)")}
      ${k(y("balance"),mny(s.balance),s.balance>=0?"var(--ok)":"var(--danger)")}
      ${k(y("commMonth"),mny(s.commission_month),"var(--purple)")}
      ${k(y("pipeline"),mny(s.pipeline),"var(--warn)")}
      ${k(y("target"),mny(s.target),"var(--info)")}
      ${k(y("myCustomers"),num(s.customers),"var(--info)")}
      ${k(y("openDeals"),num(s.open_deals),"var(--warn)")}
      ${k(y("loyalty"),num(s.loyalty.points)+" · "+(A.lang==="ar"?s.loyalty.tier.ar:s.loyalty.tier.en),TC(s.loyalty.tier.color))}</div>
    <div class="card"><b>${y("monthly")}</b><div style="height:10px"></div>
      ${s.monthly.length?`<div class="bars">${s.monthly.map(m=>`<div class="bar">
        <div>${es(m.k)}</div><div class="barbg"><div class="barfill" style="width:${(m.v||0)/mx*100}%"></div></div>
        <div style="text-align:end;font-weight:700">${mny(m.v)}</div></div>`).join("")}</div>`
        :`<div class="empty">${y("noData")}</div>`}</div>`;
}
async function aCust(){
  const cs=await aa("/customers");
  ac.innerHTML=`<div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
    <th>${y("name")}</th><th>${y("region")}</th><th>${y("phone")}</th><th>${y("segment")}</th>
    <th>${y("revenue")}</th><th>${y("outstanding")}</th></tr></thead><tbody>
    ${cs.map(c=>`<tr><td><b>${es(c.name)}</b><div class="mut" style="font-size:11px">${es(c.industry||"")}</div></td>
      <td class="mut">${es(c.gov_ar||"—")}${c.dis_ar?" · "+es(c.dis_ar):""}</td>
      <td class="mut">${es(c.phone||"—")}</td><td>${bg(c.segment)}</td>
      <td><b>${mny(c.revenue)}</b></td>
      <td style="color:${c.outstanding>0?"var(--danger)":"var(--mut)"}">${mny(c.outstanding)}</td></tr>`).join("")
      ||`<tr><td colspan="6"><div class="empty">${y("noData")}</div></td></tr>`}
    </tbody></table></div></div>`;
}
async function aDeals(){
  const ds=await aa("/deals");
  ac.innerHTML=`<div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
    <th>${y("name")}</th><th>${y("account")}</th><th>${y("amount")}</th><th>${y("stage")}</th>
    <th>%</th><th>${y("closing")}</th><th>${y("nextStep")}</th></tr></thead><tbody>
    ${ds.map(d=>`<tr><td><b>${es(d.name)}</b></td><td class="mut">${es(d.account||"—")}</td>
      <td><b>${mny(d.amount)}</b></td><td>${bg(d.stage)}</td>
      <td><div class="row"><div class="barbg" style="width:44px"><div class="barfill" style="width:${d.probability||0}%"></div></div>
        <span class="mut">${d.probability||0}</span></div></td>
      <td class="mut">${d.closing_date||"—"}</td><td class="mut" style="font-size:11.5px">${es(d.next_step||"—")}</td></tr>`).join("")
      ||`<tr><td colspan="7"><div class="empty">${y("noData")}</div></td></tr>`}
    </tbody></table></div></div>`;
}
async function aLeads(){
  const ls=await aa("/leads");
  ac.innerHTML=`<div class="row" style="margin-bottom:12px"><b style="font-size:16px">🌱 ${y("leads")}</b>
      <div style="flex:1"></div><button class="btn pri sm" id="nl">+ ${y("newLead")}</button></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${y("name")}</th><th>${y("company")}</th><th>${y("phone")}</th><th>${y("status")}</th>
      <th>${y("date")}</th></tr></thead><tbody>
      ${ls.map(l=>`<tr><td><b>${es(l.name)}</b></td><td class="mut">${es(l.company||"—")}</td>
        <td class="mut">${es(l.phone||"—")}</td><td>${bg(l.status)} ${bg(l.rating)}</td>
        <td class="mut">${(l.created_at||"").slice(0,10)}</td></tr>`).join("")
        ||`<tr><td colspan="5"><div class="empty">${y("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  nl.onclick=()=>{
    const el=md(y("newLead"),`<form id="lf" class="f2">
      <div class="fld"><label>${y("name")} *</label><input name="name" required></div>
      <div class="fld"><label>${y("company")}</label><input name="company"></div>
      <div class="fld"><label>${y("phone")}</label><input name="phone"></div>
      <div class="fld"><label>${y("email")}</label><input name="email" type="email"></div>
      <div class="fld"><label>${y("city")}</label><input name="city"></div>
      <div class="fld"><label>${y("estValue")}</label><input name="estimated_value" type="number"></div>
      <div class="fld" style="grid-column:span 2"><label>${y("notes")}</label><textarea name="description"></textarea></div>
    </form>`,[[y("cancel"),cl,""],[y("submit"),async()=>{
      const fd=new FormData(el.querySelector("#lf"));const b={};fd.forEach((v,k)=>b[k]=v);
      b.estimated_value=+b.estimated_value||0;
      if(!b.name.trim())return;
      try{await aa("/leads",{method:"POST",body:JSON.stringify(b)});tst(y("sent"));cl();aLeads();}catch{}},"pri"]]);};
}
async function aStmt(){
  const s=await aa("/statement"); const b=s.balance;
  ac.innerHTML=`<div class="kpis" style="margin-bottom:14px">
      <div class="kpi" style="--pri:var(--ok)"><div class="l">${y("credit")}</div><div class="v">${mny(b.credit)}</div></div>
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${y("debit")}</div><div class="v">${mny(b.debit)}</div></div>
      <div class="kpi" style="--pri:${b.balance>=0?"var(--ok)":"var(--danger)"}"><div class="l">${y("balance")}</div>
        <div class="v">${mny(b.balance)}</div></div></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${y("date")}</th><th>${y("kind")}</th><th>${y("notes")}</th><th>${y("amount")}</th>
      <th>${y("running")}</th></tr></thead><tbody>
      ${s.rows.map(r=>`<tr><td class="mut" style="font-size:11.5px">${(r.created_at||"").slice(0,10)}</td>
        <td><span class="badge" style="color:${r.signed>0?"var(--ok)":"var(--danger)"};background:${r.signed>0?"var(--ok)":"var(--danger)"}22">
          ${es(A.lang==="ar"?r.kind_ar:r.kind_en)}</span></td>
        <td class="mut" style="font-size:11.5px">${es((r.note||"").slice(0,48))}</td>
        <td><b style="color:${r.signed>0?"var(--ok)":"var(--danger)"}">${r.signed>0?"+":""}${mny(r.signed)}</b></td>
        <td class="mut">${mny(r.running)}</td></tr>`).join("")
        ||`<tr><td colspan="5"><div class="empty">${y("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
}
async function aStock(){
  const st=await aa("/stock");
  ac.innerHTML=`<div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
    <th>${y("product")}</th><th>${y("consigned")}</th><th>${y("sold")}</th><th>${y("remaining")}</th>
    <th>${y("amount")}</th></tr></thead><tbody>
    ${st.map(s=>`<tr><td><b>${es(s.product||"—")}</b><div class="mut" style="font-size:11px">${es(s.code||"")}</div></td>
      <td>${num(s.consigned)}</td><td style="color:var(--ok)">${num(s.sold)}</td>
      <td><b>${num(s.qty)}</b></td><td class="mut">${mny((s.qty||0)*(s.unit_price||0))}</td></tr>`).join("")
      ||`<tr><td colspan="5"><div class="empty">${y("noData")}</div></td></tr>`}
    </tbody></table></div></div>
    <div style="height:12px"></div><button class="btn sm" id="rs">📦 ${y("requestStock")}</button>`;
  rs.onclick=()=>reqForm("stock");
}
async function aLoy(){
  const l=await aa("/loyalty");
  ac.innerHTML=`<div class="row" style="gap:12px;flex-wrap:wrap;margin-bottom:14px">
      <div class="kpi" style="--pri:${TC(l.tier.color)};flex:1"><div class="l">${y("tier")}</div>
        <div class="v" style="font-size:19px">${A.lang==="ar"?l.tier.ar:l.tier.en}</div></div>
      <div class="kpi" style="--pri:var(--pri);flex:1"><div class="l">${y("points")}</div><div class="v">${num(l.points)}</div></div>
      <div class="kpi" style="--pri:var(--ok);flex:1"><div class="l">${y("available")}</div><div class="v">${num(l.available)}</div></div></div>
    <div class="card" style="margin-bottom:12px;font-size:12.5px">🎁 ${es(l.tier.perks_ar)}</div>
    ${l.next?`<div class="card" style="margin-bottom:12px">
      <div class="row"><span style="font-size:12.5px">${y("nextTier")}:
        <b style="color:${TC(l.next.tier.color)}">${A.lang==="ar"?l.next.tier.ar:l.next.tier.en}</b></span>
        <div style="flex:1"></div><span class="mut" style="font-size:12px">${num(l.next.gap)} ${y("points")}</span></div>
      <div class="barbg" style="margin-top:8px"><div class="barfill" style="width:${l.points/l.next.tier.min*100}%"></div></div></div>`:""}
    <div class="card"><b>${y("breakdown")}</b>
      <div class="wrap-scroll" style="margin-top:8px"><table class="tbl"><thead><tr>
      <th>${y("rule")}</th><th>${y("basis")}</th><th>${y("points")}</th></tr></thead><tbody>
      ${l.breakdown.map(r=>`<tr><td><b>${es(A.lang==="ar"?r.label_ar:r.label_en)}</b>
        <div class="mut" style="font-size:11px">${es(r.desc_ar)}</div></td>
        <td class="mut">${es(r.basis)}</td>
        <td><b style="color:${r.points<0?"var(--danger)":r.points>0?"var(--ok)":"var(--mut)"}">
          ${r.points>0?"+":""}${num(r.points)}</b></td></tr>`).join("")}
      </tbody></table></div></div>`;
}
async function aReq(){
  const rs=await aa("/requests");
  ac.innerHTML=`<div class="row" style="margin-bottom:12px;flex-wrap:wrap;gap:8px">
      <b style="font-size:16px">📨 ${y("requests")}</b><div style="flex:1"></div>
      <button class="btn pri sm" id="rp">💵 ${y("requestPayout")}</button>
      <button class="btn sm" id="rk">📦 ${y("requestStock")}</button>
      <button class="btn sm" id="rh">💬 ${y("requestSupport")}</button></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${y("date")}</th><th>${y("kind")}</th><th>${y("subject")}</th><th>${y("amount")}</th>
      <th>${y("status")}</th><th>${y("reply")}</th></tr></thead><tbody>
      ${rs.map(r=>`<tr><td class="mut" style="font-size:11.5px">${(r.created_at||"").slice(0,10)}</td>
        <td>${es(r.kind)}</td><td>${es(r.subject||"—")}</td>
        <td>${r.amount?mny(r.amount):"—"}</td><td>${bg(r.status)}</td>
        <td class="mut" style="font-size:11.5px">${es(r.reply||"—")}</td></tr>`).join("")
        ||`<tr><td colspan="6"><div class="empty">${y("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  rp.onclick=()=>reqForm("payout");rk.onclick=()=>reqForm("stock");rh.onclick=()=>reqForm("support");
}
async function reqForm(kind){
  const s=A.sum||await aa("/summary");
  const el=md(kind==="payout"?y("requestPayout"):kind==="stock"?y("requestStock"):y("requestSupport"),
    `<form id="qf">
      ${kind==="payout"?`<div class="card" style="background:var(--bg2);margin-bottom:12px;font-size:12.5px">
        ${y("balance")}: <b>${mny(s.balance)}</b> · ${y("maxPayout")}: <b>${mny(Math.max(0,s.balance))}</b></div>
        <div class="fld"><label>${y("amount")}</label><input name="amount" type="number" step="0.01"
          max="${Math.max(0,s.balance)}" required></div>`:""}
      <div class="fld"><label>${y("subject")}</label><input name="subject"></div>
      <div class="fld"><label>${y("body")}</label><textarea name="body"></textarea></div></form>`,
    [[y("cancel"),cl,""],[y("submit"),async()=>{
      const fd=new FormData(el.querySelector("#qf"));const b={kind};fd.forEach((v,k)=>b[k]=v);
      b.amount=+b.amount||0;
      try{await aa("/requests",{method:"POST",body:JSON.stringify(b)});tst(y("sent"));cl();
        A.tab="requests";shell();}catch{}},"pri"]]);
}
async function aProf(){
  const ts=await aa("/territories");
  ac.innerHTML=`<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
    <div class="card">${[[y("name"),A.me.name],[y("code"),A.me.code],[y("type"),A.me.type],
      [y("email"),A.me.email],[y("phone"),A.me.phone],[y("region"),A.me.gov],
      [y("rate"),A.me.rate+(A.me.commission_model==="flat"?"":"%")],[y("joined"),A.me.joined_at]]
      .map(([l,v])=>`<div style="padding:9px 0;border-bottom:1px solid var(--line)">
        <div class="mut" style="font-size:11.5px">${l}</div><div>${es(v||"—")}</div></div>`).join("")}</div>
    <div class="card"><b>🗺️ ${y("territories")}</b><div style="height:8px"></div>
      ${ts.length?ts.map(t=>`<div class="row" style="padding:7px 0;border-bottom:1px solid var(--line)">
        <span style="flex:1">${es(t.gov_ar||"")}${t.dis_ar?" / "+es(t.dis_ar):""}</span>
        ${t.exclusive?`<span class="badge" style="color:var(--ok);background:var(--ok)22">⭐ ${y("exclusive")}</span>`:""}
        </div>`).join(""):`<div class="mut" style="font-size:12.5px">${y("noData")}</div>`}</div>
    <div class="card"><b>🔒 ${y("changePw")}</b><div style="height:10px"></div>
      <div class="fld"><label>${y("current")}</label><input type="password" id="cp"></div>
      <div class="fld"><label>${y("newPw")}</label><input type="password" id="np"></div>
      <button class="btn pri sm" id="sp">${y("save")}</button></div></div>`;
  sp.onclick=async()=>{try{await aa("/password",{method:"POST",
    body:JSON.stringify({current:cp.value,new:np.value})});tst(y("saved"));cp.value=np.value="";}catch{}};
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
aboot();
