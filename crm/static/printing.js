/* NebrasCRM — shared printable records, matrices, and payment vouchers.
   All data is received through the same permission-scoped APIs used by the UI. */

function printLanguage(){
  if(typeof S !== "undefined" && S.lang) return S.lang;
  if(typeof P !== "undefined" && P.lang) return P.lang;
  if(typeof A !== "undefined" && A.lang) return A.lang;
  return "en";
}
function printLangIsArabic(){ return printLanguage() === "ar"; }
function printText(ar, en){ return printLangIsArabic() ? ar : en; }
function printEscape(value){
  return String(value ?? "").replace(/[&<>\"]/g, char => ({
    "&":"&amp;", "<":"&lt;", ">":"&gt;", '"':"&quot;",
  }[char]));
}
function printCompanyName(){
  return (typeof S !== "undefined" && S.meta && S.meta.company) || "NebrasCRM";
}
function printMoneyValue(value, currency="USD"){
  const amount=Number(value || 0);
  try{
    return new Intl.NumberFormat(printLangIsArabic()?"ar-EG":"en-US", {
      style:"currency", currency:currency || "USD", maximumFractionDigits:2,
    }).format(Number.isFinite(amount) ? amount : 0);
  }catch{
    return `${Number.isFinite(amount) ? amount.toFixed(2) : "0.00"} ${currency || ""}`.trim();
  }
}
function printNumberValue(value){
  const amount=Number(value || 0);
  try{return new Intl.NumberFormat(printLangIsArabic()?"ar-EG":"en-US", {maximumFractionDigits:2}).format(amount);}
  catch{return String(value ?? "");}
}
function printDateValue(value, includeTime=false){
  if(!value) return "—";
  const raw=String(value);
  const date=new Date(raw.includes("T") ? raw : `${raw.slice(0,10)}T12:00:00`);
  if(Number.isNaN(date.getTime())) return raw.replace("T", " ");
  try{
    return new Intl.DateTimeFormat(printLangIsArabic()?"ar-EG":"en-US", includeTime ? {
      dateStyle:"medium", timeStyle:"short",
    } : {dateStyle:"medium"}).format(date);
  }catch{return raw.replace("T", " ");}
}
function printNotifyBlocked(){
  const message=printText("تعذّر فتح نافذة الطباعة. اسمح بالنوافذ المنبثقة ثم أعد المحاولة.",
    "Print window was blocked. Allow pop-ups and try again.");
  if(typeof toast === "function") toast(message); else window.alert(message);
}
function openPrintWindow(title){
  const win=window.open("", "_blank");
  if(!win){ printNotifyBlocked(); return null; }
  win.document.open();
  win.document.write(`<!doctype html><html><head><meta charset="utf-8"><title>${printEscape(title)}</title></head>
    <body style="font-family:system-ui,Segoe UI,Tahoma,Arial,sans-serif;padding:32px;color:#334155">Loading…</body></html>`);
  win.document.close();
  return win;
}
function finishPrintWindow(win, html){
  if(!win || win.closed) return;
  win.document.open();
  win.document.write(html);
  win.document.close();
  // The visual layouts are self-contained, so a short delay is enough for the
  // print document to be laid out without relying on external styles or fonts.
  window.setTimeout(()=>{
    if(!win.closed){ win.focus(); win.print(); }
  }, 220);
}
function failPrintWindow(win){
  if(!win || win.closed) return;
  win.document.body.innerHTML=`<p style="font-family:system-ui,Segoe UI,Tahoma,Arial,sans-serif;padding:24px;color:#b42318">
    ${printText("تعذّر تجهيز المستند للطباعة.", "The document could not be prepared for printing.")}</p>`;
  window.setTimeout(()=>{ if(!win.closed) win.close(); }, 900);
}

