import streamlit as st
import streamlit.components.v1 as _stc
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed

# ファビコン（ロゴPNG）を読み込む
import os as _os
from PIL import Image as _PILImage
_favicon_path = _os.path.join(_os.path.dirname(__file__), "favicon.png")
_favicon = _PILImage.open(_favicon_path) if _os.path.exists(_favicon_path) else "🌊"

st.set_page_config(
    page_title="StockWaveJP",
    page_icon=_favicon,
    layout="wide",
    initial_sidebar_state="auto",
    menu_items={}
)

# ── StockWaveJP ロゴ（Streamlit標準ヘッダーバーにCSSで埋め込む） ──
# position:fixedはiframe内では機能しないため、
# Streamlitのheaderバー内にロゴをCSSで表示する方式を採用
st.markdown("""
<link href="https://fonts.googleapis.com/css2?family=Bebas+Neue&display=swap" rel="stylesheet">
<style>
/* Streamlitデフォルトヘッダーバーを活用してロゴを表示 */
header[data-testid="stHeader"] {
    background: #0a0c14 !important;
    border-bottom: 1px solid #1a1e30 !important;
    height: 48px !important;
    display: flex !important;
    visibility: visible !important;
}
/* ヘッダー内にロゴをCSSで挿入 */
header[data-testid="stHeader"]::before {
    content: "StockWaveJP";
    font-family: 'Arial Black', sans-serif;
    font-size: 22px;
    font-weight: 900;
    letter-spacing: 0.02em;
    color: #ffffff;
    position: absolute;
    left: 16px;
    top: 50%;
    transform: translateY(-50%);
}
/* ヘッダー内ツールバーを右端に寄せる */
header[data-testid="stHeader"] > div {
    justify-content: flex-end !important;
}
/* ヘッダー分のトップ余白確保 */
.block-container {
    margin-top: 0 !important;
}
</style>
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

# ══════════════════════════════════════════════
# 画面幅の自動判定（JS）＋ 手動切り替えボタン
# ══════════════════════════════════════════════

# JSで画面幅を取得してクエリパラメータ経由でセッションに渡す
_stc.html("""
<script>
(function() {
    const w = window.innerWidth;
    const isMobile = w <= 640;
    // Streamlitのpostmessageで幅をセッションに渡すのは不可なため
    // URLパラメータに埋め込む方式を使用
    const url = new URL(window.parent.location.href);
    const current = url.searchParams.get("_mobile");
    const newVal  = isMobile ? "1" : "0";
    if (current !== newVal) {
        url.searchParams.set("_mobile", newVal);
        window.parent.history.replaceState({}, "", url.toString());
    }
})();
</script>
""", height=0)

# URLパラメータから画面幅判定結果を取得
_qp = st.query_params
_auto_mobile = _qp.get("_mobile", "0") == "1"

# view_modeに応じてis_mobileを決定
_vm = st.session_state.get("view_mode", "auto")
if _vm == "mobile":
    st.session_state["is_mobile"] = True
elif _vm == "desktop":
    st.session_state["is_mobile"] = False
else:  # auto
    st.session_state["is_mobile"] = _auto_mobile

_is_mobile = st.session_state["is_mobile"]

# ── 手動切り替えトグル（右上：モバイル ／ PC） ──
st.markdown("""
<style>
/* トグルをコンパクトに横並び */
div[data-testid="stHorizontalBlock"]:has(div.toggle-row) { gap: 0 !important; }
/* トグル行の上下余白をゼロに */
div[data-testid="stHorizontalBlock"]:has(.toggle-wrap) {
    margin-top: 0 !important;
    margin-bottom: 0 !important;
    padding-top: 0 !important;
    padding-bottom: 0 !important;
}
.toggle-wrap { margin: 0 !important; padding: 0 !important; }
.toggle-wrap div[data-testid="stRadio"] > label { display: none; }
.toggle-wrap div[data-testid="stRadio"] [data-baseweb="radio-group"] {
    display: flex !important;
    flex-direction: row !important;
    gap: 0 !important;
    border: 1px solid #3a3e50;
    border-radius: 8px;
    overflow: hidden;
    width: fit-content;
}
.toggle-wrap div[data-testid="stRadio"] [data-baseweb="radio-group"] label {
    margin: 0 !important;
    padding: 5px 14px !important;
    font-size: 12px !important;
    cursor: pointer;
    background: #1a1e2e;
    color: #6a7080;
    border-right: 1px solid #3a3e50;
    white-space: nowrap;
}
.toggle-wrap div[data-testid="stRadio"] [data-baseweb="radio-group"] label:last-child {
    border-right: none;
}
.toggle-wrap div[data-testid="stRadio"] [aria-checked="true"] + div,
.toggle-wrap div[data-testid="stRadio"] input:checked + div {
    background: #e63030 !important;
}
</style>
""", unsafe_allow_html=True)



# ── スマホ時に追加で適用するCSS ──
if _is_mobile:
    st.markdown("""
<style>
/* スマホ強制適用（自動判定またはボタン切り替え時） */
h1 { font-size: 1.3em !important; line-height: 1.3 !important; }
h2 { font-size: 1.1em !important; line-height: 1.3 !important; }
h3 { font-size: 1.0em !important; }
.stMarkdown p, .stMarkdown li {
    font-size: 0.88em !important;
    line-height: 1.6 !important;
    word-break: break-word !important;
}
[data-testid="stCaptionContainer"] * { font-size: 0.78em !important; }
[data-testid="stMetricValue"] { font-size: 1.1em !important; }
[data-testid="stMetricLabel"] { font-size: 0.78em !important; }
div.stButton > button {
    font-size: 0.85em !important;
    height: 2.8em !important;
    padding: 0 8px !important;
}
div[data-testid="stSelectbox"] > div { font-size: 0.88em !important; }
[data-testid="stDataFrame"] { font-size: 0.78em !important; }
.stTabs [data-baseweb="tab"] {
    font-size: 0.82em !important;
    padding: 6px 8px !important;
}
[data-testid="stExpander"] summary { font-size: 0.88em !important; }
.block-container {
    padding-left: 0.8rem !important;
    padding-right: 0.8rem !important;
}
</style>
""", unsafe_allow_html=True)

_ct = st.session_state.get("color_theme", "dark")
_c  = COLOR_THEMES.get(_ct, COLOR_THEMES["dark"])

st.markdown(f"""
<style>
/* ── カラーテーマ: {_ct} ── */

/* 固定ヘッダーの背景をカラーテーマに合わせる */
#swjp-fixed-header {{
    background: {_c['bg_sidebar']} !important;
    border-bottom: 1px solid {_c['border']} !important;
}}

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

/* ── メインエリアのテキスト全般（Plotly SVG要素・DataFrame iframeは除外） ── */
.stMarkdown, .stMarkdown p, .stMarkdown li, .stMarkdown span {{
    color: {_c['text_primary']} !important;
}}
h1, h2, h3, h4, h5, h6 {{
    color: {_c['text_primary']} !important;
}}
[data-testid="stMarkdownContainer"] p,
[data-testid="stMarkdownContainer"] li,
[data-testid="stMarkdownContainer"] span,
[data-testid="stMarkdownContainer"] a {{
    color: {_c['text_primary']} !important;
}}
[data-testid="stText"] {{
    color: {_c['text_primary']} !important;
}}
[data-testid="stCaptionContainer"] * {{
    color: {_c['text_secondary']} !important;
}}

/* ── メトリクス ── */
[data-testid="metric-container"] [data-testid="stMetricValue"],
[data-testid="metric-container"] [data-testid="stMetricLabel"],
[data-testid="metric-container"] [data-testid="stMetricDelta"] {{
    color: {_c['text_primary']} !important;
}}
/* ── キャプション ── */
.stCaption {{
    color: {_c['text_secondary']} !important;
}}

