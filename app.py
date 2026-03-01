import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(
    page_title="日本株テーマトラッカー",
    page_icon="🇯🇵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🇯🇵 日本株テーマトラッカー")

# スマホ対応CSS
st.markdown("""
<style>
div.stButton > button {
    width: 100%;
    height: 3em;
    font-size: 1em;
}
.stPlotlyChart { overflow-x: auto; }
@media (max-width: 640px) {
    h1 { font-size: 1.5em !important; }
    h2 { font-size: 1.2em !important; }
}
</style>
""", unsafe_allow_html=True)

# session_stateの初期化
if "selected_stock" not in st.session_state:
    st.session_state["selected_stock"] = "東京エレクトロン"
if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = "8035.T"
if "page" not in st.session_state:
    st.session_state["page"] = "テーマ一覧"
if "favorites" not in st.session_state:
    st.session_state["favorites"] = {}  # {"銘柄名": "ティッカー"}

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
        "富士通":               "6702.T",
        "NEC":                  "6701.T",
        "さくらインターネット": "3778.T",
        "KDDI":                 "9433.T",
    },
    "EV・電気自動車": {
        "トヨタ":       "7203.T",
        "パナソニック": "6752.T",
        "住友電気工業": "5802.T",
        "デンソー":     "6902.T",
    },
    "ゲーム・エンタメ": {
        "任天堂":         "7974.T",
        "ソニー":         "6758.T",
        "カプコン":       "9697.T",
        "バンダイナムコ": "7832.T",
    },
    "銀行・金融": {
        "三菱UFJ": "8306.T",
        "三井住友": "8316.T",
        "みずほ":   "8411.T",
        "りそな":   "8308.T",
    },
    "保険": {
        "東京海上HD": "8766.T",
        "MS&AD":      "8725.T",
        "第一生命":   "8750.T",
    },
    "不動産": {
        "三井不動産":   "8801.T",
        "住友不動産":   "8830.T",
        "東急不動産HD": "3289.T",
    },
    "医薬品・バイオ": {
        "武田薬品":       "4502.T",
        "アステラス製薬": "4503.T",
        "第一三共":       "4568.T",
        "中外製薬":       "4519.T",
    },
    "食品・飲料": {
        "味の素":     "2802.T",
        "キリンHD":   "2503.T",
        "日清食品HD": "2897.T",
        "明治HD":     "2269.T",
    },
    "小売・EC": {
        "ファーストリテイリング": "9983.T",
        "セブン&アイ":           "3382.T",
        "MonotaRO":              "3064.T",
    },
    "通信": {
        "NTT":          "9432.T",
        "ソフトバンク": "9434.T",
        "楽天グループ": "4755.T",
    },
    "鉄鋼・素材": {
        "日本製鉄":            "5401.T",
        "JFEホールディングス": "5411.T",
        "神戸製鋼所":          "5406.T",
    },
    "化学": {
        "信越化学工業": "4063.T",
        "東レ":         "3402.T",
        "住友化学":     "4005.T",
    },
    "建設・インフラ": {
        "大林組":   "1802.T",
        "鹿島建設": "1812.T",
        "大成建設": "1801.T",
    },
    "輸送・物流": {
        "日本郵船": "9101.T",
        "商船三井": "9104.T",
        "ヤマトHD": "9064.T",
    },
}

# グラフ設定
PLOT_CONFIG = {
    "displayModeBar": False,
    "staticPlot": True,
}

def make_bar_chart(labels, values, colors, height=520, left_margin=140):
    text_positions = []
    text_colors = []
    for v in values:
        if abs(v) > 3:
            text_positions.append("inside")
            text_colors.append("white")
        else:
            text_positions.append("outside")
            text_colors.append("white")
    fig = go.Figure(go.Bar(
        y=labels,
        x=values,
        orientation="h",
        marker_color=colors,
        text=[f"{v}%" for v in values],
        textposition=text_positions,
        textfont=dict(color=text_colors, size=11),
        insidetextanchor="middle",
    ))
    fig.update_layout(
        xaxis=dict(
            title="騰落率（%）",
            ticksuffix="%",
            zeroline=True,
            zerolinecolor="gray",
            zerolinewidth=1,
            range=[
                min(values) * 1.3 if min(values) < 0 else -2,
                max(values) * 1.3 if max(values) > 0 else 2,
            ],
        ),
        yaxis=dict(title="", autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=11),
        height=height,
        margin=dict(t=30, b=50, l=left_margin, r=20),
    )
    return fig

