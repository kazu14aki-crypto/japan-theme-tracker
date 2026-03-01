import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(page_title="日本株テーマトラッカー", layout="wide")
st.title("🇯🇵 日本株テーマトラッカー")

# session_stateの初期化
if "selected_stock" not in st.session_state:
    st.session_state["selected_stock"] = "東京エレクトロン"
if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = "8035.T"
if "page" not in st.session_state:
    st.session_state["page"] = "テーマ一覧"

# 期間選択
period_options = {
    "1週間": "5d",
    "1ヶ月": "1mo",
    "3ヶ月": "3mo",
    "6ヶ月": "6mo",
}
selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()))
period = period_options[selected_label]

# テーマと銘柄
themes = {
    "半導体": {
        "東京エレクトロン": "8035.T",
        "アドバンテスト":   "6857.T",
        "ルネサス":         "6723.T",
        "ディスコ":         "6146.T",
    },
    "AI・クラウド": {
        "富士通":           "6702.T",
        "NEC":              "6701.T",
        "さくらインターネット": "3778.T",
        "KDDI":             "9433.T",
    },
    "EV・電気自動車": {
        "トヨタ":           "7203.T",
        "パナソニック":     "6752.T",
        "住友電気工業":     "5802.T",
        "デンソー":         "6902.T",
    },
    "ゲーム・エンタメ": {
        "任天堂":           "7974.T",
        "ソニー":           "6758.T",
        "カプコン":         "9697.T",
        "バンダイナムコ":   "7832.T",
    },
    "銀行・金融": {
        "三菱UFJ":          "8306.T",
        "三井住友":         "8316.T",
        "みずほ":           "8411.T",
        "りそな":           "8308.T",
    },
    "保険": {
        "東京海上HD":       "8766.T",
        "MS&AD":            "8725.T",
        "第一生命":         "8750.T",
    },
    "不動産": {
        "三井不動産":       "8801.T",
        "住友不動産":       "8830.T",
        "東急不動産HD":     "3289.T",
    },
    "医薬品・バイオ": {
        "武田薬品":         "4502.T",
        "アステラス製薬":   "4503.T",
        "第一三共":         "4568.T",
        "中外製薬":         "4519.T",
    },
    "食品・飲料": {
        "味の素":           "2802.T",
        "キリンHD":         "2503.T",
        "日清食品HD":       "2897.T",
        "明治HD":           "2269.T",
    },
    "小売・EC": {
        "ファーストリテイリング": "9983.T",
        "セブン&アイ":      "3382.T",
        "MonotaRO":         "3064.T",
    },
    "通信": {
        "NTT":              "9432.T",
        "ソフトバンク":     "9434.T",
        "楽天グループ":     "4755.T",
    },
    "鉄鋼・素材": {
        "日本製鉄":         "5401.T",
        "JFEホールディングス": "5411.T",
        "神戸製鋼所":       "5406.T",
    },
    "化学": {
        "信越化学工業":     "4063.T",
        "東レ":             "3402.T",
        "住友化学":         "4005.T",
    },
    "建設・インフラ": {
        "大林組":           "1802.T",
        "鹿島建設":         "1812.T",
        "大成建設":         "1801.T",
    },
    "輸送・物流": {
        "日本郵船":         "9101.T",
        "商船三井":         "9104.T",
        "ヤマトHD":         "9064.T",
    },
}

# ページ切り替え
page = st.sidebar.radio("ページ", ["📊 テーマ一覧", "🔍 個別株詳細"])

