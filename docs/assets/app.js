const DEFAULT_API_BASE = "http://127.0.0.1:8000";

const state = {
  apiBase: "",
  apiHealth: {
    base: "",
    checkedAt: 0,
    ok: false,
  },
  hits: [],
  lastQueries: [],
  mode: "single",
  outputEntries: [],
  selectedIndex: -1,
};

const elements = {
  bibtexOutput: document.querySelector("#bibtex-output"),
  copyButton: document.querySelector("#copy-button"),
  customPattern: document.querySelector("#custom-pattern"),
  customPatternGroup: document.querySelector("#custom-pattern-group"),
  downloadButton: document.querySelector("#download-button"),
  paperTitle: document.querySelector("#paper-title"),
  publicationPreference: document.querySelector("#publication-preference"),
  settingsDrawer: document.querySelector("#settings-drawer"),
  settingsOverlay: document.querySelector("#settings-overlay"),
  openSettings: document.querySelector("#open-settings"),
  closeSettings: document.querySelector("#close-settings"),
  renameStyle: document.querySelector("#rename-style"),
  resultLimit: document.querySelector("#result-limit"),
  resultSort: document.querySelector("#result-sort"),
  results: document.querySelector("#results"),
  resultTemplate: document.querySelector("#result-card-template"),
  searchButton: document.querySelector("#search-button"),
  searchForm: document.querySelector("#search-form"),
  selectedKey: document.querySelector("#selected-key"),
  selectedPaper: document.querySelector("#selected-paper"),
  status: document.querySelector("#status"),
};

elements.searchForm.addEventListener("submit", handleSearch);
elements.paperTitle.addEventListener("keydown", handlePaperTitleKeydown);
elements.openSettings.addEventListener("click", openSettingsDrawer);
elements.closeSettings.addEventListener("click", closeSettingsDrawer);
elements.settingsOverlay.addEventListener("click", closeSettingsDrawer);
elements.renameStyle.addEventListener("change", () => {
  handleRenameStyleChange();
});
elements.resultSort.addEventListener("change", () => {
  void handleResultSortChange();
});
elements.customPattern.addEventListener("input", handleCustomPatternInput);
elements.copyButton.addEventListener("click", copyBibtex);
elements.downloadButton.addEventListener("click", downloadBibtex);
document.addEventListener("keydown", handleGlobalKeydown);

handleRenameStyleChange();

async function handleSearch(event) {
  event.preventDefault();

  const queries = parseQueries(elements.paperTitle.value);
  if (!queries.length) {
    setStatus("请输入论文标题。", true);
    return;
  }

  setLoading(true);
  try {
    setStatus("正在检查服务状态...");
    const healthy = await ensureApiHealthy();
    if (!healthy) {
      return;
    }

    state.lastQueries = queries;
    setStatus(
      queries.length > 1 ? `正在通过 API 批量处理 ${queries.length} 篇论文...` : "正在通过 API 搜索...",
    );
    elements.results.innerHTML = "";
    clearSelection();

    const searchTask =
      queries.length > 1 ? handleBatchSearch(queries) : handleSingleSearch(queries[0]);
    await withTimeout(searchTask, 60000, "搜索超时（>60s），请稍后重试。");
  } catch (error) {
    console.error(error);
    setStatus(error.message || "查询失败，请稍后再试。", true);
  } finally {
    setLoading(false);
  }
}

function parseQueries(value) {
  return value
    .split("\n")
    .map((line) => line.trim())
    .filter(Boolean);
}

function handlePaperTitleKeydown(event) {
  if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
    event.preventDefault();
    elements.searchForm.requestSubmit();
  }
}

function handleGlobalKeydown(event) {
  if (event.key === "Escape") {
    closeSettingsDrawer();
  }
}

function openSettingsDrawer() {
  elements.settingsDrawer.classList.add("open");
  elements.settingsDrawer.setAttribute("aria-hidden", "false");
  elements.settingsOverlay.hidden = false;
  document.body.style.overflow = "hidden";
}

