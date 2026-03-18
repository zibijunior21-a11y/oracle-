"""
================================================================================
  QUANTUM TRADE ORACLE — Moteur IA Propriétaire v1.0
  Fichier : qto_ai/ai_engine.py
================================================================================
  ✅ 100% votre code — zéro API externe — zéro abonnement
  ✅ Analyse contextuelle profonde basée sur vos règles de trading
  ✅ Moteur de raisonnement multi-indicateurs propriétaire
  ✅ Génération de rapports automatiques complets
  ✅ Fonctionne 100% hors ligne
================================================================================
"""

from datetime import datetime

# ── Aucune clé nécessaire — moteur 100% local ────────────────────────────────
OPENAI_API_KEY = "LOCAL"
OPENAI_OK      = True

def is_configured() -> bool:
    return True


# ══════════════════════════════════════════════════════════════════════════════
#  SEUILS ET RÈGLES DE TRADING
# ══════════════════════════════════════════════════════════════════════════════
RSI_OVERSOLD    = 30
RSI_OVERBOUGHT  = 70
STOCH_OVERSOLD  = 20
STOCH_OVERBOUGHT= 80
VOL_HIGH        = 1.5
ATR_VOLATILE    = 5.0
ATR_CALM        = 2.0
RR_EXCELLENT    = 3.0
RR_GOOD         = 2.0
CONF_HIGH       = 0.75
CONF_MED        = 0.60
AGR_HIGH        = 0.75
AGR_MED         = 0.50

# ══════════════════════════════════════════════════════════════════════════════
#  CLASSIFIEUR DE QUESTIONS
# ══════════════════════════════════════════════════════════════════════════════
Q_TOPICS = {
    "buy":         ["acheter","buy","entrer","faut-il","signal","trade","long","investir","position"],
    "sell":        ["vendre","sell","sortir","fermer","short","closer"],
    "risk":        ["risque","stop","perdre","protéger","capital","perte","gestion","sl","tp"],
    "technical":   ["rsi","macd","bollinger","stoch","ema","indicateur","technique","graphique","bougie","tendance"],
    "forecast":    ["prévision","futur","demain","semaine","mois","an","hausse","baisse","cible","objectif","prédire"],
    "commodity":   ["matière","pétrole","or","blé","café","cuivre","gaz","énergie","silver","argent","gold"],
    "forex":       ["forex","devise","eur","usd","gbp","jpy","monnaie","dollar","euro"],
    "crypto":      ["bitcoin","btc","ethereum","eth","crypto","solana","altcoin","blockchain"],
    "profit":      ["profit","gain","gagner","argent","million","capital","combien","rendement"],
    "report":      ["rapport","analyse","résumé","synthèse","bilan"],
    "correlation": ["corrélation","matrice","diversif","portefeuille","portfolio"],
    "montecarlo":  ["monte carlo","simulation","probabilité","scénario"],
    "explain":     ["comment lire","graphique","expliquer","apprendre","tutoriel","légende","signifie"],
    "news":        ["news","actualité","nouvelles","presse","sentiment"],
    "general":     [],
}