/* ── ライトテーマ専用: StreamlitのCSS変数を上書きして全テキストを黒に ── */
{"" if _ct != "light" else f"""
:root {{
    --text-color: {_c['text_primary']} !important;
    --background-color: {_c['bg_main']} !important;
    --secondary-background-color: {_c['bg_card']} !important;
    --font: sans-serif;
}}
.stApp, .main, [data-testid="stAppViewContainer"] {{
    color: {_c['text_primary']} !important;
    background-color: {_c['bg_main']} !important;
}}
/* widget ラベル・テキスト */
[data-testid="stAppViewContainer"] [class*="st-"] {{
    color: {_c['text_primary']};
}}
/* selectbox / multiselect のドロップダウン */
[data-baseweb="select"] * {{
    color: {_c['text_primary']} !important;
    background-color: {_c['bg_card']} !important;
}}
[data-baseweb="menu"] * {{
    color: {_c['text_primary']} !important;
    background-color: {_c['bg_card']} !important;
}}
/* radio, checkbox */
[data-testid="stRadio"] label span,
[data-testid="stCheckbox"] label span {{
    color: {_c['text_primary']} !important;
}}
/* widget ラベル全般 */
[data-testid*="st"] [data-testid="stWidgetLabel"] p {{
    color: {_c['text_primary']} !important;
}}
/* subheader / header */
[data-testid="stAppViewContainer"] h1,
[data-testid="stAppViewContainer"] h2,
[data-testid="stAppViewContainer"] h3 {{
    color: {_c['text_primary']} !important;
}}
/* caption / info / success / warning */
[data-testid="stCaptionContainer"] p,
[data-testid="stNotificationContentInfo"] p,
[data-testid="stNotificationContentSuccess"] p,
[data-testid="stNotificationContentWarning"] p {{
    color: {_c['text_primary']} !important;
}}
/* expander ヘッダー */
[data-testid="stExpander"] summary p,
[data-testid="stExpander"] summary span {{
    color: {_c['text_primary']} !important;
}}
/* multiselect タグ */
[data-baseweb="tag"] span {{
    color: {_c['text_primary']} !important;
}}
"""}

/* ── セレクトボックス・ラジオ（テキスト色のみ、背景はStreamlitデフォルト） ── */
[data-testid="stSelectbox"] label, [data-testid="stMultiSelect"] label,
[data-testid="stTextInput"] label, [data-testid="stRadio"] label {{
    color: {_c['text_primary']} !important;
}}

