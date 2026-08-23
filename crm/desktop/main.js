/* NebrasCRM Desktop — Electron main process.
 *
 * Design notes:
 *  - The desktop app is a *native shell around the real server*, not a fork of
 *    the UI. One codebase, so features never drift between web and desktop.
 *  - Security is not optional in a shell that loads remote content: context
 *    isolation on, node integration off, a strict navigation allowlist, and
 *    external links forced to the system browser.
 *  - The server URL is user-configurable and persisted, because every customer
 *    self-hosts on their own domain.
 */
const {
  app, BrowserWindow, Menu, Tray, shell, ipcMain, dialog,
  nativeImage, nativeTheme, session, globalShortcut, powerMonitor,
} = require("electron");
const path = require("path");
const fs = require("fs");

const isDev = !!process.env.NEBRAS_DEV;
const isMac = process.platform === "darwin";

// ---------------------------------------------------------------- config
const CONFIG_FILE = path.join(app.getPath("userData"), "config.json");
const DEFAULTS = {
  serverUrl: "http://localhost:8000",
  lang: "ar",
  startMinimized: false,
  minimizeToTray: true,
  hardwareAcceleration: true,
  zoom: 1,
  bounds: null,
};

function loadConfig() {
  try {
    return { ...DEFAULTS, ...JSON.parse(fs.readFileSync(CONFIG_FILE, "utf8")) };
  } catch { return { ...DEFAULTS }; }
}
function saveConfig(patch) {
  cfg = { ...cfg, ...patch };
  try {
    fs.mkdirSync(path.dirname(CONFIG_FILE), { recursive: true });
    fs.writeFileSync(CONFIG_FILE, JSON.stringify(cfg, null, 2));
  } catch (e) { console.error("config save failed", e); }
  return cfg;
}
let cfg = loadConfig();

if (!cfg.hardwareAcceleration) app.disableHardwareAcceleration();

// single instance — a second launch focuses the existing window
if (!app.requestSingleInstanceLock()) { app.quit(); process.exit(0); }

let win = null, tray = null, splash = null, settingsWin = null;
const T = () => (cfg.lang === "ar" ? AR : EN);

const AR = {
  dashboard: "لوحة التحكم", ai: "المساعد الذكي", customers: "بوابة العملاء",
  partners: "بوابة الشركاء", file: "ملف", edit: "تحرير", view: "عرض",
  window: "نافذة", help: "مساعدة", settings: "الإعدادات", reload: "تحديث",
  back: "رجوع", forward: "تقدّم", zoomIn: "تكبير", zoomOut: "تصغير",
  zoomReset: "الحجم الأصلي", fullscreen: "ملء الشاشة", devtools: "أدوات المطوّر",
  quit: "خروج", show: "إظهار النافذة", hide: "إخفاء", about: "حول البرنامج",
  offlineTitle: "تعذّر الاتصال بالخادم",
  offlineBody: "لم نتمكن من الوصول إلى:\n\n{url}\n\nتأكد من تشغيل الخادم ومن صحة العنوان في الإعدادات.",
  retry: "إعادة المحاولة", openSettings: "فتح الإعدادات", exit: "إغلاق",
  print: "طباعة", copy: "نسخ", paste: "لصق", cut: "قص", selectAll: "تحديد الكل",
  undo: "تراجع", redo: "إعادة", minimize: "تصغير", tray: "نبراس يعمل في الخلفية",
};
const EN = {
  dashboard: "Dashboard", ai: "AI Assistant", customers: "Customer Portal",
  partners: "Partner Portal", file: "File", edit: "Edit", view: "View",
  window: "Window", help: "Help", settings: "Settings", reload: "Reload",
  back: "Back", forward: "Forward", zoomIn: "Zoom In", zoomOut: "Zoom Out",
  zoomReset: "Actual Size", fullscreen: "Full Screen", devtools: "Developer Tools",
  quit: "Quit", show: "Show Window", hide: "Hide", about: "About",
  offlineTitle: "Cannot reach the server",
  offlineBody: "Could not connect to:\n\n{url}\n\nMake sure the server is running and the URL is correct in Settings.",
  retry: "Retry", openSettings: "Open Settings", exit: "Close",
  print: "Print", copy: "Copy", paste: "Paste", cut: "Cut", selectAll: "Select All",
  undo: "Undo", redo: "Redo", minimize: "Minimize", tray: "Nebras is running in the background",
};

