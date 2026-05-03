// helpers
function getUsers() { return JSON.parse(localStorage.getItem('nourish_users') || '{}'); }
function saveUsers(u) { localStorage.setItem('nourish_users', JSON.stringify(u)); }
function getSession() { return JSON.parse(localStorage.getItem('nourish_session') || 'null'); }
function saveSession(s) { localStorage.setItem('nourish_session', JSON.stringify(s)); }
function clearSession() { localStorage.removeItem('nourish_session'); }

// navigation
function goTo(pageId) {
    const open = ['login', 'register'];
    if (!open.includes(pageId) && !getSession()) { goTo('login'); return; }
    document.querySelectorAll('.page').forEach(p => p.classList.remove('active'));
    document.getElementById('page-' + pageId).classList.add('active');
    window.scrollTo({ top: 0, behavior: 'smooth' });
    if (pageId === 'home') updateNavUser();
}

function updateNavUser() {
    const s = getSession();
    const el = document.getElementById('navUserName');
    if (el && s) el.textContent = 'Hi, ' + s.name.split(' ')[0];
}

function setError(id, msg) {
    const el = document.getElementById('err-' + id);
    const inp = document.getElementById(id);
    if (el) el.textContent = msg;
    if (inp) inp.classList.toggle('error', !!msg);
}
function clearErrors(...ids) { ids.forEach(id => setError(id, '')); }
function isValidEmail(e) { return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(e); }

// password
function togglePass(inputId, btn) {
    const inp = document.getElementById(inputId);
    if (!inp) return;
    const show = inp.type === 'password';
    inp.type = show ? 'text' : 'password';
    btn.style.color = show ? 'var(--purple)' : '';
}

function handleRegister() {
    const name = document.getElementById('regName').value.trim();
    const email = document.getElementById('regEmail').value.trim();
    const pass = document.getElementById('regPass').value;
    const pass2 = document.getElementById('regPass2').value;

    clearErrors('regName', 'regEmail', 'regPass', 'regPass2');
    let ok = true;

    if (!name) { setError('regName', 'Please enter your full name.'); ok = false; }
    if (!email) { setError('regEmail', 'Please enter your email address.'); ok = false; }
    else if (!isValidEmail(email)) { setError('regEmail', 'Please enter a valid email address.'); ok = false; }
    if (!pass) { setError('regPass', 'Please enter a password.'); ok = false; }
    else if (pass.length < 6) { setError('regPass', 'Password must be at least 6 characters.'); ok = false; }
    if (!pass2) { setError('regPass2', 'Please confirm your password.'); ok = false; }
    else if (pass !== pass2) { setError('regPass2', 'Passwords do not match.'); ok = false; }

    if (!ok) return;

    const users = getUsers();
    if (users[email]) { setError('regEmail', 'An account with this email already exists.'); return; }

    users[email] = { name, email, password: pass };
    saveUsers(users);
    saveSession({ name, email });
    goTo('home');
}

function handleLogin() {
    const email = document.getElementById('loginEmail').value.trim();
    const pass = document.getElementById('loginPass').value;

    clearErrors('loginEmail', 'loginPass');
    let ok = true;

    if (!email) { setError('loginEmail', 'Please enter your email address.'); ok = false; }
    else if (!isValidEmail(email)) { setError('loginEmail', 'Please enter a valid email address.'); ok = false; }
    if (!pass) { setError('loginPass', 'Please enter your password.'); ok = false; }

    if (!ok) return;

    const users = getUsers();
    const user = users[email];

    if (!user) { setError('loginEmail', 'No account found with this email.'); return; }
    if (user.password !== pass) { setError('loginPass', 'Incorrect password.'); return; }

    saveSession({ name: user.name, email });
    goTo('home');
}

function handleLogout() {
    clearSession();
    goTo('login');
}

// this checks seession
(function init() {
    if (getSession()) goTo('home');
    else goTo('register');
})();

