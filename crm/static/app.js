/* NebrasCRM — bilingual enterprise CRM SPA */
const S = {
  token: localStorage.getItem("tok") || "",
  user: null, meta: null, lang: localStorage.getItem("lang") || "ar",
  theme: localStorage.getItem("theme") || "dark",
  view: "dashboard", module: null, page: 1, q: "", sort: "id", dir: "desc",
  filters: [], mine: 0, sel: new Set(), viewMode: "list", data: [], total: 0, notifs: [],
};
const T = {
  ar: {dashboard:"لوحة التحكم",reports:"التقارير",settings:"الإعدادات",users:"المستخدمون",workflows:"الأتمتة",
    search:"بحث شامل...",new:"جديد",edit:"تعديل",delete:"حذف",save:"حفظ",cancel:"إلغاء",close:"إغلاق",
    export:"تصدير CSV",import:"استيراد",convert:"تحويل",records:"سجل",of:"من",page:"صفحة",noData:"لا توجد بيانات",
    logout:"خروج",mine:"سجلاتي فقط",all:"الكل",list:"قائمة",kanban:"كانبان",details:"التفاصيل",notes:"الملاحظات",
    history:"السجل",items:"البنود",addNote:"أضف ملاحظة...",post:"إرسال",selected:"محدد",bulkDelete:"حذف المحدد",
    total:"الإجمالي",filters:"الفلاتر",addFilter:"أضف فلتر",clear:"مسح",apply:"تطبيق",required:"حقل مطلوب",
    login:"تسجيل الدخول",email:"البريد الإلكتروني",password:"كلمة المرور",demoAccounts:"حسابات تجريبية (اضغط للتعبئة)",
    revenue:"الإيرادات المحققة",pipeline:"قيمة خط المبيعات",winRate:"نسبة الفوز",avgDeal:"متوسط الصفقة",
    leads:"عملاء محتملون",openDeals:"صفقات مفتوحة",openTickets:"تذاكر مفتوحة",overdue:"مهام متأخرة",
    unpaid:"مستحقات غير مدفوعة",byStage:"التوزيع حسب المرحلة",bySource:"حسب المصدر",leaderboard:"ترتيب المندوبين",
    monthly:"الإيرادات الشهرية",leadStatus:"حالات العملاء المحتملين",ticketStatus:"حالات التذاكر",activity:"آخر النشاطات",
    target:"الهدف",role:"الدور",active:"نشط",name:"الاسم",addUser:"مستخدم جديد",addWf:"قاعدة أتمتة جديدة",
    module:"الوحدة",field:"الحقل",operator:"الشرط",value:"القيمة",action:"الإجراء",runs:"مرات التنفيذ",
    reportBuilder:"منشئ التقارير",groupBy:"تجميع حسب",metric:"المقياس",run:"تشغيل",count:"عدد",sum:"مجموع",avg:"متوسط",
    notifications:"الإشعارات",noNotifs:"لا توجد إشعارات",converted:"تم التحويل بنجاح",saved:"تم الحفظ",deleted:"تم الحذف",
    confirmDel:"هل أنت متأكد من الحذف؟",addItem:"إضافة بند",qty:"الكمية",price:"السعر",disc:"خصم %",tax:"ضريبة %",
    product:"المنتج",lineTotal:"إجمالي البند",saveItems:"حفظ البنود",globalNoRes:"لا نتائج",portal:"بوابة العملاء",grantAccess:"منح صلاحية دخول",contact:"جهة الاتصال",lastLogin:"آخر دخول",revoke:"إلغاء الوصول",resetPw:"إعادة تعيين كلمة المرور",openPortal:"فتح البوابة",portalThread:"محادثة البوابة",replyCustomer:"الرد على العميل",credsMsg:"بيانات الدخول",email_m:"البريد الإلكتروني",outbox:"الصادر",templates:"القوالب",smtp:"إعدادات SMTP",compose:"رسالة جديدة",to:"إلى",subj:"الموضوع",body:"النص",sendMail:"إرسال",testMail:"إرسال رسالة اختبار",sandboxMode:"وضع الاختبار (لا يتم إرسال فعلي)",smtpMode:"مفعّل عبر SMTP",payments:"المدفوعات",collected:"المحصّل",pendingP:"قيد الانتظار",refunded:"مسترجع",outstandingP:"مستحقات",overdueP:"متأخرة",payLink:"رابط دفع",manualPay:"تسجيل دفعة",refund:"استرجاع",method:"الطريقة",ref:"المرجع",copy:"نسخ",copied:"تم النسخ",sendWithEmail:"إرسال الرابط بالبريد",emails:"رسائل البريد",invoice:"الفاتورة",payEvents:"سجل العملية",variables:"المتغيرات المتاحة",preview:"معاينة",intel:"ذكاء السوق",battlecard:"بطاقة المواجهة",matrix:"مصفوفة المقارنة",overview:"نظرة عامة",competitorsK:"المنافسون",primaryThreats:"تهديدات رئيسية",trackedProducts:"منتجات مرصودة",studiesK:"الدراسات",tam:"حجم السوق",avgGrowth:"متوسط النمو",ourShare:"حصتنا",contested:"صفقات متنازع عليها",lostTo:"خسائر للمنافسين",winLoss:"الفوز والخسارة حسب المنافس",lossReasons:"أسباب الخسارة",priceGap:"فجوة التسعير",positioningK:"الموقع التنافسي",marketShare:"الحصص السوقية",tamBySeg:"حجم السوق حسب الشريحة",threat:"التهديد",wonK:"فوز",lostK:"خسارة",openK:"مفتوحة",winRateK:"نسبة الفوز",vsUs:"مقابلنا",cheaper:"أرخص",pricier:"أغلى",strengths:"نقاط القوة",weaknesses:"نقاط الضعف",counterStrategy:"استراتيجيتنا",theirProducts:"منتجاتهم",recentDeals:"صفقات حديثة",ourPrice:"سعرنا",theirPrice:"سعرهم",gap:"الفرق",basis:"الأساس: لكل مستخدم/سنة",marketRange:"نطاق السوق",noRivals:"لا منافسين مرصودين",openBattlecard:"عرض بطاقة المواجهة",findings:"أهم النتائج",recommendations:"التوصيات",opps:"الفرص",oppPotential:"فرص محتملة",oppWon:"فرص محققة",oppLost:"فرص ضائعة",weighted:"القيمة المرجّحة",winReasons:"أسباب الفوز",convertOpp:"تحويل إلى صفقة",segmentsM:"تصنيف العملاء",lists:"القوائم",recompute:"إعادة احتساب التصنيف",applySeg:"تطبيق التصنيف",score:"النقاط",suggested:"المقترح",current:"الحالي",lastActivity:"آخر نشاط",daysIdle:"أيام الركود",tagAs:"تصنيف كـ",reason:"السبب",members:"الأعضاء",stagnant:"الرواكد",deadStock:"المنتجات الراكدة",idleCustomers:"العملاء الراكدون",tiedCapital:"رأس مال محتجز",neverSold:"لم يُبع أبداً",revenueAtRisk:"إيرادات معرضة للخطر",risk:"الخطورة",inStock:"بالمخزون",lastSold:"آخر بيع",channels:"وسائل الدفع",fees:"الرسوم",netAmt:"الصافي",awaitingS:"بانتظار التسوية",settle:"تأكيد الاستلام",blocked:"محظور",blacklistWarn:"هذا العميل في القائمة السوداء",geo:"الخريطة الإدارية العالمية",country:"دولة",region:"منطقة / ولاية",city:"مدينة",neighborhood:"حي",street:"شارع",governorate:"دولة",district:"منطقة",uzlah:"مدينة",village:"مدينة",quarter:"حي",partners:"الوكلاء والموزعون",partnerT:"وكيل",distributorT:"موزع",repT:"مندوب",brokerT:"وسيط",commission:"العمولة",commModel:"نموذج العمولة",rate:"النسبة",owedTo:"له",owedBy:"عليه",netBal:"الرصيد",statement:"كشف حساب",addTxn:"حركة جديدة",accrue:"احتساب العمولات",payout:"صرف",territoriesT:"المناطق",coverage:"التغطية",achievement:"نسبة الإنجاز",targetT:"الهدف",loyalty:"الولاء",tier:"الفئة",points:"النقاط",available:"المتاح",breakdown:"تفصيل النقاط",nextTier:"الفئة التالية",redeem:"استبدال",reward:"المكافأة",principles:"مبادئ البرنامج",programRules:"قواعد البرنامج",recomputeL:"إعادة الاحتساب",perks:"المزايا",discount:"الخصم",consigned:"بضاعة أمانة",sold:"مباع",addPartner:"وكيل جديد",locations:"المواقع",searchGeo:"ابحث عن دولة أو منطقة أو مدينة...",members:"الأعضاء",penaltiesL:"الخصومات",agentPortal:"بوابة الشركاء",agentReqs:"طلبات الشركاء",grantAgent:"منح دخول للشريك",approve:"موافقة",reject:"رفض",pendingR:"قيد المراجعة",replyR:"الرد",requestKind:"نوع الطلب",openAgent:"فتح بوابة الشركاء",ai:"المساعد الذكي",copilot:"مساعدي",digest:"موجز اليوم",forecast:"التنبؤ بالمبيعات",leadScoring:"ترتيب العملاء المحتملين",pipelineHealth:"صحة المسار",churnRisk:"مخاطر فقد العملاء",nba:"الخطوة القادمة الأفضل",whyThis:"لماذا؟",genEmail:"توليد رسالة",summarize:"تلخيص",view360:"العرض الشامل",timeline:"السجل الزمني",channelsL:"القنوات",winProb:"احتمالية الفوز",expected:"القيمة المتوقعة",atRisk:"معرّضة للخطر",factors:"العوامل",readiness:"الجاهزية",integrations:"التكاملات",apiKeys:"مفاتيح API",customFields:"الحقول المخصصة",builder:"منشئ اللوحات",addWidget:"إضافة عنصر",saveDash:"حفظ اللوحة",overdueTasks:"مهام متأخرة",todayTasks:"مهام اليوم",hotLeads:"الأكثر جاهزية",closingSoon:"قرب الإغلاق",enable:"تفعيل",disable:"تعطيل",newKey:"مفتاح جديد",scopes:"الصلاحيات",webhookUrl:"رابط الويب هوك",addField:"حقل جديد",fieldLabel:"التسمية",fieldType:"النوع",showInList:"إظهار بالقائمة",quota:"الحصة",committed:"مؤكدة",low:"متحفظ",high:"متفائل",generate:"توليد",meetingNotes:"ملاحظات الاجتماع",actionItems:"مهام مستخرجة",insert:"إدراج",aiOff:"يعمل محلياً بدون مفتاح",aiOn:"مدعوم بنموذج لغوي",reportCentre:"مركز التقارير",settingsSys:"إعدادات النظام",printR:"طباعة",exportCsv:"تصدير CSV",exportXls:"تصدير Excel",dateFrom:"من تاريخ",dateTo:"إلى تاريخ",runReport:"تشغيل",totalRow:"الإجمالي",records2:"سجل",generatedAt:"تاريخ الإصدار",noRows:"لا توجد بيانات لهذه الفترة",backToList:"رجوع للقائمة",saveSettings:"حفظ الإعدادات",thisMonth:"هذا الشهر",lastMonth:"الشهر الماضي",thisYear:"هذه السنة",allTime:"كل الفترات",quickRange:"فترة سريعة"},
  en: {dashboard:"Dashboard",reports:"Reports",settings:"Settings",users:"Users",workflows:"Automation",
    search:"Global search...",new:"New",edit:"Edit",delete:"Delete",save:"Save",cancel:"Cancel",close:"Close",
    export:"Export CSV",import:"Import",convert:"Convert",records:"records",of:"of",page:"Page",noData:"No data",
    logout:"Logout",mine:"My records",all:"All",list:"List",kanban:"Kanban",details:"Details",notes:"Notes",
    history:"History",items:"Line Items",addNote:"Add a note...",post:"Post",selected:"selected",bulkDelete:"Delete selected",
    total:"Total",filters:"Filters",addFilter:"Add filter",clear:"Clear",apply:"Apply",required:"Required",
    login:"Sign in",email:"Email",password:"Password",demoAccounts:"Demo accounts (click to fill)",
    revenue:"Revenue Won",pipeline:"Pipeline Value",winRate:"Win Rate",avgDeal:"Avg Deal Size",
    leads:"Leads",openDeals:"Open Deals",openTickets:"Open Tickets",overdue:"Overdue Tasks",
    unpaid:"Unpaid Invoices",byStage:"Deals by Stage",bySource:"By Source",leaderboard:"Sales Leaderboard",
    monthly:"Monthly Revenue",leadStatus:"Lead Status",ticketStatus:"Ticket Status",activity:"Recent Activity",
    target:"Target",role:"Role",active:"Active",name:"Name",addUser:"New User",addWf:"New Automation Rule",
    module:"Module",field:"Field",operator:"Operator",value:"Value",action:"Action",runs:"Runs",
    reportBuilder:"Report Builder",groupBy:"Group by",metric:"Metric",run:"Run",count:"Count",sum:"Sum",avg:"Average",
    notifications:"Notifications",noNotifs:"No notifications",converted:"Converted successfully",saved:"Saved",deleted:"Deleted",
    confirmDel:"Delete this record?",addItem:"Add item",qty:"Qty",price:"Price",disc:"Disc %",tax:"Tax %",
    product:"Product",lineTotal:"Line total",saveItems:"Save items",globalNoRes:"No results",portal:"Customer Portal",grantAccess:"Grant Access",contact:"Contact",lastLogin:"Last login",revoke:"Revoke",resetPw:"Reset password",openPortal:"Open portal",portalThread:"Portal Thread",replyCustomer:"Reply to customer",credsMsg:"Login credentials",email_m:"Email",outbox:"Outbox",templates:"Templates",smtp:"SMTP Settings",compose:"Compose",to:"To",subj:"Subject",body:"Body",sendMail:"Send",testMail:"Send test email",sandboxMode:"Sandbox mode (nothing is actually delivered)",smtpMode:"Live via SMTP",payments:"Payments",collected:"Collected",pendingP:"Pending",refunded:"Refunded",outstandingP:"Outstanding",overdueP:"Overdue",payLink:"Payment link",manualPay:"Record payment",refund:"Refund",method:"Method",ref:"Reference",copy:"Copy",copied:"Copied",sendWithEmail:"Email the link",emails:"Emails",invoice:"Invoice",payEvents:"Event log",variables:"Available variables",preview:"Preview",intel:"Market Intelligence",battlecard:"Battlecard",matrix:"Comparison Matrix",overview:"Overview",competitorsK:"Competitors",primaryThreats:"Primary Threats",trackedProducts:"Tracked Products",studiesK:"Studies",tam:"Total Market (TAM)",avgGrowth:"Avg Growth",ourShare:"Our Share",contested:"Contested Pipeline",lostTo:"Lost to Competitors",winLoss:"Win/Loss by Competitor",lossReasons:"Why We Lose",priceGap:"Price Gap",positioningK:"Positioning",marketShare:"Market Share",tamBySeg:"Market Size by Segment",threat:"Threat",wonK:"Won",lostK:"Lost",openK:"Open",winRateK:"Win Rate",vsUs:"vs Us",cheaper:"cheaper",pricier:"pricier",strengths:"Strengths",weaknesses:"Weaknesses",counterStrategy:"Our Counter-Strategy",theirProducts:"Their Products",recentDeals:"Recent Deals",ourPrice:"Our Price",theirPrice:"Their Price",gap:"Gap",basis:"Basis: per user / year",marketRange:"Market Range",noRivals:"No rivals tracked",openBattlecard:"Open battlecard",findings:"Key Findings",recommendations:"Recommendations",opps:"Opportunities",oppPotential:"Potential",oppWon:"Won",oppLost:"Lost",weighted:"Weighted Value",winReasons:"Win Reasons",convertOpp:"Convert to Deal",segmentsM:"Customer Segments",lists:"Lists",recompute:"Recompute",applySeg:"Apply segments",score:"Score",suggested:"Suggested",current:"Current",lastActivity:"Last activity",daysIdle:"Days idle",tagAs:"Tag as",reason:"Reason",members:"Members",stagnant:"Stagnation",deadStock:"Dead Stock",idleCustomers:"Inactive Customers",tiedCapital:"Tied Capital",neverSold:"Never sold",revenueAtRisk:"Revenue at risk",risk:"Risk",inStock:"In stock",lastSold:"Last sold",channels:"Payment Channels",fees:"Fees",netAmt:"Net",awaitingS:"Awaiting settlement",settle:"Confirm receipt",blocked:"Blocked",blacklistWarn:"This account is blacklisted",geo:"Global Administrative Map",country:"Country",region:"Region / State",city:"City",neighborhood:"Neighborhood",street:"Street",governorate:"Country",district:"Region",uzlah:"City",village:"City",quarter:"Neighborhood",partners:"Agents & Distributors",partnerT:"Agent",distributorT:"Distributor",repT:"Sales Rep",brokerT:"Broker",commission:"Commission",commModel:"Commission model",rate:"Rate",owedTo:"Credit",owedBy:"Debit",netBal:"Balance",statement:"Statement",addTxn:"New transaction",accrue:"Accrue commissions",payout:"Payout",territoriesT:"Territories",coverage:"Coverage",achievement:"Achievement",targetT:"Target",loyalty:"Loyalty",tier:"Tier",points:"Points",available:"Available",breakdown:"Points breakdown",nextTier:"Next tier",redeem:"Redeem",reward:"Reward",principles:"Program principles",programRules:"Program rules",recomputeL:"Recompute",perks:"Perks",discount:"Discount",consigned:"Consigned",sold:"Sold",addPartner:"New partner",locations:"Locations",searchGeo:"Search country, region or city...",members:"Members",penaltiesL:"Penalties",agentPortal:"Partner Portal",agentReqs:"Partner Requests",grantAgent:"Grant partner access",approve:"Approve",reject:"Reject",pendingR:"Pending",replyR:"Reply",requestKind:"Request type",openAgent:"Open partner portal",ai:"AI Assistant",copilot:"Copilot",digest:"Today\u2019s brief",forecast:"Sales Forecast",leadScoring:"Lead Scoring",pipelineHealth:"Pipeline Health",churnRisk:"Churn Risk",nba:"Next Best Action",whyThis:"Why?",genEmail:"Generate email",summarize:"Summarize",view360:"360° View",timeline:"Timeline",channelsL:"Channels",winProb:"Win probability",expected:"Expected value",atRisk:"At risk",factors:"Factors",readiness:"Readiness",integrations:"Integrations",apiKeys:"API Keys",customFields:"Custom Fields",builder:"Dashboard Builder",addWidget:"Add widget",saveDash:"Save dashboard",overdueTasks:"Overdue tasks",todayTasks:"Today",hotLeads:"Hottest leads",closingSoon:"Closing soon",enable:"Enable",disable:"Disable",newKey:"New key",scopes:"Scopes",webhookUrl:"Webhook URL",addField:"New field",fieldLabel:"Label",fieldType:"Type",showInList:"Show in list",quota:"Quota",committed:"Committed",low:"Low",high:"High",generate:"Generate",meetingNotes:"Meeting notes",actionItems:"Action items",insert:"Insert",aiOff:"Runs locally, no key",aiOn:"LLM-powered",reportCentre:"Report Centre",settingsSys:"System Settings",printR:"Print",exportCsv:"Export CSV",exportXls:"Export Excel",dateFrom:"From",dateTo:"To",runReport:"Run",totalRow:"TOTAL",records2:"rows",generatedAt:"Generated",noRows:"No data for this period",backToList:"Back to list",saveSettings:"Save settings",thisMonth:"This month",lastMonth:"Last month",thisYear:"This year",allTime:"All time",quickRange:"Quick range"},
};
Object.assign(T.ar, {
  printPage:"طباعة الصفحة", printMatrix:"طباعة المصفوفة", printRecord:"طباعة السجل",
  printDocument:"طباعة المستند", printVoucher:"طباعة سند الدفع", paymentVoucher:"سند دفع",
});
Object.assign(T.en, {
  printPage:"Print page", printMatrix:"Print matrix", printRecord:"Print record",
  printDocument:"Print document", printVoucher:"Print payment voucher", paymentVoucher:"Payment voucher",
});
const t = k => (T[S.lang][k] || k);
const L = o => S.lang === "ar" ? (o.label_ar || o.ar || o.label_en) : (o.label_en || o.en);

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
const esc = s => String(s ?? "").replace(/[&<>"]/g, c => ({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;"}[c]));
const fmtMoney = v => (v == null || v === "") ? "—" : new Intl.NumberFormat(S.lang === "ar" ? "ar-EG" : "en-US",
  {style:"currency",currency:"USD",maximumFractionDigits:0}).format(v);
const fmtNum = v => new Intl.NumberFormat(S.lang==="ar"?"ar-EG":"en-US").format(Math.round(v||0));

async function api(path, opts = {}) {
  const r = await fetch("/api" + path, {...opts, headers: {"Content-Type":"application/json",
    ...(S.token ? {Authorization:"Bearer " + S.token} : {}), ...(opts.headers||{})}});
  if (r.status === 401) { logout(); throw new Error("auth"); }
  if (!r.ok) { const e = await r.json().catch(()=>({detail:"Error"})); toast(e.detail || "Error"); throw new Error(e.detail); }
  return r.json();
}
async function downloadApi(path, fallbackName){
  const r=await fetch("/api"+path,{headers:{...(S.token?{Authorization:"Bearer "+S.token}:{})}});
  if(r.status===401){logout();throw new Error("auth");}
  if(!r.ok){const e=await r.json().catch(()=>({detail:"Error"}));toast(e.detail||"Error");throw new Error(e.detail);}
  const blob=await r.blob(), cd=r.headers.get("Content-Disposition")||"";
  const match=/filename="?([^";]+)"?/i.exec(cd), a=document.createElement("a");
  a.href=URL.createObjectURL(blob);a.download=(match&&match[1])||fallbackName||"download";
  document.body.append(a);a.click();a.remove();setTimeout(()=>URL.revokeObjectURL(a.href),0);
}
function toast(msg){const d=document.createElement("div");d.className="toast";d.textContent=msg;document.body.append(d);setTimeout(()=>d.remove(),2600);}
function logout(){localStorage.removeItem("tok");S.token="";S.user=null;render();}

/* ---------- colors ---------- */
const COLOR = {
  "Closed Won":"var(--ok)","Closed Lost":"var(--danger)","Negotiation":"var(--warn)","Proposal":"var(--info)",
  "Qualification":"var(--mut)","Needs Analysis":"var(--purple)","New":"var(--info)","Contacted":"var(--warn)",
  "Qualified":"var(--ok)","Unqualified":"var(--danger)","Converted":"var(--purple)","Hot":"var(--danger)",
  "Warm":"var(--warn)","Cold":"var(--info)","Open":"var(--info)","In Progress":"var(--warn)","Escalated":"var(--danger)",
  "Closed":"var(--mut)","Completed":"var(--ok)","Not Started":"var(--mut)","Urgent":"var(--danger)","High":"var(--warn)",
  "Medium":"var(--info)","Low":"var(--mut)","Paid":"var(--ok)","Overdue":"var(--danger)","Draft":"var(--mut)",
  "Sent":"var(--info)","Accepted":"var(--ok)","Rejected":"var(--danger)","Active":"var(--ok)","Planning":"var(--info)",
};
const badge = v => v==null||v===""?"—":`<span class="badge" style="color:${COLOR[v]||"var(--mut)"};background:${COLOR[v]||"var(--mut)"}22;border-color:${COLOR[v]||"var(--mut)"}55">${esc(v)}</span>`;

/* ---------- boot ---------- */
async function boot(){
  document.body.dir = S.lang === "ar" ? "rtl" : "ltr";
  document.body.className = S.theme === "light" ? "light" : "";
  if (S.token && !S.user) { try { S.user = await api("/auth/me"); } catch { return render(); } }
  if (S.user && !S.meta) S.meta = await api("/meta");
  render();
}
function applyShell(){
  const rtl = S.lang === "ar";
  document.documentElement.lang = S.lang;
  document.documentElement.dir = rtl ? "rtl" : "ltr";
  document.body.dir = rtl ? "rtl" : "ltr";
  document.body.classList.toggle("light", S.theme === "light");
  const mt = document.querySelector('meta[name="theme-color"]');
  if (mt) mt.setAttribute("content", S.theme === "light" ? "#EEF2F8" : "#2B4ACB");
}

function render(){
  applyShell();
  if (!S.user) return renderLogin();
  renderApp();
}

/* ---------- login ---------- */
function renderLogin(){
  applyShell();
  const ar=S.lang==="ar";
  const T=ar?{
    tag:"منصة إدارة علاقات العملاء للمؤسسات",
    h:"أدر مبيعاتك", h2:"بذكاء يشرح نفسه",
    p:"منصة متكاملة تجمع المبيعات والتسويق والدعم والمخزون والمالية — بتعريب أصلي كامل وذكاء اصطناعي يعمل على خادمك.",
    f:[["15 وحدة عمل مترابطة","من العملاء المحتملين حتى الفواتير والمخزون"],
       ["7 محركات ذكاء اصطناعي","تنبؤ بالمبيعات وتسجيل العملاء — مع شرح كل نقطة"],
       ["36 قناة دفع","محافظ الجوال والحوالات المحلية والبوابات الدولية"],
       ["خريطة إدارية عالمية","252 دولة و3,865 منطقة وأكثر من 235 ألف مدينة حول العالم"]],
    badges:["عربي RTL أصلي","استضافة ذاتية","3 بوابات","بلا كود"],
    welcome:"أهلاً بعودتك 👋", sub:"سجّل الدخول للمتابعة إلى لوحة التحكم",
    demo:"حسابات تجريبية — اضغط للدخول مباشرة", signing:"جارٍ الدخول...",
    land:"الصفحة الرئيسية", cust:"بوابة العملاء", part:"بوابة الشركاء"
  }:{
    tag:"Enterprise Customer Relationship Platform",
    h:"Run your sales", h2:"with AI that explains itself",
    p:"A unified suite for sales, marketing, support, inventory and finance — native Arabic RTL and AI that runs on your own server.",
    f:[["15 connected modules","From leads all the way to invoices and stock"],
       ["7 AI engines","Forecasting and lead scoring — every point explained"],
       ["36 payment channels","Mobile wallets, remittance networks, global gateways"],
       ["Global administrative map","252 countries, 3,865 regions and 235,000+ cities worldwide"]],
    badges:["Native RTL","Self-hosted","3 portals","No-code"],
    welcome:"Welcome back 👋", sub:"Sign in to continue to your dashboard",
    demo:"Demo accounts — click to sign in instantly", signing:"Signing in...",
    land:"Home", cust:"Customer portal", part:"Partner portal"
  };
  const DEMO=[["admin@nebrascrm.io","admin123",ar?"مدير النظام":"Administrator"],
              ["manager@nebrascrm.io","manager123",ar?"مدير مبيعات":"Sales Manager"],
              ["sara@nebrascrm.io","sara123",ar?"مندوب مبيعات":"Sales Rep"],
              ["viewer@nebrascrm.io","viewer123",ar?"قراءة فقط":"Read-only"]];
  document.body.innerHTML=`
    <div class="auth-bg"><i></i><i></i><i></i></div><div class="auth-grid"></div>
    <div class="auth">
      <div class="auth-art">
        <a href="/" class="logo" style="font-size:21px"><span class="mark"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</a>
        <div>
          <h2>${T.h}<br><span class="gr">${T.h2}</span></h2>
          <p style="margin-top:14px">${T.p}</p>
        </div>
        <div class="auth-feats">
          ${T.f.map(([a,b])=>`<div><span class="tick">✓</span>
            <span><b>${esc(a)}</b><br>${esc(b)}</span></div>`).join("")}
        </div>
        <div class="auth-badges">${T.badges.map(b=>`<span>${esc(b)}</span>`).join("")}</div>
      </div>

      <div class="auth-side"><form class="auth-card" id="lf">
        <div class="logo"><span class="mark"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</div>
        <div class="auth-sub">${T.tag}</div>
        <div style="font-size:19px;font-weight:800">${T.welcome}</div>
        <div class="auth-sub" style="margin:5px 0 20px">${T.sub}</div>
        <div id="errbox"></div>
        <div class="ifield"><span class="ico">✉️</span>
          <input id="em" type="email" placeholder="${t("email")}" value="admin@nebrascrm.io" required autocomplete="username"></div>
        <div class="ifield"><span class="ico">🔒</span>
          <input id="pw" type="password" placeholder="${t("password")}" value="admin123" required autocomplete="current-password">
          <button type="button" class="eye" id="eye">👁️</button></div>
        <button class="btn-auth" id="sb">${t("login")} →</button>
        <div class="divider">${T.demo}</div>
        <div class="demo-grid">
          ${DEMO.map(([e,p,r])=>`<button type="button" data-e="${e}" data-p="${p}">
            <b>${esc(r)}</b><small>${e}</small></button>`).join("")}
        </div>
        <div class="auth-links">
          <a href="/">${T.land}</a><a href="/portal">${T.cust}</a><a href="/agent">${T.part}</a>
          <a id="lng">${ar?"English":"العربية"}</a>
          <a id="thm">${S.theme==="dark"?"☀️":"🌙"}</a>
        </div>
      </form></div>
    </div>`;

  eye.onclick=()=>{pw.type=pw.type==="password"?"text":"password";eye.textContent=pw.type==="password"?"👁️":"🙈";};
  lng.onclick=()=>{S.lang=S.lang==="ar"?"en":"ar";localStorage.setItem("lang",S.lang);render();};
  thm.onclick=()=>{S.theme=S.theme==="dark"?"light":"dark";localStorage.setItem("theme",S.theme);render();};
  document.querySelectorAll(".demo-grid button").forEach(b=>b.onclick=()=>{
    em.value=b.dataset.e;pw.value=b.dataset.p;lf.requestSubmit();});

  lf.onsubmit=async e=>{
    e.preventDefault();
    const btn=document.getElementById("sb");
    btn.disabled=true;btn.textContent=T.signing;
    errbox.innerHTML="";
    try{
      const r=await fetch("/api/auth/login",{method:"POST",headers:{"Content-Type":"application/json"},
        body:JSON.stringify({email:em.value,password:pw.value})});
      const j=await r.json();
      if(!r.ok) throw new Error(j.detail||"Error");
      S.token=j.token;S.user=j.user;localStorage.setItem("tok",j.token);
      S.meta=await api("/meta");S.view="dashboard";render();
    }catch(err){
      errbox.innerHTML=`<div class="auth-err">⚠ ${esc(err.message)}</div>`;
      btn.disabled=false;btn.textContent=t("login")+" →";
    }
  };
}

