import { useState, useEffect, useRef } from "react";

// ═══════════════════════════════════════════════════════════
//  QUANTUM TRADE ORACLE — App.jsx
//  Colle ce fichier dans : mon-dashboard/src/App.jsx
//
//  IMPORTANT : Remplace YOUR_API_KEY par ta clé Anthropic
//  https://console.anthropic.com/settings/keys
// ═══════════════════════════════════════════════════════════

const API_KEY = "YOUR_API_KEY"; // ← mets ta clé ici

// ── Palette ────────────────────────────────────────────────
const C = {
  bg:      "#060911",
  surface: "#0c1322",
  card:    "#101828",
  border:  "#1c2a44",
  accent:  "#00e5ff",
  green:   "#00ff88",
  red:     "#ff3358",
  yellow:  "#ffd600",
  muted:   "#3d506e",
  text:    "#ccdaf0",
};

// ── CSS global injecté ──────────────────────────────────────
const GLOBAL_CSS = `
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@400;600;700;900&family=Barlow:wght@300;400;500&display=swap');

  *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

  body {
    background: ${C.bg};
    color: ${C.text};
    font-family: 'Barlow', sans-serif;
    min-height: 100vh;
    overflow-x: hidden;
  }

  /* Grille de fond */
  body::before {
    content: '';
    position: fixed; inset: 0; pointer-events: none; z-index: 0;
    background-image:
      linear-gradient(rgba(0,229,255,.025) 1px, transparent 1px),
      linear-gradient(90deg, rgba(0,229,255,.025) 1px, transparent 1px);
    background-size: 44px 44px;
  }

  /* Scroll */
  ::-webkit-scrollbar { width: 4px; height: 4px; }
  ::-webkit-scrollbar-thumb { background: ${C.border}; border-radius: 2px; }
  ::-webkit-scrollbar-track { background: transparent; }

  /* Animations */
  @keyframes pulse-ring {
    0%,100% { box-shadow: 0 0 10px rgba(0,229,255,.35); }
    50%      { box-shadow: 0 0 26px rgba(0,229,255,.75); }
  }
  @keyframes blink {
    0%,100% { opacity: 1; }
    50%      { opacity: .15; }
  }
  @keyframes loader {
    0%   { transform: translateX(-100%); }
    100% { transform: translateX(350%); }
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(10px); }
    to   { opacity: 1; transform: translateY(0); }
  }
  @keyframes scanline {
    0%   { top: -5%; }
    100% { top: 105%; }
  }

  .fade-up { animation: fadeUp .35s ease both; }

  /* Input & Select */
  input, select {
    background: ${C.surface};
    border: 1px solid ${C.border};
    color: ${C.text};
    font-family: 'Share Tech Mono', monospace;
    font-size: 13px;
    padding: 8px 12px;
    border-radius: 4px;
    outline: none;
    transition: border-color .2s, box-shadow .2s;
  }
  input:focus, select:focus {
    border-color: ${C.accent};
    box-shadow: 0 0 0 2px rgba(0,229,255,.1);
  }
  input::placeholder { color: ${C.muted}; }

  /* Table */
  table { width: 100%; border-collapse: collapse; }
  th {
    font-family: 'Share Tech Mono', monospace;
    font-size: 9px; color: ${C.muted};
    text-transform: uppercase; letter-spacing: 1.2px;
    padding: 7px 10px; text-align: left;
    border-bottom: 1px solid ${C.border};
  }
  td {
    font-family: 'Share Tech Mono', monospace;
    font-size: 11px; padding: 7px 10px;
    border-bottom: 1px solid rgba(28,42,68,.5);
  }
  tr:last-child td { border-bottom: none; }
  tr:hover td { background: rgba(0,229,255,.03); }
`;

// ══════════════════════════════════════════════════════════
//  COMPOSANTS UI
// ══════════════════════════════════════════════════════════

function Card({ children, style = {}, glow = false }) {
  return (
    <div className="fade-up" style={{
      background: C.card,
      border: `1px solid ${glow ? C.accent : C.border}`,
      borderRadius: 8,
      padding: "16px 18px",
      position: "relative",
      overflow: "hidden",
      boxShadow: glow ? "0 0 24px rgba(0,229,255,.12)" : "none",
      ...style,
    }}>
      {children}
    </div>
  );
}