function iconPath(name) {
  const p = path.join(__dirname, "build", name);
  return fs.existsSync(p) ? p : path.join(__dirname, "build", "icon.png");
}

// ---------------------------------------------------------------- splash
function createSplash() {
  splash = new BrowserWindow({
    width: 420, height: 300, frame: false, transparent: true,
    resizable: false, center: true, show: true, skipTaskbar: true,
    alwaysOnTop: true, backgroundColor: "#00000000",
  });
  splash.loadFile(path.join(__dirname, "splash.html"));
  splash.on("closed", () => { splash = null; });
}

// ---------------------------------------------------------------- main window
function createWindow() {
  const b = cfg.bounds || {};
  win = new BrowserWindow({
    width: b.width || 1440,
    height: b.height || 900,
    x: b.x, y: b.y,
    minWidth: 960, minHeight: 620,
    show: false,
    backgroundColor: nativeTheme.shouldUseDarkColors ? "#0F1420" : "#EEF2F8",
    icon: iconPath("icon.png"),
    title: "NebrasCRM",
    titleBarStyle: isMac ? "hiddenInset" : "default",
    trafficLightPosition: isMac ? { x: 14, y: 14 } : undefined,
    autoHideMenuBar: false,
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true,
      nodeIntegration: false,
      sandbox: false,
      webSecurity: true,
      spellcheck: true,
    },
  });

  if (cfg.zoom && cfg.zoom !== 1) {
    win.webContents.on("did-finish-load", () =>
      win.webContents.setZoomFactor(cfg.zoom));
  }

  loadApp();

  win.once("ready-to-show", () => {
    splash?.close();
    if (!cfg.startMinimized) { win.show(); win.focus(); }
  });

  // remember geometry
  const persist = () => {
    if (win && !win.isMaximized() && !win.isFullScreen()) {
      saveConfig({ bounds: win.getBounds() });
    }
  };
  win.on("resize", persist);
  win.on("move", persist);

  win.on("close", e => {
    if (cfg.minimizeToTray && !app.isQuitting) {
      e.preventDefault();
      win.hide();
      if (tray && !tray.__notified) {
        tray.displayBalloon?.({ title: "NebrasCRM", content: T().tray });
        tray.__notified = true;
      }
    }
  });
  win.on("closed", () => { win = null; });

  // failed load -> actionable dialog, not a blank white window
  win.webContents.on("did-fail-load", (_e, code, desc, url, isMainFrame) => {
    if (!isMainFrame || code === -3) return;   // -3 = user aborted
    splash?.close();
    showConnectionError();
  });

  // external links open in the real browser
  win.webContents.setWindowOpenHandler(({ url }) => {
    if (isInternal(url)) return { action: "allow" };
    shell.openExternal(url);
    return { action: "deny" };
  });

  // hard navigation allowlist
  win.webContents.on("will-navigate", (e, url) => {
    if (!isInternal(url)) { e.preventDefault(); shell.openExternal(url); }
  });

  // permissions: deny everything we don't explicitly need
  session.defaultSession.setPermissionRequestHandler((wc, perm, cb) => {
    cb(["notifications", "clipboard-read", "clipboard-sanitized-write"].includes(perm));
  });
}

function isInternal(u) {
  try {
    const target = new URL(u);
    const base = new URL(cfg.serverUrl);
    return target.origin === base.origin;
  } catch { return false; }
}

function loadApp(sub = "/app") {
  const url = cfg.serverUrl.replace(/\/+$/, "") + sub;
  win?.loadURL(url, { userAgent: `${session.defaultSession.getUserAgent()} NebrasDesktop/1.0.0` });
}

async function showConnectionError() {
  if (!win) return;
  const r = await dialog.showMessageBox(win, {
    type: "error",
    title: T().offlineTitle,
    message: T().offlineTitle,
    detail: T().offlineBody.replace("{url}", cfg.serverUrl),
    buttons: [T().retry, T().openSettings, T().exit],
    defaultId: 0, cancelId: 2, noLink: true,
  });
  if (r.response === 0) loadApp();
  else if (r.response === 1) openSettings();
  else { app.isQuitting = true; app.quit(); }
}

