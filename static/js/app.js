/**
 * app.js  –  NutriAI Enhanced Frontend
 * Handles navigation, API calls, chat, forms, and all UI interactions.
 */

"use strict";

// ── State ─────────────────────────────────────────────────────────────────────
let currentPanel = "chat";
let selectedImageFile = null;
let fbRating = 3;
let mpRating = 0;

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", async () => {
  // Profile values depend on metadata-generated options and cuisine checkboxes.
  await loadMetadata();
  await loadProfile();
  checkHealth();
  buildStars("fbStars", 3, (r) => { fbRating = r; });
  buildStars("mpStars", 0, (r) => {
    mpRating = r;
    if (mpRating > 0) submitPlanFeedback(mpRating);
  });
});

// ── Panel navigation ──────────────────────────────────────────────────────────
function showPanel(name) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-item").forEach(b => b.classList.remove("active"));

  const panel = document.getElementById("panel-" + name);
  const btn   = document.querySelector(`[data-panel="${name}"]`);
  if (panel) panel.classList.add("active");
  if (btn)   btn.classList.add("active");
  currentPanel = name;

  const titles = {
    chat:        "💬 Chat Assistant",
    profile:     "👤 My Profile",
    mealplan:    "📅 Meal Planner",
    foodswap:    "🔄 Food Swaps",
    explain:     "🔬 Explain Food",
    image:       "📷 Image Analysis",
    lookup:      "🔍 Food Lookup",
    suggestions: "✨ AI Suggestions",
  };
  document.getElementById("panelTitle").textContent = titles[name] || name;

  // Close sidebar on mobile
  if (window.innerWidth <= 768) {
    document.getElementById("sidebar").classList.remove("open");
    document.getElementById("sidebarOverlay").classList.remove("visible");
  }
}

// ── Sidebar ───────────────────────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar  = document.getElementById("sidebar");
  const overlay  = document.getElementById("sidebarOverlay");
  const wrapper  = document.getElementById("mainWrapper");

  if (window.innerWidth <= 768) {
    sidebar.classList.toggle("open");
    overlay.classList.toggle("visible");
  } else {
    sidebar.classList.toggle("collapsed");
    wrapper.classList.toggle("expanded");
  }
}
document.getElementById("sidebarClose").addEventListener("click", toggleSidebar);

// ── Health check ──────────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res  = await fetch("/api/health");
    const data = await readJSON(res);
    const dot  = document.getElementById("statusDot");
    const txt  = document.getElementById("statusText");
    if (data.granite_ready) {
      dot.className = "status-dot live";
      txt.textContent = "Granite: Live";
    } else {
      dot.className = "status-dot demo";
      txt.textContent = "Demo Mode";
    }
  } catch {
    document.getElementById("statusDot").className = "status-dot error";
    document.getElementById("statusText").textContent = "Offline";
  }
}

// ── Metadata (dropdowns) ──────────────────────────────────────────────────────
async function loadMetadata() {
  try {
    const res  = await fetch("/api/metadata");
    const data = await readJSON(res);
    populateSelect("pHealthGoal",    data.health_goals,        formatOption);
    populateSelect("pActivityLevel", data.activity_levels,     formatOption);
    populateSelect("pDietaryPref",   data.dietary_preferences, formatOption);
    buildCuisineCheckboxes(data.cuisines);
  } catch (e) {
    console.error("Metadata load error:", e);
  }
}

function populateSelect(id, options, formatter) {
  const sel = document.getElementById(id);
  if (!sel) return;
  // Remove existing dynamic options (keep first placeholder if any)
  while (sel.options.length > 0) sel.remove(0);
  options.forEach(opt => {
    const el = document.createElement("option");
    el.value = opt;
    el.textContent = formatter ? formatter(opt) : opt;
    sel.appendChild(el);
  });
}

function formatOption(val) {
  return val.replace(/_/g, " ").replace(/\b\w/g, c => c.toUpperCase());
}

