"""
================================================================================
  QUANTUM TRADE ORACLE — Interface de connexion Streamlit
  Fichier : qto_auth/auth_ui.py
================================================================================
  UTILISATION dans dashboard.py :
  ─────────────────────────────────
  from qto_auth.auth_ui import auth_gate, user_badge

  # Tout en haut du dashboard, AVANT tout le reste :
  if not auth_gate():
      st.stop()

  # Dans la sidebar :
  user_badge()
================================================================================
"""
import streamlit as st
import json, hashlib, secrets
from pathlib import Path
from datetime import datetime

SESSION_FILE = Path(__file__).parent / ".session"

# ══════════════════════════════════════════════════════════════════════════════
#  SESSION
# ══════════════════════════════════════════════════════════════════════════════
def _save(data: dict):
    try: SESSION_FILE.write_text(json.dumps(data))
    except Exception: pass

def _clear():
    try:
        if SESSION_FILE.exists(): SESSION_FILE.unlink()
    except Exception: pass

def _set_state(res: dict):
    st.session_state.qto_ok       = True
    st.session_state.qto_email    = res["email"]
    st.session_state.qto_username = res.get("username", res["email"].split("@")[0])
    st.session_state.qto_plan     = res.get("plan", "PRO")
    st.session_state.qto_expires  = res.get("expires_at", "")
    _save(res)