// ---------------------------------------------------------------- settings window
function openSettings() {
  if (settingsWin) { settingsWin.focus(); return; }
  settingsWin = new BrowserWindow({
    width: 520, height: 560, parent: win || undefined, modal: false,
    resizable: false, minimizable: false, maximizable: false,
    title: T().settings, icon: iconPath("icon.png"),
    backgroundColor: nativeTheme.shouldUseDarkColors ? "#0F1420" : "#EEF2F8",
    webPreferences: {
      preload: path.join(__dirname, "preload.js"),
      contextIsolation: true, nodeIntegration: false,
    },
  });
  settingsWin.setMenu(null);
  settingsWin.loadFile(path.join(__dirname, "settings.html"));
  settingsWin.on("closed", () => { settingsWin = null; });
}

// ---------------------------------------------------------------- tray
function createTray() {
  const img = nativeImage.createFromPath(iconPath("tray.png"));
  tray = new Tray(img.isEmpty() ? nativeImage.createFromPath(iconPath("icon.png")) : img);
  tray.setToolTip("NebrasCRM");
  rebuildTray();
  tray.on("click", () => {
    if (!win) return createWindow();
    win.isVisible() ? win.hide() : (win.show(), win.focus());
  });
}

function rebuildTray() {
  if (!tray) return;
  const t = T();
  tray.setContextMenu(Menu.buildFromTemplate([
    { label: t.show, click: () => { win ? (win.show(), win.focus()) : createWindow(); } },
    { type: "separator" },
    { label: t.dashboard, click: () => { loadApp("/app"); win?.show(); } },
    { label: t.ai, click: () => { loadApp("/app?view=ai"); win?.show(); } },
    { label: t.customers, click: () => { loadApp("/portal"); win?.show(); } },
    { label: t.partners, click: () => { loadApp("/agent"); win?.show(); } },
    { type: "separator" },
    { label: t.settings, click: openSettings },
    { label: t.quit, click: () => { app.isQuitting = true; app.quit(); } },
  ]));
}

// ---------------------------------------------------------------- menu
function buildMenu() {
  const t = T();
  const template = [
    ...(isMac ? [{
      label: "NebrasCRM",
      submenu: [
        { label: t.about, role: "about" },
        { type: "separator" },
        { label: t.settings, accelerator: "Cmd+,", click: openSettings },
        { type: "separator" },
        { role: "services" }, { type: "separator" },
        { role: "hide", label: t.hide }, { role: "hideOthers" }, { role: "unhide" },
        { type: "separator" },
        { label: t.quit, accelerator: "Cmd+Q",
          click: () => { app.isQuitting = true; app.quit(); } },
      ],
    }] : []),
    {
      label: t.file,
      submenu: [
        { label: t.dashboard, accelerator: "CmdOrCtrl+1", click: () => loadApp("/app") },
        { label: t.ai, accelerator: "CmdOrCtrl+2", click: () => loadApp("/app?view=ai") },
        { label: t.customers, accelerator: "CmdOrCtrl+3", click: () => loadApp("/portal") },
        { label: t.partners, accelerator: "CmdOrCtrl+4", click: () => loadApp("/agent") },
        { type: "separator" },
        { label: t.print, accelerator: "CmdOrCtrl+P",
          click: () => win?.webContents.print({}) },
        ...(isMac ? [] : [
          { type: "separator" },
          { label: t.settings, accelerator: "Ctrl+,", click: openSettings },
          { type: "separator" },
          { label: t.quit, accelerator: "Alt+F4",
            click: () => { app.isQuitting = true; app.quit(); } },
        ]),
      ],
    },
    {
      label: t.edit,
      submenu: [
        { role: "undo", label: t.undo }, { role: "redo", label: t.redo },
        { type: "separator" },
        { role: "cut", label: t.cut }, { role: "copy", label: t.copy },
        { role: "paste", label: t.paste }, { role: "selectAll", label: t.selectAll },
      ],
    },
    {
      label: t.view,
      submenu: [
        { label: t.reload, accelerator: "CmdOrCtrl+R", click: () => win?.webContents.reload() },
        { label: t.back, accelerator: "Alt+Left",
          click: () => win?.webContents.canGoBack() && win.webContents.goBack() },
        { label: t.forward, accelerator: "Alt+Right",
          click: () => win?.webContents.canGoForward() && win.webContents.goForward() },
        { type: "separator" },
        { label: t.zoomIn, accelerator: "CmdOrCtrl+Plus", click: () => zoom(+0.1) },
        { label: t.zoomOut, accelerator: "CmdOrCtrl+-", click: () => zoom(-0.1) },
        { label: t.zoomReset, accelerator: "CmdOrCtrl+0", click: () => zoom(0, true) },
        { type: "separator" },
        { role: "togglefullscreen", label: t.fullscreen },
        { label: t.devtools, accelerator: "F12",
          click: () => win?.webContents.toggleDevTools() },
      ],
    },
    {
      label: t.window,
      submenu: [
        { role: "minimize", label: t.minimize },
        ...(isMac ? [{ role: "zoom" }, { type: "separator" }, { role: "front" }] : []),
      ],
    },
    {
      label: t.help,
      submenu: [
        { label: "nebrascrm.io", click: () => shell.openExternal("https://nebrascrm.io") },
        { label: t.about, click: showAbout },
      ],
    },
  ];
  Menu.setApplicationMenu(Menu.buildFromTemplate(template));
}

