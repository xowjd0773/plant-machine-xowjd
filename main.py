import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots

from pathlib import Path
import unicodedata
import io

# =========================
# 기본 설정
# =========================
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

# =========================
# 유틸
# =========================
def norm(name):
    return unicodedata.normalize("NFC", name)

def find_file(dir_path, target):
    target = norm(target)
    for p in dir_path.iterdir():
        if norm(p.name) == target:
            return p
    return None

# =========================
# 데이터 로딩
# =========================
@st.cache_data
def load_env():
    data_dir = Path("data")
    result = {}
    files = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

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
def load_growth():
    data_dir = Path("data")
    xlsx = find_file(data_dir, "4개교_생육결과데이터.xlsx")
    if xlsx is None:
        st.error("❌ 생육 XLSX 없음")
        return {}

    xls = pd.ExcelFile(xlsx)
    result = {}
    for sheet in xls.sheet_names:
        result[sheet] = pd.read_excel(xlsx, sheet_name=sheet)

    return result


env_data = load_env()
growth_data = load_growth()

if not env_data or not growth_data:
    st.stop()

# =========================
# 메타 정보
# =========================
ec_map = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

# =========================
# 사이드바
# =========================
st.sidebar.title("학교 선택")
school_option = st.sidebar.selectbox(
    "학교",
    ["전체"] + list(ec_map.keys())
)

# =========================
# 제목 (이게 안 보이면 앱 자체가 안 켜진 것)
# =========================
st.title("🌱 극지식물 최적 EC 농도 연구")
st.write("✅ 앱이 정상적으로 실행 중입니다.")

tabs = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ======================================================
# Tab 1
# ======================================================
with tabs[0]:
    st.subheader("연구 목적")
    st.markdown("""
    서로 다른 EC 농도 조건에서 극지식물의 생육 차이를 비교하여  
    **최적 EC 농도**를 도출한다.
    """)

    summary = []
    for school, df in growth_data.items():
        summary.append({
            "학교": school,
            "EC": ec_map[school],
            "개체수": len(df)
        })

    st.dataframe(pd.DataFrame(summary), use_container_width=True)

# ======================================================
# Tab 2
# ======================================================
with tabs[1]:
    st.subheader("환경 데이터 평균")

    avg = []
    for school, df in env_data.items():
        avg.append({
            "학교": school,
            "온도": df["temperature"].mean(),
            "습도": df["humidity"].mean(),
            "pH": df["ph"].mean(),
            "EC": df["ec"].mean()
        })

    avg_df = pd.DataFrame(avg)

    fig = px.bar(
        avg_df,
        x="학교",
        y=["온도", "습도", "EC"],
        barmode="group"
    )
    fig.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

# ======================================================
# Tab 3
# ======================================================
with tabs[2]:
    st.subheader("EC별 생중량 비교")

    rows = []
    for school, df in growth_data.items():
        rows.append({
            "학교": school,
            "EC": ec_map[school],
            "평균 생중량": df["생중량(g)"].mean()
        })

    ec_df = pd.DataFrame(rows)
    best = ec_df.loc[ec_df["평균 생중량"].idxmax()]

    st.metric("최적 EC", f"{best['EC']} ( {best['학교']} ) ⭐")

    fig = px.bar(
        ec_df,
        x="EC",
        y="평균 생중량",
        color="학교",
        text="평균 생중량"
    )
    fig.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)
