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
div.stButton > button { width: 100%; height: 2.5em; font-size: 0.95em; }
.stPlotlyChart { overflow-x: auto; }
div[data-testid="column"] div.stButton > button {
    background-color: #1e2130;
    border: 1px solid #444;
    color: white;
}
div[data-testid="column"] div.stButton > button:hover {
    background-color: #ff4b4b;
    border-color: #ff4b4b;
}
@media (max-width: 640px) {
    h1 { font-size: 1.4em !important; }
    h2 { font-size: 1.1em !important; }
}
</style>
""", unsafe_allow_html=True)

# =====================
# session_state初期化
# =====================
if "selected_stock" not in st.session_state:
    st.session_state["selected_stock"] = "東京エレクトロン"
if "selected_ticker" not in st.session_state:
    st.session_state["selected_ticker"] = "8035.T"
if "favorites" not in st.session_state:
    st.session_state["favorites"] = {}
if "selected_period" not in st.session_state:
    st.session_state["selected_period"] = "1ヶ月"
if "custom_themes" not in st.session_state:
    st.session_state["custom_themes"] = {}

# =====================
# 25テーマ・約180銘柄
# =====================
DEFAULT_THEMES = {
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
        "伊予銀行":"8385.T","山口FG":"8418.T",
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
        "エムスリー":"2413.T","メドレー":"4480.T","ケアネット":"2150.T",
        "ツムラ":"4540.T","テルモ":"4543.T","シスメックス":"6869.T",
        "オリンパス":"7733.T",
    },
    "食品・飲料": {
        "味の素":"2802.T","キリンHD":"2503.T","日清食品HD":"2897.T",
        "明治HD":"2269.T","サントリー食品":"2587.T","日本ハム":"2282.T",
        "カゴメ":"2811.T","ニッスイ":"1332.T",
    },
    "小売・EC": {
        "ファーストリテイリング":"9983.T","セブン&アイ":"3382.T","MonotaRO":"3064.T",
        "イオン":"8267.T","ニトリHD":"9843.T","Zホールディングス":"4689.T",
        "ウエルシアHD":"3141.T",
    },
    "通信": {
        "NTT":"9432.T","ソフトバンク":"9434.T","KDDI":"9433.T",
        "楽天グループ":"4755.T","インターネットイニシアティブ":"3774.T",
    },
    "鉄鋼・素材": {
        "日本製鉄":"5401.T","JFEホールディングス":"5411.T","神戸製鋼所":"5406.T",
        "大和工業":"5444.T","東京製鐵":"5423.T","日本軽金属HD":"5703.T",
    },
    "化学": {
        "信越化学工業":"4063.T","東レ":"3402.T","住友化学":"4005.T",
        "旭化成":"3407.T","三菱ケミカルグループ":"4188.T","花王":"4452.T",
        "富士フイルムHD":"4901.T",
    },
    "建設・インフラ": {
        "大林組":"1802.T","鹿島建設":"1812.T","大成建設":"1801.T",
        "清水建設":"1803.T","積水ハウス":"1928.T","大和ハウス工業":"1925.T",
    },
    "輸送・物流": {
        "日本郵船":"9101.T","商船三井":"9104.T","ヤマトHD":"9064.T",
        "川崎汽船":"9107.T","センコーグループ":"9069.T","日本通運":"9062.T",
    },
    "防衛・航空宇宙": {
        "三菱重工業":"7011.T","川崎重工業":"7012.T","IHI":"7013.T",
        "三菱電機":"6503.T","豊和工業":"6203.T","日本航空電子工業":"6807.T",
    },
    "フィンテック": {
        "マネックスグループ":"8698.T","SBIホールディングス":"8473.T",
        "GMOフィナンシャルHD":"7177.T","メルカリ":"4385.T",
        "インフォマート":"2492.T","オリエントコーポレーション":"8585.T",
    },
    "再生可能エネルギー": {
        "レノバ":"9519.T","ウエストHD":"1407.T",
        "東京電力HD":"9501.T","関西電力":"9503.T","中部電力":"9502.T",
        "出光興産":"5019.T","ENEOS HD":"5020.T",
    },
    "ロボット・自動化": {
        "ファナック":"6954.T","安川電機":"6506.T","キーエンス":"6861.T",
        "不二越":"6474.T","三菱電機":"6503.T","オムロン":"6645.T",
    },
    "レアアース・資源": {
        "住友金属鉱山":"5713.T","三井物産":"8031.T","三菱商事":"8058.T",
        "丸紅":"8002.T","DOWAホールディングス":"5714.T","太平洋金属":"5441.T",
    },
    "サイバーセキュリティ": {
        "トレンドマイクロ":"4704.T","サイバーセキュリティクラウド":"4493.T",
        "デジタルアーツ":"2326.T","FFRIセキュリティ":"3692.T",
        "ソリトンシステムズ":"3040.T","野村総合研究所":"4307.T",
    },
    "ドローン・空飛ぶ車": {
        "ACSLエアロスペース":"6232.T","ヤマハ発動機":"7272.T",
        "川崎重工業":"7012.T","NTT":"9432.T","富士通":"6702.T",
        "セキド":"9878.T",
    },
    "造船": {
        "三菱重工業":"7011.T","川崎重工業":"7012.T",
        "住友重機械工業":"6302.T","名村造船所":"7014.T","内海造船":"7018.T",
    },
}

# 市場分類データ（日経225・プライム・スタンダード・グロース）
MARKET_SEGMENTS = {
    "日経225主要銘柄": {
        "トヨタ":"7203.T","ソニー":"6758.T","キーエンス":"6861.T",
        "三菱UFJ":"8306.T","東京エレクトロン":"8035.T","信越化学工業":"4063.T",
        "ファーストリテイリング":"9983.T","任天堂":"7974.T","KDDI":"9433.T",
        "リクルートHD":"6098.T","ダイキン工業":"6367.T","富士通":"6702.T",
        "三井物産":"8031.T","三菱商事":"8058.T","日立製作所":"6501.T",
        "NTT":"9432.T","オリンパス":"7733.T","中外製薬":"4519.T",
        "第一三共":"4568.T","武田薬品":"4502.T",
    },
    "プライム注目銘柄": {
        "三菱重工業":"7011.T","川崎重工業":"7012.T","IHI":"7013.T",
        "住友金属鉱山":"5713.T","日本製鉄":"5401.T","JFEホールディングス":"5411.T",
        "東京海上HD":"8766.T","MS&AD":"8725.T","三井不動産":"8801.T",
        "三菱地所":"8802.T","大和ハウス工業":"1925.T","積水ハウス":"1928.T",
    },
    "スタンダード注目銘柄": {
        "静岡銀行":"8355.T","広島銀行":"8379.T","七十七銀行":"8341.T",
        "名村造船所":"7014.T","内海造船":"7018.T","太平洋金属":"5441.T",
        "東京製鐵":"5423.T","大和工業":"5444.T",
    },
    "グロース注目銘柄": {
        "さくらインターネット":"3778.T","メルカリ":"4385.T",
        "サイバーセキュリティクラウド":"4493.T","FFRIセキュリティ":"3692.T",
        "メドレー":"4480.T","ケアネット":"2150.T","レノバ":"9519.T",
        "ACSLエアロスペース":"6232.T",
    },
}

# カスタムテーマとデフォルトテーマを結合
def get_all_themes():
    combined = dict(DEFAULT_THEMES)
    combined.update(st.session_state["custom_themes"])
    return combined

PLOT_CONFIG = {"displayModeBar": False, "staticPlot": True}

# 期間ボタン設定
PERIOD_OPTIONS = {
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
    if period == "1d":   return df.tail(2)
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
def fetch_all_theme_data(period: str, theme_keys: tuple) -> tuple:
    themes = get_all_themes()
    theme_results = []
    theme_details = {}

    for theme_name in theme_keys:
        stocks = themes.get(theme_name, {})
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
                w52_low  = round(df["Low"].tail(252).min(), 0)
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
            total_tv = sum(d["trade_value"] for d in details.values())
            theme_results.append({
                "テーマ": theme_name,
                "平均騰落率(%)": avg,
                "出来高増減(%)": vol_chg,
                "合計出来高": int(total_vol),
                "合計売買代金": total_tv,
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
        return None

def save_theme_history(theme_results):
    try:
        spreadsheet = get_gsheet()
        if spreadsheet is None: return False
        try:
            sheet = spreadsheet.worksheet("履歴")
        except gspread.WorksheetNotFound:
            sheet = spreadsheet.add_worksheet(title="履歴", rows=10000, cols=40)
            headers = ["日時"] + [r["テーマ"] for r in theme_results]
            sheet.append_row(headers)
        today_date = datetime.now().strftime("%Y-%m-%d")
        existing = sheet.col_values(1)
        if any(today_date in str(d) for d in existing):
            return False
        row = [datetime.now().strftime("%Y-%m-%d %H:%M")] + [r["平均騰落率(%)"] for r in theme_results]
        sheet.append_row(row)
        return True
    except:
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
def make_bar_chart(labels, values, colors, height=520, left_margin=160):
    if not values or not labels:
        fig = go.Figure()
        fig.update_layout(height=200, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        return fig
    min_v = min(values)
    max_v = max(values)
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
                   range=[min_v*1.3 if min_v<0 else -2, max_v*1.3 if max_v>0 else 2]),
        yaxis=dict(title="", autorange="reversed"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=11),
        height=height, margin=dict(t=10, b=40, l=left_margin, r=20),
    )
    return fig

def make_price_chart(df, display_df, chart_type="ローソク足", show_ma=True):
    """株価チャート：目盛りを月単位に設定"""
    fig = go.Figure()
    if chart_type == "ローソク足":
        fig.add_trace(go.Candlestick(
            x=display_df.index, open=display_df["Open"], high=display_df["High"],
            low=display_df["Low"], close=display_df["Close"],
            increasing_line_color="#ff4b4b", decreasing_line_color="#39d353", name="株価",
        ))
    else:
        fig.add_trace(go.Scatter(
            x=display_df.index, y=display_df["Close"], mode="lines",
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
        xaxis=dict(
            title="日付",
            rangeslider=dict(visible=False),
            dtick="M1",           # 1ヶ月ごとの目盛り
            tickformat="%y/%m",   # 例：25/01
            ticklabelmode="period",
            range=[display_df.index[0], display_df.index[-1]],
        ),
        yaxis=dict(title="株価（円）", tickprefix="¥"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"), height=400,
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=40, b=40, l=70, r=20),
    )
    return fig

def period_buttons():
    """期間ボタンをボタン形式で横並び表示"""
    cols = st.columns(len(PERIOD_OPTIONS))
    for i, (label, code) in enumerate(PERIOD_OPTIONS.items()):
        with cols[i]:
            is_selected = st.session_state["selected_period"] == label
            btn_label = f"**{label}**" if is_selected else label
            if st.button(btn_label, key=f"period_btn_{label}",
                         use_container_width=True):
                st.session_state["selected_period"] = label
                st.rerun()
    # 選択中の期間を表示
    st.caption(f"📅 選択中：**{st.session_state['selected_period']}**")
    return PERIOD_OPTIONS[st.session_state["selected_period"]]

# =====================
# ページ切り替え
# =====================
page = st.sidebar.radio("ページ", [
    "📊 テーマ一覧",
    "📈 騰落推移",
    "🔥 ヒートマップ",
    "📉 テーマ比較",
    "🌍 マクロ比較",
    "📋 市場別ランキング",
    "🔎 銘柄検索",
    "⭐ お気に入り",
    "🔍 個別株詳細",
    "🏷️ カスタムテーマ",
])

fav_count = len(st.session_state["favorites"])
if fav_count > 0:
    st.sidebar.info(f"⭐ お気に入り：{fav_count}銘柄")
if st.sidebar.button("🔄 データを最新に更新"):
    st.cache_data.clear()
    st.rerun()
st.sidebar.caption("※データは1時間キャッシュされます")

now = datetime.now().strftime("%Y年%m月%d日 %H:%M")
themes = get_all_themes()
all_stocks = {}
for stk in themes.values():
    for name, ticker in stk.items():
        all_stocks[name] = ticker

# =====================
# テーマ一覧
# =====================
if page == "📊 テーマ一覧":
    st.caption(f"🕐 最終更新：{now}　　{len(themes)}テーマ・約{len(all_stocks)}銘柄")

    # 期間ボタン（上部）
    period = period_buttons()

    # 表示テーマ数選択
    col_disp1, col_disp2 = st.columns([3, 1])
    with col_disp2:
        display_count = st.selectbox("表示テーマ数", [5, 10, 15, 25, 99], index=0,
                                      label_visibility="collapsed")
        st.caption(f"上位/下位 {display_count if display_count < 99 else '全'}テーマ")

    theme_keys = tuple(themes.keys())
    with st.spinner("データを取得中...（初回は時間がかかります）"):
        theme_results, theme_details = fetch_all_theme_data(period, theme_keys)

    # 履歴保存
    saved = save_theme_history(theme_results)
    if saved:
        st.success("📊 本日のテーマ騰落率を履歴に保存しました！")

    # 表示件数に応じて上位・下位を切り出し
    n = display_count if display_count < 99 else len(theme_results)
    top_results = theme_results[:n]
    bot_results = theme_results[-n:] if display_count < 99 else []

    # === 上位テーマランキング ===
    st.subheader(f"🔴 上位{n}テーマ　騰落率ランキング")
    top_labels = [f"{i+1}位　{r['テーマ']}" for i, r in enumerate(top_results)]
    top_values = [r["平均騰落率(%)"] for r in top_results]
    top_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in top_values]
    st.plotly_chart(make_bar_chart(top_labels, top_values, top_colors,
                    max(300, len(top_results)*38), 170),
                    use_container_width=True, config=PLOT_CONFIG)

    # === 下位テーマランキング ===
    if bot_results and display_count < 99:
        st.subheader(f"🟢 下位{n}テーマ　騰落率ランキング")
        total = len(theme_results)
        bot_labels = [f"{total-n+i+1}位　{r['テーマ']}" for i, r in enumerate(bot_results)]
        bot_values = [r["平均騰落率(%)"] for r in bot_results]
        bot_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in bot_values]
        st.plotly_chart(make_bar_chart(bot_labels, bot_values, bot_colors,
                        max(300, len(bot_results)*38), 170),
                        use_container_width=True, config=PLOT_CONFIG)

    # === テーマ別出来高・売買代金ランキング ===
    st.subheader("📊 テーマ別ランキング")
    col_rank1, col_rank2 = st.columns(2)

    # 出来高ランキング
    vol_sorted = sorted(theme_results, key=lambda x: x["合計出来高"], reverse=True)[:10]
    with col_rank1:
        st.markdown("**🔢 テーマ別出来高 TOP10**")
        vol_df = pd.DataFrame([
            {"テーマ": r["テーマ"], "出来高": f"{int(r['合計出来高']):,}"}
            for r in vol_sorted
        ]).set_index("テーマ")
        st.dataframe(vol_df, use_container_width=True)

    # 売買代金ランキング
    tv_sorted = sorted(theme_results, key=lambda x: x["合計売買代金"], reverse=True)[:10]
    with col_rank2:
        st.markdown("**💴 テーマ別売買代金 TOP10**")
        tv_df = pd.DataFrame([
            {"テーマ": r["テーマ"], "売買代金": format_large_number(r["合計売買代金"])}
            for r in tv_sorted
        ]).set_index("テーマ")
        st.dataframe(tv_df, use_container_width=True)

    # === 全テーマ一覧表 ===
    st.subheader("📋 全テーマ一覧")
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

    # === テーマ別詳細 ===
    st.subheader("🔍 テーマ別詳細（クリックで展開）")
    for result in theme_results:
        theme_name = result["テーマ"]
        stocks_d = theme_details.get(theme_name, {})
        if not stocks_d: continue
        with st.expander(f"{theme_name}　騰落率 {result['平均騰落率(%)']}%　出来高増減 {result['出来高増減(%)']}%"):
            s_labels = list(stocks_d.keys())
            s_values = [stocks_d[s]["change"] for s in s_labels]
            s_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in s_values]
            st.plotly_chart(make_bar_chart(s_labels, s_values, s_colors,
                            max(220, len(s_labels)*38), 140),
                            use_container_width=True, config=PLOT_CONFIG)

            # テーマ内 個別株出来高・売買代金ランキング
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("**🔢 個別株出来高ランキング**")
                vol_rank = sorted(stocks_d.items(), key=lambda x: x[1]["volume"], reverse=True)
                vr_df = pd.DataFrame([{"銘柄":k,"出来高":f"{v['volume']:,}"} for k,v in vol_rank]).set_index("銘柄")
                st.dataframe(vr_df, use_container_width=True)
            with col_r2:
                st.markdown("**💴 個別株売買代金ランキング**")
                tv_rank = sorted(stocks_d.items(), key=lambda x: x[1]["trade_value"], reverse=True)
                tvr_df = pd.DataFrame([{"銘柄":k,"売買代金":format_large_number(v["trade_value"])} for k,v in tv_rank]).set_index("銘柄")
                st.dataframe(tvr_df, use_container_width=True)

            # 銘柄詳細テーブル
            stock_table = []
            for sn, d in stocks_d.items():
                rsi = d.get("rsi")
                rsi_alert = "⚠️買" if rsi and rsi>70 else "⚠️売" if rsi and rsi<30 else "✅"
                day_c = d.get("day_change")
                stock_table.append({
                    "銘柄": sn,
                    "株価": f"¥{int(d['price']):,}",
                    "前日比": f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                    "騰落率": f"🔴 +{d['change']}%" if d["change"]>0 else f"🟢 {d['change']}%",
                    "RSI": f"{rsi} {rsi_alert}" if rsi else "N/A",
                    "シャープ": f"{d['sharpe']}" if d["sharpe"] else "N/A",
                    "52W高値": f"¥{int(d['52w_high']):,}" if d["52w_high"] else "N/A",
                    "52W安値": f"¥{int(d['52w_low']):,}" if d["52w_low"] else "N/A",
                })
            df_stock = pd.DataFrame(stock_table).set_index("銘柄")
            st.dataframe(df_stock, use_container_width=True)
            st.download_button(f"📥 {theme_name} CSV", df_stock.to_csv(encoding="utf-8-sig"),
                               f"{theme_name}_{now}.csv", "text/csv", key=f"csv_{theme_name}")

            for sn, d in stocks_d.items():
                c = "🔴" if d["change"]>0 else "🟢"
                is_fav = sn in st.session_state["favorites"]
                col1, col2, col3 = st.columns([3,1,1])
                with col1: st.write(f"{c} **{sn}**　{d['change']}%")
                with col2:
                    if st.button("詳細チャート", key=f"chart_{theme_name}_{sn}"):
                        st.session_state["selected_stock"] = sn
                        st.session_state["selected_ticker"] = d["ticker"]
                        st.rerun()
                with col3:
                    if is_fav:
                        if st.button("⭐ 解除", key=f"fav_{theme_name}_{sn}"):
                            del st.session_state["favorites"][sn]; st.rerun()
                    else:
                        if st.button("☆ 登録", key=f"fav_{theme_name}_{sn}"):
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
                xaxis=dict(title="日付", dtick="M1", tickformat="%y/%m"),
                yaxis=dict(title="平均騰落率（%）", ticksuffix="%"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=12), height=500,
                legend=dict(orientation="h", y=1.1),
                margin=dict(t=60, b=50, l=70, r=20),
            )
            st.plotly_chart(fig_hist, use_container_width=True, config=PLOT_CONFIG)
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
    def fetch_heatmap_data(theme_keys):
        heatmap_periods = {"1週間":"5d","1ヶ月":"1mo","3ヶ月":"3mo","6ヶ月":"6mo","1年":"1y"}
        heatmap_data = {}
        _themes = get_all_themes()
        for theme_name in theme_keys:
            stocks = _themes.get(theme_name, {})
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

    theme_keys = tuple(themes.keys())
    with st.spinner("データ取得中..."):
        heatmap_data = fetch_heatmap_data(theme_keys)

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
        font=dict(color="white", size=11), height=max(600, len(df_heat)*28),
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
    period = period_buttons()
    selected_themes_cmp = st.multiselect("比較するテーマを選択", list(themes.keys()),
                                          default=list(themes.keys())[:2])
    if len(selected_themes_cmp) < 2:
        st.warning("2つ以上のテーマを選択してください")
    else:
        with st.spinner("データ取得中..."):
            fig_comp = go.Figure()
            for theme_name in selected_themes_cmp:
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
                    fig_comp.add_trace(go.Scatter(x=dates, y=avgs, mode="lines",
                                                   name=theme_name, line=dict(width=2)))
        fig_comp.add_hline(y=0, line_dash="dash", line_color="gray")
        fig_comp.update_layout(
            xaxis=dict(title="日付", dtick="M1", tickformat="%y/%m"),
            yaxis=dict(title="累積リターン（%）", ticksuffix="%"),
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
    period = period_buttons()
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
        xaxis=dict(title="日付", dtick="M1", tickformat="%y/%m"),
        yaxis=dict(title="累積リターン（%）", ticksuffix="%"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=12), height=500,
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=60, b=50, l=70, r=20),
    )
    st.plotly_chart(fig_macro, use_container_width=True, config=PLOT_CONFIG)

# =====================
# 市場別ランキング（新機能）
# =====================
elif page == "📋 市場別ランキング":
    st.subheader("📋 市場別ランキング")
    st.caption("日経225・プライム・スタンダード・グロース別の騰落率ランキング")
    period = period_buttons()

    for seg_name, seg_stocks in MARKET_SEGMENTS.items():
        with st.expander(f"📌 {seg_name}", expanded=True):
            with st.spinner(f"{seg_name} データ取得中..."):
                seg_results = []
                for sn, ticker in seg_stocks.items():
                    try:
                        df = fetch_stock_data(ticker, "2y")
                        if len(df) < 2: continue
                        target_df = get_target_df(df, period)
                        if len(target_df) < 2: continue
                        change = calc_change(target_df)
                        if change is None: continue
                        day_c = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None
                        price = int(df["Close"].iloc[-1])
                        rv = target_df["Volume"].mean()
                        trade_val = int(rv * price)
                        seg_results.append({
                            "銘柄": sn, "株価": f"¥{price:,}",
                            "前日比": f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                            "騰落率": change,
                            "売買代金": format_large_number(trade_val),
                            "ticker": ticker,
                        })
                    except: pass

            if seg_results:
                seg_results.sort(key=lambda x: x["騰落率"], reverse=True)
                labels = [f"{i+1}位 {r['銘柄']}" for i, r in enumerate(seg_results)]
                values = [r["騰落率"] for r in seg_results]
                colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in values]
                st.plotly_chart(make_bar_chart(labels, values, colors,
                                max(250, len(seg_results)*35), 160),
                                use_container_width=True, config=PLOT_CONFIG)

                df_seg = pd.DataFrame([{
                    "銘柄": r["銘柄"], "株価": r["株価"], "前日比": r["前日比"],
                    "騰落率": f"🔴 +{r['騰落率']}%" if r["騰落率"]>0 else f"🟢 {r['騰落率']}%",
                    "売買代金": r["売買代金"],
                } for r in seg_results]).set_index("銘柄")
                st.dataframe(df_seg, use_container_width=True)

# =====================
# 銘柄検索
# =====================
elif page == "🔎 銘柄検索":
    st.subheader("🔎 銘柄検索")
    period = period_buttons()
    query = st.text_input("銘柄名を入力", placeholder="例：トヨタ、ソニー、三菱...")
    theme_filter = st.multiselect("テーマで絞り込む（任意）", list(themes.keys()))

    search_targets = {}
    for tn, stocks_s in themes.items():
        if theme_filter and tn not in theme_filter: continue
        for sn, ticker in stocks_s.items():
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
                        "銘柄":sn, "テーマ":info["theme"], "株価":f"¥{price:,}",
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
    period = period_buttons()
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
                        max(280, len(fav_results)*45), 130),
                        use_container_width=True, config=PLOT_CONFIG)

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
    period = period_buttons()
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
            w52_low  = round(df["Low"].tail(252).min(), 0)
            price_pos = round((last_price-w52_low)/(w52_high-w52_low)*100,1) if w52_high!=w52_low else None

            col1,col2,col3,col4,col5,col6 = st.columns(6)
            col1.metric("株価", f"¥{last_price:,}")
            col2.metric("前日比", f"{day_c}%" if day_c else "N/A")
            col3.metric("騰落率", f"{price_change}%")
            col4.metric("52W高値", f"¥{int(w52_high):,}")
            col5.metric("52W安値", f"¥{int(w52_low):,}")
            col6.metric("レンジ位置", f"{price_pos}%" if price_pos else "N/A",
                        "高値圏⚠️" if price_pos and price_pos>80 else "安値圏✅" if price_pos and price_pos<20 else "中間")

            with st.spinner("財務データ取得中..."):
                f = fetch_fundamentals(selected_ticker)
            fund_df = pd.DataFrame([{
                "PER": f"{f['PER']}倍" if f["PER"] else "N/A",
                "PBR": f"{f['PBR']}倍" if f["PBR"] else "N/A",
                "時価総額": f["時価総額"], "売上高": f["売上高"],
                "EPS": f"{f['EPS']}円" if f["EPS"] else "N/A",
            }])
            st.dataframe(fund_df, use_container_width=True, hide_index=True)

            col_a, col_b = st.columns(2)
            with col_a: chart_type = st.radio("チャート", ["ローソク足","折れ線"], horizontal=True)
            with col_b: show_ma = st.checkbox("移動平均線（25日・75日）", value=True)

            # 月単位目盛りの株価チャート
            st.plotly_chart(make_price_chart(df, display_df, chart_type, show_ma),
                            use_container_width=True, config=PLOT_CONFIG)

            vol_colors = ["#ff4b4b" if display_df["Close"].iloc[i]>=display_df["Close"].iloc[i-1]
                          else "#39d353" for i in range(len(display_df))]
            fig_vol = go.Figure(go.Bar(x=display_df.index, y=display_df["Volume"], marker_color=vol_colors))
            fig_vol.update_layout(
                xaxis=dict(title="日付", dtick="M1", tickformat="%y/%m"),
                yaxis=dict(title="出来高"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white"), height=180,
                margin=dict(t=5, b=30, l=70, r=20),
            )
            st.plotly_chart(fig_vol, use_container_width=True, config=PLOT_CONFIG)

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
                fig_rsi.update_layout(
                    yaxis=dict(title="RSI", range=[0,100]),
                    xaxis=dict(dtick="M1", tickformat="%y/%m",
                               range=[display_df.index[0], display_df.index[-1]]),
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
                fig_macd.add_trace(go.Bar(x=df.index, y=hist, marker_color=hist_colors,
                                           opacity=0.6, name="ヒスト"))
                fig_macd.update_layout(
                    xaxis=dict(dtick="M1", tickformat="%y/%m",
                               range=[display_df.index[0], display_df.index[-1]]),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
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

# =====================
# カスタムテーマ（新機能）
# =====================
elif page == "🏷️ カスタムテーマ":
    st.subheader("🏷️ カスタムテーマ作成・編集")
    st.caption("自分だけのオリジナルテーマを作成できます。")

    tab1, tab2 = st.tabs(["➕ 新規作成", "✏️ 編集・削除"])

    with tab1:
        st.markdown("#### 新しいテーマを作成")
        new_theme_name = st.text_input("テーマ名", placeholder="例：マイお気に入り、注目銘柄...")

        st.markdown("#### 銘柄を追加（銘柄名とティッカーコードを入力）")
        st.caption("ティッカーコード例：トヨタ → 7203.T　ソニー → 6758.T")

        if "new_stocks" not in st.session_state:
            st.session_state["new_stocks"] = [{"name":"","ticker":""}]

        for i, stock in enumerate(st.session_state["new_stocks"]):
            col1, col2, col3 = st.columns([2,2,1])
            with col1:
                st.session_state["new_stocks"][i]["name"] = st.text_input(
                    f"銘柄名 {i+1}", value=stock["name"], key=f"ns_name_{i}",
                    placeholder="例：トヨタ")
            with col2:
                st.session_state["new_stocks"][i]["ticker"] = st.text_input(
                    f"ティッカー {i+1}", value=stock["ticker"], key=f"ns_ticker_{i}",
                    placeholder="例：7203.T")
            with col3:
                st.write("")
                st.write("")
                if st.button("削除", key=f"ns_del_{i}") and len(st.session_state["new_stocks"]) > 1:
                    st.session_state["new_stocks"].pop(i)
                    st.rerun()

        if st.button("➕ 銘柄を追加"):
            st.session_state["new_stocks"].append({"name":"","ticker":""})
            st.rerun()

        if st.button("✅ テーマを保存", type="primary"):
            if not new_theme_name:
                st.error("テーマ名を入力してください")
            elif new_theme_name in DEFAULT_THEMES:
                st.error("デフォルトテーマと同じ名前は使えません")
            else:
                valid_stocks = {s["name"]: s["ticker"]
                                for s in st.session_state["new_stocks"]
                                if s["name"] and s["ticker"]}
                if not valid_stocks:
                    st.error("銘柄を1つ以上入力してください")
                else:
                    st.session_state["custom_themes"][new_theme_name] = valid_stocks
                    st.session_state["new_stocks"] = [{"name":"","ticker":""}]
                    st.success(f"「{new_theme_name}」を保存しました！テーマ一覧に反映されます。")
                    st.rerun()

    with tab2:
        if not st.session_state["custom_themes"]:
            st.info("まだカスタムテーマがありません。「新規作成」タブから作成してください。")
        else:
            st.markdown("#### 作成済みカスタムテーマ")
            for ct_name, ct_stocks in list(st.session_state["custom_themes"].items()):
                with st.expander(f"📌 {ct_name}（{len(ct_stocks)}銘柄）"):
                    st.write("**銘柄一覧：**")
                    for sn, ticker in ct_stocks.items():
                        st.write(f"・{sn}（{ticker}）")

                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        if st.button(f"✏️ 編集", key=f"edit_{ct_name}"):
                            st.session_state["editing_theme"] = ct_name
                            st.session_state["new_stocks"] = [{"name":k,"ticker":v} for k,v in ct_stocks.items()]
                            st.info(f"「新規作成」タブで「{ct_name}」を編集できます。保存すると上書きされます。")
                    with col_edit2:
                        if st.button(f"🗑️ 削除", key=f"del_{ct_name}"):
                            del st.session_state["custom_themes"][ct_name]
                            st.success(f"「{ct_name}」を削除しました")
                            st.rerun()
