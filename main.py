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
# 1. 기본 식품 영양 & 혈당지수(GI) 데이터베이스
#    (100g 기준 영양성분 및 문헌 기반 대표 GI 값)
# ---------------------------------------------------------
FOOD_DATA = [
    # 채소 / 해조류 / 식이섬유 (Fiber)
    {"식품명": "양배추 샐러드(무가당)", "분류": "채소·식이섬유", "중량(g)": 100, "열량(kcal)": 24, "탄수화물(g)": 5.2, "식이섬유(g)": 2.5, "단백질(g)": 1.3, "지방(g)": 0.1, "GI": 15},
    {"식품명": "브로콜리(데친 것)", "분류": "채소·식이섬유", "중량(g)": 100, "열량(kcal)": 35, "탄수화물(g)": 7.2, "식이섬유(g)": 3.3, "단백질(g)": 2.4, "지방(g)": 0.4, "GI": 15},
    {"식품명": "미역국(건더기 위주)", "분류": "채소·식이섬유", "중량(g)": 250, "열량(kcal)": 45, "탄수화물(g)": 4.0, "식이섬유(g)": 2.8, "단백질(g)": 3.2, "지방(g)": 1.5, "GI": 18},
    {"식품명": "시금치나물", "분류": "채소·식이섬유", "중량(g)": 70, "열량(kcal)": 42, "탄수화물(g)": 3.1, "식이섬유(g)": 2.2, "단백질(g)": 2.5, "지방(g)": 2.1, "GI": 15},
    {"식품명": "방울토마토", "분류": "채소·식이섬유", "중량(g)": 100, "열량(kcal)": 18, "탄수화물(g)": 3.9, "식이섬유(g)": 1.2, "단백질(g)": 0.9, "지방(g)": 0.2, "GI": 30},

    # 단백질 / 건강한 지방 (Protein & Fat)
    {"식품명": "닭가슴살 구이", "분류": "단백질·지방", "중량(g)": 100, "열량(kcal)": 165, "탄수화물(g)": 0.0, "식이섬유(g)": 0.0, "단백질(g)": 31.0, "지방(g)": 3.6, "GI": 0},
    {"식품명": "삶은 달걀 (2개)", "분류": "단백질·지방", "중량(g)": 100, "열량(kcal)": 155, "탄수화물(g)": 1.1, "식이섬유(g)": 0.0, "단백질(g)": 12.6, "지방(g)": 10.6, "GI": 0},
    {"식품명": "두부 부침", "분류": "단백질·지방", "중량(g)": 100, "열량(kcal)": 145, "탄수화물(g)": 3.5, "식이섬유(g)": 1.4, "단백질(g)": 12.0, "지방(g)": 9.2, "GI": 15},
    {"식품명": "고등어 구이", "분류": "단백질·지방", "중량(g)": 100, "열량(kcal)": 262, "탄수화물(g)": 0.0, "식이섬유(g)": 0.0, "단백질(g)": 24.0, "지방(g)": 18.0, "GI": 0},
    {"식품명": "그릭요거트(무가당)", "분류": "단백질·지방", "중량(g)": 100, "열량(kcal)": 95, "탄수화물(g)": 4.0, "식이섬유(g)": 0.0, "단백질(g)": 10.0, "지방(g)": 4.5, "GI": 14},
    {"식품명": "아몬드 한 줌", "분류": "단백질·지방", "중량(g)": 25, "열량(kcal)": 145, "탄수화물(g)": 5.4, "식이섬유(g)": 3.1, "단백질(g)": 5.3, "지방(g)": 12.5, "GI": 15},

    # 탄수화물 주식 (Carbohydrate)
    {"식품명": "흰쌀밥 (1공기)", "분류": "탄수화물", "중량(g)": 210, "열량(kcal)": 300, "탄수화물(g)": 65.5, "식이섬유(g)": 0.8, "단백질(g)": 5.2, "지방(g)": 0.6, "GI": 73},
    {"식품명": "현미잡곡밥 (1공기)", "분류": "탄수화물", "중량(g)": 210, "열량(kcal)": 285, "탄수화물(g)": 60.0, "식이섬유(g)": 3.8, "단백질(g)": 6.5, "지방(g)": 1.8, "GI": 55},
    {"식품명": "식빵 (2장)", "분류": "탄수화물", "중량(g)": 70, "열량(kcal)": 185, "탄수화물(g)": 34.0, "식이섬유(g)": 1.5, "단백질(g)": 5.8, "지방(g)": 2.6, "GI": 75},
    {"식품명": "라면 (1봉지)", "분류": "탄수화물", "중량(g)": 120, "열량(kcal)": 500, "탄수화물(g)": 78.0, "식이섬유(g)": 2.4, "단백질(g)": 10.0, "지방(g)": 16.0, "GI": 73},
    {"식품명": "삶은 고구마 (중 1개)", "분류": "탄수화물", "중량(g)": 150, "열량(kcal)": 195, "탄수화물(g)": 45.0, "식이섬유(g)": 4.5, "단백질(g)": 2.4, "지방(g)": 0.3, "GI": 54},
    {"식품명": "떡볶이 (1인분)", "분류": "탄수화물", "중량(g)": 200, "열량(kcal)": 380, "탄수화물(g)": 76.0, "식이섬유(g)": 1.8, "단백질(g)": 7.5, "지방(g)": 4.5, "GI": 82},

    # 음료 / 디저트 (Beverage & Sugar)
    {"식품명": "가당 카페라떼/밀크티", "분류": "음료·당류", "중량(g)": 350, "열량(kcal)": 220, "탄수화물(g)": 32.0, "식이섬유(g)": 0.0, "단백질(g)": 6.0, "지방(g)": 7.0, "GI": 68},
    {"식품명": "탄산음료 (1캔)", "분류": "음료·당류", "중량(g)": 250, "열량(kcal)": 108, "탄수화물(g)": 27.0, "식이섬유(g)": 0.0, "단백질(g)": 0.0, "지방(g)": 0.0, "GI": 63},
    {"식품명": "아메리카노/물/무가당 차", "분류": "음료·당류", "중량(g)": 300, "열량(kcal)": 5, "탄수화물(g)": 0.5, "식이섬유(g)": 0.0, "단백질(g)": 0.2, "지방(g)": 0.0, "GI": 0},
]

