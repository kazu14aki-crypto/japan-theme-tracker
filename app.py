import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime

st.set_page_config(
    page_title="日本株テーマトラッカー",
    page_icon="🇯🇵",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.title("🇯🇵 日本株テーマトラッカー")

st.markdown("""
<style>
div.stButton > button { width: 100%; height: 3em; font-size: 1em; }
.stPlotlyChart { overflow-x: auto; }
@media (max-width: 640px) {
    h1 { font-size: 1.5em !important; }
    h2 { font-size: 1.2em !important; }
}
</style>
""", unsafe_allow_html=True)

# session_state初期化
if "selected_stock" not in st.session_state:
    st.session_state["selected_stock"] = "東京エレクトロン"
if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = "8035.T"
if "favorites" not in st.session_state:
    st.session_state["favorites"] = {}

# テーマと銘柄
themes = {
    "半導体": {"東京エレクトロン":"8035.T","アドバンテスト":"6857.T","ルネサス":"6723.T","ディスコ":"6146.T"},
    "AI・クラウド": {"富士通":"6702.T","NEC":"6701.T","さくらインターネット":"3778.T","KDDI":"9433.T"},
    "EV・電気自動車": {"トヨタ":"7203.T","パナソニック":"6752.T","住友電気工業":"5802.T","デンソー":"6902.T"},
    "ゲーム・エンタメ": {"任天堂":"7974.T","ソニー":"6758.T","カプコン":"9697.T","バンダイナムコ":"7832.T"},
    "銀行・金融": {"三菱UFJ":"8306.T","三井住友":"8316.T","みずほ":"8411.T","りそな":"8308.T"},
    "保険": {"東京海上HD":"8766.T","MS&AD":"8725.T","第一生命":"8750.T"},
    "不動産": {"三井不動産":"8801.T","住友不動産":"8830.T","東急不動産HD":"3289.T"},
    "医薬品・バイオ": {"武田薬品":"4502.T","アステラス製薬":"4503.T","第一三共":"4568.T","中外製薬":"4519.T"},
    "食品・飲料": {"味の素":"2802.T","キリンHD":"2503.T","日清食品HD":"2897.T","明治HD":"2269.T"},
    "小売・EC": {"ファーストリテイリング":"9983.T","セブン&アイ":"3382.T","MonotaRO":"3064.T"},
    "通信": {"NTT":"9432.T","ソフトバンク":"9434.T","楽天グループ":"4755.T"},
    "鉄鋼・素材": {"日本製鉄":"5401.T","JFEホールディングス":"5411.T","神戸製鋼所":"5406.T"},
    "化学": {"信越化学工業":"4063.T","東レ":"3402.T","住友化学":"4005.T"},
    "建設・インフラ": {"大林組":"1802.T","鹿島建設":"1812.T","大成建設":"1801.T"},
    "輸送・物流": {"日本郵船":"9101.T","商船三井":"9104.T","ヤマトHD":"9064.T"},
}

all_stocks = {}
for stocks in themes.values():
    for name, ticker in stocks.items():
        all_stocks[name] = ticker

PLOT_CONFIG = {"displayModeBar": False, "staticPlot": True}
period_options = {"1週間":"5d","1ヶ月":"1mo","3ヶ月":"3mo","6ヶ月":"6mo"}

# =====================
# ユーティリティ関数
# =====================
def get_target_df(df, period):
    if period == "5d": return df.tail(5)
    elif period == "1mo": return df.tail(21)
    elif period == "3mo": return df.tail(63)
    return df

def calc_change(df):
    if len(df) < 2: return None
    return round((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100, 2)

def calc_vol_change(df):
    half = len(df) // 2
    if half == 0: return 0
    r = df["Volume"].tail(half).mean()
    p = df["Volume"].head(half).mean()
    return round((r - p) / p * 100, 1) if p > 0 else 0

def calc_rsi(series, period=14):
    delta = series.diff()
    gain = delta.clip(lower=0).rolling(period).mean()
    loss = (-delta.clip(upper=0)).rolling(period).mean()
    rs = gain / loss
    return 100 - (100 / (1 + rs))

def calc_macd(series, fast=12, slow=26, signal=9):
    ema_fast = series.ewm(span=fast, adjust=False).mean()
    ema_slow = series.ewm(span=slow, adjust=False).mean()
    macd = ema_fast - ema_slow
    sig = macd.ewm(span=signal, adjust=False).mean()
    return macd, sig, macd - sig

def calc_sharpe(series, rf=0.001):
    ret = series.pct_change().dropna()
    if ret.std() == 0 or len(ret) < 5: return None
    return round((ret.mean() - rf/252) / ret.std() * np.sqrt(252), 2)

def format_large_number(n):
    if n is None: return "N/A"
    if n >= 1e12: return f"{n/1e12:.1f}兆円"
    elif n >= 1e8: return f"{n/1e8:.0f}億円"
    return f"{n:,.0f}円"

def get_fundamentals(ticker):
    try:
        info = yf.Ticker(ticker).info
        return {
            "PER": round(info.get("trailingPE"), 1) if info.get("trailingPE") else None,
            "PBR": round(info.get("priceToBook"), 1) if info.get("priceToBook") else None,
            "時価総額": format_large_number(info.get("marketCap")),
            "売上高": format_large_number(info.get("totalRevenue")),
            "EPS": round(info.get("trailingEps"), 1) if info.get("trailingEps") else None,
        }
    except:
        return {"PER":None,"PBR":None,"時価総額":"N/A","売上高":"N/A","EPS":None}

def make_bar_chart(labels, values, colors, height=520, left_margin=140):
    text_positions = ["inside" if abs(v) > 3 else "outside" for v in values]
    fig = go.Figure(go.Bar(
        y=labels, x=values, orientation="h",
        marker_color=colors,
        text=[f"{v}%" for v in values],
        textposition=text_positions,
        textfont=dict(color="white", size=11),
        insidetextanchor="middle",
    ))
    fig.update_layout(
        xaxis=dict(title="騰落率（%）", ticksuffix="%", zeroline=True, zerolinecolor="gray",
                   range=[min(values)*1.3 if min(values)<0 else -2,
                          max(values)*1.3 if max(values)>0 else 2]),
        yaxis=dict(title="", autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=11),
        height=height, margin=dict(t=30, b=50, l=left_margin, r=20),
    )
    return fig

def make_price_chart(df, chart_type="ローソク足", show_ma=True):
    """株価チャート（ローソク足 or 折れ線 + 移動平均線）"""
    fig = go.Figure()

    if chart_type == "ローソク足":
        fig.add_trace(go.Candlestick(
            x=df.index,
            open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            increasing_line_color="#ff4b4b",
            decreasing_line_color="#39d353",
            name="株価",
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"],
            mode="lines", line=dict(color="#ff4b4b", width=2),
            fill="tozeroy", fillcolor="rgba(255,75,75,0.1)",
            name="終値",
        ))

    if show_ma and len(df) >= 25:
        ma25 = df["Close"].rolling(25).mean()
        fig.add_trace(go.Scatter(
            x=df.index, y=ma25,
            mode="lines", line=dict(color="#ffd700", width=1.5, dash="dot"),
            name="25日移動平均",
        ))
    if show_ma and len(df) >= 75:
        ma75 = df["Close"].rolling(75).mean()
        fig.add_trace(go.Scatter(
            x=df.index, y=ma75,
            mode="lines", line=dict(color="#4b8bff", width=1.5, dash="dot"),
            name="75日移動平均",
        ))

    fig.update_layout(
        xaxis=dict(title="日付", rangeslider=dict(visible=False)),
        yaxis=dict(title="株価（円）", tickprefix="¥"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"), height=420,
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=40, b=40, l=70, r=20),
    )
    return fig

# ページ切り替え
page = st.sidebar.radio("ページ", [
    "📊 テーマ一覧",
    "🔥 ヒートマップ",
    "📉 テーマ比較",
    "🌍 マクロ比較",
    "🔎 銘柄検索",
    "⭐ お気に入り",
    "🔍 個別株詳細",
])

fav_count = len(st.session_state["favorites"])
if fav_count > 0:
    st.sidebar.info(f"⭐ お気に入り：{fav_count}銘柄")

now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

# =====================
# テーマ一覧
# =====================
if page == "📊 テーマ一覧":
    st.caption(f"🕐 最終更新：{now}")
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()))
    period = period_options[selected_label]

    with st.spinner("株価データを取得中..."):
        theme_results = []
        theme_details = {}

        for theme_name, stocks in themes.items():
            changes, details = [], {}
            total_vol = prev_total_vol = 0

            for stock_name, ticker in stocks.items():
                try:
                    df = yf.Ticker(ticker).history(period="3mo")
                    if len(df) < 2: continue
                    target_df = get_target_df(df, period)
                    change = calc_change(target_df)
                    if change is None: continue
                    changes.append(change)

                    half = len(target_df) // 2
                    rv = target_df["Volume"].tail(half).mean()
                    pv = target_df["Volume"].head(half).mean()
                    total_vol += rv; prev_total_vol += pv

                    # 前日比
                    prev_close = df["Close"].iloc[-2] if len(df) >= 2 else None
                    last_close = df["Close"].iloc[-1]
                    day_change = round((last_close - prev_close) / prev_close * 100, 2) if prev_close else None

                    rsi_val = round(calc_rsi(df["Close"]).iloc[-1], 1)
                    sharpe = calc_sharpe(target_df["Close"])

                    # 52週高値・安値
                    df_52w = yf.Ticker(ticker).history(period="1y")
                    w52_high = round(df_52w["High"].max(), 0) if len(df_52w) > 0 else None
                    w52_low = round(df_52w["Low"].min(), 0) if len(df_52w) > 0 else None

                    details[stock_name] = {
                        "change": change,
                        "day_change": day_change,
                        "volume_change": round((rv-pv)/pv*100,1) if pv>0 else 0,
                        "ticker": ticker,
                        "rsi": rsi_val,
                        "sharpe": sharpe,
                        "52w_high": w52_high,
                        "52w_low": w52_low,
                        "price": round(last_close, 0),
                    }
                except:
                    pass

            if changes:
                avg = round(sum(changes)/len(changes), 2)
                vol_chg = round((total_vol-prev_total_vol)/prev_total_vol*100,1) if prev_total_vol>0 else 0
                theme_results.append({"テーマ":theme_name,"平均騰落率(%)":avg,"出来高増減(%)":vol_chg})
                theme_details[theme_name] = details

    theme_results.sort(key=lambda x: x["平均騰落率(%)"], reverse=True)
    labels = [r["テーマ"] for r in theme_results]
    values = [r["平均騰落率(%)"] for r in theme_results]
    colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in values]

    st.subheader("📊 テーマ別騰落率ランキング")
    st.plotly_chart(make_bar_chart(labels, values, colors, 520, 140), use_container_width=True, config=PLOT_CONFIG)

    st.subheader("📋 テーマ一覧")
    table_data = []
    for rank, r in enumerate(theme_results, 1):
        c, v = r["平均騰落率(%)"], r["出来高増減(%)"]
        table_data.append({"順位":f"{rank}位","テーマ":r["テーマ"],
                           "騰落率":f"🔴 +{c}%" if c>0 else f"🟢 {c}%",
                           "出来高増減":f"📈 +{v}%" if v>0 else f"📉 {v}%"})
    df_table = pd.DataFrame(table_data).set_index("順位")
    st.dataframe(df_table, use_container_width=True)
    st.download_button("📥 CSVダウンロード", df_table.to_csv(encoding="utf-8-sig"),
                       f"テーマ一覧_{now}.csv", "text/csv")

    st.subheader("🔍 テーマ別詳細（クリックで展開）")
    for result in theme_results:
        theme_name = result["テーマ"]
        stocks = theme_details.get(theme_name, {})
        with st.expander(f"{theme_name}　騰落率 {result['平均騰落率(%)']}%　出来高増減 {result['出来高増減(%)']}%"):
            s_labels = list(stocks.keys())
            s_values = [stocks[s]["change"] for s in s_labels]
            s_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in s_values]
            st.plotly_chart(make_bar_chart(s_labels, s_values, s_colors, 280, 130),
                            use_container_width=True, config=PLOT_CONFIG)

            stock_table = []
            for sn, d in stocks.items():
                rsi = d.get("rsi")
                rsi_alert = "⚠️買" if rsi and rsi>70 else "⚠️売" if rsi and rsi<30 else "✅"
                day_c = d.get("day_change")
                stock_table.append({
                    "銘柄": sn,
                    "現在株価": f"¥{int(d['price']):,}",
                    "前日比": f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                    "期間騰落率": f"🔴 +{d['change']}%" if d["change"]>0 else f"🟢 {d['change']}%",
                    "出来高増減": f"📈 +{d['volume_change']}%" if d["volume_change"]>0 else f"📉 {d['volume_change']}%",
                    "RSI": f"{rsi} {rsi_alert}" if rsi else "N/A",
                    "シャープレシオ": f"{d['sharpe']}" if d["sharpe"] else "N/A",
                    "52週高値": f"¥{int(d['52w_high']):,}" if d["52w_high"] else "N/A",
                    "52週安値": f"¥{int(d['52w_low']):,}" if d["52w_low"] else "N/A",
                })
            df_stock = pd.DataFrame(stock_table).set_index("銘柄")
            st.dataframe(df_stock, use_container_width=True)
            st.download_button(f"📥 {theme_name} CSV", df_stock.to_csv(encoding="utf-8-sig"),
                               f"{theme_name}_{now}.csv", "text/csv", key=f"csv_{theme_name}")

            for sn, d in stocks.items():
                c = "🔴" if d["change"]>0 else "🟢"
                is_fav = sn in st.session_state["favorites"]
                col1, col2, col3 = st.columns([3,1,1])
                with col1:
                    st.write(f"{c} **{sn}**　{d['change']}%")
                with col2:
                    if st.button("詳細チャート", key=f"chart_{sn}"):
                        st.session_state["selected_stock"] = sn
                        st.session_state["selected_ticker"] = d["ticker"]
                        st.rerun()
                with col3:
                    if is_fav:
                        if st.button("⭐ 解除", key=f"fav_{sn}"):
                            del st.session_state["favorites"][sn]; st.rerun()
                    else:
                        if st.button("☆ 登録", key=f"fav_{sn}"):
                            st.session_state["favorites"][sn] = d["ticker"]; st.rerun()

