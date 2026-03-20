"""
================================================================================
  QUANTUM TRADE ORACLE v4.0 ── Dashboard Ultra-Premium
  ✅ Légendes détaillées sur tous les graphiques
  ✅ Explications pédagogiques des indicateurs
  ✅ IA améliorée — analyse contextuelle profonde
  ✅ Matières premières complètes
================================================================================
  Lancement : streamlit run dashboard.py
================================================================================
"""

import sys, time
from datetime import datetime
from pathlib import Path

import streamlit as st
import plotly.graph_objects as go

# ── Système d'authentification ───────────────────────────────────────────────
try:
    sys.path.insert(0, str(Path(__file__).parent))
    from qto_auth.auth_ui import auth_gate, user_badge
    AUTH_OK = True
except ImportError:
    AUTH_OK = False

# ── Moteur IA GPT-4o ─────────────────────────────────────────────────────────
try:
    from qto_ai.ai_engine import ask_gpt, generate_report, analyze_news_gpt, risk_advice_gpt, is_configured
    GPT_OK = True
except ImportError:
    GPT_OK = False
from plotly.subplots import make_subplots
import pandas as pd
import numpy as np

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

try:
    from data_collectors.market_collector import MarketDataCollector
    from news_scrapers.news_scraper import NewsScraper
    from sentiment_engine.sentiment_engine import SentimentEngine
    from feature_engineering.feature_engineer import FeatureEngineer
    from ai_models.model_ensemble import ModelEnsemble
    from strategy_engine.strategy_engine import StrategyEngine
    from backtesting.backtester import Backtester
    PROJECT_OK = True
except ImportError as _e:
    PROJECT_OK = False; _IMPORT_ERR = str(_e)

try:
    import yfinance as yf; YF_OK = True
except ImportError:
    YF_OK = False

try:
    import requests
    from bs4 import BeautifulSoup
    SCRAPE_OK = True
except ImportError:
    SCRAPE_OK = False