df_foods = pd.DataFrame(FOOD_DATA)

# ---------------------------------------------------------
# 2. 생리학 기반 혈당 부하(GL) 및 예측 곡선 모델 함수
# ---------------------------------------------------------
SEQUENCE_OPTIONS = {
    "탄수화물·음료 먼저 섭취 (혈당 급상승 패턴)": {
        "peak_multiplier": 1.15,
        "peak_time": 35,
        "spread": 22,
        "desc": "공복 상태에서 정제 탄수화물·액상 당류가 소장에 빠르게 도달하여 포도당 흡수와 인슐린 급분비를 유발합니다."
    },
    "일반적인 혼합 섭취 (반찬과 밥을 함께)": {
        "peak_multiplier": 1.00,
        "peak_time": 45,
        "spread": 28,
        "desc": "탄수화물과 부식이 섞여 소화되며 표준적인 식후 혈당 상승 곡선을 보입니다."
    },
    "거꾸로 식사법 (채소/식이섬유 → 단백질/지방 → 탄수화물)": {
        "peak_multiplier": 0.72,
        "peak_time": 60,
        "spread": 38,
        "desc": "식이섬유가 장 점막에 점성 장벽을 형성하고 단백질·지방이 위 배출 속도를 늦춰 혈당 피크를 약 25~30% 완화합니다."
    },
}


