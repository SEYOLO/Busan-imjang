import streamlit as st
import pandas as pd
import datetime
import os

# 페이지 기본 설정
st.set_page_config(page_title="부산 집사 - 부동산 임장 노트", layout="centered", page_icon="🏢")

# 타이틀 및 안내문구
st.title("🏢 부산 집사 (Busan Real Estate)")
st.caption("💡 초보자를 위한 부산 아파트 현장 임장 & 스코어링 노트")

DATA_FILE = "imjang_data.csv"

def load_data():
    if os.path.exists(DATA_FILE):
        return pd.read_csv(DATA_FILE)
    else:
        return pd.DataFrame(columns=[
            "날짜", "구/군", "단지명", "평형", "매매가(억)", "전세가(억)", "갭(억)",
            "경사도", "교통", "학군/상권", "주차/관리", "상품성", "입지총점(25점만점)", "특이사항/중개사팁"
        ])

# 1. 입력 폼
with st.form("imjang_form", clear_on_submit=True):
    st.subheader("📝 1. 기본 정보 & 시세 입력")
    
    col1, col2 = st.columns(2)
    with col1:
        gu = st.selectbox("부산 구/군", ["해운대구", "수영구", "남구", "동래구", "금정구", "연제구", "부산진구", "기타"])
        apt_name = st.text_input("단지명", placeholder="예: 래미안장전")
        pyeong = st.text_input("평형", placeholder="예: 34평")
    with col2:
        price_buy = st.number_input("매매 호가 (억원)", min_value=0.0, step=0.1, format="%.1f")
        price_rent = st.number_input("전세 호가 (억원)", min_value=0.0, step=0.1, format="%.1f")
        gap = round(price_buy - price_rent, 1)
        st.write(f"👉 **자동 계산 갭(GAP):** :blue[{gap} 억원]")

    st.markdown("---")
    st.subheader("🔍 2. 초보자 임장 체크 가이드 & 스코어링")
    st.info("각 항목의 안내 설명을 참고하여 1~5점 슬라이더를 조정하세요.")

    st.markdown("**① 경사도 (부산 필수 체크)**")
    st.caption("· 5점: 완벽한 평지 | 3점: 완만한 경사 | 1점: 심한 경사/단차 높음")
    slope = st.slider("경사도 점수", 1, 5, 3, key="slope")

    st.markdown("**② 교통 / 역세권**")
    st.caption("· 5점: 지하철 도보 5분 이내 | 3점: 도보 10~15분 | 1점: 버스 환승 필수")
    subway = st.slider("교통 점수", 1, 5, 3, key="subway")

    st.markdown("**③ 학군 및 상권**")
    st.caption("· 5점: 초품아 + 학원가/마트 도보권 | 3점: 초등학교 도보 10분 | 1점: 상권/인프라 부족")
    infra = st.slider("학군/상권 점수", 1, 5, 3, key="infra")

    st.markdown("**④ 주차 및 단지 관리**")
    st.caption("· 5점: 세대당 1.2대 이상 + 지하주차장 엘리베이터 연결 | 3점: 주차 약간 부족 | 1점: 지상주차 위주")
    parking = st.slider("주차/관리 점수", 1, 5, 3, key="parking")

    st.markdown("**⑤ 상품성 및 브랜드**")
    st.caption("· 5점: 5년 이내 신축/대단지/1군 브랜드 | 3점: 10~15년 차 구축 | 1점: 20년 이상 노후")
    brand = st.slider("상품성 점수", 1, 5, 3, key="brand")

    total_score = slope + subway + infra + parking + brand
    st.markdown(f"📊 **입지 평가 총점:** :green[{total_score}점 / 25점 만점]")

    st.markdown("---")
    st.subheader("🗣️ 3. 현장 메모 및 중개업소 브리핑")
    notes = st.text_area(
        "현장 메모",
        placeholder="체크 예시: 로얄동/라인, 남향 여부, 조망, 대로변 소음, 집주인 급매 사유 등",
        height=100
    )

    submitted = st.form_submit_button("💾 임장 노트 저장하기")

    if submitted:
        if not apt_name:
            st.error("⚠️ 단지명을 입력해 주세요!")
        else:
            new_data = {
                "날짜": datetime.date.today().strftime("%Y-%m-%d"),
                "구/군": gu,
                "단지명": apt_name,
                "평형": pyeong,
                "매매가(억)": price_buy,
                "전세가(억)": price_rent,
                "갭(억)": gap,
                "경사도": slope,
                "교통": subway,
                "학군/상권": infra,
                "주차/관리": parking,
                "상품성": brand,
                "입지총점(25점만점)": total_score,
                "특이사항/중개사팁": notes
            }
            df = load_data()
            df = pd.concat([df, pd.DataFrame([new_data])], ignore_index=True)
            df.to_csv(DATA_FILE, index=False)
            st.success(f"🎉 '{apt_name}' 임장 노트가 저장되었습니다!")

# 2. 저장 데이터 조회
st.markdown("---")
st.subheader("📊 임장 데이터 리스트")
df_current = load_data()

if not df_current.empty:
    st.dataframe(df_current.sort_values(by="입지총점(25점만점)", ascending=False), use_container_width=True)
    csv = df_current.to_csv(index=False).encode('utf-8-sig')
    st.download_button("📥 엑셀/CSV 내보내기", data=csv, file_name="busan_imjang_result.csv", mime="text/csv")
else:
    st.info("아직 입력된 데이터가 없습니다.")