/* ── expander（枠と背景のみ、内部テキストはStreamlitデフォルト） ── */
[data-testid="stExpander"] {{
    background-color: {_c['bg_card']} !important;
    border: 1px solid {_c['border']} !important;
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

/* ── 全体余白の削減（情報密度を上げる） ── */
.block-container {{
    padding-top: 0 !important;
    padding-bottom: 1rem !important;
}}
/* サブヘッダー上下余白を詰める */
h2, h3 {{
    margin-top: 0.2em !important;
    margin-bottom: 0.1em !important;
}}
/* subheader直後のdivider余白を詰める */
hr {{
    margin-top: 0.3em !important;
    margin-bottom: 0.3em !important;
}}
/* caption 上下余白を詰める */
[data-testid="stCaptionContainer"] {{
    margin-top: 0 !important;
    margin-bottom: 0.1em !important;
}}

/* ── レスポンシブ（スマホ文字サイズ最適化） ── */
@media (max-width: 640px) {{
    /* 見出し */
    h1 {{ font-size: 1.3em !important; line-height: 1.3 !important; }}
    h2 {{ font-size: 1.1em !important; line-height: 1.3 !important; }}
    h3 {{ font-size: 1.0em !important; }}

    /* 本文・キャプション */
    .stMarkdown p, .stMarkdown li {{
        font-size: 0.88em !important;
        line-height: 1.6 !important;
        word-break: break-word !important;
    }}
    [data-testid="stCaptionContainer"] * {{
        font-size: 0.78em !important;
    }}

    /* メトリクス */
    [data-testid="stMetricValue"] {{
        font-size: 1.1em !important;
    }}
    [data-testid="stMetricLabel"] {{
        font-size: 0.78em !important;
    }}

    /* ボタン */
    div.stButton > button {{
        font-size: 0.85em !important;
        height: 2.8em !important;
        padding: 0 8px !important;
    }}

    /* セレクトボックス */
    div[data-testid="stSelectbox"] > div {{
        font-size: 0.88em !important;
    }}

    /* DataFrame */
    [data-testid="stDataFrame"] {{
        font-size: 0.78em !important;
    }}

    /* タブ */
    .stTabs [data-baseweb="tab"] {{
        font-size: 0.82em !important;
        padding: 6px 8px !important;
    }}

    /* expander */
    [data-testid="stExpander"] summary {{
        font-size: 0.88em !important;
    }}

    /* 余白詰め */
    .block-container {{
        padding-left: 0.8rem !important;
        padding-right: 0.8rem !important;
    }}
}}

/* ── ツールバー・デプロイボタン・フッター等を非表示 ── */
/* サイドバー開閉ボタン(≡)は残し、それ以外のツールバーを非表示 */
[data-testid="stDecoration"] {{ display: none !important; }}
[data-testid="stDeployButton"] {{ display: none !important; }}
#MainMenu {{ display: none !important; }}
footer {{ display: none !important; }}
button[title="View fullscreen"] {{ display: none !important; }}
/* Share・スター・編集・GitHubボタンを非表示（開閉ボタンは除外） */
[data-testid="stToolbar"] > *:not([data-testid="stSidebarNavToggleButton"]) {{
    display: none !important;
}}
/* PC版ツールバーの右側ボタン群を非表示 */
[data-testid="stToolbarActions"] {{ display: none !important; }}
header[data-testid="stHeader"] a {{ display: none !important; }}
header[data-testid="stHeader"] [data-testid="stActionButton"] {{ display: none !important; }}
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
if "is_mobile" not in st.session_state:
    st.session_state["is_mobile"] = False   # JS判定で上書きされる
if "view_mode" not in st.session_state:
    st.session_state["view_mode"] = "auto"  # "auto" | "mobile" | "desktop"
if "selected_period" not in st.session_state:
    st.session_state["selected_period"] = "1ヶ月"
if "custom_themes" not in st.session_state:
    st.session_state["custom_themes"] = {}
# 設定タブ用
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
    "ドローン": {
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
    _labels_ja = ["1日","1週間","1ヶ月","3ヶ月","6ヶ月","1年","1年半","2年"]
    labels = _labels_ja
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


# ──────────────────────────────────────────────
# USD/JPY レート取得（TTL=市場時間と同じ動的キャッシュ）
# ──────────────────────────────────────────────
@st.cache_data(ttl=_get_ttl())
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
    lm = left_margin if left_margin else max(120, (max_label_len + rank_prefix_len) * 10 + 15)
    lm = min(lm, 240)

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
        textfont=dict(color="white", size=10),
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

def make_price_chart(df, display_df, chart_type="candlestick", show_ma=True):
    """株価チャート：目盛りを月単位に設定"""
    fig = go.Figure()
    if chart_type == "candlestick":
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

def period_buttons(key_prefix="main", col=None):
    """
    期間選択セレクトボックス。
    col を渡すと そのカラム内に配置、None なら自前で [1,3] 列を作る。
    """
    period_opts   = get_period_options()
    period_labels = list(period_opts.keys())
    current_val   = st.session_state.get("selected_period_val", "1mo")
    val_to_label  = {v: k for k, v in period_opts.items()}
    current_label = val_to_label.get(current_val, period_labels[2])

    target = col if col is not None else st.columns([1, 3])[0]
    with target:
        selected = st.selectbox(
            "📅 期間",
            period_labels,
            index=period_labels.index(current_label) if current_label in period_labels else 2,
            key=f"period_sel_{key_prefix}",
        )

    selected_val = period_opts[selected]
    if selected_val != current_val:
        st.session_state["selected_period_val"] = selected_val
        st.session_state["selected_period"] = selected
        st.rerun()

    return selected_val



# =====================
# ページ切り替え（クリックで即切替）
# =====================
def get_pages():
    return [
        "📊 テーマ一覧",
        "📡 騰落モメンタム",
        "💹 資金フロー",
        "📈 騰落推移",
        "🔥 ヒートマップ",
        "📉 テーマ比較",
        "🌍 マクロ比較",
        "📋 市場別ランキング",
        "🔍 テーマ別詳細",
        "⭐ お気に入り",
        "🎨 カスタムテーマ",
        "📣 お知らせ",
        "📖 使い方",
        "⚙️ 設定",
        "⚖️ 免責事項",
    ]

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

# ── サイドバーナビゲーション（アクティブ強調CSS付き） ──
_pidx_now = st.session_state["current_page_idx"]

# アクティブボタンを赤く強調するCSS
# nth-of-typeではなくdata属性で特定できないため、JS不使用でCSSのみ対応
st.sidebar.markdown(f"""
<style>
div[data-testid="stSidebar"] .stButton > button {{
    background: #1a1e2e;
    color: #b0b8c8;
    border: 1px solid #2a2e40;
    text-align: left;
    font-size: 13px;
    white-space: nowrap !important;
    overflow: hidden !important;
    text-overflow: ellipsis !important;
    padding-left: 8px !important;
    padding-right: 8px !important;
}}
@media (max-width: 640px) {{
    div[data-testid="stSidebar"] .stButton > button {{
        font-size: 11.5px !important;
        padding-left: 6px !important;
        padding-right: 6px !important;
        letter-spacing: -0.01em;
    }}
}}
div[data-testid="stSidebar"] .stButton > button:hover {{
    background: #252a3e;
    color: #ffffff;
    border-color: #445;
}}
/* アクティブページ: n番目のボタンを赤にする */
div[data-testid="stSidebar"] .stButton:nth-of-type({_pidx_now + 2}) > button {{
    background: #e63030 !important;
    color: white !important;
    border-color: #e63030 !important;
    font-weight: 700;
}}
</style>
""", unsafe_allow_html=True)

# ── サイドバー上部：ロゴ固定表示 ──
st.sidebar.markdown("""
<style>
/* サイドバーロゴを上部固定 */
div[data-testid="stSidebar"] > div:first-child {
    padding-top: 0 !important;
}
#swjp-sidebar-logo {
    position: sticky;
    top: 0;
    z-index: 100;
    background: #0d1020;
    padding: 8px 12px 6px 12px;
    margin: -1rem -1rem 0.2rem -1rem;
    border-bottom: 1px solid #1a1e30;
}
</style>
<div id="swjp-sidebar-logo">
  <div style="display:flex;align-items:center;gap:8px;">
    <svg width="28" height="28" viewBox="0 0 56 56" fill="none" xmlns="http://www.w3.org/2000/svg">
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
    <div style="line-height:1;">
      <div style="display:flex;align-items:baseline;gap:0;">
        <span style="font-family:'Arial Black',sans-serif;font-size:16px;font-weight:900;color:#e63030;letter-spacing:0.03em;">Stock</span>
        <span style="font-family:'Arial Black',sans-serif;font-size:16px;font-weight:900;color:#ffffff;letter-spacing:0.03em;">Wave</span>
        <span style="font-family:'Arial Black',sans-serif;font-size:10px;font-weight:900;color:#e63030;margin-left:2px;letter-spacing:0.1em;">JP</span>
      </div>
      <div style="font-size:7px;letter-spacing:0.4em;color:#3a4560;font-weight:700;margin-top:1px;">株　式　波　動</div>
    </div>
  </div>
</div>
""", unsafe_allow_html=True)

st.sidebar.markdown("### メニュー")
for _i, _p in enumerate(PAGES):
    if st.sidebar.button(_p, key=f"nav_{_i}", use_container_width=True):
        st.session_state["current_page_idx"] = _i
        st.session_state["current_page"] = _p
        st.rerun()

page = st.session_state["current_page"]

fav_count = len(st.session_state["favorites"])
if fav_count > 0:
    st.sidebar.info("⭐ お気に入り：{}銘柄".format(fav_count))
if st.sidebar.button("🔄 データを最新に更新"):
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
    _market_status = "🔴 市場閉（土日）"
    _ttl_min = 60
elif _mo <= _t <= _mc:
    _market_status = "🟢 市場オープン中"
    _ttl_min = 3
else:
    _market_status = "🟡 市場閉（時間外）"
    _ttl_min = 30

st.sidebar.markdown(f"**{_market_status}**")
st.sidebar.caption("🔄 更新頻度：約{}分ごと".format(_ttl_min))
st.sidebar.caption("🕐 現在時刻(JST)：{}".format(_now_jst.strftime('%H:%M')))
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
    dt = _dt2.datetime.utcnow() + _dt2.timedelta(hours=9)
    return dt.strftime("%Y年%m月%d日 %H:%M")
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
PAGE_SETTINGS      = 13
PAGE_DISCLAIMER    = 14

pidx = st.session_state.get("current_page_idx", 0)

# =====================
# テーマ一覧
# =====================
if pidx == PAGE_THEME_LIST:
    now = _get_now_str()

    # ── 期間・テーマ数・トグルを1行に ──
    _col_period, _col_count, _col_sp, _col_toggle = st.columns([2, 2, 1, 2])

    # 期間選択
    period_opts   = get_period_options()
    period_labels = list(period_opts.keys())
    current_val   = st.session_state.get("selected_period_val", "1mo")
    val_to_label  = {v: k for k, v in period_opts.items()}
    current_label = val_to_label.get(current_val, period_labels[2])
    with _col_period:
        selected = st.selectbox(
            "📅 期間",
            period_labels,
            index=period_labels.index(current_label) if current_label in period_labels else 2,
            key="period_sel_home",
        )
    st.session_state["selected_period_val"] = period_opts[selected]
    period = period_opts[selected]

    # テーマ数選択
    with _col_count:
        display_count = st.selectbox(
            "📊 テーマ数",
            [5, 10, 15, 25, 99],
            index=0,
        )

    # モバイル／PCトグル
    with _col_toggle:
        st.markdown('<div class="toggle-wrap" style="padding-top:22px;">', unsafe_allow_html=True)
        _toggle_val = st.radio(
            "表示モード",
            ["📱 モバイル", "🖥️ PC"],
            index=0 if _is_mobile else 1,
            key="view_toggle_radio",
            horizontal=True,
            label_visibility="collapsed",
        )
        st.markdown('</div>', unsafe_allow_html=True)
        if (_toggle_val == "📱 モバイル") != _is_mobile:
            st.session_state["view_mode"] = "mobile" if _toggle_val == "📱 モバイル" else "desktop"
            st.rerun()

    theme_keys = tuple(themes.keys())
    with st.spinner("データを取得中...（初回は時間がかかります）"):
        theme_results, theme_details, _cache_time = fetch_all_theme_data(period, theme_keys)


    # データ取得後に現在時刻・更新時刻を表示（_cache_time定義後）
    st.caption(f"🕐 現在時刻：{now}　｜　📦 データ更新：{_cache_time}　　{len(themes)}テーマ・約{len(all_stocks)}銘柄")

    # 表示件数に応じて上位・下位を切り出し
    n = display_count if display_count < 99 else len(theme_results)
    top_results = theme_results[:n]
    bot_results = theme_results[-n:] if display_count < 99 else []

    # === 上昇・下落テーマを横並びで表示 ===
    _col_top, _col_bot = st.columns(2)

    top_labels = [r["テーマ"] for r in top_results]
    top_ranks  = [f"{i+1}" for i in range(len(top_results))]
    top_values = [r["平均騰落率(%)"] for r in top_results]
    top_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in top_values]
    chart_h = max(200, len(top_results) * 38)

    with _col_top:
        st.markdown(f'<p style="font-size:12px;font-weight:700;margin:4px 0 2px;">🔴 上昇テーマ TOP{n}</p>', unsafe_allow_html=True)
        st.plotly_chart(
            make_bar_chart(top_labels, top_values, top_colors, height=chart_h, rank_labels=top_ranks),
            use_container_width=True, config=PLOT_CONFIG
        )

    if bot_results and display_count < 99:
        total = len(theme_results)
        bot_labels = [r["テーマ"] for r in bot_results]
        bot_ranks  = [f"{total-n+i+1}" for i in range(len(bot_results))]
        bot_values = [r["平均騰落率(%)"] for r in bot_results]
        bot_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in bot_values]
        chart_h2 = max(200, len(bot_results) * 38)
        with _col_bot:
            st.markdown(f'<p style="font-size:12px;font-weight:700;margin:4px 0 2px;">🟢 下落テーマ TOP{n}</p>', unsafe_allow_html=True)
            st.plotly_chart(
                make_bar_chart(bot_labels, bot_values, bot_colors, height=chart_h2, rank_labels=bot_ranks),
                use_container_width=True, config=PLOT_CONFIG
            )

    # === テーマ別出来高・売買代金ランキング ===
    st.subheader("📊 テーマ別ランキング")
    col_rank1, col_rank2 = st.columns(2)

    if "show_vol_all" not in st.session_state:
        st.session_state["show_vol_all"] = False
    if "show_tv_all" not in st.session_state:
        st.session_state["show_tv_all"] = False

    # 出来高ランキング
    vol_sorted_all = sorted(theme_results, key=lambda x: x["合計出来高"], reverse=True)
    with col_rank1:
        st.markdown("**🔢 テーマ別出来高**")
        show_v = st.session_state["show_vol_all"]
        disp_vol = vol_sorted_all if show_v else vol_sorted_all[:5]
        vol_rows = [
            {"順位": "{}位".format(i+1), "テーマ": r["テーマ"], "出来高増減": f"{int(r['合計出来高']):,}"}
            for i, r in enumerate(disp_vol)
        ]
        st.dataframe(pd.DataFrame(vol_rows).set_index("順位"), use_container_width=True)
        btn_label_v = "▲ 閉じる" if show_v else "▼ 6位以下を表示（残り{}件）".format(len(vol_sorted_all)-5)
        if st.button(btn_label_v, key="btn_vol_toggle", use_container_width=True):
            st.session_state["show_vol_all"] = not show_v
            st.rerun()

    # 売買代金ランキング
    tv_sorted_all = sorted(theme_results, key=lambda x: x["合計売買代金"], reverse=True)
    with col_rank2:
        st.markdown(f"**{"💴 テーマ別売買代金"}**")
        show_t = st.session_state["show_tv_all"]
        disp_tv = tv_sorted_all if show_t else tv_sorted_all[:5]
        tv_rows = [
            {"順位": "{}位".format(i+1), "テーマ": r["テーマ"], "売買代金": format_large_number(r["合計売買代金"])}
            for i, r in enumerate(disp_tv)
        ]
        st.dataframe(pd.DataFrame(tv_rows).set_index("順位"), use_container_width=True)
        btn_label_t = "▲ 閉じる" if show_t else "▼ 6位以下を表示（残り{}件）".format(len(tv_sorted_all)-5)
        if st.button(btn_label_t, key="btn_tv_toggle", use_container_width=True):
            st.session_state["show_tv_all"] = not show_t
            st.rerun()

    # === 全テーマ一覧表 ===
    st.subheader("📋 全テーマ一覧")
    table_data = []
    for rank, r in enumerate(theme_results, 1):
        c_ret, v = r["平均騰落率(%)"], r["出来高増減(%)"]
        row = {
            "順位": "{}位".format(rank),
            "テーマ": r["テーマ"],
            "騰落率": f"🔴 +{c_ret}%" if c_ret>0 else f"🟢 {c_ret}%",
            "出来高増減": f"📈 +{v}%" if v>0 else f"📉 {v}%",
        }
        table_data.append(row)
    df_table = pd.DataFrame(table_data).set_index("順位")
    st.dataframe(df_table, use_container_width=True)
    st.download_button("📥 CSVダウンロード", df_table.to_csv(encoding="utf-8-sig"),
                       f"theme_list_{now}.csv", "text/csv")



# =====================
# 騰落モメンタム
# =====================
elif pidx == PAGE_MOMENTUM:
    st.subheader("📡 騰落モメンタム")
    st.caption("現在の騰落率 ＋ 先週比・先月比の変化で「加速・失速・転換」テーマを一目で把握")
    # 期間 ＋ 並び替えを1行横並び
    _mc1, _mc2, _mc3 = st.columns([1, 1, 2])
    period = period_buttons(key_prefix="momentum_page", col=_mc1)
    with _mc2:
        sort_key = st.selectbox("📊 並び替え", ["騰落率（降順）", "先週比変化（降順）", "先月比変化（降順）"])

    theme_keys = tuple(themes.keys())
    with st.spinner("データ取得中..."):
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
        if   dw > 3  and dm > 5:  state = "🔥加速"
        elif dw < -3 and dm < -5: state = "❄️失速"
        elif dw > 2:               state = "↗転換↑"
        elif dw < -2:              state = "↘転換↓"
        else:                      state = "→横ばい"
        momentum_data.append({"テーマ": theme_n, "騰落率": cur, "先週比": dw, "先月比": dm, "状態": state})
    if sort_key == "騰落率（降順）":
        momentum_data.sort(key=lambda x: x["騰落率"], reverse=True)
    elif sort_key == "先週比変化（降順）":
        momentum_data.sort(key=lambda x: x["先週比"], reverse=True)
    else:
        momentum_data.sort(key=lambda x: x["先月比"], reverse=True)

    # フィルター（3列目に配置）
    with _mc3:
        filter_state = st.multiselect("🔍 状態フィルター",
                                       ["🔥加速","↗転換↑","→横ばい","↘転換↓","❄️失速"])
    if filter_state:
        momentum_data = [d for d in momentum_data if d["状態"] in filter_state]

    # ヘッダー行
    hcol1, hcol2, hcol3, hcol4, hcol5 = st.columns([3, 2, 2, 2, 2])
    hcol1.markdown(f"<small style='color:#666'>{"テーマ名"}</small>", unsafe_allow_html=True)
    hcol2.markdown(f"<small style='color:#666'>{"騰落率(%)"}</small>", unsafe_allow_html=True)
    hcol3.markdown(f"<small style='color:#666'>{"先週比(pt)"}</small>", unsafe_allow_html=True)
    hcol4.markdown(f"<small style='color:#666'>{"先月比(pt)"}</small>", unsafe_allow_html=True)
    hcol5.markdown(f"<small style='color:#666'>{"状態"}</small>", unsafe_allow_html=True)
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
        col1.write(f"**{i+1}. {d['テーマ']}**")
        col2.write(f"{c_color} {sign}{cur}%")
        col3.write(f"{dw_icon} {dw_sign}{dw}pt")
        col4.write(f"{dm_icon} {dm_sign}{dm}pt")
        col5.write(state)

    st.caption("💡 騰落率=選択期間の変化率 / 先週比・先月比=騰落率との差分(ポイント) / 🔥加速=両方↑ / ❄️失速=両方↓")

# =====================
# 資金フロー
# =====================
elif pidx == PAGE_FUND_FLOW:
    st.subheader("💹 テーマ別 資金フロー")
    st.caption("上昇テーマ vs 下落テーマの騰落幅を比較。どのテーマに資金が集まっているか把握できます。")
    _fc1, _fc2 = st.columns([1, 3])
    period = period_buttons(key_prefix="flow_page", col=_fc1)

    theme_keys = tuple(themes.keys())
    with st.spinner("データ取得中..."):
        flow_results, _, _ct_flow = fetch_all_theme_data(period, theme_keys)

    flow_sorted = sorted(flow_results, key=lambda x: x["平均騰落率(%)"], reverse=True)
    gainers = flow_sorted[:10]
    losers  = flow_sorted[-10:][::-1]
    total   = len(flow_sorted)

    col_g, col_l = st.columns(2)
    with col_g:
        st.markdown("### 🔥 資金流入テーマ TOP10")
        g_labels = [r["テーマ"] for r in gainers]
        g_ranks  = [str(i+1) for i in range(len(gainers))]
        g_values = [r["平均騰落率(%)"] for r in gainers]
        g_colors = ["#ff4b4b"] * len(gainers)
        st.plotly_chart(make_bar_chart(g_labels, g_values, g_colors,
                                       height=max(200, len(gainers)*38),
                                       rank_labels=g_ranks),
                        use_container_width=True, config=PLOT_CONFIG)

    with col_l:
        st.markdown("### ❄️ 資金流出テーマ TOP10")
        l_labels = [r["テーマ"] for r in losers]
        l_ranks  = [str(total - len(losers) + i + 1) for i in range(len(losers))]
        l_values = [r["平均騰落率(%)"] for r in losers]
        l_colors = ["#39d353"] * len(losers)
        st.plotly_chart(make_bar_chart(l_labels, l_values, l_colors,
                                       height=max(200, len(losers)*38),
                                       rank_labels=l_ranks),
                        use_container_width=True, config=PLOT_CONFIG)

    # 全テーマ一覧
    st.markdown("---")
    st.markdown("**📊 全テーマ 騰落率一覧（資金フロー全景）**")
    all_labels = [r["テーマ"] for r in flow_sorted]
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
    st.subheader("📈 テーマ別 騰落率の推移")
    st.caption(f"🕐 {_get_now_str()}  |  {"yfinanceの日次終値から算出（スプレッドシート不要）"}")

    # 期間選択
    trend_period = st.selectbox(
        "表示期間",
        ["1週間", "1ヶ月", "3ヶ月", "6ヶ月", "1年"],
        index=4,
        key="trend_period_sel",
    )
    period_map = {"1週間": "5d", "1ヶ月": "1mo", "3ヶ月": "3mo", "6ヶ月": "6mo", "1年": "1y"}
    sel_period = period_map[trend_period]

    theme_keys = tuple(themes.keys())

    with st.spinner("日次データを取得中...（初回は少し時間がかかります）"):
        trend_data = fetch_theme_trend(theme_keys, sel_period)

    if not trend_data:
        st.warning("データを取得できませんでした。しばらく待ってから再度お試しください。")
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
            "表示モード",
            ["🏆 上位5＋ワースト5", "✅ テーマを手動選択", "📊 全テーマ"],
            horizontal=True,
            key="trend_mode",
        )

        all_theme_names = list(trend_data.keys())
        # 英語表示用: 日本語テーマ名 → 英語名 の変換
        _en2jp_tab3 = {k: k for k in all_theme_names}
        _all_names_en = [k for k in all_theme_names]
        _default_sel_en = [k for k in default_sel]

        if mode == "🏆 上位5＋ワースト5":
            selected_en = _default_sel_en
        elif mode == "✅ テーマを手動選択":
            selected_en = st.multiselect(
                "表示テーマを選択",
                _all_names_en,
                default=_default_sel_en,
                key="trend_manual_sel",
            )
        else:
            selected_en = _all_names_en
        # 英語名→日本語名（内部キー）に逆引き
        selected = [_en2jp_tab3.get(n, n) for n in selected_en]

        if not selected:
            st.info("テーマを1つ以上選択してください。")
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
                display_name = theme_n
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
                yaxis=dict(title="騰落率（%）", ticksuffix="%", zeroline=False),
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
            st.markdown("**📋 テーマ騰落率ランキング（{}）**".format(trend_period))
            rank_df = pd.DataFrame([
                {"順位": i+1, "テーマ": theme_n, "騰落率（{}）".format(trend_period): f"{v:+.2f}%"}
                for i, (theme_n, v) in enumerate(sorted_themes)
            ])
            st.dataframe(rank_df.set_index("順位"), use_container_width=True, height=min(600, len(rank_df)*36+40))

            # CSV出力
            csv_data = []
            for theme_n in all_theme_names:
                if theme_n in trend_data and trend_data[theme_n] is not None:
                    s = trend_data[theme_n]
                    for date, val in s.items():
                        csv_data.append({"日付": date.strftime("%Y-%m-%d"), "テーマ": theme_n, "騰落率(%)": val})
            if csv_data:
                csv_df = pd.DataFrame(csv_data)
                st.download_button(
                    "📥 全テーマCSVダウンロード",
                    csv_df.to_csv(index=False, encoding="utf-8-sig"),
f"テーマ騰落推移_{trend_period}_{now}.csv",
                    "text/csv",
                )

