GLOBAL_CSS = """
<style>
/* ============ Base ============ */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');

:root {
    --mk-blue: #0a66c2;
    --mk-cyan: #00b4d8;
    --mk-cobalt: #3d4feb;
    --mk-violet: #7b2cbf;
    --mk-dark: #1a2a3a;
    --mk-gray: #6b7f94;
    --mk-light: #f4f8fb;
    --mk-bg: #f8fafc;
    --mk-card: #ffffff;
    --mk-border: #e2e8f0;
    --mk-text: #1f2937;
    --mk-success: #16a34a;
    --mk-warning: #d97706;
    --mk-danger: #dc2626;
    --gradient: linear-gradient(135deg, #0a66c2 0%, #00b4d8 50%, #3d4feb 100%);
    --gradient-soft: linear-gradient(135deg, rgba(10,102,194,0.08) 0%, rgba(0,180,216,0.08) 50%, rgba(61,79,235,0.08) 100%);
    --shadow-sm: 0 1px 3px rgba(26,42,58,0.08);
    --shadow-md: 0 4px 12px rgba(26,42,58,0.10);
    --shadow-lg: 0 12px 32px rgba(26,42,58,0.14);
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 20px;
}

html, body, [class*="css"] {
    font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
}

.stApp {
    background: var(--mk-bg);
    color: var(--mk-text);
}

[data-testid="stHeader"] { background: transparent; }

[data-testid="stSidebar"] {
    background: #ffffff;
    border-right: 1px solid var(--mk-border);
}

[data-testid="stSidebarNav"] { background: #ffffff; }

/* Hide the native browser password reveal icon so only Streamlit's toggle shows */
::-ms-reveal { display: none; }
::-ms-clear { display: none; }

/* ============ Typography ============ */
h1, h2, h3, h4, h5, h6 {
    font-family: 'Inter', sans-serif !important;
    color: var(--mk-dark) !important;
    font-weight: 700 !important;
    letter-spacing: -0.02em;
}

h1 {
    font-size: 2.4rem !important;
    line-height: 1.15 !important;
}

/* ============ Buttons ============ */
.stButton button {
    border-radius: var(--radius-sm) !important;
    font-weight: 600 !important;
    transition: all 0.25s cubic-bezier(0.4, 0, 0.2, 1) !important;
    box-shadow: var(--shadow-sm);
    font-family: 'Inter', sans-serif !important;
}

.stButton button:hover {
    box-shadow: var(--shadow-md);
    border-color: #c8d8ea;
}

.stButton button:active { transform: translateY(0px); }

.stButton > button[kind="primary"] {
    background: var(--gradient) !important;
    border: none !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover {
    box-shadow: 0 6px 20px rgba(10,102,194,0.35);
}

/* ============ Cards ============ */
.mk-card {
    background: var(--mk-card);
    border: 1px solid var(--mk-border);
    border-radius: var(--radius-md);
    padding: 1.4rem;
    box-shadow: var(--shadow-sm);
    transition: box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    margin-bottom: 1rem;
}

.mk-card:hover {
    box-shadow: var(--shadow-md);
    border-color: #c8d8ea;
}

.mk-card-title {
    font-size: 1rem;
    font-weight: 700;
    color: var(--mk-dark);
    margin-bottom: 0.5rem;
}

.mk-card-subtitle {
    font-size: 0.85rem;
    color: var(--mk-gray);
    margin-bottom: 0.75rem;
}

.mk-eyebrow {
    text-transform: uppercase;
    letter-spacing: 0.1em;
    font-size: 0.7rem;
    font-weight: 700;
    color: var(--mk-blue);
}

/* ============ Badges ============ */
.mk-badge {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    border-radius: 999px;
    font-size: 0.75rem;
    font-weight: 600;
    letter-spacing: 0.02em;
}

.mk-badge-blue { background: #e8f1fd; color: #0a66c2; }
.mk-badge-green { background: #e6f7ee; color: #15803d; }
.mk-badge-orange { background: #fef3e2; color: #c2620a; }
.mk-badge-red { background: #fee8e8; color: #b91c1c; }
.mk-badge-gray { background: #eef2f6; color: #4b5a68; }
.mk-badge-violet { background: #f1eafc; color: #6d28d9; }
.mk-badge-cyan { background: #e1f5fb; color: #0891b2; }

.mk-badge-sm { padding: 0.15rem 0.5rem; font-size: 0.65rem; }

/* ============ Alerts ============ */
.mk-alert {
    border-radius: var(--radius-sm);
    padding: 0.9rem 1.2rem;
    margin: 0.8rem 0;
    font-size: 0.92rem;
    font-weight: 500;
    border-left: 4px solid;
}

.mk-alert-info { background: #f0f7ff; border-left-color: var(--mk-blue); color: #0c4a8c; }
.mk-alert-warning { background: #fef9ef; border-left-color: var(--mk-warning); color: #92400e; }
.mk-alert-danger { background: #fef2f2; border-left-color: var(--mk-danger); color: #991b1b; }
.mk-alert-success { background: #f0fdf4; border-left-color: var(--mk-success); color: #166534; }

/* ============ Hero ============ */
.mk-hero {
    background: var(--gradient-soft);
    border: 1px solid #dbe7f5;
    border-radius: var(--radius-lg);
    padding: 3rem 2.5rem;
    position: relative;
    overflow: hidden;
}

.mk-hero::before {
    content: '';
    position: absolute;
    top: -50%;
    right: -20%;
    width: 500px;
    height: 500px;
    background: radial-gradient(circle, rgba(0,180,216,0.15) 0%, transparent 70%);
    pointer-events: none;
}

.mk-hero h1 {
    font-size: 2.8rem !important;
    background: linear-gradient(135deg, #0a66c2, #0096c7, #3d4feb);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    margin-bottom: 0.75rem !important;
}

.mk-hero-span {
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.mk-hero-sub {
    font-size: 1.1rem;
    color: var(--mk-gray);
    max-width: 560px;
    line-height: 1.65;
}

/* ============ Stats ============ */
.mk-stat {
    text-align: center;
    padding: 1rem;
}

.mk-stat-value {
    font-size: 1.9rem;
    font-weight: 800;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.mk-stat-label {
    font-size: 0.8rem;
    color: var(--mk-gray);
    font-weight: 500;
}

/* ============ AI Companion ============ */
.mk-ai-wrap {
    display: flex;
    justify-content: center;
    padding: 0.5rem 0;
}

.mk-ai-orb {
    width: 120px;
    height: 120px;
    border-radius: 50%;
    background: var(--gradient);
    position: relative;
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 32px rgba(10,102,194,0.35);
    animation: ai-breathe 4s ease-in-out infinite;
}

.mk-ai-orb::before {
    content: '';
    position: absolute;
    inset: -14px;
    border-radius: 50%;
    border: 2px solid rgba(0,180,216,0.3);
    animation: ai-ring 3.5s ease-out infinite;
}

.mk-ai-orb::after {
    content: '';
    position: absolute;
    inset: -28px;
    border-radius: 50%;
    border: 2px solid rgba(61,79,235,0.15);
    animation: ai-ring 3.5s ease-out 1.2s infinite;
}

.mk-ai-inner {
    width: 74px;
    height: 74px;
    border-radius: 50%;
    background: rgba(255,255,255,0.18);
    display: flex;
    align-items: center;
    justify-content: center;
    backdrop-filter: blur(2px);
}

.mk-ai-pulse {
    font-size: 1.7rem;
    color: white;
    text-shadow: 0 2px 8px rgba(0,0,0,0.25);
}

.mk-ai-orb.listening { animation: ai-breathe-fast 2s ease-in-out infinite; }
.mk-ai-orb.listening::before, .mk-ai-orb.listening::after { display: none; }

.mk-ai-orb.thinking .mk-ai-pulse { animation: ai-orbital 2.4s linear infinite; }

.mk-ai-orb.concerned {
    background: linear-gradient(135deg, #b91c1c 0%, #dc2626 50%, #ea580c 100%);
    box-shadow: 0 8px 32px rgba(220,38,38,0.35);
}

.mk-ai-orb.success { animation: ai-success 0.8s ease-in-out; }

.mk-ai-status {
    text-align: center;
    font-size: 0.85rem;
    font-weight: 600;
    color: var(--mk-gray);
    margin-top: 0.5rem;
}

/* ============ Typing dots ============ */
.mk-typing {
    display: inline-flex;
    align-items: center;
    gap: 4px;
    padding: 0.5rem 1rem;
    background: #f1f5f9;
    border-radius: var(--radius-md);
}

.mk-typing span {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: var(--mk-blue);
    display: inline-block;
    animation: typing-bounce 1.2s ease-in-out infinite;
}

.mk-typing span:nth-child(2) { animation-delay: 0.2s; }
.mk-typing span:nth-child(3) { animation-delay: 0.4s; }

/* ============ Progress stepper ============ */
.mk-stepper {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 1rem 0 1.5rem;
    position: relative;
    padding: 0 0.5rem;
}

.mk-step {
    display: flex;
    flex-direction: column;
    align-items: center;
    flex: 1;
    position: relative;
    z-index: 1;
}

.mk-step-dot {
    width: 36px;
    height: 36px;
    border-radius: 50%;
    background: white;
    border: 2px solid var(--mk-border);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
    font-weight: 700;
    color: var(--mk-gray);
    transition: all 0.3s ease;
}

.mk-step.active .mk-step-dot {
    background: var(--gradient);
    border-color: transparent;
    color: white;
    box-shadow: 0 4px 12px rgba(10,102,194,0.35);
    transform: scale(1.08);
}

.mk-step.completed .mk-step-dot {
    background: var(--mk-success);
    border-color: transparent;
    color: white;
}

.mk-step-label {
    margin-top: 0.4rem;
    font-size: 0.72rem;
    font-weight: 600;
    color: var(--mk-gray);
    text-align: center;
}

.mk-step.active .mk-step-label, .mk-step.completed .mk-step-label { color: var(--mk-dark); }

.mk-step-line {
    position: absolute;
    top: 18px;
    left: 50%;
    right: -50%;
    height: 2px;
    background: var(--mk-border);
    z-index: 0;
}

.mk-step:last-child .mk-step-line { display: none; }

.mk-step.completed .mk-step-line, .mk-step.active ~ .mk-step .mk-step-line {
    background: var(--mk-border);
}

/* ============ Chat ============ */
.mk-chat-msg {
    animation: slide-up 0.4s cubic-bezier(0.4, 0, 0.2, 1);
    border-radius: var(--radius-md);
    padding: 0.75rem 1.1rem;
    margin: 0.4rem 0;
    font-size: 0.95rem;
    line-height: 1.5;
}

.mk-chat-user {
    background: var(--gradient);
    color: white;
    border-radius: var(--radius-md) var(--radius-md) var(--radius-sm) var(--radius-md);
    max-width: 80%;
    margin-left: auto;
}

.mk-chat-ai {
    background: #edf4fb;
    color: var(--mk-dark);
    border-radius: var(--radius-md) var(--radius-md) var(--radius-md) var(--radius-sm);
    max-width: 85%;
}

.mk-quick-reply {
    display: inline-block;
    padding: 0.5rem 1.1rem;
    border-radius: 999px;
    border: 1.5px solid #cfe0f2;
    background: white;
    color: var(--mk-blue);
    font-size: 0.85rem;
    font-weight: 600;
    cursor: pointer;
    transition: all 0.25s ease;
    margin: 0 0.4rem 0.4rem 0;
}

.mk-quick-reply:hover {
    background: var(--mk-blue);
    color: white;
    border-color: var(--mk-blue);
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(10,102,194,0.25);
}

/* ============ Info row ============ */
.mk-info-row {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.35rem 0;
    font-size: 0.88rem;
    color: var(--mk-text);
}

.mk-info-icon {
    width: 28px;
    height: 28px;
    border-radius: 8px;
    background: #eef4fb;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 0.85rem;
}

.mk-info-label { color: var(--mk-gray); font-size: 0.8rem; }

.mk-info-value { font-weight: 600; color: var(--mk-dark); }

/* ============ Section header ============ */
.mk-section {
    margin: 2rem 0 1rem;
    padding-bottom: 0.5rem;
}

.mk-section-title {
    font-size: 1.4rem;
    font-weight: 800;
    color: var(--mk-dark);
}

.mk-section-sub {
    color: var(--mk-gray);
    font-size: 0.9rem;
    margin-top: 0.25rem;
}

/* ============ Emergency ============ */
.mk-emergency {
    background: #fef2f2;
    border: 2px solid #fca5a5;
    border-radius: var(--radius-md);
    padding: 1.4rem 1.6rem;
    margin: 1rem 0;
    animation: emergency-pulse 2s ease-in-out;
    border-left: 6px solid var(--mk-danger);
}

.mk-emergency-title {
    color: #991b1b;
    font-weight: 800;
    font-size: 1.1rem;
    margin-bottom: 0.5rem;
}

.mk-emergency-body { color: #7f1d1d; font-size: 0.92rem; line-height: 1.6; }

/* ============ Doctor card ============ */
.mk-doctor-card {
    background: white;
    border: 1px solid var(--mk-border);
    border-radius: var(--radius-md);
    padding: 1.3rem 1.4rem;
    transition: box-shadow 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    height: 100%;
    box-shadow: var(--shadow-sm);
    display: flex;
    flex-direction: column;
    align-items: stretch;
}

.mk-doctor-card:hover {
    box-shadow: var(--shadow-md);
    border-color: #b8d2ea;
}

.mk-card-head {
    display: flex;
    align-items: center;
    gap: 0.9rem;
}

.mk-bio {
    font-size: 0.85rem;
    color: var(--mk-gray);
    line-height: 1.6;
    margin: 0.5rem 0 0.25rem;
    display: -webkit-box;
    -webkit-line-clamp: 3;
    -webkit-box-orient: vertical;
    overflow: hidden;
}

.mk-card-foot {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 0.6rem;
    flex-wrap: wrap;
    gap: 0.5rem;
}

.mk-fee {
    font-weight: 700;
    color: var(--mk-dark);
    font-size: 1.05rem;
}

.mk-lang {
    font-size: 0.8rem;
    color: var(--mk-gray);
}

.mk-doctor-avatar {
    width: 64px;
    height: 64px;
    border-radius: 50%;
    background: var(--gradient-soft);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
    font-weight: 800;
    color: var(--mk-blue);
    border: 2px solid #dbe7f5;
    overflow: hidden;
}

.mk-doctor-avatar img {
    width: 100%; height: 100%; object-fit: cover;
}

.mk-doctor-name {
    font-weight: 700;
    font-size: 1.05rem;
    color: var(--mk-dark);
}

.mk-doctor-spec {
    color: var(--mk-blue);
    font-size: 0.82rem;
    font-weight: 600;
}

.mk-star {
    color: #f59e0b;
    font-size: 0.85rem;
}

.mk-doctor-meta {
    font-size: 0.82rem;
    color: var(--mk-gray);
    display: flex;
    align-items: center;
    gap: 0.35rem;
}

/* ============ Footer ============ */
.mk-footer {
    margin-top: 4rem;
    padding: 2.5rem 0 1rem;
    border-top: 1px solid var(--mk-border);
    text-align: center;
    color: var(--mk-gray);
    font-size: 0.85rem;
}

/* ============ Empty state ============ */
.mk-empty {
    text-align: center;
    padding: 3rem 1.5rem;
    color: var(--mk-gray);
    border: 1.5px dashed #cbd5e1;
    border-radius: var(--radius-md);
    background: white;
}

.mk-empty-icon {
    font-size: 2.5rem;
    margin-bottom: 0.75rem;
    opacity: 0.5;
}

.mk-empty-title {
    font-weight: 700;
    color: var(--mk-dark);
    font-size: 1.05rem;
    margin-bottom: 0.35rem;
}

.mk-empty-text { font-size: 0.88rem; max-width: 320px; margin: 0 auto; }

/* ============ Success check ============ */
.mk-success-check {
    width: 72px;
    height: 72px;
    border-radius: 50%;
    background: linear-gradient(135deg, #16a34a, #22c55e);
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto;
    box-shadow: 0 8px 24px rgba(22,163,74,0.35);
    animation: success-pop 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
}

.mk-success-check span {
    color: white;
    font-size: 2.2rem;
    font-weight: 800;
}

/* ============ Feature tile ============ */
.mk-feature {
    text-align: center;
    padding: 1.75rem 1.25rem;
    border-radius: var(--radius-md);
    background: white;
    border: 1px solid var(--mk-border);
    transition: all 0.3s ease;
    height: 100%;
}

.mk-feature:hover { transform: translateY(-4px); box-shadow: var(--shadow-md); }

.mk-feature-icon {
    width: 56px;
    height: 56px;
    margin: 0 auto 1rem;
    border-radius: 14px;
    background: var(--gradient-soft);
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 1.6rem;
}

.mk-feature-title { font-weight: 700; color: var(--mk-dark); margin-bottom: 0.4rem; }

.mk-feature-desc { font-size: 0.85rem; color: var(--mk-gray); line-height: 1.55; }

/* ============ Notification item ============ */
.mk-notif {
    padding: 0.9rem 1.1rem;
    border-radius: var(--radius-sm);
    background: white;
    border: 1px solid var(--mk-border);
    margin-bottom: 0.6rem;
    transition: all 0.25s ease;
    animation: fade-in 0.4s ease;
}

.mk-notif:hover { box-shadow: var(--shadow-sm); border-color: #c8d8ea; }
.mk-notif-title { font-weight: 700; font-size: 0.92rem; color: var(--mk-dark); }
.mk-notif-msg { font-size: 0.85rem; color: var(--mk-gray); margin-top: 0.2rem; line-height: 1.45; }
.mk-notif-time { font-size: 0.72rem; color: #9aa9b9; margin-top: 0.3rem; }

.mk-notif.unread {
    background: #f0f7ff;
    border-left: 4px solid var(--mk-blue);
}

/* ============ Animations ============ */
@keyframes ai-breathe {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.05); }
}

@keyframes ai-breathe-fast {
    0%, 100% { transform: scale(1); }
    50% { transform: scale(1.08); }
}

@keyframes ai-ring {
    0% { transform: scale(0.8); opacity: 0.6; }
    100% { transform: scale(1.5); opacity: 0; }
}

@keyframes ai-orbital {
    0% { transform: rotate(0deg); }
    100% { transform: rotate(360deg); }
}

@keyframes typing-bounce {
    0%, 60%, 100% { transform: translateY(0); opacity: 0.6; }
    30% { transform: translateY(-6px); opacity: 1; }
}

@keyframes fade-in {
    from { opacity: 0; }
    to { opacity: 1; }
}

@keyframes slide-up {
    from { opacity: 0; transform: translateY(14px); }
    to { opacity: 1; transform: translateY(0); }
}

@keyframes success-pop {
    0% { transform: scale(0); opacity: 0; }
    60% { transform: scale(1.15); }
    100% { transform: scale(1); opacity: 1; }
}

@keyframes emergency-pulse {
    0% { box-shadow: 0 0 0 0 rgba(220,38,38,0.35); }
    70% { box-shadow: 0 0 0 14px rgba(220,38,38,0); }
    100% { box-shadow: 0 0 0 0 rgba(220,38,38,0); }
}

@keyframes soft-pulse {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.6; }
}

.mk-soft-pulse { animation: soft-pulse 2.5s ease-in-out infinite; }

/* ============ Reduced motion ============ */
@media (prefers-reduced-motion: reduce) {
    .mk-ai-orb, .mk-ai-orb.listening, .mk-step-dot,
    .mk-typing span, .mk-doctor-card, .mk-feature,
    .mk-hero h1, .mk-success-check {
        animation: none !important;
        transition: none !important;
        transform: none !important;
    }
}

/* ============ Misc polish ============ */
[data-testid="stMetricValue"] {
    font-size: 1.4rem !important;
    font-weight: 700 !important;
    color: var(--mk-dark) !important;
}

[data-testid="stMetricLabel"] {
    font-size: 0.8rem !important;
    color: var(--mk-gray) !important;
}

[data-testid="stMetric"] {
    background: white;
    border: 1px solid var(--mk-border);
    border-radius: var(--radius-sm);
    padding: 0.9rem 1.2rem;
    box-shadow: var(--shadow-sm);
}

div[data-testid="stForm"] {
    background: white;
    border: 1px solid var(--mk-border);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    box-shadow: var(--shadow-sm);
}

div[data-baseweb="input"], div[data-baseweb="select"] > div {
    border-radius: var(--radius-sm) !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0.5rem;
}

.stTabs [data-baseweb="tab"] {
    border-radius: 8px 8px 0 0;
    padding: 0.6rem 1.2rem;
    font-weight: 600;
}

.stTabs [aria-selected="true"] {
    background: #f0f7ff;
    color: var(--mk-blue) !important;
}

[data-testid="stChatMessage"] {
    animation: slide-up 0.35s ease;
}

[data-testid="stExpander"] {
    border: 1px solid var(--mk-border) !important;
    border-radius: var(--radius-md) !important;
    background: white;
    box-shadow: var(--shadow-sm);
}

/* Logo text */
.mk-logo {
    display: flex;
    align-items: center;
    gap: 0.6rem;
    padding: 0.4rem 0.2rem;
}

.mk-logo-mark {
    width: 38px;
    height: 38px;
    border-radius: 12px;
    background: var(--gradient);
    display: flex;
    align-items: center;
    justify-content: center;
    color: white;
    font-size: 1.15rem;
    font-weight: 800;
    box-shadow: 0 4px 12px rgba(10,102,194,0.3);
}

.mk-logo-text {
    font-weight: 800;
    font-size: 1.15rem;
    background: var(--gradient);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    letter-spacing: -0.02em;
}

/* Sidebar nav polish */
[data-testid="stSidebarNav"] a {
    padding: 0.5rem 0.75rem !important;
    border-radius: var(--radius-sm) !important;
    transition: all 0.2s ease;
}

[data-testid="stSidebarNav"] a:hover {
    background: #f0f7ff !important;
}

[data-testid="stSidebarNav"] a[aria-current="page"] {
    background: var(--gradient-soft) !important;
    font-weight: 600;
}
</style>
"""


def inject_global_styles():
    import streamlit as st
    st.markdown(GLOBAL_CSS, unsafe_allow_html=True)