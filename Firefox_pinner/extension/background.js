const SERVER_URL = "http://localhost:8765/image";

// Convert ArrayBuffer to base64 without stack overflow on large images
function arrayBufferToBase64(buffer) {
  const bytes = new Uint8Array(buffer);
  const chunkSize = 8192;
  let binary = "";
  for (let i = 0; i < bytes.length; i += chunkSize) {
    binary += String.fromCharCode(...bytes.subarray(i, i + chunkSize));
  }
  return btoa(binary);
}

browser.webRequest.onCompleted.addListener(
  async (details) => {
    const imageUrl = details.url;
    // documentUrl is the page that triggered the request
    const pageUrl = details.documentUrl || details.originUrl || "";

    try {
      const response = await fetch(imageUrl);
      if (!response.ok) return;

      const mimetype = (response.headers.get("content-type") || "application/octet-stream")
        .split(";")[0].trim();

      const buffer = await response.arrayBuffer();
      if (buffer.byteLength === 0) return;

      const base64 = arrayBufferToBase64(buffer);

      await fetch(SERVER_URL, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          image_data: base64,
          image_url: imageUrl,
          page_url: pageUrl,
          mimetype: mimetype,
        }),
      });
    } catch (e) {
      console.error("[pintest] failed to capture image:", imageUrl, e);
    }
  },
  { urls: ["<all_urls>"], types: ["image"] }
);