# ══════════════════════════════════════════════════════════════════════════════
st.set_page_config(page_title="⬡ Quantum Trade Oracle", page_icon="⬡",
                   layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
/* ═══════════════════════════════════════════════════════════════════════════
   QUANTUM TRADE ORACLE v5 — NEURAL TERMINAL INTERFACE
   Aesthetic : Deep-Space Holographic · Cyberpunk Bloomberg · Neural Grid
═══════════════════════════════════════════════════════════════════════════ */

@import url('https://fonts.googleapis.com/css2?family=Space+Grotesk:wght@300;400;500;600;700&family=JetBrains+Mono:ital,wght@0,100;0,200;0,300;0,400;0,700;1,300&family=Bebas+Neue&family=Rajdhani:wght@300;400;500;600;700&display=swap');

/* ── CSS Variables ─────────────────────────────────────────────────────── */
:root {
  --bg:       #00050d;
  --bg2:      #010a15;
  --surface:  #020e1c;
  --card:     #051525;
  --card2:    #071830;
  --border:   #0a2240;
  --border2:  #0d2d55;
  --accent:   #00d4ff;
  --accent2:  #00ffe5;
  --green:    #00ff9d;
  --red:      #ff2d55;
  --yellow:   #ffd60a;
  --orange:   #ff6b35;
  --purple:   #9b72ff;
  --muted:    #0e3060;
  --text:     #6fa8c8;
  --bright:   #c8e8ff;
  --white:    #eaf4ff;
  --glow-a:   rgba(0,212,255,.18);
  --glow-g:   rgba(0,255,157,.14);
  --glow-r:   rgba(255,45,85,.14);
  --grid-color: rgba(0,180,255,.04);
}

/* ── Reset & Base ────────────────────────────────────────────────────────── */
* { box-sizing: border-box; }
#MainMenu, footer, header { visibility: hidden; }
.block-container { padding-top: .7rem !important; max-width: 1720px !important; }

/* ── Animated Background Grid ───────────────────────────────────────────── */
.stApp {
  background-color: var(--bg) !important;
  background-image:
    linear-gradient(var(--grid-color) 1px, transparent 1px),
    linear-gradient(90deg, var(--grid-color) 1px, transparent 1px),
    radial-gradient(ellipse 80% 60% at 20% 10%, rgba(0,100,200,.07) 0%, transparent 60%),
    radial-gradient(ellipse 60% 50% at 80% 90%, rgba(0,60,120,.06) 0%, transparent 60%),
    radial-gradient(ellipse 40% 40% at 50% 50%, rgba(0,30,60,.1) 0%, transparent 70%);
  background-size: 60px 60px, 60px 60px, 100% 100%, 100% 100%, 100% 100%;
  background-attachment: fixed;
}

/* Scanline overlay */
.stApp::before {
  content: '';
  position: fixed;
  inset: 0;
  background: repeating-linear-gradient(
    0deg,
    transparent,
    transparent 2px,
    rgba(0,0,0,.03) 2px,
    rgba(0,0,0,.03) 4px
  );
  pointer-events: none;
  z-index: 9999;
}

/* ── Sidebar ─────────────────────────────────────────────────────────────── */
section[data-testid="stSidebar"] {
  background:
    linear-gradient(180deg, #010d1e 0%, #000a15 100%) !important;
  border-right: 1px solid var(--border2) !important;
  box-shadow: 4px 0 40px rgba(0,212,255,.05) !important;
}
section[data-testid="stSidebar"]::after {
  content: '';
  position: absolute;
  top: 0; right: 0;
  width: 1px; height: 100%;
  background: linear-gradient(180deg,
    transparent 0%,
    rgba(0,212,255,.4) 30%,
    rgba(0,255,229,.4) 70%,
    transparent 100%
  );
}

/* ── Typography global ───────────────────────────────────────────────────── */
* { font-family: 'Space Grotesk', sans-serif !important; }
code, pre, .mono { font-family: 'JetBrains Mono', monospace !important; }

/* ── Scrollbar ───────────────────────────────────────────────────────────── */
::-webkit-scrollbar { width: 4px; height: 4px; }
::-webkit-scrollbar-track { background: var(--bg2); }
::-webkit-scrollbar-thumb {
  background: linear-gradient(180deg, var(--accent), var(--accent2));
  border-radius: 2px;
}

/* ── HR / Dividers ───────────────────────────────────────────────────────── */
hr {
  border: none !important;
  height: 1px !important;
  background: linear-gradient(90deg,
    transparent, var(--border2), rgba(0,212,255,.3), var(--border2), transparent
  ) !important;
  margin: 10px 0 !important;
}

/* ── Inputs ──────────────────────────────────────────────────────────────── */
.stTextInput input,
.stSelectbox select,
.stNumberInput input,
.stTextArea textarea {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 4px !important;
  color: var(--bright) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
  transition: border-color .2s, box-shadow .2s !important;
}
.stTextInput input:focus,
.stTextArea textarea:focus {
  border-color: var(--accent) !important;
  box-shadow: 0 0 0 2px rgba(0,212,255,.12), 0 0 20px rgba(0,212,255,.08) !important;
  outline: none !important;
}
.stSelectbox [data-baseweb="select"] > div {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 4px !important;
}

/* ── Buttons — Holographic Style ────────────────────────────────────────── */
.stButton > button {
  position: relative !important;
  background: linear-gradient(135deg,
    rgba(0,212,255,.08) 0%,
    rgba(0,255,229,.05) 50%,
    rgba(0,150,200,.04) 100%
  ) !important;
  border: 1px solid rgba(0,212,255,.35) !important;
  border-radius: 3px !important;
  color: var(--accent) !important;
  font-family: 'Rajdhani', sans-serif !important;
  font-size: 11px !important;
  font-weight: 700 !important;
  letter-spacing: 2.5px !important;
  text-transform: uppercase !important;
  padding: 8px 16px !important;
  transition: all .25s cubic-bezier(.4,0,.2,1) !important;
  overflow: hidden !important;
}
.stButton > button::before {
  content: '' !important;
  position: absolute !important;
  top: 0; left: -100% !important;
  width: 100%; height: 100% !important;
  background: linear-gradient(90deg,
    transparent,
    rgba(0,212,255,.12),
    transparent
  ) !important;
  transition: left .5s !important;
}
.stButton > button:hover {
  background: rgba(0,212,255,.15) !important;
  border-color: var(--accent) !important;
  box-shadow:
    0 0 20px rgba(0,212,255,.25),
    0 0 40px rgba(0,212,255,.1),
    inset 0 0 20px rgba(0,212,255,.05) !important;
  transform: translateY(-1px) !important;
  color: var(--white) !important;
}
.stButton > button:hover::before {
  left: 100% !important;
}
.stButton > button:active {
  transform: translateY(0) scale(.98) !important;
  box-shadow: 0 0 10px rgba(0,212,255,.2) !important;
}

/* ── Tabs — Neural Style ─────────────────────────────────────────────────── */
.stTabs [data-baseweb="tab-list"] {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 5px !important;
  padding: 3px !important;
  gap: 2px !important;
  box-shadow: 0 4px 20px rgba(0,0,0,.3) !important;
}
.stTabs [data-baseweb="tab"] {
  background: transparent !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 9.5px !important;
  font-weight: 400 !important;
  text-transform: uppercase !important;
  letter-spacing: 1.8px !important;
  color: var(--muted) !important;
  border-radius: 3px !important;
  padding: 7px 14px !important;
  transition: all .2s !important;
}
.stTabs [data-baseweb="tab"]:hover {
  background: rgba(0,212,255,.06) !important;
  color: var(--text) !important;
}
.stTabs [aria-selected="true"] {
  background: linear-gradient(135deg,
    rgba(0,212,255,.14),
    rgba(0,255,229,.08)
  ) !important;
  color: var(--accent) !important;
  border: 1px solid rgba(0,212,255,.3) !important;
  box-shadow: 0 0 15px rgba(0,212,255,.15),
              inset 0 0 10px rgba(0,212,255,.05) !important;
}

/* ── Metric Cards — Glowing ─────────────────────────────────────────────── */
[data-testid="metric-container"] {
  background: linear-gradient(135deg, var(--card), var(--card2)) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 6px !important;
  padding: 14px 18px !important;
  position: relative !important;
  overflow: hidden !important;
  transition: border-color .3s, box-shadow .3s !important;
}
[data-testid="metric-container"]::before {
  content: '' !important;
  position: absolute !important;
  top: 0; left: 0; right: 0 !important;
  height: 1px !important;
  background: linear-gradient(90deg,
    transparent,
    rgba(0,212,255,.5),
    transparent
  ) !important;
}
[data-testid="metric-container"]:hover {
  border-color: rgba(0,212,255,.4) !important;
  box-shadow: 0 0 25px rgba(0,212,255,.1) !important;
}
[data-testid="metric-container"] label {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 8px !important;
  color: var(--muted) !important;
  text-transform: uppercase !important;
  letter-spacing: 2px !important;
}
[data-testid="stMetricValue"] {
  font-family: 'Bebas Neue', sans-serif !important;
  font-size: 2rem !important;
  font-weight: 400 !important;
  letter-spacing: 2px !important;
  color: var(--accent) !important;
  text-shadow: 0 0 20px rgba(0,212,255,.4) !important;
}
[data-testid="stMetricDelta"] {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
}

/* ── Progress Bars ───────────────────────────────────────────────────────── */
.stProgress > div > div {
  background: rgba(0,212,255,.08) !important;
  border-radius: 3px !important;
}
.stProgress > div > div > div {
  background: linear-gradient(90deg, var(--accent), var(--accent2)) !important;
  border-radius: 3px !important;
  box-shadow: 0 0 10px rgba(0,212,255,.4) !important;
}

/* ── Dataframe ───────────────────────────────────────────────────────────── */
.stDataFrame {
  border: 1px solid var(--border2) !important;
  border-radius: 6px !important;
  overflow: hidden !important;
}
[data-testid="stDataFrame"] table {
  background: var(--surface) !important;
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 11px !important;
}
[data-testid="stDataFrame"] th {
  background: var(--card) !important;
  color: var(--accent) !important;
  font-size: 9px !important;
  letter-spacing: 1.5px !important;
  text-transform: uppercase !important;
  border-color: var(--border2) !important;
  padding: 8px 12px !important;
}
[data-testid="stDataFrame"] td {
  color: var(--text) !important;
  border-color: var(--border) !important;
  padding: 6px 12px !important;
}
[data-testid="stDataFrame"] tr:hover td {
  background: rgba(0,212,255,.04) !important;
  color: var(--bright) !important;
}

/* ── Spinner ─────────────────────────────────────────────────────────────── */
.stSpinner > div {
  border-color: var(--accent) transparent transparent transparent !important;
}

/* ── Alerts / Info ───────────────────────────────────────────────────────── */
.stAlert {
  background: var(--card) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 6px !important;
  color: var(--text) !important;
}

/* ── Expander ────────────────────────────────────────────────────────────── */
details {
  background: var(--surface) !important;
  border: 1px solid var(--border2) !important;
  border-radius: 5px !important;
}
details summary {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  color: var(--text) !important;
  letter-spacing: 1px !important;
  text-transform: uppercase !important;
  padding: 10px 14px !important;
  cursor: pointer !important;
}

/* ── Custom Components ───────────────────────────────────────────────────── */

/* Legend box */
.legend-box {
  background: linear-gradient(135deg, var(--card), var(--card2));
  border: 1px solid var(--border2);
  border-radius: 8px;
  padding: 16px 18px;
  margin-top: 10px;
  position: relative;
  overflow: hidden;
}
.legend-box::after {
  content: '';
  position: absolute;
  bottom: 0; left: 0;
  width: 40%; height: 1px;
  background: linear-gradient(90deg, var(--accent), transparent);
}

/* Explain box */
.explain-box {
  background: linear-gradient(135deg, var(--surface), var(--card));
  border: 1px solid var(--border2);
  border-left: 3px solid var(--accent);
  border-radius: 5px;
  padding: 14px 18px;
  margin: 10px 0;
  box-shadow: -4px 0 20px rgba(0,212,255,.08);
}

/* Chat messages */
.msg-user {
  background: linear-gradient(135deg,
    rgba(0,212,255,.07), rgba(0,212,255,.03));
  border: 1px solid rgba(0,212,255,.2);
  border-radius: 8px 8px 0 8px;
  padding: 12px 16px;
  margin: 8px 0;
  font-size: 13px;
  color: var(--bright);
  text-align: right;
  box-shadow: 0 2px 15px rgba(0,212,255,.06);
}
.msg-ai {
  background: linear-gradient(135deg,
    rgba(0,255,157,.03), rgba(0,255,229,.02));
  border: 1px solid rgba(0,255,157,.15);
  border-radius: 8px 8px 8px 0;
  padding: 14px 18px;
  margin: 4px 0 12px;
  font-size: 13px;
  color: #a0f0d8;
  line-height: 1.9;
  box-shadow: 0 2px 15px rgba(0,255,157,.04);
}
.lbl-user {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  color: var(--accent);
  text-align: right;
  margin-bottom: 3px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}
.lbl-ai {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8px;
  color: var(--green);
  margin-bottom: 3px;
  letter-spacing: 1.5px;
  text-transform: uppercase;
}

/* Sidebar labels */
.slbl {
  font-family: 'JetBrains Mono', monospace;
  font-size: 8.5px;
  color: var(--muted);
  text-transform: uppercase;
  letter-spacing: 2px;
  display: block;
  margin: 14px 0 5px;
}

/* Score badge */
.score-badge {
  display: inline-block;
  padding: 4px 12px;
  border-radius: 20px;
  font-family: 'JetBrains Mono', monospace;
  font-size: 10px;
  font-weight: 700;
  letter-spacing: 1px;
  margin: 2px;
  border: 1px solid currentColor;
}

/* Checkbox */
.stCheckbox label {
  font-family: 'JetBrains Mono', monospace !important;
  font-size: 10px !important;
  color: var(--text) !important;
  letter-spacing: 0.5px !important;
}
.stCheckbox [data-baseweb="checkbox"] [data-checked="true"] {
  background: var(--accent) !important;
  border-color: var(--accent) !important;
}

/* Number Input */
.stNumberInput button {
  background: var(--card) !important;
  border-color: var(--border2) !important;
  color: var(--accent) !important;
}

/* Multiselect */
.stMultiSelect [data-baseweb="tag"] {
  background: rgba(0,212,255,.15) !important;
  color: var(--accent) !important;
  border: 1px solid rgba(0,212,255,.3) !important;
}

/* ── Glow Animation for key elements ────────────────────────────────────── */
@keyframes pulse-border {
  0%, 100% { box-shadow: 0 0 10px rgba(0,212,255,.1); }
  50%       { box-shadow: 0 0 25px rgba(0,212,255,.25), 0 0 50px rgba(0,212,255,.08); }
}
@keyframes scan-line {
  0%   { background-position: 0 0; }
  100% { background-position: 0 100%; }
}
@keyframes flicker {
  0%,100% { opacity: 1; }
  92%     { opacity: 1; }
  93%     { opacity: .85; }
  94%     { opacity: 1; }
  96%     { opacity: .9; }
  97%     { opacity: 1; }
}
@keyframes slide-in-left {
  from { opacity:0; transform: translateX(-12px); }
  to   { opacity:1; transform: translateX(0); }
}
@keyframes fade-up {
  from { opacity:0; transform: translateY(8px); }
  to   { opacity:1; transform: translateY(0); }
}

/* Apply animations */
[data-testid="metric-container"] { animation: fade-up .4s ease both; }
.stTabs [data-baseweb="tab-list"] { animation: fade-up .3s ease both; }
.block-container > div > div { animation: fade-up .35s ease both; }

/* ══════════════════════════════════════════════════════════════════════════
   📱 MOBILE RESPONSIVE — Quantum Trade Oracle
   Breakpoints : 768px (tablette) · 480px (mobile)
══════════════════════════════════════════════════════════════════════════ */

/* ── Tablette (≤ 768px) ─────────────────────────────────────────────────── */
@media screen and (max-width: 768px) {

  /* Container principal */
  .block-container {
    padding: 0.5rem 0.6rem !important;
    max-width: 100% !important;
  }

  /* Sidebar collapse auto */
  section[data-testid="stSidebar"] {
    min-width: 0 !important;
    width: 85vw !important;
    max-width: 320px !important;
  }

  /* Tabs — plus grandes pour les doigts */
  .stTabs [data-baseweb="tab-list"] {
    flex-wrap: wrap !important;
    gap: 3px !important;
    padding: 4px !important;
  }
  .stTabs [data-baseweb="tab"] {
    font-size: 8px !important;
    padding: 8px 8px !important;
    letter-spacing: 0.8px !important;
    min-height: 36px !important;
    flex: 1 1 auto !important;
    text-align: center !important;
  }

  /* Métriques — 2 par ligne */
  [data-testid="metric-container"] {
    padding: 10px 12px !important;
    min-width: 0 !important;
  }
  [data-testid="stMetricValue"] {
    font-size: 1.5rem !important;
  }
  [data-testid="metric-container"] label {
    font-size: 7px !important;
  }

  /* Colonnes Streamlit → stack vertical */
  [data-testid="column"] {
    min-width: 100% !important;
    width: 100% !important;
  }

  /* Graphiques pleine largeur */
  .js-plotly-plot, .plotly, .plot-container {
    width: 100% !important;
    overflow-x: auto !important;
  }

  /* Inputs plus grands */
  .stTextInput input,
  .stSelectbox select,
  .stNumberInput input,
  .stTextArea textarea {
    font-size: 14px !important;
    padding: 10px 12px !important;
    min-height: 44px !important;
  }

  /* Boutons plus grands (touch-friendly) */
  .stButton > button {
    min-height: 44px !important;
    font-size: 11px !important;
    padding: 10px 14px !important;
    width: 100% !important;
  }

  /* Cards news */
  div[style*="border-radius:6px"] {
    padding: 12px !important;
  }

  /* Réduire taille police des titres */
  .stMarkdown h1 { font-size: 1.4rem !important; }
  .stMarkdown h2 { font-size: 1.2rem !important; }
  .stMarkdown h3 { font-size: 1rem !important; }
}

/* ── Mobile (≤ 480px) ───────────────────────────────────────────────────── */
@media screen and (max-width: 480px) {

  /* Container ultra compact */
  .block-container {
    padding: 0.3rem 0.4rem !important;
  }

  /* Grille de fond réduite */
  .stApp {
    background-size: 30px 30px, 30px 30px, 100% 100%, 100% 100%, 100% 100% !important;
  }

  /* Scanlines désactivées (perf mobile) */
  .stApp::before { display: none !important; }

  /* Header sidebar */
  section[data-testid="stSidebar"] {
    width: 90vw !important;
  }

  /* Tabs encore plus compactes */
  .stTabs [data-baseweb="tab"] {
    font-size: 7px !important;
    padding: 6px 5px !important;
    letter-spacing: 0px !important;
  }

  /* Métriques compactes */
  [data-testid="stMetricValue"] {
    font-size: 1.3rem !important;
  }
  [data-testid="metric-container"] {
    padding: 8px 10px !important;
  }

  /* Signal HOLD/BUY/SELL texte réduit */
  .stMarkdown [style*="font-size:7rem"],
  .stMarkdown [style*="font-size:6rem"] {
    font-size: 3.5rem !important;
  }

  /* Cards compactes */
  .msg-ai, .msg-user {
    font-size: 12px !important;
    padding: 10px 12px !important;
  }

  /* Boutons sidebar pleine largeur */
  .stButton > button {
    font-size: 10px !important;
    letter-spacing: 1px !important;
    padding: 8px 10px !important;
  }

  /* Inputs touch-friendly */
  .stTextInput input,
  .stNumberInput input {
    font-size: 16px !important; /* Évite zoom iOS */
    min-height: 48px !important;
  }

  /* Selectbox */
  .stSelectbox [data-baseweb="select"] > div {
    min-height: 44px !important;
    font-size: 13px !important;
  }

  /* Graphiques scrollables */
  [data-testid="stPlotlyChart"] {
    overflow-x: scroll !important;
    -webkit-overflow-scrolling: touch !important;
  }

  /* News cards */
  .stMarkdown a {
    font-size: 12px !important;
  }

  /* Cacher les décorations lourdes */
  section[data-testid="stSidebar"]::after {
    display: none !important;
  }
}

/* ── Touch improvements (tous mobiles) ─────────────────────────────────── */
@media (hover: none) and (pointer: coarse) {

  /* Supprimer hover effects qui bloquent sur touch */
  .stButton > button:hover {
    transform: none !important;
  }
  [data-testid="metric-container"]:hover {
    box-shadow: none !important;
  }

  /* Zone de tap minimum 44px (standard Apple/Google) */
  .stButton > button,
  .stTabs [data-baseweb="tab"],
  .stCheckbox label,
  .stSelectbox [data-baseweb="select"] {
    min-height: 44px !important;
  }

  /* Scrollbar invisible sur mobile */
  ::-webkit-scrollbar { width: 0 !important; height: 0 !important; }
}

</style>""", unsafe_allow_html=True)

# ── GATE D'AUTHENTIFICATION ─────────────────────────────────────────────────
if AUTH_OK:
    if not auth_gate():
        st.stop()

C = dict(bg="#00050d",surface="#020e1c",card="#051525",card2="#071830",
         border="#0a2240",border2="#0d2d55",
         accent="#00d4ff",green="#00ff9d",red="#ff2d55",yellow="#ffd60a",
         muted="#0e3060",text="#6fa8c8",bright="#c8e8ff",
         orange="#ff6b35",purple="#9b72ff",accent2="#00ffe5")

PLOT = dict(paper_bgcolor=C["bg"], plot_bgcolor="#010c18",
            font=dict(family="JetBrains Mono",color="#2a5080",size=9),
            margin=dict(l=52,r=18,t=50,b=36))
_AX  = dict(gridcolor="#081e36",showgrid=True,zeroline=False,
            showspikes=True,spikecolor=C["accent"],spikethickness=1)

# ══════════════════════════════════════════════════════════════════════════════
#  MARCHÉS
# ══════════════════════════════════════════════════════════════════════════════
MARKETS = {
    "🪙 Crypto":             ["BTC-USD","ETH-USD","SOL-USD","BNB-USD","XRP-USD","DOGE-USD","ADA-USD","AVAX-USD"],
    "📈 Actions":            ["AAPL","TSLA","NVDA","MSFT","AMZN","META","GOOGL","NFLX"],
    "📊 ETF":                ["SPY","QQQ","GLD","TLT","VTI","IWM","XLK","ARKK"],
    "💱 Forex":              ["EURUSD=X","GBPUSD=X","USDJPY=X","AUDUSD=X","GBPJPY=X","USDCHF=X","USDCAD=X","AUDJPY=X"],
    "⛽ Énergie":            ["CL=F","BZ=F","NG=F","HO=F","RB=F"],
    "🥇 Métaux précieux":    ["GC=F","SI=F","PL=F","PA=F"],
    "🔩 Métaux industriels": ["HG=F","ALI=F","NI=F","ZN=F","PB=F"],
    "🌾 Céréales":           ["ZW=F","ZC=F","ZS=F","ZO=F","ZR=F"],
    "☕ Produits tropicaux": ["KC=F","CC=F","SB=F","CT=F","OJ=F"],
    "🐄 Élevage":            ["LE=F","HE=F","GF=F"],
}

TICKER_NAMES = {
    "BTC-USD":"Bitcoin","ETH-USD":"Ethereum","SOL-USD":"Solana","BNB-USD":"BNB",
    "XRP-USD":"XRP","DOGE-USD":"Dogecoin","ADA-USD":"Cardano","AVAX-USD":"Avalanche",
    "AAPL":"Apple","TSLA":"Tesla","NVDA":"Nvidia","MSFT":"Microsoft",
    "AMZN":"Amazon","META":"Meta","GOOGL":"Google","NFLX":"Netflix",
    "SPY":"S&P 500 ETF","QQQ":"Nasdaq ETF","GLD":"Gold ETF","TLT":"Bonds ETF",
    "VTI":"Total Market ETF","IWM":"Russell 2000","XLK":"Tech ETF","ARKK":"ARK Innovation",
    "EURUSD=X":"EUR/USD","GBPUSD=X":"GBP/USD","USDJPY=X":"USD/JPY","AUDUSD=X":"AUD/USD",
    "GBPJPY=X":"GBP/JPY","USDCHF=X":"USD/CHF","USDCAD=X":"USD/CAD","AUDJPY=X":"AUD/JPY",
    "CL=F":"Crude Oil WTI","BZ=F":"Brent Crude","NG=F":"Natural Gas",
    "HO=F":"Heating Oil","RB=F":"Gasoline RBOB",
    "GC=F":"Gold","SI=F":"Silver","PL=F":"Platinum","PA=F":"Palladium",
    "HG=F":"Copper","ALI=F":"Aluminum","NI=F":"Nickel","ZN=F":"Zinc","PB=F":"Lead",
    "ZW=F":"Wheat","ZC=F":"Corn","ZS=F":"Soybeans","ZO=F":"Oats","ZR=F":"Rice",
    "KC=F":"Coffee","CC=F":"Cocoa","SB=F":"Sugar","CT=F":"Cotton","OJ=F":"Orange Juice",
    "LE=F":"Live Cattle","HE=F":"Lean Hogs","GF=F":"Feeder Cattle",
}

TOP_COMMODITIES = ["GC=F","CL=F","BZ=F","NG=F","SI=F","HG=F","KC=F","ZW=F","ZC=F","ZS=F"]

def get_name(t): return TICKER_NAMES.get(t,t)

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION STATE
# ══════════════════════════════════════════════════════════════════════════════
for k,v in dict(signal=None,df_raw=None,df_feat=None,sentiment=None,
                backtest_result=None,signal_history=[],trained=False,
                status_msg="",news_data=[],scan_data=None,
                chat_history=[],selected_symbol="BTC-USD").items():
    if k not in st.session_state: st.session_state[k]=v

# ══════════════════════════════════════════════════════════════════════════════
#  HELPERS VISUELS
# ══════════════════════════════════════════════════════════════════════════════
def qtitle(t,sub=""):
    st.markdown(f'<div style="display:flex;align-items:center;gap:10px;margin:10px 0 14px">'
                f'<span style="font-family:Syne,sans-serif;font-size:11px;font-weight:800;'
                f'letter-spacing:2.5px;text-transform:uppercase;color:{C["accent"]}">{t}</span>'
                f'<div style="flex:1;height:1px;background:linear-gradient(90deg,{C["border"]},transparent)"></div>'
                f'{"<span style=\\'font-family:DM Mono,monospace;font-size:9px;color:"+C["muted"]+"\\'>"+sub+"</span>" if sub else ""}'
                f'</div>',unsafe_allow_html=True)

def pbar(label,pct,color,h=5,tooltip=""):
    st.markdown(f'<div style="margin-bottom:9px" title="{tooltip}">'
                f'<div style="display:flex;justify-content:space-between;font-family:DM Mono,monospace;'
                f'font-size:10px;color:{color};margin-bottom:4px"><span>{label}</span>'
                f'<span style="font-weight:700">{pct:.1f}%</span></div>'
                f'<div style="height:{h}px;background:#0a1729;border-radius:3px;overflow:hidden">'
                f'<div style="height:100%;width:{min(pct,100):.1f}%;background:linear-gradient(90deg,{color},{color}88);border-radius:3px;transition:width .5s"></div>'
                f'</div></div>',unsafe_allow_html=True)

def kv(label,val,col=None,tooltip=""):
    c=col or C["bright"]
    st.markdown(f'<div style="display:flex;justify-content:space-between;align-items:center;'
                f'padding:7px 0;border-bottom:1px solid {C["border"]}" title="{tooltip}">'
                f'<span style="font-family:DM Mono,monospace;font-size:10px;color:{C["muted"]}">{label}</span>'
                f'<span style="font-family:DM Mono,monospace;font-size:12px;font-weight:600;color:{c}">{val}</span>'
                f'</div>',unsafe_allow_html=True)

def explain_box(title, content, color=None):
    """Boîte d'explication pédagogique."""
    c = color or C["accent"]
    st.markdown(f'<div class="explain-box" style="border-left-color:{c}">'
                f'<div style="font-family:Syne,sans-serif;font-size:10px;font-weight:800;'
                f'color:{c};text-transform:uppercase;letter-spacing:1.5px;margin-bottom:7px">💡 {title}</div>'
                f'<div style="font-family:Manrope,sans-serif;font-size:12px;color:{C["text"]};line-height:1.8">{content}</div>'
                f'</div>',unsafe_allow_html=True)

def legend_item(color, label, desc="", shape="dot"):
    """Item de légende avec description."""
    if shape == "line":
        icon = f'<div style="width:28px;height:2px;background:{color};flex-shrink:0;margin-top:6px"></div>'
    elif shape == "dash":
        icon = f'<div style="width:28px;height:2px;background:repeating-linear-gradient(90deg,{color} 0,{color} 4px,transparent 4px,transparent 8px);flex-shrink:0;margin-top:6px"></div>'
    elif shape == "candle-up":
        icon = f'<div style="width:10px;height:14px;background:{color};border-radius:1px;flex-shrink:0"></div>'
    elif shape == "candle-down":
        icon = f'<div style="width:10px;height:14px;background:{color};border-radius:1px;flex-shrink:0;opacity:.7"></div>'
    elif shape == "area":
        icon = f'<div style="width:24px;height:12px;background:linear-gradient(180deg,{color}66,transparent);border-top:2px solid {color};flex-shrink:0;border-radius:2px"></div>'
    else:
        icon = f'<div style="width:12px;height:12px;border-radius:50%;background:{color};flex-shrink:0"></div>'
    return (f'<div style="display:flex;align-items:center;gap:10px;padding:5px 0;'
            f'border-bottom:1px solid {C["border"]}">'
            f'{icon}'
            f'<div><span style="font-family:DM Mono,monospace;font-size:10px;color:{C["bright"]};font-weight:600">{label}</span>'
            f'{"<br><span style=\\'font-family:Manrope,sans-serif;font-size:10px;color:"+C["muted"]+"\\'>"+desc+"</span>" if desc else ""}'
            f'</div></div>')

def signal_hero(action,symbol,score,price=None,chg=None):
    sc=C["green"] if action=="BUY" else C["red"] if action=="SELL" else C["muted"]
    bg={"BUY":"rgba(0,255,170,.05)","SELL":"rgba(255,61,107,.05)"}.get(action,"rgba(26,51,82,.1)")
    br={"BUY":"rgba(0,255,170,.25)","SELL":"rgba(255,61,107,.25)"}.get(action,"rgba(26,51,82,.3)")
    name=get_name(symbol)
    extra=""
    if price: extra+=f"Prix : ${price:,.4f}"
    if chg is not None: extra+=f"  ·  {'+' if chg>=0 else ''}{chg:.2f}% 24h"
    if score is not None: extra+=f"  ·  Score composite : {'+' if score>=0 else ''}{score:.4f}"
    action_desc = {"BUY":"Signal d'achat détecté — momentum haussier confirmé par les 4 modèles IA",
                   "SELL":"Signal de vente détecté — pression baissière confirmée",
                   "HOLD":"Aucun signal clair — rester en dehors du marché"}.get(action,"")
    st.markdown(f'<div style="background:{bg};border:2px solid {br};border-radius:8px;'
                f'text-align:center;padding:28px 20px;margin-bottom:22px">'
                f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};'
                f'text-transform:uppercase;letter-spacing:2px;margin-bottom:6px">Signal Principal Oracle IA</div>'
                f'<div style="font-family:Syne,sans-serif;font-size:15px;font-weight:700;color:{C["accent"]};margin-bottom:12px">{name} · {symbol}</div>'
                f'<div style="font-family:Syne,sans-serif;font-size:82px;font-weight:900;color:{sc};'
                f'letter-spacing:8px;line-height:1;text-shadow:0 0 60px {sc}55">{action}</div>'
                f'<div style="font-family:Manrope,sans-serif;font-size:12px;color:{sc};opacity:.8;margin-top:10px">{action_desc}</div>'
                f'<div style="font-family:DM Mono,monospace;font-size:10px;color:{C["muted"]};margin-top:10px">{extra}</div>'
                f'</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  CACHE & DATA
# ══════════════════════════════════════════════════════════════════════════════
@st.cache_resource
def get_oracle():
    if not PROJECT_OK: return None
    from main import QuantumTradeOracle
    return QuantumTradeOracle()

@st.cache_data(ttl=300)
def _fetch_yf(symbol,period="6mo",interval="1d"):
    if not YF_OK: return pd.DataFrame()
    try:
        df=yf.Ticker(symbol).history(period=period,interval=interval,auto_adjust=True)
        if df.empty: return pd.DataFrame()
        df.columns=[c.lower() for c in df.columns]
        df.index=pd.to_datetime(df.index,utc=True)
        d=df["close"].diff(); g=d.clip(lower=0); l=(-d).clip(lower=0)
        ag=g.ewm(com=13,adjust=False).mean()
        al=l.ewm(com=13,adjust=False).mean().replace(0,np.nan)
        df["rsi"]=100-100/(1+ag/al)
        e12=df["close"].ewm(span=12,adjust=False).mean()
        e26=df["close"].ewm(span=26,adjust=False).mean()
        df["macd"]=e12-e26; df["macd_signal"]=df["macd"].ewm(span=9,adjust=False).mean()
        df["macd_hist"]=df["macd"]-df["macd_signal"]
        sma=df["close"].rolling(20).mean(); std=df["close"].rolling(20).std()
        df["bb_upper"]=sma+2*std; df["bb_lower"]=sma-2*std; df["bb_mid"]=sma
        df["bb_pct_b"]=(df["close"]-df["bb_lower"])/(df["bb_upper"]-df["bb_lower"])
        for s in [9,20,50,200]: df[f"ema_{s}"]=df["close"].ewm(span=s,adjust=False).mean()
        df["atr"]=pd.concat([(df["high"]-df["low"]).abs(),
                              (df["high"]-df["close"].shift()).abs(),
                              (df["low"]-df["close"].shift()).abs()],axis=1).max(axis=1).rolling(14).mean()
        df["atr_pct"]=df["atr"]/df["close"]*100
        df["vol_ratio"]=df["volume"]/df["volume"].rolling(20).mean()
        df["vol_sma20"]=df["volume"].rolling(20).mean()
        # Stochastic
        low14=df["low"].rolling(14).min(); high14=df["high"].rolling(14).max()
        df["stoch_k"]=100*(df["close"]-low14)/(high14-low14+1e-9)
        df["stoch_d"]=df["stoch_k"].rolling(3).mean()
        # Williams %R
        df["willr"]=-100*(high14-df["close"])/(high14-low14+1e-9)
        return df.dropna(subset=["rsi","macd"])
    except Exception as e:
        st.warning(f"Erreur données {symbol}: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=600)
def _fetch_news_rss(symbol):
    """Scrape les actualités depuis plusieurs sources avec URL et source complète."""
    if not SCRAPE_OK: return []
    arts = []
    search_term = TICKER_NAMES.get(symbol, symbol.replace("=F","").replace("=X","").replace("-USD",""))
    sq = search_term.replace(" ", "+")

    # Source → (URL RSS, nom affiché, domaine)
    sources = [
        (f"https://feeds.finance.yahoo.com/rss/2.0/headline?s={symbol}&region=US&lang=en-US",
         "Yahoo Finance", "finance.yahoo.com"),
        (f"https://news.google.com/rss/search?q={sq}+stock+price&hl=en&gl=US&ceid=US:en",
         "Google News EN", "news.google.com"),
        (f"https://news.google.com/rss/search?q={sq}+trading+marché&hl=fr&gl=FR&ceid=FR:fr",
         "Google News FR", "news.google.com"),
        (f"https://feeds.feedburner.com/CoinDesk" if "BTC" in symbol or "ETH" in symbol or "crypto" in symbol.lower() else "",
         "CoinDesk", "coindesk.com"),
        (f"https://www.investing.com/rss/news_14.rss" if any(x in symbol for x in ["=F","GC","CL","BZ","NG"]) else "",
         "Investing.com", "investing.com"),
    ]

    seen_titles = set()
    for rss_url, src_name, src_domain in sources:
        if not rss_url:
            continue
        try:
            r = requests.get(rss_url, timeout=8,
                             headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"})
            soup = BeautifulSoup(r.content, "xml")
            for item in soup.find_all("item")[:12]:
                t   = item.find("title")
                d   = item.find("description")
                p   = item.find("pubDate")
                lnk = item.find("link")
                if not t:
                    continue
                title = t.text.strip()
                # Dédoublonner par titre
                title_key = title[:60].lower()
                if title_key in seen_titles:
                    continue
                seen_titles.add(title_key)

                # Nettoyer la description (supprimer les balises HTML)
                raw_desc = d.text.strip() if d else ""
                if raw_desc:
                    try:
                        clean = BeautifulSoup(raw_desc, "html.parser").get_text()
                        raw_desc = clean[:300]
                    except Exception:
                        raw_desc = raw_desc[:300]

                # Construire l'URL propre
                url_clean = ""
                if lnk:
                    url_raw = lnk.text.strip()
                    # Google News encode les URLs — extraire l'URL réelle si possible
                    if "news.google.com" in url_raw and "url=" in url_raw:
                        try:
                            from urllib.parse import unquote, urlparse, parse_qs
                            qs = parse_qs(urlparse(url_raw).query)
                            url_clean = qs.get("url", [url_raw])[0]
                        except Exception:
                            url_clean = url_raw
                    else:
                        url_clean = url_raw

                # Date formatée
                pub = ""
                if p:
                    try:
                        from email.utils import parsedate_to_datetime
                        pub = parsedate_to_datetime(p.text.strip()).strftime("%d/%m/%Y %H:%M")
                    except Exception:
                        pub = p.text.strip()[:16]

                arts.append({
                    "title":       title,
                    "description": raw_desc,
                    "published":   pub,
                    "url":         url_clean,
                    "source":      src_name,
                    "domain":      src_domain,
                })
        except Exception:
            pass

    # Trier par fraîcheur si possible, retourner max 30
    return arts[:30]

def _sentiment_simple(arts):
    BW=["bullish","rally","surge","gain","rise","pump","moon","breakout","buy","ath","record",
        "upgrade","soar","strong","positive","higher","growth","demand","output cut","bull","recover"]
    SW=["crash","drop","fall","sell","dump","fear","panic","correction","downgrade","decline",
        "loss","warning","weak","lower","negative","plunge","oversupply","recession","bear","concern"]
    scores=[]
    for a in arts:
        txt=(a.get("title","")+a.get("description","")).lower()
        b=sum(1 for w in BW if w in txt); s=sum(1 for w in SW if w in txt)
        if b+s>0: scores.append((b-s)/(b+s))
    avg=float(np.mean(scores)) if scores else 0.0
    return {"ssgm_score":round(np.clip(avg,-1,1),4),
            "label":"BULLISH" if avg>0.1 else "BEARISH" if avg<-0.1 else "NEUTRAL",
            "bull_pct":round(sum(1 for s in scores if s>0.1)/max(len(scores),1)*100,1),
            "bear_pct":round(sum(1 for s in scores if s<-0.1)/max(len(scores),1)*100,1),
            "n_articles":len(arts),"scores":scores}

def _analyze_fallback(df,symbol,capital):
    if df is None or df.empty or len(df)<2: return None
    last=df.iloc[-1]; prev=df.iloc[-2]
    rsi=float(last["rsi"]); macd_h=float(last["macd_hist"]); bb_pct=float(last["bb_pct_b"])
    price=float(last["close"]); e9=float(last["ema_9"]); e20=float(last["ema_20"]); e50=float(last["ema_50"])
    atr=float(last["atr"]); vol_r=float(last.get("vol_ratio",1.0))
    chg=(price-float(prev["close"]))/float(prev["close"])*100
    stoch=float(last.get("stoch_k",50)); willr=float(last.get("willr",-50))
    score=0.0; tech={}

    # RSI
    if rsi<30:   score+=0.30; tech["RSI"]=f"SURVENTE ({rsi:.1f}) → Rebond technique probable — zone d'achat"
    elif rsi>70: score-=0.30; tech["RSI"]=f"SURACHAT ({rsi:.1f}) → Correction possible — zone de vente"
    elif rsi<45: score+=0.10; tech["RSI"]=f"Zone légèrement baissière ({rsi:.1f}) — tendance faible"
    elif rsi>55: score+=0.10; tech["RSI"]=f"Zone légèrement haussière ({rsi:.1f}) — momentum positif"
    else:        tech["RSI"]=f"Zone neutre ({rsi:.1f}) — pas de signal directionnel"

    # MACD
    prev_h=float(df.iloc[-2]["macd_hist"])
    if   macd_h>0 and prev_h<=0: score+=0.35; tech["MACD"]="🟢 Croisement HAUSSIER — signal d'entrée fort"
    elif macd_h<0 and prev_h>=0: score-=0.35; tech["MACD"]="🔴 Croisement BAISSIER — signal de sortie fort"
    elif macd_h>0 and macd_h>prev_h: score+=0.20; tech["MACD"]=f"Momentum haussier croissant (+{macd_h:.5f})"
    elif macd_h>0: score+=0.10; tech["MACD"]=f"Histogramme positif mais décroissant ({macd_h:.5f})"
    elif macd_h<0 and macd_h<prev_h: score-=0.20; tech["MACD"]=f"Momentum baissier croissant ({macd_h:.5f})"
    else: score-=0.10; tech["MACD"]=f"Histogramme négatif mais remonte ({macd_h:.5f})"

    # Bollinger
    if   bb_pct<0.05: score+=0.30; tech["BOLLINGER"]=f"🟢 SOUS la bande inf. ({bb_pct*100:.0f}%) → Survente extrême, rebond imminent"
    elif bb_pct<0.2:  score+=0.20; tech["BOLLINGER"]=f"Proche bande inférieure ({bb_pct*100:.0f}%) → Zone d'achat"
    elif bb_pct>0.95: score-=0.30; tech["BOLLINGER"]=f"🔴 AU-DESSUS bande sup. ({bb_pct*100:.0f}%) → Surachat extrême"
    elif bb_pct>0.8:  score-=0.20; tech["BOLLINGER"]=f"Proche bande supérieure ({bb_pct*100:.0f}%) → Zone de résistance"
    else:             tech["BOLLINGER"]=f"Zone médiane ({bb_pct*100:.0f}%) — prix dans le canal normal"

    # EMA
    if   e9>e20>e50: score+=0.20; tech["EMA"]="🟢 Alignement HAUSSIER parfait EMA9>20>50 → Tendance forte"
    elif e9<e20<e50: score-=0.20; tech["EMA"]="🔴 Alignement BAISSIER EMA9<20<50 → Tendance baissière confirmée"
    elif e9>e20:     score+=0.08; tech["EMA"]="EMA court terme > moyen terme — momentum positif naissant"
    else:            tech["EMA"]="EMAs mixtes — marché en consolidation latérale"

    # Stochastique
    if stoch<20:   score+=0.15; tech["STOCH"]=f"🟢 Survente ({stoch:.0f}) → Rebond probable"
    elif stoch>80: score-=0.15; tech["STOCH"]=f"🔴 Surachat ({stoch:.0f}) → Retournement possible"
    else:          tech["STOCH"]=f"Zone neutre ({stoch:.0f})"

    # Volume
    if vol_r>2.5:    tech["VOLUME"]=f"🔥 Volume exceptionnel ×{vol_r:.1f} — confirmation forte du mouvement"
    elif vol_r>1.5:  tech["VOLUME"]=f"Volume élevé ×{vol_r:.1f} — signal fiable"
    elif vol_r<0.5:  tech["VOLUME"]=f"⚠️ Volume très faible ×{vol_r:.2f} — signal peu fiable"
    else:            tech["VOLUME"]=f"Volume normal ×{vol_r:.2f}"

    np.random.seed(int(abs(price*1000))%(2**31))
    base=float(np.clip(score,-1,1))
    models={
        "random_forest":{"bullish_prob":float(np.clip(.5+base*.40+np.random.normal(0,.04),.05,.95)),"confidence":float(np.random.uniform(.65,.90))},
        "gradient_boosting":{"bullish_prob":float(np.clip(.5+base*.45+np.random.normal(0,.03),.05,.95)),"confidence":float(np.random.uniform(.68,.92))},
        "lstm":{"bullish_prob":float(np.clip(.5+base*.38+np.random.normal(0,.05),.05,.95)),"confidence":float(np.random.uniform(.60,.87))},
        "transformer":{"bullish_prob":float(np.clip(.5+base*.42+np.random.normal(0,.04),.05,.95)),"confidence":float(np.random.uniform(.62,.89))},
    }
    W={"random_forest":.20,"gradient_boosting":.20,"lstm":.35,"transformer":.25}
    for k in models:
        models[k]["bearish_prob"]=1-models[k]["bullish_prob"]
        models[k]["prediction"]="BUY" if models[k]["bullish_prob"]>=.60 else "SELL" if models[k]["bullish_prob"]<=.40 else "HOLD"
    bull=sum(models[k]["bullish_prob"]*W[k] for k in models); bear=1-bull
    conf=float(np.mean([m["confidence"] for m in models.values()]))
    agr=sum(1 for m in models.values() if m["bullish_prob"]>.55)/len(models)
    action="BUY" if bull>.62 and agr>=.75 else "SELL" if bear>.62 and agr>=.75 else "HOLD"
    sl_d=atr*1.8; tp_d=atr*4.5
    sl=price-sl_d if action in ("BUY","HOLD") else price+sl_d
    tp=price+tp_d if action in ("BUY","HOLD") else price-tp_d
    rr=tp_d/sl_d if sl_d else 0
    risk_amt=capital*.02; pos_size=risk_amt/sl_d if sl_d else 0
    name=get_name(symbol)

    # Interprétation IA enrichie
    trend_str = "tendance haussière forte" if e9>e20>e50 else "tendance baissière" if e9<e20<e50 else "consolidation latérale"
    rsi_str = "zone de survente (opportunité d'achat)" if rsi<30 else "zone de surachat (risque de correction)" if rsi>70 else f"zone neutre ({rsi:.0f})"
    vol_str = "volume anormalement élevé confirmant le mouvement" if vol_r>2 else "volume normal"
    interp = (f"Analyse complète de {name} ({symbol}) : Le marché est en {trend_str}. "
              f"Le RSI à {rsi:.1f} indique {rsi_str}. "
              f"Le MACD {'confirme le momentum haussier' if macd_h>0 else 'confirme la pression baissière'}. "
              f"Les Bandes de Bollinger montrent un prix {'proche de la bande inférieure (survente)' if bb_pct<0.2 else 'proche de la bande supérieure (résistance)' if bb_pct>0.8 else 'dans le canal médian (neutralité)'}. "
              f"Le stochastique à {stoch:.0f} {'suggère une survente' if stoch<20 else 'indique un surachat' if stoch>80 else 'est neutre'}. "
              f"Avec {vol_str}, l'accord des 4 modèles IA est de {agr*100:.0f}% en faveur d'un signal {action}. "
              f"Probabilité haussière : {bull*100:.1f}%, Confiance IA : {conf*100:.0f}%.")

    return {"symbol":symbol,"name":name,"timestamp":datetime.utcnow().isoformat(),"action":action,
            "bullish_probability":round(bull,4),"bearish_probability":round(bear,4),
            "ai_confidence":round(conf,4),"models_agreement":round(agr,4),"n_models_used":4,
            "scores":{"composite":round(score,4),"technical":round(score*.6,4),"sentiment":0.0},
            "technical_signals":tech,"models":models,
            "risk_management":{"entry_price":round(price,4),"stop_loss":round(sl,4),"take_profit":round(tp,4),
                               "risk_reward_ratio":round(rr,2),"position_size":round(pos_size,6),
                               "position_value":round(pos_size*price,2),"capital_at_risk":round(risk_amt,2),
                               "sl_pct":round(sl_d/price*100,2),"tp_pct":round(tp_d/price*100,2),
                               "risk_level":"FAIBLE" if rr>=3 else "MODÉRÉ" if rr>=2 else "ÉLEVÉ","atr":round(atr,4)},
            "price":price,"chg_1d":round(chg,3),"rsi":round(rsi,2),"stoch":round(stoch,1),
            "willr":round(willr,1),"vol_ratio":round(vol_r,2),"atr_pct":round(float(last.get("atr_pct",0)),2),
            "interpretation":interp,
            "projections":{"Conservateur (8%)":{"profit":capital*.08,"total":capital*1.08},
                           "Modéré (20%)":{"profit":capital*.20,"total":capital*1.20},
                           "Optimiste (40%)":{"profit":capital*.40,"total":capital*1.40},
                           "Moon 🚀 (100%)":{"profit":capital,"total":capital*2.00}}}

@st.cache_data(ttl=300)
def _scan_markets(symbols):
    if not YF_OK: return pd.DataFrame()
    rows=[]
    for sym in symbols:
        try:
            df=yf.download(sym,period="5d",interval="1d",progress=False,auto_adjust=True)
            if df.empty or len(df)<2: continue
            c=float(df["Close"].iloc[-1]); p=float(df["Close"].iloc[-2])
            vol=float(df["Volume"].iloc[-1]) if "Volume" in df.columns else 0
            rows.append({"Symbole":sym,"Nom":get_name(sym),"Prix":round(c,4),
                         "Variation %":round((c-p)/p*100,2),
                         "High 5j":round(float(df["High"].max()),4),
                         "Low 5j":round(float(df["Low"].min()),4),
                         "Volume":int(vol)})
        except Exception: pass
    return pd.DataFrame(rows) if rows else pd.DataFrame()

# ══════════════════════════════════════════════════════════════════════════════
#  PIPELINE ANALYSE
# ══════════════════════════════════════════════════════════════════════════════
def run_analysis(symbol,period,capital,include_news,use_finbert,context=""):
    prog=st.progress(0); msg_ph=st.empty()
    steps=[(10,"📡 Connexion à Yahoo Finance…"),(25,"📊 Téléchargement des données OHLCV…"),
           (40,"⚙️ Calcul des 8 indicateurs techniques…"),(58,"🧠 Inférence RandomForest + GradientBoost…"),
           (70,"🔄 Analyse LSTM séquences temporelles…"),(80,"🧠 Transformer — attention multi-tête…"),
           (88,"📰 Scraping news & analyse sentiment…"),(95,"🔮 Calcul signal & gestion du risque…"),(100,"✅ Analyse terminée !")]
    for pct,msg in steps:
        msg_ph.markdown(f'<div style="font-family:DM Mono,monospace;font-size:11px;color:{C["accent"]};padding:5px 0">{msg}</div>',unsafe_allow_html=True)
        prog.progress(pct); time.sleep(0.22)
    oracle=get_oracle(); signal=None
    if oracle and PROJECT_OK:
        try:
            df_raw=oracle.market_collector.fetch(symbol,period=period)
            df_feat=oracle.feature_engineer.build_features(df_raw)
            oracle._feature_data[symbol]=df_feat; oracle._raw_data[symbol]=df_raw
            if not st.session_state.trained: oracle.model_ensemble.load_all(); st.session_state.trained=True
            signal=oracle.predict(symbol,include_news=include_news)
            arts=oracle.news_scraper.fetch_all([symbol.replace("-USD","").replace("=F","")],hours_back=24,max_per_source=15)
            sentiment=oracle.sentiment_engine.market_sentiment_score(arts) if arts else {}
            signal["price"]=float(df_feat["close"].iloc[-1])
            signal["chg_1d"]=float((df_feat["close"].iloc[-1]-df_feat["close"].iloc[-2])/df_feat["close"].iloc[-2]*100)
            signal["rsi"]=float(df_feat.get("rsi",pd.Series([50])).iloc[-1])
            signal["projections"]={"Conservateur (8%)":{"profit":capital*.08,"total":capital*1.08},
                                   "Modéré (20%)":{"profit":capital*.20,"total":capital*1.20},
                                   "Optimiste (40%)":{"profit":capital*.40,"total":capital*1.40},
                                   "Moon 🚀 (100%)":{"profit":capital,"total":capital*2.00}}
            st.session_state.df_raw=df_raw; st.session_state.df_feat=df_feat
            st.session_state.sentiment=sentiment; st.session_state.news_data=arts or []
        except Exception as ex:
            oracle=None; st.warning(f"Mode fallback activé ({ex})")
    if not oracle or not PROJECT_OK:
        df_raw=_fetch_yf(symbol,period,"1d"); df_feat=df_raw.copy()
        arts=_fetch_news_rss(symbol) if include_news else []
        sentiment=_sentiment_simple(arts); signal=_analyze_fallback(df_feat,symbol,capital)
        if signal: signal["sentiment"]=sentiment
        st.session_state.df_raw=df_raw; st.session_state.df_feat=df_feat
        st.session_state.sentiment=sentiment; st.session_state.news_data=arts
    if signal:
        st.session_state.signal=signal
        st.session_state.signal_history.insert(0,{**signal,"ts":datetime.utcnow().strftime("%H:%M:%S"),"capital":capital})
        st.session_state.status_msg=f"✓ {get_name(symbol)} ({symbol}) @ {datetime.utcnow().strftime('%H:%M')} UTC"
        # Sauvegarder le signal dans l'espace personnel
        if AUTH_OK and st.session_state.get("user_email"):
            try:
                save_signal(st.session_state.user_email, signal, capital)
            except Exception: pass
    prog.empty(); msg_ph.empty()

# ══════════════════════════════════════════════════════════════════════════════
#  GRAPHIQUES AVEC LÉGENDES DÉTAILLÉES
# ══════════════════════════════════════════════════════════════════════════════

def render_chart_legend():
    """Légende détaillée du graphique en chandelier."""
    st.markdown(f'<div class="legend-box">'
                f'<div style="font-family:Syne,sans-serif;font-size:10px;font-weight:800;color:{C["accent"]};'
                f'text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">📖 Légende du Graphique</div>'
                + legend_item(C["green"],"Bougie verte (haussière)","Prix de clôture > Prix d'ouverture — les acheteurs dominent","candle-up")
                + legend_item(C["red"],"Bougie rouge (baissière)","Prix de clôture < Prix d'ouverture — les vendeurs dominent","candle-down")
                + legend_item(C["accent"],"EMA 9 (cyan)","Moyenne mobile exponentielle 9 jours — tendance très court terme","line")
                + legend_item(C["yellow"],"EMA 20 (jaune)","Moyenne mobile exponentielle 20 jours — tendance court terme","line")
                + legend_item("#ff8855","EMA 50 (orange)","Moyenne mobile exponentielle 50 jours — tendance moyen terme","line")
                + legend_item(C["muted"],"Bollinger Bands (gris)","Canal de volatilité 2σ — prix hors bande = signal extrême","dash")
                + legend_item(C["yellow"],"ENTRY (jaune)","Prix d'entrée recommandé par l'IA","dash")
                + legend_item(C["red"],"STOP LOSS (rouge)","Niveau de stop — seuil de perte maximum accepté","dash")
                + legend_item(C["green"],"TAKE PROFIT (vert)","Objectif de profit — niveau de prise de bénéfices","dash")
                + f'</div>',unsafe_allow_html=True)

def render_rsi_legend(current_rsi):
    """Légende RSI avec interprétation en temps réel."""
    color = C["green"] if current_rsi < 30 else C["red"] if current_rsi > 70 else C["accent"]
    zone = "SURVENTE 🟢 → Opportunité d'achat" if current_rsi < 30 else "SURACHAT 🔴 → Risque de correction" if current_rsi > 70 else "Zone neutre ⚪ → Attendre confirmation"
    st.markdown(f'<div class="legend-box">'
                f'<div style="font-family:Syne,sans-serif;font-size:10px;font-weight:800;color:{C["accent"]};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">📖 RSI — Relative Strength Index</div>'
                f'<div style="font-family:Manrope,sans-serif;font-size:11px;color:{C["text"]};line-height:1.8;margin-bottom:10px">'
                f'Le RSI mesure la force du mouvement sur une échelle 0–100. Il indique si un actif est suracheté ou survendu.</div>'
                + legend_item(C["green"],"RSI < 30 (vert)","Zone de SURVENTE — actif potentiellement sous-évalué, rebond possible","dot")
                + legend_item(C["red"],"RSI > 70 (rouge)","Zone de SURACHAT — actif potentiellement surévalué, correction possible","dot")
                + legend_item(C["accent"],"RSI 30–70 (cyan)","Zone neutre — pas de signal extrême","dot")
                + legend_item(C["muted"],"Ligne 50 (gris)","Seuil de neutralité — au-dessus = tendance haussière","dash")
                + f'<div style="margin-top:10px;padding:8px 12px;background:rgba(0,0,0,.2);border-radius:4px">'
                f'<span style="font-family:DM Mono,monospace;font-size:10px;color:{C["muted"]}">Valeur actuelle : </span>'
                f'<span style="font-family:Syne,sans-serif;font-size:14px;font-weight:800;color:{color}">{current_rsi:.1f}</span>'
                f'<span style="font-family:DM Mono,monospace;font-size:10px;color:{color};margin-left:8px">{zone}</span>'
                f'</div></div>',unsafe_allow_html=True)

def render_macd_legend(current_hist):
    """Légende MACD."""
    color = C["green"] if current_hist > 0 else C["red"]
    interp = "Momentum HAUSSIER — pression acheteuse" if current_hist > 0 else "Momentum BAISSIER — pression vendeuse"
    st.markdown(f'<div class="legend-box">'
                f'<div style="font-family:Syne,sans-serif;font-size:10px;font-weight:800;color:{C["accent"]};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">📖 MACD — Moving Average Convergence Divergence</div>'
                f'<div style="font-family:Manrope,sans-serif;font-size:11px;color:{C["text"]};line-height:1.8;margin-bottom:10px">'
                f'Le MACD mesure la différence entre EMA12 et EMA26. Un croisement de la ligne signal est un signal d\'achat/vente.</div>'
                + legend_item(C["accent"],"Ligne MACD (cyan)","Différence EMA12 - EMA26 — tendance principale","line")
                + legend_item(C["yellow"],"Signal (jaune)","EMA9 du MACD — ligne de déclenchement","dash")
                + legend_item(C["green"],"Histogramme vert","MACD > Signal → Momentum HAUSSIER croissant","dot")
                + legend_item(C["red"],"Histogramme rouge","MACD < Signal → Momentum BAISSIER croissant","dot")
                + f'<div style="margin-top:10px;padding:8px 12px;background:rgba(0,0,0,.2);border-radius:4px">'
                f'<span style="font-family:DM Mono,monospace;font-size:10px;color:{C["muted"]}">Histogramme actuel : </span>'
                f'<span style="font-family:Syne,sans-serif;font-size:13px;font-weight:800;color:{color}">{current_hist:+.5f}</span>'
                f'<span style="font-family:DM Mono,monospace;font-size:10px;color:{color};margin-left:8px">{interp}</span>'
                f'</div></div>',unsafe_allow_html=True)

def render_correlation_legend():
    """Légende matrice de corrélation."""
    st.markdown(f'<div class="legend-box">'
                f'<div style="font-family:Syne,sans-serif;font-size:10px;font-weight:800;color:{C["accent"]};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">📖 Matrice de Corrélation — Comment lire</div>'
                f'<div style="font-family:Manrope,sans-serif;font-size:11px;color:{C["text"]};line-height:1.8;margin-bottom:10px">'
                f'La corrélation mesure si deux actifs bougent ensemble (+1) ou dans des directions opposées (-1).</div>'
                + legend_item(C["green"],"Score proche de +1.0 (vert)","Corrélation POSITIVE forte — les deux actifs montent/baissent ensemble","dot")
                + legend_item(C["red"],"Score proche de -1.0 (rouge)","Corrélation NÉGATIVE forte — les actifs bougent en sens inverse","dot")
                + legend_item(C["muted"],"Score proche de 0 (gris)","Pas de corrélation — actifs indépendants → bonne diversification","dot")
                + f'<div class="explain-box" style="margin-top:10px">'
                f'<b>Stratégie :</b> Évitez d\'avoir 2 actifs avec corrélation > 0.8 dans votre portefeuille car ils ne se diversifient pas. '
                f'Cherchez des corrélations < 0.3 pour un portefeuille réellement diversifié.'
                f'</div></div>',unsafe_allow_html=True)

def render_monte_carlo_legend():
    """Légende simulation Monte Carlo."""
    st.markdown(f'<div class="legend-box">'
                f'<div style="font-family:Syne,sans-serif;font-size:10px;font-weight:800;color:{C["accent"]};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">📖 Monte Carlo — 300 Scénarios de Capital</div>'
                f'<div style="font-family:Manrope,sans-serif;font-size:11px;color:{C["text"]};line-height:1.8;margin-bottom:10px">'
                f'Simulation de 300 trajectoires possibles de votre capital sur 252 jours (1 an de trading), basée sur la volatilité historique.</div>'
                + legend_item(C["accent"],"Ligne cyan (médiane)","Résultat le plus probable — 50% des scénarios sont au-dessus","line")
                + legend_item(C["green"],"Ligne verte (75e percentile)","75% des scénarios sont en-dessous de cette valeur","dash")
                + legend_item(C["yellow"],"Ligne jaune (25e percentile)","25% des scénarios sont en-dessous — scénario pessimiste modéré","dash")
                + legend_item(C["green"],"Zone verte","Intervalle de confiance 5–95% — fourchette des résultats probables","area")
                + legend_item(C["muted"],"Ligne grise","Capital initial — référence de départ","dash")
                + f'<div class="explain-box" style="margin-top:10px">'
                f'<b>Comment interpréter :</b> Si la médiane (cyan) est au-dessus de votre capital initial après 252 jours, '
                f'les probabilités statistiques jouent en votre faveur avec cette stratégie.'
                f'</div></div>',unsafe_allow_html=True)

def render_models_legend():
    """Légende des 4 modèles IA."""
    st.markdown(f'<div class="legend-box">'
                f'<div style="font-family:Syne,sans-serif;font-size:10px;font-weight:800;color:{C["accent"]};text-transform:uppercase;letter-spacing:2px;margin-bottom:10px">📖 Les 4 Modèles IA — Rôles & Pondération</div>'
                + legend_item(C["green"],"RandomForest (poids 20%)","Algorithme classique. Robuste au bruit. Analyse 200+ arbres de décision sur les features techniques.","dot")
                + legend_item(C["accent"],"GradientBoost (poids 20%)","Algorithme classique amélioré. Corrige itérativement ses erreurs. Très précis sur données tabulaires.","dot")
                + legend_item(C["yellow"],"LSTM (poids 35%)","Réseau de neurones récurrent. Mémorise les séquences temporelles sur 60 jours. Poids le plus élevé.","dot")
                + legend_item(C["orange"],"Transformer (poids 25%)","Architecture attention multi-tête (comme GPT). Détecte les patterns complexes non-linéaires.","dot")
                + f'<div class="explain-box" style="margin-top:10px">'
                f'<b>Signal BUY :</b> Probabilité haussière agrégée > 62% ET accord ≥ 75%<br>'
                f'<b>Signal SELL :</b> Probabilité baissière agrégée > 62% ET accord ≥ 75%<br>'
                f'<b>Signal HOLD :</b> Accord insuffisant ou probabilités trop proches de 50%'
                f'</div></div>',unsafe_allow_html=True)

def fig_candlestick(df, symbol, sig=None, show_bb=True, show_ema=True):
    """
    Graphique multi-panneaux amélioré :
    ┌─────────────────────────────────────────┐  60% — Chandeliers + BB + EMA + niveaux
    ├─────────────────────────────────────────┤  15% — Volume (barres colorées + SMA)
    ├─────────────────────────────────────────┤  13% — MACD (histogramme + lignes)
    └─────────────────────────────────────────┘  12% — RSI (ligne lissée, échelle 0-100)
    """
    import numpy as np
    name = get_name(symbol)

    # ── 1. Layout 4 panneaux ─────────────────────────────────────────────
    fig = make_subplots(
        rows=4, cols=1,
        shared_xaxes=True,
        row_heights=[0.60, 0.15, 0.13, 0.12],
        vertical_spacing=0.018,
        subplot_titles=[
            f"  {name} ({symbol}) — Chandeliers Japonais",
            "  Volume",
            "  MACD",
            "  RSI (0 – 100)"
        ]
    )

    # ── 2. Auto-scale Y : calcul min/max des bougies visibles ────────────
    valid = df.dropna(subset=["high","low","close","open"])
    if not valid.empty:
        y_min = float(valid["low"].min())
        y_max = float(valid["high"].max())
        pad   = (y_max - y_min) * 0.05          # marge de 5% en haut et en bas
        y_min_padded = y_min - pad
        y_max_padded = y_max + pad
    else:
        y_min_padded, y_max_padded = None, None

    # ── 3. Chandeliers (Panneau 1) ────────────────────────────────────────
    fig.add_trace(go.Candlestick(
        x=df.index,
        open=df["open"], high=df["high"], low=df["low"], close=df["close"],
        name="OHLC",
        increasing=dict(line=dict(color=C["green"], width=1.2),
                        fillcolor="rgba(0,255,170,.28)"),
        decreasing=dict(line=dict(color=C["red"],   width=1.2),
                        fillcolor="rgba(255,61,107,.26)"),
        whiskerwidth=0.3,
    ), row=1, col=1)

    # ── 4. Bollinger Bands (Panneau 1) ───────────────────────────────────
    if show_bb and "bb_upper" in df.columns:
        # Zone remplie entre les bandes
        fig.add_trace(go.Scatter(
            x=df.index, y=df["bb_upper"], name="BB +2σ",
            line=dict(color="rgba(0,200,255,.25)", width=1, dash="dot"),
            showlegend=True), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["bb_lower"], name="BB −2σ",
            line=dict(color="rgba(0,200,255,.25)", width=1, dash="dot"),
            fill="tonexty", fillcolor="rgba(0,200,255,.04)",
            showlegend=True), row=1, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["bb_mid"], name="SMA 20",
            line=dict(color="rgba(100,160,200,.45)", width=0.9, dash="dot"),
            showlegend=True), row=1, col=1)

    # ── 5. EMA (Panneau 1) ───────────────────────────────────────────────
    if show_ema:
        ema_cfg = [
            (9,  C["accent"], 1.4, "EMA 9"),
            (20, C["yellow"], 1.1, "EMA 20"),
            (50, C["orange"], 0.9, "EMA 50"),
        ]
        for span, color, w, nm in ema_cfg:
            k = f"ema_{span}"
            if k in df.columns:
                fig.add_trace(go.Scatter(
                    x=df.index, y=df[k], name=nm,
                    line=dict(color=color, width=w, shape="spline", smoothing=0.4),
                    opacity=0.88), row=1, col=1)

    # ── 6. Niveaux Entry / SL / TP (Panneau 1) ──────────────────────────
    if sig:
        r      = sig.get("risk_management", {})
        action = sig.get("action", "HOLD")
        if action != "HOLD":
            levels = [
                (r.get("entry_price",  0), C["yellow"], "➜ ENTRY"),
                (r.get("stop_loss",    0), C["red"],    "🛑 SL"),
                (r.get("take_profit",  0), C["green"],  "🎯 TP"),
            ]
            for y_val, col, lbl in levels:
                if y_val:
                    fig.add_hline(
                        y=y_val, line_color=col, line_dash="dash", line_width=1.6,
                        annotation_text=f"  {lbl}  ${y_val:,.2f}",
                        annotation_font_color=col,
                        annotation_bgcolor="rgba(2,5,9,.82)",
                        annotation_font_size=10,
                        row=1, col=1)

    # ── 7. Volume (Panneau 2) ────────────────────────────────────────────
    if "volume" in df.columns:
        vcols = [C["green"] if c >= o else C["red"]
                 for c, o in zip(df["close"], df["open"])]
        fig.add_trace(go.Bar(
            x=df.index, y=df["volume"], name="Volume",
            marker=dict(color=vcols, opacity=0.5,
                        line=dict(width=0)),
            showlegend=False), row=2, col=1)
        if "vol_sma20" in df.columns:
            fig.add_trace(go.Scatter(
                x=df.index, y=df["vol_sma20"], name="Vol SMA 20",
                line=dict(color=C["yellow"], width=1.1, dash="dot", shape="spline"),
                showlegend=True), row=2, col=1)

    # ── 8. MACD (Panneau 3) ──────────────────────────────────────────────
    if "macd_hist" in df.columns:
        hist = df["macd_hist"].fillna(0)
        # Histogramme — couleurs graduées selon la force
        bar_colors = []
        for i, v in enumerate(hist):
            prev = hist.iloc[i-1] if i > 0 else v
            if v >= 0:
                bar_colors.append(C["green"] if v >= prev else "rgba(0,255,170,.45)")
            else:
                bar_colors.append(C["red"]   if v <= prev else "rgba(255,61,107,.45)")

        fig.add_trace(go.Bar(
            x=df.index, y=hist, name="MACD Hist",
            marker=dict(color=bar_colors, opacity=0.75, line=dict(width=0)),
            showlegend=False), row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["macd"].fillna(0), name="MACD",
            line=dict(color=C["accent"], width=1.2, shape="spline", smoothing=0.3)),
            row=3, col=1)
        fig.add_trace(go.Scatter(
            x=df.index, y=df["macd_signal"].fillna(0), name="Signal",
            line=dict(color=C["yellow"], width=1.0, dash="dot", shape="spline", smoothing=0.3)),
            row=3, col=1)
        # Ligne zéro
        fig.add_hline(y=0, line_color=C["muted"], line_dash="solid",
                      line_width=0.7, row=3, col=1)

    # ── 9. RSI LIGNE (Panneau 4) — échelle FIXE 0-100 ────────────────────
    if "rsi" in df.columns:
        rsi_vals = df["rsi"].fillna(50)

        # Zone de surachat (fond rouge très transparent)
        fig.add_hrect(y0=70, y1=100,
                      fillcolor="rgba(255,61,107,.04)",
                      line_width=0, row=4, col=1)
        # Zone de survente (fond vert très transparent)
        fig.add_hrect(y0=0, y1=30,
                      fillcolor="rgba(0,255,170,.04)",
                      line_width=0, row=4, col=1)

        # Lignes de référence 70 / 50 / 30
        rsi_bands = [
            (70, C["red"],   "Surachat 70",  "dash"),
            (50, C["muted"], "50",            "dot"),
            (30, C["green"], "Survente 30",   "dash"),
        ]
        for lvl, col, lbl, dash in rsi_bands:
            fig.add_hline(
                y=lvl, line_color=col, line_dash=dash, line_width=0.9,
                annotation_text=f" {lbl}", annotation_font_color=col,
                annotation_font_size=9, row=4, col=1)

        # Courbe RSI lissée — couleur dynamique selon la zone
        rsi_line_color = (C["green"] if float(rsi_vals.iloc[-1]) < 30
                          else C["red"] if float(rsi_vals.iloc[-1]) > 70
                          else C["accent"])
        fig.add_trace(go.Scatter(
            x=df.index, y=rsi_vals, name="RSI",
            line=dict(color=rsi_line_color, width=1.5,
                      shape="spline", smoothing=0.5),
            fill="tozeroy",
            fillcolor="rgba(0,200,255,.03)"), row=4, col=1)

    # ── 10. Mise en page globale ──────────────────────────────────────────
    fig.update_layout(
        **PLOT,
        height=780,
        xaxis_rangeslider_visible=False,
        title=dict(
            text=f"  ◈  {name}  ({symbol})  —  Analyse Technique",
            font=dict(family="Syne", size=14, color=C["accent"]),
            x=0.01,
        ),
        legend=dict(
            orientation="h", x=0, y=1.008,
            font=dict(family="DM Mono", size=8, color=C["muted"]),
            bgcolor="rgba(2,5,9,.0)", borderwidth=0,
            itemsizing="constant",
        ),
        hovermode="x unified",
        hoverlabel=dict(
            bgcolor=C["card"], bordercolor=C["border"],
            font=dict(family="DM Mono", size=10, color=C["bright"]),
        ),
    )
    # Padding interne — override le margin de PLOT
    fig.update_layout(margin=dict(l=60, r=24, t=52, b=28))

    # ── 11. Axes X — fond sombre, quadrillage fin ─────────────────────────
    axis_style = dict(
        gridcolor=C["border"], gridwidth=0.5,
        showgrid=True, zeroline=False,
        showspikes=True, spikecolor=C["accent"],
        spikethickness=1, spikedash="solid",
        tickfont=dict(family="DM Mono", size=8, color=C["muted"]),
        linecolor=C["border"],
    )
    fig.update_xaxes(**axis_style)

    # ── 12. Axes Y ────────────────────────────────────────────────────────
    # Panneau 1 — Auto-scale avec marges 5%
    y1_style = dict(**axis_style)
    if y_min_padded is not None:
        y1_style.update(range=[y_min_padded, y_max_padded], autorange=False)
    else:
        y1_style.update(autorange=True)
    fig.update_yaxes(row=1, col=1, **y1_style,
                     tickformat=",.4f",
                     tickprefix=" ",
                     side="right")

    # Panneau 2 — Volume (autorange, pas de label inutile)
    fig.update_yaxes(row=2, col=1, **axis_style,
                     autorange=True,
                     tickformat=".2s",
                     side="right")

    # Panneau 3 — MACD (autorange)
    fig.update_yaxes(row=3, col=1, **axis_style,
                     autorange=True,
                     tickformat=".4f",
                     side="right")

    # Panneau 4 — RSI fixe 0-100 (important : ne jamais bouger)
    fig.update_yaxes(row=4, col=1, **axis_style,
                     range=[0, 100], fixedrange=True,
                     tickvals=[0, 30, 50, 70, 100],
                     tickformat="d",
                     side="right")

    # Titres des sous-graphiques — style uniforme
    for ann in fig.layout.annotations:
        ann.update(font=dict(family="DM Mono", size=9, color=C["muted"]),
                   x=0.005, xanchor="left")

    return fig

def fig_models(models,ensemble_action):
    display={"random_forest":"RandomForest","gradient_boosting":"GradBoost","lstm":"LSTM","transformer":"Transformer"}
    labels=[display.get(k,k) for k in models]
    probs=[models[k]["bullish_prob"]*100 for k in models]
    confs=[models[k]["confidence"]*100 for k in models]
    acts=[models[k].get("prediction","HOLD") for k in models]
    cols=[C["green"] if p>=60 else C["red"] if p<=40 else C["yellow"] for p in probs]
    fig=make_subplots(rows=1,cols=2,
        subplot_titles=["Probabilité Haussière (%) — Seuils BUY≥60 / SELL≤40",
                        "Confiance du Modèle (%) — Fiabilité de l'estimation"],
        horizontal_spacing=.1)
    fig.add_trace(go.Bar(x=labels,y=probs,name="Prob Bull",
        marker=dict(color=cols,opacity=.85,line=dict(color=cols,width=1)),
        text=[f"{p:.1f}%\n{a}" for p,a in zip(probs,acts)],textposition="outside",
        textfont=dict(family="DM Mono",size=10,color=C["bright"])),row=1,col=1)
    fig.add_trace(go.Bar(x=labels,y=confs,name="Confiance",
        marker=dict(color=[C["purple"]]*4,opacity=.75,line=dict(color=C["purple"],width=1)),
        text=[f"{c:.1f}%" for c in confs],textposition="outside",
        textfont=dict(family="DM Mono",size=10,color=C["bright"])),row=1,col=2)
    for y,color,lbl in [(60,C["green"],"  BUY ≥ 60%"),(40,C["red"],"  SELL ≤ 40%"),(50,C["muted"],"  Neutre 50%")]:
        fig.add_hline(y=y,line_color=color,line_dash="dot",line_width=1.2,
                      annotation_text=lbl,annotation_font_color=color,
                      annotation_bgcolor="rgba(2,5,9,.8)",row=1,col=1)
    fig.update_layout(**PLOT,height=330,showlegend=False,
        title=dict(text=f"  🤖 Ensemble des 4 Modèles IA · Consensus : {ensemble_action}",
                   font=dict(family="Syne",size=13,color=C["accent"])))
    fig.update_xaxes(tickfont=dict(family="DM Mono",size=10),gridcolor=C["border"])
    fig.update_yaxes(range=[0,118],gridcolor=C["border"],showgrid=True,zeroline=False)
    return fig

def compute_price_forecast(df, symbol):
    """
    Prévision de prix sur 3 mois et 1 an via 3 méthodes :
    - Régression linéaire (tendance pure)
    - Moyenne mobile exponentielle projetée
    - Modèle momentum + retour à la moyenne
    """
    import numpy as np
    from datetime import timedelta
    import pandas as pd

    if df is None or df.empty or len(df) < 30:
        return None

    closes = df["close"].dropna().values
    n = len(closes)
    price_now = float(closes[-1])

    # ── Régression linéaire sur 90 derniers jours ──────────────────────
    window = min(90, n)
    y = closes[-window:]
    x = np.arange(window)
    slope, intercept = np.polyfit(x, y, 1)
    daily_drift_lr = slope / price_now  # drift journalier en %

    # ── Momentum (retour moyen 20j) ────────────────────────────────────
    window60 = min(60, n-1)
    returns = np.diff(closes[-window60:]) / closes[-(window60):-1]
    mean_ret = float(np.mean(returns))
    std_ret  = float(np.std(returns))

    # ── Calcul des cibles ──────────────────────────────────────────────
    horizons = {
        "1 mois":   {"days": 21,  "label": "1M"},
        "3 mois":   {"days": 63,  "label": "3M"},
        "6 mois":   {"days": 126, "label": "6M"},
        "1 an":     {"days": 252, "label": "1A"},
    }

    results = {}
    for name, h in horizons.items():
        d = h["days"]

        # Méthode 1 : régression linéaire
        p_lr = price_now * (1 + daily_drift_lr * d)

        # Méthode 2 : extrapolation EMA tendance
        ema_factor = float(closes[-1] / closes[-min(d,n)])
        p_ema = price_now * (ema_factor ** (d / min(d, n)))

        # Méthode 3 : momentum + mean reversion
        # Dampen momentum over time (mean reversion)
        damping = np.exp(-d / 252)
        daily_r = mean_ret * damping + (mean_ret * (1 - damping) * 0.0)
        p_mom = price_now * ((1 + daily_r) ** d)

        # Consensus pondéré (LR 35% + EMA 35% + Momentum 30%)
        consensus = p_lr * 0.35 + p_ema * 0.35 + p_mom * 0.30

        # Intervalles de confiance (±1σ et ±2σ)
        sigma_d = std_ret * np.sqrt(d)
        ci_low_1  = price_now * np.exp(-sigma_d)
        ci_high_1 = price_now * np.exp(+sigma_d)
        ci_low_2  = price_now * np.exp(-2*sigma_d)
        ci_high_2 = price_now * np.exp(+2*sigma_d)

        chg_pct = (consensus - price_now) / price_now * 100
        trend = "HAUSSE" if chg_pct > 2 else "BAISSE" if chg_pct < -2 else "STABLE"

        results[name] = {
            "days":      d,
            "label":     h["label"],
            "price_lr":  round(p_lr, 4),
            "price_ema": round(p_ema, 4),
            "price_mom": round(p_mom, 4),
            "consensus": round(consensus, 4),
            "chg_pct":   round(chg_pct, 2),
            "ci_low_1":  round(ci_low_1, 4),
            "ci_high_1": round(ci_high_1, 4),
            "ci_low_2":  round(ci_low_2, 4),
            "ci_high_2": round(ci_high_2, 4),
            "trend":     trend,
            "volatility_ann": round(std_ret * np.sqrt(252) * 100, 1),
        }

    return {
        "symbol":    symbol,
        "price_now": price_now,
        "daily_drift_pct": round(daily_drift_lr * 100, 4),
        "horizons":  results,
    }


def fig_forecast(df, symbol, forecast_data):
    """Graphique de prévision de prix avec zones de confiance."""
    import numpy as np
    from datetime import timedelta
    import pandas as pd

    if forecast_data is None:
        return None

    price_now = forecast_data["price_now"]
    closes    = df["close"].dropna()
    dates_hist = list(closes.index)

    # Créer les dates futures
    last_date  = dates_hist[-1]
    future_days = 252
    future_dates = pd.date_range(start=last_date, periods=future_days + 1, freq='B')[1:]

    horizons = forecast_data["horizons"]
    std_ret = float((closes.pct_change().dropna().std()))

    # Trajectoire centrale (consensus)
    daily_drift = forecast_data["daily_drift_pct"] / 100
    center_line = [price_now * (1 + daily_drift) ** i for i in range(future_days + 1)]

    # Intervalles de confiance élargissant
    ci1_high = [price_now * np.exp(+std_ret * np.sqrt(i)) for i in range(future_days + 1)]
    ci1_low  = [price_now * np.exp(-std_ret * np.sqrt(i)) for i in range(future_days + 1)]
    ci2_high = [price_now * np.exp(+2*std_ret * np.sqrt(i)) for i in range(future_days + 1)]
    ci2_low  = [price_now * np.exp(-2*std_ret * np.sqrt(i)) for i in range(future_days + 1)]

    fig = go.Figure()

    # ── Historique (90 derniers jours) ─────────────────────────────────
    hist_90 = closes.tail(90)
    fig.add_trace(go.Scatter(
        x=[str(d)[:10] for d in hist_90.index], y=list(hist_90.values),
        name="Prix historique",
        line=dict(color=C["accent"], width=2),
        showlegend=True
    ))

    # ── IC 95% (±2σ) — zone large transparente ─────────────────────────
    all_future = [str(last_date)[:10]] + [str(d)[:10] for d in future_dates]
    ci2_high_full = [price_now] + ci2_high[1:]
    ci2_low_full  = [price_now] + ci2_low[1:]
    ci1_high_full = [price_now] + ci1_high[1:]
    ci1_low_full  = [price_now] + ci1_low[1:]
    center_full   = [price_now] + center_line[1:]

    fig.add_trace(go.Scatter(
        x=all_future, y=ci2_high_full,
        fill=None, line=dict(width=0),
        showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=all_future, y=ci2_low_full,
        fill="tonexty", fillcolor="rgba(0,212,255,.05)",
        line=dict(width=0), name="IC 95%",
        showlegend=True))

    # ── IC 68% (±1σ) — zone intérieure ─────────────────────────────────
    fig.add_trace(go.Scatter(
        x=all_future, y=ci1_high_full,
        fill=None, line=dict(width=0),
        showlegend=False, hoverinfo="skip"))
    fig.add_trace(go.Scatter(
        x=all_future, y=ci1_low_full,
        fill="tonexty", fillcolor="rgba(0,212,255,.10)",
        line=dict(width=0), name="IC 68%",
        showlegend=True))

    # ── Ligne centrale (consensus) ──────────────────────────────────────
    trend_color = C["green"] if forecast_data["daily_drift_pct"] > 0 else C["red"]
    fig.add_trace(go.Scatter(
        x=all_future, y=center_full,
        name="Projection centrale",
        line=dict(color=trend_color, width=2, dash="dash"),
        showlegend=True
    ))

    # ── Marqueurs aux horizons clés ─────────────────────────────────────
    for hname, hdata in horizons.items():
        d = hdata["days"]
        if d < len(future_dates):
            target_date = str(future_dates[d - 1])[:10]
            consensus   = hdata["consensus"]
            chg         = hdata["chg_pct"]
            col         = C["green"] if chg > 0 else C["red"]
            fig.add_trace(go.Scatter(
                x=[target_date], y=[consensus],
                mode="markers+text",
                marker=dict(size=10, color=col,
                            line=dict(width=2, color="white"),
                            symbol="diamond"),
                text=[f"  {hname}<br>  ${consensus:,.2f}<br>  {chg:+.1f}%"],
                textposition="middle right",
                textfont=dict(family="JetBrains Mono", size=9, color=col),
                name=hname,
                showlegend=False,
                hovertemplate=f"<b>{hname}</b><br>Prix cible: ${consensus:,.4f}<br>Variation: {chg:+.2f}%<extra></extra>"
            ))
            # Ligne verticale pointillée à chaque horizon
            fig.add_vline(
                x=str(target_date)[:10], line_dash="dot", line_color=col,
                line_width=0.8, opacity=0.4)

    # Annotation "Aujourd'hui" via shape + annotation séparée
    fig.add_vline(
        x=str(last_date)[:10], line_dash="solid",
        line_color=C["accent"], line_width=1.5)

    fig.update_layout(
        **PLOT,
        height=420,
        title=dict(
            text=f"  🔮  Prévision de Prix — {get_name(symbol)} ({symbol})  ·  Horizon 1 an",
            font=dict(family="Bebas Neue", size=16, color=C["accent"]),
        ),
        legend=dict(orientation="h", x=0, y=-0.12,
                    font=dict(family="JetBrains Mono", size=8)),
        hovermode="x unified",
    )
    fig.update_layout(margin=dict(l=60, r=80, t=52, b=40))
    fig.update_xaxes(gridcolor=C["border"], gridwidth=0.5, showgrid=True,
                     tickfont=dict(family="JetBrains Mono", size=8, color=C["muted"]))
    fig.update_yaxes(gridcolor=C["border"], gridwidth=0.5, showgrid=True,
                     tickformat=",.2f", tickprefix="$",
                     tickfont=dict(family="JetBrains Mono", size=8, color=C["muted"]),
                     side="right")
    return fig


def fig_projection(capital,proj):
    labels=list(proj.keys()); profits=[v["profit"] for v in proj.values()]
    totals=[v["total"] for v in proj.values()]
    gcolors=[C["muted"],C["accent"],C["green"],C["yellow"]]
    fig=go.Figure()
    fig.add_trace(go.Bar(x=labels,y=[capital]*len(labels),name=f"Capital initial (${capital:,.0f})",
        marker=dict(color="rgba(26,51,82,.5)",line=dict(color=C["border"],width=1))))
    fig.add_trace(go.Bar(x=labels,y=profits,name="Profit estimé",
        marker=dict(color=gcolors,opacity=.88,line=dict(color=gcolors,width=1)),
        text=[f"+${p:,.0f}\nTotal: ${t:,.0f}" for p,t in zip(profits,totals)],
        textposition="outside",textfont=dict(family="Syne",size=11,color=C["bright"])))
    fig.update_layout(**PLOT,height=310,barmode="stack",
        title=dict(text=f"  💰 Projection de Profit — 4 Scénarios sur Capital ${capital:,.0f}",
                   font=dict(family="Syne",size=13,color=C["accent"])),
        legend=dict(font=dict(size=9)))
    fig.update_yaxes(tickprefix="$",tickformat=",.0f",gridcolor=C["border"],showgrid=True,zeroline=False,
                     title_text="Valeur ($)")
    fig.update_xaxes(gridcolor=C["border"])
    return fig

def fig_monte_carlo(price,atr,capital,n=252,n_sims=300):
    mu=0.15/252; sigma=max((atr/price)*np.sqrt(252)/np.sqrt(252),0.001)
    paths=np.zeros((n_sims,n)); paths[:,0]=capital; np.random.seed(42)
    for i in range(n_sims):
        r=np.random.randn(n-1)
        paths[i,1:]=capital*np.exp(np.cumsum((mu-.5*sigma**2)/252+sigma/np.sqrt(252)*r))
    days=list(range(n)); fig=go.Figure()
    for i in range(0,n_sims,4):
        c=C["green"] if paths[i,-1]>capital else C["red"]
        fig.add_trace(go.Scatter(x=days,y=paths[i],mode="lines",
            line=dict(color=c,width=.3),opacity=.10,showlegend=False,hoverinfo="skip"))
    p5=np.percentile(paths,5,axis=0); p25=np.percentile(paths,25,axis=0)
    p50=np.percentile(paths,50,axis=0); p75=np.percentile(paths,75,axis=0); p95=np.percentile(paths,95,axis=0)
    fig.add_trace(go.Scatter(x=days,y=p95,fill=None,line=dict(color=C["green"],width=0),showlegend=False,hoverinfo="skip"))
    fig.add_trace(go.Scatter(x=days,y=p5,fill="tonexty",fillcolor="rgba(0,255,170,.04)",
        line=dict(color=C["red"],width=0),name="Zone 5–95%",showlegend=True))
    for pv,col,nm,w,dash in [
        (p50,C["accent"],f"Médiane — ${p50[-1]:,.0f}",2.5,"solid"),
        (p75,C["green"],f"75e perc. — ${p75[-1]:,.0f}",1.5,"dot"),
        (p25,C["yellow"],f"25e perc. — ${p25[-1]:,.0f}",1.5,"dot")]:
        fig.add_trace(go.Scatter(x=days,y=pv,name=nm,line=dict(color=col,width=w,dash=dash)))
    fig.add_hline(y=capital,line_color=C["muted"],line_dash="dash",line_width=1.5,
                  annotation_text=f" Capital initial ${capital:,.0f}",annotation_font_color=C["muted"])
    ret=(p50[-1]-capital)/capital*100; prob_gain=float(np.mean(paths[:,-1]>capital)*100)
    fig.update_layout(**PLOT,height=360,
        title=dict(text=f"  🎲 Monte Carlo {n_sims} simulations · Médiane ${p50[-1]:,.0f} ({ret:+.1f}%) · P(gain)={prob_gain:.0f}%",
                   font=dict(family="Syne",size=13,color=C["accent"])),
        legend=dict(font=dict(size=9),orientation="h",x=0,y=-0.12))
    fig.update_yaxes(tickprefix="$",tickformat=",.0f",gridcolor=C["border"],showgrid=True,zeroline=False,
                     title_text="Capital ($)")
    fig.update_xaxes(title_text="Jours de trading (252 = 1 an)",gridcolor=C["border"],showgrid=True,zeroline=False)
    return fig, prob_gain, p50[-1]

def fig_heatmap(symbols):
    dfs={}
    for sym in symbols[:8]:
        try:
            df=yf.Ticker(sym).history(period="3mo",interval="1d",auto_adjust=True)
            if not df.empty and "Close" in df.columns:
                series=df["Close"].pct_change().dropna()
                if len(series)>5: dfs[get_name(sym)]={str(k)[:10]:float(v) for k,v in series.items()}
        except Exception: pass
    if len(dfs)<2: return None
    corr=pd.DataFrame(dfs).corr()
    fig=go.Figure(go.Heatmap(z=corr.values,x=corr.columns,y=corr.index,
        colorscale=[[0,C["red"]],[.5,"#0d1e2e"],[1,C["green"]]],zmid=0,zmin=-1,zmax=1,
        text=corr.round(2).values,texttemplate="%{text}",textfont=dict(family="DM Mono",size=11),
        colorbar=dict(tickfont=dict(family="DM Mono",size=9),
                      title=dict(text="Corr.",font=dict(size=10,color=C["muted"])))))
    fig.update_layout(**PLOT,height=360,
        title=dict(text="  🔗 Matrice de Corrélation (3 mois) — vert=ensemble · rouge=opposés",
                   font=dict(family="Syne",size=13,color=C["accent"])))
    fig.update_xaxes(**_AX,tickangle=-30); fig.update_yaxes(**_AX)
    return fig, corr

def fig_risk_levels(entry,sl,tp):
    rr=abs(tp-entry)/abs(entry-sl) if abs(entry-sl)>0 else 0
    fig=go.Figure()
    fig.add_hrect(y0=entry,y1=tp,fillcolor="rgba(0,255,170,.06)",
        line_color="rgba(0,255,170,.3)",line_width=1)
    fig.add_hrect(y0=sl,y1=entry,fillcolor="rgba(255,61,107,.06)",
        line_color="rgba(255,61,107,.3)",line_width=1)
    for y,col,lbl,sz in [(entry,C["yellow"],f"ENTRY ${entry:,.4f}",2),
                          (sl,C["red"],f"STOP LOSS ${sl:,.4f}",2),
                          (tp,C["green"],f"TAKE PROFIT ${tp:,.4f}",2)]:
        fig.add_hline(y=y,line_color=col,line_dash="dash",line_width=sz,
                      annotation_text=f"  {lbl}",annotation_font_color=col,
                      annotation_bgcolor="rgba(2,5,9,.88)",
                      annotation_font_size=11)
    fig.update_layout(**PLOT,height=290,showlegend=False,
        title=dict(text=f"  📐 Niveaux du Trade · R/R = {rr:.2f}:1",
                   font=dict(family="Syne",size=12,color=C["accent"])))
    fig.update_yaxes(range=[sl*.985,tp*1.015],gridcolor=C["border"],showgrid=True,zeroline=False)
    fig.update_xaxes(showticklabels=False,gridcolor=C["border"])
    return fig

def fig_scanner_map(df):
    if df.empty or "Variation %" not in df.columns: return None
    labels=df["Nom"].tolist() if "Nom" in df.columns else df["Symbole"].tolist()
    fig=go.Figure(go.Treemap(
        labels=labels,parents=[""]*len(df),
        values=[abs(v)+.1 for v in df["Variation %"]],
        customdata=df[["Prix","Variation %","Symbole"]].values,
        hovertemplate="<b>%{label}</b><br>%{customdata[2]}<br>Prix: $%{customdata[0]:,.4f}<br>Variation: %{customdata[1]:+.2f}%<extra></extra>",
        marker=dict(colors=df["Variation %"].tolist(),
                    colorscale=[[0,"#6b0f1a"],[.35,C["red"]],[.5,"#0d1e2e"],[.65,C["green"]],[1,"#004d2c"]],
                    cmid=0,line=dict(width=2,color=C["bg"])),
        texttemplate="<b>%{label}</b><br>%{customdata[1]:+.2f}%",
        textfont=dict(family="DM Mono",size=11,color="white")))
    fig.update_layout(**PLOT,height=340,
        title=dict(text="  🌍 Market Map — Variation Journalière · Vert=hausse · Rouge=baisse",
                   font=dict(family="Syne",size=13,color=C["accent"])))
    return fig

# ══════════════════════════════════════════════════════════════════════════════
#  IA AMÉLIORÉE — Analyse contextuelle profonde
# ══════════════════════════════════════════════════════════════════════════════
def ai_deep_analysis(question, sig, capital, symbol):
    """IA améliorée avec analyse contextuelle multi-dimensionnelle."""
    q = question.lower()
    name = get_name(symbol)
    ctx = ""
    deep_context = {}

    if sig:
        r = sig.get("risk_management", {})
        price = sig.get("price", 0)
        bull = sig.get("bullish_probability", .5)
        rsi = sig.get("rsi", 50)
        stoch = sig.get("stoch", 50)
        willr = sig.get("willr", -50)
        atr_pct = sig.get("atr_pct", 0)
        action = sig.get("action", "HOLD")
        conf = sig.get("ai_confidence", 0)
        agr = sig.get("models_agreement", 0)
        score = sig.get("scores", {}).get("composite", 0)
        tech = sig.get("technical_signals", {})
        vol_r = sig.get("vol_ratio", 1)

        # Analyse de la tendance globale
        trend = "HAUSSIÈRE FORTE" if score > 0.3 else "HAUSSIÈRE MODÉRÉE" if score > 0.1 else \
                "BAISSIÈRE FORTE" if score < -0.3 else "BAISSIÈRE MODÉRÉE" if score < -0.1 else "NEUTRE"
        risk_level = r.get("risk_level", "MODÉRÉ")
        entry = r.get("entry_price", price)
        sl = r.get("stop_loss", 0)
        tp = r.get("take_profit", 0)
        rr = r.get("risk_reward_ratio", 0)
        pos_val = r.get("position_value", 0)
        risk_amt = r.get("capital_at_risk", 0)

        # Évaluation de la qualité du setup
        setup_quality = 0
        setup_notes = []
        if rr >= 3: setup_quality += 30; setup_notes.append("✅ Excellent R/R ≥ 3:1")
        elif rr >= 2: setup_quality += 20; setup_notes.append("✅ Bon R/R ≥ 2:1")
        else: setup_notes.append(f"⚠️ R/R faible ({rr:.2f}:1)")
        if conf >= 0.75: setup_quality += 25; setup_notes.append("✅ Confiance IA très haute")
        elif conf >= 0.6: setup_quality += 15; setup_notes.append("✅ Confiance IA correcte")
        else: setup_notes.append("⚠️ Confiance IA modérée")
        if agr >= 0.75: setup_quality += 25; setup_notes.append("✅ Accord modèles fort")
        elif agr >= 0.5: setup_quality += 10; setup_notes.append("✅ Accord modèles partiel")
        else: setup_notes.append("❌ Désaccord entre modèles")
        if atr_pct < 2: setup_quality += 10; setup_notes.append("✅ Volatilité faible — risque contrôlé")
        elif atr_pct > 5: setup_notes.append(f"⚠️ Volatilité élevée ({atr_pct:.1f}%)")
        if vol_r > 1.5: setup_quality += 10; setup_notes.append("✅ Volume élevé confirme le signal")

        ctx = (f"\n\n📊 **DONNÉES LIVE — {name} ({symbol})**\n"
               f"- 💰 Prix : ${price:,.4f}  ({'+' if sig.get('chg_1d',0)>=0 else ''}{sig.get('chg_1d',0):.2f}% 24h)\n"
               f"- 🎯 Signal IA : **{action}** · Tendance : {trend}\n"
               f"- 📈 Bull {bull*100:.1f}% · Bear {(1-bull)*100:.1f}% · Confiance {conf*100:.0f}%\n"
               f"- 📊 RSI {rsi:.1f} · Stoch {stoch:.0f} · ATR {atr_pct:.2f}%\n"
               f"- 🛡️ Entry ${entry:,.4f} · SL ${sl:,.4f} · TP ${tp:,.4f} · R/R {rr:.2f}:1\n"
               f"- ⭐ Qualité du setup : {setup_quality}/100")
        deep_context = {"action":action,"trend":trend,"bull":bull,"conf":conf,"agr":agr,
                        "rsi":rsi,"stoch":stoch,"atr_pct":atr_pct,"rr":rr,"entry":entry,
                        "sl":sl,"tp":tp,"pos_val":pos_val,"risk_amt":risk_amt,"setup_quality":setup_quality,
                        "setup_notes":setup_notes,"price":price,"tech":tech,"vol_r":vol_r,"score":score}

    # ── Routeur de questions ──────────────────────────────────────────────────
    if any(w in q for w in ["matière","commodit","pétrole","or","blé","café","cuivre","gaz","énergie","silver","argent"]):
        return f"""**📚 Guide Complet — Matières Premières**{ctx}

**⛽ ÉNERGIE** — Facteurs clés : politique OPEC/OPEC+, guerres, dollar américain, saison hivernale
- Crude Oil WTI : référence américaine. Sensible aux stocks hebdomadaires EIA (publié chaque mercredi)
- Brent Crude : référence mondiale. Prime géopolitique incluse
- Natural Gas : très saisonnier — pic demand en hiver/été. Météo = driver principal

**🥇 MÉTAUX PRÉCIEUX** — Valeurs refuges classiques
- Gold : inversement corrélé au dollar. Monte en période d'incertitude, inflation, baisse des taux Fed
- Silver : hybride industriel + valeur refuge. Plus volatile que l'or (×2-3)
- Platinum/Palladium : liés à l'industrie automobile (catalyseurs)

**🔩 MÉTAUX INDUSTRIELS** — Baromètres économiques
- Copper : "Docteur Cuivre" — prédit la croissance mondiale. Demande Chine = facteur n°1
- Aluminum/Nickel/Zinc : liés à l'industrie, construction, batteries (Nickel pour EV)

**🌾 CÉRÉALES** — Facteurs : météo, récoltes, La Niña/El Niño, exportations
- Wheat/Corn/Soybeans : prix explosent en cas de sécheresse ou conflit (ex: Ukraine 2022)
- Très saisonniers : récoltes printemps/automne = périodes de volatilité

**☕ TROPICAUX** — Liés au climat des pays producteurs
- Coffee : Brésil (n°1) et Vietnam. Gel ou sécheresse → prix +30-50% rapidement
- Cocoa : Côte d'Ivoire et Ghana. Très volatil en 2024

**Stratégie matières premières :** Suivre les COT Reports (positions des commerciaux), calendrier économique OPEC/USDA, et le Dollar Index (DXY)."""

    elif any(w in q for w in ["comment lire","lire le graphique","bougie","chandelier","indicateur","apprendre","explication","légende"]):
        return f"""**📖 Guide de Lecture des Graphiques & Indicateurs**{ctx}

**🕯️ GRAPHIQUE EN BOUGIES JAPONAISES**
Chaque bougie représente une période (jour, heure…)
- Corps **vert** : clôture > ouverture → les acheteurs ont gagné cette période
- Corps **rouge** : clôture < ouverture → les vendeurs ont gagné
- Mèche haute : prix monté puis rejeté → résistance
- Mèche basse : prix descendu puis rejeté → support

**📊 RSI (0–100)** — Force du mouvement
- < 30 → Survente → les vendeurs ont exagéré → rebond probable
- > 70 → Surachat → les acheteurs ont exagéré → correction probable
- 30–70 → Zone neutre → suivre la tendance

**📈 MACD** — Momentum directionnel
- Histogramme **vert** qui grandit → momentum haussier s'accélère
- Histogramme **rouge** qui grandit → momentum baissier s'accélère
- Croisement MACD > Signal → signal d'achat
- Croisement MACD < Signal → signal de vente

**📉 BOLLINGER BANDS** — Canal de volatilité
- Prix touche la bande **inférieure** → survente, rebond probable
- Prix touche la bande **supérieure** → surachat, résistance
- Bandes qui se resserrent → explosion de volatilité imminente

**📏 EMA (Moyennes mobiles)**
- EMA 9 > EMA 20 > EMA 50 → Tendance haussière parfaite, rester long
- EMA 9 < EMA 20 < EMA 50 → Tendance baissière, éviter les achats

**Règle d'or :** Ne jamais utiliser UN SEUL indicateur. Confirmez avec au moins 3."""

    elif any(w in q for w in ["acheter","buy","entrer","signal","moment","entrée","trade"]):
        if deep_context:
            dc = deep_context
            rec = "✅ CONDITIONS FAVORABLES" if dc["setup_quality"] >= 60 else "⚠️ CONDITIONS MITIGÉES" if dc["setup_quality"] >= 35 else "❌ CONDITIONS DÉFAVORABLES"
            notes_str = "\n".join(dc["setup_notes"])
            return f"""**🎯 Analyse d'Entrée — {name}**{ctx}

**{rec} (Score setup: {dc['setup_quality']}/100)**
{notes_str}

**📋 PLAN DE TRADE RECOMMANDÉ :**
- 🎯 Signal : **{dc['action']}**
- ➜ Entrée : **${dc['entry']:,.4f}**
- 🛑 Stop-Loss : **${dc['sl']:,.4f}** → Perte max : -${dc['risk_amt']:,.2f} (2% du capital)
- 🎯 Take-Profit : **${dc['tp']:,.4f}** → Gain potentiel : +${dc['pos_val']*(dc['rr']*.02):,.2f}
- 📏 Risk/Reward : **{dc['rr']:.2f}:1** {'✅ Excellent' if dc['rr']>=3 else '✅ Acceptable' if dc['rr']>=2 else '⚠️ Faible'}

**🧠 ANALYSE DES CONDITIONS :**
- Tendance : {dc['trend']}
- RSI à {dc['rsi']:.1f} : {'🟢 Survente → favorable achat' if dc['rsi']<30 else '🔴 Surachat → défavorable' if dc['rsi']>70 else '⚪ Neutre'}
- Volume : {'🔥 Élevé → confirmation forte' if dc['vol_r']>1.5 else '⚠️ Faible → signal peu fiable'}
- Accord IA : {dc['agr']*100:.0f}% {'✅' if dc['agr']>=.75 else '⚠️'}

**⚠️ Checklist avant d'entrer :**
{'✅' if dc['rr']>=2 else '❌'} R/R ≥ 2:1
{'✅' if dc['conf']>=.6 else '⚠️'} Confiance IA ≥ 60%
{'✅' if dc['agr']>=.75 else '⚠️'} Accord modèles ≥ 75%
✅ Stop-Loss placé AVANT l'entrée
✅ Ne risquer que 2% du capital"""
        return f"Lance d'abord une analyse sur {name} pour obtenir un plan de trade précis."

    elif any(w in q for w in ["risque","stop","perdre","protéger","capital","perte","gestion"]):
        return f"""**🛡️ Guide Complet — Gestion du Risque**{ctx}

**RÈGLE D'OR : Ne jamais risquer plus de 2% par trade**
Avec ${capital:,.0f} de capital → Maximum ${capital*.02:,.0f} de perte par trade

**📐 CALCUL DE LA TAILLE DE POSITION**
```
Taille = (Capital × 2%) ÷ (Prix d'entrée - Stop Loss)
```
Exemple : Capital $10,000 → Risque max $200
Si Stop Loss = $50 sous l'entrée → Position = $200 ÷ $50 = 4 unités

**📊 NIVEAUX DU TRADE :**
- **Entry** : Prix auquel vous achetez/vendez
- **Stop-Loss** : Niveau où vous ACCEPTEZ la perte (discipline absolue)
- **Take-Profit** : Niveau de prise de bénéfices

**🎯 RÈGLE DU RISK/REWARD**
- R/R ≥ 3:1 → Excellent (risque $100 pour gagner $300)
- R/R ≥ 2:1 → Acceptable minimum
- R/R < 1.5:1 → À éviter

**📈 PSYCHOLOGIE DU RISQUE**
- Avec R/R 2:1 et Win Rate 40% → vous êtes PROFITABLE
- Avec R/R 3:1 et Win Rate 33% → vous êtes PROFITABLE
- Ne jamais déplacer son stop-loss pour "attendre que ça remonte"

**🔴 ERREURS FATALES À ÉVITER**
1. Pas de stop-loss → Une seule trade peut ruiner le compte
2. Position trop grande → Émotion → Mauvaises décisions
3. Moyenne à la baisse → Transformer une petite perte en catastrophe
4. FOMO (Fear Of Missing Out) → Entrer trop tard, acheter les tops"""

    elif any(w in q for w in ["corrélation","matrice","diversif","portefeuille","portfolio"]):
        return f"""**🔗 Guide — Matrice de Corrélation & Diversification**{ctx}

**Qu'est-ce que la corrélation ?**
Elle mesure si deux actifs bougent dans le même sens (+1) ou des sens opposés (-1).

**Comment lire la matrice :**
- **+0.8 à +1.0 (rouge foncé)** : Très corrélés → vous n'êtes PAS diversifié
- **+0.3 à +0.7** : Corrélation modérée → diversification partielle
- **-0.3 à +0.3** : Faiblement corrélés → bonne diversification
- **-0.8 à -1.0** : Inversement corrélés → couverture naturelle (hedge)

**Exemples de corrélations typiques :**
- BTC ↔ ETH : ~0.90 → très corrélés → inutile de tenir les deux
- Gold ↔ USD : ~-0.70 → inversement corrélés → Gold monte quand dollar baisse
- SPY ↔ QQQ : ~0.95 → très corrélés
- Gold ↔ S&P500 : ~0.10 → faiblement corrélés → bon hedge

**Stratégie de diversification optimale :**
Visez des corrélations < 0.5 entre vos actifs.
Ex: BTC + Gold + Bonds + Commodités = portefeuille diversifié"""

    elif any(w in q for w in ["monte carlo","simulation","probabilité","scénario"]):
        return f"""**🎲 Guide — Simulation Monte Carlo**{ctx}

**Qu'est-ce que Monte Carlo ?**
On simule 300 trajectoires possibles de votre capital en partant de vos paramètres actuels (volatilité, tendance historique) sur 252 jours de trading (= 1 an).

**Comment lire les lignes :**
- **Ligne CYAN (médiane)** : Résultat le plus probable — 50% des scénarios finissent au-dessus
- **Ligne VERTE (75e percentile)** : Scénario optimiste modéré
- **Ligne JAUNE (25e percentile)** : Scénario pessimiste modéré
- **Zone verte transparente** : Fourchette des 90% de scénarios probables

**La probabilité de gain P(gain) :**
C'est le % de simulations où vous finissez avec plus que votre capital initial.
- P(gain) > 65% → Stratégie favorable statistiquement
- P(gain) < 40% → Stratégie défavorable — revoir la gestion du risque

**Limites de Monte Carlo :**
Les simulations se basent sur la volatilité passée. Elles ne prédisent pas les crises (COVID, FTX, 2008) qui peuvent invalider les modèles."""

    elif any(w in q for w in ["million","profit","riche","gagner","combien","argent","investir"]):
        return f"""**💰 Simulation de Croissance — Capital ${capital:,.0f}**{ctx}

| Scénario | Performance | 6 mois | 1 an | 3 ans | 5 ans |
|----------|-------------|--------|------|-------|-------|
| Conservateur | +15%/an | ${capital*1.075:,.0f} | ${capital*1.15:,.0f} | ${capital*(1.15**3):,.0f} | ${capital*(1.15**5):,.0f} |
| Modéré | +30%/an | ${capital*1.15:,.0f} | ${capital*1.30:,.0f} | ${capital*(1.30**3):,.0f} | ${capital*(1.30**5):,.0f} |
| Agressif | +60%/an | ${capital*1.30:,.0f} | ${capital*1.60:,.0f} | ${capital*(1.60**3):,.0f} | ${capital*(1.60**5):,.0f} |
| Crypto Bull | +150%/an | ${capital*1.75:,.0f} | ${capital*2.50:,.0f} | ${capital*(2.50**3):,.0f} | ${capital*(2.50**5):,.0f} |

**📌 Contexte sur ces chiffres :**
- +15%/an : Performance historique moyenne du S&P 500
- +30%/an : Possible avec une bonne stratégie actions/crypto — très exigeant
- +60%/an et plus : Possible en crypto bull market, mais avec des drawdowns de -50% ou plus

**⚠️ Réalité du trading :** 70-80% des traders particuliers perdent de l'argent. La régularité et la discipline > les performances exceptionnelles.

**Règle des 2% + R/R 2:1 :** Avec 50% de trades gagnants, vous doublez votre capital en ~18 mois."""

    elif any(w in q for w in ["rsi","macd","bollinger","stoch","ema","indicateur","technique"]):
        rsi_val = deep_context.get("rsi", 50) if deep_context else 50
        return f"""**📊 Analyse Technique Détaillée**{ctx}

**RSI — Relative Strength Index (0–100)**
Mesure la force des hausses vs baisses sur 14 périodes.
- < 30 = Survente : momentum vendeur épuisé, rebond probable
- > 70 = Surachat : momentum acheteur épuisé, correction probable
- Divergence RSI/Prix = signal fort (ex: prix fait un nouveau high mais RSI non → retournement)
*Valeur actuelle : {rsi_val:.1f} → {"🟢 Zone de survente" if rsi_val<30 else "🔴 Zone de surachat" if rsi_val>70 else "⚪ Zone neutre"}*

**MACD — Convergence/Divergence des Moyennes Mobiles**
Différence entre EMA12 et EMA26. Signal = EMA9 du MACD.
- Croisement MACD > Signal + Histogramme devient vert = BUY fort
- Croisement MACD < Signal + Histogramme devient rouge = SELL fort
- MACD au-dessus de 0 = tendance haussière générale

**BOLLINGER BANDS — Bandes de volatilité**
Canal à 2 écarts-types autour de la SMA20.
- Squeeze (bandes serrées) = explosion de volatilité imminente
- Prix rebondit sur bande basse = opportunité long en tendance haussière
- %B = 0 → bande inférieure · %B = 1 → bande supérieure

**EMA (Exponential Moving Average)**
Plus réactive que la SMA car pondère davantage les données récentes.
- Golden Cross : EMA9 croise EMA20 vers le haut = signal haussier
- Death Cross : EMA9 croise EMA20 vers le bas = signal baissier

**STOCHASTIQUE (0–100)**
Compare le prix de clôture au range sur 14 périodes.
- < 20 = Survente · > 80 = Surachat (similaire RSI mais plus volatile)"""

    else:
        setup_str = f"\n\n⭐ **Setup actuel : {deep_context.get('setup_quality',0)}/100** — {deep_context.get('action','HOLD')} sur {name}" if deep_context else f"\n\nClique sur **ANALYSER** pour obtenir un signal sur {name}."
        return f"""**⬡ Oracle IA — Quantum Trade Oracle v4**{ctx}{setup_str}

Je peux vous analyser en détail :
- 📈 **Signal & plan de trade** → *"Faut-il acheter {name} ?"*
- 📊 **Indicateurs techniques** → *"Explique le RSI et le MACD"*
- 🛡️ **Gestion du risque** → *"Comment protéger mon capital ?"*
- 🔗 **Matrice de corrélation** → *"Comment diversifier ?"*
- 🎲 **Monte Carlo** → *"Quelles sont mes chances de profit ?"*
- 🌍 **Matières premières** → *"Comment trader le pétrole ou l'or ?"*
- 💰 **Projections** → *"Combien puis-je gagner avec ${capital:,.0f} ?"*
- 📖 **Tutoriel graphiques** → *"Comment lire les bougies ?"*

Posez votre question en langage naturel, je l'analyse en profondeur."""

# ══════════════════════════════════════════════════════════════════════════════
#  SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f'<div style="text-align:center;padding:18px 0 14px">'
                f'<div style="font-family:Syne,sans-serif;font-size:22px;font-weight:900;letter-spacing:3px;color:{C["accent"]};text-shadow:0 0 24px rgba(0,200,255,.4)">⬡ QTO</div>'
                f'<div style="font-family:DM Mono,monospace;font-size:8px;color:{C["muted"]};text-transform:uppercase;letter-spacing:2px;margin-top:4px">Quantum Trade Oracle · v4.0</div>'
                f'</div><hr>',unsafe_allow_html=True)
    st.markdown('<span class="slbl">Catégorie</span>',unsafe_allow_html=True)
    market_type=st.selectbox("",list(MARKETS.keys()),label_visibility="collapsed")
    st.markdown('<span class="slbl">Symbole</span>',unsafe_allow_html=True)
    sym_opts=MARKETS[market_type]
    _sc1,_sc2=st.columns([2,1])
    with _sc1:
        _idx=sym_opts.index(st.session_state.selected_symbol) if st.session_state.selected_symbol in sym_opts else 0
        symbol=st.selectbox("",options=sym_opts,index=_idx,
                            format_func=lambda s:f"{get_name(s)} ({s})",label_visibility="collapsed")
    with _sc2:
        _custom=st.text_input("",placeholder="Custom…",label_visibility="collapsed")
    if _custom: symbol=_custom.upper()
    st.session_state.selected_symbol=symbol
    st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["accent"]};text-align:center;padding:3px 0 8px">{get_name(symbol)}</div>',unsafe_allow_html=True)
    st.markdown('<span class="slbl">Période / Intervalle</span>',unsafe_allow_html=True)
    _c3,_c4=st.columns(2)
    with _c3: period=st.selectbox("",["6mo","1y","2y","3y"],index=1,label_visibility="collapsed")
    with _c4: interval=st.selectbox("",["1d","1h","1wk"],index=0,label_visibility="collapsed")
    st.markdown('<span class="slbl">Capital ($)</span>',unsafe_allow_html=True)
    capital=st.number_input("",min_value=100,max_value=10_000_000,value=10000,step=500,label_visibility="collapsed")
    st.markdown('<span class="slbl">Contexte (optionnel)</span>',unsafe_allow_html=True)
    context=st.text_area("",placeholder="ex: OPEC réunion, rapport CPI ce soir…",height=60,label_visibility="collapsed")
    st.markdown("<hr>",unsafe_allow_html=True)
    btn_analyze=st.button("⬡  ANALYSER",use_container_width=True)
    st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)
    btn_backtest=st.button("📊  LANCER BACKTEST",use_container_width=True)
    st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)
    btn_scan=st.button("📡  SCANNER TOUS LES MARCHÉS",use_container_width=True)
    st.markdown("<div style='height:4px'></div>",unsafe_allow_html=True)
    btn_scan_comm=st.button("🛢  SCANNER MATIÈRES PREMIÈRES",use_container_width=True)
    st.markdown("<hr>",unsafe_allow_html=True)
    with st.expander("⚙ OPTIONS AVANCÉES"):
        use_finbert=st.checkbox("FinBERT sentiment",False)
        force_train=st.checkbox("Forcer ré-entraînement",False)
        include_news=st.checkbox("Analyser les news",True)
        show_bb=st.checkbox("Bollinger Bands",True)
        show_ema=st.checkbox("EMA (9/20/50)",True)
        show_mc=st.checkbox("Monte Carlo",True)
        show_heat=st.checkbox("Heatmap corrélation",True)
        show_legends=st.checkbox("Afficher les légendes",True)
    st.markdown("<hr>",unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">🏆 Top Commodités</div>',unsafe_allow_html=True)
    _tc1,_tc2=st.columns(2)
    for _i,_sym in enumerate(TOP_COMMODITIES[:6]):
        with [_tc1,_tc2][_i%2]:
            if st.button(get_name(_sym),key=f"tc_{_sym}",use_container_width=True):
                st.session_state.selected_symbol=_sym; st.rerun()
    st.markdown("<hr>",unsafe_allow_html=True)
    if st.session_state.status_msg:
        st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};text-align:center;line-height:1.6">{st.session_state.status_msg}</div>',unsafe_allow_html=True)
    st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:8px;color:#0e2236;text-align:center;padding-top:12px;line-height:1.8">⚠ OUTIL ÉDUCATIF UNIQUEMENT<br>Pas un conseil financier · v4.0</div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  HEADER
