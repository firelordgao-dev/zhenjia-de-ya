import http from "node:http";
import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import { analyzeCase } from "./agent.mjs";
import { loadEnvFile } from "./deepseekClient.mjs";

loadEnvFile();

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(__dirname, "..");
const publicDir = path.join(rootDir, "public");
const port = Number(process.env.PORT || 5177);

const mimeTypes = {
  ".html": "text/html; charset=utf-8",
  ".css": "text/css; charset=utf-8",
  ".js": "text/javascript; charset=utf-8",
  ".json": "application/json; charset=utf-8",
  ".svg": "image/svg+xml",
  ".png": "image/png",
  ".jpg": "image/jpeg",
  ".jpeg": "image/jpeg",
  ".webp": "image/webp"
};

const server = http.createServer(async (req, res) => {
  try {
    const url = new URL(req.url, `http://${req.headers.host || "localhost"}`);

    if (req.method === "GET" && url.pathname === "/api/health") {
      return sendJson(res, 200, { ok: true, name: "真的假的鸭", time: new Date().toISOString() });
    }

    if (req.method === "POST" && url.pathname === "/api/analyze") {
      const payload = await readJsonBody(req);
      if (!payload.text && !payload.imageNotes?.length) {
        return sendJson(res, 400, { error: "请先粘贴可疑内容，或补充截图中的文字说明。" });
      }
      const result = await analyzeCase(payload);
      return sendJson(res, 200, result);
    }

    if (req.method === "POST" && url.pathname === "/api/feedback") {
      const payload = await readJsonBody(req);
      console.info("[feedback]", JSON.stringify(payload).slice(0, 1000));
      return sendJson(res, 200, { ok: true });
    }

    if (req.method === "POST" && url.pathname === "/api/report-guide") {
      return sendJson(res, 200, {
        hotline: "110",
        anti_fraud_line: "96110",
        steps: [
          "立即停止转账、充值、屏幕共享或继续沟通。",
          "保存聊天记录、短信、电话、链接、二维码、转账凭证和收款账户。",
          "拨打 110 报警，说明已经发生或疑似发生电信网络诈骗。",
          "尽快联系银行或支付平台冻结账户、撤销可疑交易或修改密码。"
        ]
      });
    }

    return serveStatic(url.pathname, res);
  } catch (error) {
    console.error(error);
    return sendJson(res, 500, { error: "服务暂时开小差了，请稍后再试。", detail: error.message });
  }
});

server.listen(port, () => {
  console.log(`真的假的鸭 running at http://localhost:${port}`);
});

function serveStatic(requestPath, res) {
  const safePath = requestPath === "/" ? "/index.html" : decodeURIComponent(requestPath);
  const filePath = path.normalize(path.join(publicDir, safePath));

  if (!filePath.startsWith(publicDir)) {
    return sendText(res, 403, "Forbidden");
  }

  fs.readFile(filePath, (error, content) => {
    if (error) {
      fs.readFile(path.join(publicDir, "index.html"), (fallbackError, fallbackContent) => {
        if (fallbackError) return sendText(res, 404, "Not found");
        sendBuffer(res, 200, fallbackContent, "text/html; charset=utf-8");
      });
      return;
    }

    const ext = path.extname(filePath).toLowerCase();
    sendBuffer(res, 200, content, mimeTypes[ext] || "application/octet-stream");
  });
}

function readJsonBody(req) {
  return new Promise((resolve, reject) => {
    let body = "";
    req.on("data", (chunk) => {
      body += chunk;
      if (body.length > 1_000_000) {
        req.destroy();
        reject(new Error("请求内容过大"));
      }
    });
    req.on("end", () => {
      if (!body) return resolve({});
      try {
        resolve(JSON.parse(body));
      } catch {
        reject(new Error("请求不是有效 JSON"));
      }
    });
    req.on("error", reject);
  });
}

function sendJson(res, status, data) {
  sendText(res, status, JSON.stringify(data), "application/json; charset=utf-8");
}

function sendText(res, status, text, type = "text/plain; charset=utf-8") {
  res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
  res.end(text);
}

function sendBuffer(res, status, buffer, type) {
  res.writeHead(status, { "Content-Type": type, "Cache-Control": "no-store" });
  res.end(buffer);
}

