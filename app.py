import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

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

# =====================
# 25テーマ・約200銘柄
# =====================
themes = {
    "半導体": {
        "東京エレクトロン":"8035.T","アドバンテスト":"6857.T","ルネサス":"6723.T",
        "ディスコ":"6146.T","SUMCO":"3436.T","レーザーテック":"6920.T",
        "ソシオネクスト":"6526.T","マイクロニクス":"6871.T","フェローテック":"6890.T",
    },
    "AI・クラウド": {
        "富士通":"6702.T","NEC":"6701.T","さくらインターネット":"3778.T",
        "日立製作所":"6501.T","オービック":"4684.T","GMOインターネット":"9449.T",
        "BIPROGY":"8056.T","TIS":"3626.T","野村総合研究所":"4307.T",
    },
    "EV・電気自動車": {
        "トヨタ":"7203.T","パナソニック":"6752.T","住友電気工業":"5802.T",
        "デンソー":"6902.T","日産自動車":"7201.T","本田技研工業":"7267.T",
        "村田製作所":"6981.T","TDK":"6762.T","古河電気工業":"5801.T",
    },
    "ゲーム・エンタメ": {
        "任天堂":"7974.T","ソニー":"6758.T","カプコン":"9697.T",
        "バンダイナムコ":"7832.T","スクウェア・エニックス":"9684.T",
        "コナミ":"9766.T","セガサミー":"6460.T","DeNA":"2432.T","ネクソン":"3659.T",
    },
    "銀行・金融": {
        "三菱UFJ":"8306.T","三井住友":"8316.T","みずほ":"8411.T",
        "りそな":"8308.T","ゆうちょ銀行":"7182.T","野村HD":"8604.T",
        "大和証券グループ":"8601.T",
    },
    "地方銀行": {
        "静岡銀行":"8355.T","コンコルディア":"7186.T","ふくおかFG":"8354.T",
        "北海道銀行":"8179.T","七十七銀行":"8341.T","広島銀行":"8379.T",
        "伊予銀行":"8385.T","百五銀行":"8368.T","山口FG":"8418.T",
    },
    "保険": {
        "東京海上HD":"8766.T","MS&AD":"8725.T","第一生命":"8750.T",
        "SOMPOホールディングス":"8630.T","かんぽ生命":"7181.T",
    },
    "不動産": {
        "三井不動産":"8801.T","住友不動産":"8830.T","東急不動産HD":"3289.T",
        "三菱地所":"8802.T","野村不動産HD":"3231.T","ヒューリック":"3003.T",
        "大東建託":"1878.T",
    },
    "医薬品・バイオ": {
        "武田薬品":"4502.T","アステラス製薬":"4503.T","第一三共":"4568.T",
        "中外製薬":"4519.T","大塚HD":"4578.T","エーザイ":"4523.T",
        "小野薬品":"4528.T","塩野義製薬":"4507.T",
    },
    "ヘルスケア・介護": {
        "シップヘルスケアHD":"3360.T","ソラスト":"6197.T","日本M&Aセンター":"2127.T",
        "エムスリー":"2413.T","メドレー":"4480.T","ケアネット":"2150.T",
        "ツムラ":"4540.T","テルモ":"4543.T",
    },
    "食品・飲料": {
        "味の素":"2802.T","キリンHD":"2503.T","日清食品HD":"2897.T",
        "明治HD":"2269.T","サントリー食品":"2587.T","日本ハム":"2282.T",
        "カゴメ":"2811.T","ニッスイ":"1332.T",
    },
    "小売・EC": {
        "ファーストリテイリング":"9983.T","セブン&アイ":"3382.T","MonotaRO":"3064.T",
        "イオン":"8267.T","ニトリHD":"9843.T","Zホールディングス":"4689.T",
        "ウエルシアHD":"3141.T","コスモス薬品":"3349.T",
    },
    "通信": {
        "NTT":"9432.T","ソフトバンク":"9434.T","KDDI":"9433.T",
        "楽天グループ":"4755.T","インターネットイニシアティブ":"3774.T",
        "JCOM":"4547.T",
    },
    "鉄鋼・素材": {
        "日本製鉄":"5401.T","JFEホールディングス":"5411.T","神戸製鋼所":"5406.T",
        "大和工業":"5444.T","東京製鐵":"5423.T","日本軽金属HD":"5703.T",
    },
    "化学": {
        "信越化学工業":"4063.T","東レ":"3402.T","住友化学":"4005.T",
        "旭化成":"3407.T","三菱ケミカルグループ":"4188.T","花王":"4452.T",
        "富士フイルムHD":"4901.T","クレハ":"4023.T",
    },
    "建設・インフラ": {
        "大林組":"1802.T","鹿島建設":"1812.T","大成建設":"1801.T",
        "清水建設":"1803.T","積水ハウス":"1928.T","大和ハウス工業":"1925.T",
        "西松建設":"1820.T",
    },
    "輸送・物流": {
        "日本郵船":"9101.T","商船三井":"9104.T","ヤマトHD":"9064.T",
        "川崎汽船":"9107.T","センコーグループ":"9069.T","日本通運":"9062.T",
        "福山通運":"9075.T",
    },
    # --- 新テーマ ---
    "防衛・航空宇宙": {
        "三菱重工業":"7011.T","川崎重工業":"7012.T","IHI":"7013.T",
        "富士通":"6702.T","日本電気":"6701.T","三菱電機":"6503.T",
        "豊和工業":"6203.T","日本航空電子工業":"6807.T",
    },
    "フィンテック・仮想通貨": {
        "マネックスグループ":"8698.T","SBIホールディングス":"8473.T",
        "GMOフィナンシャルHD":"7177.T","オリエントコーポレーション":"8585.T",
        "Kyash":"なし","メルカリ":"4385.T","インフォマート":"2492.T",
        "ネットムーブ":"3383.T",
    },
    "再生可能エネルギー": {
        "レノバ":"9519.T","ウエストHD":"1407.T","エネコート":"なし",
        "東京電力HD":"9501.T","関西電力":"9503.T","中部電力":"9502.T",
        "出光興産":"5019.T","ENEOS HD":"5020.T",
    },
    "ロボット・自動化": {
        "ファナック":"6954.T","安川電機":"6506.T","キーエンス":"6861.T",
        "不二越":"6474.T","三菱電機":"6503.T","オムロン":"6645.T",
        "デンソー":"6902.T","川崎重工業":"7012.T",
    },
    "レアアース・資源": {
        "住友金属鉱山":"5713.T","三井物産":"8031.T","三菱商事":"8058.T",
        "丸紅":"8002.T","JX金属":"5721.T","DOWAホールディングス":"5714.T",
        "太平洋金属":"5441.T",
    },
    "サイバーセキュリティ": {
        "NRI（野村総研）":"4307.T","LAC":"なし","トレンドマイクロ":"4704.T",
        "サイバーセキュリティクラウド":"4493.T","GMOサイバーセキュリティ":"なし",
        "デジタルアーツ":"2326.T","FFRIセキュリティ":"3692.T",
        "ソリトンシステムズ":"3040.T",
    },
    "ドローン・空飛ぶ車": {
        "テラドローン":"なし","スカイドライブ":"なし","ACSLエアロスペース":"6232.T",
        "セキド":"9878.T","ヤマハ発動機":"7272.T","川崎重工業":"7012.T",
        "NTT":"9432.T","富士通":"6702.T",
    },
    "造船": {
        "今治造船":"なし","三菱重工業":"7011.T","川崎重工業":"7012.T",
        "住友重機械工業":"6302.T","名村造船所":"7014.T",
        "内海造船":"7018.T","日本郵船":"9101.T",
    },
}

