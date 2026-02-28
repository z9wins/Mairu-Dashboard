import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import streamlit.components.v1 as components

# ==========================================
# ⚙️ ตั้งค่าหน้าเว็บเป็นแบบ Wide กว้างเต็มจอ
# ==========================================
st.set_page_config(page_title="Mairu AI Dashboard", layout="wide", page_icon="🤖", initial_sidebar_state="expanded")

# ==========================================
# 📥 1. ระบบโหลดและรวมข้อมูล (Data Loading)
# ==========================================
@st.cache_data(ttl=60)
def load_data():
    try:
        df_scrapler = pd.read_csv("db_scrapler.csv", on_bad_lines="skip")
        df_scrapler["bot_type"] = "Scrapler ⚡"
    except:
        df_scrapler = pd.DataFrame()

    try:
        df_swing = pd.read_csv("db_swing.csv", on_bad_lines="skip")
        df_swing["bot_type"] = "Swing 🏰"
    except:
        df_swing = pd.DataFrame()

    if df_scrapler.empty and df_swing.empty:
        return None

    df_all = pd.concat([df_scrapler, df_swing], ignore_index=True)
    if not df_all.empty:
        df_all["timestamp"] = pd.to_datetime(df_all["timestamp"], errors="coerce")
        df_all = df_all.sort_values("timestamp", ascending=False)
        df_all["profit_loss"] = pd.to_numeric(df_all["profit_loss"], errors="coerce").fillna(0)
    
    return df_all

df = load_data()

# ==========================================
# 🧭 2. แถบเมนูนำทาง (Sidebar Navigation)
# ==========================================
st.sidebar.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio(
    "เลือกหน้าต่าง:", ["📊 Market & Overview", "📜 Trade History & Filters"]
)
st.sidebar.markdown("---")
st.sidebar.info("💡 ข้อมูลจะรีเฟรชอัตโนมัติทุกๆ 60 วินาที\n\n🟢 ระบบทำงานปกติ 24/7")

st.title("🤖 Mairu AI Trading Dashboard")
st.markdown("ระบบติดตามผลกำไรบอทแบบ Multi-Strategy | 🔄 อัปเดตข้อมูล Real-time")

if df is None or df.empty:
    st.warning("⚠️ ไม่พบไฟล์ข้อมูล กรุณาตรวจสอบว่าบอทบน VPS ได้ส่งไฟล์ขึ้น GitHub แล้ว")
