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
    return theme_results, theme_details

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
def make_bar_chart(labels, values, colors, height=None, left_margin=None):
    """
    ランキングバーチャート。
    ラベルを「順位（固定幅）」と「テーマ名」の2列に分離し、
    annotationsで左端に順位を固定表示、yticksにテーマ名のみ表示。
    これによりテーマ名の文字数に関係なく順位が常に左端で揃う。
    """
    if not values or not labels:
        fig = go.Figure()
        fig.update_layout(height=150, paper_bgcolor="rgba(0,0,0,0)", font=dict(color="white"))
        return fig

    n = len(values)
    h = height if height else max(200, n * 34)

    # ラベルを「順位」と「テーマ名」に分割
    rank_parts = []
    name_parts = []
    for lbl in labels:
        if "　" in lbl:
            parts = lbl.split("　", 1)
        elif "  " in lbl:
            parts = lbl.split("  ", 1)
        else:
            parts = ["", lbl]
        rank_parts.append(parts[0].strip() if len(parts) == 2 else "")
        name_parts.append(parts[1].strip() if len(parts) == 2 else lbl)

    # left_marginはテーマ名の最大文字数で自動計算
    max_name_len = max(len(n) for n in name_parts)
    # 日本語1文字≒12px、余白込み
    lm = left_margin if left_margin else max(130, max_name_len * 13 + 45)

    min_v = min(values)
    max_v = max(values)
    text_positions = ["inside" if abs(v) > 4 else "outside" for v in values]

    fig = go.Figure(go.Bar(
        y=list(range(n)),
        x=values,
        orientation="h",
        marker_color=colors,
        text=[f" {v}%" for v in values],
        textposition=text_positions,
        textfont=dict(color="white", size=11),
        insidetextanchor="middle",
    ))

    # yaxisのticktextはテーマ名のみ（右揃えでバーの左端に接する）
    # 順位はannotationsで左端（x=-1のpaper座標）に固定配置
    annotations = []
    for i, (rank, name) in enumerate(zip(rank_parts, name_parts)):
        if rank:
            annotations.append(dict(
                x=0,           # xref="paper"の左端
                y=i,
                xref="paper",
                yref="y",
                text=f"<b>{rank}</b>",
                showarrow=False,
                xanchor="right",
                yanchor="middle",
                font=dict(color="white", size=10, family="Arial"),
                xshift=-8,    # テーマ名との間隔
            ))

    fig.update_layout(
        xaxis=dict(
            title="騰落率（%）", ticksuffix="%",
            zeroline=True, zerolinecolor="#555", zerolinewidth=1,
            range=[min_v * 1.2 if min_v < 0 else -1,
                   max_v * 1.2 if max_v > 0 else 1],
            tickfont=dict(size=10), title_font=dict(size=11),
        ),
        yaxis=dict(
            tickmode="array",
            tickvals=list(range(n)),
            ticktext=name_parts,   # テーマ名のみ
            autorange="reversed",
            tickfont=dict(size=11),
            ticklabelposition="outside",
        ),
        annotations=annotations,
        plot_bgcolor="rgba(0,0,0,0)", paper_bgcolor="rgba(0,0,0,0)",
        font=dict(color="white", size=11),
        height=h, bargap=0.2,
        margin=dict(t=8, b=36, l=lm, r=16),
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

    period_labels = list(PERIOD_OPTIONS.keys())
    current = st.session_state.get("selected_period", "1ヶ月")
    if current not in period_labels:
        current = "1ヶ月"

    col_sel, col_cap = st.columns([1, 3])
    with col_sel:
        selected = st.selectbox(
            "期間",
            period_labels,
            index=period_labels.index(current),
            key=f"period_sel_{key_prefix}",
            label_visibility="collapsed",
        )
    with col_cap:
        st.markdown(f"<div style='padding-top:0.5em; font-size:0.9em; color:#aaa;'>📅 選択中：<b>{selected}</b></div>",
                    unsafe_allow_html=True)

    if selected != current:
        st.session_state["selected_period"] = selected
        st.rerun()

    return PERIOD_OPTIONS[selected]

# =====================
# ページ切り替え（クリックで即切替）
# =====================
PAGES = [
    "📊 テーマ一覧",
    "📡 騰落モメンタム",
    "💹 資金フロー",
    "📈 騰落推移",
    "🔥 ヒートマップ",
    "📉 テーマ比較",
    "🌍 マクロ比較",
    "📋 市場別ランキング",
    "🔎 銘柄検索",
    "⭐ お気に入り",
    "🔍 個別株詳細",
    "🏷️ カスタムテーマ",
]
if "current_page" not in st.session_state:
    st.session_state["current_page"] = PAGES[0]

st.sidebar.markdown("### メニュー")
for _p in PAGES:
    _active = st.session_state["current_page"] == _p
    _style = "background:#ff4b4b;color:white;border-radius:4px;padding:2px 8px;" if _active else ""
    if st.sidebar.button(_p, key=f"nav_{_p}", use_container_width=True):
        st.session_state["current_page"] = _p
        st.rerun()

page = st.session_state["current_page"]

fav_count = len(st.session_state["favorites"])
if fav_count > 0:
    st.sidebar.info(f"⭐ お気に入り：{fav_count}銘柄")
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
st.sidebar.caption(f"🔄 更新頻度：約{_ttl_min}分ごと")
st.sidebar.caption(f"🕐 現在時刻(JST)：{_now_jst.strftime('%H:%M')}")

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
    period = period_buttons(key_prefix="home")

    # 表示テーマ数選択
    col_disp1, col_disp2 = st.columns([3, 1])
    with col_disp2:
        display_count = st.selectbox("表示テーマ数", [5, 10, 15, 25, 99], index=0,
                                      label_visibility="collapsed")
        st.caption(f"上位/下位 {display_count if display_count < 99 else '全'}テーマ")

    theme_keys = tuple(themes.keys())
    with st.spinner("データを取得中...（初回は時間がかかります）"):
        theme_results, theme_details = fetch_all_theme_data(period, theme_keys)

    # 表示件数に応じて上位・下位を切り出し
    n = display_count if display_count < 99 else len(theme_results)
    top_results = theme_results[:n]
    bot_results = theme_results[-n:] if display_count < 99 else []

    # === 上位テーマランキング ===
    st.subheader(f"🔴 上位{n}テーマ　騰落率ランキング")
    top_labels = [f"{i+1}位　{r['テーマ']}" for i, r in enumerate(top_results)]
    top_values = [r["平均騰落率(%)"] for r in top_results]
    top_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in top_values]
    # スクロール枠内に表示（グラフは全件分の高さ、枠でスクロール）
    chart_h = max(200, len(top_results) * 34)
    st.plotly_chart(make_bar_chart(top_labels, top_values, top_colors, height=chart_h),
                    use_container_width=True, config=PLOT_CONFIG)

    # === 下位テーマランキング ===
    if bot_results and display_count < 99:
        st.subheader(f"🟢 下位{n}テーマ　騰落率ランキング")
        total = len(theme_results)
        bot_labels = [f"{total-n+i+1}位　{r['テーマ']}" for i, r in enumerate(bot_results)]
        bot_values = [r["平均騰落率(%)"] for r in bot_results]
        bot_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in bot_values]
        chart_h2 = max(200, len(bot_results) * 34)
        st.plotly_chart(make_bar_chart(bot_labels, bot_values, bot_colors, height=chart_h2),
                        use_container_width=True, config=PLOT_CONFIG)

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
            {"順位": f"{i+1}位", "テーマ": r["テーマ"], "出来高": f"{int(r['合計出来高']):,}"}
            for i, r in enumerate(disp_vol)
        ]
        st.dataframe(pd.DataFrame(vol_rows).set_index("順位"), use_container_width=True)
        btn_label_v = "▲ 閉じる" if show_v else f"▼ 6位以下を表示（残り{len(vol_sorted_all)-5}件）"
        if st.button(btn_label_v, key="btn_vol_toggle", use_container_width=True):
            st.session_state["show_vol_all"] = not show_v
            st.rerun()

    # 売買代金ランキング
    tv_sorted_all = sorted(theme_results, key=lambda x: x["合計売買代金"], reverse=True)
    with col_rank2:
        st.markdown("**💴 テーマ別売買代金**")
        show_t = st.session_state["show_tv_all"]
        disp_tv = tv_sorted_all if show_t else tv_sorted_all[:5]
        tv_rows = [
            {"順位": f"{i+1}位", "テーマ": r["テーマ"], "売買代金": format_large_number(r["合計売買代金"])}
            for i, r in enumerate(disp_tv)
        ]
        st.dataframe(pd.DataFrame(tv_rows).set_index("順位"), use_container_width=True)
        btn_label_t = "▲ 閉じる" if show_t else f"▼ 6位以下を表示（残り{len(tv_sorted_all)-5}件）"
        if st.button(btn_label_t, key="btn_tv_toggle", use_container_width=True):
            st.session_state["show_tv_all"] = not show_t
            st.rerun()

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
    # 下部にも期間選択（長いページ対策）
    st.caption("📅 期間を変更する場合は上部の期間選択、または以下で再選択")
    period = period_buttons(key_prefix="home_bottom")
    for result in theme_results:
        theme_name = result["テーマ"]
        stocks_d = theme_details.get(theme_name, {})
        if not stocks_d: continue
        # expanderはテーマ名のみ表示、展開すると騰落率・詳細を表示
        with st.expander(f"📌 {theme_name}"):
            # 展開後に騰落率・出来高増減を表示
            c_val = result["平均騰落率(%)"]
            v_val = result["出来高増減(%)"]
            col_h1, col_h2, col_h3 = st.columns(3)
            col_h1.metric("平均騰落率", f"{'🔴 +' if c_val>0 else '🟢 '}{c_val}%")
            col_h2.metric("出来高増減", f"{'📈 +' if v_val>0 else '📉 '}{v_val}%")
            col_h3.metric("銘柄数", f"{len(stocks_d)}銘柄")
            # 証券コード付きラベル
            theme_s_map = themes.get(theme_name, {})
            s_labels = [
                f"{s}({theme_s_map.get(s,'').replace('.T','')})" if theme_s_map.get(s) else s
                for s in stocks_d.keys()
            ]
            s_values = [stocks_d[s]["change"] for s in stocks_d.keys()]
            s_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in s_values]
            st.plotly_chart(make_bar_chart(s_labels, s_values, s_colors),
                            use_container_width=True, config=PLOT_CONFIG)

            # テーマ内 個別株出来高・売買代金ランキング（順位付き）
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                st.markdown("**🔢 個別株出来高ランキング**")
                vol_rank = sorted(stocks_d.items(), key=lambda x: x[1]["volume"], reverse=True)
                vr_df = pd.DataFrame([
                    {"順位": f"{i+1}位", "銘柄": k, "出来高": f"{v['volume']:,}"}
                    for i, (k, v) in enumerate(vol_rank)
                ]).set_index("順位")
                st.dataframe(vr_df, use_container_width=True)
            with col_r2:
                st.markdown("**💴 個別株売買代金ランキング**")
                tv_rank = sorted(stocks_d.items(), key=lambda x: x[1]["trade_value"], reverse=True)
                tvr_df = pd.DataFrame([
                    {"順位": f"{i+1}位", "銘柄": k, "売買代金": format_large_number(v["trade_value"])}
                    for i, (k, v) in enumerate(tv_rank)
                ]).set_index("順位")
                st.dataframe(tvr_df, use_container_width=True)

            # 銘柄詳細テーブル（証券コード付き）
            stock_table = []
            theme_stocks_map = themes.get(theme_name, {})
            for sn, d in stocks_d.items():
                rsi = d.get("rsi")
                rsi_alert = "⚠️買" if rsi and rsi>70 else "⚠️売" if rsi and rsi<30 else "✅"
                day_c = d.get("day_change")
                ticker_raw = theme_stocks_map.get(sn, "")
                code = ticker_raw.replace(".T","") if ticker_raw else ""
                stock_table.append({
                    "銘柄": sn,
                    "証券コード": code,
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
# 騰落モメンタム
# =====================
elif page == "📡 騰落モメンタム":
    st.subheader("📡 騰落モメンタム")
    st.caption("現在の騰落率 ＋ 先週比・先月比の変化で「加速・失速・転換」テーマを一目で把握")
    period = period_buttons(key_prefix="momentum_page")

    theme_keys = tuple(themes.keys())
    with st.spinner("データ取得中..."):
        results_now, _  = fetch_all_theme_data(period, theme_keys)
        results_1w, _   = fetch_all_theme_data("5d",  theme_keys)
        results_1m, _   = fetch_all_theme_data("1mo", theme_keys)

    # 辞書化
    now_map = {r["テーマ"]: r["平均騰落率(%)"] for r in results_now}
    w1_map  = {r["テーマ"]: r["平均騰落率(%)"] for r in results_1w}
    m1_map  = {r["テーマ"]: r["平均騰落率(%)"] for r in results_1m}

    # モメンタムデータ組み立て
    momentum_data = []
    for tn in now_map:
        cur   = now_map.get(tn, 0)
        dw    = round(cur - w1_map.get(tn, cur), 2)
        dm    = round(cur - m1_map.get(tn, cur), 2)
        if   dw > 3  and dm > 5:  state = "🔥加速"
        elif dw < -3 and dm < -5: state = "❄️失速"
        elif dw > 2:               state = "↗転換↑"
        elif dw < -2:              state = "↘転換↓"
        else:                      state = "→横ばい"
        momentum_data.append({"テーマ": tn, "騰落率": cur, "先週比": dw, "先月比": dm, "状態": state})

    # 並び替え選択
    sort_key = st.selectbox("並び替え", ["騰落率（高→低）","先週比変化（大→小）","先月比変化（大→小）"],
                             label_visibility="collapsed")
    if sort_key == "騰落率（高→低）":
        momentum_data.sort(key=lambda x: x["騰落率"], reverse=True)
    elif sort_key == "先週比変化（大→小）":
        momentum_data.sort(key=lambda x: x["先週比"], reverse=True)
    else:
        momentum_data.sort(key=lambda x: x["先月比"], reverse=True)

    # フィルター
    filter_state = st.multiselect("状態フィルター（空=全表示）",
                                   ["🔥加速","↗転換↑","→横ばい","↘転換↓","❄️失速"])
    if filter_state:
        momentum_data = [d for d in momentum_data if d["状態"] in filter_state]

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
        col3.write(f"{dw_icon} {dw_sign}{dw}")
        col4.write(f"{dw_icon} {dm_sign}{dm}")
        col5.write(state)

    st.caption("💡 先週比・先月比ともプラス加速=🔥加速 / 両方マイナス=❄️失速 / 直近だけ転換=↗↘転換")

# =====================
# 資金フロー
# =====================
elif page == "💹 資金フロー":
    st.subheader("💹 テーマ別 資金フロー")
    st.caption("上昇テーマ vs 下落テーマの騰落幅を比較。どのテーマに資金が集まっているか把握できます。")
    period = period_buttons(key_prefix="flow_page")

    theme_keys = tuple(themes.keys())
    with st.spinner("データ取得中..."):
        flow_results, _ = fetch_all_theme_data(period, theme_keys)

    flow_sorted = sorted(flow_results, key=lambda x: x["平均騰落率(%)"], reverse=True)
    gainers = flow_sorted[:10]
    losers  = flow_sorted[-10:][::-1]

    col_g, col_l = st.columns(2)
    with col_g:
        st.markdown("### 🔥 資金流入テーマ TOP10")
        g_labels = [f"{i+1}位　{r['テーマ']}" for i, r in enumerate(gainers)]
        g_values = [r["平均騰落率(%)"] for r in gainers]
        g_colors = ["#ff4b4b"] * len(gainers)
        st.plotly_chart(make_bar_chart(g_labels, g_values, g_colors,
                                       height=max(200, len(gainers)*34)),
                        use_container_width=True, config=PLOT_CONFIG)

    with col_l:
        st.markdown("### ❄️ 資金流出テーマ TOP10")
        total = len(flow_sorted)
        l_labels = [f"{total-len(losers)+i+1}位　{r['テーマ']}" for i, r in enumerate(losers)]
        l_values = [r["平均騰落率(%)"] for r in losers]
        l_colors = ["#39d353"] * len(losers)
        st.plotly_chart(make_bar_chart(l_labels, l_values, l_colors,
                                       height=max(200, len(losers)*34)),
                        use_container_width=True, config=PLOT_CONFIG)

    # 全テーマ騰落バブル的な横棒グラフ（全テーマ一覧）
    st.markdown("---")
    st.markdown("**📊 全テーマ 騰落率一覧（資金フロー全景）**")
    all_labels = [f"{i+1}位　{r['テーマ']}" for i, r in enumerate(flow_sorted)]
    all_values = [r["平均騰落率(%)"] for r in flow_sorted]
    all_colors = ["#ff4b4b" if v >= 0 else "#39d353" for v in all_values]
    st.plotly_chart(make_bar_chart(all_labels, all_values, all_colors,
                                   height=max(400, len(flow_sorted)*28)),
                    use_container_width=True, config=PLOT_CONFIG)

# =====================
# 騰落推移（yfinance日次データ版）
# =====================
elif page == "📈 騰落推移":
    st.subheader("📈 テーマ別 騰落率の推移")
    st.caption(f"🕐 最終更新：{now}　|　yfinanceの日次終値から算出（スプレッドシート不要）")

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
        for tn, s in trend_data.items():
            if s is not None and len(s) > 0:
                final_changes[tn] = s.iloc[-1]

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
        if mode == "🏆 上位5＋ワースト5":
            selected = default_sel
        elif mode == "✅ テーマを手動選択":
            selected = st.multiselect(
                "表示テーマを選択",
                all_theme_names,
                default=default_sel,
                key="trend_manual_sel",
            )
        else:
            selected = all_theme_names

        if not selected:
            st.info("テーマを1つ以上選択してください。")
        else:
            fig = go.Figure()
            colors = [
                "#ff4b4b","#ff9955","#ffdd55","#55dd99","#55aaff",
                "#aa77ff","#ff77aa","#44dddd","#aaddff","#ffaa77",
                "#88ff88","#ff6688","#66aaff","#ffcc44","#99ffcc",
            ]
            for i, tn in enumerate(selected):
                if tn not in trend_data:
                    continue
                s = trend_data[tn]
                if s is None or len(s) < 2:
                    continue
                color = colors[i % len(colors)]
                final_val = s.iloc[-1]
                sign = "+" if final_val >= 0 else ""
                fig.add_trace(go.Scatter(
                    x=s.index,
                    y=s.values,
                    mode="lines",
                    name=f"{tn}（{sign}{final_val:.1f}%）",
                    line=dict(width=2, color=color),
                    hovertemplate="%{x|%Y/%m/%d}<br>%{y:.2f}%<extra>" + tn + "</extra>",
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
            st.markdown(f"**📋 テーマ騰落率ランキング（{trend_period}）**")
            rank_df = pd.DataFrame([
                {"順位": i+1, "テーマ": t, f"騰落率（{trend_period}）": f"{v:+.2f}%"}
                for i, (t, v) in enumerate(sorted_themes)
            ])
            st.dataframe(rank_df.set_index("順位"), use_container_width=True, height=min(600, len(rank_df)*36+40))

            # CSV出力
            csv_data = []
            for tn in all_theme_names:
                if tn in trend_data and trend_data[tn] is not None:
                    s = trend_data[tn]
                    for date, val in s.items():
                        csv_data.append({"日付": date.strftime("%Y-%m-%d"), "テーマ": tn, "騰落率(%)": val})
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
elif page == "🔥 ヒートマップ":
    st.subheader("🔥 テーマ別騰落率 ヒートマップ")
    st.caption(f"🕐 最終更新：{now}")

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
        st.download_button("📥 CSV", df_heat.to_csv(encoding="utf-8-sig"), f"ヒートマップ_{now}.csv", "text/csv")

    # ============================================================
    # タブ2: 月次推移ヒートマップ（過去12ヶ月・月単位）
    # ============================================================
    with tab_monthly:
        st.markdown("**過去12ヶ月の月別騰落率** 🔴赤=上昇　🟢緑=下落")
        st.caption("各月の始値→終値の騰落率（テーマ内銘柄の平均）")
        with st.spinner("月次データ取得中...（少し時間がかかります）"):
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
        st.markdown("**📋 月次騰落率テーブル**")
        df_m_disp = df_monthly.copy()
        df_m_disp.columns = short_months
        df_m_disp = df_m_disp.applymap(lambda v: f"+{v:.1f}%" if v and v>0 else f"{v:.1f}%" if v else "N/A")
        st.dataframe(df_m_disp, use_container_width=True, height=min(500, n_t*35+40))
        st.download_button("📥 月次CSV", df_monthly.to_csv(encoding="utf-8-sig"), f"月次ヒートマップ_{now}.csv", "text/csv")

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
            for idx, tn in enumerate(selected_line_themes):
                if tn not in df_heat2.index: continue
                vals = [df_heat2.loc[tn, col] for col in period_cols]
                fig_line.add_trace(go.Scatter(
                    x=period_cols, y=vals, mode="lines+markers", name=tn,
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

elif page == "📉 テーマ比較":
    st.subheader("📉 テーマ間比較チャート")
    period = period_buttons(key_prefix="comp")
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
    period = period_buttons(key_prefix="macro")
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
elif page == "📋 市場別ランキング":
    st.subheader("📋 市場別ランキング")
    st.caption("日経225・プライム・スタンダード・グロース別の騰落率ランキング")
    period = period_buttons(key_prefix="market")

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
                n_seg = len(seg_results)

                # 上位5件グラフ
                top5 = seg_results[:5]
                bot5 = seg_results[-5:] if n_seg > 5 else []

                col_t, col_b = st.columns(2)
                with col_t:
                    st.markdown("**🔴 上位5銘柄**")
                    t_labels = [f"{i+1}位 {r['銘柄']}" for i, r in enumerate(top5)]
                    t_values = [r["騰落率"] for r in top5]
                    t_colors = ["#ff4b4b" if v>=0 else "#39d353" for v in t_values]
                    st.plotly_chart(make_bar_chart(t_labels, t_values, t_colors),
                                    use_container_width=True, config=PLOT_CONFIG)
                with col_b:
                    if bot5:
                        st.markdown("**🟢 下位5銘柄**")
                        b_labels = [f"{n_seg-4+i}位 {r['銘柄']}" for i, r in enumerate(bot5)]
                        b_values = [r["騰落率"] for r in bot5]
                        b_colors = ["#ff4b4b" if v>=0 else "#39d353" for v in b_values]
                        st.plotly_chart(make_bar_chart(b_labels, b_values, b_colors),
                                        use_container_width=True, config=PLOT_CONFIG)

                # 上位5件テーブル
                df_top5 = pd.DataFrame([{
                    "銘柄": r["銘柄"], "株価": r["株価"], "前日比": r["前日比"],
                    "騰落率": f"🔴 +{r['騰落率']}%" if r["騰落率"]>0 else f"🟢 {r['騰落率']}%",
                    "売買代金": r["売買代金"],
                } for r in top5]).set_index("銘柄")
                st.dataframe(df_top5, use_container_width=True)

                # 全件展開
                with st.expander(f"全{n_seg}銘柄を表示"):
                    df_all_seg = pd.DataFrame([{
                        "順位": f"{i+1}位",
                        "銘柄": r["銘柄"], "株価": r["株価"], "前日比": r["前日比"],
                        "騰落率": f"🔴 +{r['騰落率']}%" if r["騰落率"]>0 else f"🟢 {r['騰落率']}%",
                        "売買代金": r["売買代金"],
                    } for i, r in enumerate(seg_results)]).set_index("順位")
                    st.dataframe(df_all_seg, use_container_width=True)

# =====================
# 銘柄検索
# =====================
elif page == "🔎 銘柄検索":
    st.subheader("🔎 銘柄検索")
    period = period_buttons(key_prefix="search")
    query = st.text_input("銘柄名を入力", placeholder="例：トヨタ、ソニー、三菱...")
    theme_filter = st.multiselect("テーマで絞り込む（任意）", list(themes.keys()))

    search_targets = {}
    for tn, stocks_s in themes.items():
        if theme_filter and tn not in theme_filter: continue
        for sn, ticker in stocks_s.items():
            search_targets[sn] = {"ticker":ticker,"theme":tn}

    # 検索ワードがある時だけ結果表示
    if not query:
        st.info("🔍 上の検索ボックスに銘柄名を入力してください")
    else:
        matched = {k:v for k,v in search_targets.items() if query in k}
        st.caption(f"該当銘柄：{len(matched)}件")
        if not matched:
            st.warning("該当する銘柄が見つかりませんでした")
        else:
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
                        code = info["ticker"].replace(".T","")
                        results.append({
                            "銘柄":sn,
                            "証券コード": code,
                            "テーマ":info["theme"],
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
                    with col1:
                        st.write(f"**{r['銘柄']}**（{r['証券コード']}）　{r['テーマ']}　{r['騰落率']}")
                    with col2:
                        if st.button("📈 詳細", key=f"sc_{r['銘柄']}"):
                            st.session_state["selected_stock"] = r["銘柄"]
                            st.session_state["selected_ticker"] = r["ticker"]
                            st.session_state["current_page"] = "🔍 個別株詳細"
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
    period = period_buttons(key_prefix="fav")
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
    period = period_buttons(key_prefix="detail")
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