# 「なし」ティッカーを除外
themes = {
    theme: {k: v for k, v in stocks.items() if v != "なし"}
    for theme, stocks in themes.items()
}

all_stocks = {}
for stocks in themes.values():
    for name, ticker in stocks.items():
        all_stocks[name] = ticker

PLOT_CONFIG = {"displayModeBar": False, "staticPlot": True}

# 期間選択（延長版）
period_options = {
    "1日":   "1d",
    "1週間": "5d",
    "1ヶ月": "1mo",
    "3ヶ月": "3mo",
    "6ヶ月": "6mo",
    "1年":   "1y",
    "1年半": "18mo",
    "2年":   "2y",
}

# =====================
# ユーティリティ関数
# =====================
def get_target_df(df, period):
    if period == "1d":   return df.tail(1)
    if period == "5d":   return df.tail(5)
    if period == "1mo":  return df.tail(21)
    if period == "3mo":  return df.tail(63)
    if period == "6mo":  return df.tail(126)
    if period == "1y":   return df.tail(252)
    if period == "18mo": return df.tail(378)
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

# =====================
# キャッシュ付きデータ取得
# =====================
@st.cache_data(ttl=3600)
def fetch_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    try:
        return yf.Ticker(ticker).history(period=period)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=21600)
def fetch_fundamentals(ticker: str) -> dict:
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