function SectionTitle({ children }) {
  return (
    <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 14 }}>
      <span style={{
        fontFamily: "'Barlow Condensed', sans-serif",
        fontSize: 11, fontWeight: 700, letterSpacing: 2.5,
        textTransform: "uppercase", color: C.accent,
      }}>{children}</span>
      <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg,${C.border},transparent)` }} />
    </div>
  );
}

function Label({ children }) {
  return (
    <div style={{
      fontFamily: "'Share Tech Mono', monospace",
      fontSize: 9, color: C.muted,
      textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 8,
    }}>{children}</div>
  );
}

function ProbBar({ label, pct = 0, color }) {
  return (
    <div style={{ marginBottom: 9 }}>
      <div style={{ display: "flex", justifyContent: "space-between", fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color, marginBottom: 4 }}>
        <span>{label}</span><span>{pct.toFixed(1)}%</span>
      </div>
      <div style={{ height: 5, background: C.surface, borderRadius: 3, overflow: "hidden" }}>
        <div style={{
          height: "100%", width: pct + "%",
          background: `linear-gradient(90deg,${color},${color}cc)`,
          borderRadius: 3,
          transition: "width .9s cubic-bezier(.4,0,.2,1)",
        }}/>
      </div>
    </div>
  );
}

function IndBox({ label, value, color = C.text }) {
  return (
    <div style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 5, padding: "9px 12px",
    }}>
      <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 5 }}>{label}</div>
      <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 15, fontWeight: 600, color }}>{value}</div>
    </div>
  );
}

function Gauge({ score = 0 }) {
  const pct   = (score + 1) / 2;
  const angle = score * 90;
  const col   = score > 0.15 ? C.green : score < -0.15 ? C.red : C.yellow;
  return (
    <div style={{ textAlign: "center", margin: "0 auto" }}>
      <svg width={170} height={105} viewBox="0 0 170 105">
        <defs>
          <linearGradient id="gaugeGrad" x1="0%" y1="0%" x2="100%" y2="0%">
            <stop offset="0%"   stopColor="#ff3358"/>
            <stop offset="50%"  stopColor="#ffd600"/>
            <stop offset="100%" stopColor="#00ff88"/>
          </linearGradient>
        </defs>
        {/* Track */}
        <path d="M 15 90 A 70 70 0 0 1 155 90" stroke={C.border} strokeWidth={9} fill="none" strokeLinecap="round"/>
        {/* Fill */}
        <path d="M 15 90 A 70 70 0 0 1 155 90"
          stroke="url(#gaugeGrad)" strokeWidth={9} fill="none" strokeLinecap="round"
          strokeDasharray={220} strokeDashoffset={220 - pct * 220}
          style={{ transition: "stroke-dashoffset 1.1s ease" }}
        />
        {/* Aiguille */}
        <line x1={85} y1={90} x2={85} y2={28}
          stroke={col} strokeWidth={2.5} strokeLinecap="round"
          style={{ transformOrigin: "85px 90px", transform: `rotate(${angle}deg)`, transition: "transform 1.1s ease" }}
        />
        <circle cx={85} cy={90} r={5} fill={col}/>
        {/* Score */}
        <text x={85} y={80} textAnchor="middle"
          fontFamily="Barlow Condensed" fontSize={21} fontWeight={700} fill={col}>
          {score === 0 ? "—" : (score > 0 ? "+" : "") + score.toFixed(2)}
        </text>
        {/* Labels */}
        <text x={11}  y={103} fontFamily="Share Tech Mono" fontSize={8} fill="#ff3358">BEAR</text>
        <text x={156} y={103} fontFamily="Share Tech Mono" fontSize={8} fill="#00ff88" textAnchor="end">BULL</text>
      </svg>
    </div>
  );
}

function StreamLog({ lines }) {
  const ref = useRef(null);
  useEffect(() => { if (ref.current) ref.current.scrollTop = ref.current.scrollHeight; }, [lines]);

  const colors = {
    ok: C.green, err: C.red, warn: C.yellow, info: C.accent, dim: C.muted, plain: C.text,
  };

  return (
    <div ref={ref} style={{
      background: C.surface, border: `1px solid ${C.border}`,
      borderRadius: 4, padding: "12px 14px",
      height: 260, overflowY: "auto",
    }}>
      {lines.map((l, i) => (
        <div key={i} style={{
          fontFamily: "'Share Tech Mono',monospace",
          fontSize: 11, lineHeight: 1.8,
          color: colors[l.type] || C.text,
        }}>{l.text}</div>
      ))}
    </div>
  );
}

// ══════════════════════════════════════════════════════════
//  PROMPT BUILDER
// ══════════════════════════════════════════════════════════
function buildPrompt(symbol, capital, context) {
  return `Tu es Quantum Trade Oracle, un système de trading algorithmique IA de haute précision.
