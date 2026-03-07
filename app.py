import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

st.set_page_config(
    page_title="StockWaveJP",
    page_icon="🌊",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ── StockWaveJP SVGロゴ（案②E / 横型ヘッダー） ──
st.markdown("""
<div style="display:flex;align-items:center;gap:14px;padding:10px 0 6px 0;">
  <!-- 日の出＋波アイコン -->
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
  <!-- テキスト部 -->
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
# カラーテーマ CSS定義
# =====================
COLOR_THEMES = {
    "dark": {
        # アプリ全体
        "bg_main":        "#0a0c14",
        "bg_sidebar":     "#0d1020",
        "bg_card":        "#0d1020",
        "border":         "#1a1e30",
        "text_primary":   "#e8eaf0",
        "text_secondary": "#8090a8",
        "text_muted":     "#3a4560",
        "btn_bg":         "#1e2130",
        "btn_border":     "#444",
        "btn_color":      "white",
        "accent":         "#ff4b4b",
        "logo_wave":      "white",
        "label":          "ダーク（黒基調）",
        "label_en":       "Dark",
    },
    "light": {
        "bg_main":        "#f4f5f8",
        "bg_sidebar":     "#ffffff",
        "bg_card":        "#ffffff",
        "border":         "#d8dae0",
        "text_primary":   "#111111",
        "text_secondary": "#444444",
        "text_muted":     "#8899aa",
        "btn_bg":         "#eaecf2",
        "btn_border":     "#cccccc",
        "btn_color":      "#111111",
        "accent":         "#cc1818",
        "logo_wave":      "#222222",
        "label":          "ライト（白基調）",
        "label_en":       "Light",
    },
    "navy": {
        "bg_main":        "#06080f",
        "bg_sidebar":     "#090c1a",
        "bg_card":        "#0b0e1e",
        "border":         "#141828",
        "text_primary":   "#e8eaf0",
        "text_secondary": "#7a8aaa",
        "text_muted":     "#2a3550",
        "btn_bg":         "#10152a",
        "btn_border":     "#252c45",
        "btn_color":      "#c8d0e8",
        "accent":         "#3a7ff0",
        "logo_wave":      "#c8d0e8",
        "label":          "ネイビー（深紺）",
        "label_en":       "Navy",
    },
}

_ct = st.session_state.get("color_theme", "dark")
_c  = COLOR_THEMES.get(_ct, COLOR_THEMES["dark"])

st.markdown(f"""
<style>
/* ── カラーテーマ: {_ct} ── */

/* ── アプリ全体背景 ── */
.stApp {{
    background-color: {_c['bg_main']} !important;
}}

/* ── サイドバー ── */
section[data-testid="stSidebar"] {{
    background-color: {_c['bg_sidebar']} !important;
}}
section[data-testid="stSidebar"] * {{
    color: {_c['text_primary']} !important;
}}

/* ── メインエリアのテキスト全般（Plotly SVG要素は除外） ── */
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span {{
    color: {_c['text_primary']} !important;
}}
p:not(.js-plotly-plot p):not([class*="plotly"] p) {{
    color: {_c['text_primary']};
}}
label:not(.js-plotly-plot label) {{
    color: {_c['text_primary']};
}}
h1, h2, h3, h4, h5, h6 {{
    color: {_c['text_primary']} !important;
}}
/* Streamlit固有のテキスト要素 */
[data-testid="stMarkdownContainer"] * {{
    color: {_c['text_primary']};
}}
[data-testid="stText"] {{
    color: {_c['text_primary']};
}}
[data-testid="stCaptionContainer"] * {{
    color: {_c['text_secondary']} !important;
}}

/* ── メトリクス ── */
[data-testid="metric-container"] * {{
    color: {_c['text_primary']} !important;
}}
/* ── キャプション ── */
.stCaption, .stCaption * {{
    color: {_c['text_secondary']} !important;
}}

/* ── テーブル・データフレーム ── */
[data-testid="stDataFrame"] * {{
    color: {_c['text_primary']} !important;
    background-color: {_c['bg_card']} !important;
}}

/* ── セレクトボックス・入力フォーム ── */
[data-testid="stSelectbox"] *, [data-testid="stMultiSelect"] *,
[data-testid="stTextInput"] *, [data-testid="stRadio"] *,
[data-baseweb="select"] *, [data-baseweb="input"] * {{
    color: {_c['text_primary']} !important;
    background-color: {_c['bg_card']} !important;
}}
[data-baseweb="select"] [role="listbox"] * {{
    background-color: {_c['bg_sidebar']} !important;
    color: {_c['text_primary']} !important;
}}

/* ── expander ── */
[data-testid="stExpander"] {{
    background-color: {_c['bg_card']} !important;
    border: 1px solid {_c['border']} !important;
}}
[data-testid="stExpander"] * {{
    color: {_c['text_primary']} !important;
}}

/* ── info / warning / error ── */
[data-testid="stAlert"] * {{
    color: {_c['text_primary']} !important;
}}

/* ── ボタン ── */
div.stButton > button {{
    width: 100%; height: 2.5em; font-size: 0.95em;
    background-color: {_c['btn_bg']} !important;
    border: 1px solid {_c['btn_border']} !important;
    color: {_c['btn_color']} !important;
}}
div.stButton > button:hover {{
    background-color: {_c['accent']} !important;
    border-color: {_c['accent']} !important;
    color: white !important;
}}
div[data-testid="column"] div.stButton > button {{
    background-color: {_c['btn_bg']} !important;
    border: 1px solid {_c['btn_border']} !important;
    color: {_c['btn_color']} !important;
}}
div[data-testid="column"] div.stButton > button:hover {{
    background-color: {_c['accent']} !important;
    border-color: {_c['accent']} !important;
    color: white !important;
}}

/* ── Plotlyチャート ── */
.stPlotlyChart {{ overflow-x: auto; }}

/* ── レスポンシブ ── */
@media (max-width: 640px) {{
    h1 {{ font-size: 1.4em !important; }}
    h2 {{ font-size: 1.1em !important; }}
}}
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
# 設定タブ用
if "app_language" not in st.session_state:
    st.session_state["app_language"] = "ja"          # "ja" or "en"
if "color_theme" not in st.session_state:
    st.session_state["color_theme"] = "dark"         # "dark" / "light" / "navy"

# =====================
# テーマ・銘柄データ
# =====================
DEFAULT_THEMES = {
    "半導体": {
        "東京エレクトロン":"8035.T","アドバンテスト":"6857.T","ルネサス":"6723.T",
        "ディスコ":"6146.T","SUMCO":"3436.T","レーザーテック":"6920.T",
        "ソシオネクスト":"6526.T","マイクロニクス":"6871.T","フェローテック":"6890.T",
        "東京精密":"7729.T","ウシオ電機":"6925.T","リバーエレテック":"6666.T",
    },
    "AI・クラウド": {
        "富士通":"6702.T","NEC":"6701.T","さくらインターネット":"3778.T",
        "日立製作所":"6501.T","オービック":"4684.T","GMOインターネット":"9449.T",
        "BIPROGY":"8056.T","TIS":"3626.T","野村総合研究所":"4307.T",
        "SCSK":"9719.T","伊藤忠テクノソリューションズ":"4739.T","日鉄ソリューションズ":"2327.T",
    },
    "EV・電気自動車": {
        "トヨタ":"7203.T","パナソニック":"6752.T","住友電気工業":"5802.T",
        "デンソー":"6902.T","日産自動車":"7201.T","本田技研工業":"7267.T",
        "村田製作所":"6981.T","TDK":"6762.T","古河電気工業":"5801.T",
        "三菱自動車":"7211.T","マツダ":"7261.T","住友電装":"5802.T",
    },
    "ゲーム・エンタメ": {
        "任天堂":"7974.T","ソニー":"6758.T","カプコン":"9697.T",
        "バンダイナムコ":"7832.T","スクウェア・エニックス":"9684.T",
        "コナミ":"9766.T","セガサミー":"6460.T","DeNA":"2432.T","ネクソン":"3659.T",
        "コーエーテクモ":"3635.T","アカツキ":"3932.T","グリー":"3632.T",
    },
    "銀行・金融": {
        "三菱UFJ":"8306.T","三井住友":"8316.T","みずほ":"8411.T",
        "りそな":"8308.T","ゆうちょ銀行":"7182.T","野村HD":"8604.T",
        "大和証券グループ":"8601.T","松井証券":"8628.T","auカブコム証券":"8703.T",
    },
    "地方銀行": {
        "静岡銀行":"8355.T","コンコルディア":"7186.T","ふくおかFG":"8354.T",
        "北海道銀行":"8179.T","七十七銀行":"8341.T","広島銀行":"8379.T",
        "伊予銀行":"8385.T","山口FG":"8418.T","東邦銀行":"8346.T",
        "滋賀銀行":"8366.T","琉球銀行":"8399.T",
    },
    "保険": {
        "東京海上HD":"8766.T","MS&AD":"8725.T","第一生命":"8750.T",
        "SOMPOホールディングス":"8630.T","かんぽ生命":"7181.T",
        "T&Dホールディングス":"8795.T",
    },
    "不動産": {
        "三井不動産":"8801.T","住友不動産":"8830.T","東急不動産HD":"3289.T",
        "三菱地所":"8802.T","野村不動産HD":"3231.T","ヒューリック":"3003.T",
        "大東建託":"1878.T","レオパレス21":"8848.T","日本エスリード":"8877.T",
        "Open House":"3288.T",
    },
    "医薬品・バイオ": {
        "武田薬品":"4502.T","アステラス製薬":"4503.T","第一三共":"4568.T",
        "中外製薬":"4519.T","大塚HD":"4578.T","エーザイ":"4523.T",
        "小野薬品":"4528.T","塩野義製薬":"4507.T","参天製薬":"4536.T",
        "久光製薬":"4530.T","ロート製薬":"4527.T",
    },
    "ヘルスケア・介護": {
        "エムスリー":"2413.T","メドレー":"4480.T","ケアネット":"2150.T",
        "ツムラ":"4540.T","テルモ":"4543.T","シスメックス":"6869.T",
        "オリンパス":"7733.T","ニプロ":"8086.T","フクダ電子":"6960.T",
    },
    "食品・飲料": {
        "味の素":"2802.T","キリンHD":"2503.T","日清食品HD":"2897.T",
        "明治HD":"2269.T","サントリー食品":"2587.T","日本ハム":"2282.T",
        "カゴメ":"2811.T","ニッスイ":"1332.T","アサヒグループHD":"2502.T",
        "山崎製パン":"2212.T","江崎グリコ":"2206.T",
    },
    "小売・EC": {
        "ファーストリテイリング":"9983.T","セブン&アイ":"3382.T","MonotaRO":"3064.T",
        "イオン":"8267.T","ニトリHD":"9843.T","Zホールディングス":"4689.T",
        "ウエルシアHD":"3141.T","ドン・キホーテ（PPIH）":"7532.T",
        "マツキヨコクミンHD":"3088.T","スギHD":"7649.T",
    },
    "通信": {
        "NTT":"9432.T","ソフトバンク":"9434.T","KDDI":"9433.T",
        "楽天グループ":"4755.T","インターネットイニシアティブ":"3774.T",
        "オプテージ（関西電力子会社）":"9503.T","JCOM":"4547.T",
    },
    "鉄鋼・素材": {
        "日本製鉄":"5401.T","JFEホールディングス":"5411.T","神戸製鋼所":"5406.T",
        "大和工業":"5444.T","東京製鐵":"5423.T","日本軽金属HD":"5703.T",
        "東邦チタニウム":"5727.T","大阪チタニウム":"5726.T",
    },
    "化学": {
        "信越化学工業":"4063.T","東レ":"3402.T","住友化学":"4005.T",
        "旭化成":"3407.T","三菱ケミカルグループ":"4188.T","花王":"4452.T",
        "富士フイルムHD":"4901.T","クレハ":"4023.T","カネカ":"4118.T",
        "日東電工":"6988.T",
    },
    "建設・インフラ": {
        "大林組":"1802.T","鹿島建設":"1812.T","大成建設":"1801.T",
        "清水建設":"1803.T","積水ハウス":"1928.T","大和ハウス工業":"1925.T",
        "長谷工コーポレーション":"1808.T","前田建設工業":"1824.T",
        "西松建設":"1820.T",
    },
    "輸送・物流": {
        "日本郵船":"9101.T","商船三井":"9104.T","ヤマトHD":"9064.T",
        "川崎汽船":"9107.T","センコーグループ":"9069.T","日本通運":"9062.T",
        "SGホールディングス":"9143.T","近鉄エクスプレス":"9375.T",
    },
    "防衛・航空宇宙": {
        "三菱重工業":"7011.T","川崎重工業":"7012.T","IHI":"7013.T",
        "三菱電機":"6503.T","豊和工業":"6203.T","日本航空電子工業":"6807.T",
        "東京計器":"7721.T","NEC":"6701.T","富士通":"6702.T",
    },
    "フィンテック": {
        "マネックスグループ":"8698.T","SBIホールディングス":"8473.T",
        "GMOフィナンシャルHD":"7177.T","メルカリ":"4385.T",
        "インフォマート":"2492.T","オリエントコーポレーション":"8585.T",
        "GMOペイメントゲートウェイ":"3769.T","アイフル":"8515.T",
    },
    "再生可能エネルギー": {
        "レノバ":"9519.T","ウエストHD":"1407.T",
        "東京電力HD":"9501.T","関西電力":"9503.T","中部電力":"9502.T",
        "出光興産":"5019.T","ENEOS HD":"5020.T","北陸電力":"9505.T",
        "Jパワー":"9513.T",
    },
    "ロボット・自動化": {
        "ファナック":"6954.T","安川電機":"6506.T","キーエンス":"6861.T",
        "不二越":"6474.T","三菱電機":"6503.T","オムロン":"6645.T",
        "川崎重工業":"7012.T","デンソー":"6902.T","THK":"6481.T",
    },
    "レアアース・資源": {
        "住友金属鉱山":"5713.T","三井物産":"8031.T","三菱商事":"8058.T",
        "丸紅":"8002.T","DOWAホールディングス":"5714.T","太平洋金属":"5441.T",
        "伊藤忠商事":"8001.T","住友商事":"8053.T",
    },
    "サイバーセキュリティ": {
        "トレンドマイクロ":"4704.T","サイバーセキュリティクラウド":"4493.T",
        "デジタルアーツ":"2326.T","FFRIセキュリティ":"3692.T",
        "ソリトンシステムズ":"3040.T","野村総合研究所":"4307.T",
        "セキュアワークス":"なし","Macnica Holdings":"3132.T",
    },
    "ドローン・空飛ぶ車": {
        "ACSLエアロスペース":"6232.T","ヤマハ発動機":"7272.T",
        "川崎重工業":"7012.T","NTT":"9432.T","富士通":"6702.T",
        "セキド":"9878.T","テラ":"2758.T",
    },
    "造船": {
        "三菱重工業":"7011.T","川崎重工業":"7012.T",
        "住友重機械工業":"6302.T","名村造船所":"7014.T","内海造船":"7018.T",
        "ジャパンマリンユナイテッド（JMU）":"7014.T","三井E&S":"7003.T",
    },
    # === 新規追加テーマ ===
    "観光・ホテル・レジャー": {
        "オリエンタルランド":"4661.T","東急":"9005.T","近鉄グループHD":"9041.T",
        "リクルートHD":"6098.T","楽天グループ":"4755.T","HISホールディングス":"9603.T",
        "星野リゾートReit":"3287.T","藤田観光":"9722.T","JAL":"9201.T","ANA":"9202.T",
    },
    "農業・フードテック": {
        "クボタ":"6326.T","ヤンマーHD":"6255.T","井関農機":"6310.T",
        "味の素":"2802.T","明治HD":"2269.T","カゴメ":"2811.T",
        "オイシックス・ラ・大地":"3182.T","ファーマフーズ":"2929.T",
    },
    "教育・HR・人材": {
        "ベネッセHD":"9783.T","リクルートHD":"6098.T","パーソルHD":"2181.T",
        "リンクアンドモチベーション":"2170.T","エン・ジャパン":"4849.T",
        "Schoo":"なし","マイナビ（非上場）":"なし","ソウルドアウト":"7034.T",
    },
    "脱炭素・ESG": {
        "ENEOS HD":"5020.T","東レ":"3402.T","旭化成":"3407.T",
        "積水ハウス":"1928.T","パナソニック":"6752.T","リコー":"7752.T",
        "コニカミノルタ":"4902.T","大王製紙":"3880.T",
    },
    "宇宙・衛星": {
        "三菱重工業":"7011.T","IHI":"7013.T","NEC":"6701.T",
        "富士通":"6702.T","NTT":"9432.T","KDDI":"9433.T",
        "スカパーJSATHD":"9412.T","東京エレクトロン":"8035.T",
    },
}

# 「なし」ティッカーを除外
DEFAULT_THEMES = {
    theme: {k: v for k, v in stocks.items() if v != "なし"}
    for theme, stocks in DEFAULT_THEMES.items()
}

# 市場分類データ
# 日経225: 全225銘柄
# TOPIX100: 時価総額上位・組み入れ比率の高い主要銘柄
MARKET_SEGMENTS = {
    # ─────────────────────────────────────
    # 日経225 全225銘柄（2025年3月時点）
    # ─────────────────────────────────────
    "日経225（水産・農林・建設・食品・繊維）": {
        "日本水産":"1332.T",
        "大林組":"1802.T","清水建設":"1803.T","鹿島建設":"1812.T",
        "大成建設":"1801.T","長谷工コーポレーション":"1808.T",
        "大和ハウス工業":"1925.T","積水ハウス":"1928.T",
        "日清食品HD":"2897.T","味の素":"2802.T","明治HD":"2269.T",
        "キリンHD":"2503.T","アサヒグループHD":"2502.T","サントリー食品":"2587.T",
        "日本ハム":"2282.T","山崎製パン":"2212.T","江崎グリコ":"2206.T",
        "東レ":"3402.T","帝人":"3401.T",
    },
    "日経225（化学・医薬品・石油・ゴム・ガラス）": {
        "信越化学工業":"4063.T","住友化学":"4005.T","旭化成":"3407.T",
        "三菱ケミカルG":"4188.T","花王":"4452.T","富士フイルムHD":"4901.T",
        "日東電工":"6988.T","クレハ":"4023.T","カネカ":"4118.T",
        "武田薬品工業":"4502.T","アステラス製薬":"4503.T","第一三共":"4568.T",
        "中外製薬":"4519.T","エーザイ":"4523.T","大塚HD":"4578.T",
        "塩野義製薬":"4507.T","小野薬品工業":"4528.T","参天製薬":"4536.T",
        "ENEOS HD":"5020.T","出光興産":"5019.T",
        "ブリヂストン":"5108.T","住友ゴム工業":"5110.T",
        "AGC":"5201.T","日本板硝子":"5202.T","日本碍子":"5333.T",
    },
    "日経225（鉄鋼・非鉄・金属・機械）": {
        "日本製鉄":"5401.T","JFE HD":"5411.T","神戸製鋼所":"5406.T",
        "住友金属鉱山":"5713.T","三菱マテリアル":"5711.T",
        "DOWAホールディングス":"5714.T","古河電気工業":"5801.T",
        "住友電気工業":"5802.T","フジクラ":"5803.T",
        "クボタ":"6326.T","コマツ":"6301.T","SMC":"6273.T",
        "ダイキン工業":"6367.T","オークマ":"6103.T","アマダ":"6113.T",
        "日立建機":"6305.T","住友重機械工業":"6302.T","荏原製作所":"6361.T",
        "三菱重工業":"7011.T","川崎重工業":"7012.T","IHI":"7013.T",
        "ミネベアミツミ":"6479.T","日本精工":"6471.T","NTN":"6472.T",
    },
    "日経225（電気機器・精密機器）": {
        "日立製作所":"6501.T","三菱電機":"6503.T","富士電機":"6504.T",
        "安川電機":"6506.T","NEC":"6701.T","富士通":"6702.T",
        "ソニーグループ":"6758.T","パナソニックHD":"6752.T","シャープ":"6753.T",
        "TDK":"6762.T","京セラ":"6971.T","村田製作所":"6981.T",
        "オムロン":"6645.T","キーエンス":"6861.T","ファナック":"6954.T",
        "アドバンテスト":"6857.T","東京エレクトロン":"8035.T","ルネサスエレクトロニクス":"6723.T",
        "レーザーテック":"6920.T","ディスコ":"6146.T","ローム":"6963.T",
        "イビデン":"4062.T","日本電気硝子":"5214.T",
        "オリンパス":"7733.T","HOYA":"7741.T","テルモ":"4543.T",
        "シスメックス":"6869.T","ニコン":"7731.T","キヤノン":"7751.T",
    },
    "日経225（輸送用機器・その他製品・電力ガス）": {
        "トヨタ自動車":"7203.T","ホンダ":"7267.T","日産自動車":"7201.T",
        "マツダ":"7261.T","三菱自動車":"7211.T","スズキ":"7269.T",
        "デンソー":"6902.T","アイシン":"7259.T","ヤマハ発動機":"7272.T",
        "任天堂":"7974.T","バンダイナムコHD":"7832.T","コナミグループ":"9766.T",
        "セガサミーHD":"6460.T","リコー":"7752.T","コニカミノルタ":"4902.T",
        "凸版印刷":"7911.T","大日本印刷":"7912.T","ヤマハ":"7951.T",
        "東京電力HD":"9501.T","関西電力":"9503.T","中部電力":"9502.T",
        "九州電力":"9508.T","東京ガス":"9531.T","大阪ガス":"9532.T",
    },
    "日経225（陸運・海運・空運・倉運・情通）": {
        "JR東日本":"9020.T","JR東海":"9022.T","JR西日本":"9021.T",
        "東急":"9005.T","近鉄グループHD":"9041.T","小田急電鉄":"9007.T",
        "京王電鉄":"9008.T","西日本旅客鉄道":"9021.T",
        "ヤマトHD":"9064.T","SGホールディングス":"9143.T",
        "日本郵船":"9101.T","商船三井":"9104.T","川崎汽船":"9107.T",
        "JAL":"9201.T","ANA HD":"9202.T",
        "日本通運":"9062.T","近鉄エクスプレス":"9375.T",
        "NTT":"9432.T","KDDI":"9433.T","ソフトバンク":"9434.T",
    },
    "日経225（卸売・小売・銀行・証券・保険・金融・不動産・サービス）": {
        "三菱商事":"8058.T","三井物産":"8031.T","伊藤忠商事":"8001.T",
        "住友商事":"8053.T","丸紅":"8002.T","豊田通商":"8015.T",
        "双日":"2768.T",
        "ファーストリテイリング":"9983.T","セブン&アイHD":"3382.T",
        "イオン":"8267.T","ニトリHD":"9843.T","良品計画":"7453.T",
        "ZOZO":"3092.T","パン・パシフィック":"7532.T",
        "三菱UFJ FG":"8306.T","三井住友FG":"8316.T","みずほFG":"8411.T",
        "りそなHD":"8308.T",
        "野村HD":"8604.T","大和証券G":"8601.T","日本取引所G":"8697.T",
        "東京海上HD":"8766.T","MS&AD保険G":"8725.T","SOMPO HD":"8630.T",
        "第一生命HD":"8750.T","T&D HD":"8795.T",
        "オリックス":"8591.T",
        "三井不動産":"8801.T","三菱地所":"8802.T",
        "リクルートHD":"6098.T","オリエンタルランド":"4661.T",
        "エムスリー":"2413.T","野村総合研究所":"4307.T",
    },
    # ─────────────────────────────────────
    # TOPIX100（時価総額上位・組み入れ比率高い主要銘柄）
    # Core30 + Large70 から時価総額上位を中心に選定
    # ─────────────────────────────────────
    "TOPIX100（Core30：時価総額最上位）": {
        "トヨタ自動車":"7203.T","ソニーグループ":"6758.T","三菱UFJ FG":"8306.T",
        "キーエンス":"6861.T","東京エレクトロン":"8035.T","信越化学工業":"4063.T",
        "ファーストリテイリング":"9983.T","リクルートHD":"6098.T","三菱商事":"8058.T",
        "三井物産":"8031.T","KDDI":"9433.T","NTT":"9432.T",
        "ソフトバンクG":"9984.T","任天堂":"7974.T","デンソー":"6902.T",
        "ダイキン工業":"6367.T","日立製作所":"6501.T","中外製薬":"4519.T",
        "第一三共":"4568.T","ホンダ":"7267.T","伊藤忠商事":"8001.T",
        "三井住友FG":"8316.T","みずほFG":"8411.T","東京海上HD":"8766.T",
        "武田薬品工業":"4502.T","村田製作所":"6981.T","ファナック":"6954.T",
        "富士通":"6702.T","花王":"4452.T","オリックス":"8591.T",
    },
    "TOPIX100（Large70：時価総額上位大型株）": {
        "パナソニックHD":"6752.T","日本電信電話":"9432.T","住友商事":"8053.T",
        "丸紅":"8002.T","豊田通商":"8015.T","三菱電機":"6503.T",
        "アドバンテスト":"6857.T","レーザーテック":"6920.T","ルネサスエレクトロニクス":"6723.T",
        "TDK":"6762.T","富士フイルムHD":"4901.T","日本製鉄":"5401.T",
        "住友金属鉱山":"5713.T","三菱重工業":"7011.T","川崎重工業":"7012.T",
        "IHI":"7013.T","コマツ":"6301.T","クボタ":"6326.T",
        "ブリヂストン":"5108.T","旭化成":"3407.T","三菱ケミカルG":"4188.T",
        "ENEOS HD":"5020.T","大塚HD":"4578.T","アステラス製薬":"4503.T",
        "エーザイ":"4523.T","塩野義製薬":"4507.T","テルモ":"4543.T",
        "HOYA":"7741.T","京セラ":"6971.T","オムロン":"6645.T",
        "ニデック":"6594.T","SMC":"6273.T","ヤマハ発動機":"7272.T",
        "三井不動産":"8801.T","三菱地所":"8802.T","日本取引所G":"8697.T",
        "野村HD":"8604.T","MS&AD保険G":"8725.T","SOMPO HD":"8630.T",
        "第一生命HD":"8750.T","JR東日本":"9020.T","JR東海":"9022.T",
        "日本郵船":"9101.T","商船三井":"9104.T","川崎汽船":"9107.T",
        "セブン&アイHD":"3382.T","イオン":"8267.T","ニトリHD":"9843.T",
        "日立建機":"6305.T","三菱UFJ信託":"8306.T",
        "大和証券G":"8601.T","りそなHD":"8308.T",
        "住友電気工業":"5802.T","古河電気工業":"5801.T",
        "AGC":"5201.T","日本碍子":"5333.T",
        "オリエンタルランド":"4661.T","リクルートHD":"6098.T",
        "エムスリー":"2413.T","野村総合研究所":"4307.T",
        "ソフトバンク":"9434.T","ZOZO":"3092.T",
        "バンダイナムコHD":"7832.T","コナミグループ":"9766.T",
        "キヤノン":"7751.T","ニコン":"7731.T",
        "JAL":"9201.T","ANA HD":"9202.T",
    },
    # ─────────────────────────────────────
    # スタンダード・グロース注目銘柄
    # ─────────────────────────────────────
    "スタンダード注目銘柄": {
        "静岡銀行":"8355.T","広島銀行":"8379.T","七十七銀行":"8341.T",
        "東邦銀行":"8346.T","滋賀銀行":"8366.T",
        "名村造船所":"7014.T","内海造船":"7018.T",
        "太平洋金属":"5441.T","東京製鐵":"5423.T","大和工業":"5444.T",
        "リリカラ":"9827.T","トーセイ":"8923.T",
    },
    "グロース注目銘柄": {
        "さくらインターネット":"3778.T","メルカリ":"4385.T",
        "サイバーセキュリティクラウド":"4493.T","FFRIセキュリティ":"3692.T",
        "メドレー":"4480.T","ケアネット":"2150.T","レノバ":"9519.T",
        "ACSL":"6232.T","Appier Group":"4180.T","弁護士ドットコム":"6027.T",
        "freee":"4478.T","マネーフォワード":"3994.T",
    },
}

# カスタムテーマとデフォルトテーマを結合
def get_all_themes():
    combined = dict(DEFAULT_THEMES)
    combined.update(st.session_state["custom_themes"])
    return combined

PLOT_CONFIG = {"displayModeBar": False, "staticPlot": True}

# 期間ボタン設定
# 期間のyfinance値マッピング（言語に依存しない内部マスター）
_PERIOD_YFINANCE = ["1d", "5d", "1mo", "3mo", "6mo", "1y", "18mo", "2y"]
_PERIOD_I18N_KEYS = [
    "period_1d", "period_1w", "period_1m", "period_3m",
    "period_6m", "period_1y", "period_18m", "period_2y",
]

def get_period_options() -> dict:
    """現在の言語設定に従って期間ラベル→yfinance期間文字列の辞書を返す。
    t()はI18N定義後に呼ばれる前提で、period_buttonsや各ページから呼ぶこと。"""
    lang = st.session_state.get("app_language", "ja")
    _labels_ja = ["1日","1週間","1ヶ月","3ヶ月","6ヶ月","1年","1年半","2年"]
    _labels_en = ["1D","1W","1M","3M","6M","1Y","18M","2Y"]
    labels = _labels_en if lang == "en" else _labels_ja
    return dict(zip(labels, _PERIOD_YFINANCE))

# 後方互換用（ページ描画時に動的に生成されるため、ここでは空dict）
PERIOD_OPTIONS = {}  # period_buttons()内で get_period_options() を呼んで上書きされる

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
def _get_ttl() -> int:
    """
    市場時間（平日9:00〜15:35 JST）は3分キャッシュ→ほぼリアルタイム。
    時間外・土日は1時間キャッシュでAPI節約。
    """
    import datetime as _dt
    now_jst = _dt.datetime.utcnow() + _dt.timedelta(hours=9)
    if now_jst.weekday() >= 5:          # 土日
        return 3600
    t = now_jst.time()
    market_open  = _dt.time(9,  0)
    market_close = _dt.time(15, 35)
    if market_open <= t <= market_close:
        return 180                       # 市場時間中：3分
    return 1800                          # 時間外：30分

@st.cache_data(ttl=_get_ttl())
def fetch_stock_data(ticker: str, period: str = "2y") -> pd.DataFrame:
    try:
        df = yf.Ticker(ticker).history(period=period, auto_adjust=True)
        return df
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

def _fetch_single_stock(args):
    """1銘柄のデータを取得・計算（並列実行用）"""
    stock_name, ticker, period = args
    try:
        df = fetch_stock_data(ticker, "2y")
        if len(df) < 2: return None
        target_df = get_target_df(df, period)
        if len(target_df) < 2: return None
        change = calc_change(target_df)
        if change is None: return None

        half = max(len(target_df)//2, 1)
        rv = target_df["Volume"].tail(half).mean()
        pv = target_df["Volume"].head(half).mean()
        day_change = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None
        rsi_val = round(calc_rsi(df["Close"]).iloc[-1], 1) if len(df)>=15 else None
        sharpe = calc_sharpe(target_df["Close"])
        w52_high = round(df["High"].tail(252).max(), 0)
        w52_low  = round(df["Low"].tail(252).min(), 0)
        last_price = round(df["Close"].iloc[-1], 0)
        trade_value = int(rv * last_price)
        return (stock_name, change, rv, pv, {
            "change": change, "day_change": day_change,
            "volume_change": round((rv-pv)/pv*100,1) if pv>0 else 0,
            "ticker": ticker, "rsi": rsi_val, "sharpe": sharpe,
            "52w_high": w52_high, "52w_low": w52_low,
            "price": last_price, "volume": int(rv),
            "trade_value": trade_value,
        })
    except:
        return None

@st.cache_data(ttl=_get_ttl())
def fetch_all_theme_data(period: str, theme_keys: tuple) -> tuple:
    _cache_created = (_dt2.datetime.utcnow() + _dt2.timedelta(hours=9)).strftime("%H:%M")
    themes = get_all_themes()
    theme_results = []
    theme_details = {}

    for theme_name in theme_keys:
        stocks = themes.get(theme_name, {})
        changes, details = [], {}
        total_vol = prev_total_vol = 0

        # 銘柄ごとの取得を並列実行（最大10スレッド）
        args_list = [(sn, ticker, period) for sn, ticker in stocks.items()]
        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = {executor.submit(_fetch_single_stock, a): a for a in args_list}
            for future in as_completed(futures):
                result = future.result()
                if result is None: continue
                stock_name, change, rv, pv, detail = result
                changes.append(change)
                total_vol += rv
                prev_total_vol += pv
                details[stock_name] = detail

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
    return theme_results, theme_details, _cache_created

# =====================
# =====================
# テーマ騰落推移（yfinance日次データ）
# =====================
@st.cache_data(ttl=1800)
def fetch_theme_trend(theme_keys, period="1y"):
    """
    yfinanceから日次終値を取得し、各テーマの日次平均騰落率（基準日=period開始日）を返す。
    戻り値: {theme_name: pd.Series(index=date, values=cumulative_change%)}
    """
    _themes = get_all_themes()

    def _fetch_ticker_daily(ticker):
        try:
            df = yf.Ticker(ticker).history(period=period, interval="1d", auto_adjust=True)
            if df is None or len(df) < 2:
                return None
            df.index = df.index.tz_localize(None)
            return df["Close"]
        except:
            return None

    trend_data = {}
    for theme_name in theme_keys:
        stocks = _themes.get(theme_name, {})
        if not stocks:
            continue
        # 並列取得
        series_list = []
        with ThreadPoolExecutor(max_workers=8) as ex:
            futs = {ex.submit(_fetch_ticker_daily, t): t for t in stocks.values()}
            for fut in as_completed(futs):
                s = fut.result()
                if s is not None and len(s) > 1:
                    # 最初の値を基準(=0%)として累積騰落率に変換
                    base = s.iloc[0]
                    if base and base != 0:
                        series_list.append((s / base - 1) * 100)
        if not series_list:
            continue
        # 全銘柄を日次で平均（日付を共通インデックスに揃える）
        combined = pd.concat(series_list, axis=1)
        trend_data[theme_name] = combined.mean(axis=1).round(2)

    return trend_data

# =====================
# グラフ関数
# =====================
def make_bar_chart(labels, values, colors, height=None, left_margin=None, rank_labels=None):
    """
    ランキングバーチャート。
    rank_labels: 順位番号リスト（文字列 or 数値）。
                 指定時は順位をannotationsで色付き表示（1位=金・2位=銀・3位=銅・4位以下=グレー）
                 Y軸ticktextはテーマ名のみ。
    """
    if not values or not labels:
        fig = go.Figure()
        fig.update_layout(height=150, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        return fig

    n = len(values)
    h = height if height else max(200, n * 34)

    # 順位色の定義
    RANK_COLORS = {
        1: "#FFD700",   # 金
        2: "#C0C0C0",   # 銀
        3: "#CD7F32",   # 銅
    }
    RANK_DEFAULT = "#7a8aaa"  # 4位以下

    # left_marginはテーマ名の最大文字数で計算
    # rank_labelsがある場合は「XX位  」の幅（最大5文字程度）を加算
    max_label_len = max(len(str(l)) for l in labels)
    rank_prefix_len = 5 if rank_labels else 0  # 「10位  」≒5文字分
    lm = left_margin if left_margin else max(140, (max_label_len + rank_prefix_len) * 11 + 20)
    lm = min(lm, 280)

    min_v = min(values)
    max_v = max(values)
    text_positions = ["inside" if abs(v) > 4 else "outside" for v in values]

    fig = go.Figure(go.Bar(
        y=list(range(n)),
        x=values,
        orientation="h",
        marker_color=colors,
        text=[f" {v:+.2f}%" for v in values],
        textposition=text_positions,
        textfont=dict(color="white", size=11),
        insidetextanchor="middle",
        cliponaxis=False,
    ))

    # Y軸はテーマ名のみ（順位はannotationsで左に別描画）
    annotations = []
    if rank_labels:
        for i, r in enumerate(rank_labels):
            rank_num = int(r)
            rank_color = RANK_COLORS.get(rank_num, RANK_DEFAULT)
            annotations.append(dict(
                x=-lm,           # xref="x domain"ではなくpixel offsetを使う
                y=i,
                xref="paper",
                yref="y",
                text=f"<b>{rank_num}位</b>",
                showarrow=False,
                xanchor="left",
                yanchor="middle",
                font=dict(color=rank_color, size=11, family="Arial"),
                xshift=0,
            ))

    fig.update_layout(
        xaxis=dict(
            title="騰落率（%）", ticksuffix="%",
            zeroline=True, zerolinecolor="#555", zerolinewidth=1,
            range=[min_v * 1.3 if min_v < 0 else -0.5,
                   max_v * 1.3 if max_v > 0 else 0.5],
            tickfont=dict(size=10), title_font=dict(size=11),
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(n)),
            ticktext=list(labels),   # テーマ名のみ
            autorange="reversed",
            tickfont=dict(size=11),
        ),
        annotations=annotations,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=11),
        height=h, bargap=0.2,
        margin=dict(t=8, b=36, l=lm, r=60),
    )
    return fig

def make_price_chart(df, display_df, chart_type="ローソク足", show_ma=True):
    """株価チャート：目盛りを月単位に設定"""
    fig = go.Figure()
    if chart_type == "ローソク足":
        fig.add_trace(go.Candlestick(
            x=display_df.index, open=display_df["Open"], high=display_df["High"],
            low=display_df["Low"], close=display_df["Close"],
            increasing_line_color="#ff4b4b", decreasing_line_color="#39d353", name=t("legend_price"),
        ))
    else:
        fig.add_trace(go.Scatter(
            x=display_df.index, y=display_df["Close"], mode="lines",
            line=dict(color="#ff4b4b", width=2),
            fill="tozeroy", fillcolor="rgba(255,75,75,0.1)", name=t("legend_close"),
        ))
    if show_ma and len(df) >= 25:
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(25).mean(),
                                  mode="lines", line=dict(color="#ffd700", width=1.5, dash="dot"), name=t("legend_ma25")))
    if show_ma and len(df) >= 75:
        fig.add_trace(go.Scatter(x=df.index, y=df["Close"].rolling(75).mean(),
                                  mode="lines", line=dict(color="#4b8bff", width=1.5, dash="dot"), name=t("legend_ma75")))
    fig.update_layout(
        xaxis=dict(
            title=t("xaxis_date"),
            rangeslider=dict(visible=False),
            dtick="M1",           # 1ヶ月ごとの目盛り
            tickformat="%y/%m",   # 例：25/01
            ticklabelmode="period",
            range=[display_df.index[0], display_df.index[-1]],
        ),
        yaxis=dict(title=t("yaxis_price"), tickprefix="¥"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white"), height=400,
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=40, b=40, l=70, r=20),
    )
    return fig

