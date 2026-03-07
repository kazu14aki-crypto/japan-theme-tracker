import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
import datetime as _dt2
from concurrent.futures import ThreadPoolExecutor, as_completed

# =====================
# ページ基本設定
# =====================
st.set_page_config(
    page_title="StockWaveJP",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── StockWaveJP SVGロゴ（ヘッダー） ──
st.markdown("""
<div style="display:flex;align-items:center;gap:14px;padding:10px 0 6px 0;">
  <svg width="52" height="52" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
    <line x1="28" y1="4" x2="28" y2="10" stroke="#e63030" stroke-width="2.2" stroke-linecap="round"/>
    <line x1="42" y1="9"  x2="38" y2="14" stroke="#e63030" stroke-width="2.2" stroke-linecap="round"/>
    <line x1="14" y1="9"  x2="18" y2="14" stroke="#e63030" stroke-width="2.2" stroke-linecap="round"/>
    <line x1="50" y1="21" x2="45" y2="23" stroke="#e63030" stroke-width="1.8" stroke-linecap="round"/>
    <line x1="6"  y1="21" x2="11" y2="23" stroke="#e63030" stroke-width="1.8" stroke-linecap="round"/>
    <path d="M11,31 A17,17 0 0,1 45,31" fill="none" stroke="#e63030" stroke-width="2.5"/>
    <circle cx="28" cy="31" r="5.5" fill="#e63030"/>
    <line x1="3"  y1="31" x2="11" y2="31" stroke="#e63030" stroke-width="2.2" stroke-linecap="round"/>
    <line x1="45" y1="31" x2="53" y2="31" stroke="#e63030" stroke-width="2.2" stroke-linecap="round"/>
    <path d="M3,43 Q9,36 15,43 Q21,50 27,43 Q33,36 39,43 Q45,50 51,43 Q54,36 53,43"
      stroke="white" stroke-width="2.5" fill="none" stroke-linecap="round" stroke-linejoin="round"/>
  </svg>
  <div style="display:flex;flex-direction:column;gap:2px;line-height:1;">
    <div style="display:flex;align-items:baseline;gap:0;">
      <span style="font-family:'Bebas Neue','Arial Black',sans-serif;font-size:36px;letter-spacing:0.06em;color:#e63030;text-shadow:0 0 20px rgba(230,48,48,0.3);line-height:1;">STOCK</span>
      <span style="font-family:'Bebas Neue','Arial Black',sans-serif;font-size:36px;letter-spacing:0.06em;color:#ffffff;line-height:1;">WAVE</span>
      <span style="font-family:'Bebas Neue','Arial Black',sans-serif;font-size:16px;letter-spacing:0.3em;color:#e63030;padding-bottom:3px;margin-left:4px;line-height:1;">JP</span>
    </div>
    <div style="font-size:11px;letter-spacing:0.55em;color:#3a4560;font-weight:700;">株　式　波　動</div>
  </div>
</div>
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
""", unsafe_allow_html=True)

# =====================
# カラーテーマ CSS
# =====================
COLOR_THEMES = {
    "dark": {
        "bg_main": "#0a0c14", "bg_sidebar": "#0d1020", "bg_card": "#0d1020",
        "border": "#1a1e30", "text_primary": "#e8eaf0", "text_secondary": "#8090a8",
        "btn_bg": "#1e2130", "btn_border": "#444", "btn_color": "white", "accent": "#ff4b4b",
    },
    "light": {
        "bg_main": "#f4f5f8", "bg_sidebar": "#ffffff", "bg_card": "#ffffff",
        "border": "#d8dae0", "text_primary": "#111111", "text_secondary": "#444444",
        "btn_bg": "#eaecf2", "btn_border": "#cccccc", "btn_color": "#111111", "accent": "#cc1818",
    },
    "navy": {
        "bg_main": "#06080f", "bg_sidebar": "#090c1a", "bg_card": "#0b0e1e",
        "border": "#141828", "text_primary": "#e8eaf0", "text_secondary": "#7a8aaa",
        "btn_bg": "#10152a", "btn_border": "#252c45", "btn_color": "#c8d0e8", "accent": "#3a7ff0",
    },
}

_ct = st.session_state.get("color_theme", "dark")
_c  = COLOR_THEMES.get(_ct, COLOR_THEMES["dark"])

st.markdown(f"""
<style>
.stApp {{ background-color: {_c['bg_main']} !important; }}
section[data-testid="stSidebar"] {{ background-color: {_c['bg_sidebar']} !important; }}
.stMarkdown, .stMarkdown p, h1, h2, h3, h4 {{ color: {_c['text_primary']} !important; }}
[data-testid="stDataFrame"] * {{ color: {_c['text_primary']} !important; background-color: {_c['bg_card']} !important; }}
div.stButton > button {{ background-color: {_c['btn_bg']} !important; color: {_c['btn_color']} !important; border: 1px solid {_c['btn_border']} !important; width:100%; }}
div.stButton > button:hover {{ background-color: {_c['accent']} !important; border-color: {_c['accent']} !important; color: white !important; }}
</style>
""", unsafe_allow_html=True)

# =====================
# セッション状態初期化
# =====================
if "selected_period" not in st.session_state: st.session_state["selected_period"] = "1ヶ月"
if "color_theme" not in st.session_state: st.session_state["color_theme"] = "dark"
if "custom_themes" not in st.session_state: st.session_state["custom_themes"] = {}

# =====================
# テーマ・銘柄データ定義
# =====================
DEFAULT_THEMES = {
    "半導体": {"東京エレクトロン":"8035.T","アドバンテスト":"6857.T","ルネサス":"6723.T","ディスコ":"6146.T","SUMCO":"3436.T","レーザーテック":"6920.T","ソシオネクスト":"6526.T"},
    "AI・クラウド": {"富士通":"6702.T","NEC":"6701.T","さくらインターネット":"3778.T","日立製作所":"6501.T","オービック":"4684.T","GMOインターネット":"9449.T"},
    "EV・電気自動車": {"トヨタ":"7203.T","パナソニック":"6752.T","住友電気工業":"5802.T","デンソー":"6902.T","日産自動車":"7201.T","本田技研工業":"7267.T"},
    "ゲーム・エンタメ": {"任天堂":"7974.T","ソニー":"6758.T","カプコン":"9697.T","バンダイナムコ":"7832.T","スクウェア・エニックス":"9684.T","コナミ":"9766.T"},
    "銀行・金融": {"三菱UFJ":"8306.T","三井住友":"8316.T","みずほ":"8411.T","りそな":"8308.T","ゆうちょ銀行":"7182.T","野村HD":"8604.T"},
    "不動産": {"三井不動産":"8801.T","住友不動産":"8830.T","東急不動産HD":"3289.T","三菱地所":"8802.T","野村不動産HD":"3231.T"},
    "防衛・航空宇宙": {"三菱重工業":"7011.T","川崎重工業":"7012.T","IHI":"7013.T","三菱電機":"6503.T","東京計器":"7721.T"},
    "再生可能エネルギー": {"レノバ":"9519.T","ウエストHD":"1407.T","東京電力HD":"9501.T","関西電力":"9503.T","ENEOS HD":"5020.T"},
    "造船": {"三菱重工業":"7011.T","川崎重工業":"7012.T","名村造船所":"7014.T","内海造船":"7018.T","三井E&S":"7003.T"},
    "観光・レジャー": {"オリエンタルランド":"4661.T","東急":"9005.T","近鉄グループHD":"9041.T","リクルートHD":"6098.T","JAL":"9201.T","ANA":"9202.T"},
}

def get_all_themes():
    combined = dict(DEFAULT_THEMES)
    combined.update(st.session_state["custom_themes"])
    return combined

# =====================
# 計算・データ取得ロジック
# =====================
def get_target_df(df, period_key):
    mapping = {"1日":2, "1週間":5, "1ヶ月":21, "3ヶ月":63, "6ヶ月":126, "1年":252, "2年":504}
    return df.tail(mapping.get(period_key, 21))

def calc_change(df):
    if len(df) < 2: return 0.0
    return round((df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0] * 100, 2)

@st.cache_data(ttl=300)
def fetch_stock_data(ticker):
    try:
        return yf.Ticker(ticker).history(period="2y", auto_adjust=True)
    except:
        return pd.DataFrame()

def _fetch_single_stock(args):
    stock_name, ticker, period_key = args
    df = fetch_stock_data(ticker)
    if df.empty or len(df) < 2: return None
    target_df = get_target_df(df, period_key)
    change = calc_change(target_df)
    last_price = df["Close"].iloc[-1]
    return {"name": stock_name, "change": change, "price": last_price}

@st.cache_data(ttl=300)
def fetch_all_theme_data(period_key, theme_keys):
    all_themes = get_all_themes()
    theme_results = []
    
    for theme_name in theme_keys:
        stocks = all_themes.get(theme_name, {})
        args_list = [(name, tk, period_key) for name, tk in stocks.items()]
        changes = []
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(_fetch_single_stock, a) for a in args_list]
            for f in as_completed(futures):
                res = f.result()
                if res: changes.append(res["change"])
        
        if changes:
            avg = round(sum(changes) / len(changes), 2)
            theme_results.append({"テーマ": theme_name, "平均騰落率(%)": avg})
    
    # ── 順位付与ロジック ──
    theme_results.sort(key=lambda x: x["平均騰落率(%)"], reverse=True)
    for i, res in enumerate(theme_results):
        res["順位"] = i + 1
        
    return theme_results