@st.cache_data(ttl=3600)
def fetch_all_theme_data(period: str) -> tuple:
    theme_results = []
    theme_details = {}

    for theme_name, stocks in themes.items():
        changes, details = [], {}
        total_vol = prev_total_vol = 0

        for stock_name, ticker in stocks.items():
            try:
                df = fetch_stock_data(ticker, "2y")
                if len(df) < 2: continue
                target_df = get_target_df(df, period)
                if len(target_df) < 2: continue
                change = calc_change(target_df)
                if change is None: continue
                changes.append(change)

                half = max(len(target_df)//2, 1)
                rv = target_df["Volume"].tail(half).mean()
                pv = target_df["Volume"].head(half).mean()
                total_vol += rv
                prev_total_vol += pv

                day_change = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None
                rsi_val = round(calc_rsi(df["Close"]).iloc[-1], 1) if len(df)>=15 else None
                sharpe = calc_sharpe(target_df["Close"])
                w52_high = round(df["High"].tail(252).max(), 0)
                w52_low = round(df["Low"].tail(252).min(), 0)
                last_price = round(df["Close"].iloc[-1], 0)
                trade_value = int(rv * last_price)

                details[stock_name] = {
                    "change": change, "day_change": day_change,
                    "volume_change": round((rv-pv)/pv*100,1) if pv>0 else 0,
                    "ticker": ticker, "rsi": rsi_val, "sharpe": sharpe,
                    "52w_high": w52_high, "52w_low": w52_low,
                    "price": last_price, "volume": int(rv),
                    "trade_value": trade_value,
                }
            except:
                pass

        if changes:
            avg = round(sum(changes)/len(changes), 2)
            vol_chg = round((total_vol-prev_total_vol)/prev_total_vol*100,1) if prev_total_vol>0 else 0
            theme_results.append({
                "テーマ": theme_name,
                "平均騰落率(%)": avg,
                "出来高増減(%)": vol_chg,
                "合計出来高": int(total_vol),
            })
            theme_details[theme_name] = details

    theme_results.sort(key=lambda x: x["平均騰落率(%)"], reverse=True)
    return theme_results, theme_details

# =====================
# Google Sheets連携
# =====================
def get_gsheet():
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"],
        )
        client = gspread.authorize(creds)
        return client.open_by_key(st.secrets["SPREADSHEET_ID"])
    except Exception as e:
        st.error(f"Google Sheets接続エラー：{e}")
        return None

def save_theme_history(theme_results):
    try:
        spreadsheet = get_gsheet()
        if spreadsheet is None: return False
        try:
            sheet = spreadsheet.worksheet("履歴")
        except gspread.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title="履歴", rows=10000, cols=30)
            headers = ["日時"] + [r["テーマ"] for r in theme_results]
            sheet.append_row(headers)

        today_date = datetime.now().strftime("%Y-%m-%d")
        existing = sheet.col_values(1)
        if any(today_date in str(d) for d in existing):
            return False

        row = [datetime.now().strftime("%Y-%m-%d %H:%M")] + [r["平均騰落率(%)"] for r in theme_results]
        sheet.append_row(row)
        return True
    except Exception as e:
        st.warning(f"履歴の保存に失敗：{e}")
        return False

@st.cache_data(ttl=600)
def load_theme_history() -> pd.DataFrame:
    try:
        creds = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"],
            scopes=["https://spreadsheets.google.com/feeds","https://www.googleapis.com/auth/drive"],
        )
        client = gspread.authorize(creds)
        spreadsheet = client.open_by_key(st.secrets["SPREADSHEET_ID"])
        try:
            sheet = spreadsheet.worksheet("履歴")
        except:
            return pd.DataFrame()
        data = sheet.get_all_values()
        if len(data) < 2: return pd.DataFrame()
        headers = data[0]
        df = pd.DataFrame(data[1:], columns=headers)
        df["日時"] = pd.to_datetime(df["日時"])
        for col in headers[1:]:
            df[col] = pd.to_numeric(df[col], errors="coerce")
        return df
    except:
        return pd.DataFrame()