def period_buttons(key_prefix="main"):
    """
    期間選択：PCはボタン横並び、スマホはセレクトボックス1行で表示。
    st.columnsはスマホで縦並びになるため、JavaScript経由の幅判定はできない。
    代わりにselectboxをコンパクトに配置し、全画面を占有しないよう制御。
    """
    st.markdown("""
    <style>
    /* 期間選択セレクトボックスをコンパクトに */
    div[data-testid="stSelectbox"] {
        max-width: 200px !important;
    }
    div[data-testid="stSelectbox"] > div {
        min-height: 2em !important;
    }
    div[data-testid="stSelectbox"] label {
        display: none !important;
    }
    </style>
    """, unsafe_allow_html=True)

    period_opts   = get_period_options()
    period_labels = list(period_opts.keys())
    # selected_periodをyfinance値で保存し、ラベルは動的に変換
    current_val = st.session_state.get("selected_period_val", "1mo")
    # ラベルからcurrent_valに対応するラベルを探す
    val_to_label = {v: k for k, v in period_opts.items()}
    current_label = val_to_label.get(current_val, period_labels[2])  # デフォルト1M

    col_sel, col_cap = st.columns([1, 3])
    with col_sel:
        selected = st.selectbox(
            t("trend_period_label"),
            period_labels,
            index=period_labels.index(current_label) if current_label in period_labels else 2,
            key=f"period_sel_{key_prefix}",
            label_visibility="collapsed",
        )
    with col_cap:
        st.markdown(f"<div style='padding-top:0.5em; font-size:0.9em; color:#aaa;'>📅 {selected}</div>",
                    unsafe_allow_html=True)

    selected_val = period_opts[selected]
    if selected_val != current_val:
        st.session_state["selected_period_val"] = selected_val
        st.session_state["selected_period"] = selected  # 後方互換
        st.rerun()

    return selected_val

