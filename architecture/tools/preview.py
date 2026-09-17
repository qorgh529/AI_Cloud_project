# -*- coding: utf-8 -*-
"""Approximate HTML renderer for the subset of draw.io styles used here."""
import xml.etree.ElementTree as ET, html, sys, os, re

def sty(s):
    d = {}
    for part in (s or '').split(';'):
        if not part: continue
        if '=' in part:
            k, v = part.split('=', 1); d[k] = v
        else: d[part] = '1'
    return d

def geo(c):
    g = c.find('mxGeometry')
    if g is None: return None
    return dict(x=float(g.get('x') or 0), y=float(g.get('y') or 0),
                w=float(g.get('width') or 0), h=float(g.get('height') or 0))

def anchor(g, ax, ay):
    return g['x'] + g['w'] * ax, g['y'] + g['h'] * ay

def render(diagram, outdir, idx):
    m = diagram.find('mxGraphModel')
    W, H = int(m.get('pageWidth')), int(m.get('pageHeight'))
    cells = m.find('root').findall('mxCell')
    by_id = {c.get('id'): c for c in cells}
    divs, paths, elabels = [], [], []

    for c in cells:
        st = sty(c.get('style')); g = geo(c); val = c.get('value') or ''
        if c.get('edge') == '1':
            s, t = by_id.get(c.get('source')), by_id.get(c.get('target'))
            if not s or not t: continue
            gs, gt = geo(s), geo(t)
            ex, ey = float(st.get('exitX', 0.5)), float(st.get('exitY', 0.5))
            nx, ny = float(st.get('entryX', 0.5)), float(st.get('entryY', 0.5))
            x1, y1 = anchor(gs, ex, ey); x2, y2 = anchor(gt, nx, ny)
            if ex in (0.0, 1.0):          # horizontal exit
                mx = (x1 + x2) / 2
                d = f"M{x1},{y1} L{mx},{y1} L{mx},{y2} L{x2},{y2}"
            else:                          # vertical exit
                my = (y1 + y2) / 2
                d = f"M{x1},{y1} L{x1},{my} L{x2},{my} L{x2},{y2}"
            col = st.get('strokeColor', '#000'); sw = st.get('strokeWidth', '1')
            dash = 'stroke-dasharray="6 4"' if st.get('dashed') == '1' else ''
            paths.append(f'<path d="{d}" fill="none" stroke="{col}" stroke-width="{sw}" {dash} '
                         f'marker-end="url(#ah{html.escape(col[1:])})"/>')
            if val:
                elabels.append((( x1+x2)/2, (y1+y2)/2, val, col, st.get('fontSize','11')))
            continue
        if g is None or c.get('vertex') != '1': continue
        css = (f"left:{g['x']}px;top:{g['y']}px;width:{g['w']}px;height:{g['h']}px;"
               f"font-size:{st.get('fontSize','12')}px;color:{st.get('fontColor','#202124')};")
        if st.get('fontStyle') == '1': css += 'font-weight:700;'
        if st.get('shape') == 'image':
            img = c.get('style').split('image=', 1)[1].rstrip(';')
            img = img.replace('data:image/svg+xml,', 'data:image/svg+xml;base64,')
            divs.append(f'<img class="ic" style="{css}" src="{html.escape(img, quote=True)}"/>')
            continue
        if st.get('text') == '1':
            al = st.get('align', 'center'); va = st.get('verticalAlign', 'top')
            fl = {'center': 'center', 'left': 'flex-start', 'right': 'flex-end'}[al]
            vl = {'top': 'flex-start', 'middle': 'center', 'bottom': 'flex-end'}[va]
            css += f"justify-content:{fl};align-items:{vl};text-align:{al};"
            divs.append(f'<div class="tx" style="{css}">{val}</div>')
            continue
        fill = st.get('fillColor', 'none'); strk = st.get('strokeColor', '#000')
        css += (f"background:{'transparent' if fill=='none' else fill};"
                f"border:{2 if st.get('dashed')=='1' else 1}px "
                f"{'dashed' if st.get('dashed')=='1' else 'solid'} {strk};"
                f"border-radius:{6 if st.get('rounded')!='0' else 0}px;"
                f"padding:{st.get('spacingTop','4')}px 8px 0 {st.get('spacingLeft','8')}px;"
                f"text-align:{st.get('align','left')};box-sizing:border-box;overflow:hidden;")
        divs.append(f'<div class="bx" style="{css}">{val}</div>')

    cols = sorted({p.split('stroke="')[1].split('"')[0] for p in paths}) if paths else []
    defs = ''.join(f'<marker id="ah{c[1:]}" markerWidth="9" markerHeight="9" refX="8" refY="3" '
                   f'orient="auto"><path d="M0,0 L8,3 L0,6 z" fill="{c}"/></marker>' for c in cols)
    el = ''.join(f'<div class="el" style="left:{x-70}px;top:{y-9}px;color:{c};font-size:{fs}px">'
                 f'{html.escape(v)}</div>' for x, y, v, c, fs in elabels)
    doc = f"""<!DOCTYPE html><meta charset="utf-8"><style>
html,body{{margin:0;padding:0;background:#fff;
font-family:"Noto Sans KR","Malgun Gothic",Helvetica,Arial,sans-serif;}}
#c{{position:relative;width:{W}px;height:{H}px;}}
.bx,.tx,.ic,.el{{position:absolute;}}
.tx{{display:flex;line-height:1.25;white-space:pre-wrap;}}
.bx{{line-height:1.35;}}
.el{{width:140px;text-align:center;background:#fff;line-height:1.1;}}
svg{{position:absolute;left:0;top:0;pointer-events:none;}}
table{{border-collapse:collapse}} td,th{{padding:1px 4px;vertical-align:top}}
code{{background:#f1f3f4;padding:0 3px;border-radius:3px;font-size:.92em}}
</style><div id="c"><svg width="{W}" height="{H}"><defs>{defs}</defs>{''.join(paths)}</svg>
{''.join(divs)}{el}</div>"""
    f = os.path.join(outdir, f'page{idx}.html')
    open(f, 'w', encoding='utf-8').write(doc)
    return f, W, H

if __name__ == '__main__':
    src, outdir = sys.argv[1], sys.argv[2]
    os.makedirs(outdir, exist_ok=True)
    for i, d in enumerate(ET.parse(src).getroot().findall('diagram'), 1):
        f, W, H = render(d, outdir, i)
        print(f, W, H)
