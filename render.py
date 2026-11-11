#!/usr/bin/env python3
"""Schleburg Immobilien: Social-Media-Grafiken (HTML -> PNG).

Aufruf:  python3 render.py spec.json out.png [--pool /tmp/pool]
Die spec.json beschreibt eine Grafik (siehe README.md). Bilder liegen als
<Drive-ID>.jpg (Fotos) bzw. <Drive-ID>.png (Freisteller) im Pool-Ordner.
"""
import base64, io, json, os, sys, html
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
NB, NB2, HON, CRE = '#14304F', '#0E2239', '#E3A93E', '#F6F1E7'
HON_DK = '#B97F0B'          # Honig auf hellem Grund (Schrift)
GREY = '#5B6E82'
E = html.escape


def b64file(p, mime):
    return f"data:{mime};base64," + base64.b64encode(open(p, 'rb').read()).decode()


def fonts_css():
    f = os.path.join(HERE, 'fonts')
    out = ''
    for w, st, fn in [(400, 'normal', 'Regular'), (500, 'normal', 'Medium'), (700, 'normal', 'Bold'), (700, 'italic', 'BoldItalic')]:
        p = os.path.join(f, f'Poppins-{fn}.ttf')
        if os.path.exists(p):
            out += f"@font-face{{font-family:'Poppins';font-weight:{w};font-style:{st};src:url('{b64file(p, 'font/ttf')}')}}"
    return out


