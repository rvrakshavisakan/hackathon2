// State management
const appState = {
  currentUser: null,
  uploadedFile: null,
  expectedEmission: 1.95,
  calculatedEmission: 2.18,
  breakdown: {
    scope1: 1.42,
    scope2: 0.51,
    transport: 0.25,
  },
  currentView: "auth",
};

// Initialize check on DOM load
window.addEventListener("DOMContentLoaded", () => {
  // Check mock auth in localStorage
  const savedUser = localStorage.getItem("carbonwise_user");
  if (savedUser) {
    try {
      appState.currentUser = JSON.parse(savedUser);
      updateAuthHeaderUI();
      navigateToView("home");
    } catch (e) {
      localStorage.removeItem("carbonwise_user");
      navigateToView("auth");
    }
  } else {
    navigateToView("auth");
  }
});

// View Navigation Router
function navigateToView(viewName) {
  appState.currentView = viewName;
  const views = ["auth", "home", "loading", "result"];
  views.forEach((v) => {
    const el = document.getElementById(`view-${v}`);
    if (el) {
      if (v === viewName) {
        el.classList.add("active");
      } else {
        el.classList.remove("active");
      }
    }
  });

  window.scrollTo({ top: 0, behavior: "smooth" });
}

// Toggle between Login and Signup tabs
function switchAuthTab(mode) {
  const loginForm = document.getElementById("loginForm");
  const signupForm = document.getElementById("signupForm");
  const tabBtnLogin = document.getElementById("tabBtnLogin");
  const tabBtnSignup = document.getElementById("tabBtnSignup");
  const title = document.getElementById("authFormTitle");
  const subtitle = document.getElementById("authFormSubtitle");
  const alertBox = document.getElementById("authAlert");

  alertBox.classList.add("hidden");

  if (mode === "signup") {
    loginForm.classList.add("hidden");
    signupForm.classList.remove("hidden");
    tabBtnSignup.classList.add("bg-white", "shadow-xs", "text-slate-800");
    tabBtnSignup.classList.remove("text-slate-500");
    tabBtnLogin.classList.remove("bg-white", "shadow-xs", "text-slate-800");
    tabBtnLogin.classList.add("text-slate-500");
    title.innerText = "Create your plant account";
    subtitle.innerText = "Register for CBAM steel footprint calculations";
  } else {
    signupForm.classList.add("hidden");
    loginForm.classList.remove("hidden");
    tabBtnLogin.classList.add("bg-white", "shadow-xs", "text-slate-800");
    tabBtnLogin.classList.remove("text-slate-500");
    tabBtnSignup.classList.remove("bg-white", "shadow-xs", "text-slate-800");
    tabBtnSignup.classList.add("text-slate-500");
    title.innerText = "Sign in to your account";
    subtitle.innerText = "Enter your credentials to access the calculator";
  }
}

// Handle Login
function handleLoginSubmit(e) {
  e.preventDefault();
  const username = document.getElementById("loginUsername").value.trim();
  if (!username) {
    showAuthAlert("Please enter a username or work email.");
    return;
  }

  const mockUser = {
    name: username.includes("@") ? username.split("@")[0] : username,
    company: "Jamshedpur Steelworks Ltd.",
    role: "Plant Compliance Lead",
  };

  loginUser(mockUser);
}

// Handle Signup
function handleSignupSubmit(e) {
  e.preventDefault();
  const name = document.getElementById("regFullName").value.trim();
  const company = document.getElementById("regCompany").value.trim();
  const role = document.getElementById("regRole").value;
  const pass = document.getElementById("regPass").value;
  const passConfirm = document.getElementById("regPassConfirm").value;

  if (pass !== passConfirm) {
    showAuthAlert("Passwords do not match. Please re-enter.");
    return;
  }

  const mockUser = {
    name: name || "Compliance Engineer",
    company: company || "Indian Steel Export Consortium",
    role: role,
  };

  loginUser(mockUser);
}

function showAuthAlert(msg) {
  const alertBox = document.getElementById("authAlert");
  const text = document.getElementById("authAlertText");
  text.innerText = msg;
  alertBox.classList.remove("hidden");
}

function loginUser(userData) {
  appState.currentUser = userData;
  localStorage.setItem("carbonwise_user", JSON.stringify(userData));
  updateAuthHeaderUI();
  navigateToView("home");
}

