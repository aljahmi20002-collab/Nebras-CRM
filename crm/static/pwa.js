/* NebrasCRM PWA runtime — install prompt, update flow, offline & sync UX.
 * Shared by the staff app, the customer portal and the partner portal.
 * Kept dependency-free and idempotent so it can be dropped into any shell.
 */
(function () {
  if (window.__nebrasPWA) return;
  window.__nebrasPWA = true;

  const AR = (localStorage.getItem("lang") || "ar") === "ar";
  const T = AR ? {
    offline: "أنت غير متصل — تعمل على النسخة المحفوظة",
    online: "عاد الاتصال ✓",
    queued: n => `تم حفظ ${n} عملية للإرسال لاحقاً`,
    synced: n => `تمت مزامنة ${n} عملية ✓`,
    syncFail: n => `تعذّرت مزامنة ${n} عملية`,
    update: "يتوفر إصدار جديد",
    reload: "تحديث الآن",
    later: "لاحقاً",
    install: "ثبّت التطبيق",
    installDesc: "شغّل نبراس كتطبيق مستقل بنافذة خاصة وأيقونة على سطح المكتب",
    dismiss: "لا شكراً",
    installed: "تم تثبيت التطبيق ✓",
  } : {
    offline: "You're offline — showing cached data",
    online: "Back online ✓",
    queued: n => `${n} change(s) saved to send later`,
    synced: n => `${n} change(s) synced ✓`,
    syncFail: n => `${n} change(s) failed to sync`,
    update: "A new version is available",
    reload: "Update now",
    later: "Later",
    install: "Install app",
    installDesc: "Run Nebras as a standalone app with its own window and icon",
    dismiss: "No thanks",
    installed: "App installed ✓",
  };

  // ---------------------------------------------------------------- toast
  function toast(msg, kind = "info", ms = 3600) {
    const c = { info: "var(--pri)", ok: "var(--ok)", warn: "var(--warn)", err: "var(--danger)" }[kind];
    const d = document.createElement("div");
    d.className = "toast";
    d.style.borderColor = c;
    d.style.borderInlineStartColor = c;
    d.textContent = msg;
    document.body.appendChild(d);
    setTimeout(() => d.remove(), ms);
  }

  // ---------------------------------------------------------------- status pill
  let pill;
  function setStatus(state, text) {
    if (!pill) {
      pill = document.createElement("div");
      pill.id = "nb-net";
      pill.style.cssText =
        "position:fixed;inset-block-end:14px;inset-inline-start:14px;z-index:9998;" +
        "padding:8px 14px;border-radius:99px;font-size:12px;font-weight:700;" +
        "display:none;align-items:center;gap:7px;box-shadow:0 6px 20px rgba(0,0,0,.25);" +
        "backdrop-filter:blur(8px);transition:.3s;cursor:pointer";
      pill.onclick = () => navigator.serviceWorker?.controller?.postMessage({ type: "replay" });
      document.body.appendChild(pill);
    }
    if (!state) { pill.style.display = "none"; return; }
    const map = {
      offline: ["var(--danger)", "●"],
      queued: ["var(--warn)", "⏳"],
      syncing: ["var(--info)", "↻"],
    }[state] || ["var(--pri)", "●"];
    pill.style.display = "flex";
    pill.style.background = `color-mix(in srgb, ${map[0]} 20%, var(--card))`;
    pill.style.border = `1px solid ${map[0]}`;
    pill.style.color = map[0];
    pill.textContent = `${map[1]} ${text}`;
  }

  // ---------------------------------------------------------------- connectivity
  function online() {
    setStatus(null);
    toast(T.online, "ok", 2200);
    navigator.serviceWorker?.controller?.postMessage({ type: "replay" });
    document.body.classList.remove("is-offline");
  }
  function offline() {
    setStatus("offline", T.offline);
    document.body.classList.add("is-offline");
  }
  window.addEventListener("online", online);
  window.addEventListener("offline", offline);
  if (!navigator.onLine) offline();

  // ---------------------------------------------------------------- SW register
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", async () => {
      try {
        const reg = await navigator.serviceWorker.register("/sw.js", { scope: "/" });

        // update available -> offer, never force (a forced reload loses form state)
        reg.addEventListener("updatefound", () => {
          const nw = reg.installing;
          if (!nw) return;
          nw.addEventListener("statechange", () => {
            if (nw.state === "installed" && navigator.serviceWorker.controller) {
              showUpdate(reg);
            }
          });
        });

        navigator.serviceWorker.addEventListener("message", e => {
          const d = e.data || {};
          if (d.type === "queued") {
            setStatus("queued", T.queued(d.n));
            toast(T.queued(d.n), "warn");
          }
          if (d.type === "sync-done") {
            if (d.ok) { toast(T.synced(d.ok), "ok"); setStatus(null); }
            if (d.fail) { toast(T.syncFail(d.fail), "err"); setStatus("queued", T.queued(d.fail)); }
          }
          if (d.type === "queue-size" && d.n > 0) setStatus("queued", T.queued(d.n));
        });

        setTimeout(() => reg.active?.postMessage({ type: "queue-size" }), 1200);
      } catch (e) { /* SW is an enhancement, never fatal */ }
    });
  }

  function showUpdate(reg) {
    if (document.getElementById("nb-upd")) return;
    const bar = document.createElement("div");
    bar.id = "nb-upd";
    bar.style.cssText =
      "position:fixed;inset-block-start:0;inset-inline:0;z-index:9999;padding:11px 16px;" +
      "display:flex;align-items:center;gap:12px;justify-content:center;flex-wrap:wrap;" +
      "background:linear-gradient(100deg,#4F7CFF,#7C3AED);color:#fff;font-size:13px;font-weight:600;" +
      "box-shadow:0 4px 18px rgba(0,0,0,.3)";
    bar.innerHTML =
      `<span>✨ ${T.update}</span>
       <button id="nb-upd-go" style="background:#fff;color:#2B4ACB;border:none;border-radius:8px;
         padding:6px 14px;font-weight:800;cursor:pointer;font-family:inherit">${T.reload}</button>
       <button id="nb-upd-no" style="background:transparent;color:#fff;border:1px solid #fff6;
         border-radius:8px;padding:6px 12px;cursor:pointer;font-family:inherit">${T.later}</button>`;
    document.body.appendChild(bar);
    document.getElementById("nb-upd-go").onclick = () => {
      reg.waiting?.postMessage({ type: "skip-waiting" });
      navigator.serviceWorker.addEventListener("controllerchange", () => location.reload(), { once: true });
      setTimeout(() => location.reload(), 900);
    };
    document.getElementById("nb-upd-no").onclick = () => bar.remove();
  }

  // ---------------------------------------------------------------- install prompt
  let deferred = null;
  const KEY = "nb-install-dismissed";

  window.addEventListener("beforeinstallprompt", e => {
    e.preventDefault();
    deferred = e;
    window.__nebrasInstall = doInstall;      // let the app trigger it from a menu
    document.dispatchEvent(new CustomEvent("nebras-installable"));
    if (localStorage.getItem(KEY)) return;
    setTimeout(showInstallCard, 12000);      // don't nag on first paint
  });

  window.addEventListener("appinstalled", () => {
    deferred = null;
    document.getElementById("nb-inst")?.remove();
    toast(T.installed, "ok");
  });

  async function doInstall() {
    if (!deferred) return false;
    deferred.prompt();
    const { outcome } = await deferred.userChoice;
    deferred = null;
    document.getElementById("nb-inst")?.remove();
    return outcome === "accepted";
  }

  function showInstallCard() {
    if (!deferred || document.getElementById("nb-inst")) return;
    const card = document.createElement("div");
    card.id = "nb-inst";
    card.style.cssText =
      "position:fixed;inset-block-end:18px;inset-inline-end:18px;z-index:9998;max-width:330px;" +
      "background:var(--card);border:1px solid var(--line2);border-radius:16px;padding:16px;" +
      "box-shadow:0 16px 44px rgba(0,0,0,.34);animation:nbIn .4s cubic-bezier(.2,.8,.3,1)";
    card.innerHTML =
      `<style>@keyframes nbIn{from{opacity:0;transform:translateY(18px)}}</style>
       <div style="display:flex;gap:12px;align-items:flex-start">
         <div style="width:44px;height:44px;border-radius:12px;flex:none;display:grid;place-items:center;
              background:linear-gradient(135deg,#4F7CFF,#2B4ACB 52%,#7C3AED)">
           <svg viewBox="0 0 64 64" width="30" height="30"><defs>
             <linearGradient id="nbpf" x1=".5" y1="0" x2=".5" y2="1">
               <stop offset="0" stop-color="#fff"/><stop offset=".55" stop-color="#FFF3D6"/>
               <stop offset="1" stop-color="#FFC53D"/></linearGradient></defs>
             <path d="M33.4 8.2C33.9 15.6 40.1 18.6 43.6 24.4C46.9 29.9 47 36 45.1 40.7C42.6 47 37.6 51.4 31.6 51.4C24 51.4 17.4 45.6 17 37.4C16.7 31.3 20 27.6 22.6 24.9C24.2 27.4 25.9 28.6 27.4 28.8C26.2 22 28.6 14.2 33.4 8.2Z" fill="url(#nbpf)"/></svg>
         </div>
         <div style="flex:1;min-width:0">
           <b style="font-size:14px">${T.install}</b>
           <div style="color:var(--mut);font-size:12px;line-height:1.8;margin-top:3px">${T.installDesc}</div>
         </div></div>
       <div style="display:flex;gap:8px;margin-top:13px">
         <button id="nb-i-go" class="btn pri sm" style="flex:1">${T.install}</button>
         <button id="nb-i-no" class="btn sm">${T.dismiss}</button>
       </div>`;
    document.body.appendChild(card);
    document.getElementById("nb-i-go").onclick = doInstall;
    document.getElementById("nb-i-no").onclick = () => {
      localStorage.setItem(KEY, "1");
      card.remove();
    };
  }

  // ---------------------------------------------------------------- desktop shell hooks
  // When running inside the Electron wrapper these become available.
  window.nebras = window.nebras || {};
  const isDesktop = /NebrasDesktop/.test(navigator.userAgent) || !!window.nebrasDesktop;
  const standalone = matchMedia("(display-mode: standalone)").matches ||
                     navigator.standalone === true || isDesktop;
  document.documentElement.classList.toggle("nb-standalone", standalone);
  document.documentElement.classList.toggle("nb-desktop", isDesktop);
  window.nebras.isDesktop = isDesktop;
  window.nebras.isStandalone = standalone;
  window.nebras.install = doInstall;
  window.nebras.toast = toast;
})();