function buildCuisineCheckboxes(cuisines) {
  const container = document.getElementById("cuisineCheckboxes");
  if (!container) return;
  container.innerHTML = "";
  cuisines.forEach(c => {
    const label = document.createElement("label");
    const cb    = document.createElement("input");
    cb.type  = "checkbox";
    cb.value = c;
    cb.name  = "cuisine";
    label.appendChild(cb);
    label.append(" " + c);
    container.appendChild(label);
  });
}

// ── Profile ───────────────────────────────────────────────────────────────────
async function loadProfile() {
  try {
    const res  = await fetch("/api/profile");
    const data = await readJSON(res);
    if (data.status !== "ok") return;
    fillProfileForm(data.profile);
    if (data.profile.bmi) renderProfileStats(data.profile, data.profile);
  } catch (e) {
    console.error("Profile load error:", e);
  }
}

function fillProfileForm(p) {
  setVal("pName",         p.name !== "User" ? p.name : "");
  setVal("pAge",          p.age         || "");
  setVal("pGender",       p.gender      || "");
  setVal("pHeight",       p.height_cm   || "");
  setVal("pWeight",       p.weight_kg   || "");
  setVal("pTargetWeight", p.target_weight_kg || "");
  setVal("pHealthGoal",   p.health_goal || "");
  setVal("pActivityLevel", p.activity_level || "");
  setVal("pDietaryPref",  p.dietary_preference || "");
  setVal("pMealsPerDay",  p.meals_per_day || 3);
  setVal("pMedical",      (p.medical_conditions || []).join(", "));
  setVal("pAllergies",    (p.allergies          || []).join(", "));
  setVal("pDisliked",     (p.disliked_foods     || []).join(", "));
  setVal("pFitness",      p.fitness_routine || "");

  document.querySelectorAll('input[name="cuisine"]').forEach(cb => {
    cb.checked = (p.preferred_cuisines || []).includes(cb.value);
  });
}

function collectProfileData() {
  const cuisines = Array.from(document.querySelectorAll('input[name="cuisine"]:checked')).map(c => c.value);
  return {
    name:               getVal("pName")         || "User",
    age:                parseInt(getVal("pAge")) || null,
    gender:             getVal("pGender")        || null,
    height_cm:          parseFloat(getVal("pHeight"))       || null,
    weight_kg:          parseFloat(getVal("pWeight"))       || null,
    target_weight_kg:   parseFloat(getVal("pTargetWeight")) || null,
    health_goal:        getVal("pHealthGoal")     || "maintenance",
    activity_level:     getVal("pActivityLevel")  || "moderately_active",
    dietary_preference: getVal("pDietaryPref")    || "none",
    meals_per_day:      parseInt(getVal("pMealsPerDay")) || 3,
    medical_conditions: splitList(getVal("pMedical")),
    allergies:          splitList(getVal("pAllergies")),
    disliked_foods:     splitList(getVal("pDisliked")),
    preferred_cuisines: cuisines,
    fitness_routine:    getVal("pFitness") || "",
  };
}