function printLayout({title, subtitle="", content="", landscape=false, accent="#3156c7", soft="#eef3ff", companyMeta=""}){
  const ar=printLangIsArabic();
  const generated=printDateValue(new Date().toISOString(), true);
  const companyLine=companyMeta || printText("مستند صادر من نظام NebrasCRM", "Document issued by NebrasCRM");
  return `<!doctype html><html lang="${ar?"ar":"en"}" dir="${ar?"rtl":"ltr"}"><head>
    <meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
    <title>${printEscape(title)}</title>
    <style>
      @page{size:${landscape?"A4 landscape":"A4"};margin:12mm}
      :root{--accent:${accent};--soft:${soft};--ink:#172033;--mut:#667085;--line:#dbe2ee;--paper:#fff;
        --ok:#087443;--warn:#a65c00;--danger:#b42318;--info:#3156c7;--purple:#7c3aed}
      *{box-sizing:border-box} body{margin:0;background:var(--paper);color:var(--ink);
        font:13px/1.55 "Segoe UI",Tahoma,Arial,sans-serif} .doc{max-width:${landscape?"273mm":"186mm"};margin:auto}
      .head{display:flex;justify-content:space-between;gap:18px;align-items:flex-start;border-bottom:3px solid var(--accent);padding:0 0 16px}
      .brand{display:flex;align-items:flex-start;gap:11px;min-width:0}.mark{width:46px;height:46px;border-radius:13px;
        display:grid;place-items:center;flex:0 0 auto;background:linear-gradient(135deg,var(--accent),#1e8acb);color:#fff;font-size:22px;font-weight:800}
      .company{font-size:20px;font-weight:800;line-height:1.25}.company-meta{color:var(--mut);font-size:10.5px;margin-top:3px;max-width:92mm}
      .doc-title{text-align:end;min-width:0}.kind{display:inline-block;padding:4px 10px;border-radius:999px;background:var(--soft);color:var(--accent);font-size:10.5px;font-weight:800}
      .doc-title h1{font-size:20px;line-height:1.3;margin:7px 0 1px}.doc-title p{margin:0;color:var(--mut);font-size:10.5px}
      .intro{margin:16px 0;padding:10px 13px;border-radius:10px;background:var(--soft);border:1px solid color-mix(in srgb,var(--accent) 20%,#fff);font-size:11.5px;color:#475569}
      .section{margin-top:18px;break-inside:avoid}.section h2{font-size:12px;margin:0 0 8px;color:#344054}.field-grid{display:grid;grid-template-columns:repeat(2,minmax(0,1fr));gap:8px 12px}
      .field{border:1px solid var(--line);border-radius:9px;padding:8px 10px;background:#fbfcff;min-height:58px}.field .label{display:block;color:var(--mut);font-size:10px;margin-bottom:3px}
      .field .value{font-weight:650;overflow-wrap:anywhere;white-space:normal}.note{border-inline-start:3px solid var(--accent);background:#f8fafc;padding:10px 12px;color:#475569;white-space:normal;overflow-wrap:anywhere}
      .notice{border:1px solid #f3cf8b;background:#fff9e9;color:#7a4d00;border-radius:9px;padding:9px 11px;font-size:11px;margin-top:12px}
      .table{width:100%;border-collapse:collapse;font-size:11px}.table thead{display:table-header-group}.table th{background:var(--accent);color:#fff;padding:8px 7px;text-align:start;font-weight:700;white-space:nowrap}
      .table td{border-bottom:1px solid var(--line);padding:8px 7px;vertical-align:top;overflow-wrap:anywhere}.table tbody tr:nth-child(even){background:#fafbfe}.table tbody tr{break-inside:avoid}
      .summary-grid{display:grid;grid-template-columns:1.2fr repeat(2,1fr);gap:10px;margin:18px 0}.amount-card{border-radius:12px;padding:13px 15px;background:linear-gradient(135deg,var(--accent),#1e8acb);color:#fff}
      .amount-card span{display:block;font-size:10.5px;opacity:.85}.amount-card strong{display:block;font-size:21px;margin-top:5px;overflow-wrap:anywhere}.summary-card{border:1px solid var(--line);border-radius:12px;padding:12px;background:#fbfcff}
      .summary-card span{display:block;color:var(--mut);font-size:10.5px}.summary-card b{display:block;font-size:14px;margin-top:5px;overflow-wrap:anywhere}.balance{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin-top:10px}
      .balance div{border:1px solid var(--line);border-radius:8px;padding:8px 10px;background:#fbfcff}.balance span{display:block;color:var(--mut);font-size:10px}.balance b{font-size:12px}
      .capture .card{border:1px solid var(--line);border-radius:10px;padding:12px;margin-bottom:12px;background:#fff;break-inside:avoid}.capture .kpis{display:grid;grid-template-columns:repeat(4,minmax(0,1fr));gap:8px;margin-bottom:12px}
      .capture .kpi{border:1px solid var(--line);border-radius:9px;padding:10px;background:#fbfcff}.capture .kpi .l{color:var(--mut);font-size:10px}.capture .kpi .v{font-size:18px;font-weight:800;margin-top:3px}
      .capture .tbl{width:100%;border-collapse:collapse;font-size:10.5px}.capture .tbl thead{display:table-header-group}.capture .tbl th{background:var(--accent);color:#fff;padding:7px;text-align:start}.capture .tbl td{border-bottom:1px solid var(--line);padding:7px;vertical-align:top}.capture .tbl tbody tr:nth-child(even){background:#fafbfe}.capture .wrap-scroll{overflow:visible!important}
      .capture .bar{display:grid;grid-template-columns:145px 1fr 80px;gap:8px;align-items:center;margin:5px 0;font-size:10.5px}.capture .barbg{height:8px;border-radius:99px;background:#e4eaf3;overflow:hidden}.capture .barfill{height:100%;background:var(--accent)}
      .capture input,.capture select,.capture textarea{border:0;background:transparent;font:inherit;color:inherit;padding:0}.mut{color:var(--mut)}
      .foot{display:flex;justify-content:space-between;gap:12px;margin-top:24px;padding-top:10px;border-top:1px solid var(--line);color:var(--mut);font-size:10px}
      @media print{body{-webkit-print-color-adjust:exact;print-color-adjust:exact}.head,.section,.summary-grid,.amount-card,.field,.summary-card{break-inside:avoid}.table th{background:var(--accent)!important;color:#fff!important}.table tbody tr:nth-child(even){background:#fafbfe!important}.amount-card{background:linear-gradient(135deg,var(--accent),#1e8acb)!important}.field,.summary-card,.balance div{background:#fbfcff!important}}
      @media(max-width:680px){.field-grid{grid-template-columns:1fr}.summary-grid{grid-template-columns:1fr}.capture .kpis{grid-template-columns:repeat(2,minmax(0,1fr))}}
    </style></head><body><main class="doc">
      <header class="head"><div class="brand"><div class="mark">${ar?"ن":"N"}</div><div><div class="company">${printEscape(printCompanyName())}</div>
        <div class="company-meta">${printEscape(companyLine)}</div></div></div>
        <div class="doc-title"><span class="kind">${printEscape(title)}</span><h1>${printEscape(title)}</h1><p>${printEscape(subtitle)}</p></div></header>
      ${content}<footer class="foot"><span>${printEscape(generated)}</span><span>${printEscape(printText("تم الإنشاء من NebrasCRM", "Generated by NebrasCRM"))}</span></footer>
    </main></body></html>`;
}