# =====================
# ヒートマップ
# =====================
elif pidx == PAGE_HEATMAP:
    st.subheader("🔥 テーマ別騰落率 ヒートマップ")
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
        with st.spinner("データ取得中..."):
            heatmap_data = fetch_heatmap_data(theme_keys)
        short_labels = ["1W","1M","3M","6M","1Y"]
        df_heat = pd.DataFrame(heatmap_data).T[short_labels]
        df_heat.index = [n for n in df_heat.index]
        all_vals = [v for row in df_heat.values.tolist() for v in row if v is not None]
        abs_max = max(abs(min(all_vals)), abs(max(all_vals))) if all_vals else 10
        n_themes = len(df_heat)

        st.markdown("🔴**赤=上昇** 　🟢**緑=下落** 　⬛**黒=±0**")

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
        st.download_button("📥 CSV", df_heat.to_csv(encoding="utf-8-sig"), f"heatmap_{now}.csv", "text/csv")

    # ============================================================
    # タブ2: 月次推移ヒートマップ（過去12ヶ月・月単位）
    # ============================================================
    with tab_monthly:
        st.markdown("**過去12ヶ月の月別騰落率** 🔴赤=上昇　🟢緑=下落")
        st.caption("各月の始値→終値の騰落率（テーマ内銘柄の平均）")
        with st.spinner("月次データ取得中...（少し時間がかかります）"):
            monthly_data, month_labels = fetch_monthly_heatmap(theme_keys)

        df_monthly = pd.DataFrame(monthly_data).T[month_labels]
        df_monthly.index = [n for n in df_monthly.index]
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
        short_months = [m[5:] + ("月") for m in month_labels]

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
        st.markdown("**📋 月次騰落率テーブル**")
        df_m_disp = df_monthly.copy()
        df_m_disp.columns = short_months
        df_m_disp = df_m_disp.applymap(lambda v: f"+{v:.1f}%" if v and v>0 else f"{v:.1f}%" if v else "N/A")
        st.dataframe(df_m_disp, use_container_width=True, height=min(500, n_t*35+40))
        st.download_button("📥 月次CSV", df_monthly.to_csv(encoding="utf-8-sig"), f"monthly_heatmap_{now}.csv", "text/csv")

    # ============================================================
    # タブ3: 折れ線グラフ（テーマ選択式）
    # ============================================================
    with tab_line:
        with st.spinner("データ取得中..."):
            heatmap_data2 = fetch_heatmap_data(theme_keys)
        period_cols = ["1W","1M","3M","6M","1Y"]
        df_heat2 = pd.DataFrame(heatmap_data2).T[period_cols]
        all_theme_names = df_heat2.index.tolist()
        sorted_by_1m2 = df_heat2["1M"].sort_values(ascending=False)

        if "hl_preset" not in st.session_state:
            st.session_state["hl_preset"] = sorted_by_1m2.head(5).index.tolist()
        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("🔴 上昇TOP5", key="hl_top5"):
                st.session_state["hl_preset"] = sorted_by_1m2.head(5).index.tolist(); st.rerun()
        with c2:
            if st.button("🟢 下落TOP5", key="hl_bot5"):
                st.session_state["hl_preset"] = sorted_by_1m2.tail(5).index.tolist(); st.rerun()
        with c3:
            if st.button("📋 全テーマ", key="hl_all"):
                st.session_state["hl_preset"] = all_theme_names; st.rerun()

        selected_line_themes = st.multiselect(
            "表示テーマを選択",
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
                    x=period_cols, y=vals, mode="lines+markers", name=theme_n,
                    line=dict(color=color_palette[idx % len(color_palette)], width=2),
                    marker=dict(size=7), connectgaps=True,
                ))
            fig_line.add_hline(y=0, line_dash="dash", line_color="#666", line_width=1)
            fig_line.update_layout(
                xaxis=dict(title="期間", categoryorder="array", categoryarray=period_cols),
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
            st.info("テーマを選択してください")

elif pidx == PAGE_COMPARE:
    st.subheader("📉 テーマ間比較チャート")
    _cc1, _cc2 = st.columns([1, 3])
    period = period_buttons(key_prefix="comp", col=_cc1)
    _en2jp_cmp = {k: k for k in themes.keys()}
    _cmp_opts = [k for k in themes.keys()]
    _cmp_def = _cmp_opts[:2]
    selected_themes_cmp_disp = st.multiselect("比較するテーマを選択（最大10）", _cmp_opts,
                                          default=_cmp_def)
    selected_themes_cmp = [_en2jp_cmp.get(n, n) for n in selected_themes_cmp_disp]
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
elif pidx == PAGE_MACRO:
    st.subheader("🌍 マクロ指標との比較")
    _mac1, _mac2 = st.columns([1, 3])
    period = period_buttons(key_prefix="macro", col=_mac1)
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
# 市場別ランキング
# =====================
elif pidx == PAGE_MARKET_RANK:
    st.subheader("📋 市場別ランキング")
    st.caption("日経225・プライム・スタンダード・グロース別の騰落率ランキング")
    _mrk1, _mrk2 = st.columns([1, 3])
    period = period_buttons(key_prefix="market", col=_mrk1)

    # テーブル列幅設定（column_config）
    _col_cfg_top5 = {
        "コード":      st.column_config.TextColumn("コード",    width=70),
        "銘柄名":      st.column_config.TextColumn("銘柄名",    width=140),
        "株価":        st.column_config.TextColumn("株価",      width=90),
        "前日比":      st.column_config.TextColumn("前日比",    width=110),
        "騰落率":      st.column_config.TextColumn("騰落率",    width=110),
        "出来高":      st.column_config.TextColumn("出来高",    width=90),
        "売買代金":    st.column_config.TextColumn("売買代金",  width=100),
    }
    _col_cfg_all = {
        "順位":        st.column_config.TextColumn("順位",      width=55),
        "コード":      st.column_config.TextColumn("コード",    width=70),
        "銘柄名":      st.column_config.TextColumn("銘柄名",    width=140),
        "株価":        st.column_config.TextColumn("株価",      width=90),
        "前日比":      st.column_config.TextColumn("前日比",    width=110),
        "騰落率":      st.column_config.TextColumn("騰落率",    width=110),
        "出来高":      st.column_config.TextColumn("出来高",    width=90),
        "売買代金":    st.column_config.TextColumn("売買代金",  width=100),
    }

    for seg_name, seg_stocks in MARKET_SEGMENTS.items():
        # デフォルト閉じる（expanded=False）
        with st.expander(f"📌 {seg_name}", expanded=False):
            with st.spinner("{} データ取得中...".format(seg_name)):
                seg_results = []
                for stock_name, ticker in seg_stocks.items():
                    try:
                        df = fetch_stock_data(ticker, "2y")
                        if len(df) < 2: continue
                        target_df = get_target_df(df, period)
                        if len(target_df) < 2: continue
                        change = calc_change(target_df)
                        if change is None: continue
                        day_c = round((df["Close"].iloc[-1]-df["Close"].iloc[-2])/df["Close"].iloc[-2]*100,2) if len(df)>=2 else None
                        price = int(df["Close"].iloc[-1])
                        # 出来高：直近1日の実際の出来高
                        volume_raw = int(df["Volume"].iloc[-1])
                        volume_str = f"{volume_raw:,}株"
                        rv = target_df["Volume"].mean()
                        trade_val = int(rv * price)
                        # 証券コード（tickerから4桁を抽出）
                        code = ticker.split(".")[0] if "." in ticker else ticker
                        seg_results.append({
                            "コード":   code,
                            "銘柄名":   stock_name,
                            "株価":     f"¥{price:,}",
                            "前日比":   f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                            "騰落率":   change,
                            "出来高":   volume_str,
                            "売買代金": format_large_number(trade_val),
                            "ticker":   ticker,
                        })
                    except: pass

            if seg_results:
                seg_results.sort(key=lambda x: x["騰落率"], reverse=True)
                n_seg = len(seg_results)

                # 上位5・下位5を1グラフに統合（軸対称でラベル被りを防ぐ）
                top5 = seg_results[:5]
                bot5 = seg_results[-5:] if n_seg > 5 else []

                # 上位5（上部）＋ 下位5（下部）を1つのリストに
                chart_items = top5 + (bot5 if bot5 else [])
                c_labels = []
                for i, r in enumerate(top5):
                    c_labels.append(f"{i+1}位 {r['コード']} {r['銘柄名']}")
                for i, r in enumerate(bot5):
                    c_labels.append(f"{n_seg-len(bot5)+i+1}位 {r['コード']} {r['銘柄名']}")
                c_values = [r["騰落率"] for r in chart_items]
                c_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in c_values]

                # 軸範囲：プラスとマイナスが混在する場合も両端に余白を確保
                _cmin = min(c_values)
                _cmax = max(c_values)
                _abs_max = max(abs(_cmin), abs(_cmax))
                _margin = _abs_max * 0.35 if _abs_max > 0 else 1.0
                _xrange = [_cmin - _margin, _cmax + _margin]

                # テキスト位置：値が小さすぎる場合はoutside固定
                _range_span = _xrange[1] - _xrange[0]
                _text_pos = [
                    "inside" if abs(v) / _range_span > 0.18 else "outside"
                    for v in c_values
                ]

                import plotly.graph_objects as _go2
                _fig_m = _go2.Figure(_go2.Bar(
                    y=list(range(len(c_values))),
                    x=c_values,
                    orientation="h",
                    marker_color=c_colors,
                    text=[f" {v:+.2f}%" for v in c_values],
                    textposition=_text_pos,
                    textfont=dict(color="white", size=11),
                    insidetextanchor="middle",
                    cliponaxis=False,
                ))
                _max_label_len = max(len(l) for l in c_labels)
                _lm = min(max(160, _max_label_len * 10 + 20), 280)
                _fig_m.update_layout(
                    xaxis=dict(
                        title="騰落率（%）", ticksuffix="%",
                        zeroline=True, zerolinecolor="#555", zerolinewidth=1,
                        range=_xrange,
                        tickfont=dict(size=10), title_font=dict(size=11),
                    ),
                    yaxis=dict(
                        tickmode="array",
                        tickvals=list(range(len(c_labels))),
                        ticktext=c_labels,
                        autorange="reversed",
                        tickfont=dict(size=11),
                    ),
                    plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
                    font=dict(color="white", size=11),
                    height=max(220, len(c_values) * 36),
                    bargap=0.2,
                    margin=dict(t=8, b=36, l=_lm, r=80),
                )
                # グラフ内：上位5と下位5の間に点線を追加
                if bot5:
                    _boundary_y = len(top5) - 0.5  # 上位5の最後と下位5の最初の間
                    _fig_m.add_shape(
                        type="line",
                        x0=_xrange[0], x1=_xrange[1],
                        y0=_boundary_y, y1=_boundary_y,
                        line=dict(color="#888888", width=1.5, dash="dot"),
                        layer="above",
                    )
                    # 区切りアノテーション
                    _fig_m.add_annotation(
                        x=_xrange[1], y=_boundary_y,
                        text="── 上位 / 下位 ──",
                        showarrow=False,
                        font=dict(size=9, color="#888888"),
                        xanchor="right", yanchor="bottom",
                    )

                st.markdown("**🔴 上位5 ／ 🟢 下位5**")
                st.plotly_chart(_fig_m, use_container_width=True, config=PLOT_CONFIG)

                # 上位5件テーブル（コード・出来高追加・列幅最適化）
                st.markdown("**🔴 上位5銘柄**")
                df_top5 = pd.DataFrame([{
                    "コード":   r["コード"],
                    "銘柄名":   r["銘柄名"],
                    "株価":     r["株価"],
                    "前日比":   r["前日比"],
                    "騰落率":   f"🔴 +{r['騰落率']}%" if r["騰落率"]>0 else f"🟢 {r['騰落率']}%",
                    "出来高":   r["出来高"],
                    "売買代金": r["売買代金"],
                } for r in top5])
                st.dataframe(df_top5, use_container_width=False,
                             column_config=_col_cfg_top5, hide_index=True)

                # 点線セパレーター
                if bot5:
                    st.markdown("""
<div style="border-top: 1.5px dashed #555; margin: 10px 0 6px 0;
            display:flex; align-items:center; gap:8px;">
  <span style="font-size:11px; color:#888; white-space:nowrap; background:transparent;
               padding: 0 6px;">▼ 下位5銘柄</span>
  <div style="flex:1; border-top: 1.5px dashed #555;"></div>
</div>""", unsafe_allow_html=True)
                    df_bot5 = pd.DataFrame([{
                        "コード":   r["コード"],
                        "銘柄名":   r["銘柄名"],
                        "株価":     r["株価"],
                        "前日比":   r["前日比"],
                        "騰落率":   f"🔴 +{r['騰落率']}%" if r["騰落率"]>0 else f"🟢 {r['騰落率']}%",
                        "出来高":   r["出来高"],
                        "売買代金": r["売買代金"],
                    } for r in bot5])
                    st.dataframe(df_bot5, use_container_width=False,
                                 column_config=_col_cfg_top5, hide_index=True)

                # 全件展開（デフォルト閉じる）
                with st.expander("全{}銘柄を表示".format(n_seg), expanded=False):
                    df_all_seg = pd.DataFrame([{
                        "順位":     "{}位".format(i+1),
                        "コード":   r["コード"],
                        "銘柄名":   r["銘柄名"],
                        "株価":     r["株価"],
                        "前日比":   r["前日比"],
                        "騰落率":   f"🔴 +{r['騰落率']}%" if r["騰落率"]>0 else f"🟢 {r['騰落率']}%",
                        "出来高":   r["出来高"],
                        "売買代金": r["売買代金"],
                    } for i, r in enumerate(seg_results)])
                    st.dataframe(df_all_seg, use_container_width=False,
                                 column_config=_col_cfg_all, hide_index=True)

