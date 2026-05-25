const cloud = require("wx-server-sdk");

cloud.init({
  env: cloud.DYNAMIC_CURRENT_ENV
});

exports.main = async (event = {}) => {
  const fileID = String(event.fileID || "");
  if (!fileID) {
    return { text: "", error: "缺少截图文件。" };
  }

  const service = process.env.OCR_SERVICE_ID;
  const api = process.env.OCR_SERVICE_API || "OcrAllInOne";
  const ocrType = process.env.OCR_TYPE;

  if (!service) {
    return {
      text: "",
      error: "OCR_SERVICE_ID 未配置。请在微信云函数环境变量中配置已开通的 OCR 服务。"
    };
  }

  try {
    const temp = await cloud.getTempFileURL({ fileList: [fileID] });
    const imgUrl = temp.fileList?.[0]?.tempFileURL;
    if (!imgUrl) {
      return { text: "", error: "没有拿到截图临时链接。" };
    }

    const data = {
      img_url: imgUrl,
      data_type: Number(process.env.OCR_DATA_TYPE || 3)
    };
    if (ocrType) {
      data.ocr_type = Number.isNaN(Number(ocrType)) ? ocrType : Number(ocrType);
    }

    const result = await cloud.openapi.serviceMarket.invokeService({
      service,
      api,
      data,
      client_msg_id: `${Date.now()}-${Math.random().toString(16).slice(2)}`
    });

    return {
      text: extractText(result),
      raw: result,
      deleted: await deleteUploadedFile(fileID)
    };
  } catch (error) {
    return {
      text: "",
      error: error.message || "OCR 调用失败",
      deleted: await deleteUploadedFile(fileID)
    };
  }
};

async function deleteUploadedFile(fileID) {
  try {
    await cloud.deleteFile({
      fileList: [fileID]
    });
    return true;
  } catch {
    return false;
  }
}

function extractText(raw) {
  const values = [];

  walk(raw, (key, value) => {
    const lower = key.toLowerCase();
    if (
      typeof value === "string" &&
      value.trim() &&
      ["text", "word", "words", "detectedtext", "itemstring", "description"].some((name) =>
        lower.includes(name)
      )
    ) {
      values.push(value.trim());
    }
  });

  return [...new Set(values)].join("\n");
}

function walk(value, visit, key = "") {
  if (Array.isArray(value)) {
    value.forEach((item) => walk(item, visit, key));
    return;
  }

  if (value && typeof value === "object") {
    Object.keys(value).forEach((childKey) => {
      const child = value[childKey];
      visit(childKey, child);
      walk(child, visit, childKey);
    });
  }
}