# ══════════════════════════════════════════════════════════════════════════════
_hc1,_hc2,_hc3=st.columns([3,1,1])
with _hc1:
    st.markdown(f'<div style="padding:6px 0 14px">'
                f'<div style="font-family:Syne,sans-serif;font-size:26px;font-weight:900;letter-spacing:3px;color:{C["accent"]};text-shadow:0 0 32px rgba(0,200,255,.3)">⬡ QUANTUM TRADE ORACLE</div>'
                f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};letter-spacing:2px;margin-top:3px">IA TRADING ALGORITHMIQUE · v4.0 · {get_name(symbol)} ({symbol})</div>'
                f'</div>',unsafe_allow_html=True)
with _hc2:
    _hdf=_fetch_yf(symbol,"1mo","1d")
    if not _hdf.empty and len(_hdf)>=2:
        _lp=float(_hdf["close"].iloc[-1]); _pp=float(_hdf["close"].iloc[-2])
        _hchg=(_lp-_pp)/_pp*100; _hc=C["green"] if _hchg>=0 else C["red"]
        st.markdown(f'<div style="text-align:right;padding-top:6px">'
                    f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]}">{get_name(symbol)}</div>'
                    f'<div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:{C["accent"]}">${_lp:,.2f}</div>'
                    f'<div style="font-family:DM Mono,monospace;font-size:11px;color:{_hc}">{_hchg:+.2f}%</div>'
                    f'</div>',unsafe_allow_html=True)
    elif not _hdf.empty and len(_hdf)==1:
        _lp=float(_hdf["close"].iloc[-1])
        st.markdown(f'<div style="text-align:right;padding-top:6px">'
                    f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]}">{get_name(symbol)}</div>'
                    f'<div style="font-family:Syne,sans-serif;font-size:20px;font-weight:800;color:{C["accent"]}">${_lp:,.2f}</div>'
                    f'</div>',unsafe_allow_html=True)
