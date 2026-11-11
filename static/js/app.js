/**
 * app.js  –  NutriAI Frontend
 * Handles all panel navigation, API calls, and UI interactions.
 */

"use strict";

// ── State ─────────────────────────────────────────────────────────────────────
let currentPanel      = "chat";
let selectedImageFile = null;
let mealPlanText      = "";   // last generated plan (for feedback)
let fbRating          = 3;
let mpRating          = 0;

// ── Boot ──────────────────────────────────────────────────────────────────────
document.addEventListener("DOMContentLoaded", () => {
  loadMetadata();
  loadProfile();
  checkHealth();
  buildStars("fbStars", 3, (r) => { fbRating = r; });
  buildStars("mpStars", 0, (r) => { mpRating = r; });
});

// ── Panel navigation ──────────────────────────────────────────────────────────
function showPanel(name) {
  document.querySelectorAll(".panel").forEach(p => p.classList.remove("active"));
  document.querySelectorAll(".nav-btn").forEach(b => b.classList.remove("active"));

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
    suggestions: "✨ Adaptive Suggestions",
  };
  document.getElementById("panelTitle").textContent = titles[name] || name;

  // Close sidebar on mobile
  if (window.innerWidth <= 768) {
    document.getElementById("sidebar").classList.remove("open");
  }
}

// ── Sidebar toggle ────────────────────────────────────────────────────────────
function toggleSidebar() {
  const sidebar = document.getElementById("sidebar");
  if (window.innerWidth <= 768) {
    sidebar.classList.toggle("open");
  } else {
    sidebar.classList.toggle("collapsed");
    document.querySelector(".main-wrapper").classList.toggle("full");
  }
}
document.getElementById("sidebarClose").addEventListener("click", toggleSidebar);

// ── Health check ──────────────────────────────────────────────────────────────
async function checkHealth() {
  try {
    const res  = await fetch("/api/health");
    const data = await res.json();
    const dot  = document.getElementById("statusDot");
    const txt  = document.getElementById("statusText");
    if (data.granite_ready) {
      dot.className = "status-dot live";
      txt.textContent = "IBM Granite: Live";
    } else {
      dot.className = "status-dot demo";
      txt.textContent = "Demo Mode";
    }
  } catch {
    document.getElementById("statusDot").className = "status-dot error";
    document.getElementById("statusText").textContent = "Server error";
  }
}

// ── Metadata (dropdowns) ──────────────────────────────────────────────────────
async function loadMetadata() {
  try {
    const res  = await fetch("/api/metadata");
    const data = await res.json();

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
    const data = await res.json();
    if (data.status !== "ok") return;
    fillProfileForm(data.profile);
    if (data.profile.bmi) renderProfileStats(data.profile, data.profile);
  } catch (e) {
    console.error("Profile load error:", e);
  }
}

function fillProfileForm(p) {
  setVal("pName",        p.name !== "User" ? p.name : "");
  setVal("pAge",         p.age         || "");
  setVal("pGender",      p.gender      || "");
  setVal("pHeight",      p.height_cm   || "");
  setVal("pWeight",      p.weight_kg   || "");
  setVal("pTargetWeight",p.target_weight_kg || "");
  setVal("pHealthGoal",  p.health_goal || "");
  setVal("pActivityLevel", p.activity_level || "");
  setVal("pDietaryPref", p.dietary_preference || "");
  setVal("pMealsPerDay", p.meals_per_day || 3);
  setVal("pMedical",     (p.medical_conditions || []).join(", "));
  setVal("pAllergies",   (p.allergies          || []).join(", "));
  setVal("pDisliked",    (p.disliked_foods     || []).join(", "));
  setVal("pFitness",     p.fitness_routine || "");

  // Cuisine checkboxes
  const checkboxes = document.querySelectorAll('input[name="cuisine"]');
  checkboxes.forEach(cb => {
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
      showToast("Save failed: " + resp.message, "error");
    }
  } catch (e) {
    hideLoading();
    showToast("Network error", "error");
  }
}

function renderProfileStats(profile, extras) {
  const container = document.getElementById("profileStats");
  if (!container) return;
  const stats = [];
  if (extras.bmi)          stats.push({ value: extras.bmi,            label: `BMI (${extras.bmi_category || ""})` });
  if (extras.daily_calories) stats.push({ value: extras.daily_calories + " kcal", label: "Daily Target" });
  if (profile.weight_kg)   stats.push({ value: profile.weight_kg + " kg",  label: "Current Weight" });
  if (profile.target_weight_kg) stats.push({ value: profile.target_weight_kg + " kg", label: "Target Weight" });

  if (stats.length === 0) { container.classList.add("hidden"); return; }

  container.innerHTML = stats.map(s =>
    `<div class="stat-card"><div class="stat-value">${s.value}</div><div class="stat-label">${s.label}</div></div>`
  ).join("");
  container.classList.remove("hidden");
}