# =====================
# 銘柄検索
# =====================
# =====================
# お気に入り
# =====================
elif pidx == PAGE_FAVORITES:
    st.subheader("⭐ お気に入り銘柄")
    _fv1, _fv2 = st.columns([1, 3])
    period = period_buttons(key_prefix="fav", col=_fv1)
    if len(st.session_state["favorites"]) == 0:
        st.info("テーマ一覧ページで「☆ 登録」ボタンを押して追加してください。")
    else:
        with st.spinner("データ取得中..."):
            fav_results = []
            for stock_name, ticker in st.session_state["favorites"].items():
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
                        "銘柄": stock_name,"ticker":ticker,"change":change,
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
                "銘柄": r["銘柄"], "株価": f"¥{r['price']:,}",
                "前日比": f"🔴 +{day_c}%" if day_c and day_c>0 else f"🟢 {day_c}%" if day_c else "N/A",
                "騰落率":f"🔴 +{r['change']}%" if r["change"]>0 else f"🟢 {r['change']}%",
                "RSI":f"{rsi} {rsi_alert}" if rsi else "N/A",
                "シャープ":f"{r['sharpe']}" if r["sharpe"] else "N/A",
            })
        df_fav = pd.DataFrame(table_data).set_index("銘柄")
        st.dataframe(df_fav, use_container_width=True)
        st.download_button("📥 お気に入りCSV", df_fav.to_csv(encoding="utf-8-sig"),
                           f"favorites_{now}.csv", "text/csv")
        for r in fav_results:
            c = "🔴" if r["change"]>0 else "🟢"
            col1, col2, col3 = st.columns([3,1,1])
            with col1: st.write(f"{c} **{r["銘柄"]}**  {r['change']}%")
            with col2:
                if st.button("⭐ 解除", key=f"fd_{list(r.values())[0]}"):
                    del st.session_state["favorites"][r["銘柄"]]; st.rerun()