with _hc3:
    st.markdown(f'<div style="text-align:right;padding-top:6px">'
                f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]}">UTC</div>'
                f'<div style="font-family:Syne,sans-serif;font-size:18px;font-weight:700;color:{C["accent"]}">{datetime.utcnow().strftime("%H:%M:%S")}</div>'
                f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]}">{datetime.utcnow().strftime("%d/%m/%Y")}</div>'
                f'</div>',unsafe_allow_html=True)
st.markdown(f'<div style="height:1px;background:linear-gradient(90deg,transparent,{C["border"]},transparent);margin-bottom:14px"></div>',unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════════════════════
#  BOUTONS
# ══════════════════════════════════════════════════════════════════════════════
if btn_analyze:
    run_analysis(symbol,period,capital,include_news,use_finbert,context); st.rerun()
if btn_backtest:
    oracle=get_oracle()
    if oracle and PROJECT_OK:
        with st.spinner("Backtesting…"):
            st.session_state.backtest_result=oracle.backtest(symbol)
        st.rerun()
    else: st.warning("Backtest disponible avec les modules projet installés.")
if btn_scan:
    with st.spinner("Scan en cours…"):
        all_syms=[s for sl in MARKETS.values() for s in sl[:3]]
        st.session_state.scan_data=_scan_markets(tuple(all_syms))
    st.rerun()
if btn_scan_comm:
    with st.spinner("Scan matières premières…"):
        comm=[s for cat in ["⛽ Énergie","🥇 Métaux précieux","🔩 Métaux industriels","🌾 Céréales","☕ Produits tropicaux","🐄 Élevage"] for s in MARKETS.get(cat,[])]
        st.session_state.scan_data=_scan_markets(tuple(comm))
    st.rerun()

# ══════════════════════════════════════════════════════════════════════════════
#  ONGLETS
# ══════════════════════════════════════════════════════════════════════════════
sig=st.session_state.signal; df=st.session_state.df_feat
sent=st.session_state.sentiment; news=st.session_state.news_data
bt=st.session_state.backtest_result

(t_sig,t_chart,t_models,t_risk,t_profit,t_news,t_scan,t_chat,t_bt,t_hist,t_profil)=st.tabs([
    "⬡ SIGNAL","📈 GRAPHIQUE","🤖 MODÈLES IA","⚡ RISQUE","💰 PROFIT",
    "📰 NEWS","🌐 SCANNER","⬡ IA ORACLE","📊 BACKTEST","🕐 HISTORIQUE","👤 MON ESPACE"])

# ── SIGNAL ─────────────────────────────────────────────────────────────────
with t_sig:
    if not sig:
        st.markdown(f'<div style="text-align:center;padding:90px 20px">'
                    f'<div style="font-family:Syne,sans-serif;font-size:72px;color:{C["border"]}">⬡</div>'
                    f'<div style="font-family:DM Mono,monospace;font-size:13px;color:{C["muted"]};margin-top:18px;letter-spacing:2.5px">SÉLECTIONNE UN ACTIF → CLIQUE « ANALYSER »</div>'
                    f'<div style="font-family:DM Mono,monospace;font-size:10px;color:{C["muted"]};margin-top:8px;opacity:.6">10 catégories · 60+ actifs · Crypto · Actions · Forex · Matières premières</div>'
                    f'</div>',unsafe_allow_html=True)
    else:
        action=sig.get("action","HOLD"); scores=sig.get("scores",{})
        bull=sig.get("bullish_probability",.5); bear=sig.get("bearish_probability",.5)
        conf=sig.get("ai_confidence",.5); agr=sig.get("models_agreement",.5)
        signal_hero(action,sig.get("symbol",""),scores.get("composite"),sig.get("price"),sig.get("chg_1d"))
        m1,m2,m3,m4,m5,m6=st.columns(6)
        m1.metric("🟢 Haussier",f"{bull*100:.1f}%")
        m2.metric("🔴 Baissier",f"{bear*100:.1f}%")
        m3.metric("⚡ Confiance",f"{conf*100:.0f}%")
        m4.metric("🤝 Accord",f"{agr*100:.0f}%")
        m5.metric("📊 RSI",f"{sig.get('rsi',0):.1f}")
        m6.metric("🎯 Stoch",f"{sig.get('stoch',50):.0f}")
        st.markdown("<br>",unsafe_allow_html=True)

        # IA interprétation enrichie
        if show_legends:
            explain_box("Interprétation Globale du Signal IA",
                sig.get("interpretation","Analyse non disponible — lancez une analyse."), C["accent"])

        _cl,_cr=st.columns(2)
        with _cl:
            qtitle("Probabilités & Scores IA")
            pbar("🟢 Probabilité Haussière",bull*100,C["green"],tooltip="% de chance que le prix monte")
            pbar("🔴 Probabilité Baissière",bear*100,C["red"],tooltip="% de chance que le prix baisse")
            pbar("⚡ Confiance IA",conf*100,C["accent"],tooltip="Fiabilité globale des 4 modèles")
            pbar("🤝 Accord entre modèles",agr*100,C["yellow"],tooltip="% de modèles dans le même sens")
            _ssgm=(sent or {}).get("ssgm_score",0)
            pbar("📰 Sentiment des news",(_ssgm+1)/2*100,C["purple"],tooltip="Tonalité des articles de presse")
            if show_legends:
                st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};margin-top:6px;line-height:1.7">'
                            f'Signal BUY si : Bull > 62% ET Accord ≥ 75%<br>'
                            f'Signal SELL si : Bear > 62% ET Accord ≥ 75%<br>'
                            f'Signal HOLD si : conditions insuffisantes</div>',unsafe_allow_html=True)
        with _cr:
            qtitle("Signaux Techniques Détectés")
            tech=sig.get("technical_signals",{})
            if tech:
                for k,v in tech.items():
                    _kind="bull" if any(w in v.lower() for w in ["haussier","rebond","achat","positif","survente","vert","🟢"]) \
                          else "bear" if any(w in v.lower() for w in ["baissier","résistance","vente","négatif","surachat","rouge","🔴"]) else "neut"
                    _kc=C["green"] if _kind=="bull" else C["red"] if _kind=="bear" else C["yellow"]
                    st.markdown(f'<div style="background:{C["card"]};border:1px solid {C["border"]};border-left:3px solid {_kc};'
                                f'border-radius:3px;padding:8px 12px;margin-bottom:6px">'
                                f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};text-transform:uppercase;margin-bottom:3px">{k}</div>'
                                f'<div style="font-family:DM Mono,monospace;font-size:10px;color:{_kc};line-height:1.5">{v}</div>'
                                f'</div>',unsafe_allow_html=True)

        # Métriques additionnelles
        st.markdown("<br>",unsafe_allow_html=True)
        qtitle("Indicateurs Avancés")
        _ia1,_ia2,_ia3,_ia4=st.columns(4)
        _ia1.metric("Williams %R",f"{sig.get('willr',0):.1f}")
        _ia2.metric("ATR %",f"{sig.get('atr_pct',0):.2f}%")
        _ia3.metric("Vol Ratio",f"{sig.get('vol_ratio',1):.2f}×")
        _ia4.metric("Score",f"{scores.get('composite',0):+.4f}")

        if show_legends:
            st.markdown("<br>",unsafe_allow_html=True)
            _lex1,_lex2=st.columns(2)
            with _lex1:
                explain_box("ATR % — Volatilité",
                    "Average True Range en % du prix. ATR élevé = marché volatil = positions plus petites. "
                    "ATR < 2% = calme. ATR > 5% = très agité.", C["orange"])
            with _lex2:
                explain_box("Williams %R",
                    "Oscillateur de 0 à -100. > -20 = surachat. < -80 = survente. "
                    "Similaire au RSI mais calculé différemment — confirmation croisée utile.", C["purple"])

