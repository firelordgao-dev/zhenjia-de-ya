const riskCopy = {
  low: "低风险",
  medium: "中风险",
  high: "高风险",
  emergency: "紧急风险"
};

const sampleText =
  "我是平台客服，你的快递丢失可以理赔 300 元。请马上点击这个链接填写银行卡号和验证码，逾期就不能退款。";

const els = {
  scenario: document.querySelector("#scenario"),
  scenarioButtons: [...document.querySelectorAll(".scenario-card")],
  caseText: document.querySelector("#caseText"),
  imageInput: document.querySelector("#imageInput"),
  imageList: document.querySelector("#imageList"),
  ocrPanel: document.querySelector("#ocrPanel"),
  ocrButton: document.querySelector("#ocrButton"),
  ocrStatus: document.querySelector("#ocrStatus"),
  analyzeButton: document.querySelector("#analyzeButton"),
  loadSampleButton: document.querySelector("#loadSampleButton"),
  textSizeButton: document.querySelector("#textSizeButton"),
  emptyState: document.querySelector("#emptyState"),
  loadingState: document.querySelector("#loadingState"),
  resultContent: document.querySelector("#resultContent"),
  statusPill: document.querySelector("#statusPill"),
  riskBanner: document.querySelector("#riskBanner"),
  riskLevelText: document.querySelector("#riskLevelText"),
  summaryText: document.querySelector("#summaryText"),
  redFlagsList: document.querySelector("#redFlagsList"),
  actionsList: document.querySelector("#actionsList"),
  policeNotice: document.querySelector("#policeNotice"),
  evidenceList: document.querySelector("#evidenceList"),
  familyMessage: document.querySelector("#familyMessage"),
  copyFamilyButton: document.querySelector("#copyFamilyButton"),
  metaText: document.querySelector("#metaText")
};

let imageNotes = [];
let selectedImages = [];
let lastAnalysis = null;

els.scenarioButtons.forEach((button) => {
  button.addEventListener("click", () => {
    setScenario(button.dataset.scenario);
  });
});

els.textSizeButton.addEventListener("click", () => {
  const isSenior = document.body.classList.toggle("senior-mode");
  els.textSizeButton.setAttribute("aria-pressed", String(isSenior));
  els.textSizeButton.textContent = isSenior ? "大字模式" : "标准字";
});

els.loadSampleButton.addEventListener("click", () => {
  els.caseText.value = sampleText;
  setScenario("payment");
  els.caseText.focus();
});

els.imageInput.addEventListener("change", () => {
  selectedImages = [...els.imageInput.files];
  imageNotes = selectedImages.map((file) => `${file.name} (${Math.round(file.size / 1024)}KB)`);
  renderImageNotes();

  els.ocrPanel.hidden = selectedImages.length === 0;
  els.ocrButton.disabled = selectedImages.length === 0;
  els.ocrStatus.textContent = selectedImages.length
    ? "可以点“识别截图文字”，识别后文字会自动放进输入框。"
    : "选择截图后，可以先识别文字，再让鸭鸭判断。";
});

els.ocrButton.addEventListener("click", runOcr);
els.analyzeButton.addEventListener("click", analyze);
els.copyFamilyButton.addEventListener("click", shareFamilyMessage);

function setScenario(value) {
  els.scenario.value = value;
  els.scenarioButtons.forEach((button) => {
    button.classList.toggle("is-selected", button.dataset.scenario === value);
  });
}

function renderImageNotes() {
  els.imageList.innerHTML = "";
  for (const note of imageNotes) {
    const chip = document.createElement("div");
    chip.className = "image-chip";
    chip.textContent = note;
    els.imageList.append(chip);
  }
}

async function runOcr() {
  if (!selectedImages.length) return;
  if (!window.Tesseract) {
    els.ocrStatus.textContent = "截图识别组件还没加载好。可以先手动输入，或稍后再试。";
    return;
  }

  els.ocrButton.disabled = true;
  els.ocrButton.textContent = "正在识别";
  const texts = [];

  try {
    for (let index = 0; index < selectedImages.length; index += 1) {
      const file = selectedImages[index];
      els.ocrStatus.textContent = `正在识别第 ${index + 1} 张截图，请稍等...`;

      const result = await window.Tesseract.recognize(file, "chi_sim+eng", {
        logger: (message) => {
          if (message.status === "recognizing text" && message.progress) {
            const percent = Math.round(message.progress * 100);
            els.ocrStatus.textContent = `正在识别第 ${index + 1} 张截图：${percent}%`;
          }
        }
      });

      const text = result?.data?.text?.trim();
      if (text) {
        texts.push(text);
      }
    }

    if (!texts.length) {
      els.ocrStatus.textContent = "没有识别出清楚文字。可以放大截图后重试，或简单打字说明。";
      return;
    }

    appendRecognizedText(texts.join("\n\n"));
    els.ocrStatus.textContent = "已识别截图文字，并放进输入框。你可以检查一下再分析。";
  } catch (error) {
    els.ocrStatus.textContent = `截图识别失败：${error.message || "请稍后再试"}`;
  } finally {
    els.ocrButton.disabled = false;
    els.ocrButton.textContent = "识别截图文字";
  }
}