/* ---------- shell ---------- */
function renderApp(){
  // Apply direction + theme on EVERY render. renderApp() is called directly by the
  // language/theme buttons, so if this lived only in render() those toggles would
  // change state without changing anything on screen.
  applyShell();
  const groups = {};
  const management = ["admin","manager"].includes(S.user.role);
  Object.entries(S.meta.modules).forEach(([k,m])=>{(groups[m.group]=groups[m.group]||[]).push([k,m]);});
  document.body.innerHTML = `<div class="app">
    <aside class="side" id="side">
      <div class="brand"><div class="logo"><span class="mark"><svg viewBox=\"0 0 64 64\" width=\"100%\" height=\"100%\" aria-hidden=\"true\"><defs><linearGradient id=\"nbf\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#fff\"/><stop offset=\".55\" stop-color=\"#FFF3D6\"/><stop offset=\"1\" stop-color=\"#FFC53D\"/></linearGradient><linearGradient id=\"nbc\" x1=\".5\" y1=\"0\" x2=\".5\" y2=\"1\"><stop offset=\"0\" stop-color=\"#FFC53D\"/><stop offset=\"1\" stop-color=\"#FF9F1C\"/></linearGradient></defs><path d=\"M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z\" fill=\"url(#nbf)\"/><path d=\"M32.6 26C33 30.4 37.2 32.6 38.6 36.6C39.8 40.1 38.4 44 35.3 45.9C32 47.9 27.4 47 25.3 43.9C23.2 40.8 23.8 37.2 25.6 34.6C26.6 36 27.6 36.6 28.5 36.7C28 32.6 29.8 28.9 32.6 26Z\" fill=\"url(#nbc)\"/></svg></span> NebrasCRM</div></div>
      <nav class="nav">
        <a data-v="dashboard" class="${S.view==="dashboard"?"on":""}"><span class="ic">📊</span>${t("dashboard")}</a>
        <a data-v="ai" class="${S.view==="ai"?"on":""}"><span class="ic">🤖</span>${t("ai")}</a>
        <a data-v="reports" class="${S.view==="reports"?"on":""}"><span class="ic">📈</span>${t("reports")}</a>
        ${management?`<a data-v="repcentre" class="${S.view==="repcentre"?"on":""}"><span class="ic">📑</span>${t("reportCentre")}</a>`:""}
        <a data-v="builder" class="${S.view==="builder"?"on":""}"><span class="ic">🧱</span>${t("builder")}</a>
        ${management?`<a data-v="emails" class="${S.view==="emails"?"on":""}"><span class="ic">✉️</span>${t("email_m")}</a>`:""}
        <a data-v="payments" class="${S.view==="payments"?"on":""}"><span class="ic">💳</span>${t("payments")}</a>
        ${S.user.role!=="readonly"?`<a data-v="pos" class="${S.view==="pos"?"on":""}"><span class="ic">🛒</span>${S.lang==="ar"?"نقطة البيع":"Point of Sale"}</a>`:""}
        <a data-v="intel" class="${S.view==="intel"?"on":""}"><span class="ic">🎯</span>${t("intel")}</a>
        ${management?`<a data-v="segments" class="${S.view==="segments"?"on":""}"><span class="ic">🏅</span>${t("segmentsM")}</a>`:""}
        ${management?`<a data-v="stagnant" class="${S.view==="stagnant"?"on":""}"><span class="ic">🧊</span>${t("stagnant")}</a>`:""}
        ${management?`<a data-v="loyalty" class="${S.view==="loyalty"?"on":""}"><span class="ic">🏆</span>${t("loyalty")}</a>`:""}
        <div class="grp">${S.lang==="ar"?"الشبكة والجغرافيا":"Network & Geography"}</div>
        ${management?`<a data-v="partners" class="${S.view==="partners"?"on":""}"><span class="ic">🤝</span>${t("partners")}</a>`:""}
        <a data-v="geo" class="${S.view==="geo"?"on":""}"><span class="ic">🗺️</span>${t("geo")}</a>
        ${Object.entries(groups).map(([g,mods])=>`<div class="grp">${L(S.meta.groups[g])}</div>`+
          mods.map(([k,m])=>`<a data-m="${k}" class="${S.view==="module"&&S.module===k?"on":""}"><span class="ic">${m.icon}</span>${L(m)}</a>`).join("")).join("")}
        ${S.user.role==="admin"||S.user.role==="manager"?`<div class="grp">${t("settings")}</div>
          ${S.user.role==="admin"?`<a data-v="users" class="${S.view==="users"?"on":""}"><span class="ic">👥</span>${t("users")}</a>`:""}
          <a data-v="workflows" class="${S.view==="workflows"?"on":""}"><span class="ic">⚡</span>${t("workflows")}</a>
          <a data-v="portal" class="${S.view==="portal"?"on":""}"><span class="ic">🌐</span>${t("portal")}</a>
          <a data-v="aportal" class="${S.view==="aportal"?"on":""}"><span class="ic">🔑</span>${t("agentPortal")}</a>
          <a data-v="integrations" class="${S.view==="integrations"?"on":""}"><span class="ic">🔌</span>${t("integrations")}</a>
          <a data-v="cfields" class="${S.view==="cfields"?"on":""}"><span class="ic">🏷️</span>${t("customFields")}</a>
          <a data-v="syssettings" class="${S.view==="syssettings"?"on":""}"><span class="ic">⚙️</span>${t("settingsSys")}</a>`:""}
      </nav>
      <div style="padding:12px;border-top:1px solid var(--line)" class="row">
        <div style="width:32px;height:32px;border-radius:99px;background:var(--pri);display:grid;place-items:center;font-weight:800;color:#fff">${esc(S.user.name[0])}</div>
        <div style="flex:1;min-width:0"><div style="font-weight:700;font-size:13px;overflow:hidden;text-overflow:ellipsis">${esc(S.user.name)}</div>
        <div class="mut" style="font-size:11px">${L(S.meta.roles[S.user.role])}</div></div>
        <button class="icbtn" id="out" title="${t("logout")}">⏻</button>
      </div>
    </aside>
    <div>
      <div class="top">
        <button class="icbtn" id="burger" style="display:none">☰</button>
        <div class="search"><input id="gs" placeholder="${t("search")}"><div id="sres"></div></div>
        <div class="spacer"></div>
        <button class="icbtn" id="bell">🔔<span id="bdot"></span></button>
        <button class="btn sm" id="pagePrint" title="${t("printPage")}">🖨 <span class="print-page-label">${t("printPage")}</span></button>
        <button class="icbtn" id="thm">${S.theme==="dark"?"☀️":"🌙"}</button>
        <button class="btn sm" id="lng">${S.lang==="ar"?"EN":"ع"}</button>
      </div>
      <div class="main" id="main"></div>
    </div>
    <nav class="fabbar">
      <a data-v="dashboard" class="${S.view==="dashboard"?"on":""}"><div>📊</div>${t("dashboard")}</a>
      <a data-v="ai" class="${S.view==="ai"?"on":""}"><div>🤖</div>${t("ai")}</a>
      <a data-m="deals" class="${S.module==="deals"?"on":""}"><div>💰</div>${L(S.meta.modules.deals)}</a>
      <a data-m="activities" class="${S.module==="activities"?"on":""}"><div>✅</div>${L(S.meta.modules.activities)}</a>
      <a data-v="__menu"><div>☰</div>${S.lang==="ar"?"المزيد":"More"}</a>
    </nav></div>`;
  document.querySelectorAll(".fabbar a").forEach(a=>a.onclick=()=>{
    if(a.dataset.v==="__menu")return side.classList.toggle("open");
    if(a.dataset.m){S.view="module";S.module=a.dataset.m;S.page=1;S.q="";S.filters=[];S.sel.clear();}
    else S.view=a.dataset.v;
    side.classList.remove("open");renderApp();});
  document.querySelectorAll(".nav a").forEach(a=>a.onclick=()=>{
    if(a.dataset.m){S.view="module";S.module=a.dataset.m;S.page=1;S.q="";S.filters=[];S.sel.clear();
      S.viewMode=S.meta.modules[a.dataset.m].kanban?"list":"list";}
    else S.view=a.dataset.v;
    side.classList.remove("open");renderApp();});
  out.onclick=logout;
  thm.onclick=()=>{S.theme=S.theme==="dark"?"light":"dark";localStorage.setItem("theme",S.theme);renderApp();};
  lng.onclick=()=>{S.lang=S.lang==="ar"?"en":"ar";localStorage.setItem("lang",S.lang);renderApp();};
  burger.style.display=window.innerWidth<900?"grid":"none";
  burger.onclick=()=>side.classList.toggle("open");
  bell.onclick=showNotifs;
  const pagePrintButton=document.getElementById("pagePrint");
  if(pagePrintButton) pagePrintButton.onclick=()=>printCurrentView();
  let tmr; gs.oninput=()=>{clearTimeout(tmr);tmr=setTimeout(doSearch,250);};
  gs.onblur=()=>setTimeout(()=>sres.innerHTML="",200);
  loadNotifBadge();
  ({dashboard:viewDashboard,module:viewModule,reports:viewReports,users:viewUsers,workflows:viewWorkflows,portal:viewPortal,emails:viewEmails,payments:viewPayments,pos:viewPOS,intel:viewIntel,segments:viewSegments,stagnant:viewStagnant,loyalty:viewLoyalty,partners:viewPartners,geo:viewGeo,aportal:viewAgentPortal,ai:viewAI,builder:viewBuilder,integrations:viewIntegrations,cfields:viewCFields,repcentre:viewReportCentre,syssettings:viewSysSettings}[S.view]||viewDashboard)();
}
async function doSearch(){
  const q=gs.value.trim(); if(q.length<2){sres.innerHTML="";return;}
  const r=await api("/search?q="+encodeURIComponent(q));
  sres.className="sres";
  sres.innerHTML=r.length?r.map(x=>`<div data-m="${x.module}" data-i="${x.id}"><span>${x.icon}</span>
    <span style="flex:1">${esc(x.title||"—")}</span><span class="mut" style="font-size:11px">${S.lang==="ar"?x.label_ar:x.label_en}</span></div>`).join("")
    :`<div class="mut">${t("globalNoRes")}</div>`;
  sres.querySelectorAll("div[data-m]").forEach(d=>d.onclick=()=>{sres.innerHTML="";gs.value="";
    S.view="module";S.module=d.dataset.m;renderApp();setTimeout(()=>openRecord(d.dataset.m,+d.dataset.i),60);});
}
async function loadNotifBadge(){
  try{S.notifs=await api("/notifications");
    const n=S.notifs.filter(x=>!x.read).length;
    bdot.innerHTML=n?`<span style="position:absolute;top:2px;inset-inline-end:2px;background:var(--danger);color:#fff;border-radius:99px;font-size:9px;padding:1px 4px">${n}</span>`:"";}catch{}
}
async function showNotifs(){
  await api("/notifications/read",{method:"POST"});
  modal(t("notifications"), S.notifs.length?S.notifs.map(n=>`<div style="padding:10px;border-bottom:1px solid var(--line)">
    <b>${esc(n.title)}</b><div class="mut" style="font-size:12px">${esc(n.body)}</div>
    <div class="mut" style="font-size:11px">${n.created_at}</div></div>`).join(""):`<div class="empty">${t("noNotifs")}</div>`,[]);
  loadNotifBadge();
}

/* ---------- dashboard ---------- */
async function viewDashboard(){
  main.innerHTML=`<div class="mut">…</div>`;
  const d=await api("/analytics/dashboard");
  const tl=await api("/timeline");
  const k=d.kpi;
  const kpi=(l,v,c)=>`<div class="kpi" style="--pri:${c}"><div class="l">${l}</div><div class="v">${v}</div></div>`;
  const bars=(arr,fmt=fmtNum,key="n")=>{const mx=Math.max(...arr.map(a=>+a[key]||0),1);
    return `<div class="bars">${arr.map(a=>`<div class="bar"><div style="overflow:hidden;text-overflow:ellipsis">${esc(a.k||"—")}</div>
      <div class="barbg"><div class="barfill" style="width:${(+a[key]||0)/mx*100}%"></div></div>
      <div style="text-align:end;font-weight:700">${fmt(a[key])}</div></div>`).join("")}</div>`;};
  main.innerHTML=`<div class="row" style="margin-bottom:16px"><div class="h1">${t("dashboard")}</div>
    <div class="spacer"></div><div class="mut">${new Date().toLocaleDateString(S.lang==="ar"?"ar-EG":"en-US",{dateStyle:"full"})}</div></div>
  <div class="kpis" style="margin-bottom:16px">
    ${kpi(t("revenue"),fmtMoney(k.revenue_won),"var(--ok)")}
    ${kpi(t("pipeline"),fmtMoney(k.pipeline_value),"var(--pri)")}
    ${kpi(t("winRate"),k.win_rate+"%","var(--purple)")}
    ${kpi(t("avgDeal"),fmtMoney(k.avg_deal),"var(--info)")}
    ${kpi(t("openDeals"),fmtNum(k.open_deals),"var(--warn)")}
    ${kpi(t("leads"),fmtNum(k.leads),"var(--info)")}
    ${kpi(t("openTickets"),fmtNum(k.open_tickets),"var(--danger)")}
    ${kpi(t("overdue"),fmtNum(k.overdue_tasks),"var(--danger)")}
    ${kpi(t("unpaid"),fmtMoney(k.unpaid),"var(--warn)")}
  </div>
  <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(340px,1fr))">
    <div class="card"><b>${t("byStage")}</b><div style="height:10px"></div>${bars(d.pipeline,fmtMoney,"v")}</div>
    <div class="card"><b>${t("leaderboard")}</b><div style="height:10px"></div>${bars(d.leaderboard,fmtMoney,"v")}</div>
    <div class="card"><b>${t("monthly")}</b><div style="height:10px"></div>${d.monthly.length?bars(d.monthly,fmtMoney,"v"):`<div class="empty">${t("noData")}</div>`}</div>
    <div class="card"><b>${t("bySource")}</b><div style="height:10px"></div>${bars(d.sources,fmtMoney,"v")}</div>
    <div class="card"><b>${t("leadStatus")}</b><div style="height:10px"></div>${bars(d.leads_status)}</div>
    <div class="card"><b>${t("ticketStatus")}</b><div style="height:10px"></div>${bars(d.tickets)}</div>
    <div class="card" style="grid-column:span 2"><b>${t("activity")}</b><div style="height:10px"></div>
      ${tl.slice(0,12).map(a=>`<div class="row" style="padding:7px 0;border-bottom:1px solid var(--line);font-size:13px">
        <span class="dot" style="background:${a.action==="create"?"var(--ok)":a.action==="delete"?"var(--danger)":"var(--info)"}"></span>
        <b>${esc(a.uname||"—")}</b><span class="mut">${a.action}</span>
        <span>${S.meta.modules[a.module]?L(S.meta.modules[a.module]):a.module} #${a.record_id}</span>
        <div class="spacer"></div><span class="mut" style="font-size:11px">${a.created_at.replace("T"," ")}</span></div>`).join("")}</div>
  </div>`;
}

/* ---------- module list ---------- */
async function viewModule(){
  const m = S.meta.modules[S.module];
  const canKanban = !!m.kanban;
  main.innerHTML=`<div class="row" style="margin-bottom:14px;flex-wrap:wrap">
      <div class="h1">${m.icon} ${L(m)}</div><div class="spacer"></div>
      ${S.module==="opportunities"?`<button class="btn sm" id="oan">📊 ${t("reports")}</button>`:""}
      ${canKanban?`<div class="tabs" style="border:none;margin:0">
        <button class="${S.viewMode==="list"?"on":""}" id="vl">${t("list")}</button>
        <button class="${S.viewMode==="kanban"?"on":""}" id="vk">${t("kanban")}</button></div>`:""}
      <button class="btn sm" id="flt">⚙ ${t("filters")}${S.filters.length?" ("+S.filters.length+")":""}</button>
      <button class="btn sm" id="pmatrix">🖨 ${t("printMatrix")}</button>
      <button class="btn sm" id="exp">⬇ ${t("export")}</button>
      <label class="btn sm" style="margin:0">⬆ ${t("import")}<input type="file" id="imp" accept=".csv" hidden></label>
      ${S.user.role!=="readonly"?`<button class="btn pri sm" id="add">+ ${t("new")}</button>`:""}
    </div>
    <div class="card" style="padding:0">
      <div class="row" style="padding:12px 14px;border-bottom:1px solid var(--line);flex-wrap:wrap">
        <input id="sq" value="${esc(S.q)}" placeholder="🔍" style="background:var(--bg2);border:1px solid var(--line);border-radius:9px;padding:7px 12px;min-width:220px">
        <label class="row" style="margin:0;font-size:13px;cursor:pointer"><input type="checkbox" id="mine" ${S.mine?"checked":""} style="width:auto">&nbsp;${t("mine")}</label>
        <div class="spacer"></div><div id="bulkbar"></div>
        <span class="mut" id="cnt"></span>
      </div>
      <div id="body" class="wrap-scroll"><div class="empty">…</div></div>
    </div>`;
  sq.oninput=debounce(()=>{S.q=sq.value;S.page=1;loadList();},300);
  mine.onchange=()=>{S.mine=mine.checked?1:0;S.page=1;loadList();};
  if(canKanban){vl.onclick=()=>{S.viewMode="list";viewModule();};vk.onclick=()=>{S.viewMode="kanban";viewModule();};}
  flt.onclick=filterDialog;
  document.getElementById("pmatrix").onclick=()=>printModuleMatrix();
  exp.onclick=()=>downloadApi(`/${S.module}/export/csv`,`${S.module}.csv`).catch(()=>{});
  imp.onchange=async e=>{const fd=new FormData();fd.append("file",e.target.files[0]);
    const r=await fetch(`/api/${S.module}/import`,{method:"POST",headers:{Authorization:"Bearer "+S.token},body:fd});
    const j=await r.json();toast(`${j.imported||0} ✓`);loadList();};
  if(document.getElementById("oan")) oan.onclick=oppAnalytics;
  if(document.getElementById("add")) add.onclick=()=>openForm(S.module,null);
  loadList();
}
function debounce(f,ms){let x;return(...a)=>{clearTimeout(x);x=setTimeout(()=>f(...a),ms);}}

async function loadList(){
  const m=S.meta.modules[S.module];
  const qs=new URLSearchParams({q:S.q,sort:S.sort,dir:S.dir,page:S.page,per_page:S.viewMode==="kanban"?200:25,
    mine:S.mine,filters:JSON.stringify(S.filters)});
  const r=await api(`/${S.module}?`+qs);
  S.data=r.data;S.total=r.total;
  cnt.textContent=`${fmtNum(r.total)} ${t("records")}`;
  if(S.viewMode==="kanban") return renderKanban(m);
  const cols=m.list;
  const fmap=Object.fromEntries(m.fields.map(f=>[f.name,f]));
  body.innerHTML=r.data.length?`<table class="tbl"><thead><tr>
      ${S.user.role!=="readonly"?`<th style="width:34px"><input type="checkbox" id="ckall"></th>`:""}
      ${cols.map(c=>`<th data-s="${c}">${L(fmap[c]||{label_en:c,label_ar:c})}${S.sort===c?(S.dir==="asc"?" ▲":" ▼"):""}</th>`).join("")}
      <th style="width:104px"></th></tr></thead><tbody>
      ${r.data.map(row=>{const isDocument=["invoices","quotes"].includes(S.module);
        return `<tr data-i="${row.id}">
        ${S.user.role!=="readonly"?`<td><input type="checkbox" class="ck" data-i="${row.id}" ${S.sel.has(row.id)?"checked":""}></td>`:""}
        ${cols.map(c=>`<td data-l="${esc(L(fmap[c]||{label_en:c,label_ar:c}))}">${cell(row,fmap[c]||{name:c,type:"text"})}</td>`).join("")}
        <td data-l="${t("printRecord")}"><button class="btn sm" ${isDocument?`data-doc="${row.id}" title="${t("printDocument")}"`:`data-recprint="${row.id}" title="${t("printRecord")}"`}>🖨</button>
          ${S.user.role!=="readonly"?`<button class="btn sm" data-e="${row.id}">✎</button>`:""}</td></tr>`;}).join("")}
    </tbody></table>
    <div class="row" style="padding:12px 14px">
      <button class="btn sm" id="prev" ${S.page<=1?"disabled":""}>‹</button>
      <span class="mut">${t("page")} ${S.page} / ${Math.max(1,Math.ceil(r.total/25))}</span>
      <button class="btn sm" id="next" ${S.page*25>=r.total?"disabled":""}>›</button></div>`
    :`<div class="empty">${t("noData")}</div>`;
  body.querySelectorAll("th[data-s]").forEach(h=>h.onclick=()=>{
    if(S.sort===h.dataset.s)S.dir=S.dir==="asc"?"desc":"asc";else{S.sort=h.dataset.s;S.dir="asc";}loadList();});
  body.querySelectorAll("[data-doc]").forEach(button=>button.onclick=event=>{
    event.stopPropagation();printDocument(S.module,+button.dataset.doc);});
  body.querySelectorAll("[data-recprint]").forEach(button=>button.onclick=event=>{
    event.stopPropagation();const row=r.data.find(item=>item.id===+button.dataset.recprint);
    if(row)printGenericRecord(S.module,row);});
  body.querySelectorAll("[data-e]").forEach(button=>button.onclick=event=>{
    event.stopPropagation();openForm(S.module,+button.dataset.e);});
  body.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=e=>{
    if(e.target.closest("input,button,a,label"))return;
    openRecord(S.module,+tr.dataset.i);});
  body.querySelectorAll(".ck").forEach(c=>c.onchange=()=>{c.checked?S.sel.add(+c.dataset.i):S.sel.delete(+c.dataset.i);bulk();});
  if(document.getElementById("ckall"))ckall.onchange=()=>{r.data.forEach(x=>ckall.checked?S.sel.add(x.id):S.sel.delete(x.id));loadList();bulk();};
  if(document.getElementById("prev")){prev.onclick=()=>{S.page--;loadList();};next.onclick=()=>{S.page++;loadList();};}
  bulk();
}
function bulk(){
  if(!document.getElementById("bulkbar"))return;
  bulkbar.innerHTML=S.sel.size?`<span class="mut">${S.sel.size} ${t("selected")}</span>
    <button class="btn sm dgr" id="bd">${t("bulkDelete")}</button>`:"";
  if(document.getElementById("bd"))bd.onclick=async()=>{
    if(!confirm(t("confirmDel")))return;
    await api(`/${S.module}/bulk`,{method:"POST",body:JSON.stringify({ids:[...S.sel],action:"delete"})});
    S.sel.clear();toast(t("deleted"));loadList();};
}
function cell(row,f){
  if(f.name==="_ai_score"){const v=row._ai||0;
    return `<div class="row"><div class="barbg" style="width:44px"><div class="barfill" style="width:${v}%"></div></div><b>${v}</b></div>`;}
  const v=row[f.name];
  if(f.type==="currency")return `<b>${fmtMoney(v)}</b>`;
  if(f.type==="user"||f.type==="lookup")return esc(row._display?.[f.name]||"—");
  if(f.type==="select")return badge(v);
  if(f.name==="probability")return `<div class="row"><div class="barbg" style="width:60px"><div class="barfill" style="width:${v||0}%"></div></div><span class="mut">${v||0}%</span></div>`;
  return esc(v ?? "—");
}
function renderKanban(m){
  const key=m.kanban;
  const stages=m.fields.find(f=>f.name===key).options;
  body.innerHTML=`<div class="kb" style="padding:14px">${stages.map(s=>{
    const items=S.data.filter(d=>d[key]===s);
    const sum=items.reduce((a,b)=>a+(+b.amount||0),0);
    return `<div class="kbcol" data-s="${esc(s)}"><h4>${badge(s)}<span class="mut">${items.length}${sum?" · "+fmtMoney(sum):""}</span></h4>
      ${items.map(i=>`<div class="kbcard" draggable="true" data-i="${i.id}">
        <div style="font-weight:600;font-size:13px">${esc(i[m.title]||"—")}</div>
        ${i.amount!=null?`<div style="color:var(--ok);font-weight:700;font-size:13px">${fmtMoney(i.amount)}</div>`:""}
        <div class="mut" style="font-size:11.5px;margin-top:4px">${esc(i._display?.account_id||i._display?.owner_id||"")}</div></div>`).join("")}
    </div>`;}).join("")}</div>`;
  let drag=null;
  body.querySelectorAll(".kbcard").forEach(c=>{
    c.ondragstart=()=>drag=+c.dataset.i;
    c.onclick=()=>openRecord(S.module,+c.dataset.i);});
  body.querySelectorAll(".kbcol").forEach(col=>{
    col.ondragover=e=>{e.preventDefault();col.classList.add("over");};
    col.ondragleave=()=>col.classList.remove("over");
    col.ondrop=async e=>{e.preventDefault();col.classList.remove("over");
      if(!drag||S.user.role==="readonly")return;
      const upd={};upd[key]=col.dataset.s;
      const r=await api(`/${S.module}/${drag}`,{method:"PUT",body:JSON.stringify(upd)});
      (r.workflows||[]).forEach(w=>toast("⚡ "+w));
      toast(t("saved"));drag=null;loadList();loadNotifBadge();};});
}

/* ---------- filters ---------- */
function filterDialog(){
  const m=S.meta.modules[S.module];
  const rows=()=>S.filters.map((f,i)=>`<div class="row" style="margin-bottom:8px" data-r="${i}">
    <select class="ff" style="flex:1;background:var(--bg2);border:1px solid var(--line);border-radius:8px;padding:7px">
      ${m.fields.map(x=>`<option value="${x.name}" ${f.field===x.name?"selected":""}>${L(x)}</option>`).join("")}</select>
    <select class="fo" style="background:var(--bg2);border:1px solid var(--line);border-radius:8px;padding:7px">
      ${[["eq","="],["ne","≠"],["contains","⊃"],["gt",">"],["lt","<"]].map(([v,l])=>`<option value="${v}" ${f.op===v?"selected":""}>${l}</option>`).join("")}</select>
    <input class="fv" value="${esc(f.value||"")}" style="flex:1;background:var(--bg2);border:1px solid var(--line);border-radius:8px;padding:7px">
    <button class="btn sm dgr fx">✕</button></div>`).join("");
  const el=modal(t("filters"),`<div id="frows">${rows()}</div><button class="btn sm" id="fadd">+ ${t("addFilter")}</button>`,
    [[t("clear"),()=>{S.filters=[];S.page=1;loadList();close_();},""],
     [t("apply"),()=>{collect();S.page=1;loadList();close_();},"pri"]]);
  function collect(){S.filters=[...el.querySelectorAll("#frows > div")].map(r=>({
    field:r.querySelector(".ff").value,op:r.querySelector(".fo").value,value:r.querySelector(".fv").value}))
    .filter(f=>f.value!=="");}
  function wire(){el.querySelectorAll(".fx").forEach((b,i)=>b.onclick=()=>{collect();S.filters.splice(i,1);
    el.querySelector("#frows").innerHTML=rows();wire();});}
  el.querySelector("#fadd").onclick=()=>{collect();S.filters.push({field:m.fields[0].name,op:"eq",value:""});
    el.querySelector("#frows").innerHTML=rows();wire();};
  wire();
}

/* ---------- modal helper ---------- */
let closeStack=[];
function modal(title,html,buttons=[]){
  const ov=document.createElement("div");ov.className="ov";
  ov.innerHTML=`<div class="modal"><header><b style="flex:1">${title}</b><button class="icbtn" data-x>✕</button></header>
    <div class="body">${html}</div>${buttons.length?`<footer>${buttons.map((b,i)=>`<button class="btn ${b[2]||""}" data-b="${i}">${b[0]}</button>`).join("")}</footer>`:""}</div>`;
  document.body.append(ov);
  ov.querySelector("[data-x]").onclick=close_;
  ov.onclick=e=>{if(e.target===ov)close_();};
  ov.querySelectorAll("[data-b]").forEach(b=>b.onclick=()=>buttons[+b.dataset.b][1]());
  closeStack.push(ov);
  return ov;
}
function close_(){const o=closeStack.pop();if(o)o.remove();}

/* ---------- record form ---------- */
async function openForm(mod,id){
  const m=S.meta.modules[mod];
  let rec={};
  if(id)rec=await api(`/${mod}/${id}`);
  const users=await api("/admin/users");
  const lookups={};
  for(const f of m.fields) if(f.type==="lookup")
    lookups[f.name]=(await api(`/${f.target}?per_page=200`)).data;
  const inp=f=>{
    const v=rec[f.name]??f.default??"";
    if(f.type==="select")return `<select name="${f.name}"><option value=""></option>${f.options.map(o=>`<option ${v===o?"selected":""}>${o}</option>`).join("")}</select>`;
    if(f.type==="user")return `<select name="${f.name}">${users.map(u=>`<option value="${u.id}" ${String(v)===String(u.id)?"selected":""}>${esc(u.name)}</option>`).join("")}</select>`;
    if(f.type==="lookup")return `<select name="${f.name}"><option value=""></option>${(lookups[f.name]||[]).map(o=>`<option value="${o.id}" ${String(v)===String(o.id)?"selected":""}>${esc(o[S.meta.modules[f.target].title]||o.id)}</option>`).join("")}</select>`;
    if(f.type==="textarea")return `<textarea name="${f.name}">${esc(v)}</textarea>`;
    const ty=f.type==="date"?"date":(f.type==="number"||f.type==="currency")?"number":f.type==="email"?"email":"text";
    return `<input type="${ty}" name="${f.name}" value="${esc(v)}" ${f.required?"required":""}>`;
  };
  const el=modal(`${id?t("edit"):t("new")} · ${L(m)}`,
    `<form id="rf" class="f2">${m.fields.map(f=>`<div class="fld" ${f.type==="textarea"?'style="grid-column:span 2"':""}>
      <label>${L(f)}${f.required?' <span style="color:var(--danger)">*</span>':""}</label>${inp(f)}</div>`).join("")}</form>`,
    [[t("cancel"),close_,""],[t("save"),save,"pri"]]);
  async function save(){
    const fd=new FormData(el.querySelector("#rf"));const body={};
    fd.forEach((v,k)=>body[k]=v);
    try{
      const r=id?await api(`/${mod}/${id}`,{method:"PUT",body:JSON.stringify(body)})
                :await api(`/${mod}`,{method:"POST",body:JSON.stringify(body)});
      (r.workflows||[]).forEach(w=>setTimeout(()=>toast("⚡ "+w),400));
      toast(t("saved"));close_();
      if(S.view==="module")loadList();loadNotifBadge();
    }catch{}
  }
}

