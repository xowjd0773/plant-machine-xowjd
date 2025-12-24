import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from pathlib import Path
import unicodedata
import io

# ===============================
# 기본 설정
# ===============================
st.set_page_config(
    page_title="극지식물 최적 EC 농도 연구",
    layout="wide"
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# ===============================
# 파일 유틸 (NFC/NFD 대응)
# ===============================
def norm(text):
    return unicodedata.normalize("NFC", text)

def find_file(dir_path, filename):
    for p in dir_path.iterdir():
        if norm(p.name) == norm(filename):
            return p
    return None

# ===============================
# 데이터 로딩
# ===============================
@st.cache_data
def load_env_data():
    data_dir = Path("data")
    result = {}
    files = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

    with st.spinner("🌡 환경 데이터 로딩 중..."):
        for f in files:
            path = find_file(data_dir, f)
            if path is None:
                st.error(f"❌ 환경 데이터 없음: {f}")
                continue
            df = pd.read_csv(path)
            df["time"] = pd.to_datetime(df["time"])
            school = f.replace("_환경데이터.csv", "")
            result[school] = df

    return result


@st.cache_data
def load_growth_data():
    data_dir = Path("data")
    path = find_file(data_dir, "4개교_생육결과데이터.xlsx")
    if path is None:
        st.error("❌ 생육 결과 XLSX 파일 없음")
        return {}

    with st.spinner("🌱 생육 데이터 로딩 중..."):
        xls = pd.ExcelFile(path)
        result = {}
        for sheet in xls.sheet_names:
            result[sheet] = pd.read_excel(path, sheet_name=sheet)

    return result


env_data = load_env_data()
growth_data = load_growth_data()

if not env_data or not growth_data:
    st.stop()

# ===============================
# 메타 정보
# ===============================
ec_map = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

# ===============================
# 사이드바
# ===============================
st.sidebar.title("🔍 분석 옵션")
school_option = st.sidebar.selectbox(
    "학교 선택",
    ["전체"] + list(ec_map.keys())
)

# ===============================
# 제목
# ===============================
st.title("🌱 극지식물 최적 EC 농도 연구")
st.markdown("""
본 대시보드는 서로 다른 EC(전기전도도) 조건에서  
극지식물의 **생육 특성 차이**를 정량적으로 분석하기 위해 제작되었다.
""")

tabs = st.tabs(["📖 실험 개요", "🌡 환경 데이터 분석", "📊 생육 결과 분석"])

# =====================================================
# TAB 1 : 실험 개요
# =====================================================
with tabs[0]:
    st.subheader("1️⃣ 연구 배경")
    st.markdown("""
    극지 환경에서는 토양과 수분 조건이 매우 제한적이기 때문에  
    **양액 내 무기이온 농도(EC)** 가 식물 생육에 큰 영향을 미친다.  

    본 실험은 EC 농도를 달리한 환경에서  
    극지식물의 생육 반응을 비교함으로써  
    **가장 효율적인 EC 농도를 도출**하는 것을 목표로 한다.
    """)

    st.subheader("2️⃣ 실험 설계")
    rows = []
    for school, df in growth_data.items():
        rows.append({
            "학교": school,
            "적용 EC": ec_map[school],
            "개체 수": len(df)
        })

    st.dataframe(pd.DataFrame(rows), use_container_width=True)

    st.subheader("3️⃣ 핵심 연구 질문")
    st.markdown("""
    - EC 농도에 따라 생중량은 어떻게 달라지는가?  
    - 생중량과 잎 수, 지상부 길이 사이에는 어떤 관계가 있는가?  
    - 극지식물 생육에 가장 적합한 EC 농도는 얼마인가?
    """)

# =====================================================
# TAB 2 : 환경 데이터
# =====================================================
with tabs[1]:
    st.subheader("🌡 학교별 환경 조건 평균 비교")

    avg_rows = []
    for school, df in env_data.items():
        avg_rows.append({
            "학교": school,
            "평균 온도(℃)": df["temperature"].mean(),
            "평균 습도(%)": df["humidity"].mean(),
            "평균 pH": df["ph"].mean(),
            "평균 EC": df["ec"].mean(),
            "목표 EC": ec_map[school]
        })

    avg_df = pd.DataFrame(avg_rows)
    st.dataframe(avg_df, use_container_width=True)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=["평균 온도", "평균 습도", "평균 pH", "EC 비교"]
    )

    fig.add_bar(x=avg_df["학교"], y=avg_df["평균 온도(℃)"], row=1, col=1)
    fig.add_bar(x=avg_df["학교"], y=avg_df["평균 습도(%)"], row=1, col=2)
    fig.add_bar(x=avg_df["학교"], y=avg_df["평균 pH"], row=2, col=1)
    fig.add_bar(x=avg_df["학교"], y=avg_df["평균 EC"], name="실측 EC", row=2, col=2)
    fig.add_bar(x=avg_df["학교"], y=avg_df["목표 EC"], name="목표 EC", row=2, col=2)

    fig.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("""
    👉 **모든 학교에서 온도·습도·pH는 큰 차이가 없었으며**,  
    생육 차이는 주로 **EC 조건 차이**에 의해 발생했음을 알 수 있다.
    """)

# =====================================================
# TAB 3 : 생육 결과
# =====================================================
with tabs[2]:
    st.subheader("📊 EC별 평균 생중량 비교")

    rows = []
    for school, df in growth_data.items():
        rows.append({
            "학교": school,
            "EC": ec_map[school],
            "평균 생중량(g)": df["생중량(g)"].mean(),
            "평균 잎 수": df["잎 수(장)"].mean(),
            "평균 지상부 길이(mm)": df["지상부 길이(mm)"].mean(),
            "개체 수": len(df)
        })

    result_df = pd.DataFrame(rows)
    best = result_df.loc[result_df["평균 생중량(g)"].idxmax()]

    col1, col2, col3 = st.columns(3)
    col1.metric("최대 평균 생중량", f"{best['평균 생중량(g)']:.2f} g")
    col2.metric("최적 EC", f"{best['EC']}")
    col3.metric("학교", best["학교"])

    fig_bar = px.bar(
        result_df,
        x="EC",
        y="평균 생중량(g)",
        color="학교",
        text="평균 생중량(g)"
    )
    fig_bar.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("📈 생육 지표 간 관계 분석")

    all_df = []
    for school, df in growth_data.items():
        tmp = df.copy()
        tmp["학교"] = school
        all_df.append(tmp)

    all_df = pd.concat(all_df)

    col1, col2 = st.columns(2)

    fig1 = px.scatter(
        all_df,
        x="잎 수(장)",
        y="생중량(g)",
        color="학교"
    )
    fig2 = px.scatter(
        all_df,
        x="지상부 길이(mm)",
        y="생중량(g)",
        color="학교"
    )

    fig1.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))
    fig2.update_layout(font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif"))

    col1.plotly_chart(fig1, use_container_width=True)
    col2.plotly_chart(fig2, use_container_width=True)

    st.markdown("""
    🔍 **분석 결과 해석**  
    - EC 2.0 조건에서 생중량이 가장 크게 나타남  
    - 잎 수 및 지상부 길이가 증가할수록 생중량도 증가하는 경향  
    - EC가 과도하게 높을 경우(EC 8.0) 생육 저해 현상 관찰
    """)

    st.success("✅ 결론: 극지식물 생육에 가장 적합한 EC 농도는 **2.0**이다.")