# =====================
# グラフ関数
# =====================
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
    fig = go.Figure()
    if chart_type == "ローソク足":
        fig.add_trace(go.Candlestick(
            x=df.index, open=df["Open"], high=df["High"],
            low=df["Low"], close=df["Close"],
            increasing_line_color="#ff4b4b",
            decreasing_line_color="#39d353",
            name="株価",
        ))
    else:
        fig.add_trace(go.Scatter(
            x=df.index, y=df["Close"], mode="lines",
            line=dict(color="#ff4b4b", width=2),
            fill="tozeroy", fillcolor="rgba(255,75,75,0.1)", name="終値",
        ))
    if show_ma and len(df) >= 25:
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(25).mean(),
                                  mode="lines", line=dict(color="#ffd700", width=1.5, dash="dot"), name="25日MA"))
    if show_ma and len(df) >= 75:
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(75).mean(),
                                  mode="lines", line=dict(color="#4b8bff", width=1.5, dash="dot"), name="75日MA"))
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
    "📈 騰落推移",
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

if st.sidebar.button("🔄 データを最新に更新"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption("※データは1時間キャッシュされます")

now = datetime.now().strftime("%Y年%m月%d日 %H:%M")

# =====================
# テーマ一覧
# =====================
if page == "📊 テーマ一覧":
    # 期間選択を上部に配置
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()), index=1)
    period = period_options[selected_label]
    st.caption(f"🕐 最終更新：{now}　　25テーマ・約200銘柄")

    with st.spinner("データを取得中...（初回は時間がかかります）"):
        theme_results, theme_details = fetch_all_theme_data(period)

    saved = save_theme_history(theme_results)
    if saved:
        st.success("📊 本日のテーマ騰落率を履歴に保存しました！")

    labels = [r["テーマ"] for r in theme_results]
    values = [r["平均騰落率(%)"] for r in theme_results]
    colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in values]

    st.subheader("📊 テーマ別騰落率ランキング")
    chart_height = max(600, len(theme_results) * 35)
    st.plotly_chart(make_bar_chart(labels, values, colors, chart_height, 160),
                    use_container_width=True, config=PLOT_CONFIG)

    st.subheader("📋 テーマ一覧")
    table_data = []
    for rank, r in enumerate(theme_results, 1):
        c, v = r["平均騰落率(%)"], r["出来高増減(%)"]
        table_data.append({
            "順位": f"{rank}位",
            "テーマ": r["テーマ"],
            "騰落率": f"🔴 +{c}%" if c>0 else f"🟢 {c}%",
            "出来高増減": f"📈 +{v}%" if v>0 else f"📉 {v}%",
        })
    df_table = pd.DataFrame(table_data).set_index("順位")
    st.dataframe(df_table, use_container_width=True)
    st.download_button("📥 CSVダウンロード", df_table.to_csv(encoding="utf-8-sig"),
                       f"テーマ一覧_{now}.csv", "text/csv")

    st.subheader("🔍 テーマ別詳細（クリックで展開）")
    for result in theme_results:
        theme_name = result["テーマ"]
        stocks = theme_details.get(theme_name, {})
        if not stocks: continue
        with st.expander(f"{theme_name}　騰落率 {result['平均騰落率(%)']}%　出来高増減 {result['出来高増減(%)']}%"):
            s_labels = list(stocks.keys())
            s_values = [stocks[s]["change"] for s in s_labels]
            s_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in s_values]
            st.plotly_chart(make_bar_chart(s_labels, s_values, s_colors, max(250, len(s_labels)*40), 130),
                            use_container_width=True, config=PLOT_CONFIG)

            stock_table = []
            for sn, d in stocks.items():
                rsi = d.get("rsi")
                rsi_alert = "⚠️買" if rsi and rsi>70 else "⚠️売" if rsi and rsi<30 else "✅"
                day_c = d.get("day_change")
                stock_table.append({
                    "銘柄": sn,
                    "株価": f"¥{int(d['price']):,}",
                    "前日比": f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                    "騰落率": f"🔴 +{d['change']}%" if d["change"]>0 else f"🟢 {d['change']}%",
                    "出来高増減": f"📈 +{d['volume_change']}%" if d["volume_change"]>0 else f"📉 {d['volume_change']}%",
                    "RSI": f"{rsi} {rsi_alert}" if rsi else "N/A",
                    "シャープ": f"{d['sharpe']}" if d["sharpe"] else "N/A",
                    "52W高値": f"¥{int(d['52w_high']):,}" if d["52w_high"] else "N/A",
                    "52W安値": f"¥{int(d['52w_low']):,}" if d["52w_low"] else "N/A",
                })
            df_stock = pd.DataFrame(stock_table).set_index("銘柄")
            st.dataframe(df_stock, use_container_width=True)
            st.download_button(f"📥 {theme_name} CSV", df_stock.to_csv(encoding="utf-8-sig"),
                               f"{theme_name}_{now}.csv", "text/csv", key=f"csv_{theme_name}")

            for sn, d in stocks.items():
                c = "🔴" if d["change"]>0 else "🟢"
                is_fav = sn in st.session_state["favorites"]
                col1, col2, col3 = st.columns([3,1,1])
                with col1: st.write(f"{c} **{sn}**　{d['change']}%")
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
# 騰落推移
# =====================
elif page == "📈 騰落推移":
    st.subheader("📈 テーマ別騰落率の推移")
    st.caption(f"🕐 最終更新：{now}")
    st.info("テーマ一覧ページを開くたびに自動記録されます。")

    with st.spinner("履歴データを読み込み中..."):
        df_hist = load_theme_history()

    if df_hist is None or len(df_hist) < 2:
        st.warning("まだ履歴データが少ないです。「📊 テーマ一覧」ページを開くと本日分が記録されます。")
    else:
        all_theme_cols = [c for c in df_hist.columns if c != "日時"]
        selected_themes = st.multiselect("表示するテーマを選択", all_theme_cols, default=all_theme_cols[:5])

        if selected_themes:
            fig_hist = go.Figure()
            for theme in selected_themes:
                if theme in df_hist.columns:
                    fig_hist.add_trace(go.Scatter(
                        x=df_hist["日時"], y=df_hist[theme],
                        mode="lines+markers", name=theme, line=dict(width=2),
                    ))
            fig_hist.add_hline(y=0, line_dash="dash", line_color="gray")
            fig_hist.update_layout(
                xaxis=dict(title="日付"),
                yaxis=dict(title="平均騰落率（%）", ticksuffix="%"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=12), height=500,
                legend=dict(orientation="h", y=1.1),
                margin=dict(t=60, b=50, l=70, r=20),
            )
            st.plotly_chart(fig_hist, use_container_width=True, config=PLOT_CONFIG)
            st.subheader("📋 直近の記録")
            st.dataframe(df_hist.set_index("日時").tail(10), use_container_width=True)
            st.download_button("📥 全履歴CSV", df_hist.to_csv(index=False, encoding="utf-8-sig"),
                               f"テーマ騰落推移_{now}.csv", "text/csv")