function zoom(delta, reset) {
  if (!win) return;
  const z = reset ? 1 : Math.min(2.5, Math.max(0.5, win.webContents.getZoomFactor() + delta));
  win.webContents.setZoomFactor(z);
  saveConfig({ zoom: z });
}

function showAbout() {
  dialog.showMessageBox(win, {
    type: "info",
    title: T().about,
    message: "NebrasCRM — نِبراس سي آر إم",
    detail:
      `${cfg.lang === "ar" ? "الإصدار" : "Version"}: ${app.getVersion()}\n` +
      `Electron: ${process.versions.electron}\n` +
      `Chromium: ${process.versions.chrome}\n\n` +
      `${cfg.lang === "ar" ? "الخادم" : "Server"}: ${cfg.serverUrl}`,
    icon: nativeImage.createFromPath(iconPath("icon.png")),
    buttons: ["OK"],
  });
}

// ---------------------------------------------------------------- IPC
ipcMain.handle("cfg:get", () => cfg);
ipcMain.handle("cfg:set", (_e, patch) => {
  const before = cfg.serverUrl, beforeLang = cfg.lang;
  saveConfig(patch);
  if (patch.lang && patch.lang !== beforeLang) { buildMenu(); rebuildTray(); }
  if (patch.serverUrl && patch.serverUrl !== before) loadApp();
  return cfg;
});
ipcMain.handle("app:info", () => ({
  version: app.getVersion(),
  electron: process.versions.electron,
  chrome: process.versions.chrome,
  platform: process.platform,
  arch: process.arch,
}));
ipcMain.handle("app:test", async (_e, url) => {
  try {
    const res = await fetch(url.replace(/\/+$/, "") + "/api/meta", { method: "GET" });
    return { ok: res.status === 200 || res.status === 401, status: res.status };
  } catch (e) { return { ok: false, error: String(e.message || e) }; }
});
ipcMain.on("win:close-settings", () => settingsWin?.close());
ipcMain.on("app:relaunch", () => { app.relaunch(); app.isQuitting = true; app.quit(); });

// ---------------------------------------------------------------- lifecycle
app.on("second-instance", () => {
  if (win) { if (win.isMinimized()) win.restore(); win.show(); win.focus(); }
});

app.whenReady().then(() => {
  if (process.platform === "win32") app.setAppUserModelId("io.nebrascrm.desktop");
  createSplash();
  setTimeout(() => { createWindow(); buildMenu(); createTray(); }, 550);

  globalShortcut.register("CommandOrControl+Shift+N", () => {
    if (!win) return createWindow();
    win.isVisible() && win.isFocused() ? win.hide() : (win.show(), win.focus());
  });

  // reconnect after the machine wakes — sessions and sockets go stale on sleep
  powerMonitor.on("resume", () => {
    if (win && !win.webContents.isLoading()) win.webContents.reload();
  });

  app.on("activate", () => {
    if (BrowserWindow.getAllWindows().length === 0) createWindow();
    else win?.show();
  });
});

app.on("before-quit", () => { app.isQuitting = true; });
app.on("will-quit", () => globalShortcut.unregisterAll());
app.on("window-all-closed", () => { if (!isMac) app.quit(); });

// never let remote content spawn a node-enabled webview
app.on("web-contents-created", (_e, contents) => {
  contents.on("will-attach-webview", (ev) => ev.preventDefault());
});
