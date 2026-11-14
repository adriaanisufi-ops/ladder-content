"""Score a VYZEE spec against FORMULA.md (100 points). Below 80: fix the spec before rendering.

Usage:  python3 toolkit/score.py SPEC.json [SPEC2.json ...]
Speech length is estimated (about 0.24 s per word at speed 1.05, measured on Kokoro am_michael); the renderer's voice timing report is the real check.
"""
import json, os, re, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import vyzee as V

DASHES = "‐‑‒–—―−"
NUMWORDS = r"\b(\d+|one|two|three|four|five|rule|steps?|method|here's|here is)\b"

def words(s): return len(re.findall(r"[A-Za-z0-9']+", s))
def est(line): return words(line["text"]) * 0.24 * 1.05 / line.get("speed", 1.05) + .12
def lstart(l): return float(l["at"]) if "at" in l else V.T(l["beat"])

def shot_events(s):
    ev = [s["from"]]
    for key in ("items", "rows", "labels", "pills", "bars", "left", "right", "words", "gaps"):
        for it in s.get(key, []) or []:
            if isinstance(it, dict) and "beat" in it: ev.append(it["beat"])
    for v in s.get("visitors", []): ev += [v["in"], v["out"]]
    for key in ("strikes", "taps"): ev += s.get(key, [])
    for key in ("snap", "tip", "stand", "gold", "pop", "flip", "at", "strike", "b_beat", "cross", "light", "stars"):
        if key in s and not isinstance(s[key], list): ev.append(s[key])
    return ev