# =====================
# ヒートマップ
# =====================
elif page == "🔥 ヒートマップ":
    st.subheader("🔥 騰落率ヒートマップ（テーマ × 期間）")
    st.caption(f"🕐 最終更新：{now}")

    @st.cache_data(ttl=3600)
    def fetch_heatmap_data():
        heatmap_periods = {"1週間":"5d","1ヶ月":"1mo","3ヶ月":"3mo","6ヶ月":"6mo","1年":"1y"}
        heatmap_data = {}
        for theme_name, stocks in themes.items():
            heatmap_data[theme_name] = {}
            for pl, pc in heatmap_periods.items():
                changes = []
                for _, ticker in stocks.items():
                    try:
                        df = fetch_stock_data(ticker, "2y")
                        if len(df) < 2: continue
                        c = calc_change(get_target_df(df, pc))
                        if c is not None: changes.append(c)
                    except: pass
                heatmap_data[theme_name][pl] = round(sum(changes)/len(changes),2) if changes else None
        return heatmap_data

    with st.spinner("データ取得中..."):
        heatmap_data = fetch_heatmap_data()

    df_heat = pd.DataFrame(heatmap_data).T[["1週間","1ヶ月","3ヶ月","6ヶ月","1年"]]
    z = df_heat.values.tolist()
    text_v = [[f"{v}%" if v is not None else "N/A" for v in row] for row in z]
    fig_heat = go.Figure(go.Heatmap(
        z=z, x=["1週間","1ヶ月","3ヶ月","6ヶ月","1年"], y=df_heat.index.tolist(),
        text=text_v, texttemplate="%{text}",
        colorscale=[[0.0,"#39d353"],[0.5,"#1a1d27"],[1.0,"#ff4b4b"]],
        zmid=0, showscale=True, colorbar=dict(title="騰落率(%)"),
    ))
    fig_heat.update_layout(
        xaxis=dict(title="期間"), yaxis=dict(title="テーマ", autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=11), height=750,
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
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()), index=2)
    period = period_options[selected_label]
    selected_themes = st.multiselect("比較するテーマを選択", list(themes.keys()), default=["半導体","AI・クラウド","防衛・航空宇宙"])

    if len(selected_themes) < 2:
        st.warning("2つ以上のテーマを選択してください")
    else:
        with st.spinner("データ取得中..."):
            fig_comp = go.Figure()
            for theme_name in selected_themes:
                all_changes = {}
                for _, ticker in themes[theme_name].items():
                    try:
                        df = fetch_stock_data(ticker, "2y")
                        if len(df) < 2: continue
                        target_df = get_target_df(df, period)
                        if len(target_df) < 2: continue
                        cum = (target_df["Close"] / target_df["Close"].iloc[0] - 1) * 100
                        for date, val in zip(target_df.index, cum):
                            if date not in all_changes: all_changes[date] = []
                            all_changes[date].append(val)
                    except: pass
                if all_changes:
                    dates = sorted(all_changes.keys())
                    avgs = [round(sum(all_changes[d])/len(all_changes[d]),2) for d in dates]
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

