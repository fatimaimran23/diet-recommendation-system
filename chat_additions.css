# NourishAI

A personalised meal planning web app powered by a Random Forest model and Grok AI. Users enter their profile — age, weight, height, activity level, dietary preference, health conditions, and goal — and get a tailored daily meal plan with calorie targets, macros, and exercise recommendations. An AI chat assistant lets users ask nutrition questions in context.

---

## Features

- **Personalised meal plans** — Breakfast, Lunch, Dinner, and Snack recommendations based on your profile
- **Dynamic calorie matching** — Recipes are filtered by proximity to your actual per-meal calorie targets (±50 kcal)
- **Random Forest model** — Trained on user-recipe pairs to score recipe suitability per person
- **Health condition support** — Filters recipes suitable for Diabetes, Hypertension, Heart Disease, Kidney Disease, and Acne
- **Dietary preferences** — Omnivore, Vegetarian, Vegan, Pescatarian
- **Cuisine preferences** — Pakistani, Indian, Afghan, Bangladeshi, Western, Fusion
- **Exercise recommendations** — Personalised based on goal, activity level, BMI, and health conditions
- **AI chat** — Grok-powered assistant that answers nutrition questions using your profile as context
- **BMI calculator** — Auto-calculated from height and weight with category

---

## Project Structure

```
NourishAI_v2/
├── app.py                        ← Flask backend
├── processed_recipes_clean.csv   ← Cleaned recipe dataset (301 recipes)
├── processed_users.csv           ← User training data for the RF model
├── rf_model_v2.pkl               ← Trained model (auto-generated on first run)
├── scaler_v2.pkl                 ← Scaler (auto-generated on first run)
└── frontend/
    ├── index.html
    ├── style.css
    └── app.js
```

---

## Setup

### 1. Install dependencies

```bash
pip install flask flask-cors scikit-learn pandas numpy
```

### 2. Set your Grok API key

The `/chat` endpoint requires an xAI API key. Get one at https://console.x.ai

**Windows:**
```cmd
set XAI_API_KEY=xai-...
```

**macOS/Linux:**
```bash
export XAI_API_KEY="xai-..."
```

The `/recommend` endpoint works without the API key. Only `/chat` requires it.

### 3. Run the server

```bash
cd NourishAI_v2
python app.py
```

First run will train the Random Forest model on the clean dataset (~30–60 seconds). Subsequent runs load the saved model instantly.

Then open: **http://localhost:5000**

---

## API Endpoints

### `POST /recommend`
Returns a personalised meal plan.

**Request body:**
```json
{
  "age": 25,
  "gender": "Female",
  "weight_kg": 60,
  "height_cm": 165,
  "activity_level": "Moderate",
  "dietary_preference": "Vegetarian",
  "goal": "Weight Loss",
  "health_conditions": ["Diabetes"],
  "cuisine_preference": "Pakistani"
}
```

**Response includes:** BMI, daily calorie target, meal breakdown, recipe suggestions per meal, exercise plan.

---

### `POST /chat`
Grok-powered nutrition chat.

**Request body:**
```json
{
  "messages": [
    { "role": "user", "content": "Why is fiber important?" }
  ],
  "user_context": {
    "age": 25,
    "gender": "Female",
    "bmi": 22.0,
    "bmi_category": "Normal",
    "goal": "Weight Loss",
    "activity_level": "Moderate",
    "dietary_preference": "Vegetarian",
    "health_conditions": ["Diabetes"],
    "daily_calories": 1600,
    "cuisine_preference": "Pakistani"
  }
}
```

Send the full `messages` array on every request — Grok has no memory between calls. `user_context` is optional but gives personalised responses.

---

### `GET /health`
Returns server status, recipe count, model status, and whether the Grok API key is set.

---

## Dataset

`processed_recipes_clean.csv` contains 301 recipes across Pakistani, Indian, Afghan, Bangladeshi, Western, and Fusion cuisines. Each recipe includes calories, macros (protein, carbs, fat, fiber, sugar), sodium, cholesterol, suitability flags for health conditions, dietary compatibility, and goal scores.

Calorie range: 41 – 845 kcal per meal.

---

## Troubleshooting

| Problem | Fix |
|---|---|
| `ModuleNotFoundError` | Run `pip install flask flask-cors scikit-learn pandas numpy` |
| Chat returns API key warning | Run `set XAI_API_KEY=xai-...` before starting the server |
| Port 5000 already in use | Change `port=5000` to `port=5001` at the bottom of `app.py` |
| Model not found | Delete `rf_model_v2.pkl` and `scaler_v2.pkl` to retrain |
| Wrong calorie suggestions | Make sure you're using the latest `app.py` with dynamic calorie matching |