if page == "📊 テーマ一覧":

    with st.spinner("株価データを取得中...少々お待ちください"):
        theme_results = []
        theme_details = {}

        for theme_name, stocks in themes.items():
            changes = []
            details = {}
            total_volume = 0
            prev_total_volume = 0

            for stock_name, ticker in stocks.items():
                try:
                    df = yf.Ticker(ticker).history(period="3mo")
                    if len(df) < 2:
                        continue
                    if period == "5d":
                        target_df = df.tail(5)
                    elif period == "1mo":
                        target_df = df.tail(21)
                    elif period == "3mo":
                        target_df = df.tail(63)
                    else:
                        target_df = df

                    start = target_df["Close"].iloc[0]
                    end = target_df["Close"].iloc[-1]
                    change = round((end - start) / start * 100, 2)
                    changes.append(change)

                    half = len(target_df) // 2
                    recent_vol = target_df["Volume"].tail(half).mean()
                    prev_vol = target_df["Volume"].head(half).mean()
                    total_volume += recent_vol
                    prev_total_volume += prev_vol

                    details[stock_name] = {
                        "change": change,
                        "volume": int(recent_vol),
                        "volume_change": round((recent_vol - prev_vol) / prev_vol * 100, 1) if prev_vol > 0 else 0,
                        "ticker": ticker
                    }
                except:
                    pass

            if changes:
                avg = round(sum(changes) / len(changes), 2)
                vol_change = round((total_volume - prev_total_volume) / prev_total_volume * 100, 1) if prev_total_volume > 0 else 0
                theme_results.append({
                    "テーマ": theme_name,
                    "平均騰落率(%)": avg,
                    "出来高増減(%)": vol_change,
                })
                theme_details[theme_name] = details

    # 騰落率でソート
    theme_results.sort(key=lambda x: x["平均騰落率(%)"], reverse=True)
    labels = [r["テーマ"] for r in theme_results]
    values = [r["平均騰落率(%)"] for r in theme_results]
    colors = ["#ff4b4b" if v >= 0 else "#4b8bff" for v in values]

    # Plotlyグラフ（テーマ別騰落率）
    st.subheader("📊 テーマ別騰落率ランキング")
    fig = go.Figure(go.Bar(
        x=labels,
        y=values,
        marker_color=colors,
        text=[f"{v}%" for v in values],
        textposition="outside",
    ))
    fig.update_layout(
        xaxis=dict(tickangle=0, title="テーマ"),
        yaxis=dict(title="騰落率（%）", ticksuffix="%", zeroline=True, zerolinecolor="gray"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=13),
        height=500,
        margin=dict(t=40, b=80),
    )
    st.plotly_chart(fig, use_container_width=True)

    # テーマ一覧
    st.subheader("📋 テーマ一覧")
    for rank, result in enumerate(theme_results, 1):
        change = result["平均騰落率(%)"]
        vol_change = result["出来高増減(%)"]
        change_color = "🔴" if change > 0 else "🔵"
        vol_color = "📈" if vol_change > 0 else "📉"
        st.write(
            f"{rank}位　{change_color}　**{result['テーマ']}**　"
            f"騰落率：{change}%　｜　"
            f"{vol_color} 出来高増減：{vol_change}%"
        )

    # テーマ別詳細
    st.subheader("🔍 テーマ別詳細（クリックで展開）")
    for result in theme_results:
        theme_name = result["テーマ"]
        stocks = theme_details.get(theme_name, {})
        with st.expander(f"{theme_name}　騰落率 {result['平均騰落率(%)']}%　出来高増減 {result['出来高増減(%)']}%"):
            s_labels = list(stocks.keys())
            s_values = [stocks[s]["change"] for s in s_labels]
            s_colors = ["#ff4b4b" if v >= 0 else "#4b8bff" for v in s_values]

            fig2 = go.Figure(go.Bar(
                x=s_labels,
                y=s_values,
                marker_color=s_colors,
                text=[f"{v}%" for v in s_values],
                textposition="outside",
            ))
            fig2.update_layout(
                xaxis=dict(tickangle=0),
                yaxis=dict(title="騰落率（%）", ticksuffix="%", zeroline=True, zerolinecolor="gray"),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=12),
                height=350,
                margin=dict(t=20, b=60),
            )
            st.plotly_chart(fig2, use_container_width=True)

            for stock_name, data in stocks.items():
                c = "🔴" if data["change"] > 0 else "🔵"
                v = "📈" if data["volume_change"] > 0 else "📉"
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"{c} **{stock_name}**　騰落率：{data['change']}%　{v} 出来高増減：{data['volume_change']}%")
                with col2:
                    if st.button("詳細チャート", key=stock_name):
                        st.session_state["selected_stock"] = stock_name
                        st.session_state["selected_ticker"] = data["ticker"]
                        st.rerun()

elif page == "🔍 個別株詳細":

    all_stocks = {}
    for stocks in themes.values():
        for name, ticker in stocks.items():
            all_stocks[name] = ticker

    selected_name = st.sidebar.selectbox(
        "銘柄を選択",
        list(all_stocks.keys()),
        index=list(all_stocks.keys()).index(st.session_state.get("selected_stock", list(all_stocks.keys())[0]))
    )
    selected_ticker = all_stocks[selected_name]

    st.subheader(f"📈 {selected_name} 詳細チャート")

    with st.spinner("データ取得中..."):
        df = yf.Ticker(selected_ticker).history(period=period)

    if len(df) > 0:
        # 株価チャート（Plotly）
        st.write("**株価推移**")
        fig3 = go.Figure(go.Scatter(
            x=df.index, y=df["Close"],
            mode="lines",
            line=dict(color="#ff4b4b", width=2),
            fill="tozeroy",
            fillcolor="rgba(255,75,75,0.1)"
        ))
        fig3.update_layout(
            xaxis=dict(title="日付"),
            yaxis=dict(title="株価（円）", tickprefix="¥"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=400,
        )
        st.plotly_chart(fig3, use_container_width=True)

        # 出来高チャート（Plotly）
        st.write("**出来高推移**")
        fig4 = go.Figure(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color="#4b8bff",
        ))
        fig4.update_layout(
            xaxis=dict(title="日付"),
            yaxis=dict(title="出来高"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=300,
        )
        st.plotly_chart(fig4, use_container_width=True)

        # メトリクス
        half = len(df) // 2
        recent_vol = df["Volume"].tail(half).mean()
        prev_vol = df["Volume"].head(half).mean()
        vol_change = round((recent_vol - prev_vol) / prev_vol * 100, 1)
        price_change = round((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100, 2)

        col1, col2, col3 = st.columns(3)
        col1.metric("現在株価", f"¥{int(df['Close'].iloc[-1]):,}")
        col2.metric("騰落率", f"{price_change}%")
        col3.metric("出来高増減", f"{vol_change}%")
    else:
        st.error("データを取得できませんでした")