function genericPrintValue(record, field){
  const value=record ? record[field.name] : null;
  if(value===null || value===undefined || value==="") return "—";
  if(field.type==="lookup" || field.type==="user") return printEscape(record._display?.[field.name] || value);
  if(field.type==="currency") return printEscape(printMoneyValue(value));
  if(field.type==="number") return printEscape(printNumberValue(value));
  if(field.type==="date") return printEscape(printDateValue(value));
  if(field.type==="textarea") return printEscape(value).replace(/\r?\n/g, "<br>");
  if(typeof value === "object") return printEscape(JSON.stringify(value));
  return printEscape(value);
}

function printGenericRecord(module, record){
  const meta=typeof S !== "undefined" && S.meta?.modules?.[module];
  if(!meta || !record) return;
  const title=`${meta.icon || ""} ${typeof L === "function" ? L(meta) : module}`.trim();
  const win=openPrintWindow(title);
  if(!win) return;
  const labels=printLangIsArabic()?{
    number:"رقم السجل",created:"تاريخ الإنشاء",updated:"آخر تحديث",notes:"الملاحظات",items:"البنود",
    product:"الصنف",qty:"الكمية",price:"السعر",discount:"الخصم",tax:"الضريبة",total:"الإجمالي",
  }:{
    number:"Record number",created:"Created",updated:"Last updated",notes:"Notes",items:"Line items",
    product:"Item",qty:"Qty",price:"Price",discount:"Discount",tax:"Tax",total:"Total",
  };
  const fields=(meta.fields || []).filter(field=>!/(password|secret|token)/i.test(field.name || ""));
  const fieldHtml=fields.map(field=>`<div class="field"><span class="label">${printEscape(typeof L === "function" ? L(field) : field.name)}</span>
    <div class="value">${genericPrintValue(record, field)}</div></div>`).join("");
  const audit=[
    [labels.number, `#${record.id ?? "—"}`],
    [labels.created, printDateValue(record.created_at, true)],
    [labels.updated, printDateValue(record.updated_at, true)],
  ].map(([label,value])=>`<div class="field"><span class="label">${printEscape(label)}</span><div class="value">${printEscape(value)}</div></div>`).join("");
  const notes=(record._notes || []).filter(note=>note && note.body);
  const notesHtml=notes.length?`<section class="section"><h2>${printEscape(labels.notes)}</h2><div class="note">${notes.map(note=>
    `<p style="margin:0 0 9px"><b>${printEscape(note.uname || "—")}</b> <span class="mut">${printEscape(printDateValue(note.created_at, true))}</span><br>${printEscape(note.body).replace(/\r?\n/g,"<br>")}</p>`
  ).join("")}</div></section>`:"";
  const items=(record._items || []);
  const itemsHtml=items.length?`<section class="section"><h2>${printEscape(labels.items)}</h2><table class="table"><thead><tr>
    <th>${printEscape(labels.product)}</th><th>${printEscape(labels.qty)}</th><th>${printEscape(labels.price)}</th><th>${printEscape(labels.discount)}</th><th>${printEscape(labels.tax)}</th><th>${printEscape(labels.total)}</th>
    </tr></thead><tbody>${items.map(item=>{
      const qty=Number(item.qty || 0), price=Number(item.price || 0), discount=Number(item.discount || 0), tax=Number(item.tax || 0);
      const total=qty*price*(1-discount/100)*(1+tax/100);
      return `<tr><td>${printEscape(item.name || "—")}</td><td>${printEscape(printNumberValue(qty))}</td><td>${printEscape(printMoneyValue(price))}</td>
        <td>${discount?`${printEscape(printNumberValue(discount))}%`:"—"}</td><td>${tax?`${printEscape(printNumberValue(tax))}%`:"—"}</td><td><b>${printEscape(printMoneyValue(total))}</b></td></tr>`;
    }).join("")}</tbody></table></section>`:"";
  const content=`<div class="intro">${printEscape(printText("بيانات السجل التفصيلية", "Detailed record information"))}</div>
    <section class="section"><div class="field-grid">${audit}</div></section>
    <section class="section"><div class="field-grid">${fieldHtml}</div></section>${itemsHtml}${notesHtml}`;
  finishPrintWindow(win, printLayout({title, subtitle:`#${record.id ?? ""}`, content}));
}

