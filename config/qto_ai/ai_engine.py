"""
================================================================================
  QUANTUM TRADE ORACLE — Moteur IA v2.0  (Claude + OpenAI + Fallback)
  Fichier : qto_ai/ai_engine.py
================================================================================
  PRIORITÉ DE CONNEXION :
    1. Claude (Anthropic)  → clé ANTHROPIC_API_KEY dans .env
    2. OpenAI (GPT-4)      → clé OPENAI_API_KEY dans .env
    3. Moteur local        → zéro clé, 100% hors-ligne (ancien comportement)

  INSTALLATION :
    pip install anthropic openai python-dotenv

  CONFIGURATION :
    Crée un fichier  .env  à la racine du projet :
      ANTHROPIC_API_KEY=sk-ant-api03-XXXXXXXXXXXX   ← Claude (recommandé)
      OPENAI_API_KEY=sk-XXXXXXXXXXXX                ← OpenAI (optionnel)
================================================================================
"""

import os, json
from datetime import datetime
from pathlib import Path

# ── Chargement du .env ────────────────────────────────────────────────────────
try:
    from dotenv import load_dotenv
    load_dotenv(Path(__file__).parent.parent / ".env")
    load_dotenv(Path(__file__).parent / ".env")
except ImportError:
    pass

# ── Détection Anthropic (Claude) ──────────────────────────────────────────────
ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY","")
try:
    import anthropic
    ANTHROPIC_OK = bool(ANTHROPIC_KEY and ANTHROPIC_KEY.startswith("sk-ant"))
except ImportError:
    ANTHROPIC_OK = False

# ── Détection OpenAI ──────────────────────────────────────────────────────────
OPENAI_KEY = os.getenv("OPENAI_API_KEY","")
try:
    import openai
    OPENAI_OK = bool(OPENAI_KEY and OPENAI_KEY.startswith("sk-"))
except ImportError:
    OPENAI_OK = False

# ── Mode actif ────────────────────────────────────────────────────────────────
if ANTHROPIC_OK:
    MODE = "claude"
elif OPENAI_OK:
    MODE = "openai"
else:
    MODE = "local"

def is_configured() -> bool:
    return True   # le moteur local fonctionne toujours

def get_mode_label() -> str:
    return {"claude":"🤖 Claude (Anthropic)","openai":"🤖 GPT-4 (OpenAI)","local":"⚙️ Moteur Local"}.get(MODE,"⚙️ Local")


# ══════════════════════════════════════════════════════════════════════════════
#  SYSTÈME PROMPT — Personnalité de l'Oracle
# ══════════════════════════════════════════════════════════════════════════════
SYSTEM_PROMPT = """Tu es le **Quantum Trade Oracle**, un expert en trading algorithmique et analyse financière.

Ton rôle :
- Analyser des signaux de trading basés sur des indicateurs techniques (RSI, MACD, Bollinger, EMA, ATR, Stochastique)
- Interpréter des données de marché en temps réel
- Fournir des plans de trading précis avec entrée, stop-loss, take-profit
- Expliquer des concepts de trading de façon claire et pédagogique
- Évaluer le risque et la gestion du capital (règle des 2%)

Ton style :
- Réponses structurées avec titres markdown et tableaux
- Chiffres précis avec symboles $ et %
- Emojis pour la lisibilité (🟢 haussier, 🔴 baissier, ⚪ neutre, ✅ bon, ⚠️ attention, ❌ mauvais)
- Toujours mentionner le risque et avertir que c'est éducatif, pas du conseil financier
- Langue : français (sauf termes techniques anglais standard)

Règles importantes :
- Si les données de marché sont fournies dans le contexte, utilise-les précisément
- Ne pas inventer des chiffres — si tu ne sais pas, dis-le
- Toujours recommander un stop-loss, jamais de position sans protection
- Maximum 2% du capital par trade
- R/R minimum 2:1 recommandé"""


