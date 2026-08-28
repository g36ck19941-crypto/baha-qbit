"use strict";

const TOKEN = document.querySelector('meta[name="anime-bridge-token"]').content;
const root = document.documentElement;
const logEl = document.getElementById("activity-log");
let busyCount = 0;
let lastObsidianDeletePlan = null;

function setChoice(kind, value) {
  root.dataset[kind] = value;
  localStorage.setItem(`anime-bridge-${kind}`, value);
  document.querySelectorAll(`[data-${kind}-choice]`).forEach((button) => {
    button.classList.toggle("is-active", button.dataset[`${kind}Choice`] === value);
  });
}

function restoreDisplay() {
  setChoice("theme", localStorage.getItem("anime-bridge-theme") || "workbench");
  setChoice("density", localStorage.getItem("anime-bridge-density") || "standard");
}

function addLog(label, value, isError = false) {
  const entry = document.createElement("article");
  entry.className = `log-entry${isError ? " error" : ""}`;
  const stamp = document.createElement("time");
  stamp.textContent = new Intl.DateTimeFormat("zh-CN", { hour: "2-digit", minute: "2-digit", second: "2-digit" }).format(new Date());
  const body = document.createElement("pre");
  body.textContent = `${label}\n${typeof value === "string" ? value : JSON.stringify(value, null, 2)}`;
  entry.append(stamp, body);
  logEl.prepend(entry);
}

function setBusy(delta, label = "") {
  busyCount = Math.max(0, busyCount + delta);
  document.body.classList.toggle("is-busy", busyCount > 0);
  document.querySelectorAll("button").forEach((button) => {
    if (!button.closest("dialog")) button.disabled = busyCount > 0;
  });
  const status = document.getElementById("global-status");
  const dot = document.getElementById("status-dot");
  status.textContent = busyCount ? label : "本机服务就绪";
  dot.classList.toggle("ready", busyCount === 0);
}

async function api(path, payload = {}, label = "执行操作") {
  setBusy(1, label);
  addLog(label, "请求已发送");
  try {
    const response = await fetch(path, {
      method: "POST",
      headers: { "Content-Type": "application/json", "X-Anime-Bridge-Token": TOKEN },
      body: JSON.stringify(payload),
    });
    const data = await response.json();
    if (!response.ok || !data.ok) throw new Error(data.error || `HTTP ${response.status}`);
    addLog(`${label}完成`, data.result);
    return data.result;
  } catch (error) {
    addLog(`${label}被拒绝`, error.message, true);
    throw error;
  } finally {
    setBusy(-1);
  }
}

function formObject(form) {
  const data = new FormData(form);
  const result = Object.fromEntries(data.entries());
  for (const [name] of data.entries()) {
    const values = data.getAll(name);
    if (values.length > 1) result[name] = values;
  }
  return result;
}

function showView(name) {
  document.querySelectorAll(".view").forEach((view) => view.classList.toggle("is-active", view.id === `view-${name}`));
  document.querySelectorAll(".nav-item").forEach((item) => item.classList.toggle("is-active", item.dataset.view === name));
}

function renderStatus(status) {
  document.getElementById("version").textContent = `V${status.version} · LOCAL WORKBENCH`;
  const list = document.getElementById("milestones");
  list.replaceChildren(...status.milestones.map((item, index) => {
    const row = document.createElement("div");
    row.className = "milestone";
    row.innerHTML = `<span class="index">${String(index + 1).padStart(2, "0")}</span><span></span><span class="state"></span>`;
    row.children[1].textContent = item.name;
    const stateLabels = { ready: "已建立", bridge_ready: "助手就绪" };
    row.children[2].textContent = stateLabels[item.state] || item.state;
    row.children[2].classList.add(item.state);
    return row;
  }));
  const settings = document.getElementById("settings-form");
  Object.entries(status.settings).forEach(([key, value]) => { settings.elements[key].value = value; });
  document.getElementById("runner-path").value = status.runner_path || "";
}

function askConfirmation(title, copy) {
  const dialog = document.getElementById("confirm-dialog");
  document.getElementById("confirm-title").textContent = title;
  document.getElementById("confirm-copy").textContent = copy;
  dialog.showModal();
  return new Promise((resolve) => {
    dialog.addEventListener("close", () => resolve(dialog.returnValue === "confirm"), { once: true });
  });
}