function appendRecognizedText(text) {
  const current = els.caseText.value.trim();
  const block = `【截图识别文字】\n${text.trim()}`;
  els.caseText.value = current ? `${current}\n\n${block}` : block;
  els.caseText.focus();
}

async function analyze() {
  const text = els.caseText.value.trim();
  if (!text) {
    const message = selectedImages.length
      ? "请先点“识别截图文字”，或简单写下对方让你做什么。"
      : "请先写下对方让你做什么。";
    showInlineError(message);
    return;
  }

  setLoading(true);
  try {
    const response = await fetch("/api/analyze", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        text,
        scenario: els.scenario.value,
        userStates: getSelectedStates(),
        imageNotes
      })
    });

    const data = await response.json();
    if (!response.ok) {
      throw new Error(data.error || "分析失败");
    }

    renderResult(data.analysis, data.meta);
  } catch (error) {
    renderResult(
      {
        risk_level: "medium",
        summary: "暂时没有分析成功，先按可疑情况处理。",
        red_flags: [error.message],
        recommended_actions: ["先不要转账。", "不要给验证码、密码、银行卡。", "找家人或官方客服一起核实。"],
        police_notice: "如果已经转账或泄露重要信息，请立即拨打 110 报警。",
        evidence_to_keep: ["聊天记录", "电话号码", "链接或二维码", "转账凭证"],
        family_message: "我遇到一段可疑信息，工具暂时没分析成功，请帮我一起看看。"
      },
      { mode: "client_error", warning: error.message }
    );
  } finally {
    setLoading(false);
  }
}

function getSelectedStates() {
  return [...document.querySelectorAll(".state-group input:checked")].map((item) => item.value);
}

function setLoading(isLoading) {
  els.analyzeButton.disabled = isLoading;
  els.emptyState.hidden = true;
  els.resultContent.hidden = true;
  els.loadingState.hidden = !isLoading;
  els.statusPill.textContent = isLoading ? "分析中" : els.statusPill.textContent;
}

function renderResult(analysis, meta) {
  lastAnalysis = analysis;
  const level = analysis.risk_level || "medium";
  els.statusPill.textContent = riskCopy[level] || "有风险";
  els.riskLevelText.textContent = riskCopy[level] || "风险提醒";
  els.summaryText.textContent = analysis.summary || "建议暂停操作并核实。";

  els.riskBanner.className = `risk-banner risk-${level}`;
  renderList(els.redFlagsList, analysis.red_flags);
  renderList(els.actionsList, analysis.recommended_actions);
  renderList(els.evidenceList, analysis.evidence_to_keep);
  els.policeNotice.textContent = analysis.police_notice || "如已造成损失，请立即拨打 110 报警。";
  els.familyMessage.textContent = analysis.family_message || "我遇到一段可疑信息，请帮我一起看看。";
  els.metaText.textContent = JSON.stringify(meta || {}, null, 2);

  els.emptyState.hidden = true;
  els.loadingState.hidden = true;
  els.resultContent.hidden = false;
  els.resultContent.scrollIntoView({ behavior: "smooth", block: "start" });
}

function renderList(container, items = []) {
  container.innerHTML = "";
  for (const item of items) {
    const li = document.createElement("li");
    li.textContent = item;
    container.append(li);
  }
}

async function shareFamilyMessage() {
  if (!lastAnalysis) return;
  const text = buildShareText(lastAnalysis);

  try {
    if (navigator.share) {
      await navigator.share({
        title: "真的假的鸭风险提醒",
        text
      });
      els.copyFamilyButton.textContent = "已打开分享";
    } else {
      await navigator.clipboard.writeText(text);
      els.copyFamilyButton.textContent = "已复制";
    }
  } catch {
    await navigator.clipboard.writeText(text);
    els.copyFamilyButton.textContent = "已复制";
  }

  setTimeout(() => {
    els.copyFamilyButton.textContent = "分享给家人";
  }, 1400);
}

function buildShareText(analysis) {
  const actions = (analysis.recommended_actions || [])
    .map((item, index) => `${index + 1}. ${item}`)
    .join("\n");

  return [
    "我用“真的假的鸭”检查了一段可疑信息，请帮我一起确认。",
    "",
    `风险等级：${riskCopy[analysis.risk_level] || "有风险"}`,
    `结论：${analysis.summary || "建议暂停操作并核实。"}`,
    "",
    "现在建议：",
    actions || "先停止操作，找家人或官方渠道核实。",
    "",
    analysis.police_notice || "如果已经转账或泄露重要信息，请立即拨打 110 报警。"
  ].join("\n");
}

function showInlineError(message) {
  renderResult(
    {
      risk_level: "medium",
      summary: message,
      red_flags: ["现在还没有足够内容可以判断。"],
      recommended_actions: ["补充对方说了什么。", "补充对方让你做什么。", "如果涉及钱或验证码，先停下。"],
      police_notice: "如果已经转账、给过验证码或泄露银行卡信息，请立即拨打 110 报警。",
      evidence_to_keep: ["聊天记录", "电话号码", "链接或二维码"],
      family_message: "我有一段可疑信息还没弄清楚，请帮我一起看看。"
    },
    { mode: "local_validation" }
  );
}
