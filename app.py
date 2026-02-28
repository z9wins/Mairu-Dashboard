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
        df_scrapler = pd.read_csv("db_scrapler.csv", on_bad_lines="skip")
        df_scrapler["bot_type"] = "Scrapler ⚡"
    except:
        pass

    # โหลดไฟล์ Swing
    try:
        df_swing = pd.read_csv("db_swing.csv", on_bad_lines="skip")
        df_swing["bot_type"] = "Swing 🏰"
    except:
        pass

    # ถ้ายกมาทั้งสองไฟล์ไม่เจอเลย ให้จบการทำงาน
    if df_scrapler.empty and df_swing.empty:
        return None

    # จับสองตารางมาต่อกัน
    df_all = pd.concat([df_scrapler, df_swing], ignore_index=True)
    if not df_all.empty:
        df_all["timestamp"] = pd.to_datetime(df_all["timestamp"], errors="coerce")
        df_all = df_all.sort_values("timestamp", ascending=True)
        # แปลงตัวเลขให้ชัวร์
        df_all["profit_loss"] = pd.to_numeric(
            df_all["profit_loss"], errors="coerce"
        ).fillna(0)

    return df_all


df = load_data()

# ==========================================
# 🧭 2. แถบเมนูนำทาง (Sidebar Navigation)
# ==========================================
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio(
    "เลือกหน้าต่าง:", ["📊 Overview (ภาพรวม)", "📜 Trade History (ประวัติการเทรด)"]
)
st.sidebar.markdown("---")
st.sidebar.info("💡 ข้อมูลจะรีเฟรชอัตโนมัติทุกๆ 60 วินาที")

if df is None or df.empty:
    st.warning(
        "⚠️ ไม่พบไฟล์ข้อมูล กรุณาตรวจสอบว่ามีไฟล์ db_scrapler.csv และ db_swing.csv อยู่ในโฟลเดอร์เดียวกัน"
    )