# =====================
# 言語辞書（日本語 / 英語）
# =====================
I18N = {
    # ─── ページ名 ───
    "page_theme_list":       {"ja": "📊 テーマ一覧",       "en": "📊 Theme List"},
    "page_momentum":         {"ja": "📡 騰落モメンタム",    "en": "📡 Momentum"},
    "page_fund_flow":        {"ja": "💹 資金フロー",         "en": "💹 Fund Flow"},
    "page_trend":            {"ja": "📈 騰落推移",           "en": "📈 Price Trend"},
    "page_heatmap":          {"ja": "🔥 ヒートマップ",       "en": "🔥 Heatmap"},
    "page_compare":          {"ja": "📉 テーマ比較",         "en": "📉 Theme Compare"},
    "page_macro":            {"ja": "🌍 マクロ比較",         "en": "🌍 Macro"},
    "page_market_rank":      {"ja": "📋 市場別ランキング",   "en": "📋 Market Ranking"},
    "page_theme_detail":     {"ja": "🔍 テーマ別詳細",       "en": "🔍 Theme Detail"},
    "page_favorites":        {"ja": "⭐ お気に入り",          "en": "⭐ Favorites"},
    "page_custom":           {"ja": "🏷️ カスタムテーマ",     "en": "🏷️ Custom Theme"},
    "page_news":             {"ja": "📣 お知らせ",            "en": "📣 News"},
    "page_howto":            {"ja": "📖 使い方・Q&A",        "en": "📖 How to Use"},
    "page_disclaimer":       {"ja": "⚖️ 免責事項",           "en": "⚖️ Disclaimer"},
    "page_settings":         {"ja": "⚙️ 設定",               "en": "⚙️ Settings"},
    # ─── 共通UI ───
    "menu":                  {"ja": "メニュー",               "en": "Menu"},
    "refresh":               {"ja": "🔄 データを最新に更新",  "en": "🔄 Refresh Data"},
    "market_open":           {"ja": "🟢 市場オープン中",      "en": "🟢 Market Open"},
    "market_closed_weekend": {"ja": "🔴 市場閉（土日）",      "en": "🔴 Market Closed (Weekend)"},
    "market_closed_hours":   {"ja": "🟡 市場閉（時間外）",    "en": "🟡 Market Closed (Off-hours)"},
    "update_interval":       {"ja": "🔄 更新頻度：約{}分ごと","en": "🔄 Updates every ~{} min"},
    "current_time":          {"ja": "🕐 現在時刻(JST)：{}",   "en": "🕐 Current time (JST): {}"},
    "fav_count":             {"ja": "⭐ お気に入り：{}銘柄",  "en": "⭐ Favorites: {} stocks"},
    "footer":                {"ja": "© 2026 StockWaveJP　|　本サービスは情報提供のみを目的とします。投資判断はご自身の責任で行ってください。",
                              "en": "© 2026 StockWaveJP  |  For informational purposes only. Not investment advice."},
    "loading":               {"ja": "データ取得中...",         "en": "Loading data..."},
    "loading_daily":         {"ja": "日次データを取得中...（初回は少し時間がかかります）",
                              "en": "Fetching daily data... (may take a moment on first load)"},
    "loading_first":         {"ja": "データを取得中...（初回は時間がかかります）",
                              "en": "Loading data... (first load may take a while)"},
    "csv_download":          {"ja": "📥 CSVダウンロード",      "en": "📥 Download CSV"},
    "csv_download_all":      {"ja": "📥 全テーマCSVダウンロード", "en": "📥 Download All Themes CSV"},
    "no_data":               {"ja": "データを取得できませんでした。しばらく待ってから再度お試しください。",
                              "en": "Could not fetch data. Please try again later."},
    "select_theme_prompt":   {"ja": "テーマを1つ以上選択してください。", "en": "Please select at least one theme."},
    # ─── 期間ラベル ───
    "period_1d":             {"ja": "1日",    "en": "1D"},
    "period_1w":             {"ja": "1週間",  "en": "1W"},
    "period_1m":             {"ja": "1ヶ月",  "en": "1M"},
    "period_3m":             {"ja": "3ヶ月",  "en": "3M"},
    "period_6m":             {"ja": "6ヶ月",  "en": "6M"},
    "period_1y":             {"ja": "1年",    "en": "1Y"},
    "period_18m":            {"ja": "1年半",  "en": "18M"},
    "period_2y":             {"ja": "2年",    "en": "2Y"},
    # ─── テーマ一覧ページ ───
    "theme_list_caption":    {"ja": "テーマ別の騰落率・資金フロー・出来高をランキング形式で表示します。",
                              "en": "Rankings of theme-based returns, fund flow, and volume."},
    "display_count_label":   {"ja": "表示テーマ数",            "en": "Themes to show"},
    "display_count_caption": {"ja": "上位/下位 {}テーマ",      "en": "Top/Bottom {} themes"},
    "display_count_all":     {"ja": "上位/下位 全テーマ",      "en": "All themes"},
    "top_gainers":           {"ja": "🔴 上昇テーマ TOP",       "en": "🔴 Top Gainers"},
    "top_losers":            {"ja": "🟢 下落テーマ TOP",       "en": "🟢 Top Losers"},
    "volume_flow":           {"ja": "💴 出来高フロー",          "en": "💴 Volume Flow"},
    "trade_value_ranking":   {"ja": "💴 テーマ別売買代金",      "en": "💴 Theme Trade Value"},
    "show_more":             {"ja": "▼ 6位以下を表示（残り{}件）", "en": "▼ Show more ({} items)"},
    "show_less":             {"ja": "▲ 閉じる",                "en": "▲ Close"},
    "all_themes_table":      {"ja": "📋 全テーマ一覧",              "en": "📋 All Themes"},
    "rank_col":              {"ja": "順位",                     "en": "Rank"},
    "theme_col":             {"ja": "テーマ",                   "en": "Theme"},
    "change_col":            {"ja": "騰落率",                   "en": "Return"},
    "volume_col":            {"ja": "出来高増減",               "en": "Volume Chg"},
    "trade_val_col":         {"ja": "売買代金",                 "en": "Trade Value"},
    "rank_suffix":           {"ja": "{}位",                     "en": "#{}"},
    # ─── 騰落モメンタムページ ───
    "momentum_caption":      {"ja": "現在の騰落率 ＋ 先週比・先月比の変化で「加速・失速・転換」テーマを一目で把握",
                              "en": "Identify accelerating, decelerating, and reversing themes using current return + weekly/monthly changes."},
    "sort_label":            {"ja": "並び替え",                 "en": "Sort by"},
    "sort_return":           {"ja": "騰落率（降順）",            "en": "Return (Desc)"},
    "sort_weekly":           {"ja": "先週比変化（降順）",         "en": "Weekly Change (Desc)"},
    "sort_monthly":          {"ja": "先月比変化（降順）",         "en": "Monthly Change (Desc)"},
    "filter_state":          {"ja": "状態フィルター（空=全表示）", "en": "State Filter (empty=all)"},
    "state_accel":           {"ja": "🔥加速",                   "en": "🔥Accelerating"},
    "state_up":              {"ja": "↗転換↑",                  "en": "↗Reversing↑"},
    "state_flat":            {"ja": "→横ばい",                  "en": "→Flat"},
    "state_down":            {"ja": "↘転換↓",                  "en": "↘Reversing↓"},
    "state_decel":           {"ja": "❄️失速",                   "en": "❄️Decelerating"},
    "col_theme":             {"ja": "テーマ名",                  "en": "Theme"},
    "col_return":            {"ja": "騰落率(%)",                 "en": "Return(%)"},
    "col_weekly":            {"ja": "先週比(pt)",                "en": "vs.1W(pt)"},
    "col_monthly":           {"ja": "先月比(pt)",                "en": "vs.1M(pt)"},
    "col_state":             {"ja": "状態",                     "en": "State"},
    "momentum_note":         {"ja": "💡 騰落率=選択期間の変化率 / 先週比・先月比=騰落率との差分(ポイント) / 🔥加速=両方↑ / ❄️失速=両方↓",
                              "en": "💡 Return=change over selected period / vs.1W,1M=difference in points / 🔥Accel=both↑ / ❄️Decel=both↓"},
    # ─── 資金フローページ ───
    "fund_flow_title":       {"ja": "💹 テーマ別 資金フロー",   "en": "💹 Theme Fund Flow"},
    "fund_flow_caption":     {"ja": "上昇テーマ vs 下落テーマの騰落幅を比較。どのテーマに資金が集まっているか把握できます。",
                              "en": "Compare gainers vs losers to identify where capital is flowing."},
    "inflow_top":            {"ja": "### 🔥 資金流入テーマ TOP10", "en": "### 🔥 Top Inflow Themes (Top 10)"},
    "outflow_top":           {"ja": "### ❄️ 資金流出テーマ TOP10", "en": "### ❄️ Top Outflow Themes (Top 10)"},
    "all_flow_overview":     {"ja": "**📊 全テーマ 騰落率一覧（資金フロー全景）**",
                              "en": "**📊 All Themes — Full Fund Flow Overview**"},
    # ─── 騰落推移ページ ───
    "trend_title":           {"ja": "📈 テーマ別 騰落率の推移",  "en": "📈 Theme Return Trend"},
    "trend_period_label":    {"ja": "表示期間",                  "en": "Period"},
    "trend_mode_label":      {"ja": "表示モード",                "en": "Display Mode"},
    "trend_mode_top":        {"ja": "🏆 上位5＋ワースト5",       "en": "🏆 Top 5 + Worst 5"},
    "trend_mode_manual":     {"ja": "✅ テーマを手動選択",        "en": "✅ Select Manually"},
    "trend_mode_all":        {"ja": "📊 全テーマ",               "en": "📊 All Themes"},
    "trend_manual_label":    {"ja": "表示テーマを選択",               "en": "Select themes to display"},
    "trend_rank_title":      {"ja": "**📋 テーマ騰落率ランキング（{}）**", "en": "**📋 Theme Return Ranking ({})**"},
    "trend_rank_period":     {"ja": "騰落率（{}）",              "en": "Return ({})"},
    "trend_date_col":        {"ja": "日付",                      "en": "Date"},
    "trend_rate_col":        {"ja": "騰落率(%)",                 "en": "Return(%)"},
    # ─── ヒートマップページ ───
    "heatmap_title":         {"ja": "🔥 テーマ別騰落率 ヒートマップ", "en": "🔥 Theme Return Heatmap"},
    "heatmap_period_label":  {"ja": "表示期間を選択",                 "en": "Select period"},
    # ─── テーマ比較ページ ───
    "compare_title":         {"ja": "📉 テーマ比較",              "en": "📉 Theme Comparison"},
    "compare_caption":       {"ja": "複数テーマの騰落率を同一チャートで比較します。",
                              "en": "Compare returns of multiple themes on the same chart."},
    "compare_select":        {"ja": "比較するテーマを選択（最大10）", "en": "Select themes to compare (max 10)"},
    "compare_period":        {"ja": "比較期間",                       "en": "Comparison period"},
    # ─── マクロ比較ページ ───
    "macro_title":           {"ja": "🌍 マクロ比較",              "en": "🌍 Macro Comparison"},
    "macro_caption":         {"ja": "日本株テーマと主要指数・ETFを比較します。",
                              "en": "Compare Japanese equity themes with major indices and ETFs."},
    # ─── 市場別ランキングページ ───
    "market_rank_title":     {"ja": "📋 市場別ランキング",         "en": "📋 Market Ranking"},
    "market_rank_caption":   {"ja": "日経225・TOPIX100・テーマ別の騰落率ランキングです。",
                              "en": "Return rankings by Nikkei 225, TOPIX100, and themes."},
    # ─── テーマ別詳細ページ ───
    "theme_detail_title":    {"ja": "🔍 テーマ別詳細",             "en": "🔍 Theme Detail"},
    "theme_detail_select":   {"ja": "テーマを選択",                   "en": "Select a theme"},
    "theme_detail_period":   {"ja": "期間",                           "en": "Period"},
    "stock_name_col":        {"ja": "銘柄名",                     "en": "Stock Name"},
    "ticker_col":            {"ja": "コード",                     "en": "Ticker"},
    "change_pct_col":        {"ja": "騰落率(%)",                  "en": "Return(%)"},
    "volume_chg_col":        {"ja": "出来高増減(%)",              "en": "Volume Chg(%)"},
    "trade_value_col":       {"ja": "売買代金(万円)",             "en": "Trade Val(¥10k)"},
    # ─── お気に入りページ ───
    "fav_title":             {"ja": "⭐ お気に入り銘柄",           "en": "⭐ Favorite Stocks"},
    "fav_empty":             {"ja": "お気に入りに銘柄が登録されていません。各ページから ⭐ ボタンで追加できます。",
                              "en": "No favorite stocks yet. Add stocks using the ⭐ button on each page."},
    "fav_remove":            {"ja": "削除",                           "en": "Remove"},
    "fav_period":            {"ja": "表示期間",                   "en": "Period"},
    # ─── カスタムテーマページ ───
    "custom_title":          {"ja": "🏷️ カスタムテーマ",          "en": "🏷️ Custom Themes"},
    "custom_caption":        {"ja": "自分だけのテーマを作成・管理できます。",
                              "en": "Create and manage your own custom themes."},
    "custom_new_name":       {"ja": "新しいテーマ名",                 "en": "New theme name"},
    "custom_create":         {"ja": "テーマを作成",                   "en": "Create Theme"},
    "custom_add_stock":      {"ja": "銘柄を追加（証券コードまたは銘柄名）", "en": "Add stock (ticker or name)"},
    "custom_add_btn":        {"ja": "追加",                       "en": "Add"},
    "custom_delete":         {"ja": "テーマを削除",                   "en": "Delete Theme"},
    "custom_save":           {"ja": "保存",                       "en": "Save"},
    # ─── グラフ軸ラベル ───
    "yaxis_return":          {"ja": "騰落率（%）",                "en": "Return (%)"},
    "yaxis_price":           {"ja": "株価（円）",                 "en": "Price (JPY)"},
    "xaxis_date":            {"ja": "日付",                       "en": "Date"},
    "legend_price":          {"ja": "株価",                       "en": "Price"},
    "legend_close":          {"ja": "終値",                       "en": "Close"},
    "legend_ma25":           {"ja": "25日MA",                    "en": "25D MA"},
    "legend_ma75":           {"ja": "75日MA",                    "en": "75D MA"},
    # ─── テーマ名英訳 ───
    "theme_半導体":                          {"ja": "半導体",                    "en": "Semiconductors"},
    "theme_AI・クラウド":                    {"ja": "AI・クラウド",              "en": "AI & Cloud"},
    "theme_EV・電気自動車":                  {"ja": "EV・電気自動車",            "en": "EV / Electric Vehicles"},
    "theme_ゲーム・エンタメ":                {"ja": "ゲーム・エンタメ",          "en": "Gaming & Entertainment"},
    "theme_銀行・金融":                      {"ja": "銀行・金融",                "en": "Banking & Finance"},
    "theme_地方銀行":                        {"ja": "地方銀行",                  "en": "Regional Banks"},
    "theme_保険":                            {"ja": "保険",                      "en": "Insurance"},
    "theme_不動産":                          {"ja": "不動産",                    "en": "Real Estate"},
    "theme_医薬品・バイオ":                  {"ja": "医薬品・バイオ",            "en": "Pharma & Biotech"},
    "theme_ヘルスケア・介護":                {"ja": "ヘルスケア・介護",          "en": "Healthcare & Nursing"},
    "theme_食品・飲料":                      {"ja": "食品・飲料",                "en": "Food & Beverage"},
    "theme_小売・EC":                        {"ja": "小売・EC",                  "en": "Retail & E-Commerce"},
    "theme_通信":                            {"ja": "通信",                      "en": "Telecom"},
    "theme_鉄鋼・素材":                      {"ja": "鉄鋼・素材",                "en": "Steel & Materials"},
    "theme_化学":                            {"ja": "化学",                      "en": "Chemicals"},
    "theme_建設・インフラ":                  {"ja": "建設・インフラ",            "en": "Construction & Infra"},
    "theme_輸送・物流":                      {"ja": "輸送・物流",                "en": "Transport & Logistics"},
    "theme_防衛・航空宇宙":                  {"ja": "防衛・航空宇宙",            "en": "Defense & Aerospace"},
    "theme_フィンテック":                    {"ja": "フィンテック",              "en": "Fintech"},
    "theme_再生可能エネルギー":              {"ja": "再生可能エネルギー",        "en": "Renewable Energy"},
    "theme_ロボット・自動化":                {"ja": "ロボット・自動化",          "en": "Robotics & Automation"},
    "theme_レアアース・資源":                {"ja": "レアアース・資源",          "en": "Rare Earth & Resources"},
    "theme_サイバーセキュリティ":            {"ja": "サイバーセキュリティ",      "en": "Cybersecurity"},
    "theme_ドローン・空飛ぶ車":              {"ja": "ドローン・空飛ぶ車",        "en": "Drones & Flying Cars"},
    "theme_造船":                            {"ja": "造船",                      "en": "Shipbuilding"},
    "theme_観光・ホテル・レジャー":          {"ja": "観光・ホテル・レジャー",    "en": "Tourism & Leisure"},
    "theme_農業・フードテック":              {"ja": "農業・フードテック",        "en": "AgriTech & FoodTech"},
    "theme_教育・HR・人材":                  {"ja": "教育・HR・人材",            "en": "Education & HR"},
    "theme_脱炭素・ESG":                     {"ja": "脱炭素・ESG",               "en": "Decarbonization & ESG"},
    "theme_宇宙・衛星":                      {"ja": "宇宙・衛星",                "en": "Space & Satellites"},
    "theme_日経225（水産・農林・建設・食品・繊維）": {"ja": "日経225（水産・農林・建設・食品・繊維）", "en": "Nikkei225 (Fishery/Agri/Construction/Food/Textiles)"},
    "theme_日経225（化学・医薬品・石油・ゴム・ガラス）": {"ja": "日経225（化学・医薬品・石油・ゴム・ガラス）", "en": "Nikkei225 (Chemicals/Pharma/Oil/Rubber/Glass)"},
    "theme_日経225（鉄鋼・非鉄・金属・機械）": {"ja": "日経225（鉄鋼・非鉄・金属・機械）", "en": "Nikkei225 (Steel/Non-ferrous/Metals/Machinery)"},
    "theme_日経225（電気機器・精密機器）":   {"ja": "日経225（電気機器・精密機器）", "en": "Nikkei225 (Electrical/Precision Equip.)"},
    "theme_日経225（輸送用機器・その他製品・電力ガス）": {"ja": "日経225（輸送用機器・その他製品・電力ガス）", "en": "Nikkei225 (Transportation/Other/Utilities)"},
    "theme_日経225（陸運・海運・空運・倉運・情通）": {"ja": "日経225（陸運・海運・空運・倉運・情通）", "en": "Nikkei225 (Land/Sea/Air/Warehouse/Telecom)"},
    "theme_日経225（卸売・小売・銀行・証券・保険・金融・不動産・サービス）": {"ja": "日経225（卸売・小売・銀行・証券・保険・金融・不動産・サービス）", "en": "Nikkei225 (Wholesale/Retail/Finance/Real Estate/Services)"},
    "theme_TOPIX100（Core30：時価総額最上位）": {"ja": "TOPIX100（Core30：時価総額最上位）", "en": "TOPIX100 (Core30: Largest Cap)"},
    "theme_TOPIX100（Large70：時価総額上位大型株）": {"ja": "TOPIX100（Large70：時価総額上位大型株）", "en": "TOPIX100 (Large70: Large Cap)"},
    "theme_日経平均":                        {"ja": "日経平均",                  "en": "Nikkei 225"},
    "theme_TOPIX(ETF)":                      {"ja": "TOPIX(ETF)",               "en": "TOPIX (ETF)"},
    # ─── 設定ページ ───
    "settings_title":        {"ja": "⚙️ 設定",               "en": "⚙️ Settings"},
    "settings_lang_title":   {"ja": "🌐 言語設定",            "en": "🌐 Language"},
    "settings_lang_desc":    {"ja": "アプリの表示言語を選択してください。",
                              "en": "Select the display language for the app."},
    "settings_theme_title":  {"ja": "🎨 カラーテーマ",        "en": "🎨 Color Theme"},
    "settings_theme_desc":   {"ja": "画面の配色を選択してください。",
                              "en": "Choose the color scheme for the app."},
    "settings_saved":        {"ja": "✅ 設定を保存しました。ページを再描画します...",
                              "en": "✅ Settings saved. Reloading..."},
    "settings_apply":        {"ja": "設定を適用する",          "en": "Apply Settings"},
    "settings_about_title":  {"ja": "ℹ️ StockWaveJP について", "en": "ℹ️ About StockWaveJP"},
    "settings_about_body":   {
        "ja": """**StockWaveJP** は、日本株のテーマ別騰落率・資金フロー・モメンタムを可視化する株式情報ツールです。
約30テーマ・250銘柄のデータをリアルタイムに近い形で集計・表示します。
投資判断の参考情報として活用してください（投資助言ではありません）。""",
        "en": """**StockWaveJP** is a Japanese equity analytics tool that visualizes theme-based returns, capital flow, and price momentum.
Covers ~30 themes and 250 stocks with near real-time data aggregation.
For informational purposes only — not investment advice.""",
    },
    # ─── 追加エントリ（第3弾：カスタムテーマ・細部） ───
    "custom_theme_name_hdr": {"ja": "#### 📌 テーマ名",           "en": "#### 📌 Theme Name"},
    "custom_search_hdr":     {"ja": "#### 🔎 銘柄を検索して追加",  "en": "#### 🔎 Search & Add Stocks"},
    "custom_search_cap":     {"ja": "銘柄名（例：トヨタ）または証券コード4桁（例：7203）で検索",
                              "en": "Search by stock name or 4-digit ticker (e.g. 7203)"},
    "custom_search_btn":     {"ja": "🔍 検索",                    "en": "🔍 Search"},
    "custom_no_result":      {"ja": "該当する銘柄が見つかりませんでした。証券コード4桁または銘柄名で再検索してください。",
                              "en": "No stocks found. Try searching with a 4-digit ticker or stock name."},
    "loading_stock":         {"ja": "{} のデータ取得中...",        "en": "Loading {} data..."},
    "no_data_short":         {"ja": "データを取得できませんでした。", "en": "Could not fetch data."},
    "fetch_error":           {"ja": "データ取得エラー：{}",         "en": "Fetch error: {}"},
    "stock_detail_hdr":      {"ja": "**📊 銘柄詳細**",             "en": "**📊 Stock Detail**"},
    "multi_hit_select":      {"ja": "複数の銘柄がヒットしました。選択してください：",
                              "en": "Multiple stocks found. Please select one:"},
    "already_added":         {"ja": "✅ **{}** はすでにリストに追加済みです。",
                              "en": "✅ **{}** is already in the list."},
    "add_to_theme_btn":      {"ja": "＋ 「{}」をテーマに追加",     "en": "＋ Add「{}」to Theme"},
    "added_stocks_hdr":      {"ja": "**📋 追加済み銘柄（{}件）**", "en": "**📋 Added Stocks ({})**"},
    "save_theme_btn":        {"ja": "✅ テーマを保存",              "en": "✅ Save Theme"},
    "err_no_name":           {"ja": "テーマ名を入力してください",   "en": "Please enter a theme name"},
    "err_dup_name":          {"ja": "デフォルトテーマと同じ名前は使えません",
                              "en": "Cannot use the same name as a default theme"},
    "err_no_stocks":         {"ja": "銘柄を1つ以上追加してください", "en": "Please add at least one stock"},
    "custom_no_themes":      {"ja": "まだカスタムテーマがありません。「新規作成」タブから作成してください。",
                              "en": "No custom themes yet. Create one using the New Theme tab."},
    "custom_existing_hdr":   {"ja": "#### 作成済みカスタムテーマ",  "en": "#### Existing Custom Themes"},
    "custom_theme_item":     {"ja": "📌 {}（{}銘柄）",             "en": "📌 {} ({} stocks)"},
    "stock_list_hdr":        {"ja": "**銘柄一覧：**",               "en": "**Stock List:**"},
    "edit_btn":              {"ja": "✏️ 編集",                    "en": "✏️ Edit"},
    "edit_hint":             {"ja": "「新規作成」タブで「{}」を編集できます。保存すると上書きされます。",
                              "en": "Edit「{}」in the New Theme tab. Saving will overwrite it."},
    "delete_btn":            {"ja": "🗑️ 削除",                   "en": "🗑️ Delete"},
    "howto_section_title":   {"ja": "### 📌 各ページの使い方",      "en": "### 📌 How to Use Each Page"},
    "faq_title":             {"ja": "### ❓ よくある質問（Q&A）",   "en": "### ❓ FAQ"},
    "settings_no_change":    {"ja": "設定に変更はありませんでした。", "en": "No changes were made."},
    # ─── 使い方・Q&A・免責事項 本文 ───
    "howto_intro_title":  {"ja": "🚀 StockWaveJP とは",
                           "en": "🚀 What is StockWaveJP?"},
    "howto_intro_body":   {
        "ja": "StockWaveJP は、日本株のテーマ別騰落率・資金フロー・モメンタムを可視化する<b style=\"color:#e8eaf0;\">無料の株式情報ツール</b>です。<br>約30テーマ・250銘柄以上のデータをリアルタイムに近い形で集計・表示します。<br>投資判断の参考情報として活用してください（投資助言ではありません）。",
        "en": "StockWaveJP is a <b style=\"color:#e8eaf0;\">free Japanese equity analytics tool</b> that visualizes theme-based returns, fund flow, and price momentum.<br>Covers ~30 themes and 250+ stocks with near real-time data aggregation.<br>For reference purposes only — not investment advice.",
    },
    "howto_feedback":     {
        "ja": "ご要望・不具合報告は GitHubのIssues または お問い合わせフォームからお寄せください。",
        "en": "For feature requests or bug reports, please use GitHub Issues or the contact form.",
    },
    "guide_items": {
        "ja": [
            ("📊 テーマ一覧",       "期間を選択して上位・下位テーマの騰落率ランキングを確認できます。表示テーマ数は5〜全件で切り替え可能です。"),
            ("📡 騰落モメンタム",   "現在の騰落率に加え、先週比・先月比の変化量（ポイント）を表示。🔥加速・❄️失速など状態ラベルで相場の勢いを把握できます。"),
            ("💹 資金フロー",       "資金流入TOP10・流出TOP10を左右で比較。全テーマの騰落率一覧も確認できます。"),
            ("📈 騰落推移",         "過去1年分のテーマ別騰落率の時系列推移をグラフ表示。上位5テーマ／手動選択／全テーマを切り替えられます。"),
            ("🔥 ヒートマップ",     "テーマ×期間のヒートマップで、どのテーマがいつ強かったかを一目で把握できます。"),
            ("📉 テーマ比較",       "複数テーマを選んで騰落率を直接比較できます。"),
            ("🌍 マクロ比較",       "日経平均・TOPIX・米国指数（S&P500・NASDAQ）と各テーマを比較します。"),
            ("📋 市場別ランキング", "日経225・TOPIX100・東証プライムなど市場セグメント別の騰落率ランキングです。"),
            ("🔍 テーマ別詳細",     "テーマを選択すると構成銘柄の個別騰落率・出来高ランキング・RSIなどを確認できます。"),
            ("⭐ お気に入り",       "テーマ別詳細ページで「☆ 登録」した銘柄をまとめて確認できます。"),
            ("🏷️ カスタムテーマ",   "銘柄名または証券コード4桁で検索して自分だけのテーマを作成できます。"),
        ],
        "en": [
            ("📊 Theme List",       "Select a period to view top/bottom theme return rankings. You can switch between showing 5 to all themes."),
            ("📡 Momentum",         "Displays current return plus weekly/monthly changes in points. State labels like 🔥Accelerating and ❄️Decelerating help you gauge market momentum at a glance."),
            ("💹 Fund Flow",        "Compare top 10 inflow vs outflow themes side by side. Also shows a full return overview for all themes."),
            ("📈 Price Trend",      "Time-series chart of theme returns over up to 1 year. Switch between Top 5, manual selection, or all themes."),
            ("🔥 Heatmap",          "Theme × period heatmap lets you instantly see which themes were strong and when."),
            ("📉 Theme Compare",    "Select multiple themes and compare their returns directly on the same chart."),
            ("🌍 Macro",            "Compare themes against the Nikkei 225, TOPIX, and US indices (S&P 500, NASDAQ)."),
            ("📋 Market Ranking",   "Return rankings by market segment: Nikkei 225, TOPIX100, TSE Prime, and more."),
            ("🔍 Theme Detail",     "Select a theme to view individual stock returns, volume rankings, RSI, and more."),
            ("⭐ Favorites",        "View all stocks you have starred from the Theme Detail page in one place."),
            ("🏷️ Custom Theme",     "Search by stock name or 4-digit ticker to build your own original theme."),
        ],
    },
    "qa_items": {
        "ja": [
            ("データはどこから取得していますか？",
             "Yahoo! Finance の公開データをyfinanceライブラリ経由で取得しています。リアルタイムではなく、市場開場中は約3分、時間外は約30〜60分のキャッシュが適用されます。"),
            ("表示される「現在時刻」と「データ更新」の違いは何ですか？",
             "「現在時刻」はページを開いた瞬間の時刻です。「データ更新」はキャッシュが最後に生成された時刻で、実際のデータ取得時刻を示します。差分がキャッシュの経過時間です。"),
            ("データが古い・更新されない場合はどうすればいいですか？",
             "サイドバー下部の「🔄 データを最新に更新」ボタンを押してください。キャッシュがクリアされ、最新データが取得されます。"),
            ("証券コードで検索する方法は？",
             "カスタムテーマページの検索バーに4桁の証券コード（例：7203）を入力して検索してください。「.T」は自動で補完されます。"),
            ("お気に入りはどこに保存されますか？",
             "現在はブラウザのセッション中のみ保持されます。ページを閉じたり更新すると消えます。将来的にはローカル保存機能の追加を検討しています。"),
            ("掲載されていないテーマ・銘柄を追加できますか？",
             "「🏷️ カスタムテーマ」ページから、任意の銘柄でオリジナルテーマを作成できます。証券コードがわかれば掲載外の銘柄も追加可能です。"),
            ("スマホでも使えますか？",
             "はい、スマートフォンブラウザに対応しています。画面サイズに合わせてレイアウトが調整されます。"),
        ],
        "en": [
            ("Where does the data come from?",
             "Data is sourced from Yahoo! Finance via the yfinance library. It is not real-time — cache is refreshed approximately every 3 minutes during market hours, and every 30–60 minutes outside market hours."),
            ("What is the difference between 'Current Time' and 'Data Updated'?",
             "'Current Time' is the moment you opened the page. 'Data Updated' is when the cache was last generated — i.e., when the data was actually fetched. The difference is how long ago the cache was created."),
            ("What should I do if the data seems stale or not refreshing?",
             "Click the '🔄 Refresh Data' button in the sidebar. This clears the cache and fetches the latest data."),
            ("How do I search by ticker code?",
             "Enter a 4-digit ticker (e.g. 7203) in the Custom Theme search bar. The '.T' suffix is added automatically."),
            ("Where are my favorites saved?",
             "Favorites are stored only within your current browser session. They will be cleared if you close or refresh the page. Local persistence is planned for a future update."),
            ("Can I add themes or stocks not currently listed?",
             "Yes — use the 🏷️ Custom Theme page to build your own theme with any stocks. As long as you have the ticker code, you can add any listed stock."),
            ("Is it available on mobile?",
             "Yes, the app is compatible with smartphone browsers and the layout adapts to your screen size."),
        ],
    },
    "disclaimer_sections": {
        "ja": [
            ("📋 サービス概要",
             "StockWaveJP（以下「本サービス」）は、日本株式市場に関するテーマ別の騰落率・資金フロー・モメンタム等の統計情報を提供する情報サービスです。本サービスはいかなる意味においても投資助言・投資推奨を行うものではありません。"),
            ("⚠️ 投資に関する免責",
             "・本サービスで提供する情報はすべて情報提供のみを目的としており、特定の有価証券の売買を推奨・勧誘するものではありません。\n・投資に関する最終判断はご自身の責任において行ってください。\n・本サービスの情報を参考にした投資行動により生じた損失・損害について、StockWaveJP および開発者は一切の責任を負いません。\n・株式投資には元本割れのリスクがあります。過去の騰落率は将来の運用成果を保証するものではありません。"),
            ("📡 データの正確性について",
             "・本サービスのデータはYahoo! Finance（yfinanceライブラリ経由）から取得しており、データの正確性・完全性・最新性を保証するものではありません。\n・データの遅延・欠損・誤りが生じる場合があります。重要な投資判断には必ず公式情報源をご確認ください。\n・yfinanceはYahoo! Financeの非公式APIであり、サービス変更により突然利用できなくなる可能性があります。"),
            ("🔒 個人情報・プライバシー",
             "・本サービスはユーザー登録不要で利用できます。\n・お気に入り・カスタムテーマ等のデータはブラウザのセッション内にのみ保持され、外部サーバーへの送信は行いません。\n・アクセス解析のため、Streamlit Cloudの標準的なログ収集が行われる場合があります。"),
            ("📜 著作権・知的財産",
             "・本サービスのデザイン・ロゴ・コード・コンテンツの著作権はStockWaveJPに帰属します。\n・無断での複製・転載・改変・商業利用を禁止します。\n・「StockWaveJP」「株式波動」の名称・ロゴは商標登録出願中です。"),
            ("🔄 サービスの変更・終了",
             "・本サービスは予告なく内容の変更・機能の追加・削除・サービスの停止を行う場合があります。\n・これらにより生じた損害について、StockWaveJP および開発者は責任を負いません。"),
            ("📅 制定・改定",
             "・本免責事項は2026年3月に制定しました。\n・内容は予告なく改定される場合があります。改定後も引き続き本サービスを利用された場合、改定後の内容に同意したものとみなします。"),
        ],
        "en": [
            ("📋 Service Overview",
             "StockWaveJP (hereinafter 'the Service') is an information service providing statistical data on Japanese equities, including theme-based returns, fund flow, and price momentum. The Service does not constitute investment advice or recommendations of any kind."),
            ("⚠️ Investment Disclaimer",
             "· All information provided by this Service is for informational purposes only and does not constitute a solicitation or recommendation to buy or sell any security.\n· All investment decisions are made solely at your own risk and responsibility.\n· StockWaveJP and its developers accept no liability for any losses or damages resulting from investment actions taken based on information provided by this Service.\n· Stock investments carry the risk of capital loss. Past returns do not guarantee future performance."),
            ("📡 Data Accuracy",
             "· Data is sourced from Yahoo! Finance via the yfinance library. We do not guarantee the accuracy, completeness, or timeliness of the data.\n· Data delays, gaps, or errors may occur. Always verify critical investment decisions against official sources.\n· yfinance is an unofficial API and may become unavailable without notice due to changes in Yahoo! Finance's services."),
            ("🔒 Privacy",
             "· No user registration is required to use this Service.\n· Favorites and custom theme data are stored only within your browser session and are never transmitted to external servers.\n· Streamlit Cloud may collect standard access logs for analytics purposes."),
            ("📜 Intellectual Property",
             "· All design, logos, code, and content of this Service are the intellectual property of StockWaveJP.\n· Unauthorized reproduction, redistribution, modification, or commercial use is prohibited.\n· The names 'StockWaveJP' and '株式波動' and associated logos are pending trademark registration."),
            ("🔄 Service Changes & Termination",
             "· The Service may be modified, updated, or terminated at any time without prior notice.\n· StockWaveJP and its developers are not liable for any damages arising from such changes."),
            ("📅 Effective Date & Revisions",
             "· This disclaimer was established in March 2026.\n· Contents may be revised without notice. Continued use of the Service following any revision constitutes acceptance of the revised terms."),
        ],
    },
    "disclaimer_footer": {
        "ja": "© 2026 StockWaveJP　|　本サービスは情報提供のみを目的とします。<br>投資に関する最終判断はご自身の責任においてお願いします。",
        "en": "© 2026 StockWaveJP  |  For informational purposes only.<br>All investment decisions are made at your own risk.",
    },


    # ─── 追加エントリ（第2弾） ───
    "theme_ranking_title":   {"ja": "📊 テーマ別ランキング",    "en": "📊 Theme Ranking"},
    "volume_by_theme":       {"ja": "**🔢 テーマ別出来高**",    "en": "**🔢 Theme Volume**"},
    "trend_cap":             {"ja": "yfinanceの日次終値から算出（スプレッドシート不要）",
                              "en": "Calculated from yfinance daily close prices."},
    "heatmap_legend":        {"ja": "🔴**赤=上昇** 　🟢**緑=下落** 　⬛**黒=±0**",
                              "en": "🔴**Red=Rise** 　🟢**Green=Fall** 　⬛**Black=±0**"},
    "monthly_heatmap_title": {"ja": "**過去12ヶ月の月別騰落率** 🔴赤=上昇　🟢緑=下落",
                              "en": "**Monthly Returns (Past 12 Months)** 🔴Red=Rise　🟢Green=Fall"},
    "monthly_cap":           {"ja": "各月の始値→終値の騰落率（テーマ内銘柄の平均）",
                              "en": "Monthly return = open→close avg across theme stocks"},
    "loading_monthly":       {"ja": "月次データ取得中...（少し時間がかかります）",
                              "en": "Fetching monthly data... (may take a moment)"},
    "monthly_table_title":   {"ja": "**📋 月次騰落率テーブル**",  "en": "**📋 Monthly Return Table**"},
    "download_monthly_csv":  {"ja": "📥 月次CSV",               "en": "📥 Monthly CSV"},
    "hl_top5_btn":           {"ja": "🔴 上昇TOP5",               "en": "🔴 Top 5 Gainers"},
    "hl_bot5_btn":           {"ja": "🟢 下落TOP5",               "en": "🟢 Top 5 Losers"},
    "hl_all_btn":            {"ja": "📋 全テーマ",               "en": "📋 All Themes"},
    "select_theme_prompt2":  {"ja": "テーマを選択してください",   "en": "Please select a theme"},
    "compare_chart_title":   {"ja": "📉 テーマ間比較チャート",    "en": "📉 Theme Comparison Chart"},
    "compare_warn":          {"ja": "2つ以上のテーマを選択してください",
                              "en": "Please select at least 2 themes"},
    "macro_comp_title":      {"ja": "🌍 マクロ指標との比較",     "en": "🌍 Macro Comparison"},
    "compare_stock_select":  {"ja": "比較する銘柄を選択",         "en": "Select stock to compare"},
    "market_rank_cap":       {"ja": "日経225・プライム・スタンダード・グロース別の騰落率ランキング",
                              "en": "Return rankings by Nikkei225 / Prime / Standard / Growth"},
    "loading_seg":           {"ja": "{} データ取得中...",         "en": "Loading {} data..."},
    "top5_stocks":           {"ja": "**🔴 上位5銘柄**",           "en": "**🔴 Top 5 Stocks**"},
    "bot5_stocks":           {"ja": "**🟢 下位5銘柄**",           "en": "**🟢 Bottom 5 Stocks**"},
    "show_all_stocks":       {"ja": "全{}銘柄を表示",             "en": "Show all {} stocks"},
    "fav_add_hint":          {"ja": "テーマ一覧ページで「☆ 登録」ボタンを押して追加してください。",
                              "en": "Go to Theme List page and press ☆ to add favorites."},
    "fav_csv":               {"ja": "📥 お気に入りCSV",           "en": "📥 Favorites CSV"},
    "fav_remove_btn":        {"ja": "⭐ 解除",                    "en": "⭐ Remove"},
    "fav_add_btn":           {"ja": "☆ 登録",                    "en": "☆ Add"},
    "vol_individual":        {"ja": "**🔢 個別株出来高**",         "en": "**🔢 Stock Volume**"},
    "tv_individual":         {"ja": "**💴 個別株売買代金**",       "en": "**💴 Stock Trade Value**"},
    "stock_detail_table":    {"ja": "**📋 銘柄詳細一覧**",         "en": "**📋 Stock Detail**"},
    "fav_section":           {"ja": "**⭐ お気に入り登録**",       "en": "**⭐ Favorites**"},
    "no_theme_data":         {"ja": "データを取得できませんでした。別のテーマを選択してください。",
                              "en": "Could not fetch data. Please select another theme."},
    "news_caption":          {"ja": "StockWaveJP の機能追加・変更・修正情報をお知らせします。",
                              "en": "News on StockWaveJP feature additions, changes, and fixes."},
    "custom_edit_title":     {"ja": "🏷️ カスタムテーマ作成・編集", "en": "🏷️ Create / Edit Custom Themes"},
    "custom_edit_cap":       {"ja": "自分だけのオリジナルテーマを作成できます。",
                              "en": "Create and manage your own original themes."},
    "download_heatmap_csv":  {"ja": "📥 CSV",                    "en": "📥 CSV"},
    "trend_rank_title_fmt":  {"ja": "**📋 テーマ騰落率ランキング（{}）**",
                              "en": "**📋 Theme Return Ranking ({})**"},
    # ─── テーブル列名 ───
    "stock_col":             {"ja": "銘柄",     "en": "Stock"},
    "price_col":             {"ja": "株価",     "en": "Price"},
    "day_change_col":        {"ja": "前日比",   "en": "Day Chg"},
}