class Ctx:
    def __init__(self, spec, pool):
        self.s = spec
        self.pool = pool
        self.land = spec.get('format', 'portrait') == 'landscape'
        self.W, self.H = (1200, 900) if self.land else (1080, 1350)
        self.FH = 110 if self.land else 140          # Hoehe Fussleiste
        logo = open(os.path.join(HERE, 'assets', 'logo_hell.svg'), encoding='utf-8').read()
        dark = logo.replace('#1F3B57', '#FFFFFF').replace('#3F6E95', '#B9CCE0')
        uri = lambda t: 'data:image/svg+xml;base64,' + base64.b64encode(t.encode()).decode()
        self.L_HELL, self.L_DUNKEL = uri(logo), uri(dark)
        fj = os.path.join(HERE, 'focus.json')
        self.focus = json.load(open(fj)) if os.path.exists(fj) else {}
        self.focus.update(spec.get('focus', {}))

    # Akzentfarbe fuer em-Woerter: optional Themenfarbe (spec.accent_dark / accent_light)
    def acc(self, on_dark):
        k = 'accent_dark' if on_dark else 'accent_light'
        return self.s.get(k) or (HON if on_dark else HON_DK)

    def photo(self, id_, w=1400):
        p = os.path.join(self.pool, id_ + '.jpg')
        im = Image.open(p).convert('RGB')
        im.thumbnail((w, w * 2))
        b = io.BytesIO(); im.save(b, 'JPEG', quality=88)
        return 'data:image/jpeg;base64,' + base64.b64encode(b.getvalue()).decode()

    def fpos(self, id_, boxw, boxh, tx, ty):
        """object-position so, dass der Fokuspunkt des Bildes bei (tx,ty) in der Box liegt."""
        fx, fy = self.focus.get(id_, (.5, .5))
        w, h = Image.open(os.path.join(self.pool, id_ + '.jpg')).size
        sc = max(boxw / w, boxh / h)
        Ws, Hs = w * sc, h * sc
        px = .5 if Ws <= boxw + 1 else min(1, max(0, (fx * Ws - tx) / (Ws - boxw)))
        py = .5 if Hs <= boxh + 1 else min(1, max(0, (fy * Hs - ty) / (Hs - boxh)))
        return f'object-position:{px*100:.1f}% {py*100:.1f}%'

    def cutout(self, id_, crop=True):
        p = os.path.join(self.pool, id_ + '.png')
        if not os.path.exists(p):
            p = os.path.join(HERE, 'assets', 'cutouts', id_ + '.png')
        im = Image.open(p).convert('RGBA')
        if crop:
            bb = im.split()[3].point(lambda a: 255 if a > 8 else 0).getbbox()
            if bb: im = im.crop(bb)
        b = io.BytesIO(); im.save(b, 'PNG')
        return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(), im.size

    # ---- Bausteine ----
    def css(self):
        return f'''{fonts_css()}
*{{margin:0;padding:0;box-sizing:border-box}}
body{{width:{self.W}px;height:{self.H}px;overflow:hidden;font-family:'Poppins','Inter',sans-serif;position:relative}}
.abs{{position:absolute}}
.bgd{{position:absolute;inset:0;background:radial-gradient(900px 700px at 85% 8%,#2A5C8E 0%,{NB} 55%,{NB2} 100%)}}
.bgl{{position:absolute;inset:0;background:radial-gradient(800px 600px at 10% 0%,#FFFFFF 0%,{CRE} 70%)}}
em{{font-style:italic;font-weight:700}}
.mk{{background:linear-gradient(transparent 50%,{HON} 50%,{HON} 90%,transparent 90%);padding:0 10px;margin:0 -4px}}
.mkd{{background:linear-gradient(transparent 50%,rgba(227,169,62,.55) 50%,rgba(227,169,62,.55) 90%,transparent 90%);padding:0 10px;margin:0 -4px}}
.foot{{position:absolute;left:0;bottom:0;width:{self.W}px;height:{self.FH}px;display:flex;align-items:center;justify-content:space-between;padding:0 {70 if not self.land else 60}px}}
.foot img{{height:{88 if not self.land else 72}px}} .foot span{{font-size:{30 if not self.land else 26}px;font-weight:600}}
.fd{{background:{NB2};color:#fff}} .fl{{background:{CRE};color:{NB}}}
'''

    def page(self, body):
        return f'<!DOCTYPE html><html><head><meta charset="utf-8"><style>{self.css()}</style></head><body>{body}</body></html>'

    def foot(self, dark):
        return f'<div class="foot {"fd" if dark else "fl"}"><img src="{self.L_DUNKEL if dark else self.L_HELL}"><span>schleburg-immobilien.de</span></div>'

    def diag(self, top, fill, h, y0, y1):
        return f'<svg class="abs" style="left:0;top:{top}px" width="{self.W}" height="{h}" viewBox="0 0 {self.W} {h}"><path d="M0 {y0} L{self.W} {y1} L{self.W} {h} L0 {h} Z" fill="{fill}"/><path d="M0 {y0} L{self.W} {y1}" fill="none" stroke="{HON}" stroke-width="10"/></svg>'

    def card(self, top, fill, h, r=70):
        return f'<div class="abs" style="left:0;top:{top}px;width:{self.W}px;height:{h}px;background:{fill};border-radius:{r}px {r}px 0 0;border-top:10px solid {HON}"></div>'

    def curve(self, top, fill, h, y0=150, y1=60, y2=170):
        return f'<svg class="abs" style="left:0;top:{top}px" width="{self.W}" height="{h}" viewBox="0 0 {self.W} {h}"><path d="M0 {y0} Q{self.W//2} {y1} {self.W} {y2} L{self.W} {h} L0 {h} Z" fill="{fill}"/><path d="M0 {y0} Q{self.W//2} {y1} {self.W} {y2}" fill="none" stroke="{HON}" stroke-width="10"/></svg>'

    def pill(self, txt, x, y, fs=56, rot=-4):
        return f'<div class="abs" style="left:{x}px;top:{y}px;background:{HON};color:{NB2};font-weight:800;font-size:{fs}px;letter-spacing:4px;padding:14px 42px;border-radius:60px;transform:rotate({rot}deg);box-shadow:0 14px 30px rgba(0,0,0,.3)">{E(txt)}</div>'

    def stamp(self, l1, l2, x, y, size=210, rot=-10, fs1=26, fs2=24):
        t2 = f'<text x="115" y="146" text-anchor="middle" font-family="Poppins" font-weight="800" font-size="{fs2}" fill="{NB2}">{E(l2)}</text>' if l2 else ''
        y1 = 108 if l2 else 124
        return f'<svg class="abs" style="left:{x}px;top:{y}px;width:{size}px;height:{size}px;transform:rotate({rot}deg)" viewBox="0 0 230 230"><circle cx="115" cy="115" r="110" fill="{HON}"/><circle cx="115" cy="115" r="98" fill="none" stroke="{NB2}" stroke-width="3" stroke-dasharray="3 8"/><text x="115" y="{y1}" text-anchor="middle" font-family="Poppins" font-weight="800" font-size="{fs1}" fill="{NB2}">{E(l1)}</text>{t2}</svg>'

    def marker(self, txt, on_dark, color=None):
        """Textmarker-Effekt: Farbband nur auf der unteren Haelfte des Wortes."""
        col = color or self.s.get('marker_color') or ('rgba(227,169,62,.80)' if on_dark else 'rgba(227,169,62,.65)')
        return (f'<span style="background:linear-gradient(transparent 56%,{col} 56%,{col} 92%,transparent 92%);'
                f'padding:0 .12em;margin:0 -.04em;-webkit-box-decoration-break:clone;box-decoration-break:clone">{E(txt)}</span>')

    def hl(self, pre, accent, post, on_dark):
        """Headline mit hervorgehobenem Wort: spec.hl_style 'italic' (Standard) oder 'marker'."""
        out = E(pre or '')
        if accent:
            if self.s.get('hl_style', 'italic') == 'marker':
                out += ' ' + self.marker(accent, on_dark)
            else:
                out += f' <em style="color:{self.acc(on_dark)}">{E(accent)}</em>'
        if post: out += ' ' + E(post)
        return out.strip()

    def src(self, top, dark=False):
        t = self.s.get('source')
        if not t: return ''
        col = '#B9C9D8' if dark else GREY
        return f'<p class="abs" style="left:{80 if not self.land else 60}px;top:{top}px;color:{col};font-size:{24 if not self.land else 22}px">{E(t)}</p>'


# =============== Hochformat 1080x1350 ===============
def p_zahl(c):
    s = c.s
    house = '<svg class="abs" style="right:-60px;top:70px;width:640px;opacity:.10" viewBox="0 0 200 200"><path d="M20 100 L100 30 L180 100 L180 180 L20 180 Z M80 180 L80 120 L120 120 L120 180" fill="none" stroke="#fff" stroke-width="6"/></svg>'
    num = E(s['number']); unit = E(s.get('unit', ''))
    n = len(s['number'])
    fs = 330 if n <= 5 else (270 if n <= 7 else 220)
    return c.page(f'''<div class="bgd"></div>{house}
<div class="abs" style="left:60px;top:90px;font-size:{fs}px;font-weight:800;line-height:1;color:{HON};letter-spacing:-12px;white-space:nowrap">{num}<span style="font-size:{int(fs*.52)}px;letter-spacing:-4px"> {unit}</span></div>
<h1 class="abs" style="left:80px;top:470px;width:900px;color:#fff;font-weight:800;font-size:78px;line-height:1.05;letter-spacing:-1.5px">{c.hl(s.get('headline'), s.get('accent'), s.get('headline_post'), True)}</h1>
{c.diag(800, CRE, 550, 150, 40)}
<p class="abs" style="left:80px;top:985px;width:900px;color:{NB};font-size:38px;line-height:1.4;font-weight:500">{E(s.get('text', ''))}</p>
{c.src(1170)}{c.foot(False)}''')