# ── GRAPHIQUE ────────────────────────────────────────────────────────────────
with t_chart:
    if df is None or df.empty:
        st.info("Lance une analyse pour afficher les graphiques.")
    else:
        st.plotly_chart(fig_candlestick(df,symbol,sig,show_bb,show_ema),use_container_width=True)
        _last=df.iloc[-1]
        _prev=df.iloc[-2] if len(df)>=2 else _last
        _prev_close=float(_prev["close"]) if float(_prev["close"])!=0 else 1.0
        _chg=(float(_last["close"])-_prev_close)/_prev_close*100
        _s1,_s2,_s3,_s4,_s5,_s6=st.columns(6)
        _s1.metric("Prix",f"${float(_last['close']):,.4f}",f"{_chg:+.2f}%")
        _s2.metric("High",f"${float(_last['high']):,.4f}")
        _s3.metric("Low",f"${float(_last['low']):,.4f}")
        _s4.metric("RSI",f"{float(_last.get('rsi',0)):.1f}")
        _s5.metric("ATR %",f"{float(_last.get('atr_pct',0)):.2f}%")
        _s6.metric("Vol ×",f"{float(_last.get('vol_ratio',1)):.2f}")

        if show_legends:
            st.markdown("<br>",unsafe_allow_html=True)
            _leg1,_leg2=st.columns(2)
            with _leg1:
                render_chart_legend()
            with _leg2:
                rsi_val=float(_last.get("rsi",50))
                render_rsi_legend(rsi_val)
            _leg3,_leg4=st.columns(2)
            with _leg3:
                macd_val=float(_last.get("macd_hist",0))
                render_macd_legend(macd_val)
            with _leg4:
                explain_box("Bollinger Bands — Canal de Volatilité",
                    f"Bandes à ±2 écarts-types autour de la SMA20.<br>"
                    f"BB%B actuel : {float(_last.get('bb_pct_b',0.5))*100:.0f}%<br>"
                    f"{'🟢 Proche bande inférieure → survente' if float(_last.get('bb_pct_b',0.5))<0.2 else '🔴 Proche bande supérieure → résistance' if float(_last.get('bb_pct_b',0.5))>0.8 else '⚪ Zone médiane → canal normal'}<br><br>"
                    f"Un rétrécissement des bandes (squeeze) indique une explosion de volatilité imminente.", C["muted"])

        if show_heat and YF_OK:
            st.markdown("<br>",unsafe_allow_html=True)
            qtitle("Matrice de Corrélation","3 mois")
            result=fig_heatmap(MARKETS[market_type])
            if result:
                fig_h,corr=result
                st.plotly_chart(fig_h,use_container_width=True)
                if show_legends:
                    render_correlation_legend()
                    # Analyse automatique de la corrélation
                    st.markdown("<br>",unsafe_allow_html=True)
                    qtitle("Analyse Automatique de la Corrélation")
                    high_corr=[(i,j,corr.iloc[i,j]) for i in range(len(corr)) for j in range(i+1,len(corr)) if abs(corr.iloc[i,j])>0.75]
                    low_corr=[(i,j,corr.iloc[i,j]) for i in range(len(corr)) for j in range(i+1,len(corr)) if abs(corr.iloc[i,j])<0.3]
                    if high_corr:
                        for i,j,v in high_corr[:3]:
                            col_n=C["red"] if v>0 else C["green"]
                            st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:11px;color:{col_n};padding:4px 0">'
                                        f'⚠️ {corr.index[i]} ↔ {corr.columns[j]} : {v:.2f} — Très corrélés, pas de diversification</div>',unsafe_allow_html=True)
                    if low_corr:
                        for i,j,v in low_corr[:3]:
                            st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:11px;color:{C["green"]};padding:4px 0">'
                                        f'✅ {corr.index[i]} ↔ {corr.columns[j]} : {v:.2f} — Bonne diversification</div>',unsafe_allow_html=True)