# ページ切り替え（お気に入りページを追加）
page = st.sidebar.radio("ページ", [
    "📊 テーマ一覧",
    "⭐ お気に入り",
    "🔍 個別株詳細",
])

# お気に入りの件数をサイドバーに表示
fav_count = len(st.session_state["favorites"])
if fav_count > 0:
    st.sidebar.info(f"⭐ お気に入り登録中：{fav_count}銘柄")

# =====================
# テーマ一覧ページ
# =====================
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

    theme_results.sort(key=lambda x: x["平均騰落率(%)"], reverse=True)
    labels = [r["テーマ"] for r in theme_results]
    values = [r["平均騰落率(%)"] for r in theme_results]
    colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in values]

    st.subheader("📊 テーマ別騰落率ランキング")
    fig = make_bar_chart(labels, values, colors, height=520, left_margin=140)
    st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

    # テーマ一覧（表形式）
    st.subheader("📋 テーマ一覧")
    table_data = []
    for rank, result in enumerate(theme_results, 1):
        change = result["平均騰落率(%)"]
        vol_change = result["出来高増減(%)"]
        change_str = f"🔴 +{change}%" if change > 0 else f"🟢 {change}%"
        vol_str = f"📈 +{vol_change}%" if vol_change > 0 else f"📉 {vol_change}%"
        table_data.append({
            "順位": f"{rank}位",
            "テーマ": result["テーマ"],
            "騰落率": change_str,
            "出来高増減": vol_str,
        })
    df_table = pd.DataFrame(table_data).set_index("順位")
    st.dataframe(df_table, use_container_width=True)

    # テーマ別詳細
    st.subheader("🔍 テーマ別詳細（クリックで展開）")
    for result in theme_results:
        theme_name = result["テーマ"]
        stocks = theme_details.get(theme_name, {})
        with st.expander(f"{theme_name}　騰落率 {result['平均騰落率(%)']}%　出来高増減 {result['出来高増減(%)']}%"):
            s_labels = list(stocks.keys())
            s_values = [stocks[s]["change"] for s in s_labels]
            s_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in s_values]

            fig2 = make_bar_chart(s_labels, s_values, s_colors, height=280, left_margin=130)
            st.plotly_chart(fig2, use_container_width=True, config=PLOT_CONFIG)

            for stock_name, data in stocks.items():
                c = "🔴" if data["change"] > 0 else "🟢"
                v = "📈" if data["volume_change"] > 0 else "📉"
                is_fav = stock_name in st.session_state["favorites"]

                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    st.write(f"{c} **{stock_name}**　騰落率：{data['change']}%　{v} 出来高増減：{data['volume_change']}%")
                with col2:
                    if st.button("詳細チャート", key=f"chart_{stock_name}"):
                        st.session_state["selected_stock"] = stock_name
                        st.session_state["selected_ticker"] = data["ticker"]
                        st.rerun()
                with col3:
                    if is_fav:
                        if st.button("⭐ 解除", key=f"fav_{stock_name}"):
                            del st.session_state["favorites"][stock_name]
                            st.rerun()
                    else:
                        if st.button("☆ 登録", key=f"fav_{stock_name}"):
                            st.session_state["favorites"][stock_name] = data["ticker"]
                            st.rerun()