def bars_svg(vals, W, H, base, maxh, bw, gap, x0, fsv=30, fsl=26, hi_last=True):
    mx = max(v for _, v in vals) * 1.12
    dec = any(v != int(v) for _, v in vals)
    out = ''
    for i, (lab, v) in enumerate(vals):
        h = v / mx * maxh; x = x0 + i * (bw + gap); last = hi_last and i == len(vals) - 1
        fv = (f'{v:.1f}' if dec else f'{v:g}').replace('.', ',')
        out += (f'<rect x="{x}" y="{base-h}" width="{bw}" height="{h}" rx="14" fill="{HON if last else NB}"/>'
                f'<text x="{x+bw/2}" y="{base-h-15}" text-anchor="middle" font-family="Poppins" font-weight="700" font-size="{fsv}" fill="{NB}">{fv}</text>'
                f'<text x="{x+bw/2}" y="{base+45}" text-anchor="middle" font-family="Poppins" font-weight="500" font-size="{fsl}" fill="{GREY}">{E(str(lab))}</text>')
    return out


def p_diagramm(c):
    s = c.s; vals = [(a, float(b)) for a, b in s['bars']]
    n = len(vals); bw = min(120, int(800 / n * .75)); gap = int((880 - n * bw) / max(1, n - 1)) if n > 1 else 0
    bars = bars_svg(vals, 980, 600, 480, 400, bw, min(gap, 80), int((980 - (n * bw + (n - 1) * min(gap, 80))) / 2))
    pill = s.get('pill')
    return c.page(f'''<div class="bgl"></div>
<h1 class="abs" style="left:80px;top:80px;width:920px;color:{NB};font-weight:800;font-size:82px;line-height:1.04;letter-spacing:-1.5px">{c.hl(s.get('headline'), s.get('accent'), s.get('headline_post'), False)}</h1>
<p class="abs" style="left:80px;top:300px;width:560px;color:#41566B;font-size:34px;line-height:1.35">{E(s.get('subtitle', ''))}</p>
<div class="abs" style="left:50px;top:420px;width:980px;height:640px;background:#fff;border-radius:44px;box-shadow:0 30px 60px rgba(14,34,57,.18)"></div>
<svg class="abs" style="left:50px;top:440px" width="980" height="600" viewBox="0 0 980 600"><line x1="20" y1="480" x2="960" y2="480" stroke="#D5DEEA" stroke-width="3"/>{bars}</svg>
{c.pill(pill, 650, 372, fs=34, rot=4) if pill else ''}
{c.src(1090)}{c.foot(False)}''')


def p_tipp(c):
    s = c.s; im = s['image']
    return c.page(f'''<div class="bgd"></div>
<img class="abs" style="left:0;top:0;width:1080px;height:830px;object-fit:cover;{c.fpos(im,1080,830,540,330)}" src="{c.photo(im)}">
{c.card(660, NB, 700, 80)}
{c.pill(s.get('pill', 'TIPP'), 80, 600, fs=64, rot=-4)}
<h1 class="abs" style="left:80px;top:790px;width:920px;color:#fff;font-weight:800;font-size:72px;line-height:1.05;letter-spacing:-1.2px">{c.hl(s.get('headline'), s.get('accent'), s.get('headline_post'), True)}</h1>
<p class="abs" style="left:80px;top:1030px;width:900px;color:#D5DEEA;font-size:33px;line-height:1.35">{E(s.get('text', ''))}</p>
{c.foot(True)}''')


def p_liste(c):
    s = c.s; im = s['image']
    li = ''.join(f'<div style="display:flex;align-items:center;gap:26px;margin-bottom:24px"><div style="flex:none;width:62px;height:62px;border-radius:50%;background:{HON};color:{NB2};font-weight:800;font-size:38px;display:flex;align-items:center;justify-content:center">✓</div><div style="font-size:42px;font-weight:600;color:{NB}">{E(t)}</div></div>' for t in s['items'][:4])
    return c.page(f'''<div class="bgl"></div>
<img class="abs" style="left:0;top:0;width:1080px;height:620px;object-fit:cover;{c.fpos(im,1080,620,540,270)}" src="{c.photo(im)}">
{c.diag(400, CRE, 950, 170, 50)}
<h1 class="abs" style="left:80px;top:668px;width:920px;color:{NB};font-weight:800;font-size:70px;line-height:1.03;letter-spacing:-1.5px">{c.hl(s.get('headline'), s.get('accent'), s.get('headline_post'), False)}</h1>
<div class="abs" style="left:80px;top:880px">{li}</div>
{c.foot(False)}''')