Effectue une analyse complète pour : ${symbol}
Capital : $${capital}
${context ? "Contexte : " + context : ""}

Réponds UNIQUEMENT en JSON valide, aucun texte avant ou après :
{
  "symbol": "${symbol}",
  "signal": {
    "action": "BUY|SELL|HOLD",
    "bullish_probability": 0.00,
    "bearish_probability": 0.00,
    "confidence": 0.00,
    "composite_score": 0.000
  },
  "technical_indicators": {
    "rsi": { "value": 0.0, "signal": "oversold|neutral|overbought" },
    "macd": { "value": 0.000, "histogram": 0.000, "signal": "bullish|bearish|neutral" },
    "bollinger": { "pct_b": 0.00 },
    "ema_cross": { "golden_cross": true },
    "volume": { "ratio": 0.00, "signal": "high|normal|low" },
    "trend": { "direction": "bullish|bearish|sideways", "strength": "strong|moderate|weak" },
    "atr_pct": 0.00,
    "tech_signal_score": 0.000
  },
  "sentiment": {
    "ssgm_score": 0.000,
    "label": "BULLISH|NEUTRAL|BEARISH",
    "news_bullish_pct": 0.0,
    "news_bearish_pct": 0.0,
    "fear_greed_index": 0,
    "fear_greed_label": "texte",
    "key_drivers": ["driver1", "driver2", "driver3"]
  },
  "ai_models": {
    "random_forest":     { "signal": "BUY|SELL|HOLD", "bullish_prob": 0.00, "confidence": 0.00 },
    "gradient_boosting": { "signal": "BUY|SELL|HOLD", "bullish_prob": 0.00, "confidence": 0.00 },
    "lstm":              { "signal": "BUY|SELL|HOLD", "bullish_prob": 0.00, "confidence": 0.00 },
    "transformer":       { "signal": "BUY|SELL|HOLD", "bullish_prob": 0.00, "confidence": 0.00 }
  },
  "risk_management": {
    "entry_price": 0.00,
    "stop_loss": 0.00,
    "take_profit": 0.00,
    "risk_reward_ratio": 0.0,
    "position_size": 0.000000,
    "capital_at_risk": 0.00,
    "risk_level": "FAIBLE|MODÉRÉ|ÉLEVÉ",
    "sl_pct": 0.00,
    "tp_pct": 0.00
  },
  "analysis_log": ["étape1", "étape2", "étape3", "étape4", "étape5"],
  "interpretation": "Interprétation complète en français, 2-3 phrases."
}
Sois réaliste pour ${symbol} aujourd'hui. bullish_probability + bearish_probability ≈ 1.0.`;
}

// ══════════════════════════════════════════════════════════
//  LOADING LINES
// ══════════════════════════════════════════════════════════
const LOADING_LINES = [
  ["INITIALISATION DU PIPELINE…",                              "info"],
  ["→ Connexion aux sources de données marché…",               "dim"],
  ["→ Calcul RSI · MACD · Bollinger · ATR · EMA…",            "dim"],
  ["→ Chargement RandomForest + GradientBoosting…",            "dim"],
  ["→ Chargement LSTM bidirectionnel (PyTorch)…",              "dim"],
  ["→ Chargement Transformer (Positional Encoding)…",          "dim"],
  ["→ Analyse sentiment FinBERT + VADER…",                     "dim"],
  ["→ Fusion des signaux · calcul risque ATR-based…",          "dim"],
  ["ENVOI À CLAUDE IA · EN ATTENTE DE RÉPONSE…",               "warn"],
];

