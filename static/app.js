// ============================================
// CONFIGURATION & STATE
// ============================================
const API_BASE_URL = window.location.origin; // Dynamic for ngrok/localhost
let CURRENT_ROLE = 'farmer';

// Default State: Includes "Target Emissions" for the Industrialist Story
const defaultData = {
    farmer: {
        gps: null,
        images: [],
        listings: [],
        verified_amount: "0.0 RCC",
        logs: [] // Stores the Audit Report
    },
    industrialist: {
        rcc_balance: 5.0,
        eth_balance: 0.45,
        target_emissions: 120.0 // The "Pollution Debt" to solve
    }
};

// Load from Memory or use Default
let sessionData = JSON.parse(localStorage.getItem('carbonSession')) || defaultData;

function saveState() {
    localStorage.setItem('carbonSession', JSON.stringify(sessionData));
}

// ============================================
// 1. UI NAVIGATION & ROUTING
// ============================================
function switchInterface(role) {
    CURRENT_ROLE = role;

    // Toggle Active Buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    document.getElementById(role === 'farmer' ? 'nav-farmer' : 'nav-indus').classList.add('active');

    // Toggle Views
    document.getElementById('view-farmer').classList.add('hidden');
    document.getElementById('view-industrialist').classList.add('hidden');
    document.getElementById(role === 'farmer' ? 'view-farmer' : 'view-industrialist').classList.remove('hidden');

    updateHeader(role);

    // Restore specific state based on role
    if (role === 'farmer' && sessionData.farmer.verified_amount !== "0.0 RCC") {
        restoreFarmerUI();
    }
    if (role === 'industrialist') {
        loadMarketplace(); // Also triggers Compliance UI update
    }
}

function updateHeader(role) {
    if (role === 'farmer') {
        document.getElementById('current-user-name').innerText = "Kavya Joshi";
        document.getElementById('current-user-role').innerText = "Verified Farmer";
        document.getElementById('wallet-address').innerText = "0x1E0e...6bAE";
        document.getElementById('page-heading').innerText = "Farm Verification Console";
    } else {
        document.getElementById('current-user-name').innerText = "Adani Green Energy";
        document.getElementById('current-user-role').innerText = "Industrial Buyer";
        document.getElementById('wallet-address').innerText = "0x5f63...705b";
        document.getElementById('page-heading').innerText = "Carbon Offset Marketplace";
    }
}

// ============================================
// 2. FARMER LOGIC: RESTORE UI (AUDIT REPORT)
// ============================================
function restoreFarmerUI() {
    // 1. Lock Mint Button
    const btn = document.getElementById('btn-mint');
    btn.innerHTML = '<i class="fas fa-check-circle"></i> VERIFIED ON-CHAIN';
    btn.style.background = "#059669";
    btn.disabled = true;

    // 2. Show Results
    const projEl = document.getElementById('projected-rcc');
    projEl.innerText = sessionData.farmer.verified_amount;
    projEl.style.color = "#10b981";

    document.getElementById('ai-confidence').innerText = "100%";

    // 3. Lock GPS UI
    if (sessionData.farmer.gps) {
        document.getElementById('gps-result').classList.remove('hidden');
        document.querySelector('.gps-box button').classList.add('hidden');
        document.getElementById('val-lat').innerText = sessionData.farmer.gps.lat;
        document.getElementById('val-lon').innerText = sessionData.farmer.gps.lon;
        // 4. RENDER AUDIT LOG (Detailed Result Section)
        const logBox = document.getElementById('batch-results');
        const logContainer = document.getElementById('detailed-results-container');

        if (sessionData.farmer.logs && sessionData.farmer.logs.length > 0) {
            logBox.classList.remove('hidden');
            logContainer.innerHTML = '';

            sessionData.farmer.logs.forEach(item => {
                const card = document.createElement('div');
                // Check status string (ACCEPTED vs REJECTED)
                const isSuccess = item.status === "ACCEPTED";

                card.className = isSuccess ? 'result-card success' : 'result-card error';
                // Detailed Check List (Green/Red Badges for each stage)
                let checkHTML = '';
                if (item.checks) {
                    checkHTML = `
                        <div class="result-details">
                            ${renderCheck('Location', item.checks.location)}
                            ${renderCheck('Biomass', item.checks.biomass)}
                            ${renderCheck('Duplicate', item.checks.duplicate)}
                            ${renderCheck('Environment', item.checks.environment)}
                        </div>
                    `;
                }

                card.innerHTML = `
                <div class="result-header">
                    <strong><i class="fas ${isSuccess ? 'fa-check-circle' : 'fa-times-circle'}"></i> ${item.file}</strong>
                    <span class="status-tag ${isSuccess ? 'valid' : 'invalid'}">${item.status}</span>
                </div>
                <div class="result-body">
                    ${isSuccess
                        ? `<p class="result-value">+${item.co2} Tons CO2</p>`
                        : `<p class="result-reason">Reason: ${item.reason}</p>`
                    }
                    ${checkHTML}
                </div>
            `;
                logContainer.appendChild(card);
            });

            document.getElementById('batch-badge').innerText = `${sessionData.farmer.logs.length} Processed`;
        }
        // 5. ADD "START NEW BATCH" BUTTON
        // Only add if it doesn't exist yet
        if (!document.getElementById('btn-reset')) {
            const resetBtn = document.createElement('button');
            resetBtn.id = 'btn-reset';
            resetBtn.innerHTML = '<i class="fas fa-redo"></i> START NEW BATCH';
            resetBtn.onclick = () => {
                if (confirm("Start new batch? This will clear current results.")) clearData();
            };
            document.querySelector('.action-card').appendChild(resetBtn);
        }
    }
}

