import streamlit as st
import pandas as pd
import datetime
import os
import plotly.graph_objects as go

# 페이지 기본 설정
st.set_page_config(page_title="부산 집사 v2.0 - 부동산 프로 임장 노트", layout="wide", page_icon="🏢")

st.title("🏢 부산 집사 v2.0 (Busan Real Estate Analytics)")
st.caption("🚀 단순 기록을 넘어 입지 스코어링 및 레이더 차트 비교 분석을 지원하는 프로용 임장 앱")

DATA_FILE = "imjang_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "날짜", "구/군", "단지명", "평형", "세대수", "준공연도", "매매가(억)", "전세가(억)", "갭(억)", "전세가율(%)",
            "경사도", "교통", "학군/상권", "주차/관리", "상품성", "입지총점", "가성비지수", "특이사항/중개사팁"
        ])

# 탭 구조 분리 (입력 / 분석 비교)
tab1, tab2 = st.tabs(["📝 현장 임장 기록", "📊 단지별 비교 분석"])

with tab1:
    with st.form("imjang_form_v2", clear_on_submit=True):
        st.subheader("1. 단지 기본 스펙 & 시세")
        c1, c2, c3 = st.columns(3)
        with c1:
            gu = st.selectbox("부산 구/군", ["해운대구", "수영구", "남구", "동래구", "금정구", "연제구", "부산진구", "기타"])
            apt_name = st.text_input("단지명", placeholder="예: 래미안장전")
            pyeong = st.text_input("평형", placeholder="예: 34평")
        with c2:
            households = st.number_input("총 세대수", min_value=0, step=100, value=1000)
            build_year = st.number_input("준공연도", min_value=1980, max_value=2026, value=2018)
        with c3:
            price_buy = st.number_input("매매 호가 (억)", min_value=0.0, step=0.1, format="%.1f")
            price_rent = st.number_input("전세 호가 (억)", min_value=0.0, step=0.1, format="%.1f")
            
            gap = round(price_buy - price_rent, 1)
            rent_ratio = round((price_rent / price_buy * 100), 1) if price_buy > 0 else 0.0
            st.metric("갭 (GAP)", f"{gap} 억")
            st.metric("전세가율", f"{rent_ratio} %")

        st.markdown("---")
        st.subheader("2. 정밀 입지 스코어링 (각 1~5점)")
        
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            slope = st.slider("⛰️ 경사도 (5: 완전평지 ~ 1: 극심한 경사/단차)", 1, 5, 3)
            subway = st.slider("🚇 교통/역세권 (5: 초역세권 ~ 1: 대중교통 불편)", 1, 5, 3)
            infra = st.slider("🏫 학군/상권 (5: 초품아+학원가 ~ 1: 인프라 부족)", 1, 5, 3)
        with col_s2:
            parking = st.slider("🚗 주차/단지관리 (5: 세대당 1.3대+지하주차장 직접연결 ~ 1: 주차난)", 1, 5, 3)
            brand = st.slider("🏗️ 상품성/브랜드 (5: 1군브랜드/신축/대단지 ~ 1: 노후 구축)", 1, 5, 3)

        total_score = slope + subway + infra + parking + brand
        # 가성비 지수 = 입지총점 / 매매가 (억당 점수)
        efficiency_idx = round(total_score / price_buy, 2) if price_buy > 0 else 0.0
        
        st.info(f"📊 **입지 총점:** {total_score}점 / 25점 만점 | 💡 **가성비 지수:** {efficiency_idx} (억당 입지점수)")

        st.markdown("---")
        st.subheader("3. 정성 메모 & 중개업소 브리핑")
        notes = st.text_area("현장 상세 노트", placeholder="로얄동/비선호동 차이, 조망/소음, 집주인 급매 사유, 사장님 추천 이유 등", height=100)

        submitted = st.form_submit_button("💾 데이터 최종 저장")

        if submitted:
            if not apt_name:
                st.error("⚠️ 단지명을 반드시 입력해야 합니다.")
            else:
                new_data = {
                    "날짜": datetime.date.today().strftime("%Y-%m-%d"),
                    "구/군": gu, "단지명": apt_name, "평형": pyeong,
                    "세대수": households, "준공연도": build_year,
                    "매매가(억)": price_buy, "전세가(억)": price_rent, "갭(억)": gap, "전세가율(%)": rent_ratio,
                    "경사도": slope, "교통": subway, "학군/상권": infra, "주차/관리": parking, "상품성": brand,
                    "입지총점": total_score, "가성비지수": efficiency_idx, "특이사항/중개사팁": notes
                }
                df = load_data()
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success(f"✅ [{apt_name}] 임장 데이터가 저장되었습니다!")

with tab2:
    st.subheader("📈 저장된 단지 입지 비교 분석")
    df_data = load_data()

    if not df_data.empty:
        # 데이터 요약 표
        st.dataframe(df_data.sort_values(by="입지총점", ascending=False), use_container_width=True)

        st.markdown("---")
        st.subheader("🕸️ 단지 간 입지 레이더 차트 (Spider Chart) 비교")
        
        selected_apts = st.multiselect("비교할 단지들을 선택하세요 (최대 3개 추천)", options=df_data["단지명"].unique(), default=df_data["단지명"].unique()[:2])

        if selected_apts:
            fig = go.Figure()
            categories = ['경사도', '교통', '학군/상권', '주차/관리', '상품성']

            for apt in selected_apts:
                apt_row = df_data[df_data["단지명"] == apt].iloc[-1]
                values = [apt_row['경사도'], apt_row['교통'], apt_row['학군/상권'], apt_row['주차/관리'], apt_row['상품성']]
                values.append(values[0]) # 폐곡선 생성

                fig.add_trace(go.Scatterpolar(
                    r=values,
                    theta=categories + [categories[0]],
                    fill='toself',
                    name=apt
                ))

            fig.update_layout(polar=dict(radialaxis=dict(visible=True, range=[0, 5])), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
            
        # CSV 다운로드
        csv_data = df_data.to_csv(index=False).encode('utf-8-sig')
        st.download_button("📥 전체 데이터 엑셀 내보내기", data=csv_data, file_name="busan_imjang_v2.csv", mime="text/csv")
    else:
        st.info("아직 입력된 데이터가 없습니다. 첫 번째 탭에서 데이터를 저장해 보세요.")