# =====================
# テーマ別詳細
# =====================
elif pidx == PAGE_THEME_DETAIL:
    st.subheader("🔍 テーマ別詳細")
    st.caption(f"🕐 {_get_now_str()}")
    _td1, _td2 = st.columns([1, 3])
    period = period_buttons(key_prefix="theme_detail", col=_td1)

    theme_keys = tuple(themes.keys())
    with st.spinner("データ取得中..."):
        td_results, td_details, _cache_time_td = fetch_all_theme_data(period, theme_keys)


    # テーマ選択 (英語モード: 英語表示名→内部日本語キーの逆引き辞書を使う)
    _en2jp_td = {r["テーマ"]: r["テーマ"] for r in td_results}
    theme_display_list = [r["テーマ"] for r in td_results]
    selected_theme_disp = st.selectbox("テーマを選択", theme_display_list, key="detail_theme_sel")
    selected_theme = _en2jp_td.get(selected_theme_disp, selected_theme_disp)

    result = next((r for r in td_results if r["テーマ"] == selected_theme), None)
    stocks_d = td_details.get(selected_theme, {})

    if result and stocks_d:
        c_val = result["平均騰落率(%)"]
        v_val = result["出来高増減(%)"]
        col_h1, col_h2, col_h3 = st.columns(3)
        col_h1.metric("平均騰落率", f"{'🔴 +' if c_val>0 else '🟢 '}{c_val}%")
        col_h2.metric("出来高増減(%)", f"{'📈 +' if v_val>0 else '📉 '}{v_val}%")
        col_h3.metric("銘柄数", f"{len(stocks_d)}{"銘柄"}")