function handleLogout() {
  localStorage.removeItem("carbonwise_user");
  appState.currentUser = null;
  updateAuthHeaderUI();
  navigateToView("auth");
}

function updateAuthHeaderUI() {
  const profile = document.getElementById("authHeaderProfile");
  const guest = document.getElementById("guestHeaderInfo");
  const nameDisp = document.getElementById("userNameDisplay");
  const orgDisp = document.getElementById("userOrgDisplay");
  const avatar = document.getElementById("userAvatarLetter");

  if (appState.currentUser) {
    profile.classList.remove("hidden");
    guest.classList.add("hidden");
    nameDisp.innerText = appState.currentUser.name;
    orgDisp.innerText = appState.currentUser.company;
    avatar.innerText = (appState.currentUser.name[0] || "U").toUpperCase();
  } else {
    profile.classList.add("hidden");
    guest.classList.remove("hidden");
  }
}

// Preset Target Buttons
function setPresetTarget(val) {
  document.getElementById("expectedEmissionInput").value = val.toFixed(2);
}

// Drag & Drop / File Upload Handlers
function handleDragOver(e) {
  e.preventDefault();
  e.stopPropagation();
  document
    .getElementById("dropZone")
    .classList.add("border-emerald-500", "bg-emerald-50/40");
}

function handleDragLeave(e) {
  e.preventDefault();
  e.stopPropagation();
  document
    .getElementById("dropZone")
    .classList.remove("border-emerald-500", "bg-emerald-50/40");
}

function handleFileDrop(e) {
  e.preventDefault();
  e.stopPropagation();
  document
    .getElementById("dropZone")
    .classList.remove("border-emerald-500", "bg-emerald-50/40");

  const files = e.dataTransfer.files;
  if (files && files.length > 0) {
    setUploadedFile(
      files[0].name,
      (files[0].size / (1024 * 1024)).toFixed(1) + " MB",
    );
  }
}

function handleFileSelected(e) {
  const files = e.target.files;
  if (files && files.length > 0) {
    setUploadedFile(
      files[0].name,
      (files[0].size / (1024 * 1024)).toFixed(1) + " MB",
    );
  }
}

function loadSampleExcelMock() {
  setUploadedFile(
    "steel_transport_and_energy_data_2026.xlsx",
    "3.8 MB • 1,840 freight & fuel entries",
  );
}

function setUploadedFile(name, meta) {
  appState.uploadedFile = { name, meta };
  document.getElementById("dropZoneEmpty").classList.add("hidden");
  document.getElementById("dropZoneFilled").classList.remove("hidden");
  document.getElementById("fileNameDisplay").innerText = name;
  document.getElementById("fileMetaDisplay").innerText = meta;
}

function clearUploadedFile() {
  appState.uploadedFile = null;
  document.getElementById("fileInput").value = "";
  document.getElementById("dropZoneFilled").classList.add("hidden");
  document.getElementById("dropZoneEmpty").classList.remove("hidden");
}

// Handle Start of Evaluation Form
function handleEvaluationStart(e) {
  e.preventDefault();

  // Ensure a file is attached or sample loaded
  if (!appState.uploadedFile) {
    loadSampleExcelMock();
  }

  const expectedVal =
    parseFloat(document.getElementById("expectedEmissionInput").value) || 1.95;
  appState.expectedEmission = expectedVal;

  // Realistic calculation: determine calculated emission around expectedVal with some variance
  // E.g., if expected is 1.95, calculated = 2.18
  const calculatedVal = Number((expectedVal * 1.118).toFixed(2));
  appState.calculatedEmission = calculatedVal;

  appState.breakdown = {
    scope1: Number((calculatedVal * 0.65).toFixed(2)),
    scope2: Number((calculatedVal * 0.23).toFixed(2)),
    transport: Number((calculatedVal * 0.12).toFixed(2)),
  };

  // Navigate to Loading view
  navigateToView("loading");
  runProcessingSimulation();
}