// Helper for Detail Cards
function renderCheck(label, check) {
    if (!check) return '';
    const icon = check.status ? 'fa-check' : 'fa-times';
    const color = check.status ? 'text-green-500' : 'text-red-500';
    return `
        <div class="check-item ${check.status ? 'pass' : 'fail'}">
            <i class="fas ${icon}"></i> 
            <span>${label}: <strong>${check.msg}</strong></span>
        </div>
    `;
}
// ============================================
// 3. FARMER LOGIC: INPUTS & ACTIONS
// ============================================
let CAMERA_STREAM = null;
let CAMERA_BLOB = null;
let UPLOAD_SOURCE = 'file'; // 'file' or 'camera'

function setUploadMode(mode) {
    UPLOAD_SOURCE = mode;

    // UI Toggles
    document.getElementById('btn-mode-file').className = mode === 'file' ? 'btn-secondary active' : 'btn-secondary';
    document.getElementById('btn-mode-camera').className = mode === 'camera' ? 'btn-secondary active' : 'btn-secondary';

    document.getElementById('section-file').classList.toggle('hidden', mode !== 'file');
    document.getElementById('section-camera').classList.toggle('hidden', mode !== 'camera');

    if (mode === 'file') {
        stopCamera();
    }
}

// --- FILE MODE ---
function previewImage(input) {
    if (input.files.length > 0) {
        const count = input.files.length;
        const reader = new FileReader();

        reader.onload = function (e) {
            document.getElementById('img-preview').src = e.target.result;
            document.getElementById('img-preview').classList.remove('hidden');

            // Badge Update
            const prompt = document.getElementById('upload-prompt');
            prompt.innerHTML = `<p>${count} Photos Selected</p>`;
            prompt.style.position = 'absolute';
            prompt.style.bottom = '10px';
            prompt.style.right = '10px';
            prompt.style.background = 'rgba(0,0,0,0.8)';
            prompt.style.padding = '5px 10px';
            prompt.style.borderRadius = '20px';

            sessionData.farmer.images = input.files;
            calculateConfidence();
        }
        reader.readAsDataURL(input.files[0]);
    }
}

