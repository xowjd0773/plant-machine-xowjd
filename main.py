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

# 한글 폰트 CSS (Streamlit)
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+KR&display=swap');
html, body, [class*="css"] {
    font-family: 'Noto Sans KR', 'Malgun Gothic', sans-serif;
}
</style>
""", unsafe_allow_html=True)

# =========================
# 유틸 함수
# =========================
def normalize_name(name: str) -> str:
    """NFC/NFD 모두 대응"""
    return unicodedata.normalize("NFC", name)

def find_file_by_name(directory: Path, target_name: str) -> Path | None:
    target_nfc = normalize_name(target_name)
    for p in directory.iterdir():
        if normalize_name(p.name) == target_nfc:
            return p
    return None

# =========================
# 데이터 로딩
# =========================
@st.cache_data
def load_env_data():
    data_dir = Path("data")
    if not data_dir.exists():
        st.error("❌ data 폴더를 찾을 수 없습니다.")
        return {}

    env_files = {}
    targets = [
        "송도고_환경데이터.csv",
        "하늘고_환경데이터.csv",
        "아라고_환경데이터.csv",
        "동산고_환경데이터.csv",
    ]

    with st.spinner("환경 데이터 로딩 중..."):
        for t in targets:
            file_path = find_file_by_name(data_dir, t)
            if file_path is None:
                st.error(f"❌ 환경 데이터 파일 누락: {t}")
                continue
            df = pd.read_csv(file_path)
            df["time"] = pd.to_datetime(df["time"])
            school = t.replace("_환경데이터.csv", "")
            env_files[school] = df

    return env_files


@st.cache_data
def load_growth_data():
    data_dir = Path("data")
    xlsx_path = find_file_by_name(data_dir, "4개교_생육결과데이터.xlsx")
    if xlsx_path is None:
        st.error("❌ 생육 결과 XLSX 파일을 찾을 수 없습니다.")
        return {}

    with st.spinner("생육 결과 데이터 로딩 중..."):
        xls = pd.ExcelFile(xlsx_path)
        result = {}
        for sheet in xls.sheet_names:
            df = pd.read_excel(xlsx_path, sheet_name=sheet)
            result[sheet] = df

    return result


env_data = load_env_data()
growth_data = load_growth_data()

if not env_data or not growth_data:
    st.stop()

# =========================
# 메타 정보
# =========================
ec_conditions = {
    "송도고": 1.0,
    "하늘고": 2.0,
    "아라고": 4.0,
    "동산고": 8.0,
}

school_colors = {
    "송도고": "#1f77b4",
    "하늘고": "#2ca02c",
    "아라고": "#ff7f0e",
    "동산고": "#d62728",
}

# =========================
# 사이드바
# =========================
st.sidebar.title("학교 선택")
school_option = st.sidebar.selectbox(
    "학교",
    ["전체"] + list(ec_conditions.keys())
)

# =========================
# 제목
# =========================
st.title("🌱 극지식물 최적 EC 농도 연구")

tabs = st.tabs(["📖 실험 개요", "🌡️ 환경 데이터", "📊 생육 결과"])

# ======================================================
# Tab 1 : 실험 개요
# ======================================================
with tabs[0]:
    st.subheader("연구 배경 및 목적")
    st.markdown(
        """
        극지 환경에서도 안정적인 식물 생육을 위해  
        **EC(전기전도도) 농도**가 생육에 미치는 영향을 분석하였다.  
        서로 다른 EC 조건을 적용한 4개 학교의 실험 데이터를 비교하여  
        **최적 EC 농도**를 도출하는 것이 목적이다.
        """
    )

    summary_rows = []
    total_count = 0
    for school, df in growth_data.items():
        count = len(df)
        total_count += count
        summary_rows.append({
            "학교명": school,
            "EC 목표": ec_conditions.get(school, None),
            "개체수": count,
            "색상": school_colors.get(school)
        })

    summary_df = pd.DataFrame(summary_rows)
    st.dataframe(summary_df, use_container_width=True)

    # 주요 지표 카드
    col1, col2, col3, col4 = st.columns(4)

    avg_temp = pd.concat(env_data.values())["temperature"].mean()
    avg_hum = pd.concat(env_data.values())["humidity"].mean()

    col1.metric("총 개체수", f"{total_count} 개")
    col2.metric("평균 온도", f"{avg_temp:.1f} ℃")
    col3.metric("평균 습도", f"{avg_hum:.1f} %")
    col4.metric("최적 EC", "2.0 (하늘고) ⭐")

# ======================================================
# Tab 2 : 환경 데이터
# ======================================================
with tabs[1]:
    st.subheader("학교별 환경 평균 비교")

    avg_env = []
    for school, df in env_data.items():
        avg_env.append({
            "학교": school,
            "temperature": df["temperature"].mean(),
            "humidity": df["humidity"].mean(),
            "ph": df["ph"].mean(),
            "ec": df["ec"].mean(),
            "target_ec": ec_conditions[school]
        })

    avg_env_df = pd.DataFrame(avg_env)

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=[
            "평균 온도", "평균 습도",
            "평균 pH", "목표 EC vs 실측 EC"
        ]
    )

    fig.add_trace(
        go.Bar(x=avg_env_df["학교"], y=avg_env_df["temperature"]),
        row=1, col=1
    )
    fig.add_trace(
        go.Bar(x=avg_env_df["학교"], y=avg_env_df["humidity"]),
        row=1, col=2
    )
    fig.add_trace(
        go.Bar(x=avg_env_df["학교"], y=avg_env_df["ph"]),
        row=2, col=1
    )
    fig.add_trace(
        go.Bar(x=avg_env_df["학교"], y=avg_env_df["ec"], name="실측 EC"),
        row=2, col=2
    )
    fig.add_trace(
        go.Bar(x=avg_env_df["학교"], y=avg_env_df["target_ec"], name="목표 EC"),
        row=2, col=2
    )

    fig.update_layout(
        height=700,
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("환경 시계열 변화")

    target_schools = (
        env_data.keys() if school_option == "전체" else [school_option]
    )

    for school in target_schools:
        df = env_data[school]

        fig_line = make_subplots(rows=3, cols=1, shared_xaxes=True)

        fig_line.add_trace(
            go.Scatter(x=df["time"], y=df["temperature"], name="온도"),
            row=1, col=1
        )
        fig_line.add_trace(
            go.Scatter(x=df["time"], y=df["humidity"], name="습도"),
            row=2, col=1
        )
        fig_line.add_trace(
            go.Scatter(x=df["time"], y=df["ec"], name="EC"),
            row=3, col=1
        )
        fig_line.add_hline(
            y=ec_conditions[school],
            line_dash="dash",
            row=3, col=1
        )

        fig_line.update_layout(
            height=600,
            title=f"{school} 환경 변화",
            font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
        )
        st.plotly_chart(fig_line, use_container_width=True)

    with st.expander("📁 환경 데이터 원본"):
        for school, df in env_data.items():
            st.markdown(f"**{school}**")
            st.dataframe(df, use_container_width=True)

        csv_buffer = io.BytesIO()
        pd.concat(env_data).to_csv(csv_buffer, index=False)
        csv_buffer.seek(0)

        st.download_button(
            "환경 데이터 CSV 다운로드",
            data=csv_buffer,
            file_name="환경데이터_전체.csv",
            mime="text/csv"
        )

# ======================================================
# Tab 3 : 생육 결과
# ======================================================
with tabs[2]:
    st.subheader("🥇 EC별 평균 생중량")

    ec_weight = []
    for school, df in growth_data.items():
        ec_weight.append({
            "학교": school,
            "EC": ec_conditions[school],
            "평균 생중량": df["생중량(g)"].mean(),
            "개체수": len(df)
        })

    ec_df = pd.DataFrame(ec_weight)
    best_row = ec_df.loc[ec_df["평균 생중량"].idxmax()]

    col1, col2, col3 = st.columns(3)
    col1.metric("최대 평균 생중량", f"{best_row['평균 생중량']:.2f} g")
    col2.metric("해당 EC", f"{best_row['EC']}")
    col3.metric("학교", best_row["학교"])

    fig_bar = px.bar(
        ec_df,
        x="EC",
        y="평균 생중량",
        color="학교",
        text="평균 생중량"
    )
    fig_bar.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_bar, use_container_width=True)

    st.subheader("학교별 생중량 분포")
    dist_df = []
    for school, df in growth_data.items():
        tmp = df.copy()
        tmp["학교"] = school
        dist_df.append(tmp)

    dist_df = pd.concat(dist_df)

    fig_box = px.box(
        dist_df,
        x="학교",
        y="생중량(g)",
        color="학교"
    )
    fig_box.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    st.plotly_chart(fig_box, use_container_width=True)

    st.subheader("상관관계 분석")

    col1, col2 = st.columns(2)

    fig_scatter1 = px.scatter(
        dist_df,
        x="잎 수(장)",
        y="생중량(g)",
        color="학교",
        trendline="ols"
    )
    fig_scatter1.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    col1.plotly_chart(fig_scatter1, use_container_width=True)

    fig_scatter2 = px.scatter(
        dist_df,
        x="지상부 길이(mm)",
        y="생중량(g)",
        color="학교",
        trendline="ols"
    )
    fig_scatter2.update_layout(
        font=dict(family="Malgun Gothic, Apple SD Gothic Neo, sans-serif")
    )
    col2.plotly_chart(fig_scatter2, use_container_width=True)

    with st.expander("📁 생육 데이터 원본"):
        for school, df in growth_data.items():
            st.markdown(f"**{school}**")
            st.dataframe(df, use_container_width=True)

        xlsx_buffer = io.BytesIO()
        with pd.ExcelWriter(xlsx_buffer, engine="openpyxl") as writer:
            for school, df in growth_data.items():
                df.to_excel(writer, sheet_name=school, index=False)
        xlsx_buffer.seek(0)

        st.download_button(
            "생육 데이터 XLSX 다운로드",
            data=xlsx_buffer,
            file_name="생육결과_전체.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