def calculate_meal_metrics(selected_items: list[dict], sequence_key: str) -> dict:
    """선택된 음식 목록과 식사 순서를 바탕으로 영양 합계, 유효 GL, 혈당 피크 예측치를 계산합니다."""
    if not selected_items:
        return {}

    total_kcal = sum(item["열량(kcal)"] * item["인분"] for item in selected_items)
    total_carb = sum(item["탄수화물(g)"] * item["인분"] for item in selected_items)
    total_fiber = sum(item["식이섬유(g)"] * item["인분"] for item in selected_items)
    total_protein = sum(item["단백질(g)"] * item["인분"] for item in selected_items)
    total_fat = sum(item["지방(g)"] * item["인분"] for item in selected_items)

    # 순탄수화물 = 총 탄수화물 - 식이섬유 (최소 0)
    net_carb = max(0.0, total_carb - total_fiber)

    # 개별 음식의 혈당부하지수(GL) 합산: GL = (GI * 순탄수화물) / 100
    raw_gl = 0.0
    for item in selected_items:
        item_net_carb = max(0.0, (item["탄수화물(g)"] - item["식이섬유(g)"]) * item["인분"])
        raw_gl += (item["GI"] * item_net_carb) / 100.0

    # 동시 섭취된 식이섬유·단백질·지방에 의한 위 배출 지연 완충 계수 (최대 25% 완화)
    buffer_score = min(0.25, (total_fiber * 0.018) + (total_protein * 0.004) + (total_fat * 0.003))
    seq_factor = SEQUENCE_OPTIONS[sequence_key]["peak_multiplier"]

    effective_gl = round(raw_gl * (1.0 - buffer_score) * seq_factor, 1)

    # 공복 기준 혈당 90 mg/dL 가정 시 예상 최고 혈당 상승폭(Δmg/dL) 추정
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
    """식후 0~180분 동안의 예상 혈당 변화 곡선 데이터를 생성합니다."""
    minutes = np.arange(0, 185, 5)
    baseline = 90.0

    # 비교를 위해 '탄수화물 먼저 섭취' vs '선택한 순서' vs '거꾸로 식사법' 3가지 곡선 생성
    rows = []
    for label, cfg in SEQUENCE_OPTIONS.items():
        # 선택된 순서 대비 비율 조정
        ratio = cfg["peak_multiplier"] / SEQUENCE_OPTIONS[sequence_key]["peak_multiplier"]
        amp = metrics["delta_glucose"] * ratio
        t_peak = cfg["peak_time"]
        sigma = cfg["spread"]

        # 비대칭 가우시안 형태로 상승 및 인슐린에 의한 하강 모사
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
    """생리학적 근거에 기반한 식사 개선 코칭 메시지를 반환합니다."""
    tips = []
    categories = {item["분류"] for item in selected_items}

    if "채소·식이섬유" not in categories:
        tips.append("🥬 **식이섬유 선섭취 추가**: 현재 식단에 채소·해조류가 없습니다. 식사 전 양배추·브로콜리·미역 등 수용성 식이섬유를 1접시 먼저 먹으면 소장 내 포도당 확산 속도를 늦출 수 있습니다.")
    if "단백질·지방" not in categories:
        tips.append("🥚 **단백질·지방 보완**: 탄수화물 위주 식사는 위 배출이 빨라 혈당 스파이크를 유발합니다. 달걀, 두부, 닭가슴살, 견과류를 곁들여 인크레틴(GLP-1) 분비와 포만감을 높이세요.")
    if any(item["식품명"] in ["가당 카페라떼/밀크티", "탄산음료 (1캔)"] for item in selected_items):
        tips.append("🥤 **액상 과당 주의**: 액체 형태의 당류는 소화 과정 없이 소장에서 즉시 흡수됩니다. 물, 탄산수, 무가당 차로 대체하면 유효 GL을 크게 낮출 수 있습니다.")
    if sequence_key != "거꾸로 식사법 (채소/식이섬유 → 단백질/지방 → 탄수화물)":
        tips.append("⏱️ **섭취 순서 변경 권장**: 메뉴를 바꾸기 어렵다면 먹는 순서만 **채소 → 단백질/지방 → 탄수화물** 순으로 바꾸어도 예상 혈당 피크를 약 25% 이상 완충할 수 있습니다.")
    if metrics["effective_gl"] >= 20:
        tips.append("🚶 **식후 15분 가벼운 걷기**: 식사 후 15~30분 사이 가볍게 걸으면 인슐린 비의존적 포도당 수송체(GLUT4)가 활성화되어 골격근이 혈중 포도당을 빠르게 흡수합니다.")

    if not tips:
        tips.append("✅ **균형 잡힌 저혈당 부하 식단**: 식이섬유·단백질 비율과 섭취 순서가 모두 이상적입니다. 현재 구성을 유지해 보세요!")
    return tips


# ---------------------------------------------------------
# 3. Session State 초기화
# ---------------------------------------------------------
if "meal_cart" not in st.session_state:
    st.session_state.meal_cart = [
        {"식품명": "흰쌀밥 (1공기)", "분류": "탄수화물", "중량(g)": 210, "열량(kcal)": 300, "탄수화물(g)": 65.5, "식이섬유(g)": 0.8, "단백질(g)": 5.2, "지방(g)": 0.6, "GI": 73, "인분": 1.0},
        {"식품명": "닭가슴살 구이", "분류": "단백질·지방", "중량(g)": 100, "열량(kcal)": 165, "탄수화물(g)": 0.0, "식이섬유(g)": 0.0, "단백질(g)": 31.0, "지방(g)": 3.6, "GI": 0, "인분": 1.0},
    ]

if "condition_logs" not in st.session_state:
    st.session_state.condition_logs = []