# =====================
# ヒートマップ
# =====================
elif page == "🔥 ヒートマップ":
    st.subheader("🔥 騰落率ヒートマップ（テーマ × 期間）")
    st.caption(f"🕐 最終更新：{now}")
    st.info("全テーマ×全期間のデータを取得するため約1〜2分かかります")

    with st.spinner("全期間データを取得中..."):
        heatmap_periods = {"1週間":"5d","1ヶ月":"1mo","3ヶ月":"3mo","6ヶ月":"6mo"}
        heatmap_data = {}
        for theme_name, stocks in themes.items():
            heatmap_data[theme_name] = {}
            for pl, pc in heatmap_periods.items():
                changes = []
                for _, ticker in stocks.items():
                    try:
                        df = yf.Ticker(ticker).history(period="6mo")
                        if len(df) < 2: continue
                        c = calc_change(get_target_df(df, pc))
                        if c is not None: changes.append(c)
                    except: pass
                heatmap_data[theme_name][pl] = round(sum(changes)/len(changes),2) if changes else None

    df_heat = pd.DataFrame(heatmap_data).T[["1週間","1ヶ月","3ヶ月","6ヶ月"]]
    z = df_heat.values.tolist()
    text_v = [[f"{v}%" if v is not None else "N/A" for v in row] for row in z]
    fig_heat = go.Figure(go.Heatmap(
        z=z, x=["1週間","1ヶ月","3ヶ月","6ヶ月"], y=df_heat.index.tolist(),
        text=text_v, texttemplate="%{text}",
        colorscale=[[0.0,"#39d353"],[0.5,"#1a1d27"],[1.0,"#ff4b4b"]],
        zmid=0, showscale=True, colorbar=dict(title="騰落率(%)"),
    ))
    fig_heat.update_layout(
        xaxis=dict(title="期間"), yaxis=dict(title="テーマ", autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=12), height=600,
        margin=dict(t=30, b=50, l=160, r=20),
    )
    st.plotly_chart(fig_heat, use_container_width=True, config=PLOT_CONFIG)
    st.download_button("📥 ヒートマップCSV", df_heat.to_csv(encoding="utf-8-sig"),
                       f"ヒートマップ_{now}.csv", "text/csv")

