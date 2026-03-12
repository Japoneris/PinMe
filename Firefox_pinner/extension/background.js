const SERVER_URL = "http://localhost:8765/image";

let isEnabled = false;

// Restore state on startup
browser.storage.local.get("enabled").then((result) => {
  isEnabled = result.enabled || false;
  updateIcon(isEnabled);
});

function updateIcon(enabled) {
  const title = enabled ? "PintMe: ON" : "PintMe: OFF";
  browser.browserAction.setTitle({ title });
  browser.browserAction.setIcon({
    path: {
      16: enabled ? "icons/on16.png" : "icons/off16.png",
      32: enabled ? "icons/on32.png" : "icons/off32.png",
    }
  });
}

// Listen for toggle messages from the popup
browser.runtime.onMessage.addListener((msg) => {
  if (msg.type === "toggle") {
    isEnabled = msg.enabled;
    browser.storage.local.set({ enabled: isEnabled });
    updateIcon(isEnabled);
  } else if (msg.type === "getState") {
    return Promise.resolve({ enabled: isEnabled });
  }
});

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
    if (!isEnabled) return;

    const imageUrl = details.url;
    // documentUrl is the page that triggered the request
    const pageUrl = details.documentUrl || details.originUrl || "";

    try {
      const response = await fetch(imageUrl);
      if (!response.ok) return;

      const mimetype = (response.headers.get("content-type") || "application/octet-stream")
        .split(";")[0].trim();

      // Reject anything that is not a raster or vector image
      if (!mimetype.startsWith("image/")) return;

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
