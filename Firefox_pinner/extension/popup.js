const btn = document.getElementById("toggleBtn");
const status = document.getElementById("status");

function render(enabled) {
  if (enabled) {
    btn.textContent = "ON";
    btn.className = "on";
    status.textContent = "Collecting images...";
  } else {
    btn.textContent = "OFF";
    btn.className = "off";
    status.textContent = "Collection disabled";
  }
}

// Get current state from background
browser.runtime.sendMessage({ type: "getState" }).then((resp) => {
  render(resp.enabled);
});

btn.addEventListener("click", () => {
  browser.runtime.sendMessage({ type: "getState" }).then((resp) => {
    const newState = !resp.enabled;
    browser.runtime.sendMessage({ type: "toggle", enabled: newState }).then(() => {
      render(newState);
    });
  });
});
