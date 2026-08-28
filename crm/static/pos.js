/* NebrasCRM POS — a fast retail workspace built on invoices, payments and stock. */
const POSUI = {
  catalog: [], categories: [], cart: [], query: "", category: "", customer: null,
  paymentMethod: "cash", amountReceived: "", session: null, summary: null, sales: [],
  currency: "USD", allowNegative: false, requireSession: false,
};

const posText = () => S.lang === "ar" ? {
  title:"نقطة البيع", subtitle:"بيع سريع ومتكامل مع المخزون والفواتير", online:"متصل", newSale:"عملية جديدة",
  session:"الوردية", openSession:"فتح وردية", closeSession:"إغلاق وردية", noSession:"لا توجد وردية مفتوحة",
  salesToday:"مبيعات اليوم", transactions:"عملية", cash:"نقدي", card:"بطاقة", lowStock:"تنبيه مخزون",
  products:"المنتجات", search:"ابحث بالاسم أو الرمز…", all:"الكل", cart:"سلة البيع", emptyCart:"السلة فارغة",
  add:"إضافة", inStock:"متوفر", outStock:"نفد", stock:"المخزون", qty:"الكمية", price:"السعر", discount:"خصم", tax:"ضريبة",
  customer:"العميل", walkIn:"عميل نقدي", chooseCustomer:"اختيار عميل", changeCustomer:"تغيير", remove:"إزالة",
  subtotal:"الإجمالي قبل الخصم", discountTotal:"إجمالي الخصم", taxTotal:"الضريبة", total:"الإجمالي", payment:"طريقة الدفع",
  received:"المبلغ المستلم", change:"الباقي", complete:"إتمام البيع", onAccount:"آجل / على الحساب", receiptEmail:"إرسال الإيصال بالبريد", email:"بريد الإيصال",
  recent:"آخر العمليات", receipt:"إيصال", refund:"استرجاع", refunded:"مسترجع", paid:"مدفوع", unpaid:"غير مدفوع",
  openCash:"رصيد افتتاحي", countedCash:"النقد الفعلي", expectedCash:"النقد المتوقع", difference:"الفرق", note:"ملاحظة", save:"حفظ",
  cancel:"إلغاء", print:"طباعة الإيصال", success:"اكتملت عملية البيع", receiptNo:"رقم الإيصال", customerSearch:"ابحث عن شركة أو هاتف…",
  noCustomers:"لا يوجد عملاء مطابقون", stockWarning:"الكمية المطلوبة تتجاوز المتاح", sessionRequired:"افتح وردية قبل البيع", date:"التاريخ", cashier:"الكاشير",
  cashMethod:"نقداً", cardMethod:"بطاقة", walletMethod:"محفظة", bankMethod:"تحويل بنكي", openNote:"يمكن تسجيل البيع دون وردية إذا لم يفرضها مدير النظام.",
  refundConfirm:"سيتم استرجاع المخزون وإلغاء الفاتورة وتسجيل العملية كمسترجعة. هل تريد المتابعة؟",
}:{
  title:"Point of Sale", subtitle:"Fast checkout connected to stock and invoices", online:"Online", newSale:"New sale",
  session:"Shift", openSession:"Open shift", closeSession:"Close shift", noSession:"No open shift",
  salesToday:"Today’s sales", transactions:"transactions", cash:"Cash", card:"Card", lowStock:"Low stock",
  products:"Products", search:"Search name or code…", all:"All", cart:"Checkout cart", emptyCart:"Your cart is empty",
  add:"Add", inStock:"In stock", outStock:"Out of stock", stock:"Stock", qty:"Qty", price:"Price", discount:"Discount", tax:"Tax",
  customer:"Customer", walkIn:"Walk-in customer", chooseCustomer:"Choose customer", changeCustomer:"Change", remove:"Remove",
  subtotal:"Subtotal", discountTotal:"Discount", taxTotal:"Tax", total:"Total", payment:"Payment method",
  received:"Amount received", change:"Change", complete:"Complete sale", onAccount:"On account", receiptEmail:"Email receipt", email:"Receipt email",
  recent:"Recent transactions", receipt:"Receipt", refund:"Refund", refunded:"Refunded", paid:"Paid", unpaid:"Unpaid",
  openCash:"Opening cash", countedCash:"Counted cash", expectedCash:"Expected cash", difference:"Difference", note:"Note", save:"Save",
  cancel:"Cancel", print:"Print receipt", success:"Sale completed", receiptNo:"Receipt no.", customerSearch:"Search account or phone…",
  noCustomers:"No matching customers", stockWarning:"Requested quantity exceeds available stock", sessionRequired:"Open a shift before selling", date:"Date", cashier:"Cashier",
  cashMethod:"Cash", cardMethod:"Card", walletMethod:"Wallet", bankMethod:"Bank transfer", openNote:"Sales can be recorded without a shift unless the administrator requires one.",
  refundConfirm:"Stock will be restored, the invoice cancelled and this sale marked refunded. Continue?",
};