def p_mythos(c):
    s = c.s; im = s['image']
    return c.page(f'''<div class="bgd"></div>
<div class="abs" style="left:80px;top:70px;color:{HON};font-weight:800;font-size:64px;letter-spacing:6px">MYTHOS</div>
<h1 class="abs" style="left:80px;top:165px;width:920px;color:#fff;font-weight:800;font-size:68px;line-height:1.05;letter-spacing:-1.2px;text-decoration:line-through;text-decoration-color:{HON};text-decoration-thickness:6px">{E(s['myth'])}</h1>
<img class="abs" style="left:0;top:400px;width:1080px;height:540px;object-fit:cover;{c.fpos(im,1080,540,540,300)};clip-path:polygon(0 12%,100% 0,100% 100%,0 100%)" src="{c.photo(im)}">
<svg class="abs" style="left:0;top:400px" width="1080" height="540"><path d="M0 65 L1080 0" stroke="{HON}" stroke-width="10" fill="none"/></svg>
<div class="abs" style="left:0;top:940px;width:1080px;height:410px;background:{CRE}"></div>
<div class="abs" style="left:80px;top:960px;color:{NB};font-weight:800;font-size:64px;letter-spacing:6px"><span class="mk">FAKT</span></div>
<p class="abs" style="left:80px;top:1050px;width:900px;color:{NB};font-weight:700;font-size:54px;line-height:1.12;letter-spacing:-1px">{c.hl(s.get('fact'), s.get('accent'), s.get('fact_post'), False)}</p>
{c.foot(False)}''')


def p_gesicht(c):
    s = c.s
    uri, (w, h) = c.cutout(s.get('cutout', '1Yu7iFzod_FkkPci0gUfTYnTq9meqMvkw'))
    ph = 1120; pw = int(ph * w / h); left = 1080 - pw + 80
    return c.page(f'''<div class="bgd"></div>
<div class="abs" style="left:80px;top:80px;color:{HON};font-weight:800;font-size:150px;line-height:.6">„</div>
<h1 class="abs" style="left:80px;top:200px;width:500px;color:#fff;font-weight:800;font-size:54px;line-height:1.1;letter-spacing:-1px">{c.hl(s.get('quote'), s.get('accent'), s.get('quote_post'), True)}</h1>
<div class="abs" style="left:310px;top:330px;width:880px;height:880px;border-radius:50%;background:{HON}"></div>
<img class="abs" style="left:300px;top:230px;height:{ph}px" src="{uri}">
<div class="abs" style="left:80px;top:1000px;width:300px;color:#fff"><div style="font-size:42px;font-weight:800;line-height:1.1">Paul<br>Schleburg</div><div style="font-size:26px;color:#D5DEEA;margin-top:12px;line-height:1.3">{E(s.get('role', 'Ihr persönlicher Ansprechpartner'))}</div></div>
<img src="{c.L_DUNKEL}" style="position:absolute;left:70px;bottom:36px;height:88px">''')


def p_objekt(c):
    s = c.s; im = s['image']; st = s.get('stamp', ['NEU IM', 'ANGEBOT'])
    return c.page(f'''<div class="bgd"></div>
<img class="abs" style="left:0;top:0;width:1080px;height:860px;object-fit:cover;{c.fpos(im,1080,860,540,400)}" src="{c.photo(im)}">
{c.curve(680, NB, 670, 170, 60, 190)}
{c.stamp(st[0], st[1] if len(st) > 1 else '', 760, 520, 250, 8, fs1=30, fs2=30)}
<div class="abs" style="left:80px;top:870px;color:{HON};font-weight:700;font-size:34px;letter-spacing:3px">{E(s.get('kicker', ''))}</div>
<h1 class="abs" style="left:80px;top:925px;width:920px;color:#fff;font-weight:800;font-size:70px;line-height:1.05;letter-spacing:-1.2px">{c.hl(s.get('headline'), s.get('accent'), s.get('headline_post'), True)}</h1>
<p class="abs" style="left:80px;top:1130px;width:900px;color:#D5DEEA;font-size:34px">{E(s.get('text', ''))}</p>
{c.foot(True)}''')


def p_bewertung(c):
    s = c.s
    uri, (w, h) = c.cutout(s.get('device', '1g6F5QhYkzIS0Dz6Xc9Doc1Tsi4k_6QW3'))
    lw = 880; lh = int(lw * h / w); top = 500
    return c.page(f'''<div class="bgd"></div>
<h1 class="abs" style="left:80px;top:80px;width:920px;color:#fff;font-weight:800;font-size:90px;line-height:1.02;letter-spacing:-2px">{c.hl(s.get('headline', 'Was ist Ihre Immobilie'), s.get('accent', 'wirklich'), s.get('headline_post', 'wert?'), True)}</h1>
<p class="abs" style="left:80px;top:395px;width:640px;color:#D5DEEA;font-size:34px;line-height:1.35">{E(s.get('text', 'Kostenlos und unverbindlich, in wenigen Minuten.'))}</p>
{c.curve(560, CRE, 790, 170, 20, 190)}
<img class="abs" style="left:100px;top:{top+20}px;width:{lw}px;filter:drop-shadow(0 40px 50px rgba(0,0,0,.45))" src="{uri}">
{c.stamp(*s.get('stamp', ['100 %', 'KOSTENLOS']), 790, 330, 210, -10)}
{c.foot(False)}''')


