/* NebrasCRM Service Worker
 *
 * Strategy is deliberately split by resource type, because a CRM has two very
 * different kinds of traffic:
 *   - The SHELL (html/css/js/fonts/brand) changes rarely  -> cache-first, fast boot.
 *   - The DATA (/api/**) must never be stale on a write   -> network-first with a
 *     read-only fallback so a rep in a dead zone can still SEE their pipeline.
 *
 * Writes made while offline are queued in IndexedDB and replayed on reconnect,
 * which is the difference between "works offline" and "pretends to work offline".
 */
const VERSION   = "nebras-v1.0.0";
const SHELL     = `shell-${VERSION}`;
const DATA      = `data-${VERSION}`;
const FALLBACK  = "/offline";

const SHELL_ASSETS = [
  "/app", "/portal", "/agent", "/offline",
  "/styles.css", "/app.js", "/portal.js", "/agent.js",
  "/brand/favicon/favicon.svg",
  "/brand/favicon/icon-192.png",
  "/brand/favicon/icon-512.png",
  "/site.webmanifest",
];

// Read endpoints worth keeping a copy of for offline viewing.
const CACHEABLE_API = [
  "/api/meta", "/api/analytics/dashboard", "/api/ai/digest",
  "/api/deals", "/api/leads", "/api/accounts", "/api/contacts",
  "/api/activities", "/api/opportunities", "/api/products",
];

// ---------------------------------------------------------------- install
self.addEventListener("install", e => {
  e.waitUntil((async () => {
    const c = await caches.open(SHELL);
    // addAll fails atomically; add individually so one 404 can't break install
    await Promise.all(SHELL_ASSETS.map(u =>
      c.add(new Request(u, { cache: "reload" })).catch(() => {})));
    await self.skipWaiting();
  })());
});

// ---------------------------------------------------------------- activate
self.addEventListener("activate", e => {
  e.waitUntil((async () => {
    const keys = await caches.keys();
    await Promise.all(keys
      .filter(k => k !== SHELL && k !== DATA)
      .map(k => caches.delete(k)));
    if (self.registration.navigationPreload) {
      await self.registration.navigationPreload.enable();
    }
    await self.clients.claim();
  })());
});

// ---------------------------------------------------------------- IndexedDB queue
function idb() {
  return new Promise((res, rej) => {
    const r = indexedDB.open("nebras-sync", 1);
    r.onupgradeneeded = () => {
      const db = r.result;
      if (!db.objectStoreNames.contains("queue")) {
        db.createObjectStore("queue", { keyPath: "id", autoIncrement: true });
      }
    };
    r.onsuccess = () => res(r.result);
    r.onerror = () => rej(r.error);
  });
}

async function queueAdd(rec) {
  const db = await idb();
  return new Promise((res, rej) => {
    const tx = db.transaction("queue", "readwrite");
    tx.objectStore("queue").add(rec);
    tx.oncomplete = res; tx.onerror = () => rej(tx.error);
  });
}

async function queueAll() {
  const db = await idb();
  return new Promise((res, rej) => {
    const tx = db.transaction("queue", "readonly");
    const rq = tx.objectStore("queue").getAll();
    rq.onsuccess = () => res(rq.result || []);
    rq.onerror = () => rej(rq.error);
  });
}

async function queueDel(id) {
  const db = await idb();
  return new Promise(res => {
    const tx = db.transaction("queue", "readwrite");
    tx.objectStore("queue").delete(id);
    tx.oncomplete = res;
  });
}

async function notifyClients(msg) {
  const cs = await self.clients.matchAll({ includeUncontrolled: true });
  cs.forEach(c => c.postMessage(msg));
}

async function replayQueue() {
  const items = await queueAll();
  let ok = 0, fail = 0;
  for (const it of items) {
    try {
      const r = await fetch(it.url, {
        method: it.method,
        headers: it.headers,
        body: it.body,
      });
      if (r.ok || (r.status >= 400 && r.status < 500)) {
        // 4xx means the server rejected it — retrying forever would never help.
        await queueDel(it.id);
        r.ok ? ok++ : fail++;
      } else { fail++; }
    } catch { fail++; }
  }
  if (ok || fail) await notifyClients({ type: "sync-done", ok, fail });
  return { ok, fail };
}

self.addEventListener("sync", e => {
  if (e.tag === "nebras-sync") e.waitUntil(replayQueue());
});

