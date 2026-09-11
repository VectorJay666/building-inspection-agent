/* Minimal layer-② demo engine. Mirrors skill contracts; does not replace skills/. */

const RULES = {
  crack_mm: { threshold: 3, rule_id: "rule.crack_mm.gt_3" },
  tilt_deg: { threshold: 0.5, rule_id: "rule.tilt_deg.gt_0_5" },
};

const KNOWN_METRICS = Object.keys(RULES);
const READING_REQUIRED = [
  "reading_id",
  "sensor_or_point",
  "metric",
  "value",
  "unit",
  "timestamp",
  "location_tag",
];
const READING_KEYS = new Set([...READING_REQUIRED, "building_id"]);
const RANK_REQUIRED = [
  "reading_id",
  "sensor_or_point",
  "metric",
  "value",
  "threshold",
  "rule_id",
  "timestamp",
  "location_tag",
];
const EVIDENCE_REQUIRED = [...RANK_REQUIRED, "conclusion", "confidence"];
const METRIC_TIE = { crack_mm: 0, tilt_deg: 1 };

const PIN_LAYOUT = {
  A: { left: "25%", top: "36%" },
  B: { left: "25%", top: "68%" },
  C: { left: "48%", top: "36%" },
  P1: { left: "50%", top: "54%" },
  "N-wall": { left: "50%", top: "18%" },
  "E-corner": { left: "86%", top: "50%" },
  X: { left: "72%", top: "72%" },
};

const EMBEDDED = {
  g01: [
    {
      reading_id: "g01-a-crack",
      sensor_or_point: "A",
      metric: "crack_mm",
      value: 4.2,
      unit: "mm",
      timestamp: "2026-09-11T08:00:00Z",
      location_tag: "A",
      building_id: "demo-building-01",
    },
    {
      reading_id: "g01-b-tilt",
      sensor_or_point: "B",
      metric: "tilt_deg",
      value: 0.2,
      unit: "deg",
      timestamp: "2026-09-11T08:00:00Z",
      location_tag: "B",
      building_id: "demo-building-01",
    },
    {
      reading_id: "g01-c-crack",
      sensor_or_point: "C",
      metric: "crack_mm",
      value: 1.0,
      unit: "mm",
      timestamp: "2026-09-11T08:00:00Z",
      location_tag: "C",
      building_id: "demo-building-01",
    },
  ],
  g02: [
    {
      reading_id: "g02-p1-tilt",
      sensor_or_point: "P1",
      metric: "tilt_deg",
      value: 0.8,
      unit: "deg",
      timestamp: "2026-09-11T08:05:00Z",
      location_tag: "P1",
      building_id: "demo-building-01",
    },
  ],
  g03: [
    {
      reading_id: "g03-n-crack",
      sensor_or_point: "N-wall",
      metric: "crack_mm",
      value: 5.1,
      unit: "mm",
      timestamp: "2026-09-11T08:10:00Z",
      location_tag: "N-wall",
      building_id: "demo-building-01",
    },
    {
      reading_id: "g03-e-tilt",
      sensor_or_point: "E-corner",
      metric: "tilt_deg",
      value: 0.9,
      unit: "deg",
      timestamp: "2026-09-11T08:10:00Z",
      location_tag: "E-corner",
      building_id: "demo-building-01",
    },
  ],
  empty: [],
  g06: [
    {
      reading_id: "g06-x-crack",
      sensor_or_point: "X",
      metric: "crack_mm",
      value: 4.5,
      unit: "mm",
      timestamp: "2026-09-11T08:20:00Z",
      location_tag: "X",
      building_id: "demo-building-01",
    },
  ],
};

const MOCK_URLS = {
  g01: "../data/mock/g01.json",
  g02: "../data/mock/g02.json",
  g03: "../data/mock/g03.json",
};

const state = {
  sourceId: "g01",
  rawBatch: structuredClone(EMBEDDED.g01),
  imported: false,
  result: null,
  selectedKey: null,
};

function isPresent(value) {
  if (value === null || value === undefined) return false;
  if (typeof value === "string") return value.length > 0;
  if (typeof value === "number") return Number.isFinite(value);
  return true;
}

function missingFields(obj, fields) {
  return fields.filter((field) => !isPresent(obj?.[field]));
}