function closeSettingsDrawer() {
  elements.settingsDrawer.classList.remove("open");
  elements.settingsDrawer.setAttribute("aria-hidden", "true");
  elements.settingsOverlay.hidden = true;
  document.body.style.overflow = "";
}

async function handleSingleSearch(query) {
  const payload = await apiRequest(
    "/search",
    {
      limit: Number(elements.resultLimit.value),
      preference: elements.resultSort.value,
      title: query,
    },
    { timeoutMs: 12000 },
  );

  const hits = payload.candidates || [];
  state.mode = "single";
  state.hits = hits;
  state.outputEntries = [];
  state.selectedIndex = -1;

  if (!hits.length) {
    setStatus("没有找到匹配结果，可以试试更完整的标题或确认 API 已启动。", true);
    return;
  }

  renderResults();
  setStatus(`找到 ${hits.length} 条候选结果。请选择一条后再生成 BibTeX。`);
}

async function handleBatchSearch(queries) {
  state.mode = "batch";
  state.hits = [];
  state.outputEntries = [];
  state.selectedIndex = -1;

  const payload = await apiRequest(
    "/bibtex/batch",
    {
      custom_pattern: getCustomPattern(),
      limit: Number(elements.resultLimit.value),
      preference: elements.publicationPreference.value,
      rename_style: elements.renameStyle.value,
      titles: queries,
    },
    { timeoutMs: 45000 },
  );

  const items = payload.items || [];
  const entries = items
    .filter((item) => item.matched && item.selected_hit && item.bibtex)
    .map((item) => ({
      ...item.selected_hit,
      query: item.query,
      renamedBibtex: item.bibtex,
    }));

  if (!entries.length) {
    renderBatchSummary(items);
    setStatus("批量模式下没有找到任何匹配结果。", true);
    return;
  }

  state.outputEntries = entries;
  elements.selectedPaper.textContent = `已生成 ${entries.length} / ${queries.length} 篇`;
  elements.selectedKey.textContent =
    entries.length === 1 ? extractEntryKey(entries[0].renamedBibtex) : `${entries.length} entries`;
  elements.bibtexOutput.value = entries.map((entry) => entry.renamedBibtex).join("\n\n");

  renderBatchSummary(items);

  const missedCount = queries.length - entries.length;
  setStatus(
    missedCount
      ? `已生成 ${entries.length} 条 BibTeX，另有 ${missedCount} 条未匹配。`
      : `已生成 ${entries.length} 条 BibTeX。`,
    missedCount > 0,
  );
}

function renderResults() {
  elements.results.innerHTML = "";

  state.hits.forEach((hit, index) => {
    const fragment = elements.resultTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".result-card");
    const selectButton = fragment.querySelector(".result-select");

    fragment.querySelector(".result-title").textContent = hit.title;
    fragment.querySelector(".result-authors").textContent =
      hit.authors.join(", ") || "作者信息缺失";
    fragment.querySelector(".result-meta").textContent = [hit.venue, hit.year]
      .filter(Boolean)
      .join(" · ");
    fragment.querySelector(".result-key").textContent = `DBLP: ${hit.key}`;

    card.style.animationDelay = `${index * 40}ms`;
    selectButton.addEventListener("click", () => {
      void selectHit(index);
    });

    elements.results.appendChild(fragment);
  });
}

async function handleResultSortChange() {
  if (state.mode !== "single" || !state.lastQueries.length) {
    return;
  }

  setLoading(true);
  setStatus("正在按新的排序方式刷新候选结果...");
  try {
    await handleSingleSearch(state.lastQueries[0]);
  } catch (error) {
    console.error(error);
    setStatus(error.message || "刷新候选结果失败。", true);
  } finally {
    setLoading(false);
  }
}