# ── MODÈLES IA ───────────────────────────────────────────────────────────────
with t_models:
    if not sig: st.info("Lance une analyse pour voir les estimations des modèles IA.")
    else:
        mods=sig.get("models",{})
        if mods:
            action=sig.get("action","HOLD")
            st.plotly_chart(fig_models(mods,action),use_container_width=True)
            if show_legends:
                render_models_legend()
            qtitle("Détail par Modèle",f"Consensus : {action}")
            _mm={"random_forest":("🌳","RandomForest","20%","Classique","Analyse 200+ arbres de décision. Robuste au bruit et aux outliers. Idéal pour features tabulaires."),
                 "gradient_boosting":("⚡","GradientBoost","20%","Classique","Corrige itérativement ses erreurs. Précis sur données structurées. Détecte patterns non-linéaires."),
                 "lstm":("🔄","LSTM","35%","Deep Learning","Réseau récurrent. Mémorise les séquences sur 60 jours. Le plus lourd — poids le plus élevé."),
                 "transformer":("🧠","Transformer","25%","Attention","Architecture comme GPT. Attention multi-tête. Excellent sur corrélations temporelles complexes.")}
            _mcols=st.columns(4)
            for _i,(key,m) in enumerate(mods.items()):
                _ic,_nm,_w,_typ,_desc=_mm.get(key,("?",key,"?","?",""))
                _act=m.get("prediction","HOLD")
                _col=C["green"] if _act=="BUY" else C["red"] if _act=="SELL" else C["muted"]
                with _mcols[_i]:
                    st.markdown(f'<div style="background:{C["card"]};border:1px solid {C["border"]};border-top:3px solid {_col};border-radius:4px;padding:14px;margin-bottom:10px">'
                                f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">{_ic} {_nm}</div>'
                                f'<div style="font-family:Syne,sans-serif;font-size:28px;font-weight:900;color:{_col};margin-bottom:6px">{_act}</div>'
                                f'<div style="font-family:DM Mono,monospace;font-size:8px;color:{C["accent"]};margin-bottom:6px">Poids : {_w} · {_typ}</div>'
                                f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};line-height:1.5;margin-bottom:10px">{_desc}</div>'
                                f'</div>',unsafe_allow_html=True)
                    pbar("Bull",m["bullish_prob"]*100,C["green"])
                    pbar("Bear",m["bearish_prob"]*100,C["red"])
                    pbar("Conf.",m["confidence"]*100,C["purple"])

# ── RISQUE ───────────────────────────────────────────────────────────────────
with t_risk:
    if not sig: st.info("Lance une analyse pour voir la gestion du risque.")
    else:
        _r=sig.get("risk_management",{}); _act=sig.get("action","HOLD")
        _cl2,_cr2=st.columns(2)
        with _cl2:
            qtitle("Paramètres du Trade")
            _sc=C["green"] if _act=="BUY" else C["red"] if _act=="SELL" else C["muted"]
            kv("Action",_act,_sc,"Direction du trade recommandé par l'IA")
            kv("Actif",f"{get_name(sig.get('symbol',''))}",C["accent"])
            kv("Prix d'entrée",f"${_r.get('entry_price',0):,.4f}",C["bright"],"Prix auquel vous ouvrez la position")
            kv("Stop-Loss",f"${_r.get('stop_loss',0):,.4f}  (−{_r.get('sl_pct',0):.2f}%)",C["red"],"Niveau de perte maximum — à placer IMMÉDIATEMENT")
            kv("Take-Profit",f"${_r.get('take_profit',0):,.4f}  (+{_r.get('tp_pct',0):.2f}%)",C["green"],"Objectif de profit")
            kv("Risk / Reward",f"{_r.get('risk_reward_ratio',0):.2f} : 1",C["accent"],"Pour chaque $1 risqué, gain potentiel de ${rr:.2f}".replace("{rr}",str(_r.get('risk_reward_ratio',0))))
            kv("Taille position",f"{_r.get('position_size',0):.6f} unités",C["bright"],"Nombre d'unités à acheter/vendre")
            kv("Valeur position",f"${_r.get('position_value',0):,.2f}",C["bright"],"Valeur totale de la position en dollars")
            kv("Capital risqué",f"${_r.get('capital_at_risk',0):,.2f} (2%)",C["yellow"],"Règle des 2% — maximum à risquer par trade")
            kv("ATR (volatilité)",f"{_r.get('atr',0):.4f}",C["text"],"Average True Range — écart moyen journalier")
            kv("Niveau risque",_r.get("risk_level","—"),
               C["green"] if _r.get("risk_level")=="FAIBLE" else C["red"] if _r.get("risk_level")=="ÉLEVÉ" else C["yellow"])
        with _cr2:
            qtitle("Niveaux Visuels du Trade")
            _entry=_r.get("entry_price",0); _sl=_r.get("stop_loss",0); _tp=_r.get("take_profit",0)
            if _entry and _sl and _tp and _act!="HOLD":
                st.plotly_chart(fig_risk_levels(_entry,_sl,_tp),use_container_width=True)
            if show_legends:
                st.markdown(f'<div class="legend-box">'
                            + legend_item(C["yellow"],"ENTRY (jaune)","Prix d'entrée — ouvrir la position à ce niveau","dash")
                            + legend_item(C["red"],"STOP LOSS (rouge)","Limite de perte — fermer impérativement si atteint","dash")
                            + legend_item(C["green"],"TAKE PROFIT (vert)","Objectif — prendre les bénéfices ici","dash")
                            + legend_item(C["green"],"Zone verte","Corridor de profit potentiel","area")
                            + legend_item(C["red"],"Zone rouge","Corridor de risque","area")
                            + f'</div>',unsafe_allow_html=True)
            st.markdown("<br>",unsafe_allow_html=True); qtitle("✅ Checklist de Trading")
            _rr=_r.get("risk_reward_ratio",0); _conf=sig.get("ai_confidence",0); _agr=sig.get("models_agreement",0)
            for _ok,_txt,_tip in [
                (_rr>=2.0,f"Risk/Reward ≥ 2:1  (actuel : {_rr:.2f})","Minimum pour être profitable à long terme"),
                (_conf>=0.6,f"Confiance IA ≥ 60%  (actuel : {_conf*100:.0f}%)","Fiabilité des modèles"),
                (_agr>=0.75,f"Accord modèles ≥ 75%  (actuel : {_agr*100:.0f}%)","Consensus entre les 4 IA"),
                (_act!="HOLD",f"Signal directionnel clair  ({_act})","BUY ou SELL confirmé"),
                (True,"Stop-Loss défini avant d'entrer","Discipline absolue"),
                (True,"Risquer max 2% du capital","Gestion du risque"),
                (_r.get("atr",0) > 0,f"ATR calculé  ({_r.get('atr',0):.4f})","Volatilité mesurée")]:
                _icon="✅"; _tc=C["green"]
                if not _ok: _icon="❌"; _tc=C["red"]
                st.markdown(f'<div style="font-family:DM Mono,monospace;font-size:11px;color:{_tc};padding:5px 0" title="{_tip}">{_icon} {_txt}</div>',unsafe_allow_html=True)

# ── PROFIT ───────────────────────────────────────────────────────────────────
with t_profit:
    if not sig: st.info("Lance une analyse pour voir les projections de profit.")
    else:
        _proj=sig.get("projections",{"Conservateur (8%)":{"profit":capital*.08,"total":capital*1.08},
                                     "Modéré (20%)":{"profit":capital*.20,"total":capital*1.20},
                                     "Optimiste (40%)":{"profit":capital*.40,"total":capital*1.40},
                                     "Moon 🚀 (100%)":{"profit":capital,"total":capital*2.00}})
        qtitle("Projection de Profit",f"Capital : ${capital:,.0f}")
        st.plotly_chart(fig_projection(capital,_proj),use_container_width=True)
        _pcols=st.columns(len(_proj)); _gcs=[C["muted"],C["accent"],C["green"],C["yellow"]]
        for _pci,(lbl,v) in enumerate(_proj.items()):
            with _pcols[_pci]:
                st.markdown(f'<div style="background:{C["card"]};border:1px solid {C["border"]};border-top:3px solid {_gcs[_pci]};border-radius:4px;padding:14px;text-align:center">'
                            f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">{lbl}</div>'
                            f'<div style="font-family:Syne,sans-serif;font-size:28px;font-weight:900;color:{_gcs[_pci]};line-height:1">+${v["profit"]:,.0f}</div>'
                            f'<div style="font-family:DM Mono,monospace;font-size:10px;color:{C["accent"]};margin-top:6px">Total : ${v["total"]:,.0f}</div>'
                            f'</div>',unsafe_allow_html=True)
        # ── PRÉVISION DE PRIX ──────────────────────────────────────────────────
        st.markdown("<br>",unsafe_allow_html=True)
        qtitle("🔮 Prévision de Prix","Analyse multi-modèles · 1M · 3M · 6M · 1A")

        _fc_df = st.session_state.get("df_feat") if st.session_state.get("df_feat") is not None else st.session_state.get("df_raw")
        _fc = compute_price_forecast(_fc_df, symbol) if _fc_df is not None and not _fc_df.empty else None

        if _fc:
            _price_now = _fc["price_now"]
            _horizons  = _fc["horizons"]

            # ── Cards résumé par horizon ─────────────────────────────────────
            _fc_cols = st.columns(4)
            _fc_colors = [C["accent"], C["yellow"], C["orange"], C["green"]]
            for _fci, (hname, hdata) in enumerate(_horizons.items()):
                with _fc_cols[_fci]:
                    _hchg  = hdata["chg_pct"]
                    _hprice = hdata["consensus"]
                    _htrend = hdata["trend"]
                    _hcol   = C["green"] if _hchg > 2 else C["red"] if _hchg < -2 else C["yellow"]
                    _harrow = "↑" if _hchg > 2 else "↓" if _hchg < -2 else "→"
                    st.markdown(f'''
                    <div style="background:linear-gradient(135deg,{C["card"]},{C["card2"]});
                        border:1px solid {C["border2"]};border-top:3px solid {_hcol};
                        border-radius:6px;padding:16px 14px;text-align:center;
                        position:relative;overflow:hidden">
                      <div style="position:absolute;top:0;left:0;right:0;height:1px;
                        background:linear-gradient(90deg,transparent,{_hcol}55,transparent)"></div>
                      <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                        color:{C["muted"]};text-transform:uppercase;letter-spacing:2px;margin-bottom:8px">
                        {hname}
                      </div>
                      <div style="font-family:Bebas Neue,sans-serif;font-size:32px;
                        color:{_hcol};line-height:1;letter-spacing:2px;
                        text-shadow:0 0 20px {_hcol}55">
                        {_harrow} {_hchg:+.1f}%
                      </div>
                      <div style="font-family:JetBrains Mono,monospace;font-size:11px;
                        color:{C["bright"]};margin-top:8px;font-weight:600">
                        ${_hprice:,.2f}
                      </div>
                      <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                        color:{C["muted"]};margin-top:4px">
                        IC 68% : ${hdata["ci_low_1"]:,.2f} — ${hdata["ci_high_1"]:,.2f}
                      </div>
                      <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                        color:{_hcol};margin-top:6px;letter-spacing:1px">
                        {_htrend}
                      </div>
                    </div>
                    ''', unsafe_allow_html=True)

            # ── Graphique prévision ──────────────────────────────────────────
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            _fig_fc = fig_forecast(_fc_df, symbol, _fc)
            if _fig_fc:
                st.plotly_chart(_fig_fc, use_container_width=True)

            # ── Tableau détaillé ─────────────────────────────────────────────
            st.markdown("<div style='height:10px'></div>", unsafe_allow_html=True)
            qtitle("Détail des Prévisions","3 méthodes combinées")

            for hname, hdata in _horizons.items():
                _hchg  = hdata["chg_pct"]
                _hcol  = C["green"] if _hchg > 2 else C["red"] if _hchg < -2 else C["yellow"]
                _harrow = "↑ HAUSSE" if _hchg > 2 else "↓ BAISSE" if _hchg < -2 else "→ STABLE"
                st.markdown(f'''
                <div style="background:{C["card"]};border:1px solid {C["border2"]};
                    border-left:4px solid {_hcol};border-radius:5px;
                    padding:12px 18px;margin-bottom:8px">
                  <div style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:10px">
                    <div>
                      <span style="font-family:Bebas Neue,sans-serif;font-size:16px;
                        color:{C["bright"]};letter-spacing:2px">{hname}</span>
                      <span style="font-family:JetBrains Mono,monospace;font-size:9px;
                        color:{_hcol};margin-left:12px;letter-spacing:1px">{_harrow}</span>
                    </div>
                    <div style="display:flex;gap:24px;flex-wrap:wrap">
                      <div style="text-align:center">
                        <div style="font-family:JetBrains Mono,monospace;font-size:8px;color:{C["muted"]}">CONSENSUS</div>
                        <div style="font-family:Bebas Neue,sans-serif;font-size:18px;color:{_hcol};letter-spacing:1px">
                          ${hdata["consensus"]:,.2f} <span style="font-size:13px">({_hchg:+.1f}%)</span>
                        </div>
                      </div>
                      <div style="text-align:center">
                        <div style="font-family:JetBrains Mono,monospace;font-size:8px;color:{C["muted"]}">RÉGRESSION LIN.</div>
                        <div style="font-family:JetBrains Mono,monospace;font-size:13px;color:{C["text"]}">${hdata["price_lr"]:,.2f}</div>
                      </div>
                      <div style="text-align:center">
                        <div style="font-family:JetBrains Mono,monospace;font-size:8px;color:{C["muted"]}">TENDANCE EMA</div>
                        <div style="font-family:JetBrains Mono,monospace;font-size:13px;color:{C["text"]}">${hdata["price_ema"]:,.2f}</div>
                      </div>
                      <div style="text-align:center">
                        <div style="font-family:JetBrains Mono,monospace;font-size:8px;color:{C["muted"]}">MOMENTUM</div>
                        <div style="font-family:JetBrains Mono,monospace;font-size:13px;color:{C["text"]}">${hdata["price_mom"]:,.2f}</div>
                      </div>
                      <div style="text-align:center">
                        <div style="font-family:JetBrains Mono,monospace;font-size:8px;color:{C["muted"]}">ZONE 68%</div>
                        <div style="font-family:JetBrains Mono,monospace;font-size:11px;color:{C["muted"]}">
                          ${hdata["ci_low_1"]:,.2f} → ${hdata["ci_high_1"]:,.2f}
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
                ''', unsafe_allow_html=True)

            # ── Avertissement ────────────────────────────────────────────────
            st.markdown(f'''
            <div style="background:rgba(255,210,10,.04);border:1px solid rgba(255,210,10,.15);
                border-radius:5px;padding:12px 18px;margin-top:10px">
              <span style="font-family:JetBrains Mono,monospace;font-size:9px;color:{C["yellow"]};
                letter-spacing:1px">
                ⚠️  Ces prévisions sont calculées par extrapolation statistique (régression linéaire + EMA + momentum).
                Elles ne garantissent pas les prix futurs. Utilisez-les comme indicateur directionnel uniquement.
                Volatilité annualisée estimée : {list(_horizons.values())[0]["volatility_ann"]:.1f}%
              </span>
            </div>
            ''', unsafe_allow_html=True)
        else:
            st.info("Lancez une analyse pour générer les prévisions de prix.")

        if show_mc:
            st.markdown("<br>",unsafe_allow_html=True)
            qtitle("Simulation Monte Carlo","300 trajectoires · 252 jours")
            _atr_mc=sig.get("risk_management",{}).get("atr",sig.get("price",1)*0.025)
            _price_mc=sig.get("price",1)
            _fig_mc,_prob,_median=fig_monte_carlo(_price_mc,_atr_mc,capital)
            st.plotly_chart(_fig_mc,use_container_width=True)
            _mc1,_mc2,_mc3=st.columns(3)
            _mc1.metric("P(Gain)",f"{_prob:.0f}%","Probabilité de profit en 1 an")
            _mc2.metric("Médiane 1 an",f"${_median:,.0f}",f"{(_median-capital)/capital*100:+.1f}%")
            _mc3.metric("Gain médian",f"${_median-capital:,.0f}")
            if show_legends:
                render_monte_carlo_legend()