async function saveProfile(event) {
  if (event) event.preventDefault();
  const data = collectProfileData();
  showLoading("Saving profile…");
  try {
    const res  = await postJSON("/api/profile", data);
    const resp = await res.json();
    hideLoading();
    if (resp.status === "ok") {
      showToast("Profile saved! ✓", "success");
      renderProfileStats(data, resp);
    } else {
      showToast("Save failed: " + (resp.message || "Unknown error"), "error");
    }
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

function renderProfileStats(profile, extras) {
  const container = document.getElementById("profileStats");
  if (!container) return;

  const stats = [];
  if (extras.bmi)            stats.push({ value: extras.bmi,                    label: `BMI (${extras.bmi_category || ""})` });
  if (extras.daily_calories) stats.push({ value: extras.daily_calories + " kcal", label: "Daily Target" });
  if (profile.weight_kg)     stats.push({ value: profile.weight_kg + " kg",     label: "Weight" });
  if (profile.height_cm)     stats.push({ value: profile.height_cm + " cm",     label: "Height" });

  if (stats.length === 0) { container.classList.add("hidden"); return; }

  container.innerHTML = stats.map(s =>
    `<div class="stat-card"><div class="stat-value">${s.value}</div><div class="stat-label">${s.label}</div></div>`
  ).join("");
  container.classList.remove("hidden");
}

async function resetProfile() {
  if (!confirm("Reset your profile and conversation history?")) return;
  await postJSON("/api/profile/reset", {});
  location.reload();
}

// ── Chat ──────────────────────────────────────────────────────────────────────
function fillChat(text) {
  const input = document.getElementById("chatInput");
  input.value = text;
  autoResize(input);
  input.focus();
  // Hide suggestion pills after use
  document.getElementById("chatSuggestions").style.display = "none";
}

function chatKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
}

function autoResize(el) {
  el.style.height = "auto";
  el.style.height = Math.min(el.scrollHeight, 160) + "px";
}

async function sendChat() {
  const input = document.getElementById("chatInput");
  const msg   = input.value.trim();
  if (!msg) return;

  appendMessage("user", msg);
  input.value = "";
  input.style.height = "auto";

  // Hide chat pills once user starts chatting
  const pills = document.getElementById("chatSuggestions");
  if (pills) pills.style.display = "none";

  const typingEl = appendTyping();
  try {
    const res  = await postJSON("/api/chat", { message: msg });
    const data = await readJSON(res);
    typingEl.remove();
    if (data.status === "ok") {
      appendMessage("assistant", data.html, true);
    } else {
      appendMessage("assistant", "Sorry, something went wrong. Please try again.");
    }
  } catch {
    typingEl.remove();
    appendMessage("assistant", "Network error. Please check your connection.");
  }
}

function appendMessage(role, content, isHtml = false) {
  const container = document.getElementById("chatMessages");
  const div       = document.createElement("div");
  div.className   = `chat-msg ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = role === "user" ? "You" : "🤖";

  const contentDiv = document.createElement("div");
  contentDiv.className = "msg-content";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  if (isHtml) {
    bubble.innerHTML = sanitizeHTML(content);
  } else {
    bubble.textContent = content;
  }

  const time = document.createElement("div");
  time.className = "msg-time";
  time.textContent = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });

  contentDiv.appendChild(bubble);
  contentDiv.appendChild(time);
  div.appendChild(avatar);
  div.appendChild(contentDiv);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

function appendTyping() {
  const container = document.getElementById("chatMessages");
  const div       = document.createElement("div");
  div.className   = "chat-msg assistant";

  const avatar = document.createElement("div");
  avatar.className = "msg-avatar";
  avatar.textContent = "🤖";

  const contentDiv = document.createElement("div");
  contentDiv.className = "msg-content";

  const bubble = document.createElement("div");
  bubble.className = "msg-bubble";
  bubble.innerHTML = '<div class="typing-dots"><span></span><span></span><span></span></div>';

  contentDiv.appendChild(bubble);
  div.appendChild(avatar);
  div.appendChild(contentDiv);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

async function clearChat() {
  await postJSON("/api/chat/clear", {});
  const container = document.getElementById("chatMessages");
  container.innerHTML = "";
  appendMessage("assistant", "Conversation cleared. How can I help you today? 🥗");
  // Show suggestions again
  const pills = document.getElementById("chatSuggestions");
  if (pills) pills.style.display = "";
}

// ── Meal Plan ─────────────────────────────────────────────────────────────────
async function generateMealPlan() {
  const days = document.getElementById("mpDays").value;
  showLoading(`Generating ${days}-day meal plan…`);
  try {
    const res  = await postJSON("/api/meal-plan", { days: parseInt(days) });
    const data = await readJSON(res);
    hideLoading();
    if (data.status === "ok") {
      showResult("mealPlanResult", data.html);
      document.getElementById("mealPlanFeedback").classList.remove("hidden");
      buildStars("mpStars", 0, (r) => { mpRating = r; submitPlanFeedback(r); });
    } else {
      showToast(data.message || "Failed to generate meal plan", "error");
    }
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

async function submitPlanFeedback(rating) {
  await postJSON("/api/feedback", {
    type:   "plan",
    item:   `${document.getElementById("mpDays").value}-day meal plan`,
    rating: rating,
    note:   "",
  });
  showToast(`Thanks for the ${rating}★ rating!`, "success");
}

// ── Food Swaps ────────────────────────────────────────────────────────────────
async function getSwaps() {
  const foods  = getVal("swapFoods").trim();
  const reason = getVal("swapReason").trim();
  if (!foods) { showToast("Please enter at least one food item", "error"); return; }

  showLoading("Finding smart food swaps…");
  try {
    const res  = await postJSON("/api/food-swap", {
      foods: foods.split(",").map(f => f.trim()).filter(Boolean),
      reason
    });
    const data = await readJSON(res);
    hideLoading();
    if (data.status === "ok") showResult("swapResult", data.html);
    else showToast(data.message || "Error getting swaps", "error");
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

// ── Nutritional Explanation ───────────────────────────────────────────────────
async function explainFoodItem() {
  const food = getVal("explainFood").trim();
  if (!food) { showToast("Please enter a food name", "error"); return; }
  await doExplain(food);
}

async function quickExplain(food) {
  setVal("explainFood", food);
  await doExplain(food);
}

async function doExplain(food) {
  showLoading(`Analysing "${food}"…`);
  try {
    const res  = await postJSON("/api/explain", { food });
    const data = await readJSON(res);
    hideLoading();
    if (data.status === "ok") showResult("explainResult", data.html);
    else showToast(data.message || "Error", "error");
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

// ── Image Analysis ────────────────────────────────────────────────────────────
function handleImageSelect(event) {
  const file = event.target.files[0];
  if (file) loadImageFile(file);
}

function handleDrop(event) {
  event.preventDefault();
  document.getElementById("uploadZone").classList.remove("drag-active");
  const file = event.dataTransfer.files[0];
  if (file) loadImageFile(file);
}

function loadImageFile(file) {
  const allowedTypes = ["image/png", "image/jpeg", "image/webp", "image/gif"];
  const maxBytes = 10 * 1024 * 1024;
  if (!allowedTypes.includes(file.type)) {
    showToast("Choose a PNG, JPG, WebP or GIF image.", "error");
    clearImage();
    return;
  }
  if (file.size > maxBytes) {
    showToast("Image must be 10 MB or smaller.", "error");
    clearImage();
    return;
  }

  const reader = new FileReader();
  reader.onerror = () => {
    showToast("Could not read this image. Please try another file.", "error");
    clearImage();
  };
  reader.onload = (e) => {
    selectedImageFile = file;
    document.getElementById("imagePreview").src = e.target.result;
    document.getElementById("imagePreviewWrapper").classList.remove("hidden");
    document.getElementById("uploadZone").classList.add("hidden");
    document.getElementById("analyseBtn").disabled = false;
  };
  reader.readAsDataURL(file);
}

function clearImage() {
  selectedImageFile = null;
  document.getElementById("imageInput").value = "";
  document.getElementById("imagePreviewWrapper").classList.add("hidden");
  document.getElementById("uploadZone").classList.remove("hidden");
  document.getElementById("analyseBtn").disabled = true;
  document.getElementById("imageResult").classList.add("hidden");
}

async function analyseImage() {
  if (!selectedImageFile) { showToast("No image selected", "error"); return; }

  showLoading("Analysing image with IBM Granite…");
  const formData = new FormData();
  formData.append("image", selectedImageFile);

  try {
    const res  = await fetch("/api/analyse-image", { method: "POST", body: formData });
    const data = await readJSON(res);
    hideLoading();
    if (data.status === "ok") showResult("imageResult", data.html);
    else showToast(data.message || "Analysis failed", "error");
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

// ── Food Lookup ───────────────────────────────────────────────────────────────
let _lookupTimer = null;

function searchFoodsLive() {
  clearTimeout(_lookupTimer);
  const q = getVal("lookupQuery").trim();
  if (q.length < 2) { document.getElementById("lookupSuggestions").innerHTML = ""; return; }
  _lookupTimer = setTimeout(async () => {
    try {
      const res  = await fetch(`/api/food-lookup?q=${encodeURIComponent(q)}`);
      const data = await readJSON(res);
      const container = document.getElementById("lookupSuggestions");
      container.replaceChildren();
      (data.suggestions || []).forEach((item) => {
        const name = String(item.name || "").trim();
        if (!name) return;
        const button = document.createElement("button");
        button.type = "button";
        button.className = "sug-tag";
        button.textContent = capitalize(name);
        button.addEventListener("click", () => quickLookup(name));
        container.appendChild(button);
      });
    } catch {}
  }, 280);
}

async function lookupFood() {
  const q = getVal("lookupQuery").trim();
  if (!q) { showToast("Enter a food name", "error"); return; }
  await quickLookup(q);
}

async function quickLookup(food) {
  setVal("lookupQuery", food);
  showLoading("Looking up nutrition data…");
  try {
    const res  = await fetch(`/api/food-lookup?q=${encodeURIComponent(food)}`);
    const data = await readJSON(res);
    hideLoading();
    if (data.food && !data.food.error) {
      const f = data.food;
      const html = `
        <h2>🥗 ${capitalize(f.name)}</h2>
        <p style="color:var(--muted);font-size:.8rem;margin-bottom:10px;">Nutritional values per 100g / serving · Source: ${f.source}</p>
        <table>
          <tr><th>Nutrient</th><th>Amount</th><th>Daily Value %</th></tr>
          <tr><td><strong>Calories</strong></td><td><strong>${f.calories} kcal</strong></td><td>—</td></tr>
          <tr><td>Protein</td><td>${f.protein} g</td><td>${Math.round((f.protein/50)*100)}%</td></tr>
          <tr><td>Carbohydrates</td><td>${f.carbs} g</td><td>${Math.round((f.carbs/275)*100)}%</td></tr>
          <tr><td>Total Fat</td><td>${f.fat} g</td><td>${Math.round((f.fat/78)*100)}%</td></tr>
          <tr><td>Dietary Fiber</td><td>${f.fiber} g</td><td>${Math.round((f.fiber/28)*100)}%</td></tr>
        </table>`;
      showResult("lookupResult", html);
    } else {
      showResult("lookupResult", `<p>No data found for <strong>${food}</strong>. Try the Chat Assistant for detailed information.</p>`);
    }
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

// ── Adaptive Suggestions ──────────────────────────────────────────────────────
async function getSuggestions() {
  showLoading("Generating personalised suggestions…");
  try {
    const res  = await fetch("/api/suggestions");
    const data = await readJSON(res);
    hideLoading();
    if (data.status === "ok") showResult("suggestionsResult", data.html);
    else showToast("Error getting suggestions", "error");
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

// ── Feedback ──────────────────────────────────────────────────────────────────
async function submitFeedback() {
  const item = getVal("fbItem").trim();
  if (!item)    { showToast("Please enter a food or meal name", "error"); return; }
  if (!fbRating){ showToast("Please select a rating", "error"); return; }

  try {
    const res  = await postJSON("/api/feedback", {
      type:   getVal("fbType"),
      item:   item,
      rating: fbRating,
      note:   getVal("fbNote"),
    });
    const data = await readJSON(res);
    if (data.status === "ok") {
      showToast("Feedback submitted! ✓", "success");
      setVal("fbItem", "");
      setVal("fbNote", "");
      buildStars("fbStars", 3, (r) => { fbRating = r; });
    } else {
      showToast(data.message || "Error", "error");
    }
  } catch {
    showToast("Network error", "error");
  }
}

// ── Stars ─────────────────────────────────────────────────────────────────────
function buildStars(containerId, initialRating, onChange) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.replaceChildren();
  let current = initialRating;
  container.setAttribute("role", "group");
  container.setAttribute("aria-label", "Rate from 1 to 5 stars");

  for (let i = 1; i <= 5; i++) {
    const button = document.createElement("button");
    button.type = "button";
    button.className = "star" + (i <= current ? " on" : "");
    button.textContent = "★";
    button.setAttribute("aria-label", `${i} out of 5 stars`);
    button.setAttribute("aria-pressed", String(i === current));
    button.addEventListener("focus", () => highlightStars(container, i));
    button.addEventListener("blur", () => highlightStars(container, current));
    button.addEventListener("mouseover", () => highlightStars(container, i));
    button.addEventListener("mouseout", () => highlightStars(container, current));
    button.addEventListener("click", () => {
      current = i;
      highlightStars(container, current);
      container.querySelectorAll(".star").forEach((star, index) =>
        star.setAttribute("aria-pressed", String(index + 1 === current))
      );
      if (onChange) onChange(current);
    });
    container.appendChild(button);
  }
}

function highlightStars(container, count) {
  container.querySelectorAll(".star").forEach((s, idx) => {
    s.classList.toggle("on", idx < count);
  });
}


/**
 * Render model/API HTML through a strict allowlist. Unknown elements are unwrapped
 * (or discarded for active-content elements); all event/style attributes are removed.
 */
function sanitizeHTML(untrustedHTML) {
  const allowedTags = new Set([
    "P", "BR", "HR", "H1", "H2", "H3", "H4", "STRONG", "B", "EM", "I",
    "UL", "OL", "LI", "BLOCKQUOTE", "PRE", "CODE", "TABLE", "THEAD",
    "TBODY", "TR", "TH", "TD", "A"
  ]);
  const blockedTags = new Set(["SCRIPT", "STYLE", "IFRAME", "OBJECT", "EMBED", "SVG", "MATH"]);
  const parser = new DOMParser();
  const parsed = parser.parseFromString(String(untrustedHTML ?? ""), "text/html");

  function clean(node) {
    [...node.childNodes].forEach((child) => {
      if (child.nodeType === Node.COMMENT_NODE) {
        child.remove();
        return;
      }
      if (child.nodeType !== Node.ELEMENT_NODE) return;
      if (blockedTags.has(child.tagName)) {
        child.remove();
        return;
      }
      clean(child);
      if (!allowedTags.has(child.tagName)) {
        child.replaceWith(...child.childNodes);
        return;
      }
      [...child.attributes].forEach((attr) => {
        const name = attr.name.toLowerCase();
        if (child.tagName === "A" && name === "href") {
          const value = attr.value.trim();
          if (/^(https?:|mailto:)/i.test(value)) {
            child.setAttribute("href", value);
            child.setAttribute("rel", "noopener noreferrer");
            child.setAttribute("target", "_blank");
            continue;
          }
        }
        if (child.tagName === "TH" && ["colspan", "rowspan", "scope"].includes(name)) continue;
        if (child.tagName === "TD" && ["colspan", "rowspan"].includes(name)) continue;
        child.removeAttribute(attr.name);
      });
    });
  }

  clean(parsed.body);
  return parsed.body.innerHTML;
}

async function readJSON(response) {
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("The server returned an unreadable response.");
  }
  if (!response.ok) {
    throw new Error(data?.message || `Request failed (${response.status}). Please try again.`);
  }
  return data;
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function getVal(id)      { const el = document.getElementById(id); return el ? el.value : ""; }
function setVal(id, val) { const el = document.getElementById(id); if (el) el.value = val; }
function splitList(str)  { return str ? str.split(",").map(s => s.trim()).filter(Boolean) : []; }
function capitalize(s)   { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

function showResult(id, html) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = sanitizeHTML(html);
  el.classList.remove("hidden");
  setTimeout(() => el.scrollIntoView({ behavior: "smooth", block: "nearest" }), 50);
}

async function postJSON(url, body) {
  return fetch(url, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(body),
  });
}

function showLoading(text = "IBM Granite is thinking…") {
  document.getElementById("loadingText").textContent = text;
  document.getElementById("loadingOverlay").classList.remove("hidden");
}

function hideLoading() {
  document.getElementById("loadingOverlay").classList.add("hidden");
}

let _toastTimer = null;
function showToast(message, type = "") {
  const toast = document.getElementById("toast");
  toast.textContent = message;
  toast.className   = "toast" + (type ? " " + type : "");
  toast.classList.remove("hidden");
  clearTimeout(_toastTimer);
  _toastTimer = setTimeout(() => toast.classList.add("hidden"), 3200);
}
