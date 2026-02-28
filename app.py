import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime

# ตั้งค่าหน้าเว็บเป็นแบบ Wide กว้างเต็มจอ
st.set_page_config(page_title="Mairu AI Dashboard", layout="wide", page_icon="🤖")

# ==========================================
# 📥 1. ระบบโหลดและรวมข้อมูล (Data Loading)
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    df_scrapler = pd.DataFrame()
    df_swing = pd.DataFrame()

    # โหลดไฟล์ Scrapler
    try:
        df_scrapler = pd.read_csv("db_scrapler.csv", on_bad_lines='skip')
        df_scrapler['bot_type'] = 'Scrapler ⚡'
    except: pass

    # โหลดไฟล์ Swing
    try:
        df_swing = pd.read_csv("db_swing.csv", on_bad_lines='skip')
        df_swing['bot_type'] = 'Swing 🏰'
    except: pass

    if df_scrapler.empty and df_swing.empty:
        return None

    # จับสองตารางมาต่อกัน
    df_all = pd.concat([df_scrapler, df_swing], ignore_index=True)
    if not df_all.empty:
        df_all['timestamp'] = pd.to_datetime(df_all['timestamp'], errors='coerce')
        df_all = df_all.sort_values('timestamp', ascending=True)
        df_all['profit_loss'] = pd.to_numeric(df_all['profit_loss'], errors='coerce').fillna(0)
    
    return df_all

df = load_data()

# ==========================================
# 🧭 2. ส่วนหัวของเว็บและระบบ Top Navigation
# ==========================================
st.title("🤖 Mairu AI Trading Dashboard")
st.markdown("ระบบติดตามผลกำไรบอทแบบ Multi-Strategy | 🔄 ข้อมูลจะรีเฟรชอัตโนมัติทุกๆ 60 วินาที")

if df is None or df.empty:
    st.warning("⚠️ ไม่พบไฟล์ข้อมูล กรุณาตรวจสอบว่าบอทบน VPS ได้ส่งไฟล์ขึ้น GitHub แล้ว")
