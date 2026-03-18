"""
================================================================================
  QUANTUM TRADE ORACLE — Outil Admin
  Fichier : qto_auth/admin.py
================================================================================
  COMMANDES :
    python admin.py genkey              → Générer 1 clé PRO 365 jours
    python admin.py genkey ELITE 180    → Clé ELITE 180 jours
    python admin.py genkey TRIAL 7      → Clé d'essai 7 jours
    python admin.py addkey QTO-ABCD-... → Ajouter une clé personnalisée
    python admin.py keys                → Voir toutes les clés
    python admin.py users               → Voir tous les comptes
    python admin.py revoke email        → Désactiver un compte
    python admin.py revokekey QTO-...   → Désactiver une clé
    python admin.py stats               → Statistiques
================================================================================
"""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from qto_auth.auth_db import (add_key, add_key_manual, list_keys, revoke_key,
                               list_users, revoke_user, stats, init)

G  = lambda t: f"\033[92m{t}\033[0m"
R  = lambda t: f"\033[91m{t}\033[0m"
C  = lambda t: f"\033[96m{t}\033[0m"
Y  = lambda t: f"\033[93m{t}\033[0m"
D  = lambda t: f"\033[2m{t}\033[0m"
B  = lambda t: f"\033[1m{t}\033[0m"

def cmd_genkey(plan="PRO", days=365):
    key = add_key(plan=plan, days=int(days))
    print(f"""
  {C('⬡ Clé générée avec succès !')}

  Clé    : {B(C(key))}
  Plan   : {Y(plan)}
  Durée  : {days} jours

  {D('→ Envoyez cette clé à votre client par email.')}
  {D('→ Il l\'utilisera pour créer son compte dans le dashboard.')}
""")

def cmd_addkey(key, plan="PRO", days=365):
    ok = add_key_manual(key, plan, int(days))
    if ok:
        print(f"\n  {G('✅ Clé ajoutée :')} {C(key.upper())}  Plan={Y(plan)}  Durée={days}j\n")
    else:
        print(f"\n  {R('❌ Clé déjà existante.')}\n")

def cmd_keys():
    keys = list_keys()
    if not keys:
        print(D("\n  Aucune clé.\n")); return
    print(C(f"\n  {'CLÉ':<35} {'PLAN':<8} {'STATUT':<12} {'UTILISÉE PAR':<35} EXPIRE"))
    print("  " + "─"*105)
    for k in keys:
        if not k["active"]:   st = R("DÉSACTIVÉE")
        elif k["used_by"]:    st = Y("UTILISÉE  ")
        else:                  st = G("DISPONIBLE")
        exp   = (k["expires_at"] or "illimitée")[:10]
        used  = k["used_by"] or "—"
        print(f"  {k['key']:<35} {k['plan']:<8} {st}  {used:<35} {exp}")
    dispo = sum(1 for k in keys if not k["used_by"] and k["active"])
    print(f"\n  {len(keys)} clés au total · {G(str(dispo))} disponibles\n")

def cmd_users():
    users = list_users()
    if not users:
        print(D("\n  Aucun utilisateur.\n")); return
    print(C(f"\n  {'EMAIL':<35} {'NOM':<18} {'PLAN':<8} {'ACTIF':<8} {'CRÉÉ':<12} DERNIÈRE CONNEXION"))
    print("  " + "─"*105)
    for u in users:
        st = G("✓ OUI") if u["active"] else R("✗ NON")
        cr = (u["created_at"] or "")[:10]
        ll = (u["last_login"] or "jamais")[:16]
        print(f"  {u['email']:<35} {u['username']:<18} {u['plan']:<8} {st:<14} {cr:<12} {ll}")
    print(f"\n  {len(users)} comptes au total\n")

def cmd_revoke(email):
    ans = input(Y(f"  ⚠️  Désactiver le compte {email} ? (o/N) : "))
    if ans.lower() == "o":
        revoke_user(email)
        print(G("  ✅ Compte désactivé.\n"))
    else:
        print(D("  Annulé.\n"))

def cmd_revokekey(key):
    ans = input(Y(f"  ⚠️  Désactiver la clé {key} ? (o/N) : "))
    if ans.lower() == "o":
        revoke_key(key)
        print(G("  ✅ Clé désactivée.\n"))
    else:
        print(D("  Annulé.\n"))

def cmd_stats():
    s = stats()
    print(f"""
  {C('⬡ STATISTIQUES — Quantum Trade Oracle')}

  Comptes créés    : {C(s['users_total'])}
  Comptes actifs   : {G(s['users_active'])}
  Clés générées    : {C(s['keys_total'])}
  Clés disponibles : {G(s['keys_available'])}
  Connexions aujourd'hui : {Y(s['logins_today'])}
""")

HELP = C("""
  ╔══════════════════════════════════════════════════════════════╗
  ║  ⬡  QUANTUM TRADE ORACLE — Admin                           ║
  ╠══════════════════════════════════════════════════════════════╣
  ║  python admin.py genkey              → Clé PRO 365 jours   ║
  ║  python admin.py genkey ELITE 180    → Clé ELITE 180 jours ║
  ║  python admin.py genkey TRIAL 7      → Clé essai 7 jours   ║
  ║  python admin.py addkey QTO-ABCD-... → Clé personnalisée   ║
  ║  python admin.py keys                → Liste des clés       ║
  ║  python admin.py users               → Liste des comptes    ║
  ║  python admin.py revoke email        → Désactiver compte    ║
  ║  python admin.py revokekey QTO-...   → Désactiver clé       ║
  ║  python admin.py stats               → Statistiques         ║
  ╚══════════════════════════════════════════════════════════════╝
""")

if __name__ == "__main__":
    init()
    a = sys.argv[1:]
    if not a:                                      print(HELP)
    elif a[0] == "genkey":
        plan = a[1] if len(a)>1 else "PRO"
        days = a[2] if len(a)>2 else "30"
        cmd_genkey(plan, days)
    elif a[0] == "addkey" and len(a)>1:
        plan = a[2] if len(a)>2 else "PRO"
        days = a[3] if len(a)>3 else "30"
        cmd_addkey(a[1], plan, days)
    elif a[0] == "keys":                           cmd_keys()
    elif a[0] == "users":                          cmd_users()
    elif a[0] == "revoke"    and len(a)>1:         cmd_revoke(a[1])
    elif a[0] == "revokekey" and len(a)>1:         cmd_revokekey(a[1])
    elif a[0] == "stats":                          cmd_stats()
    else:                                          print(HELP)
