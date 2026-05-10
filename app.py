import os
import pickle
import warnings
warnings.filterwarnings('ignore')

import numpy as np
import pandas as pd
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS

from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import accuracy_score

app = Flask(__name__, static_folder='frontend', static_url_path='')
CORS(app)

import urllib.request
import json as _json

GROK_MODEL   = "grok-3-mini"
GROK_API_URL = "https://api.x.ai/v1/chat/completions"

def call_grok(system_prompt: str, messages: list, max_tokens: int = 1024) -> str:
    """Call the xAI Grok API (OpenAI-compatible) and return the assistant text."""
    api_key = os.environ.get("XAI_API_KEY", "")
    if not api_key:
        return "⚠️  XAI_API_KEY not set. Get your free key at https://console.x.ai and run: set XAI_API_KEY=xai-..."

    full_messages = [{"role": "system", "content": system_prompt}] + messages

    payload = _json.dumps({
        "model"      : GROK_MODEL,
        "max_tokens" : max_tokens,
        "messages"   : full_messages,
    }).encode("utf-8")

    req = urllib.request.Request(
        GROK_API_URL,
        data=payload,
        headers={
            "Content-Type" : "application/json",
            "Authorization": f"Bearer {api_key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            data = _json.loads(resp.read().decode("utf-8"))
            return data["choices"][0]["message"]["content"]
    except urllib.error.HTTPError as e:
        body = e.read().decode("utf-8")
        return f"Grok API error {e.code}: {body[:300]}"
    except Exception as e:
        return f"Grok API error: {str(e)}"

recipes  = None
rf_model = None
scaler   = None

BASE_DIR     = os.path.dirname(os.path.abspath(__file__))
RECIPE_CSV   = os.path.join(BASE_DIR, 'processed_recipes_clean.csv')
FALLBACK_CSV = os.path.join(BASE_DIR, 'processed_recipes_final.csv')
MODEL_PATH   = 'rf_model_v2.pkl'
SCALER_PATH  = 'scaler_v2.pkl'

GOAL_SCORE_MAP = {
    'Weight Loss'    : 'score_weight_loss',
    'Weight Gain'    : 'score_weight_gain',
    'Muscle Gain'    : 'score_muscle_gain',
    'Maintain'       : 'score_maintain',
    'Maintain Weight': 'score_maintain',
    'Healthy Balance': 'score_maintain',
}

DIET_COMPAT_MAP = {
    'Omnivore'   : 'compatible_omnivore',
    'Vegetarian' : 'compatible_vegetarian',
    'Vegan'      : 'compatible_vegan',
    'Pescatarian': 'compatible_pescatarian',
}

ACTIVITY_MAP = {
    'Sedentary'         : 1,
    'Lightly Active'    : 2,
    'Moderate'          : 3,
    'Moderately Active' : 3,
    'Very Active'       : 4,
    'Athlete'           : 5,
    'Extremely Active'  : 5,
}

ACTIVITY_MULTIPLIER = {
    'Sedentary'         : 1.20,
    'Lightly Active'    : 1.375,
    'Moderate'          : 1.55,
    'Moderately Active' : 1.55,
    'Very Active'       : 1.725,
    'Athlete'           : 1.90,
    'Extremely Active'  : 1.90,
}

TIER_MAP   = {'very_low': 0, 'low': 1, 'medium': 2, 'high': 3, 'very_high': 4}
CAL_SPLITS = {'Breakfast': 0.25, 'Lunch': 0.35, 'Dinner': 0.30, 'Snack': 0.10}

def get_exercise_plan(activity_level, health_conditions, goal, bmi):
    exercises, notes = [], []

    if 'Weight Loss' in goal or goal == 'Healthy Balance':
        exercises = ['Brisk Walking', 'Cycling', 'Swimming', 'Jump Rope']
        duration, intensity = '45–60 min/day', 'Moderate'
    elif 'Muscle Gain' in goal:
        exercises = ['Weight Training', 'Resistance Bands', 'Push-ups / Pull-ups', 'Compound Lifts']
        duration, intensity = '50–70 min/day', 'High'
    elif 'Maintain' in goal:
        exercises = ['Jogging', 'Yoga', 'Cycling', 'Bodyweight Circuit']
        duration, intensity = '30–45 min/day', 'Moderate'
    else:
        exercises = ['Walking', 'Light Yoga', 'Stretching']
        duration, intensity = '30 min/day', 'Low'

    if activity_level == 'Sedentary':
        exercises = ['Walking (start slow)', 'Gentle Yoga', 'Light Stretching']
        duration, intensity = '20–30 min/day', 'Low'
        notes.append('Build up gradually — start with 3 days/week.')

    if activity_level in ('Athlete', 'Extremely Active'):
        notes.append('You are already very active — focus on recovery & nutrition timing.')

    if 'Hypertension' in health_conditions:
        exercises += ['Walking', 'Light Swimming']
        intensity = 'Low–Moderate'
        notes.append('Avoid heavy lifting and high-intensity intervals with hypertension.')

    if 'Heart Disease' in health_conditions:
        exercises = ['Walking', 'Light Yoga', 'Gentle Cycling']
        duration, intensity = '20–30 min/day', 'Low'
        notes.append('Consult your cardiologist before starting any exercise programme.')

    if 'Kidney Disease' in health_conditions or 'Kidney Issues' in health_conditions:
        exercises = ['Walking', 'Stretching', 'Chair Exercises']
        duration, intensity = '20–30 min/day', 'Low'
        notes.append('Avoid dehydration — drink water before and after exercise.')

    if 'Diabetes' in health_conditions:
        notes.append('Check blood sugar before and after workouts. Carry a snack.')

    if bmi >= 30:
        exercises = [e for e in exercises if 'Running' not in e]
        if 'Walking' not in exercises:
            exercises.insert(0, 'Brisk Walking')
        notes.append('Low-impact cardio preferred to protect joints.')

    return {
        'exercises': list(dict.fromkeys(exercises))[:4],
        'duration' : duration,
        'intensity': intensity,
        'notes'    : notes,
    }

def calculate_bmi(weight_kg, height_cm):
    h = height_cm / 100
    bmi = weight_kg / (h * h)
    if bmi < 18.5:   cat = 'Underweight'
    elif bmi < 25:   cat = 'Normal'
    elif bmi < 30:   cat = 'Overweight'
    else:            cat = 'Obese'
    return round(bmi, 1), cat

def calculate_calories(age, gender, weight_kg, height_cm, activity_level, goal):
    if gender.lower() == 'male':
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age + 5
    else:
        bmr = 10 * weight_kg + 6.25 * height_cm - 5 * age - 161

    mult = ACTIVITY_MULTIPLIER.get(activity_level, 1.55)
    tdee = bmr * mult

    if 'Weight Loss' in goal:    tdee -= 500
    elif 'Weight Gain' in goal:  tdee += 500
    elif 'Muscle Gain' in goal:  tdee += 300

    return round(tdee)

def train_and_save_model():
    global rf_model, scaler
    print('🔧  Training Random Forest model…')
    users_df = pd.read_csv('processed_users.csv')

    rows = []
    for _, user in users_df.iterrows():
        goal      = user['goal']
        diet_pref = user['dietary_preference']
        score_col  = GOAL_SCORE_MAP.get(goal, 'score_maintain')
        compat_col = DIET_COMPAT_MAP.get(diet_pref, 'compatible_omnivore')

        compatible = recipes[recipes[compat_col] == 1].copy()
        if user['has_diabetes']:       compatible = compatible[compatible['suitable_diabetes'] == 1]
        if user['has_hypertension']:   compatible = compatible[compatible['suitable_hypertension'] == 1]
        if user['has_heart_disease']:  compatible = compatible[compatible['suitable_heart_disease'] == 1]
        if user['has_kidney_disease']: compatible = compatible[compatible['suitable_kidney_disease'] == 1]
        if len(compatible) < 10:
            compatible = recipes[recipes[compat_col] == 1].copy()

        pos = compatible.nlargest(8, score_col)
        neg = compatible.nsmallest(8, score_col)

        def build_row(u, recipe, label):
            return {
                'age'                    : u['age'],
                'gender'                 : 1 if u['gender'] == 'Male' else 0,
                'bmi'                    : u['bmi'],
                'activity_encoded'       : u['activity_encoded'],
                'daily_calorie_target'   : u['daily_calorie_target'],
                'has_diabetes'           : u['has_diabetes'],
                'has_hypertension'       : u['has_hypertension'],
                'has_heart_disease'      : u['has_heart_disease'],
                'has_kidney_disease'     : u['has_kidney_disease'],
                'has_acne'               : u['has_acne'],
                'calories'               : recipe['calories'],
                'protein_g'              : recipe['protein_g'],
                'carbohydrates_g'        : recipe['carbohydrates_g'],
                'fat_g'                  : recipe['fat_g'],
                'fiber_g'                : recipe['fiber_g'],
                'sugar_g'                : recipe['sugar_g'],
                'sodium_mg'              : recipe['sodium_mg'],
                'cholesterol_mg'         : recipe['cholesterol_mg'],
                'score_weight_loss'      : recipe['score_weight_loss'],
                'score_weight_gain'      : recipe['score_weight_gain'],
                'score_muscle_gain'      : recipe['score_muscle_gain'],
                'score_maintain'         : recipe['score_maintain'],
                'suitable_diabetes'      : recipe['suitable_diabetes'],
                'suitable_hypertension'  : recipe['suitable_hypertension'],
                'suitable_heart_disease' : recipe['suitable_heart_disease'],
                'suitable_kidney_disease': recipe['suitable_kidney_disease'],
                'calorie_tier'           : TIER_MAP.get(str(recipe['calorie_tier']), 2),
                'rating'                 : recipe['rating'],
                'recommended'            : label,
            }

        for _, r in pos.iterrows(): rows.append(build_row(user, r, 1))
        for _, r in neg.iterrows(): rows.append(build_row(user, r, 0))

    train_df = pd.DataFrame(rows)
    X = train_df.drop(columns=['recommended'])
    y = train_df['recommended']
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42, stratify=y
    )
    scaler = StandardScaler()
    scaler.fit(X_train)
    rf_model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
    rf_model.fit(X_train, y_train)
    acc = accuracy_score(y_test, rf_model.predict(X_test))
    print(f'✅  Model trained — Accuracy: {acc:.4f}')
    with open(MODEL_PATH,  'wb') as f: pickle.dump(rf_model, f)
    with open(SCALER_PATH, 'wb') as f: pickle.dump(scaler,   f)
    print('✅  Model + scaler saved to disk')

def startup():
    global recipes, rf_model, scaler

    if os.path.exists(RECIPE_CSV):
        csv_file = RECIPE_CSV
    elif os.path.exists(FALLBACK_CSV):
        csv_file = FALLBACK_CSV
    else:
        raise FileNotFoundError(
            f"\n❌  No recipe CSV found!\n"
            f"    Expected: {RECIPE_CSV} or {FALLBACK_CSV}\n"
            f"    Make sure you copied processed_recipes_clean.csv into:\n"
            f"    {os.path.abspath('.')}"
        )

    print(f'📂  Loading recipe dataset from {csv_file}…')
    recipes = pd.read_csv(csv_file)
    print(f'    {len(recipes):,} recipes loaded')
    print(f'    Columns: {list(recipes.columns[:6])} …')

    if 'recipe_name' not in recipes.columns:
        for candidate in ['name', 'Name', 'recipe name', 'Recipe Name', 'title', 'Title']:
            if candidate in recipes.columns:
                recipes.rename(columns={candidate: 'recipe_name'}, inplace=True)
                print(f'    ℹ️  Renamed column "{candidate}" → "recipe_name"')
                break
        else:
            raise KeyError(
                f"\n❌  Could not find a recipe name column.\n"
                f"    Available columns: {list(recipes.columns)}\n"
                f"    Please rename your recipe name column to 'recipe_name' in the CSV."
            )

    junk_keywords = ['isolate', 'gluten', 'gum', 'seed gum', 'locust bean',
                     'soy protein', 'wheat gluten', 'vital wheat', 'guar']
    mask = recipes['recipe_name'].str.lower().apply(
        lambda n: not any(k in n for k in junk_keywords)
    )
    recipes = recipes[mask].reset_index(drop=True)
    print(f'    {len(recipes):,} recipes after quality filter')

    if os.path.exists(MODEL_PATH) and os.path.exists(SCALER_PATH):
        print('📦  Loading pre-trained model from disk…')
        with open(MODEL_PATH,  'rb') as f: rf_model = pickle.load(f)
        with open(SCALER_PATH, 'rb') as f: scaler   = pickle.load(f)
        print('✅  Model ready')
    else:
        train_and_save_model()

def recommend_meals(age, gender, weight_kg, height_cm, activity_level,
                    dietary_preference, goal, health_conditions,
                    cuisine_preference='All', top_n=3):

    bmi, bmi_cat = calculate_bmi(weight_kg, height_cm)
    daily_cal    = calculate_calories(age, gender, weight_kg, height_cm, activity_level, goal)
    activity_enc = ACTIVITY_MAP.get(activity_level, 3)

    has_diabetes       = 1 if 'Diabetes'      in health_conditions else 0
    has_hypertension   = 1 if 'Hypertension'  in health_conditions else 0
    has_heart_disease  = 1 if 'Heart Disease' in health_conditions else 0
    has_kidney_disease = 1 if ('Kidney Disease' in health_conditions or
                                'Kidney Issues'  in health_conditions) else 0
    has_acne           = 1 if 'Acne'          in health_conditions else 0

    compat_col = DIET_COMPAT_MAP.get(dietary_preference, 'compatible_omnivore')
    filtered   = recipes[recipes[compat_col] == 1].copy()

    if cuisine_preference and cuisine_preference != 'All':
        tmp = filtered[filtered['cuisine'] == cuisine_preference]
        if len(tmp) >= 20:
            filtered = tmp

    if has_diabetes:       filtered = filtered[filtered['suitable_diabetes'] == 1]
    if has_hypertension:   filtered = filtered[filtered['suitable_hypertension'] == 1]
    if has_heart_disease:  filtered = filtered[filtered['suitable_heart_disease'] == 1]
    if has_kidney_disease: filtered = filtered[filtered['suitable_kidney_disease'] == 1]
    if has_acne:           filtered = filtered[filtered['suitable_acne'] == 1]

    if len(filtered) < 10:
        filtered = recipes[recipes[compat_col] == 1].copy()

    score_col = GOAL_SCORE_MAP.get(goal, 'score_maintain')

    meal_cal_targets = {m: round(daily_cal * s) for m, s in CAL_SPLITS.items()}

    CAL_TOLERANCES = [50, 100, 150]

    results, used_indices = {}, set()

    for meal in ['Breakfast', 'Lunch', 'Dinner', 'Snack']:
        target = meal_cal_targets[meal]

        meal_recipes = pd.DataFrame()

        for tol in CAL_TOLERANCES:
            cal_mask = filtered['calories'].between(target - tol, target + tol)
            candidate = filtered[cal_mask & (filtered['meal_type'] == meal)].copy()
            if len(candidate) >= top_n:
                meal_recipes = candidate
                break
            candidate = filtered[cal_mask].copy()
            if len(candidate) >= top_n:
                meal_recipes = candidate
                break

        if len(meal_recipes) < top_n:
            fallback = filtered.copy()
            fallback['_cal_dist'] = (fallback['calories'] - target).abs()
            meal_recipes = fallback.nsmallest(max(top_n * 3, 10), '_cal_dist').drop(columns=['_cal_dist'])

        meal_recipes = meal_recipes[~meal_recipes.index.isin(used_indices)].copy()
        if len(meal_recipes) < top_n:
            meal_recipes_fallback = filtered.copy()
            meal_recipes_fallback['_cal_dist'] = (meal_recipes_fallback['calories'] - target).abs()
            meal_recipes = meal_recipes_fallback.nsmallest(max(top_n * 3, 10), '_cal_dist').drop(columns=['_cal_dist'])

        feature_rows = []
        for _, recipe in meal_recipes.iterrows():
            feature_rows.append({
                'age'                    : age,
                'gender'                 : 1 if gender == 'Male' else 0,
                'bmi'                    : bmi,
                'activity_encoded'       : activity_enc,
                'daily_calorie_target'   : daily_cal,
                'has_diabetes'           : has_diabetes,
                'has_hypertension'       : has_hypertension,
                'has_heart_disease'      : has_heart_disease,
                'has_kidney_disease'     : has_kidney_disease,
                'has_acne'               : has_acne,
                'calories'               : recipe['calories'],
                'protein_g'              : recipe['protein_g'],
                'carbohydrates_g'        : recipe['carbohydrates_g'],
                'fat_g'                  : recipe['fat_g'],
                'fiber_g'                : recipe['fiber_g'],
                'sugar_g'                : recipe['sugar_g'],
                'sodium_mg'              : recipe['sodium_mg'],
                'cholesterol_mg'         : recipe['cholesterol_mg'],
                'score_weight_loss'      : recipe['score_weight_loss'],
                'score_weight_gain'      : recipe['score_weight_gain'],
                'score_muscle_gain'      : recipe['score_muscle_gain'],
                'score_maintain'         : recipe['score_maintain'],
                'suitable_diabetes'      : recipe['suitable_diabetes'],
                'suitable_hypertension'  : recipe['suitable_hypertension'],
                'suitable_heart_disease' : recipe['suitable_heart_disease'],
                'suitable_kidney_disease': recipe['suitable_kidney_disease'],
                'calorie_tier'           : TIER_MAP.get(str(recipe['calorie_tier']), 2),
                'rating'                 : recipe['rating'],
            })

        feat_df = pd.DataFrame(feature_rows)
        proba   = rf_model.predict_proba(feat_df)[:, 1]

        meal_recipes = meal_recipes.copy()
        meal_recipes['rec_score']   = proba
        meal_recipes['goal_score']  = meal_recipes[score_col]
        meal_recipes['cal_proximity'] = 1 - (meal_recipes['calories'] - target).abs() / max(target, 1)
        meal_recipes['final_score'] = (
            meal_recipes['rec_score']    * 0.5 +
            meal_recipes['goal_score']   * 0.3 +
            meal_recipes['cal_proximity'] * 0.2
        )

        top = meal_recipes.nlargest(top_n, 'final_score')
        used_indices.update(top.index.tolist())

        results[meal] = [
            {
                'name'       : row['recipe_name'],
                'cuisine'    : row['cuisine'],
                'category'   : row['category'],
                'calories'   : int(row['calories']),
                'protein_g'  : round(float(row['protein_g']), 1),
                'carbs_g'    : round(float(row['carbohydrates_g']), 1),
                'fat_g'      : round(float(row['fat_g']), 1),
                'fiber_g'    : round(float(row['fiber_g']), 1),
                'spice_level': row['spice_level'],
                'rating'     : round(float(row['rating']), 1),
            }
            for _, row in top.iterrows()
        ]

    exercise = get_exercise_plan(activity_level, health_conditions, goal, bmi)

    return {
        'bmi'              : bmi,
        'bmi_category'     : bmi_cat,
        'daily_calories'   : daily_cal,
        'cal_breakdown'    : {m: round(daily_cal * s) for m, s in CAL_SPLITS.items()},
        'meals'            : results,
        'exercise'         : exercise,
        'health_conditions': health_conditions,
        'goal'             : goal,
    }

def build_system_prompt(user_context: dict = None) -> str:
    context_block = ""
    if user_context:
        context_block = f"""
The user's current profile:
- Age: {user_context.get('age', 'unknown')}
- Gender: {user_context.get('gender', 'unknown')}
- BMI: {user_context.get('bmi', 'unknown')} ({user_context.get('bmi_category', '')})
- Goal: {user_context.get('goal', 'unknown')}
- Activity: {user_context.get('activity_level', 'unknown')}
- Diet: {user_context.get('dietary_preference', 'unknown')}
- Health conditions: {', '.join(user_context.get('health_conditions', [])) or 'None'}
- Daily calorie target: {user_context.get('daily_calories', 'unknown')} kcal
- Cuisine preference: {user_context.get('cuisine_preference', 'All')}
"""

    return f"""You are NutriAI, a knowledgeable and friendly AI diet and nutrition assistant.
You help users understand their meal plans, answer questions about nutrition,
and provide personalised dietary advice.
{context_block}
Guidelines:
- Be warm, encouraging, and practical
- Give concrete, actionable advice
- Reference the user's profile when relevant
- For medical conditions, always recommend consulting a healthcare professional
- Keep answers concise (2-4 paragraphs max) unless the user asks for detail
- You can suggest alternative foods, explain nutritional concepts,
  interpret BMI/calorie data, and answer general diet questions
- Do not diagnose or prescribe — you are an assistant, not a doctor
- If asked about something outside nutrition/diet/fitness, politely redirect
"""

@app.route('/')
def index():
    return send_from_directory('frontend', 'index.html')

@app.route('/recommend', methods=['POST'])
def recommend():
    try:
        data = request.get_json()
        age                = int(data['age'])
        gender             = data['gender']
        weight_kg          = float(data['weight_kg'])
        height_cm          = float(data['height_cm'])
        activity_level     = data['activity_level']
        dietary_preference = data.get('dietary_preference', 'Omnivore')
        goal               = data['goal']
        health_conditions  = data.get('health_conditions', ['None'])
        cuisine_preference = data.get('cuisine_preference', 'All')

        result = recommend_meals(
            age, gender, weight_kg, height_cm,
            activity_level, dietary_preference,
            goal, health_conditions, cuisine_preference,
            top_n=3
        )
        return jsonify({'status': 'ok', 'data': result})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/chat', methods=['POST'])
def chat():
    """
    Claude-powered conversational endpoint.

    Request body:
    {
        "messages": [
            {"role": "user", "content": "Why is fiber important for diabetics?"},
            ...
        ],
        "user_context": {          // optional — pass after /recommend completes
            "age": 30, "gender": "Female", "bmi": 24.5, "bmi_category": "Normal",
            "goal": "Weight Loss", "activity_level": "Moderate",
            "dietary_preference": "Vegetarian", "health_conditions": ["Diabetes"],
            "daily_calories": 1650, "cuisine_preference": "Pakistani"
        }
    }

    Response:
    {
        "status": "ok",
        "reply": "Fiber slows glucose absorption, which helps..."
    }
    """
    try:
        data         = request.get_json()
        messages     = data.get('messages', [])
        user_context = data.get('user_context', None)

        if not messages:
            return jsonify({'status': 'error', 'message': 'No messages provided'}), 400

        system = build_system_prompt(user_context)
        reply  = call_grok(system, messages, max_tokens=1024)

        return jsonify({'status': 'ok', 'reply': reply})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 400

@app.route('/health')
def health():
    api_key_set = bool(os.environ.get("XAI_API_KEY", ""))
    csv_used    = RECIPE_CSV if os.path.exists(RECIPE_CSV) else FALLBACK_CSV
    return jsonify({
        'status'          : 'ok',
        'model_loaded'    : rf_model is not None,
        'recipe_count'    : len(recipes) if recipes is not None else 0,
        'dataset'         : csv_used,
        'grok_api_ready'  : api_key_set,
    })
    
startup()

if __name__ == '__main__':
    api_key_set = bool(os.environ.get("XAI_API_KEY", ""))
    print(f'\n🚀  NutriAI v2 running at http://localhost:5000')
    print(f'🤖  Grok AI chat: {"✅ ready" if api_key_set else "⚠️  set XAI_API_KEY to enable /chat"}')
    print()
    app.run(debug=False, host='0.0.0.0', port=5000)
