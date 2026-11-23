import os
import streamlit as st
import pandas as pd
import numpy as np
import altair as alt
from datetime import date

st.set_page_config(
    page_title="GLUCO-FLOW | 혈당 스파이크 & 식사 순서 코치",
    page_icon="🧬",
    layout="wide",
)

# ---------------------------------------------------------
# 1. 정제된 공공 식품 DB 로드 (foods_gluco_db.csv)
# ---------------------------------------------------------
FALLBACK_FOODS = [
    {"식품명": "흰쌀밥 (1공기)", "분류": "탄수화물", "원본분류": "밥류", "기준량": "100g", "열량(kcal)": 143.0, "탄수화물(g)": 31.2, "식이섬유(g)": 0.4, "당류(g)": 0.0, "단백질(g)": 2.5, "지방(g)": 0.3, "GI": 73},
    {"식품명": "닭가슴살 구이", "분류": "단백질·지방", "원본분류": "구이류", "기준량": "100g", "열량(kcal)": 165.0, "탄수화물(g)": 0.0, "식이섬유(g)": 0.0, "당류(g)": 0.0, "단백질(g)": 31.0, "지방(g)": 3.6, "GI": 25},
    {"식품명": "양배추 샐러드", "분류": "채소·식이섬유", "원본분류": "생채·무침류", "기준량": "100g", "열량(kcal)": 24.0, "탄수화물(g)": 5.2, "식이섬유(g)": 2.5, "당류(g)": 2.0, "단백질(g)": 1.3, "지방(g)": 0.1, "GI": 18},
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
# 2. 생리학 기반 혈당 부하(GL) 및 예측 곡선 모델 함수
# ---------------------------------------------------------
SEQUENCE_OPTIONS = {
    "탄수화물·음료 먼저 섭취 (혈당 급상승 패턴)": {
        "peak_multiplier": 1.15,
        "peak_time": 35,
        "spread": 22,
        "desc": "공복 상태에서 정제 탄수화물·액상 당류가 소장에 빠르게 도달하여 포도당 흡수와 인슐린 급분비를 유발합니다.",
    },
    "일반적인 혼합 섭취 (반찬과 밥을 함께)": {
        "peak_multiplier": 1.00,
        "peak_time": 45,
        "spread": 28,
        "desc": "탄수화물과 부식이 섞여 소화되며 표준적인 식후 혈당 상승 곡선을 보입니다.",
    },
    "거꾸로 식사법 (채소/식이섬유 → 단백질/지방 → 탄수화물)": {
        "peak_multiplier": 0.72,
        "peak_time": 60,
        "spread": 38,
        "desc": "식이섬유가 장 점막에 점성 장벽을 형성하고 단백질·지방이 위 배출 속도를 늦춰 혈당 피크를 약 25~30% 완화합니다.",
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

    if effective_gl < 11:
        risk_level = "안정 (Low GL)"
    elif effective_gl < 20:
        risk_level = "주의 (Medium GL)"
    else:
        risk_level = "스파이크 위험 (High GL)"

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
        "risk_level": risk_level,
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
            rows.append({"경과 시간(분)": t, "예상 혈당(mg/dL)": g, "섭취 방식": label})

    return pd.DataFrame(rows)


def generate_coaching_tips(selected_items: list[dict], metrics: dict, sequence_key: str) -> list[str]:
    tips = []
    categories = {item["분류"] for item in selected_items}

    if "채소·식이섬유" not in categories:
        tips.append("🥬 **식이섬유 선섭취 추가**: 채소·나물·김치 등 식이섬유 메뉴를 먼저 먹으면 소장 내 포도당 흡수 속도를 늦추는 데 도움이 됩니다.")
    if "단백질·지방" not in categories:
        tips.append("🥚 **단백질·지방 보완**: 구이·조림·찜·두부·달걀 등 단백질 반찬을 곁들이면 위 배출 속도와 포만감 유지에 유리합니다.")
    if "음료·당류" in categories and metrics["effective_gl"] >= 15:
        tips.append("🥤 **당류 음료 주의**: 당류가 포함된 음료는 혈당을 빠르게 올릴 수 있으므로 무가당 음료나 물로 대체해 보세요.")
    if sequence_key != "거꾸로 식사법 (채소/식이섬유 → 단백질/지방 → 탄수화물)":
        tips.append("⏱️ **섭취 순서 변경 권장**: 채소 → 단백질/지방 → 탄수화물 순으로 먹으면 예상 혈당 피크를 낮출 수 있습니다.")
    if metrics["effective_gl"] >= 20:
        tips.append("🚶 **식후 가벼운 움직임**: 식사 후 10~15분 정도 가볍게 걸으면 혈중 포도당 활용에 도움이 됩니다.")

    if not tips:
        tips.append("✅ **균형 잡힌 구성**: 식이섬유·단백질 조합과 섭취 순서가 비교적 안정적입니다.")
    return tips


# ---------------------------------------------------------
# 3. Session State 초기화
# ---------------------------------------------------------
if "meal_cart" not in st.session_state:
    st.session_state.meal_cart = []

if "condition_logs" not in st.session_state:
    st.session_state.condition_logs = []

# ---------------------------------------------------------
# 4. UI 구성
# ---------------------------------------------------------
st.title("🧬 GLUCO-FLOW : 혈당 스파이크 예측 & 식사 순서 코치")
st.caption(f"공공 식품 영양 DB 기반 ({len(df_foods):,}개 음식) · 식사 순서와 영양소 조합에 따른 혈당 변동 시뮬레이션")

tab1, tab2, tab3 = st.tabs([
    "1️⃣ 식단 조합 & 혈당 시뮬레이터",
    "2️⃣ 식후 컨디션 & 혈당 로그",
    "3️⃣ 생명과학 원리 & 수식 해설",
])

with tab1:
    col_left, col_right = st.columns([1.05, 1.35], gap="large")

    with col_left:
        st.subheader("🍽️ 한 끼 식단 구성하기")
        cat_filter = st.selectbox("식품 분류 선택", ["전체"] + sorted(df_foods["분류"].unique().tolist()))
        search_query = st.text_input("음식명 검색 (예: 비빔밥, 라면, 아메리카노, 두부)")

        filtered_df = df_foods if cat_filter == "전체" else df_foods[df_foods["분류"] == cat_filter]
        if search_query.strip():
            filtered_df = filtered_df[filtered_df["식품명"].str.contains(search_query.strip(), case=False, na=False)]

        if filtered_df.empty:
            st.warning("검색 조건에 맞는 음식이 없습니다. 검색어를 바꿔 보세요.")
        else:
            st.caption(f"검색 결과: {len(filtered_df):,}개")
            selected_food_name = st.selectbox("음식 선택", filtered_df["식품명"].tolist())
            selected_row = filtered_df[filtered_df["식품명"] == selected_food_name].iloc[0]
            st.caption(
                f"기준량: {selected_row['기준량']} | 열량: {selected_row['열량(kcal)']}kcal | "
                f"탄수화물: {selected_row['탄수화물(g)']}g | 식이섬유: {selected_row['식이섬유(g)']}g | "
                f"단백질: {selected_row['단백질(g)']}g | 추정 GI: {int(selected_row['GI'])}"
            )
            portion = st.number_input("섭취량 (기준량 배수)", min_value=0.5, max_value=5.0, value=1.0, step=0.5)

            btn_c1, btn_c2 = st.columns(2)
            with btn_c1:
                if st.button("➕ 식단에 추가", use_container_width=True):
                    item_dict = selected_row.to_dict()
                    item_dict["인분"] = float(portion)
                    st.session_state.meal_cart.append(item_dict)
                    st.rerun()
            with btn_c2:
                if st.button("🗑️ 식단 초기화", use_container_width=True):
                    st.session_state.meal_cart = []
                    st.rerun()

        st.markdown("#### 현재 담긴 한 끼 메뉴")
        if st.session_state.meal_cart:
            cart_df = pd.DataFrame(st.session_state.meal_cart)[
                ["식품명", "분류", "인분", "열량(kcal)", "탄수화물(g)", "식이섬유(g)", "단백질(g)", "GI"]
            ]
            st.dataframe(cart_df, use_container_width=True, hide_index=True)
        else:
            st.info("왼쪽에서 음식을 검색·선택한 뒤 '식단에 추가'를 눌러보세요.")

        st.markdown("#### ⏱️ 식사 순서 선택")
        selected_seq = st.radio(
            "어떤 순서로 드실 예정인가요?",
            list(SEQUENCE_OPTIONS.keys()),
            index=1,
        )
        st.caption(SEQUENCE_OPTIONS[selected_seq]["desc"])

    with col_right:
        st.subheader("📈 예상 혈당 반응 & 코칭 결과")
        if not st.session_state.meal_cart:
            st.warning("분석할 음식이 없습니다. 최소 1개 이상의 음식을 식단에 추가해 주세요.")
        else:
            metrics = calculate_meal_metrics(st.session_state.meal_cart, selected_seq)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("총 열량", f"{metrics['total_kcal']} kcal")
            m2.metric("유효 혈당부하(GL)", f"{metrics['effective_gl']}", f"기본 GL {metrics['raw_gl']}")
            m3.metric("예상 최고 혈당", f"{metrics['peak_glucose']} mg/dL", f"+{metrics['delta_glucose']} mg/dL", delta_color="inverse")
            m4.metric("혈당 위험도", metrics["risk_level"])

            order_priority = {"채소·식이섬유": 1, "단백질·지방": 2, "탄수화물": 3, "음료·당류": 4}
            sorted_items = sorted(st.session_state.meal_cart, key=lambda x: order_priority.get(x["분류"], 5))
            recommended_order_str = " → ".join([f"{i['식품명']}({i['분류'].split('·')[0]})" for i in sorted_items])
            st.success(f"**권장 섭취 순서 시퀀스:** {recommended_order_str}")

            curve_df = simulate_glucose_curve(metrics, selected_seq)
            chart = (
                alt.Chart(curve_df)
                .mark_line(strokeWidth=3)
                .encode(
                    x=alt.X("경과 시간(분):Q", title="식사 후 경과 시간 (분)"),
                    y=alt.Y("예상 혈당(mg/dL):Q", scale=alt.Scale(domain=[80, 210]), title="예상 혈당 농도 (mg/dL)"),
                    color=alt.Color("섭취 방식:N", legend=alt.Legend(orient="bottom", title=None)),
                    tooltip=["섭취 방식", "경과 시간(분)", "예상 혈당(mg/dL)"],
                )
                .properties(height=320, title="섭취 순서에 따른 식후 3시간 혈당 변동 시뮬레이션")
            )
            st.altair_chart(chart, use_container_width=True)

            st.markdown("#### 💡 맞춤형 생리학 코칭")
            for tip in generate_coaching_tips(st.session_state.meal_cart, metrics, selected_seq):
                st.markdown(f"- {tip}")

with tab2:
    st.subheader("📝 식후 컨디션 & 혈당 반응 기록장")
    st.write("실제 식사 후 졸림, 집중력 저하, 허기짐 등 인체 반응을 기록해 나만의 혈당 반응 패턴을 확인하세요.")

    with st.form("log_form"):
        c1, c2, c3 = st.columns(3)
        log_date = c1.date_input("날짜", value=date.today())
        meal_time = c2.selectbox("끼니", ["아침", "점심", "저녁", "간식"])
        post_symptom = c3.selectbox(
            "식후 1~2시간 체감 반응",
            ["컨디션 쾌적·집중 잘됨", "약간 나른함", "심한 식곤증·졸림 (스파이크 의심)", "금방 허기짐·단 음식 당김"],
        )
        memo = st.text_input("메모 (예: 채소 먼저 먹고 15분 산책함)")
        submitted = st.form_submit_button("기록 저장하기")

        if submitted:
            if not st.session_state.meal_cart:
                st.error("먼저 1번 탭에서 식단을 구성해 주세요.")
            else:
                curr_metrics = calculate_meal_metrics(st.session_state.meal_cart, selected_seq)
                menu_summary = ", ".join([f"{x['식품명']}x{x['인분']}" for x in st.session_state.meal_cart])
                st.session_state.condition_logs.append({
                    "날짜": str(log_date),
                    "끼니": meal_time,
                    "구성 메뉴": menu_summary,
                    "섭취 순서": selected_seq.split(" (")[0],
                    "유효 GL": curr_metrics["effective_gl"],
                    "예상 피크(mg/dL)": curr_metrics["peak_glucose"],
                    "식후 반응": post_symptom,
                    "메모": memo,
                })
                st.success("식단과 식후 반응이 기록되었습니다!")

    if st.session_state.condition_logs:
        st.dataframe(pd.DataFrame(st.session_state.condition_logs), use_container_width=True, hide_index=True)
    else:
        st.info("아직 저장된 기록이 없습니다. 식단을 구성한 뒤 위 양식으로 기록을 남겨보세요.")

with tab3:
    st.subheader("🔬 탐구 배경: 왜 식사 순서와 조합이 혈당을 바꿀까?")
    st.markdown("""
    1. **순탄수화물과 혈당부하지수(GL)**
       - 실제 섭취량을 반영한 혈당부하지수(GL)는 $GL = \\frac{GI \\times \\text{순탄수화물(g)}}{100}$ 으로 계산합니다.
       - 식이섬유는 소화 효소로 분해되지 않으므로 총 탄수화물에서 제외하여 순탄수화물($\\text{총 탄수화물} - \\text{식이섬유}$)을 구합니다.

    2. **거꾸로 식사법(Meal Sequencing)의 생리학적 기전**
       - **위 배출 지연**: 단백질·지방과 식이섬유가 위에서 소장으로 넘어가는 속도를 늦추고 소화 효소 작용 및 포도당 흡수 속도를 완만하게 만듭니다.
       - **인슐린 스파이크 완화**: 혈당이 급격히 치솟았다가 떨어지는 변동을 줄여 식후 졸림과 갑작스러운 허기짐을 완화하는 데 도움을 줍니다.
    """)
