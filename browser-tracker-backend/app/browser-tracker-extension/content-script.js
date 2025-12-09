// content-script.js

// HIER Backend-URL anpassen
const BACKEND_BASE_URL = "http://0.0.0.0:8000";
const EVENT_BATCH_MAX = 20;   // wie viele Events vor Flush
const EVENT_BATCH_INTERVAL = 3000; // ms

let eventBuffer = [];
let sessionKey = null;
let userExternalId = null;

// einfache Session-ID generieren
function generateSessionKey() {
  return 'sess-' + Math.random().toString(36).substring(2) + Date.now().toString(36);
}

// Beispiel: User aus DOM lesen – das musst du später an deine BC-Umgebung anpassen
function detectUserExternalId() {
  // TODO: Anpassen wenn Business Central User im DOM irgendwo sichtbar ist
  // Fallback: localStorage oder ein Element wie "#userName"
  let fromDom = document.querySelector("#userName, .username, .ms-nav-username");
  if (fromDom && fromDom.textContent) {
    return fromDom.textContent.trim();
  }
  // als Notfall: Name aus Title oder gar nichts
  return null;
}

// Event-Objekt generieren
function buildEventPayload(evt, extra = {}) {
  const target = evt.target || evt.srcElement;
  if (!target) return null;

  const pageUrl = window.location.href;
  const pageTitle = document.title || "";

  const elementType = target.tagName ? target.tagName.toLowerCase() : null;
  let elementRole = null;

  if (target.tagName === "BUTTON") {
    elementRole = "Button";
  } else if (target.tagName === "INPUT" || target.tagName === "SELECT" || target.tagName === "TEXTAREA") {
    elementRole = "Field";
  } else if (target.tagName === "A") {
    elementRole = "Link";
  }

  const elementLabel =
    (target.getAttribute("aria-label")) ||
    (target.labels && target.labels[0] && target.labels[0].innerText) ||
    target.placeholder ||
    target.innerText ||
    null;

  const elementName = target.name || null;
  const elementId = target.id || null;
  const elementPath = getDomPath(target);

  // Input-Werte nur bei passenden Aktionen
  let newVal = null;
  if (target.value !== undefined && (evt.type === "change" || evt.type === "input" || evt.type === "blur")) {
    newVal = target.value;
  }

  const payload = {
    timestamp: new Date().toISOString(),
    user_external_id: userExternalId,
    session_key: sessionKey,

    page_url: pageUrl,
    page_title: pageTitle,

    element_type: elementType,
    element_role: elementRole,
    element_label: truncate(elementLabel, 200),
    element_name: truncate(elementName, 200),
    element_id: truncate(elementId, 200),
    element_path: truncate(elementPath, 500),

    action_type: evt.type,
    old_value: null,   // kann man später im Script tracken
    new_value: newVal,

    meta: extra
  };

  return payload;
}

// DOM-Pfad einfach (nicht 100% unique, aber ausreichend für Prototyp)
function getDomPath(el) {
  if (!el || !el.parentNode) return el.tagName;
  const stack = [];
  let node = el;
  while (node.parentNode != null) {
    let sibCount = 0;
    let sibIndex = 0;
    for (let i = 0; i < node.parentNode.childNodes.length; i++) {
      const sib = node.parentNode.childNodes[i];
      if (sib.nodeName === node.nodeName) {
        if (sib === node) {
          sibIndex = sibCount;
        }
        sibCount++;
      }
    }
    const nodeName = node.nodeName.toLowerCase();
    if (sibCount > 1) {
      stack.unshift(`${nodeName}:nth-of-type(${sibIndex + 1})`);
    } else {
      stack.unshift(nodeName);
    }
    node = node.parentNode;
    if (!node || !node.tagName) break;
  }
  return stack.join(" > ");
}

function truncate(str, maxLength) {
  if (!str) return null;
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength) + "...";
}

// Buffer verarbeiten
function flushEventBuffer() {
  if (eventBuffer.length === 0) return;
  const batch = eventBuffer.slice();
  eventBuffer = [];

  chrome.runtime.sendMessage(
    {
      type: "BROWSER_EVENTS_BATCH",
      events: batch
    },
    () => {
      // Optional: Callback-Fehler ignorieren
      const err = chrome.runtime.lastError;
      if (err) {
        console.debug("Error sending batch to background:", err.message);
      }
    }
  );
}

// Listener registrieren
function setupEventListeners() {
  document.addEventListener("click", (evt) => {
    const payload = buildEventPayload(evt, {
      mouse_button: evt.button,
      client_x: evt.clientX,
      client_y: evt.clientY
    });
    if (payload) {
      eventBuffer.push(payload);
      if (eventBuffer.length >= EVENT_BATCH_MAX) {
        flushEventBuffer();
      }
    }
  }, true);

  document.addEventListener("change", (evt) => {
    const payload = buildEventPayload(evt);
    if (payload) {
      eventBuffer.push(payload);
      if (eventBuffer.length >= EVENT_BATCH_MAX) {
        flushEventBuffer();
      }
    }
  }, true);

  document.addEventListener("input", (evt) => {
    // Optional: nur bei bestimmten Feldern loggen, um Spam zu vermeiden
    const payload = buildEventPayload(evt);
    if (payload) {
      eventBuffer.push(payload);
      if (eventBuffer.length >= EVENT_BATCH_MAX) {
        flushEventBuffer();
      }
    }
  }, true);

  document.addEventListener("keydown", (evt) => {
    const payload = buildEventPayload(evt, {
      key: evt.key,
      code: evt.code
    });
    if (payload) {
      eventBuffer.push(payload);
      if (eventBuffer.length >= EVENT_BATCH_MAX) {
        flushEventBuffer();
      }
    }
  }, true);

  // zyklischer Flush
  setInterval(flushEventBuffer, EVENT_BATCH_INTERVAL);
}

// Init
(function init() {
  sessionKey = generateSessionKey();
  userExternalId = detectUserExternalId();
  setupEventListeners();
})();