// --- CAMERA MODE ---
async function startCamera() {
    try {
        CAMERA_STREAM = await navigator.mediaDevices.getUserMedia({ video: { facingMode: 'environment' } });
        const video = document.getElementById('cameraPreview');
        video.srcObject = CAMERA_STREAM;
        video.style.display = 'block';
        document.getElementById('camera-snapshot').classList.add('hidden');

        document.getElementById('btn-start-cam').classList.add('hidden');
        document.getElementById('btn-capture').classList.remove('hidden');
        document.getElementById('btn-retake').classList.add('hidden');
    } catch (err) {
        alert("Camera Error: " + err.message);
    }
}

function stopCamera() {
    if (CAMERA_STREAM) {
        CAMERA_STREAM.getTracks().forEach(t => t.stop());
        CAMERA_STREAM = null;
    }
}

function captureSnapshot() {
    const video = document.getElementById('cameraPreview');
    const canvas = document.getElementById('cameraCanvas');
    const snapshot = document.getElementById('camera-snapshot');

    canvas.width = video.videoWidth;
    canvas.height = video.videoHeight;
    canvas.getContext('2d').drawImage(video, 0, 0);

    canvas.toBlob(blob => {
        CAMERA_BLOB = blob;
        snapshot.src = URL.createObjectURL(blob);
        snapshot.classList.remove('hidden');
        video.style.display = 'none';

        stopCamera();

        // Update Session Data
        sessionData.farmer.images = [blob];
        calculateConfidence();

        // UI Controls
        document.getElementById('btn-capture').classList.add('hidden');
        document.getElementById('btn-retake').classList.remove('hidden');
    }, 'image/jpeg', 0.95);
}

function retakeSnapshot() {
    startCamera();
}

function captureGPS() {
    const btn = document.querySelector('.gps-box button');
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> Locking Satellites...';

    if (navigator.geolocation) {
        navigator.geolocation.getCurrentPosition((pos) => {
            const lat = pos.coords.latitude.toFixed(4);
            const lon = pos.coords.longitude.toFixed(4);

            sessionData.farmer.gps = { lat, lon };
            saveState();

            document.getElementById('val-lat').innerText = lat;
            document.getElementById('val-lon').innerText = lon;
            btn.classList.add('hidden');
            document.getElementById('gps-result').classList.remove('hidden');
            calculateConfidence();
        }, (err) => { alert("GPS Error: " + err.message); });
    } else { alert("GPS not supported"); }
}

function calculateConfidence() {
    // Enable button only if GPS + Images exist
    if (sessionData.farmer.gps && sessionData.farmer.images) {
        const count = sessionData.farmer.images.length;

        document.getElementById('ai-confidence').innerText = "Ready";
        document.getElementById('ai-confidence').style.color = "#10b981";
        document.getElementById('projected-rcc').innerText = `~${count * 5} (Est)`;

        const mintBtn = document.getElementById('btn-mint');
        if (!mintBtn.innerText.includes("VERIFIED")) {
            mintBtn.disabled = false;
            mintBtn.innerHTML = `<i class="fas fa-cube"></i> MINT BATCH (${count} FILES)`;
            mintBtn.classList.add('pulse-animation');
        }
    }
}