async function fetchModulePrintRows(module){
  const perPage=200, maxRows=2000;
  const rows=[];
  let page=1, total=0;
  while(rows.length<maxRows){
    const query=new URLSearchParams({
      q:S.q || "", sort:S.sort || "id", dir:S.dir || "desc", page:String(page), per_page:String(perPage),
      mine:String(S.mine || 0), filters:JSON.stringify(S.filters || []),
    });
    const result=await api(`/${module}?${query}`);
    total=Number(result.total || 0);
    const batch=result.data || [];
    rows.push(...batch.slice(0, maxRows-rows.length));
    if(!batch.length || rows.length>=total || batch.length<perPage) break;
    page += 1;
  }
  return {rows,total,limited:total>rows.length};
}
function matrixPrintValue(row, field){
  return genericPrintValue(row, field);
}
function matrixCriteria(module){
  const meta=S.meta.modules[module], fields=Object.fromEntries((meta.fields || []).map(field=>[field.name,field]));
  const bits=[];
  if(S.q) bits.push(`${printText("البحث", "Search")}: ${S.q}`);
  if(S.mine) bits.push(printText("سجلاتي فقط", "My records only"));
  const ops={eq:"=",ne:"≠",contains:"⊃",gt:">",lt:"<"};
  (S.filters || []).forEach(filter=>{
    if(filter && filter.value!==undefined && filter.value!==""){
      const field=fields[filter.field];
      bits.push(`${typeof L === "function" ? L(field || {label_ar:filter.field,label_en:filter.field}) : filter.field} ${ops[filter.op] || "="} ${filter.value}`);
    }
  });
  return bits;
}
async function printModuleMatrix(){
  const module=typeof S !== "undefined" && S.module;
  const meta=module && S.meta?.modules?.[module];
  if(!meta) return printCurrentView();
  const title=`${meta.icon || ""} ${typeof L === "function" ? L(meta) : module}`.trim();
  const win=openPrintWindow(`${printText("مصفوفة", "Matrix")} — ${title}`);
  if(!win) return;
  try{
    const result=await fetchModulePrintRows(module);
    const columns=(meta.list || []).map(name=>(meta.fields || []).find(field=>field.name===name) || {
      name, label_ar:name, label_en:name, type:"text",
    });
    const criteria=matrixCriteria(module);
    const labels=printLangIsArabic()?{records:"سجل",shown:"السجلات المعروضة",none:"لا توجد سجلات مطابقة",limit:"حُدّدت الطباعة بأول 2,000 سجل لحماية أداء المتصفح."}:{records:"records",shown:"Displayed records",none:"No matching records",limit:"Printing is limited to the first 2,000 records to protect browser performance."};
    const rowsHtml=result.rows.length?`<table class="table"><thead><tr><th>#</th>${columns.map(column=>
      `<th>${printEscape(typeof L === "function" ? L(column) : column.name)}</th>`).join("")}</tr></thead><tbody>${result.rows.map((row,index)=>
      `<tr><td>${printEscape(printNumberValue(index+1))}</td>${columns.map(column=>`<td>${matrixPrintValue(row,column)}</td>`).join("")}</tr>`
    ).join("")}</tbody></table>`:`<div class="notice">${printEscape(labels.none)}</div>`;
    const criteriaHtml=criteria.length?`<div class="intro"><b>${printEscape(printText("معايير الطباعة", "Print criteria"))}:</b> ${printEscape(criteria.join(" · "))}</div>`:"";
    const note=result.limited?`<div class="notice">${printEscape(labels.limit)}</div>`:"";
    const content=`${criteriaHtml}<section class="section"><div class="field-grid"><div class="field"><span class="label">${printEscape(labels.shown)}</span><div class="value">${printEscape(printNumberValue(result.rows.length))} / ${printEscape(printNumberValue(result.total))} ${printEscape(labels.records)}</div></div>
      <div class="field"><span class="label">${printEscape(printText("الترتيب", "Sort order"))}</span><div class="value">${printEscape(S.sort || "id")} · ${printEscape((S.dir || "desc").toUpperCase())}</div></div></div></section>
      <section class="section">${rowsHtml}</section>${note}`;
    finishPrintWindow(win, printLayout({title:`${printText("مصفوفة", "Matrix")} — ${title}`, subtitle:`${result.rows.length} ${labels.records}`, content, landscape:true}));
  }catch(error){
    failPrintWindow(win);
  }
}

