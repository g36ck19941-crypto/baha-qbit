"use strict";

const { Plugin, PluginSettingTab, Setting, Notice, Modal } = require("obsidian");
const { spawn } = require("child_process");
const path = require("path");
const { reorderCheckedCandidates } = require("./candidate-sort");

const DEFAULT_SETTINGS = {
  runnerPath: "",
  launcherPath: "",
  formalRoot: "C/bangumi",
  pinCheckedOnOpen: true,
};

class ConfirmApplyModal extends Modal {
  constructor(app, onConfirm) {
    super(app);
    this.onConfirm = onConfirm;
  }

  onOpen() {
    const { contentEl } = this;
    contentEl.createEl("h2", { text: "正式归入动画库？" });
    contentEl.createEl("p", {
      text: "Anime Bridge 将重新读取已勾选条目并写入正式笔记。若任一目标已存在，整批操作会拒绝。",
    });
    const row = contentEl.createDiv({ cls: "anime-bridge-actions" });
    const cancel = row.createEl("button", { text: "取消" });
    cancel.addEventListener("click", () => this.close());
    const confirm = row.createEl("button", {
      text: "确认归入",
      cls: "mod-cta",
    });
    confirm.addEventListener("click", () => {
      this.close();
      this.onConfirm();
    });
  }

  onClose() {
    this.contentEl.empty();
  }
}

class AnimeBridgePlugin extends Plugin {
  async onload() {
    this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());
    this.addSettingTab(new AnimeBridgeSettingTab(this.app, this));
    this.registerEvent(
      this.app.workspace.on("file-open", (file) => this.pinCheckedCandidates(file)),
    );

    this.addCommand({
      id: "preview-checked-candidates",
      name: "预览已勾选动画的正式归入计划",
      checkCallback: (checking) => this.candidateCommand(checking, false),
    });
    this.addCommand({
      id: "apply-checked-candidates",
      name: "正式归入已勾选动画",
      checkCallback: (checking) => this.candidateCommand(checking, true),
    });
  }

  async pinCheckedCandidates(file) {
    if (!this.settings.pinCheckedOnOpen || !file || file.extension !== "md") return;
    const content = await this.app.vault.read(file);
    const reordered = reorderCheckedCandidates(content);
    if (reordered === content) return;
    await this.app.vault.modify(file, reordered);
    new Notice("Anime Bridge 已将勾选动画置顶。", 5000);
  }

  candidateCommand(checking, apply) {
    const file = this.app.workspace.getActiveFile();
    const eligible = Boolean(file && file.extension === "md");
    if (checking) return eligible;
    if (!eligible) return false;
    if (apply) {
      new ConfirmApplyModal(this.app, () => this.runImport(file, true)).open();
    } else {
      this.runImport(file, false);
    }
    return true;
  }

  async runImport(file, apply) {
    if (!this.settings.runnerPath) {
      new Notice("请先在 Anime Bridge 设置中配置运行程序路径。", 7000);
      return;
    }
    const content = await this.app.vault.read(file);
    if (!content.includes("anime_bridge_document: candidates")) {
      new Notice("当前笔记不是 Anime Bridge 候选文档。", 7000);
      return;
    }

    const vaultPath = this.app.vault.adapter.getBasePath();
    const candidatePath = path.join(vaultPath, file.path);
    const planPath = path.join(vaultPath, ".anime-bridge", "obsidian-import-plan.json");
    const args = [];
    if (this.settings.launcherPath) args.push(this.settings.launcherPath);
    args.push(
      "obsidian-import",
      candidatePath,
      "--vault",
      vaultPath,
      "--formal-root",
      this.settings.formalRoot,
      "--plan-output",
      planPath,
    );
    if (apply) args.push("--apply");

    new Notice(apply ? "正在正式归入……" : "正在生成归入预览……");
    try {
      const result = await runProcess(this.settings.runnerPath, args);
      new Notice(result.stdout.trim() || "Anime Bridge 操作完成。", 10000);
    } catch (error) {
      new Notice(`Anime Bridge 拒绝操作：${error.message}`, 12000);
      console.error("Anime Bridge", error);
    }
  }
}

class AnimeBridgeSettingTab extends PluginSettingTab {
  constructor(app, plugin) {
    super(app, plugin);
    this.plugin = plugin;
  }

  display() {
    const { containerEl } = this;
    containerEl.empty();
    containerEl.createEl("h2", { text: "Anime Bridge 设置" });

    new Setting(containerEl)
      .setName("运行程序")
      .setDesc("打包后选择 anime-bridge.exe；源码开发时选择 Python 解释器。")
      .addText((text) =>
        text.setValue(this.plugin.settings.runnerPath).onChange(async (value) => {
          this.plugin.settings.runnerPath = value.trim();
          await this.plugin.saveData(this.plugin.settings);
        }),
      );
    new Setting(containerEl)
      .setName("源码启动文件（可选）")
      .setDesc("仅源码模式填写 launcher.py 的绝对路径；使用 exe 时留空。")
      .addText((text) =>
        text.setValue(this.plugin.settings.launcherPath).onChange(async (value) => {
          this.plugin.settings.launcherPath = value.trim();
          await this.plugin.saveData(this.plugin.settings);
        }),
      );
    new Setting(containerEl)
      .setName("正式动画目录")
      .setDesc("相对于 Vault 的目录，保持与动画库.base 现有笔记一致。")
      .addText((text) =>
        text.setValue(this.plugin.settings.formalRoot).onChange(async (value) => {
          this.plugin.settings.formalRoot = value.trim() || DEFAULT_SETTINGS.formalRoot;
          await this.plugin.saveData(this.plugin.settings);
        }),
      );
    new Setting(containerEl)
      .setName("打开候选笔记时将勾选动画置顶")
      .setDesc("只重排 Anime Bridge 生成的候选条目，保持勾选组和未勾选组各自原有顺序。")
      .addToggle((toggle) =>
        toggle.setValue(this.plugin.settings.pinCheckedOnOpen).onChange(async (value) => {
          this.plugin.settings.pinCheckedOnOpen = value;
          await this.plugin.saveData(this.plugin.settings);
        }),
      );
  }
}

function runProcess(executable, args) {
  return new Promise((resolve, reject) => {
    const child = spawn(executable, args, { windowsHide: true, shell: false });
    let stdout = "";
    let stderr = "";
    child.stdout.on("data", (chunk) => { stdout += chunk.toString("utf8"); });
    child.stderr.on("data", (chunk) => { stderr += chunk.toString("utf8"); });
    child.on("error", (error) => reject(error));
    child.on("close", (code) => {
      if (code === 0) resolve({ stdout, stderr });
      else reject(new Error(stderr.trim() || stdout.trim() || `退出码 ${code}`));
    });
  });
}

module.exports = AnimeBridgePlugin;
