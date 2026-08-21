// ==UserScript==
// @name         Anime Bridge - 巴哈姆特收藏导出
// @namespace    https://github.com/g36ck19941-crypto/baha-qbit
// @version      0.1.0
// @description  在已登录的动画疯“我的动画”页面导出收藏；不导出 Cookie、密码或页面 HTML。
// @match        https://ani.gamer.com.tw/mygather.php*
// @grant        none
// @run-at       document-idle
// ==/UserScript==

(function () {
  "use strict";

  const FORMAT = "anime-bridge-bahamut-favorites";
  const MAX_PAGES = 50;
  const BUTTON_ID = "anime-bridge-export-favorites";

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

  function downloadJson(payload) {
    const date = new Date().toISOString().slice(0, 10).replaceAll("-", "");
    const blob = new Blob([`${JSON.stringify(payload, null, 2)}\n`], {
      type: "application/json;charset=utf-8",
    });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = `anime-bridge-bahamut-favorites-${date}.json`;
    document.body.appendChild(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(link.href), 1000);
  }

  if (document.getElementById(BUTTON_ID)) return;
  const button = document.createElement("button");
  button.id = BUTTON_ID;
  button.type = "button";
  button.textContent = "导出 Anime Bridge 收藏";
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
  button.addEventListener("click", async () => {
    button.disabled = true;
    button.textContent = "正在读取收藏…";
    try {
      const payload = await collectFavorites();
      downloadJson(payload);
      const suffix = payload.warnings.length ? `，${payload.warnings.length} 条警告` : "";
      alert(`Anime Bridge：已导出 ${payload.favorites.length} 个收藏，共扫描 ${payload.pages_scanned} 页${suffix}。`);
    } catch (error) {
      alert(`Anime Bridge 导出失败：${error instanceof Error ? error.message : String(error)}`);
    } finally {
      button.disabled = false;
      button.textContent = "导出 Anime Bridge 收藏";
    }
  });
  document.body.appendChild(button);
})();