/* ---------- record detail ---------- */
async function openRecord(mod,id){
  const m=S.meta.modules[mod];
  const r=await api(`/${mod}/${id}`);
  const tabs=[["details",t("details")],["notes",t("notes")],["history",t("history")]];
  if(m.line_items)tabs.splice(1,0,["items",t("items")]);
  if(mod==="tickets")tabs.splice(1,0,["thread",t("portalThread")]);
  if(mod==="invoices")tabs.splice(1,0,["pay",t("payments")]);
  if(mod==="competitors")tabs.splice(1,0,["bc",t("battlecard")]);
  if(["deals","leads","accounts"].includes(mod))tabs.splice(1,0,["ai","🤖 "+t("nba")]);
  tabs.splice(tabs.length-1,0,["mail",t("emails")]);
  const el=modal(`${m.icon} ${esc(r[m.title]||"#"+id)}`,
    `<div class="tabs" id="tb">${tabs.map((x,i)=>`<button data-t="${x[0]}" class="${i?"":"on"}">${x[1]}</button>`).join("")}</div>
     <div id="tc"></div>`,
    [...(mod==="leads"&&r.status!=="Converted"&&S.user.role!=="readonly"?[["🔄 "+t("convert"),conv,""]]:[]),
     ...(mod==="opportunities"&&!r.deal_id&&S.user.role!=="readonly"?[["🔄 "+t("convertOpp"),convOpp,""]]:[]),
     ...(["accounts","contacts","leads"].includes(mod)?[["🔎 "+t("view360"),()=>{close_();open360(mod,id);},""]]:[]),
     ...([["🖨 "+(["invoices","quotes"].includes(mod)?t("printDocument"):t("printRecord")),
       ()=>["invoices","quotes"].includes(mod)?printDocument(mod,id):printGenericRecord(mod,r),""]]),
     ...(S.user.role!=="readonly"?[[t("delete"),del,"dgr"],[t("edit"),()=>{close_();openForm(mod,id);},"pri"]]:[])]);
  const tc=el.querySelector("#tc");
  const paint=k=>{
    if(k==="details")tc.innerHTML=`${mod==="accounts"&&r.list_tag==="Blacklist"?
      `<div class="card" style="border:1px solid var(--danger);background:var(--danger)15;margin-bottom:12px">
       <b style="color:var(--danger)">⛔ ${t("blacklistWarn")}</b>
       <div class="mut" style="font-size:12.5px;margin-top:4px">${esc(r.blacklist_reason||"")}</div></div>`:""}<div class="f2">${m.fields.map(f=>`<div style="padding:9px 0;border-bottom:1px solid var(--line)">
      <div class="mut" style="font-size:11.5px">${L(f)}</div><div>${cell(r,f)}</div></div>`).join("")}</div>`;
    else if(k==="notes")tc.innerHTML=`<div class="fld"><textarea id="nb" placeholder="${t("addNote")}"></textarea></div>
      <button class="btn pri sm" id="np">${t("post")}</button><div style="height:12px"></div>
      ${(r._notes||[]).map(n=>`<div class="card" style="margin-bottom:8px;padding:10px"><div class="row">
        <b style="font-size:12.5px">${esc(n.uname||"—")}</b><div class="spacer"></div>
        <span class="mut" style="font-size:11px">${n.created_at.replace("T"," ")}</span></div>
        <div style="margin-top:4px">${esc(n.body)}</div></div>`).join("")||`<div class="empty">${t("noData")}</div>`}`;
    else if(k==="history")tc.innerHTML=(r._audit||[]).map(a=>`<div style="padding:8px 0;border-bottom:1px solid var(--line);font-size:12.5px">
      <b>${esc(a.uname||"—")}</b> <span class="badge" style="color:var(--info);background:var(--info)22">${a.action}</span>
      <span class="mut">${a.created_at.replace("T"," ")}</span>
      <div class="mut" style="font-size:11.5px;margin-top:3px">${esc((a.changes||"").slice(0,220))}</div></div>`).join("")||`<div class="empty">${t("noData")}</div>`;
    else if(k==="items")paintItems();
    else if(k==="thread")paintThread();
    else if(k==="pay")paintPay();
    else if(k==="bc"){close_();openBattlecard(id);return;}
    else if(k==="ai")paintAI();
    else if(k==="mail")paintMail();
    if(k==="notes")tc.querySelector("#np").onclick=async()=>{
      const b=tc.querySelector("#nb").value.trim();if(!b)return;
      await api(`/notes/${mod}/${id}`,{method:"POST",body:JSON.stringify({body:b})});
      close_();openRecord(mod,id);};
  };
  async function paintAI(){
    tc.innerHTML='<div class="mut">…</div>';
    try{
      const a=await api(`/ai/next-best-action/${mod}/${id}`);
      const pr=a.prediction, sc=a.score;
      tc.innerHTML=`
        ${pr?`<div class="card" style="margin-bottom:10px"><div class="row">
          <div style="flex:1"><div class="mut" style="font-size:11.5px">${t("winProb")}</div>
            <b style="font-size:26px;color:${pr.probability>=65?"var(--ok)":pr.probability>=35?"var(--warn)":"var(--danger)"}">${pr.probability}%</b></div>
          <div style="flex:1"><div class="mut" style="font-size:11.5px">${t("expected")}</div>
            <b style="font-size:20px">${fmtMoney(pr.expected_value)}</b></div></div>
          <div class="barbg" style="margin-top:8px"><div class="barfill" style="width:${pr.probability}%"></div></div>
          <div style="margin-top:10px"><b style="font-size:12px">${t("factors")}</b>
          ${pr.factors.map(f=>`<div class="row" style="padding:4px 0;font-size:12px">
            <span style="flex:1">${esc(S.lang==="ar"?f.ar:f.en)} <span class="mut">${esc(f.detail||"")}</span></span>
            <b style="color:${f.points<0?"var(--danger)":"var(--ok)"}">${f.points>0?"+":""}${f.points}</b></div>`).join("")}</div></div>`:""}
        ${sc?`<div class="card" style="margin-bottom:10px"><div class="row">
          <div style="flex:1"><div class="mut" style="font-size:11.5px">${t("readiness")}</div>
            <b style="font-size:26px">${sc.score}</b>
            <span class="badge" style="color:var(--pri);background:var(--pri)22">${sc.band_ar}</span></div></div>
          <div class="barbg" style="margin-top:8px"><div class="barfill" style="width:${sc.score}%"></div></div>
          <div style="margin-top:10px">${sc.factors.map(f=>`<div class="row" style="padding:4px 0;font-size:12px">
            <span style="flex:1">${esc(S.lang==="ar"?f.ar:f.en)} <span class="mut">${esc(f.detail||"")}</span></span>
            <b style="color:${f.points<0?"var(--danger)":"var(--ok)"}">${f.points>0?"+":""}${f.points}</b></div>`).join("")}</div></div>`:""}
        <div class="card"><b style="font-size:12.5px">🤖 ${t("nba")}</b>
          ${a.actions.map(x=>`<div style="padding:8px 0;border-bottom:1px solid var(--line)">
            <div class="row"><span class="badge" style="color:${x.priority===1?"var(--danger)":x.priority===2?"var(--warn)":"var(--mut)"};
              background:${x.priority===1?"var(--danger)":x.priority===2?"var(--warn)":"var(--mut)"}22">P${x.priority}</span>
              <b style="flex:1;font-size:12.5px">${esc(S.lang==="ar"?x.ar:x.en)}</b></div>
            <div class="mut" style="font-size:11px">${esc(x.why_ar||"")}</div></div>`).join("")
            ||`<div class="mut" style="font-size:12.5px">${t("noData")}</div>`}</div>
        ${S.user.role!=="readonly"?`<button class="btn pri sm" id="aig" style="margin-top:10px">✍️ ${t("genEmail")}</button>`:""}`;
      const g=tc.querySelector("#aig");
      if(g)g.onclick=async()=>{
        const kind=mod==="leads"?"intro":"followup";
        const r2=await api("/ai/generate-email",{method:"POST",
          body:JSON.stringify({kind,module:mod,record_id:id})});
        composeMail({to_email:r.email||"",to_name:r[m.title]||"",subject:r2.subject,
                     body:r2.body,module:mod,record_id:id});};
    }catch(e){tc.innerHTML=`<div class="empty">${t("noData")}</div>`;}
  }
  async function paintMail(){
    const ms=await api(`/email/thread/${mod}/${id}`);
    const em=r.email||r._display?.email||"";
    tc.innerHTML=`${S.user.role!=="readonly"?`<button class="btn pri sm" id="cm">✉ ${t("compose")}</button><div style="height:12px"></div>`:""}
      ${ms.map(m=>`<div class="card" style="margin-bottom:8px;padding:11px"><div class="row">
        <b style="font-size:12.5px;flex:1">${esc(m.subject)}</b>
        <span class="badge" style="color:var(--info);background:var(--info)22">${m.status}</span></div>
        <div class="mut" style="font-size:11.5px">${esc(m.to_email)} · ${(m.created_at||"").replace("T"," ")}</div>
        <div style="font-size:12.5px;white-space:pre-wrap;margin-top:6px;max-height:80px;overflow:hidden">${esc(m.body)}</div></div>`).join("")
        ||`<div class="empty">${t("noData")}</div>`}`;
    const cm=tc.querySelector("#cm");
    if(cm)cm.onclick=()=>composeMail({to_email:em,to_name:r[m.title]||"",module:mod,record_id:id});
  }
  async function paintPay(){
    const ps=await api(`/payments?invoice_id=${id}`);
    const bal=(r.amount||0)-(r.paid_amount||0);
    const pcl=x=>({paid:"var(--ok)",pending:"var(--warn)",failed:"var(--danger)",refunded:"var(--purple)"}[x]||"var(--mut)");
    tc.innerHTML=`<div class="row" style="margin-bottom:12px"><div><div class="mut" style="font-size:11.5px">${t("remaining")||"Balance"}</div>
      <b style="font-size:20px;color:${bal>0?"var(--danger)":"var(--ok)"}">${fmtMoney(bal)}</b></div>
      <div class="spacer"></div>${bal>0.01&&S.user.role!=="readonly"?`<button class="btn sm" id="pm">＋ ${t("manualPay")}</button>
      <button class="btn pri sm" id="pk">🔗 ${t("payLink")}</button>`:""}</div>
      ${ps.map(p=>`<div class="card" style="margin-bottom:8px;padding:11px"><div class="row">
        <b style="flex:1">${fmtMoney(p.amount)}</b>
        <span class="badge" style="color:${pcl(p.status)};background:${pcl(p.status)}22">${p.status}</span></div>
        <div class="mut" style="font-size:11.5px">${esc(p.method||"")} · ${esc(p.provider_ref||"—")} · ${(p.paid_at||p.created_at||"").replace("T"," ")}</div>
        ${p.status==="pending"?`<button class="btn sm" style="margin-top:7px" data-l="${p.token}">🔗 ${t("copy")}</button>`:""}</div>`).join("")
        ||`<div class="empty">${t("noData")}</div>`}`;
    tc.querySelectorAll("[data-l]").forEach(b=>b.onclick=()=>copyTxt(location.origin+"/pay/"+b.dataset.l));
    const pk=tc.querySelector("#pk");
    if(pk){pk.onclick=async()=>{const res=await api("/payments/link",{method:"POST",
        body:JSON.stringify({invoice_id:id,amount:null,send_email:false})});
      copyTxt(location.origin+res.url);paintPay();};
      tc.querySelector("#pm").onclick=async()=>{
        const a=prompt(t("manualPay"),String(bal)); if(!a)return;
        try{await api("/payments/manual",{method:"POST",body:JSON.stringify({invoice_id:id,amount:+a,method:"Bank Transfer"})});
          toast(t("saved"));close_();openRecord(mod,id);}catch{}};}
  }
  async function paintThread(){
    const ms=await api(`/tickets/${id}/portal-thread`);
    tc.innerHTML=`<div style="max-height:300px;overflow:auto;margin-bottom:12px">
      ${ms.map(m=>`<div style="padding:10px 12px;border-radius:12px;margin-bottom:8px;max-width:78%;
        ${m.author==="staff"?"margin-inline-start:auto;background:var(--pri)22;border:1px solid var(--pri)55":"background:var(--bg2);border:1px solid var(--line)"}">
        <div class="row" style="gap:6px"><b style="font-size:11.5px">${esc(m.author_name||m.author)}</b>
        <span class="mut" style="font-size:10.5px">${(m.created_at||"").replace("T"," ")}</span></div>
        <div style="font-size:13px;white-space:pre-wrap;margin-top:3px">${esc(m.body)}</div></div>`).join("")
        ||`<div class="empty">${t("noData")}</div>`}</div>
      ${S.user.role!=="readonly"?`<div class="fld"><textarea id="sm" placeholder="${t("replyCustomer")}"></textarea></div>
      <button class="btn pri sm" id="ss">${t("post")}</button>`:""}`;
    const ss=tc.querySelector("#ss");
    if(ss)ss.onclick=async()=>{const b=tc.querySelector("#sm").value.trim();if(!b)return;
      await api(`/tickets/${id}/portal-thread`,{method:"POST",body:JSON.stringify({body:b})});
      toast(t("saved"));paintThread();if(S.view==="module")loadList();};
  }
  async function paintItems(){
    const prods=(await api("/products?per_page=200")).data;
    let items=(r._items||[]).map(x=>({...x}));
    const draw=()=>{
      const tot=items.reduce((a,i)=>a+i.qty*i.price*(1-i.discount/100)*(1+i.tax/100),0);
      tc.innerHTML=`<table class="tbl"><thead><tr><th>${t("product")}</th><th>${t("qty")}</th><th>${t("price")}</th>
        <th>${t("disc")}</th><th>${t("tax")}</th><th>${t("lineTotal")}</th><th></th></tr></thead><tbody>
        ${items.map((it,i)=>`<tr><td><select data-i="${i}" data-f="product_id" style="background:var(--bg2);border:1px solid var(--line);border-radius:7px;padding:5px">
          ${prods.map(p=>`<option value="${p.id}" ${String(it.product_id)===String(p.id)?"selected":""}>${esc(p.name)}</option>`).join("")}</select></td>
          ${["qty","price","discount","tax"].map(f=>`<td><input type="number" data-i="${i}" data-f="${f}" value="${it[f]}" style="width:74px;background:var(--bg2);border:1px solid var(--line);border-radius:7px;padding:5px"></td>`).join("")}
          <td><b>${fmtMoney(it.qty*it.price*(1-it.discount/100)*(1+it.tax/100))}</b></td>
          <td><button class="btn sm dgr" data-d="${i}">✕</button></td></tr>`).join("")}
        </tbody></table>
        <div class="row" style="margin-top:12px"><button class="btn sm" id="ai">+ ${t("addItem")}</button>
        <div class="spacer"></div><b style="font-size:17px">${t("total")}: ${fmtMoney(tot)}</b>
        <button class="btn pri sm" id="si">${t("saveItems")}</button></div>`;
      tc.querySelectorAll("[data-f]").forEach(inp=>inp.onchange=()=>{
        const i=+inp.dataset.i,f=inp.dataset.f;
        items[i][f]=f==="product_id"?inp.value:+inp.value;
        if(f==="product_id"){const p=prods.find(p=>String(p.id)===inp.value);
          if(p){items[i].price=p.unit_price;items[i].name=p.name;items[i].tax=p.tax_rate||0;}}
        draw();});
      tc.querySelectorAll("[data-d]").forEach(b=>b.onclick=()=>{items.splice(+b.dataset.d,1);draw();});
      tc.querySelector("#ai").onclick=()=>{const p=prods[0]||{};
        items.push({product_id:p.id,name:p.name||"",qty:1,price:p.unit_price||0,discount:0,tax:p.tax_rate||0});draw();};
      tc.querySelector("#si").onclick=async()=>{
        const res=await api(`/items/${mod}/${id}`,{method:"POST",body:JSON.stringify({items})});
        toast(t("saved")+" · "+fmtMoney(res.total));close_();if(S.view==="module")loadList();};
    };draw();
  }
  async function convOpp(){
    try{const res=await api(`/opportunities/${id}/convert`,{method:"POST"});
      toast(t("converted"));close_();loadList();}catch{}}
  async function conv(){const res=await api(`/leads/${id}/convert`,{method:"POST"});
    toast(t("converted"));close_();loadList();}
  async function del(){if(!confirm(t("confirmDel")))return;
    await api(`/${mod}/${id}`,{method:"DELETE"});toast(t("deleted"));close_();loadList();}
  el.querySelectorAll("#tb button").forEach(b=>b.onclick=()=>{
    el.querySelectorAll("#tb button").forEach(x=>x.classList.remove("on"));b.classList.add("on");paint(b.dataset.t);});
  paint("details");
}

/* ---------- printable invoices and quotations ---------- */
function printDocument(module,recordId){
  const kind=module==="invoices"?"invoice":"quote";
  const title=S.lang==="ar"?(kind==="invoice"?"فاتورة":"عرض سعر"):(kind==="invoice"?"Invoice":"Quotation");
  const win=window.open("","_blank");
  if(!win){toast(S.lang==="ar"?"تعذّر فتح نافذة الطباعة. اسمح بالنوافذ المنبثقة ثم أعد المحاولة.":"Print window was blocked. Allow pop-ups and try again.");return;}
  win.document.write(`<title>${title}</title><body style="font-family:system-ui;padding:32px">Loading document…</body>`);
  const money=(value,currency)=>{
    try{return new Intl.NumberFormat(S.lang==="ar"?"ar-EG":"en-US",{style:"currency",currency:currency||"USD",maximumFractionDigits:2}).format(value||0);}
    catch{return `${Number(value||0).toFixed(2)} ${currency||""}`;}
  };
  const date=value=>{
    if(!value)return "—";
    const raw=String(value).slice(0,10);
    try{return new Intl.DateTimeFormat(S.lang==="ar"?"ar-EG":"en-US",{dateStyle:"medium"}).format(new Date(raw+"T12:00:00"));}
    catch{return raw;}
  };
  const label=S.lang==="ar"?{
    bill:"بيانات العميل",contact:"جهة الاتصال",phone:"الهاتف",email:"البريد الإلكتروني",address:"العنوان",
    issue:"تاريخ الإصدار",due:kind==="invoice"?"تاريخ الاستحقاق":"صالح حتى",status:"الحالة",owner:"المسؤول",
    item:"الصنف",code:"الرمز",qty:"الكمية",unit:"سعر الوحدة",discount:"الخصم",tax:"الضريبة",line:"الإجمالي",
    subtotal:"الإجمالي قبل الخصم",discountTotal:"إجمالي الخصم",taxTotal:"إجمالي الضريبة",total:"الإجمالي النهائي",
    paid:"المدفوع",balance:"المتبقي",terms:kind==="invoice"?"ملاحظات":"الشروط والأحكام",thank:"شكرًا لتعاملكم معنا",
  }:{
    bill:"Bill to",contact:"Contact",phone:"Phone",email:"Email",address:"Address",
    issue:"Issued",due:kind==="invoice"?"Due date":"Valid until",status:"Status",owner:"Owner",
    item:"Item",code:"Code",qty:"Qty",unit:"Unit price",discount:"Discount",tax:"Tax",line:"Line total",
    subtotal:"Subtotal",discountTotal:"Discount",taxTotal:"Tax",total:"Grand total",
    paid:"Paid",balance:"Balance due",terms:kind==="invoice"?"Notes":"Terms",thank:"Thank you for your business",
  };
  const palette=kind==="invoice"
    ? {accent:"#3156c7",accent2:"#1e8acb",soft:"#eef3ff"}
    : {accent:"#7c3aed",accent2:"#c14fe4",soft:"#f6efff"};
  api(`/documents/${kind}/${recordId}`).then(data=>{
    const doc=data.document, company=data.company, account=data.account, contact=data.contact, totals=data.totals;
    const contactLine=[contact.name,contact.title].filter(Boolean).map(esc).join(" · ");
    const contactMeta=[contact.phone,contact.email].filter(Boolean).map(esc).join(" · ");
    const companyMeta=[company.address,company.phone,company.tax_number?`${S.lang==="ar"?"رقم ضريبي":"Tax no."}: ${company.tax_number}`:""].filter(Boolean).map(esc).join("<br>");
    const lineRows=data.items.map((item,index)=>`<tr>
      <td class="item"><b>${esc(item.name||"—")}</b>${item.product_code?`<small>${label.code}: ${esc(item.product_code)}</small>`:""}</td>
      <td>${Number(item.qty||0).toLocaleString(S.lang==="ar"?"ar-EG":"en-US",{maximumFractionDigits:2})}</td>
      <td>${money(item.price,company.currency)}</td>
      <td>${item.discount?`${Number(item.discount).toFixed(2)}%<small>−${money(item.discount_amount,company.currency)}</small>`:"—"}</td>
      <td>${item.tax?`${Number(item.tax).toFixed(2)}%<small>+${money(item.tax_amount,company.currency)}</small>`:"—"}</td>
      <td class="line-total">${money(item.line_total,company.currency)}</td>
    </tr>`).join("")||`<tr><td colspan="6" class="empty">${S.lang==="ar"?"لا توجد أصناف مسجلة":"No line items were recorded"}</td></tr>`;
    const settlement=kind==="invoice"?`<div class="settlement"><div><span>${label.paid}</span><b>${money(doc.paid,company.currency)}</b></div><div><span>${label.balance}</span><b>${money(doc.remaining,company.currency)}</b></div></div>`:"";
    const terms=doc.terms?`<section class="terms"><h3>${label.terms}</h3><p>${esc(doc.terms).replace(/\n/g,"<br>")}</p></section>`:"";
    const html=`<!doctype html><html lang="${S.lang}" dir="${S.lang==="ar"?"rtl":"ltr"}"><head><meta charset="utf-8">
      <meta name="viewport" content="width=device-width,initial-scale=1"><title>${esc(data.reference)}</title>
      <style>
        :root{--accent:${palette.accent};--accent2:${palette.accent2};--soft:${palette.soft}}@page{size:A4;margin:12mm}.doc{max-width:186mm;margin:auto;color:#172033;font:13px/1.6 "Segoe UI",Tahoma,Arial,sans-serif}.top{display:flex;justify-content:space-between;gap:18px;padding:0 0 18px;border-bottom:3px solid var(--accent)}.brand{display:flex;gap:12px;align-items:flex-start}.mark{width:48px;height:48px;border-radius:14px;display:grid;place-items:center;background:linear-gradient(135deg,var(--accent),var(--accent2));color:#fff;font-size:24px;font-weight:800;box-shadow:0 8px 20px color-mix(in srgb,var(--accent) 22%,transparent)}.company h1{font-size:22px;margin:0 0 3px}.company .meta{font-size:11px;color:#667085}.doc-title{text-align:end}.doc-title .kind{display:inline-block;padding:4px 12px;border-radius:999px;background:var(--soft);color:var(--accent);font-size:11px;font-weight:700}.doc-title h2{margin:8px 0 0;font-size:20px}.doc-title p{margin:2px 0;color:#667085;font-size:11px}.info{display:grid;grid-template-columns:1.35fr 1fr;gap:14px;margin:20px 0}.box{border:1px solid #dbe2ee;border-radius:12px;padding:13px 15px;background:#fbfcff}.box h3{margin:0 0 8px;font-size:11px;letter-spacing:.3px;text-transform:uppercase;color:#5f6e85}.box strong{font-size:15px}.box p{margin:3px 0;color:#526078;font-size:11.5px}.meta-grid{display:grid;grid-template-columns:1fr 1fr;gap:8px 14px}.meta-grid div span{display:block;font-size:10px;color:#7a8799}.meta-grid div b{font-size:12px}.status{color:var(--accent)}.items{width:100%;border-collapse:collapse;margin-top:18px}.items thead{display:table-header-group}.items th{background:var(--accent);color:#fff;padding:9px 8px;font-size:10.5px;text-align:center}.items th:first-child{text-align:start;border-radius:7px 0 0 7px}.items th:last-child{border-radius:0 7px 7px 0}.items td{padding:10px 8px;border-bottom:1px solid #e4e9f1;text-align:center;vertical-align:top;font-size:11px}.items tr:nth-child(even){background:#fafbfe}.items td.item{text-align:start;min-width:42%}.items small{display:block;color:#758196;font-size:9.5px}.line-total{font-weight:700;color:#172f83}.empty{text-align:center;color:#7a8799;padding:18px!important}.bottom{display:grid;grid-template-columns:1fr 72mm;gap:18px;align-items:start;margin-top:18px}.terms{border-inline-start:3px solid #b6c4ff;padding-inline-start:11px;color:#4b5a70}.terms h3{font-size:11px;margin:0 0 5px}.terms p{font-size:11px;margin:0;white-space:normal}.totals{border:1px solid #dbe2ee;border-radius:12px;padding:10px 14px;background:#fbfcff}.totals .row{display:flex;justify-content:space-between;padding:5px 0;font-size:11.5px;color:#526078}.totals .grand{margin-top:5px;padding-top:10px;border-top:1px solid #cdd7e7;color:#172033;font-size:15px;font-weight:800}.settlement{display:grid;grid-template-columns:1fr 1fr;gap:8px;margin-top:10px}.settlement div{padding:8px 10px;border-radius:8px;background:#f1f5ff}.settlement span{display:block;color:#63728a;font-size:10px}.settlement b{font-size:12px}.footer{display:flex;justify-content:space-between;align-items:center;margin-top:26px;padding-top:10px;border-top:1px solid #e4e9f1;color:#7a8799;font-size:10px}.footer .thank{color:var(--accent);font-weight:700}@media print{body{margin:0}.doc{max-width:none}.top{break-inside:avoid}.items tr{break-inside:avoid}.box{background:#fbfcff!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}.items th{background:var(--accent)!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}.items tr:nth-child(even){background:#fafbfe!important;-webkit-print-color-adjust:exact;print-color-adjust:exact}}
      </style></head><body><main class="doc"><header class="top"><div class="brand"><div class="mark">${S.lang==="ar"?"ن":"N"}</div><div class="company"><h1>${esc(company.name)}</h1><div class="meta">${companyMeta||"—"}</div></div></div><div class="doc-title"><span class="kind">${esc(S.lang==="ar"?data.label_ar:data.label_en)}</span><h2>${esc(data.reference)}</h2><p>${esc(doc.status||"")}</p></div></header><section class="info"><div class="box"><h3>${label.bill}</h3><strong>${esc(account.name||"—")}</strong>${contactLine?`<p>${contactLine}</p>`:""}${contactMeta?`<p>${contactMeta}</p>`:""}${account.address?`<p>${esc(account.address).replace(/\n/g,"<br>")}</p>`:""}${account.website?`<p>${esc(account.website)}</p>`:""}</div><div class="box meta-grid"><div><span>${label.issue}</span><b>${date(doc.issued_on)}</b></div><div><span>${label.due}</span><b>${date(doc.due_on)}</b></div><div><span>${label.status}</span><b class="status">${esc(doc.status||"—")}</b></div><div><span>${label.owner}</span><b>${esc(data.owner.name||"—")}</b></div></div></section><table class="items"><thead><tr><th>${label.item}</th><th>${label.qty}</th><th>${label.unit}</th><th>${label.discount}</th><th>${label.tax}</th><th>${label.line}</th></tr></thead><tbody>${lineRows}</tbody></table><section class="bottom"><div>${terms}</div><div><div class="totals"><div class="row"><span>${label.subtotal}</span><b>${money(totals.subtotal,company.currency)}</b></div><div class="row"><span>${label.discountTotal}</span><b>− ${money(totals.discount_total,company.currency)}</b></div><div class="row"><span>${label.taxTotal}</span><b>+ ${money(totals.tax_total,company.currency)}</b></div><div class="row grand"><span>${label.total}</span><b>${money(totals.total,company.currency)}</b></div></div>${settlement}</div></section><footer class="footer"><span>${date(data.generated_at)}</span><span class="thank">${label.thank}</span></footer></main></body></html>`;
    win.document.open();win.document.write(html);win.document.close();
    win.onload=()=>setTimeout(()=>{win.focus();win.print();},180);
  }).catch(()=>{win.close();});
}