# =====================
# マクロ比較
# =====================
elif page == "🌍 マクロ比較":
    st.subheader("🌍 マクロ指標との比較")
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()), index=3)
    period = period_options[selected_label]
    selected_stock_name = st.selectbox("比較する銘柄を選択", list(all_stocks.keys()))
    selected_ticker = all_stocks[selected_stock_name]

    macro_items = {"日経平均":"^N225","S&P500":"^GSPC","ドル円":"JPY=X","TOPIX(ETF)":"1306.T"}
    colors_macro = {"日経平均":"#ffd700","S&P500":"#4b8bff","ドル円":"#ff9900","TOPIX(ETF)":"#cc44ff"}

    with st.spinner("データ取得中..."):
        fig_macro = go.Figure()
        try:
            df_sel = fetch_stock_data(selected_ticker, "2y")
            target = get_target_df(df_sel, period)
            if len(target) >= 2:
                cum = (target["Close"] / target["Close"].iloc[0] - 1) * 100
                fig_macro.add_trace(go.Scatter(x=target.index, y=cum, mode="lines",
                                                line=dict(color="#ff4b4b", width=3), name=selected_stock_name))
        except: pass

        for name, ticker in macro_items.items():
            try:
                df_m = fetch_stock_data(ticker, "2y")
                target_m = get_target_df(df_m, period)
                if len(target_m) >= 2:
                    cum_m = (target_m["Close"] / target_m["Close"].iloc[0] - 1) * 100
                    fig_macro.add_trace(go.Scatter(x=target_m.index, y=cum_m, mode="lines",
                                                    line=dict(color=colors_macro[name], width=2, dash="dot"), name=name))
            except: pass

    fig_macro.add_hline(y=0, line_dash="dash", line_color="gray")
    fig_macro.update_layout(
        xaxis=dict(title="日付"), yaxis=dict(title="累積リターン（%）", ticksuffix="%"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=12), height=500,
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=60, b=50, l=70, r=20),
    )
    st.plotly_chart(fig_macro, use_container_width=True, config=PLOT_CONFIG)
    st.caption("🔴 選択銘柄　🟡 日経平均　🔵 S&P500　🟠 ドル円　🟣 TOPIX ETF（点線）")

