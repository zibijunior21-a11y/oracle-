import { useState, useEffect, useRef } from "react";

const STYLES = {
    bg: "#050810", surface: "#0b1020", card: "#0f1628", border: "#1a2540",
    accent: "#00e5ff", green: "#00ff88", red: "#ff3358", yellow: "#ffd600",
    muted: "#3a4a6b", text: "#c8d8f0",
};

const css = `
  @import url('https://fonts.googleapis.com/css2?family=Share+Tech+Mono&family=Barlow+Condensed:wght@400;700;900&family=Barlow:wght@400;500&display=swap');
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body { background: #050810; }
  .qto-root {
    background: #050810; color: #c8d8f0;
    font-family: 'Barlow', sans-serif;
    min-height: 100vh; position: relative; overflow-x: hidden;
  }
  .qto-root::before {
    content:''; position:fixed; inset:0; pointer-events:none; z-index:0;
    background-image: linear-gradient(rgba(0,229,255,.025) 1px,transparent 1px),
      linear-gradient(90deg,rgba(0,229,255,.025) 1px,transparent 1px);
    background-size: 40px 40px;
  }
  .mono { font-family: 'Share Tech Mono', monospace; }
  .display { font-family: 'Barlow Condensed', sans-serif; }
  @keyframes pulse { 0%,100%{box-shadow:0 0 12px rgba(0,229,255,.4)} 50%{box-shadow:0 0 28px rgba(0,229,255,.8)} }
  @keyframes blink { 0%,100%{opacity:1} 50%{opacity:.15} }
  @keyframes slide { 0%{transform:translateX(-100%)} 100%{transform:translateX(350%)} }
  @keyframes fadeUp { from{opacity:0;transform:translateY(10px)} to{opacity:1;transform:translateY(0)} }
  @keyframes scanline {
    0%{top:-10%} 100%{top:110%}
  }
  .scan-anim { animation: scanline 4s linear infinite; }
`;

function StreamLine({ text, type }) {
    const colors = {
        ok: STYLES.green, err: STYLES.red, warn: STYLES.yellow,
        info: STYLES.accent, dim: STYLES.muted, plain: STYLES.text,
    };
    return (
        <div style={{ color: colors[type] || STYLES.text, lineHeight: 1.7, fontSize: 11, fontFamily: "Share Tech Mono, monospace" }}>
            {text}
        </div>
    );
}

function ProbBar({ label, pct, color }) {
    return (
        <div style={{ marginBottom: 8 }}>
            <div style={{ display: "flex", justifyContent: "space-between", fontSize: 10, fontFamily: "Share Tech Mono,monospace", color: color, marginBottom: 4 }}>
                <span>{label}</span><span>{pct.toFixed(1)}%</span>
            </div>
            <div style={{ height: 5, background: STYLES.surface, borderRadius: 3, overflow: "hidden" }}>
                <div style={{ height: "100%", width: pct + "%", background: color, borderRadius: 3, transition: "width .9s cubic-bezier(.4,0,.2,1)" }} />
            </div>
        </div>
    );
}

function Card({ children, style, glow }) {
    return (
        <div style={{
            background: STYLES.card, border: `1px solid ${glow ? STYLES.accent : STYLES.border}`,
            borderRadius: 8, padding: "16px 18px", position: "relative", overflow: "hidden",
            boxShadow: glow ? `0 0 20px rgba(0,229,255,.15)` : "none",
            animation: "fadeUp .4s ease both", ...style
        }}>
            {children}
        </div>
    );
}

function Label({ children }) {
    return <div style={{ fontFamily: "Share Tech Mono,monospace", fontSize: 9, color: STYLES.muted, textTransform: "uppercase", letterSpacing: 1.5, marginBottom: 8 }}>{children}</div>;
}