async function selectHit(index) {
  const hit = state.hits[index];
  if (!hit) {
    return;
  }

  state.selectedIndex = index;
  highlightSelectedCard();
  elements.selectedPaper.textContent = `${hit.title}${hit.year ? ` (${hit.year})` : ""}`;
  elements.selectedKey.textContent = "生成中...";
  elements.bibtexOutput.value = "";
  setStatus("正在通过 API 生成 BibTeX...");

  try {
    const payload = await apiRequest(
      "/bibtex/by-key",
      {
        authors: hit.authors || [],
        custom_pattern: getCustomPattern(),
        key: hit.key,
        rename_style: elements.renameStyle.value,
        title: hit.title,
        venue: hit.venue || "",
        year: hit.year || "",
      },
      { timeoutMs: 20000 },
    );

    hit.renamedBibtex = payload.bibtex || "";
    state.outputEntries = hit.renamedBibtex ? [hit] : [];

    elements.selectedKey.textContent = extractEntryKey(hit.renamedBibtex);
    elements.bibtexOutput.value = hit.renamedBibtex;
    setStatus("BibTeX 已生成。");
  } catch (error) {
    console.error(error);
    elements.selectedKey.textContent = "-";
    setStatus(error.message || "BibTeX 获取失败。", true);
  }
}

function highlightSelectedCard() {
  const cards = elements.results.querySelectorAll(".result-card");
  cards.forEach((card, index) => {
    card.classList.toggle("active", index === state.selectedIndex);
  });
}

function handleRenameStyleChange() {
  const isCustom = elements.renameStyle.value === "custom";
  elements.customPatternGroup.hidden = !isCustom;
  void rerenderSelectedBibtex();
}

async function rerenderSelectedBibtex() {
  if (state.mode === "batch") {
    await rerenderBatchBibtex();
    return;
  }

  if (state.selectedIndex < 0) {
    return;
  }

  await selectHit(state.selectedIndex);
}

async function rerenderBatchBibtex() {
  if (state.mode !== "batch" || !state.lastQueries.length) {
    return;
  }

  setLoading(true);
  setStatus("正在按新的命名规则刷新批量 BibTeX...");
  try {
    await handleBatchSearch(state.lastQueries);
  } catch (error) {
    console.error(error);
    setStatus(error.message || "刷新批量 BibTeX 失败。", true);
  } finally {
    setLoading(false);
  }
}

function renderBatchSummary(items) {
  elements.results.innerHTML = "";

  items.forEach((item, index) => {
    const fragment = elements.resultTemplate.content.cloneNode(true);
    const card = fragment.querySelector(".result-card");
    const button = fragment.querySelector(".result-select");
    const entry = item.selected_hit;

    fragment.querySelector(".result-title").textContent = item.query;
    fragment.querySelector(".result-authors").textContent = entry
      ? entry.title
      : "未找到匹配结果";
    fragment.querySelector(".result-meta").textContent = entry
      ? [entry.venue, entry.year].filter(Boolean).join(" · ") || "已生成 BibTeX"
      : item.error || "请尝试更完整的标题";
    fragment.querySelector(".result-key").textContent = entry
      ? `Key: ${extractEntryKey(item.bibtex || "")}`
      : "Key: -";

    button.textContent = entry ? "已加入输出" : "未匹配";
    button.disabled = true;
    card.style.animationDelay = `${index * 40}ms`;

    elements.results.appendChild(fragment);
  });
}