# ---------------------------------------------------------
# 4. UI 구성
# ---------------------------------------------------------
st.title("🧬 GLUCO-FLOW : 혈당 스파이크 예측 & 식사 순서 코치")
st.caption("같은 칼로리라도 '무엇을, 어떤 순서로' 먹느냐에 따라 인체의 혈당·인슐린 반응이 달라집니다.")

tab1, tab2, tab3 = st.tabs([
    "1️⃣ 식단 조합 & 혈당 시뮬레이터",
    "2️⃣ 식후 컨디션 & 혈당 로그",
    "3️⃣ 생명과학 원리 & 수식 해설",
])

with tab1:
    col_left, col_right = st.columns([1.05, 1.35], gap="large")

    with col_left:
        st.subheader("🍽️ 한 끼 식단 구성하기")
        cat_filter = st.selectbox("식품 분류 선택", ["전체"] + list(df_foods["분류"].unique()))
        filtered_df = df_foods if cat_filter == "전체" else df_foods[df_foods["분류"] == cat_filter]

        selected_food_name = st.selectbox("음식 선택", filtered_df["식품명"].tolist())
        portion = st.number_input("섭취량 (인분/기준 단위 배수)", min_value=0.5, max_value=3.0, value=1.0, step=0.5)

        btn_c1, btn_c2 = st.columns(2)
        with btn_c1:
            if st.button("➕ 식단에 추가", use_container_width=True):
                row = df_foods[df_foods["식품명"] == selected_food_name].iloc[0].to_dict()
                row["인분"] = portion
                st.session_state.meal_cart.append(row)
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
            st.info("왼쪽에서 음식을 추가해 한 끼 식단을 구성해 보세요.")

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
            st.warning("분석할 음식이 없습니다. 최소 1개 이상의 음식을 추가해 주세요.")
        else:
            metrics = calculate_meal_metrics(st.session_state.meal_cart, selected_seq)

            m1, m2, m3, m4 = st.columns(4)
            m1.metric("총 열량", f"{metrics['total_kcal']} kcal")
            m2.metric("유효 혈당부하(GL)", f"{metrics['effective_gl']}", f"기본 GL {metrics['raw_gl']}")
            m3.metric("예상 최고 혈당", f"{metrics['peak_glucose']} mg/dL", f"+{metrics['delta_glucose']} mg/dL", delta_color="inverse")
            m4.metric("혈당 위험도", metrics["risk_level"])

            # 권장 식사 순서 자동 정렬 제안
            order_priority = {"채소·식이섬유": 1, "단백질·지방": 2, "탄수화물": 3, "음료·당류": 4}
            sorted_items = sorted(st.session_state.meal_cart, key=lambda x: order_priority.get(x["분류"], 5))
            recommended_order_str = " → ".join([f"{i['식품명']}({i['분류'].split('·')[0]})" for i in sorted_items])
            st.success(f"**권장 섭취 순서 시퀀스:** {recommended_order_str}")

            # Altair 혈당 곡선 비교 차트
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
       - 식품의 혈당지수(GI)는 탄수화물 50g을 섭취했을 때의 상대적 혈당 상승 속도를 의미하며, 실제 섭취량을 반영하기 위해 **혈당부하지수(GL)**를 사용합니다.
       $$GL = \\frac{GI \\times \\text{순탄수화물(g)}}{100}$$
       - 이때 식이섬유는 인체 소화 효소로 분해되지 않으므로 총 탄수화물에서 제외하여 순탄수화물($\\text{총 탄수화물} - \\text{식이섬유}$)을 계산합니다.

    2. **거꾸로 식사법(Meal Sequencing)의 생리학적 기전**
       - **위 배출 지연(Delayed Gastric Emptying)**: 단백질과 지방은 십이지장에서 **콜레시스토키닌(CCK)**과 **GLP-1** 분비를 촉진해 위에서 소장으로 음식물이 넘어가는 속도를 늦춥니다.
       - **소장 내 확산 장벽**: 수용성 식이섬유가 수분과 결합해 점성 겔(Gel)을 형성하면, 아밀레이스 등 탄수화물 소화 효소의 접근과 소장 융모에서의 포도당 흡수 속도가 완만해집니다.
       - **인슐린 스파이크 완화**: 혈중 포도당 농도가 완만하게 상승하면 이자(췌장)의 $\\beta$세포에서 인슐린이 과도하게 급분비되는 현상을 줄여, 이후 발생하는 반응성 저혈당(식곤증·허기)을 예방할 수 있습니다.
    """)