// ============================================
// 4. SUBMIT BATCH TO BLOCKCHAIN
// ============================================
async function submitToBlockchain() {
    const btn = document.getElementById('btn-mint');
    btn.disabled = true;
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> AUDITING BATCH...';
    showToast("Uploading to AI Engine...", "info");

    const formData = new FormData();
    // Append images based on source
    if (UPLOAD_SOURCE === 'camera' && CAMERA_BLOB) {
        formData.append('images', CAMERA_BLOB, 'camera_capture.jpg');
    } else {
        for (let i = 0; i < sessionData.farmer.images.length; i++) {
            formData.append('images', sessionData.farmer.images[i]);
        }
    }

    formData.append('latitude', sessionData.farmer.gps.lat);
    formData.append('longitude', sessionData.farmer.gps.lon);
    formData.append('source', UPLOAD_SOURCE);

    // Check Dev Mode Toggle
    const isHackathonMode = document.getElementById('hackathon-toggle') ? document.getElementById('hackathon-toggle').checked : false;
    formData.append('hackathon_mode', isHackathonMode);

    try {
        const response = await fetch(`${API_BASE_URL}/test-mint/`, { method: 'POST', body: formData });
        const data = await response.json();

        // Check if server returned a 400/500 code AND has a message
        if (!response.ok) {
            throw new Error(data.message || data.detail || "Server Error");
        }

        if (data.status === "Success") {
            showToast("Batch Audit Successful!", "success");

            // SAVE RESULTS TO SESSION
            sessionData.farmer.verified_amount = data.ai_data.co2_tons + " RCC";
            sessionData.farmer.logs = data.batch_log; // Save the log list

            // Add to User's Listing Inventory
            sessionData.farmer.listings.push({
                farmer: "Kavya Joshi",
                amount: data.ai_data.co2_tons + " RCC",
                hash: data.tx_hash,
                isSold: false
            });
            saveState();

            // Update UI
            restoreFarmerUI();

        } else {
            // Logic Error (e.g. 200 OK but status="Error" from backend)
            // If we have detailed logs, show them instead of just erroring out
            if (data.batch_log && data.batch_log.length > 0) {
                // ... logic to handle logs
                sessionData.farmer.logs = data.batch_log;
                saveState();
                restoreFarmerUI();

                // Specific toast message (temporary)
                showToast("Verification Finished. See Report below.", "warning");
            } else {
                throw new Error(data.message || "Batch Rejected");
            }

            // Always reset button if it was a soft reject with logs
            btn.disabled = false;
            btn.innerHTML = `<i class="fas fa-cube"></i> RE-TRY BATCH`;

            // Auto-scroll to results
            setTimeout(() => {
                const el = document.getElementById('batch-results');
                if (el) el.scrollIntoView({ behavior: 'smooth' });
            }, 500);
        }
    } catch (error) {
        console.error(error);
        showToast(error.message, "warning"); // The showToast function handles its own timeout
        btn.innerHTML = '❌ ERROR';
        setTimeout(() => {
            btn.disabled = false;
            btn.innerHTML = `<i class="fas fa-cube"></i> RE-TRY BATCH`;
        }, 3000);
    }
}

// ============================================
// 5. INDUSTRIALIST: MARKETPLACE & COMPLIANCE
// ============================================
function loadMarketplace() {
    // 1. Update Compliance Dashboard First
    updateComplianceUI();

    // 2. Render Grid
    const grid = document.getElementById('market-grid');
    grid.innerHTML = '';

    const mockListings = [
        { id: 1, name: "Rajesh Patel", loc: "Gujarat (Sec 4)", amount: "10.0 RCC", price: "0.05 ETH" },
        { id: 2, name: "Anita Desai", loc: "Maharashtra", amount: "5.5 RCC", price: "0.025 ETH" },
        { id: 3, name: "Green Corp", loc: "Karnataka", amount: "25.0 RCC", price: "0.12 ETH" }
    ];

    // Add My Listing (if unsold)
    if (sessionData.farmer.listings.length > 0) {
        const myListing = sessionData.farmer.listings[sessionData.farmer.listings.length - 1];
        if (!myListing.isSold) {
            mockListings.unshift({
                id: 999, name: "YOU (Kavya Joshi)", loc: "Ahmedabad (Verified)",
                amount: myListing.amount, price: "0.04 ETH", isMine: true
            });
        }
    }

    mockListings.forEach(item => {
        const card = document.createElement('div');
        card.className = 'listing-card';
        card.innerHTML = `
    < div style = "display:flex; justify-content:space-between; margin-bottom:10px;" >
                <strong>${item.name}</strong>
                <span style="color:var(--primary); font-size:12px"><i class="fas fa-check"></i> Verified</span>
            </div >
            <div style="color:#94a3b8; font-size:13px; margin-bottom:15px;">
                <i class="fas fa-map-marker-alt"></i> ${item.loc}
            </div>
            <div style="background:rgba(255,255,255,0.05); padding:10px; border-radius:8px; margin-bottom:15px;">
                <div style="display:flex; justify-content:space-between;">
                    <span>Volume:</span> <strong style="color:#10b981">${item.amount}</strong>
                </div>
                <div style="display:flex; justify-content:space-between; margin-top:5px;">
                    <span>Price:</span> <strong>${item.price}</strong>
                </div>
            </div>
            <button class="btn-primary" style="width:100%" 
                onclick="buyListing(this, ${item.id}, '${item.amount}')" 
                ${item.isMine ? 'disabled' : ''}>
                ${item.isMine ? 'OWNED BY YOU' : 'BUY CREDITS'}
            </button>
`;
        grid.appendChild(card);
    });
}