def t(key: str) -> str:
    """現在の言語設定に従って翻訳テキストを返す"""
    lang = st.session_state.get("app_language", "ja")
    entry = I18N.get(key, {})
    return entry.get(lang, entry.get("ja", key))

def tn(theme_name: str) -> str:
    """テーマ名を現在の言語に翻訳して返す（英語未登録の場合は原文）"""
    lang = st.session_state.get("app_language", "ja")
    if lang == "ja":
        return theme_name
    key = f"theme_{theme_name}"
    entry = I18N.get(key, {})
    return entry.get("en", theme_name)

# PAGESリストを言語設定に応じて動的生成
def get_pages():
    return [
        t("page_theme_list"),
        t("page_momentum"),
        t("page_fund_flow"),
        t("page_trend"),
        t("page_heatmap"),
        t("page_compare"),
        t("page_macro"),
        t("page_market_rank"),
        t("page_theme_detail"),
        t("page_favorites"),
        t("page_custom"),
        t("page_news"),
        t("page_howto"),
        t("page_disclaimer"),
        t("page_settings"),
    ]

# =====================
# ページ切り替え（クリックで即切替）
# =====================
PAGES = get_pages()

if "current_page" not in st.session_state:
    st.session_state["current_page"] = PAGES[0]

# 言語切り替え時にcurrent_pageが旧言語のページ名のままになるのを防ぐ
# → ページインデックスで管理して言語変更後も同ページに留まる
if "current_page_idx" not in st.session_state:
    st.session_state["current_page_idx"] = 0