function ingestReadings(data) {
  const rejected = [];
  const accepted = [];
  if (!Array.isArray(data)) {
    return {
      ok: false,
      error: "Batch must be a JSON array; entire payload rejected.",
      accepted,
      rejected,
    };
  }
  data.forEach((item, index) => {
    const readingId = item && typeof item === "object" ? item.reading_id : undefined;
    if (!item || typeof item !== "object" || Array.isArray(item)) {
      rejected.push({ index, reading_id: readingId, reason: "Item is not an object." });
      return;
    }
    const extra = Object.keys(item).filter((key) => !READING_KEYS.has(key));
    if (extra.length) {
      rejected.push({
        index,
        reading_id: readingId,
        reason: `additionalProperties not allowed: ${extra.join(", ")}`,
      });
      return;
    }
    const missing = missingFields(item, READING_REQUIRED);
    if (missing.length) {
      rejected.push({
        index,
        reading_id: readingId,
        reason: `Missing required fields: ${missing.join(", ")}`,
      });
      return;
    }
    if (typeof item.value !== "number" || !Number.isFinite(item.value)) {
      rejected.push({ index, reading_id: readingId, reason: "value must be a finite number." });
      return;
    }
    if (!KNOWN_METRICS.includes(item.metric)) {
      rejected.push({
        index,
        reading_id: readingId,
        reason: `Unknown metric '${item.metric}' (no invented threshold).`,
      });
      return;
    }
    accepted.push({ ...item });
  });
  return { ok: true, accepted, rejected };
}

function flagAnomalies(accepted, options = {}) {
  const alerts = [];
  const notices = [];
  const quiet = [];
  for (const reading of accepted) {
    const rule = RULES[reading.metric];
    if (!rule) {
      notices.push({
        reading_id: reading.reading_id,
        code: "UNKNOWN_METRIC",
        detail: `No rule for metric '${reading.metric}'. Threshold not invented.`,
      });
      continue;
    }
    if (!(reading.value > rule.threshold)) {
      quiet.push({
        ...reading,
        threshold: rule.threshold,
        rule_id: rule.rule_id,
      });
      continue;
    }
    const alert = {
      reading_id: reading.reading_id,
      sensor_or_point: reading.sensor_or_point,
      metric: reading.metric,
      value: reading.value,
      timestamp: reading.timestamp,
      location_tag: reading.location_tag,
    };
    if (!options.omitEvidenceFields) {
      alert.threshold = rule.threshold;
      alert.rule_id = rule.rule_id;
    }
    alerts.push(alert);
  }
  return { alerts, notices, quiet };
}

function rankPriorities(alerts) {
  const dropped = [];
  const keep = [];
  for (const alert of alerts) {
    const missing = missingFields(alert, RANK_REQUIRED);
    if (missing.length) {
      dropped.push({
        ...alert,
        drop_reason: `Missing evidence fields: ${missing.join(", ")}`,
        missing,
      });
      continue;
    }
    keep.push({ ...alert, ratio: alert.value / alert.threshold });
  }
  keep.sort((a, b) => {
    if (b.ratio !== a.ratio) return b.ratio - a.ratio;
    const ma = METRIC_TIE[a.metric] ?? 99;
    const mb = METRIC_TIE[b.metric] ?? 99;
    if (ma !== mb) return ma - mb;
    if (a.location_tag !== b.location_tag) {
      return a.location_tag < b.location_tag ? -1 : 1;
    }
    if (a.reading_id !== b.reading_id) {
      return a.reading_id < b.reading_id ? -1 : 1;
    }
    return 0;
  });
  const ranked = keep.map((item, index) => ({
    ...item,
    rank: index + 1,
    recheck_task: `recheck:${item.location_tag}:${item.metric}`,
  }));
  return { ranked, dropped };
}