function posMoney(value){
  try{return new Intl.NumberFormat(S.lang === "ar" ? "ar-EG" : "en-US", {style:"currency",currency:POSUI.currency||"USD",maximumFractionDigits:2}).format(Number(value||0));}
  catch{return `${Number(value||0).toFixed(2)} ${POSUI.currency||""}`;}
}
function posNumber(value){
  return new Intl.NumberFormat(S.lang === "ar" ? "ar-EG" : "en-US", {maximumFractionDigits:2}).format(Number(value||0));
}
function posLine(line){
  const gross=(+line.qty||0)*(+line.price||0);
  const discount=gross*(+line.discount||0)/100;
  const taxable=gross-discount;
  const tax=taxable*(+line.tax||0)/100;
  return {gross,discount,tax,total:taxable+tax};
}
function posTotals(){
  return POSUI.cart.reduce((totals,line)=>{
    const calc=posLine(line);
    totals.subtotal+=calc.gross;totals.discount+=calc.discount;totals.tax+=calc.tax;totals.total+=calc.total;
    return totals;
  },{subtotal:0,discount:0,tax:0,total:0});
}
function posProduct(id){return POSUI.catalog.find(product=>product.id===+id);}
function posCartLine(id){return POSUI.cart.find(line=>line.product_id===+id);}
function posStatusClass(status){return status==="completed"?"ok":status==="refunded"?"danger":"warn";}

async function viewPOS(){
  if(S.user.role === "readonly"){ S.view="dashboard"; renderApp(); return; }
  main.innerHTML=`<div class="pos-loading"><div class="pos-orbit"></div><b>${S.lang==="ar"?"جارٍ تجهيز نقطة البيع…":"Preparing POS…"}</b></div>`;
  try{await posReload();}catch(error){
    main.innerHTML=`<div class="empty">${S.lang==="ar"?"تعذّر تحميل نقطة البيع":"Could not load Point of Sale"}</div>`;
  }
}

async function posReload(){
  const [catalog,session,summary,sales]=await Promise.all([
    api("/pos/catalog"),api("/pos/session"),api("/pos/summary"),api("/pos/sales?limit=12"),
  ]);
  POSUI.catalog=catalog.products||[];
  POSUI.categories=catalog.categories||[];
  POSUI.currency=catalog.currency||summary.currency||"USD";
  POSUI.allowNegative=!!catalog.allow_negative_stock;
  POSUI.requireSession=!!catalog.require_session;
  POSUI.session=session.session||null;
  POSUI.summary=summary;
  POSUI.sales=sales||[];
  // Keep a cart if the operator changes a filter, but remove products that are no
  // longer active in the POS catalogue.
  POSUI.cart=POSUI.cart.filter(line=>POSUI.catalog.some(product=>product.id===line.product_id));
  if(S.view === "pos") posRender();
}

