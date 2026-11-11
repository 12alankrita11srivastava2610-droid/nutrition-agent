# 🥗 NutriAI – AI Nutrition Assistant
### Powered by IBM Granite (watsonx.ai)

> **Problem Statement #8** — The Smartest AI Nutrition Assistant  
> Built with IBM Cloud Lite services and IBM Granite LLM

---

## 📋 Overview

NutriAI is a full-stack, AI-powered nutrition assistant that delivers **personalised, adaptive, and culturally-aware** dietary guidance. Unlike generic diet apps, NutriAI uses **IBM Granite** (via watsonx.ai) to reason about your entire health profile and generate dynamic, context-aware recommendations.

### ✨ Key Features

| Feature | Description |
|---|---|
| 💬 **Chat Assistant** | Conversational nutrition Q&A powered by IBM Granite |
| 📅 **Meal Planner** | 1–14 day personalised meal plans with macros & shopping list |
| 🔄 **Smart Food Swaps** | Healthier alternatives tailored to your goals |
| 🔬 **Nutritional Explainer** | Deep nutritional science for any food or meal |
| 📷 **Image Analysis** | Upload food photos or grocery labels for AI analysis (OCR) |
| 🔍 **Food Lookup** | Instant calorie/macro data from built-in DB + USDA/Nutritionix |
| ✨ **Adaptive Suggestions** | ML-style learning from your feedback history |
| 👤 **Health Profile** | BMI, TDEE, goals, allergies, cuisines, medical conditions |

---

## 🏗️ Architecture

```
NutriAI/
├── app.py                  # Flask REST API (12 endpoints)
├── nutrition_agent.py      # Core AI agent (IBM Granite prompts)
├── granite_client.py       # IBM watsonx.ai SDK wrapper
├── user_profile.py         # Profile management + adaptive memory
├── food_database.py        # Built-in DB + USDA/Nutritionix APIs
├── image_handler.py        # OCR image processing (Pillow + Tesseract)
├── requirements.txt        # Python dependencies
├── env.example             # Configuration template
├── templates/
│   └── index.html          # Single-page app shell
└── static/
    ├── css/style.css        # IBM Design–inspired styles
    └── js/app.js            # Frontend logic (vanilla JS)
```

### Technology Stack

| Layer | Technology |
|---|---|
| **LLM** | IBM Granite 13B Instruct v2 (watsonx.ai) |
| **Backend** | Python 3.10+, Flask 3.0 |
| **Frontend** | Vanilla HTML5/CSS3/JavaScript (IBM Design System) |
| **OCR** | Pytesseract + Pillow |
| **Food Data** | Built-in database + USDA FoodData Central + Nutritionix |
| **Deployment** | Gunicorn (production), Flask dev server |

---

## 🚀 Quick Start

### 1. Clone / Download the project

```bash
cd "Nutrition Agent"
```

### 2. Create a virtual environment

```bash
python -m venv venv
# Windows
venv\Scripts\activate
# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure IBM Granite credentials

Copy `env.example` to `.env` and fill in your IBM Cloud credentials:

```bash
copy env.example .env   # Windows
cp env.example .env     # macOS/Linux
```

Edit `.env`:
```env
IBM_API_KEY=<your IBM Cloud API key>
IBM_WATSONX_URL=https://us-south.ml.cloud.ibm.com
IBM_PROJECT_ID=<your watsonx.ai project ID>
IBM_GRANITE_MODEL_ID=ibm/granite-13b-instruct-v2
```

**How to get credentials:**
1. Sign up at [IBM Cloud](https://cloud.ibm.com) (Lite/Free tier available)
2. Create a **watsonx.ai** service instance
3. Create a project and note the **Project ID**
4. Generate an **API key** from IBM Cloud IAM → Service credentials

### 5. (Optional) Install Tesseract for image OCR

- **Windows:** Download from [UB-Mannheim/tesseract](https://github.com/UB-Mannheim/tesseract/wiki)
- **macOS:** `brew install tesseract`
- **Linux:** `sudo apt install tesseract-ocr`

### 6. Run the application

```bash
python app.py
```

Open **http://localhost:5000** in your browser.

---

## 🔌 API Endpoints

| Method | Endpoint | Description |
|---|---|---|
| GET | `/api/health` | Service health + Granite status |
| GET | `/api/metadata` | Dropdown options for profile form |
| GET/POST | `/api/profile` | Get/update user health profile |
| POST | `/api/profile/reset` | Reset profile and conversation |
| POST | `/api/meal-plan` | Generate personalised meal plan |
| POST | `/api/food-swap` | Get smart food swap suggestions |
| POST | `/api/explain` | Nutritional explanation for food |
| POST | `/api/chat` | Conversational nutrition Q&A |
| POST | `/api/chat/clear` | Clear conversation history |
| POST | `/api/analyse-image` | Analyse food image/label (OCR) |
| GET | `/api/food-lookup` | Look up food nutrition data |
| GET | `/api/suggestions` | Adaptive personalised suggestions |
| POST | `/api/feedback` | Submit meal/plan feedback |

---

## 🤖 IBM Granite Integration

NutriAI uses **IBM Granite 13B Instruct v2** through the official `ibm-watsonx-ai` SDK.

### Prompt Engineering Strategy

Each feature uses a carefully crafted prompt template:

1. **System persona** – Establishes NutriAI as an expert nutritionist with the user's full profile context
2. **Task-specific instructions** – Precise requirements (calories, allergies, cuisines, goals)
3. **Output format requirements** – Structured markdown for clean rendering

Live Link:nutrition-agent-01.vercel.app


## 📊 Adaptive Learning

NutriAI improves over time through explicit feedback:

1. Users rate meals/plans (1–5 stars)
2. Feedback stored in session profile
3. `get_adaptive_suggestions()` incorporates liked/disliked items into prompts
4. IBM Granite generates suggestions that avoid dislikes and build on preferences

---

## 🏥 Health & Safety Disclaimer

NutriAI provides general nutritional information and AI-generated suggestions. It is **not a substitute for professional medical or dietary advice**. Users with medical conditions should consult a registered dietician or healthcare provider.

---

## 📄 License

MIT License – Free for educational and non-commercial use.

---

*Built for IBM Hackathon – Problem Statement #8: AI Nutrition Assistant*  
*IBM Granite | watsonx.ai | Flask | IBM Cloud Lite*
Live Link:nutrition-agent-01.vercel.app