/* ---------- reports ---------- */
function viewReports(){
  const mods=Object.entries(S.meta.modules);
  main.innerHTML=`<div class="h1" style="margin-bottom:14px">📈 ${t("reportBuilder")}</div>
   <div class="card"><div class="row" style="flex-wrap:wrap;gap:12px">
    <div class="fld" style="margin:0"><label>${t("module")}</label><select id="rm">${mods.map(([k,m])=>`<option value="${k}">${m.icon} ${L(m)}</option>`).join("")}</select></div>
    <div class="fld" style="margin:0"><label>${t("groupBy")}</label><select id="rg"></select></div>
    <div class="fld" style="margin:0"><label>${t("metric")}</label><select id="rmt">
      <option value="count">${t("count")}</option><option value="sum">${t("sum")}</option><option value="avg">${t("avg")}</option></select></div>
    <div class="fld" style="margin:0"><label>${t("field")}</label><select id="rf"></select></div>
    <button class="btn pri" id="rr" style="align-self:end">${t("run")}</button></div></div>
   <div style="height:14px"></div><div id="rout"></div>`;
  const fill=()=>{const m=S.meta.modules[rm.value];
    rg.innerHTML=m.fields.filter(f=>["select","text","user","lookup","date"].includes(f.type)).map(f=>`<option value="${f.name}">${L(f)}</option>`).join("");
    rf.innerHTML=m.fields.filter(f=>["number","currency"].includes(f.type)).map(f=>`<option value="${f.name}">${L(f)}</option>`).join("")||"<option value=''>—</option>";};
  rm.onchange=fill;fill();
  rr.onclick=async()=>{
    const d=await api(`/analytics/report?module=${rm.value}&group_by=${rg.value}&metric=${rmt.value}&field=${rf.value}`);
    const mx=Math.max(...d.rows.map(r=>+r.v||0),1);
    const money=rmt.value!=="count";
    rout.innerHTML=`<div class="card"><b>${S.meta.modules[rm.value].icon} ${L(S.meta.modules[rm.value])} — ${rg.selectedOptions[0].text}</b>
      <div style="height:12px"></div><div class="bars">${d.rows.map(r=>`<div class="bar">
      <div style="overflow:hidden;text-overflow:ellipsis">${esc(r.k)}</div><div class="barbg"><div class="barfill" style="width:${r.v/mx*100}%"></div></div>
      <div style="text-align:end;font-weight:700">${money?fmtMoney(r.v):fmtNum(r.v)}</div></div>`).join("")}</div>
      <div style="margin-top:14px;padding-top:12px;border-top:1px solid var(--line)" class="row">
      <b>${t("total")}</b><div class="spacer"></div><b>${money?fmtMoney(d.rows.reduce((a,b)=>a+ +b.v,0)):fmtNum(d.rows.reduce((a,b)=>a+ +b.v,0))}</b></div></div>`;};
  rr.click();
}

/* ---------- users ---------- */
async function viewUsers(){
  const us=await api("/admin/users");
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">👥 ${t("users")}</div><div class="spacer"></div>
    ${S.user.role==="admin"?`<button class="btn pri sm" id="au">+ ${t("addUser")}</button>`:""}</div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${t("email")}</th><th>${t("role")}</th><th>${t("target")}</th><th>${t("active")}</th><th></th></tr></thead><tbody>
      ${us.map(u=>`<tr><td><b>${esc(u.name)}</b></td><td class="mut">${esc(u.email)}</td>
        <td>${badge(L(S.meta.roles[u.role]||{en:u.role}))}</td><td>${fmtMoney(u.target)}</td>
        <td>${u.active?'<span class="dot" style="background:var(--ok)"></span>':'<span class="dot" style="background:var(--danger)"></span>'}</td>
        <td>${S.user.role==="admin"?`<button class="btn sm" data-u="${u.id}">✎</button>`:""}</td></tr>`).join("")}
      </tbody></table></div></div>`;
  if(document.getElementById("au"))au.onclick=()=>userForm(null);
  main.querySelectorAll("[data-u]").forEach(b=>b.onclick=()=>userForm(us.find(x=>x.id==b.dataset.u)));
}
function userForm(u){
  const el=modal(u?t("edit"):t("addUser"),`<form id="uf">
    <div class="fld"><label>${t("name")}</label><input name="name" value="${esc(u?.name||"")}" required></div>
    ${u?"":`<div class="fld"><label>${t("email")}</label><input name="email" type="email" required></div>`}
    <div class="fld"><label>${t("password")}</label><input name="password" type="password" placeholder="${u?"••••":""}"></div>
    <div class="fld"><label>${t("role")}</label><select name="role">${Object.entries(S.meta.roles).map(([k,v])=>`<option value="${k}" ${u?.role===k?"selected":""}>${L(v)}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("target")}</label><input name="target" type="number" value="${u?.target||0}"></div>
    <div class="fld"><label>${t("active")}</label><select name="active"><option value="1" ${u?.active!==0?"selected":""}>✔</option><option value="0" ${u?.active===0?"selected":""}>✕</option></select></div>
  </form>`,[[t("cancel"),close_,""],[t("save"),async()=>{
    const fd=new FormData(el.querySelector("#uf"));const b={};fd.forEach((v,k)=>b[k]=v);
    b.active=+b.active;b.target=+b.target;if(!b.password)delete b.password;
    try{u?await api(`/admin/users/${u.id}`,{method:"PUT",body:JSON.stringify(b)})
        :await api("/admin/users",{method:"POST",body:JSON.stringify(b)});
      toast(t("saved"));close_();viewUsers();}catch{}},"pri"]]);
}

/* ---------- workflows ---------- */
async function viewWorkflows(){
  const ws=await api("/admin/workflows");
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">⚡ ${t("workflows")}</div><div class="spacer"></div>
    <button class="btn pri sm" id="aw">+ ${t("addWf")}</button></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${t("module")}</th><th>${t("field")}</th><th>${t("operator")}</th><th>${t("value")}</th>
      <th>${t("action")}</th><th>${t("runs")}</th><th></th></tr></thead><tbody>
      ${ws.map(w=>`<tr><td><b>${esc(w.name)}</b></td><td>${S.meta.modules[w.module]?L(S.meta.modules[w.module]):w.module}</td>
        <td class="mut">${esc(w.field)}</td><td>${esc(w.operator)}</td><td>${esc(w.value)}</td>
        <td>${badge(w.action)}<div class="mut" style="font-size:11px">${esc(w.action_value||"")}</div></td>
        <td><b>${w.runs}</b></td><td><button class="btn sm dgr" data-w="${w.id}">✕</button></td></tr>`).join("")
        ||`<tr><td colspan="8"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  aw.onclick=wfForm;
  main.querySelectorAll("[data-w]").forEach(b=>b.onclick=async()=>{
    await api(`/admin/workflows/${b.dataset.w}`,{method:"DELETE"});toast(t("deleted"));viewWorkflows();});
}
function wfForm(){
  const el=modal(t("addWf"),`<form id="wf" class="f2">
    <div class="fld" style="grid-column:span 2"><label>${t("name")}</label><input name="name" required></div>
    <div class="fld"><label>${t("module")}</label><select name="module" id="wm">${Object.entries(S.meta.modules).map(([k,m])=>`<option value="${k}">${L(m)}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("field")}</label><select name="field" id="wfd"></select></div>
    <div class="fld"><label>${t("operator")}</label><select name="operator">
      <option value="eq">=</option><option value="ne">≠</option><option value="contains">⊃</option><option value="gt">&gt;</option><option value="lt">&lt;</option></select></div>
    <div class="fld"><label>${t("value")}</label><input name="value"></div>
    <div class="fld"><label>${t("action")}</label><select name="action">
      <option value="notify">notify</option><option value="create_task">create_task</option><option value="send_email">send_email</option><option value="set_field">set_field</option></select></div>
    <div class="fld"><label>${t("value")} (action)</label><input name="action_value" placeholder="field:value"></div>
  </form>`,[[t("cancel"),close_,""],[t("save"),async()=>{
    const fd=new FormData(el.querySelector("#wf"));const b={};fd.forEach((v,k)=>b[k]=v);
    await api("/admin/workflows",{method:"POST",body:JSON.stringify(b)});toast(t("saved"));close_();viewWorkflows();},"pri"]]);
  const wm=el.querySelector("#wm"),wfd=el.querySelector("#wfd");
  const fill=()=>wfd.innerHTML=S.meta.modules[wm.value].fields.map(f=>`<option value="${f.name}">${L(f)}</option>`).join("");
  wm.onchange=fill;fill();
}

/* ---------- portal access admin ---------- */
async function viewPortal(){
  const rows=await api("/portal-access");
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🌐 ${t("portal")}</div><div class="spacer"></div>
    <a class="btn sm" href="/portal" target="_blank">↗ ${t("openPortal")}</a>
    <button class="btn pri sm" id="ga">+ ${t("grantAccess")}</button></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("contact")}</th><th>${t("email")}</th><th>${S.lang==="ar"?"الشركة":"Account"}</th>
      <th>${t("lastLogin")}</th><th>${t("active")}</th><th></th></tr></thead><tbody>
      ${rows.map(r=>`<tr><td><b>${esc(r.cname||"—")}</b></td><td class="mut">${esc(r.email)}</td>
        <td>${esc(r.aname||"—")}</td><td class="mut">${(r.last_login||"—").replace("T"," ")}</td>
        <td>${r.active?'<span class="dot" style="background:var(--ok)"></span>':'<span class="dot" style="background:var(--danger)"></span>'}</td>
        <td><button class="btn sm" data-tg="${r.id}" data-a="${r.active}">${r.active?"⏸":"▶"}</button>
            <button class="btn sm" data-rp="${r.id}">🔑</button>
            ${S.user.role==="admin"?`<button class="btn sm dgr" data-rv="${r.id}">✕</button>`:""}</td></tr>`).join("")
        ||`<tr><td colspan="6"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  ga.onclick=grantForm;
  main.querySelectorAll("[data-tg]").forEach(b=>b.onclick=async()=>{
    await api(`/portal-access/${b.dataset.tg}`,{method:"PUT",body:JSON.stringify({active:b.dataset.a=="1"?0:1})});
    toast(t("saved"));viewPortal();});
  main.querySelectorAll("[data-rp]").forEach(b=>b.onclick=async()=>{
    const pw=prompt(t("resetPw"),"portal123"); if(!pw)return;
    await api(`/portal-access/${b.dataset.rp}`,{method:"PUT",body:JSON.stringify({password:pw})});
    toast(t("saved")+" · "+pw);});
  main.querySelectorAll("[data-rv]").forEach(b=>b.onclick=async()=>{
    if(!confirm(t("confirmDel")))return;
    await api(`/portal-access/${b.dataset.rv}`,{method:"DELETE"});toast(t("deleted"));viewPortal();});
}
async function grantForm(){
  const cs=(await api("/contacts?per_page=200")).data;
  const el=modal(t("grantAccess"),`<form id="gf">
    <div class="fld"><label>${t("contact")}</label><select name="contact_id" id="gc">
      ${cs.map(c=>`<option value="${c.id}" data-e="${esc(c.email||"")}">${esc(c.name)} — ${esc(c._display?.account_id||"")}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("email")}</label><input name="email" id="ge"></div>
    <div class="fld"><label>${t("password")}</label><input name="password" value="portal123"></div></form>`,
    [[t("cancel"),close_,""],[t("save"),async()=>{
      const fd=new FormData(el.querySelector("#gf"));const b={};fd.forEach((v,k)=>b[k]=v);
      try{const r=await api("/portal-access",{method:"POST",body:JSON.stringify(b)});
        close_();alert(`${t("credsMsg")}:\n${r.email}\n${r.password}`);viewPortal();}catch{}},"pri"]]);
  const gc=el.querySelector("#gc"),ge=el.querySelector("#ge");
  const sync=()=>ge.value=gc.selectedOptions[0].dataset.e||"";
  gc.onchange=sync;sync();
}

/* ---------- email ---------- */
let emailTab="outbox";
async function viewEmails(){
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">✉️ ${t("email_m")}</div>
    <div class="spacer"></div>${S.user.role!=="readonly"?`<button class="btn pri sm" id="cp">+ ${t("compose")}</button>`:""}</div>
    <div class="tabs" id="et">
      <button data-t="outbox" class="${emailTab==="outbox"?"on":""}">${t("outbox")}</button>
      <button data-t="templates" class="${emailTab==="templates"?"on":""}">${t("templates")}</button>
      ${S.user.role==="admin"?`<button data-t="smtp" class="${emailTab==="smtp"?"on":""}">⚙ ${S.lang==="ar"?"إعدادات الإرسال":"Delivery settings"}</button>`:""}
    </div><div id="ec"><div class="empty">…</div></div>`;
  if(document.getElementById("cp"))cp.onclick=()=>composeMail();
  main.querySelectorAll("#et button").forEach(b=>b.onclick=()=>{emailTab=b.dataset.t;viewEmails();});
  ({outbox:eOutbox,templates:eTemplates,smtp:eSmtp}[emailTab])();
}
const mailStatus=s=>({sent:"var(--ok)",sandbox:"var(--info)",queued:"var(--warn)",failed:"var(--danger)"}[s]||"var(--mut)");
async function eOutbox(){
  const rows=await api("/email/outbox");
  ec.innerHTML=`<div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
    <th>${t("to")}</th><th>${t("subj")}</th><th>${t("status")||"Status"}</th><th>${S.lang==="ar"?"المزود":"Provider"}</th><th>${t("created")||"Date"}</th></tr></thead><tbody>
    ${rows.map(r=>`<tr data-i="${r.id}"><td>${esc(r.to_email)}</td><td><b>${esc(r.subject)}</b>
      ${r.template?`<div class="mut" style="font-size:11px">${esc(r.template)}</div>`:""}</td>
      <td><span class="badge" style="color:${mailStatus(r.status)};background:${mailStatus(r.status)}22">${r.status}</span>
      ${r.error?`<div class="mut" style="font-size:10.5px;color:var(--danger)">${esc(r.error.slice(0,50))}</div>`:""}</td>
      <td class="mut">${esc(r.provider||"—")}</td><td class="mut">${(r.created_at||"").replace("T"," ")}</td></tr>`).join("")
      ||`<tr><td colspan="5"><div class="empty">${t("noData")}</div></td></tr>`}
    </tbody></table></div></div>`;
  ec.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=()=>{
    const r=rows.find(z=>z.id==tr.dataset.i);
    modal(esc(r.subject),`<div class="mut" style="font-size:12px;margin-bottom:10px">${t("to")}: ${esc(r.to_email)} · ${r.status}</div>
      <div style="white-space:pre-wrap;background:var(--bg2);padding:14px;border-radius:10px;font-size:13px">${esc(r.body)}</div>`,[]);});
}
async function eTemplates(){
  const ts=await api("/email/templates");
  ec.innerHTML=`<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
    ${ts.map(x=>`<div class="card"><div class="row"><b style="flex:1">${esc(x.name)}</b>
      <span class="badge" style="color:var(--info);background:var(--info)22">${esc(x.code)}</span></div>
      <div class="mut" style="font-size:12.5px;margin:8px 0">${esc(x.subject)}</div>
      <div class="mut" style="font-size:11.5px;max-height:56px;overflow:hidden">${esc(x.body.slice(0,140))}…</div>
      ${S.user.role!=="readonly"?`<button class="btn sm" style="margin-top:10px" data-e="${x.id}">✎ ${t("edit")}</button>
      <button class="btn sm" style="margin-top:10px" data-u="${x.id}">✉ ${t("sendMail")}</button>`:""}</div>`).join("")}</div>`;
  ec.querySelectorAll("[data-e]").forEach(b=>b.onclick=()=>{
    const x=ts.find(z=>z.id==b.dataset.e);
    const el=modal(t("edit")+" · "+esc(x.code),`<form id="tf">
      <div class="fld"><label>${t("name")}</label><input name="name" value="${esc(x.name)}"></div>
      <div class="fld"><label>${t("subj")}</label><input name="subject" value="${esc(x.subject)}"></div>
      <div class="fld"><label>${t("body")}</label><textarea name="body" style="min-height:220px">${esc(x.body)}</textarea></div>
      <div class="mut" style="font-size:11.5px">${t("variables")}: {{name}} {{company}} {{owner}} {{subject}} {{amount}} {{due_date}} {{pay_link}}</div></form>`,
      [[t("cancel"),close_,""],[t("save"),async()=>{
        const fd=new FormData(el.querySelector("#tf"));const b2={};fd.forEach((v,k)=>b2[k]=v);
        await api(`/email/templates/${x.id}`,{method:"PUT",body:JSON.stringify(b2)});
        toast(t("saved"));close_();eTemplates();},"pri"]]);});
  ec.querySelectorAll("[data-u]").forEach(b=>b.onclick=()=>{
    const x=ts.find(z=>z.id==b.dataset.u);composeMail({subject:x.subject,body:x.body});});
}
function composeMail(pre={}){
  const el=modal(t("compose"),`<form id="cf">
    <div class="fld"><label>${t("to")}</label><input name="to_email" type="email" value="${esc(pre.to_email||"")}" required></div>
    <div class="fld"><label>${t("subj")}</label><input name="subject" value="${esc(pre.subject||"")}" required></div>
    <div class="fld"><label>${t("body")}</label><textarea name="body" style="min-height:200px">${esc(pre.body||"")}</textarea></div>
    <div class="mut" style="font-size:11.5px">{{name}} {{company}} {{owner}}</div></form>`,
    [[t("cancel"),close_,""],[t("sendMail"),async()=>{
      const fd=new FormData(el.querySelector("#cf"));const b={};fd.forEach((v,k)=>b[k]=v);
      if(pre.module){b.module=pre.module;b.record_id=pre.record_id;}
      b.to_name=pre.to_name||"";
      try{const r=await api("/email/send",{method:"POST",body:JSON.stringify(b)});
        toast(t("sendMail")+" ✓ "+r.status);close_();
        if(S.view==="emails"&&emailTab==="outbox")eOutbox();}catch{}},"pri"]]);
}
async function eSmtp(){
  const c=await api("/email/settings");
  const tx=S.lang==="ar"?{
    title:"إعدادات إرسال البريد",provider:"مزود الإرسال",sandbox:"تجريبي — تُحفظ الرسائل داخل النظام فقط",
    smtp:"SMTP",resend:"Resend",resendKey:"مفتاح Resend API",resendFrom:"عنوان الإرسال المعتمد",replyTo:"الرد إلى (اختياري)",
    resendHint:"أضف نطاقك وتحقق من عنوان الإرسال في Resend قبل تفعيل الإرسال.",smtpHint:"استخدم بيانات خادم البريد أو مزود الاستضافة الخاص بك.",
    company:"اسم الشركة",base:"رابط النظام العام",save:"حفظ الإعدادات",test:"إرسال رسالة اختبار",configured:"مُهيأ",notConfigured:"يلزم استكمال الإعدادات",host:"الخادم",port:"المنفذ",user:"اسم المستخدم",password:"كلمة المرور",from:"من",tls:"TLS",
  }:{
    title:"Email delivery settings",provider:"Delivery provider",sandbox:"Sandbox — messages stay inside NebrasCRM",
    smtp:"SMTP",resend:"Resend",resendKey:"Resend API key",resendFrom:"Verified From address",replyTo:"Reply-to (optional)",
    resendHint:"Verify your sending domain and From address in Resend before going live.",smtpHint:"Use your mail host or hosting-provider credentials.",
    company:"Company name",base:"Public CRM URL",save:"Save settings",test:"Send test email",configured:"Configured",notConfigured:"Configuration required",host:"Host",port:"Port",user:"User",password:"Password",from:"From",tls:"TLS",
  };
  const provider=c.email_provider||c.mode||"sandbox";
  const color=provider==="resend"?"var(--purple)":provider==="smtp"?"var(--ok)":"var(--info)";
  const label=provider==="resend"?tx.resend:provider==="smtp"?tx.smtp:tx.sandbox;
  ec.innerHTML=`<div class="card" style="max-width:760px">
    <div class="row" style="margin-bottom:12px;gap:10px"><div><b>${tx.title}</b><div class="mut" style="font-size:11.5px;margin-top:3px">${label}</div></div><div class="spacer"></div>
      <span class="badge" style="color:${color};background:${color}22">${esc(label)}</span></div>
    <form id="deliveryForm">
      <div class="fld"><label>${tx.provider}</label><select name="email_provider" id="deliveryProvider">
        <option value="sandbox" ${provider==="sandbox"?"selected":""}>${tx.sandbox}</option>
        <option value="resend" ${provider==="resend"?"selected":""}>${tx.resend}</option>
        <option value="smtp" ${provider==="smtp"?"selected":""}>${tx.smtp}</option></select></div>
      <div id="resendFields" style="display:${provider==="resend"?"block":"none"}">
        <div class="card" style="padding:14px;margin:10px 0;background:var(--purple)10;border-color:var(--purple)55">
          <div class="row" style="margin-bottom:8px"><b style="color:var(--purple)">✉ ${tx.resend}</b><div class="spacer"></div>
            <span class="badge" style="color:${c.resend_configured?"var(--ok)":"var(--warn)"};background:${c.resend_configured?"var(--ok)":"var(--warn)"}22">${c.resend_configured?tx.configured:tx.notConfigured}</span></div>
          <div class="f2"><div class="fld"><label>${tx.resendKey}</label><input name="resend_api_key" type="password" value="${esc(c.resend_api_key||"")}" placeholder="re_…" autocomplete="new-password"></div>
            <div class="fld"><label>${tx.resendFrom}</label><input name="resend_from" value="${esc(c.resend_from||"")}" placeholder="Sales <sales@yourdomain.com>"></div>
            <div class="fld"><label>${tx.replyTo}</label><input name="resend_reply_to" type="email" value="${esc(c.resend_reply_to||"")}" placeholder="support@yourdomain.com"></div></div>
          <div class="mut" style="font-size:11px">${tx.resendHint}</div></div></div>
      <div id="smtpFields" style="display:${provider==="smtp"?"block":"none"}">
        <div class="card" style="padding:14px;margin:10px 0;background:var(--info)10;border-color:var(--info)55"><div class="f2">
          <div class="fld"><label>${tx.host}</label><input name="smtp_host" value="${esc(c.smtp_host||"")}" placeholder="smtp.example.com"></div>
          <div class="fld"><label>${tx.port}</label><input name="smtp_port" value="${esc(c.smtp_port||"587")}" inputmode="numeric"></div>
          <div class="fld"><label>${tx.user}</label><input name="smtp_user" value="${esc(c.smtp_user||"")}" autocomplete="username"></div>
          <div class="fld"><label>${tx.password}</label><input name="smtp_pass" type="password" value="${esc(c.smtp_pass||"")}" autocomplete="new-password"></div>
          <div class="fld"><label>${tx.from}</label><input name="smtp_from" type="email" value="${esc(c.smtp_from||"")}"></div>
          <div class="fld"><label>${tx.tls}</label><select name="smtp_tls"><option value="1" ${c.smtp_tls==="1"?"selected":""}>ON</option><option value="0" ${c.smtp_tls!=="1"?"selected":""}>OFF</option></select></div>
        </div><div class="mut" style="font-size:11px">${tx.smtpHint}</div></div></div>
      <div class="f2"><div class="fld"><label>${tx.company}</label><input name="company_name" value="${esc(c.company_name||"")}"></div>
        <div class="fld"><label>${tx.base}</label><input name="base_url" value="${esc(c.base_url||"")}" placeholder="https://crm.example.com"></div></div>
    </form>
    <div class="row" style="margin-top:4px"><button class="btn pri sm" id="saveDelivery">💾 ${tx.save}</button><button class="btn sm" id="testDelivery">✉ ${tx.test}</button></div>
  </div>`;
  const providerSelect=ec.querySelector("#deliveryProvider"),smtpFields=ec.querySelector("#smtpFields"),resendFields=ec.querySelector("#resendFields");
  providerSelect.onchange=()=>{smtpFields.style.display=providerSelect.value==="smtp"?"block":"none";resendFields.style.display=providerSelect.value==="resend"?"block":"none";};
  ec.querySelector("#saveDelivery").onclick=async()=>{const fd=new FormData(ec.querySelector("#deliveryForm")),body={};fd.forEach((value,key)=>body[key]=value);
    await api("/email/settings",{method:"PUT",body:JSON.stringify(body)});toast(t("saved"));eSmtp();};
  ec.querySelector("#testDelivery").onclick=async()=>{const result=await api("/email/test",{method:"POST",body:JSON.stringify({to:S.user.email})});
    toast(`${result.provider||providerSelect.value}: ${result.status}${result.error?": "+result.error:" ✓"}`);};
}

/* ---------- payments ---------- */
async function viewPayments(){
  const [s,rows]=await Promise.all([api("/payments/summary"),api("/payments")]);
  const k=(l,v,c)=>`<div class="kpi" style="--pri:${c}"><div class="l">${l}</div><div class="v">${v}</div></div>`;
  const pcl=x=>({paid:"var(--ok)",pending:"var(--warn)",awaiting_settlement:"var(--info)",failed:"var(--danger)",refunded:"var(--purple)"}[x]||"var(--mut)");
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">💳 ${t("payments")}</div>
    <div class="spacer"></div><button class="btn sm" id="paymentMatrix">🖨 ${t("printMatrix")}</button>
    ${S.user.role!=="readonly"?`<button class="btn sm" id="mp">＋ ${t("manualPay")}</button>
    <button class="btn pri sm" id="pl">🔗 ${t("payLink")}</button>`:""}</div>
    <div class="kpis" style="margin-bottom:16px">
      ${k(t("collected"),fmtMoney(s.collected),"var(--ok)")}
      ${k(t("outstandingP"),fmtMoney(s.outstanding),"var(--warn)")}
      ${k(t("overdueP"),fmtMoney(s.overdue),"var(--danger)")}
      ${k(t("pendingP"),fmtMoney(s.pending),"var(--info)")}
      ${k(t("refunded"),fmtMoney(s.refunded),"var(--purple)")}
      ${k(t("awaitingS"),fmtMoney(s.awaiting),"var(--info)")}
      ${k(t("fees"),fmtMoney(s.fees),"var(--danger)")}
      ${k(t("netAmt"),fmtMoney(s.net),"var(--ok)")}</div>
    <div class="card" style="margin-bottom:14px"><b>💳 ${t("channels")}</b><div style="height:10px"></div>
      <div id="chbox" class="mut">…</div></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>#</th><th>${t("invoice")}</th><th>${S.lang==="ar"?"الشركة":"Account"}</th><th>${t("amount")||"Amount"}</th>
      <th>${t("method")}</th><th>Status</th><th>${t("ref")}</th><th></th></tr></thead><tbody>
      ${rows.map(r=>`<tr data-i="${r.id}"><td class="mut" data-l="#">#${r.id}</td><td data-l="${t("invoice")}">${esc(r.invoice_subject||"—")}</td>
        <td data-l="${S.lang==="ar"?"الشركة":"Account"}">${esc(r.account||"—")}</td><td data-l="${t("amount")||"Amount"}"><b>${fmtMoney(r.amount)}</b></td><td data-l="${t("method")}">${esc(r.method||"—")}</td>
        <td data-l="Status"><span class="badge" style="color:${pcl(r.status)};background:${pcl(r.status)}22">${esc(r.status)}</span></td>
        <td class="mut" data-l="${t("ref")}" style="font-size:11.5px">${esc(r.provider_ref||"—")}</td>
        <td data-l="${t("paymentVoucher")}"><button class="btn sm" data-pv="${r.id}" title="${t("printVoucher")}">🖨</button>
          ${r.status==="pending"?`<button class="btn sm" data-cp="${r.token}">🔗</button>`:""}
          ${r.status==="awaiting_settlement"&&["admin","manager"].includes(S.user.role)?`<button class="btn sm" data-st="${r.id}" style="color:var(--ok);border-color:var(--ok)55">✓</button>`:""}
          ${r.status==="paid"&&["admin","manager"].includes(S.user.role)?`<button class="btn sm dgr" data-rf="${r.id}">↩</button>`:""}</td></tr>`).join("")
        ||`<tr><td colspan="8"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  if(document.getElementById("pl")){pl.onclick=payLinkForm;mp.onclick=manualPayForm;}
  document.getElementById("paymentMatrix").onclick=()=>printCurrentView();
  api("/payments/by-channel").then(ch=>{
    const box=document.getElementById("chbox"); if(!box)return;
    const mx=Math.max(...ch.map(c=>c.v||0),1);
    box.innerHTML=ch.length?`<div class="bars">${ch.map(c=>`<div class="bar">
      <div style="overflow:hidden;text-overflow:ellipsis">${c.icon||""} ${esc(S.lang==="ar"?c.name_ar:c.name_en)}</div>
      <div class="barbg"><div class="barfill" style="width:${(c.v||0)/mx*100}%"></div></div>
      <div style="text-align:end;font-weight:700">${fmtMoney(c.v)}<span class="mut" style="font-size:10.5px"> −${fmtMoney(c.fees)}</span></div>
    </div>`).join("")}</div>`:`<div class="empty">${t("noData")}</div>`;});
  main.querySelectorAll("[data-pv]").forEach(b=>b.onclick=e=>{e.stopPropagation();printPaymentReceipt(+b.dataset.pv);});
  main.querySelectorAll("[data-cp]").forEach(b=>b.onclick=e=>{e.stopPropagation();
    copyTxt(location.origin+"/pay/"+b.dataset.cp);});
  main.querySelectorAll("[data-st]").forEach(b=>b.onclick=async e=>{e.stopPropagation();
    await api(`/payments/${b.dataset.st}/settle`,{method:"POST"});toast(t("saved"));viewPayments();});
  main.querySelectorAll("[data-rf]").forEach(b=>b.onclick=async e=>{e.stopPropagation();
    if(!confirm(t("confirmQ")||"?"))return;
    await api(`/payments/${b.dataset.rf}/refund`,{method:"POST"});toast(t("saved"));viewPayments();});
  main.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=e=>{
    if(e.target.closest("button,a,input"))return;
    openPaymentRecord(+tr.dataset.i);});
}

async function openPaymentRecord(paymentId){
  const [doc,events]=await Promise.all([
    api(`/documents/payment/${paymentId}`), api(`/payments/${paymentId}/events`),
  ]);
  const p=doc.payment||{}, invoice=doc.invoice||{}, account=doc.account||{}, contact=doc.contact||{};
  const currency=p.currency||doc.company?.currency||"USD";
  const money=value=>printMoneyValue(value,currency);
  const label=S.lang==="ar"?{
    title:"سند دفع",customer:"العميل",payment:"تفاصيل السداد",invoice:"الفاتورة المرتبطة",amount:"المبلغ",method:"الطريقة",status:"الحالة",date:"التاريخ",reference:"المرجع",balance:"المتبقي",events:"سجل العملية",
  }:{
    title:"Payment voucher",customer:"Customer",payment:"Payment details",invoice:"Linked invoice",amount:"Amount",method:"Method",status:"Status",date:"Date",reference:"Reference",balance:"Balance due",events:"Event log",
  };
  const field=(name,value)=>`<div style="padding:8px 0;border-bottom:1px solid var(--line)"><div class="mut" style="font-size:11px">${esc(name)}</div><b style="font-size:12.5px">${esc(value||"—")}</b></div>`;
  const contactLine=[contact.name,contact.title].filter(Boolean).join(" · ");
  const eventHtml=events.map(event=>`<div style="padding:8px 0;border-bottom:1px solid var(--line);font-size:12px">
    <b>${esc(event.event)}</b> <span class="mut">${(event.created_at||"").replace("T"," ")}</span>
    <div class="mut" style="font-size:10.5px;overflow-wrap:anywhere">${esc(event.payload||"")}</div></div>`).join("")||`<div class="empty">${t("noData")}</div>`;
  modal(`${label.title} · ${esc(doc.reference||"#"+paymentId)}`,`<div class="f2">
    <div class="card" style="padding:12px"><b>${label.customer}</b>${field(S.lang==="ar"?"الشركة":"Account",account.name)}${field(t("contact"),contactLine)}${field(t("phone"),[contact.phone,contact.email].filter(Boolean).join(" · ")||account.phone)}</div>
    <div class="card" style="padding:12px"><b>${label.payment}</b>${field(label.amount,money(p.amount))}${field(label.method,[p.method,p.channel].filter(Boolean).join(" · "))}${field(label.status,p.status)}${field(label.date,(p.paid_on||p.created_on||"").replace("T"," "))}${field(label.reference,p.provider_ref||doc.reference)}</div>
  </div><div class="card" style="padding:12px;margin-top:10px"><b>${label.invoice}</b>${field(t("invoice"),invoice.subject||"#"+invoice.id)}${field(label.balance,money(invoice.remaining))}</div>
  <div style="margin-top:14px"><b style="font-size:12.5px">${label.events}</b>${eventHtml}</div>`,
  [["🖨 "+t("printVoucher"),()=>printPaymentReceipt(paymentId),"pri"]]);
}
function copyTxt(s){navigator.clipboard?.writeText(s);toast(t("copied")+": "+s);}
async function invoicePicker(){
  const r=await api("/invoices?per_page=200");
  return r.data.filter(i=>(i.amount||0)-(i.paid_amount||0)>0.01);
}
async function payLinkForm(){
  const inv=await invoicePicker();
  if(!inv.length)return toast(t("noData"));
  const el=modal(t("payLink"),`<form id="lf2">
    <div class="fld"><label>${t("invoice")}</label><select name="invoice_id" id="iv">
      ${inv.map(i=>`<option value="${i.id}" data-b="${(i.amount||0)-(i.paid_amount||0)}">${esc(i.subject)} — ${fmtMoney((i.amount||0)-(i.paid_amount||0))}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("amount")||"Amount"}</label><input name="amount" id="am" type="number" step="0.01"></div>
    <div class="fld"><label>${t("email")}</label><input name="email" type="email"></div>
    <label class="row" style="font-size:13px;cursor:pointer"><input type="checkbox" name="send_email" style="width:auto">&nbsp;${t("sendWithEmail")}</label>
    </form>`,[[t("cancel"),close_,""],[t("save"),async()=>{
      const fd=new FormData(el.querySelector("#lf2"));const b={};fd.forEach((v,k)=>b[k]=v);
      b.invoice_id=+b.invoice_id;b.amount=b.amount?+b.amount:null;b.send_email=!!b.send_email;
      try{const r=await api("/payments/link",{method:"POST",body:JSON.stringify(b)});
        close_();const url=location.origin+r.url;
        modal(t("payLink"),`<div class="fld"><input id="lk" value="${url}" readonly></div>
          <div class="row"><button class="btn pri sm" id="cy">${t("copy")}</button>
          <a class="btn sm" href="${url}" target="_blank">↗</a></div>
          ${r.emailed_to?`<div class="mut" style="margin-top:10px;font-size:12px">✉ ${esc(r.emailed_to)}</div>`:""}`,[]);
        document.getElementById("cy").onclick=()=>copyTxt(url);
        viewPayments();}catch{}},"pri"]]);
  const iv=el.querySelector("#iv"),am=el.querySelector("#am");
  const sync=()=>am.value=iv.selectedOptions[0].dataset.b;iv.onchange=sync;sync();
}
async function manualPayForm(){
  const inv=await invoicePicker();
  if(!inv.length)return toast(t("noData"));
  const el=modal(t("manualPay"),`<form id="mpf">
    <div class="fld"><label>${t("invoice")}</label><select name="invoice_id" id="iv2">
      ${inv.map(i=>`<option value="${i.id}" data-b="${(i.amount||0)-(i.paid_amount||0)}">${esc(i.subject)} — ${fmtMoney((i.amount||0)-(i.paid_amount||0))}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("amount")||"Amount"}</label><input name="amount" id="am2" type="number" step="0.01"></div>
    <div class="fld"><label>${t("method")}</label><select name="method">
      <option>Bank Transfer</option><option>Cash</option><option>Card</option><option>Wallet</option></select></div>
    <div class="fld"><label>${t("notes")||"Note"}</label><input name="note"></div></form>`,
    [[t("cancel"),close_,""],[t("save"),async()=>{
      const fd=new FormData(el.querySelector("#mpf"));const b={};fd.forEach((v,k)=>b[k]=v);
      b.invoice_id=+b.invoice_id;b.amount=+b.amount;
      try{await api("/payments/manual",{method:"POST",body:JSON.stringify(b)});
        toast(t("saved"));close_();viewPayments();}catch{}},"pri"]]);
  const iv=el.querySelector("#iv2"),am=el.querySelector("#am2");
  const sync=()=>am.value=iv.selectedOptions[0].dataset.b;iv.onchange=sync;sync();
}

/* ---------- market intelligence ---------- */
let intelTab="overview";
function viewIntel(){
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🎯 ${t("intel")}</div></div>
    <div class="tabs" id="it">
      <button data-t="overview" class="${intelTab==="overview"?"on":""}">${t("overview")}</button>
      <button data-t="battle" class="${intelTab==="battle"?"on":""}">⚔️ ${t("battlecard")}</button>
      <button data-t="matrix" class="${intelTab==="matrix"?"on":""}">📊 ${t("matrix")}</button>
    </div><div id="ic"><div class="empty">…</div></div>`;
  main.querySelectorAll("#it button").forEach(b=>b.onclick=()=>{intelTab=b.dataset.t;viewIntel();});
  ({overview:iOverview,battle:iBattle,matrix:iMatrix}[intelTab])();
}
const tierColor=v=>({Primary:"var(--danger)",Secondary:"var(--warn)",Emerging:"var(--info)",Niche:"var(--mut)"}[v]||"var(--mut)");
const posColor=v=>({"We Win":"var(--ok)","Parity":"var(--warn)","They Win":"var(--danger)"}[v]||"var(--mut)");
function bars(arr,fmt,key){const mx=Math.max(...arr.map(a=>+a[key]||0),1);
  return `<div class="bars">${arr.map(a=>`<div class="bar"><div style="overflow:hidden;text-overflow:ellipsis">${esc(a.k||"—")}</div>
    <div class="barbg"><div class="barfill" style="width:${(+a[key]||0)/mx*100}%"></div></div>
    <div style="text-align:end;font-weight:700">${fmt(a[key])}</div></div>`).join("")}</div>`;}

async function iOverview(){
  const d=await api("/intel/dashboard");
  const k=d.kpi;
  const kp=(l,v,c)=>`<div class="kpi" style="--pri:${c}"><div class="l">${l}</div><div class="v">${v}</div></div>`;
  ic.innerHTML=`<div class="kpis" style="margin-bottom:16px">
      ${kp(t("tam"),fmtMoney(k.tam),"var(--pri)")}
      ${kp(t("avgGrowth"),k.avg_growth+"%","var(--ok)")}
      ${kp(t("ourShare"),k.our_share+"%","var(--purple)")}
      ${kp(t("competitorsK"),fmtNum(k.competitors),"var(--info)")}
      ${kp(t("primaryThreats"),fmtNum(k.primary_threats),"var(--danger)")}
      ${kp(t("contested"),fmtMoney(k.contested_pipeline),"var(--warn)")}
      ${kp(t("lostTo"),fmtMoney(k.lost_to_competitors),"var(--danger)")}
      ${kp(t("trackedProducts"),fmtNum(k.tracked_products),"var(--info)")}
      ${kp(t("studiesK"),fmtNum(k.studies),"var(--purple)")}</div>
    <div class="card" style="margin-bottom:14px"><b>⚔️ ${t("winLoss")}</b><div style="height:10px"></div>
      <div class="wrap-scroll"><table class="tbl"><thead><tr>
        <th>${t("competitorsK")}</th><th>${t("threat")}</th><th>${t("wonK")}</th><th>${t("lostK")}</th>
        <th>${t("winRateK")}</th><th>${t("lostTo")}</th><th></th></tr></thead><tbody>
      ${d.winloss.map(w=>`<tr><td><b>${esc(w.k)}</b>
        <span class="badge" style="margin-inline-start:6px;color:${tierColor(w.tier)};background:${tierColor(w.tier)}22">${esc(w.tier||"")}</span></td>
        <td><div class="row"><div class="barbg" style="width:52px"><div class="barfill" style="width:${(w.threat_score||0)*10}%"></div></div>
          <span class="mut">${w.threat_score||0}</span></div></td>
        <td style="color:var(--ok);font-weight:700">${w.won||0}</td>
        <td style="color:var(--danger);font-weight:700">${w.lost||0}</td>
        <td>${w.win_rate==null?'<span class="mut">—</span>':`<b style="color:${w.win_rate>=50?"var(--ok)":"var(--danger)"}">${w.win_rate}%</b>`}</td>
        <td>${fmtMoney(w.lost_value)}</td>
        <td><button class="btn sm" data-bc="${w.id}">⚔️</button></td></tr>`).join("")}
      </tbody></table></div></div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(330px,1fr))">
      <div class="card"><b>${t("lossReasons")}</b><div style="height:10px"></div>${bars(d.loss_reasons,fmtMoney,"v")}</div>
      <div class="card"><b>${t("marketShare")}</b><div style="height:10px"></div>${bars(d.share,v=>v+"%","v")}</div>
      <div class="card"><b>${t("tamBySeg")}</b><div style="height:10px"></div>${bars(d.tam,fmtMoney,"v")}</div>
      <div class="card"><b>${t("positioningK")}</b><div style="height:10px"></div>
        ${d.positioning.map(p=>`<div class="row" style="padding:7px 0;border-bottom:1px solid var(--line)">
          <span class="badge" style="color:${posColor(p.k)};background:${posColor(p.k)}22">${esc(p.k)}</span>
          <div class="spacer"></div><b>${p.n}</b></div>`).join("")}</div>
      <div class="card" style="grid-column:span 2"><b>💰 ${t("priceGap")}</b> <span class="mut" style="font-size:11px">· ${t("basis")}</span><div style="height:10px"></div>
        <div class="wrap-scroll"><table class="tbl"><thead><tr><th>${t("theirProducts")}</th><th>${t("competitorsK")}</th>
        <th>${t("theirPrice")}</th><th>${t("ourPrice")}</th><th>${t("gap")}</th></tr></thead><tbody>
        ${d.price_gap.map(p=>`<tr><td>${esc(p.name)}</td><td class="mut">${esc(p.competitor||"—")}</td>
          <td>${fmtMoney(p.price)}</td><td>${fmtMoney(p.our_price)}</td>
          <td><b style="color:${p.gap<0?"var(--ok)":"var(--danger)"}">${p.gap_pct==null?"—":(p.gap_pct>0?"+":"")+p.gap_pct+"%"}</b>
          <span class="mut" style="font-size:11px">${p.gap_pct==null?"":(p.gap<0?t("cheaper"):t("pricier"))}</span></td></tr>`).join("")}
        </tbody></table></div></div>
    </div>`;
  ic.querySelectorAll("[data-bc]").forEach(b=>b.onclick=()=>openBattlecard(+b.dataset.bc));
}

async function iBattle(){
  const cs=(await api("/competitors?per_page=100")).data;
  ic.innerHTML=`<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))">
    ${cs.map(c=>`<div class="card" style="cursor:pointer" data-bc="${c.id}">
      <div class="row"><b style="flex:1;font-size:15px">${esc(c.name)}</b>
        <span class="badge" style="color:${tierColor(c.tier)};background:${tierColor(c.tier)}22">${esc(c.tier||"")}</span></div>
      <div class="row" style="margin:8px 0;gap:14px">
        <div><div class="mut" style="font-size:11px">${t("marketShare")}</div><b>${c.market_share||0}%</b></div>
        <div><div class="mut" style="font-size:11px">${t("threat")}</div><b>${c.threat_score||0}/10</b></div>
        <div><div class="mut" style="font-size:11px">${t("segment")||"Segment"}</div><b style="font-size:12px">${esc(c.segment||"—")}</b></div></div>
      <div class="barbg"><div class="barfill" style="width:${(c.threat_score||0)*10}%"></div></div>
      <div class="mut" style="font-size:11.5px;margin-top:10px;max-height:44px;overflow:hidden">${esc((c.strengths||"").slice(0,110))}</div>
      <button class="btn sm" style="margin-top:10px;width:100%">⚔️ ${t("openBattlecard")}</button></div>`).join("")}</div>`;
  ic.querySelectorAll("[data-bc]").forEach(b=>b.onclick=()=>openBattlecard(+b.dataset.bc));
}

async function openBattlecard(cid){
  const b=await api("/intel/battlecard/"+cid);
  const c=b.competitor, st=b.stats;
  const box=(title,txt,color)=>`<div class="card" style="border-inline-start:3px solid ${color};margin-bottom:10px">
    <b style="font-size:12.5px;color:${color}">${title}</b>
    <div style="font-size:12.5px;margin-top:6px;white-space:pre-wrap;line-height:1.9">${esc(txt||"—")}</div></div>`;
  modal(`⚔️ ${esc(c.name)}`,
   `<div class="row" style="gap:8px;flex-wrap:wrap;margin-bottom:14px">
      <span class="badge" style="color:${tierColor(c.tier)};background:${tierColor(c.tier)}22">${esc(c.tier||"")}</span>
      <span class="mut" style="font-size:12px">${esc(c.segment||"")} · ${esc(c.hq_country||"")} · ${esc(c.website||"")}</span></div>
    <div class="kpis" style="margin-bottom:14px">
      <div class="kpi" style="--pri:var(--ok)"><div class="l">${t("wonK")}</div><div class="v">${st.won}</div></div>
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("lostK")}</div><div class="v">${st.lost}</div></div>
      <div class="kpi" style="--pri:var(--warn)"><div class="l">${t("openK")}</div><div class="v">${st.open}</div></div>
      <div class="kpi" style="--pri:var(--purple)"><div class="l">${t("winRateK")}</div><div class="v">${st.win_rate==null?"—":st.win_rate+"%"}</div></div>
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("lostTo")}</div><div class="v" style="font-size:17px">${fmtMoney(st.lost_value)}</div></div>
      <div class="kpi" style="--pri:var(--info)"><div class="l">${t("marketShare")}</div><div class="v">${c.market_share||0}%</div></div></div>
    ${box("✅ "+t("strengths"),c.strengths,"var(--ok)")}
    ${box("⚠️ "+t("weaknesses"),c.weaknesses,"var(--danger)")}
    ${box("🎯 "+t("counterStrategy"),c.strategy,"var(--pri)")}
    ${b.loss_reasons.length?`<div class="card" style="margin-bottom:10px"><b style="font-size:12.5px">${t("lossReasons")}</b>
      <div style="height:8px"></div>${b.loss_reasons.map(r=>`<div class="row" style="padding:5px 0">
      <span>${esc(r.k)}</span><div class="spacer"></div><b>${r.n}</b></div>`).join("")}</div>`:""}
    ${b.products.length?`<div class="card" style="margin-bottom:10px"><b style="font-size:12.5px">${t("theirProducts")}</b>
      <div class="wrap-scroll" style="margin-top:8px"><table class="tbl"><thead><tr><th>${t("name")}</th>
      <th>${t("theirPrice")}</th><th>${t("ourPrice")}</th><th>${t("gap")}</th><th>${t("positioningK")}</th></tr></thead><tbody>
      ${b.products.map(p=>`<tr><td>${esc(p.name)}</td><td>${fmtMoney(p.price)}</td><td>${fmtMoney(p.our_effective)}</td>
        <td><b style="color:${p.gap<0?"var(--ok)":"var(--danger)"}">${p.gap_pct==null?"—":(p.gap_pct>0?"+":"")+p.gap_pct+"%"}</b></td>
        <td><span class="badge" style="color:${posColor(p.positioning)};background:${posColor(p.positioning)}22">${esc(p.positioning||"")}</span></td></tr>`).join("")}
      </tbody></table></div></div>`:""}
    ${b.deals.length?`<div class="card"><b style="font-size:12.5px">${t("recentDeals")}</b><div style="height:8px"></div>
      ${b.deals.map(d=>`<div class="row" style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px">
        <span style="flex:1">${esc(d.name)}</span><b>${fmtMoney(d.amount)}</b>
        <span class="badge" style="color:${d.stage==="Closed Won"?"var(--ok)":d.stage==="Closed Lost"?"var(--danger)":"var(--info)"};
          background:${d.stage==="Closed Won"?"var(--ok)":d.stage==="Closed Lost"?"var(--danger)":"var(--info)"}22">${esc(d.stage)}</span>
        ${d.loss_reason?`<span class="mut" style="font-size:11px">${esc(d.loss_reason)}</span>`:""}</div>`).join("")}</div>`:""}`,
   []);
}

async function iMatrix(){
  const m=await api("/intel/matrix");
  ic.innerHTML=m.rows.length?m.rows.map(r=>`<div class="card" style="margin-bottom:12px">
    <div class="row" style="flex-wrap:wrap"><b style="font-size:15px">${esc(r.product)}</b>
      <span class="badge" style="color:var(--pri);background:var(--pri)22">${fmtMoney(r.our_price)}</span>
      <div class="spacer"></div>
      <span class="mut" style="font-size:12px">${t("basis")} · ${t("marketRange")}: ${fmtMoney(r.market_low)} – ${fmtMoney(r.market_high)}
      · ${S.lang==="ar"?"المتوسط":"avg"} ${fmtMoney(r.market_avg)}</span></div>
    <div class="wrap-scroll" style="margin-top:10px"><table class="tbl"><thead><tr>
      <th>${t("competitorsK")}</th><th>${t("theirProducts")}</th><th>${t("theirPrice")}</th>
      <th>${t("gap")}</th><th>${t("positioningK")}</th><th>${S.lang==="ar"?"الفجوات":"Their gaps"}</th></tr></thead><tbody>
      ${r.rivals.map(v=>{const g=r.our_price-(v.price||0);
        const gp=v.price?Math.round(g/v.price*1000)/10:null;
        return `<tr><td><b>${esc(v.competitor||"—")}</b></td><td>${esc(v.name)}</td><td>${fmtMoney(v.price)}</td>
        <td><b style="color:${g<0?"var(--ok)":"var(--danger)"}">${gp==null?"—":(gp>0?"+":"")+gp+"%"}</b></td>
        <td><span class="badge" style="color:${posColor(v.positioning)};background:${posColor(v.positioning)}22">${esc(v.positioning||"")}</span></td>
        <td class="mut" style="font-size:11.5px;max-width:240px">${esc((v.gaps||"—").slice(0,90))}</td></tr>`;}).join("")}
    </tbody></table></div></div>`).join("")
    :`<div class="empty">${t("noRivals")}</div>`;
}

/* ---------- customer segmentation & lists ---------- */
let segTab="scores", SEGMETA=null;
async function viewSegments(){
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🏅 ${t("segmentsM")}</div>
    <div class="spacer"></div>${["admin","manager"].includes(S.user.role)?`<button class="btn pri sm" id="ap">↻ ${t("applySeg")}</button>`:""}</div>
    <div class="tabs" id="sg">
      <button data-t="scores" class="${segTab==="scores"?"on":""}">${t("score")}</button>
      <button data-t="lists" class="${segTab==="lists"?"on":""}">${t("lists")}</button>
    </div><div id="sc"><div class="empty">…</div></div>`;
  if(document.getElementById("ap"))ap.onclick=async()=>{
    const r=await api("/segments/apply",{method:"POST"});toast(t("saved")+" · "+r.updated);viewSegments();};
  main.querySelectorAll("#sg button").forEach(b=>b.onclick=()=>{segTab=b.dataset.t;viewSegments();});
  segTab==="scores"?sgScores():sgLists();
}
const segColor=(m,k)=>(m.segments[k]||{}).color||"var(--mut)";
const listColor=(m,k)=>(m.lists[k]||{}).color||"var(--mut)";
async function sgScores(){
  const d=await api("/segments/scores"); SEGMETA=d.meta;
  const m=d.meta;
  sc.innerHTML=`<div class="kpis" style="margin-bottom:14px">
    ${Object.entries(m.segments).map(([k,v])=>`<div class="kpi" style="--pri:${TC(v.color)}">
      <div class="l">${S.lang==="ar"?v.ar:v.en}</div><div class="v">${d.distribution[k]||0}</div></div>`).join("")}</div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th><input type="checkbox" id="sall"></th><th>${t("name")}</th><th>${t("score")}</th>
      <th>${t("current")}</th><th>${t("suggested")}</th><th>${t("lists")}</th>
      <th>${t("revenue")}</th><th>${t("lastActivity")}</th></tr></thead><tbody>
      ${d.accounts.map(a=>`<tr data-i="${a.id}">
        <td><input type="checkbox" class="sck" value="${a.id}"></td>
        <td><b>${esc(a.name)}</b></td>
        <td><div class="row"><div class="barbg" style="width:56px"><div class="barfill" style="width:${a.score}%"></div></div>
          <b>${a.score}</b></div></td>
        <td>${a.segment?`<span class="badge" style="color:${TC(segColor(m,a.segment))};background:${TC(segColor(m,a.segment))}22">${S.lang==="ar"?(m.segments[a.segment]||{}).ar:a.segment}</span>`:"—"}</td>
        <td><span class="badge" style="color:${TC(segColor(m,a.suggested))};background:${TC(segColor(m,a.suggested))}22">${S.lang==="ar"?(m.segments[a.suggested]||{}).ar:a.suggested}</span></td>
        <td>${a.list_tag?`<span class="badge" style="color:${TC(listColor(m,a.list_tag))};background:${TC(listColor(m,a.list_tag))}22">${(m.lists[a.list_tag]||{}).icon||""} ${S.lang==="ar"?(m.lists[a.list_tag]||{}).ar:a.list_tag}</span>`:"—"}</td>
        <td><b>${fmtMoney(a.revenue)}</b></td>
        <td class="mut">${a.last_activity||"—"}${a.days_inactive!=null?` <span style="font-size:10.5px">(${a.days_inactive}d)</span>`:""}</td></tr>`).join("")}
      </tbody></table></div>
      <div class="row" style="padding:12px 14px;flex-wrap:wrap"><span class="mut" id="selc">0 ${t("selected")}</span>
        <div class="spacer"></div>
        ${Object.entries(m.lists).map(([k,v])=>`<button class="btn sm" data-tag="${k}"
          style="color:${TC(v.color)};border-color:${TC(v.color)}55">${v.icon} ${S.lang==="ar"?v.ar:v.en}</button>`).join("")}
        <button class="btn sm" data-tag="">✕</button></div></div>`;
  const sel=()=>[...sc.querySelectorAll(".sck:checked")].map(x=>+x.value);
  const upd=()=>document.getElementById("selc").textContent=sel().length+" "+t("selected");
  sc.querySelectorAll(".sck").forEach(c=>c.onchange=upd);
  sall.onchange=()=>{sc.querySelectorAll(".sck").forEach(c=>c.checked=sall.checked);upd();};
  sc.querySelectorAll("[data-tag]").forEach(b=>b.onclick=async()=>{
    const ids=sel(); if(!ids.length)return toast(t("noData"));
    const tag=b.dataset.tag;
    let reason="";
    if(tag==="Blacklist"){reason=prompt(t("reason"));if(!reason)return;}
    await api("/segments/tag",{method:"POST",body:JSON.stringify({account_ids:ids,list_tag:tag,reason})});
    toast(t("saved"));sgScores();});
}
async function sgLists(){
  const meta=(await api("/segments/meta"));
  const data={};
  for(const k of Object.keys(meta.lists)) data[k]=await api("/segments/list/"+encodeURIComponent(k));
  sc.innerHTML=`<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(320px,1fr))">
    ${Object.entries(meta.lists).map(([k,v])=>{const d=data[k];
      return `<div class="card" style="border-inline-start:3px solid ${TC(v.color)}">
      <div class="row"><b style="flex:1;font-size:15px">${v.icon} ${S.lang==="ar"?v.ar:v.en}</b>
        <span class="badge" style="color:${TC(v.color)};background:${TC(v.color)}22">${d.members.length}</span></div>
      <div class="mut" style="font-size:12px;margin:6px 0">${t("revenue")}: <b>${fmtMoney(d.total_revenue)}</b></div>
      ${d.members.slice(0,6).map(x=>`<div class="row" style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px">
        <span style="flex:1">${esc(x.name)}</span><b>${fmtMoney(x.revenue)}</b></div>`).join("")
        ||`<div class="mut" style="font-size:12px">${t("noData")}</div>`}
      ${d.members.length>6?`<div class="mut" style="font-size:11px;margin-top:6px">+${d.members.length-6}</div>`:""}
      ${k==="Blacklist"&&d.members.length?`<div class="mut" style="font-size:11px;margin-top:8px;color:var(--danger)">
        ⛔ ${esc(d.members[0].blacklist_reason||"")}</div>`:""}</div>`;}).join("")}</div>`;
}