# =====================
# テーマ比較
# =====================
elif page == "📉 テーマ比較":
    st.subheader("📉 テーマ間比較チャート")
    st.caption(f"🕐 最終更新：{now}")
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()))
    period = period_options[selected_label]
    selected_themes = st.multiselect("比較するテーマを選択", list(themes.keys()), default=["半導体","AI・クラウド"])

    if len(selected_themes) < 2:
        st.warning("2つ以上のテーマを選択してください")
    else:
        with st.spinner("データ取得中..."):
            fig_comp = go.Figure()
            comp_data = {}
            for theme_name in selected_themes:
                all_changes = {}
                for _, ticker in themes[theme_name].items():
                    try:
                        df = yf.Ticker(ticker).history(period="6mo")
                        if len(df) < 2: continue
                        target_df = get_target_df(df, period)
                        cum = (target_df["Close"] / target_df["Close"].iloc[0] - 1) * 100
                        for date, val in zip(target_df.index, cum):
                            if date not in all_changes: all_changes[date] = []
                            all_changes[date].append(val)
                    except: pass

                if all_changes:
                    dates = sorted(all_changes.keys())
                    avgs = [round(sum(all_changes[d])/len(all_changes[d]),2) for d in dates]
                    comp_data[theme_name] = {"dates":dates,"returns":avgs}
                    fig_comp.add_trace(go.Scatter(x=dates, y=avgs, mode="lines", name=theme_name, line=dict(width=2)))

            fig_comp.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_comp.update_layout(
                xaxis=dict(title="日付"), yaxis=dict(title="累積リターン（%）", ticksuffix="%"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=12), height=500,
                legend=dict(orientation="h", y=1.1),
                margin=dict(t=60, b=50, l=70, r=20),
            )
            st.plotly_chart(fig_comp, use_container_width=True, config=PLOT_CONFIG)

            summary = [{"テーマ":tn, "期間リターン":f"🔴 +{d['returns'][-1]}%" if d['returns'][-1]>0 else f"🟢 {d['returns'][-1]}%"}
                       for tn, d in comp_data.items() if d["returns"]]
            df_sum = pd.DataFrame(summary).set_index("テーマ")
            st.dataframe(df_sum, use_container_width=True)
            st.download_button("📥 比較データCSV", df_sum.to_csv(encoding="utf-8-sig"),
                               f"テーマ比較_{now}.csv", "text/csv")

