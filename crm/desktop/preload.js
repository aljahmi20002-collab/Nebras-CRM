/* Preload — the only bridge between the renderer and Node.
 * Nothing here exposes raw IPC or fs; each call is an explicit, narrow verb.
 */
const { contextBridge, ipcRenderer } = require("electron");

contextBridge.exposeInMainWorld("nebrasDesktop", {
  version: "1.0.0",
  platform: process.platform,

  getConfig: () => ipcRenderer.invoke("cfg:get"),
  setConfig: (patch) => ipcRenderer.invoke("cfg:set", patch),
  appInfo: () => ipcRenderer.invoke("app:info"),
  testServer: (url) => ipcRenderer.invoke("app:test", url),

  closeSettings: () => ipcRenderer.send("win:close-settings"),
  relaunch: () => ipcRenderer.send("app:relaunch"),
});

// Let the web app know it is running inside the desktop shell so it can adapt
// (e.g. hide the browser install prompt, show native-only affordances).
window.addEventListener("DOMContentLoaded", () => {
  document.documentElement.classList.add("nb-desktop");
});
