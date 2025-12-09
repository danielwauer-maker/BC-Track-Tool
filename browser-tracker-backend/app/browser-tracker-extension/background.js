// background.js

// Backend URL – identisch zur content-script-Konfiguration
const BACKEND_EVENTS_URL = "http://0.0.0.0:8000/api/events/batch";

// simple Queue, falls mehrere Tabs senden
let sending = false;
let queue = [];

// Nachrichten von content-script
chrome.runtime.onMessage.addListener((message, sender, sendResponse) => {
  if (message.type === "BROWSER_EVENTS_BATCH" && Array.isArray(message.events)) {
    queue.push(...message.events);
    processQueue();
    sendResponse({ ok: true });
  }
  // true = async response möglich, hier aber nicht nötig
  return false;
});


function processQueue() {
  if (sending) return;
  if (queue.length === 0) return;

  sending = true;
  const batchSize = 50;
  const toSend = queue.splice(0, batchSize);

  fetch(BACKEND_EVENTS_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
      // Optional: später Auth-Header, Lizenz-Token etc.
    },
    body: JSON.stringify(toSend)
  })
    .then((res) => {
      if (!res.ok) {
        console.error("Failed to send events batch:", res.status, res.statusText);
        // Optional: Wieder in Queue schieben
      }
    })
    .catch((err) => {
      console.error("Error sending events:", err);
      // Optional: Wieder in Queue schieben
    })
    .finally(() => {
      sending = false;
      if (queue.length > 0) {
        // Weitere Batches direkt verarbeiten
        processQueue();
      }
    });
}