def mw_card(c, x, y, w, h, price, d, rot, fs):
    col = HON if d == 'up' else '#3F6E95'
    arrow = (f'<path d="M0 34 L34 0 L68 34 L46 34 L46 80 L22 80 L22 34 Z" fill="{col}"/>' if d == 'up'
             else f'<path d="M0 46 L34 80 L68 46 L46 46 L46 0 L22 0 L22 46 Z" fill="{col}"/>')
    ico = f'<svg width="{int(h*.30)}" viewBox="0 0 100 90" fill="none" stroke="{NB}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"><path d="M8 46 L50 10 L92 46"/><path d="M22 40 V78 Q22 82 26 82 H74 Q78 82 78 78 V40"/></svg>'
    return (f'<div class="abs" style="left:{x}px;top:{y}px;width:{w}px;height:{h}px;background:{CRE};border-radius:30px;'
            f'transform:rotate({rot}deg);box-shadow:0 22px 44px rgba(0,0,0,.38);display:flex;flex-direction:column;align-items:center;justify-content:space-evenly">'
            f'{ico}<div style="font-weight:800;font-size:{fs}px;color:{NB};letter-spacing:-.5px">{E(price)}</div>'
            f'<svg width="{int(h*.22)}" viewBox="0 0 68 80">{arrow}</svg></div>')


def mw_pin(c, tx, ty, w, h, price, d, fs=34, style=0):
    """Preis-Marker, der mit seiner Spitze (tx,ty) auf ein Gebaeude zeigt. style 0 = weiss, 1 = nachtblau, 2 = glas, 3 = pille."""
    dark = style in (1, 2, 3)
    col = ('#3DCB7A' if d == 'up' else '#FF6464') if dark else ('#2E9E5B' if d == 'up' else '#D64545')
    arrow = (f'<path d="M0 34 L34 0 L68 34 L46 34 L46 80 L22 80 L22 34 Z" fill="{col}"/>' if d == 'up'
             else f'<path d="M0 46 L34 80 L68 46 L46 46 L46 0 L22 0 L22 46 Z" fill="{col}"/>')
    dot = (f'<div class="abs" style="left:{tx-11}px;top:{ty-11}px;width:22px;height:22px;border-radius:50%;background:{HON};border:4px solid #fff;box-shadow:0 4px 10px rgba(0,0,0,.4)"></div>')
    if style == 3:
        ph_, pw = 84, 300
        pill = (f'<div class="abs" style="left:{tx-pw//2}px;top:{ty-70-ph_}px;width:{pw}px;height:{ph_}px;background:{NB};border-radius:42px;border:3px solid {HON};'
                f'box-shadow:0 14px 30px rgba(0,0,0,.4);display:flex;align-items:center;justify-content:center;gap:16px;color:#fff;font-weight:800;font-size:38px;letter-spacing:-.5px">'
                f'<svg height="40" viewBox="0 0 68 80">{arrow}</svg>{E(price)}</div>'
                f'<div class="abs" style="left:{tx-2}px;top:{ty-70}px;width:4px;height:70px;background:{HON}"></div>')
        return pill + dot
    ico_c = '#fff' if dark else NB
    ico = f'<svg width="{int(h*.28)}" viewBox="0 0 100 90" fill="none" stroke="{ico_c}" stroke-width="7" stroke-linejoin="round" stroke-linecap="round"><path d="M8 46 L50 10 L92 46"/><path d="M22 40 V78 Q22 82 26 82 H74 Q78 82 78 78 V40"/></svg>'
    tail = 30
    if style == 1:
        bg = f'background:{NB};border-top:8px solid {HON};'; tc = NB; txt = '#fff'
    elif style == 2:
        bg = 'background:rgba(31,59,87,.58);backdrop-filter:blur(14px);-webkit-backdrop-filter:blur(14px);border:2px solid rgba(255,255,255,.45);'; tc = 'rgba(31,59,87,.58)'; txt = '#fff'
    else:
        bg = f'background:{CRE};border-top:8px solid {HON};'; tc = CRE; txt = NB
    return (f'<div class="abs" style="left:{tx-w//2}px;top:{ty-tail-h}px;width:{w}px;height:{h}px;{bg}border-radius:26px;'
            f'box-shadow:0 18px 36px rgba(0,0,0,.40);display:flex;flex-direction:column;align-items:center;justify-content:space-evenly">'
            f'{ico}<div style="font-weight:800;font-size:{fs}px;color:{txt};letter-spacing:-.5px">{E(price)}</div>'
            f'<svg width="{int(h*.2)}" viewBox="0 0 68 80">{arrow}</svg></div>'
            f'<div class="abs" style="left:{tx-20}px;top:{ty-tail-2}px;width:0;height:0;border-left:20px solid transparent;border-right:20px solid transparent;border-top:{tail}px solid {tc};filter:drop-shadow(0 8px 6px rgba(0,0,0,.25))"></div>'
            + dot)


def mw_common(c):
    s = c.s
    cards = s.get('cards') or [{'v': '595.000 €', 'd': 'up'}, {'v': '640.000 €', 'd': 'down'}, {'v': '615.000 €', 'd': 'up'}]
    return cards