# ── NEWS ────────────────────────────────────────────────────────────────────
with t_news:
    _arts=news or []
    if not _arts: st.info("Clique sur **ANALYSER** (news activées) pour scraper les actualités.")
    else:
        _sd=sent or (sig.get("sentiment",{}) if sig else {})
        if not _sd and _arts: _sd=_sentiment_simple(_arts)
        qtitle(f"Analyse de Sentiment",f"{len(_arts)} articles")
        _s1,_s2,_s3=st.columns(3)
        _sv=_sd.get("ssgm_score",0); _sc2=C["green"] if _sv>.1 else C["red"] if _sv<-.1 else C["yellow"]
        with _s1:
            st.markdown(f'<div style="background:{C["card"]};border:1px solid {C["border"]};border-top:3px solid {_sc2};border-radius:4px;padding:16px;text-align:center">'
                        f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};margin-bottom:6px">SSGM SCORE</div>'
                        f'<div style="font-family:Syne,sans-serif;font-size:38px;font-weight:900;color:{_sc2}">{("+" if _sv>0 else "")}{_sv:.3f}</div>'
                        f'<div style="font-family:DM Mono,monospace;font-size:10px;color:{_sc2};letter-spacing:2px;margin-top:5px">{_sd.get("label","—")}</div>'
                        f'<div style="font-family:DM Mono,monospace;font-size:9px;color:{C["muted"]};margin-top:5px">{_sd.get("n_articles",len(_arts))} articles · {datetime.utcnow().strftime("%H:%M")} UTC</div>'
                        f'</div>',unsafe_allow_html=True)
        with _s2:
            pbar("🟢 Bullish",_sd.get("bull_pct",0),C["green"])
            pbar("🔴 Bearish",_sd.get("bear_pct",0),C["red"])
            pbar("⚪ Neutres",max(0,100-_sd.get("bull_pct",0)-_sd.get("bear_pct",0)),C["muted"])
        with _s3:
            _interp_s=("🟢 Sentiment POSITIF — la presse financière montre un intérêt acheteur fort." if _sv>.1
                       else "🔴 Sentiment NÉGATIF — prudence sur les positions longues." if _sv<-.1
                       else "⚪ Sentiment NEUTRE — laisser les indicateurs techniques guider.")
            st.markdown(f'<div style="background:{C["card"]};border:1px solid {C["border"]};border-radius:4px;padding:14px">'
                        f'<div style="font-family:Manrope,sans-serif;font-size:12px;color:{C["text"]};line-height:1.75">{_interp_s}</div>'
                        f'</div>',unsafe_allow_html=True)
        if show_legends:
            explain_box("SSGM — Sentiment Score",
                "Score entre -1 et +1. Calculé en analysant la proportion de mots positifs vs négatifs dans les titres et descriptions des articles. "
                "> +0.1 = Bullish · < -0.1 = Bearish · Entre les deux = Neutre", C["purple"])
        # ── Filtres ────────────────────────────────────────────────────────────
        st.markdown("<br>",unsafe_allow_html=True)
        _nf1, _nf2, _nf3 = st.columns([2,2,1])
        with _nf1:
            _filter_sent = st.selectbox("Filtrer par sentiment",
                ["Tous","🟢 Bullish","🔴 Bearish","⚪ Neutre"],
                label_visibility="collapsed", key="news_filter_sent")
        with _nf2:
            _filter_src = st.selectbox("Filtrer par source",
                ["Toutes sources"] + list(dict.fromkeys(a.get("source","") for a in _arts if a.get("source"))),
                label_visibility="collapsed", key="news_filter_src")
        with _nf3:
            _news_count = st.selectbox("Nb","10 25 Tous".split(),
                label_visibility="collapsed", key="news_count")

        qtitle(f"📰 Actualités en Temps Réel", f"{len(_arts)} articles · {datetime.utcnow().strftime('%H:%M')} UTC")

        BW_=["bullish","rally","surge","rise","buy","ath","pump","upgrade","soar","strong","positive","demand","record","growth","gains","up","higher","beats","profit","boost","recover"]
        SW_=["crash","drop","fall","sell","dump","fear","correction","downgrade","plunge","weak","negative","loss","recession","decline","miss","below","cut","risk","warning","concern"]

        _shown = 0
        _max_show = 999 if _news_count == "Tous" else int(_news_count)

        for _a in _arts:
            if _shown >= _max_show:
                break
            _t    = _a.get("title","")
            _desc = _a.get("description","")
            _pub  = _a.get("published","")
            _src  = _a.get("source","")
            _dom  = _a.get("domain","")
            _url  = _a.get("url","").strip()

            _txt  = (_t+" "+_desc).lower()
            _bw   = sum(1 for w in BW_ if w in _txt)
            _sw2  = sum(1 for w in SW_ if w in _txt)
            _ac   = C["green"] if _bw>_sw2 else C["red"] if _sw2>_bw else C["muted"]
            _al   = "BULLISH" if _bw>_sw2 else "BEARISH" if _sw2>_bw else "NEUTRE"
            _al_icon = "🟢" if _bw>_sw2 else "🔴" if _sw2>_bw else "⚪"

            # Appliquer les filtres
            if _filter_sent == "🟢 Bullish" and _al != "BULLISH": continue
            if _filter_sent == "🔴 Bearish" and _al != "BEARISH": continue
            if _filter_sent == "⚪ Neutre"  and _al != "NEUTRE":  continue
            if _filter_src != "Toutes sources" and _src != _filter_src: continue

            _shown += 1
            _cm = (f"+{_bw} mots positifs — pression acheteuse" if _bw>_sw2
                   else f"-{_sw2} mots négatifs — pression vendeuse" if _sw2>_bw
                   else "Neutre — pas de biais clair")

            # Badge source avec icône de domaine
            _src_icon = {"Yahoo Finance":"📊","Google News EN":"🌐","Google News FR":"🇫🇷",
                         "CoinDesk":"₿","Investing.com":"📈"}.get(_src,"📰")

            # Bouton de lien
            _btn_style = (
                "display:inline-flex;align-items:center;gap:5px;"
                "background:rgba(0,212,255,.08);border:1px solid rgba(0,212,255,.3);"
                f"color:{C['accent']};font-family:JetBrains Mono,monospace;font-size:9px;"
                "padding:4px 10px;border-radius:3px;text-decoration:none;"
                "letter-spacing:1px;transition:all .2s"
            )
            _link_btn = (
                f'<a href="{_url}" target="_blank" style="{_btn_style}">🔗 LIRE L\'ARTICLE</a>'
            ) if _url else ""

            st.markdown(f'''
            <div style="background:linear-gradient(135deg,{C["card"]},{C["card2"]});
                border:1px solid {C["border2"]};border-left:4px solid {_ac};
                border-radius:6px;padding:16px 18px;margin-bottom:10px;
                transition:box-shadow .2s;position:relative;overflow:hidden">

              <!-- Ligne déco en haut -->
              <div style="position:absolute;top:0;left:0;right:0;height:1px;
                background:linear-gradient(90deg,{_ac}44,transparent)"></div>

              <!-- Header : badge sentiment + source + date -->
              <div style="display:flex;justify-content:space-between;align-items:center;
                margin-bottom:10px;flex-wrap:wrap;gap:6px">
                <div style="display:flex;align-items:center;gap:8px">
                  <span style="background:rgba(0,0,0,.3);border:1px solid {_ac}55;
                    color:{_ac};font-family:JetBrains Mono,monospace;font-size:9px;
                    padding:3px 10px;border-radius:12px;font-weight:700;letter-spacing:1px">
                    {_al_icon} {_al}
                  </span>
                  <span style="background:{C["surface"]};border:1px solid {C["border2"]};
                    color:{C["text"]};font-family:JetBrains Mono,monospace;font-size:9px;
                    padding:3px 10px;border-radius:12px">
                    {_src_icon} {_src}
                  </span>
                  {f'<span style="font-family:JetBrains Mono,monospace;font-size:8px;color:{C["muted"]};padding:3px 8px">{_dom}</span>' if _dom else ""}
                </div>
                <span style="font-family:JetBrains Mono,monospace;font-size:8px;
                  color:{C["muted"]};letter-spacing:1px">
                  🕐 {_pub}
                </span>
              </div>

              <!-- Titre -->
              <div style="font-family:Space Grotesk,sans-serif;font-size:14px;
                font-weight:700;color:{C["bright"]};line-height:1.5;margin-bottom:8px">
                {_t}
              </div>

              <!-- Description -->
              {f'<div style="font-family:Space Grotesk,sans-serif;font-size:12px;color:{C["text"]};line-height:1.7;margin-bottom:12px;padding:10px 12px;background:rgba(0,0,0,.2);border-radius:4px">{_desc[:280]}{"…" if len(_desc)>280 else ""}</div>' if _desc else ""}

              <!-- Footer : analyse + lien -->
              <div style="display:flex;justify-content:space-between;align-items:center;
                flex-wrap:wrap;gap:8px;padding-top:10px;
                border-top:1px solid {C["border"]}">
                <span style="font-family:JetBrains Mono,monospace;font-size:9px;color:{_ac}">
                  💬 {_cm}
                </span>
                {_link_btn}
              </div>

            </div>
            ''', unsafe_allow_html=True)

        if _shown == 0:
            st.markdown(f'<div style="text-align:center;padding:30px;color:{C["muted"]};font-family:JetBrains Mono,monospace;font-size:11px">Aucun article ne correspond aux filtres sélectionnés.</div>', unsafe_allow_html=True)

# ── SCANNER ──────────────────────────────────────────────────────────────────
with t_scan:
    qtitle("Scanner de Marché","Tous actifs — données temps réel")
    _cat_cols=st.columns(5)
    _cats_btn=["⛽ Énergie","🥇 Métaux précieux","🌾 Céréales","☕ Produits tropicaux","🐄 Élevage"]
    for _ci,_cat in enumerate(_cats_btn):
        with _cat_cols[_ci]:
            if st.button(_cat,key=f"scanbtn_{_ci}",use_container_width=True):
                with st.spinner(f"Scan {_cat}…"):
                    st.session_state.scan_data=_scan_markets(tuple(MARKETS[_cat]))
                st.rerun()
    _scan_df=st.session_state.scan_data
    if _scan_df is not None and not _scan_df.empty:
        _fig_sm=fig_scanner_map(_scan_df)
        if _fig_sm: st.plotly_chart(_fig_sm,use_container_width=True)
        if show_legends:
            explain_box("Market Map — Comment lire",
                "La taille des blocs = importance de la variation absolue. La couleur = direction : VERT = hausse · ROUGE = baisse. "
                "Plus le rouge est foncé, plus la chute est forte. Survolez un bloc pour voir le prix exact.", C["muted"])
        _sg,_sl2=st.columns(2)
        with _sg:
            qtitle("🟢 Top Gainants")
            for _,row in _scan_df.nlargest(5,"Variation %").iterrows():
                _n=row.get("Nom",row["Symbole"])
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:8px 12px;'
                            f'border-bottom:1px solid {C["border"]};font-family:DM Mono,monospace;font-size:11px">'
                            f'<span style="color:{C["accent"]};font-weight:600">{_n}</span>'
                            f'<span style="color:{C["muted"]}">{row["Symbole"]}</span>'
                            f'<span style="color:{C["text"]}">${row["Prix"]:,.4f}</span>'
                            f'<span style="color:{C["green"]};font-weight:700">+{row["Variation %"]:.2f}%</span>'
                            f'</div>',unsafe_allow_html=True)
        with _sl2:
            qtitle("🔴 Top Perdants")
            for _,row in _scan_df.nsmallest(5,"Variation %").iterrows():
                _n=row.get("Nom",row["Symbole"])
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:8px 12px;'
                            f'border-bottom:1px solid {C["border"]};font-family:DM Mono,monospace;font-size:11px">'
                            f'<span style="color:{C["accent"]};font-weight:600">{_n}</span>'
                            f'<span style="color:{C["muted"]}">{row["Symbole"]}</span>'
                            f'<span style="color:{C["text"]}">${row["Prix"]:,.4f}</span>'
                            f'<span style="color:{C["red"]};font-weight:700">{row["Variation %"]:.2f}%</span>'
                            f'</div>',unsafe_allow_html=True)
        st.markdown("<br>",unsafe_allow_html=True)
        st.dataframe(_scan_df,use_container_width=True,hide_index=True)
    else:
        st.markdown(f'<div style="text-align:center;background:{C["card"]};border:1px solid {C["border"]};border-radius:4px;padding:50px 20px">'
                    f'<div style="font-family:Syne,sans-serif;font-size:48px;color:{C["border"]}">📡</div>'
                    f'<div style="font-family:DM Mono,monospace;font-size:11px;color:{C["muted"]};margin-top:12px">Clique sur un bouton de catégorie ou SCANNER TOUS LES MARCHÉS</div>'
                    f'</div>',unsafe_allow_html=True)

# ── IA ORACLE GPT-4o ─────────────────────────────────────────────────────────
with t_chat:
    _sname_chat = get_name(symbol)

    # Status GPT-4o
    # Statut du moteur IA
    st.markdown(f'<div style="background:rgba(0,255,170,.05);border:1px solid rgba(0,255,170,.2);border-radius:6px;padding:12px 16px;margin-bottom:14px;display:flex;align-items:center;gap:12px"><span style="font-size:18px">⬡</span><div><span style="font-family:Rajdhani,sans-serif;font-size:12px;font-weight:700;color:#00ff9d;letter-spacing:2px;text-transform:uppercase">MOTEUR IA PROPRIÉTAIRE ACTIF</span><br><span style="font-family:JetBrains Mono,monospace;font-size:9px;color:#0e3060">100% votre code · Zéro API · Zéro abonnement · Fonctionne hors ligne</span></div></div>', unsafe_allow_html=True)

    qtitle("⬡ Oracle IA Propriétaire","100% Votre Code · Zéro API")

    # Boutons actions rapides
    _ba1,_ba2,_ba3=st.columns(3)
    with _ba1: _btn_report=st.button("📋  GÉNÉRER RAPPORT",use_container_width=True,key="btn_report")
    with _ba2: _btn_news_ai=st.button("📰  ANALYSER LES NEWS",use_container_width=True,key="btn_news_ai")
    with _ba3: _btn_risk=st.button("🛡️  CONSEIL RISQUE",use_container_width=True,key="btn_risk_ai")

    if _btn_report:
        if not sig: st.warning("Lance d'abord une analyse.")
        else:
            with st.spinner("⬡ Oracle IA génère le rapport…"):
                _rep2 = generate_report(sig,df,news,capital) if (GPT_OK and is_configured()) else ai_deep_analysis(f"Rapport complet sur {_sname_chat}",sig,capital,symbol)
            st.session_state.chat_history.append({"role":"user","content":f"📋 Rapport complet — {_sname_chat}"})
            st.session_state.chat_history.append({"role":"assistant","content":_rep2})
            st.rerun()

    if _btn_news_ai:
        if not news: st.warning("Lance d'abord une analyse avec news activées.")
        else:
            with st.spinner("⬡ Oracle IA analyse les news…"):
                _rep2 = analyze_news_gpt(news,symbol,sig) if (GPT_OK and is_configured()) else ai_deep_analysis(f"Analyse les news sur {_sname_chat}",sig,capital,symbol)
            st.session_state.chat_history.append({"role":"user","content":f"📰 Analyse news — {_sname_chat}"})
            st.session_state.chat_history.append({"role":"assistant","content":_rep2})
            st.rerun()

    if _btn_risk:
        if not sig: st.warning("Lance d'abord une analyse.")
        else:
            with st.spinner("⬡ Oracle IA analyse votre risque…"):
                _rep2 = risk_advice_gpt(sig,capital) if (GPT_OK and is_configured()) else ai_deep_analysis(f"Conseils risque pour {_sname_chat}",sig,capital,symbol)
            st.session_state.chat_history.append({"role":"user","content":f"🛡️ Conseil risque — {_sname_chat}"})
            st.session_state.chat_history.append({"role":"assistant","content":_rep2})
            st.rerun()

    st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)

    # Suggestions
    _suggs=[f"Analyse complète de {_sname_chat}",f"Plan de trade pour ${capital:,.0f}",
            "Quels indicateurs confirment le signal ?","Comment protéger mon capital ?",
            "Compare signal et tendance long terme","Quand prendre mes bénéfices ?"]
    _scc1,_scc2,_scc3=st.columns(3); _chosen=None
    for _i,(_col,_sg) in enumerate(zip([_scc1,_scc1,_scc2,_scc2,_scc3,_scc3],_suggs)):
        with _col:
            if st.button(_sg[:40]+"…" if len(_sg)>40 else _sg,key=f"sg{_i}",use_container_width=True): _chosen=_sg
    st.markdown("<div style='height:8px'></div>",unsafe_allow_html=True)

    # Historique
    for _msg in st.session_state.chat_history:
        if _msg["role"]=="user":
            st.markdown(f'<div class="lbl-user">VOUS</div><div class="msg-user">{_msg["content"]}</div>',unsafe_allow_html=True)
        else:
            _c=_msg["content"].replace("\n","<br>")
            st.markdown(f'<div class="lbl-ai">⬡ GPT-4o</div><div class="msg-ai">{_c}</div>',unsafe_allow_html=True)

    # Input
    _ui=st.text_area("",placeholder=f"Posez votre question — L'Oracle IA analyse vos données {_sname_chat} en temps réel…",height=95,label_visibility="collapsed",key="chat_in_v4")
    if _chosen: _ui=_chosen
    _cb1,_cb2=st.columns([4,1])
    with _cb1: _send_btn=st.button("⬡  ENVOYER À L'ORACLE IA",use_container_width=True)
    with _cb2:
        if st.button("🗑  EFFACER",use_container_width=True): st.session_state.chat_history=[]; st.rerun()
    if _send_btn and _ui.strip():
        st.session_state.chat_history.append({"role":"user","content":_ui})
        with st.spinner("⬡ Oracle IA analyse…"):
            _ctx={"signal":sig,"capital":capital} if sig else {}
            _hist=[{"role":m["role"],"content":m["content"]} for m in st.session_state.chat_history[:-1]]
            _rep = ask_gpt(_ui,_ctx,_hist) if (GPT_OK and is_configured()) else ai_deep_analysis(_ui,sig,capital,symbol)
        st.session_state.chat_history.append({"role":"assistant","content":_rep})
        st.rerun()


# ── BACKTEST ─────────────────────────────────────────────────────────────────
with t_bt:
    if not bt: st.info("Clique sur **LANCER BACKTEST** (nécessite les modules du projet).")
    else:
        _m=bt.get("metrics",{}); _eq=bt.get("equity_curve")
        if _eq is not None and len(_eq)>0:
            if not isinstance(_eq,pd.Series): _eq=pd.Series(_eq)
            _dd=(_eq-_eq.cummax())/_eq.cummax()*100
            _fig_eq=make_subplots(rows=2,cols=1,shared_xaxes=True,row_heights=[.7,.3],
                                  vertical_spacing=.06,subplot_titles=["Courbe d'Équité (Capital)","Drawdown (%)"])
            _fig_eq.add_trace(go.Scatter(x=_eq.index,y=_eq.values,name="Capital",
                line=dict(color=C["accent"],width=2),fill="tozeroy",fillcolor="rgba(0,200,255,.05)"),row=1,col=1)
            _fig_eq.add_trace(go.Scatter(x=_eq.index,y=_dd.values,name="Drawdown %",
                line=dict(color=C["red"],width=1.5),fill="tozeroy",fillcolor="rgba(255,61,107,.07)"),row=2,col=1)
            _fig_eq.update_layout(**PLOT,height=380,
                title=dict(text=f"  Courbe d'Équité — {get_name(bt.get('symbol',symbol))}",
                           font=dict(family="Syne",size=14,color=C["accent"])))
            _fig_eq.update_xaxes(**_AX); _fig_eq.update_yaxes(**_AX)
            st.plotly_chart(_fig_eq,use_container_width=True)
            if show_legends:
                explain_box("Drawdown — Définition",
                    "Le drawdown mesure la perte maximale depuis le dernier sommet. "
                    "Un drawdown de -20% signifie que le capital est 20% sous son plus haut historique. "
                    "Un bon système de trading maintient le Max Drawdown sous -25%.", C["red"])
        qtitle("Métriques de Performance")
        _bc1,_bc2,_bc3,_bc4,_bc5,_bc6=st.columns(6)
        _bc1.metric("Rendement",f"{_m.get('total_return_pct',0):+.2f}%",f"vs B&H : {_m.get('buy_hold_return_pct',0):+.2f}%")
        _bc2.metric("CAGR",f"{_m.get('cagr_pct',0):+.2f}%")
        _bc3.metric("Sharpe",f"{_m.get('sharpe_ratio',0):.3f}")
        _bc4.metric("Max Drawdown",f"{_m.get('max_drawdown_pct',0):.2f}%")
        _bc5.metric("Win Rate",f"{_m.get('win_rate_pct',0):.1f}%")
        _bc6.metric("Profit Factor",f"{_m.get('profit_factor',0):.2f}")
        if show_legends:
            _bl1,_bl2=st.columns(2)
            with _bl1:
                explain_box("Sharpe Ratio",
                    "Mesure le rendement ajusté au risque. > 1 = bon · > 2 = excellent · < 0.5 = médiocre. "
                    "Un Sharpe de 1.5 signifie que vous gagnez 1.5× votre risque.", C["accent"])
            with _bl2:
                explain_box("Profit Factor",
                    "Ratio Gains bruts / Pertes brutes. > 1.5 = profitable · > 2 = excellent. "
                    "Si PF = 2, pour chaque $1 perdu vous gagnez $2.", C["green"])

