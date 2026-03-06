const TOTAL_STEPS = 3;

const MOCK_EMAIL = `Hey Fal team, we are a massive e-commerce company. We need to process 100,000 product images a day. We need a custom deployment that uses a specific Dockerfile with ffmpeg installed, and it absolutely must run distributed across multiple H100 GPUs to handle the volume. Can you send us the deployment script?`;

let currentStep = 1;

function mdToHtml(md) {
  let s = md.replace(/```[\w]*\n([\s\S]*?)```/g, (_, code) => "<pre><code>" + escapeHtml(code.trim()) + "</code></pre>");
  const lines = s.split("\n");
  let out = "";
  for (const line of lines) {
    if (line.startsWith("## ")) out += "<h2>" + escapeHtml(line.slice(3)) + "</h2>";
    else if (line.startsWith("# ")) out += "<h1>" + escapeHtml(line.slice(2)) + "</h1>";
    else if (line.trim()) out += "<p>" + escapeHtml(line).replace(/\*\*([^*]+)\*\*/g, "<strong>$1</strong>").replace(/`([^`]+)`/g, "<code>$1</code>") + "</p>";
    else out += "<br>";
  }
  return out;
}

function escapeHtml(str) {
  const div = document.createElement("div");
  div.textContent = str;
  return div.innerHTML;
}

/** Explanation → clean bullets: sentence split, drop markdown/README cruft. */
function explanationToBullets(text) {
  if (!text || !text.trim()) return [];
  let clean = text
    .replace(/\n+/g, " ")
    .trim();
  if (clean.includes("README:") || clean.includes("```markdown")) {
    clean = clean.split(/README:|```markdown/)[0].trim();
  }
  const sentences = clean.split(/(?<=[.!?])\s+/).filter(Boolean);
  const bullets = sentences.filter((s) => {
    const t = s.trim();
    if (t.length < 10) return false;
    if (/^#+\s/.test(t) || /^-\s/.test(t) || /^`/.test(t)) return false;
    if (/\bfal\s+(run|deploy)\b/.test(t)) return false;
    return true;
  });
  return bullets.length ? bullets : [clean];
}

const $ = (id) => document.getElementById(id);
const clientEmail = $("client-email");
const mockBtn = $("mock-email");
const generateBtn = $("generate");
const messageEl = $("message");
const loadingEl = $("loading");
const resultEl = $("result");
const resultStepLabel = $("result-step-label");
const resultBackBtn = $("result-back");
const resultNextBtn = $("result-next");
const resultStep1 = $("result-step-1");
const resultStep2 = $("result-step-2");
const resultStep3 = $("result-step-3");
const resultCode = $("result-code");
const resultExplanation = $("result-explanation");
const resultReadme = $("result-readme");

function showMessage(text, type = "error") {
  messageEl.textContent = text;
  messageEl.className = "message " + type;
  messageEl.hidden = false;
  resultEl.hidden = true;
}

function hideMessage() {
  messageEl.hidden = true;
}

function setLoading(on) {
  loadingEl.hidden = !on;
  generateBtn.disabled = on;
  if (on) {
    resultEl.hidden = true;
    hideMessage();
  }
}

function showResultStep(step) {
  currentStep = step;
  resultStep1.hidden = step !== 1;
  resultStep2.hidden = step !== 2;
  resultStep3.hidden = step !== 3;
  resultStepLabel.textContent = step + " of " + TOTAL_STEPS;
  resultBackBtn.hidden = step === 1;
  resultNextBtn.textContent = step === TOTAL_STEPS ? "Done" : "Next";
  resultNextBtn.hidden = false;
}

function goHome() {
  resultEl.hidden = true;
  hideMessage();
  document.querySelector(".page").scrollIntoView({ behavior: "smooth", block: "start" });
}

function showResult(data) {
  loadingEl.hidden = true;
  resultCode.textContent = data.code;
  const bullets = explanationToBullets(data.explanation);
  resultExplanation.innerHTML = bullets.map((s) => "<li>" + escapeHtml(s.trim()) + "</li>").join("");
  resultReadme.innerHTML = mdToHtml(data.readme);
  resultEl.hidden = false;
  showResultStep(1);
  hideMessage();
  resultEl.scrollIntoView({ behavior: "smooth", block: "start" });
}

mockBtn.addEventListener("click", () => {
  clientEmail.value = MOCK_EMAIL;
  hideMessage();
});

resultBackBtn.addEventListener("click", () => {
  if (currentStep > 1) showResultStep(currentStep - 1);
});

resultNextBtn.addEventListener("click", () => {
  if (currentStep < TOTAL_STEPS) {
    showResultStep(currentStep + 1);
  } else {
    goHome();
  }
});

generateBtn.addEventListener("click", async () => {
  const text = clientEmail.value.trim();
  if (!text) {
    showMessage("Paste client requirements before generating a blueprint.", "warning");
    return;
  }
  setLoading(true);
  try {
    const res = await fetch("/api/generate", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ client_email: text }),
    });
    const data = await res.json();
    if (!res.ok) {
      showMessage(data.detail || "Request failed");
      return;
    }
    showResult(data);
  } catch (err) {
    showMessage(err.message || "Network error");
  } finally {
    setLoading(false);
  }
});