function pagePrintTitle(source){
  if(typeof S !== "undefined" && S.view === "module" && S.module && S.meta?.modules?.[S.module]){
    const meta=S.meta.modules[S.module];
    return `${meta.icon || ""} ${typeof L === "function" ? L(meta) : S.module}`.trim();
  }
  const heading=source.querySelector(".h1,h1,h2");
  return (heading && heading.textContent.trim()) || printText("طباعة الصفحة", "Page print");
}
function cleanPrintCapture(clone){
  clone.querySelectorAll("script,style,.no-print,.tabs,.toast,button,.btn,.icbtn,.fabbar").forEach(node=>node.remove());
  clone.querySelectorAll("input,textarea,select").forEach(node=>{
    const signal=[node.name,node.id,node.type,node.closest(".fld")?.textContent].join(" ").toLowerCase();
    if(/password|smtp_pass|secret|token|api.?key|كلمة المرور|مفتاح/.test(signal)){
      (node.closest(".fld") || node).remove();
      return;
    }
    const replacement=document.createElement("span");
    replacement.className="printed-input";
    if(node.tagName === "SELECT") replacement.textContent=node.selectedOptions?.[0]?.textContent || "—";
    else replacement.textContent=node.value || "—";
    node.replaceWith(replacement);
  });
  clone.querySelectorAll("a").forEach(link=>link.removeAttribute("href"));
}
function printCurrentView(){
  const source=document.getElementById("main") || document.getElementById("pc") || document.getElementById("ac");
  if(!source || !source.textContent.trim()) return;
  const title=pagePrintTitle(source);
  const win=openPrintWindow(title);
  if(!win) return;
  const clone=source.cloneNode(true);
  cleanPrintCapture(clone);
  const content=`<section class="section capture">${clone.innerHTML || `<div class="notice">${printEscape(printText("لا توجد بيانات للطباعة", "There is no data to print"))}</div>`}</section>`;
  finishPrintWindow(win, printLayout({
    title, subtitle:printText("نسخة مطبوعة من الصفحة الحالية", "Printed copy of the current page"), content, landscape:true,
  }));
}