else:
    # คัดเฉพาะไม้ที่ปิดแล้วมาคำนวณ KPI
    df_closed = df[df["status"] == "CLOSED"].copy()

    # ==========================================
    # 📈 หน้า Overview (ภาพรวมพอร์ต)
    # ==========================================
    if page == "📊 Overview (ภาพรวม)":
        st.title("📈 Mairu AI Trading Overview")
        st.markdown("ระบบติดตามผลกำไรบอทแบบ Multi-Strategy")

        # --- ฟังก์ชันช่วยคำนวณ KPI ---
        def render_kpi(bot_name, data):
            if data.empty:
                st.metric(f"Total Trades ({bot_name})", 0)
                return

            total_profit = data["profit_loss"].sum()
            total_trades = len(data)
            win_trades = len(data[data["profit_loss"] > 0])
            win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0

            col1, col2, col3 = st.columns(3)
            col1.metric(f"💰 Net Profit ({bot_name})", f"${total_profit:.2f}")
            col2.metric(f"🎯 Win Rate", f"{win_rate:.2f}%")
            col3.metric(f"📊 Total Closed", f"{total_trades}")

        # --- โซนแสดง KPI แยกบอท ---
        st.subheader("⚡ Scrapler Performance")
        render_kpi("Scrapler", df_closed[df_closed["bot_type"] == "Scrapler ⚡"])

        st.markdown("---")

        st.subheader("🏰 Swing Performance")
        render_kpi("Swing", df_closed[df_closed["bot_type"] == "Swing 🏰"])

        # --- กราฟ Equity Curve รวม 2 บอท ---
        st.markdown("---")
        st.subheader("🚀 Combined Equity Curve")

        # คำนวณกำไรสะสมแยกตามบอท
        df_closed["cumulative_profit"] = df_closed.groupby("bot_type")[
            "profit_loss"
        ].cumsum()

        fig = px.line(
            df_closed,
            x="timestamp",
            y="cumulative_profit",
            color="bot_type",
            markers=True,
            line_shape="spline",
            title="การเติบโตของพอร์ตแยกตามกลยุทธ์",
            color_discrete_map={"Scrapler ⚡": "#00d4ff", "Swing 🏰": "#ffaa00"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # ==========================================
    # 📜 หน้า Trade History (ประวัติและเจาะลึก AI)
    # ==========================================
    elif page == "📜 Trade History (ประวัติการเทรด)":
        st.title("📜 Trade History & AI Thought Process")

        # --- แผงควบคุมตัวกรอง (Filters) ---
        col1, col2 = st.columns(2)
        with col1:
            filter_bot = st.selectbox(
                "🤖 เลือกบอท:", ["ทั้งหมด (All)", "Scrapler ⚡", "Swing 🏰"]
            )
        with col2:
            filter_time = st.selectbox(
                "📅 ช่วงเวลา:",
                [
                    "รายวัน (Today)",
                    "รายสัปดาห์ (This Week)",
                    "รายเดือน (This Month)",
                    "ทั้งหมด (All)",
                ],
            )

        # --- ลอจิกการกรองข้อมูล ---
        df_filtered = df.copy()

        if filter_bot != "ทั้งหมด (All)":
            df_filtered = df_filtered[df_filtered["bot_type"] == filter_bot]

        now = datetime.now()
        if filter_time == "รายวัน (Today)":
            df_filtered = df_filtered[df_filtered["timestamp"].dt.date == now.date()]
        elif filter_time == "รายสัปดาห์ (This Week)":
            df_filtered = df_filtered[
                df_filtered["timestamp"].dt.isocalendar().week == now.isocalendar().week
            ]
        elif filter_time == "รายเดือน (This Month)":
            df_filtered = df_filtered[df_filtered["timestamp"].dt.month == now.month]

        # เรียงจากล่าสุดไปเก่าสุด
        df_filtered = df_filtered.sort_values("timestamp", ascending=False)

        st.markdown(f"**พบข้อมูลทั้งหมด {len(df_filtered)} รายการ**")

        # --- โซนแสดงประวัติแบบกดขยายได้ (Expander) ---
        if df_filtered.empty:
            st.info("ไม่พบประวัติการเทรดในช่วงเวลาที่เลือก")
        else:
            for index, row in df_filtered.iterrows():
                # ตกแต่งสีสถานะและกำไร
                status_icon = "🟢" if row["status"] == "OPEN" else "🔒"
                p_color = (
                    "🟢"
                    if row["profit_loss"] > 0
                    else "🔴" if row["profit_loss"] < 0 else "⚪"
                )
                pl_text = (
                    f"P/L: {row['profit_loss']} USD {p_color}"
                    if row["status"] == "CLOSED"
                    else "กำลังเทรด..."
                )

                # หัวข้อที่กดขยายได้
                with st.expander(
                    f"{status_icon} [{row['timestamp'].strftime('%Y-%m-%d %H:%M')}] | {row['bot_type']} | {row['action']} | {pl_text}"
                ):

                    st.markdown("#### 📊 ข้อมูล Technical ตอนเข้าเทรด")
                    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                    col_t1.metric("SL (Stop Loss)", row.get("sl", "N/A"))
                    col_t2.metric("TP (Take Profit)", row.get("tp", "N/A"))
                    col_t3.metric(
                        "RSI Fast", row.get("rsi_fast", row.get("rsi", "N/A"))
                    )
                    col_t4.metric("Sentiment Score", row.get("sentiment_score", "N/A"))

                    st.markdown("---")
                    st.markdown("#### 🧠 AI Thought Process (กระบวนการคิด)")
                    st.info(row.get("thought_process", "ไม่มีข้อมูล"))

                    st.markdown("#### ⚡ เหตุผลในการตัดสินใจ (Reasoning)")
                    st.success(row.get("reason_text", "ไม่มีข้อมูล"))