# =====================
# お気に入りページ
# =====================
elif page == "⭐ お気に入り":

    st.subheader("⭐ お気に入り銘柄")

    if len(st.session_state["favorites"]) == 0:
        st.info("まだお気に入り登録がありません。テーマ一覧ページで「☆ 登録」ボタンを押して追加してください。")
    else:
        with st.spinner("データを取得中..."):
            fav_results = []
            for stock_name, ticker in st.session_state["favorites"].items():
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

                    half = len(target_df) // 2
                    recent_vol = target_df["Volume"].tail(half).mean()
                    prev_vol = target_df["Volume"].head(half).mean()
                    vol_change = round((recent_vol - prev_vol) / prev_vol * 100, 1) if prev_vol > 0 else 0

                    fav_results.append({
                        "銘柄": stock_name,
                        "ticker": ticker,
                        "change": change,
                        "vol_change": vol_change,
                        "price": int(target_df["Close"].iloc[-1]),
                    })
                except:
                    pass

        # 騰落率でソート
        fav_results.sort(key=lambda x: x["change"], reverse=True)

        # お気に入りグラフ
        fav_labels = [r["銘柄"] for r in fav_results]
        fav_values = [r["change"] for r in fav_results]
        fav_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in fav_values]

        fig_fav = make_bar_chart(fav_labels, fav_values, fav_colors,
                                  height=max(300, len(fav_results) * 50),
                                  left_margin=130)
        st.plotly_chart(fig_fav, use_container_width=True, config=PLOT_CONFIG)

        # お気に入り一覧表
        st.subheader("📋 お気に入り一覧")
        table_data = []
        for r in fav_results:
            change_str = f"🔴 +{r['change']}%" if r["change"] > 0 else f"🟢 {r['change']}%"
            vol_str = f"📈 +{r['vol_change']}%" if r["vol_change"] > 0 else f"📉 {r['vol_change']}%"
            table_data.append({
                "銘柄": r["銘柄"],
                "現在株価": f"¥{r['price']:,}",
                "騰落率": change_str,
                "出来高増減": vol_str,
            })
        df_fav = pd.DataFrame(table_data).set_index("銘柄")
        st.dataframe(df_fav, use_container_width=True)

        # 個別ボタン
        st.subheader("🔍 詳細・登録解除")
        for r in fav_results:
            c = "🔴" if r["change"] > 0 else "🟢"
            v = "📈" if r["vol_change"] > 0 else "📉"
            col1, col2, col3 = st.columns([3, 1, 1])
            with col1:
                st.write(f"{c} **{r['銘柄']}**　{r['change']}%　{v} {r['vol_change']}%")
            with col2:
                if st.button("詳細チャート", key=f"fav_chart_{r['銘柄']}"):
                    st.session_state["selected_stock"] = r["銘柄"]
                    st.session_state["selected_ticker"] = r["ticker"]
                    st.rerun()
            with col3:
                if st.button("⭐ 解除", key=f"fav_del_{r['銘柄']}"):
                    del st.session_state["favorites"][r["銘柄"]]
                    st.rerun()

# =====================
# 個別株詳細ページ
# =====================
elif page == "🔍 個別株詳細":

    all_stocks = {}
    for stocks in themes.values():
        for name, ticker in stocks.items():
            all_stocks[name] = ticker

    selected_name = st.sidebar.selectbox(
        "銘柄を選択",
        list(all_stocks.keys()),
        index=list(all_stocks.keys()).index(
            st.session_state.get("selected_stock", list(all_stocks.keys())[0])
        )
    )
    selected_ticker = all_stocks[selected_name]

    st.subheader(f"📈 {selected_name} 詳細チャート")

    # お気に入りボタン
    is_fav = selected_name in st.session_state["favorites"]
    if is_fav:
        if st.button("⭐ お気に入り解除"):
            del st.session_state["favorites"][selected_name]
            st.rerun()
    else:
        if st.button("☆ お気に入りに追加"):
            st.session_state["favorites"][selected_name] = selected_ticker
            st.rerun()

    with st.spinner("データ取得中..."):
        df = yf.Ticker(selected_ticker).history(period=period)

    if len(df) > 0:
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
            margin=dict(t=30, b=50, l=70, r=20),
        )
        st.plotly_chart(fig3, use_container_width=True, config=PLOT_CONFIG)

        st.write("**出来高推移**")
        vol_colors = ["#ff4b4b" if df["Close"].iloc[i] >= df["Close"].iloc[i-1]
                      else "#39d353" for i in range(len(df))]
        fig4 = go.Figure(go.Bar(
            x=df.index, y=df["Volume"],
            marker_color=vol_colors,
        ))
        fig4.update_layout(
            xaxis=dict(title="日付"),
            yaxis=dict(title="出来高"),
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=300,
            margin=dict(t=30, b=50, l=70, r=20),
        )
        st.plotly_chart(fig4, use_container_width=True, config=PLOT_CONFIG)

        half = len(df) // 2
        recent_vol = df["Volume"].tail(half).mean()
        prev_vol = df["Volume"].head(half).mean()
        vol_change = round((recent_vol - prev_vol) / prev_vol * 100, 1)
        price_change = round(
            (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100, 2
        )

        col1, col2, col3 = st.columns(3)
        col1.metric("現在株価", f"¥{int(df['Close'].iloc[-1]):,}")
        col2.metric("騰落率", f"{price_change}%")
        col3.metric("出来高増減", f"{vol_change}%")
    else:
        st.error("データを取得できませんでした")