# =====================
# お知らせ
# =====================
elif pidx == PAGE_NEWS:
    st.subheader("📣 お知らせ")
    st.caption("StockWaveJP の機能追加・変更・修正情報をお知らせします。")

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
    st.subheader("🏷️ カスタムテーマ作成・編集")
    st.caption("自分だけのオリジナルテーマを作成できます。")

    tab1, tab2 = st.tabs(["➕ 新規作成", "✏️ 編集・削除"])

    with tab1:

        # ── セッションステート初期化 ──
        if "new_stocks" not in st.session_state:
            st.session_state["new_stocks"] = []
        if "ct_search_result" not in st.session_state:
            st.session_state["ct_search_result"] = None  # {"name":..,"ticker":..,"price":..,...}
        if "ct_search_query" not in st.session_state:
            st.session_state["ct_search_query"] = ""

        st.markdown("#### 📌 テーマ名")
        new_theme_name = st.text_input("テーマ名", placeholder="例：マイ注目銘柄、AIテーマ...",
                                        label_visibility="collapsed")

        st.markdown("---")
        st.markdown("#### 🔎 銘柄を検索して追加")
        st.caption("銘柄名（例：トヨタ）または証券コード4桁（例：7203）で検索")

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
            do_search = st.button("🔍 検索", key="ct_search_btn", use_container_width=True)

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
                st.warning("該当する銘柄が見つかりませんでした。証券コード4桁または銘柄名で再検索してください。")
                st.session_state["ct_search_result"] = None
            else:
                # 最初にヒットした銘柄のデータを取得
                found_name, found_ticker = next(iter(search_targets.items()))
                with st.spinner("{} のデータ取得中...".format(found_name)):
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
                            st.warning("データを取得できませんでした。")
                            st.session_state["ct_search_result"] = None
                    except Exception as e:
                        st.error("データ取得エラー：{}".format(e))
                        st.session_state["ct_search_result"] = None

        # ── 検索結果の表示 ──
        res = st.session_state.get("ct_search_result")
        if res:
            st.markdown("---")
            st.markdown("**📊 銘柄詳細**")

            # 複数ヒット時は選択できるように
            if res["hit_count"] > 1:
                hit_names = [n for n, _ in res["all_hits"]]
                sel_name = st.selectbox("複数の銘柄がヒットしました。選択してください：",
                                         hit_names, key="ct_hit_select")
                if sel_name != res["name"]:
                    # 選択が変わったら再取得
                    sel_ticker = dict(res["all_hits"])[sel_name]
                    with st.spinner("{} のデータ取得中...".format(sel_name)):
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
            d_col2.metric("コード", res["code"])
            d_col3.metric("株価", f"¥{res['price']:,}")
            sign = "+" if res["change"] and res["change"] >= 0 else ""
            d_col4.metric("騰落率(1ヶ月)", f"{sign}{res['change']}%" if res["change"] else "N/A")

            d_col5, d_col6, d_col7, _ = st.columns(4)
            dc = res["day_change"]
            d_col5.metric("前日比", f"{'+'if dc and dc>=0 else ''}{dc}%" if dc else "N/A")
            d_col6.metric("RSI", f"{res['rsi']}" if res["rsi"] else "N/A")
            d_col7.metric("コード", res["ticker"])

            # 追加ボタン
            already = any(s["ticker"] == res["ticker"]
                          for s in st.session_state["new_stocks"])
            if already:
                st.info("✅ **{}** はすでにリストに追加済みです。".format(res['name']))
            else:
                if st.button("＋ 「{}」をテーマに追加".format(res['name']),
                              type="primary", key="ct_add_btn"):
                    st.session_state["new_stocks"].append({
                        "name": res["name"],
                        "ticker": res["ticker"],
                    })
                    st.success("「{}」を追加しました！".format(res['name']))
                    st.session_state["ct_search_result"] = None
                    st.rerun()

        # ── 追加済み銘柄リスト ──
        if st.session_state["new_stocks"]:
            st.markdown("---")
            st.markdown("**📋 追加済み銘柄（{}件）**".format(len(st.session_state['new_stocks'])))
            for i, stock in enumerate(st.session_state["new_stocks"]):
                r_col1, r_col2, r_col3 = st.columns([3, 2, 1])
                with r_col1:
                    st.write(f"**{stock['name']}**")
                with r_col2:
                    st.caption(stock["ticker"])
                with r_col3:
                    if st.button("🗑️", key=f"ns_del_{i}",
                                  help="{}を削除".format(stock['name'])):
                        st.session_state["new_stocks"].pop(i)
                        st.rerun()

        st.markdown("---")
        # ── テーマ保存 ──
        if st.button("✅ テーマを保存", type="primary", key="ct_save_btn"):
            if not new_theme_name:
                st.error("テーマ名を入力してください")
            elif new_theme_name in DEFAULT_THEMES:
                st.error("デフォルトテーマと同じ名前は使えません")
            elif not st.session_state["new_stocks"]:
                st.error("銘柄を1つ以上追加してください")
            else:
                valid_stocks = {s["name"]: s["ticker"]
                                for s in st.session_state["new_stocks"]
                                if s["name"] and s["ticker"]}
                st.session_state["custom_themes"][new_theme_name] = valid_stocks
                st.session_state["new_stocks"] = []
                st.session_state["ct_search_result"] = None
                st.success("「{}」を保存しました！テーマ一覧に反映されます。".format(new_theme_name))
                st.rerun()

    with tab2:
        if not st.session_state["custom_themes"]:
            st.info("まだカスタムテーマがありません。「新規作成」タブから作成してください。")
        else:
            st.markdown("#### 作成済みカスタムテーマ")
            for ct_name, ct_stocks in list(st.session_state["custom_themes"].items()):
                with st.expander("📌 {}（{}銘柄）".format(ct_name, len(ct_stocks))):
                    st.write("**銘柄一覧：**")
                    for sn, ticker in ct_stocks.items():
                        st.write(f"・{sn}（{ticker}）")

                    col_edit1, col_edit2 = st.columns(2)
                    with col_edit1:
                        if st.button("✏️ 編集", key=f"edit_{ct_name}"):
                            st.session_state["editing_theme"] = ct_name
                            st.session_state["new_stocks"] = [{"name":k,"ticker":v} for k,v in ct_stocks.items()]
                            st.info("「新規作成」タブで「{}」を編集できます。保存すると上書きされます。".format(ct_name))
                    with col_edit2:
                        if st.button("🗑️ 削除", key=f"del_{ct_name}"):
                            del st.session_state["custom_themes"][ct_name]
                            st.success("「{}」を削除しました".format(ct_name))
                            st.rerun()


