import streamlit as st
import pandas as pd
import streamlit.components.v1 as components
import os

# ==========================================
# ⚙️ ตั้งค่าหน้าเว็บให้เป็นแบบเต็มจอ (Wide Layout) และ Dark Mode เบื้องต้น
# ==========================================
st.set_page_config(page_title="Mairu AI Trading", page_icon="🤖", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# 📊 ฟังก์ชันอ่านข้อมูลจาก Database ของบอท
# ==========================================
@st.cache_data(ttl=60) # รีเฟรชข้อมูลทุก 60 วินาที
def load_data():
    # กำหนด Path ไปหาไฟล์ CSV ของบอท (แก้ Path ให้ตรงกับเครื่อง)
    swing_path = r"C:\Mairu_AI_wing\trade_performance_db.csv"
    scrapler_path = r"C:\Mairu_AI_Scrapler\trade_performance_db.csv"
    
    df_list = []
    if os.path.exists(swing_path):
        df_swing = pd.read_csv(swing_path, on_bad_lines="skip")
        df_swing['Bot'] = 'Swing (H1)'
        df_list.append(df_swing)
        
    if os.path.exists(scrapler_path):
        df_scrapler = pd.read_csv(scrapler_path, on_bad_lines="skip")
        df_scrapler['Bot'] = 'Scrapler (M5)'
        df_list.append(df_scrapler)
        
    if df_list:
        df_all = pd.concat(df_list, ignore_index=True)
        # แปลงข้อมูลเวลา
        df_all['timestamp'] = pd.to_datetime(df_all['timestamp'])
        df_all = df_all.sort_values(by='timestamp', ascending=False)
        return df_all
    return pd.DataFrame()

df = load_data()

# ==========================================
# 🧭 Sidebar Navigation (เมนูด้านซ้าย)
# ==========================================
st.sidebar.image("https://img.icons8.com/fluency/96/artificial-intelligence.png", width=60)
st.sidebar.title("Mairu.AI System")
menu = st.sidebar.radio("📌 Navigation", ["📊 Market Overview", "📋 Trade History & Filters"])

st.sidebar.markdown("---")
st.sidebar.info("💡 **Status:** Bots are running 24/7\n\n🔄 Data auto-refreshes every 1 min.")

# ==========================================
# 🟢 หน้า 1: Market Overview (กราฟ + ข่าว + สถิติ)
# ==========================================
if menu == "📊 Market Overview":
    st.title("📈 Market Overview & Real-Time Setup")
    
    # 🌟 โซนโชว์ตัวเลขสถิติภาพรวม (จำลองข้อมูล)
    col1, col2, col3, col4 = st.columns(4)
    if not df.empty:
        total_trades = len(df)
        win_trades = len(df[df['profit_loss'] > 0])
        total_profit = df['profit_loss'].sum()
        win_rate = (win_trades / total_trades) * 100 if total_trades > 0 else 0
    else:
        total_trades, total_profit, win_rate = 0, 0.0, 0.0

    col1.metric("Total Profit", f"${total_profit:.2f}", f"{total_profit:.2f} Today")
    col2.metric("Win Rate", f"{win_rate:.1f}%", "-")
    col3.metric("Total Trades", f"{total_trades}", "Active bots: 2")
    col4.metric("System Status", "Online 🟢", "Latency: 12ms")
    
    st.markdown("---")
    
    # 🌟 โซนแสดงกราฟ TradingView และปฏิทินข่าว
    col_chart, col_news = st.columns([7, 3]) # แบ่งสัดส่วนจอ กราฟ 70% ข่าว 30%
    
    with col_chart:
        st.subheader("🪙 XAU/USD Live Chart")
        # ฝัง Widget TradingView กราฟทองคำ (ปรับเป็น Dark Mode อัตโนมัติ)
        components.html(
            """
            <div class="tradingview-widget-container" style="height: 500px;">
              <div id="tradingview_xauusd" style="height: 100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/tv.js"></script>
              <script type="text/javascript">
              new TradingView.widget({
              "autosize": true,
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
            """, height=500
        )

    with col_news:
        st.subheader("📅 Economic Calendar (TH Time)")
        # ฝัง Widget ปฏิทินเศรษฐกิจ (ตั้งค่าเวลาไทย Asia/Bangkok)
        components.html(
            """
            <div class="tradingview-widget-container" style="height: 500px;">
              <div class="tradingview-widget-container__widget" style="height: 100%;"></div>
              <script type="text/javascript" src="https://s3.tradingview.com/external-embedding/embed-widget-events.js" async>
              {
              "colorTheme": "dark",
              "isTransparent": false,
              "width": "100%",
              "height": "100%",
              "locale": "th_TH",
              "importanceFilter": "0,1",
              "currencyFilter": "USD,EUR,GBP,JPY,AUD,CAD,CHF,CNY"
            }
              </script>
            </div>
            """, height=500
        )

# ==========================================
# 🔵 หน้า 2: Trade History (ตารางประวัติ + ฟิลเตอร์)
# ==========================================
elif menu == "📋 Trade History & Filters":
    st.title("🗂️ Trade Performance & Filtering")
    
    if df.empty:
        st.warning("⚠️ No trade data found. Please check if the bot has generated trade_performance_db.csv")
    else:
        # 🌟 โซนเครื่องมือ Filter
        st.markdown("### 🔍 Filter Options")
        f_col1, f_col2, f_col3 = st.columns(3)
        
        bot_filter = f_col1.multiselect("🤖 Select Bot", options=df['Bot'].unique(), default=df['Bot'].unique())
        action_filter = f_col2.multiselect("🛒 Action", options=df['action'].unique(), default=df['action'].unique())
        status_filter = f_col3.multiselect("📌 Status", options=df['status'].unique(), default=df['status'].unique())
        
        # กรองข้อมูลตามที่เลือก
        filtered_df = df[
            (df['Bot'].isin(bot_filter)) &
            (df['action'].isin(action_filter)) &
            (df['status'].isin(status_filter))
        ]
        
        # 🌟 แสดงตารางข้อมูลแบบ Interactive (กดเรียงลำดับได้)
        st.markdown(f"**Showing {len(filtered_df)} trades**")
        st.dataframe(
            filtered_df[['timestamp', 'Bot', 'action', 'status', 'profit_loss', 'sl', 'tp', 'thought_process']],
            use_container_width=True,
            hide_index=True
        )