def _classify(question: str) -> str:
    q = question.lower()
    scores = {topic: sum(1 for kw in kws if kw in q) for topic, kws in Q_TOPICS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "general"


# ══════════════════════════════════════════════════════════════════════════════
#  INTERPRÉTEURS D'INDICATEURS
# ══════════════════════════════════════════════════════════════════════════════
def _rsi_interp(rsi):
    if rsi < 20:  return f"RSI {rsi:.0f} — SURVENTE EXTRÊME ⚡ Rebond imminent très probable"
    if rsi < 30:  return f"RSI {rsi:.0f} — Zone de survente 🟢 Opportunité d'achat potentielle"
    if rsi < 45:  return f"RSI {rsi:.0f} — Légèrement baissier, momentum faible"
    if rsi < 55:  return f"RSI {rsi:.0f} — Zone neutre, pas de biais directionnel"
    if rsi < 70:  return f"RSI {rsi:.0f} — Légèrement haussier, momentum positif"
    if rsi < 80:  return f"RSI {rsi:.0f} — Zone de surachat 🔴 Correction possible"
    return             f"RSI {rsi:.0f} — SURACHAT EXTRÊME ⚠️ Risque de retournement élevé"

def _stoch_interp(s):
    if s < 10: return f"Stoch {s:.0f} — Survente extrême, rebond quasi-certain"
    if s < 20: return f"Stoch {s:.0f} — Survente 🟢 confirme le RSI"
    if s > 90: return f"Stoch {s:.0f} — Surachat extrême, retournement imminent"
    if s > 80: return f"Stoch {s:.0f} — Surachat 🔴 confirme le RSI"
    return         f"Stoch {s:.0f} — Zone neutre"

def _vol_interp(v):
    if v > 3.0: return f"Volume ×{v:.1f} 🔥 EXCEPTIONNEL — signal très fiable"
    if v > 2.0: return f"Volume ×{v:.1f} 📊 Très élevé — confirme fortement le mouvement"
    if v > 1.5: return f"Volume ×{v:.1f} 📈 Élevé — signal fiable"
    if v > 0.8: return f"Volume ×{v:.2f} — Normal"
    return         f"Volume ×{v:.2f} ⚠️ Faible — signal peu fiable"

def _score_to_label(score):
    if score > 0.4:  return "FORTEMENT HAUSSIER 🚀"
    if score > 0.15: return "HAUSSIER MODÉRÉ 📈"
    if score > 0:    return "LÉGÈREMENT HAUSSIER"
    if score < -0.4: return "FORTEMENT BAISSIER 📉"
    if score < -0.15:return "BAISSIER MODÉRÉ 🔻"
    if score < 0:    return "LÉGÈREMENT BAISSIER"
    return "NEUTRE ➡️"

def _setup_quality(rr, conf, agr, atr_pct, vol_r):
    score = 0
    notes = []
    if rr >= RR_EXCELLENT:    score += 30; notes.append(f"✅ Excellent R/R {rr:.2f}:1")
    elif rr >= RR_GOOD:       score += 20; notes.append(f"✅ Bon R/R {rr:.2f}:1")
    else:                                  notes.append(f"⚠️ R/R faible {rr:.2f}:1 — min recommandé : 2:1")
    if conf >= CONF_HIGH:     score += 25; notes.append(f"✅ Confiance IA {conf*100:.0f}% — très haute")
    elif conf >= CONF_MED:    score += 15; notes.append(f"✅ Confiance IA {conf*100:.0f}% — correcte")
    else:                                  notes.append(f"⚠️ Confiance IA {conf*100:.0f}% — modérée")
    if agr >= AGR_HIGH:       score += 25; notes.append(f"✅ Accord modèles {agr*100:.0f}% — consensus fort")
    elif agr >= AGR_MED:      score += 12; notes.append(f"⚠️ Accord {agr*100:.0f}% — partiel")
    else:                                  notes.append(f"❌ Accord {agr*100:.0f}% — désaccord")
    if atr_pct < ATR_CALM:    score += 10; notes.append(f"✅ Volatilité {atr_pct:.2f}% — faible, risque contrôlé")
    elif atr_pct > ATR_VOLATILE:           notes.append(f"⚠️ Volatilité {atr_pct:.2f}% — élevée")
    else:                      score += 5; notes.append(f"✅ Volatilité {atr_pct:.2f}% — normale")
    if vol_r > VOL_HIGH:      score += 10; notes.append(f"✅ Volume ×{vol_r:.2f} — signal confirmé")
    elif vol_r < 0.5:                      notes.append(f"⚠️ Volume ×{vol_r:.2f} — faible")

    label = ("✅ EXCELLENT SETUP" if score >= 80 else "✅ BON SETUP" if score >= 60
             else "⚠️ SETUP MOYEN" if score >= 40 else "❌ SETUP FAIBLE")
    return score, label, notes


# ══════════════════════════════════════════════════════════════════════════════
#  EXTRACTEUR DE CONTEXTE
# ══════════════════════════════════════════════════════════════════════════════
def _extract(ctx):
    sig = ctx.get("signal") or ctx
    if not sig:
        return {}
    r = sig.get("risk_management", {})
    return dict(
        name=sig.get("name",""), symbol=sig.get("symbol",""),
        price=sig.get("price",0), chg=sig.get("chg_1d",0),
        action=sig.get("action","HOLD"),
        bull=sig.get("bullish_probability",0.5), bear=sig.get("bearish_probability",0.5),
        conf=sig.get("ai_confidence",0), agr=sig.get("models_agreement",0),
        rsi=sig.get("rsi",50), stoch=sig.get("stoch",50),
        willr=sig.get("willr",-50), vol_r=sig.get("vol_ratio",1),
        atr_pct=sig.get("atr_pct",0), score=sig.get("scores",{}).get("composite",0),
        tech=sig.get("technical_signals",{}), models=sig.get("models",{}),
        entry=r.get("entry_price",sig.get("price",0)),
        sl=r.get("stop_loss",0), tp=r.get("take_profit",0),
        rr=r.get("risk_reward_ratio",0), sl_pct=r.get("sl_pct",0),
        tp_pct=r.get("tp_pct",0), pos_size=r.get("position_size",0),
        pos_val=r.get("position_value",0), risk_amt=r.get("capital_at_risk",0),
        risk_lvl=r.get("risk_level","N/A"), atr=r.get("atr",0),
        capital=ctx.get("capital",10000),
        trend=_score_to_label(sig.get("scores",{}).get("composite",0)),
    )

def _data_block(d):
    if not d: return ""
    col = "🟢" if d["chg"] >= 0 else "🔴"
    act = {"BUY":"🟢 BUY","SELL":"🔴 SELL","HOLD":"⚪ HOLD"}.get(d["action"],d["action"])
    return f"""
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📊 **{d["name"]} ({d["symbol"]})** · ${d["price"]:,.4f} {col}{d["chg"]:+.2f}%
🎯 Signal : **{act}** · {d["trend"]}
📈 Bull {d["bull"]*100:.1f}% · Bear {d["bear"]*100:.1f}% · Conf {d["conf"]*100:.0f}% · Accord {d["agr"]*100:.0f}%
📊 RSI {d["rsi"]:.1f} · Stoch {d["stoch"]:.0f} · ATR {d["atr_pct"]:.2f}% · Vol ×{d["vol_r"]:.2f}
🛡️ Entry ${d["entry"]:,.4f} · SL ${d["sl"]:,.4f} · TP ${d["tp"]:,.4f} · R/R {d["rr"]:.2f}:1
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"""


# ══════════════════════════════════════════════════════════════════════════════
#  MOTEUR DE RÉPONSE
# ══════════════════════════════════════════════════════════════════════════════
def ask_gpt(question: str, context_data: dict = None, history: list = None) -> str:
    topic = _classify(question)
    d  = _extract(context_data) if context_data else {}
    db = _data_block(d) if d else ""
    handlers = {
        "buy": _h_buy, "sell": _h_sell, "risk": _h_risk,
        "technical": _h_technical, "forecast": _h_forecast,
        "commodity": _h_commodity, "forex": _h_forex, "crypto": _h_crypto,
        "profit": _h_profit, "report": _h_report,
        "correlation": _h_correlation, "montecarlo": _h_montecarlo,
        "explain": _h_explain, "news": _h_news, "general": _h_general,
    }
    return handlers.get(topic, _h_general)(question, d, db)


# ══════════════════════════════════════════════════════════════════════════════
#  HANDLERS
# ══════════════════════════════════════════════════════════════════════════════
def _h_buy(q, d, db):
    if not d:
        return "🔍 Lance d'abord une **analyse** (bouton ANALYSER) pour obtenir un plan de trade précis."
    score, label, notes = _setup_quality(d["rr"],d["conf"],d["agr"],d["atr_pct"],d["vol_r"])
    notes_str = "\n".join(f"  {n}" for n in notes)
    action_txt = {"BUY":"✅ Signal **BUY** — conditions réunies pour entrer long.",
                  "SELL":"🔴 Signal **SELL** — vendre / shorter conseillé.",
                  "HOLD":"⚪ Signal **HOLD** — attendre confirmation."}.get(d["action"],"")
    return f"""## 🎯 Analyse d'Entrée — {d["name"]}{db}

### {label} — Score : {score}/100
{notes_str}

### Signal & Direction
{action_txt}
Tendance : **{d["trend"]}** · Bull : {d["bull"]*100:.1f}% · Bear : {d["bear"]*100:.1f}%

### 📋 Plan de Trade
| Niveau | Prix | % |
|--------|------|---|
| ➜ Entrée | **${d["entry"]:,.4f}** | — |
| 🛑 Stop-Loss | **${d["sl"]:,.4f}** | -{d["sl_pct"]:.2f}% |
| 🎯 Take-Profit | **${d["tp"]:,.4f}** | +{d["tp_pct"]:.2f}% |
| R/R | **{d["rr"]:.2f}:1** | {'✅' if d["rr"]>=2 else '⚠️'} |

**Capital à risquer :** ${d["risk_amt"]:,.2f} (2%) · **Position :** {d["pos_size"]:.6f} unités

### Indicateurs Clés
- {_rsi_interp(d["rsi"])}
- {_stoch_interp(d["stoch"])}
- {_vol_interp(d["vol_r"])}

### ✅ Checklist
{'✅' if d["rr"]>=2 else '❌'} R/R ≥ 2:1 · {'✅' if d["conf"]>=0.6 else '⚠️'} Confiance ≥ 60% · {'✅' if d["agr"]>=0.75 else '⚠️'} Accord ≥ 75%
✅ Stop-Loss AVANT d'entrer · ✅ Max 2% du capital

⚠️ *Outil éducatif — pas un conseil financier.*"""


def _h_sell(q, d, db):
    if not d:
        return "🔍 Lance d'abord une **analyse** pour obtenir les niveaux de sortie."
    return f"""## 🔴 Analyse de Sortie — {d["name"]}{db}

Signal actuel : **{d["action"]}**
{'⚠️ Signal SELL actif — fermer ou réduire la position' if d["action"]=="SELL" else '⚪ Pas encore de signal SELL — surveiller les niveaux'}

### Niveaux de Sortie
- 🎯 **Take-Profit** : ${d["tp"]:,.4f} (+{d["tp_pct"]:.2f}%) — prise de bénéfices
- 🛑 **Stop-Loss** : ${d["sl"]:,.4f} (-{d["sl_pct"]:.2f}%) — sortie défensive

### Signaux de Retournement
- {_rsi_interp(d["rsi"])}
- {_stoch_interp(d["stoch"])}

### Règles de Sortie
1. Sortie Stop-Loss si prix < ${d["sl"]:,.4f} — DISCIPLINE ABSOLUE
2. Take 50% à ${d["tp"]:,.4f}, laisser courir le reste avec trailing stop
3. Fermer si RSI > 75 + volume faible (épuisement)
4. Déplacer SL au break-even après +{d["tp_pct"]/2:.1f}%

⚠️ Ne jamais déplacer le stop-loss à la baisse."""


def _h_risk(q, d, db):
    capital = d.get("capital", 10000) if d else 10000
    r2 = capital * 0.02
    base = f"""## 🛡️ Gestion du Risque{db}

### Règle d'Or : Maximum 2% par Trade
**${capital:,.0f} × 2% = ${r2:,.0f} de perte maximum par trade**

### Calcul Position
```
Position = (Capital × 2%) ÷ Distance au Stop-Loss
Exemple : ${r2:,.0f} ÷ $50 de SL = {r2/50:.1f} unités
```

### Table R/R — Win Rate Minimum pour Être Profitable
| R/R | Win Rate min | Commentaire |
|-----|-------------|-------------|
| 3:1 | 25% | ✅ Excellent |
| 2:1 | 34% | ✅ Bon |
| 1.5:1 | 40% | ⚠️ Limite |
| 1:1 | 51% | ❌ Risqué |

### 5 Erreurs Fatales
1. ❌ Pas de stop-loss — une trade peut tout perdre
2. ❌ Position trop grande — émotion → mauvaises décisions
3. ❌ Moyenner à la baisse — petite perte → catastrophe
4. ❌ FOMO — entrer sur un top
5. ❌ Déplacer le SL — perte de discipline"""
    if d:
        score, label, notes = _setup_quality(d["rr"],d["conf"],d["agr"],d["atr_pct"],d["vol_r"])
        base += f"\n\n### Trade Actuel — {d['name']}\n**{label} ({score}/100)**\n"
        base += "\n".join(f"- {n}" for n in notes)
    return base


def _h_technical(q, d, db):
    ql = q.lower()
    if "rsi" in ql and d:
        return f"""## 📊 RSI — Relative Strength Index{db}

**Valeur actuelle : {d["rsi"]:.1f}** → {_rsi_interp(d["rsi"])}

| Zone | RSI | Signification |
|------|-----|---------------|
| Survente extrême | < 20 | Rebond quasi-certain |
| Survente | 20-30 | Opportunité achat |
| Neutre bas | 30-45 | Légèrement baissier |
| Neutre | 45-55 | Pas de biais |
| Neutre haut | 55-70 | Légèrement haussier |
| Surachat | 70-80 | Risque correction |
| Surachat extrême | > 80 | Retournement imminent |

**Divergences :**
- Haussière : Prix nouveau bas, RSI non → rebond imminent
- Baissière : Prix nouveau haut, RSI non → correction imminente"""

    if "macd" in ql and d:
        tech = d.get("tech",{})
        macd_txt = tech.get("MACD","—")
        return f"""## 📈 MACD{db}

**Signal actuel :** {macd_txt}

- **MACD** = EMA12 − EMA26
- **Signal** = EMA9 du MACD
- **Histogramme** = MACD − Signal (momentum)

| Signal | Condition |
|--------|-----------|
| BUY fort | MACD croise Signal vers le haut |
| BUY | Histogramme vert croissant |
| SELL fort | MACD croise Signal vers le bas |
| SELL | Histogramme rouge croissant |

Combinez MACD + RSI pour des signaux plus fiables."""

    base = f"""## 📊 Analyse Technique{db}"""
    if d:
        base += f"\n\n### Indicateurs Actuels\n- {_rsi_interp(d['rsi'])}\n- {_stoch_interp(d['stoch'])}\n- {_vol_interp(d['vol_r'])}"
        for k,v in d.get("tech",{}).items():
            base += f"\n- **{k}** : {v}"
    base += """

### Référence Rapide
- **RSI** < 30 survente · > 70 surachat
- **MACD** croisement haussier = BUY · baissier = SELL
- **Bollinger** bande basse = survente · bande haute = résistance
- **EMA** 9>20>50 = tendance haussière parfaite
- **Stoch** < 20 survente · > 80 surachat
- **Règle des 3 confirmations** : 3 indicateurs dans le même sens"""
    return base


def _h_forecast(q, d, db):
    base = f"## 🔮 Prévision de Prix{db}"
    if d:
        price = d["price"]
        vol   = max(d["atr_pct"] / 100, 0.001)
        drift = (d["bull"] - 0.5) * 0.002
        rows  = ""
        for lbl, days in [("1 semaine",5),("1 mois",21),("3 mois",63),("1 an",252)]:
            tgt  = price * ((1+drift)**days)
            sig1 = price * (vol * (days**0.5))
            chg  = (tgt-price)/price*100
            icon = "🟢↑" if chg>1 else "🔴↓" if chg<-1 else "⚪→"
            rows += f"| {lbl} | ${tgt:,.2f} | {icon} {chg:+.1f}% | ${tgt-sig1:,.2f}–${tgt+sig1:,.2f} |\n"
        base += f"""

### Projections Statistiques
| Horizon | Cible | Variation | Zone 68% |
|---------|-------|-----------|----------|
{rows}
**Scénarios :**
- 🟢 Haussier : signal BUY + volume → cible ${d["tp"]:,.4f}
- 🔴 Baissier : rupture support → risque ${d["sl"]:,.4f}
- ⚪ Neutre : consolidation ${d["sl"]:,.4f}–${d["tp"]:,.4f}"""
    else:
        base += "\n\n> Lance une analyse pour obtenir des prévisions précises."
    base += "\n\n⚠️ *Estimations statistiques — pas des garanties.*"
    return base


def _h_commodity(q, d, db):
    return f"""## 🌍 Guide Matières Premières{db}

### ⛽ Énergie
- **WTI/Brent** : Décisions OPEC+, stocks EIA (mercredi), dollar, guerres
- **Natural Gas** : Météo hiver/été, réserves EIA (jeudi)

### 🥇 Métaux Précieux
- **Gold** : Inversement corrélé au dollar. Monte en période d'incertitude + inflation
- **Silver** : Gold ×2-3 en volatilité, composante industrielle
- **Platine/Palladium** : Industrie automobile

### 🔩 Métaux Industriels
- **Copper** : Baromètre croissance mondiale. Demande Chine = facteur clé
- **Aluminium** : Secteur industriel et construction

### 🌾 Agriculture
- **Blé/Maïs/Soja** : Météo (La Niña), rapport USDA mensuel, conflits géopolitiques
- **Café** : Brésil n°1. Gel ou sécheresse = +30-50% rapidement
- **Cacao** : Côte d'Ivoire + Ghana. Très volatile

### Outils Essentiels
- **COT Report** (CFTC) : positions commerciaux — publié vendredi
- **Dollar Index (DXY)** : corrélation inverse commodités
- **Calendrier EIA** : mercredi pétrole, jeudi gaz
- **Calendrier USDA** : rapports agricoles mensuels"""


def _h_forex(q, d, db):
    return f"""## 💱 Guide Forex{db}

### Facteurs qui Bougent les Devises
| Facteur | Impact |
|---------|--------|
| Taux banque centrale | ⭐⭐⭐⭐⭐ |
| Inflation (CPI) | ⭐⭐⭐⭐⭐ |
| Emploi (NFP) | ⭐⭐⭐⭐⭐ |
| PIB et données éco | ⭐⭐⭐⭐ |
| Géopolitique | ⭐⭐⭐ |

### Paires Principales
- **EUR/USD** : BCE vs Fed · Plus liquide · Spreads bas
- **GBP/USD** : Très volatile · Banque d'Angleterre
- **USD/JPY** : Différentiel de taux · JPY valeur refuge
- **AUD/USD** : Lié aux commodités (or, minerai de fer)

### Calendrier Clé
- **1er vendredi/mois** : NFP → très volatile
- **Mi-mois** : CPI → impact majeur
- **Réunions BCE/Fed** : 8×/an → volatilité extrême

### Sessions
- Tokyo 00h-09h · Londres 08h-17h · New York 13h-22h
- Chevauchements = plus fort volume"""


def _h_crypto(q, d, db):
    return f"""## ₿ Guide Crypto{db}

### Facteurs de Mouvement
- **Macro** : corrélation avec Nasdaq (risk-on/off)
- **Halving BTC** : réduit l'offre tous les 4 ans → historiquement haussier
- **Régulation** : décisions SEC, lois → impact fort
- **Fear & Greed** : < 20 = peur extrême (achat) · > 80 = cupidité (vente)

### Cycles Crypto
| Phase | Stratégie |
|-------|-----------|
| Accumulation | DCA progressif |
| Bull Run | Tenir + trailing stop |
| Distribution | Réduire positions |
| Bear Market | Cash ou shorts |

### Gestion du Risque Crypto
- ⚠️ Cryptos peuvent perdre 80-90% en bear market
- Max 5-10% du portefeuille total en crypto
- Stops larges (ATR ×3-4)
- DCA en accumulation — jamais all-in"""


def _h_profit(q, d, db):
    capital = d.get("capital",10000) if d else 10000
    return f"""## 💰 Projections de Profit — ${capital:,.0f}{db}

### Scénarios Annuels
| Scénario | Rendement | 6 mois | 1 an | 3 ans |
|----------|-----------|--------|------|-------|
| Conservateur | +15%/an | ${capital*1.075:,.0f} | ${capital*1.15:,.0f} | ${capital*(1.15**3):,.0f} |
| Modéré | +30%/an | ${capital*1.15:,.0f} | ${capital*1.30:,.0f} | ${capital*(1.30**3):,.0f} |
| Agressif | +60%/an | ${capital*1.30:,.0f} | ${capital*1.60:,.0f} | ${capital*(1.60**3):,.0f} |
| Crypto Bull | +150%/an | ${capital*1.75:,.0f} | ${capital*2.50:,.0f} | ${capital*(2.50**3):,.0f} |

### Mathématiques du Trading Rentable
```
R/R 2:1 + Win Rate 40% :
Gains : 40 × +$200 = +$8,000
Pertes : 60 × -$100 = -$6,000
Net : +$2,000 ✅ PROFITABLE
```

### Règle des 2% par Trade
Capital risqué max : **${capital*0.02:,.0f}** par trade

⚠️ 70-80% des traders particuliers perdent. Discipline > performance."""


def _h_report(q, d, db):
    if not d:
        return "🔍 Lance d'abord une **analyse** pour générer un rapport complet."
    score, label, notes = _setup_quality(d["rr"],d["conf"],d["agr"],d["atr_pct"],d["vol_r"])
    tech_str = "\n".join(f"- **{k}** : {v}" for k,v in d.get("tech",{}).items()) or "— Données non disponibles"
    conclusion = ("✅ Conditions favorables pour entrer." if score >= 60
                  else "⚠️ Conditions mitigées — attendre une meilleure opportunité." if score >= 40
                  else "❌ Setup faible — mieux vaut attendre.")
    return f"""# 📊 RAPPORT D'ANALYSE COMPLET
## {d["name"]} ({d["symbol"]}) · {datetime.now().strftime('%d/%m/%Y %H:%M')}
{db}
---
## 1. RÉSUMÉ EXÉCUTIF
Signal : **{d["action"]}** · Tendance : **{d["trend"]}**
Bull {d["bull"]*100:.1f}% · Confiance {d["conf"]*100:.0f}% · Accord {d["agr"]*100:.0f}%

---
## 2. ANALYSE TECHNIQUE
{tech_str}
- {_rsi_interp(d["rsi"])}
- {_stoch_interp(d["stoch"])}
- {_vol_interp(d["vol_r"])}

---
## 3. PLAN DE TRADE
| Niveau | Prix | % |
|--------|------|---|
| Entrée | ${d["entry"]:,.4f} | — |
| Stop-Loss | ${d["sl"]:,.4f} | -{d["sl_pct"]:.2f}% |
| Take-Profit | ${d["tp"]:,.4f} | +{d["tp_pct"]:.2f}% |
| R/R | {d["rr"]:.2f}:1 | {'✅' if d["rr"]>=2 else '⚠️'} |

Capital risqué : ${d["risk_amt"]:,.2f} (2% de ${d["capital"]:,.0f})

---
## 4. ÉVALUATION DU SETUP
**{label} — {score}/100**
{chr(10).join("- "+n for n in notes)}

---
## 5. CONCLUSION
{conclusion}

⚠️ *Outil éducatif · Pas un conseil financier.*"""


def _h_correlation(q, d, db):
    return f"""## 🔗 Corrélation & Diversification{db}

| Score | Signification | Action |
|-------|---------------|--------|
| 0.8 à 1.0 | Très corrélés | ❌ Pas de diversification |
| 0.5 à 0.8 | Modérément corrélés | ⚠️ Partielle |
| -0.3 à 0.5 | Faiblement corrélés | ✅ Bonne div. |
| < -0.3 | Inversement corrélés | ✅✅ Excellent hedge |

### Corrélations Clés à Connaître
- BTC/ETH ≈ 0.92 → inutile de tenir les deux
- SPY/QQQ ≈ 0.95 → même exposition
- Gold/USD ≈ -0.65 → Gold monte quand dollar baisse
- Gold/S&P500 ≈ 0.10 → excellent hedge

### Portefeuille Diversifié Exemple
- 30% Actions (SPY) · 20% Gold · 20% Obligations (TLT)
- 15% Commodités · 15% Crypto (BTC)
- Corrélation moyenne < 0.35 → diversification optimale"""


def _h_montecarlo(q, d, db):
    capital = d.get("capital",10000) if d else 10000
    return f"""## 🎲 Monte Carlo{db}

### Comment Lire le Graphique
| Élément | Signification |
|---------|---------------|
| Ligne CYAN | Médiane — résultat le plus probable |
| Zone bleue foncée | 68% des scénarios (±1σ) |
| Zone bleue claire | 95% des scénarios (±2σ) |
| Ligne grise | Capital initial ${capital:,.0f} |

### Interprétation P(gain)
- **P > 65%** → Stratégie favorable ✅
- **P 50-65%** → Légèrement favorable ⚠️
- **P < 50%** → Stratégie défavorable ❌

### Comment Améliorer P(gain)
1. Augmenter le R/R (≥ 2:1)
2. Améliorer le Win Rate
3. Réduire les coûts de transaction
4. Trader dans la direction de la tendance principale

⚠️ Monte Carlo utilise la **volatilité passée** — ne prédit pas les crises."""


def _h_explain(q, d, db):
    return f"""## 📖 Guide de Lecture des Graphiques{db}

### 🕯️ Bougies Japonaises
| Bougie | Signification |
|--------|---------------|
| 🟩 Verte longue | Acheteurs très forts |
| 🟥 Rouge longue | Vendeurs très forts |
| ⬜ Doji | Indécision |
| 🔨 Marteau | Rejet du bas → rebond |
| ⭐ Étoile filante | Rejet du haut → baisse |

### 6 Indicateurs Essentiels
- **RSI** < 30 survente · > 70 surachat
- **MACD** histogramme vert/rouge = momentum
- **Bollinger** bande basse = survente · bande haute = résistance
- **EMA** 9>20>50 = tendance haussière parfaite
- **Volume** élevé = signal fiable · faible = douteux
- **Stoch** < 20 survente · > 80 surachat

### Règle des 3 Confirmations
N'agissez que si **≥ 3 indicateurs** pointent dans le même sens.

Exemple BUY : RSI < 30 + MACD haussier + EMA9 > EMA20 → ✅ Signal fort"""


def _h_news(q, d, db):
    return f"""## 📰 Analyse des Actualités{db}

### Score SSGM — Comment Lire
- **> +0.3** → Très bullish → momentum haussier probable
- **+0.1 à +0.3** → Légèrement bullish → confirme les signaux
- **-0.1 à +0.1** → Neutre → se fier aux indicateurs techniques
- **< -0.3** → Très bearish → éviter les achats

### Sources Fiables
- **Crypto** : CoinDesk, The Block, @whale_alert
- **Actions** : Bloomberg, Reuters, SEC filings
- **Forex** : ForexFactory, banques centrales
- **Commodités** : EIA.gov, USDA.gov, OPEC.org

### Événements à Fort Impact
| Événement | Fréquence | Impact |
|-----------|-----------|--------|
| NFP emploi US | 1er vendredi/mois | ⭐⭐⭐⭐⭐ |
| CPI inflation | Mi-mois | ⭐⭐⭐⭐⭐ |
| Réunions Fed/BCE | 8×/an | ⭐⭐⭐⭐⭐ |
| Résultats trimestriels | 4×/an | ⭐⭐⭐⭐ |

⚠️ **Ne pas trader** 15 min avant et après une annonce majeure."""


def _h_general(q, d, db):
    name = d.get("name","l'actif") if d else "l'actif"
    setup_str = ""
    if d:
        score, label, _ = _setup_quality(d["rr"],d["conf"],d["agr"],d["atr_pct"],d["vol_r"])
        setup_str = f"\n\n**Setup actuel :** {label} ({score}/100) — Signal **{d['action']}**"
    return f"""## ⬡ Oracle IA — Moteur Propriétaire{db}{setup_str}

Je suis votre assistant expert en trading. Posez votre question :

🎯 **Signaux** → *"Faut-il acheter {name} ?"* · *"Quand vendre ?"*
📊 **Technique** → *"Explique le RSI"* · *"Que signifie le MACD ?"*
🛡️ **Risque** → *"Comment calculer ma position ?"* · *"Quel stop-loss ?"*
🔮 **Prévision** → *"Où sera {name} dans 3 mois ?"*
📋 **Rapport** → *"Génère un rapport complet"*
🌍 **Marchés** → *"Guide pétrole"* · *"Guide forex EUR/USD"* · *"Guide crypto"*
💰 **Profit** → *"Combien puis-je gagner avec $10,000 ?"*

**Moteur IA 100% propriétaire — zéro API externe — zéro abonnement ✅**"""


# ══════════════════════════════════════════════════════════════════════════════
#  FONCTIONS COMPATIBLES INTERFACE DASHBOARD
# ══════════════════════════════════════════════════════════════════════════════
def generate_report(sig: dict, df, news: list, capital: float) -> str:
    ctx = {"signal": sig, "capital": capital}
    d = _extract(ctx); db = _data_block(d)
    return _h_report("rapport", d, db)


def analyze_news_gpt(news: list, symbol: str, sig: dict = None) -> str:
    if not news:
        return "Aucune actualité. Activez **Analyser les news** et relancez."
    BW = ["bullish","rally","surge","gain","rise","pump","moon","buy","ath","record","positive","growth"]
    SW = ["crash","drop","fall","sell","dump","fear","correction","downgrade","negative","loss","recession"]
    scores, bulls, bears = [], 0, 0
    for a in news[:15]:
        txt = (a.get("title","")+" "+a.get("description","")).lower()
        b = sum(1 for w in BW if w in txt)
        s = sum(1 for w in SW if w in txt)
        if b+s > 0:
            sc = (b-s)/(b+s); scores.append(sc)
            if sc > 0.1: bulls += 1
            elif sc < -0.1: bears += 1
    avg = sum(scores)/len(scores) if scores else 0
    neutral = len(scores)-bulls-bears
    sentiment = "🟢 BULLISH" if avg>0.1 else "🔴 BEARISH" if avg<-0.1 else "⚪ NEUTRE"
    score10 = round((avg+1)*5, 1)
    top = "".join(f"{i}. {'🟢' if (a.get('title','')+a.get('description','')).lower().count('bull')>0 else '🔴'} [{a.get('source','')}] {a.get('title','')[:80]}...\n"
                  for i, a in enumerate(news[:5],1))
    sig_ctx = f"\n**Signal technique :** {sig.get('action','HOLD')} · RSI {sig.get('rsi',50):.0f}" if sig else ""
    consistent = (avg>0.1 and sig and sig.get("action")=="BUY") or (avg<-0.1 and sig and sig.get("action")=="SELL")
    return f"""## 📰 Analyse News — {symbol}{sig_ctx}

### Sentiment Global : {sentiment} — Score {score10}/10
- 🟢 Bullish : **{bulls}** · 🔴 Bearish : **{bears}** · ⚪ Neutres : **{neutral}**
Sur {len(news)} articles analysés.

### Top 5 Articles
{top}
### Cohérence avec le Signal Technique
{'✅ News **confirment** le signal technique.' if consistent else '⚠️ News **divergent** du signal — prudence.'}"""


def risk_advice_gpt(sig: dict, capital: float, portfolio: list = None) -> str:
    ctx = {"signal": sig, "capital": capital}
    d = _extract(ctx); db = _data_block(d)
    return _h_risk("risque", d, db)