else:
    df_closed = df[df["status"] == "CLOSED"].copy()

    # ==========================================
    # 📈 หน้า 1: Market & Overview (ภาพรวมพอร์ต)
    # ==========================================
    if page == "📊 Market & Overview":
        
        st.markdown("### 🌐 Live Market & Economic Calendar")
        col_chart, col_news = st.columns([6, 4]) 
        
        with col_chart:
            components.html(
                """
                <div class="tradingview-widget-container" style="height: 600px; overflow: hidden;">
                  <div id="tradingview_xauusd" style="height: 100%;"></div>
                  <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
                  <script type="text/javascript">
                  new TradingView.widget({
                  "autosize": false,
                  "width": "100%",
                  "height": "600",
                  "symbol": "OANDA:XAUUSD",
                  "interval": "15",
                  "timezone": "Asia/Bangkok",
                  "theme": "dark",
                  "style": "1",
                  "locale": "th_TH",
                  "enable_publishing": false,
                  "allow_symbol_change": true,
                  "container_id": "tradingview_xauusd"
                });
                  </script>
                </div>
                """, height=600
            )

        with col_news:
            components.html(
                """
                <div class="tradingview-widget-container" style="height: 600px; overflow: hidden;">
                  <div class="tradingview-widget-container__widget" style="height: 600px;"></div>
                  <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
                  {
                  "colorTheme": "dark",
                  "isTransparent": false,
                  "width": "100%",
                  "height": "600", 
                  "locale": "th_TH",
                  "importanceFilter": "0,1",
                  "currencyFilter": "USD" 
                }
                  </script>
                </div>
                """, height=600
            )
            
        st.markdown("---")
        
        # --- โซนแสดง KPI แยกบอท ---
        st.markdown("### 🎯 Bots Performance")
        def render_kpi(bot_name, data):
            if data.empty:
                st.metric(f"Total Trades ({bot_name})", 0)
                return

            total_profit = data["profit_loss"].sum()
            total_trades = len(data)
            win_trades = len(data[data["profit_loss"] > 0])
            win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0

            # คำนวณ Win Streak
            data_sorted = data.sort_values("timestamp", ascending=True)
            current_streak, max_streak = 0, 0
            for profit in data_sorted["profit_loss"]:
                if profit > 0:
                    current_streak += 1
                    max_streak = max(max_streak, current_streak)
                else:
                    current_streak = 0
                    
            # คำนวณ Max Drawdown
            cumulative = data_sorted["profit_loss"].cumsum()
            peak = cumulative.cummax()
            drawdown = peak - cumulative
            max_dd = drawdown.max() if not drawdown.empty else 0.0

            col1, col2, col3, col4, col5 = st.columns(5)
            col1.metric(f"💰 Net Profit ({bot_name})", f"${total_profit:.2f}")
            col2.metric(f"🎯 Win Rate", f"{win_rate:.1f}%")
            col3.metric(f"📉 Max Drawdown", f"${max_dd:.2f}")
            col4.metric(f"🔥 Max Win Streak", f"{max_streak} ไม้")
            col5.metric(f"📊 Total Closed", f"{total_trades}")

        # 🌟 เรียกใช้งานฟังก์ชันที่ลืมใส่ไป
        st.subheader("⚡ Scrapler (M5) Performance")
        render_kpi("Scrapler", df_closed[df_closed["bot_type"] == "Scrapler ⚡"])
        
        st.subheader("🏰 Swing (H1/H4) Performance")
        render_kpi("Swing", df_closed[df_closed["bot_type"] == "Swing 🏰"])

        st.markdown("---")

        # --- โซนกราฟสถิติ (Line Chart & Bar Chart) ที่แหว่งไป ---
        st.markdown("### 🚀 Profit Analytics")
        col_line, col_bar = st.columns(2)
        
        with col_line:
            df_chart = df_closed.sort_values("timestamp", ascending=True).copy()
            df_chart["cumulative_profit"] = df_chart.groupby("bot_type")["profit_loss"].cumsum()

            fig_line = px.line(
                df_chart, x="timestamp", y="cumulative_profit", color="bot_type",
                markers=True, line_shape="spline", title="📈 การเติบโตของพอร์ต (Equity Curve)",
                color_discrete_map={"Scrapler ⚡": "#00d4ff", "Swing 🏰": "#ffaa00"}
            )
            st.plotly_chart(fig_line, use_container_width=True)

        with col_bar:
            df_bar = df_closed.copy()
            df_bar['date'] = df_bar['timestamp'].dt.date
            daily_profit = df_bar.groupby(['date', 'bot_type'])['profit_loss'].sum().reset_index()

            fig_bar = px.bar(
                daily_profit, x="date", y="profit_loss", color="bot_type", barmode="group",
                title="📊 สรุปกำไร/ขาดทุนรายวัน (Daily Profit & Loss)",
                color_discrete_map={"Scrapler ⚡": "#00d4ff", "Swing 🏰": "#ffaa00"}
            )
            fig_bar.update_layout(xaxis_title="วันที่", yaxis_title="กำไร (USD)")
            st.plotly_chart(fig_bar, use_container_width=True)

    # ==========================================
    # 📜 หน้า 2: Trade History (ประวัติและเจาะลึก AI)
    # ==========================================
    elif page == "📜 Trade History & Filters":
        st.markdown("### 📜 Trade History & AI Thought Process")
        st.subheader("🔍 กรองข้อมูลประวัติ (Filters)")
        
        col1, col2 = st.columns(2)
        with col1:
            filter_bot = st.selectbox("🤖 เลือกบอท:", ["ทั้งหมด (All)", "Scrapler ⚡", "Swing 🏰"])
        with col2:
            filter_time = st.selectbox("📅 ช่วงเวลา:", ["ทั้งหมด (All)", "รายวัน (Today)", "รายสัปดาห์ (This Week)", "รายเดือน (This Month)"])

        df_filtered = df.copy()
        if filter_bot != "ทั้งหมด (All)":
            df_filtered = df_filtered[df_filtered["bot_type"] == filter_bot]

        now = datetime.now()
        if filter_time == "รายวัน (Today)":
            df_filtered = df_filtered[df_filtered["timestamp"].dt.date == now.date()]
        elif filter_time == "รายสัปดาห์ (This Week)":
            df_filtered = df_filtered[df_filtered["timestamp"].dt.isocalendar().week == now.isocalendar().week]
        elif filter_time == "รายเดือน (This Month)":
            df_filtered = df_filtered[df_filtered["timestamp"].dt.month == now.month]

        df_filtered_closed = df_filtered[df_filtered['status'] == 'CLOSED']
        if not df_filtered_closed.empty:
            f_profit = df_filtered_closed['profit_loss'].sum()
            f_trades = len(df_filtered_closed)
            f_wins = len(df_filtered_closed[df_filtered_closed['profit_loss'] > 0])
            f_winrate = (f_wins / f_trades) * 100 if f_trades > 0 else 0
        else:
            f_profit, f_trades, f_winrate = 0, 0, 0

        df_filtered = df_filtered.sort_values("timestamp", ascending=False)
        st.markdown("---")
        st.markdown(f"### 📊 สถิติเฉพาะช่วงเวลา: {filter_time}")
        k_col1, k_col2, k_col3 = st.columns(3)
        k_col1.metric("💵 กำไร/ขาดทุน (P/L)", f"${f_profit:.2f}")
        k_col2.metric("🎯 Win Rate", f"{f_winrate:.2f}%")
        k_col3.metric("📈 จำนวนไม้ที่ปิดแล้ว", f"{f_trades} ไม้")
        st.markdown("---")

        st.markdown(f"**พบข้อมูลประวัติทั้งหมด {len(df_filtered)} รายการ (รวมไม้ที่กำลังเปิดอยู่)**")

        if df_filtered.empty:
            st.info("ไม่พบประวัติการเทรดในช่วงเวลาที่เลือก")
        else:
            for index, row in df_filtered.iterrows():
                status_icon = "🟢" if row["status"] == "OPEN" else "🔒"
                p_color = "🟢" if row["profit_loss"] > 0 else "🔴" if row["profit_loss"] < 0 else "⚪"
                pl_text = f"P/L: {row['profit_loss']} USD {p_color}" if row["status"] == "CLOSED" else "กำลังเทรด..."

                with st.expander(f"{status_icon} [{row['timestamp'].strftime('%Y-%m-%d %H:%M')}] | {row['bot_type']} | {row['action']} | {pl_text}"):
                    st.markdown("#### 📊 ข้อมูล Technical ตอนเข้าเทรด")
                    col_t1, col_t2, col_t3, col_t4 = st.columns(4)
                    col_t1.metric("SL (Stop Loss)", row.get("sl", "N/A"))
                    col_t2.metric("TP (Take Profit)", row.get("tp", "N/A"))
                    col_t3.metric("RSI Fast", row.get("rsi_fast", row.get("rsi", "N/A")))
                    col_t4.metric("Sentiment Score", row.get("sentiment_score", "N/A"))

                    st.markdown("---")
                    st.markdown("#### 🧠 AI Thought Process (กระบวนการคิด)")
                    st.info(row.get("thought_process", "ไม่มีข้อมูล"))
                    st.markdown("#### ⚡ เหตุผลในการตัดสินใจ (Reasoning)")
                    st.success(row.get("reason_text", "ไม่มีข้อมูล"))