# ══════════════════════════════════════════════════════════════════════════════
#  CONSTRUCTEUR DE CONTEXTE
# ══════════════════════════════════════════════════════════════════════════════
def _build_context_message(context_data: dict) -> str:
    """Transforme les données du signal en contexte texte pour le LLM."""
    if not context_data:
        return ""
    sig = context_data.get("signal") or context_data
    if not sig or not sig.get("symbol"):
        return ""
    r = sig.get("risk_management", {})
    scores = sig.get("scores", {})
    tech = sig.get("technical_signals", {})
    models = sig.get("models", {})
    capital = context_data.get("capital", 10000)

    lines = [
        "=== DONNÉES DE MARCHÉ EN TEMPS RÉEL ===",
        f"Actif         : {sig.get('name', sig.get('symbol',''))} ({sig.get('symbol','')})",
        f"Prix actuel   : ${sig.get('price',0):,.4f}  ({sig.get('chg_1d',0):+.2f}% 24h)",
        f"Signal        : {sig.get('action','HOLD')}",
        f"Bull prob     : {sig.get('bullish_probability',0)*100:.1f}%",
        f"Bear prob     : {sig.get('bearish_probability',0)*100:.1f}%",
        f"Confiance IA  : {sig.get('ai_confidence',0)*100:.0f}%",
        f"Accord modèles: {sig.get('models_agreement',0)*100:.0f}%",
        f"RSI           : {sig.get('rsi',0):.1f}",
        f"Stoch         : {sig.get('stoch',50):.0f}",
        f"ATR %         : {sig.get('atr_pct',0):.2f}%",
        f"Vol ratio     : ×{sig.get('vol_ratio',1):.2f}",
        f"Score compo   : {scores.get('composite',0):+.4f}",
        "--- Plan de trade ---",
        f"Entrée        : ${r.get('entry_price',0):,.4f}",
        f"Stop-Loss     : ${r.get('stop_loss',0):,.4f}  (-{r.get('sl_pct',0):.2f}%)",
        f"Take-Profit   : ${r.get('take_profit',0):,.4f}  (+{r.get('tp_pct',0):.2f}%)",
        f"R/R           : {r.get('risk_reward_ratio',0):.2f}:1",
        f"Capital       : ${capital:,.0f}",
        f"Capital 2%    : ${capital*0.02:,.0f}",
        f"Position size : {r.get('position_size',0):.6f} unités",
    ]
    if tech:
        lines.append("--- Signaux techniques ---")
        for k, v in tech.items():
            lines.append(f"{k:13}: {v}")
    if models:
        lines.append("--- Modèles IA ---")
        for k, m in models.items():
            lines.append(f"{k:20}: {m.get('prediction','?')}  bull={m.get('bullish_prob',0)*100:.0f}%  conf={m.get('confidence',0)*100:.0f}%")
    lines.append("=== FIN DES DONNÉES ===")
    return "\n".join(lines)


# ══════════════════════════════════════════════════════════════════════════════
#  APPEL CLAUDE (ANTHROPIC)
# ══════════════════════════════════════════════════════════════════════════════
def _call_claude(question: str, context_msg: str, history: list) -> str:
    client = anthropic.Anthropic(api_key=ANTHROPIC_KEY)
    messages = []
    # Historique de conversation
    for msg in (history or [])[-6:]:   # max 6 derniers messages
        role = "user" if msg.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("content","")})
    # Message utilisateur avec contexte
    user_content = question
    if context_msg:
        user_content = f"{context_msg}\n\nQuestion : {question}"
    messages.append({"role": "user", "content": user_content})

    response = client.messages.create(
        model="claude-opus-4-6",
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        messages=messages,
    )
    return response.content[0].text


# ══════════════════════════════════════════════════════════════════════════════
#  APPEL OPENAI (GPT-4)
# ══════════════════════════════════════════════════════════════════════════════
def _call_openai(question: str, context_msg: str, history: list) -> str:
    client = openai.OpenAI(api_key=OPENAI_KEY)
    messages = [{"role": "system", "content": SYSTEM_PROMPT}]
    for msg in (history or [])[-6:]:
        role = "user" if msg.get("role") == "user" else "assistant"
        messages.append({"role": role, "content": msg.get("content","")})
    user_content = question
    if context_msg:
        user_content = f"{context_msg}\n\nQuestion : {question}"
    messages.append({"role": "user", "content": user_content})

    response = client.chat.completions.create(
        model="gpt-4o",
        messages=messages,
        max_tokens=2048,
        temperature=0.4,
    )
    return response.choices[0].message.content