// Simulated background evaluation pipeline (3.5 seconds)
function runProcessingSimulation() {
  const progressBar = document.getElementById("loadingProgressBar");
  const percentText = document.getElementById("loadingPercentText");
  const subtext = document.getElementById("loadingSubtext");

  let progress = 15;
  const interval = setInterval(() => {
    progress += Math.floor(Math.random() * 20) + 12;
    if (progress > 100) progress = 100;

    progressBar.style.width = `${progress}%`;
    percentText.innerText = `${progress}% complete`;

    if (progress < 40) {
      subtext.innerText =
        "Extracting freight rows: Distance km, Rail vs Truck transport modes...";
    } else if (progress < 75) {
      subtext.innerText =
        "Applying GLEC & DEFRA emission factors for Scope 3 freight logistics...";
    } else if (progress < 95) {
      subtext.innerText =
        "Querying RAG Vector Index for EU CBAM 2026 Annex IV Steel benchmarks...";
    }

    if (progress >= 100) {
      clearInterval(interval);
      setTimeout(() => {
        renderResultPage();
        navigateToView("result");
      }, 600);
    }
  }, 400);
}

// Render Result Page with calculated values, comparison, and RAG guidance
function renderResultPage() {
  const calc = appState.calculatedEmission;
  const exp = appState.expectedEmission;
  const delta = Number((calc - exp).toFixed(2));
  const pctDelta = Number(((delta / exp) * 100).toFixed(1));

  // Update values
  document.getElementById("resCalculatedValue").innerText = calc.toFixed(2);
  document.getElementById("resExpectedValue").innerText = exp.toFixed(2);
  document.getElementById("markerExpected").innerText = exp.toFixed(2);
  document.getElementById("markerCalculated").innerText = calc.toFixed(2);
  document.getElementById("ragCalcInline").innerText =
    `${calc.toFixed(2)} tCO₂e/t`;

  // Breakdown
  document.getElementById("breakdownScope1").innerText =
    `${appState.breakdown.scope1} t`;
  document.getElementById("breakdownScope2").innerText =
    `${appState.breakdown.scope2} t`;
  document.getElementById("breakdownTransport").innerText =
    `${appState.breakdown.transport} t`;

  // Variance styling and text
  const varianceBadge = document.getElementById("varianceBadge");
  const summaryText = document.getElementById("comparisonSummaryText");
  const varianceDetail = document.getElementById("varianceExplanation");
  const ragBody = document.getElementById("ragMessageBody");

  if (calc > exp) {
    varianceBadge.className =
      "text-xs font-bold px-2.5 py-1 rounded-full bg-amber-50 text-amber-700 border border-amber-200";
    varianceBadge.innerText = `+${pctDelta}% Above Expected`;
    summaryText.className = "font-bold text-amber-700";
    summaryText.innerText = `Calculated value exceeds target by +${delta} tCO₂e/t`;

    varianceDetail.innerText = `The uploaded transport workbook includes 3 long-haul diesel freight legs (Jamshedpur to Haldia port, 320km) that carry heavy carbon penalties. Shifting these batches to electrified rail will save approx 0.16 tCO₂e/t and return emissions below your ${exp.toFixed(2)} target.`;

    ragBody.innerHTML = `Under the European Union Carbon Border Adjustment Mechanism (CBAM) definitive period guidelines for Iron and Steel (CN codes 7208 to 7217), your calculated embedded emissions of <strong>${calc.toFixed(2)} tCO₂e per tonne of finished steel</strong> exceed both your expected target (<strong>${exp.toFixed(2)} tCO₂e/t</strong>) and the EU default transitional benchmark (<strong>1.85 tCO₂e/t</strong>). Immediate mitigation in freight mode choice is recommended prior to quarterly verification.`;
  } else {
    varianceBadge.className =
      "text-xs font-bold px-2.5 py-1 rounded-full bg-emerald-50 text-emerald-700 border border-emerald-200";
    varianceBadge.innerText = `${pctDelta}% Within Target Budget`;
    summaryText.className = "font-bold text-emerald-700";
    summaryText.innerText = `Calculated value is strictly compliant (-${Math.abs(delta)} tCO₂e/t)`;

    varianceDetail.innerText = `Your logistics and direct fuel ratios meet internal targets. Verified electrified rail shipping from plant to port contributed to a competitive footprint of ${calc.toFixed(2)} tCO₂e/t.`;

    ragBody.innerHTML = `Good compliance standing: Your calculated embedded emissions of <strong>${calc.toFixed(2)} tCO₂e per tonne</strong> satisfy your benchmark of <strong>${exp.toFixed(2)} tCO₂e/t</strong> under EU Regulation 2023/956. Maintain batch invoices and grid certificates for auditor sign-off.`;
  }
}