function browserInstallTarget() {
  const agent = navigator.userAgent;
  if (/Edg\//.test(agent)) {
    return { name: "Microsoft Edge", url: "https://www.tampermonkey.net/index.php?browser=edge" };
  }
  if (/Firefox\//.test(agent)) {
    return { name: "Mozilla Firefox", url: "https://www.tampermonkey.net/index.php?browser=firefox" };
  }
  if (/(?:Chrome|Chromium|CriOS)\//.test(agent)) {
    return { name: "Google Chrome / Chromium", url: "https://www.tampermonkey.net/index.php?browser=chrome" };
  }
  return { name: "未识别的浏览器", url: "https://www.tampermonkey.net/" };
}

function openBrowserHelperGuide() {
  const target = browserInstallTarget();
  document.getElementById("detected-browser").textContent = target.name;
  document.getElementById("open-tampermonkey").href = target.url;
  document.getElementById("browser-helper-dialog").showModal();
}

document.querySelectorAll("[data-theme-choice]").forEach((button) => button.addEventListener("click", () => setChoice("theme", button.dataset.themeChoice)));
document.querySelectorAll("[data-density-choice]").forEach((button) => button.addEventListener("click", () => setChoice("density", button.dataset.densityChoice)));
document.querySelectorAll(".nav-item").forEach((button) => button.addEventListener("click", () => showView(button.dataset.view)));
document.getElementById("clear-log").addEventListener("click", () => logEl.replaceChildren());
document.getElementById("install-browser-helper").addEventListener("click", openBrowserHelperGuide);

document.getElementById("scan-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try {
    const result = await api("/api/scan", formObject(event.currentTarget), "扫描当前季度并执行巴哈差集");
    document.getElementById("candidate-path").value = result.output;
    showView("obsidian");
  } catch (_) {}
});

document.getElementById("obsidian-plan").addEventListener("click", async () => {
  try { await api("/api/obsidian/plan", formObject(document.getElementById("obsidian-form")), "预览 Obsidian 入库"); } catch (_) {}
});
document.getElementById("obsidian-apply").addEventListener("click", async () => {
  const confirmed = await askConfirmation("正式归入动画库？", "将重新读取所有已勾选条目。任何目标冲突都会拒绝整批写入。此操作会创建 Markdown 文件。");
  if (!confirmed) return;
  try { await api("/api/obsidian/apply", { ...formObject(document.getElementById("obsidian-form")), confirmed: true }, "正式归入 Obsidian"); } catch (_) {}
});
document.getElementById("obsidian-library-refresh").addEventListener("click", async () => {
  try {
    const result = await api("/api/obsidian/library", {}, "读取 Obsidian 动画库");
    const select = document.getElementById("obsidian-library-select");
    select.replaceChildren(...result.items.map((item) => {
      const option = document.createElement("option");
      option.value = item.relative_path;
      option.textContent = `${item.title} · ${item.relative_path}`;
      return option;
    }));
    if (!result.items.length) {
      const option = document.createElement("option");
      option.value = "";
      option.textContent = "当前没有可管理的 bangumi 笔记";
      select.append(option);
    }
    lastObsidianDeletePlan = null;
  } catch (_) {}
});
document.getElementById("obsidian-delete-plan").addEventListener("click", async () => {
  try {
    lastObsidianDeletePlan = await api(
      "/api/obsidian/delete-plan",
      formObject(document.getElementById("obsidian-delete-form")),
      "预览 Obsidian 动画删除",
    );
  } catch (_) { lastObsidianDeletePlan = null; }
});
document.getElementById("obsidian-delete-apply").addEventListener("click", async () => {
  const selected = document.getElementById("obsidian-library-select").value;
  if (!lastObsidianDeletePlan || lastObsidianDeletePlan.relative_path !== selected) {
    addLog("删除被拒绝", "请先为当前选中的动画生成删除预览。", true);
    return;
  }
  const confirmed = await askConfirmation(
    `从动画库删除「${lastObsidianDeletePlan.title}」？`,
    `笔记将移至 ${lastObsidianDeletePlan.trash_relative_path}，可以手动恢复。`,
  );
  if (!confirmed) return;
  try {
    await api("/api/obsidian/delete-apply", {
      relative_path: selected,
      expected_sha256: lastObsidianDeletePlan.sha256,
      confirmed: true,
    }, "删除 Obsidian 动画笔记");
    lastObsidianDeletePlan = null;
    document.getElementById("obsidian-library-refresh").click();
  } catch (_) {}
});