/* ---------- stagnation reports ---------- */
let stTab="products", stDays={products:90,customers:180};
async function viewStagnant(){
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🧊 ${t("stagnant")}</div></div>
    <div class="tabs" id="stt">
      <button data-t="products" class="${stTab==="products"?"on":""}">📦 ${t("deadStock")}</button>
      <button data-t="customers" class="${stTab==="customers"?"on":""}">😴 ${t("idleCustomers")}</button>
    </div><div id="stc"><div class="empty">…</div></div>`;
  main.querySelectorAll("#stt button").forEach(b=>b.onclick=()=>{stTab=b.dataset.t;viewStagnant();});
  stTab==="products"?stProducts():stCustomers();
}
function daysPicker(cur,opts,cb){
  return `<div class="row" style="gap:6px">${opts.map(o=>`<button class="btn sm${cur===o?" pri":""}" data-d="${o}">${o}d</button>`).join("")}</div>`;
}
async function stProducts(){
  const d=await api("/reports/stagnant-products?days="+stDays.products);
  const rc=x=>({["Never Sold"]:"var(--danger)",["Quoted, Never Sold"]:"var(--purple)",Critical:"var(--danger)",Stagnant:"var(--warn)"}[x]||"var(--mut)");
  stc.innerHTML=`<div class="row" style="margin-bottom:12px">${daysPicker(stDays.products,[30,90,180,365])}</div>
    <div class="kpis" style="margin-bottom:14px">
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("tiedCapital")}</div><div class="v">${fmtMoney(d.total_tied)}</div></div>
      <div class="kpi" style="--pri:var(--warn)"><div class="l">${t("deadStock")}</div><div class="v">${d.rows.length}</div></div>
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("neverSold")}</div><div class="v">${d.never_sold}</div></div>
      <div class="kpi" style="--pri:var(--purple)"><div class="l">Critical</div><div class="v">${d.critical}</div></div>
      <div class="kpi" style="--pri:var(--info)"><div class="l">${S.lang==="ar"?"عُرض ولم يُبع":"Quoted, not sold"}</div><div class="v">${d.quoted_not_sold||0}</div></div></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${t("category")||"Category"}</th><th>${t("inStock")}</th><th>${t("tiedCapital")}</th>
      <th>${t("lastSold")}</th><th>${t("daysIdle")}</th><th>Status</th></tr></thead><tbody>
      ${d.rows.map(r=>`<tr><td><b>${esc(r.name)}</b><div class="mut" style="font-size:11px">${esc(r.code||"")}</div></td>
        <td class="mut">${esc(r.category||"—")}</td><td>${fmtNum(r.qty_in_stock)}</td>
        <td><b style="color:var(--danger)">${fmtMoney(r.tied_capital)}</b></td>
        <td class="mut">${r.last_sold||"—"}</td><td>${r.days_idle==null?"—":r.days_idle}</td>
        <td><span class="badge" style="color:${rc(r.status)};background:${rc(r.status)}22">${r.status}</span></td></tr>`).join("")
        ||`<tr><td colspan="7"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  stc.querySelectorAll("[data-d]").forEach(b=>b.onclick=()=>{stDays.products=+b.dataset.d;stProducts();});
}
async function stCustomers(){
  const d=await api("/reports/stagnant-customers?days="+stDays.customers);
  const rc=x=>({Lost:"var(--danger)",High:"var(--warn)",Medium:"var(--info)"}[x]||"var(--mut)");
  stc.innerHTML=`<div class="row" style="margin-bottom:12px">${daysPicker(stDays.customers,[90,180,365,540])}</div>
    <div class="kpis" style="margin-bottom:14px">
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("revenueAtRisk")}</div><div class="v">${fmtMoney(d.revenue_at_risk)}</div></div>
      <div class="kpi" style="--pri:var(--warn)"><div class="l">${t("idleCustomers")}</div><div class="v">${d.rows.length}</div></div>
      <div class="kpi" style="--pri:var(--info)"><div class="l">${t("outstandingP")}</div><div class="v">${fmtMoney(d.outstanding_at_risk)}</div></div></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${t("revenue")}</th><th>${t("outstandingP")}</th><th>${t("lastActivity")}</th>
      <th>${t("daysIdle")}</th><th>${t("risk")}</th><th>${t("lists")}</th></tr></thead><tbody>
      ${d.rows.map(r=>`<tr><td><b>${esc(r.name)}</b></td><td>${fmtMoney(r.revenue)}</td>
        <td style="color:${r.outstanding>0?"var(--danger)":"var(--mut)"}">${fmtMoney(r.outstanding)}</td>
        <td class="mut">${r.last_activity||"—"}</td><td>${r.days_inactive==null?"—":r.days_inactive}</td>
        <td><span class="badge" style="color:${rc(r.risk)};background:${rc(r.risk)}22">${r.risk}</span></td>
        <td class="mut">${esc(r.list_tag||"—")}</td></tr>`).join("")
        ||`<tr><td colspan="7"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  stc.querySelectorAll("[data-d]").forEach(b=>b.onclick=()=>{stDays.customers=+b.dataset.d;stCustomers();});
}

async function oppAnalytics(){
  const d=await api("/opportunities/analytics"); const k=d.kpi;
  const kp=(l,v,c)=>`<div class="kpi" style="--pri:${c}"><div class="l">${l}</div><div class="v">${v}</div></div>`;
  const bb=(arr,fmt,key)=>{const mx=Math.max(...arr.map(a=>+a[key]||0),1);
    return `<div class="bars">${arr.map(a=>`<div class="bar"><div style="overflow:hidden;text-overflow:ellipsis">${esc(a.k||"—")}</div>
      <div class="barbg"><div class="barfill" style="width:${(+a[key]||0)/mx*100}%"></div></div>
      <div style="text-align:end;font-weight:700">${fmt(a[key])}</div></div>`).join("")}</div>`;};
  modal("🌱 "+t("opps"),`<div class="kpis" style="margin-bottom:14px">
      ${kp(t("oppPotential"),fmtNum(k.potential),"var(--info)")}
      ${kp(t("oppPotential")+" $",fmtMoney(k.potential_value),"var(--pri)")}
      ${kp(t("weighted"),fmtMoney(k.weighted),"var(--purple)")}
      ${kp(t("oppWon"),fmtNum(k.won),"var(--ok)")}
      ${kp(t("oppLost"),fmtNum(k.lost),"var(--danger)")}
      ${kp(t("winRateK"),k.win_rate+"%","var(--warn)")}</div>
    <div class="card" style="margin-bottom:10px"><b>${t("byStage")}</b><div style="height:8px"></div>${bb(d.by_stage,fmtMoney,"v")}</div>
    <div class="card" style="margin-bottom:10px"><b>${t("winReasons")}</b><div style="height:8px"></div>${bb(d.win_reasons,fmtNum,"n")}</div>
    <div class="card" style="margin-bottom:10px"><b>${t("lossReasons")}</b><div style="height:8px"></div>${bb(d.loss_reasons,fmtMoney,"v")}</div>
    <div class="card"><b>${t("bySource")}</b><div style="height:8px"></div>${bb(d.sources,fmtMoney,"v")}</div>`,[]);
}

/* ---------- global geography ---------- */
let geoSel={country:null,region:null,city:null};
async function viewGeo(){
  const st=await api("/geo/stats"), c=st.counts;
  const kp=(l,v,col)=>`<div class="kpi" style="--pri:${col}"><div class="l">${l}</div><div class="v">${fmtNum(v)}</div></div>`;
  main.innerHTML=`<div class="row" style="margin-bottom:14px;flex-wrap:wrap"><div class="h1">🌍 ${t("geo")}</div>
    <div class="spacer"></div><span class="mut" style="font-size:12px">${fmtNum(c.countries)} ${t("country")} · ${fmtNum(c.regions)} ${t("region")} · ${fmtNum(c.cities)} ${t("city")}</span></div>
    <div class="kpis" style="margin-bottom:14px">
      ${kp(t("country"),c.countries,"var(--pri)")}
      ${kp(t("region"),c.regions,"var(--info)")}
      ${kp(t("city"),c.cities,"var(--purple)")}
      ${kp(t("neighborhood"),c.neighborhoods,"var(--warn)")}
      ${kp(t("street"),c.streets,"var(--danger)")}</div>
    <div class="card" style="margin-bottom:14px">
      <input id="gq" placeholder="${t("searchGeo")}" style="width:100%;background:var(--bg2);border:1px solid var(--line);border-radius:9px;padding:9px 12px"><div id="gres"></div></div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(240px,1fr));margin-bottom:14px">
      <div class="card" style="padding:0"><div style="padding:10px 12px;border-bottom:1px solid var(--line)"><b>🌐 ${t("country")}</b></div>
        <div id="ccountry" style="max-height:360px;overflow:auto"></div></div>
      <div class="card" style="padding:0"><div style="padding:10px 12px;border-bottom:1px solid var(--line)"><b>🗺️ ${t("region")}</b></div>
        <div id="cregion" style="max-height:360px;overflow:auto"><div class="empty" style="padding:20px">—</div></div></div>
      <div class="card" style="padding:0"><div style="padding:10px 12px;border-bottom:1px solid var(--line)"><b>🏙️ ${t("city")}</b></div>
        <div id="ccity" style="max-height:360px;overflow:auto"><div class="empty" style="padding:20px">—</div></div></div>
    </div>
    <div class="card"><b>${S.lang==="ar"?"الأداء حسب الدولة":"Performance by country"}</b><div style="height:10px"></div>
      <div class="wrap-scroll"><table class="tbl"><thead><tr><th>${t("country")}</th><th>${t("region")}</th><th>${t("city")}</th>
      <th>${t("accounts")||"Accounts"}</th><th>${t("revenue")}</th><th>${t("partners")}</th></tr></thead><tbody>
      ${st.by_country.filter(x=>x.accounts||x.revenue||x.partners).slice(0,50).map(x=>`<tr><td><b>${esc(x.k)}</b> <span class="mut" style="font-size:11px">${esc(x.code||"")}</span></td>
        <td>${fmtNum(x.regions)}</td><td>${fmtNum(x.cities)}</td><td>${x.accounts}</td><td><b>${fmtMoney(x.revenue)}</b></td><td>${x.partners}</td></tr>`).join("")
        ||`<tr><td colspan="6"><div class="empty">${t("noData")}</div></td></tr>`}</tbody></table></div></div>`;

  const countryBox=document.getElementById("ccountry"), regionBox=document.getElementById("cregion"), cityBox=document.getElementById("ccity");
  const geoName=(item,kind)=>{try{if(kind==="country"&&S.lang==="ar"&&item.code&&Intl.DisplayNames)
    return new Intl.DisplayNames(["ar"],{type:"region"}).of(item.code)||item.name_ar||item.name_en;}catch{}return item.name_ar||item.name_en;};
  const itemList=(el,items,selected,onPick,kind)=>{
    el.innerHTML=items.length?items.map(item=>`<div data-i="${item.id}" style="padding:8px 12px;cursor:pointer;border-bottom:1px solid var(--line);font-size:12.5px;${selected===item.id?"background:var(--pri)22":""}">
      <div class="row"><span style="flex:1">${esc(geoName(item,kind))}</span>
      <span class="mut" style="font-size:10.5px">${kind==="country"?item.code||"":kind==="region"?(item.cities||0):fmtNum(item.population||0)}</span></div>
      ${item.name_en&&item.name_en!==item.name_ar?`<div class="mut" style="font-size:10.5px">${esc(item.name_en)}</div>`:""}</div>`).join("")
      :`<div class="empty" style="padding:20px">${t("noData")}</div>`;
    el.querySelectorAll("[data-i]").forEach(node=>node.onclick=()=>onPick(+node.dataset.i));
  };
  const countries=await api("/geo/countries");
  const selectCity=id=>{geoSel.city=id;};
  const selectRegion=async id=>{
    geoSel.region=id; geoSel.city=null;
    const cities=await api("/geo/cities?region_id="+id+"&limit=200");
    itemList(cityBox,cities,geoSel.city,selectCity,"city");
  };
  const selectCountry=async id=>{
    geoSel.country=id;geoSel.region=null;geoSel.city=null;
    itemList(countryBox,countries,geoSel.country,selectCountry,"country");
    const regions=await api("/geo/regions?country_id="+id+"&limit=200");
    itemList(regionBox,regions,geoSel.region,selectRegion,"region");
    cityBox.innerHTML=`<div class="empty" style="padding:20px">${S.lang==="ar"?"اختر منطقة":"Select a region"}</div>`;
  };
  itemList(countryBox,countries,geoSel.country,selectCountry,"country");
  if(geoSel.country) selectCountry(geoSel.country);

  let timer;gq.oninput=()=>{clearTimeout(timer);timer=setTimeout(async()=>{
    const q=gq.value.trim();if(q.length<2){gres.innerHTML="";return;}
    const rows=await api("/geo/search?q="+encodeURIComponent(q));
    gres.innerHTML=rows.length?`<div style="margin-top:10px;max-height:260px;overflow:auto">${rows.map(x=>`<div style="padding:7px 0;border-bottom:1px solid var(--line);font-size:12.5px">
      <div class="row"><b style="flex:1">${esc(x.name_ar||x.name_en)}</b><span class="badge" style="color:var(--info);background:var(--info)22">${esc(S.lang==="ar"?x.level_ar:x.level_en)}</span></div>
      <div class="mut" style="font-size:11px">${esc(x.name_en||"")}${x.parent?" · "+esc(x.parent):""}${x.population?" · "+fmtNum(x.population):""}</div></div>`).join("")}</div>`
      :`<div class="mut" style="margin-top:8px;font-size:12px">${t("noData")}</div>`;},250);};
}

/* ---------- partners ---------- */
let PMETA=null;
async function viewPartners(){
  if(!PMETA)PMETA=await api("/partners/meta");
  const [s,rows]=await Promise.all([api("/partners/analytics/summary"),api("/partners")]);
  const k=s.kpi;
  const kp=(l,v,c)=>`<div class="kpi" style="--pri:${c}"><div class="l">${l}</div><div class="v">${v}</div></div>`;
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🤝 ${t("partners")}</div>
    <div class="spacer"></div>${["admin","manager"].includes(S.user.role)?
      `<button class="btn sm" id="acc">⚙ ${t("accrue")}</button>
       <button class="btn pri sm" id="ap">+ ${t("addPartner")}</button>`:""}</div>
    <div class="kpis" style="margin-bottom:16px">
      ${kp(t("partners"),fmtNum(k.partners),"var(--pri)")}
      ${kp(t("revenue"),fmtMoney(k.partner_sales),"var(--ok)")}
      ${kp(t("commission"),fmtMoney(k.commission_earned),"var(--purple)")}
      ${kp(t("payout"),fmtMoney(k.paid_out),"var(--info)")}
      ${kp(t("netBal"),fmtMoney(k.owed),"var(--warn)")}
      ${kp(S.lang==="ar"?"السلف":"Advances",fmtMoney(k.advances),"var(--danger)")}</div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${t("type")||"Type"}</th><th>${t("country")}</th>
      <th>${t("commModel")}</th><th>${t("revenue")}</th><th>${t("achievement")}</th>
      <th>${t("owedTo")}</th><th>${t("owedBy")}</th><th>${t("netBal")}</th></tr></thead><tbody>
      ${rows.map(r=>{const ach=r.target?Math.round(r.sales/r.target*100):null;
        return `<tr data-i="${r.id}"><td><b>${esc(r.name)}</b><div class="mut" style="font-size:11px">${esc(r.code||"")}</div></td>
        <td><span class="badge" style="color:var(--info);background:var(--info)22">${(PMETA.types[r.type]||{}).icon||""} ${S.lang==="ar"?(PMETA.types[r.type]||{}).ar:r.type}</span></td>
        <td class="mut">${esc(r.gov_ar||"—")}</td>
        <td class="mut" style="font-size:11.5px">${S.lang==="ar"?(PMETA.models[r.commission_model]||{}).ar:r.commission_model}
          ${r.commission_model!=="tiered"?` ${r.commission_rate}`:""}</td>
        <td><b>${fmtMoney(r.sales)}</b></td>
        <td>${ach==null?"—":`<div class="row"><div class="barbg" style="width:48px"><div class="barfill" style="width:${Math.min(100,ach)}%"></div></div><span class="mut">${ach}%</span></div>`}</td>
        <td style="color:var(--ok)">${fmtMoney(r.credit)}</td>
        <td style="color:var(--danger)">${fmtMoney(r.debit)}</td>
        <td><b style="color:${r.balance>=0?"var(--ok)":"var(--danger)"}">${fmtMoney(r.balance)}</b></td></tr>`;}).join("")
        ||`<tr><td colspan="9"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  if(document.getElementById("ap")){
    ap.onclick=()=>partnerForm(null);
    acc.onclick=async()=>{const r=await api("/partners/accrue",{method:"POST"});
      toast(`${r.posted} · ${fmtMoney(r.total)}`);viewPartners();};}
  main.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=()=>openPartner(+tr.dataset.i));
}
async function partnerForm(p){
  const govs=await api("/geo/countries");
  const el=modal(p?t("edit"):t("addPartner"),`<form id="pf" class="f2">
    <div class="fld"><label>${t("name")} *</label><input name="name" value="${esc(p?.name||"")}" required></div>
    <div class="fld"><label>${t("type")||"Type"}</label><select name="type">
      ${Object.entries(PMETA.types).map(([k,v])=>`<option value="${k}" ${p?.type===k?"selected":""}>${v.icon} ${S.lang==="ar"?v.ar:v.en}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("phone")||"Phone"}</label><input name="phone" value="${esc(p?.phone||"")}"></div>
    <div class="fld"><label>${t("email")}</label><input name="email" value="${esc(p?.email||"")}"></div>
    <div class="fld"><label>${t("country")}</label><select name="gov_id" id="pg"><option value="0"></option>
      ${govs.map(g=>`<option value="${g.id}" ${String(p?.gov_id)===String(g.id)?"selected":""}>${esc(g.name_ar)}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("region")}</label><select name="district_id" id="pd"><option value="0"></option></select></div>
    <div class="fld"><label>${t("commModel")}</label><select name="commission_model" id="pm">
      ${Object.entries(PMETA.models).map(([k,v])=>`<option value="${k}" ${p?.commission_model===k?"selected":""}>${S.lang==="ar"?v.ar:v.en}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("rate")}</label><input name="commission_rate" type="number" step="0.1" value="${p?.commission_rate??3}"></div>
    <div class="fld"><label>${t("targetT")}</label><input name="target" type="number" value="${p?.target||0}"></div>
    <div class="fld"><label>${S.lang==="ar"?"سقف السلف":"Credit limit"}</label><input name="credit_limit" type="number" value="${p?.credit_limit||0}"></div>
    <div class="fld" style="grid-column:span 2"><label>${t("notes")||"Notes"}</label><textarea name="notes">${esc(p?.notes||"")}</textarea></div>
    <div class="mut" id="tierhint" style="grid-column:span 2;font-size:11.5px"></div>
  </form>`,[[t("cancel"),close_,""],[t("save"),async()=>{
    const fd=new FormData(el.querySelector("#pf"));const b={};fd.forEach((v,k)=>b[k]=v);
    b.gov_id=+b.gov_id;b.district_id=+b.district_id;b.commission_rate=+b.commission_rate;
    b.target=+b.target;b.credit_limit=+b.credit_limit;
    try{p?await api("/partners/"+p.id,{method:"PUT",body:JSON.stringify(b)})
        :await api("/partners",{method:"POST",body:JSON.stringify(b)});
      toast(t("saved"));close_();viewPartners();}catch{}},"pri"]]);
  const pg=el.querySelector("#pg"),pd=el.querySelector("#pd"),pm=el.querySelector("#pm");
  const loadD=async()=>{if(!+pg.value){pd.innerHTML="<option value=0></option>";return;}
    const ds=await api("/geo/regions?country_id="+pg.value);
    pd.innerHTML=`<option value="0"></option>`+ds.map(d=>`<option value="${d.id}" ${String(p?.district_id)===String(d.id)?"selected":""}>${esc(d.name_ar)}</option>`).join("");};
  pg.onchange=loadD; loadD();
  const hint=()=>el.querySelector("#tierhint").innerHTML = pm.value==="tiered"
    ? "📊 "+PMETA.default_tiers.map(x=>`${fmtNum(x.min)}+ → ${x.rate}%`).join(" · ") : "";
  pm.onchange=hint; hint();
}
async function openPartner(id){
  const p=await api("/partners/"+id);
  const st=await api(`/partners/${id}/statement`);
  const b=p.balance;
  const el=modal(`${(PMETA.types[p.type]||{}).icon||""} ${esc(p.name)}`,
   `<div class="kpis" style="margin-bottom:12px">
      <div class="kpi" style="--pri:var(--ok)"><div class="l">${t("revenue")}</div><div class="v" style="font-size:18px">${fmtMoney(p.sales)}</div></div>
      <div class="kpi" style="--pri:var(--ok)"><div class="l">${t("owedTo")}</div><div class="v" style="font-size:18px">${fmtMoney(b.credit)}</div></div>
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("owedBy")}</div><div class="v" style="font-size:18px">${fmtMoney(b.debit)}</div></div>
      <div class="kpi" style="--pri:${b.balance>=0?"var(--ok)":"var(--danger)"}"><div class="l">${t("netBal")}</div>
        <div class="v" style="font-size:18px">${fmtMoney(b.balance)}</div></div>
      <div class="kpi" style="--pri:var(--purple)"><div class="l">${t("achievement")}</div><div class="v" style="font-size:18px">${p.achievement==null?"—":p.achievement+"%"}</div></div>
      <div class="kpi" style="--pri:var(--info)"><div class="l">${t("rate")}</div><div class="v" style="font-size:18px">${p.current_rate}${p.commission_model==="flat"?"":"%"}</div></div></div>
    <div class="row" style="gap:8px;flex-wrap:wrap;margin-bottom:12px">
      <span class="mut" style="font-size:12px">📍 ${esc(p.gov_ar||"—")} ${p.dis_ar?"· "+esc(p.dis_ar):""}</span>
      <span class="mut" style="font-size:12px">📞 ${esc(p.phone||"—")}</span>
      <div class="spacer"></div>
      ${["admin","manager"].includes(S.user.role)?`<button class="btn sm" id="txn">+ ${t("addTxn")}</button>
      <button class="btn sm" id="edp">✎</button>`:""}</div>
    ${p.territories.length?`<div class="card" style="margin-bottom:10px"><b style="font-size:12.5px">${t("territoriesT")}</b>
      <div class="row" style="gap:6px;flex-wrap:wrap;margin-top:8px">
      ${p.territories.map(x=>`<span class="badge" style="color:var(--info);background:var(--info)22">
        ${esc(x.gov_ar||"")}${x.dis_ar?" / "+esc(x.dis_ar):""}${x.exclusive?" ⭐":""}</span>`).join("")}</div></div>`:""}
    ${p.stock.length?`<div class="card" style="margin-bottom:10px"><b style="font-size:12.5px">${t("consigned")}</b>
      <table class="tbl" style="margin-top:6px"><tbody>${p.stock.map(x=>`<tr><td>${esc(x.product||"—")}</td>
      <td class="mut">${t("consigned")} ${fmtNum(x.consigned)}</td><td style="color:var(--ok)">${t("sold")} ${fmtNum(x.sold)}</td>
      <td><b>${fmtNum(x.qty)}</b></td></tr>`).join("")}</tbody></table></div>`:""}
    <div class="card"><b style="font-size:12.5px">${t("statement")}</b>
      <div class="wrap-scroll" style="margin-top:8px;max-height:280px;overflow:auto"><table class="tbl"><thead><tr>
        <th>${t("date")||"Date"}</th><th>${t("type")||"Kind"}</th><th>${t("notes")||"Note"}</th>
        <th>${t("amount")||"Amount"}</th><th>${t("netBal")}</th></tr></thead><tbody>
      ${st.rows.map(r=>`<tr><td class="mut" style="font-size:11.5px">${(r.created_at||"").slice(0,10)}</td>
        <td><span class="badge" style="color:${r.signed>0?"var(--ok)":"var(--danger)"};background:${r.signed>0?"var(--ok)":"var(--danger)"}22">
          ${S.lang==="ar"?r.kind_ar:r.kind_en}</span></td>
        <td class="mut" style="font-size:11.5px">${esc((r.note||"").slice(0,44))}</td>
        <td><b style="color:${r.signed>0?"var(--ok)":"var(--danger)"}">${r.signed>0?"+":""}${fmtMoney(r.signed)}</b></td>
        <td class="mut">${fmtMoney(r.running)}</td></tr>`).join("")
        ||`<tr><td colspan="5"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`,[]);
  const tx=el.querySelector("#txn");
  if(tx)tx.onclick=()=>txnForm(id);
  const ed=el.querySelector("#edp");
  if(ed)ed.onclick=()=>{close_();partnerForm(p);};
}
function txnForm(aid){
  const el=modal(t("addTxn"),`<form id="tf">
    <div class="fld"><label>${t("type")||"Kind"}</label><select name="kind">
      ${Object.entries(PMETA.txn_kinds).map(([k,v])=>`<option value="${k}">${v.sign>0?"➕":"➖"} ${S.lang==="ar"?v.ar:v.en}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("amount")||"Amount"}</label><input name="amount" type="number" step="0.01" required></div>
    <div class="fld"><label>${t("notes")||"Note"}</label><input name="note"></div></form>`,
    [[t("cancel"),close_,""],[t("save"),async()=>{
      const fd=new FormData(el.querySelector("#tf"));const b={agent_id:aid};fd.forEach((v,k)=>b[k]=v);
      b.amount=+b.amount;
      try{await api("/partners/txn",{method:"POST",body:JSON.stringify(b)});
        toast(t("saved"));close_();close_();openPartner(aid);}catch{}},"pri"]]);
}

/* ---------- loyalty ---------- */
let loyTab="customer", LOYPROG=null;
async function viewLoyalty(){
  if(!LOYPROG)LOYPROG=await api("/loyalty/program");
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🏆 ${t("loyalty")}</div>
    <div class="spacer"></div>
    <button class="btn sm" id="prg">📖 ${t("programRules")}</button>
    ${["admin","manager"].includes(S.user.role)?`<button class="btn pri sm" id="rc">↻ ${t("recomputeL")}</button>`:""}</div>
    <div class="tabs" id="lt">
      <button data-t="customer" class="${loyTab==="customer"?"on":""}">👥 ${S.lang==="ar"?"العملاء":"Customers"}</button>
      <button data-t="partner" class="${loyTab==="partner"?"on":""}">🤝 ${t("partners")}</button>
    </div><div id="lc"><div class="empty">…</div></div>`;
  prg.onclick=showProgram;
  if(document.getElementById("rc"))rc.onclick=async()=>{
    await api("/loyalty/recompute?member_type="+loyTab,{method:"POST"});toast(t("saved"));viewLoyalty();};
  main.querySelectorAll("#lt button").forEach(b=>b.onclick=()=>{loyTab=b.dataset.t;viewLoyalty();});
  loyMembers();
}
function showProgram(){
  modal("📖 "+t("programRules"),
   `<b style="font-size:13px">${t("principles")}</b>
    <div style="margin:8px 0 16px">${LOYPROG.principles_ar.map(p=>`<div class="row" style="align-items:flex-start;padding:5px 0">
      <span style="color:var(--ok)">✔</span><span style="font-size:12.5px;margin-inline-start:6px">${esc(p)}</span></div>`).join("")}</div>
    <b style="font-size:13px">${t("tier")}</b>
    <div class="wrap-scroll" style="margin:8px 0 16px"><table class="tbl"><thead><tr><th>${t("tier")}</th>
      <th>${t("points")}</th><th>${t("discount")}</th><th>${t("perks")}</th></tr></thead><tbody>
      ${LOYPROG.tiers.map(x=>`<tr><td><span class="badge" style="color:${TC(x.color)};background:${TC(x.color)}22">${S.lang==="ar"?x.ar:x.en}</span></td>
        <td><b>${fmtNum(x.min)}+</b></td><td>${x.discount}%</td>
        <td class="mut" style="font-size:11.5px">${esc(x.perks_ar)}</td></tr>`).join("")}</tbody></table></div>
    <b style="font-size:13px">${t("programRules")}</b>
    <div style="margin-top:8px">${Object.entries(LOYPROG.rules).map(([k,v])=>`
      <div class="row" style="padding:7px 0;border-bottom:1px solid var(--line);font-size:12.5px">
      <b style="flex:1;color:${v.cap<0?"var(--danger)":"var(--txt)"}">${esc(v.ar)}</b>
      <span class="mut" style="flex:2">${esc(v.desc_ar)}</span>
      <span class="badge" style="color:${v.cap<0?"var(--danger)":"var(--info)"};background:${v.cap<0?"var(--danger)":"var(--info)"}22">
        ${v.cap<0?"":"≤ "}${fmtNum(Math.abs(v.cap))}</span></div>`).join("")}</div>
    <div class="mut" style="font-size:11.5px;margin-top:12px">⏳ ${S.lang==="ar"?
      "النقاط تنتهي بعد "+LOYPROG.expiry_months+" شهراً":"Points expire after "+LOYPROG.expiry_months+" months"}</div>`,[]);
}
async function loyMembers(){
  const d=await api("/loyalty/members?member_type="+loyTab);
  lc.innerHTML=`<div class="kpis" style="margin-bottom:14px">
      ${d.tiers.map(x=>`<div class="kpi" style="--pri:${TC(x.color)}"><div class="l">${S.lang==="ar"?x.ar:x.en}</div>
        <div class="v">${d.distribution[x.code]||0}</div></div>`).join("")}</div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${t("tier")}</th><th>${t("points")}</th><th>${t("available")}</th>
      <th>${t("penaltiesL")}</th><th>${t("discount")}</th><th></th></tr></thead><tbody>
      ${d.members.map(m=>`<tr data-i="${m.member_id}"><td><b>${esc(m.name)}</b></td>
        <td><span class="badge" style="color:${TC(m.color)};background:${TC(m.color)}22">${S.lang==="ar"?m.tier_ar:m.tier_en}</span></td>
        <td><div class="row"><div class="barbg" style="width:56px"><div class="barfill" style="width:${Math.min(100,m.points/5000*100)}%"></div></div>
          <b>${fmtNum(m.points)}</b></div></td>
        <td>${fmtNum(m.available)}</td>
        <td style="color:${m.penalties<0?"var(--danger)":"var(--mut)"}">${m.penalties?fmtNum(m.penalties):"—"}</td>
        <td>${m.discount}%</td>
        <td><button class="btn sm" data-v="${m.member_id}">📊</button></td></tr>`).join("")
        ||`<tr><td colspan="7"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  lc.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=()=>loyDetail(+tr.dataset.i));
}
async function loyDetail(mid){
  const m=await api(`/loyalty/member/${loyTab}/${mid}`);
  const el=modal(`🏆 ${esc(m.name)}`,
   `<div class="row" style="gap:12px;margin-bottom:14px;flex-wrap:wrap">
      <div class="kpi" style="--pri:${TC(m.tier.color)};flex:1"><div class="l">${t("tier")}</div>
        <div class="v" style="font-size:19px">${S.lang==="ar"?m.tier.ar:m.tier.en}</div></div>
      <div class="kpi" style="--pri:var(--pri);flex:1"><div class="l">${t("points")}</div><div class="v">${fmtNum(m.points)}</div></div>
      <div class="kpi" style="--pri:var(--ok);flex:1"><div class="l">${t("available")}</div><div class="v">${fmtNum(m.available)}</div></div>
      <div class="kpi" style="--pri:var(--warn);flex:1"><div class="l">${t("discount")}</div><div class="v">${m.tier.discount}%</div></div></div>
    <div class="card" style="margin-bottom:12px;font-size:12.5px">🎁 ${esc(m.tier.perks_ar)}</div>
    ${m.next?`<div class="card" style="margin-bottom:12px">
      <div class="row"><span style="font-size:12.5px">${t("nextTier")}:
        <b style="color:${TC(m.next.tier.color)}">${S.lang==="ar"?m.next.tier.ar:m.next.tier.en}</b></span>
        <div class="spacer"></div><span class="mut" style="font-size:12px">${fmtNum(m.next.gap)} ${t("points")}</span></div>
      <div class="barbg" style="margin-top:8px"><div class="barfill" style="width:${m.points/m.next.tier.min*100}%"></div></div></div>`:""}
    <b style="font-size:13px">${t("breakdown")}</b>
    <div class="wrap-scroll" style="margin-top:8px"><table class="tbl"><thead><tr>
      <th>${S.lang==="ar"?"القاعدة":"Rule"}</th><th>${S.lang==="ar"?"الأساس":"Basis"}</th><th>${t("points")}</th></tr></thead><tbody>
      ${m.breakdown.map(r=>`<tr><td><b>${esc(S.lang==="ar"?r.label_ar:r.label_en)}</b>
        <div class="mut" style="font-size:11px">${esc(r.desc_ar)}</div></td>
        <td class="mut">${esc(r.basis)}</td>
        <td><b style="color:${r.points<0?"var(--danger)":r.points>0?"var(--ok)":"var(--mut)"}">
          ${r.points>0?"+":""}${fmtNum(r.points)}</b></td></tr>`).join("")}
      </tbody></table></div>
    ${S.user.role!=="readonly"?`<button class="btn pri sm" style="margin-top:12px" id="rd">🎁 ${t("redeem")}</button>`:""}
    ${m.redemptions.length?`<div style="margin-top:12px"><b style="font-size:12.5px">${t("redeem")}</b>
      ${m.redemptions.map(r=>`<div class="row" style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px">
      <span style="flex:1">${esc(r.reward)}</span><b>−${fmtNum(r.points)}</b>
      <span class="mut">${(r.created_at||"").slice(0,10)}</span></div>`).join("")}</div>`:""}`,[]);
  const rd=el.querySelector("#rd");
  if(rd)rd.onclick=()=>{
    const el2=modal(t("redeem"),`<form id="rf2">
      <div class="fld"><label>${t("reward")}</label><input name="reward" required placeholder="${S.lang==="ar"?"خصم على الفاتورة القادمة":"Discount on next invoice"}"></div>
      <div class="fld"><label>${t("points")} (${t("available")}: ${fmtNum(m.available)})</label>
        <input name="points" type="number" max="${m.available}" required></div>
      <div class="fld"><label>${S.lang==="ar"?"القيمة":"Value"}</label><input name="value" type="number"></div></form>`,
      [[t("cancel"),close_,""],[t("save"),async()=>{
        const fd=new FormData(el2.querySelector("#rf2"));const b={member_type:loyTab,member_id:mid};
        fd.forEach((v,k)=>b[k]=v); b.points=+b.points; b.value=+b.value||0;
        try{await api("/loyalty/redeem",{method:"POST",body:JSON.stringify(b)});
          toast(t("saved"));close_();close_();loyDetail(mid);}catch{}},"pri"]]);};
}