function attachEvidence(ranked, dropped) {
  const attached = [];
  const blocked = [];

  function attempt(item, fromDrop) {
    const candidate = { ...item };
    if (
      isPresent(candidate.value) &&
      isPresent(candidate.threshold) &&
      isPresent(candidate.rule_id) &&
      isPresent(candidate.metric)
    ) {
      candidate.conclusion = `${candidate.metric} ${formatNumber(candidate.value)} > ${formatNumber(candidate.threshold)} (${candidate.rule_id})`;
      candidate.confidence = 1.0;
    }
    const missing = missingFields(candidate, EVIDENCE_REQUIRED);
    if (missing.length) {
      blocked.push({
        status: "blocked",
        reading_id: candidate.reading_id,
        sensor_or_point: candidate.sensor_or_point,
        metric: candidate.metric,
        value: candidate.value,
        threshold: candidate.threshold,
        rule_id: candidate.rule_id,
        timestamp: candidate.timestamp,
        location_tag: candidate.location_tag,
        conclusion: null,
        confidence: null,
        missing_fields: missing,
        missing,
        reason: fromDrop
          ? `${item.drop_reason || "Dropped at rank"}; attach BLOCKED, no conclusion.`
          : `Missing required evidence fields: ${missing.join(", ")}`,
      });
      return;
    }
    attached.push({
      status: "attached",
      reading_id: candidate.reading_id,
      sensor_or_point: candidate.sensor_or_point,
      metric: candidate.metric,
      value: candidate.value,
      threshold: candidate.threshold,
      rule_id: candidate.rule_id,
      timestamp: candidate.timestamp,
      location_tag: candidate.location_tag,
      conclusion: candidate.conclusion,
      confidence: candidate.confidence,
      rank: item.rank,
      recheck_task: item.recheck_task,
      ratio: item.ratio,
    });
  }

  ranked.forEach((item) => attempt(item, false));
  dropped.forEach((item) => attempt(item, true));
  return { attached, blocked };
}

function runPipeline(raw, options = {}) {
  const log = [];
  const ingested = ingestReadings(raw);
  if (!ingested.ok) {
    log.push(ingested.error);
    return {
      log,
      accepted: [],
      rejected: ingested.rejected,
      alerts: [],
      notices: [],
      quiet: [],
      ranked: [],
      dropped: [],
      attached: [],
      blocked: [],
      stopped: true,
      error: ingested.error,
    };
  }
  log.push(
    `ingest_readings: accepted ${ingested.accepted.length}, rejected ${ingested.rejected.length}`
  );
  ingested.rejected.forEach((row) => {
    log.push(`reject[${row.index}] ${row.reading_id || "(no id)"}: ${row.reason}`);
  });
  if (ingested.accepted.length === 0) {
    log.push("empty or all-rejected: do not invent readings; do not call downstream.");
    return {
      log,
      accepted: ingested.accepted,
      rejected: ingested.rejected,
      alerts: [],
      notices: [],
      quiet: [],
      ranked: [],
      dropped: [],
      attached: [],
      blocked: [],
      stopped: true,
    };
  }
  const flagged = flagAnomalies(ingested.accepted, options);
  log.push(
    `flag_anomalies: ${flagged.alerts.length} over-threshold, ${flagged.quiet.length} quiet, ${flagged.notices.length} UNKNOWN_METRIC`
  );
  flagged.notices.forEach((notice) => log.push(`${notice.code}: ${notice.detail}`));
  const rankedResult = rankPriorities(flagged.alerts);
  log.push(
    `rank_priorities: ${rankedResult.ranked.length} ranked, ${rankedResult.dropped.length} dropped`
  );
  rankedResult.dropped.forEach((row) => {
    log.push(`drop ${row.reading_id || row.location_tag}: ${row.drop_reason}`);
  });
  const evidence = attachEvidence(rankedResult.ranked, rankedResult.dropped);
  log.push(
    `attach_evidence: ${evidence.attached.length} attached, ${evidence.blocked.length} BLOCKED`
  );
  evidence.blocked.forEach((row) => log.push(`BLOCK ${row.reading_id || "(no id)"}: ${row.reason}`));
  return {
    log,
    accepted: ingested.accepted,
    rejected: ingested.rejected,
    alerts: flagged.alerts,
    notices: flagged.notices,
    quiet: flagged.quiet,
    ranked: rankedResult.ranked,
    dropped: rankedResult.dropped,
    attached: evidence.attached,
    blocked: evidence.blocked,
    stopped: false,
  };
}

function formatNumber(value) {
  if (typeof value !== "number" || !Number.isFinite(value)) return String(value);
  if (Number.isInteger(value)) return String(value);
  return String(value);
}

function formatMetric(metric, value) {
  if (metric === "crack_mm") return `crack ${value} mm`;
  if (metric === "tilt_deg") return `tilt ${value}°`;
  return `${metric} ${value}`;
}