function posRender(){
  const tx=posText(), totals=posTotals();
  const query=POSUI.query.trim().toLowerCase();
  const products=POSUI.catalog.filter(product=>{
    const text=`${product.name||""} ${product.code||""} ${product.category||""}`.toLowerCase();
    return (!query||text.includes(query)) && (!POSUI.category||product.category===POSUI.category);
  });
  const today=POSUI.summary?.today||{count:0,total:0,cash:0,card:0};
  const session=POSUI.session;
  const selectedCustomer=POSUI.customer;
  const customerName=selectedCustomer?.name||tx.walkIn;
  const cashReceived=POSUI.amountReceived===""?totals.total:Number(POSUI.amountReceived||0);
  const change=Math.max(0,cashReceived-totals.total);
  const saleDisabled=!POSUI.cart.length || (POSUI.requireSession&&!session);

  main.innerHTML=`<section class="pos-shell">
    <header class="pos-hero">
      <div class="pos-hero-main"><div class="pos-icon">🛒</div><div><div class="pos-overline">NEBRAS RETAIL</div>
        <h1>${tx.title}</h1><p>${tx.subtitle}</p></div></div>
      <div class="pos-hero-actions"><span class="pos-live"><i></i>${tx.online}</span>
        <button class="btn pos-session-btn" id="posSession">${session?`⏱ ${tx.closeSession}`:`＋ ${tx.openSession}`}</button>
        <button class="btn pri" id="posReset">↺ ${tx.newSale}</button></div>
    </header>

    <section class="pos-kpis">
      <article class="pos-kpi"><span>▣ ${tx.salesToday}</span><b>${posMoney(today.total)}</b><small>${posNumber(today.count)} ${tx.transactions}</small></article>
      <article class="pos-kpi"><span>◉ ${tx.cash}</span><b>${posMoney(today.cash)}</b><small>${session?`${tx.session} #${session.id}`:tx.noSession}</small></article>
      <article class="pos-kpi"><span>◈ ${tx.card}</span><b>${posMoney(today.card)}</b><small>${POSUI.currency}</small></article>
      <article class="pos-kpi ${POSUI.summary?.low_stock?"attention":""}"><span>⚠ ${tx.lowStock}</span><b>${posNumber(POSUI.summary?.low_stock||0)}</b><small>${tx.stock}</small></article>
    </section>

    <div class="pos-workspace">
      <section class="pos-catalog card">
        <div class="pos-catalog-top"><div><h2>${tx.products}</h2><span>${posNumber(products.length)} / ${posNumber(POSUI.catalog.length)}</span></div>
          <label class="pos-search"><span>⌕</span><input id="posQuery" value="${esc(POSUI.query)}" placeholder="${tx.search}" autocomplete="off"></label></div>
        <div class="pos-categories"><button data-pos-cat="" class="${!POSUI.category?"on":""}">${tx.all}</button>
          ${POSUI.categories.map(category=>`<button data-pos-cat="${esc(category)}" class="${POSUI.category===category?"on":""}">${esc(category)}</button>`).join("")}</div>
        <div class="pos-products">${products.map(product=>{
          const stock=Number(product.qty_in_stock||0), empty=stock<=0&&!POSUI.allowNegative;
          const low=Number(product.reorder_level||0)>0&&stock<=Number(product.reorder_level||0);
          return `<article class="pos-product ${empty?"soldout":""}" data-pos-add="${product.id}">
            <div class="pos-product-icon">${(product.name||"P").trim().slice(0,1).toUpperCase()}</div>
            <div class="pos-product-body"><div class="pos-product-name">${esc(product.name)}</div>
              <div class="pos-product-code">${esc(product.code||product.category||"—")}</div>
              <div class="pos-product-foot"><b>${posMoney(product.unit_price)}</b>
                <span class="${empty?"bad":low?"low":""}">${empty?tx.outStock:`${tx.stock}: ${posNumber(stock)}`}</span></div></div>
            <button class="pos-add" ${empty?"disabled":""} aria-label="${tx.add}">＋</button></article>`;
        }).join("")||`<div class="pos-no-products">⌕<br>${S.lang==="ar"?"لا توجد منتجات مطابقة":"No matching products"}</div>`}</div>
      </section>

      <aside class="pos-checkout card">
        <div class="pos-cart-head"><div><span>${tx.cart}</span><b>${posNumber(POSUI.cart.length)}</b></div><button class="pos-clear" id="posClear" ${POSUI.cart.length?"":"disabled"}>${tx.newSale}</button></div>
        <div class="pos-cart-items">${POSUI.cart.map(line=>{
          const calc=posLine(line);
          return `<article class="pos-cart-line"><div class="pos-cart-line-main"><b>${esc(line.name)}</b><span>${posMoney(line.price)} ${line.tax?`· ${line.tax}%`:""}</span></div>
            <button class="pos-remove" data-pos-remove="${line.product_id}" title="${tx.remove}">×</button>
            <div class="pos-cart-controls"><div class="pos-stepper"><button data-pos-minus="${line.product_id}">−</button><input data-pos-qty="${line.product_id}" type="number" min="0.01" step="1" value="${line.qty}"><button data-pos-plus="${line.product_id}">＋</button></div>
              <label class="pos-discount"><span>${tx.discount}</span><input data-pos-disc="${line.product_id}" type="number" min="0" max="100" step="1" value="${line.discount||0}">%</label>
              <strong>${posMoney(calc.total)}</strong></div></article>`;
        }).join("")||`<div class="pos-empty-cart"><div>🧺</div><b>${tx.emptyCart}</b><span>${S.lang==="ar"?"اختر المنتجات من الكتالوج لبدء البيع":"Choose products from the catalogue to begin"}</span></div>`}</div>

        <button class="pos-customer" id="posCustomer"><span>◉</span><div><small>${tx.customer}</small><b>${esc(customerName)}</b></div><em>${selectedCustomer?tx.changeCustomer:tx.chooseCustomer}</em></button>
        <div class="pos-payment-block"><div class="pos-payment-label">${tx.payment}</div>
          <div class="pos-payment-methods">${[
            ["cash",tx.cashMethod,"💵"],["card",tx.cardMethod,"▣"],["wallet",tx.walletMethod,"◉"],["bank",tx.bankMethod,"⇄"],["on_account",tx.onAccount,"◷"],
          ].map(([method,label,icon])=>`<button data-pos-method="${method}" class="${POSUI.paymentMethod===method?"on":""}"><span>${icon}</span>${label}</button>`).join("")}</div>
          ${POSUI.paymentMethod==="cash"?`<label class="pos-received"><span>${tx.received}</span><input id="posReceived" type="number" min="0" step="0.01" value="${POSUI.amountReceived===""?totals.total:POSUI.amountReceived}"></label>
            <div class="pos-change"><span>${tx.change}</span><b id="posChange">${posMoney(change)}</b></div>`:""}
          ${POSUI.paymentMethod==="on_account"?`<div class="pos-credit-note">◷ ${tx.onAccount}</div>`:""}
        </div>
        <div class="pos-totals"><div><span>${tx.subtotal}</span><b>${posMoney(totals.subtotal)}</b></div><div><span>${tx.discountTotal}</span><b>− ${posMoney(totals.discount)}</b></div><div><span>${tx.taxTotal}</span><b>+ ${posMoney(totals.tax)}</b></div><div class="pos-grand"><span>${tx.total}</span><b>${posMoney(totals.total)}</b></div></div>
        <label class="pos-email-toggle"><input id="posSendEmail" type="checkbox"> <span>${tx.receiptEmail}</span></label>
        <input id="posReceiptEmail" class="pos-email-input" type="email" placeholder="${tx.email}">
        ${POSUI.requireSession&&!session?`<div class="pos-session-warning">⚠ ${tx.sessionRequired}</div>`:""}
        ${!POSUI.requireSession&&!session?`<div class="pos-session-hint">${tx.openNote}</div>`:""}
        <button class="pos-complete" id="posComplete" ${saleDisabled?"disabled":""}><span>✓</span>${tx.complete}<b>${posMoney(totals.total)}</b></button>
      </aside>
    </div>

    <section class="pos-recent card"><div class="pos-recent-head"><div><h2>${tx.recent}</h2><span>${POSUI.sales.length}</span></div><button class="btn sm" id="posRefresh">↻</button></div>
      <div class="pos-recent-list">${POSUI.sales.map(sale=>`<article class="pos-sale-row">
        <div class="pos-sale-icon ${posStatusClass(sale.status)}">${sale.status==="refunded"?"↩":"✓"}</div><div class="pos-sale-ref"><b>${esc(sale.receipt_no)}</b><span>${esc(sale.customer_name||sale.account_name||tx.walkIn)} · ${(sale.created_at||"").replace("T"," ")}</span></div>
        <div class="pos-sale-method">${esc((sale.payment_method||"").replace("_"," "))}</div><strong>${posMoney(sale.total)}</strong>
        <span class="pos-sale-status ${posStatusClass(sale.status)}">${sale.status==="refunded"?tx.refunded:sale.payment_status==="paid"?tx.paid:tx.unpaid}</span>
        <button class="btn sm" data-pos-print="${sale.id}">🖨</button>${["admin","manager"].includes(S.user.role)&&sale.status==="completed"?`<button class="btn sm dgr" data-pos-refund="${sale.id}">${tx.refund}</button>`:""}</article>`).join("")||`<div class="pos-empty-history">${S.lang==="ar"?"لا توجد عمليات بيع بعد":"No sales have been recorded yet"}</div>`}</div>
    </section>
  </section>`;
  posBind();
}

function posBind(){
  const tx=posText();
  const root=main;
  const query=root.querySelector("#posQuery");
  query.oninput=()=>{const value=query.value, caret=query.selectionStart;POSUI.query=value;posRender();requestAnimationFrame(()=>{
    const next=main.querySelector("#posQuery");if(next){next.focus();next.setSelectionRange(caret,caret);}
  });};
  root.querySelectorAll("[data-pos-cat]").forEach(button=>button.onclick=()=>{POSUI.category=button.dataset.posCat;posRender();});
  root.querySelectorAll("[data-pos-add]").forEach(card=>card.onclick=event=>{
    if(event.target.closest("button")?.disabled)return;
    posAdd(+card.dataset.posAdd);
  });
  root.querySelectorAll("[data-pos-plus]").forEach(button=>button.onclick=()=>posAdjust(+button.dataset.posPlus,1));
  root.querySelectorAll("[data-pos-minus]").forEach(button=>button.onclick=()=>posAdjust(+button.dataset.posMinus,-1));
  root.querySelectorAll("[data-pos-remove]").forEach(button=>button.onclick=()=>{POSUI.cart=POSUI.cart.filter(line=>line.product_id!==+button.dataset.posRemove);posRender();});
  root.querySelectorAll("[data-pos-qty]").forEach(input=>input.onchange=()=>posSetQty(+input.dataset.posQty,input.value));
  root.querySelectorAll("[data-pos-disc]").forEach(input=>input.onchange=()=>{
    const line=posCartLine(+input.dataset.posDisc);if(!line)return;line.discount=Math.max(0,Math.min(100,Number(input.value)||0));posRender();
  });
  root.querySelectorAll("[data-pos-method]").forEach(button=>button.onclick=()=>{POSUI.paymentMethod=button.dataset.posMethod;POSUI.amountReceived="";posRender();});
  const received=root.querySelector("#posReceived");
  if(received)received.oninput=()=>{POSUI.amountReceived=received.value;const change=Math.max(0,(Number(received.value)||0)-posTotals().total);root.querySelector("#posChange").textContent=posMoney(change);};
  root.querySelector("#posClear").onclick=()=>{POSUI.cart=[];POSUI.customer=null;POSUI.amountReceived="";posRender();};
  root.querySelector("#posCustomer").onclick=posCustomerPicker;
  root.querySelector("#posSession").onclick=posSessionDialog;
  root.querySelector("#posReset").onclick=()=>{POSUI.cart=[];POSUI.customer=null;POSUI.amountReceived="";posRender();};
  root.querySelector("#posComplete").onclick=posCompleteSale;
  root.querySelector("#posRefresh").onclick=()=>posReload().catch(()=>{});
  root.querySelectorAll("[data-pos-print]").forEach(button=>button.onclick=()=>posPrintReceipt(+button.dataset.posPrint));
  root.querySelectorAll("[data-pos-refund]").forEach(button=>button.onclick=()=>posRefund(+button.dataset.posRefund));
}

function posAdd(productId){
  const product=posProduct(productId);if(!product)return;
  const line=posCartLine(productId);
  const next=(line?.qty||0)+1;
  if(!POSUI.allowNegative&&next>Number(product.qty_in_stock||0)+0.00001){toast(posText().stockWarning);return;}
  if(line)line.qty=next;
  else POSUI.cart.push({product_id:product.id,name:product.name,code:product.code,qty:1,price:Number(product.unit_price||0),discount:0,tax:Number(product.tax_rate||0),stock:Number(product.qty_in_stock||0)});
  posRender();
}
function posAdjust(productId,delta){
  const line=posCartLine(productId);if(!line)return;
  posSetQty(productId,Number(line.qty)+delta);
}
function posSetQty(productId,value){
  const line=posCartLine(productId);if(!line)return;
  let qty=Number(value);
  if(!Number.isFinite(qty)||qty<=0){POSUI.cart=POSUI.cart.filter(item=>item.product_id!==productId);posRender();return;}
  if(!POSUI.allowNegative&&qty>line.stock+0.00001){toast(posText().stockWarning);qty=line.stock;}
  line.qty=Math.max(0.01,qty);posRender();
}

async function posCustomerPicker(){
  const tx=posText();
  const el=modal(tx.chooseCustomer,`<div class="pos-picker-search"><input id="posCustomerQuery" placeholder="${tx.customerSearch}" autocomplete="off"></div><div id="posCustomerRows" class="pos-customer-rows">…</div>`,[[tx.cancel,close_,""]]);
  const input=el.querySelector("#posCustomerQuery"), rows=el.querySelector("#posCustomerRows");
  let timer;
  const load=async()=>{
    const accounts=await api(`/pos/customers?q=${encodeURIComponent(input.value.trim())}&limit=80`);
    rows.innerHTML=accounts.length?accounts.map(account=>`<button class="pos-customer-row" data-pos-customer="${account.id}"><span>🏢</span><div><b>${esc(account.name)}</b><small>${esc([account.contact_name,account.phone,account.contact_email].filter(Boolean).join(" · ")||"—")}</small></div></button>`).join(""):`<div class="empty">${tx.noCustomers}</div>`;
    rows.querySelectorAll("[data-pos-customer]").forEach(button=>button.onclick=()=>{
      const customer=accounts.find(account=>account.id===+button.dataset.posCustomer);POSUI.customer=customer||null;close_();posRender();
    });
  };
  input.oninput=()=>{clearTimeout(timer);timer=setTimeout(()=>load().catch(()=>{}),220);};
  load().catch(()=>{rows.innerHTML=`<div class="empty">${tx.noCustomers}</div>`;});
}

function posSessionDialog(){
  const tx=posText(), session=POSUI.session;
  if(!session){
    const el=modal(tx.openSession,`<form id="posOpenSession"><div class="fld"><label>${tx.openCash}</label><input name="opening_cash" type="number" min="0" step="0.01" value="0"></div><div class="fld"><label>${tx.note}</label><input name="note"></div></form>`,[[tx.cancel,close_,""],[tx.save,async()=>{
      const fd=new FormData(el.querySelector("#posOpenSession"));const body={};fd.forEach((value,key)=>body[key]=value);body.opening_cash=Number(body.opening_cash)||0;
      await api("/pos/sessions/open",{method:"POST",body:JSON.stringify(body)});toast(tx.openSession+" ✓");close_();posReload();
    },"pri"]]);
    return;
  }
  const expected=Number(session.expected_cash||0);
  const el=modal(tx.closeSession,`<div class="pos-session-summary"><div><span>${tx.openCash}</span><b>${posMoney(session.opening_cash)}</b></div><div><span>${tx.cash}</span><b>${posMoney(session.cash_sales)}</b></div><div><span>${tx.expectedCash}</span><b>${posMoney(expected)}</b></div></div><form id="posCloseSession"><div class="fld"><label>${tx.countedCash}</label><input name="closing_cash" type="number" min="0" step="0.01" value="${expected}"></div><div class="fld"><label>${tx.note}</label><input name="note" value="${esc(session.note||"")}"></div></form>`,[[tx.cancel,close_,""],[tx.closeSession,async()=>{
    const fd=new FormData(el.querySelector("#posCloseSession"));const body={};fd.forEach((value,key)=>body[key]=value);body.closing_cash=Number(body.closing_cash)||0;
    const result=await api(`/pos/sessions/${session.id}/close`,{method:"POST",body:JSON.stringify(body)});toast(`${tx.closeSession} · ${tx.difference}: ${posMoney(result.session.difference)}`);close_();posReload();
  },"pri"]]);
}

async function posCompleteSale(){
  const tx=posText(), totals=posTotals();
  if(!POSUI.cart.length)return;
  if(POSUI.requireSession&&!POSUI.session){toast(tx.sessionRequired);return;}
  const root=main;
  const checkbox=root.querySelector("#posSendEmail");
  const email=root.querySelector("#posReceiptEmail");
  const received=root.querySelector("#posReceived");
  const button=root.querySelector("#posComplete");button.disabled=true;
  try{
    const payload={
      items:POSUI.cart.map(line=>({product_id:line.product_id,qty:+line.qty,discount:+line.discount||0})),
      account_id:POSUI.customer?.id||null,
      customer_name:POSUI.customer?"":tx.walkIn,
      customer_phone:POSUI.customer?.phone||"",
      payment_method:POSUI.paymentMethod,
      amount_received:POSUI.paymentMethod==="cash"?(Number(received?.value)||0):null,
      send_receipt:!!checkbox?.checked,
      receipt_email:email?.value.trim()||"",
    };
    const sale=await api("/pos/sale",{method:"POST",body:JSON.stringify(payload)});
    POSUI.cart=[];POSUI.customer=null;POSUI.amountReceived="";
    await posReload();
    modal(tx.success,`<div class="pos-success"><div>✓</div><h3>${esc(sale.receipt_no)}</h3><p>${tx.total}: <b>${posMoney(sale.totals.total)}</b></p>${sale.change_due?`<p>${tx.change}: <b>${posMoney(sale.change_due)}</b></p>`:""}${sale.receipt_queued?`<small>✉ ${tx.receiptEmail}</small>`:""}</div>`,[[tx.cancel,close_,""],["🖨 "+tx.print,()=>posPrintReceipt(sale.sale_id),"pri"]]);
  }catch(error){button.disabled=false;}
}

async function posRefund(saleId){
  const tx=posText();if(!confirm(tx.refundConfirm))return;
  const note=prompt(tx.note,"");if(note===null)return;
  try{await api(`/pos/sales/${saleId}/refund`,{method:"POST",body:JSON.stringify({note})});toast(tx.refunded+" ✓");posReload();}catch{}
}

function posPrintReceipt(saleId){
  const win=window.open("","_blank");
  if(!win){toast(S.lang==="ar"?"اسمح بالنوافذ المنبثقة للطباعة":"Allow pop-ups to print");return;}
  win.document.write(`<title>POS receipt</title><body style="font-family:system-ui;padding:24px">Loading…</body>`);
  api(`/pos/sales/${saleId}/receipt`).then(data=>{
    const ar=S.lang==="ar", sale=data.sale||{}, company=data.company||{}, customer=data.account||{}, cashier=data.cashier||{};
    const currency=company.currency||POSUI.currency||"USD";
    const money=value=>{try{return new Intl.NumberFormat(ar?"ar-EG":"en-US",{style:"currency",currency,maximumFractionDigits:2}).format(value||0);}catch{return `${Number(value||0).toFixed(2)} ${currency}`;}};
    const L=ar?{receipt:"إيصال بيع",customer:"العميل",cashier:"الكاشير",qty:"الكمية",price:"السعر",total:"الإجمالي",sub:"قبل الخصم",discount:"الخصم",tax:"الضريبة",received:"المستلم",change:"الباقي",thanks:"شكرًا لتسوقكم معنا"}:{receipt:"Sale Receipt",customer:"Customer",cashier:"Cashier",qty:"Qty",price:"Price",total:"Total",sub:"Subtotal",discount:"Discount",tax:"Tax",received:"Received",change:"Change",thanks:"Thank you for shopping with us"};
    const itemRows=(data.items||[]).map(item=>{const gross=(item.qty||0)*(item.price||0), disc=gross*(item.discount||0)/100, net=gross-disc, tax=net*(item.tax||0)/100;return `<tr><td><b>${esc(item.name||"—")}</b>${item.product_code?`<small>${esc(item.product_code)}</small>`:""}</td><td>${item.qty}</td><td>${money(item.price)}</td><td>${money(net+tax)}</td></tr>`;}).join("");
    const html=`<!doctype html><html lang="${ar?"ar":"en"}" dir="${ar?"rtl":"ltr"}"><head><meta charset="utf-8"><title>${esc(sale.receipt_no||L.receipt)}</title><style>@page{size:80mm auto;margin:3mm}*{box-sizing:border-box}body{margin:0;color:#172033;font:11px/1.5 "Segoe UI",Tahoma,Arial,sans-serif}.receipt{width:74mm;margin:auto}.head{text-align:center;border-bottom:2px dashed #1f3e82;padding:5px 0 10px}.mark{width:28px;height:28px;margin:auto auto 5px;border-radius:9px;display:grid;place-items:center;background:linear-gradient(135deg,#173b80,#5d43c6);color:#fff;font-weight:800}.head h1{font-size:16px;margin:0}.head p{margin:2px 0;color:#667085;font-size:9px}.badge{display:inline-block;background:#eef3ff;color:#173b80;padding:3px 7px;border-radius:99px;font-weight:800;margin-top:5px}.meta{border-bottom:1px dashed #cbd5e1;padding:8px 0;font-size:10px}.meta div{display:flex;justify-content:space-between;gap:8px;padding:1px 0}.items{width:100%;border-collapse:collapse;margin:8px 0}.items th{font-size:9px;padding:4px 2px;border-bottom:1px solid #172033;text-align:start}.items td{padding:5px 2px;border-bottom:1px dotted #cbd5e1;vertical-align:top}.items td:not(:first-child),.items th:not(:first-child){text-align:end}.items small{display:block;color:#667085;font-size:8px}.totals{border-top:2px solid #172033;padding-top:5px}.r{display:flex;justify-content:space-between;padding:2px 0}.grand{font-size:14px;font-weight:900;padding-top:5px;margin-top:4px;border-top:1px solid #172033}.foot{text-align:center;border-top:1px dashed #cbd5e1;margin-top:10px;padding-top:7px;color:#667085;font-size:9px}@media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}}</style></head><body><main class="receipt"><header class="head"><div class="mark">N</div><h1>${esc(company.name||"NebrasCRM")}</h1><p>${esc([company.address,company.phone].filter(Boolean).join(" · "))}</p><span class="badge">${esc(L.receipt)}</span><p><b>${esc(sale.receipt_no||"")}</b><br>${esc((sale.created_at||"").replace("T"," "))}</p></header><section class="meta"><div><span>${esc(L.customer)}</span><b>${esc(customer.name||sale.customer_name||"—")}</b></div><div><span>${esc(L.cashier)}</span><b>${esc(cashier.name||"—")}</b></div><div><span>${esc(ar?"الدفع":"Payment")}</span><b>${esc((sale.payment_method||"").replace("_"," "))}</b></div></section><table class="items"><thead><tr><th>${esc(ar?"الصنف":"Item")}</th><th>${esc(L.qty)}</th><th>${esc(L.price)}</th><th>${esc(L.total)}</th></tr></thead><tbody>${itemRows}</tbody></table><section class="totals"><div class="r"><span>${esc(L.sub)}</span><b>${money(sale.subtotal)}</b></div><div class="r"><span>${esc(L.discount)}</span><b>− ${money(sale.discount_total)}</b></div><div class="r"><span>${esc(L.tax)}</span><b>+ ${money(sale.tax_total)}</b></div><div class="r grand"><span>${esc(L.total)}</span><b>${money(sale.total)}</b></div>${sale.payment_method==="cash"?`<div class="r"><span>${esc(L.received)}</span><b>${money(sale.amount_received)}</b></div><div class="r"><span>${esc(L.change)}</span><b>${money(sale.change_due)}</b></div>`:""}</section><footer class="foot">${esc(L.thanks)}<br>${company.tax_number?`${esc(ar?"رقم ضريبي":"Tax no.")}: ${esc(company.tax_number)}`:""}</footer></main></body></html>`;
    win.document.open();win.document.write(html);win.document.close();win.onload=()=>setTimeout(()=>{win.focus();win.print();},180);
  }).catch(()=>win.close());
}