async function resetProfile() {
  if (!confirm("Reset your profile and conversation?")) return;
  await postJSON("/api/profile/reset", {});
  location.reload();
}

// ── Chat ──────────────────────────────────────────────────────────────────────
function chatKeydown(e) {
  if (e.key === "Enter" && !e.shiftKey) {
    e.preventDefault();
    sendChat();
  }
}

async function sendChat() {
  const input = document.getElementById("chatInput");
  const msg   = input.value.trim();
  if (!msg) return;

  appendMessage("user", msg);
  input.value = "";

  const typing = appendMessage("assistant", "…", true);
  try {
    const res  = await postJSON("/api/chat", { message: msg });
    const data = await res.json();
    typing.remove();
    if (data.status === "ok") {
      appendMessage("assistant", data.html, false, true);
    } else {
      appendMessage("assistant", "Sorry, something went wrong. Please try again.");
    }
  } catch {
    typing.remove();
    appendMessage("assistant", "Network error. Please check your connection.");
  }
}

function appendMessage(role, content, isTyping = false, isHtml = false) {
  const container = document.getElementById("chatMessages");
  const div       = document.createElement("div");
  div.className   = `chat-message ${role}`;

  const avatar = document.createElement("div");
  avatar.className = "avatar";
  avatar.textContent = role === "user" ? "You" : "🤖";

  const bubble = document.createElement("div");
  bubble.className = "bubble";
  if (isTyping) {
    bubble.innerHTML = '<span style="opacity:.5">NutriAI is thinking…</span>';
  } else if (isHtml) {
    bubble.innerHTML = content;
  } else {
    bubble.textContent = content;
  }

  div.appendChild(avatar);
  div.appendChild(bubble);
  container.appendChild(div);
  container.scrollTop = container.scrollHeight;
  return div;
}

async function clearChat() {
  await postJSON("/api/chat/clear", {});
  const container = document.getElementById("chatMessages");
  container.innerHTML = "";
  appendMessage("assistant", "Conversation cleared. How can I help you today? 🥗", false, false);
}