function updateProgress() {
    const ageVal = document.getElementById('f-age')?.value;
    const weightVal = document.getElementById('f-weight')?.value;
    const heightVal = document.getElementById('f-height')?.value;
    const gBtn = document.querySelector('#genderGroup .toggle-btn.selected');
    const aCard = document.querySelector('#activityGroup .activity-card-new.selected');
    const gCard = document.querySelector('#goalGroup .goal-card-new.selected');

    const basicDone = !!(ageVal && weightVal && heightVal && gBtn);
    const activityDone = !!aCard;
    const goalDone = !!gCard;

    let score = 0;
    if (basicDone) score++;
    if (activityDone) score++;
    score++; 
    score++; 
    if (goalDone) score++;

    const pct = Math.round((score / 5) * 100);
    const fill = document.getElementById('progressFill');
    const label = document.getElementById('progressLabel');
    if (fill) fill.style.width = pct + '%';
    if (label) label.textContent = pct + '% complete';

    const ring = document.getElementById('sidebarRingFill');
    const ringPct = document.getElementById('sidebarPct');
    if (ring) {
        const circumference = 201;
        ring.style.strokeDashoffset = circumference - (pct / 100) * circumference;
    }
    if (ringPct) ringPct.textContent = pct + '%';

    updateSidebarItem('rsb-basic',
        basicDone,
        ageVal && weightVal && heightVal && gBtn
            ? `Age ${ageVal} · ${weightVal}${document.querySelector('#weightUnit .unit-btn.active')?.textContent || 'kg'} · ${gBtn.textContent}`
            : 'Not filled'
    );
    updateSidebarItem('rsb-activity',
        activityDone,
        activityDone ? aCard.querySelector('.act-label').textContent : 'Not selected'
    );
    updateSidebarItem('rsb-goal',
        goalDone,
        goalDone ? gCard.querySelector('.goal-title').textContent : 'Not selected'
    );

    const diseases = [...document.querySelectorAll('#diseaseGroup .pill-new.active')].map(p => p.textContent.trim());
    document.getElementById('rsb-health-val').textContent = diseases.length ? diseases.join(', ') : 'None selected';

    const foods = [...document.querySelectorAll('#prefGroup .pill-new.active')].map(p => p.textContent.trim());
    document.getElementById('rsb-food-val').textContent = foods.length ? foods.join(', ') : 'Any cuisine';
}

function updateSidebarItem(id, done, text) {
    const valEl = document.getElementById(id + '-val');
    if (valEl) valEl.textContent = text;
    // Update icon state
    const item = document.getElementById(id);
    if (item) {
        const icon = item.querySelector('.rsb-item-icon');
        if (icon) {
            icon.className = 'rsb-item-icon ' + (done ? 'rsb-icon--filled' : 'rsb-icon--pending');
        }
    }
}

function selectToggle(groupId, btn) {
    document.querySelectorAll('#' + groupId + ' .toggle-btn').forEach(b => b.classList.remove('selected'));
    btn.classList.add('selected');
    updateProgress();
}
function selectUnit(groupId, btn) {
    document.querySelectorAll('#' + groupId + ' .unit-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
}
function selectActivity(card) {
    document.querySelectorAll('#activityGroup .activity-card-new').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    updateProgress();
}
function togglePill(pill) { pill.classList.toggle('active'); updateProgress(); }
function selectGoal(card) {
    document.querySelectorAll('#goalGroup .goal-card-new').forEach(c => c.classList.remove('selected'));
    card.classList.add('selected');
    updateProgress();
}

function getActivePills(groupId) {
    return [...document.querySelectorAll('#' + groupId + ' .pill-new.active')]
        .map(p => p.textContent.trim()).filter(t => t !== 'None');
}
function toKg(v, u) { return u === 'lbs' ? v * 0.453592 : parseFloat(v); }
function toCm(v, u) { return u === 'ft' ? v * 30.48 : parseFloat(v); }

const ACTIVITY_MAP = {
    'Sedentary': 'Sedentary', 'Lightly Active': 'Lightly Active',
    'Moderate': 'Moderate', 'Very Active': 'Very Active', 'Athlete': 'Athlete',
};
const CUISINE_MAP = {
    'Pakistani': 'Pakistani', 'Mediterranean': 'Mediterranean', 'Chinese': 'Chinese',
    'Italian': 'Italian', 'Indian': 'Indian', 'Vegetarian': null, 'Vegan': null,
};

let lastApiPayload = null;

//plan
async function generatePlan() {
    const age = document.getElementById('f-age').value;
    const weight = document.getElementById('f-weight').value;
    const height = document.getElementById('f-height').value;
    const gBtn = document.querySelector('#genderGroup .toggle-btn.selected');
    const aCard = document.querySelector('#activityGroup .activity-card-new.selected');
    const gCard = document.querySelector('#goalGroup .goal-card-new.selected');

    if (!age || !weight || !height || !gBtn || !aCard || !gCard) {
        const btn = document.getElementById('generateBtn');
        btn.textContent = 'Please fill in all required fields';
        btn.style.background = '#ef4444';
        setTimeout(() => {
            btn.textContent = 'Generate My Plan';
            btn.style.background = '';
        }, 2200);
        return;
    }

    const gender = gBtn.textContent.trim();
    const activityLabel = aCard.querySelector('.act-label').textContent.trim();
    const goal = gCard.querySelector('.goal-title').textContent.trim();
    const weightUnit = document.querySelector('#weightUnit .unit-btn.active').textContent.trim();
    const heightUnit = document.querySelector('#heightUnit .unit-btn.active').textContent.trim();

    const weight_kg = toKg(parseFloat(weight), weightUnit);
    const height_cm = toCm(parseFloat(height), heightUnit);

    const diseases = getActivePills('diseaseGroup');
    const healthConditions = diseases.length ? diseases : ['None'];

    const cuisinePills = getActivePills('prefGroup');
    let cuisinePreference = 'All';
    for (const pill of cuisinePills) {
        const mapped = CUISINE_MAP[pill];
        if (mapped) { cuisinePreference = mapped; break; }
    }

    let dietaryPreference = 'Omnivore';
    if (cuisinePills.includes('Vegan')) dietaryPreference = 'Vegan';
    else if (cuisinePills.includes('Vegetarian')) dietaryPreference = 'Vegetarian';

    const payload = {
        age: parseInt(age), gender, weight_kg, height_cm,
        activity_level: ACTIVITY_MAP[activityLabel] || activityLabel,
        dietary_preference: dietaryPreference, goal,
        health_conditions: healthConditions,
        cuisine_preference: cuisinePreference,
    };
    lastApiPayload = payload;

    document.getElementById('loadingOverlay').classList.add('show');

    try {
        const res = await fetch('/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload),
        });
        const json = await res.json();
        if (json.status !== 'ok') throw new Error(json.message || 'Server error');
        document.getElementById('loadingOverlay').classList.remove('show');
        buildMealPlanPage(json.data, { age, weight, weightUnit, height, heightUnit, gender, activity: activityLabel, goal });
        storePlanContext(json.data, { age, gender, activity: activityLabel });
        goTo('mealplan');
    } catch (err) {
        document.getElementById('loadingOverlay').classList.remove('show');
        alert('Could not get recommendations:\n' + err.message + '\n\nMake sure the Flask server is running.');
    }
}