# ══════════════════════════════════════════════════════════════════════════════
#  CSS
# ══════════════════════════════════════════════════════════════════════════════
LOGIN_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@300;400;500&family=Syne:wght@700;800;900&family=Manrope:wght@400;600&display=swap');
#MainMenu,footer,header{visibility:hidden}
.stApp{background:#020509!important}
section[data-testid="stSidebar"]{display:none!important}
.block-container{padding:0!important;max-width:100%!important}

/* Inputs */
.stTextInput>div>div>input{
    background:#07101c!important;border:1px solid #122035!important;
    color:#d0e8f8!important;font-family:'DM Mono',monospace!important;
    font-size:13px!important;border-radius:5px!important;
    padding:12px 16px!important;transition:all .2s!important}
.stTextInput>div>div>input:focus{
    border-color:#00c8ff!important;
    box-shadow:0 0 0 2px rgba(0,200,255,.12)!important}
.stTextInput label{
    font-family:'DM Mono',monospace!important;font-size:9px!important;
    color:#1a3352!important;text-transform:uppercase!important;letter-spacing:2px!important}

/* Boutons */
.stButton>button{
    background:linear-gradient(135deg,rgba(0,200,255,.1),rgba(0,255,170,.05))!important;
    border:1px solid #00c8ff!important;color:#00c8ff!important;
    font-family:'Syne',sans-serif!important;font-size:11px!important;
    font-weight:900!important;letter-spacing:3px!important;
    text-transform:uppercase!important;border-radius:4px!important;
    padding:14px 20px!important;transition:all .2s!important;width:100%!important}
.stButton>button:hover{
    background:rgba(0,200,255,.18)!important;
    box-shadow:0 0 30px rgba(0,200,255,.22)!important;
    transform:translateY(-1px)!important}

/* Tabs */
.stTabs [data-baseweb="tab-list"]{
    background:#07101c!important;border:1px solid #122035!important;
    border-radius:5px!important;padding:3px!important;gap:2px!important}
.stTabs [data-baseweb="tab"]{
    font-family:'DM Mono',monospace!important;font-size:10px!important;
    color:#1a3352!important;text-transform:uppercase!important;
    letter-spacing:2px!important;border-radius:4px!important;
    padding:9px 20px!important;transition:all .15s!important}
.stTabs [aria-selected="true"]{
    background:rgba(0,200,255,.1)!important;color:#00c8ff!important;
    border:1px solid rgba(0,200,255,.2)!important}
</style>"""

def _alert(msg, kind="error") -> str:
    p = {"error":  ("#ff3d6b","rgba(255,61,107,.08)","rgba(255,61,107,.22)"),
         "success":("#00ffaa","rgba(0,255,170,.06)","rgba(0,255,170,.18)"),
         "warn":   ("#ffc107","rgba(255,193,7,.06)","rgba(255,193,7,.18)")}
    col, bg, brd = p.get(kind, p["error"])
    return (f'<div style="background:{bg};border:1px solid {brd};border-radius:5px;'
            f'padding:13px 16px;margin-top:12px;text-align:center;'
            f'font-family:DM Mono,monospace;font-size:11px;color:{col};line-height:1.7">'
            f'{msg}</div>')

# ══════════════════════════════════════════════════════════════════════════════
#  GATE PRINCIPAL — appelez auth_gate() dans dashboard.py
# ══════════════════════════════════════════════════════════════════════════════
def auth_gate() -> bool:
    """Retourne True si l'utilisateur est connecté, sinon affiche la page de login."""
    if st.session_state.get("qto_ok"):
        return True

    from qto_auth.auth_db import register, login

    # Injecter le CSS pleine page
    st.markdown(LOGIN_CSS, unsafe_allow_html=True)
    st.markdown("<div style='height:44px'></div>", unsafe_allow_html=True)

    _, col, _ = st.columns([1, 1.05, 1])
    with col:

        # ── Logo ─────────────────────────────────────────────────────────
        st.markdown("""
        <div style="text-align:center;margin-bottom:26px">
          <div style="font-size:50px;line-height:1;margin-bottom:10px;
                      filter:drop-shadow(0 0 28px rgba(0,200,255,.55))">⬡</div>
          <div style="font-family:'Syne',sans-serif;font-size:19px;font-weight:900;
                      color:#00c8ff;letter-spacing:5px;text-transform:uppercase">
            QUANTUM TRADE ORACLE
          </div>
          <div style="font-family:'DM Mono',monospace;font-size:8px;color:#1a3352;
                      letter-spacing:3px;margin-top:5px">
            PLATEFORME IA · TRADING ALGORITHMIQUE
          </div>
        </div>""", unsafe_allow_html=True)

        tab_login, tab_signup = st.tabs(["   🔑  CONNEXION   ",
                                          "   ✨  CRÉER UN COMPTE   "])

        # ══════════════════════════════════════════════════════════════
        #  CONNEXION
        # ══════════════════════════════════════════════════════════════
        with tab_login:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background:#07101c;border:1px solid #122035;border-radius:8px;
                        padding:26px 24px 20px">
              <div style="font-family:'DM Mono',monospace;font-size:9px;color:#1a3352;
                          letter-spacing:2px;text-transform:uppercase;
                          text-align:center;margin-bottom:18px">Entrez vos identifiants</div>
            """, unsafe_allow_html=True)

            l_email = st.text_input("Email", placeholder="votre@email.com", key="l_em")
            l_pass  = st.text_input("Mot de passe", placeholder="••••••••",
                                    type="password", key="l_pw")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            btn_login = st.button("⬡  SE CONNECTER", key="b_login")
            st.markdown("</div>", unsafe_allow_html=True)

            if btn_login:
                if not l_email.strip() or not l_pass.strip():
                    st.markdown(_alert("⚠️ Remplissez tous les champs.", "warn"),
                                unsafe_allow_html=True)
                else:
                    with st.spinner("Vérification…"):
                        import time; time.sleep(0.5)
                        res = login(l_email.strip(), l_pass)
                    if res["ok"]:
                        _set_state(res); st.rerun()
                    else:
                        st.markdown(_alert(f"❌  {res['msg']}", "error"),
                                    unsafe_allow_html=True)

            st.markdown("""
            <div style="text-align:center;margin-top:14px;font-family:'DM Mono',monospace;
                        font-size:9px;color:#0d1c2e;line-height:2.2">
              Pas de compte ?
              <span style="color:#1a3352"> → Onglet ✨ CRÉER UN COMPTE</span><br>
              <a href="mailto:support@votre-site.com"
                 style="color:#0d1c2e;text-decoration:none">support@votre-site.com</a>
            </div>""", unsafe_allow_html=True)

        # ══════════════════════════════════════════════════════════════
        #  CRÉER UN COMPTE
        # ══════════════════════════════════════════════════════════════
        with tab_signup:
            st.markdown("<div style='height:6px'></div>", unsafe_allow_html=True)
            st.markdown("""
            <div style="background:#07101c;border:1px solid #122035;border-radius:8px;
                        padding:26px 24px 20px">
              <div style="font-family:'DM Mono',monospace;font-size:9px;color:#1a3352;
                          letter-spacing:2px;text-transform:uppercase;
                          text-align:center;margin-bottom:18px">Créez votre accès Premium</div>
            """, unsafe_allow_html=True)

            r_user  = st.text_input("Nom d'utilisateur", placeholder="Ex: Trader94",
                                    key="r_us")
            r_email = st.text_input("Email", placeholder="votre@email.com", key="r_em")
            r_pass  = st.text_input("Mot de passe (min. 6 caractères)",
                                    placeholder="••••••••", type="password", key="r_pw")
            r_pass2 = st.text_input("Confirmer le mot de passe",
                                    placeholder="••••••••", type="password", key="r_pw2")

            # Info clé
            st.markdown("""
            <div style="margin:10px 0 5px;padding:10px 14px;background:#020509;
                        border:1px solid #0d1c2e;border-left:3px solid #00c8ff55;
                        border-radius:4px">
              <div style="font-family:'DM Mono',monospace;font-size:9px;color:#1a3352;
                          line-height:1.9">
                🔑 <b style="color:#122035">Clé de licence</b> — reçue après paiement<br>
                Format : <span style="color:#122035">QTO-XXXX-XXXX-XXXX-XXXX</span>
              </div>
            </div>""", unsafe_allow_html=True)

            r_key   = st.text_input("Clé de licence",
                                    placeholder="QTO-XXXX-XXXX-XXXX-XXXX", key="r_key")
            st.markdown("<div style='height:4px'></div>", unsafe_allow_html=True)
            btn_reg = st.button("✨  CRÉER MON COMPTE", key="b_reg")
            st.markdown("</div>", unsafe_allow_html=True)

            if btn_reg:
                err = None
                if not all([r_user.strip(), r_email.strip(), r_pass.strip(), r_key.strip()]):
                    err = "⚠️ Remplissez tous les champs."
                elif r_pass != r_pass2:
                    err = "❌ Les mots de passe ne correspondent pas."
                elif len(r_pass) < 6:
                    err = "❌ Mot de passe trop court (min. 6 caractères)."
                elif not r_key.strip().upper().startswith("QTO-"):
                    err = "❌ Format de clé invalide. (QTO-XXXX-XXXX-XXXX-XXXX)"

                if err:
                    st.markdown(_alert(err, "error"), unsafe_allow_html=True)
                else:
                    with st.spinner("Création du compte…"):
                        import time; time.sleep(0.6)
                        res = register(r_email.strip(), r_user.strip(),
                                       r_pass, r_key.strip())
                    if res["ok"]:
                        st.markdown(_alert(
                            f"✅  Compte créé ! Bienvenue <b>{res['username']}</b> "
                            f"— Plan <b>{res['plan']}</b> activé.<br>"
                            f"Rendez-vous dans l'onglet <b>🔑 CONNEXION</b>.",
                            "success"), unsafe_allow_html=True)
                    else:
                        st.markdown(_alert(f"❌  {res['msg']}", "error"),
                                    unsafe_allow_html=True)

            st.markdown("""
            <div style="text-align:center;margin-top:14px;font-family:'DM Mono',monospace;
                        font-size:9px;color:#0d1c2e;line-height:2.2">
              Pas encore de clé ?
              <a href="https://votre-site.com"
                 style="color:#1a3352;text-decoration:none">Achetez votre accès ici →</a>
            </div>""", unsafe_allow_html=True)

    return False


# ══════════════════════════════════════════════════════════════════════════════
#  BADGE SIDEBAR
# ══════════════════════════════════════════════════════════════════════════════
def user_badge():
    """Badge utilisateur dans la sidebar + bouton déconnexion."""
    if not st.session_state.get("qto_ok"):
        return
    username = st.session_state.get("qto_username", "")
    email    = st.session_state.get("qto_email", "")
    plan     = st.session_state.get("qto_plan", "PRO")
    expires  = st.session_state.get("qto_expires", "")
    pc = {"PRO":"#00c8ff","ELITE":"#00ffaa","TRIAL":"#ffc107"}.get(plan,"#8bb8d8")

    st.sidebar.markdown(f"""
    <div style="background:#07101c;border:1px solid #122035;border-radius:6px;
                padding:12px 14px;margin-bottom:10px">
      <div style="display:flex;align-items:center;justify-content:space-between;margin-bottom:8px">
        <span style="font-size:18px">👤</span>
        <span style="border:1px solid {pc}55;color:{pc};
                     font-family:'DM Mono',monospace;font-size:8px;
                     padding:2px 8px;border-radius:2px;
                     text-transform:uppercase;letter-spacing:1px">{plan}</span>
      </div>
      <div style="font-family:'Syne',sans-serif;font-size:13px;font-weight:800;
                  color:#d0e8f8;margin-bottom:2px">{username}</div>
      <div style="font-family:'DM Mono',monospace;font-size:9px;color:#1a3352;
                  overflow:hidden;text-overflow:ellipsis;white-space:nowrap">{email}</div>
      {"<div style='font-family:DM Mono,monospace;font-size:9px;color:#0d1c2e;margin-top:5px'>⏱ Expire : "+expires+"</div>" if expires else ""}
    </div>""", unsafe_allow_html=True)

    if st.sidebar.button("🔒  Déconnexion", key="btn_logout", use_container_width=True):
        for k in ["qto_ok","qto_email","qto_username","qto_plan","qto_expires"]:
            st.session_state.pop(k, None)
        _clear()
        st.rerun()