def p_marktwert(c):
    s = c.s; im = s['image']; W, H, FH = c.W, c.H, c.FH; ph = H - FH
    lay = s.get('layout', 1)
    cards = mw_common(c)
    cd = ''.join(mw_pin(c, k['x'], k['y'], 170, 205, k['v'], k['d'], fs=29, style=s.get('pin', 0)) for k in cards)
    tl = s.get('top') == 'light'
    head = c.hl(s.get('headline', 'Was ist Ihre Immobilie'), s.get('accent', 'wirklich'), s.get('headline_post', 'wert?'), not tl)
    h1 = f'<h1 class="abs" style="left:70px;top:70px;width:940px;color:{NB if tl else '#fff'};font-weight:800;font-size:92px;line-height:1.03;letter-spacing:-2px;text-wrap:balance">{head}</h1>'
    photo = f'<img class="abs" style="left:0;top:0;width:{W}px;height:{ph}px;object-fit:cover;{c.fpos(im, W, ph, W//2, ph//2)}" src="{c.photo(im)}">'
    shade = f'<div class="abs" style="left:0;top:0;width:{W}px;height:{ph}px;background:linear-gradient(180deg,rgba(31,59,87,.88) 0%,rgba(31,59,87,.55) 38%,rgba(31,59,87,.10) 70%,rgba(31,59,87,.30) 100%)"></div>'
    banner = s.get('banner', 'Kostenlose Marktwert-Einschätzung online anfragen.')
    src = f'<p class="abs" style="left:40px;top:{ph-44}px;color:#fff;opacity:.9;font-size:22px;text-shadow:0 1px 6px rgba(0,0,0,.6)">{E(s.get("source", ""))}</p>'
    if lay == 1:   # Angebotsleiste unten ueber dem Footer
        cta = (f'<div class="abs" style="left:0;top:{ph-110}px;width:{W}px;height:110px;background:{NB};border-top:8px solid {HON};display:flex;align-items:center;justify-content:center;'
               f'color:#fff;font-weight:700;font-size:38px;letter-spacing:-.5px">{E(banner)}</div>')
        stamp = c.stamp(*s.get('stamp', ['100 %', 'KOSTENLOS']), 850, ph-110-210, 190, -10)
        src = src.replace(f'top:{ph-44}px', f'top:{ph-110-44}px')
        body = f'{photo}{shade}{h1}{cd}{stamp}{cta}{src}'
    elif lay == 2:  # Diagonale: oben Nachtblau mit Headline + Angebot, darunter Foto
        y0, y1 = 545, 455
        body = (f'<div class="abs" style="left:0;top:0;width:{W}px;height:{ph}px;clip-path:polygon(0 {y0}px,100% {y1}px,100% 100%,0 100%)">{photo}</div>'
                f'<svg class="abs" style="left:0;top:0" width="{W}" height="{ph}" viewBox="0 0 {W} {ph}"><path d="M0 {y0} L{W} {y1}" stroke="{HON}" stroke-width="12" fill="none"/></svg>'
                f'{h1.replace("top:70px", "top:105px") if not banner else h1}' + (f'<p class="abs" style="left:70px;top:392px;width:940px;color:#D5DEEA;font-size:36px;font-weight:500;line-height:1.3">{E(banner)}</p>' if banner else '') +
                f'{cd}{c.stamp(*s.get("stamp", ["100 %", "KOSTENLOS"]), 850, ph-250, 190, -10)}{src}')
    else:           # Stempel traegt die Aussage, kein Balken
        body = (f'{photo}{shade}{h1}{cd}'
                f'{c.stamp(*s.get("stamp", ["Kostenlose", "Bewertung"]), 800, 262, 230, -8, 28, 28)}{src}')
    return c.page(f'<div class="{'bgl' if tl and lay == 2 else 'bgd'}"></div>{body}{c.foot(s.get('foot') != 'light')}{'<div class="abs" style="left:0;top:'+str(ph-5)+'px;width:'+str(W)+'px;height:10px;background:'+HON+'"></div>' if s.get('foot') == 'light' else ''}')


def l_marktwert(c):
    """Querformat: Diagonale, oben dunkel mit Headline, Foto mit schwebenden Preis-Kacheln, heller Footer.
    Pin-Spitzen (x,y) in Foto-Box-Koordinaten (1200 x ph); s['off'] = vertikaler Bildausschnitt in px."""
    s = c.s; im = s['image']; W, H, FH = c.W, c.H, c.FH; ph = H - FH
    cards = mw_common(c)
    cd = ''.join(mw_pin(c, k['x'], k['y'], 150, 180, k['v'], k['d'], fs=26, style=s.get('pin', 0)) for k in cards)
    iw, ih = Image.open(os.path.join(c.pool, im + '.jpg')).size
    hs = ih * W / iw; off = s.get('off', 407)
    pos = f'object-position:50% {min(100, max(0, off / max(1, hs - ph) * 100)):.1f}%'
    y0, y1 = 360, 290
    head = c.hl(s.get('headline', 'Was ist Ihre Immobilie'), s.get('accent', 'wirklich'), s.get('headline_post', 'wert?'), True)
    return c.page(f'''<div class="bgd"></div>
<div class="abs" style="left:0;top:0;width:{W}px;height:{ph}px;clip-path:polygon(0 {y0}px,100% {y1}px,100% 100%,0 100%)"><img class="abs" style="left:0;top:0;width:{W}px;height:{ph}px;object-fit:cover;{pos}" src="{c.photo(im)}"></div>
<svg class="abs" style="left:0;top:0" width="{W}" height="{ph}" viewBox="0 0 {W} {ph}"><path d="M0 {y0} L{W} {y1}" stroke="{HON}" stroke-width="10" fill="none"/></svg>
<h1 class="abs" style="left:70px;top:58px;width:1060px;color:#fff;font-weight:800;font-size:80px;line-height:1.04;letter-spacing:-2px">{head}</h1>
{cd}
{c.stamp(*s.get('stamp', ['100 %', 'KOSTENLOS']), W-175, ph-165, 145, -10, 22, 20)}
<p class="abs" style="left:34px;top:{ph-38}px;color:#fff;opacity:.9;font-size:20px;text-shadow:0 1px 6px rgba(0,0,0,.6)">{E(s.get('source', ''))}</p>
<div class="abs" style="left:0;top:{ph-5}px;width:{W}px;height:10px;background:{HON}"></div>
{c.foot(False)}''')


