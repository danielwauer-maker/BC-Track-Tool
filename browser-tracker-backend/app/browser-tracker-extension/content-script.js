// content-script.js

// Backend-Endpunkt
const BACKEND_EVENTS_URL = "http://127.0.0.1:8000/api/events/batch";
const EVENT_BATCH_MAX = 20;
const EVENT_BATCH_INTERVAL = 3000;

let eventBuffer = [];
let sessionKey = null;
let userExternalId = null;

// Debug: Content-Script geladen?
console.log("[LAT] Content script geladen auf:", window.location.href);

// einfache Session-ID generieren
function generateSessionKey() {
  return "sess-" + Math.random().toString(36).substring(2) + Date.now().toString(36);
}

// TODO: Später an BC-DOM anpassen
function detectUserExternalId() {
  // Beispiel: BC blende irgendwo den Usernamen ein
  let fromDom = document.querySelector("#userName, .username, .ms-nav-username");
  if (fromDom && fromDom.textContent) {
    return fromDom.textContent.trim();
  }
  return null;
}

function truncate(str, maxLength) {
  if (!str) return null;
  if (str.length <= maxLength) return str;
  return str.substring(0, maxLength) + "...";
}

// Dom-Pfad
function getDomPath(el) {
  if (!el || !el.parentNode) return el?.tagName || null;
  const stack = [];
  let node = el;
  while (node && node.parentNode) {
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

function buildEventPayload(evt, extra = {}) {
  const target = evt.target || evt.srcElement;
  if (!target) return null;

  const pageUrl = window.location.href;
  const pageTitle = document.title || "";

  const elementType = target.tagName ? target.tagName.toLowerCase() : null;
  let elementRole = null;

  if (target.tagName === "BUTTON") {
    elementRole = "Button";
  } else if (["INPUT", "SELECT", "TEXTAREA"].includes(target.tagName)) {
    elementRole = "Field";
  } else if (target.tagName === "A") {
    elementRole = "Link";
  }

  const elementLabel =
    target.getAttribute("aria-label") ||
    (target.labels && target.labels[0] && target.labels[0].innerText) ||
    target.placeholder ||
    target.innerText ||
    null;

  const elementName = target.name || null;
  const elementId = target.id || null;
  const elementPath = getDomPath(target);

  let newVal = null;
  if (
    target.value !== undefined &&
    (evt.type === "change" || evt.type === "blur")
  ) {
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
    old_value: null,
    new_value: newVal,
    meta: extra
  };

  return payload;
}

function flushEventBuffer() {
  if (eventBuffer.length === 0) return;

  const batch = eventBuffer.slice();
  eventBuffer = [];

  console.log("[LAT] Sende Batch an Backend:", batch.length, "Events");

  fetch(BACKEND_EVENTS_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json"
    },
    body: JSON.stringify(batch)
  })
    .then((res) => {
      console.log("[LAT] Antwort vom Backend:", res.status, res.statusText);
      if (!res.ok) {
        return res.text().then((t) => {
          console.error("[LAT] Fehler-Body:", t);
        });
      }
    })
    .catch((err) => {
      console.error("[LAT] Fetch-Fehler:", err);
    });
}

function setupEventListeners() {
  console.log("[LAT] Registriere Event-Listener im Frame:", window.location.href);

  document.addEventListener(
    "click",
    (evt) => {
      console.log("[LAT] Raw click event auf", window.location.href, "Target:", evt.target);

      const payload = buildEventPayload(evt, {
        mouse_button: evt.button,
        client_x: evt.clientX,
        client_y: evt.clientY
      });
      if (payload) {
        eventBuffer.push(payload);
        console.log("[LAT] Event in Buffer gelegt. Buffer-Länge:", eventBuffer.length);
        if (eventBuffer.length >= EVENT_BATCH_MAX) {
          flushEventBuffer();
        }
      } else {
        console.log("[LAT] Konnte für diesen Click kein Payload bauen");
      }
    },
    true
  );

  document.addEventListener(
    "change",
    (evt) => {
      console.log("[LAT] Raw change event auf", window.location.href, "Target:", evt.target);

      const payload = buildEventPayload(evt);
      if (payload) {
        eventBuffer.push(payload);
        console.log("[LAT] Event in Buffer gelegt (change). Buffer-Länge:", eventBuffer.length);
        if (eventBuffer.length >= EVENT_BATCH_MAX) {
          flushEventBuffer();
        }
      }
    },
    true
  );

  document.addEventListener(
    "keydown",
    (evt) => {
      const payload = buildEventPayload(evt, {
        key: evt.key,
        code: evt.code
      });
      if (payload) {
        eventBuffer.push(payload);
        console.log("[LAT] Keydown-Event in Buffer. Buffer-Länge:", eventBuffer.length, "Key:", evt.key);
        if (eventBuffer.length >= EVENT_BATCH_MAX) {
          flushEventBuffer();
        }
      }
    },
    true
  );

  setInterval(() => {
    console.log("[LAT] Timer-Flush. Aktuelle Buffer-Länge:", eventBuffer.length);
    flushEventBuffer();
  }, EVENT_BATCH_INTERVAL);
}


// Init
(function init() {
  sessionKey = generateSessionKey();
  userExternalId = detectUserExternalId();
  console.log("[LAT] Session:", sessionKey, "User:", userExternalId);
  setupEventListeners();
})();