function SectionTitle({ children }) {
    return (
        <div style={{ display: "flex", alignItems: "center", gap: 8, marginBottom: 12 }}>
            <span style={{ fontFamily: "Barlow Condensed,sans-serif", fontSize: 12, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase", color: STYLES.accent }}>{children}</span>
            <div style={{ flex: 1, height: 1, background: `linear-gradient(90deg,${STYLES.border},transparent)` }} />
        </div>
    );
}

function Gauge({ score }) {
    const pct = (score + 1) / 2;
    const angle = score * 90;
    const c = score > 0.15 ? STYLES.green : score < -0.15 ? STYLES.red : STYLES.yellow;
    return (
        <div style={{ textAlign: "center" }}>
            <svg width={170} height={100} viewBox="0 0 170 100">
                <defs>
                    <linearGradient id="gg" x1="0%" y1="0%" x2="100%" y2="0%">
                        <stop offset="0%" stopColor="#ff3358" />
                        <stop offset="50%" stopColor="#ffd600" />
                        <stop offset="100%" stopColor="#00ff88" />
                    </linearGradient>
                </defs>
                <path d="M 15 88 A 70 70 0 0 1 155 88" stroke={STYLES.border} strokeWidth={8} fill="none" strokeLinecap="round" />
                <path d="M 15 88 A 70 70 0 0 1 155 88" stroke="url(#gg)" strokeWidth={8} fill="none" strokeLinecap="round"
                    strokeDasharray={220} strokeDashoffset={220 - pct * 220} style={{ transition: "stroke-dashoffset 1s ease" }} />
                <line x1={85} y1={88} x2={85} y2={30} stroke={c} strokeWidth={2} strokeLinecap="round"
                    style={{ transformOrigin: "85px 88px", transform: `rotate(${angle}deg)`, transition: "transform 1s ease" }} />
                <circle cx={85} cy={88} r={4} fill={c} />
                <text x={85} y={75} textAnchor="middle" fontFamily="Barlow Condensed" fontSize={22} fontWeight={700} fill={c}>
                    {score === null ? "—" : (score > 0 ? "+" : "") + score.toFixed(2)}
                </text>
                <text x={12} y={100} fontFamily="Share Tech Mono" fontSize={8} fill="#ff3358">BEAR</text>
                <text x={156} y={100} fontFamily="Share Tech Mono" fontSize={8} fill="#00ff88" textAnchor="end">BULL</text>
            </svg>
        </div>
    );
}

function IndBox({ label, value, color }) {
    return (
        <div style={{ background: STYLES.surface, border: `1px solid ${STYLES.border}`, borderRadius: 4, padding: "8px 12px" }}>
            <div style={{ fontFamily: "Share Tech Mono,monospace", fontSize: 9, color: STYLES.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 4 }}>{label}</div>
            <div style={{ fontFamily: "Share Tech Mono,monospace", fontSize: 15, fontWeight: 600, color: color || STYLES.text }}>{value}</div>
        </div>
    );
}

const LOADING_LINES = [
    ["INITIALISATION DU PIPELINE…", "info"],
    ["→ Connexion aux sources de données marché…", "dim"],
    ["→ Calcul des indicateurs techniques (RSI, MACD, BB, ATR…)", "dim"],
    ["→ Chargement des 4 modèles IA…", "dim"],
    ["→ Analyse du sentiment des news financières…", "dim"],
    ["→ Prédiction de l'ensemble (RF + GB + LSTM + Transformer)…", "dim"],
    ["→ Calcul des niveaux de risque (ATR-based SL/TP)…", "dim"],
    ["→ Fusion des signaux et génération de la décision finale…", "dim"],
    ["APPEL À CLAUDE IA…", "warn"],
];

export default function QuantumTradeOracle() {
    const [symbol, setSymbol] = useState("BTC-USD");
    const [capital, setCapital] = useState("10000");
    const [context, setContext] = useState("");
    const [loading, setLoading] = useState(false);
    const [data, setData] = useState(null);
    const [lines, setLines] = useState([{ text: "// Entrez un symbole et cliquez ANALYSER…", type: "dim" },
    { text: "// Le système simule 4 modèles IA + sentiment + risk management.", type: "dim" }]);
    const [clock, setClock] = useState("");
    const [history, setHistory] = useState([]);
    const streamRef = useRef(null);

    useEffect(() => {
        const t = setInterval(() => {
            const n = new Date();
            setClock(n.toUTCString().slice(17, 25) + " UTC");
        }, 1000);
        return () => clearInterval(t);
    }, []);

    useEffect(() => {
        if (streamRef.current) streamRef.current.scrollTop = streamRef.current.scrollHeight;
    }, [lines]);

    function addLine(text, type = "plain") {
        setLines(prev => [...prev, { text, type }]);
    }

    async function runAnalysis() {
        if (loading) return;
        setLoading(true);
        setData(null);
        setLines([]);

        // Animate loading
        for (let i = 0; i < LOADING_LINES.length; i++) {
            await new Promise(r => setTimeout(r, 160));
            setLines(prev => [...prev, { text: LOADING_LINES[i][0], type: LOADING_LINES[i][1] }]);
        }

        const prompt = `Tu es Quantum Trade Oracle, un système de trading algorithmique IA.
Effectue une analyse complète pour : ${symbol}
Capital : $${capital}
${context ? "Contexte : " + context : ""}

Réponds UNIQUEMENT en JSON valide (aucun texte avant/après), format exact :
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
    "rsi": {"value": 0.0, "signal": "oversold|neutral|overbought"},
    "macd": {"value": 0.000, "histogram": 0.000, "signal": "bullish|bearish|neutral"},
    "bollinger": {"pct_b": 0.00},
    "ema_cross": {"golden_cross": true},
    "volume": {"ratio": 0.00, "signal": "high|normal|low"},
    "trend": {"direction": "bullish|bearish|sideways", "strength": "strong|moderate|weak"},
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
    "random_forest":     {"signal": "BUY|SELL|HOLD", "bullish_prob": 0.00, "confidence": 0.00},
    "gradient_boosting": {"signal": "BUY|SELL|HOLD", "bullish_prob": 0.00, "confidence": 0.00},
    "lstm":              {"signal": "BUY|SELL|HOLD", "bullish_prob": 0.00, "confidence": 0.00},
    "transformer":       {"signal": "BUY|SELL|HOLD", "bullish_prob": 0.00, "confidence": 0.00}
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
  "analysis_log": ["ligne1","ligne2","ligne3","ligne4","ligne5"],
  "interpretation": "Texte complet d'interprétation en français, 2-3 phrases."
}

Sois réaliste pour ${symbol} en mars 2026. bullish_prob + bearish_prob ≈ 1.0.`;

        try {
            const res = await fetch("https://api.anthropic.com/v1/messages", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({
                    model: "claude-sonnet-4-20250514",
                    max_tokens: 1500,
                    messages: [{ role: "user", content: prompt }],
                }),
            });

            if (!res.ok) throw new Error("API " + res.status);
            const raw = await res.json();
            const text = raw.content?.map(b => b.text || "").join("") || "";
            const json = JSON.parse(text.replace(/```json\s*/g, "").replace(/```\s*/g, "").trim());

            setData(json);
            setLines(prev => [...prev,
            { text: "", type: "plain" },
            { text: "✓ RÉPONSE REÇUE — MISE À JOUR DU DASHBOARD", type: "ok" },
            { text: "", type: "plain" },
            ]);

            // Stream the analysis log
            if (json.analysis_log) {
                json.analysis_log.forEach((l, i) => {
                    setLines(prev => [...prev, { text: "▸ " + l, type: i === 0 ? "info" : "plain" }]);
                });
            }
            setLines(prev => [...prev,
            { text: "", type: "plain" },
            { text: `SIGNAL: ${json.signal.action}  |  Bull: ${(json.signal.bullish_probability * 100).toFixed(1)}%  Bear: ${(json.signal.bearish_probability * 100).toFixed(1)}%`, type: json.signal.action === "BUY" ? "ok" : json.signal.action === "SELL" ? "err" : "warn" },
            { text: `Sentiment: ${json.sentiment.label}  (SSGM ${json.sentiment.ssgm_score > 0 ? "+" : ""}${json.sentiment.ssgm_score.toFixed(3)})`, type: "plain" },
            { text: "", type: "plain" },
            { text: "✓ ANALYSE TERMINÉE", type: "ok" },
            ]);

            setHistory(prev => [{ time: new Date().toISOString().slice(11, 19), ...json }, ...prev.slice(0, 9)]);

        } catch (err) {
            setLines(prev => [...prev,
            { text: "", type: "plain" },
            { text: "[ ERREUR ] " + err.message, type: "err" },
            { text: "Vérifiez que l'API est accessible dans cet environnement.", type: "dim" },
            ]);
        } finally {
            setLoading(false);
        }
    }

    const d = data;
    const sig = d?.signal;
    const tech = d?.technical_indicators;
    const sent = d?.sentiment;
    const risk = d?.risk_management;
    const mods = d?.ai_models;

    const signalColor = !sig ? STYLES.muted : sig.action === "BUY" ? STYLES.green : sig.action === "SELL" ? STYLES.red : STYLES.muted;

    const modelList = [
        { label: "RandomForest", key: "random_forest" },
        { label: "GradientBoost", key: "gradient_boosting" },
        { label: "LSTM", key: "lstm" },
        { label: "Transformer", key: "transformer" },
    ];

    return (
        <>
            <style>{css}</style>
            <div className="qto-root" style={{ minHeight: "100vh" }}>

                {/* HEADER */}
                <div style={{
                    display: "flex", alignItems: "center", gap: 14, padding: "0 24px",
                    height: 56, borderBottom: `1px solid ${STYLES.border}`,
                    background: "rgba(5,8,16,.95)", backdropFilter: "blur(10px)",
                    position: "sticky", top: 0, zIndex: 100,
                }}>
                    <div style={{ display: "flex", alignItems: "center", gap: 10 }}>
                        <div style={{
                            width: 30, height: 30, border: `2px solid ${STYLES.accent}`, borderRadius: "50%",
                            display: "flex", alignItems: "center", justifyContent: "center",
                            fontSize: 14, color: STYLES.accent, animation: "pulse 2s ease-in-out infinite",
                        }}>⬡</div>
                        <span className="display" style={{ fontSize: 20, fontWeight: 900, letterSpacing: 2, color: STYLES.accent, textTransform: "uppercase" }}>
                            QUANTUM TRADE ORACLE
                        </span>
                    </div>
                    <div style={{ marginLeft: "auto", display: "flex", alignItems: "center", gap: 16 }}>
                        <div style={{ display: "flex", alignItems: "center", gap: 6, fontFamily: "Share Tech Mono,monospace", fontSize: 10, color: STYLES.green }}>
                            <div style={{ width: 6, height: 6, borderRadius: "50%", background: STYLES.green, boxShadow: `0 0 6px ${STYLES.green}`, animation: "blink 1s ease-in-out infinite" }} />
                            LIVE
                        </div>
                        <span className="mono" style={{ fontSize: 11, color: STYLES.muted }}>{clock}</span>
                    </div>
                </div>

                <div style={{ padding: "18px 20px", maxWidth: 1380, margin: "0 auto" }}>

                    {/* CONTROLS */}
                    <div style={{
                        background: STYLES.card, border: `1px solid ${STYLES.border}`, borderRadius: 8,
                        padding: "14px 18px", marginBottom: 18,
                        display: "flex", gap: 12, flexWrap: "wrap", alignItems: "flex-end",
                    }}>
                        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                            <label className="mono" style={{ fontSize: 9, color: STYLES.muted, textTransform: "uppercase", letterSpacing: 1 }}>Symbole</label>
                            <input value={symbol} onChange={e => setSymbol(e.target.value.toUpperCase())}
                                onKeyDown={e => e.key === "Enter" && runAnalysis()}
                                style={{ background: STYLES.surface, border: `1px solid ${STYLES.border}`, color: STYLES.text, fontFamily: "Share Tech Mono,monospace", fontSize: 13, padding: "7px 12px", borderRadius: 4, outline: "none", width: 150 }}
                                placeholder="BTC-USD, AAPL…" />
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 5 }}>
                            <label className="mono" style={{ fontSize: 9, color: STYLES.muted, textTransform: "uppercase", letterSpacing: 1 }}>Capital ($)</label>
                            <input value={capital} onChange={e => setCapital(e.target.value)} type="number"
                                style={{ background: STYLES.surface, border: `1px solid ${STYLES.border}`, color: STYLES.text, fontFamily: "Share Tech Mono,monospace", fontSize: 13, padding: "7px 12px", borderRadius: 4, outline: "none", width: 120 }} />
                        </div>
                        <div style={{ display: "flex", flexDirection: "column", gap: 5, flex: 1, minWidth: 220 }}>
                            <label className="mono" style={{ fontSize: 9, color: STYLES.muted, textTransform: "uppercase", letterSpacing: 1 }}>Contexte (optionnel)</label>
                            <input value={context} onChange={e => setContext(e.target.value)}
                                onKeyDown={e => e.key === "Enter" && runAnalysis()}
                                style={{ background: STYLES.surface, border: `1px solid ${STYLES.border}`, color: STYLES.text, fontFamily: "Share Tech Mono,monospace", fontSize: 12, padding: "7px 12px", borderRadius: 4, outline: "none", width: "100%" }}
                                placeholder="ex: halving prochain, Fed meeting ce soir…" />
                        </div>
                        <button onClick={runAnalysis} disabled={loading} className="display"
                            style={{
                                padding: "8px 22px", background: "transparent", border: `1px solid ${STYLES.accent}`,
                                color: loading ? STYLES.muted : STYLES.accent, fontFamily: "Barlow Condensed,sans-serif",
                                fontSize: 14, fontWeight: 700, letterSpacing: 2, textTransform: "uppercase",
                                cursor: loading ? "not-allowed" : "pointer", borderRadius: 4,
                                transition: "all .2s", opacity: loading ? .5 : 1,
                                boxShadow: loading ? "none" : `0 0 0px rgba(0,229,255,0)`,
                            }}
                            onMouseEnter={e => { if (!loading) e.target.style.boxShadow = "0 0 16px rgba(0,229,255,.3)"; }}
                            onMouseLeave={e => { e.target.style.boxShadow = "none"; }}>
                            {loading ? "ANALYSE…" : "⬡  ANALYSER"}
                        </button>

                        {loading && (
                            <div style={{ display: "flex", alignItems: "center", gap: 8 }}>
                                <div style={{ width: 100, height: 2, background: STYLES.border, borderRadius: 1, overflow: "hidden" }}>
                                    <div style={{ height: "100%", width: "40%", background: STYLES.accent, animation: "slide 1.2s ease-in-out infinite", borderRadius: 1 }} />
                                </div>
                                <span className="mono" style={{ fontSize: 10, color: STYLES.accent }}>EN COURS…</span>
                            </div>
                        )}
                    </div>

                    {/* TOP METRICS */}
                    <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12, marginBottom: 16 }}>
                        <Card glow={!!sig}>
                            <Label>Signal Principal</Label>
                            <div className="display" style={{ fontSize: 40, fontWeight: 700, color: signalColor, lineHeight: 1, marginBottom: 6 }}>
                                {sig?.action || "—"}
                            </div>
                            <div className="mono" style={{ fontSize: 10, color: STYLES.muted }}>
                                {sig ? `Score: ${sig.composite_score > 0 ? "+" : ""}${sig.composite_score.toFixed(3)}` : "En attente d'analyse"}
                            </div>
                        </Card>

                        <Card>
                            <Label>Probabilité Haussière</Label>
                            <div className="display" style={{ fontSize: 38, fontWeight: 700, color: STYLES.green, lineHeight: 1, marginBottom: 8 }}>
                                {sig ? Math.round(sig.bullish_probability * 100) + "%" : "—"}
                            </div>
                            <ProbBar label="" pct={sig ? sig.bullish_probability * 100 : 0} color={STYLES.green} />
                        </Card>

                        <Card>
                            <Label>Probabilité Baissière</Label>
                            <div className="display" style={{ fontSize: 38, fontWeight: 700, color: STYLES.red, lineHeight: 1, marginBottom: 8 }}>
                                {sig ? Math.round(sig.bearish_probability * 100) + "%" : "—"}
                            </div>
                            <ProbBar label="" pct={sig ? sig.bearish_probability * 100 : 0} color={STYLES.red} />
                        </Card>

                        <Card>
                            <Label>Confiance du Modèle</Label>
                            <div className="display" style={{ fontSize: 38, fontWeight: 700, color: STYLES.accent, lineHeight: 1, marginBottom: 6 }}>
                                {sig ? Math.round(sig.confidence * 100) + "%" : "—"}
                            </div>
                            <div className="mono" style={{ fontSize: 10, color: STYLES.muted }}>
                                {sig ? (sig.confidence >= .75 ? "HAUTE CONFIANCE" : sig.confidence >= .55 ? "CONFIANCE MODÉRÉE" : "CONFIANCE FAIBLE") : "—"}
                            </div>
                        </Card>
                    </div>

                    {/* MID ROW */}
                    <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: 16, marginBottom: 16 }}>

                        {/* STREAM */}
                        <Card>
                            <SectionTitle>Journal d'analyse IA</SectionTitle>
                            <div ref={streamRef} style={{
                                background: STYLES.surface, border: `1px solid ${STYLES.border}`,
                                borderRadius: 4, padding: "12px 14px", maxHeight: 280, overflowY: "auto",
                                scrollbarWidth: "thin", scrollbarColor: `${STYLES.border} transparent`,
                            }}>
                                {lines.map((l, i) => <StreamLine key={i} text={l.text} type={l.type} />)}
                            </div>
                            {d?.interpretation && (
                                <div className="mono" style={{ fontSize: 11, color: STYLES.text, marginTop: 12, lineHeight: 1.7, borderLeft: `2px solid ${STYLES.accent}`, paddingLeft: 12 }}>
                                    {d.interpretation}
                                </div>
                            )}
                        </Card>

                        {/* SENTIMENT */}
                        <Card>
                            <SectionTitle>Sentiment du Marché</SectionTitle>
                            <Gauge score={sent ? sent.ssgm_score : 0} />
                            <div className="display" style={{ textAlign: "center", fontSize: 16, fontWeight: 700, letterSpacing: 2, color: sent?.ssgm_score > 0.1 ? STYLES.green : sent?.ssgm_score < -0.1 ? STYLES.red : STYLES.yellow, marginBottom: 14 }}>
                                {sent?.label || "EN ATTENTE"}
                            </div>
                            <ProbBar label="Bullish News" pct={sent ? sent.news_bullish_pct : 0} color={STYLES.green} />
                            <ProbBar label="Bearish News" pct={sent ? sent.news_bearish_pct : 0} color={STYLES.red} />
                            {sent?.key_drivers && (
                                <div style={{ marginTop: 8 }}>
                                    {sent.key_drivers.map((kd, i) => (
                                        <div key={i} className="mono" style={{ fontSize: 10, color: STYLES.muted, padding: "3px 0", borderBottom: i < sent.key_drivers.length - 1 ? `1px solid ${STYLES.border}` : "none" }}>
                                            › {kd}
                                        </div>
                                    ))}
                                </div>
                            )}
                            {sent && (
                                <div style={{ marginTop: 10, textAlign: "center" }}>
                                    <span className="mono" style={{ fontSize: 10, color: STYLES.muted }}>Fear & Greed: </span>
                                    <span className="mono" style={{ fontSize: 11, color: STYLES.yellow }}>{sent.fear_greed_index}/100 — {sent.fear_greed_label}</span>
                                </div>
                            )}
                        </Card>
                    </div>

                    {/* BOTTOM ROW */}
                    <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 16, marginBottom: 16 }}>

                        {/* TECH INDICATORS */}
                        <Card>
                            <SectionTitle>Indicateurs Techniques</SectionTitle>
                            <div style={{ display: "grid", gridTemplateColumns: "1fr 1fr", gap: 8 }}>
                                <IndBox label="RSI (14)" value={tech ? tech.rsi.value.toFixed(1) : "—"} color={tech ? (tech.rsi.value < 35 ? STYLES.green : tech.rsi.value > 65 ? STYLES.red : STYLES.yellow) : STYLES.muted} />
                                <IndBox label="MACD" value={tech ? tech.macd.signal.toUpperCase() : "—"} color={tech ? (tech.macd.signal === "bullish" ? STYLES.green : tech.macd.signal === "bearish" ? STYLES.red : STYLES.yellow) : STYLES.muted} />
                                <IndBox label="Bollinger %B" value={tech ? (tech.bollinger.pct_b * 100).toFixed(0) + "%" : "—"} color={tech ? (tech.bollinger.pct_b < 0.2 ? STYLES.green : tech.bollinger.pct_b > 0.8 ? STYLES.red : STYLES.yellow) : STYLES.muted} />
                                <IndBox label="EMA Cross" value={tech ? (tech.ema_cross.golden_cross ? "GOLDEN ✓" : "DEATH ✗") : "—"} color={tech ? (tech.ema_cross.golden_cross ? STYLES.green : STYLES.red) : STYLES.muted} />
                                <IndBox label="Volume" value={tech ? tech.volume.ratio.toFixed(2) + "x" : "—"} color={tech?.volume.signal === "high" ? STYLES.yellow : STYLES.text} />
                                <IndBox label="Tendance" value={tech ? (tech.trend.strength + " " + tech.trend.direction).toUpperCase() : "—"} color={tech ? (tech.trend.direction === "bullish" ? STYLES.green : tech.trend.direction === "bearish" ? STYLES.red : STYLES.yellow) : STYLES.muted} />
                                <IndBox label="ATR (vol.)" value={tech ? tech.atr_pct.toFixed(2) + "%" : "—"} color={STYLES.accent} />
                                <IndBox label="Score Technique" value={tech ? (tech.tech_signal_score > 0 ? "+" : "") + tech.tech_signal_score.toFixed(3) : "—"} color={tech ? (tech.tech_signal_score > 0.1 ? STYLES.green : tech.tech_signal_score < -0.1 ? STYLES.red : STYLES.yellow) : STYLES.muted} />
                            </div>
                        </Card>

                        {/* RISK */}
                        <Card>
                            <SectionTitle>Gestion du Risque</SectionTitle>
                            {[
                                ["Action", risk?.risk_level === "FAIBLE" ? STYLES.green : risk?.risk_level === "ÉLEVÉ" ? STYLES.red : STYLES.yellow, risk ? sig?.action || "—" : "—"],
                                ["Prix d'entrée", STYLES.text, risk ? "$" + risk.entry_price.toLocaleString() : "—"],
                                ["Stop-Loss", STYLES.red, risk ? "$" + risk.stop_loss.toLocaleString() + ` (−${risk.sl_pct}%)` : "—"],
                                ["Take-Profit", STYLES.green, risk ? "$" + risk.take_profit.toLocaleString() + ` (+${risk.tp_pct}%)` : "—"],
                                ["Risk / Reward", STYLES.accent, risk ? risk.risk_reward_ratio.toFixed(2) + " : 1" : "—"],
                                ["Taille position", STYLES.text, risk ? risk.position_size.toFixed(5) + " unités" : "—"],
                                ["Capital risqué", STYLES.yellow, risk ? "$" + risk.capital_at_risk.toFixed(2) : "—"],
                                ["Niveau de risque", risk?.risk_level === "FAIBLE" ? STYLES.green : risk?.risk_level === "ÉLEVÉ" ? STYLES.red : STYLES.yellow, risk?.risk_level || "—"],
                            ].map(([k, c, v]) => (
                                <div key={k} style={{ display: "flex", justifyContent: "space-between", padding: "7px 0", borderBottom: `1px solid rgba(26,37,64,.4)` }}>
                                    <span className="mono" style={{ fontSize: 11, color: STYLES.muted }}>{k}</span>
                                    <span className="mono" style={{ fontSize: 12, fontWeight: 600, color: c }}>{v}</span>
                                </div>
                            ))}
                        </Card>
                    </div>

                    {/* AI MODELS */}
                    <Card style={{ marginBottom: 16 }}>
                        <SectionTitle>Contribution des Modèles IA</SectionTitle>
                        <div style={{ display: "grid", gridTemplateColumns: "repeat(4,1fr)", gap: 12 }}>
                            {modelList.map(({ label, key }) => {
                                const m = mods?.[key];
                                const col = m?.signal === "BUY" ? STYLES.green : m?.signal === "SELL" ? STYLES.red : STYLES.muted;
                                return (
                                    <div key={key} style={{ background: STYLES.surface, border: `1px solid ${STYLES.border}`, borderRadius: 6, padding: "12px 14px" }}>
                                        <div className="mono" style={{ fontSize: 9, color: STYLES.muted, textTransform: "uppercase", letterSpacing: 1, marginBottom: 6 }}>{label}</div>
                                        <div className="display" style={{ fontSize: 22, fontWeight: 700, color: col, marginBottom: 4 }}>{m?.signal || "—"}</div>
                                        <ProbBar label="Bull" pct={m ? m.bullish_prob * 100 : 0} color={STYLES.green} />
                                        <div className="mono" style={{ fontSize: 10, color: STYLES.muted }}>Conf: {m ? (m.confidence * 100).toFixed(0) + "%" : "—"}</div>
                                    </div>
                                );
                            })}
                        </div>
                    </Card>

                    {/* HISTORY */}
                    <Card>
                        <SectionTitle>Historique des Signaux</SectionTitle>
                        {history.length === 0 ? (
                            <div className="mono" style={{ textAlign: "center", color: STYLES.muted, padding: "18px 0", fontSize: 11 }}>
                                Aucun signal généré — lancez une analyse
                            </div>
                        ) : (
                            <div style={{ overflowX: "auto" }}>
                                <table style={{ width: "100%", borderCollapse: "collapse" }}>
                                    <thead>
                                        <tr>{["Heure", "Symbole", "Signal", "Bull%", "Bear%", "Conf.", "Sentiment", "Entrée", "SL", "TP"].map(h => (
                                            <th key={h} className="mono" style={{ fontSize: 9, color: STYLES.muted, textTransform: "uppercase", letterSpacing: 1, padding: "6px 10px", textAlign: "left", borderBottom: `1px solid ${STYLES.border}` }}>{h}</th>
                                        ))}</tr>
                                    </thead>
                                    <tbody>
                                        {history.map((h, i) => {
                                            const sc = h.signal?.action === "BUY" ? STYLES.green : h.signal?.action === "SELL" ? STYLES.red : STYLES.muted;
                                            const sentc = h.sentiment?.ssgm_score > 0 ? STYLES.green : h.sentiment?.ssgm_score < 0 ? STYLES.red : STYLES.muted;
                                            return (
                                                <tr key={i} style={{ borderBottom: `1px solid rgba(26,37,64,.4)` }}>
                                                    {[
                                                        [h.time, STYLES.muted],
                                                        [h.symbol, STYLES.text],
                                                        [h.signal?.action, sc],
                                                        [(h.signal?.bullish_probability * 100).toFixed(1) + "%", STYLES.green],
                                                        [(h.signal?.bearish_probability * 100).toFixed(1) + "%", STYLES.red],
                                                        [(h.signal?.confidence * 100).toFixed(0) + "%", STYLES.accent],
                                                        [h.sentiment?.label, sentc],
                                                        [h.risk_management?.entry_price ? "$" + h.risk_management.entry_price.toLocaleString() : "—", STYLES.text],
                                                        [h.risk_management?.stop_loss ? "$" + h.risk_management.stop_loss.toLocaleString() : "—", STYLES.red],
                                                        [h.risk_management?.take_profit ? "$" + h.risk_management.take_profit.toLocaleString() : "—", STYLES.green],
                                                    ].map(([val, col], j) => (
                                                        <td key={j} className="mono" style={{ fontSize: 11, color: col, padding: "7px 10px" }}>{val}</td>
                                                    ))}
                                                </tr>
                                            );
                                        })}
                                    </tbody>
                                </table>
                            </div>
                        )}
                    </Card>

                    {/* DISCLAIMER */}
                    <div className="mono" style={{ textAlign: "center", fontSize: 9, color: STYLES.muted, padding: "16px 0 8px", borderTop: `1px solid ${STYLES.border}`, marginTop: 20, letterSpacing: .5 }}>
                        ⚠ OUTIL ÉDUCATIF UNIQUEMENT — Les analyses sont générées par IA et ne constituent pas des conseils financiers. Ne jamais investir plus que ce que vous pouvez vous permettre de perdre.
                    </div>
                </div>
            </div>
        </>
    );
}