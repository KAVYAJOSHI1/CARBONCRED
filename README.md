# CarbonCred Biomass Verification Protocol

## Project Overview

CarbonCred is a decentralized verification platform designed to validate carbon offset claims through a multi-layered AI analysis engine. The system allows farmers to capture and upload images of biomass (trees/crops), which are then rigorously analyzed to prevent fraud, ensure data integrity, and calculate accurate carbon credit allocations.

## AI Verification Architecture (The Gatekeepers)

The core of the system relies on a sequential "Gatekeeper" architecture. An image must pass all validation layers to be Minted as a carbon credit on the blockchain.

### 1. Location Integrity Gatekeeper
**Purpose:** Ensures the physical asset exists at the claimed coordinates.
**Mechanism:** The system extracts EXIF metadata from the uploaded image and calculates the geodesic distance between the image's internal GPS tag and the user's claimed location.
**Failure Condition:** If the distance exceeds the allowable threshold, or if GPS metadata is stripped/missing, the asset is rejected immediately.

### 2. Biomass Classification Gatekeeper (Deep Learning)
**Purpose:** Verifies that the image actually contains valid biomass (trees, dense vegetation) rather than irrelevant objects.
**Model:** TensorFlow MobileNetV2.
**Mechanism:** A pre-trained Convolutional Neural Network (CNN) analyzes the visual features of the image. It outputs a confidence score indicating the probability of the image being "Biomass".
**Failure Condition:** If the confidence score is below the set threshold (e.g., 40%), the image is rejected as "Not Biomass".

### 3. Duplicate Prevention Gatekeeper
**Purpose:** Prevents double-spending of carbon assets (uploading the same tree multiple times).
**Mechanism:** Perceptual Hashing (pHash). unlike standard file hashing (MD5), pHash generates a fingerprint based on the visual structure of the image. This allows the system to detect duplicates even if the file has been slightly resized or re-saved.
**Failure Condition:** If the generated fingerprint matches a hash already stored in the active ledger, the image is rejected as a "Duplicate".

### 4. Object Quantification (YOLOv8)
**Purpose:** Estimates the density and potential carbon value of the asset.
**Model:** YOLOv8 (You Only Look Once).
**Mechanism:** An object detection model scans the verified biomass to count individual organic structures (trees, plants). This count contributes to the final carbon tonnage estimation.

---

## Installation and Local Setup

### Prerequisites
1. Python 3.9 or higher
2. PIP (Python Package Manager)

### Steps

1. **Install Dependencies**
   Navigate to the project root directory and install the required Python packages:
   ```bash
   pip install -r requirements.txt
   ```

2. **Run Database Migrations**
   Initialize the database schema:
   ```bash
   python manage.py migrate
   ```

3. **Start Local Server**
   Launch the Django development server:
   ```bash
   python manage.py runserver
   ```
   The application will be accessible at `http://127.0.0.1:8000/`.

---

## Remote Access Configuration (ngrok)

To test the application on a mobile device (required for Camera/GPS features), you must expose your local server to the internet using ngrok.

### 1. Install ngrok
Download the ngrok executable for your operating system from the official website or install via package manager (e.g., Chocolatey on Windows):
```bash
choco install ngrok
```

### 2. Launch ngrok
Open a new terminal window. If ngrok is not in your system PATH, navigate (`cd`) to the directory where `ngrok.exe` is located.

Run the following command to tunnel port 8000:
```bash
ngrok http 8000
```

### 3. Accessing the Application
1. Copy the "Forwarding" URL provided by ngrok (e.g., `https://unwhitewashed-enzo-piezometrical.ngrok-free.dev/`).
2. Open this URL on your mobile device's browser.
3. The application will automatically detect the dynamic URL and configure the API endpoints accordingly.

**Note:** Ensure `DEBUG=True` is set in `core/settings.py` for development purposes, and that the ngrok domain is included in `CSRF_TRUSTED_ORIGINS` (already configured in the default setup).