# =============== Querformat 1200x900 (Google) ===============
def l_foto(c):
    """tipp / liste / mythos / objekt / bewertung: Foto mit Karte links."""
    s = c.s; t = s['template']; im = s.get('image')
    W, H, FH = c.W, c.H, c.FH
    if t == 'mythos':
        head = f'<p style="color:{HON};font-weight:800;font-size:34px;letter-spacing:5px;margin-bottom:10px">MYTHOS</p><h1 style="color:#fff;font-weight:800;font-size:40px;line-height:1.1;text-decoration:line-through;text-decoration-color:{HON};text-decoration-thickness:4px">{E(s["myth"])}</h1><p style="color:#fff;font-weight:800;font-size:34px;letter-spacing:5px;margin:26px 0 8px"><span class="mkd">FAKT</span></p><p style="color:#fff;font-weight:700;font-size:38px;line-height:1.12">{c.hl(s.get("fact"), s.get("accent"), s.get("fact_post"), True)}</p>'
    elif t == 'liste':
        li = ''.join(f'<div style="display:flex;align-items:center;gap:16px;margin-top:12px"><div style="flex:none;width:36px;height:36px;border-radius:50%;background:{HON};color:{NB2};font-weight:800;font-size:22px;display:flex;align-items:center;justify-content:center">✓</div><div style="font-size:27px;font-weight:600;color:#fff">{E(x)}</div></div>' for x in s['items'][:4])
        head = f'<h1 style="color:#fff;font-weight:800;font-size:46px;line-height:1.08;letter-spacing:-1px">{c.hl(s.get("headline"), s.get("accent"), s.get("headline_post"), True)}</h1><div style="margin-top:14px">{li}</div>'
    else:
        pill = ''
        if t == 'tipp': pill = f'<div style="display:inline-block;background:{HON};color:{NB2};font-weight:800;font-size:30px;letter-spacing:4px;padding:8px 28px;border-radius:40px;margin-bottom:18px;transform:rotate(-3deg);align-self:flex-start">{E(s.get("pill", "TIPP"))}</div>'
        if t == 'objekt': pill = f'<p style="color:{HON};font-weight:700;font-size:22px;letter-spacing:3px;margin-bottom:12px">{E(s.get("kicker", ""))}</p>'
        head = f'{pill}<h1 style="color:#fff;font-weight:800;font-size:50px;line-height:1.07;letter-spacing:-1px">{c.hl(s.get("headline"), s.get("accent"), s.get("headline_post"), True)}</h1><p style="color:#D5DEEA;font-size:26px;line-height:1.35;margin-top:18px">{E(s.get("text", ""))}</p>'
    if t == 'bewertung':
        uri, (dw, dh) = c.cutout(s.get('device', '1g6F5QhYkzIS0Dz6Xc9Doc1Tsi4k_6QW3'))
        if dh > dw:  # Handy/Hand: unten und rechts über den Rand hinaus, Anschnitt liegt unter Footer/Goldlinie
            dw_ = 570; dh_ = int(dw_ * dh / dw)
            img = f'<img class="abs" style="left:640px;top:{(H-FH)+10-dh_}px;width:{dw_}px;filter:drop-shadow(0 30px 40px rgba(0,0,0,.45))" src="{uri}">'
        else:
            img = f'<img class="abs" style="left:560px;top:{(H-FH)//2-int(620*dh/dw/2)}px;width:620px;filter:drop-shadow(0 30px 40px rgba(0,0,0,.45))" src="{uri}">'
        img += f'<div class="abs" style="left:0;top:{H-FH-5}px;width:{W}px;height:10px;background:{HON}"></div>'
    else:
        img = f'<img class="abs" style="left:400px;top:0;width:800px;height:{H-FH}px;object-fit:cover;{c.fpos(im,800,H-FH,500,330)}" src="{c.photo(im)}">'
    ph = H - FH
    panel = f'<svg class="abs" style="left:0;top:0" width="{W}" height="{ph}" viewBox="0 0 {W} {ph}"><polygon points="0,0 690,0 590,{ph} 0,{ph}" fill="{NB}"/><polyline points="690,0 590,{ph}" stroke="{HON}" stroke-width="10" fill="none"/></svg>'
    txt = f'<div class="abs" style="left:56px;top:0;width:{440 if t=='bewertung' else 520}px;height:{ph}px;display:flex;flex-direction:column;justify-content:center">{head}</div>'
    return c.page(f'<div class="bgd"></div>{panel+img if t=="bewertung" else img+panel}{txt}{c.foot(True)}')


