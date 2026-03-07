# CarbonVerse: Enterprise Carbon Offset Verification

## Project Overview

Welcome to **CarbonVerse**, a next-generation decentralized platform designed to validate carbon offset claims using advanced Artificial Intelligence. 

Our system allows land owners to capture images of their trees and crops. These images are rigorously analyzed by our AI engine to prevent fraud, ensure data integrity, and accurately calculate how much carbon the plants absorb. These carbon credits can then be securely minted and purchased by corporate buyers to offset their emissions.

---

## The Three User Roles

CarbonVerse is built upon a professional three-role ecosystem to manage the entire lifecycle of a carbon credit:

### 1. The Offset Generator (Seller)
**Who they are:** Farmers, landowners, or agro-forestry managers.
**What they do:** They use the CarbonVerse app on their mobile devices to capture geo-tagged photos of their biomass (trees/crops). They upload this evidence to our AI engine to automatically generate and verify Carbon Credits.

### 2. Corporate Compliance (Buyer)
**Who they are:** Businesses, industrialists, and corporations looking to reach "Net Zero" emissions.
**What they do:** They access the CarbonVerse Marketplace to securely purchase AI-verified carbon credits from the Sellers, track their pollution debt, and manage their environmental compliance.

### 3. Network Overseer (Admin)
**Who they are:** System administrators and protocol auditors.
**What they do:** They have a God's-eye view of the entire network. They monitor active seller nodes, track the total volume of carbon credits generated, and ensure the system is running smoothly without fraudulent activity.

---

## How the AI Magic Works (The Gatekeepers)

To ensure every carbon credit is 100% real and accurate, uploaded images must pass through our strict "Gatekeeper" checks before they become valid credits:

1. **Location Check (Geospatial & GEE):** We extract hidden GPS data from the photo to ensure the farmer is actually at the claimed location. We also cross-reference this with Google Earth Engine (GEE) satellite data to verify the NDVI (Vegetation Index) of that exact spot, making sure it corresponds to a natural environment.
2. **Deep Fake & Screen Prevention (Intel DPT Depth Estimation):** To stop fraudsters from simply taking a picture of a tree on a computer screen, we use **DPT-Hybrid-Midas**. This AI model generates a 3D depth map of the image. Real forests have high depth variance (trees in front, sky in back), while a photo of a flat screen has zero variance. Flat images are instantly rejected!
3. **Zero-Shot Object Classification (OpenAI CLIP):** To confirm the image actually contains valid biomass and even classify specific Indian species (e.g., Neem, Teak, Mango, or Sandalwood), we use **CLIP-ViT** (Contrastive Language-Image Pre-Training). Because it understands the complex relationship between text and images without needing massive retraining, it is incredibly accurate at rejecting unrelated objects (walls, cars) and focusing on true agriculture.
4. **Volume & Counting (Google OWL-ViT):** To scientifically calculate the carbon absorbed, we use **OWL-ViT** (Vision Transformer for Open-World Localization). This state-of-the-art model draws bounding boxes around individual trees and foliage clusters. By combining this counting mechanism with hard algorithmic green-pixel density analysis (HSV Color Space mapping), we estimate the precise Carbon Tonnage.
5. **Anti-Fraud Check (pHash Duplicate Detection):** We generate a unique structural "fingerprint" of the photo. If a user tries to upload the exact same picture of a tree twice to get double credits, the system blocks it on the blockchain ledger.

---

## Installation and Local Setup

Follow these simple steps to get CarbonVerse running on your local machine.

### Prerequisites
- **Python 3.9 or higher** installed on your computer.
- **Git** (optional, for cloning the code).

### Step-by-Step Guide

#### 1. Configure the Environment
The application needs some secret keys to work properly.
- Look for a file named `.env.example` in the main folder.
- Copy it and rename the copy to `.env`.
- *(Optional)* If you are using real satellite data, you will need to add your Google Earth Engine (GEE) JSON key file to this folder and update the `.env` file to point to it.

#### 2. Install Dependencies
Open your terminal (Command Prompt or PowerShell) and navigate strictly into the project folder (`CARBONCRED-main`). Then, run this command to download all the necessary code libraries:
```bash
pip install -r requirements.txt
```

#### 3. Setup the Database (Migrations)
Before running the app for the first time, you must set up the database structure. Run these two commands in order:

Make sure you have created the initial migration files:
```bash
python manage.py makemigrations
```

Then, apply them to create the database:
```bash
python manage.py migrate
```
*Note: If you ever see an error like `no such column`, running `python manage.py migrate` usually fixes it!*

#### 4. Start the Application Server
Now you are ready to launch CarbonVerse! Run:
```bash
python manage.py runserver
```
Open your web browser and go to: `http://127.0.0.1:8000/`

---

## Testing on your Phone (Ngrok)

If you want to test the camera and GPS features on your actual smartphone (as a Farmer would), you need to securely tunnel your local server to the internet so your phone can reach it.

1. **Install Ngrok:** Download and install ngrok from their website.
2. **Start the Tunnel:** While your Django server is running (from Step 4 above), open a *new* terminal window and run:
   ```bash
   ngrok http 8000
   ```
3. **Access on Phone:** Ngrok will give you a "Forwarding" link that looks something like `https://random-words.ngrok-free.dev`. Open this link on your phone's browser!

*(Make sure your phone gives the browser permission to use the Camera and Location services).*
