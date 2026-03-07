// ============================================
// CONFIGURATION & STATE
// ============================================
const API_BASE_URL = window.location.origin; // Dynamic for ngrok/localhost

// Multi-Role Mock Data Structure
const defaultSessionData = {
    admin: {
        name: "SysAdmin Node",
        role: "Network Overseer",
        address: "0x0000...0000"
    },
    seller: {
        name: "AgriCorp Ltd.",
        role: "Verified Offset Generator",
        gps: null,
        images: [],
        listings: [],
        verified_amount: "0.0 RCC",
        logs: [], // Stores the Audit Report
        area: 2.5,
        address: "0x1E0e...6bAE"
    },
    buyer: {
        name: "Global Tech Inc.",
        role: "Corporate Compliance",
        address: "0xC21B...8A9D",
        emissions: 120.0, // The "Pollution Debt" to solve
        credits: 0.0,
        compliant: false
    }
};

// Load from Memory or use Default
let sessionData = JSON.parse(localStorage.getItem('carbonVerseSession_v2')) || defaultSessionData;

function saveState() {
    localStorage.setItem('carbonVerseSession_v2', JSON.stringify(sessionData));
}

// ==========================================
// 1. INITIATION & NAVIGATION
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    switchInterface('admin');

    // Simulate Network Block Loading
    setInterval(() => {
        document.getElementById('block-num').innerText =
            '5,39' + Math.floor(Math.random() * 1000).toString().padStart(3, '0');
    }, 4000);
});

function switchInterface(role) {
    console.log(`Switching interface to: ${role}`);

    // 1. Update Navigation Buttons
    document.querySelectorAll('.nav-btn').forEach(btn => btn.classList.remove('active'));
    const activeBtn = document.getElementById(`nav-${role}`);
    if (activeBtn) activeBtn.classList.add('active');

    // 2. Hide all views
    document.getElementById('view-admin').classList.add('hidden');
    document.getElementById('view-seller').classList.add('hidden');
    document.getElementById('view-buyer').classList.add('hidden');

    // 3. Show requested view
    const viewElement = document.getElementById(`view-${role}`);
    if (viewElement) viewElement.classList.remove('hidden');

    // 4. Update Header and User Profile
    const userData = sessionData[role];
    if (userData) {
        document.getElementById('current-user-name').innerText = userData.name;
        document.getElementById('current-user-role').innerText = userData.role;
        document.getElementById('wallet-address').innerText = userData.address;
    }

    // 5. Update Page Heading
    const headerElement = document.getElementById('page-heading');
    if (role === 'admin') headerElement.innerText = 'Network Overview';
    if (role === 'seller') headerElement.innerText = 'Offset Generation Node';
    if (role === 'buyer') headerElement.innerText = 'Corporate Compliance Dashboard';

    // Restore specific state based on role
    if (role === 'seller' && sessionData.seller.verified_amount !== "0.0 RCC") {
        restoreSellerUI();
    }
    if (role === 'buyer') {
        loadMarketplace(); // Also triggers Compliance UI update
    }
}