function escapeHtml(value) {
  return String(value)
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function displayValue(value) {
  if (value === null || value === undefined || value === "") return "—";
  return escapeHtml(value);
}

async function loadSource(sourceId) {
  if (sourceId === "empty" || sourceId === "g06") {
    return structuredClone(EMBEDDED[sourceId]);
  }
  const url = MOCK_URLS[sourceId];
  if (url) {
    try {
      const response = await fetch(url);
      if (response.ok) return await response.json();
    } catch {
      /* file:// or missing server: use embedded copy of data/mock */
    }
  }
  return structuredClone(EMBEDDED[sourceId] || []);
}

function renderReadings() {
  const list = document.getElementById("reading-list");
  const result = state.result;
  const quietIds = new Set((result?.quiet || []).map((row) => row.reading_id));
  const alertIds = new Set((result?.alerts || []).map((row) => row.reading_id));
  if (!state.imported) {
    list.innerHTML = `<li class="muted">No batch loaded.</li>`;
    return;
  }
  if (!Array.isArray(state.rawBatch) || state.rawBatch.length === 0) {
    list.innerHTML = `<li class="reading-item">[] empty batch — no invented points.</li>`;
    return;
  }
  list.innerHTML = state.rawBatch
    .map((row) => {
      let badge = "";
      if (result) {
        if (alertIds.has(row.reading_id)) badge = `<span class="badge badge-over">over</span>`;
        else if (quietIds.has(row.reading_id)) badge = `<span class="badge badge-quiet">quiet</span>`;
      }
      const label = row.location_tag || row.sensor_or_point || "(no location)";
      const metric = row.metric ?? "—";
      const value = row.value ?? "missing";
      return `<li class="reading-item"><strong>${escapeHtml(label)}</strong> ${escapeHtml(
        formatMetric(metric, value)
      )}${badge}<div class="meta">${escapeHtml(row.reading_id || "no reading_id")}</div></li>`;
    })
    .join("");
  (result?.rejected || []).forEach((row) => {
    const item = document.createElement("li");
    item.className = "reading-item";
    item.innerHTML = `<span class="badge badge-reject">rejected</span> ${escapeHtml(
      row.reading_id || `index ${row.index}`
    )}: ${escapeHtml(row.reason)}`;
    list.appendChild(item);
  });
}

function renderLog() {
  const logEl = document.getElementById("pipeline-log");
  const rows = state.result?.log || [];
  if (!rows.length) {
    logEl.innerHTML = `<li class="muted">Waiting for Run ②.</li>`;
    return;
  }
  logEl.innerHTML = rows.map((line) => `<li class="log-item">${escapeHtml(line)}</li>`).join("");
}

function pinStyle(tag) {
  const pos = PIN_LAYOUT[tag] || { left: "50%", top: "50%" };
  return `left:${pos.left};top:${pos.top}`;
}

function renderPlan() {
  const pins = document.getElementById("plan-pins");
  const status = document.getElementById("plan-status");
  pins.innerHTML = "";
  if (!state.imported) {
    status.textContent = "Import a batch. Plan is quiet until ② runs.";
    return;
  }
  const batchPoints = Array.isArray(state.rawBatch)
    ? state.rawBatch.filter((row) => row && row.location_tag)
    : [];
  const attachedById = new Map((state.result?.attached || []).map((row) => [row.reading_id, row]));
  const blockedById = new Map((state.result?.blocked || []).map((row) => [row.reading_id, row]));
  const alertIds = new Set((state.result?.alerts || []).map((row) => row.reading_id));

  batchPoints.forEach((row) => {
    const tag = row.location_tag;
    const btn = document.createElement("button");
    btn.type = "button";
    btn.className = "pin";
    btn.style.cssText = pinStyle(tag);
    btn.dataset.readingId = row.reading_id || "";
    const isAlert = state.result && alertIds.has(row.reading_id);
    const isBlocked = state.result && blockedById.has(row.reading_id);
    if (!state.result) {
      btn.classList.add("quiet");
      btn.title = `${tag} imported — not flagged yet`;
    } else if (isBlocked) {
      btn.classList.add("blocked");
      btn.title = `${tag} BLOCKED`;
      btn.addEventListener("click", () => openEvidence("blocked:" + row.reading_id));
    } else if (isAlert && attachedById.has(row.reading_id)) {
      btn.classList.add("alert");
      btn.title = `${tag} over threshold`;
      btn.addEventListener("click", () => openEvidence("attached:" + row.reading_id));
    } else {
      btn.classList.add("quiet");
      btn.title = `${tag} under threshold — no alert`;
    }
    btn.innerHTML = `<span class="dot"></span><span class="pin-label">${escapeHtml(tag)}</span>`;
    pins.appendChild(btn);
  });

  if (!state.result) {
    status.textContent = `${batchPoints.length} imported point(s). Center is quiet until flag.`;
  } else if (state.result.stopped && state.result.accepted.length === 0) {
    status.textContent = "No downstream points. Empty/rejected batch did not invent marks.";
  } else {
    const lit = (state.result.attached || []).map((row) => row.location_tag);
    status.textContent = lit.length
      ? `Lit: ${lit.join(", ")}. Quiet points stay dark.`
      : "No over-threshold points. Plan stays dark.";
  }
}

function renderRight() {
  const rankedList = document.getElementById("ranked-list");
  const blockedList = document.getElementById("blocked-list");
  const meta = document.getElementById("rank-meta");
  const attached = state.result?.attached || [];
  const blocked = state.result?.blocked || [];
  meta.textContent = state.result
    ? `Ranked alerts: ${attached.length}. Recheck tasks: ${attached.length}.`
    : "No ranked alerts.";
  rankedList.innerHTML = attached.length
    ? attached
        .map(
          (row) => `<li>
            <button type="button" class="rank-card" data-key="attached:${escapeHtml(row.reading_id)}">
              <span class="rank-index">#${row.rank}</span>
              <strong>${escapeHtml(row.location_tag)}</strong>
              · ${escapeHtml(formatMetric(row.metric, row.value))}
              <div class="meta">threshold ${displayValue(row.threshold)} · ratio ${(row.ratio || 0).toFixed(2)} · ${escapeHtml(row.rule_id)}</div>
              <div class="recheck">${escapeHtml(row.recheck_task)}</div>
            </button>
          </li>`
        )
        .join("")
    : `<li class="muted">${state.result ? "Ranked list length 0." : "Run ② to rank alerts."}</li>`;
  blockedList.innerHTML = blocked.length
    ? blocked
        .map(
          (row) => `<li>
            <button type="button" class="block-card" data-key="blocked:${escapeHtml(row.reading_id || "")}">
              <strong>BLOCKED</strong> ${escapeHtml(row.location_tag || row.reading_id || "item")}
              <div class="meta">${escapeHtml(row.reason)}</div>
            </button>
          </li>`
        )
        .join("")
    : `<li class="muted">None. Incomplete evidence would appear here — never silently filled.</li>`;

  rankedList.querySelectorAll(".rank-card").forEach((btn) => {
    btn.addEventListener("click", () => openEvidence(btn.dataset.key));
  });
  blockedList.querySelectorAll(".block-card").forEach((btn) => {
    btn.addEventListener("click", () => openEvidence(btn.dataset.key));
  });
}

function findEvidence(key) {
  if (!key || !state.result) return null;
  const [kind, ...rest] = key.split(":");
  const id = rest.join(":");
  if (kind === "attached") {
    return state.result.attached.find((row) => row.reading_id === id) || null;
  }
  if (kind === "blocked") {
    return state.result.blocked.find((row) => row.reading_id === id) || null;
  }
  return null;
}

function renderDrawer(item) {
  const drawer = document.getElementById("drawer");
  const body = document.getElementById("drawer-body");
  const summary = document.getElementById("drawer-summary");
  document.querySelectorAll(".rank-card, .block-card").forEach((el) => {
    el.classList.toggle("active", el.dataset.key === state.selectedKey);
  });
  if (!item) {
    drawer.dataset.open = "false";
    summary.textContent =
      "Click a priority, anomaly, or alert pin. Incomplete chain → BLOCKED, no conclusion.";
    body.innerHTML = `<p class="muted">No evidence selected.</p>`;
    return;
  }
  drawer.dataset.open = "true";
  const blocked = item.status === "blocked";
  summary.textContent = blocked
    ? `BLOCKED — no conclusion. Missing: ${(item.missing_fields || item.missing || []).join(", ") || "required evidence fields"}`
    : `Evidence chain for ${item.location_tag} (${item.reading_id})`;
  const fields = [
    "reading_id",
    "sensor_or_point",
    "metric",
    "value",
    "threshold",
    "rule_id",
    "timestamp",
    "location_tag",
    "conclusion",
    "confidence",
  ];
  const cells = fields
    .map((field) => {
      const missing = !isPresent(item[field]);
      const value =
        field === "conclusion" && blocked
          ? "no conclusion"
          : field === "confidence" && blocked
            ? "—"
            : displayValue(item[field]);
      return `<div class="${missing || blocked && (field === "conclusion" || field === "confidence") ? "missing" : ""}">
        <dt>${field}</dt><dd>${value}</dd>
      </div>`;
    })
    .join("");
  body.innerHTML = `
    <span class="evidence-banner ${blocked ? "blocked" : "ok"}">${blocked ? "BLOCKED" : "ATTACHED"}</span>
    ${blocked ? `<p class="muted">${escapeHtml(item.reason)}</p>` : ""}
    <dl class="evidence-grid">${cells}</dl>
  `;
}

function openEvidence(key) {
  state.selectedKey = key;
  renderDrawer(findEvidence(key));
}

function renderAll() {
  renderReadings();
  renderLog();
  renderPlan();
  renderRight();
  renderDrawer(findEvidence(state.selectedKey));
}

async function importSource(sourceId, batchOverride) {
  state.sourceId = sourceId;
  state.rawBatch = batchOverride ?? (await loadSource(sourceId));
  state.imported = true;
  state.result = null;
  state.selectedKey = null;
  document.querySelectorAll(".source-btn").forEach((btn) => {
    btn.classList.toggle("active", btn.dataset.source === sourceId);
  });
  document.getElementById("run-engine").disabled = false;
  renderAll();
}

function runEngine() {
  if (!state.imported) return;
  const options = { omitEvidenceFields: state.sourceId === "g06" };
  state.result = runPipeline(state.rawBatch, options);
  state.selectedKey = null;
  renderAll();
}

function bindUi() {
  document.querySelectorAll(".source-btn").forEach((btn) => {
    btn.addEventListener("click", () => importSource(btn.dataset.source));
  });
  document.getElementById("run-engine").addEventListener("click", runEngine);
  document.getElementById("drawer-close").addEventListener("click", () => {
    state.selectedKey = null;
    renderDrawer(null);
  });
  document.getElementById("file-input").addEventListener("change", async (event) => {
    const file = event.target.files && event.target.files[0];
    if (!file) return;
    try {
      const parsed = JSON.parse(await file.text());
      await importSource("custom", parsed);
      document.querySelectorAll(".source-btn").forEach((btn) => btn.classList.remove("active"));
    } catch (err) {
      state.imported = true;
      state.rawBatch = null;
      state.result = {
        log: [`FAIL: illegal JSON, do not invent a batch: ${err.message}`],
        accepted: [],
        rejected: [],
        alerts: [],
        notices: [],
        quiet: [],
        ranked: [],
        dropped: [],
        attached: [],
        blocked: [],
        stopped: true,
        error: err.message,
      };
      renderAll();
    }
  });
  document.getElementById("tease-decision").addEventListener("click", () => {
    document.getElementById("tease-overlay").hidden = false;
  });
  document.getElementById("tease-dismiss").addEventListener("click", () => {
    document.getElementById("tease-overlay").hidden = true;
  });
}

function selfCheck() {
  const g01 = runPipeline(EMBEDDED.g01);
  const g02 = runPipeline(EMBEDDED.g02);
  const g03 = runPipeline(EMBEDDED.g03);
  const g03b = runPipeline(EMBEDDED.g03);
  const empty = runPipeline([]);
  const g06 = runPipeline(EMBEDDED.g06, { omitEvidenceFields: true });
  const checks = [
    g01.attached.length === 1 && g01.attached[0].location_tag === "A",
    g01.attached[0]?.conclusion === "crack_mm 4.2 > 3 (rule.crack_mm.gt_3)",
    !g01.attached.some((row) => row.location_tag === "B" || row.location_tag === "C"),
    g02.attached.length === 1 && g02.attached[0].recheck_task === "recheck:P1:tilt_deg",
    g03.attached.map((row) => row.location_tag).join(",") === "E-corner,N-wall",
    g03.attached.map((row) => row.conclusion).join("|") ===
      g03b.attached.map((row) => row.conclusion).join("|"),
    empty.attached.length === 0 && empty.stopped,
    g06.blocked.length === 1 && g06.blocked[0].conclusion === null &&
      (g06.blocked[0].missing_fields || []).includes("threshold"),
  ];
  if (checks.every(Boolean)) {
    console.info("demo self-check: G01–G03 / empty / G06 BLOCK passed");
  } else {
    console.error("demo self-check failed", checks);
  }
}

selfCheck();
if (typeof document !== "undefined") {
  bindUi();
  importSource("g01");
}
