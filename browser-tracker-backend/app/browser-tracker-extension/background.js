// background.js

// Backend URL – identisch zur content-script-Konfiguration
const BACKEND_EVENTS_URL = "http://127.0.0.1:8000/api/events/batch";

// simple Queue, falls mehrere Tabs senden
let sending = false;
let queue = [];

// Nachrichten von content-script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  console.log("[LAT-BG] Message erhalten:", message.type);

  if (message.type === "BROWSER_EVENTS_BATCH" && Array.isArray(message.events)) {
    console.log("[LAT-BG] Events im Batch:", message.events.length);
    queue.push(...message.events);
    processQueue();
    sendResponse({ ok: true });
  }
  return false;
});

function processQueue() {
  if (sending) return;
  if (queue.length === 0) return;

  sending = true;
  const batchSize = 50;
  const toSend = queue.splice(0, batchSize);

  console.log("[LAT-BG] Sende an Backend:", BACKEND_EVENTS_URL, "Events:", toSend.length);

  fetch(BACKEND_EVENTS_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(toSend)
  })
    .then((res) => {
      console.log("[LAT-BG] Antwort vom Backend:", res.status, res.statusText);
      if (!res.ok) {
        console.error("Failed to send events batch:", res.status, res.statusText);
      }
    })
    .catch((err) => {
      console.error("[LAT-BG] Fehler beim Senden:", err);
    })
    .finally(() => {
      sending = false;
      if (queue.length > 0) {
        processQueue();
      }
    });
}