# =====================
# グラフ描画関数（完成版）
# =====================
def make_bar_chart(labels, values, colors, rank_labels=None):
    if not values: return go.Figure()
    n = len(values)
    
    # 順位色の設定
    RANK_COLORS = {1: "#FFD700", 2: "#C0C0C0", 3: "#CD7F32"}
    RANK_DEFAULT = "#7a8aaa"

    fig = go.Figure(go.Bar(
        y=list(range(n)),
        x=values,
        orientation="h",
        marker_color=colors,
        text=[f" {v:+.2f}%" for v in values],
        textposition="auto",
        textfont=dict(color="white", size=12),
        cliponaxis=False
    ))

    # 💡 順位ラベル（アノテーション）の追加
    annotations = []
    if rank_labels:
        for i, rank in enumerate(rank_labels):
            color = RANK_COLORS.get(rank, RANK_DEFAULT)
            annotations.append(dict(
                xref="paper", yref="y", x=-0.02, y=i,
                xanchor="right", yanchor="middle",
                text=f"<b>{rank}位</b>",
                font=dict(color=color, size=13),
                showarrow=False
            ))

    fig.update_layout(
        height=max(300, n * 40),
        margin=dict(l=150, r=40, t=20, b=20),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        xaxis=dict(showgrid=False, zeroline=True, zerolinecolor="#444", showticklabels=False),
        yaxis=dict(tickvals=list(range(n)), ticktext=labels, showgrid=False),
        annotations=annotations,
        showlegend=False
    )
    return fig