# =====================
# 銘柄検索
# =====================
elif page == "🔎 銘柄検索":
    st.subheader("🔎 銘柄検索")
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()), index=1)
    period = period_options[selected_label]
    query = st.text_input("銘柄名を入力", placeholder="例：トヨタ、ソニー、三菱...")
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
                    df = fetch_stock_data(info["ticker"], "2y")
                    if len(df) < 2: continue
                    target_df = get_target_df(df, period)
                    if len(target_df) < 2: continue
                    change = calc_change(target_df)
                    price = int(target_df["Close"].iloc[-1])
                    day_c = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None
                    rsi_val = round(calc_rsi(df["Close"]).iloc[-1], 1) if len(df)>=15 else None
                    results.append({
                        "銘柄":sn, "テーマ":info["theme"],
                        "株価":f"¥{price:,}",
                        "前日比":f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                        "騰落率":f"🔴 +{change}%" if change and change>0 else f"🟢 {change}%",
                        "RSI":f"{rsi_val}" if rsi_val else "N/A",
                        "ticker":info["ticker"],
                    })
                except: pass

        if results:
            df_s = pd.DataFrame(results).drop(columns=["ticker"]).set_index("銘柄")
            st.dataframe(df_s, use_container_width=True)
            st.download_button("📥 検索結果CSV", df_s.to_csv(encoding="utf-8-sig"),
                               f"銘柄検索_{now}.csv", "text/csv")
            for r in results:
                is_fav = r["銘柄"] in st.session_state["favorites"]
                col1, col2, col3 = st.columns([3,1,1])
                with col1: st.write(f"**{r['銘柄']}**（{r['テーマ']}）　{r['騰落率']}")
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
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()), index=1)
    period = period_options[selected_label]

    if len(st.session_state["favorites"]) == 0:
        st.info("テーマ一覧ページで「☆ 登録」ボタンを押して追加してください。")
    else:
        with st.spinner("データ取得中..."):
            fav_results = []
            for sn, ticker in st.session_state["favorites"].items():
                try:
                    df = fetch_stock_data(ticker, "2y")
                    if len(df) < 2: continue
                    target_df = get_target_df(df, period)
                    if len(target_df) < 2: continue
                    change = calc_change(target_df)
                    rsi_val = round(calc_rsi(df["Close"]).iloc[-1], 1) if len(df)>=15 else None
                    sharpe = calc_sharpe(target_df["Close"])
                    price = int(target_df["Close"].iloc[-1])
                    day_c = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None
                    fav_results.append({
                        "銘柄":sn,"ticker":ticker,"change":change,
                        "price":price,"rsi":rsi_val,"sharpe":sharpe,"day_change":day_c,
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
                "銘柄":r["銘柄"], "株価":f"¥{r['price']:,}",
                "前日比":f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                "騰落率":f"🔴 +{r['change']}%" if r["change"]>0 else f"🟢 {r['change']}%",
                "RSI":f"{rsi} {rsi_alert}" if rsi else "N/A",
                "シャープ":f"{r['sharpe']}" if r["sharpe"] else "N/A",
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
    selected_label = st.selectbox("📅 期間を選択", list(period_options.keys()), index=3)
    period = period_options[selected_label]
    st.caption(f"🕐 最終更新：{now}")

    selected_name = st.sidebar.selectbox(
        "銘柄を選択", list(all_stocks.keys()),
        index=list(all_stocks.keys()).index(st.session_state.get("selected_stock", list(all_stocks.keys())[0]))
    )
    selected_ticker = all_stocks[selected_name]
    st.subheader(f"📈 {selected_name}")

    is_fav = selected_name in st.session_state["favorites"]
    col_f1, col_f2 = st.columns([1,5])
    with col_f1:
        if is_fav:
            if st.button("⭐ 解除"):
                del st.session_state["favorites"][selected_name]; st.rerun()
        else:
            if st.button("☆ 登録"):
                st.session_state["favorites"][selected_name] = selected_ticker; st.rerun()

    with st.spinner("データ取得中..."):
        df = fetch_stock_data(selected_ticker, "2y")

    if len(df) > 0:
        display_df = get_target_df(df, period)
        if len(display_df) < 2:
            st.warning("選択期間のデータが不足しています。別の期間を選択してください。")
        else:
            price_change = calc_change(display_df)
            last_price = int(display_df["Close"].iloc[-1])
            day_c = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None
            w52_high = round(df["High"].tail(252).max(), 0)
            w52_low = round(df["Low"].tail(252).min(), 0)
            price_pos = round((last_price-w52_low)/(w52_high-w52_low)*100,1) if w52_high!=w52_low else None

            # コンパクト指標
            col1,col2,col3,col4,col5,col6 = st.columns(6)
            col1.metric("株価", f"¥{last_price:,}")
            col2.metric("前日比", f"{day_c}%" if day_c else "N/A")
            col3.metric("騰落率", f"{price_change}%")
            col4.metric("52W高値", f"¥{int(w52_high):,}")
            col5.metric("52W安値", f"¥{int(w52_low):,}")
            col6.metric("レンジ位置", f"{price_pos}%" if price_pos else "N/A",
                        "高値圏⚠️" if price_pos and price_pos>80 else "安値圏✅" if price_pos and price_pos<20 else "中間")

            # 財務指標（表形式）
            with st.spinner("財務データ取得中..."):
                f = fetch_fundamentals(selected_ticker)
            fund_df = pd.DataFrame([{
                "PER": f"{f['PER']}倍" if f["PER"] else "N/A",
                "PBR": f"{f['PBR']}倍" if f["PBR"] else "N/A",
                "時価総額": f["時価総額"],
                "売上高": f["売上高"],
                "EPS": f"{f['EPS']}円" if f["EPS"] else "N/A",
            }])
            st.dataframe(fund_df, use_container_width=True, hide_index=True)

            # チャート
            col_a, col_b = st.columns(2)
            with col_a: chart_type = st.radio("チャート", ["ローソク足","折れ線"], horizontal=True)
            with col_b: show_ma = st.checkbox("移動平均線（25日・75日）", value=True)

            st.plotly_chart(make_price_chart(df, chart_type, show_ma),
                            use_container_width=True, config=PLOT_CONFIG)

            vol_colors = ["#ff4b4b" if display_df["Close"].iloc[i]>=display_df["Close"].iloc[i-1]
                          else "#39d353" for i in range(len(display_df))]
            fig_vol = go.Figure(go.Bar(x=display_df.index, y=display_df["Volume"], marker_color=vol_colors))
            fig_vol.update_layout(
                xaxis=dict(title="日付"), yaxis=dict(title="出来高"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=180,
                margin=dict(t=5, b=30, l=70, r=20),
            )
            st.plotly_chart(fig_vol, use_container_width=True, config=PLOT_CONFIG)

            # テクニカル指標（表形式）
            if len(df) >= 30:
                close = df["Close"]
                rsi_series = calc_rsi(close)
                macd, sig_line, hist = calc_macd(close)
                sharpe = calc_sharpe(display_df["Close"])
                rsi_val = round(rsi_series.iloc[-1], 1)
                macd_val = round(macd.iloc[-1], 2)

                tech_df = pd.DataFrame([{
                    "RSI": f"{rsi_val}　{'⚠️買われすぎ' if rsi_val>70 else '⚠️売られすぎ' if rsi_val<30 else '✅中立'}",
                    "MACD": f"{macd_val}　{'📈強気' if hist.iloc[-1]>0 else '📉弱気'}",
                    "シャープレシオ": f"{sharpe}　{'✅良好' if sharpe and sharpe>1 else '⚠️要注意' if sharpe and sharpe<0 else '普通'}" if sharpe else "N/A",
                }])
                st.dataframe(tech_df, use_container_width=True, hide_index=True)

                fig_rsi = go.Figure()
                fig_rsi.add_trace(go.Scatter(x=df.index, y=rsi_series, mode="lines",
                                              line=dict(color="#ff4b4b", width=2), name="RSI"))
                fig_rsi.add_hline(y=70, line_dash="dash", line_color="orange")
                fig_rsi.add_hline(y=30, line_dash="dash", line_color="#39d353")
                fig_rsi.update_layout(yaxis=dict(title="RSI", range=[0,100]),
                                       plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                       font=dict(color="white"), height=180,
                                       margin=dict(t=5,b=25,l=50,r=10))
                st.plotly_chart(fig_rsi, use_container_width=True, config=PLOT_CONFIG)

                hist_colors = ["#ff4b4b" if v>=0 else "#39d353" for v in hist]
                fig_macd = go.Figure()
                fig_macd.add_trace(go.Scatter(x=df.index, y=macd, mode="lines",
                                               line=dict(color="#ff4b4b", width=2), name="MACD"))
                fig_macd.add_trace(go.Scatter(x=df.index, y=sig_line, mode="lines",
                                               line=dict(color="#4b8bff", width=2), name="シグナル"))
                fig_macd.add_trace(go.Bar(x=df.index, y=hist, marker_color=hist_colors, opacity=0.6, name="ヒスト"))
                fig_macd.update_layout(plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                                        font=dict(color="white"), height=180,
                                        legend=dict(orientation="h", y=1.25),
                                        margin=dict(t=20,b=25,l=50,r=10))
                st.plotly_chart(fig_macd, use_container_width=True, config=PLOT_CONFIG)

            csv_d = display_df[["Open","High","Low","Close","Volume"]].copy()
            csv_d.index = csv_d.index.strftime("%Y-%m-%d")
            st.download_button("📥 株価データCSV", csv_d.to_csv(encoding="utf-8-sig"),
                               f"{selected_name}_{now}.csv", "text/csv")
    else:
        st.error("データを取得できませんでした")