def score(path):
    sp = json.load(open(path))
    if sp.get("sound"): V.load_sound(sp["sound"])
    LEN = float(sp.get("length", 44.5)); drop_t = V.T(V.DROP_BEAT)
    lines = sorted(sp["lines"], key=lstart); texts = sp.get("text", []); shots = sp["shots"]
    out = []; total = 0
    def part(name, pts, mx, notes):
        nonlocal total; total += pts; out.append(f"{name:<14}{pts:>3}/{mx}  " + "; ".join(n for n in notes if n))

    # 1 hook (25)
    p, n = 0, []
    h = lines[0]; ht = [t for t in texts if (t["from"] if not isinstance(t["from"], dict) else 1) == 0]
    if ht: p += 7
    else: n.append("NO hook text in frame 1")
    if lstart(h) <= .2: p += 4
    else: n.append("hook voice starts late")
    if words(h["text"]) <= 8: p += 6
    else: n.append(f"hook is {words(h['text'])} words (max 8)")
    if lstart(h) + est(h) <= 2.4: p += 4
    else: n.append(f"hook ends around {lstart(h) + est(h):.1f} s (max 2.3)")
    if sp.get("hook_type") in ("claim", "stop", "question", "proof"): p += 2
    else: n.append("set hook_type")
    if re.search(r"\byou(r|'re)?\b", h["text"], re.I) or sp.get("hook_type") == "proof": p += 2
    else: n.append("hook doesn't talk to 'you'")
    part("hook", p, 25, n)

    # 2 open loop (10)
    p, n = 0, []
    if any(re.search(NUMWORDS, l["text"], re.I) for l in lines if 1.5 < lstart(l) < 5.5): p += 5
    else: n.append("no promise in the first 5 s ('Here's the 4 step rule.')")
    q = [l for l in lines if l["text"].strip().endswith("?") and V.T(24) <= lstart(l) < V.SILENCE]
    if q and lstart(q[-1]) + est(q[-1]) <= V.SILENCE + .5: p += 5
    elif q: n.append("question before the silence runs into it")
    else: n.append("no question right before the silence")
    part("open loop", p, 10, n)

    # 3 pacing (20)
    p, n = 0, []
    ev = [0.0] + [lstart(l) for l in lines] + [V.T(t["from"]) for t in texts]
    for s in shots: ev += [V.T(e) for e in shot_events(s)]
    ev += [V.T(b) for b in V.punch_beats(sp)]
    if sp.get("comment_q"): ev.append(V.T(sp["comment_q"]["from"]))
    ev = sorted(set(round(e, 2) for e in ev if 0 <= e <= LEN)) + [LEN]
    gaps = [(b - a, a) for a, b in zip(ev, ev[1:])]
    big = [(g, a) for g, a in gaps if g > 2.5 and not (a + g >= LEN - .01 and g <= 4)]   # the last hold (reading the comment question) may be up to 4 s
    p += max(0, 10 - 3 * len(big)); n += [f"nothing changes {a:.1f} to {a + g:.1f} s" for g, a in big[:4]]
    long_txt = [t for t in texts if V.T(t["from"]) < drop_t and words(t.get("big", t.get("pill", t.get("small", "")))) > 7]
    p += max(0, 5 - 2 * len(long_txt)); n += [f"screen text over 7 words: '{t.get('big', '')[:30]}...'" for t in long_txt[:2]]
    if sp.get("punch"): p += 5
    else: n.append("no camera punch on the drop (\"punch\": \"drop\")")
    part("pacing", p, 20, n)

    # 4 payoff (20)
    p, n = 0, []
    num = [s for s in shots if s["type"] == "numbered"]
    if num:
        s = num[0]; it = s["items"]
        if abs(V.T(it[0]["beat"]) - drop_t) < .1: p += 6
        else: n.append("first step not on the drop")
        if 3 <= len(it) <= 5: p += 3
        else: n.append(f"{len(it)} steps (3 to 5)")
        lw = [x["text"] for x in it if words(x["text"]) > 5]
        if not lw: p += 4
        else: n.append(f"step over 5 words: {lw[0]}")
        hold = V.T(s["to"]) - V.T(it[-1]["beat"]) if "to" in s else 9
        if hold >= 3: p += 4
        else: n.append(f"full list only {hold:.1f} s on screen (min 3, the save moment)")
        if any(x["type"] in ("convert", "chart") for x in shots) or any(re.search(r"\bfor example\b|\d", l["text"]) for l in lines if lstart(l) > drop_t): p += 3
        else: n.append("no concrete examples after the steps")
    else: n.append("no numbered method on the drop")
    part("payoff", p, 20, n)

    # 5 emotion, gold, loop (10)
    p, n = 0, []
    if any(lstart(l) >= V.BREAK_T - .1 for l in lines): p += 4
    else: n.append("no line in the quiet part")
    if any(t.get("gold") for t in texts) or any("gold" in s for s in shots): p += 4
    else: n.append("no gold moment")
    if 30 <= LEN <= 47: p += 2
    else: n.append(f"length {LEN} s")
    part("emotion+gold", p, 10, n)

    # 6 comment engine (15)
    p, n = 0, []
    cq = sp.get("comment_q")
    if cq:
        p += 6
        if cq["text"].strip().endswith("?") or re.search(r"\b(write|drop|name|pick)\b", cq["text"], re.I): p += 3
        else: n.append("comment_q isn't a question or a fill in")
        if V.T(cq["from"]) >= V.BREAK_T - .1: p += 3
        else: n.append("comment_q comes before the quiet part")
        if any(l["text"].lower().rstrip("?.") in cq["text"].lower() or cq["text"].lower().rstrip("?.") in l["text"].lower() for l in lines): p += 3
        else: n.append("comment question isn't spoken (add it to lines)")
    else: n.append("no comment_q at the end")
    if re.search(r"comment book|link in bio|unlock", json.dumps(sp), re.I): p -= 5; n.append("CTA/bait in the video")
    part("comments", p, 15, n)

    blob = json.dumps(sp, ensure_ascii=False)
    if any(c in blob for c in DASHES): total -= 10; out.append("DASH CHARACTER FOUND: -10")
    print(f"== {os.path.basename(path)}: {total}/100 {'OK' if total >= 80 else 'FIX BEFORE RENDERING'}")
    print("\n".join("   " + o for o in out))
    return total

if __name__ == "__main__":
    for f in sys.argv[1:]: score(f)