def l_zahl(c):
    s = c.s; n = len(s['number']); fs = 250 if n <= 5 else 200
    return c.page(f'''<div class="bgd"></div>
<div class="abs" style="left:50px;top:40px;font-size:{fs}px;font-weight:800;line-height:1;color:{HON};letter-spacing:-9px;white-space:nowrap">{E(s['number'])}<span style="font-size:{int(fs*.52)}px;letter-spacing:-3px"> {E(s.get('unit',''))}</span></div>
<h1 class="abs" style="left:60px;top:310px;width:1060px;color:#fff;font-weight:800;font-size:56px;line-height:1.06;letter-spacing:-1px">{c.hl(s.get('headline'), s.get('accent'), s.get('headline_post'), True)}</h1>
{c.diag(520, CRE, 380, 90, 20)}
<p class="abs" style="left:60px;top:615px;width:1060px;color:{NB};font-size:30px;line-height:1.35;font-weight:500">{E(s.get('text',''))}</p>
{c.src(725)}{c.foot(False)}''')


def l_diagramm(c):
    s = c.s; vals = [(a, float(b)) for a, b in s['bars']]
    n = len(vals); bw = min(90, int(560 / n * .75)); gap = min(50, int((560 - n * bw) / max(1, n - 1))) if n > 1 else 0
    x0 = int((640 - (n * bw + (n - 1) * gap)) / 2)
    bars = bars_svg(vals, 640, 560, 400, 300, bw, gap, x0, fsv=26, fsl=22)
    pill = s.get('pill')
    return c.page(f'''<div class="bgl"></div>
<h1 class="abs" style="left:60px;top:60px;width:470px;color:{NB};font-weight:800;font-size:56px;line-height:1.05;letter-spacing:-1px">{c.hl(s.get('headline'), s.get('accent'), s.get('headline_post'), False)}</h1>
<p class="abs" style="left:60px;top:330px;width:440px;color:#41566B;font-size:27px;line-height:1.35">{E(s.get('subtitle',''))}</p>
<div class="abs" style="left:520px;top:50px;width:640px;height:690px;background:#fff;border-radius:40px;box-shadow:0 26px 50px rgba(14,34,57,.18)"></div>
<svg class="abs" style="left:520px;top:100px" width="640" height="560" viewBox="0 0 640 560"><line x1="20" y1="440" x2="620" y2="440" stroke="#D5DEEA" stroke-width="3"/><g transform="translate(0,40)">{bars}</g></svg>
{c.pill(pill, 790, 20, fs=26, rot=4) if pill else ''}
{c.src(755)}{c.foot(False)}''')


def l_gesicht(c):
    s = c.s
    uri, (w, h) = c.cutout(s.get('cutout', '1Yu7iFzod_FkkPci0gUfTYnTq9meqMvkw'))
    ph = 840; pw = int(ph * w / h)
    return c.page(f'''<div class="bgd"></div>
<div class="abs" style="left:560px;top:150px;width:700px;height:700px;border-radius:50%;background:{HON}"></div>
<img class="abs" style="left:{820-pw//2}px;top:60px;height:{ph}px" src="{uri}">
<div class="abs" style="left:60px;top:50px;color:{HON};font-weight:800;font-size:120px;line-height:.6">„</div>
<h1 class="abs" style="left:60px;top:150px;width:520px;color:#fff;font-weight:800;font-size:46px;line-height:1.1;letter-spacing:-1px">{c.hl(s.get('quote'), s.get('accent'), s.get('quote_post'), True)}</h1>
<div class="abs" style="left:60px;top:560px;width:380px;color:#fff"><div style="font-size:36px;font-weight:800;line-height:1.1">Paul Schleburg</div><div style="font-size:22px;color:#D5DEEA;margin-top:8px">{E(s.get('role','Ihr persönlicher Ansprechpartner'))}</div></div>
<img src="{c.L_DUNKEL}" style="position:absolute;left:56px;bottom:30px;height:72px">''')


PORTRAIT = {'zahl': p_zahl, 'diagramm': p_diagramm, 'tipp': p_tipp, 'liste': p_liste, 'mythos': p_mythos,
            'gesicht': p_gesicht, 'objekt': p_objekt, 'bewertung': p_bewertung, 'marktwert': p_marktwert}
LAND = {'zahl': l_zahl, 'diagramm': l_diagramm, 'gesicht': l_gesicht, 'tipp': l_foto, 'liste': l_foto,
        'mythos': l_foto, 'objekt': l_foto, 'bewertung': l_foto, 'marktwert': l_marktwert}


def build_html(spec, pool):
    c = Ctx(spec, pool)
    t = spec['template']
    fn = (LAND if c.land else PORTRAIT).get(t)
    if fn is None:
        raise SystemExit(f'Vorlage {t} gibt es nicht im Format {spec.get("format")}')
    return fn(c), c.W, c.H


def render(spec, out, pool):
    from playwright.sync_api import sync_playwright
    h, W, H = build_html(spec, pool)
    tmp = out + '.html'
    open(tmp, 'w', encoding='utf-8').write(h)
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': W, 'height': H})
        pg.goto('file://' + os.path.abspath(tmp))
        pg.wait_for_timeout(600)
        png = out if out.lower().endswith('.png') else out + '.tmp.png'
        pg.screenshot(path=png)
        b.close()
    if png != out:
        Image.open(png).convert('RGB').save(out, 'JPEG', quality=92)
        os.remove(png)
    os.remove(tmp)


if __name__ == '__main__':
    a = sys.argv[1:]
    pool = '/tmp/pool'
    if '--pool' in a:
        i = a.index('--pool'); pool = a[i + 1]; del a[i:i + 2]
    render(json.load(open(a[0])), a[1], pool)