// ============================================
// 2. FARMER LOGIC: RESTORE UI (AUDIT REPORT)
// ============================================
function restoreSellerUI() {
    // 1. Lock Mint Button
    const btn = document.getElementById('btn-mint');
    btn.innerHTML = '<i class="fas fa-check-circle"></i> VERIFIED ON-CHAIN';
    btn.style.background = "#059669";
    btn.disabled = true;

    // 2. Show Results
    const projEl = document.getElementById('projected-rcc');
    projEl.innerText = sessionData.seller.verified_amount;
    projEl.style.color = "#10b981";

    document.getElementById('ai-confidence').innerText = "100%";

    // 3. Lock GPS UI
    if (sessionData.seller.gps) {
        document.getElementById('gps-result').classList.remove('hidden');
        document.querySelector('.gps-box button').classList.add('hidden');
        document.getElementById('val-lat').innerText = sessionData.seller.gps.lat;
        document.getElementById('val-lon').innerText = sessionData.seller.gps.lon;
        // 4. RENDER AUDIT LOG (Detailed Result Section)
        const logBox = document.getElementById('batch-results');
        const logContainer = document.getElementById('detailed-results-container');

        if (sessionData.seller.logs && sessionData.seller.logs.length > 0) {
            logBox.classList.remove('hidden');
            logContainer.innerHTML = '';

            sessionData.seller.logs.forEach(item => {
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

            document.getElementById('batch-badge').innerText = `${sessionData.seller.logs.length} Processed`;
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

            sessionData.seller.images = input.files;
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
        sessionData.seller.images = [blob];
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

            sessionData.seller.gps = { lat, lon };
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
    if (sessionData.seller.gps && sessionData.seller.images) {
        const count = sessionData.seller.images.length;

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

// Helper function to convert data URL to File object
async function dataURLtoFile(dataurl, filename) {
    const res = await fetch(dataurl);
    const blob = await res.blob();
    return new File([blob], filename, { type: blob.type });
}

// ============================================
// 4. SUBMIT BATCH TO BLOCKCHAIN
// ============================================
async function submitToBlockchain() {
    const btn = document.getElementById('btn-mint');
    const isHackathonMode = document.getElementById('hackathon-toggle') ? document.getElementById('hackathon-toggle').checked : false;

    const checkGpsResult = document.getElementById('gps-result');
    if (checkGpsResult && checkGpsResult.classList.contains('hidden') && !isHackathonMode) {
        showToast("Error: Complete Geo-Tagging First", "error");
        return;
    }

    const fileInput = document.getElementById('file-upload');
    const images = (UPLOAD_SOURCE === 'camera') ?
        [await dataURLtoFile(document.getElementById('camera-snapshot').src, 'snapshot.jpg')] :
        fileInput.files;

    if (images.length === 0) {
        showToast("Please upload images or take a snapshot first.", "error");
        return;
    }

    btn.innerHTML = '<i class="fas fa-spinner fa-spin"></i> Processing...';
    btn.disabled = true;
    showToast("Uploading to AI Engine...", "info");

    const formData = new FormData();
    for (let i = 0; i < images.length; i++) {
        formData.append('images', images[i]);
    }

    formData.append('latitude', sessionData.seller.gps.lat);
    formData.append('longitude', sessionData.seller.gps.lon);
    formData.append('source', UPLOAD_SOURCE);

    // Check Dev Mode Toggle
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
            sessionData.seller.verified_amount = data.ai_data.co2_tons + " RCC";
            sessionData.seller.logs = data.batch_log; // Save the log list

            // Add to User's Listing Inventory
            sessionData.seller.listings.push({
                farmer: "Kavya Joshi",
                amount: data.ai_data.co2_tons + " RCC",
                hash: data.tx_hash,
                isSold: false
            });
            saveState();

            // Update UI
            restoreSellerUI();

        } else {
            // Logic Error (e.g. 200 OK but status="Error" from backend)
            // If we have detailed logs, show them instead of just erroring out
            if (data.batch_log && data.batch_log.length > 0) {
                // ... logic to handle logs
                sessionData.seller.logs = data.batch_log;
                saveState();
                restoreSellerUI();

                // Specific toast message (temporary)
                showToast("Verification Finished. See Report below.", "warning");
            } else {
                throw new Error(data.message || "Batch Rejected");
            }

            // Always reset button if it was a soft reject with logs
            btn.disabled = false;
            btn.innerHTML = `<i class="fas fa-cube"></i> RETRY BATCH`;

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
            btn.innerHTML = `<i class="fas fa-cube"></i> RETRY BATCH`;
        }, 3000);
    }
}

// ==========================================
// 4. CORPORATE MARKETPLACE ACTIONS
// ==========================================
const availableListings = [
    { id: 1, type: "Agro-Forestry", location: "Uttar Pradesh", volume: 15.5, price: 0.05, verified: true },
    { id: 2, type: "Bamboo Plantation", location: "Assam", volume: 50.0, price: 0.04, verified: true },
    { id: 3, type: "Mangrove Restoration", location: "West Bengal", volume: 100.0, price: 0.08, verified: true },
    { id: 4, type: "Biochar Application", location: "Punjab", volume: 25.0, price: 0.06, verified: true }
];

function loadMarketplace() {
    const grid = document.getElementById('market-grid');
    if (!grid) return;
    grid.innerHTML = '';

    availableListings.forEach(item => {
        grid.innerHTML += `
    <div class="listing-card">
                <div style="display: flex; justify-content: space-between; margin-bottom: 15px;">
                    <span class="badge" style="background: rgba(16,185,129,0.2); color: var(--primary);">
                        <i class="fas fa-check-circle"></i> AI Verified
                    </span>
                    <strong>${item.volume} RCC</strong>
                </div>
                <h4>${item.type}</h4>
                <p style="color: var(--text-muted); font-size: 13px; margin-bottom: 20px;">
                    <i class="fas fa-map-marker-alt"></i> ${item.location}
                </p>
                <div style="display: flex; justify-content: space-between; align-items: center;">
                    <strong><i class="fab fa-ethereum" style="color:var(--text-muted)"></i> ${item.price}</strong>
                    <button class="btn-primary" style="padding: 8px 16px; width: auto; font-size: 13px;" onclick="buyCredits(${item.id}, ${item.volume})">
                        Purchase
                    </button>
                </div>
            </div>
    `;
    });
    updateComplianceUI(); // Ensure compliance UI is updated when marketplace loads
}

function buyCredits(id, amount) {
    showToast(`Initiating Smart Contract purchase of ${amount} RCC...`);

    // Simulate Blockchain Tx
    setTimeout(() => {
        sessionData.buyer.credits += amount;
        saveState(); // Save state after updating credits

        document.getElementById('indus-balance').innerText = `${sessionData.buyer.credits.toFixed(1)} RCC`;

        let debt = sessionData.buyer.emissions - sessionData.buyer.credits;
        if (debt <= 0) {
            debt = 0;
            sessionData.buyer.compliant = true;

            const badge = document.getElementById('compliance-badge');
            badge.className = "status-badge success";
            badge.innerText = "FULLY COMPLIANT";

            document.querySelector('.compliance-card').classList.add('safe');
        }

        document.getElementById('indus-debt').innerText = `${debt.toFixed(1)} Tons`;

        const prog = Math.min((sessionData.buyer.credits / sessionData.buyer.emissions) * 100, 100);
        document.getElementById('progress-text').innerText = `${prog.toFixed(1)}% `;
        document.getElementById('progress-fill').style.width = `${prog}% `;

        showToast("Purchase Confirmed & Added to Registry");
    }, 2000);
}

function updateComplianceUI() {
    const totalGoal = sessionData.buyer.emissions;
    const current = sessionData.buyer.credits;

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

// Remove legacy initializers