/* ---------- partner portal admin ---------- */
let apTab="access";
async function viewAgentPortal(){
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🔑 ${t("agentPortal")}</div>
    <div class="spacer"></div><a class="btn sm" href="/agent" target="_blank">↗ ${t("openAgent")}</a>
    <button class="btn pri sm" id="ga">+ ${t("grantAgent")}</button></div>
    <div class="tabs" id="apt">
      <button data-t="access" class="${apTab==="access"?"on":""}">🔑 ${t("users")}</button>
      <button data-t="reqs" class="${apTab==="reqs"?"on":""}">📨 ${t("agentReqs")}</button>
    </div><div id="apc"><div class="empty">…</div></div>`;
  ga.onclick=grantAgentForm;
  main.querySelectorAll("#apt button").forEach(b=>b.onclick=()=>{apTab=b.dataset.t;viewAgentPortal();});
  apTab==="access"?apAccess():apReqs();
}
async function apAccess(){
  const rows=await api("/agent-access");
  apc.innerHTML=`<div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
    <th>${t("name")}</th><th>${t("type")||"Type"}</th><th>${t("email")}</th><th>${t("lastLogin")}</th>
    <th>${t("active")}</th><th></th></tr></thead><tbody>
    ${rows.map(r=>`<tr><td><b>${esc(r.aname||"—")}</b></td><td class="mut">${esc(r.type||"")}</td>
      <td class="mut">${esc(r.email)}</td><td class="mut">${(r.last_login||"—").replace("T"," ")}</td>
      <td>${r.active?'<span class="dot" style="background:var(--ok)"></span>':'<span class="dot" style="background:var(--danger)"></span>'}</td>
      <td><button class="btn sm" data-tg="${r.id}" data-a="${r.active}">${r.active?"⏸":"▶"}</button>
        <button class="btn sm" data-rp="${r.id}">🔑</button>
        ${S.user.role==="admin"?`<button class="btn sm dgr" data-rv="${r.id}">✕</button>`:""}</td></tr>`).join("")
      ||`<tr><td colspan="6"><div class="empty">${t("noData")}</div></td></tr>`}
    </tbody></table></div></div>`;
  apc.querySelectorAll("[data-tg]").forEach(b=>b.onclick=async()=>{
    await api(`/agent-access/${b.dataset.tg}`,{method:"PUT",body:JSON.stringify({active:b.dataset.a=="1"?0:1})});
    toast(t("saved"));apAccess();});
  apc.querySelectorAll("[data-rp]").forEach(b=>b.onclick=async()=>{
    const pw=prompt(t("resetPw"),"agent123"); if(!pw)return;
    await api(`/agent-access/${b.dataset.rp}`,{method:"PUT",body:JSON.stringify({password:pw})});
    toast(t("saved")+" · "+pw);});
  apc.querySelectorAll("[data-rv]").forEach(b=>b.onclick=async()=>{
    if(!confirm(t("confirmDel")))return;
    await api(`/agent-access/${b.dataset.rv}`,{method:"DELETE"});toast(t("deleted"));apAccess();});
}
async function grantAgentForm(){
  const ps=await api("/partners");
  const el=modal(t("grantAgent"),`<form id="gaf">
    <div class="fld"><label>${t("partners")}</label><select name="agent_id" id="gas">
      ${ps.map(p=>`<option value="${p.id}" data-e="${esc(p.email||"")}">${esc(p.name)} — ${esc(p.type)}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("email")}</label><input name="email" id="gae"></div>
    <div class="fld"><label>${t("password")}</label><input name="password" value="agent123"></div></form>`,
    [[t("cancel"),close_,""],[t("save"),async()=>{
      const fd=new FormData(el.querySelector("#gaf"));const b={};fd.forEach((v,k)=>b[k]=v);
      b.agent_id=+b.agent_id;
      try{const r=await api("/agent-access",{method:"POST",body:JSON.stringify(b)});
        close_();alert(`${t("credsMsg")}:\n${r.email}\n${r.password}`);apAccess();}catch{}},"pri"]]);
  const gs=el.querySelector("#gas"),ge=el.querySelector("#gae");
  const sync=()=>ge.value=gs.selectedOptions[0].dataset.e||"";
  gs.onchange=sync;sync();
}
async function apReqs(){
  const rs=await api("/agent-requests");
  const sc=v=>({pending:"var(--warn)",approved:"var(--ok)",rejected:"var(--danger)"}[v]||"var(--mut)");
  apc.innerHTML=`<div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
    <th>${t("date")||"Date"}</th><th>${t("partners")}</th><th>${t("requestKind")}</th><th>${t("subj")}</th>
    <th>${t("amount")||"Amount"}</th><th>Status</th><th></th></tr></thead><tbody>
    ${rs.map(r=>`<tr><td class="mut" style="font-size:11.5px">${(r.created_at||"").slice(0,10)}</td>
      <td><b>${esc(r.aname||"—")}</b></td><td>${esc(r.kind)}</td>
      <td class="mut">${esc(r.subject||"—")}</td><td>${r.amount?fmtMoney(r.amount):"—"}</td>
      <td><span class="badge" style="color:${sc(r.status)};background:${sc(r.status)}22">${r.status}</span>
        ${r.reply?`<div class="mut" style="font-size:10.5px">${esc(r.reply.slice(0,40))}</div>`:""}</td>
      <td>${r.status==="pending"&&["admin","manager"].includes(S.user.role)?
        `<button class="btn sm" data-ok="${r.id}" style="color:var(--ok);border-color:var(--ok)55">✓</button>
         <button class="btn sm dgr" data-no="${r.id}">✕</button>`:""}</td></tr>`).join("")
      ||`<tr><td colspan="7"><div class="empty">${t("noData")}</div></td></tr>`}
    </tbody></table></div></div>`;
  const decide=async(id,d)=>{const reply=prompt(t("replyR"),"")??"";
    try{await api(`/agent-requests/${id}/decide`,{method:"POST",
      body:JSON.stringify({decision:d,reply})});toast(t("saved"));apReqs();}catch{}};
  apc.querySelectorAll("[data-ok]").forEach(b=>b.onclick=()=>decide(b.dataset.ok,"approved"));
  apc.querySelectorAll("[data-no]").forEach(b=>b.onclick=()=>decide(b.dataset.no,"rejected"));
}

/* ================= AI ================= */
let aiTab="digest", AISTAT=null;
async function viewAI(){
  if(!AISTAT)AISTAT=await api("/ai/status");
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🤖 ${t("ai")}</div>
    <span class="badge" style="color:${AISTAT.llm?"var(--ok)":"var(--info)"};background:${AISTAT.llm?"var(--ok)":"var(--info)"}22">
      ${AISTAT.llm?t("aiOn"):t("aiOff")}</span><div class="spacer"></div></div>
    <div class="tabs" id="ait">
      <button data-t="digest" class="${aiTab==="digest"?"on":""}">☀️ ${t("digest")}</button>
      <button data-t="forecast" class="${aiTab==="forecast"?"on":""}">📈 ${t("forecast")}</button>
      <button data-t="leads" class="${aiTab==="leads"?"on":""}">🎯 ${t("leadScoring")}</button>
      <button data-t="pipeline" class="${aiTab==="pipeline"?"on":""}">💓 ${t("pipelineHealth")}</button>
      <button data-t="churn" class="${aiTab==="churn"?"on":""}">⚠️ ${t("churnRisk")}</button>
      <button data-t="tools" class="${aiTab==="tools"?"on":""}">✍️ ${t("genEmail")}</button>
    </div><div id="aic"><div class="empty">…</div></div>`;
  main.querySelectorAll("#ait button").forEach(b=>b.onclick=()=>{aiTab=b.dataset.t;viewAI();});
  ({digest:aiDigest,forecast:aiForecast,leads:aiLeads,pipeline:aiPipe,churn:aiChurn,tools:aiTools}[aiTab])();
}
async function aiDigest(){
  const d=await api("/ai/digest");
  const card=(t_,items,render,icon)=>`<div class="card"><b>${icon} ${t_}</b><div style="height:8px"></div>
    ${items.length?items.map(render).join(""):`<div class="mut" style="font-size:12.5px">${t("noData")}</div>`}</div>`;
  aic.innerHTML=`<div class="kpis" style="margin-bottom:14px">
      <div class="kpi" style="--pri:var(--pri)"><div class="l">${t("pipeline")}</div><div class="v">${fmtMoney(d.weighted_pipeline)}</div></div>
      ${d.forecast_month?`<div class="kpi" style="--pri:var(--ok)"><div class="l">${t("forecast")}</div>
        <div class="v">${fmtMoney(d.forecast_month.forecast)}</div></div>`:""}
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("overdueTasks")}</div><div class="v">${d.overdue_tasks.length}</div></div>
      <div class="kpi" style="--pri:var(--warn)"><div class="l">${t("atRisk")}</div><div class="v">${d.deals_at_risk.length}</div></div></div>
    <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(320px,1fr))">
    ${card(t("overdueTasks"),d.overdue_tasks,x=>`<div class="row" style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px">
      <span style="flex:1">${esc(x.subject)}</span><span class="badge" style="color:var(--danger);background:var(--danger)22">${x.due_date||""}</span></div>`,"🔴")}
    ${card(t("todayTasks"),d.today_tasks,x=>`<div class="row" style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px">
      <span style="flex:1">${esc(x.subject)}</span>${badge(x.priority)}</div>`,"📅")}
    ${card(t("hotLeads"),d.hot_leads,x=>`<div class="row" style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px;cursor:pointer" data-l="${x.id}">
      <span style="flex:1">${esc(x.name)}</span><div class="barbg" style="width:44px"><div class="barfill" style="width:${x.score}%"></div></div>
      <b>${x.score}</b></div>`,"🔥")}
    ${card(t("closingSoon"),d.closing_soon,x=>`<div class="row" style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px;cursor:pointer" data-d="${x.id}">
      <span style="flex:1">${esc(x.name)}</span><b>${fmtMoney(x.amount)}</b>
      <span class="badge" style="color:var(--ok);background:var(--ok)22">${x.probability}%</span></div>`,"🎯")}
    ${card(t("atRisk"),d.deals_at_risk,x=>`<div style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px;cursor:pointer" data-d="${x.id}">
      <div class="row"><span style="flex:1">${esc(x.name)}</span><b>${fmtMoney(x.amount)}</b></div>
      <div class="mut" style="font-size:11px">${esc((x.risks||[]).join(" · "))}</div></div>`,"⚠️")}
    ${card(t("churnRisk"),d.churn_risk,x=>`<div style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px;cursor:pointer" data-a="${x.id}">
      <div class="row"><span style="flex:1">${esc(x.name)}</span>
        <span class="badge" style="color:var(--danger);background:var(--danger)22">${x.risk}</span></div>
      <div class="mut" style="font-size:11px">${esc((x.reasons||[]).join(" · "))}</div></div>`,"💔")}
    </div>`;
  aic.querySelectorAll("[data-d]").forEach(e=>e.onclick=()=>openRecord("deals",+e.dataset.d));
  aic.querySelectorAll("[data-l]").forEach(e=>e.onclick=()=>openRecord("leads",+e.dataset.l));
  aic.querySelectorAll("[data-a]").forEach(e=>e.onclick=()=>open360("accounts",+e.dataset.a));
}
async function aiForecast(){
  const f=await api("/ai/forecast?months=3");
  const all=[...f.history.map(h=>({k:h.k,v:h.v,hist:true})),...f.forecast.map(x=>({k:x.month,v:x.forecast,lo:x.low,hi:x.high}))];
  const mx=Math.max(...all.map(a=>a.v||0),1);
  aic.innerHTML=`<div class="kpis" style="margin-bottom:14px">
      <div class="kpi" style="--pri:var(--ok)"><div class="l">${t("forecast")} (3م)</div><div class="v">${fmtMoney(f.total_forecast)}</div></div>
      <div class="kpi" style="--pri:var(--warn)"><div class="l">${t("committed")}</div><div class="v">${fmtMoney(f.committed)}</div></div>
      <div class="kpi" style="--pri:var(--purple)"><div class="l">${t("quota")}</div><div class="v">${fmtMoney(f.quota)}</div></div></div>
    <div class="card" style="margin-bottom:14px"><b>${t("monthly")} · ${t("forecast")}</b><div style="height:10px"></div>
      <div class="bars">${all.map(a=>`<div class="bar"><div>${esc(a.k)}${a.hist?"":" 🔮"}</div>
        <div class="barbg"><div class="barfill" style="width:${(a.v||0)/mx*100}%;${a.hist?"":"opacity:.65;background:linear-gradient(90deg,var(--warn),var(--purple))"}"></div></div>
        <div style="text-align:end;font-weight:700">${fmtMoney(a.v)}</div></div>`).join("")}</div></div>
    <div class="card"><b>${t("forecast")}</b><div class="wrap-scroll" style="margin-top:8px"><table class="tbl"><thead><tr>
      <th>${t("month")||"Month"}</th><th>${t("pipeline")}</th><th>${t("deals")||"Deals"}</th>
      <th>${t("low")}</th><th>${t("forecast")}</th><th>${t("high")}</th></tr></thead><tbody>
      ${f.forecast.map(x=>`<tr><td><b>${esc(x.month)}</b></td><td>${fmtMoney(x.weighted_pipeline)}</td>
        <td>${x.deals}</td><td class="mut">${fmtMoney(x.low)}</td>
        <td><b style="color:var(--ok)">${fmtMoney(x.forecast)}</b></td>
        <td class="mut">${fmtMoney(x.high)}</td></tr>`).join("")}</tbody></table></div>
      <div class="mut" style="font-size:11.5px;margin-top:10px">🔮 ${S.lang==="ar"
        ?"التنبؤ مزيج من المسار المرجّح باحتمالات الفوز واتجاه المبيعات التاريخي.":
         "Forecast blends probability-weighted pipeline with the historical trend."}</div></div>`;
}
async function aiLeads(){
  const d=await api("/ai/lead-scores");
  const bc=x=>({Hot:"var(--danger)",Warm:"var(--warn)",Cool:"var(--info)",Cold:"var(--mut)"}[x]||"var(--mut)");
  aic.innerHTML=`<div class="kpis" style="margin-bottom:14px">
      ${["Hot","Warm","Cool","Cold"].map(b=>`<div class="kpi" style="--pri:${bc(b)}">
        <div class="l">${b}</div><div class="v">${d.distribution[b]||0}</div></div>`).join("")}</div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${S.lang==="ar"?"الشركة":"Company"}</th><th>${t("readiness")}</th>
      <th>${t("status")||"Status"}</th><th>${S.lang==="ar"?"أهم عامل":"Top factor"}</th></tr></thead><tbody>
      ${d.leads.map(l=>`<tr data-i="${l.id}"><td><b>${esc(l.name)}</b></td><td class="mut">${esc(l.company||"—")}</td>
        <td><div class="row"><div class="barbg" style="width:60px"><div class="barfill" style="width:${l.score}%"></div></div>
          <b>${l.score}</b><span class="badge" style="color:${bc(l.band)};background:${bc(l.band)}22">${l.band_ar}</span></div></td>
        <td>${badge(l.status)}</td><td class="mut" style="font-size:11.5px">${esc(l.top_factor)}</td></tr>`).join("")}
      </tbody></table></div></div>`;
  aic.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=()=>openRecord("leads",+tr.dataset.i));
}
async function aiPipe(){
  const d=await api("/ai/pipeline-health");
  const bc=x=>({High:"var(--ok)",Medium:"var(--warn)",Low:"var(--danger)"}[x]||"var(--mut)");
  aic.innerHTML=`<div class="kpis" style="margin-bottom:14px">
      <div class="kpi" style="--pri:var(--pri)"><div class="l">${t("expected")}</div><div class="v">${fmtMoney(d.weighted_total)}</div></div>
      <div class="kpi" style="--pri:var(--info)"><div class="l">${t("openDeals")}</div><div class="v">${d.count}</div></div>
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("atRisk")}</div><div class="v">${fmtMoney(d.at_risk_value)}</div></div></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${t("stage")||"Stage"}</th><th>${t("amount")||"Amount"}</th>
      <th>${t("winProb")}</th><th>${t("expected")}</th><th>${S.lang==="ar"?"مخاطر":"Risks"}</th></tr></thead><tbody>
      ${d.deals.map(x=>`<tr data-i="${x.id}"><td><b>${esc(x.name)}</b></td><td>${badge(x.stage)}</td>
        <td>${fmtMoney(x.amount)}</td>
        <td><div class="row"><div class="barbg" style="width:52px"><div class="barfill" style="width:${x.probability}%"></div></div>
          <b style="color:${bc(x.band)}">${x.probability}%</b></div></td>
        <td><b>${fmtMoney(x.expected)}</b></td>
        <td class="mut" style="font-size:11px">${esc((x.risks||[]).join(" · "))||"—"}</td></tr>`).join("")}
      </tbody></table></div></div>`;
  aic.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=()=>openRecord("deals",+tr.dataset.i));
}
async function aiChurn(){
  const d=await api("/ai/churn-risk");
  const bc=x=>({Critical:"var(--danger)",High:"var(--warn)",Medium:"var(--info)"}[x]||"var(--mut)");
  aic.innerHTML=`<div class="kpi" style="--pri:var(--danger);margin-bottom:14px">
      <div class="l">${S.lang==="ar"?"إيرادات معرضة للفقد":"Revenue at risk"}</div>
      <div class="v">${fmtMoney(d.total_at_risk)}</div></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("name")}</th><th>${S.lang==="ar"?"درجة الخطر":"Risk"}</th><th>${t("revenue")}</th>
      <th>${S.lang==="ar"?"الأسباب":"Reasons"}</th></tr></thead><tbody>
      ${d.accounts.map(a=>`<tr data-i="${a.id}"><td><b>${esc(a.name)}</b></td>
        <td><div class="row"><div class="barbg" style="width:52px"><div class="barfill" style="width:${a.risk}%;background:${bc(a.band)}"></div></div>
          <span class="badge" style="color:${bc(a.band)};background:${bc(a.band)}22">${a.risk}</span></div></td>
        <td>${fmtMoney(a.revenue_at_risk)}</td>
        <td class="mut" style="font-size:11.5px">${esc(a.reasons.join(" · "))}</td></tr>`).join("")
        ||`<tr><td colspan="4"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>`;
  aic.querySelectorAll("tr[data-i]").forEach(tr=>tr.onclick=()=>open360("accounts",+tr.dataset.i));
}
function aiTools(){
  aic.innerHTML=`<div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(340px,1fr))">
    <div class="card"><b>✍️ ${t("genEmail")}</b><div style="height:10px"></div>
      <div class="fld"><label>${S.lang==="ar"?"النوع":"Type"}</label><select id="gk">
        <option value="intro">${S.lang==="ar"?"تعارف":"Intro"}</option>
        <option value="followup">${S.lang==="ar"?"متابعة":"Follow-up"}</option>
        <option value="proposal">${S.lang==="ar"?"عرض":"Proposal"}</option>
        <option value="winback">${S.lang==="ar"?"استرجاع":"Win-back"}</option>
        <option value="overdue">${S.lang==="ar"?"تذكير فاتورة":"Overdue"}</option>
        <option value="thanks">${S.lang==="ar"?"شكر":"Thanks"}</option></select></div>
      <div class="fld"><label>${t("name")}</label><input id="gn"></div>
      <button class="btn pri sm" id="gg">${t("generate")}</button>
      <div id="gout" style="margin-top:12px"></div></div>
    <div class="card"><b>📝 ${t("summarize")}</b><div style="height:10px"></div>
      <div class="fld"><label>${t("meetingNotes")}</label><textarea id="sx" style="min-height:170px"
        placeholder="${S.lang==="ar"?"الصق ملاحظات الاجتماع هنا...":"Paste meeting notes..."}"></textarea></div>
      <button class="btn pri sm" id="sg">${t("summarize")}</button>
      <div id="sout" style="margin-top:12px"></div></div></div>`;
  gg.onclick=async()=>{gout.innerHTML='<div class="mut">…</div>';
    const r=await api("/ai/generate-email",{method:"POST",
      body:JSON.stringify({kind:gk.value,extra:{name:gn.value}})});
    gout.innerHTML=`<div class="card" style="background:var(--bg2)">
      <b style="font-size:12.5px">${esc(r.subject)}</b>
      <div style="white-space:pre-wrap;font-size:12.5px;margin-top:8px">${esc(r.body)}</div>
      <div class="row" style="margin-top:10px"><span class="badge" style="color:var(--info);background:var(--info)22">${r.source}</span>
        <div class="spacer"></div><button class="btn sm" id="cpy">${t("copy")}</button></div></div>`;
    document.getElementById("cpy").onclick=()=>copyTxt(r.body);};
  sg.onclick=async()=>{if(!sx.value.trim())return;sout.innerHTML='<div class="mut">…</div>';
    const r=await api("/ai/summarize",{method:"POST",body:JSON.stringify({text:sx.value})});
    sout.innerHTML=`<div class="card" style="background:var(--bg2)">
      <div style="white-space:pre-wrap;font-size:12.5px">${esc(r.summary)}</div>
      ${(r.actions||[]).length?`<div style="margin-top:10px"><b style="font-size:12px">${t("actionItems")}</b>
        ${r.actions.map(a=>`<div style="font-size:12px;padding:3px 0">☑ ${esc(a)}</div>`).join("")}</div>`:""}
      <span class="badge" style="color:var(--info);background:var(--info)22;margin-top:8px;display:inline-block">${r.source}</span></div>`;};
}