# =====================
# マクロ比較（新機能）
# =====================
elif page == "🌍 マクロ比較":
    st.subheader("🌍 マクロ指標との比較")
    st.caption(f"🕐 最終更新：{now}")
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()))
    period = period_options[selected_label]

    # 比較する銘柄・テーマを選択
    selected_stock_name = st.selectbox("比較する銘柄またはテーマを選択", list(all_stocks.keys()))
    selected_ticker = all_stocks[selected_stock_name]

    macro_items = {
        "日経平均": "^N225",
        "S&P500": "^GSPC",
        "ドル円": "JPY=X",
    }

    with st.spinner("データ取得中..."):
        fig_macro = go.Figure()
        colors_macro = {"日経平均":"#ffd700","S&P500":"#4b8bff","ドル円":"#ff9900"}

        # 選択銘柄
        try:
            df_sel = yf.Ticker(selected_ticker).history(period="6mo")
            target = get_target_df(df_sel, period)
            cum = (target["Close"] / target["Close"].iloc[0] - 1) * 100
            fig_macro.add_trace(go.Scatter(
                x=target.index, y=cum, mode="lines",
                line=dict(color="#ff4b4b", width=3),
                name=selected_stock_name,
            ))
        except: pass

        # マクロ指標
        for name, ticker in macro_items.items():
            try:
                df_m = yf.Ticker(ticker).history(period="6mo")
                target_m = get_target_df(df_m, period)
                cum_m = (target_m["Close"] / target_m["Close"].iloc[0] - 1) * 100
                fig_macro.add_trace(go.Scatter(
                    x=target_m.index, y=cum_m, mode="lines",
                    line=dict(color=colors_macro[name], width=2, dash="dot"),
                    name=name,
                ))
            except: pass

    fig_macro.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_macro.update_layout(
        xaxis=dict(title="日付"),
        yaxis=dict(title="累積リターン（%）", ticksuffix="%"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=12), height=500,
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=60, b=50, l=70, r=20),
    )
    st.plotly_chart(fig_macro, use_container_width=True, config=PLOT_CONFIG)

    st.caption("🔴 選択銘柄　🟡 日経平均　🔵 S&P500　🟠 ドル円（点線）")