# current_page_idxからページ名を同期
_pidx = st.session_state["current_page_idx"]
if _pidx < len(PAGES):
    st.session_state["current_page"] = PAGES[_pidx]
else:
    st.session_state["current_page_idx"] = 0
    st.session_state["current_page"] = PAGES[0]

st.sidebar.markdown(f"### {t('menu')}")
for _i, _p in enumerate(PAGES):
    _active = st.session_state["current_page_idx"] == _i
    if st.sidebar.button(_p, key=f"nav_{_i}", use_container_width=True):
        st.session_state["current_page_idx"] = _i
        st.session_state["current_page"] = _p
        st.rerun()

page = st.session_state["current_page"]

fav_count = len(st.session_state["favorites"])
if fav_count > 0:
    st.sidebar.info(t("fav_count").format(fav_count))
if st.sidebar.button(t("refresh")):
    st.cache_data.clear()
    st.rerun()

# 市場状態と更新頻度の表示
import datetime as _dt2
_now_jst = _dt2.datetime.utcnow() + _dt2.timedelta(hours=9)
_wd = _now_jst.weekday()
_t = _now_jst.time()
_mo = _dt2.time(9, 0)
_mc = _dt2.time(15, 35)

if _wd >= 5:
    _market_status = t("market_closed_weekend")
    _ttl_min = 60
elif _mo <= _t <= _mc:
    _market_status = t("market_open")
    _ttl_min = 3
else:
    _market_status = t("market_closed_hours")
    _ttl_min = 30

st.sidebar.markdown(f"**{_market_status}**")
st.sidebar.caption(t("update_interval").format(_ttl_min))
st.sidebar.caption(t("current_time").format(_now_jst.strftime('%H:%M')))
st.sidebar.markdown("---")
st.sidebar.markdown(
    "<div style='font-size:10px;color:#3a4560;text-align:center;line-height:1.8;'>"
    "© 2026 StockWaveJP<br>"
    "本サービスは情報提供のみを目的とします。<br>"
    "For informational purposes only."
    "</div>",
    unsafe_allow_html=True
)

# now は毎回リアルタイムで現在時刻を取得（キャッシュに依存しない）
def _get_now_str():
    return (_dt2.datetime.utcnow() + _dt2.timedelta(hours=9)).strftime("%Y年%m月%d日 %H:%M")
now = _get_now_str()
themes = get_all_themes()
all_stocks = {}
for stk in themes.values():
    for name, ticker in stk.items():
        all_stocks[name] = ticker

# ページIDをインデックスで定義（言語に依存しない判定用）
PAGE_THEME_LIST    = 0
PAGE_MOMENTUM      = 1
PAGE_FUND_FLOW     = 2
PAGE_TREND         = 3
PAGE_HEATMAP       = 4
PAGE_COMPARE       = 5
PAGE_MACRO         = 6
PAGE_MARKET_RANK   = 7
PAGE_THEME_DETAIL  = 8
PAGE_FAVORITES     = 9
PAGE_CUSTOM        = 10
PAGE_NEWS          = 11
PAGE_HOWTO         = 12
PAGE_DISCLAIMER    = 13
PAGE_SETTINGS      = 14

pidx = st.session_state.get("current_page_idx", 0)

# =====================
# テーマ一覧
# =====================
if pidx == PAGE_THEME_LIST:
    now = _get_now_str()

    # 期間ボタン（上部）
    period = period_buttons(key_prefix="home")

    # 表示テーマ数選択
    col_disp1, col_disp2 = st.columns([3, 1])
    with col_disp2:
        display_count = st.selectbox(t("display_count_label"), [5, 10, 15, 25, 99], index=0,
                                      label_visibility="collapsed")
        st.caption(t("display_count_all") if display_count >= 99 else t("display_count_caption").format(display_count))

    theme_keys = tuple(themes.keys())
    with st.spinner(t("loading_first")):
        theme_results, theme_details, _cache_time = fetch_all_theme_data(period, theme_keys)

    # データ取得後に現在時刻・更新時刻を表示（_cache_time定義後）
    st.caption(f"🕐 {now}  |  📦 {_cache_time}  |  {len(themes)} themes · ~{len(all_stocks)} stocks" if st.session_state.get("app_language","ja")=="en" else f"🕐 現在時刻：{now}　｜　📦 データ更新：{_cache_time}　　{len(themes)}テーマ・約{len(all_stocks)}銘柄")

    # 表示件数に応じて上位・下位を切り出し
    n = display_count if display_count < 99 else len(theme_results)
    top_results = theme_results[:n]
    bot_results = theme_results[-n:] if display_count < 99 else []

    # === 上位テーマランキング ===
    st.markdown(f'<p style="font-size:13px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:8px 0 4px;">{t("top_gainers")} TOP{n}</p>', unsafe_allow_html=True)
    top_labels = [tn(r["テーマ"]) for r in top_results]
    top_ranks  = [f"{i+1}" for i in range(len(top_results))]
    top_values = [r["平均騰落率(%)"] for r in top_results]
    top_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in top_values]
    # スクロール枠内に表示（グラフは全件分の高さ、枠でスクロール）
    chart_h = max(200, len(top_results) * 34)
    st.plotly_chart(make_bar_chart(top_labels, top_values, top_colors, height=chart_h, rank_labels=top_ranks),
                    use_container_width=True, config=PLOT_CONFIG)

    # === 下位テーマランキング ===
    if bot_results and display_count < 99:
        st.markdown(f'<p style="font-size:13px;font-weight:700;white-space:nowrap;overflow:hidden;text-overflow:ellipsis;margin:8px 0 4px;">{t("top_losers")} TOP{n}</p>', unsafe_allow_html=True)
        total = len(theme_results)
        bot_labels = [tn(r["テーマ"]) for r in bot_results]
        bot_ranks  = [f"{total-n+i+1}" for i in range(len(bot_results))]
        bot_values = [r["平均騰落率(%)"] for r in bot_results]
        bot_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in bot_values]
        chart_h2 = max(200, len(bot_results) * 34)
        st.plotly_chart(make_bar_chart(bot_labels, bot_values, bot_colors, height=chart_h2, rank_labels=bot_ranks),
                        use_container_width=True, config=PLOT_CONFIG)

    # === テーマ別出来高・売買代金ランキング ===
    st.subheader(t("theme_ranking_title"))
    col_rank1, col_rank2 = st.columns(2)

    if "show_vol_all" not in st.session_state:
        st.session_state["show_vol_all"] = False
    if "show_tv_all" not in st.session_state:
        st.session_state["show_tv_all"] = False

    # 出来高ランキング
    vol_sorted_all = sorted(theme_results, key=lambda x: x["合計出来高"], reverse=True)
    with col_rank1:
        st.markdown(t("volume_by_theme"))
        show_v = st.session_state["show_vol_all"]
        disp_vol = vol_sorted_all if show_v else vol_sorted_all[:5]
        vol_rows = [
            {t("rank_col"): t("rank_suffix").format(i+1), t("theme_col"): tn(r["テーマ"]), t("volume_col"): f"{int(r['合計出来高']):,}"}
            for i, r in enumerate(disp_vol)
        ]
        st.dataframe(pd.DataFrame(vol_rows).set_index(t("rank_col")), use_container_width=True)
        btn_label_v = "▲ 閉じる" if show_v else f"▼ 6位以下を表示（残り{len(vol_sorted_all)-5}件）"
        if st.button(btn_label_v, key="btn_vol_toggle", use_container_width=True):
            st.session_state["show_vol_all"] = not show_v
            st.rerun()

    # 売買代金ランキング
    tv_sorted_all = sorted(theme_results, key=lambda x: x["合計売買代金"], reverse=True)
    with col_rank2:
        st.markdown(f"**{t('trade_value_ranking')}**")
        show_t = st.session_state["show_tv_all"]
        disp_tv = tv_sorted_all if show_t else tv_sorted_all[:5]
        tv_rows = [
            {t("rank_col"): t("rank_suffix").format(i+1), t("theme_col"): tn(r["テーマ"]), t("trade_val_col"): format_large_number(r["合計売買代金"])}
            for i, r in enumerate(disp_tv)
        ]
        st.dataframe(pd.DataFrame(tv_rows).set_index(t("rank_col")), use_container_width=True)
        btn_label_t = t("show_less") if show_t else t("show_more").format(len(tv_sorted_all)-5)
        if st.button(btn_label_t, key="btn_tv_toggle", use_container_width=True):
            st.session_state["show_tv_all"] = not show_t
            st.rerun()

    # === 全テーマ一覧表 ===
    st.subheader(t("all_themes_table"))
    table_data = []
    for rank, r in enumerate(theme_results, 1):
        c, v = r["平均騰落率(%)"], r["出来高増減(%)"]
        table_data.append({
            t("rank_col"): t("rank_suffix").format(rank),
            t("theme_col"): tn(r["テーマ"]),
            t("change_col"): f"🔴 +{c}%" if c>0 else f"🟢 {c}%",
            t("volume_col"): f"📈 +{v}%" if v>0 else f"📉 {v}%",
        })
    df_table = pd.DataFrame(table_data).set_index(t("rank_col"))
    st.dataframe(df_table, use_container_width=True)
    st.download_button(t("csv_download"), df_table.to_csv(encoding="utf-8-sig"),
                       f"theme_list_{now}.csv", "text/csv")



