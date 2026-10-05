---
title: FoodBridge
emoji: 🍲
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
---

# FoodBridge – Smart Surplus Food Redistribution & Wastage Reduction Platform

Final-year B.Tech (CSE – AI) project, BBD University, Lucknow.

Donors (restaurants, hotels, households, events) list surplus food with a photo.
The platform checks the photo with AI, estimates spoilage risk and a pickup
deadline, and matches the food to the most suitable nearby verified NGO,
shelter or community kitchen.

## Modules
1. **Food listing & image preprocessing** – OpenCV: EXIF fix, resize, low-light denoise, gamma, CLAHE
2. **AI classification & freshness** – pretrained CLIP (zero-shot): food check, dish, category, spoilage, quantity
3. **Matching & route optimisation** – MongoDB geo search + Match Priority Score, deadline-aware pickup route
4. **Notifications** – live dashboard alerts and SMS *(in progress)*
5. **Dashboards** – donor, NGO and admin web interfaces with Leaflet maps

## Tech stack
Python 3.11 · FastAPI · MongoDB Atlas · PyTorch + Hugging Face Transformers · OpenCV · HTML/CSS/JS · Leaflet

## Run locally
```bash
conda activate foodbridge
pip install -r requirements.txt
cp .env.example .env          # then fill in DB_HOST etc.
python -m scripts.seed_db     # demo NGOs + accounts
uvicorn app.main:app --reload # http://127.0.0.1:8000
```

## Configuration (environment variables / Space secrets)
| Name | Purpose |
|---|---|
| `DB_HOST` | MongoDB Atlas connection string |
| `DB_NAME` | Database name (default `foodbridge`) |
| `JWT_SECRET` | Secret for signing login tokens |
| `ADMIN_EMAIL` / `ADMIN_PASSWORD` | Admin account created by the seed script |
