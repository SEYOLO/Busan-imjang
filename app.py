import streamlit as st
import pandas as pd
import datetime
import os
import folium
from streamlit_folium import st_folium
from geopy.geocoders import Nominatim

# 페이지 기본 설정
st.set_page_config(page_title="부산 집사 v3.0 - 지도 기반 임장 노트", layout="wide", page_icon="🗺️")

# 커스텀 CSS (UI 모바일 앱 느낌 개선)
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stButton>button { width: 100%; background-color: #3182ce; color: white; border-radius: 8px; font-weight: bold; }
    div[data-testid="metric-container"] { background-color: #ffffff; padding: 10px; border-radius: 8px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    </style>
""", unsafe_allow_html=True)

st.title("🗺️ 부산 집사 v3.0 (Map-Based Real Estate)")
st.caption("📍 지도상에서 한눈에 보는 부산 아파트 임장 지적도 & 스코어링")

DATA_FILE = "imjang_data.csv"

# 데이터 불러오기
def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "날짜", "구/군", "단지명", "위도", "경도", "매매가(억)", "전세가(억)", "갭(억)",
            "경사도", "교통", "학군/상권", "주차/관리", "상품성", "입지총점", "특이사항/중개사팁"
        ])

# 주소를 위도/경도로 변환하는 함수
def get_coordinates(address):
    try:
        geolocator = Nominatim(user_agent="busan_imjang_app")
        location = geolocator.geocode(address)
        if location:
            return location.latitude, location.longitude
        else:
            return 35.1795543, 129.0756416  # 변환 실패 시 부산시청 좌표 기본값
    except:
        return 35.1795543, 129.0756416

# 탭 구성 (1. 지도 중심 임장지 조회 / 2. 현장 신규 데이터 입력)
tab_map, tab_input = st.tabs(["📍 부산 임장 지도 (Map View)", "📝 현장 임장 노트 작성"])

df_data = load_data()

# [TAB 1] 지도 뷰 모듈
with tab_map:
    st.subheader("📍 임장 아파트 지도 마커")
    
    # 부산 중심점 좌표
    m = folium.Map(location=[35.1795543, 129.0756416], zoom_start=11, tiles="OpenStreetMap")

    if not df_data.empty:
        for idx, row in df_data.iterrows():
            # 점수대별 마커 색상 구분
            score = row['입지총점']
            color = "green" if score >= 20 else ("blue" if score >= 15 else "orange")
            
            # 팝업 HTML 생성 (클릭 시 노출)
            popup_html = f"""
            <div style="width:200px; font-family: sans-serif;">
                <h4 style="margin-bottom:5px; color:#2b6cb0;">{row['단지명']}</h4>
                <p style="margin:2px 0;"><b>매매:</b> {row['매매가(억)']}억 / <b>전세:</b> {row['전세가(억)']}억</p>
                <p style="margin:2px 0; color:#e53e3e;"><b>갭(GAP): {row['갭(억)']}억원</b></p>
                <hr style="margin:5px 0;">
                <p style="margin:2px 0;"><b>입지총점:</b> <span style="font-size:14px; font-weight:bold; color:{color};">{score}점 / 25점</span></p>
                <p style="margin:2px 0; font-size:12px; color:#4a5568;"><b>경사도:</b> {row['경사도']}점 | <b>교통:</b> {row['교통']}점</p>
                <p style="margin:5px 0; font-size:11px; background:#f7fafc; padding:4px; border-radius:4px;">💬 {row['특이사항/중개사팁']}</p>
            </div>
            """
            
            folium.Marker(
                location=[row['위도'], row['경도']],
                popup=folium.Popup(popup_html, max_width=250),
                tooltip=f"{row['단지명']} ({score}점)",
                icon=folium.Icon(color=color, icon="home", prefix="fa")
            ).add_to(m)

    # 지도 출력
    st_folium(m, width="100%", height=500)

    st.markdown("---")
    st.subheader("📋 전체 임장 리스트")
    if not df_data.empty:
        st.dataframe(df_data[["구/군", "단지명", "매매가(억)", "전세가(억)", "갭(억)", "입지총점", "특이사항/중개사팁"]].sort_values(by="입지총점", ascending=False), use_container_width=True)
    else:
        st.info("아직 저장된 임장 데이터가 없습니다. 오른쪽 '현장 임장 노트 작성' 탭에서 첫 데이터를 입력해보세요.")

# [TAB 2] 입력 폼 모듈
with tab_input:
    with st.form("input_form_v3", clear_on_submit=True):
        st.subheader("1. 단지명 & 가격 입력")
        c1, c2, c3 = st.columns(3)
        with c1:
            gu = st.selectbox("부산 구/군", ["해운대구", "수영구", "남구", "동래구", "금정구", "연제구", "부산진구", "기타"])
            apt_name = st.text_input("단지명 (정확히 입력)", placeholder="예: 래미안장전")
        with c2:
            price_buy = st.number_input("매매 호가 (억)", min_value=0.0, step=0.1, format="%.1f")
            price_rent = st.number_input("전세 호가 (억)", min_value=0.0, step=0.1, format="%.1f")
        with c3:
            gap = round(price_buy - price_rent, 1)
            st.metric("자동 계산 갭(GAP)", f"{gap} 억원")

        st.markdown("---")
        st.subheader("2. 핵심 현장 스코어링 (1~5점)")
        col_a, col_b = st.columns(2)
        with col_a:
            slope = st.slider("⛰️ 경사도 (5: 완전평지 ~ 1: 극심한 경사)", 1, 5, 3)
            subway = st.slider("🚇 교통/역세권 (5: 도보 5분 이내 ~ 1: 대중교통 불편)", 1, 5, 3)
            infra = st.slider("🏫 학군/상권 (5: 초품아+학원가 ~ 1: 인프라 부족)", 1, 5, 3)
        with col_b:
            parking = st.slider("🚗 주차/관리 (5: 세대당 1.2대이상+지하 direct ~ 1: 주차난)", 1, 5, 3)
            brand = st.slider("🏗️ 상품성 (5: 신축/대단지/1군브랜드 ~ 1: 노후 구축)", 1, 5, 3)

        total_score = slope + subway + infra + parking + brand
        st.info(f"📊 **입지 평가 총점:** {total_score}점 / 25점 만점")

        st.markdown("---")
        st.subheader("3. 현장 메모 & 중개사 브리핑")
        notes = st.text_area("현장 메모", placeholder="로얄동/라인, 남향 여부, 조망, 대로변 소음, 집주인 급매 사유 등", height=80)

        submitted = st.form_submit_button("📍 좌표 계산 및 지도에 핀 찍기 저장")

        if submitted:
            if not apt_name:
                st.error("⚠️ 단지명을 반드시 입력해야 합니다.")
            else:
                # 주소 자동 변환 (예: 부산 해운대구 래미안장전)
                full_address = f"부산 {gu} {apt_name}"
                lat, lon = get_coordinates(full_address)

                new_data = {
                    "날짜": datetime.date.today().strftime("%Y-%m-%d"),
                    "구/군": gu, "단지명": apt_name, "위도": lat, "경도": lon,
                    "매매가(억)": price_buy, "전세가(억)": price_rent, "갭(억)": gap,
                    "경사도": slope, "교통": subway, "학군/상권": infra, "주차/관리": parking, "상품성": brand,
                    "입지총점": total_score, "특이사항/중개사팁": notes
                }
                df = load_data()
                df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
                df.to_csv(DATA_FILE, index=False)
                st.success(f"🎉 [{apt_name}] 좌표({lat:.4f}, {lon:.4f}) 변환 완료! 지도에 마커가 생성되었습니다.")