// ── Meal Plan ─────────────────────────────────────────────────────────────────
async function generateMealPlan() {
  const days = document.getElementById("mpDays").value;
  showLoading(`Generating ${days}-day meal plan with IBM Granite…`);
  try {
    const res  = await postJSON("/api/meal-plan", { days: parseInt(days) });
    const data = await res.json();
    hideLoading();
    if (data.status === "ok") {
      mealPlanText = data.meal_plan;
      showResult("mealPlanResult", data.html);
      document.getElementById("mealPlanFeedback").classList.remove("hidden");
      buildStars("mpStars", 0, (r) => {
        mpRating = r;
        submitPlanFeedback(r);
      });
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
  showToast("Feedback recorded – thanks! ✓", "success");
}

// ── Food Swaps ────────────────────────────────────────────────────────────────
async function getSwaps() {
  const foods  = getVal("swapFoods").trim();
  const reason = getVal("swapReason").trim();
  if (!foods) { showToast("Please enter at least one food item", "error"); return; }

  showLoading("Finding smart food swaps…");
  try {
    const res  = await postJSON("/api/food-swap", { foods: foods.split(",").map(f => f.trim()), reason });
    const data = await res.json();
    hideLoading();
    if (data.status === "ok") {
      showResult("swapResult", data.html);
    } else {
      showToast(data.message || "Error getting swaps", "error");
    }
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

// ── Nutritional Explanation ───────────────────────────────────────────────────
async function explainFoodItem() {
  const food = getVal("explainFood").trim();
  if (!food) { showToast("Please enter a food name", "error"); return; }

  showLoading(`Analysing nutrition for "${food}"…`);
  try {
    const res  = await postJSON("/api/explain", { food });
    const data = await res.json();
    hideLoading();
    if (data.status === "ok") {
      showResult("explainResult", data.html);
    } else {
      showToast(data.message || "Error", "error");
    }
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
  document.getElementById("uploadZone").classList.remove("drag-over");
  const file = event.dataTransfer.files[0];
  if (file) loadImageFile(file);
}

function loadImageFile(file) {
  selectedImageFile = file;
  const reader = new FileReader();
  reader.onload = (e) => {
    const preview = document.getElementById("imagePreview");
    preview.src   = e.target.result;
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

  showLoading("Analysing food image with IBM Granite…");
  const formData = new FormData();
  formData.append("image", selectedImageFile);

  try {
    const res  = await fetch("/api/analyse-image", { method: "POST", body: formData });
    const data = await res.json();
    hideLoading();
    if (data.status === "ok") {
      showResult("imageResult", data.html);
    } else {
      showToast(data.message || "Analysis failed", "error");
    }
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
      const data = await res.json();
      if (data.suggestions && data.suggestions.length) {
        const container = document.getElementById("lookupSuggestions");
        container.innerHTML = data.suggestions.map(f =>
          `<span class="tag" onclick="quickLookup('${f.name}')">${f.name}</span>`
        ).join("");
      }
    } catch {}
  }, 300);
}

async function lookupFood() {
  const q = getVal("lookupQuery").trim();
  if (!q) { showToast("Enter a food name to look up", "error"); return; }
  await quickLookup(q);
}

async function quickLookup(food) {
  setVal("lookupQuery", food);
  showLoading("Looking up nutrition data…");
  try {
    const res  = await fetch(`/api/food-lookup?q=${encodeURIComponent(food)}`);
    const data = await res.json();
    hideLoading();
    if (data.food && !data.food.error) {
      const f = data.food;
      const html = `
        <h3>🥗 ${capitalize(f.name)}</h3>
        <table>
          <tr><th>Nutrient</th><th>Per 100g</th></tr>
          <tr><td>Calories</td><td><strong>${f.calories} kcal</strong></td></tr>
          <tr><td>Protein</td><td>${f.protein} g</td></tr>
          <tr><td>Carbohydrates</td><td>${f.carbs} g</td></tr>
          <tr><td>Total Fat</td><td>${f.fat} g</td></tr>
          <tr><td>Dietary Fiber</td><td>${f.fiber} g</td></tr>
        </table>
        <p class="muted">Source: ${f.source}</p>`;
      showResult("lookupResult", html);
    } else {
      showResult("lookupResult", `<p>No nutritional data found for "<strong>${food}</strong>". Try using the Chat Assistant for detailed information.</p>`);
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
    const data = await res.json();
    hideLoading();
    if (data.status === "ok") {
      showResult("suggestionsResult", data.html);
    } else {
      showToast("Error getting suggestions", "error");
    }
  } catch {
    hideLoading();
    showToast("Network error", "error");
  }
}

// ── Feedback ──────────────────────────────────────────────────────────────────
async function submitFeedback() {
  const item = getVal("fbItem").trim();
  if (!item) { showToast("Please enter a food or meal name", "error"); return; }
  if (!fbRating) { showToast("Please select a rating", "error"); return; }

  try {
    const res  = await postJSON("/api/feedback", {
      type:   getVal("fbType"),
      item:   item,
      rating: fbRating,
      note:   getVal("fbNote"),
    });
    const data = await res.json();
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

// ── Stars widget ──────────────────────────────────────────────────────────────
function buildStars(containerId, initialRating, onChange) {
  const container = document.getElementById(containerId);
  if (!container) return;
  container.innerHTML = "";
  let current = initialRating;

  for (let i = 1; i <= 5; i++) {
    const span = document.createElement("span");
    span.className = "star" + (i <= current ? " active" : "");
    span.textContent = "★";
    span.dataset.val = i;
    span.addEventListener("mouseover", () => highlightStars(container, i));
    span.addEventListener("mouseout",  () => highlightStars(container, current));
    span.addEventListener("click",     () => {
      current = i;
      highlightStars(container, current);
      if (onChange) onChange(current);
    });
    container.appendChild(span);
  }
}

function highlightStars(container, count) {
  container.querySelectorAll(".star").forEach((s, idx) => {
    s.classList.toggle("active", idx < count);
  });
}

// ── Helpers ───────────────────────────────────────────────────────────────────
function getVal(id)       { const el = document.getElementById(id); return el ? el.value : ""; }
function setVal(id, val)  { const el = document.getElementById(id); if (el) el.value = val; }
function splitList(str)   { return str ? str.split(",").map(s => s.trim()).filter(Boolean) : []; }
function capitalize(s)    { return s ? s.charAt(0).toUpperCase() + s.slice(1) : s; }

function showResult(id, html) {
  const el = document.getElementById(id);
  if (!el) return;
  el.innerHTML = html;
  el.classList.remove("hidden");
  el.scrollIntoView({ behavior: "smooth", block: "nearest" });
}

async function postJSON(url, body) {
  return fetch(url, {
    method:  "POST",
    headers: { "Content-Type": "application/json" },
    body:    JSON.stringify(body),
  });
}

function showLoading(text = "Processing with IBM Granite…") {
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
  _toastTimer = setTimeout(() => toast.classList.add("hidden"), 3000);
}