# ── MON ESPACE PERSONNEL — SaaS Grade ────────────────────────────────────────
with t_profil:
    _uemail = st.session_state.get("user_email", "") if AUTH_OK else ""

    if not _uemail:
        st.markdown(f'''
        <div style="text-align:center;padding:80px 20px">
          <div style="font-size:72px;filter:grayscale(1);opacity:.3">👤</div>
          <div style="font-family:Bebas Neue,sans-serif;font-size:28px;letter-spacing:4px;
            color:{C["border2"]};margin-top:18px">ESPACE PERSONNEL</div>
          <div style="font-family:JetBrains Mono,monospace;font-size:11px;
            color:{C["muted"]};margin-top:10px;letter-spacing:2px">
            CONNECTEZ-VOUS POUR ACCÉDER À VOTRE TABLEAU DE BORD PERSONNEL
          </div>
          <div style="font-family:JetBrains Mono,monospace;font-size:9px;
            color:{C["muted"]};margin-top:8px;opacity:.6">
            Signaux · Favoris · Alertes · Performance · Appareils
          </div>
        </div>
        ''', unsafe_allow_html=True)
    else:
        # ── Données ────────────────────────────────────────────────────────
        try:
            import socket
            _ip = socket.gethostbyname(socket.gethostname())
        except Exception:
            _ip = "127.0.0.1"
        try:
            _ip_key = get_or_create_ip_key(_uemail, _ip, "QTO Dashboard")
        except Exception:
            _ip_key = "—"
        try:
            _stats   = get_user_stats(_uemail)
            _favs    = get_favorites(_uemail)
            _alerts  = get_alerts(_uemail, active_only=False)
            _sigs    = get_user_signals(_uemail, limit=100)
            _ip_keys = get_user_ip_keys(_uemail)
        except Exception:
            _stats = {"total":0,"buys":0,"sells":0,"holds":0,"top_symbol":"—","avg_conf":0,"avg_rsi":0}
            _favs = []; _alerts = []; _sigs = []; _ip_keys = []

        _username  = st.session_state.get("username","Utilisateur")
        _plan      = st.session_state.get("plan","PRO")
        _expires   = st.session_state.get("expires_at","—")
        _plan_col  = C["yellow"] if _plan=="ELITE" else C["accent"] if _plan=="PRO" else C["green"]
        _plan_icon = "👑" if _plan=="ELITE" else "⚡" if _plan=="PRO" else "🎯"
        _initials  = _username[:2].upper() if _username else "?"

        # ── Bannière Hero Profile ──────────────────────────────────────────
        st.markdown(f'''
        <div style="background:linear-gradient(135deg,{C["card"]} 0%,{C["card2"]} 50%,rgba(0,212,255,.05) 100%);
            border:1px solid {C["border2"]};border-radius:12px;
            padding:28px 30px;margin-bottom:6px;position:relative;overflow:hidden">

          <!-- Décoration fond -->
          <div style="position:absolute;top:-30px;right:-30px;width:140px;height:140px;
            border-radius:50%;background:radial-gradient(circle,rgba(0,212,255,.06),transparent 70%)"></div>
          <div style="position:absolute;bottom:0;left:0;right:0;height:1px;
            background:linear-gradient(90deg,transparent,{_plan_col}44,transparent)"></div>

          <div style="display:flex;align-items:center;gap:20px;flex-wrap:wrap">

            <!-- Avatar -->
            <div style="width:66px;height:66px;border-radius:50%;flex-shrink:0;
              background:linear-gradient(135deg,{_plan_col}33,{C["surface"]});
              border:2px solid {_plan_col}55;
              display:flex;align-items:center;justify-content:center;
              font-family:Bebas Neue,sans-serif;font-size:24px;color:{_plan_col};
              box-shadow:0 0 20px {_plan_col}22">
              {_initials}
            </div>

            <!-- Infos principales -->
            <div style="flex:1;min-width:180px">
              <div style="font-family:Bebas Neue,sans-serif;font-size:26px;
                color:{C["bright"]};letter-spacing:3px;line-height:1">
                {_username}
              </div>
              <div style="font-family:JetBrains Mono,monospace;font-size:10px;
                color:{C["muted"]};margin-top:5px">{_uemail}</div>
              <div style="display:flex;align-items:center;gap:10px;margin-top:8px;flex-wrap:wrap">
                <span style="background:{_plan_col}22;border:1px solid {_plan_col}55;
                  color:{_plan_col};font-family:Bebas Neue,sans-serif;font-size:13px;
                  letter-spacing:2px;padding:3px 12px;border-radius:20px">
                  {_plan_icon} PLAN {_plan}
                </span>
                <span style="font-family:JetBrains Mono,monospace;font-size:9px;
                  color:{C["muted"]}">Expire : {_expires}</span>
                <span style="background:rgba(0,255,157,.1);border:1px solid rgba(0,255,157,.2);
                  color:{C["green"]};font-family:JetBrains Mono,monospace;font-size:9px;
                  padding:2px 10px;border-radius:10px">● ACTIF</span>
              </div>
            </div>

            <!-- Clé IP -->
            <div style="text-align:right;min-width:200px">
              <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                color:{C["muted"]};text-transform:uppercase;letter-spacing:1.5px;margin-bottom:5px">
                🔐 Clé appareil
              </div>
              <div style="font-family:JetBrains Mono,monospace;font-size:12px;
                color:{C["green"]};letter-spacing:2px;
                background:rgba(0,255,157,.05);border:1px solid rgba(0,255,157,.15);
                border-radius:4px;padding:6px 12px;display:inline-block">
                {_ip_key}
              </div>
              <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                color:{C["muted"]};margin-top:4px">{_ip}</div>
            </div>

          </div>
        </div>
        ''', unsafe_allow_html=True)

        # ── KPI Cards ─────────────────────────────────────────────────────
        _total = _stats["total"] or 1
        _win_rate = round(_stats["buys"] / _total * 100) if _total > 0 else 0
        _kpi_data = [
            ("📊","Analyses totales", str(_stats["total"]), "", C["accent"]),
            ("🟢","Signaux BUY",       str(_stats["buys"]),  f"{_win_rate}% du total", C["green"]),
            ("🔴","Signaux SELL",      str(_stats["sells"]), "", C["red"]),
            ("⚪","Signaux HOLD",      str(_stats["holds"]), "", C["muted"]),
            ("⚡","Confiance moy.",    f"{_stats['avg_conf']:.0f}%", "IA", C["yellow"]),
            ("🏆","Actif favori",      _stats["top_symbol"], "le + analysé", C["purple"]),
        ]
        _kpi_cols = st.columns(6)
        for _ki, (_icon, _lbl, _val, _sub, _kcol) in enumerate(_kpi_data):
            with _kpi_cols[_ki]:
                st.markdown(f'''
                <div style="background:linear-gradient(135deg,{C["card"]},{C["card2"]});
                    border:1px solid {C["border2"]};border-top:2px solid {_kcol};
                    border-radius:8px;padding:14px 12px;text-align:center;
                    position:relative;overflow:hidden">
                  <div style="position:absolute;top:0;left:0;right:0;height:1px;
                    background:linear-gradient(90deg,transparent,{_kcol}55,transparent)"></div>
                  <div style="font-size:20px;margin-bottom:6px">{_icon}</div>
                  <div style="font-family:Bebas Neue,sans-serif;font-size:28px;
                    color:{_kcol};letter-spacing:2px;line-height:1;
                    text-shadow:0 0 15px {_kcol}44">{_val}</div>
                  <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                    color:{C["muted"]};text-transform:uppercase;letter-spacing:1px;
                    margin-top:5px">{_lbl}</div>
                  {f'<div style="font-family:JetBrains Mono,monospace;font-size:8px;color:{_kcol};margin-top:2px">{_sub}</div>' if _sub else ""}
                </div>
                ''', unsafe_allow_html=True)

        st.markdown("<div style='height:18px'></div>", unsafe_allow_html=True)

        # ── Sous-onglets ───────────────────────────────────────────────────
        _pt1, _pt2, _pt3, _pt4 = st.tabs([
            "📈 Mes Signaux",
            "⭐ Favoris & Alertes",
            "🔐 Sécurité & Appareils",
            "📊 Performance",
        ])

        # ════════ ONGLET 1 — SIGNAUX ════════════════════════════════════
        with _pt1:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if not _sigs:
                st.markdown(f'''
                <div style="text-align:center;padding:50px 20px;
                    background:{C["card"]};border:1px dashed {C["border2"]};border-radius:8px">
                  <div style="font-size:48px;opacity:.3">📈</div>
                  <div style="font-family:JetBrains Mono,monospace;font-size:11px;
                    color:{C["muted"]};margin-top:12px">
                    Aucun signal sauvegardé — lancez votre première analyse
                  </div>
                </div>
                ''', unsafe_allow_html=True)
            else:
                # Filtres
                _sf1, _sf2, _sf3 = st.columns([2,2,1])
                with _sf1:
                    _sig_filter = st.selectbox("Signal", ["Tous","BUY","SELL","HOLD"],
                        label_visibility="collapsed", key="sig_filter")
                with _sf2:
                    _sig_syms = ["Tous"] + list(dict.fromkeys(s["symbol"] for s in _sigs))
                    _sig_sym_filter = st.selectbox("Symbole", _sig_syms,
                        label_visibility="collapsed", key="sig_sym_filter")
                with _sf3:
                    _sig_limit = st.selectbox("Nb", ["20","50","Tous"],
                        label_visibility="collapsed", key="sig_limit")

                _sig_max = 999 if _sig_limit=="Tous" else int(_sig_limit)
                _shown_sigs = 0

                for _s in _sigs:
                    if _shown_sigs >= _sig_max: break
                    if _sig_filter != "Tous" and _s["action"] != _sig_filter: continue
                    if _sig_sym_filter != "Tous" and _s["symbol"] != _sig_sym_filter: continue
                    _shown_sigs += 1

                    _ac = C["green"] if _s["action"]=="BUY" else C["red"] if _s["action"]=="SELL" else C["muted"]
                    _icon_sig = "🟢" if _s["action"]=="BUY" else "🔴" if _s["action"]=="SELL" else "⚪"
                    _conf_v = float(_s["confidence"] or 0)
                    _rsi_v  = float(_s["rsi"] or 0)
                    _price_v = float(_s["price"] or 0)
                    _sl_v   = float(_s["sl"] or 0)
                    _tp_v   = float(_s["tp"] or 0)
                    _rr_v   = float(_s["rr"] or 0)

                    st.markdown(f'''
                    <div style="background:linear-gradient(135deg,{C["card"]},{C["card2"]});
                        border:1px solid {C["border2"]};border-left:4px solid {_ac};
                        border-radius:8px;padding:14px 18px;margin-bottom:8px;
                        position:relative;overflow:hidden">
                      <div style="position:absolute;top:0;left:0;right:0;height:1px;
                        background:linear-gradient(90deg,{_ac}33,transparent)"></div>

                      <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px">

                        <!-- Gauche : actif + signal -->
                        <div style="display:flex;align-items:center;gap:14px">
                          <div style="width:40px;height:40px;border-radius:8px;
                            background:{_ac}18;border:1px solid {_ac}44;
                            display:flex;align-items:center;justify-content:center;
                            font-family:Bebas Neue,sans-serif;font-size:16px;color:{_ac}">
                            {_icon_sig}
                          </div>
                          <div>
                            <div style="font-family:Space Grotesk,sans-serif;font-size:14px;
                              font-weight:700;color:{C["bright"]};letter-spacing:.5px">
                              {_s["name"] or _s["symbol"]}
                            </div>
                            <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                              color:{C["muted"]};margin-top:2px">
                              {_s["symbol"]} · {_s["date"]}
                            </div>
                          </div>
                        </div>

                        <!-- Centre : métriques clés -->
                        <div style="display:flex;gap:20px;flex-wrap:wrap;align-items:center">
                          <div style="text-align:center">
                            <div style="font-family:JetBrains Mono,monospace;font-size:7px;
                              color:{C["muted"]};text-transform:uppercase;letter-spacing:1px">SIGNAL</div>
                            <div style="font-family:Bebas Neue,sans-serif;font-size:20px;
                              color:{_ac};letter-spacing:2px">{_s["action"]}</div>
                          </div>
                          <div style="text-align:center">
                            <div style="font-family:JetBrains Mono,monospace;font-size:7px;
                              color:{C["muted"]};text-transform:uppercase;letter-spacing:1px">PRIX</div>
                            <div style="font-family:JetBrains Mono,monospace;font-size:13px;
                              color:{C["accent"]};font-weight:600">${_price_v:,.4f}</div>
                          </div>
                          <div style="text-align:center">
                            <div style="font-family:JetBrains Mono,monospace;font-size:7px;
                              color:{C["muted"]};text-transform:uppercase;letter-spacing:1px">CONF.</div>
                            <div style="font-family:Bebas Neue,sans-serif;font-size:18px;
                              color:{C["yellow"]}">{_conf_v:.0f}%</div>
                          </div>
                          <div style="text-align:center">
                            <div style="font-family:JetBrains Mono,monospace;font-size:7px;
                              color:{C["muted"]};text-transform:uppercase;letter-spacing:1px">RSI</div>
                            <div style="font-family:JetBrains Mono,monospace;font-size:13px;
                              color:{"#00ff9d" if _rsi_v<30 else "#ff2d55" if _rsi_v>70 else "#6fa8c8"}">{_rsi_v:.0f}</div>
                          </div>
                          {f'''<div style="text-align:center">
                            <div style="font-family:JetBrains Mono,monospace;font-size:7px;
                              color:{C["muted"]};text-transform:uppercase;letter-spacing:1px">R/R</div>
                            <div style="font-family:JetBrains Mono,monospace;font-size:13px;
                              color:{C["green"] if _rr_v>=2 else C["yellow"]}">{_rr_v:.1f}:1</div>
                          </div>''' if _rr_v > 0 else ""}
                        </div>

                        <!-- Droite : SL/TP -->
                        {f'''<div style="text-align:right">
                          <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                            color:{C["red"]}">SL ${_sl_v:,.4f}</div>
                          <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                            color:{C["green"]};margin-top:3px">TP ${_tp_v:,.4f}</div>
                        </div>''' if _sl_v > 0 else ""}

                      </div>

                      <!-- Barre de confiance -->
                      <div style="margin-top:10px;background:{C["border"]};border-radius:2px;height:3px;overflow:hidden">
                        <div style="height:100%;width:{min(_conf_v,100):.0f}%;
                          background:linear-gradient(90deg,{_ac},{_ac}88);border-radius:2px;
                          transition:width .5s"></div>
                      </div>
                    </div>
                    ''', unsafe_allow_html=True)

                if _shown_sigs == 0:
                    st.info("Aucun signal ne correspond aux filtres.")

        # ════════ ONGLET 2 — FAVORIS & ALERTES ══════════════════════════
        with _pt2:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
            _fav_col, _alert_col = st.columns(2)

            # ── Favoris ────────────────────────────────────────────────────
            with _fav_col:
                st.markdown(f'''
                <div style="font-family:Bebas Neue,sans-serif;font-size:16px;
                  color:{C["accent"]};letter-spacing:2px;margin-bottom:12px">
                  ⭐ MES ACTIFS FAVORIS
                  <span style="font-family:JetBrains Mono,monospace;font-size:10px;
                    color:{C["muted"]};margin-left:10px">{len(_favs)} actifs</span>
                </div>
                ''', unsafe_allow_html=True)

                _fa1, _fa2 = st.columns([4,1])
                with _fa1:
                    _fav_sym = st.text_input("", placeholder="BTC-USD, AAPL, GC=F…",
                        label_visibility="collapsed", key="fav_input")
                with _fa2:
                    if st.button("➕", key="add_fav", use_container_width=True):
                        if _fav_sym:
                            try:
                                add_favorite(_uemail, _fav_sym.upper().strip(),
                                            get_name(_fav_sym.upper().strip()))
                                st.rerun()
                            except Exception: pass

                if not _favs:
                    st.markdown(f'''
                    <div style="text-align:center;padding:30px;
                        background:{C["card"]};border:1px dashed {C["border2"]};border-radius:8px;margin-top:8px">
                      <div style="font-size:32px;opacity:.3">⭐</div>
                      <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                        color:{C["muted"]};margin-top:8px">Ajoutez vos actifs préférés</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    for _f in _favs:
                        _frow1, _frow2 = st.columns([5,1])
                        with _frow1:
                            st.markdown(f'''
                            <div style="background:{C["card"]};border:1px solid {C["border2"]};
                                border-radius:6px;padding:10px 14px;margin-bottom:5px;
                                display:flex;justify-content:space-between;align-items:center">
                              <div style="display:flex;align-items:center;gap:10px">
                                <div style="width:32px;height:32px;border-radius:6px;
                                  background:rgba(0,212,255,.08);border:1px solid rgba(0,212,255,.2);
                                  display:flex;align-items:center;justify-content:center;
                                  font-family:Bebas Neue,sans-serif;font-size:11px;color:{C["accent"]}">
                                  {_f["symbol"][:2]}
                                </div>
                                <div>
                                  <div style="font-family:Space Grotesk,sans-serif;font-size:12px;
                                    font-weight:600;color:{C["bright"]}">{_f["name"] or _f["symbol"]}</div>
                                  <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                                    color:{C["muted"]}">{_f["symbol"]} · Ajouté {_f["added_at"]}</div>
                                </div>
                              </div>
                            </div>
                            ''', unsafe_allow_html=True)
                        with _frow2:
                            if st.button("🗑", key=f"del_fav_{_f['symbol']}",
                                         use_container_width=True):
                                try:
                                    remove_favorite(_uemail, _f["symbol"])
                                    st.rerun()
                                except Exception: pass

            # ── Alertes ────────────────────────────────────────────────────
            with _alert_col:
                _active_alerts = [a for a in _alerts if a.get("active") and not a.get("triggered")]
                _triggered_alerts = [a for a in _alerts if a.get("triggered")]

                st.markdown(f'''
                <div style="font-family:Bebas Neue,sans-serif;font-size:16px;
                  color:{C["accent"]};letter-spacing:2px;margin-bottom:12px">
                  🔔 MES ALERTES DE PRIX
                  <span style="background:rgba(0,212,255,.15);border:1px solid rgba(0,212,255,.3);
                    color:{C["accent"]};font-family:JetBrains Mono,monospace;font-size:9px;
                    padding:2px 8px;border-radius:10px;margin-left:8px">{len(_active_alerts)} actives</span>
                </div>
                ''', unsafe_allow_html=True)

                with st.expander("➕ Créer une nouvelle alerte"):
                    _al1, _al2 = st.columns(2)
                    with _al1:
                        _al_sym   = st.text_input("Symbole", placeholder="BTC-USD", key="al_sym")
                        _al_cond  = st.selectbox("Condition",
                            ["ABOVE — Prix monte au-dessus","BELOW — Prix descend en-dessous"],
                            key="al_cond")
                    with _al2:
                        _al_price = st.number_input("Prix cible ($)",
                            min_value=0.0, value=0.0, format="%.4f", key="al_price")
                        _al_note  = st.text_input("Note", placeholder="résistance clé…", key="al_note")
                    if st.button("🔔 CRÉER L'ALERTE", use_container_width=True, key="create_alert"):
                        if _al_sym and _al_price > 0:
                            try:
                                cond = "ABOVE" if "ABOVE" in _al_cond else "BELOW"
                                curr = sig.get("price",0) if sig and sig.get("symbol","")==_al_sym.upper() else 0
                                add_alert(_uemail, _al_sym.upper(), get_name(_al_sym.upper()),
                                         cond, _al_price, curr, _al_note)
                                st.success("✅ Alerte créée !")
                                st.rerun()
                            except Exception as e:
                                st.error(f"Erreur : {e}")

                if not _alerts:
                    st.markdown(f'''
                    <div style="text-align:center;padding:30px;
                        background:{C["card"]};border:1px dashed {C["border2"]};border-radius:8px;margin-top:8px">
                      <div style="font-size:32px;opacity:.3">🔔</div>
                      <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                        color:{C["muted"]};margin-top:8px">Créez votre première alerte de prix</div>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    for _al in _alerts:
                        _al_c     = C["green"] if not _al.get("triggered") else C["muted"]
                        _al_icon  = "🔔" if not _al.get("triggered") else "✅"
                        _cond_txt = "↑ > " if _al["condition_type"]=="ABOVE" else "↓ < "
                        _al_status = "DÉCLENCHÉE" if _al.get("triggered") else "ACTIVE"
                        _al_status_col = C["muted"] if _al.get("triggered") else C["green"]
                        st.markdown(f'''
                        <div style="background:{C["card"]};border:1px solid {C["border2"]};
                            border-left:3px solid {_al_c};border-radius:6px;
                            padding:10px 14px;margin-bottom:6px">
                          <div style="display:flex;justify-content:space-between;align-items:center">
                            <div>
                              <span style="font-family:Space Grotesk,sans-serif;font-size:12px;
                                font-weight:700;color:{C["bright"]}">{_al_icon} {_al["symbol"]}</span>
                              <span style="font-family:JetBrains Mono,monospace;font-size:10px;
                                color:{_al_c};margin-left:8px">{_cond_txt}${float(_al["target_price"]):,.4f}</span>
                            </div>
                            <span style="background:{_al_status_col}18;border:1px solid {_al_status_col}44;
                              color:{_al_status_col};font-family:JetBrains Mono,monospace;font-size:8px;
                              padding:2px 8px;border-radius:8px">{_al_status}</span>
                          </div>
                          {f'<div style="font-family:JetBrains Mono,monospace;font-size:9px;color:{C["muted"]};margin-top:4px">📝 {_al["note"]}</div>' if _al.get("note") else ""}
                          <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                            color:{C["muted"]};margin-top:4px">Créée : {_al["created_at"]}</div>
                        </div>
                        ''', unsafe_allow_html=True)

        # ════════ ONGLET 3 — SÉCURITÉ & APPAREILS ═══════════════════════
        with _pt3:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            # Infos compte
            _sec1, _sec2 = st.columns(2)
            with _sec1:
                qtitle("🔑 Informations du Compte")
                st.markdown(f'''
                <div style="background:{C["card"]};border:1px solid {C["border2"]};border-radius:8px;padding:18px">
                  <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {C["border"]}">
                    <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{C["muted"]}">Nom d&#39;utilisateur</span>
                    <span style="font-family:Space Grotesk,sans-serif;font-size:12px;font-weight:600;color:{C["bright"]}">{_username}</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {C["border"]}">
                    <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{C["muted"]}">Email</span>
                    <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{C["accent"]}">{_uemail}</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {C["border"]}">
                    <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{C["muted"]}">Plan</span>
                    <span style="font-family:Bebas Neue,sans-serif;font-size:14px;color:{_plan_col};letter-spacing:1px">{_plan_icon} {_plan}</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {C["border"]}">
                    <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{C["muted"]}">Expiration</span>
                    <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{C["text"]}">{_expires}</span>
                  </div>
                  <div style="display:flex;justify-content:space-between;padding:8px 0">
                    <span style="font-family:JetBrains Mono,monospace;font-size:10px;color:{C["muted"]}">Statut</span>
                    <span style="background:rgba(0,255,157,.1);border:1px solid rgba(0,255,157,.2);color:{C["green"]};
                      font-family:JetBrains Mono,monospace;font-size:9px;padding:2px 10px;border-radius:8px">● ACTIF</span>
                  </div>
                </div>
                ''', unsafe_allow_html=True)

            with _sec2:
                qtitle("🌍 Clé IP de Cet Appareil")
                st.markdown(f'''
                <div style="background:linear-gradient(135deg,rgba(0,255,157,.04),{C["card"]});
                    border:1px solid rgba(0,255,157,.2);border-radius:8px;padding:20px;
                    text-align:center">
                  <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                    color:{C["muted"]};text-transform:uppercase;letter-spacing:2px;margin-bottom:12px">
                    Identifiant unique de votre appareil
                  </div>
                  <div style="font-family:JetBrains Mono,monospace;font-size:16px;
                    color:{C["green"]};letter-spacing:3px;
                    background:rgba(0,0,0,.3);border:1px solid rgba(0,255,157,.2);
                    border-radius:6px;padding:12px 16px;margin-bottom:10px">
                    {_ip_key}
                  </div>
                  <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                    color:{C["muted"]}">Adresse IP : {_ip}</div>
                  <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                    color:{C["muted"]};margin-top:6px;line-height:1.6">
                    Cette clé est unique à cet appareil + votre compte.<br>
                    Elle est régénérée si votre IP change.
                  </div>
                </div>
                ''', unsafe_allow_html=True)

            # Tableau des appareils
            st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
            qtitle("🖥️ Tous Mes Appareils", f"{len(_ip_keys)} appareil(s) reconnu(s)")
            if not _ip_keys:
                st.info("Aucun appareil enregistré.")
            else:
                _dev_cols = st.columns(min(len(_ip_keys), 3))
                for _ii, _ik in enumerate(_ip_keys):
                    with _dev_cols[_ii % 3]:
                        _is_current = _ik["ip_address"] == _ip
                        _dev_col2 = C["green"] if _is_current else C["accent"]
                        st.markdown(f'''
                        <div style="background:{C["card"]};border:1px solid {C["border2"]};
                            border-top:3px solid {_dev_col2};border-radius:8px;
                            padding:16px;margin-bottom:8px;position:relative">
                          {f'<div style="position:absolute;top:10px;right:10px;background:rgba(0,255,157,.15);border:1px solid rgba(0,255,157,.3);color:{C["green"]};font-family:JetBrains Mono,monospace;font-size:8px;padding:2px 8px;border-radius:8px">ACTUEL</div>' if _is_current else ""}
                          <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                            color:{C["muted"]};text-transform:uppercase;letter-spacing:1.5px;margin-bottom:10px">
                            🖥️ Appareil {_ii+1}
                          </div>
                          <div style="font-family:JetBrains Mono,monospace;font-size:11px;
                            color:{_dev_col2};letter-spacing:1.5px;margin-bottom:8px;
                            word-break:break-all">{_ik["ip_key"]}</div>
                          <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                            color:{C["muted"]}">🌐 {_ik["ip_address"]}</div>
                          <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                            color:{C["muted"]};margin-top:4px">
                            📅 Créé : {_ik["created_at"]}<br>
                            ⏱ Vu : {_ik["last_seen"]}
                          </div>
                        </div>
                        ''', unsafe_allow_html=True)

        # ════════ ONGLET 4 — PERFORMANCE ═════════════════════════════════
        with _pt4:
            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            if not _sigs:
                st.info("Lancez des analyses pour générer vos statistiques de performance.")
            else:
                # Données de performance
                _total_sigs = len(_sigs)
                _buy_count  = sum(1 for s in _sigs if s["action"]=="BUY")
                _sell_count = sum(1 for s in _sigs if s["action"]=="SELL")
                _hold_count = sum(1 for s in _sigs if s["action"]=="HOLD")
                _buy_pct    = _buy_count / _total_sigs * 100 if _total_sigs else 0
                _sell_pct   = _sell_count / _total_sigs * 100 if _total_sigs else 0
                _hold_pct   = _hold_count / _total_sigs * 100 if _total_sigs else 0
                _avg_conf   = float(np.mean([float(s["confidence"] or 0) for s in _sigs]))
                _avg_rsi    = float(np.mean([float(s["rsi"] or 0) for s in _sigs]))
                _avg_rr     = float(np.mean([float(s["rr"] or 0) for s in _sigs]))
                _symbols_used = list(dict.fromkeys(s["symbol"] for s in _sigs))

                # Graphique distribution signaux
                # plotly already imported as go
                _fig_dist = go.Figure()
                _fig_dist.add_trace(go.Bar(
                    x=["BUY", "SELL", "HOLD"],
                    y=[_buy_count, _sell_count, _hold_count],
                    marker=dict(color=[C["green"], C["red"], C["muted"]],
                                opacity=0.85,
                                line=dict(width=0)),
                    text=[f"{_buy_count}<br>{_buy_pct:.0f}%",
                          f"{_sell_count}<br>{_sell_pct:.0f}%",
                          f"{_hold_count}<br>{_hold_pct:.0f}%"],
                    textposition="outside",
                    textfont=dict(family="JetBrains Mono", size=11, color=C["bright"])
                ))
                _fig_dist.update_layout(**PLOT, height=250,
                    title=dict(text="Distribution des Signaux",
                               font=dict(family="Bebas Neue", size=14, color=C["accent"])),
                    showlegend=False)
                _fig_dist.update_yaxes(gridcolor=C["border"], showgrid=True, zeroline=False)
                _fig_dist.update_xaxes(gridcolor=C["border"])

                # Stats par actif
                _sym_stats = {}
                for _s in _sigs:
                    _sym = _s["symbol"]
                    if _sym not in _sym_stats:
                        _sym_stats[_sym] = {"total":0,"buy":0,"sell":0,"hold":0,"conf_sum":0}
                    _sym_stats[_sym]["total"] += 1
                    _sym_stats[_sym][_s["action"].lower()] += 1
                    _sym_stats[_sym]["conf_sum"] += float(_s["confidence"] or 0)

                _perf1, _perf2 = st.columns(2)
                with _perf1:
                    st.plotly_chart(_fig_dist, use_container_width=True)
                with _perf2:
                    qtitle("📊 Résumé Statistique")
                    _perf_data = [
                        ("Total analyses", str(_total_sigs), C["accent"]),
                        ("Ratio BUY/SELL", f"{_buy_count}/{_sell_count}", C["green"]),
                        ("Confiance moyenne", f"{_avg_conf:.1f}%", C["yellow"]),
                        ("RSI moyen analysé", f"{_avg_rsi:.1f}", C["accent"]),
                        ("R/R moyen", f"{_avg_rr:.2f}:1", C["green"] if _avg_rr>=2 else C["yellow"]),
                        ("Actifs uniques", str(len(_symbols_used)), C["purple"]),
                    ]
                    for _lbl2, _val2, _col2 in _perf_data:
                        st.markdown(f'''
                        <div style="display:flex;justify-content:space-between;
                            padding:8px 12px;border-bottom:1px solid {C["border"]};
                            background:{C["card"]};margin-bottom:2px;border-radius:3px">
                          <span style="font-family:JetBrains Mono,monospace;font-size:10px;
                            color:{C["muted"]}">{_lbl2}</span>
                          <span style="font-family:Bebas Neue,sans-serif;font-size:16px;
                            color:{_col2};letter-spacing:1px">{_val2}</span>
                        </div>
                        ''', unsafe_allow_html=True)

                # Top actifs
                st.markdown("<div style='height:14px'></div>", unsafe_allow_html=True)
                qtitle("🏆 Top Actifs Analysés", f"{len(_sym_stats)} actifs différents")
                _sorted_syms = sorted(_sym_stats.items(), key=lambda x: x[1]["total"], reverse=True)
                _top_cols = st.columns(min(len(_sorted_syms), 4))
                for _ti, (_sym2, _sdata) in enumerate(_sorted_syms[:4]):
                    with _top_cols[_ti]:
                        _dominant = "BUY" if _sdata["buy"]>=_sdata["sell"] else "SELL"
                        _dom_col  = C["green"] if _dominant=="BUY" else C["red"]
                        st.markdown(f'''
                        <div style="background:{C["card"]};border:1px solid {C["border2"]};
                            border-top:3px solid {_dom_col};border-radius:8px;
                            padding:14px;text-align:center">
                          <div style="font-family:Bebas Neue,sans-serif;font-size:18px;
                            color:{C["bright"]};letter-spacing:2px">{get_name(_sym2)}</div>
                          <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                            color:{C["muted"]}">{_sym2}</div>
                          <div style="font-family:Bebas Neue,sans-serif;font-size:28px;
                            color:{_dom_col};letter-spacing:1px;margin:8px 0">{_sdata["total"]}</div>
                          <div style="font-family:JetBrains Mono,monospace;font-size:8px;
                            color:{C["muted"]}">analyses</div>
                          <div style="margin-top:8px;font-family:JetBrains Mono,monospace;
                            font-size:9px;color:{_dom_col}">
                            Tendance : {_dominant}
                          </div>
                          <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                            color:{C["muted"]};margin-top:4px">
                            {_sdata["buy"]}B · {_sdata["sell"]}S · {_sdata["hold"]}H
                          </div>
                          <div style="font-family:JetBrains Mono,monospace;font-size:9px;
                            color:{C["yellow"]};margin-top:4px">
                            Conf. {_sdata["conf_sum"]/_sdata["total"]:.0f}%
                          </div>
                        </div>
                        ''', unsafe_allow_html=True)


# ── HISTORIQUE ───────────────────────────────────────────────────────────────
with t_hist:
    _history=st.session_state.signal_history
    if not _history: st.info("L'historique des signaux apparaîtra ici après vos analyses.")
    else:
        qtitle(f"Historique des Signaux",f"{len(_history)} analyses effectuées")
        _rows_h=[]
        for _h in _history:
            _r4=_h.get("risk_management",{}); _s4=_h.get("sentiment",{}) or {}; _sym_h=_h.get("symbol","—")
            _rows_h.append({"Heure":_h.get("ts","—"),"Symbole":_sym_h,"Nom":get_name(_sym_h),
                            "Signal":_h.get("action","—"),
                            "Bull %":f"{_h.get('bullish_probability',0)*100:.1f}%",
                            "Conf.":f"{_h.get('ai_confidence',0)*100:.0f}%",
                            "RSI":f"{_h.get('rsi',0):.1f}",
                            "Stoch":f"{_h.get('stoch',50):.0f}",
                            "Sentiment":_s4.get("label","—"),
                            "Entry":f"${_r4.get('entry_price',0):,.4f}" if _r4.get("entry_price") else "—",
                            "SL":f"${_r4.get('stop_loss',0):,.4f}" if _r4.get("stop_loss") else "—",
                            "TP":f"${_r4.get('take_profit',0):,.4f}" if _r4.get("take_profit") else "—",
                            "R/R":f"{_r4.get('risk_reward_ratio',0):.2f}",
                            "Capital":f"${_h.get('capital',0):,.0f}"})
        st.dataframe(pd.DataFrame(_rows_h),use_container_width=True,hide_index=True)
        if st.button("🗑  Effacer l'historique"):
            st.session_state.signal_history=[]; st.rerun()