function buyListing(btn, id, amountStr) {
    btn.innerHTML = '<i class="fas fa-circle-notch fa-spin"></i> BUYING...';

    setTimeout(() => {
        btn.innerHTML = 'PURCHASED';
        btn.style.background = '#334155';
        showToast("Credits Purchased Successfully!", "success");

        // Update Balance
        const amountVal = parseFloat(amountStr.split(' ')[0]);
        sessionData.industrialist.rcc_balance += amountVal;

        // Mark as sold if it was ours
        if (id === 999) {
            sessionData.farmer.listings[sessionData.farmer.listings.length - 1].isSold = true;
        }

        saveState();
        updateComplianceUI(); // Refresh Progress Bar

    }, 1000);
}

function updateComplianceUI() {
    const totalGoal = sessionData.industrialist.target_emissions;
    const current = sessionData.industrialist.rcc_balance;

    // Calculate %
    let percent = (current / totalGoal) * 100;
    if (percent > 100) percent = 100;

    const debt = Math.max(0, totalGoal - current);

    // Update Labels
    document.getElementById('indus-balance').innerText = current.toFixed(2) + " RCC";
    document.getElementById('indus-debt').innerText = debt.toFixed(2) + " Tons";
    document.getElementById('progress-text').innerText = percent.toFixed(1) + "%";

    // Update Bar Width
    const bar = document.getElementById('progress-fill');
    bar.style.width = percent + "%";

    // Logic for Colors & Badges
    const badge = document.getElementById('compliance-badge');
    const card = document.querySelector('.compliance-card');

    badge.className = "status-badge"; // Reset
    card.classList.remove('safe');

    if (percent >= 100) {
        badge.classList.add('success');
        badge.innerHTML = '<i class="fas fa-check-circle"></i> NET ZERO ACHIEVED';
        bar.style.background = "var(--primary)";
        card.classList.add('safe');
    } else if (percent > 30) {
        badge.classList.add('warning');
        badge.innerHTML = '<i class="fas fa-exclamation-circle"></i> OFFSETTING...';
        bar.style.background = "var(--warning)";
    } else {
        badge.classList.add('danger');
        badge.innerHTML = '<i class="fas fa-radiation-alt"></i> NON-COMPLIANT';
        bar.style.background = "var(--danger)";
    }
}

// ============================================
// 6. UTILS
// ============================================
function clearData() {
    localStorage.removeItem('carbonSession');
    location.reload();
}

let toastTimeout = null;

function showToast(msg, type) {
    const toast = document.getElementById('toast');
    if (!toast) return;

    // Clear any existing timer to prevent hiding bugs if clicked rapidly
    if (toastTimeout) {
        clearTimeout(toastTimeout);
    }

    // Set structure: text on left, optional close button logic
    toast.innerHTML = `<span style="margin-right: 15px;">${msg}</span> 
                       <i class="fas fa-times" style="cursor:pointer; opacity:0.7;"></i>`;

    toast.className = "toast show";
    toast.style.background = type === 'warning' ? '#f59e0b' : (type === 'success' ? '#10b981' : '#3b82f6');

    // Allow user to click the toast to dismiss immediately
    toast.onclick = () => {
        toast.classList.remove('show');
        if (toastTimeout) clearTimeout(toastTimeout);
    };

    // Auto-hide after 4 seconds
    toastTimeout = setTimeout(() => {
        toast.classList.remove('show');
    }, 4000);
}

// Initialize
updateHeader('farmer');
if (sessionData.farmer.verified_amount !== "0.0 RCC") {
    restoreFarmerUI();
}