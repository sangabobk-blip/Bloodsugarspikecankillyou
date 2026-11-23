import os
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import date

st.set_page_config(
    page_title="GLUCO-FLOW | 췌장 생존 혈당 코치",
    page_icon="🩸",
    layout="wide",
)

# ---------------------------------------------------------
# 0. 1번 아이디어: Y2K 세기말 밈 & 싸이월드·네오브루탈리즘 스타일
# ---------------------------------------------------------
st.markdown(
    """
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Black+Han+Sans&family=Gowun+Batang:wght@700&family=Jua&display=swap');

    /* 형광 라임-레몬 모눈종이 배경 */
    .stApp {
        background-color: #f4ff5c;
        background-image:
            linear-gradient(90deg, rgba(255, 0, 128, 0.16) 2px, transparent 2px),
            linear-gradient(rgba(0, 102, 255, 0.16) 2px, transparent 2px);
        background-size: 36px 36px;
        font-family: 'Jua', 'Gulim', 'Comic Sans MS', sans-serif !important;
        color: #111111;
    }

    /* 궁서/굵은 밈 스타일 제목 + 핫핑크·시안 이중 그림자 */
    h1 {
        font-family: 'Black Han Sans', 'Gungsuh', serif !important;
        color: #ff1e6e !important;
        text-shadow: 3px 3px 0px #000000, -1px -1px 0px #00ffff;
        letter-spacing: -0.5px;
    }
    h2, h3, h4 {
        font-family: 'Jua', 'Gungsuh', sans-serif !important;
        color: #111111 !important;
    }

    /* 굵은 검정 테두리 + 하드 그림자 카드 */
    div[data-testid="stMetric"], div[data-testid="stForm"], div.stTabs [data-baseweb="tab-panel"] {
        background-color: #ffffff !important;
        border: 3px solid #000000 !important;
        box-shadow: 6px 6px 0px #000000 !important;
        border-radius: 12px !important;
        padding: 14px !important;
    }

    /* 쫀득한 버튼 */
    div.stButton > button {
        background-color: #ff66c4 !important;
        color: #000000 !important;
        font-family: 'Jua', sans-serif !important;
        font-size: 16px !important;
        border: 3px solid #000000 !important;
        box-shadow: 4px 4px 0px #000000 !important;
        border-radius: 10px !important;
        transition: transform 0.08s ease;
    }
    div.stButton > button:hover {
        background-color: #00f5d4 !important;
        transform: translate(-2px, -2px);
    }

    /* 전광판 밈 배너 */
    .retro-marquee {
        background: #000000;
        color: #39ff14;
        border: 3px solid #ff1e6e;
        padding: 8px 12px;
        font-family: 'Gungsuh', 'Jua', monospace;
        font-size: 16px;
        font-weight: bold;
        border-radius: 8px;
        margin-bottom: 12px;
        box-shadow: 4px 4px 0px #ff1e6e;
    }

    /* 캐릭터 스테이지 */
    .char-stage {
        background: radial-gradient(circle, #fff0f6 0%, #ffd6e7 100%);
        border: 4px solid #000000;
        box-shadow: 7px 7px 0px #000000;
        border-radius: 16px;
        padding: 16px;
        text-align: center;
        margin-bottom: 14px;
    }
    .char-speech {
        background: #ffffff;
        border: 2.5px solid #000000;
        border-radius: 12px;
        padding: 8px 12px;
        margin-top: 8px;
        font-size: 15px;
        font-weight: bold;
        box-shadow: 3px 3px 0px #000000;
    }

    /* SVG 애니메이션 키프레임 */
    @keyframes floatHappy {
        0%, 100% { transform: translateY(0px) rotate(0deg); }
        50% { transform: translateY(-7px) rotate(2deg); }
    }
    @keyframes shiverCry {
        0%, 100% { transform: translateX(0px); }
        25% { transform: translateX(-4px) rotate(-1.5deg); }
        75% { transform: translateX(4px) rotate(1.5deg); }
    }
    @keyframes tearDrop {
        0% { transform: translateY(0px); opacity: 1; }
        100% { transform: translateY(26px); opacity: 0; }
    }
    @keyframes koFall {
        0% { transform: rotate(0deg) translateY(0px); }
        35% { transform: rotate(-15deg) translateY(-6px); }
        100% { transform: rotate(84deg) translate(28px, 18px); }
    }
    @keyframes soulRise {
        0% { transform: translateY(10px) scale(0.85); opacity: 0.2; }
        50% { transform: translateY(-14px) scale(1.05); opacity: 1; }
        100% { transform: translateY(-32px) scale(0.9); opacity: 0; }
    }

    .anim-happy { animation: floatHappy 2s ease-in-out infinite; transform-origin: center; }
    .anim-cry { animation: shiverCry 0.28s linear infinite; transform-origin: center; }
    .anim-tear { animation: tearDrop 0.9s ease-in infinite; }
    .anim-ko { animation: koFall 1.1s cubic-bezier(.36,.07,.19,.97) forwards; transform-origin: 100px 145px; }
    .anim-soul { animation: soulRise 1.8s ease-out infinite; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ---------------------------------------------------------
# 1. 정제된 공공 식품 DB 로드 (foods_gluco_db.csv)
# ---------------------------------------------------------
FALLBACK_FOODS = [
    {"식품명": "흰쌀밥 (1공기)", "분류": "탄수화물", "원본분류": "밥류", "기준량": "100g", "열량(kcal)": 143.0, "탄수화물(g)": 31.2, "식이섬유(g)": 0.4, "당류(g)": 0.0, "단백질(g)": 2.5, "지방(g)": 0.3, "GI": 73},
    {"식품명": "닭가슴살 구이", "분류": "단백질·지방", "원본분류": "구이류", "기준량": "100g", "열량(kcal)": 165.0, "탄수화물(g)": 0.0, "식이섬유(g)": 0.0, "당류(g)": 0.0, "단백질(g)": 31.0, "지방(g)": 3.6, "GI": 25},
    {"식품명": "양배추 샐러드", "분류": "채소·식이섬유", "원본분류": "생채·무침류", "기준량": "100g", "열량(kcal)": 24.0, "탄수화물(g)": 5.2, "식이섬유(g)": 2.5, "당류(g)": 2.0, "단백질(g)": 1.3, "지방(g)": 0.1, "GI": 18},
    {"식품명": "달달한 밀크티", "분류": "음료·당류", "원본분류": "음료 및 차류", "기준량": "300ml", "열량(kcal)": 240.0, "탄수화물(g)": 38.0, "식이섬유(g)": 0.0, "당류(g)": 35.0, "단백질(g)": 3.0, "지방(g)": 6.0, "GI": 72},
]


@st.cache_data
def load_food_db() -> pd.DataFrame:
    csv_path = "foods_gluco_db.csv"
    if os.path.exists(csv_path):
        df = pd.read_csv(csv_path, encoding="utf-8-sig")
    else:
        df = pd.DataFrame(FALLBACK_FOODS)

    for col in ["열량(kcal)", "탄수화물(g)", "식이섬유(g)", "당류(g)", "단백질(g)", "지방(g)", "GI"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0.0)
    df["식품명"] = df["식품명"].astype(str)
    df["분류"] = df["분류"].astype(str)
    df["기준량"] = df["기준량"].astype(str)
    return df


df_foods = load_food_db()

# ---------------------------------------------------------
# 2. SVG 캐릭터 생성기 (록걸 / 스페인 미남 / 췌장 요정 / 헬스 관장)
# ---------------------------------------------------------
CHARACTER_PROFILES = {
    "🎸 검정 립스틱 시크 록걸 (레이나)": {
        "key": "rock_girl",
        "happy": "오~ 채소랑 단백질 먼저 챙겼네? 오늘 내 혈당 폼 미쳤다 🤘🖤",
        "cry": "잠깐만... 탄수화물 너무 치고 들어오는데?! 아이라인 번지게 울기 직전이야 ಥ_ಥ",
        "ko": "끄악... 혈당 스파이크 직격탄 맞고 무대 위에서 기절함... (X_X)",
    },
    "🌹 고전 서양 스페인 미남 (알레한드로)": {
        "key": "spanish_handsome",
        "happy": "완벽한 식사 순서로군, 아미고. 내 조각 같은 턱선과 혈당이 흔들림 없지. ✨",
        "cry": "오, 디오스 미오...! 이토록 거친 당분의 파도라니, 눈물이 멈추지 않는군... 💧",
        "ko": "아디오스... 과도한 탄수화물에 이 스페인 미남도 쓰러지고 말았다... (X_X)",
    },
    "🧬 과로 직전 췌장 요정 (베타세포군)": {
        "key": "pancreas",
        "happy": "인슐린 야근 없음! 오늘 칼퇴 가능! 너무 행복해~ 💖",
        "cry": "으아앙 인슐린 공장 풀가동 중!! 제발 채소 좀 먼저 넣어줘요 엉엉 😭",
        "ko": "췌장 과부하로 시스템 종료... 영혼 탈출 중... 👻",
    },
    "💪 3대 500 헬스 관장님 (머슬킹)": {
        "key": "muscle_king",
        "happy": "좋았어 회원님!! 근손실 방지에 혈당까지 완벽 통제! 득근!! 🔥",
        "cry": "회원님!! 지금 당류를 그렇게 들이부으면 내 눈에서 프로틴 눈물이 납니다!! 😢",
        "ko": "회원님... 이건 3대 500보다 무거운 혈당이다... 관장 먼저 눕는다... 🏋️‍♂️💀",
    },
}


def render_character_svg(char_key: str, state: str) -> str:
    """state: 'happy' | 'cry' | 'ko'"""
    group_class = {"happy": "anim-happy", "cry": "anim-cry", "ko": "anim-ko"}[state]

    if state == "happy":
        eyes_svg = """
            <circle cx="82" cy="88" r="5.5" fill="#111"/>
            <circle cx="84" cy="86" r="2" fill="#fff"/>
            <circle cx="118" cy="88" r="5.5" fill="#111"/>
            <circle cx="120" cy="86" r="2" fill="#fff"/>
            <path d="M 74 80 Q 82 75 90 80" stroke="#111" stroke-width="2.5" fill="none"/>
            <path d="M 110 80 Q 118 75 126 80" stroke="#111" stroke-width="2.5" fill="none"/>
        """
        tears_svg = """
            <text x="148" y="55" font-size="20">✨</text>
            <text x="36" y="65" font-size="18">💖</text>
        """
    elif state == "cry":
        eyes_svg = """
            <ellipse cx="82" cy="89" rx="6" ry="7" fill="#111"/>
            <circle cx="80" cy="87" r="2.5" fill="#fff"/>
            <ellipse cx="118" cy="89" rx="6" ry="7" fill="#111"/>
            <circle cx="116" cy="87" r="2.5" fill="#fff"/>
            <path d="M 73 78 L 90 83" stroke="#111" stroke-width="3" stroke-linecap="round"/>
            <path d="M 127 78 L 110 83" stroke="#111" stroke-width="3" stroke-linecap="round"/>
        """
        tears_svg = """
            <g class="anim-tear">
                <path d="M 78 96 Q 74 108 78 114 Q 82 108 78 96 Z" fill="#00b4d8"/>
                <path d="M 122 96 Q 118 108 122 114 Q 126 108 122 96 Z" fill="#00b4d8"/>
            </g>
            <text x="145" y="62" font-size="20">💦</text>
        """
    else:
        eyes_svg = """
            <path d="M 76 83 L 88 94 M 88 83 L 76 94" stroke="#d00000" stroke-width="3.5" stroke-linecap="round"/>
            <path d="M 112 83 L 124 94 M 124 83 L 112 94" stroke="#d00000" stroke-width="3.5" stroke-linecap="round"/>
        """
        tears_svg = ""

    if char_key == "rock_girl":
        mouth_svg = (
            '<path d="M 88 112 Q 100 123 112 112 Q 100 117 88 112 Z" fill="#111111" stroke="#000" stroke-width="1.5"/>'
            if state == "happy"
            else '<ellipse cx="100" cy="114" rx="8" ry="6" fill="#111111" stroke="#000" stroke-width="2"/>'
        )
        body_svg = f"""
            <path d="M 48 95 C 42 40, 158 40, 152 95 L 160 155 L 40 155 Z" fill="#1a1a2e" stroke="#000" stroke-width="3"/>
            <path d="M 55 75 C 48 110, 48 135, 52 150" stroke="#9d4edd" stroke-width="6" fill="none" stroke-linecap="round"/>
            <path d="M 145 75 C 152 110, 152 135, 148 150" stroke="#ff007f" stroke-width="6" fill="none" stroke-linecap="round"/>
            <path d="M 62 142 L 138 142 L 146 185 L 54 185 Z" fill="#111" stroke="#000" stroke-width="3"/>
            <rect x="86" y="128" width="28" height="10" rx="3" fill="#000"/>
            <circle cx="100" cy="133" r="3" fill="#e0e0e0" stroke="#fff" stroke-width="1.5"/>
            <path d="M 68 72 C 68 52, 132 52, 132 72 L 128 112 C 124 128, 76 128, 72 112 Z" fill="#ffe5d9" stroke="#000" stroke-width="3"/>
            <path d="M 66 74 L 82 58 L 94 74 L 106 56 L 120 74 L 134 62 L 132 48 L 68 48 Z" fill="#1a1a2e"/>
            <polygon points="124,52 118,64 125,64 120,76 133,61 126,61" fill="#ffbe0b" stroke="#000" stroke-width="1.5"/>
            <ellipse cx="82" cy="88" rx="10" ry="7" fill="#6c757d" opacity="0.45"/>
            <ellipse cx="118" cy="88" rx="10" ry="7" fill="#6c757d" opacity="0.45"/>
            {eyes_svg}
            {mouth_svg}
            <circle cx="112" cy="118" r="2" fill="#e0e0e0" stroke="#000" stroke-width="1"/>
        """
    elif char_key == "spanish_handsome":
        mouth_svg = (
            '<path d="M 88 112 Q 102 120 113 110" stroke="#9e2a2b" stroke-width="3.2" fill="none" stroke-linecap="round"/>'
            if state == "happy"
            else '<path d="M 89 116 Q 100 109 111 116" stroke="#9e2a2b" stroke-width="3" fill="none" stroke-linecap="round"/>'
        )
        body_svg = f"""
            <path d="M 58 88 C 52 38, 148 38, 142 88 L 145 125 L 55 125 Z" fill="#1b1b1b" stroke="#000" stroke-width="3"/>
            <path d="M 58 140 L 142 140 L 150 185 L 50 185 Z" fill="#ffffff" stroke="#000" stroke-width="3"/>
            <path d="M 58 140 L 85 185 L 50 185 Z" fill="#c1121f" stroke="#000" stroke-width="2.5"/>
            <circle cx="72" cy="154" r="7" fill="#e63946" stroke="#000" stroke-width="2"/>
            <path d="M 68 70 C 68 50, 132 50, 132 70 L 128 110 L 108 128 L 92 128 L 72 110 Z" fill="#f4cbb2" stroke="#000" stroke-width="3"/>
            <path d="M 65 74 C 72 52, 102 52, 114 68 C 122 56, 134 62, 134 74 C 134 44, 65 44, 65 74 Z" fill="#1b1b1b"/>
            <path d="M 71 78 L 92 80" stroke="#111" stroke-width="4" stroke-linecap="round"/>
            <path d="M 108 80 L 129 78" stroke="#111" stroke-width="4" stroke-linecap="round"/>
            <path d="M 100 84 L 97 102 L 103 103" stroke="#c99679" stroke-width="2.5" fill="none" stroke-linecap="round"/>
            {eyes_svg}
            {mouth_svg}
        """
    elif char_key == "pancreas":
        mouth_svg = (
            '<path d="M 88 108 Q 100 120 112 108" stroke="#000" stroke-width="3" fill="none" stroke-linecap="round"/>'
            if state == "happy"
            else '<ellipse cx="100" cy="112" rx="9" ry="7" fill="#ff4d6d" stroke="#000" stroke-width="2.5"/>'
        )
        body_svg = f"""
            <path d="M 45 105 C 42 72, 95 62, 135 76 C 162 85, 165 122, 135 132 C 102 142, 48 138, 45 105 Z"
                  fill="#ffccd5" stroke="#000" stroke-width="3.5"/>
            <circle cx="72" cy="100" r="6" fill="#ff8fa3" opacity="0.7"/>
            <circle cx="128" cy="100" r="6" fill="#ff8fa3" opacity="0.7"/>
            {eyes_svg}
            {mouth_svg}
        """
    else:
        mouth_svg = (
            '<path d="M 85 112 Q 100 122 115 112" stroke="#000" stroke-width="3.5" fill="none"/>'
            if state == "happy"
            else '<path d="M 86 116 Q 100 107 114 116" stroke="#000" stroke-width="3.5" fill="none"/>'
        )
        body_svg = f"""
            <path d="M 45 142 Q 100 124 155 142 L 165 185 L 35 185 Z" fill="#3a86ff" stroke="#000" stroke-width="3.5"/>
            <rect x="68" y="56" width="64" height="72" rx="18" fill="#e0a96d" stroke="#000" stroke-width="3.5"/>
            <rect x="67" y="64" width="66" height="10" fill="#ff006e" stroke="#000" stroke-width="2.5"/>
            {eyes_svg}
            {mouth_svg}
        """

    soul_svg = ""
    if state == "ko":
        soul_svg = """
            <g class="anim-soul">
                <path d="M 145 75 C 145 55, 175 55, 175 75 L 175 100 L 168 94 L 160 100 L 152 94 L 145 100 Z"
                      fill="#ffffff" stroke="#000" stroke-width="2.5" opacity="0.9"/>
                <circle cx="155" cy="73" r="2.5" fill="#000"/>
                <circle cx="165" cy="73" r="2.5" fill="#000"/>
                <text x="146" y="48" font-size="14" font-weight="bold" fill="#000">KO...</text>
            </g>
        """

    return f"""
    <svg width="210" height="190" viewBox="0 0 210 190" xmlns="http://www.w3.org/2000/svg">
        <g class="{group_class}">
            {body_svg}
            {tears_svg}
        </g>
        {soul_svg}
    </svg>
    """


# ---------------------------------------------------------
# 3. 생리학 기반 혈당 모델 (쉬운 용어 + 과학 원리 연결)
# ---------------------------------------------------------
SEQUENCE_OPTIONS = {
    "탄수화물·단 음료부터 먹기 (혈당 급상승)": {
        "peak_multiplier": 1.15,
        "peak_time": 35,
        "spread": 22,
        "desc": "빈속에 밥·면·빵·달달한 음료가 먼저 들어가면 포도당이 혈관으로 한꺼번에 쏟아져 인슐린이 과로합니다.",
    },
    "보통 식사 (반찬이랑 밥 같이 먹기)": {
        "peak_multiplier": 1.00,
        "peak_time": 45,
        "spread": 28,
        "desc": "일반적인 식사 방식으로, 음식 구성에 따라 무난하거나 다소 높은 혈당 파도를 만듭니다.",
    },
    "거꾸로 식사법 (채소 → 고기/단백질 → 밥/면)": {
        "peak_multiplier": 0.72,
        "peak_time": 60,
        "spread": 38,
        "desc": "채소의 식이섬유가 장에 방어막을 치고 단백질이 소화 속도를 늦춰 혈당 급등을 약 25~30% 막아줍니다!",
    },
}


def calculate_meal_metrics(selected_items: list[dict], sequence_key: str) -> dict:
    if not selected_items:
        return {}

    total_kcal = sum(item["열량(kcal)"] * item["인분"] for item in selected_items)
    total_carb = sum(item["탄수화물(g)"] * item["인분"] for item in selected_items)
    total_fiber = sum(item["식이섬유(g)"] * item["인분"] for item in selected_items)
    total_protein = sum(item["단백질(g)"] * item["인분"] for item in selected_items)
    total_fat = sum(item["지방(g)"] * item["인분"] for item in selected_items)

    net_carb = max(0.0, total_carb - total_fiber)

    raw_gl = 0.0
    for item in selected_items:
        item_net_carb = max(0.0, (item["탄수화물(g)"] - item["식이섬유(g)"]) * item["인분"])
        raw_gl += (item["GI"] * item_net_carb) / 100.0

    buffer_score = min(0.25, (total_fiber * 0.018) + (total_protein * 0.004) + (total_fat * 0.003))
    seq_factor = SEQUENCE_OPTIONS[sequence_key]["peak_multiplier"]

    effective_gl = round(raw_gl * (1.0 - buffer_score) * seq_factor, 1)
    delta_glucose = round(effective_gl * 2.35, 1)
    peak_glucose = round(90.0 + delta_glucose, 1)

    if effective_gl >= 22 or total_kcal >= 1100:
        char_state = "ko"
        risk_label = "🚨 혈당 폭발·과식 (KO)"
    elif effective_gl >= 12 or total_kcal >= 750:
        char_state = "cry"
        risk_label = "💦 혈당 출렁임 주의"
    else:
        char_state = "happy"
        risk_label = "✨ 혈당 안정·평온"

    return {
        "total_kcal": round(total_kcal, 1),
        "total_carb": round(total_carb, 1),
        "net_carb": round(net_carb, 1),
        "total_fiber": round(total_fiber, 1),
        "total_protein": round(total_protein, 1),
        "total_fat": round(total_fat, 1),
        "raw_gl": round(raw_gl, 1),
        "effective_gl": effective_gl,
        "delta_glucose": delta_glucose,
        "peak_glucose": peak_glucose,
        "risk_label": risk_label,
        "char_state": char_state,
    }


def simulate_glucose_curve(metrics: dict, sequence_key: str) -> pd.DataFrame:
    minutes = np.arange(0, 185, 5)
    baseline = 90.0
    rows = []

    for label, cfg in SEQUENCE_OPTIONS.items():
        ratio = cfg["peak_multiplier"] / SEQUENCE_OPTIONS[sequence_key]["peak_multiplier"]
        amp = metrics["delta_glucose"] * ratio
        t_peak = cfg["peak_time"]
        sigma = cfg["spread"]

        curve = []
        for t in minutes:
            if t == 0:
                val = baseline
            elif t <= t_peak:
                val = baseline + amp * np.exp(-((t - t_peak) ** 2) / (2 * (sigma * 0.75) ** 2))
            else:
                val = baseline + amp * np.exp(-((t - t_peak) ** 2) / (2 * (sigma * 1.25) ** 2))
            curve.append(round(val, 1))

        for t, g in zip(minutes, curve):
            rows.append({"경과 시간(분)": t, "예상 혈당(mg/dL)": g, "먹는 순서": label})

    return pd.DataFrame(rows)


def generate_coaching_tips(selected_items: list[dict], metrics: dict, sequence_key: str) -> list[str]:
    tips = []
    categories = {item["분류"] for item in selected_items}

    if "채소·식이섬유" not in categories:
        tips.append("🥬 **채소 방어막 추가하기**: 식단에 채소·나물이 없어요! 밥 먹기 전 샐러드나 나물 반찬을 먼저 먹으면 당 흡수가 확 느려집니다.")
    if "단백질·지방" not in categories:
        tips.append("🥚 **단백질 짝꿍 추가하기**: 탄수화물만 먹으면 배도 금방 고프고 졸려요. 달걀, 두부, 고기·생선 반찬을 같이 곁들여 보세요.")
    if "음료·당류" in categories and metrics["effective_gl"] >= 14:
        tips.append("🥤 **액체 설탕 경보**: 달달한 음료는 씹는 과정 없이 혈관으로 직행해요! 물이나 무가당 차로 바꾸면 캐릭터가 다시 살아납니다.")
    if sequence_key != "거꾸로 식사법 (채소 → 고기/단백질 → 밥/면)":
        tips.append("⏱️ **순서만 바꿔도 절반은 성공**: 메뉴를 바꾸기 힘들다면 **채소 → 단백질 → 탄수화물** 순서로만 드셔보세요!")
    if metrics["char_state"] == "ko":
        tips.append("🚶 **긴급 처방! 식후 15분 산책**: 지금 혈당과 칼로리가 캐릭터를 쓰러뜨렸어요. 식사 후 15분만 걸어도 근육이 혈당을 쭉 흡수해 줍니다.")

    if not tips:
        tips.append("🎉 **완벽한 식단 밸런스**: 식이섬유·단백질 조합과 먹는 순서까지 나무랄 데가 없습니다!")
    return tips


# ---------------------------------------------------------
# 4. Session State 초기화
# ---------------------------------------------------------
if "meal_cart" not in st.session_state:
    st.session_state.meal_cart = []

if "condition_logs" not in st.session_state:
    st.session_state.condition_logs = []

# ---------------------------------------------------------
# 5. 상단 배너 & 캐릭터 선택 바 (3단 레이아웃)
# ---------------------------------------------------------
st.title("🩸 GLUCO-FLOW : 내 췌장 살리는 혈당 시뮬레이터")

top_c1, top_c2 = st.columns([1.4, 1.0], gap="medium")
with top_c1:
    st.markdown(
        '<div class="retro-marquee">📢 [긴급속보] 같은 밥을 먹어도 "채소 → 고기 → 밥" 순서로 먹으면 식곤증과 혈당 스파이크가 줄어듭니다!! 📢</div>',
        unsafe_allow_html=True,
    )
with top_c2:
    selected_char_name = st.selectbox(
        "🎭 내 혈당 상태를 연기할 캐릭터 고르기",
        list(CHARACTER_PROFILES.keys()),
    )

with st.expander("📖 잠깐! '혈당 출렁임 점수(유효 GL)'가 무슨 뜻인가요? (클릭해서 쉬운 설명 보기)", expanded=False):
    st.markdown("""
    ### 💡 어려운 의학 용어, 10초 만에 이해하기!
    * **혈당 스파이크란?** 음식을 먹은 뒤 핏속의 포도당(혈당)이 롤러코스터처럼 급격히 치솟았다가 뚝 떨어지는 현상이에요. 이때 **심한 식곤증(졸림), 집중력 저하, 금방 배고파짐**이 찾아옵니다.
    * **혈당 출렁임 점수 (의학 용어: 유효 GL)**란?
      * 음식의 종류뿐만 아니라 **내가 실제로 먹은 양**과 **먹는 순서**까지 합쳐서 *"이 한 끼가 내 혈당을 얼마나 크게 출렁이게 할까?"*를 점수로 나타낸 값이에요!
      * **11점 미만 (✨ 안정)**: 캐릭터가 춤추는 평온한 상태
      * **12 ~ 21점 (💦 주의)**: 캐릭터가 식은땀 흘리며 울먹이는 상태
      * **22점 이상 또는 1,100kcal 이상 (🚨 폭발·과식)**: 캐릭터가 기절해서 영혼이 빠져나가는 상태!
    """)

tab1, tab2, tab3 = st.tabs([
    "1️⃣ 식단 담기 & 캐릭터 반응 보기",
    "2️⃣ 식후 졸림·컨디션 일기장",
    "3️⃣ 생명과학 원리 (발표·탐구용)",
])

with tab1:
    col_food, col_char, col_result = st.columns([1.05, 0.95, 1.25], gap="medium")

    with col_food:
        st.subheader("🍽️ 1. 음식 담기")
        cat_filter = st.selectbox("음식 종류", ["전체"] + sorted(df_foods["분류"].unique().tolist()))
        search_query = st.text_input("음식 이름 검색 (예: 떡볶이, 비빔밥, 닭가슴살, 샐러드)")

        filtered_df = df_foods if cat_filter == "전체" else df_foods[df_foods["분류"] == cat_filter]
        if search_query.strip():
            filtered_df = filtered_df[filtered_df["식품명"].str.contains(search_query.strip(), case=False, na=False)]

        if filtered_df.empty:
            st.warning("찾는 음식이 없어요! 다른 단어로 검색해 보세요.")
        else:
            st.caption(f"검색된 음식: {len(filtered_df):,}개")
            selected_food_name = st.selectbox("목록에서 선택", filtered_df["식품명"].tolist())
            selected_row = filtered_df[filtered_df["식품명"] == selected_food_name].iloc[0]
            st.caption(
                f"기준량 {selected_row['기준량']} · {selected_row['열량(kcal)']}kcal · "
                f"탄수 {selected_row['탄수화물(g)']}g · 식이섬유 {selected_row['식이섬유(g)']}g"
            )
            portion = st.number_input("몇 인분(배수) 드셨나요?", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

            b1, b2 = st.columns(2)
            with b1:
                if st.button("➕ 식판에 추가", use_container_width=True):
                    item_dict = selected_row.to_dict()
                    item_dict["인분"] = float(portion)
                    st.session_state.meal_cart.append(item_dict)
                    st.rerun()
            with b2:
                if st.button("🗑️ 식판 비우기", use_container_width=True):
                    st.session_state.meal_cart = []
                    st.rerun()

        st.markdown("#### 🍱 현재 내 식판")
        if st.session_state.meal_cart:
            cart_df = pd.DataFrame(st.session_state.meal_cart)[
                ["식품명", "분류", "인분", "열량(kcal)", "탄수화물(g)", "식이섬유(g)"]
            ]
            st.dataframe(cart_df, use_container_width=True, hide_index=True)
        else:
            st.info("위에서 음식을 골라 '식판에 추가'를 눌러보세요!")

    with col_char:
        st.subheader("🎭 2. 캐릭터 실시간 상태")
        selected_seq = st.radio(
            "어떤 순서로 드실 건가요?",
            list(SEQUENCE_OPTIONS.keys()),
            index=1,
        )
        st.caption(SEQUENCE_OPTIONS[selected_seq]["desc"])

        char_info = CHARACTER_PROFILES[selected_char_name]
        if st.session_state.meal_cart:
            metrics = calculate_meal_metrics(st.session_state.meal_cart, selected_seq)
            current_state = metrics["char_state"]
        else:
            metrics = None
            current_state = "happy"

        svg_code = render_character_svg(char_info["key"], current_state)
        speech_text = (
            "아직 식판이 비어있어! 음식을 담아주면 내 반응을 보여줄게~"
            if not metrics
            else char_info[current_state]
        )

        st.markdown(
            f"""
            <div class="char-stage">
                {svg_code}
                <div class="char-speech">“{speech_text}”</div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with col_result:
        st.subheader("📈 3. 혈당 출렁임 분석")
        if not metrics:
            st.warning("식판에 음식을 1개 이상 담으면 혈당 그래프와 처방전이 나타납니다!")
        else:
            m1, m2 = st.columns(2)
            m1.metric("총 섭취 칼로리", f"{metrics['total_kcal']} kcal")
            m2.metric("혈당 출렁임 점수 (유효 GL)", f"{metrics['effective_gl']} 점", metrics["risk_label"])

            m3, m4 = st.columns(2)
            m3.metric("식후 최고 예상 혈당", f"{metrics['peak_glucose']} mg/dL", f"평소보다 +{metrics['delta_glucose']}")
            m4.metric("순탄수화물 / 식이섬유", f"{metrics['net_carb']}g / {metrics['total_fiber']}g")

            order_priority = {"채소·식이섬유": 1, "단백질·지방": 2, "탄수화물": 3, "음료·당류": 4}
            sorted_items = sorted(st.session_state.meal_cart, key=lambda x: order_priority.get(x["분류"], 5))
            rec_seq = " → ".join([f"{i['식품명']}" for i in sorted_items])
            st.success(f"🥢 **추천 먹는 순서:** {rec_seq}")

            curve_df = simulate_glucose_curve(metrics, selected_seq)
            chart = (
                alt.Chart(curve_df)
                .mark_line(strokeWidth=3.5)
                .encode(
                    x=alt.X("경과 시간(분):Q", title="식사 후 시간 (분)"),
                    y=alt.Y("예상 혈당(mg/dL):Q", scale=alt.Scale(domain=[80, 220]), title="예상 혈당 (mg/dL)"),
                    color=alt.Color("먹는 순서:N", legend=alt.Legend(orient="bottom", title=None)),
                    tooltip=["먹는 순서", "경과 시간(분)", "예상 혈당(mg/dL)"],
                )
                .properties(height=270, title="먹는 순서별 식후 3시간 혈당 롤러코스터 비교")
            )
            st.altair_chart(chart, use_container_width=True)

            st.markdown("#### 🩺 캐릭터 살리는 맞춤 처방")
            for tip in generate_coaching_tips(st.session_state.meal_cart, metrics, selected_seq):
                st.markdown(f"- {tip}")

with tab2:
    st.subheader("📝 식후 졸림 & 컨디션 일기장")
    st.write("실제로 밥을 먹은 뒤 졸렸는지, 멀쩡했는지 기록해서 나에게 맞는 식사 순서를 찾아보세요!")

    with st.form("log_form"):
        c1, c2, c3 = st.columns(3)
        log_date = c1.date_input("날짜", value=date.today())
        meal_time = c2.selectbox("끼니", ["아침", "점심", "저녁", "간식"])
        post_symptom = c3.selectbox(
            "먹고 난 뒤 내 상태",
            ["머리 맑고 집중 잘됨 ✨", "살짝 노곤함 🥱", "눈꺼풀 천근만근·기절 직전 😴", "먹은 지 얼마 안 돼서 또 배고픔 🍪"],
        )
        memo = st.text_input("한 줄 메모 (예: 채소 반찬 먼저 다 먹고 밥 먹음)")
        submitted = st.form_submit_button("일기 저장하기")

        if submitted:
            if not st.session_state.meal_cart:
                st.error("먼저 1번 탭 식판에 음식을 담아주세요!")
            else:
                curr_metrics = calculate_meal_metrics(st.session_state.meal_cart, selected_seq)
                menu_summary = ", ".join([f"{x['식품명']}x{x['인분']}" for x in st.session_state.meal_cart])
                st.session_state.condition_logs.append({
                    "날짜": str(log_date),
                    "끼니": meal_time,
                    "먹은 메뉴": menu_summary,
                    "식사 순서": selected_seq.split(" (")[0],
                    "출렁임 점수(GL)": curr_metrics["effective_gl"],
                    "캐릭터 상태": curr_metrics["risk_label"],
                    "실제 몸 반응": post_symptom,
                    "메모": memo,
                })
                st.success("일기가 저장되었습니다!")

    if st.session_state.condition_logs:
        st.dataframe(pd.DataFrame(st.session_state.condition_logs), use_container_width=True, hide_index=True)
    else:
        st.info("아직 작성된 일기가 없습니다. 1번 탭에서 식단을 고른 뒤 기록해 보세요.")

with tab3:
    st.subheader("🔬 생명과학 원리 & 수식 해설 (심화탐구용)")
    st.markdown("""
    1. **순탄수화물과 혈당부하지수(GL)**
       - 식품의 혈당지수(GI)에 실제 섭취량(순탄수화물)을 반영한 지표가 **혈당부하지수(GL)**입니다.
       $$GL = \\frac{GI \\times \\text{순탄수화물(g)}}{100}$$
       - 식이섬유는 인체 소화 효소로 분해되지 않으므로 총 탄수화물에서 제외하여 순탄수화물($\\text{총 탄수화물} - \\text{식이섬유}$)을 계산합니다.

    2. **거꾸로 식사법(Meal Sequencing)의 생리학적 기전**
       - **위 배출 지연(Delayed Gastric Emptying)**: 단백질과 지방은 십이지장에서 **콜레시스토키닌(CCK)**과 **GLP-1** 분비를 촉진해 위에서 소장으로 음식물이 넘어가는 속도를 늦춥니다.
       - **소장 내 확산 장벽**: 수용성 식이섬유가 수분과 결합해 점성 겔(Gel)을 형성하면, 소화 효소의 접근과 소장 융모에서의 포도당 흡수 속도가 완만해집니다.
       - **인슐린 스파이크 완화**: 혈당이 완만하게 오르면 이자(췌장)의 $\\beta$세포에서 인슐린이 과도하게 분비되는 현상을 줄여 식후 졸림(반응성 저혈당)을 예방할 수 있습니다.
    """)
