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
    apiKey: envValue("DEEPSEEK_API_KEY"),
    apiBase: envValue("DEEPSEEK_API_BASE", "https://api.deepseek.com"),
    flashModel: envValue("DEEPSEEK_FLASH_MODEL", "deepseek-v4-flash")
  };
}

export function getModelProviders() {
  loadEnvFile();
  const providers = [];

  const minimaxApiKey = envValue("MINIMAX_API_KEY");
  if (minimaxApiKey) {
    providers.push({
      name: "minimax",
      apiKey: minimaxApiKey,
      apiBase: normalizeMiniMaxApiBase(envValue("MINIMAX_API_BASE", "https://api.minimaxi.com/v1")),
      path: envValue("MINIMAX_CHAT_PATH", "/chat/completions"),
      model: envValue("MINIMAX_MODEL", "MiniMax-M3"),
      temperature: envNumber("MINIMAX_TEMPERATURE", 0.2),
      maxCompletionTokens: envNumber("MINIMAX_MAX_COMPLETION_TOKENS", 1200)
    });
  }

  if (envValue("DEEPSEEK_API_KEY")) {
    const config = getDeepSeekConfig();
    providers.push({
      name: "deepseek",
      apiKey: config.apiKey,
      apiBase: config.apiBase,
      path: "/chat/completions",
      model: config.flashModel,
      temperature: envNumber("DEEPSEEK_TEMPERATURE", 0.2),
      maxCompletionTokens: envNumber("DEEPSEEK_MAX_TOKENS", 1200)
    });
  }

  return providers;
}

export async function chatCompletion({ provider, messages }) {
  if (!provider?.apiKey) {
    throw new Error("Missing provider API key");
  }

  const controller = new AbortController();
  const timer = setTimeout(() => controller.abort(), 25000);
  const base = provider.apiBase.replace(/\/$/, "");
  const pathPart = provider.path.startsWith("/") ? provider.path : `/${provider.path}`;
  const body = buildProviderBody(provider, messages);

  try {
    const response = await fetch(`${base}${pathPart}`, {
      method: "POST",
      headers: {
        Authorization: `Bearer ${provider.apiKey}`,
        "Content-Type": "application/json"
      },
      body: JSON.stringify(body),
      signal: controller.signal
    });

    const raw = await response.text();
    if (!response.ok) {
      throw new Error(`${provider.name} API ${response.status}: ${raw.slice(0, 500)}`);
    }

    const data = JSON.parse(raw);
    const content = data?.choices?.[0]?.message?.content;
    if (!content) {
      throw new Error(`${provider.name} API returned empty content`);
    }

    return {
      content,
      usage: data.usage,
      model: data.model || provider.model
    };
  } finally {
    clearTimeout(timer);
  }
}

function buildProviderBody(provider, messages) {
  const body = {
    model: provider.model,
    messages,
    temperature: provider.temperature,
    max_completion_tokens: provider.maxCompletionTokens
  };

  if (provider.name === "deepseek") {
    body.max_tokens = provider.maxCompletionTokens;
    body.response_format = { type: "json_object" };
  }

  if (provider.name === "minimax") {
    body.stream = false;
    if (envValue("MINIMAX_ENABLE_THINKING") === "false") {
      body.thinking = { type: "disabled" };
    }
  }

  return body;
}

function envValue(name, fallback = "") {
  const value = String(process.env[name] || "").trim();
  if (!value || /^\$\{[A-Z0-9_]+\}$/.test(value)) return fallback;
  return value;
}

function envNumber(name, fallback) {
  const value = envValue(name);
  if (!value) return fallback;
  const parsed = Number(value);
  return Number.isFinite(parsed) ? parsed : fallback;
}

function normalizeMiniMaxApiBase(value) {
  return String(value || "").replace("api.minimax.com", "api.minimaxi.com");
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