# =====================
# 使い方・Q&A
# =====================
elif pidx == PAGE_HOWTO:
    st.subheader("📖 使い方・Q&A")

    st.markdown("""
<div style="background:#0d1020;border:1px solid #1a1e30;border-radius:12px;padding:20px 22px;margin-bottom:16px;">
  <div style="font-size:16px;font-weight:700;margin-bottom:12px;color:#e8eaf0;">StockWaveJP とは？</div>
  <div style="font-size:13px;color:#8090a8;line-height:1.9;">
    日本株のテーマ別騰落率・資金フロー・モメンタムをリアルタイムに近い形で可視化するツールです。<br>
    約30テーマ・250銘柄のデータを自動集計し、投資テーマの強弱を素早く把握できます。<br>
    🌐 公式サイト：<a href="https://stockwavejp.com" style="color:#4a7cdc;" target="_blank">stockwavejp.com</a><br>
    ※ 本ツールは投資判断の参考情報として提供するものであり、投資助言ではありません。
  </div>
</div>
""", unsafe_allow_html=True)

    st.markdown("### 📌 各ページの使い方")
    _guide = [
        ("📊 テーマ一覧", "全テーマの平均騰落率・出来高増減をランキング形式で表示。期間（1日〜2年）を切り替えて確認できます。"),
        ("📡 騰落モメンタム", "テーマごとの短期・中期モメンタムを比較。強いトレンドのテーマを素早く発見できます。"),
        ("💹 資金フロー", "売買代金・出来高の増減からマネーフローを分析します。"),
        ("📈 騰落推移", "テーマの騰落率を時系列で折れ線グラフ表示。複数テーマの比較も可能です。"),
        ("🔥 ヒートマップ", "テーマ×期間のマトリクスを色で可視化。全体感を一目で把握できます。"),
        ("📉 テーマ比較", "複数テーマを選んで騰落率を並べて比較します。"),
        ("🌍 マクロ比較", "日経平均・ドル円・S&P500・TOPIXを同一グラフで比較します。"),
        ("📋 市場別ランキング", "日経225・プライム・スタンダード・グロース市場別の騰落率ランキングです。"),
        ("🔍 テーマ別詳細", "テーマを選ぶと構成銘柄の詳細データ（RSI・シャープレシオ・52週高値安値）を確認できます。"),
        ("⭐ お気に入り", "気になる銘柄をお気に入り登録して一覧表示できます。"),
        ("🎨 カスタムテーマ", "独自のテーマ・銘柄リストを作成して追跡できます。"),
    ]
    for title, desc in _guide:
        st.markdown(f"""
<div style="border-left:3px solid #ff4b4b;padding:8px 14px;margin-bottom:10px;background:#0d1020;border-radius:0 8px 8px 0;">
  <div style="font-size:13px;font-weight:700;color:#e8eaf0;margin-bottom:3px;">{title}</div>
  <div style="font-size:12px;color:#8090a8;line-height:1.7;">{desc}</div>
</div>
""", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### ❓ よくある質問（Q&A）")
    _qa = [
        ("データはどのくらいの頻度で更新されますか？",
         "市場時間中（9:00〜15:35）は約3分ごと、時間外は約30分ごとに自動更新されます。"),
        ("銘柄データのソースは？",
         "Yahoo Finance（yfinance ライブラリ）経由で取得しています。若干のタイムラグがある場合があります。"),
        ("お気に入りはどこに保存されますか？",
         "ブラウザのセッション内に保存されます。ページを閉じるとリセットされます。"),
        ("カスタムテーマは永続化されますか？",
         "現在はセッション内のみです。ページを再読み込みするとリセットされます。"),
        ("データが取得できない銘柄があります",
         "上場廃止・ティッカー変更・yfinanceの一時的なエラーの可能性があります。しばらく待ってから再試行してください。"),
    ]
    for q, a in _qa:
        with st.expander(f"Q. {q}"):
            st.markdown(f"**A.** {a}")

    st.markdown("---")
    st.markdown(
        "<div style='font-size:11px;color:#3a4560;text-align:center;padding:8px;'>"
        "改善要望・バグ報告は GitHub Issues へ"
        "</div>",
        unsafe_allow_html=True
    )


# =====================
# 設定
# =====================
elif pidx == PAGE_SETTINGS:
    st.subheader("⚙️ 設定")
    st.caption("アプリの表示設定を変更できます。")

    st.markdown("---")
    st.markdown("### 🎨 カラーテーマ")
    st.caption("背景・文字・アクセントカラーを切り替えます。変更は即座に反映されます。")

    # テーマ選択カード
    _theme_options = {
        "dark":  {"label": "🌑 ダーク（黒基調）",      "desc": "目に優しい黒背景。デフォルト設定。"},
        "navy":  {"label": "🌊 ネイビー（深紺）",       "desc": "落ち着いた深紺背景。夜間利用に最適。"},
        "light": {"label": "☀️ ライト（白基調）",       "desc": "明るい白背景。日中の使用に適しています。"},
    }

    _current_theme = st.session_state.get("color_theme", "dark")

    for _tid, _tinfo in _theme_options.items():
        _is_active = (_tid == _current_theme)
        _border = "#e63030" if _is_active else "#2a2e40"
        _bg     = "#1a1e30" if _is_active else "#0d1020"
        _badge  = "　✅ 現在適用中" if _is_active else ""
        st.markdown(
            f"<div style='border:2px solid {_border};border-radius:10px;"
            f"padding:12px 16px;margin-bottom:8px;background:{_bg};'>"
            f"<span style='font-size:1em;font-weight:700;'>{_tinfo['label']}</span>"
            f"<span style='font-size:0.8em;color:#e63030;'>{_badge}</span><br>"
            f"<span style='font-size:0.85em;color:#8090a8;'>{_tinfo['desc']}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        if not _is_active:
            if st.button(f"{_tinfo['label']} に切り替え", key=f"theme_btn_{_tid}", use_container_width=False):
                st.session_state["color_theme"] = _tid
                st.rerun()

    st.markdown("---")
    st.markdown("### 📋 今後追加予定のテーマ")
    st.info("ホワイト（白・クリーン）、ライトネイビー（明るめ紺）などを順次追加予定です。")

# =====================
# 免責事項
# =====================
elif pidx == PAGE_DISCLAIMER:
    st.subheader("⚖️ 免責事項・利用規約")

    _sections = [
        ("📋 免責事項",
         "本ツールで提供する情報は投資判断の参考を目的とした情報提供のみを目的としており、特定の銘柄や金融商品の売買を推奨・勧誘するものではありません。"
         "投資に関する最終判断はご自身の責任において行ってください。"),
        ("📊 データについて",
         "データは Yahoo Finance（yfinance）経由で取得しています。データの正確性・完全性・適時性については保証しません。"
         "システム障害・通信障害等によりデータが取得できない場合があります。"),
        ("⚠️ 投資リスクについて",
         "株式投資には価格変動リスク・流動性リスク等があり、投資元本が保証されるものではありません。"
         "過去の実績は将来の成果を保証するものではありません。"),
        ("🔒 個人情報・プライバシー",
         "本ツールはユーザーの個人情報を収集・保存しません。"
         "お気に入り・カスタムテーマ等のデータはブラウザのセッション内にのみ保存され、サーバーには送信されません。"),
        ("📝 著作権・利用条件",
         "本ツールのソースコードは GitHub にて公開しています。非商用・個人利用の範囲で自由にご利用いただけます。"
         "商用利用・再配布の際は stockwavejp.com よりお問い合わせください。"),
    ]
    for title, body in _sections:
        st.markdown(f"""
<div style="border:1px solid #1a1e30;border-radius:10px;padding:16px 18px;margin-bottom:14px;background:#0d1020;">
  <div style="font-size:14px;font-weight:700;color:#e8eaf0;margin-bottom:8px;">{title}</div>
  <div style="font-size:12px;color:#8090a8;line-height:1.9;white-space:pre-line;">{body.strip()}</div>
</div>
""", unsafe_allow_html=True)


# ── メインエリア フッター（全ページ共通・分岐の外側） ──
st.markdown("---")
st.markdown(
    "<div style='text-align:center;font-size:11px;color:#8090a8;padding:6px 0 4px;'>"
    "© 2025 StockWaveJP — "
    "<a href='https://stockwavejp.com' style='color:#556080;text-decoration:none;' "
    "target='_blank'>stockwavejp.com</a>"
    " — 投資助言ではありません"
    "</div>",
    unsafe_allow_html=True
)
