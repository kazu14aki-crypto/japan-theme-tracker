import streamlit as st
import yfinance as yf
import pandas as pd
st.title("🇯🇵 日本株テーマトラッカー")
period_options = {
    "1週間": "5d",
    "1ヶ月": "1mo",
    "3ヶ月": "3mo",
    "6ヶ月": "6mo",
}
selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()))
period = period_options[selected_label]
themes = {
    "半導体": {
        "東京エレクトロン": "8035.T",
        "ルネサス":         "6723.T",
        "アドバンテスト":   "6857.T",
    },
    "EV・電気自動車": {
        "トヨタ":       "7203.T",
        "パナソニック": "6752.T",
        "住友電気工業": "5802.T",
    },
    "ゲーム": {
        "任天堂": "7974.T",
        "ソニー": "6758.T",
        "カプコン": "9697.T",
    },
    "AI・クラウド": {
        "富士通":   "6702.T",
        "NEC":      "6701.T",
        "さくらインターネット": "3778.T",
    },
    "銀行・金融": {
        "三菱UFJ": "8306.T",
        "三井住友": "8316.T",
        "みずほ":  "8411.T",
    },
}
with st.spinner("株価データを取得中..."):
    theme_results = []
    theme_details = {}

    for theme_name, stocks in themes.items():
        changes = []
        details = {}
        for stock_name, ticker in stocks.items():
            try:
                df = yf.Ticker(ticker).history(period=period)
                start = df["Close"].iloc[0]
                end = df["Close"].iloc[-1]
                change = round((end - start) / start * 100, 2)
                changes.append(change)
                details[stock_name] = change
            except:
                details[stock_name] = None
        avg = round(sum(changes) / len(changes), 2)
        theme_results.append({"テーマ": theme_name, "平均騰落率(%)": avg})
        theme_details[theme_name] = details
theme_results.sort(key=lambda x: x["平均騰落率(%)"], reverse=True)
df_themes = pd.DataFrame(theme_results).set_index("テーマ")

st.subheader("📊 テーマ別騰落率ランキング")
st.bar_chart(df_themes)
for rank, result in enumerate(theme_results, 1):
    change = result["平均騰落率(%)"]
    color = "🔴" if change > 0 else "🔵"
    st.write(f"{rank}位　{color}　**{result['テーマ']}**　{change}%")
st.subheader("🔍 テーマ別詳細")
for theme_name, stocks in theme_details.items():
    with st.expander(theme_name):
        detail_data = {
            "銘柄": list(stocks.keys()),
            "騰落率(%)": list(stocks.values())
        }
        df_detail = pd.DataFrame(detail_data).set_index("銘柄")
        st.bar_chart(df_detail)
