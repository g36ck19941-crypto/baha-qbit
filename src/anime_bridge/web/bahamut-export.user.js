// ==UserScript==
// @name         Anime Bridge - 巴哈姆特收藏自动同步
// @namespace    https://github.com/g36ck19941-crypto/baha-qbit
// @version      0.2.0
// @description  检测动画疯登录后自动同步收藏到本机 Anime Bridge；不导出 Cookie、密码或页面 HTML。
// @match        https://ani.gamer.com.tw/mygather.php*
// @grant        GM_xmlhttpRequest
// @connect      127.0.0.1
// @run-at       document-idle
// ==/UserScript==

(function () {
  "use strict";

  const FORMAT = "anime-bridge-bahamut-favorites";
  const MAX_PAGES = 50;
  const BUTTON_ID = "anime-bridge-export-favorites";
  const ENDPOINT = "__ANIME_BRIDGE_ENDPOINT__";
  const BRIDGE_TOKEN = "__ANIME_BRIDGE_BRIDGE_TOKEN__";
  const LAST_SYNC_KEY = "anime-bridge-last-auto-sync";
  const AUTO_SYNC_INTERVAL_MS = 6 * 60 * 60 * 1000;

  function canonicalPageUrl(raw) {
    const url = new URL(raw, location.href);
    if (url.origin !== location.origin || url.pathname !== "/mygather.php") return null;
    url.hash = "";
    return url.href;
  }

  function paginationLinks(doc, baseUrl) {
    const links = [];
    for (const anchor of doc.querySelectorAll("a[href]")) {
      const label = (anchor.textContent || "").trim();
      if (!/^(?:\d+|下一頁|下頁|next|›|»|>)$/i.test(label)) continue;
      const url = canonicalPageUrl(new URL(anchor.getAttribute("href"), baseUrl).href);
      if (url) links.push(url);
    }
    return links;
  }

  function extractFavorites(doc, pageNumber) {
    const rows = [];
    for (const anchor of doc.querySelectorAll(".theme-list-block a[href]")) {
      const name = anchor.querySelector(".theme-name");
      const title = (name?.textContent || "").replace(/\s+/g, " ").trim();
      if (!title) continue;
      const href = new URL(anchor.getAttribute("href"), location.origin);
      if (href.origin !== location.origin || href.pathname !== "/animeRef.php") continue;
      const snText = href.searchParams.get("sn");
      rows.push({
        title,
        href: href.href,
        sn: snText && /^\d+$/.test(snText) ? Number(snText) : null,
        page: pageNumber,
      });
    }
    return rows;
  }

  async function readPage(url, first) {
    if (first) return document;
    const response = await fetch(url, {
      credentials: "include",
      redirect: "follow",
      headers: { Accept: "text/html" },
    });
    if (!response.ok) throw new Error(`HTTP ${response.status}`);
    const html = await response.text();
    const parsed = new DOMParser().parseFromString(html, "text/html");
    if (/請稍候|just a moment/i.test(parsed.title || "")) {
      throw new Error("页面返回了人机验证，请先在浏览器中完成验证");
    }
    return parsed;
  }

  async function collectFavorites() {
    const start = canonicalPageUrl(location.href);
    if (!start) throw new Error("请在动画疯“我的动画”页面运行导出助手");
    const queue = [start];
    const queued = new Set(queue);
    const visited = new Set();
    const warnings = [];
    const favorites = new Map();

    while (queue.length && visited.size < MAX_PAGES) {
      const url = queue.shift();
      if (!url || visited.has(url)) continue;
      const pageNumber = visited.size + 1;
      try {
        const doc = await readPage(url, visited.size === 0);
        visited.add(url);
        const pageFavorites = extractFavorites(doc, pageNumber);
        const emptyCollection = (doc.body?.textContent || "").includes("目前沒有訂閱內容");
        if (pageNumber === 1 && pageFavorites.length === 0 && !emptyCollection) {
          throw new Error("未识别到收藏列表或空收藏标记，页面结构可能已变化");
        }
        for (const item of pageFavorites) {
          favorites.set(`${item.title}\n${item.href}`, item);
        }
        for (const next of paginationLinks(doc, url)) {
          if (!queued.has(next) && queued.size < MAX_PAGES) {
            queued.add(next);
            queue.push(next);
          }
        }
      } catch (error) {
        visited.add(url);
        warnings.push(`${url}: ${error instanceof Error ? error.message : String(error)}`);
      }
    }
    if (queue.length) warnings.push(`达到 ${MAX_PAGES} 页安全上限，可能仍有未扫描页面`);
    return {
      format: FORMAT,
      schema_version: 1,
      exported_at: new Date().toISOString(),
      source_url: start,
      pages_scanned: visited.size,
      complete: warnings.length === 0,
      warnings,
      favorites: [...favorites.values()],
    };
  }

  function pushToAnimeBridge(payload) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: "POST",
        url: ENDPOINT,
        headers: {
          "Content-Type": "application/json",
          "X-Anime-Bridge-Bridge-Token": BRIDGE_TOKEN,
        },
        data: JSON.stringify(payload),
        timeout: 120000,
        onload(response) {
          let body;
          try { body = JSON.parse(response.responseText); }
          catch (_) { reject(new Error(`本机服务返回了无法识别的响应（HTTP ${response.status}）`)); return; }
          if (response.status < 200 || response.status >= 300 || !body.ok) {
            reject(new Error(body.error || `本机服务返回 HTTP ${response.status}`));
            return;
          }
          resolve(body.result);
        },
        ontimeout() { reject(new Error("本机扫描超时，请保持 Anime Bridge 运行后重试")); },
        onerror() { reject(new Error("无法连接本机 Anime Bridge，请先启动程序")); },
      });
    });
  }

  if (document.getElementById(BUTTON_ID)) return;
  const button = document.createElement("button");
  button.id = BUTTON_ID;
  button.type = "button";
  button.textContent = "同步 Anime Bridge 收藏";
  Object.assign(button.style, {
    position: "fixed",
    right: "20px",
    bottom: "20px",
    zIndex: "2147483647",
    padding: "12px 16px",
    border: "1px solid #1f2937",
    borderRadius: "6px",
    background: "#f7c948",
    color: "#111827",
    font: "600 14px system-ui, sans-serif",
    cursor: "pointer",
  });
  async function synchronize({ manual = false } = {}) {
    button.disabled = true;
    button.textContent = "正在读取收藏…";
    try {
      const payload = await collectFavorites();
      if (!payload.complete) throw new Error(payload.warnings.join("；") || "收藏读取不完整");
      button.textContent = "正在生成候选笔记…";
      const result = await pushToAnimeBridge(payload);
      localStorage.setItem(LAST_SYNC_KEY, String(Date.now()));
      button.textContent = `已同步 ${payload.favorites.length} 项`;
      if (manual) alert(`Anime Bridge：已同步 ${payload.favorites.length} 个收藏，并生成 ${result.count} 个候选条目。`);
    } catch (error) {
      button.textContent = "同步失败，点击重试";
      if (manual) alert(`Anime Bridge 同步失败：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      button.disabled = false;
      if (!button.textContent.startsWith("已同步") && !button.textContent.startsWith("同步失败")) {
        button.textContent = "同步 Anime Bridge 收藏";
      }
    }
  }
  button.addEventListener("click", () => synchronize({ manual: true }));
  document.body.appendChild(button);

  const pageShowsCollection = document.querySelector(".theme-list-block")
    || (document.body?.textContent || "").includes("目前沒有訂閱內容");
  const lastSync = Number(localStorage.getItem(LAST_SYNC_KEY) || "0");
  if (pageShowsCollection && Date.now() - lastSync >= AUTO_SYNC_INTERVAL_MS) {
    setTimeout(() => synchronize(), 800);
  } else if (!pageShowsCollection) {
    button.textContent = "等待动画疯登录";
  }
})();
