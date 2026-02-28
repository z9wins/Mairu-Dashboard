# --- โซนแสดงกราฟ TradingView และ ปฏิทินข่าว ---
        st.markdown("### 🌐 Live Market & Economic Calendar")
        col_chart, col_news = st.columns([6, 4]) 
        
        with col_chart:
            components.html(
                """
                <div class="tradingview-widget-container">
                  <div id="tradingview_xauusd"></div>
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
                """, height=600  # 🌟 บังคับความสูงกล่อง Streamlit
            )

        with col_news:
            components.html(
                """
                <div class="tradingview-widget-container">
                  <div class="tradingview-widget-container__widget"></div>
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
                """, height=600  # 🌟 บังคับความสูงกล่อง Streamlit
            )