# =====================
# 騰落モメンタム
# =====================
elif pidx == PAGE_MOMENTUM:
    st.subheader(t("page_momentum"))
    st.caption(t("momentum_caption"))
    period = period_buttons(key_prefix="momentum_page")

    theme_keys = tuple(themes.keys())
    with st.spinner(t("loading")):
        results_now, _, _ct1 = fetch_all_theme_data(period, theme_keys)
        results_1w, _, _ct2 = fetch_all_theme_data("5d",  theme_keys)
        results_1m, _, _ct3 = fetch_all_theme_data("1mo", theme_keys)

    # 辞書化
    now_map = {r["テーマ"]: r["平均騰落率(%)"] for r in results_now}
    w1_map  = {r["テーマ"]: r["平均騰落率(%)"] for r in results_1w}
    m1_map  = {r["テーマ"]: r["平均騰落率(%)"] for r in results_1m}

    # モメンタムデータ組み立て
    momentum_data = []
    for theme_n in now_map:
        cur   = now_map.get(theme_n, 0)
        dw    = round(cur - w1_map.get(theme_n, cur), 2)
        dm    = round(cur - m1_map.get(theme_n, cur), 2)
        if   dw > 3  and dm > 5:  state = t("state_accel")
        elif dw < -3 and dm < -5: state = t("state_decel")
        elif dw > 2:               state = t("state_up")
        elif dw < -2:              state = t("state_down")
        else:                      state = t("state_flat")
        momentum_data.append({"テーマ": theme_n, "騰落率": cur, "先週比": dw, "先月比": dm, "状態": state})

    # 並び替え選択
    sort_key = st.selectbox(t("sort_label"), [t("sort_return"), t("sort_weekly"), t("sort_monthly")],
                             label_visibility="collapsed")
    if sort_key == t("sort_return"):
        momentum_data.sort(key=lambda x: x["騰落率"], reverse=True)
    elif sort_key == t("sort_weekly"):
        momentum_data.sort(key=lambda x: x["先週比"], reverse=True)
    else:
        momentum_data.sort(key=lambda x: x["先月比"], reverse=True)

    # フィルター
    filter_state = st.multiselect(t("filter_state"),
                                   [t("state_accel"),t("state_up"),t("state_flat"),t("state_down"),t("state_decel")])
    if filter_state:
        momentum_data = [d for d in momentum_data if d["状態"] in filter_state]

    # ヘッダー行
    hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([3, 2, 2, 2, 2])
    hcol1.markdown(f"<small style='color:#666'>{t('col_theme')}</small>", unsafe_allow_html=True)
    hcol2.markdown(f"<small style='color:#666'>{t('col_return')}</small>", unsafe_allow_html=True)
    hcol3.markdown(f"<small style='color:#666'>{t('col_weekly')}</small>", unsafe_allow_html=True)
    hcol4.markdown(f"<small style='color:#666'>{t('col_monthly')}</small>", unsafe_allow_html=True)
    hcol5.markdown(f"<small style='color:#666'>{t('col_state')}</small>", unsafe_allow_html=True)
    st.markdown("<hr style='margin:2px 0 6px;border-color:#2a2a3a'>", unsafe_allow_html=True)

    # 表示
    for i, d in enumerate(momentum_data):
        cur = d["騰落率"]
        dw  = d["先週比"]
        dm  = d["先月比"]
        state = d["状態"]
        c_color = "🔴" if cur >= 0 else "🟢"
        dw_icon = "▲" if dw > 1 else "▼" if dw < -1 else "→"
        dm_icon = "▲" if dm > 1 else "▼" if dm < -1 else "→"
        sign = "+" if cur >= 0 else ""
        dw_sign = "+" if dw >= 0 else ""
        dm_sign = "+" if dm >= 0 else ""
        col1, col2, col3, col4, col5 = st.columns([3, 2, 2, 2, 2])
        col1.write(f"**{i+1}. {tn(d['テーマ'])}**")
        col2.write(f"{c_color} {sign}{cur}%")
        col3.write(f"{dw_icon} {dw_sign}{dw}pt")
        col4.write(f"{dm_icon} {dm_sign}{dm}pt")
        col5.write(state)

    st.caption(t("momentum_note"))

# =====================
# 資金フロー
# =====================
elif pidx == PAGE_FUND_FLOW:
    st.subheader(t("fund_flow_title"))
    st.caption(t("fund_flow_caption"))
    period = period_buttons(key_prefix="flow_page")

    theme_keys = tuple(themes.keys())
    with st.spinner(t("loading")):
        flow_results, _, _ct_flow = fetch_all_theme_data(period, theme_keys)

    flow_sorted = sorted(flow_results, key=lambda x: x["平均騰落率(%)"], reverse=True)
    gainers = flow_sorted[:10]
    losers  = flow_sorted[-10:][::-1]
    total   = len(flow_sorted)

    col_g, col_l = st.columns(2)
    with col_g:
        st.markdown(t("inflow_top"))
        g_labels = [tn(r["テーマ"]) for r in gainers]
        g_ranks  = [str(i+1) for i in range(len(gainers))]
        g_values = [r["平均騰落率(%)"] for r in gainers]
        g_colors = ["#ff4b4b"] * len(gainers)
        st.plotly_chart(make_bar_chart(g_labels, g_values, g_colors,
                                       height=max(200, len(gainers)*38),
                                       rank_labels=g_ranks),
                        use_container_width=True, config=PLOT_CONFIG)

    with col_l:
        st.markdown(t("outflow_top"))
        l_labels = [tn(r["テーマ"]) for r in losers]
        l_ranks  = [str(total - len(losers) + i + 1) for i in range(len(losers))]
        l_values = [r["平均騰落率(%)"] for r in losers]
        l_colors = ["#39d353"] * len(losers)
        st.plotly_chart(make_bar_chart(l_labels, l_values, l_colors,
                                       height=max(200, len(losers)*38),
                                       rank_labels=l_ranks),
                        use_container_width=True, config=PLOT_CONFIG)

    # 全テーマ一覧
    st.markdown("---")
    st.markdown(t("all_flow_overview"))
    all_labels = [tn(r["テーマ"]) for r in flow_sorted]
    all_ranks  = [str(i+1) for i in range(len(flow_sorted))]
    all_values = [r["平均騰落率(%)"] for r in flow_sorted]
    all_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in all_values]
    st.plotly_chart(make_bar_chart(all_labels, all_values, all_colors,
                                   height=max(400, len(flow_sorted)*30),
                                   rank_labels=all_ranks),
                    use_container_width=True, config=PLOT_CONFIG)

# =====================
# 騰落推移（yfinance日次データ版）
# =====================
elif pidx == PAGE_TREND:
    st.subheader(t("trend_title"))
    st.caption(f"🕐 {_get_now_str()}  |  {t('trend_cap')}")

    # 期間選択
    trend_period = st.selectbox(
        t("trend_period_label"),
        [t("period_1w"), t("period_1m"), t("period_3m"), t("period_6m"), t("period_1y")],
        index=4,
        key="trend_period_sel",
    )
    period_map = {t("period_1w"): "5d", t("period_1m"): "1mo", t("period_3m"): "3mo", t("period_6m"): "6mo", t("period_1y"): "1y"}
    sel_period = period_map[trend_period]

    theme_keys = tuple(themes.keys())

    with st.spinner(t("loading_daily")):
        trend_data = fetch_theme_trend(theme_keys, sel_period)

    if not trend_data:
        st.warning(t("no_data"))
    else:
        # 期間末の騰落率でランキング
        final_changes = {}
        for theme_n, s in trend_data.items():
            if s is not None and len(s) > 0:
                final_changes[theme_n] = s.iloc[-1]

        sorted_themes = sorted(final_changes.items(), key=lambda x: x[1], reverse=True)

        # デフォルト: 上位5・下位5
        top5    = [t for t, _ in sorted_themes[:5]]
        worst5  = [t for t, _ in sorted_themes[-5:]]
        default_sel = list(dict.fromkeys(top5 + worst5))  # 重複排除

        # 表示モード
        mode = st.radio(
            t("trend_mode_label"),
            [t("trend_mode_top"), t("trend_mode_manual"), t("trend_mode_all")],
            horizontal=True,
            key="trend_mode",
        )

        all_theme_names = list(trend_data.keys())
        if mode == t("trend_mode_top"):
            selected = default_sel
        elif mode == t("trend_mode_manual"):
            selected = st.multiselect(
                t("trend_manual_label"),
                all_theme_names,
                default=default_sel,
                key="trend_manual_sel",
            )
        else:
            selected = all_theme_names

        if not selected:
            st.info(t("select_theme_prompt"))
        else:
            fig = go.Figure()
            colors = [
                "#ff4b4b","#ff9955","#ffdd55","#55dd99","#55aaff",
                "#aa77ff","#ff77aa","#44dddd","#aaddff","#ffaa77",
                "#88ff88","#ff6688","#66aaff","#ffcc44","#99ffcc",
            ]
            for i, theme_n in enumerate(selected):
                if theme_n not in trend_data:
                    continue
                s = trend_data[theme_n]
                if s is None or len(s) < 2:
                    continue
                color = colors[i % len(colors)]
                final_val = s.iloc[-1]
                sign = "+" if final_val >= 0 else ""
                display_name = tn(theme_n)
                fig.add_trace(go.Scatter(
                    x=s.index,
                    y=s.values,
                    mode="lines",
                    name=f"{display_name}（{sign}{final_val:.1f}%）",
                    line=dict(width=2, color=color),
                    hovertemplate="%{x|%Y/%m/%d}<br>%{y:.2f}%<extra>" + display_name + "</extra>",
                ))

            fig.add_hline(y=0, line_dash="dash", line_color="rgba(180,180,180,0.4)", line_width=1)
            fig.update_layout(
                xaxis=dict(
                    title="",
                    tickformat="%y/%m",
                    tickangle=0,
                    dtick="M1" if sel_period in ["6mo","1y"] else None,
                ),
                yaxis=dict(title=t("yaxis_return"), ticksuffix="%", zeroline=False),
                plot_bgcolor="rgba(0,0,0,0)",
                paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=12),
                height=520,
                legend=dict(orientation="h", y=-0.2, x=0, font=dict(size=11)),
                margin=dict(t=30, b=80, l=60, r=20),
                hovermode="x unified",
            )
            st.plotly_chart(fig, use_container_width=True, config=PLOT_CONFIG)

            # ランキングサマリー表
            st.markdown("---")
            st.markdown(t("trend_rank_title_fmt").format(trend_period))
            rank_df = pd.DataFrame([
                {t("rank_col"): i+1, t("theme_col"): tn(theme_n), t("trend_rank_period").format(trend_period): f"{v:+.2f}%"}
                for i, (theme_n, v) in enumerate(sorted_themes)
            ])
            st.dataframe(rank_df.set_index(t("rank_col")), use_container_width=True, height=min(600, len(rank_df)*36+40))

            # CSV出力
            csv_data = []
            for theme_n in all_theme_names:
                if theme_n in trend_data and trend_data[theme_n] is not None:
                    s = trend_data[theme_n]
                    for date, val in s.items():
                        csv_data.append({t("trend_date_col"): date.strftime("%Y-%m-%d"), t("theme_col"): tn(theme_n), t("trend_rate_col"): val})
            if csv_data:
                csv_df = pd.DataFrame(csv_data)
                st.download_button(
                    t("csv_download_all"),
                    csv_df.to_csv(index=False, encoding="utf-8-sig"),
                    f"テーマ騰落推移_{trend_period}_{now}.csv",
                    "text/csv",
                )