# ══════════════════════════════════════════════════════════════════════════════
#  MOTEUR LOCAL (fallback sans clé API)
# ══════════════════════════════════════════════════════════════════════════════

RSI_OVERSOLD=30; RSI_OVERBOUGHT=70; VOL_HIGH=1.5; ATR_VOLATILE=5.0; ATR_CALM=2.0
RR_EXCELLENT=3.0; RR_GOOD=2.0; CONF_HIGH=0.75; CONF_MED=0.60; AGR_HIGH=0.75; AGR_MED=0.50

Q_TOPICS = {
    "buy":       ["acheter","buy","entrer","faut-il","signal","trade","long","investir"],
    "sell":      ["vendre","sell","sortir","fermer","short"],
    "risk":      ["risque","stop","perdre","protéger","capital","perte","gestion","sl","tp"],
    "technical": ["rsi","macd","bollinger","stoch","ema","indicateur","technique","graphique"],
    "forecast":  ["prévision","futur","demain","semaine","mois","hausse","baisse","cible"],
    "profit":    ["profit","gain","gagner","argent","million","capital","combien","rendement"],
    "report":    ["rapport","analyse","résumé","synthèse","bilan"],
    "crypto":    ["bitcoin","btc","ethereum","eth","crypto","solana","blockchain"],
    "forex":     ["forex","devise","eur","usd","gbp","jpy","monnaie","dollar"],
    "explain":   ["comment","expliquer","apprendre","tutoriel","signifie","légende"],
    "news":      ["news","actualité","nouvelles","presse","sentiment"],
}