function printPaymentReceipt(paymentId){
  const win=openPrintWindow(printText("سند دفع", "Payment Voucher"));
  if(!win) return;
  api(`/documents/payment/${encodeURIComponent(paymentId)}`).then(data=>{
    const company=data.company || {}, payment=data.payment || {}, invoice=data.invoice || {}, account=data.account || {}, contact=data.contact || {};
    const currency=payment.currency || company.currency || "USD";
    const labels=printLangIsArabic()?{
      title:"سند دفع",number:"رقم السند",amount:"المبلغ المسدد",status:"الحالة",method:"طريقة الدفع",channel:"القناة",date:"تاريخ الدفع",reference:"المرجع",
      customer:"بيانات العميل",contact:"جهة الاتصال",phone:"الهاتف",email:"البريد الإلكتروني",address:"العنوان",invoice:"الفاتورة المرتبطة",issued:"تاريخ الفاتورة",invoiceTotal:"إجمالي الفاتورة",paid:"المدفوع حتى الآن",balance:"الرصيد المتبقي",note:"ملاحظات",payerRef:"مرجع الدافع",createdBy:"تم التسجيل بواسطة",
    }:{
      title:"Payment Voucher",number:"Voucher number",amount:"Amount paid",status:"Status",method:"Payment method",channel:"Channel",date:"Payment date",reference:"Reference",
      customer:"Customer information",contact:"Contact",phone:"Phone",email:"Email",address:"Address",invoice:"Linked invoice",issued:"Invoice date",invoiceTotal:"Invoice total",paid:"Paid to date",balance:"Balance due",note:"Notes",payerRef:"Payer reference",createdBy:"Recorded by",
    };
    const person=[contact.name,contact.title].filter(Boolean).join(" · ");
    const personDetails=[contact.phone,contact.email].filter(Boolean).join(" · ");
    const basicFields=[
      [labels.status,payment.status || "—"], [labels.method,payment.method || "—"], [labels.channel,payment.channel || "—"],
      [labels.date,printDateValue(payment.paid_on || payment.created_on,true)], [labels.reference,payment.provider_ref || data.reference || "—"],
      [labels.payerRef,payment.payer_ref || "—"], [labels.createdBy,data.owner?.name || "—"],
    ];
    const customerFields=[
      [labels.customer,account.name || "—"], [labels.contact,person || "—"], [labels.phone,personDetails || account.phone || "—"], [labels.address,account.address || "—"],
    ];
    const fields=list=>list.map(([label,value])=>`<div class="field"><span class="label">${printEscape(label)}</span><div class="value">${printEscape(value)}</div></div>`).join("");
    const invoiceBlock=`<section class="section"><h2>${printEscape(labels.invoice)}</h2><div class="field-grid">${fields([
      [labels.invoice,invoice.subject || `#${invoice.id || "—"}`], [labels.issued,printDateValue(invoice.issued_on)], [labels.invoiceTotal,printMoneyValue(invoice.total,currency)], [labels.paid,printMoneyValue(invoice.paid,currency)], [labels.balance,printMoneyValue(invoice.remaining,currency)],
    ])}</div><div class="balance"><div><span>${printEscape(labels.invoiceTotal)}</span><b>${printEscape(printMoneyValue(invoice.total,currency))}</b></div><div><span>${printEscape(labels.paid)}</span><b>${printEscape(printMoneyValue(invoice.paid,currency))}</b></div><div><span>${printEscape(labels.balance)}</span><b>${printEscape(printMoneyValue(invoice.remaining,currency))}</b></div></div></section>`;
    const note=payment.note?`<section class="section"><h2>${printEscape(labels.note)}</h2><div class="note">${printEscape(payment.note).replace(/\r?\n/g,"<br>")}</div></section>`:"";
    const content=`<section class="summary-grid"><div class="amount-card"><span>${printEscape(labels.amount)}</span><strong>${printEscape(printMoneyValue(payment.amount,currency))}</strong></div>
      <div class="summary-card"><span>${printEscape(labels.number)}</span><b>${printEscape(data.reference || `PAY-${payment.id || ""}`)}</b></div>
      <div class="summary-card"><span>${printEscape(labels.status)}</span><b>${printEscape(payment.status || "—")}</b></div></section>
      <section class="section"><h2>${printEscape(labels.customer)}</h2><div class="field-grid">${fields(customerFields)}</div></section>
      <section class="section"><h2>${printEscape(printText("تفاصيل السداد", "Payment details"))}</h2><div class="field-grid">${fields(basicFields)}</div></section>${invoiceBlock}${note}`;
    const companyMeta=[company.address,company.phone,company.tax_number ? `${printText("رقم ضريبي", "Tax no.")}: ${company.tax_number}` : ""].filter(Boolean).join(" · ");
    finishPrintWindow(win, printLayout({
      title:labels.title, subtitle:data.reference || `#${payment.id || paymentId}`, content, accent:"#087443", soft:"#edf9f1", companyMeta,
    }));
  }).catch(()=>failPrintWindow(win));
}