document.getElementById("qbit-check").addEventListener("click", async () => {
  try { await api("/api/qbit/status", {}, "读取 qBittorrent RSS 状态"); } catch (_) {}
});
document.getElementById("rss-plan").addEventListener("click", async () => {
  try { await api("/api/qbit/plan", formObject(document.getElementById("rss-form")), "预览 RSS 规则"); } catch (_) {}
});
document.getElementById("rss-apply").addEventListener("click", async () => {
  const confirmed = await askConfirmation("创建 RSS 订阅与规则？", "这会改变 qBittorrent。新规则保持禁用，匹配任务保持暂停；创建过程不是原子事务。");
  if (!confirmed) return;
  try { await api("/api/qbit/apply", { ...formObject(document.getElementById("rss-form")), confirmed: true }, "创建 RSS 订阅和规则"); } catch (_) {}
});

document.getElementById("settings-form").addEventListener("submit", async (event) => {
  event.preventDefault();
  try { await api("/api/settings", formObject(event.currentTarget), "保存本机设置"); } catch (_) {}
});
document.getElementById("rss-batch-plan").addEventListener("click", async () => {
  try { await api("/api/qbit/batch-plan", formObject(document.getElementById("rss-batch-form")), "预览批量 RSS 草案"); } catch (_) {}
});
document.getElementById("rss-batch-apply").addEventListener("click", async () => {
  const confirmed = await askConfirmation("批量创建 RSS 订阅与规则？", "将为候选笔记中每个已勾选动画创建一个订阅和规则。规则全部禁用，下载全部暂停；qBittorrent API 不支持事务，中途失败可能留下部分项目。");
  if (!confirmed) return;
  try { await api("/api/qbit/batch-apply", { ...formObject(document.getElementById("rss-batch-form")), confirmed: true }, "批量创建 RSS 订阅和规则"); } catch (_) {}
});
document.getElementById("migration-plan").addEventListener("click", async () => {
  try { await api("/api/migration/plan", { runner_path: document.getElementById("runner-path").value }, "预览迁移安装"); } catch (_) {}
});
document.getElementById("migration-auto-repair").addEventListener("click", async () => {
  try {
    const plan = await api("/api/migration/plan", {}, "自动检测 Obsidian 集成");
    if (plan.plugin_state === "current" && plan.repairs.length === 0) {
      addLog("自动检测结果", "当前运行路径和 Obsidian 插件均有效，无需修复。");
      return;
    }
    const ok = await askConfirmation(
      "修复 Obsidian 集成？",
      `将使用当前软件路径修复 ${plan.repairs.length} 个受管文件。不会覆盖无法确认身份的插件目录。`,
    );
    if (!ok) return;
    await api("/api/migration/apply", { confirmed: true }, "自动修复 Obsidian 集成");
  } catch (_) {}
});
document.getElementById("migration-apply").addEventListener("click", async () => {
  const confirmed = await askConfirmation("安装 Obsidian 集成？", "将把 Anime Bridge 插件安装到当前 Vault 并保存非敏感本机设置。已有不同文件时会整批拒绝，安装后仍需在 Obsidian 中手动启用。");
  if (!confirmed) return;
  try { await api("/api/migration/apply", { runner_path: document.getElementById("runner-path").value, confirmed: true }, "安装 Obsidian 集成"); } catch (_) {}
});
document.getElementById("shutdown").addEventListener("click", async () => {
  if (!confirm("结束 Anime Bridge 本机界面服务？")) return;
  try {
    await api("/api/shutdown", {}, "结束本机界面服务");
    document.getElementById("global-status").textContent = "服务已结束，可以关闭此页面";
  } catch (_) {}
});

restoreDisplay();
api("/api/status", {}, "读取项目状态").then(renderStatus).catch(() => {});