def _classify(q: str) -> str:
    q = q.lower()
    scores = {t: sum(1 for kw in kws if kw in q) for t, kws in Q_TOPICS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"

def _rsi_i(r):
    if r<20:  return f"RSI {r:.0f} — SURVENTE EXTRÊME ⚡ Rebond imminent"
    if r<30:  return f"RSI {r:.0f} — Survente 🟢 Opportunité d'achat"
    if r<45:  return f"RSI {r:.0f} — Légèrement baissier"
    if r<55:  return f"RSI {r:.0f} — Zone neutre"
    if r<70:  return f"RSI {r:.0f} — Légèrement haussier"
    if r<80:  return f"RSI {r:.0f} — Surachat 🔴 Correction possible"
    return        f"RSI {r:.0f} — SURACHAT EXTRÊME ⚠️"

def _vol_i(v):
    if v>3.0: return f"Volume ×{v:.1f} 🔥 EXCEPTIONNEL"
    if v>2.0: return f"Volume ×{v:.1f} 📊 Très élevé"
    if v>1.5: return f"Volume ×{v:.1f} 📈 Élevé"
    return       f"Volume ×{v:.2f} — Normal"

def _score_label(s):
    if s>.4:   return "FORTEMENT HAUSSIER 🚀"
    if s>.15:  return "HAUSSIER MODÉRÉ 📈"
    if s>0:    return "LÉGÈREMENT HAUSSIER"
    if s<-.4:  return "FORTEMENT BAISSIER 📉"
    if s<-.15: return "BAISSIER MODÉRÉ 🔻"
    if s<0:    return "LÉGÈREMENT BAISSIER"
    return "NEUTRE ➡️"

def _setup_q(rr,conf,agr,atr_pct,vol_r):
    score=0; notes=[]
    if rr>=RR_EXCELLENT:  score+=30; notes.append(f"✅ Excellent R/R {rr:.2f}:1")
    elif rr>=RR_GOOD:     score+=20; notes.append(f"✅ Bon R/R {rr:.2f}:1")
    else:                            notes.append(f"⚠️ R/R faible {rr:.2f}:1")
    if conf>=CONF_HIGH:   score+=25; notes.append(f"✅ Confiance {conf*100:.0f}% — haute")
    elif conf>=CONF_MED:  score+=15; notes.append(f"✅ Confiance {conf*100:.0f}% — correcte")
    else:                            notes.append(f"⚠️ Confiance {conf*100:.0f}% — faible")
    if agr>=AGR_HIGH:     score+=25; notes.append(f"✅ Accord {agr*100:.0f}% — consensus fort")
    elif agr>=AGR_MED:    score+=12; notes.append(f"⚠️ Accord {agr*100:.0f}% — partiel")
    else:                            notes.append(f"❌ Accord {agr*100:.0f}% — désaccord")
    if atr_pct<ATR_CALM:  score+=10; notes.append(f"✅ Volatilité {atr_pct:.2f}% — faible")
    elif atr_pct>ATR_VOLATILE:       notes.append(f"⚠️ Volatilité {atr_pct:.2f}% — élevée")
    else:                 score+=5;  notes.append(f"✅ Volatilité {atr_pct:.2f}% — normale")
    if vol_r>VOL_HIGH:    score+=10; notes.append(f"✅ Volume ×{vol_r:.2f} — confirmé")
    lbl=("✅ EXCELLENT SETUP" if score>=80 else "✅ BON SETUP" if score>=60
         else "⚠️ SETUP MOYEN" if score>=40 else "❌ SETUP FAIBLE")
    return score,lbl,notes

def _extract(ctx):
    sig=ctx.get("signal") or ctx
    if not sig: return {}
    r=sig.get("risk_management",{})
    return dict(
        name=sig.get("name",sig.get("symbol","")), symbol=sig.get("symbol",""),
        price=sig.get("price",0), chg=sig.get("chg_1d",0),
        action=sig.get("action","HOLD"),
        bull=sig.get("bullish_probability",.5), bear=sig.get("bearish_probability",.5),
        conf=sig.get("ai_confidence",0), agr=sig.get("models_agreement",0),
        rsi=sig.get("rsi",50), stoch=sig.get("stoch",50), vol_r=sig.get("vol_ratio",1),
        atr_pct=sig.get("atr_pct",0), score=sig.get("scores",{}).get("composite",0),
        tech=sig.get("technical_signals",{}),
        entry=r.get("entry_price",sig.get("price",0)),
        sl=r.get("stop_loss",0), tp=r.get("take_profit",0),
        rr=r.get("risk_reward_ratio",0), sl_pct=r.get("sl_pct",0), tp_pct=r.get("tp_pct",0),
        pos_size=r.get("position_size",0), pos_val=r.get("position_value",0),
        risk_amt=r.get("capital_at_risk",0), atr=r.get("atr",0),
        capital=ctx.get("capital",10000),
        trend=_score_label(sig.get("scores",{}).get("composite",0)),
    )

def _db(d):
    if not d: return ""
    col="🟢" if d["chg"]>=0 else "🔴"
    act={"BUY":"🟢 BUY","SELL":"🔴 SELL","HOLD":"⚪ HOLD"}.get(d["action"],d["action"])
    return (f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
            f"📊 **{d['name']} ({d['symbol']})** · ${d['price']:,.4f} {col}{d['chg']:+.2f}%\n"
            f"🎯 **{act}** · {d['trend']}\n"
            f"📈 Bull {d['bull']*100:.1f}% · Conf {d['conf']*100:.0f}% · Accord {d['agr']*100:.0f}%\n"
            f"📊 RSI {d['rsi']:.1f} · ATR {d['atr_pct']:.2f}% · Vol ×{d['vol_r']:.2f}\n"
            f"🛡️ Entry ${d['entry']:,.4f} · SL ${d['sl']:,.4f} · TP ${d['tp']:,.4f} · R/R {d['rr']:.2f}:1\n"
            f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

def _local_response(question: str, context_data: dict, history: list) -> str:
    topic = _classify(question)
    d = _extract(context_data) if context_data else {}
    db = _db(d) if d else ""
    capital = d.get("capital",10000) if d else 10000

    if topic == "buy":
        if not d: return "🔍 Lance d'abord une **analyse** (bouton ANALYSER)."
        sc,lbl,notes = _setup_q(d["rr"],d["conf"],d["agr"],d["atr_pct"],d["vol_r"])
        return f"""## 🎯 Analyse d'Entrée — {d['name']}{db}
### {lbl} — Score {sc}/100
{chr(10).join("- "+n for n in notes)}
### Plan de Trade
| Niveau | Prix | % |
|--------|------|---|
| ➜ Entrée | **${d['entry']:,.4f}** | — |
| 🛑 Stop-Loss | **${d['sl']:,.4f}** | -{d['sl_pct']:.2f}% |
| 🎯 Take-Profit | **${d['tp']:,.4f}** | +{d['tp_pct']:.2f}% |
| R/R | **{d['rr']:.2f}:1** | {'✅' if d['rr']>=2 else '⚠️'} |
Capital risqué : **${d['risk_amt']:,.2f}** (2% de ${capital:,.0f})
### Indicateurs
- {_rsi_i(d['rsi'])} · {_vol_i(d['vol_r'])}
⚠️ *Outil éducatif — pas un conseil financier.*"""

    if topic == "risk":
        r2=capital*0.02
        base=f"""## 🛡️ Gestion du Risque{db}
**Règle d'or : Maximum 2% = ${r2:,.0f} de perte par trade**
| R/R | Win Rate min | Note |
|-----|-------------|------|
| 3:1 | 25% | ✅ Excellent |
| 2:1 | 34% | ✅ Bon |
| 1.5:1| 40% | ⚠️ Limite |
**5 erreurs fatales :** ❌ Pas de SL · ❌ Position trop grande · ❌ Moyenner à la baisse · ❌ FOMO · ❌ Déplacer le SL"""
        if d:
            sc,lbl,notes=_setup_q(d["rr"],d["conf"],d["agr"],d["atr_pct"],d["vol_r"])
            base+=f"\n**Trade actuel :** {lbl} ({sc}/100)\n"+"".join(f"- {n}\n" for n in notes)
        return base

    if topic == "technical":
        base=f"## 📊 Analyse Technique{db}"
        if d:
            base+=f"\n- {_rsi_i(d['rsi'])}\n- {_vol_i(d['vol_r'])}"
            for k,v in d.get("tech",{}).items(): base+=f"\n- **{k}** : {v}"
        base+="\n\n**Références :** RSI<30 survente · MACD croisement = signal · BB bande basse = rebond · EMA 9>20>50 = tendance haussière"
        return base

    if topic == "profit":
        return f"""## 💰 Projections — ${capital:,.0f}
| Scénario | 1 an | 3 ans |
|----------|------|-------|
| +15%/an | ${capital*1.15:,.0f} | ${capital*(1.15**3):,.0f} |
| +30%/an | ${capital*1.30:,.0f} | ${capital*(1.30**3):,.0f} |
| +60%/an | ${capital*1.60:,.0f} | ${capital*(1.60**3):,.0f} |
⚠️ *Estimations — aucune garantie. 70-80% des traders perdent.*"""

    if topic == "report":
        if not d: return "🔍 Lance d'abord une **analyse**."
        sc,lbl,notes=_setup_q(d["rr"],d["conf"],d["agr"],d["atr_pct"],d["vol_r"])
        tech_str="\n".join(f"- **{k}** : {v}" for k,v in d.get("tech",{}).items()) or "—"
        return f"""# 📊 RAPPORT COMPLET — {d['name']} ({datetime.now().strftime('%d/%m/%Y %H:%M')}){db}
## Signal : **{d['action']}** · {d['trend']}
## Plan
| Entrée | SL | TP | R/R |
|--------|----|----|-----|
| ${d['entry']:,.4f} | ${d['sl']:,.4f} | ${d['tp']:,.4f} | {d['rr']:.2f}:1 |
## Technique
{tech_str}
- {_rsi_i(d['rsi'])} · {_vol_i(d['vol_r'])}
## Setup : **{lbl} ({sc}/100)**
{chr(10).join("- "+n for n in notes)}
⚠️ *Outil éducatif · Pas un conseil financier.*"""

    # Général
    si = (f"**{d.get('action','?')}** · Bull {d.get('bull',0)*100:.1f}% · RSI {d.get('rsi',0):.1f}" if d else
          "Lance **ANALYSER** pour un signal précis.")
    return f"""## ⬡ Oracle IA — {get_mode_label()}{db}
Signal actuel : {si}
Posez une question précise :
🎯 *"Faut-il acheter ?"* · 🛡️ *"Quel stop-loss ?"* · 📊 *"Analyse RSI"*
📋 *"Génère un rapport complet"* · 💰 *"Projections de profit"*
⚠️ *Moteur local — ajoute une clé API dans .env pour utiliser Claude ou GPT-4*"""


# ══════════════════════════════════════════════════════════════════════════════
#  POINT D'ENTRÉE PRINCIPAL
# ══════════════════════════════════════════════════════════════════════════════
def ask_gpt(question: str, context_data: dict = None, history: list = None) -> str:
    """
    Appelle le meilleur moteur disponible :
      - Claude  si ANTHROPIC_API_KEY configurée
      - GPT-4   si OPENAI_API_KEY configurée
      - Local   sinon (fallback hors ligne)
    """
    context_msg = _build_context_message(context_data) if context_data else ""

    if MODE == "claude":
        try:
            return _call_claude(question, context_msg, history or [])
        except Exception as e:
            return f"⚠️ Erreur Claude API : {e}\n\n{_local_response(question, context_data, history)}"

    if MODE == "openai":
        try:
            return _call_openai(question, context_msg, history or [])
        except Exception as e:
            return f"⚠️ Erreur OpenAI API : {e}\n\n{_local_response(question, context_data, history)}"

    return _local_response(question, context_data, history or [])


# ══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS UTILITAIRES (interface dashboard)
# ══════════════════════════════════════════════════════════════════════════════
def generate_report(sig: dict, df, news: list, capital: float) -> str:
    return ask_gpt("Génère un rapport d'analyse complet détaillé",
                   {"signal": sig, "capital": capital}, None)


def analyze_news_gpt(news: list, symbol: str, sig: dict = None) -> str:
    if not news:
        return "Aucune actualité disponible."
    BW=["bullish","rally","surge","gain","rise","pump","buy","ath","positive","growth"]
    SW=["crash","drop","fall","sell","dump","fear","correction","negative","loss"]
    scores=[]; bulls=0; bears=0
    for a in news[:15]:
        txt=(a.get("title","")+a.get("description","")).lower()
        b=sum(1 for w in BW if w in txt); s=sum(1 for w in SW if w in txt)
        if b+s>0:
            sc=(b-s)/(b+s); scores.append(sc)
            if sc>0.1: bulls+=1
            elif sc<-0.1: bears+=1
    avg=sum(scores)/len(scores) if scores else 0
    neutral=len(scores)-bulls-bears
    sentiment="🟢 BULLISH" if avg>0.1 else "🔴 BEARISH" if avg<-0.1 else "⚪ NEUTRE"
    sig_txt=f"\n**Signal technique :** {sig.get('action','HOLD')} · RSI {sig.get('rsi',50):.0f}" if sig else ""
    top="".join(f"{i}. {a.get('title','')[:90]}\n" for i,a in enumerate(news[:5],1))
    consistent=(avg>0.1 and sig and sig.get("action")=="BUY") or (avg<-0.1 and sig and sig.get("action")=="SELL")
    return f"""## 📰 Analyse News — {symbol}{sig_txt}
### Sentiment : {sentiment} — SSGM {avg:+.3f}
🟢 Bullish {bulls} · 🔴 Bearish {bears} · ⚪ Neutres {neutral} · Total {len(news)} articles
### Top Articles
{top}
{'✅ News confirment le signal.' if consistent else '⚠️ News divergent du signal — prudence.'}"""


def risk_advice_gpt(sig: dict, capital: float, portfolio: list = None) -> str:
    return ask_gpt("Donne-moi une analyse de risque complète pour ce trade",
                   {"signal": sig, "capital": capital}, None)
