const API_BASE_URL = (window.FEDLENS_API_BASE_URL || "http://127.0.0.1:8000").replace(/\/$/, "");
const threadId = `fedlens-${Date.now()}`;

const elements = {
  activity: document.querySelector("#activity"),
  chart: document.querySelector("#chart"),
  chartUnit: document.querySelector("#chart-unit"),
  connectionLabel: document.querySelector("#connection-label"),
  form: document.querySelector("#chat-form"),
  hint: document.querySelector("#composer-hint"),
  input: document.querySelector("#message-input"),
  keyNumbers: document.querySelector("#key-numbers"),
  messages: document.querySelector("#messages"),
  resultStatus: document.querySelector("#result-status"),
  sendButton: document.querySelector("#send-button"),
  sourceCount: document.querySelector("#source-count"),
  sources: document.querySelector("#sources"),
};

function addMessage(role, content, pending = false) {
  const message = document.createElement("article");
  message.className = `message ${role}${pending ? " pending" : ""}`;
  const label = document.createElement("span");
  label.className = "message-label";
  label.textContent = role === "user" ? "You" : "FedLens";
  const body = document.createElement("p");
  body.textContent = content;
  message.append(label, body);
  elements.messages.appendChild(message);
  elements.messages.scrollTop = elements.messages.scrollHeight;
  return message;
}

function formatValue(value) {
  if (typeof value !== "number") return String(value);
  return new Intl.NumberFormat("en-US", {
    style: "currency",
    currency: "USD",
    maximumFractionDigits: 0,
  }).format(value);
}

function renderKeyNumbers(numbers) {
  elements.keyNumbers.className = "key-numbers";
  elements.keyNumbers.replaceChildren();
  numbers.forEach((number) => {
    const item = document.createElement("div");
    item.className = "key-number";
    const label = document.createElement("span");
    label.textContent = number.label;
    const value = document.createElement("strong");
    value.textContent = number.unit === "USD" ? formatValue(number.value) : `${number.value} ${number.unit || ""}`.trim();
    item.append(label, value);
    elements.keyNumbers.appendChild(item);
  });
}

function renderChart(visualization) {
  elements.chart.className = "chart";
  elements.chart.replaceChildren();
  elements.chartUnit.textContent = visualization.unit || "USD";
  const data = visualization.data || [];
  if (!data.length) {
    elements.chart.className = "chart empty-state";
    elements.chart.textContent = "No chartable records returned.";
    return;
  }
  const maxValue = Math.max(...data.map((item) => Number(item.value) || 0), 1);
  data.forEach((item) => {
    const row = document.createElement("div");
    row.className = "chart-row";
    const label = document.createElement("span");
    label.className = "chart-label";
    label.textContent = item.agency ? `${item.agency} · ${item.label}` : item.label;
    const track = document.createElement("span");
    track.className = "chart-track";
    const bar = document.createElement("span");
    bar.className = "chart-bar";
    bar.style.width = `${Math.max(4, ((Number(item.value) || 0) / maxValue) * 100)}%`;
    track.appendChild(bar);
    const value = document.createElement("strong");
    value.className = "chart-value";
    value.textContent = formatValue(Number(item.value) || 0);
    row.append(label, track, value);
    elements.chart.appendChild(row);
  });
}

function renderSources(sources) {
  elements.sourceCount.textContent = sources.length;
  elements.sources.replaceChildren();
  if (!sources.length) {
    elements.sources.className = "source-list empty-state";
    elements.sources.textContent = "No source metadata returned.";
    return;
  }
  elements.sources.className = "source-list";
  sources.forEach((source) => {
    const item = document.createElement("div");
    item.className = "source-item";
    const name = document.createElement("strong");
    name.textContent = source.name;
    const endpoint = document.createElement("a");
    endpoint.href = source.endpoint;
    endpoint.target = "_blank";
    endpoint.rel = "noreferrer";
    endpoint.textContent = new URL(source.endpoint).hostname;
    item.append(name, endpoint);
    elements.sources.appendChild(item);
  });
}

function renderActivity(activity) {
  elements.activity.className = "activity-list";
  elements.activity.replaceChildren();
  activity.forEach((event) => {
    const item = document.createElement("li");
    item.className = event.type === "tool" ? "tool-event" : "";
    item.textContent = event.message;
    elements.activity.appendChild(item);
  });
}

function renderResponse(response) {
  elements.resultStatus.textContent = response.warnings?.length ? "Review" : "Verified";
  renderKeyNumbers(response.key_numbers || []);
  renderChart(response.visualizations?.[0] || {data: []});
  renderSources(response.sources || []);
  renderActivity(response.activity || []);
}

async function submitQuestion(question) {
  const message = question.trim();
  if (!message) return;
  addMessage("user", message);
  const pending = addMessage("assistant", "Working through the verified data...", true);
  elements.sendButton.disabled = true;
  elements.input.disabled = true;
  elements.connectionLabel.textContent = "Analyzing";
  elements.resultStatus.textContent = "Running";
  elements.hint.textContent = "Interpreting the question and querying Neon...";
  try {
    const response = await fetch(`${API_BASE_URL}/v1/chat`, {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({thread_id: threadId, message}),
    });
    const payload = await response.json();
    if (!response.ok) throw new Error(payload.detail || "The backend returned an error.");
    pending.remove();
    addMessage("assistant", payload.answer || "The workflow completed without an answer.");
    renderResponse(payload);
    elements.connectionLabel.textContent = "Ready";
    elements.hint.textContent = payload.warnings?.length ? payload.warnings.join(" ") : "Verified against the connected database.";
  } catch (error) {
    pending.remove();
    addMessage("assistant", `I could not reach the FedLens backend. ${error.message}`);
    elements.connectionLabel.textContent = "Offline";
    elements.resultStatus.textContent = "Unavailable";
    elements.hint.textContent = `Backend URL: ${API_BASE_URL}`;
  } finally {
    elements.sendButton.disabled = false;
    elements.input.disabled = false;
    elements.input.focus();
  }
}

elements.form.addEventListener("submit", (event) => {
  event.preventDefault();
  const question = elements.input.value;
  elements.input.value = "";
  submitQuestion(question);
});

elements.input.addEventListener("keydown", (event) => {
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    elements.form.requestSubmit();
  }
});

document.querySelectorAll("[data-prompt]").forEach((button) => {
  button.addEventListener("click", () => {
    elements.input.value = button.dataset.prompt;
    elements.input.focus();
  });
});

addMessage("assistant", "I can analyze official agency spending from the connected Neon database. Start with an agency, a fiscal year, or a comparison.");