function buildMealPlanPage(data, user) {
    
    document.getElementById('planSummaryBar').innerHTML = [
        ['Age', user.age],
        ['Weight', user.weight + ' ' + user.weightUnit],
        ['Gender', user.gender],
        ['Activity', user.activity],
        ['Goal', user.goal],
        ['BMI', data.bmi + ' — ' + data.bmi_category],
    ].map(([k, v]) => `<span class="summary-chip">${k}: <strong>${v}</strong></span>`).join('');

    document.getElementById('calTarget').textContent = data.daily_calories + ' kcal';
    setTimeout(() => {
        document.getElementById('calFill').style.width =
            Math.min(Math.round((data.daily_calories / 3500) * 100), 100) + '%';
    }, 300);

    const grid = document.getElementById('mealsGrid');
    grid.innerHTML = '';

    const conditions = (data.health_conditions || []).filter(c => c !== 'None');
    if (conditions.length) {
        const alert = document.createElement('div');
        alert.className = 'health-alert';
        alert.innerHTML = `<strong>Health-aware plan</strong> — filtered and adjusted for: ${conditions.join(', ')}`;
        grid.appendChild(alert);
    }

    const headerClass = { Breakfast: 'breakfast', Lunch: 'lunch', Dinner: 'dinner', Snack: 'snack' };

    ['Breakfast', 'Lunch', 'Dinner', 'Snack'].forEach(mealName => {
        const items = data.meals[mealName] || [];
        if (!items.length) return;

        const targetCal = data.cal_breakdown[mealName] || 0;
        const card = document.createElement('div');
        card.className = 'meal-card';

        const itemsHTML = items.map(item => `
      <div class="meal-item">
        <div>
          <div class="item-name">${item.name}</div>
          <div class="item-meta">${item.cuisine} · ${item.spice_level} spice · ⭐ ${item.rating}</div>
        </div>
        <div style="text-align:right;flex-shrink:0;margin-left:16px;">
          <div class="item-cal">${item.calories} kcal</div>
          <div class="item-macros">P ${item.protein_g}g · C ${item.carbs_g}g · F ${item.fat_g}g</div>
        </div>
      </div>`).join('');

        card.innerHTML = `
      <div class="meal-card-header meal-card-header--${headerClass[mealName] || 'breakfast'}">
        <span class="meal-slot-name">${mealName}</span>
        <span class="meal-slot-target">Target ~${targetCal} kcal</span>
      </div>
      <div class="meal-items">${itemsHTML}</div>`;
        grid.appendChild(card);
    });

    buildExerciseCard(data.exercise);
}

function buildExerciseCard(exercise) {
    const old = document.getElementById('exerciseCard');
    if (old) old.remove();
    if (!exercise) return;

    const grid = document.getElementById('mealsGrid');
    const card = document.createElement('div');
    card.id = 'exerciseCard';
    card.className = 'exercise-card';

    const pills = exercise.exercises.map(e =>
        `<span class="exercise-pill">${e}</span>`
    ).join('');

    const notes = exercise.notes.map(n =>
        `<div class="exercise-note">${n}</div>`
    ).join('');

    card.innerHTML = `
    <div class="exercise-card-title">Exercise Recommendations</div>
    <div class="exercise-card-sub">${exercise.duration} · ${exercise.intensity} intensity</div>
    <div class="exercise-pills">${pills}</div>
    ${notes}`;
    grid.appendChild(card);
}