/* ================= 360 view ================= */
async function open360(module,rid){
  const d=await api(`/360/${module}/${rid}`);
  const k=d.kpi||{};
  const CH=d.channels||{};
  const tl=d.timeline||[];
  const el=modal(`🔎 ${esc(d.record.name||d.record.subject||"#"+rid)} — ${t("view360")}`,
   `<div class="kpis" style="margin-bottom:12px">
      <div class="kpi" style="--pri:var(--ok)"><div class="l">${t("revenue")}</div><div class="v" style="font-size:17px">${fmtMoney(k.revenue)}</div></div>
      <div class="kpi" style="--pri:var(--danger)"><div class="l">${t("outstandingP")}</div><div class="v" style="font-size:17px">${fmtMoney(k.outstanding)}</div></div>
      <div class="kpi" style="--pri:var(--info)"><div class="l">${t("deals")||"Deals"}</div><div class="v" style="font-size:17px">${k.deals||0}</div></div>
      <div class="kpi" style="--pri:var(--warn)"><div class="l">${t("openTickets")}</div><div class="v" style="font-size:17px">${k.open_tickets||0}</div></div>
      ${k.loyalty_tier?`<div class="kpi" style="--pri:${TC(k.loyalty_tier.color)}"><div class="l">${t("loyalty")}</div>
        <div class="v" style="font-size:17px">${S.lang==="ar"?k.loyalty_tier.ar:k.loyalty_tier.en}</div></div>`:""}</div>
    ${d.ai&&d.ai.actions&&d.ai.actions.length?`<div class="card" style="margin-bottom:12px;border-inline-start:3px solid var(--pri)">
      <b style="font-size:12.5px">🤖 ${t("nba")}</b>
      ${d.ai.actions.slice(0,4).map(a=>`<div style="padding:6px 0;border-bottom:1px solid var(--line);font-size:12.5px">
        <div class="row"><span class="badge" style="color:${a.priority===1?"var(--danger)":a.priority===2?"var(--warn)":"var(--mut)"};
          background:${a.priority===1?"var(--danger)":a.priority===2?"var(--warn)":"var(--mut)"}22">P${a.priority}</span>
          <span style="flex:1">${esc(S.lang==="ar"?a.ar:a.en)}</span></div>
        <div class="mut" style="font-size:11px">${esc(a.why_ar||"")}</div></div>`).join("")}</div>`:""}
    <div class="row" style="gap:6px;flex-wrap:wrap;margin-bottom:10px">
      ${Object.entries(d.channel_counts||{}).map(([c,n])=>`<span class="badge"
        style="color:var(--info);background:var(--info)22">${(CH[c]||{}).icon||""} ${esc((CH[c]||{}).ar||c)} ${n}</span>`).join("")}</div>
    <div class="tabs" id="t360">
      <button data-t="tl" class="on">🕒 ${t("timeline")}</button>
      <button data-t="deals">💰 ${t("deals")||"Deals"}</button>
      <button data-t="fin">🧾 ${S.lang==="ar"?"المالية":"Financials"}</button>
      <button data-t="people">👥 ${S.lang==="ar"?"الأشخاص":"People"}</button>
      <button data-t="sup">🎫 ${S.lang==="ar"?"الدعم":"Support"}</button>
    </div><div id="c360"></div>`,[]);
  const c=el.querySelector("#c360");
  const rows=(arr,cols,head)=>arr&&arr.length?`<div class="wrap-scroll"><table class="tbl"><thead><tr>
    ${head.map(h=>`<th>${h}</th>`).join("")}</tr></thead><tbody>
    ${arr.map(r=>`<tr>${cols.map(fn=>`<td>${fn(r)}</td>`).join("")}</tr>`).join("")}</tbody></table></div>`
    :`<div class="empty">${t("noData")}</div>`;
  const P={
    tl:()=>`<div style="max-height:400px;overflow:auto">${tl.map(x=>{
      const ch=CH[x.channel]||{};
      return `<div class="row" style="align-items:flex-start;padding:9px 0;border-bottom:1px solid var(--line)">
        <span style="font-size:16px">${ch.icon||"•"}</span>
        <div style="flex:1;min-width:0;margin-inline-start:8px">
          <div class="row"><b style="font-size:12.5px">${esc(x.subject||ch.ar||"")}</b>
            <span class="badge" style="color:${x.direction==="in"?"var(--info)":"var(--ok)"};
              background:${x.direction==="in"?"var(--info)":"var(--ok)"}22;font-size:9.5px">
              ${x.direction==="in"?(S.lang==="ar"?"وارد":"in"):(S.lang==="ar"?"صادر":"out")}</span>
            <div class="spacer"></div><span class="mut" style="font-size:10.5px">${(x.occurred_at||"").replace("T"," ").slice(0,16)}</span></div>
          <div class="mut" style="font-size:11.5px;white-space:pre-wrap;max-height:40px;overflow:hidden">${esc((x.body||"").slice(0,160))}</div>
          ${x.actor?`<div class="mut" style="font-size:10.5px">— ${esc(x.actor)}</div>`:""}</div></div>`;}).join("")
      ||`<div class="empty">${t("noData")}</div>`}</div>
      ${S.user.role!=="readonly"?`<button class="btn sm" id="addint" style="margin-top:10px">+ ${S.lang==="ar"?"تسجيل تفاعل":"Log interaction"}</button>`:""}`,
    deals:()=>rows(d.deals,[r=>`<b>${esc(r.name)}</b>`,r=>badge(r.stage),r=>fmtMoney(r.amount),
        r=>r.probability+"%",r=>`<span class="mut">${r.closing_date||"—"}</span>`],
        [t("name"),t("stage")||"Stage",t("amount")||"Amount","%",t("closing")||"Close"])
      +(d.opportunities&&d.opportunities.length?`<div style="height:10px"></div><b style="font-size:12.5px">🌱 ${t("opps")}</b>`
        +rows(d.opportunities,[r=>esc(r.name),r=>badge(r.stage),r=>fmtMoney(r.value),r=>badge(r.outcome)],
        [t("name"),t("stage")||"Stage",t("amount")||"Value",t("outcome")||"Outcome"]):""),
    fin:()=>`<b style="font-size:12.5px">🧾 ${t("invoices")||"Invoices"}</b>`
      +rows(d.invoices,[r=>esc(r.subject),r=>badge(r.status),r=>fmtMoney(r.amount),
        r=>fmtMoney((r.amount||0)-(r.paid_amount||0)),r=>`<span class="mut">${r.due_date||"—"}</span>`],
        [t("subj"),t("status")||"Status",t("amount")||"Amount",t("remaining")||"Due",t("due")||"Date"])
      +`<div style="height:10px"></div><b style="font-size:12.5px">💳 ${t("payments")}</b>`
      +rows(d.payments,[r=>fmtMoney(r.amount),r=>esc(r.method||"—"),r=>badge(r.status),
        r=>`<span class="mut">${(r.paid_at||"").slice(0,10)}</span>`],
        [t("amount")||"Amount",t("method"),t("status")||"Status",t("date")||"Date"]),
    people:()=>rows(d.contacts,[r=>`<b>${esc(r.name)}</b>`,r=>esc(r.title||"—"),
        r=>esc(r.email||"—"),r=>esc(r.phone||"—")],[t("name"),"—",t("email"),t("phone")||"Phone"]),
    sup:()=>rows(d.tickets,[r=>esc(r.subject),r=>badge(r.status),r=>badge(r.priority),
        r=>`<span class="mut">${r.due_date||"—"}</span>`],
        [t("subj"),t("status")||"Status",t("priority")||"Priority",t("due")||"Due"]),
  };
  const draw=k2=>{c.innerHTML=P[k2]();
    const ai2=c.querySelector("#addint");
    if(ai2)ai2.onclick=()=>logInteraction(module,rid,d.account_id,()=>{close_();open360(module,rid);});};
  el.querySelectorAll("#t360 button").forEach(b=>b.onclick=()=>{
    el.querySelectorAll("#t360 button").forEach(z=>z.classList.remove("on"));
    b.classList.add("on");draw(b.dataset.t);});
  draw("tl");
}
function logInteraction(module,rid,aid,cb){
  const CH={email:"✉️ بريد",call:"📞 مكالمة",meeting:"🤝 اجتماع",whatsapp:"💬 واتساب",
    sms:"📱 رسالة",facebook:"📘 فيسبوك",instagram:"📸 إنستغرام",linkedin:"💼 لينكدإن",
    x:"✖️ X",web:"🌍 الموقع",note:"📝 ملاحظة"};
  const el=modal(S.lang==="ar"?"تسجيل تفاعل":"Log interaction",`<form id="itf">
    <div class="fld"><label>${t("channelsL")}</label><select name="channel">
      ${Object.entries(CH).map(([k,v])=>`<option value="${k}">${v}</option>`).join("")}</select></div>
    <div class="fld"><label>${S.lang==="ar"?"الاتجاه":"Direction"}</label><select name="direction">
      <option value="out">${S.lang==="ar"?"صادر":"Outbound"}</option>
      <option value="in">${S.lang==="ar"?"وارد":"Inbound"}</option></select></div>
    <div class="fld"><label>${t("subj")}</label><input name="subject"></div>
    <div class="fld"><label>${t("body")}</label><textarea name="body"></textarea></div></form>`,
    [[t("cancel"),close_,""],[t("save"),async()=>{
      const fd=new FormData(el.querySelector("#itf"));const b={module,record_id:rid,account_id:aid};
      fd.forEach((v,k)=>b[k]=v);
      await api("/interactions",{method:"POST",body:JSON.stringify(b)});
      toast(t("saved"));close_();if(cb)cb();},"pri"]]);
}