# =====================
# メイン UI 制御
# =====================
def main():
    # サイドバー：設定
    with st.sidebar:
        st.header("⚙️ 設定")
        st.session_state["selected_period"] = st.radio(
            "表示期間", ["1日", "1週間", "1ヶ月", "3ヶ月", "6ヶ月", "1年", "2年"], 
            index=2
        )
        st.session_state["color_theme"] = st.selectbox(
            "テーマカラー", list(COLOR_THEMES.keys()), 
            format_func=lambda x: COLOR_THEMES[x]["label"] if "label" in COLOR_THEMES[x] else x
        )

    # メインエリア
    st.write(f"### 📊 テーマ別騰落ランキング ({st.session_state['selected_period']})")
    
    # データ取得
    with st.spinner("データを取得中..."):
        results = fetch_all_theme_data(
            st.session_state["selected_period"], 
            tuple(get_all_themes().keys())
        )

    if not results:
        st.error("データの取得に失敗しました。")
        return

    # 表示用データフレーム作成
    df = pd.DataFrame(results)
    
    # レイアウト分け
    col1, col2 = st.columns([1, 1.2])

    with col1:
        st.subheader("順位一覧")
        # 順位を一番左にして表示
        st.dataframe(
            df[["順位", "テーマ", "平均騰落率(%)"]].set_index("順位"),
            use_container_width=True,
            height=600
        )

    with col2:
        st.subheader("騰落率グラフ")
        # グラフ用にデータを逆順（上位が上に来るようにPlotlyは下のIndexから描画するため）
        plot_df = df.iloc[::-1]
        labels = plot_df["テーマ"].tolist()
        values = plot_df["平均騰落率(%)"].tolist()
        ranks = plot_df["順位"].tolist()
        colors = ["#ff4b4b" if v >= 0 else "#00d1b2" for v in values]
        
        fig = make_bar_chart(labels, values, colors, rank_labels=ranks)
        st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})

    # フッター
    st.markdown("---")
    st.caption(f"最終更新: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | Data by yfinance")

if __name__ == "__main__":
    main()