function extractEntryKey(bibtex) {
  return bibtex.match(/^@([^{]+)\{([^,]+),/m)?.[2] || "-";
}

async function copyBibtex() {
  const content = elements.bibtexOutput.value.trim();
  if (!content) {
    setStatus("没有可复制的 BibTeX。", true);
    return;
  }

  try {
    await navigator.clipboard.writeText(content);
    setStatus("BibTeX 已复制到剪贴板。");
  } catch (error) {
    console.error(error);
    setStatus("复制失败，请手动复制。", true);
  }
}

function downloadBibtex() {
  const content = elements.bibtexOutput.value.trim();
  if (!content) {
    setStatus("没有可下载的 BibTeX。", true);
    return;
  }

  const key =
    state.outputEntries.length > 1 ? `dblp_batch_${state.outputEntries.length}` : extractEntryKey(content);
  const blob = new Blob([content], { type: "application/x-bibtex;charset=utf-8" });
  const url = URL.createObjectURL(blob);
  const anchor = document.createElement("a");
  anchor.href = url;
  anchor.download = `${key || "reference"}.bib`;
  anchor.click();
  URL.revokeObjectURL(url);
  setStatus("BibTeX 文件已下载。");
}

function setLoading(loading) {
  elements.searchButton.disabled = loading;
  elements.searchButton.textContent = loading ? "搜索中..." : "搜索";
}

function setStatus(message, isError = false) {
  elements.status.textContent = message;
  elements.status.style.color = isError ? "#a12424" : "";
}

function clearSelection() {
  state.outputEntries = [];
  elements.selectedPaper.textContent = "暂未生成";
  elements.selectedKey.textContent = "-";
  elements.bibtexOutput.value = "";
}

function getApiBaseCandidates() {
  const candidates = [DEFAULT_API_BASE, "http://localhost:8000"];

  if (location.protocol.startsWith("http")) {
    const sameOrigin = location.origin.replace(/\/+$/, "");
    const host8000 = `${location.protocol}//${location.hostname}:8000`;
    candidates.push(host8000, sameOrigin);
  }

  return [...new Set(candidates)];
}

async function apiRequest(path, payload, options = {}) {
  const timeoutMs = options.timeoutMs ?? 15000;
  const controller = new AbortController();
  const base = await resolveApiBase();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, timeoutMs);

  try {
    const response = await fetch(`${base}${path}`, {
      body: JSON.stringify(payload),
      headers: {
        "Content-Type": "application/json",
        Accept: "application/json",
      },
      method: "POST",
      signal: controller.signal,
    });

    if (!response.ok) {
      throw new Error(`API 请求失败：${response.status}`);
    }

    return await response.json();
  } catch (error) {
    if (error.name === "AbortError") {
      throw new Error(
        `请求超时（>${Math.round(timeoutMs / 1000)}s）。请检查服务地址、后端状态或网络连接。`,
      );
    }
    throw error;
  } finally {
    window.clearTimeout(timeoutId);
  }
}

async function withTimeout(promise, timeoutMs, message) {
  let timeoutId = null;
  const timeoutPromise = new Promise((_, reject) => {
    timeoutId = window.setTimeout(() => {
      reject(new Error(message));
    }, timeoutMs);
  });

  try {
    return await Promise.race([promise, timeoutPromise]);
  } finally {
    if (timeoutId !== null) {
      window.clearTimeout(timeoutId);
    }
  }
}

async function ensureApiHealthy() {
  const now = Date.now();
  if (
    state.apiHealth.ok &&
    state.apiHealth.base === state.apiBase &&
    now - state.apiHealth.checkedAt < 10000
  ) {
    return true;
  }

  try {
    const base = await resolveApiBase();
    state.apiHealth = { base, checkedAt: now, ok: true };
    return true;
  } catch (_error) {
    state.apiHealth = { base: "", checkedAt: now, ok: false };
    setStatus(
      "服务不可达。请确认 FastAPI 已启动在 127.0.0.1:8000。",
      true,
    );
    return false;
  }
}

async function resolveApiBase() {
  if (state.apiBase) {
    return state.apiBase;
  }

  const candidates = getApiBaseCandidates();
  for (const base of candidates) {
    try {
      const response = await fetchWithTimeout(`${base}/health`, { method: "GET" }, 1200);
      if (response.ok) {
        state.apiBase = base;
        return base;
      }
    } catch (_error) {
      // Try next candidate.
    }
  }

  throw new Error(
    "无法连接到 API。请启动 FastAPI：python3 -m uvicorn dblp_bib.api:app --host 127.0.0.1 --port 8000",
  );
}

async function fetchWithTimeout(url, options, timeoutMs) {
  const controller = new AbortController();
  const timeoutId = window.setTimeout(() => {
    controller.abort();
  }, timeoutMs);
  try {
    return await fetch(url, { ...options, signal: controller.signal });
  } finally {
    window.clearTimeout(timeoutId);
  }
}

function getCustomPattern() {
  return elements.customPattern.value.trim() || "{author}{year}{title}";
}

let customPatternTimer = null;

function handleCustomPatternInput() {
  window.clearTimeout(customPatternTimer);
  customPatternTimer = window.setTimeout(() => {
    void rerenderSelectedBibtex();
  }, 300);
}