# =====================
# 銘柄検索
# =====================
elif page == "🔎 銘柄検索":
    st.subheader("🔎 銘柄検索")
    st.caption(f"🕐 最終更新：{now}")
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()))
    period = period_options[selected_label]
    query = st.text_input("銘柄名を入力", placeholder="例：トヨタ、ソニー、任天堂...")
    theme_filter = st.multiselect("テーマで絞り込む（任意）", list(themes.keys()))

    search_targets = {}
    for tn, stocks in themes.items():
        if theme_filter and tn not in theme_filter: continue
        for sn, ticker in stocks.items():
            search_targets[sn] = {"ticker":ticker,"theme":tn}

    matched = {k:v for k,v in search_targets.items() if query in k} if query else search_targets
    st.caption(f"該当銘柄：{len(matched)}件")

    if matched:
        with st.spinner("データ取得中..."):
            results = []
            for sn, info in matched.items():
                try:
                    df = yf.Ticker(info["ticker"]).history(period="3mo")
                    if len(df) < 2: continue
                    target_df = get_target_df(df, period)
                    change = calc_change(target_df)
                    vol_change = calc_vol_change(target_df)
                    rsi_val = round(calc_rsi(df["Close"]).iloc[-1], 1)
                    price = int(target_df["Close"].iloc[-1])
                    day_c = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None

                    df_52w = yf.Ticker(info["ticker"]).history(period="1y")
                    w52_high = int(df_52w["High"].max()) if len(df_52w)>0 else None
                    w52_low = int(df_52w["Low"].min()) if len(df_52w)>0 else None

                    results.append({
                        "銘柄": sn, "テーマ": info["theme"],
                        "現在株価": f"¥{price:,}",
                        "前日比": f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                        "騰落率": f"🔴 +{change}%" if change and change>0 else f"🟢 {change}%",
                        "出来高増減": f"📈 +{vol_change}%" if vol_change>0 else f"📉 {vol_change}%",
                        "RSI": f"{rsi_val}",
                        "52週高値": f"¥{w52_high:,}" if w52_high else "N/A",
                        "52週安値": f"¥{w52_low:,}" if w52_low else "N/A",
                        "ticker": info["ticker"],
                    })
                except: pass

        if results:
            df_search = pd.DataFrame(results)
            df_display = df_search.drop(columns=["ticker"]).set_index("銘柄")
            st.dataframe(df_display, use_container_width=True)
            st.download_button("📥 検索結果CSV", df_display.to_csv(encoding="utf-8-sig"),
                               f"銘柄検索_{query}_{now}.csv", "text/csv")

            for r in results:
                is_fav = r["銘柄"] in st.session_state["favorites"]
                col1, col2, col3 = st.columns([3,1,1])
                with col1:
                    st.write(f"**{r['銘柄']}**（{r['テーマ']}）　{r['騰落率']}　{r['現在株価']}")
                with col2:
                    if st.button("詳細チャート", key=f"sc_{r['銘柄']}"):
                        st.session_state["selected_stock"] = r["銘柄"]
                        st.session_state["selected_ticker"] = r["ticker"]
                        st.rerun()
                with col3:
                    if is_fav:
                        if st.button("⭐ 解除", key=f"sf_{r['銘柄']}"):
                            del st.session_state["favorites"][r["銘柄"]]; st.rerun()
                    else:
                        if st.button("☆ 登録", key=f"sf_{r['銘柄']}"):
                            st.session_state["favorites"][r["銘柄"]] = r["ticker"]; st.rerun()