# =====================
# ヒートマップ
# =====================
elif pidx == PAGE_HEATMAP:
    st.subheader(t("heatmap_title"))
    st.caption(f"🕐 {_get_now_str()}")

    # --- データ取得: 期間比較ヒートマップ ---
    @st.cache_data(ttl=_get_ttl())
    def fetch_heatmap_data(theme_keys):
        heatmap_periods = {"1W":"5d","1M":"1mo","3M":"3mo","6M":"6mo","1Y":"1y"}
        _themes = get_all_themes()

        def _ticker_hmap(ticker):
            res = {}
            try:
                df = fetch_stock_data(ticker, "2y")
                if len(df) < 2: return res
                for pl, pc in heatmap_periods.items():
                    c = calc_change(get_target_df(df, pc))
                    if c is not None: res[pl] = c
            except: pass
            return res

        heatmap_data = {}
        for theme_name in theme_keys:
            stocks = _themes.get(theme_name, {})
            accum = {pl: [] for pl in heatmap_periods}
            with ThreadPoolExecutor(max_workers=8) as ex:
                futs = {ex.submit(_ticker_hmap, t): t for t in stocks.values()}
                for fut in as_completed(futs):
                    for pl, c in fut.result().items():
                        accum[pl].append(c)
            heatmap_data[theme_name] = {
                pl: round(sum(v)/len(v),2) if v else None
                for pl, v in accum.items()
            }
        return heatmap_data

    # --- データ取得: 月次推移ヒートマップ ---
    @st.cache_data(ttl=1800)
    def fetch_monthly_heatmap(theme_keys):
        """過去12ヶ月の月別騰落率を並列計算"""
        _themes = get_all_themes()
        today = pd.Timestamp.now()
        months = []
        for i in range(11, -1, -1):
            d = today - pd.DateOffset(months=i)
            months.append(d.strftime("%Y/%m"))

        def _calc_ticker_monthly(ticker):
            """1銘柄の全月分を一括計算"""
            result = {}
            try:
                df = fetch_stock_data(ticker, "2y")
                if df is None or len(df) < 2: return result
                for m_label in months:
                    year, month = int(m_label[:4]), int(m_label[5:])
                    month_df = df[(df.index.year == year) & (df.index.month == month)]
                    if len(month_df) < 2: continue
                    s, e = month_df["Close"].iloc[0], month_df["Close"].iloc[-1]
                    if s > 0:
                        result[m_label] = round((e - s) / s * 100, 2)
            except: pass
            return result

        monthly_data = {}
        for theme_name in theme_keys:
            stocks = _themes.get(theme_name, {})
            monthly_data[theme_name] = {m: [] for m in months}
            # 銘柄ごとに並列取得
            with ThreadPoolExecutor(max_workers=8) as ex:
                futs = {ex.submit(_calc_ticker_monthly, t): t for t in stocks.values()}
                for fut in as_completed(futs):
                    res = fut.result()
                    for m_label, chg in res.items():
                        monthly_data[theme_name][m_label].append(chg)
            # 平均を計算
            monthly_data[theme_name] = {
                m: round(sum(v)/len(v), 2) if v else None
                for m, v in monthly_data[theme_name].items()
            }
        return monthly_data, months

    theme_keys = tuple(themes.keys())

    # タブ切り替え
    tab_heat, tab_monthly, tab_line = st.tabs([
        "🟥 期間別ヒートマップ",
        "📅 月次推移ヒートマップ",
        "📈 折れ線グラフ",
    ])

    # ============================================================
    # タブ1: 期間別ヒートマップ（1W/1M/3M/6M/1Y）
    # ============================================================
    with tab_heat:
        with st.spinner(t("loading")):
            heatmap_data = fetch_heatmap_data(theme_keys)
        short_labels = ["1W","1M","3M","6M","1Y"]
        df_heat = pd.DataFrame(heatmap_data).T[short_labels]
        all_vals = [v for row in df_heat.values.tolist() for v in row if v is not None]
        abs_max = max(abs(min(all_vals)), abs(max(all_vals))) if all_vals else 10
        n_themes = len(df_heat)

        st.markdown(t("heatmap_legend"))

        z = df_heat.values.tolist()
        cell_text = [[f"{v:.1f}%" if v is not None else "" for v in row] for row in z]
        hover_text = [
            [f"{df_heat.index[i]}<br>{short_labels[j]}: {z[i][j]}%" if z[i][j] is not None else "N/A"
             for j in range(len(short_labels))]
            for i in range(n_themes)
        ]
        fig_h1 = go.Figure(go.Heatmap(
            z=z, x=short_labels, y=df_heat.index.tolist(),
            text=cell_text,
            hovertext=hover_text,
            hovertemplate="%{hovertext}<extra></extra>",
            texttemplate="%{text}",
            textfont=dict(size=9, color="white"),
            colorscale=[[0,"#0d6e2a"],[0.35,"#52c76a"],[0.5,"#23263a"],[0.65,"#e8845a"],[1,"#e8192c"]],
            zmid=0, zmin=-abs_max, zmax=abs_max,
            showscale=True,
            colorbar=dict(title=dict(text="%",side="right"),thickness=12,ticksuffix="%",x=1.01),
            xgap=3, ygap=3,
        ))
        fig_h1.update_layout(
            xaxis=dict(side="top", tickfont=dict(size=12), tickangle=0, fixedrange=True),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10), fixedrange=True),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=max(420, n_themes * 26 + 60),
            margin=dict(t=45, b=10, l=155, r=60),
        )
        st.plotly_chart(fig_h1, use_container_width=True, config={"displayModeBar":False,"staticPlot":False})
        st.download_button(t("download_heatmap_csv"), df_heat.to_csv(encoding="utf-8-sig"), f"heatmap_{now}.csv", "text/csv")

    # ============================================================
    # タブ2: 月次推移ヒートマップ（過去12ヶ月・月単位）
    # ============================================================
    with tab_monthly:
        st.markdown(t("monthly_heatmap_title"))
        st.caption(t("monthly_cap"))
        with st.spinner(t("loading_monthly")):
            monthly_data, month_labels = fetch_monthly_heatmap(theme_keys)

        df_monthly = pd.DataFrame(monthly_data).T[month_labels]
        mn_vals = [v for row in df_monthly.values.tolist() for v in row if v is not None]
        mn_abs_max = max(abs(min(mn_vals)), abs(max(mn_vals))) if mn_vals else 10
        n_t = len(df_monthly)

        zm = df_monthly.values.tolist()
        # セル内テキスト：短く
        cell_m = [[f"{v:.1f}%" if v is not None else "" for v in row] for row in zm]
        # ホバーテキスト
        hover_m = [
            [f"{df_monthly.index[i]}<br>{month_labels[j]}: {zm[i][j]}%" if zm[i][j] is not None else "N/A"
             for j in range(len(month_labels))]
            for i in range(n_t)
        ]
        # 月ラベルを短縮（MM月のみ表示）
        short_months = [m[5:] + "月" for m in month_labels]  # "01月"〜"12月"

        fig_m = go.Figure(go.Heatmap(
            z=zm,
            x=short_months,
            y=df_monthly.index.tolist(),
            text=cell_m,
            hovertext=hover_m,
            hovertemplate="%{hovertext}<extra></extra>",
            texttemplate="%{text}",
            textfont=dict(size=8, color="white"),
            colorscale=[[0,"#0d6e2a"],[0.35,"#52c76a"],[0.5,"#23263a"],[0.65,"#e8845a"],[1,"#e8192c"]],
            zmid=0, zmin=-mn_abs_max, zmax=mn_abs_max,
            showscale=True,
            colorbar=dict(title=dict(text="%",side="right"),thickness=12,ticksuffix="%",x=1.01),
            xgap=2, ygap=2,
        ))
        fig_m.update_layout(
            xaxis=dict(
                side="top",
                tickfont=dict(size=10),
                tickangle=0,
                fixedrange=True,
                title=dict(text=f"← {month_labels[0]}　〜　{month_labels[-1]} →", font=dict(size=10)),
            ),
            yaxis=dict(autorange="reversed", tickfont=dict(size=10), fixedrange=True),
            plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
            font=dict(color="white"),
            height=max(420, n_t * 26 + 70),
            margin=dict(t=55, b=10, l=155, r=60),
        )
        st.plotly_chart(fig_m, use_container_width=True, config={"displayModeBar":False,"staticPlot":False})

        # 月次数値テーブル
        st.markdown(t("monthly_table_title"))
        df_m_disp = df_monthly.copy()
        df_m_disp.columns = short_months
        df_m_disp = df_m_disp.applymap(lambda v: f"+{v:.1f}%" if v and v>0 else f"{v:.1f}%" if v else "N/A")
        st.dataframe(df_m_disp, use_container_width=True, height=min(500, n_t*35+40))
        st.download_button(t("download_monthly_csv"), df_monthly.to_csv(encoding="utf-8-sig"), f"monthly_heatmap_{now}.csv", "text/csv")

    # ============================================================
    # タブ3: 折れ線グラフ（テーマ選択式）
    # ============================================================
    with tab_line:
        with st.spinner(t("loading")):
            heatmap_data2 = fetch_heatmap_data(theme_keys)
        period_cols = ["1W","1M","3M","6M","1Y"]
        df_heat2 = pd.DataFrame(heatmap_data2).T[period_cols]
        all_theme_names = df_heat2.index.tolist()
        sorted_by_1m2 = df_heat2["1M"].sort_values(ascending=False)

        if "hl_preset" not in st.session_state:
            st.session_state["hl_preset"] = sorted_by_1m2.head(5).index.tolist()
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button(t("hl_top5_btn"), key="hl_top5"):
                st.session_state["hl_preset"] = sorted_by_1m2.head(5).index.tolist(); st.rerun()
        with c2:
            if st.button(t("hl_bot5_btn"), key="hl_bot5"):
                st.session_state["hl_preset"] = sorted_by_1m2.tail(5).index.tolist(); st.rerun()
        with c3:
            if st.button(t("hl_all_btn"), key="hl_all"):
                st.session_state["hl_preset"] = all_theme_names; st.rerun()

        selected_line_themes = st.multiselect(
            "表示テーマを選択（複数OK）",
            all_theme_names,
            default=st.session_state["hl_preset"],
        )
        if selected_line_themes:
            color_palette = [
                "#ff4b4b","#4b8bff","#ffd700","#39d353","#ff9900",
                "#cc44ff","#00cccc","#ff69b4","#90ee90","#ff6347",
                "#87ceeb","#dda0dd","#98fb98","#ffa07a","#20b2aa",
                "#f0e68c","#add8e6","#ffb6c1","#7fffd4","#e6e6fa",
            ]
            fig_line = go.Figure()
            for idx, theme_n in enumerate(selected_line_themes):
                if theme_n not in df_heat2.index: continue
                vals = [df_heat2.loc[theme_n, col] for col in period_cols]
                fig_line.add_trace(go.Scatter(
                    x=period_cols, y=vals, mode="lines+markers", name=tn(theme_n),
                    line=dict(color=color_palette[idx % len(color_palette)], width=2),
                    marker=dict(size=7), connectgaps=True,
                ))
            fig_line.add_hline(y=0, line_dash="dash", line_color="#666", line_width=1)
            fig_line.update_layout(
                xaxis=dict(title=t("theme_detail_period"), categoryorder="array", categoryarray=period_cols),
                yaxis=dict(title="騰落率（%）", ticksuffix="%"),
                plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                font=dict(color="white", size=11), height=460,
                legend=dict(orientation="h", x=0, y=-0.22, font=dict(size=10)),
                margin=dict(t=30, b=120, l=60, r=20),
            )
            st.plotly_chart(fig_line, use_container_width=True, config=PLOT_CONFIG)
            df_sel = df_heat2.loc[selected_line_themes].copy()
            df_sel = df_sel.applymap(lambda x: f"🔴 +{x}%" if x and x>0 else f"🟢 {x}%" if x else "N/A")
            st.dataframe(df_sel, use_container_width=True)
        else:
            st.info(t("select_theme_prompt2"))

elif pidx == PAGE_COMPARE:
    st.subheader(t("compare_chart_title"))
    period = period_buttons(key_prefix="comp")
    selected_themes_cmp = st.multiselect("比較するテーマを選択", list(themes.keys()),
                                          default=list(themes.keys())[:2])
    if len(selected_themes_cmp) < 2:
        st.warning(t("compare_warn"))
    else:
        with st.spinner(t("loading")):
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
            xaxis=dict(title=t("xaxis_date"), dtick="M1", tickformat="%y/%m"),
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
elif pidx == PAGE_MACRO:
    st.subheader(t("macro_comp_title"))
    period = period_buttons(key_prefix="macro")
    selected_stock_name = st.selectbox(t("compare_stock_select"), list(all_stocks.keys()))
    selected_ticker = all_stocks[selected_stock_name]
    macro_items = {"日経平均":"^N225","S&P500":"^GSPC","ドル円":"JPY=X","TOPIX(ETF)":"1306.T"}
    colors_macro = {"日経平均":"#ffd700","S&P500":"#4b8bff","ドル円":"#ff9900","TOPIX(ETF)":"#cc44ff"}
    with st.spinner(t("loading")):
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
        xaxis=dict(title=t("xaxis_date"), dtick="M1", tickformat="%y/%m"),
        yaxis=dict(title="累積リターン（%）", ticksuffix="%"),
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=12), height=500,
        legend=dict(orientation="h", y=1.1),
        margin=dict(t=60, b=50, l=70, r=20),
    )
    st.plotly_chart(fig_macro, use_container_width=True, config=PLOT_CONFIG)

# =====================
# 市場別ランキング
# =====================
elif pidx == PAGE_MARKET_RANK:
    st.subheader(t("page_market_rank"))
    st.caption(t("market_rank_cap"))
    period = period_buttons(key_prefix="market")

    for seg_name, seg_stocks in MARKET_SEGMENTS.items():
        with st.expander(f"📌 {seg_name}", expanded=True):
            with st.spinner(t("loading_seg").format(seg_name)):
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
                n_seg = len(seg_results)

                # 上位5件グラフ
                top5 = seg_results[:5]
                bot5 = seg_results[-5:] if n_seg > 5 else []

                col_t, col_b = st.columns(2)
                with col_t:
                    st.markdown(t("top5_stocks"))
                    t_labels = [f"{i+1}位 {r['銘柄']}" for i, r in enumerate(top5)]
                    t_values = [r["騰落率"] for r in top5]
                    t_colors = ["#ff4b4b" if v>=0 else "#39d353" for v in t_values]
                    st.plotly_chart(make_bar_chart(t_labels, t_values, t_colors),
                                    use_container_width=True, config=PLOT_CONFIG)
                with col_b:
                    if bot5:
                        st.markdown(t("bot5_stocks"))
                        b_labels = [f"{n_seg-4+i}位 {r['銘柄']}" for i, r in enumerate(bot5)]
                        b_values = [r["騰落率"] for r in bot5]
                        b_colors = ["#ff4b4b" if v>=0 else "#39d353" for v in b_values]
                        st.plotly_chart(make_bar_chart(b_labels, b_values, b_colors),
                                        use_container_width=True, config=PLOT_CONFIG)

                # 上位5件テーブル
                df_top5 = pd.DataFrame([{
                    t("stock_col"): r["銘柄"], t("price_col"): r["株価"],
                    t("day_change_col"): r["前日比"],
                    t("change_col"): f"🔴 +{r['騰落率']}%" if r["騰落率"]>0 else f"🟢 {r['騰落率']}%",
                    t("trade_val_col"): r["売買代金"],
                } for r in top5]).set_index(t("stock_col"))
                st.dataframe(df_top5, use_container_width=True)

                # 全件展開
                with st.expander(t("show_all_stocks").format(n_seg)):
                    df_all_seg = pd.DataFrame([{
                        t("rank_col"): t("rank_suffix").format(i+1),
                        t("stock_col"): r["銘柄"], t("price_col"): r["株価"],
                        t("day_change_col"): r["前日比"],
                        t("change_col"): f"🔴 +{r['騰落率']}%" if r["騰落率"]>0 else f"🟢 {r['騰落率']}%",
                        t("trade_val_col"): r["売買代金"],
                    } for i, r in enumerate(seg_results)]).set_index(t("rank_col"))
                    st.dataframe(df_all_seg, use_container_width=True)