/* ================= dashboard builder ================= */
let curDash=[];
async function viewBuilder(){
  const saved=await api("/dashboards");
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🧱 ${t("builder")}</div>
    <div class="spacer"></div>
    <select id="dsel" style="background:var(--card);border:1px solid var(--line);border-radius:9px;padding:7px">
      <option value="">— ${S.lang==="ar"?"لوحة جديدة":"New dashboard"} —</option>
      ${saved.map(d=>`<option value="${d.id}">${esc(d.name)}</option>`).join("")}</select>
    <button class="btn sm" id="aw">+ ${t("addWidget")}</button>
    <button class="btn pri sm" id="sv">💾 ${t("saveDash")}</button></div>
    <div id="dgrid" class="grid" style="grid-template-columns:repeat(auto-fit,minmax(300px,1fr))"></div>`;
  aw.onclick=widgetForm;
  sv.onclick=async()=>{if(!curDash.length)return toast(t("noData"));
    const name=prompt(t("name"),"لوحتي"); if(!name)return;
    await api("/dashboards",{method:"POST",body:JSON.stringify({name,layout:curDash,shared:false})});
    toast(t("saved"));viewBuilder();};
  dsel.onchange=async()=>{const d=saved.find(x=>x.id==dsel.value);
    curDash=d?JSON.parse(d.layout):[];renderDash();};
  renderDash();
}
async function renderDash(){
  const g=document.getElementById("dgrid"); if(!g)return;
  if(!curDash.length){g.innerHTML=`<div class="empty">${S.lang==="ar"?"أضف عنصراً للبدء":"Add a widget to start"}</div>`;return;}
  g.innerHTML=curDash.map((w,i)=>`<div class="card" id="w${i}">
    <div class="row"><b style="flex:1;font-size:13px">${esc(w.title)}</b>
      <button class="btn sm dgr" data-x="${i}">✕</button></div>
    <div id="wb${i}" class="mut" style="margin-top:8px">…</div></div>`).join("");
  g.querySelectorAll("[data-x]").forEach(b=>b.onclick=()=>{curDash.splice(+b.dataset.x,1);renderDash();});
  curDash.forEach(async(w,i)=>{
    const qs=new URLSearchParams({module:w.module,metric:w.metric,field:w.field||"",
      group_by:w.group_by||"",filter_field:w.filter_field||"",filter_value:w.filter_value||""});
    try{const r=await api("/widget?"+qs);
      const el=document.getElementById("wb"+i); if(!el)return;
      const money=w.metric!=="count";
      if(r.rows){const mx=Math.max(...r.rows.map(x=>x.v||0),1);
        el.innerHTML=`<div class="bars">${r.rows.slice(0,10).map(x=>`<div class="bar">
          <div style="overflow:hidden;text-overflow:ellipsis">${esc(x.k)}</div>
          <div class="barbg"><div class="barfill" style="width:${(x.v||0)/mx*100}%"></div></div>
          <div style="text-align:end;font-weight:700">${money?fmtMoney(x.v):fmtNum(x.v)}</div></div>`).join("")}</div>`;}
      else el.innerHTML=`<div style="font-size:28px;font-weight:800;color:var(--pri)">${money?fmtMoney(r.value):fmtNum(r.value)}</div>`;
    }catch{}});
}
function widgetForm(){
  const mods=Object.entries(S.meta.modules);
  const el=modal(t("addWidget"),`<form id="wf2" class="f2">
    <div class="fld"><label>${t("name")}</label><input name="title" required></div>
    <div class="fld"><label>${t("module")}</label><select name="module" id="wm2">
      ${mods.map(([k,m])=>`<option value="${k}">${m.icon} ${L(m)}</option>`).join("")}</select></div>
    <div class="fld"><label>${t("metric")}</label><select name="metric" id="wmt">
      <option value="count">${t("count")}</option><option value="sum">${t("sum")}</option>
      <option value="avg">${t("avg")}</option></select></div>
    <div class="fld"><label>${t("field")}</label><select name="field" id="wfd2"></select></div>
    <div class="fld"><label>${t("groupBy")}</label><select name="group_by" id="wgb"><option value="">—</option></select></div>
  </form>`,[[t("cancel"),close_,""],[t("save"),()=>{
    const fd=new FormData(el.querySelector("#wf2"));const w={};fd.forEach((v,k)=>w[k]=v);
    curDash.push(w);close_();renderDash();},"pri"]]);
  const wm=el.querySelector("#wm2"),wf=el.querySelector("#wfd2"),wg=el.querySelector("#wgb");
  const fill=()=>{const m=S.meta.modules[wm.value];
    wf.innerHTML=m.fields.filter(f=>["number","currency"].includes(f.type))
      .map(f=>`<option value="${f.name}">${L(f)}</option>`).join("")||"<option value=''>—</option>";
    wg.innerHTML='<option value="">—</option>'+m.fields.filter(f=>["select","text","user","lookup","date"].includes(f.type))
      .map(f=>`<option value="${f.name}">${L(f)}</option>`).join("");};
  wm.onchange=fill;fill();
}

/* ================= integrations ================= */
async function viewIntegrations(){
  const d=await api("/integrations");
  const keys=S.user.role==="admin"?await api("/keys"):[];
  const byCat={};
  d.integrations.forEach(i=>{(byCat[i.cat]=byCat[i.cat]||[]).push(i);});
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🔌 ${t("integrations")}</div></div>
    ${Object.entries(byCat).map(([c,items])=>`
      <div class="mut" style="font-weight:700;font-size:11.5px;margin:14px 0 8px">
        ${S.lang==="ar"?(d.categories[c]||{}).ar:(d.categories[c]||{}).en}</div>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(270px,1fr))">
      ${items.map(i=>`<div class="card"><div class="row">
        <span style="font-size:20px">${i.icon}</span>
        <b style="flex:1;margin-inline-start:8px">${esc(S.lang==="ar"?i.name_ar:i.name_en)}</b>
        <span class="badge" style="color:${i.enabled||i.status==="active"?"var(--ok)":"var(--mut)"};
          background:${i.enabled||i.status==="active"?"var(--ok)":"var(--mut)"}22">
          ${i.enabled||i.status==="active"?"●":"○"}</span></div>
        <div class="mut" style="font-size:11.5px;margin:8px 0">${esc(i.desc_ar)}</div>
        ${i.webhook?`<div class="mut" style="font-size:10.5px">🔗 <code>${esc(i.webhook)}</code></div>`:""}
        <button class="btn sm" style="margin-top:8px;width:100%" data-i="${i.code}" data-e="${i.enabled?1:0}">
          ${i.enabled?t("disable"):t("enable")}</button></div>`).join("")}</div>`).join("")}
    ${S.user.role==="admin"?`<div class="mut" style="font-weight:700;font-size:11.5px;margin:18px 0 8px">${t("apiKeys")}</div>
      <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
        <th>${t("name")}</th><th>Prefix</th><th>${t("scopes")}</th><th>${t("runs")}</th>
        <th>${t("lastLogin")}</th><th></th></tr></thead><tbody>
        ${keys.map(k=>`<tr><td><b>${esc(k.name)}</b></td><td class="mut"><code>${esc(k.prefix)}…</code></td>
          <td>${badge(k.scopes)}</td><td>${k.calls}</td>
          <td class="mut">${(k.last_used||"—").replace("T"," ")}</td>
          <td><button class="btn sm dgr" data-k="${k.id}">✕</button></td></tr>`).join("")
          ||`<tr><td colspan="6"><div class="empty">${t("noData")}</div></td></tr>`}
        </tbody></table></div>
        <div style="padding:12px"><button class="btn pri sm" id="nk">+ ${t("newKey")}</button>
        <span class="mut" style="font-size:11.5px;margin-inline-start:10px">
          ${S.lang==="ar"?"استخدم الترويسة":"Use header"} <code>X-API-Key</code> ${S.lang==="ar"?"مع":"with"} <code>/api/v1/{module}</code></span></div></div>`:""}`;
  main.querySelectorAll("[data-i]").forEach(b=>b.onclick=async()=>{
    await api(`/integrations/${b.dataset.i}`,{method:"PUT",
      body:JSON.stringify({enabled:b.dataset.e!=="1"})});toast(t("saved"));viewIntegrations();});
  main.querySelectorAll("[data-k]").forEach(b=>b.onclick=async()=>{
    if(!confirm(t("confirmDel")))return;
    await api(`/keys/${b.dataset.k}`,{method:"DELETE"});toast(t("deleted"));viewIntegrations();});
  const nk=document.getElementById("nk");
  if(nk)nk.onclick=()=>{
    const el=modal(t("newKey"),`<form id="kf">
      <div class="fld"><label>${t("name")}</label><input name="name" required></div>
      <div class="fld"><label>${t("scopes")}</label><select name="scopes">
        <option value="read">read</option><option value="read,write">read + write</option></select></div></form>`,
      [[t("cancel"),close_,""],[t("save"),async()=>{
        const fd=new FormData(el.querySelector("#kf"));const b={};fd.forEach((v,k)=>b[k]=v);
        const r=await api("/keys",{method:"POST",body:JSON.stringify(b)});
        close_();modal(t("newKey"),`<div class="fld"><input value="${esc(r.key)}" readonly
          style="font-family:monospace;font-size:12px"></div>
          <div class="mut" style="font-size:12px;color:var(--warn)">⚠ ${esc(r.note)}</div>`,[]);
        viewIntegrations();},"pri"]]);};
}

/* ================= custom fields ================= */
async function viewCFields(){
  const d=await api("/custom-fields");
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">🏷️ ${t("customFields")}</div>
    <div class="spacer"></div><button class="btn pri sm" id="af2">+ ${t("addField")}</button></div>
    <div class="card" style="padding:0"><div class="wrap-scroll"><table class="tbl"><thead><tr>
      <th>${t("module")}</th><th>${t("fieldLabel")}</th><th>${t("field")}</th><th>${t("fieldType")}</th>
      <th>${t("showInList")}</th><th></th></tr></thead><tbody>
      ${d.fields.map(f=>`<tr><td>${S.meta.modules[f.module]?L(S.meta.modules[f.module]):f.module}</td>
        <td><b>${esc(f.label_ar)}</b></td><td class="mut"><code>${esc(f.name)}</code></td>
        <td>${badge((d.types[f.type]||{}).ar||f.type)}</td>
        <td>${f.show_in_list?"✓":"—"}</td>
        <td><button class="btn sm dgr" data-f="${f.id}">✕</button></td></tr>`).join("")
        ||`<tr><td colspan="6"><div class="empty">${t("noData")}</div></td></tr>`}
      </tbody></table></div></div>
      <div class="mut" style="font-size:11.5px;margin-top:10px">💡 ${S.lang==="ar"
        ?"الحقول المضافة تظهر تلقائياً في النماذج والقوائم والتقارير والبحث دون أي برمجة."
        :"Custom fields appear automatically across forms, lists, reports and search."}</div>`;
  af2.onclick=()=>{
    const mods=Object.entries(S.meta.modules);
    const el=modal(t("addField"),`<form id="cff" class="f2">
      <div class="fld"><label>${t("module")}</label><select name="module">
        ${mods.map(([k,m])=>`<option value="${k}">${m.icon} ${L(m)}</option>`).join("")}</select></div>
      <div class="fld"><label>${t("fieldType")}</label><select name="type">
        ${Object.entries(d.types).map(([k,v])=>`<option value="${k}">${S.lang==="ar"?v.ar:v.en}</option>`).join("")}</select></div>
      <div class="fld"><label>${t("fieldLabel")} (ع)</label><input name="label_ar" required></div>
      <div class="fld"><label>${t("fieldLabel")} (EN)</label><input name="label_en"></div>
      <div class="fld"><label>${S.lang==="ar"?"الاسم البرمجي":"Field key"}</label><input name="name" required placeholder="branch_code"></div>
      <div class="fld"><label>${S.lang==="ar"?"خيارات (مفصولة بفاصلة)":"Options (comma separated)"}</label><input name="options"></div>
      <label class="row" style="font-size:13px;grid-column:span 2"><input type="checkbox" name="show_in_list" style="width:auto">&nbsp;${t("showInList")}</label>
    </form>`,[[t("cancel"),close_,""],[t("save"),async()=>{
      const fd=new FormData(el.querySelector("#cff"));const b={};fd.forEach((v,k)=>b[k]=v);
      b.show_in_list=!!b.show_in_list;b.required=false;
      try{await api("/custom-fields",{method:"POST",body:JSON.stringify(b)});
        toast(t("saved"));close_();S.meta=await api("/meta");viewCFields();}catch{}},"pri"]]);};
  main.querySelectorAll("[data-f]").forEach(b=>b.onclick=async()=>{
    if(!confirm(t("confirmDel")))return;
    await api(`/custom-fields/${b.dataset.f}`,{method:"DELETE"});
    toast(t("deleted"));S.meta=await api("/meta");viewCFields();});
}

/* ================= report centre ================= */
let RC={cat:null,code:null,from:"",to:"",data:null};
async function viewReportCentre(){
  if(!RC.cat) RC.cat=await api("/reports/catalogue");
  if(RC.code) return rcRun();
  const byG={};
  RC.cat.reports.forEach(r=>{(byG[r.group]=byG[r.group]||[]).push(r);});
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">📑 ${t("reportCentre")}</div>
      <div class="spacer"></div><span class="mut">${RC.cat.reports.length} ${S.lang==="ar"?"تقرير":"reports"}</span></div>
    ${Object.entries(byG).map(([g,items])=>{const G=RC.cat.groups[g]||{};
      return `<div class="mut" style="font-weight:700;font-size:11.5px;margin:16px 0 8px">
        ${G.icon||""} ${S.lang==="ar"?G.ar:G.en}</div>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr))">
      ${items.map(r=>`<div class="card" style="cursor:pointer" data-r="${r.code}">
        <div class="row"><span style="font-size:19px">${r.icon}</span>
          <b style="flex:1;margin-inline-start:8px">${esc(S.lang==="ar"?r.ar:r.en)}</b></div>
        <div class="mut" style="font-size:11.5px;margin-top:6px;line-height:1.8">${esc(r.desc_ar)}</div>
        <div class="row" style="margin-top:9px;gap:5px">
          <span class="badge" style="color:var(--info);background:var(--info)22">${r.cols.length} ${S.lang==="ar"?"عمود":"cols"}</span>
          ${r.has_date?`<span class="badge" style="color:var(--warn);background:var(--warn)22">📅</span>`:""}
        </div></div>`).join("")}</div>`;}).join("")}`;
  main.querySelectorAll("[data-r]").forEach(c=>c.onclick=()=>{RC.code=c.dataset.r;rcRun();});
}
function rcQuick(kind){
  const d=new Date(), p=n=>String(n).padStart(2,"0");
  const y=d.getFullYear(), m=d.getMonth();
  if(kind==="tm"){RC.from=`${y}-${p(m+1)}-01`;RC.to=`${y}-${p(m+1)}-31`;}
  else if(kind==="lm"){const lm=m===0?11:m-1,ly=m===0?y-1:y;
    RC.from=`${ly}-${p(lm+1)}-01`;RC.to=`${ly}-${p(lm+1)}-31`;}
  else if(kind==="ty"){RC.from=`${y}-01-01`;RC.to=`${y}-12-31`;}
  else {RC.from="";RC.to="";}
  rcRun();
}
async function rcRun(){
  const meta=RC.cat.reports.find(r=>r.code===RC.code);
  main.innerHTML=`<div class="mut">…</div>`;
  const qs=new URLSearchParams({date_from:RC.from,date_to:RC.to});
  let d; try{ d=await api(`/reports/run/${RC.code}?`+qs); }catch{ RC.code=null; return viewReportCentre(); }
  RC.data=d;
  const fmt=(v,typ)=>{
    if(v==null||v==="") return "—";
    if(typ==="money") return fmtMoney(v);
    if(typ==="int") return fmtNum(v);
    if(typ==="pct") return (Math.round(v*10)/10)+"%";
    return esc(v);
  };
  const cols=meta.cols;
  const exportPath=f=>`/reports/export/${RC.code}.${f}?`+new URLSearchParams({date_from:RC.from,date_to:RC.to,lang:S.lang});
  main.innerHTML=`
    <div class="row no-print" style="margin-bottom:12px;flex-wrap:wrap;gap:8px">
      <button class="btn sm" id="rcBack">← ${t("backToList")}</button>
      <div class="h1" style="font-size:19px">${meta.icon} ${esc(S.lang==="ar"?meta.ar:meta.en)}</div>
      <div class="spacer"></div>
      <button class="btn sm" id="rcPrint">🖨 ${t("printR")}</button>
      <button class="btn sm" id="rcCsv">⬇ ${t("exportCsv")}</button>
      <button class="btn sm" id="rcXls">⬇ ${t("exportXls")}</button>
    </div>
    ${meta.has_date?`<div class="card no-print" style="margin-bottom:12px">
      <div class="row" style="flex-wrap:wrap;gap:10px;align-items:flex-end">
        <div class="fld" style="margin:0"><label>${t("dateFrom")}</label>
          <input type="date" id="rcFrom" value="${RC.from}"></div>
        <div class="fld" style="margin:0"><label>${t("dateTo")}</label>
          <input type="date" id="rcTo" value="${RC.to}"></div>
        <button class="btn pri sm" id="rcGo">${t("runReport")}</button>
        <div class="spacer"></div>
        <div class="row" style="gap:5px">
          <span class="mut" style="font-size:11px">${t("quickRange")}:</span>
          <button class="btn sm" data-q="tm">${t("thisMonth")}</button>
          <button class="btn sm" data-q="lm">${t("lastMonth")}</button>
          <button class="btn sm" data-q="ty">${t("thisYear")}</button>
          <button class="btn sm" data-q="all">${t("allTime")}</button>
        </div></div></div>`:""}

    <div class="card print-area">
      <div class="print-head" style="display:none">
        <div style="display:flex;justify-content:space-between;align-items:flex-start;
             border-bottom:2px solid #111;padding-bottom:10px;margin-bottom:14px">
          <div><b style="font-size:17px">${esc(S.meta.company||"NebrasCRM")}</b>
            <div style="font-size:12px">${esc(S.lang==="ar"?meta.ar:meta.en)}</div></div>
          <div style="text-align:end;font-size:11px">
            <div>${t("generatedAt")}: ${(d.generated_at||"").replace("T"," ")}</div>
            ${RC.from||RC.to?`<div>${RC.from||"—"} → ${RC.to||"—"}</div>`:""}
            <div>${d.count} ${t("records2")}</div></div></div></div>
      <div class="row no-print" style="margin-bottom:10px">
        <span class="mut" style="font-size:12px">${d.count} ${t("records2")}</span>
        <div class="spacer"></div>
        <span class="mut" style="font-size:11px">${t("generatedAt")}: ${(d.generated_at||"").replace("T"," ")}</span>
      </div>
      ${d.rows.length?`<div class="wrap-scroll"><table class="tbl rep-tbl"><thead><tr>
        ${cols.map(c=>`<th>${esc(S.lang==="ar"?c.ar:c.en)}</th>`).join("")}</tr></thead>
        <tbody>${d.rows.map(r=>`<tr>${cols.map(c=>
          `<td data-l="${esc(S.lang==="ar"?c.ar:c.en)}"${["money","int","pct"].includes(c.type)?' style="font-weight:600"':""}>${fmt(r[c.key],c.type)}</td>`).join("")}</tr>`).join("")}
        </tbody>
        ${Object.keys(d.totals).length?`<tfoot><tr style="border-top:2px solid var(--line2)">
          <td style="font-weight:800">${t("totalRow")}</td>
          ${cols.slice(1).map(c=>`<td style="font-weight:800">${d.totals[c.key]!==undefined?fmt(d.totals[c.key],c.type):""}</td>`).join("")}
        </tr></tfoot>`:""}
      </table></div>`:`<div class="empty">${t("noRows")}</div>`}
    </div>`;
  document.getElementById("rcBack").onclick=()=>{RC.code=null;RC.data=null;viewReportCentre();};
  document.getElementById("rcPrint").onclick=()=>printCurrentView();
  document.getElementById("rcCsv").onclick=()=>downloadApi(exportPath("csv"),`${RC.code}.csv`).catch(()=>{});
  document.getElementById("rcXls").onclick=()=>downloadApi(exportPath("xls"),`${RC.code}.xls`).catch(()=>{});
  const go=document.getElementById("rcGo");
  if(go){go.onclick=()=>{RC.from=document.getElementById("rcFrom").value;
    RC.to=document.getElementById("rcTo").value;rcRun();};
    main.querySelectorAll("[data-q]").forEach(b=>b.onclick=()=>rcQuick(b.dataset.q));}
}

/* ================= system settings ================= */
async function viewSysSettings(){
  const isAdmin=S.user.role==="admin";
  const [d,demo]=await Promise.all([
    api("/settings/all"),
    isAdmin?api("/admin/demo-data/summary"):Promise.resolve(null),
  ]);
  const byG={};
  d.settings.forEach(s2=>{(byG[s2.group]=byG[s2.group]||[]).push(s2);});
  const tx=S.lang==="ar"?{
    title:"إدارة البيانات التجريبية",addTitle:"إضافة بيانات تجريبية",addButton:"✨ إضافة بيانات تجريبية",
    addDesc:"يضيف حزمة بيانات جاهزة تشمل منتجات وعملاء وعروض أسعار وفواتير ومدفوعات وبيعاً تجريبياً في نقطة البيع.",
    addKeeps:"لن يستبدل بياناتك الحالية ولن يغيّر المستخدمين أو الإعدادات أو الخريطة العالمية.",
    addPhrase:"اكتب العبارة التالية للتأكيد",addConfirm:"إضافة البيانات التجريبية",addDone:"تمت إضافة البيانات التجريبية",already:"حزمة البيانات التجريبية موجودة بالفعل",
    deleteTitle:"حذف البيانات التجريبية",deleteButton:"🗑 حذف البيانات التجريبية",count:"سجل سيتم حذفه",
    deleteDesc:"سيتم حذف العملاء والعملاء المحتملون والصفقات والفواتير والمدفوعات والأنشطة والبيانات التجريبية المرتبطة بها.",
    keeps:"سيتم الإبقاء على حسابات المستخدمين والإعدادات وقوالب البريد والتخصيصات ومفاتيح API والتكاملات والخريطة العالمية.",
    warning:"هذه العملية لا يمكن التراجع عنها. لا تستخدمها إذا كانت قاعدة البيانات تحتوي على بيانات تشغيل حقيقية.",
    deletePhrase:"اكتب العبارة التالية للتأكيد",deleteConfirm:"تنفيذ الحذف النهائي",deleteDone:"تم حذف البيانات التجريبية بنجاح",present:"البيانات التجريبية موجودة",absent:"لا توجد حزمة بيانات تجريبية مضافة",
  }:{
    title:"Demo data management",addTitle:"Add demo data",addButton:"✨ Add demo data",
    addDesc:"Adds a ready-to-use pack of products, customers, quotes, invoices, payments and a sample POS sale.",
    addKeeps:"It does not overwrite current business data or change users, settings or global geography.",
    addPhrase:"Type the following phrase to confirm",addConfirm:"Add demo data",addDone:"Demo data was added",already:"The demo sample pack is already present",
    deleteTitle:"Delete demo data",deleteButton:"🗑 Delete demo data",count:"records will be deleted",
    deleteDesc:"This removes demo customers, leads, deals, invoices, payments, activities and their related business data.",
    keeps:"User accounts, settings, email templates, customizations, API keys, integrations and the global map are preserved.",
    warning:"This cannot be undone. Do not use it when the database contains real operating data.",
    deletePhrase:"Type the following phrase to confirm",deleteConfirm:"Delete permanently",deleteDone:"Demo data was deleted",present:"Demo data is present",absent:"No UI-added demo pack yet",
  };
  main.innerHTML=`<div class="row" style="margin-bottom:14px"><div class="h1">⚙️ ${t("settingsSys")}</div>
      <div class="spacer"></div>
      ${isAdmin?`<button class="btn pri sm" id="ssSave">💾 ${t("saveSettings")}</button>`:""}</div>
    <form id="ssForm">
    ${Object.entries(byG).map(([g,items])=>{const G=d.groups[g]||{};
      return `<div class="card" style="margin-bottom:12px">
        <b style="font-size:13px">${G.icon||""} ${S.lang==="ar"?G.ar:G.en}</b>
        <div class="f2" style="margin-top:10px">
        ${items.map(s2=>{
          const lbl=esc(S.lang==="ar"?s2.ar:s2.en);
          if(s2.type.startsWith("select:")){
            const opts=s2.type.slice(7).split(",");
            return `<div class="fld"><label>${lbl}</label><select name="${s2.key}">
              ${opts.map(o=>`<option value="${o}" ${String(s2.value)===o?"selected":""}>${
                o==="1"?(S.lang==="ar"?"نعم":"Yes"):o==="0"?(S.lang==="ar"?"لا":"No"):o}</option>`).join("")}
            </select></div>`;}
          const it=s2.type==="password"?"password":s2.type==="number"?"number":"text";
          return `<div class="fld"><label>${lbl}</label>
            <input type="${it}" name="${s2.key}" value="${esc(s2.value)}"></div>`;
        }).join("")}</div></div>`;}).join("")}
    </form>
    ${demo?`<section class="card" style="margin-top:16px;border:1px solid var(--line2);background:linear-gradient(135deg,var(--pri)08,transparent)">
      <div class="row" style="align-items:flex-start;gap:10px;margin-bottom:12px"><div style="font-size:22px">🧪</div><div style="flex:1"><b>${tx.title}</b>
        <div class="mut" style="font-size:11.5px;margin-top:3px">${demo.sample_pack_present?tx.present:tx.absent}</div></div>
        <span class="badge" style="color:var(--info);background:var(--info)22">${fmtNum(demo.total)} ${tx.count}</span></div>
      <div class="grid" style="grid-template-columns:repeat(auto-fit,minmax(280px,1fr));gap:10px">
        <div style="border:1px solid var(--ok);background:var(--ok)10;border-radius:12px;padding:13px"><div class="row" style="gap:9px;align-items:flex-start"><div style="font-size:20px">✨</div><div style="flex:1"><b>${tx.addTitle}</b>
          <div class="mut" style="font-size:12px;margin-top:4px">${tx.addDesc}</div><div class="mut" style="font-size:10.5px;margin-top:5px">${tx.addKeeps}</div></div></div>
          <button class="btn sm" id="addDemo" style="margin-top:11px;color:var(--ok);border-color:var(--ok)66">${tx.addButton}</button></div>
        <div style="border:1px solid var(--danger);background:var(--danger)10;border-radius:12px;padding:13px"><div class="row" style="gap:9px;align-items:flex-start"><div style="font-size:20px">⚠️</div><div style="flex:1"><b>${tx.deleteTitle}</b>
          <div class="mut" style="font-size:12px;margin-top:4px">${tx.deleteDesc}</div><div class="mut" style="font-size:10.5px;margin-top:5px">${tx.keeps}</div></div></div>
          <button class="btn dgr sm" id="clearDemo" style="margin-top:11px">${tx.deleteButton}</button></div>
      </div></section>`:""}`;
  const btn=document.getElementById("ssSave");
  if(btn)btn.onclick=async()=>{
    const fd=new FormData(document.getElementById("ssForm"));const b={};
    fd.forEach((v,k)=>b[k]=v);
    try{await api("/settings/all",{method:"PUT",body:JSON.stringify(b)});
      toast(t("saved"));viewSysSettings();}catch{}};
  const addBtn=document.getElementById("addDemo");
  if(addBtn)addBtn.onclick=()=>{
    const phraseRequired=demo.add_confirmation||"ADD DEMO DATA";
    const el=modal(tx.addTitle,`<div class="card" style="border:1px solid var(--ok);background:var(--ok)10;margin-bottom:12px">
      <b style="color:var(--ok)">✨ ${tx.addTitle}</b><div class="mut" style="font-size:12px;margin-top:5px">${tx.addKeeps}</div></div>
      <div style="font-size:13px;margin-bottom:8px">${tx.addDesc}</div>
      <div class="fld"><label>${tx.addPhrase}: <code>${phraseRequired}</code></label>
        <input id="addDemoPhrase" autocomplete="off" spellcheck="false" placeholder="${phraseRequired}"></div>`,
      [[t("cancel"),close_,""],[tx.addConfirm,async()=>{
        const phrase=(el.querySelector("#addDemoPhrase").value||"").trim();
        if(phrase!==phraseRequired){toast(tx.addPhrase+": "+phraseRequired);return;}
        try{
          const result=await api("/admin/demo-data/add",{method:"POST",body:JSON.stringify({confirmation:phrase})});
          toast(result.already_present?tx.already:`${tx.addDone} · ${fmtNum(result.total)}`);close_();viewSysSettings();
        }catch{}
      },"pri"]]);
  };
  const clearBtn=document.getElementById("clearDemo");
  if(clearBtn)clearBtn.onclick=()=>{
    const el=modal(tx.deleteTitle,`<div class="card" style="border:1px solid var(--danger);background:var(--danger)12;margin-bottom:12px">
      <b style="color:var(--danger)">⚠ ${tx.warning}</b></div>
      <div style="font-size:13px;margin-bottom:8px">${tx.deleteDesc}</div>
      <div class="mut" style="font-size:12px;margin-bottom:14px">${tx.keeps}</div>
      <div class="fld"><label>${tx.deletePhrase}: <code>${demo.confirmation}</code></label>
        <input id="demoPhrase" autocomplete="off" spellcheck="false" placeholder="${demo.confirmation}"></div>`,
      [[t("cancel"),close_,""],[tx.deleteConfirm,async()=>{
        const phrase=(el.querySelector("#demoPhrase").value||"").trim();
        if(phrase!==demo.confirmation){toast(tx.deletePhrase+": "+demo.confirmation);return;}
        try{
          const result=await api("/admin/demo-data/clear",{method:"POST",body:JSON.stringify({confirmation:phrase})});
          toast(`${tx.deleteDone} · ${fmtNum(result.total)}`);close_();viewSysSettings();
        }catch{}
      },"dgr"]]);
  };
}

boot();
