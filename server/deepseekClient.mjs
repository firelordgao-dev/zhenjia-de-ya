import fs from "node:fs";
import path from "node:path";

let envLoaded = false;

export function loadEnvFile(cwd = process.cwd()) {
  if (envLoaded) return;
  envLoaded = true;

  const envPath = path.join(cwd, ".env");
  if (!fs.existsSync(envPath)) return;

  const content = fs.readFileSync(envPath, "utf8");
  for (const line of content.split(/\r?\n/)) {
    const trimmed = line.trim();
    if (!trimmed || trimmed.startsWith("#")) continue;
    const eqIndex = trimmed.indexOf("=");
    if (eqIndex === -1) continue;

    const key = trimmed.slice(0, eqIndex).trim();
    let value = trimmed.slice(eqIndex + 1).trim();
    if (
      (value.startsWith('"') && value.endsWith('"')) ||
      (value.startsWith("'") && value.endsWith("'"))
    ) {
      value = value.slice(1, -1);
    }
    if (!process.env[key]) {
      process.env[key] = value;
    }
  }
}

export function getDeepSeekConfig() {
  loadEnvFile();
  return {
    apiKey: process.env.DEEPSEEK_API_KEY || "",
    apiBase: process.env.DEEPSEEK_API_BASE || "https://api.deepseek.com",
    flashModel: process.env.DEEPSEEK_FLASH_MODEL || "deepseek-v4-flash",
    proModel: process.env.DEEPSEEK_PRO_MODEL || "deepseek-v4-pro"
  };
}

export async function chatCompletion({ model, messages, temperature = 0.2, maxTokens = 1200 }) {
  const config = getDeepSeekConfig();
  if (!config.apiKey) {
    throw new Error("Missing DEEPSEEK_API_KEY");
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 25000);

  try {
    const response = await fetch(`${config.apiBase.replace(/\/$/, "")}/chat/completions`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${config.apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        model,
        messages,
        temperature,
        max_tokens: maxTokens,
        response_format: { type: "json_object" }
      }),
      signal: controller.signal
    });

    const raw = await response.text();
    if (!response.ok) {
      throw new Error(`DeepSeek API ${response.status}: ${raw.slice(0, 500)}`);
    }

    const data = JSON.parse(raw);
    const content = data?.choices?.[0]?.message?.content;
    if (!content) {
      throw new Error("DeepSeek API returned empty content");
    }

    return {
      content,
      usage: data.usage,
      model: data.model || model
    };
  } finally {
    clearTimeout(timer);
  }
}

export function parseModelJson(content) {
  const text = String(content || "").trim();
  try {
    return JSON.parse(text);
  } catch {
    const start = text.indexOf("{");
    const end = text.lastIndexOf("}");
    if (start >= 0 && end > start) {
      return JSON.parse(text.slice(start, end + 1));
    }
    throw new Error("Model response was not valid JSON");
  }
}