self.addEventListener("message", e => {
  const d = e.data || {};
  if (d.type === "skip-waiting") self.skipWaiting();
  if (d.type === "replay") e.waitUntil(replayQueue());
  if (d.type === "queue-size") {
    e.waitUntil(queueAll().then(q =>
      e.source && e.source.postMessage({ type: "queue-size", n: q.length })));
  }
});

// ---------------------------------------------------------------- fetch
self.addEventListener("fetch", event => {
  const { request } = event;
  const url = new URL(request.url);
  if (url.origin !== self.location.origin) return;       // never touch 3rd-party
  if (request.method !== "GET") return event.respondWith(handleWrite(request));

  // navigations -> network first, shell fallback, offline page as last resort
  if (request.mode === "navigate") {
    return event.respondWith((async () => {
      try {
        const pre = await event.preloadResponse;
        if (pre) return pre;
        const net = await fetch(request);
        const c = await caches.open(SHELL);
        c.put(request, net.clone());
        return net;
      } catch {
        return (await caches.match(request)) ||
               (await caches.match(FALLBACK)) ||
               new Response("Offline", { status: 503 });
      }
    })());
  }

  const isAPI = url.pathname.startsWith("/api/");
  event.respondWith(isAPI ? apiFirst(request) : shellFirst(request));
});

// static: cache-first, refresh in background (stale-while-revalidate)
async function shellFirst(req) {
  const cached = await caches.match(req);
  const net = fetch(req).then(r => {
    if (r && r.status === 200) caches.open(SHELL).then(c => c.put(req, r.clone()));
    return r;
  }).catch(() => null);
  return cached || (await net) || new Response("", { status: 504 });
}

// api reads: network-first, fall back to the last good copy
async function apiFirst(req) {
  const url = new URL(req.url);
  const worth = CACHEABLE_API.some(p => url.pathname.startsWith(p));
  try {
    const net = await fetch(req);
    if (worth && net.status === 200) {
      const c = await caches.open(DATA);
      c.put(req, net.clone());
    }
    return net;
  } catch {
    const hit = await caches.match(req);
    if (hit) {
      // Flag it so the UI can show "viewing cached data"
      const h = new Headers(hit.headers);
      h.set("X-Nebras-Cache", "1");
      return new Response(await hit.blob(), { status: 200, headers: h });
    }
    return new Response(JSON.stringify({
      detail: "أنت غير متصل — لا توجد نسخة محفوظة لهذا الطلب",
      offline: true,
    }), { status: 503, headers: { "Content-Type": "application/json" } });
  }
}

// writes: try network, otherwise queue for replay
async function handleWrite(req) {
  try {
    return await fetch(req.clone());
  } catch {
    // Only queue idempotent-ish business writes, never auth.
    const u = new URL(req.url);
    if (u.pathname.includes("/auth/") || u.pathname.includes("/login")) {
      return new Response(JSON.stringify({ detail: "يتطلب اتصالاً بالإنترنت" }),
        { status: 503, headers: { "Content-Type": "application/json" } });
    }
    const body = await req.clone().text();
    const headers = {};
    req.headers.forEach((v, k) => { headers[k] = v; });
    await queueAdd({ url: req.url, method: req.method, headers, body, at: Date.now() });
    try { await self.registration.sync.register("nebras-sync"); } catch {}
    const q = await queueAll();
    await notifyClients({ type: "queued", n: q.length });
    return new Response(JSON.stringify({
      queued: true, ok: true,
      detail: "لا يوجد اتصال — تم حفظ العملية وستُرسل تلقائياً عند عودة الشبكة",
    }), { status: 202, headers: { "Content-Type": "application/json" } });
  }
}

// ---------------------------------------------------------------- push
self.addEventListener("push", e => {
  let d = { title: "NebrasCRM", body: "لديك تحديث جديد" };
  try { if (e.data) d = { ...d, ...e.data.json() }; } catch {}
  e.waitUntil(self.registration.showNotification(d.title, {
    body: d.body,
    icon: "/brand/favicon/icon-192.png",
    badge: "/brand/favicon/icon-96.png",
    dir: "rtl", lang: "ar",
    data: { url: d.url || "/app" },
    vibrate: [90, 40, 90],
  }));
});

self.addEventListener("notificationclick", e => {
  e.notification.close();
  const target = (e.notification.data && e.notification.data.url) || "/app";
  e.waitUntil((async () => {
    const cs = await self.clients.matchAll({ type: "window", includeUncontrolled: true });
    for (const c of cs) {
      if (c.url.includes(target) && "focus" in c) return c.focus();
    }
    return self.clients.openWindow(target);
  })());
});