else:
    # 🌟 เปลี่ยนจาก Sidebar มาใช้ระบบ Tabs (เมนูด้านบน)
    tab_overview, tab_history = st.tabs(["📊 Overview (ภาพรวมพอร์ต)", "📜 Trade History (ประวัติการเทรดเจาะลึก)"])

    df_closed = df[df['status'] == 'CLOSED'].copy()

    # ==========================================
    # 📈 หน้า Overview (ภาพรวมพอร์ต)
    # ==========================================
    with tab_overview:
        # --- ฟังก์ชันช่วยคำนวณ KPI ---
        def render_kpi(bot_name, data):
            if data.empty:
                st.metric(f"Total Trades ({bot_name})", 0)
                return
            
            total_profit = data['profit_loss'].sum()
            total_trades = len(data)
            win_trades = len(data[data['profit_loss'] > 0])
            win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric(f"💰 Net Profit ({bot_name})", f"${total_profit:.2f}")
            col2.metric(f"🎯 Win Rate", f"{win_rate:.2f}%")
            col3.metric(f"📊 Total Closed Trades", f"{total_trades}")

        st.subheader("⚡ Scrapler Performance")
        render_kpi("Scrapler", df_closed[df_closed['bot_type'] == 'Scrapler ⚡'])
        
        st.markdown("---")
        
        st.subheader("🏰 Swing Performance")
        render_kpi("Swing", df_closed[df_closed['bot_type'] == 'Swing 🏰'])

        st.markdown("---")
        st.subheader("🚀 Combined Equity Curve")
        
        df_closed['cumulative_profit'] = df_closed.groupby('bot_type')['profit_loss'].cumsum()
        fig = px.line(df_closed, x='timestamp', y='cumulative_profit', color='bot_type',
                      markers=True, line_shape="spline", title="การเติบโตของพอร์ตแยกตามกลยุทธ์",
                      color_discrete_map={"Scrapler ⚡": "#00d4ff", "Swing 🏰": "#ffaa00"})
        st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 📜 หน้า Trade History (ประวัติและเจาะลึก AI)
    # ==========================================
    with tab_history:
        st.subheader("🔍 กรองข้อมูลประวัติ")
        
        # --- แผงควบคุมตัวกรอง (Filters) ---
        col1, col2 = st.columns(2)
        with col1:
            filter_bot = st.selectbox("🤖 เลือกบอท:", ["ทั้งหมด (All)", "Scrapler ⚡", "Swing 🏰"])
        with col2:
            filter_time = st.selectbox("📅 ช่วงเวลา:", ["ทั้งหมด (All)", "รายวัน (Today)", "รายสัปดาห์ (This Week)", "รายเดือน (This Month)"])

        # --- ลอจิกการกรองข้อมูล ---
        df_filtered = df.copy()
        if filter_bot != "ทั้งหมด (All)":
            df_filtered = df_filtered[df_filtered['bot_type'] == filter_bot]

        now = datetime.now()
        if filter_time == "รายวัน (Today)":
            df_filtered = df_filtered[df_filtered['timestamp'].dt.date == now.date()]
        elif filter_time == "รายสัปดาห์ (This Week)":
            df_filtered = df_filtered[df_filtered['timestamp'].dt.isocalendar().week == now.isocalendar().week]
        elif filter_time == "รายเดือน (This Month)":
            df_filtered = df_filtered[df_filtered['timestamp'].dt.month == now.month]

        df_filtered = df_filtered.sort_values('timestamp', ascending=False)

        # 🌟 [ไฮไลท์อัปเกรด] คำนวณสถิติเฉพาะหน้าต่างที่ฟิลเตอร์มา
        df_filtered_closed = df_filtered[df_filtered['status'] == 'CLOSED']
        if not df_filtered_closed.empty:
            f_profit = df_filtered_closed['profit_loss'].sum()
            f_trades = len(df_filtered_closed)
            f_wins = len(df_filtered_closed[df_filtered_closed['profit_loss'] > 0])
            f_winrate = (f_wins / f_trades) * 100 if f_trades > 0 else 0
        else:
            f_profit, f_trades, f_winrate = 0, 0, 0

        st.markdown("---")
        st.markdown(f"### 📊 สถิติเฉพาะช่วงเวลา: {filter_time}")
        k_col1, k_col2, k_col3 = st.columns(3)
        k_col1.metric("💵 กำไร/ขาดทุน (P/L)", f"${f_profit:.2f}")
        k_col2.metric("🎯 Win Rate", f"{f_winrate:.2f}%")
        k_col3.metric("📈 จำนวนไม้ที่ปิดแล้ว", f"{f_trades} ไม้")
        st.markdown("---")

        st.markdown(f"**พบข้อมูลประวัติทั้งหมด {len(df_filtered)} รายการ (รวมไม้ที่กำลังเปิดอยู่)**")

        # --- โซนแสดงประวัติแบบกดขยายได้ ---
        if df_filtered.empty:
            st.info("ไม่พบประวัติการเทรดในช่วงเวลาที่เลือก")
        else:
            for index, row in df_filtered.iterrows():
                status_icon = "🟢" if row['status'] == "OPEN" else "🔒"
                p_color = "🟢" if row['profit_loss'] > 0 else "🔴" if row['profit_loss'] < 0 else "⚪"
                pl_text = f"P/L: {row['profit_loss']} USD {p_color}" if row['status'] == "CLOSED" else "กำลังเทรด..."

                with st.expander(f"{status_icon} [{row['timestamp'].strftime('%Y-%m-%d %H:%M')}] | {row['bot_type']} | {row['action']} | {pl_text}"):
                    
                    st.markdown("#### 📊 ข้อมูล Technical ตอนเข้าเทรด")
                    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                    col_t1.metric("SL (Stop Loss)", row.get('sl', 'N/A'))
                    col_t2.metric("TP (Take Profit)", row.get('tp', 'N/A'))
                    # รองรับทั้งคอลัมน์เก่า (rsi) และใหม่ (rsi_fast)
                    col_t3.metric("RSI Fast", row.get('rsi_fast', row.get('rsi', 'N/A')))
                    col_t4.metric("Sentiment Score", row.get('sentiment_score', 'N/A'))

                    st.markdown("---")
                    st.markdown("#### 🧠 AI Thought Process (กระบวนการคิด)")
                    st.info(row.get('thought_process', 'ไม่มีข้อมูล'))
                    
                    st.markdown("#### ⚡ เหตุผลในการตัดสินใจ (Reasoning)")
                    st.success(row.get('reason_text', 'ไม่มีข้อมูล'))