async function regeneratePlan() {
    if (!lastApiPayload) { goTo('requirements'); return; }
    document.getElementById('loadingOverlay').classList.add('show');
    try {
        const res = await fetch('/recommend', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(lastApiPayload),
        });
        const json = await res.json();
        if (json.status !== 'ok') throw new Error(json.message);
        document.getElementById('loadingOverlay').classList.remove('show');
        const u = lastApiPayload;
        buildMealPlanPage(json.data, {
            age: u.age, weight: Math.round(u.weight_kg), weightUnit: 'kg',
            height: Math.round(u.height_cm), heightUnit: 'cm',
            gender: u.gender, activity: u.activity_level, goal: u.goal,
        });
    } catch (err) {
        document.getElementById('loadingOverlay').classList.remove('show');
        alert('Could not regenerate: ' + err.message);
    }
}

let chatMessages   = [];   
let lastPlanContext = null; 

function storePlanContext(data, user) {
    lastPlanContext = {
        age: user.age,
        gender: user.gender,
        bmi: data.bmi,
        bmi_category: data.bmi_category,
        goal: data.goal || lastApiPayload?.goal,
        activity_level: user.activity || lastApiPayload?.activity_level,
        dietary_preference: lastApiPayload?.dietary_preference || 'Omnivore',
        health_conditions: data.health_conditions || [],
        daily_calories: data.daily_calories,
        cuisine_preference: lastApiPayload?.cuisine_preference || 'All',
    };
}

function openChat() {
    const overlay = document.getElementById('chatOverlay');
    if (overlay) { overlay.classList.add('show'); return; }
    //build if it doesnt exist
    const panel = document.createElement('div');
    panel.id = 'chatOverlay';
    panel.className = 'chat-overlay show';
    panel.innerHTML = `
      <div class="chat-panel">
        <div class="chat-header">
          <span>🥗 NutriAI Assistant</span>
          <button class="chat-close" onclick="closeChat()">✕</button>
        </div>
        <div class="chat-messages" id="chatMessages">
          <div class="chat-bubble chat-bubble--ai">
            Hi! I'm your NutriAI assistant. Ask me anything about your meal plan, nutrition, or diet goals! 🌿
          </div>
        </div>
        <div class="chat-input-row">
          <input id="chatInput" class="chat-input" type="text"
            placeholder="Ask about your plan, nutrients, substitutions…"
            onkeydown="if(event.key==='Enter') sendChat()" />
          <button class="chat-send" onclick="sendChat()">Send</button>
        </div>
      </div>`;
    document.body.appendChild(panel);
}

function closeChat() {
    const overlay = document.getElementById('chatOverlay');
    if (overlay) overlay.classList.remove('show');
}

async function sendChat() {
    const input = document.getElementById('chatInput');
    const text = input.value.trim();
    if (!text) return;

    input.value = '';
    addChatBubble(text, 'user');
    chatMessages.push({ role: 'user', content: text });

    const typingId = addTypingIndicator();

    try {
        const res = await fetch('/chat', {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({
                messages: chatMessages,
                user_context: lastPlanContext,
            }),
        });
        const json = await res.json();
        removeTypingIndicator(typingId);

        if (json.status !== 'ok') throw new Error(json.message || 'Unknown error');

        const reply = json.reply;
        chatMessages.push({ role: 'assistant', content: reply });
        addChatBubble(reply, 'ai');
    } catch (err) {
        removeTypingIndicator(typingId);
        addChatBubble('Sorry, I couldn\'t connect to the AI assistant. Make sure the server is running with a valid ANTHROPIC_API_KEY.', 'ai error');
    }
}

function addChatBubble(text, type) {
    const container = document.getElementById('chatMessages');
    if (!container) return;
    const div = document.createElement('div');
    div.className = `chat-bubble chat-bubble--${type.includes('ai') ? 'ai' : 'user'}`;
    div.textContent = text;
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
}

function addTypingIndicator() {
    const container = document.getElementById('chatMessages');
    if (!container) return null;
    const id = 'typing-' + Date.now();
    const div = document.createElement('div');
    div.id = id;
    div.className = 'chat-bubble chat-bubble--ai chat-typing';
    div.innerHTML = '<span></span><span></span><span></span>';
    container.appendChild(div);
    container.scrollTop = container.scrollHeight;
    return id;
}

function removeTypingIndicator(id) {
    if (id) document.getElementById(id)?.remove();
}