# =====================
# 銘柄検索
# =====================
# =====================
# お気に入り
# =====================
elif pidx == PAGE_FAVORITES:
    st.subheader(t("fav_title"))
    period = period_buttons(key_prefix="fav")
    if len(st.session_state["favorites"]) == 0:
        st.info(t("fav_add_hint"))
    else:
        with st.spinner(t("loading")):
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
        st.plotly_chart(make_bar_chart(fav_labels, fav_values, fav_colors),
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
        st.download_button(t("fav_csv"), df_fav.to_csv(encoding="utf-8-sig"),
                           f"favorites_{now}.csv", "text/csv")
        for r in fav_results:
            c = "🔴" if r["change"]>0 else "🟢"
            col1, col2, col3 = st.columns([3,1,1])
            with col1: st.write(f"{c} **{r['銘柄']}**  {r['change']}%")
            with col2:
                if st.button(t("fav_remove_btn"), key=f"fd_{r['銘柄']}"):
                    del st.session_state["favorites"][r["銘柄"]]; st.rerun()

# =====================
# テーマ別詳細
# =====================
elif pidx == PAGE_THEME_DETAIL:
    st.subheader(t("page_theme_detail"))
    st.caption(f"🕐 {_get_now_str()}")
    period = period_buttons(key_prefix="theme_detail")

    theme_keys = tuple(themes.keys())
    with st.spinner(t("loading")):
        td_results, td_details, _cache_time_td = fetch_all_theme_data(period, theme_keys)

    # テーマ選択
    theme_name_list = [r["テーマ"] for r in td_results]
    selected_theme = st.selectbox(t("theme_detail_select"), theme_name_list, key="detail_theme_sel")

    result = next((r for r in td_results if r["テーマ"] == selected_theme), None)
    stocks_d = td_details.get(selected_theme, {})

    if result and stocks_d:
        c_val = result["平均騰落率(%)"]
        v_val = result["出来高増減(%)"]
        col_h1, col_h2, col_h3 = st.columns(3)
        col_h1.metric("平均騰落率", f"{'🔴 +' if c_val>0 else '🟢 '}{c_val}%")
        col_h2.metric("出来高増減", f"{'📈 +' if v_val>0 else '📉 '}{v_val}%")
        col_h3.metric("銘柄数", f"{len(stocks_d)}銘柄")

        # 個別銘柄バーチャート
        theme_s_map = themes.get(selected_theme, {})
        s_labels = [
            f"{s}({theme_s_map.get(s,'').replace('.T','')})" if theme_s_map.get(s) else s
            for s in stocks_d.keys()
        ]
        s_values = [stocks_d[s]["change"] for s in stocks_d.keys()]
        s_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in s_values]
        s_ranks  = [str(i+1) for i in range(len(s_labels))]
        # 騰落率順に並び替え
        sorted_idx = sorted(range(len(s_values)), key=lambda i: s_values[i], reverse=True)
        s_labels  = [s_labels[i]  for i in sorted_idx]
        s_values  = [s_values[i]  for i in sorted_idx]
        s_colors  = [s_colors[i]  for i in sorted_idx]
        chart_h_d = max(200, len(s_labels) * 30)
        st.plotly_chart(make_bar_chart(s_labels, s_values, s_colors,
                                       height=chart_h_d, rank_labels=s_ranks),
                        use_container_width=True, config=PLOT_CONFIG)

        # 出来高・売買代金ランキング
        col_r1, col_r2 = st.columns(2)
        with col_r1:
            st.markdown(t("vol_individual"))
            vol_rank = sorted(stocks_d.items(), key=lambda x: x[1]["volume"], reverse=True)
            vr_df = pd.DataFrame([
                {"順位": f"{i+1}位", "銘柄": k, "出来高": f"{v['volume']:,}"}
                for i, (k, v) in enumerate(vol_rank)
            ]).set_index(t("rank_col"))
            st.dataframe(vr_df, use_container_width=True)
        with col_r2:
            st.markdown(t("tv_individual"))
            tv_rank = sorted(stocks_d.items(), key=lambda x: x[1]["trade_value"], reverse=True)
            tvr_df = pd.DataFrame([
                {"順位": f"{i+1}位", "銘柄": k, "売買代金": format_large_number(v["trade_value"])}
                for i, (k, v) in enumerate(tv_rank)
            ]).set_index(t("rank_col"))
            st.dataframe(tvr_df, use_container_width=True)

        # 銘柄詳細テーブル
        st.markdown("---")
        st.markdown(t("stock_detail_table"))
        stock_table = []
        for sn, d in stocks_d.items():
            rsi = d.get("rsi")
            rsi_alert = "⚠️買" if rsi and rsi>70 else "⚠️売" if rsi and rsi<30 else "✅"
            day_c = d.get("day_change")
            ticker_raw = theme_s_map.get(sn, "")
            code = ticker_raw.replace(".T","") if ticker_raw else ""
            stock_table.append({
                "銘柄": sn, "コード": code,
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
        st.download_button(f"📥 {selected_theme} CSV",
                           df_stock.to_csv(encoding="utf-8-sig"),
                           f"{selected_theme}_{now}.csv", "text/csv")

        # お気に入り登録
        st.markdown("---")
        st.markdown(t("fav_section"))
        for sn, d in stocks_d.items():
            c_icon = "🔴" if d["change"]>0 else "🟢"
            is_fav = sn in st.session_state["favorites"]
            col1, col2 = st.columns([4, 1])
            with col1:
                st.write(f"{c_icon} **{sn}**　{d['change']}%")
            with col2:
                if is_fav:
                    if st.button(t("fav_remove_btn"), key=f"fav_td_{selected_theme}_{sn}"):
                        del st.session_state["favorites"][sn]; st.rerun()
                else:
                    if st.button(t("fav_add_btn"), key=f"fav_td_{selected_theme}_{sn}"):
                        st.session_state["favorites"][sn] = d["ticker"]; st.rerun()
    else:
        st.info(t("no_theme_data"))

# =====================
# お知らせ
# =====================
elif pidx == PAGE_NEWS:
    st.subheader(t("page_news"))
    st.caption(t("news_caption"))

    notices = [
        {
            "date": "2025-03-06",
            "tag": "🆕 機能追加",
            "title": "日経225全225銘柄・TOPIX100主要銘柄を追加",
            "body": "市場別ランキングページに日経225の全225銘柄とTOPIX100の主要銘柄（Core30・Large70）を追加しました。より網羅的な市場動向の把握が可能になりました。",
        },
        {
            "date": "2025-03-06",
            "tag": "🆕 機能追加",
            "title": "「騰落モメンタム」ページを新設",
            "body": "テーマの騰落率・先週比・先月比を一覧表示し、加速・失速・転換を自動判定する「📡 騰落モメンタム」ページを追加しました。",
        },
        {
            "date": "2025-03-06",
            "tag": "🆕 機能追加",
            "title": "「資金フロー」ページを新設",
            "body": "資金流入TOP10・流出TOP10および全テーマの騰落率一覧を表示する「💹 資金フロー」ページを追加しました。",
        },
        {
            "date": "2025-03-05",
            "tag": "✅ 改善",
            "title": "騰落推移をGoogle Spreadsheet不要に変更",
            "body": "騰落推移の記録をGoogle Spreadsheetからyfinanceの日次データを直接取得する方式に変更しました。アプリを開くだけで過去1年分の推移グラフが表示されます。",
        },
        {
            "date": "2025-03-05",
            "tag": "✅ 改善",
            "title": "「テーマ別詳細」を独立ページに移動",
            "body": "これまでテーマ一覧ページの下部にあったテーマ別詳細を「🔍 テーマ別詳細」として独立ページに移動しました。テーマをセレクトボックスで選択して確認できます。",
        },
        {
            "date": "2025-03-04",
            "tag": "🆕 機能追加",
            "title": "並列データ取得で高速化（約10倍）",
            "body": "ThreadPoolExecutorを使った並列処理により、データ取得時間を約75秒から7〜8秒に短縮しました。",
        },
        {
            "date": "2025-03-03",
            "tag": "🆕 機能追加",
            "title": "12ヶ月ヒートマップを追加",
            "body": "ヒートマップページに過去12ヶ月の月別騰落率ヒートマップを追加。連続上昇・連続下落テーマを一目で把握できます。",
        },
    ]

    tag_colors = {
        "🆕 機能追加": "#1a3a5c",
        "✅ 改善": "#1a4a2a",
        "🐛 修正": "#4a2a1a",
        "⚠️ 重要": "#4a1a1a",
    }

    for n in notices:
        tag_color = tag_colors.get(n["tag"], "#1a2a3a")
        st.markdown(f"""
<div style="border:1px solid #2a2a3a;border-radius:10px;padding:14px 16px;margin-bottom:12px;background:#0d1020;">
  <div style="display:flex;align-items:center;gap:10px;margin-bottom:6px;flex-wrap:wrap;">
    <span style="background:{tag_color};color:white;font-size:11px;padding:2px 8px;border-radius:4px;white-space:nowrap;">{n["tag"]}</span>
    <span style="font-size:12px;color:#4a5570;">{n["date"]}</span>
  </div>
  <div style="font-weight:700;font-size:14px;margin-bottom:4px;">{n["title"]}</div>
  <div style="font-size:12px;color:#8090a8;line-height:1.6;">{n["body"]}</div>
</div>
""", unsafe_allow_html=True)

# =====================
# カスタムテーマ
# =====================
elif pidx == PAGE_CUSTOM:
    st.subheader(t("custom_edit_title"))
    st.caption(t("custom_edit_cap"))

    tab1, tab2 = st.tabs(["➕ 新規作成", "✏️ 編集・削除"])

    with tab1:

        # ── セッションステート初期化 ──
        if "new_stocks" not in st.session_state:
            st.session_state["new_stocks"] = []
        if "ct_search_result" not in st.session_state:
            st.session_state["ct_search_result"] = None  # {"name":..,"ticker":..,"price":..,...}
        if "ct_search_query" not in st.session_state:
            st.session_state["ct_search_query"] = ""

        st.markdown(t("custom_theme_name_hdr"))
        new_theme_name = st.text_input("テーマ名", placeholder="例：マイ注目銘柄、AIテーマ...",
                                        label_visibility="collapsed")

        st.markdown("---")
        st.markdown(t("custom_search_hdr"))
        st.caption(t("custom_search_cap"))

        # 検索バー
        search_col, btn_col = st.columns([4, 1])
        with search_col:
            ct_query = st.text_input(
                "銘柄名 or 証券コード",
                placeholder="銘柄名 or 証券コード（例：7203 / トヨタ）",
                label_visibility="collapsed",
                key="ct_search_input",
            )
        with btn_col:
            st.write("")
            do_search = st.button(t("custom_search_btn"), key="ct_search_btn", use_container_width=True)

        # 検索実行
        if do_search and ct_query:
            ct_query_stripped = ct_query.strip()
            # 証券コード4桁の場合は .T を補完
            if ct_query_stripped.isdigit() and len(ct_query_stripped) == 4:
                search_ticker = ct_query_stripped + ".T"
                # all_stocksからticker一致を探す
                matched_name = next(
                    (name for name, t in all_stocks.items() if t == search_ticker), None
                )
                if matched_name:
                    search_targets = {matched_name: search_ticker}
                else:
                    # DBにない場合もティッカーとして直接取得を試みる
                    search_targets = {ct_query_stripped: search_ticker}
            else:
                # 銘柄名部分一致
                search_targets = {
                    name: ticker for name, ticker in all_stocks.items()
                    if ct_query_stripped in name
                }

            if not search_targets:
                st.warning(t("custom_no_result"))
                st.session_state["ct_search_result"] = None
            else:
                # 最初にヒットした銘柄のデータを取得
                found_name, found_ticker = next(iter(search_targets.items()))
                with st.spinner(t("loading_stock").format(found_name)):
                    try:
                        df_ct = fetch_stock_data(found_ticker, "2y")
                        if len(df_ct) >= 2:
                            target_ct = get_target_df(df_ct, "1mo")
                            change_ct = calc_change(target_ct)
                            price_ct = int(df_ct["Close"].iloc[-1])
                            day_c_ct = round(
                                (df_ct["Close"].iloc[-1] - df_ct["Close"].iloc[-2])
                                / df_ct["Close"].iloc[-2] * 100, 2
                            )
                            rsi_ct = round(calc_rsi(df_ct["Close"]).iloc[-1], 1) if len(df_ct) >= 15 else None
                            code_ct = found_ticker.replace(".T", "")
                            st.session_state["ct_search_result"] = {
                                "name": found_name,
                                "ticker": found_ticker,
                                "code": code_ct,
                                "price": price_ct,
                                "change": change_ct,
                                "day_change": day_c_ct,
                                "rsi": rsi_ct,
                                "hit_count": len(search_targets),
                                "all_hits": list(search_targets.items()),
                            }
                        else:
                            st.warning(t("no_data_short"))
                            st.session_state["ct_search_result"] = None
                    except Exception as e:
                        st.error(t("fetch_error").format(e))
                        st.session_state["ct_search_result"] = None

        # ── 検索結果の表示 ──
        res = st.session_state.get("ct_search_result")
        if res:
            st.markdown("---")
            st.markdown(t("stock_detail_hdr"))

            # 複数ヒット時は選択できるように
            if res["hit_count"] > 1:
                hit_names = [n for n, _ in res["all_hits"]]
                sel_name = st.selectbox(t("multi_hit_select"),
                                         hit_names, key="ct_hit_select")
                if sel_name != res["name"]:
                    # 選択が変わったら再取得
                    sel_ticker = dict(res["all_hits"])[sel_name]
                    with st.spinner(t("loading_stock").format(sel_name)):
                        try:
                            df_sel = fetch_stock_data(sel_ticker, "2y")
                            if len(df_sel) >= 2:
                                t_sel = get_target_df(df_sel, "1mo")
                                res = {
                                    "name": sel_name,
                                    "ticker": sel_ticker,
                                    "code": sel_ticker.replace(".T",""),
                                    "price": int(df_sel["Close"].iloc[-1]),
                                    "change": calc_change(t_sel),
                                    "day_change": round(
                                        (df_sel["Close"].iloc[-1]-df_sel["Close"].iloc[-2])
                                        /df_sel["Close"].iloc[-2]*100, 2),
                                    "rsi": round(calc_rsi(df_sel["Close"]).iloc[-1],1) if len(df_sel)>=15 else None,
                                    "hit_count": res["hit_count"],
                                    "all_hits": res["all_hits"],
                                }
                                st.session_state["ct_search_result"] = res
                        except:
                            pass

            # 銘柄詳細カード
            d_col1, d_col2, d_col3, d_col4 = st.columns(4)
            d_col1.metric("銘柄名", res["name"])
            d_col2.metric("証券コード", res["code"])
            d_col3.metric("株価", f"¥{res['price']:,}")
            sign = "+" if res["change"] and res["change"] >= 0 else ""
            d_col4.metric("騰落率(1ヶ月)", f"{sign}{res['change']}%" if res["change"] else "N/A")

            d_col5, d_col6, d_col7, _ = st.columns(4)
            dc = res["day_change"]
            d_col5.metric("前日比", f"{'+'if dc and dc>=0 else ''}{dc}%" if dc else "N/A")
            d_col6.metric("RSI", f"{res['rsi']}" if res["rsi"] else "N/A")
            d_col7.metric("ティッカー", res["ticker"])

            # 追加ボタン
            already = any(s["ticker"] == res["ticker"]
                          for s in st.session_state["new_stocks"])
            if already:
                st.info(t('already_added').format(res['name']))
            else:
                if st.button(t('add_to_theme_btn').format(res['name']),
                              type="primary", key="ct_add_btn"):
                    st.session_state["new_stocks"].append({
                        "name": res["name"],
                        "ticker": res["ticker"],
                    })
                    st.success(f"「{res['name']}」を追加しました！")
                    st.session_state["ct_search_result"] = None
                    st.rerun()

        # ── 追加済み銘柄リスト ──
        if st.session_state["new_stocks"]:
            st.markdown("---")
            st.markdown(t('added_stocks_hdr').format(len(st.session_state['new_stocks'])))
            for i, stock in enumerate(st.session_state["new_stocks"]):
                r_col1, r_col2, r_col3 = st.columns([3, 2, 1])
                with r_col1:
                    st.write(f"**{stock['name']}**")
                with r_col2:
                    st.caption(stock["ticker"])
                with r_col3:
                    if st.button("🗑️", key=f"ns_del_{i}",
                                  help=f"{stock['name']}を削除"):
                        st.session_state["new_stocks"].pop(i)
                        st.rerun()

        st.markdown("---")
        # ── テーマ保存 ──
        if st.button(t("save_theme_btn"), type="primary", key="ct_save_btn"):
            if not new_theme_name:
                st.error(t("err_no_name"))
            elif new_theme_name in DEFAULT_THEMES:
                st.error(t("err_dup_name"))
            elif not st.session_state["new_stocks"]:
                st.error(t("err_no_stocks"))
            else:
                valid_stocks = {s["name"]: s["ticker"]
                                for s in st.session_state["new_stocks"]
                                if s["name"] and s["ticker"]}
                st.session_state["custom_themes"][new_theme_name] = valid_stocks
                st.session_state["new_stocks"] = []
                st.session_state["ct_search_result"] = None
                st.success(f"「{new_theme_name}」を保存しました！テーマ一覧に反映されます。")
                st.rerun()

    with tab2:
        if not st.session_state["custom_themes"]:
            st.info(t("custom_no_themes"))
        else:
            st.markdown(t("custom_existing_hdr"))
            for ct_name, ct_stocks in list(st.session_state["custom_themes"].items()):
                with st.expander(t("custom_theme_item").format(ct_name, len(ct_stocks))):
                    st.write(t("stock_list_hdr"))
                    for sn, ticker in ct_stocks.items():
                        st.write(f"・{sn}（{ticker}）")

                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        if st.button(t("edit_btn"), key=f"edit_{ct_name}"):
                            st.session_state["editing_theme"] = ct_name
                            st.session_state["new_stocks"] = [{"name":k,"ticker":v} for k,v in ct_stocks.items()]
                            st.info(t("edit_hint").format(ct_name))
                    with col_edit2:
                        if st.button(t("delete_btn"), key=f"del_{ct_name}"):
                            del st.session_state["custom_themes"][ct_name]
                            st.success(f"「{ct_name}」を削除しました")
                            st.rerun()


# =====================
# 使い方・Q&A
# =====================
elif pidx == PAGE_HOWTO:
    st.subheader(t("page_howto"))

    _lang = st.session_state.get("app_language", "ja")
    _intro_title = I18N["howto_intro_title"][_lang]
    _intro_body  = I18N["howto_intro_body"][_lang]

    st.markdown(f"""
<div style="background:#0d1020;border:1px solid #1a1e30;border-radius:12px;padding:20px 22px;margin-bottom:16px;">
  <div style="font-size:16px;font-weight:700;margin-bottom:12px;color:#e8eaf0;">{_intro_title}</div>
  <div style="font-size:13px;color:#8090a8;line-height:1.9;">{_intro_body}</div>
</div>
""", unsafe_allow_html=True)

    # 使い方
    st.markdown(t("howto_section_title"))
    _guide_items = I18N["guide_items"][_lang]
    for icon_title, desc in _guide_items:
        st.markdown(f"""
<div style="border-left:3px solid #ff4b4b;padding:8px 14px;margin-bottom:10px;background:#0d1020;border-radius:0 8px 8px 0;">
  <div style="font-size:13px;font-weight:700;color:#e8eaf0;margin-bottom:3px;">{icon_title}</div>
  <div style="font-size:12px;color:#8090a8;line-height:1.7;">{desc}</div>
</div>
""", unsafe_allow_html=True)

    # Q&A
    st.markdown("---")
    st.markdown(t("faq_title"))
    _qa_items = I18N["qa_items"][_lang]
    _q_prefix = "Q. " if _lang == "ja" else "Q. "
    _a_prefix = "**A.** "
    for q, a in _qa_items:
        with st.expander(f"{_q_prefix}{q}"):
            st.markdown(f"{_a_prefix}{a}")

    st.markdown("---")
    st.markdown(
        f"<div style='font-size:11px;color:#3a4560;text-align:center;padding:8px;'>"
        f"{t('howto_feedback')}"
        f"</div>",
        unsafe_allow_html=True
    )

# =====================
# 免責事項
# =====================
elif pidx == PAGE_DISCLAIMER:
    _lang = st.session_state.get("app_language", "ja")
    _title_suffix = "・利用規約" if _lang == "ja" else " / Terms of Use"
    st.subheader(t("page_disclaimer") + _title_suffix)

    _sections = I18N["disclaimer_sections"][_lang]
    for title, body in _sections:
        st.markdown(f"""
<div style="border:1px solid #1a1e30;border-radius:10px;padding:16px 18px;margin-bottom:14px;background:#0d1020;">
  <div style="font-size:14px;font-weight:700;color:#e8eaf0;margin-bottom:8px;">{title}</div>
  <div style="font-size:12px;color:#8090a8;line-height:1.9;white-space:pre-line;">{body.strip()}</div>
</div>
""", unsafe_allow_html=True)

    _footer_text = I18N["disclaimer_footer"][_lang]
    st.markdown(
        f"<div style='text-align:center;font-size:11px;color:#3a4560;margin-top:24px;padding:12px;"
        f"border-top:1px solid #1a1e30;'>{_footer_text}</div>",
        unsafe_allow_html=True
    )


# =====================
# 設定ページ
# =====================
elif pidx == PAGE_SETTINGS:
    lang = st.session_state.get("app_language", "ja")
    ct   = st.session_state.get("color_theme", "dark")
    _c   = COLOR_THEMES.get(ct, COLOR_THEMES["dark"])

    st.subheader(t("settings_title"))
    st.markdown("---")

    # ─── About ───
    st.markdown(f"### {t('settings_about_title')}")
    st.markdown(t("settings_about_body"))
    st.markdown("---")

    # ─── 言語設定 ───
    st.markdown(f"### {t('settings_lang_title')}")
    st.markdown(t("settings_lang_desc"))

    lang_options = {"🇯🇵  日本語 (Japanese)": "ja", "🇺🇸  English": "en"}
    lang_labels   = list(lang_options.keys())
    lang_values   = list(lang_options.values())
    current_lang_label = lang_labels[lang_values.index(lang)] if lang in lang_values else lang_labels[0]

    new_lang_label = st.radio(
        "Language",
        lang_labels,
        index=lang_labels.index(current_lang_label),
        horizontal=True,
        label_visibility="collapsed",
        key="settings_lang_radio",
    )
    new_lang = lang_options[new_lang_label]

    st.markdown("---")

    # ─── カラーテーマ ───
    st.markdown(f"### {t('settings_theme_title')}")
    st.markdown(t("settings_theme_desc"))

    _lkey = "label_en" if lang == "en" else "label"
    theme_options = {
        f"🌑  {COLOR_THEMES['dark'][_lkey]}":  "dark",
        f"☀️  {COLOR_THEMES['light'][_lkey]}": "light",
        f"🌊  {COLOR_THEMES['navy'][_lkey]}":  "navy",
    }
    theme_labels  = list(theme_options.keys())
    theme_values  = list(theme_options.values())
    current_theme_label = theme_labels[theme_values.index(ct)] if ct in theme_values else theme_labels[0]

    new_theme_label = st.radio(
        "Color Theme",
        theme_labels,
        index=theme_labels.index(current_theme_label),
        horizontal=True,
        label_visibility="collapsed",
        key="settings_theme_radio",
    )
    new_theme = theme_options[new_theme_label]

    _pc = COLOR_THEMES[new_theme]
    _pc_label = _pc['label_en'] if lang == "en" else _pc['label']
    _preview_word = "Preview" if lang == "en" else "プレビュー / Preview"
    st.markdown(f"""
<div style="margin-top:12px;padding:18px 22px;border-radius:10px;
  background:{_pc['bg_card']};border:1px solid {_pc['border']};
  max-width:400px;">
  <div style="font-size:13px;font-weight:700;color:{_pc['text_primary']};margin-bottom:6px;">
    {_pc_label} — {_preview_word}
  </div>
  <div style="font-size:12px;color:{_pc['text_secondary']};margin-bottom:4px;">
    StockWaveJP · 株式波動 · 日本株テーマ分析
  </div>
  <div style="font-size:11px;color:{_pc['text_muted']};">
    © 2026 StockWaveJP  |  For informational purposes only.
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ─── 適用ボタン ───
    if st.button(t("settings_apply"), type="primary", use_container_width=False):
        changed = False
        if new_lang != lang:
            st.session_state["app_language"] = new_lang
            changed = True
        if new_theme != ct:
            st.session_state["color_theme"] = new_theme
            changed = True
        if changed:
            st.success(t("settings_saved"))
            st.rerun()
        else:
            if lang == "ja":
                st.info(t("settings_no_change"))
            else:
                st.info("No changes were made.")

    st.markdown("---")
    # 現在の設定表示
    st.markdown(f"""
<div style="font-size:11px;color:{_c['text_muted']};line-height:2;">
{'現在の設定' if lang=='ja' else 'Current Settings'} ：
言語 / Language = <b style="color:{_c['text_secondary']}">{'日本語' if lang=='ja' else 'English'}</b>　
テーマ / Theme = <b style="color:{_c['text_secondary']}">{_c['label']} / {_c['label_en']}</b>
</div>
""", unsafe_allow_html=True)

# ── メインエリア フッター（全ページ共通・分岐の外側） ──
st.markdown("---")
st.markdown(
    f"<div style='text-align:center;font-size:11px;color:#8090a8;padding:6px 0 4px;'>"
    f"{t('footer')}"
    f"</div>",
    unsafe_allow_html=True
)