# =====================
# お気に入り
# =====================
elif page == "⭐ お気に入り":
    st.subheader("⭐ お気に入り銘柄")
    st.caption(f"🕐 最終更新：{now}")
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()))
    period = period_options[selected_label]

    if len(st.session_state["favorites"]) == 0:
        st.info("テーマ一覧ページで「☆ 登録」ボタンを押して追加してください。")
    else:
        with st.spinner("データ取得中..."):
            fav_results = []
            for sn, ticker in st.session_state["favorites"].items():
                try:
                    df = yf.Ticker(ticker).history(period="3mo")
                    if len(df) < 2: continue
                    target_df = get_target_df(df, period)
                    change = calc_change(target_df)
                    vol_change = calc_vol_change(target_df)
                    rsi_val = round(calc_rsi(df["Close"]).iloc[-1], 1)
                    sharpe = calc_sharpe(target_df["Close"])
                    price = int(target_df["Close"].iloc[-1])
                    day_c = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None
                    df_52w = yf.Ticker(ticker).history(period="1y")
                    w52_high = int(df_52w["High"].max()) if len(df_52w)>0 else None
                    w52_low = int(df_52w["Low"].min()) if len(df_52w)>0 else None
                    fav_results.append({
                        "銘柄":sn,"ticker":ticker,"change":change,"vol_change":vol_change,
                        "price":price,"rsi":rsi_val,"sharpe":sharpe,
                        "day_change":day_c,"52w_high":w52_high,"52w_low":w52_low,
                    })
                except: pass

        fav_results.sort(key=lambda x: x["change"], reverse=True)
        fav_labels = [r["銘柄"] for r in fav_results]
        fav_values = [r["change"] for r in fav_results]
        fav_colors = ["#ff4b4b" if v>=0 else "#39d353" for v in fav_values]
        st.plotly_chart(make_bar_chart(fav_labels, fav_values, fav_colors,
                        max(300,len(fav_results)*50), 130), use_container_width=True, config=PLOT_CONFIG)

        table_data = []
        for r in fav_results:
            rsi = r.get("rsi")
            rsi_alert = "⚠️買" if rsi and rsi>70 else "⚠️売" if rsi and rsi<30 else "✅"
            day_c = r.get("day_change")
            table_data.append({
                "銘柄": r["銘柄"],
                "現在株価": f"¥{r['price']:,}",
                "前日比": f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                "期間騰落率": f"🔴 +{r['change']}%" if r["change"]>0 else f"🟢 {r['change']}%",
                "出来高増減": f"📈 +{r['vol_change']}%" if r["vol_change"]>0 else f"📉 {r['vol_change']}%",
                "RSI": f"{rsi} {rsi_alert}" if rsi else "N/A",
                "シャープレシオ": f"{r['sharpe']}" if r["sharpe"] else "N/A",
                "52週高値": f"¥{r['52w_high']:,}" if r["52w_high"] else "N/A",
                "52週安値": f"¥{r['52w_low']:,}" if r["52w_low"] else "N/A",
            })
        df_fav = pd.DataFrame(table_data).set_index("銘柄")
        st.dataframe(df_fav, use_container_width=True)
        st.download_button("📥 お気に入りCSV", df_fav.to_csv(encoding="utf-8-sig"),
                           f"お気に入り_{now}.csv", "text/csv")

        for r in fav_results:
            c = "🔴" if r["change"]>0 else "🟢"
            col1, col2, col3 = st.columns([3,1,1])
            with col1: st.write(f"{c} **{r['銘柄']}**　{r['change']}%")
            with col2:
                if st.button("詳細チャート", key=f"fc_{r['銘柄']}"):
                    st.session_state["selected_stock"] = r["銘柄"]
                    st.session_state["selected_ticker"] = r["ticker"]
                    st.rerun()
            with col3:
                if st.button("⭐ 解除", key=f"fd_{r['銘柄']}"):
                    del st.session_state["favorites"][r["銘柄"]]; st.rerun()

