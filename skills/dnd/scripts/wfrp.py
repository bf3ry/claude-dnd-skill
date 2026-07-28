#!/usr/bin/env python3
"""
wfrp.py — moteur de resolution WFRP4 (d100 sous-seuil, Degres de Reussite)

Remplace dice.py/combat.py/character.py pour la campagne L'Ennemi Interieur.
Sortie au FORMAT COMPLET impose par la regle de table n.6 :
    competence (carac) modificateur -> seuil | d100 = X -> REUSSITE/ECHEC, DR +/-N

Usage :
    python3 wfrp.py test --carac 46 --label "Channelling (FM)" --diff tres_difficile
    python3 wfrp.py test --carac 31 --label "Corps a corps (CC)" --mod +10 --av 2
    python3 wfrp.py test --carac 36 --label "Intuition (Int)" --roll 47      # rejouer un jet
    python3 wfrp.py oppose --a 46 --a-label "Erys (FM)" --b 38 --b-label "Cible (FM)" --a-diff difficile
    python3 wfrp.py diff                                                     # table des difficultes

Table de difficulte = celle du livre WFRP4 officiel (7 paliers, +60 a -30).
"""

import argparse
import random
import sys

DIFF = {
    "tres_facile":    (+60, "Tres Facile"),
    "facile":         (+40, "Facile"),
    "accessible":     (+20, "Accessible"),
    "intermediaire":  (0,   "Intermediaire"),
    "complexe":       (-10, "Complexe"),
    "difficile":      (-20, "Difficile"),
    "tres_difficile": (-30, "Tres Difficile"),
}


def tens(n):
    """Chiffre des dizaines. 100 -> 10, 07 -> 0."""
    return n // 10


def resolve(carac, mod=0, advantage=0, diff=None, roll=None):
    """Resout un test d100 WFRP4. Retourne un dict."""
    diff_mod, diff_name = DIFF.get(diff, (0, None))
    target = carac + mod + diff_mod + (advantage * 10)
    target = max(0, min(100, target))

    if roll is None:
        roll = random.randint(1, 100)

    # 01-05 reussite automatique, 96-100 echec automatique
    if roll <= 5:
        success, forced = True, "auto-reussite (01-05)"
    elif roll >= 96:
        success, forced = False, "auto-echec (96-100)"
    else:
        success, forced = (roll <= target), None

    sl = tens(target) - tens(roll)
    # Un jet force garde au minimum +1 / -1 DR
    if forced == "auto-reussite (01-05)" and sl < 1:
        sl = 1
    if forced == "auto-echec (96-100)" and sl > -1:
        sl = -1

    # Doubles = critique (reussite) ou maladresse (echec). 100 compte comme double.
    is_double = (roll % 11 == 0) or (roll == 100)
    crit = is_double and success
    fumble = is_double and not success

    return {
        "roll": roll, "target": target, "carac": carac, "mod": mod,
        "advantage": advantage, "diff_mod": diff_mod, "diff_name": diff_name,
        "success": success, "sl": sl, "crit": crit, "fumble": fumble,
        "forced": forced,
    }


def fmt(r, label="Test"):
    """Ligne au format complet de la table."""
    parts = []
    if r["diff_name"]:
        parts.append(f"{r['diff_name']} {r['diff_mod']:+d}")
    if r["mod"]:
        parts.append(f"mod {r['mod']:+d}")
    if r["advantage"]:
        parts.append(f"Avantage {r['advantage']} ({r['advantage'] * 10:+d})")
    modtxt = " ".join(parts) if parts else "sans modificateur"

    verdict = "REUSSITE" if r["success"] else "ECHEC"
    if r["crit"]:
        verdict = "REUSSITE CRITIQUE"
    if r["fumble"]:
        verdict = "MALADRESSE"

    line = (f"{label} {r['carac']} | {modtxt} -> seuil {r['target']} | "
            f"d100 = {r['roll']:02d} -> {verdict}, DR {r['sl']:+d}")
    if r["forced"]:
        line += f"  [{r['forced']}]"
    return line


def main():
    p = argparse.ArgumentParser(description="Moteur de tests WFRP4")
    sub = p.add_subparsers(dest="cmd", required=True)

    t = sub.add_parser("test")
    t.add_argument("--carac", type=int, required=True)
    t.add_argument("--label", default="Test")
    t.add_argument("--mod", type=int, default=0)
    t.add_argument("--av", type=int, default=0, help="points d'Avantage (+10 chacun)")
    t.add_argument("--diff", choices=list(DIFF), default=None)
    t.add_argument("--roll", type=int, default=None, help="forcer le de (rejeu/audit)")

    o = sub.add_parser("oppose")
    o.add_argument("--a", type=int, required=True)
    o.add_argument("--a-label", default="A")
    o.add_argument("--a-mod", type=int, default=0)
    o.add_argument("--a-diff", choices=list(DIFF), default=None)
    o.add_argument("--b", type=int, required=True)
    o.add_argument("--b-label", default="B")
    o.add_argument("--b-mod", type=int, default=0)
    o.add_argument("--b-diff", choices=list(DIFF), default=None)

    sub.add_parser("diff")

    a = p.parse_args()

    if a.cmd == "diff":
        for k, (v, n) in DIFF.items():
            print(f"{k:16s} {v:+3d}  {n}")
        return

    if a.cmd == "test":
        r = resolve(a.carac, a.mod, a.av, a.diff, a.roll)
        print(fmt(r, a.label))
        return

    if a.cmd == "oppose":
        ra = resolve(a.a, a.a_mod, 0, a.a_diff)
        rb = resolve(a.b, a.b_mod, 0, a.b_diff)
        print(fmt(ra, a.a_label))
        print(fmt(rb, a.b_label))
        margin = ra["sl"] - rb["sl"]
        if margin > 0:
            print(f"-> {a.a_label} l'emporte, DR net +{margin}")
        elif margin < 0:
            print(f"-> {a.b_label} l'emporte, DR net +{-margin}")
        else:
            win = a.a_label if a.a >= a.b else a.b_label
            print(f"-> egalite de DR, departage sur la caracteristique : {win}")
        return


if __name__ == "__main__":
    sys.exit(main())