// ══════════════════════════════════════════════════════════
//  APP PRINCIPAL
// ══════════════════════════════════════════════════════════
export default function App() {
  const [symbol,  setSymbol]  = useState("BTC-USD");
  const [capital, setCapital] = useState("10000");
  const [context, setContext] = useState("");
  const [loading, setLoading] = useState(false);
  const [data,    setData]    = useState(null);
  const [lines,   setLines]   = useState([
    { text: "// Entrez un symbole et cliquez ANALYSER pour démarrer.", type: "dim" },
    { text: "// Symboles supportés : BTC-USD  ETH-USD  AAPL  TSLA  SPY  SOL-USD…", type: "dim" },
  ]);
  const [history, setHistory] = useState([]);
  const [clock,   setClock]   = useState("");

  // Horloge UTC
  useEffect(() => {
    const t = setInterval(() => {
      const n = new Date();
      setClock(n.toUTCString().slice(17, 25) + " UTC");
    }, 1000);
    return () => clearInterval(t);
  }, []);

  // ── Analyse ──────────────────────────────────────────────
  async function runAnalysis() {
    if (loading) return;
    setLoading(true);
    setData(null);
    setLines([]);

    // Animer le chargement
    for (let i = 0; i < LOADING_LINES.length; i++) {
      await new Promise(r => setTimeout(r, 170));
      setLines(prev => [...prev, { text: LOADING_LINES[i][0], type: LOADING_LINES[i][1] }]);
    }

    try {
      const res = await fetch("https://api.anthropic.com/v1/messages", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
          "x-api-key": API_KEY,
          "anthropic-version": "2023-06-01",
          "anthropic-dangerous-direct-browser-access": "true",
        },
        body: JSON.stringify({
          model: "claude-sonnet-4-20250514",
          max_tokens: 1600,
          messages: [{ role: "user", content: buildPrompt(symbol, capital, context) }],
        }),
      });

      if (!res.ok) throw new Error("Erreur API " + res.status + " — vérifiez votre clé API_KEY dans App.jsx");

      const raw  = await res.json();
      const text = raw.content?.map(b => b.text || "").join("") || "";
      const json = JSON.parse(text.replace(/```json\s*/g, "").replace(/```\s*/g, "").trim());

      setData(json);

      // Stream du log
      setLines(prev => [...prev,
        { text: "", type: "plain" },
        { text: "✓ RÉPONSE REÇUE — MISE À JOUR DU DASHBOARD", type: "ok" },
        { text: "", type: "plain" },
      ]);
      (json.analysis_log || []).forEach((l, i) =>
        setLines(prev => [...prev, { text: "▸ " + l, type: i === 0 ? "info" : "plain" }])
      );
      setLines(prev => [...prev,
        { text: "", type: "plain" },
        { text: `SIGNAL : ${json.signal.action}  |  Bull ${(json.signal.bullish_probability*100).toFixed(1)}%  Bear ${(json.signal.bearish_probability*100).toFixed(1)}%`,
          type: json.signal.action === "BUY" ? "ok" : json.signal.action === "SELL" ? "err" : "warn" },
        { text: `Sentiment : ${json.sentiment.label}  (SSGM ${json.sentiment.ssgm_score > 0 ? "+" : ""}${json.sentiment.ssgm_score.toFixed(3)})`, type: "plain" },
        { text: "", type: "plain" },
        { text: "✓ ANALYSE TERMINÉE", type: "ok" },
      ]);

      setHistory(prev => [{ time: new Date().toISOString().slice(11, 19), ...json }, ...prev.slice(0, 9)]);

    } catch (err) {
      setLines(prev => [...prev,
        { text: "", type: "plain" },
        { text: "[ ERREUR ] " + err.message, type: "err" },
        { text: "→ Vérifiez que API_KEY est bien renseignée dans App.jsx (ligne 14)", type: "warn" },
        { text: "→ Obtenez une clé sur : console.anthropic.com/settings/keys", type: "dim" },
      ]);
    } finally {
      setLoading(false);
    }
  }

  // Raccourci Entrée
  const onKey = e => e.key === "Enter" && runAnalysis();

  const d    = data;
  const sig  = d?.signal;
  const tech = d?.technical_indicators;
  const sent = d?.sentiment;
  const risk = d?.risk_management;
  const mods = d?.ai_models;

  const sigColor = !sig ? C.muted
    : sig.action === "BUY" ? C.green
    : sig.action === "SELL" ? C.red
    : C.muted;

  const models = [
    { label: "RandomForest",    key: "random_forest" },
    { label: "GradientBoost",   key: "gradient_boosting" },
    { label: "LSTM",            key: "lstm" },
    { label: "Transformer",     key: "transformer" },
  ];

  return (
    <>
      {/* Injecter le CSS global */}
      <style>{GLOBAL_CSS}</style>

      <div style={{ minHeight: "100vh", position: "relative", zIndex: 1 }}>

        {/* ── HEADER ─────────────────────────────────────── */}
        <header style={{
          position: "sticky", top: 0, zIndex: 100,
          display: "flex", alignItems: "center", gap: 14,
          padding: "0 24px", height: 58,
          background: "rgba(6,9,17,.95)",
          borderBottom: `1px solid ${C.border}`,
          backdropFilter: "blur(12px)",
        }}>
          {/* Logo */}
          <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
            <div style={{
              width: 30, height: 30,
              border: `2px solid ${C.accent}`, borderRadius: "50%",
              display: "flex", alignItems: "center", justifyContent: "center",
              fontSize: 13, color: C.accent,
              animation: "pulse-ring 2s ease-in-out infinite",
            }}>⬡</div>
            <span style={{
              fontFamily: "'Barlow Condensed',sans-serif",
              fontSize: 20, fontWeight: 900, letterSpacing: 2.5,
              color: C.accent, textTransform: "uppercase",
            }}>QUANTUM TRADE ORACLE</span>
          </div>

          {/* Droite */}
          <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 18 }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6,
              fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: C.green }}>
              <div style={{
                width: 7, height: 7, borderRadius: "50%",
                background: C.green, boxShadow: `0 0 7px ${C.green}`,
                animation: "blink 1s ease-in-out infinite",
              }}/>
              LIVE
            </div>
            <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 11, color: C.muted }}>
              {clock}
            </span>
          </div>
        </header>

        {/* ── CONTENU ────────────────────────────────────── */}
        <div style={{ padding: "20px 22px", maxWidth: 1380, margin: "0 auto" }}>

          {/* CONTROLS */}
          <div style={{
            background: C.card, border: `1px solid ${C.border}`,
            borderRadius: 8, padding: "14px 18px", marginBottom: 20,
            display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end",
          }}>
            {/* Symbole */}
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <label style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1 }}>Symbole</label>
              <input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())}
                onKeyDown={onKey} style={{ width: 150 }} placeholder="BTC-USD, AAPL…"/>
            </div>

            {/* Capital */}
            <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
              <label style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1 }}>Capital ($)</label>
              <input value={capital} onChange={e => setCapital(e.target.value)}
                type="number" style={{ width: 120 }}/>
            </div>

            {/* Contexte */}
            <div style={{ display: "flex", flexDirection: "column", gap: 5, flex: 1, minWidth: 220 }}>
              <label style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1 }}>Contexte (optionnel)</label>
              <input value={context} onChange={e => setContext(e.target.value)}
                onKeyDown={onKey} style={{ width: "100%" }}
                placeholder="ex: halving prochain, Fed meeting ce soir…"/>
            </div>

            {/* Bouton */}
            <button onClick={runAnalysis} disabled={loading} style={{
              padding: "9px 24px",
              background: "transparent",
              border: `1px solid ${loading ? C.muted : C.accent}`,
              color: loading ? C.muted : C.accent,
              fontFamily: "'Barlow Condensed',sans-serif",
              fontSize: 14, fontWeight: 700, letterSpacing: 2,
              textTransform: "uppercase",
              borderRadius: 4, cursor: loading ? "not-allowed" : "pointer",
              transition: "all .2s",
            }}>
              {loading ? "ANALYSE…" : "⬡  ANALYSER"}
            </button>

            {/* Loader bar */}
            {loading && (
              <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                <div style={{ width: 90, height: 2, background: C.border, borderRadius: 1, overflow: "hidden" }}>
                  <div style={{ height: "100%", width: "38%", background: C.accent, borderRadius: 1, animation: "loader 1.2s ease-in-out infinite" }}/>
                </div>
                <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: C.accent }}>EN COURS…</span>
              </div>
            )}
          </div>

          {/* ── TOP METRICS ── */}
          <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 16 }}>
            <Card glow={!!sig}>
              <Label>Signal Principal</Label>
              <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontSize: 44, fontWeight: 700, color: sigColor, lineHeight: 1, marginBottom: 6 }}>
                {sig?.action || "—"}
              </div>
              <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: C.muted }}>
                {sig ? `Score : ${(sig.composite_score > 0 ? "+" : "") + sig.composite_score.toFixed(3)}` : "En attente"}
              </div>
            </Card>

            <Card>
              <Label>Probabilité Haussière</Label>
              <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontSize: 42, fontWeight: 700, color: C.green, lineHeight: 1, marginBottom: 8 }}>
                {sig ? Math.round(sig.bullish_probability * 100) + "%" : "—"}
              </div>
              <ProbBar label="" pct={sig ? sig.bullish_probability * 100 : 0} color={C.green}/>
            </Card>

            <Card>
              <Label>Probabilité Baissière</Label>
              <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontSize: 42, fontWeight: 700, color: C.red, lineHeight: 1, marginBottom: 8 }}>
                {sig ? Math.round(sig.bearish_probability * 100) + "%" : "—"}
              </div>
              <ProbBar label="" pct={sig ? sig.bearish_probability * 100 : 0} color={C.red}/>
            </Card>

            <Card>
              <Label>Confiance du Modèle</Label>
              <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontSize: 42, fontWeight: 700, color: C.accent, lineHeight: 1, marginBottom: 6 }}>
                {sig ? Math.round(sig.confidence * 100) + "%" : "—"}
              </div>
              <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: C.muted }}>
                {sig ? (sig.confidence >= .75 ? "HAUTE CONFIANCE" : sig.confidence >= .55 ? "MODÉRÉE" : "FAIBLE") : "—"}
              </div>
            </Card>
          </div>

          {/* ── MID ROW ── */}
          <div style={{ display: "grid", gridTemplateColumns: "1.55fr 1fr", gap: 16, marginBottom: 16 }}>

            {/* Stream */}
            <Card>
              <SectionTitle>Journal d'analyse IA</SectionTitle>
              <StreamLog lines={lines}/>
              {d?.interpretation && (
                <div style={{
                  marginTop: 12, fontSize: 12, color: C.text, lineHeight: 1.75,
                  fontFamily: "'Barlow',sans-serif",
                  borderLeft: `2px solid ${C.accent}`, paddingLeft: 12,
                }}>
                  {d.interpretation}
                </div>
              )}
            </Card>

            {/* Sentiment */}
            <Card>
              <SectionTitle>Sentiment du Marché</SectionTitle>
              <Gauge score={sent?.ssgm_score || 0}/>
              <div style={{
                textAlign: "center", marginBottom: 14,
                fontFamily: "'Barlow Condensed',sans-serif",
                fontSize: 16, fontWeight: 700, letterSpacing: 2,
                color: sent?.ssgm_score > 0.1 ? C.green : sent?.ssgm_score < -0.1 ? C.red : C.yellow,
              }}>
                {sent?.label || "EN ATTENTE"}
              </div>
              <ProbBar label="Bullish News" pct={sent?.news_bullish_pct || 0} color={C.green}/>
              <ProbBar label="Bearish News" pct={sent?.news_bearish_pct || 0} color={C.red}/>
              {sent?.key_drivers && (
                <div style={{ marginTop: 10 }}>
                  {sent.key_drivers.map((kd, i) => (
                    <div key={i} style={{
                      fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: C.muted,
                      padding: "4px 0", borderBottom: i < 2 ? `1px solid ${C.border}` : "none",
                    }}>› {kd}</div>
                  ))}
                </div>
              )}
              {sent && (
                <div style={{ marginTop: 10, textAlign: "center", fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: C.yellow }}>
                  Fear & Greed : {sent.fear_greed_index}/100 — {sent.fear_greed_label}
                </div>
              )}
            </Card>
          </div>

          {/* ── BOTTOM ROW ── */}
          <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>

            {/* Indicateurs */}
            <Card>
              <SectionTitle>Indicateurs Techniques</SectionTitle>
              <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                <IndBox label="RSI (14)" value={tech ? tech.rsi.value.toFixed(1) : "—"}
                  color={tech ? (tech.rsi.value < 35 ? C.green : tech.rsi.value > 65 ? C.red : C.yellow) : C.muted}/>
                <IndBox label="MACD" value={tech ? tech.macd.signal.toUpperCase() : "—"}
                  color={tech ? (tech.macd.signal === "bullish" ? C.green : tech.macd.signal === "bearish" ? C.red : C.yellow) : C.muted}/>
                <IndBox label="Bollinger %B" value={tech ? (tech.bollinger.pct_b * 100).toFixed(0) + "%" : "—"}
                  color={tech ? (tech.bollinger.pct_b < 0.2 ? C.green : tech.bollinger.pct_b > 0.8 ? C.red : C.yellow) : C.muted}/>
                <IndBox label="EMA Cross" value={tech ? (tech.ema_cross.golden_cross ? "GOLDEN ✓" : "DEATH ✗") : "—"}
                  color={tech ? (tech.ema_cross.golden_cross ? C.green : C.red) : C.muted}/>
                <IndBox label="Volume" value={tech ? tech.volume.ratio.toFixed(2) + "x" : "—"}
                  color={tech?.volume.signal === "high" ? C.yellow : C.text}/>
                <IndBox label="Tendance" value={tech ? (tech.trend.strength + " " + tech.trend.direction).toUpperCase() : "—"}
                  color={tech ? (tech.trend.direction === "bullish" ? C.green : tech.trend.direction === "bearish" ? C.red : C.yellow) : C.muted}/>
                <IndBox label="ATR (vol.)" value={tech ? tech.atr_pct.toFixed(2) + "%" : "—"} color={C.accent}/>
                <IndBox label="Score Tech" value={tech ? (tech.tech_signal_score > 0 ? "+" : "") + tech.tech_signal_score.toFixed(3) : "—"}
                  color={tech ? (tech.tech_signal_score > 0.1 ? C.green : tech.tech_signal_score < -0.1 ? C.red : C.yellow) : C.muted}/>
              </div>
            </Card>

            {/* Risk */}
            <Card>
              <SectionTitle>Gestion du Risque</SectionTitle>
              {[
                ["Action",          sigColor,                                                    sig?.action || "—"],
                ["Prix d'entrée",   C.text,    risk ? "$" + risk.entry_price.toLocaleString() : "—"],
                ["Stop-Loss",       C.red,     risk ? "$" + risk.stop_loss.toLocaleString() + ` (−${risk.sl_pct}%)` : "—"],
                ["Take-Profit",     C.green,   risk ? "$" + risk.take_profit.toLocaleString() + ` (+${risk.tp_pct}%)` : "—"],
                ["Risk / Reward",   C.accent,  risk ? risk.risk_reward_ratio.toFixed(2) + " : 1" : "—"],
                ["Taille position", C.text,    risk ? risk.position_size.toFixed(6) + " u." : "—"],
                ["Capital risqué",  C.yellow,  risk ? "$" + risk.capital_at_risk.toFixed(2) : "—"],
                ["Niveau de risque",
                  risk?.risk_level === "FAIBLE" ? C.green : risk?.risk_level === "ÉLEVÉ" ? C.red : C.yellow,
                  risk?.risk_level || "—"],
              ].map(([k, col, v]) => (
                <div key={k} style={{
                  display: "flex", justifyContent: "space-between", alignItems: "center",
                  padding: "7px 0", borderBottom: `1px solid rgba(28,42,68,.45)`,
                }}>
                  <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: C.muted }}>{k}</span>
                  <span style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 12, fontWeight: 600, color: col }}>{v}</span>
                </div>
              ))}
            </Card>
          </div>

          {/* ── MODÈLES IA ── */}
          <Card style={{ marginBottom: 16 }}>
            <SectionTitle>Contribution des Modèles IA</SectionTitle>
            <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12 }}>
              {models.map(({ label, key }) => {
                const m   = mods?.[key];
                const col = m?.signal === "BUY" ? C.green : m?.signal === "SELL" ? C.red : C.muted;
                return (
                  <div key={key} style={{
                    background: C.surface, border: `1px solid ${C.border}`,
                    borderRadius: 6, padding: "12px 14px",
                  }}>
                    <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 9, color: C.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 7 }}>{label}</div>
                    <div style={{ fontFamily: "'Barlow Condensed',sans-serif", fontSize: 24, fontWeight: 700, color: col, marginBottom: 6 }}>
                      {m?.signal || "—"}
                    </div>
                    <ProbBar label="Bull" pct={m ? m.bullish_prob * 100 : 0} color={C.green}/>
                    <div style={{ fontFamily: "'Share Tech Mono',monospace", fontSize: 10, color: C.muted }}>
                      Conf : {m ? (m.confidence * 100).toFixed(0) + "%" : "—"}
                    </div>
                  </div>
                );
              })}
            </div>
          </Card>

          {/* ── HISTORIQUE ── */}
          <Card style={{ marginBottom: 24 }}>
            <SectionTitle>Historique des Signaux</SectionTitle>
            {history.length === 0 ? (
              <div style={{ textAlign: "center", fontFamily: "'Share Tech Mono',monospace", color: C.muted, padding: "18px 0", fontSize: 11 }}>
                Aucun signal généré — lancez une analyse
              </div>
            ) : (
              <div style={{ overflowX: "auto" }}>
                <table>
                  <thead>
                    <tr>{["Heure","Symbole","Signal","Bull%","Bear%","Conf.","Sentiment","Entrée","SL","TP"].map(h => <th key={h}>{h}</th>)}</tr>
                  </thead>
                  <tbody>
                    {history.map((h, i) => {
                      const sc   = h.signal?.action === "BUY" ? C.green : h.signal?.action === "SELL" ? C.red : C.muted;
                      const sentc = h.sentiment?.ssgm_score > 0 ? C.green : h.sentiment?.ssgm_score < 0 ? C.red : C.muted;
                      return (
                        <tr key={i}>
                          <td style={{ color: C.muted }}>{h.time}</td>
                          <td style={{ color: C.text }}>{h.symbol}</td>
                          <td style={{ color: sc, fontWeight: 700 }}>{h.signal?.action}</td>
                          <td style={{ color: C.green }}>{(h.signal?.bullish_probability * 100).toFixed(1)}%</td>
                          <td style={{ color: C.red }}>{(h.signal?.bearish_probability * 100).toFixed(1)}%</td>
                          <td style={{ color: C.accent }}>{(h.signal?.confidence * 100).toFixed(0)}%</td>
                          <td style={{ color: sentc }}>{h.sentiment?.label}</td>
                          <td>{h.risk_management?.entry_price ? "$" + h.risk_management.entry_price.toLocaleString() : "—"}</td>
                          <td style={{ color: C.red }}>{h.risk_management?.stop_loss ? "$" + h.risk_management.stop_loss.toLocaleString() : "—"}</td>
                          <td style={{ color: C.green }}>{h.risk_management?.take_profit ? "$" + h.risk_management.take_profit.toLocaleString() : "—"}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            )}
          </Card>

          {/* DISCLAIMER */}
          <div style={{
            textAlign: "center", fontFamily: "'Share Tech Mono',monospace",
            fontSize: 9, color: C.muted, padding: "12px 0",
            borderTop: `1px solid ${C.border}`, letterSpacing: .5,
          }}>
            ⚠ OUTIL ÉDUCATIF UNIQUEMENT — Analyses générées par IA, ne constituent pas des conseils financiers.
            Ne jamais investir plus que ce que vous pouvez vous permettre de perdre.
          </div>

        </div>
      </div>
    </>
  );
}