# =====================
# 個別株詳細
# =====================
elif page == "🔍 個別株詳細":
    st.caption(f"🕐 最終更新：{now}")
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()))
    period = period_options[selected_label]

    selected_name = st.sidebar.selectbox(
        "銘柄を選択", list(all_stocks.keys()),
        index=list(all_stocks.keys()).index(st.session_state.get("selected_stock", list(all_stocks.keys())[0]))
    )
    selected_ticker = all_stocks[selected_name]
    st.subheader(f"📈 {selected_name}")

    is_fav = selected_name in st.session_state["favorites"]
    if is_fav:
        if st.button("⭐ お気に入り解除"):
            del st.session_state["favorites"][selected_name]; st.rerun()
    else:
        if st.button("☆ お気に入りに追加"):
            st.session_state["favorites"][selected_name] = selected_ticker; st.rerun()

    with st.spinner("データ取得中..."):
        df = yf.Ticker(selected_ticker).history(period="1y")

    if len(df) > 0:
        display_df = get_target_df(df, period)
        price_change = calc_change(display_df)
        vol_change = calc_vol_change(display_df)
        last_price = int(display_df["Close"].iloc[-1])
        day_c = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None

        # 52週高値・安値
        w52_high = round(df["High"].max(), 0)
        w52_low = round(df["Low"].min(), 0)
        price_pos = round((last_price - w52_low) / (w52_high - w52_low) * 100, 1) if w52_high != w52_low else None

        # 基本メトリクス
        col1, col2, col3, col4 = st.columns(4)
        col1.metric("現在株価", f"¥{last_price:,}")
        col2.metric("前日比", f"{day_c}%" if day_c else "N/A")
        col3.metric("期間騰落率", f"{price_change}%")
        col4.metric("出来高増減", f"{vol_change}%")

        # 52週高値・安値
        st.markdown("#### 📊 52週レンジ")
        col1, col2, col3 = st.columns(3)
        col1.metric("52週高値", f"¥{int(w52_high):,}")
        col2.metric("52週安値", f"¥{int(w52_low):,}")
        col3.metric("レンジ内位置", f"{price_pos}%" if price_pos else "N/A",
                    "高値圏⚠️" if price_pos and price_pos>80 else "安値圏✅" if price_pos and price_pos<20 else "中間帯")

        # 財務指標
        st.markdown("#### 💼 財務指標")
        with st.spinner("財務データ取得中..."):
            f = get_fundamentals(selected_ticker)
        col1,col2,col3,col4,col5 = st.columns(5)
        col1.metric("PER", f"{f['PER']}倍" if f["PER"] else "N/A")
        col2.metric("PBR", f"{f['PBR']}倍" if f["PBR"] else "N/A")
        col3.metric("時価総額", f["時価総額"])
        col4.metric("売上高", f["売上高"])
        col5.metric("EPS", f"{f['EPS']}円" if f["EPS"] else "N/A")

        # チャート切り替え
        st.markdown("#### 📉 株価チャート")
        col_a, col_b = st.columns(2)
        with col_a:
            chart_type = st.radio("チャートの種類", ["ローソク足", "折れ線"], horizontal=True)
        with col_b:
            show_ma = st.checkbox("移動平均線を表示（25日・75日）", value=True)

        # ローソク足/折れ線+移動平均線（1年分データで移動平均を計算し、表示期間だけ表示）
        fig_price = make_price_chart(display_df if not show_ma else df, chart_type, show_ma)
        if show_ma and period != "6mo":
            # 表示範囲を絞る
            fig_price.update_xaxes(range=[display_df.index[0], display_df.index[-1]])
        st.plotly_chart(fig_price, use_container_width=True, config=PLOT_CONFIG)

        # 出来高チャート
        vol_colors = ["#ff4b4b" if display_df["Close"].iloc[i]>=display_df["Close"].iloc[i-1]
                      else "#39d353" for i in range(len(display_df))]
        fig_vol = go.Figure(go.Bar(x=display_df.index, y=display_df["Volume"], marker_color=vol_colors))
        fig_vol.update_layout(
            xaxis=dict(title="日付"), yaxis=dict(title="出来高"),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"), height=220,
            margin=dict(t=10, b=40, l=70, r=20),
        )
        st.plotly_chart(fig_vol, use_container_width=True, config=PLOT_CONFIG)

        # テクニカル指標
        if len(df) >= 30:
            close = df["Close"]
            rsi = calc_rsi(close)
            macd, sig_line, hist = calc_macd(close)
            sharpe = calc_sharpe(display_df["Close"])
            rsi_val = round(rsi.iloc[-1], 1)
            macd_val = round(macd.iloc[-1], 2)

            st.markdown("#### 📈 テクニカル指標")
            col1,col2,col3 = st.columns(3)
            col1.metric("RSI（14日）", f"{rsi_val}",
                        "買われすぎ⚠️" if rsi_val>70 else "売られすぎ⚠️" if rsi_val<30 else "中立✅")
            col2.metric("MACD", f"{macd_val}", "強気📈" if hist.iloc[-1]>0 else "弱気📉")
            col3.metric("シャープレシオ", f"{sharpe}" if sharpe else "N/A",
                        "良好✅" if sharpe and sharpe>1 else "要注意⚠️" if sharpe and sharpe<0 else "普通")

            fig_rsi = go.Figure()
            fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi, mode="lines",
                                          line=dict(color="#ff4b4b", width=2), name="RSI"))
            fig_rsi.add_hline(y=70, line_dash="dash", line_color="orange", annotation_text="買われすぎ(70)")
            fig_rsi.add_hline(y=30, line_dash="dash", line_color="#39d353", annotation_text="売られすぎ(30)")
            fig_rsi.update_layout(
                yaxis=dict(title="RSI", range=[0,100]), xaxis=dict(title="日付"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=230,
                margin=dict(t=10, b=40, l=60, r=20),
            )
            if period != "6mo":
                fig_rsi.update_xaxes(range=[display_df.index[0], display_df.index[-1]])
            st.plotly_chart(fig_rsi, use_container_width=True, config=PLOT_CONFIG)

            hist_colors = ["#ff4b4b" if v>=0 else "#39d353" for v in hist]
            fig_macd = go.Figure()
            fig_macd.add_trace(go.Scatter(x=df.index, y=macd, mode="lines",
                                           line=dict(color="#ff4b4b", width=2), name="MACD"))
            fig_macd.add_trace(go.Scatter(x=df.index, y=sig_line, mode="lines",
                                           line=dict(color="#4b8bff", width=2), name="シグナル"))
            fig_macd.add_trace(go.Bar(x=df.index, y=hist, marker_color=hist_colors,
                                       name="ヒストグラム", opacity=0.6))
            fig_macd.update_layout(
                yaxis=dict(title="MACD"), xaxis=dict(title="日付"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=230,
                legend=dict(orientation="h", y=1.15),
                margin=dict(t=30, b=40, l=60, r=20),
            )
            if period != "6mo":
                fig_macd.update_xaxes(range=[display_df.index[0], display_df.index[-1]])
            st.plotly_chart(fig_macd, use_container_width=True, config=PLOT_CONFIG)

        # CSVダウンロード
        csv_detail = display_df[["Open","High","Low","Close","Volume"]].copy()
        csv_detail.index = csv_detail.index.strftime("%Y-%m-%d")
        st.download_button("📥 株価データCSV", csv_detail.to_csv(encoding="utf-8-sig"),
                           f"{selected_name}_{now}.csv", "text/csv")
    else:
        st.error("データを取得できませんでした")
