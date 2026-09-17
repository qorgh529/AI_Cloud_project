# -*- coding: utf-8 -*-
"""Helpers to emit draw.io (mxGraph) XML using official GCP product icons."""
import json, os

ICONS = json.load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'gcpicons.json')))

ICON_STYLE = ("editableCssRules=.*;html=1;shape=image;verticalLabelPosition=bottom;"
              "labelBackgroundColor=none;verticalAlign=top;aspect=fixed;imageAspect=0;"
              "image=data:image/svg+xml,{b64};")

# Google brand palette
BLUE, RED, YEL, GRN, GREY = '#4285F4', '#EA4335', '#FBBC04', '#34A853', '#5F6368'
INK = '#202124'


def esc(s):
    return (str(s).replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;')
            .replace('"', '&quot;').replace('\n', '&#10;'))


class Page:
    def __init__(self, name, w=2300, h=1800):
        self.name, self.w, self.h = name, w, h
        self.cells = []

    def raw(self, xml):
        self.cells.append(xml)

    def box(self, cid, x, y, w, h, label='', stroke=BLUE, fill='none', dashed=1,
            fs=13, fc=None, extra='', rounded=1):
        fc = fc or stroke
        st = (f"rounded={rounded};whiteSpace=wrap;html=1;dashed={dashed};strokeColor={stroke};"
              f"fillColor={fill};verticalAlign=top;align=left;fontSize={fs};fontStyle=1;"
              f"fontColor={fc};spacingLeft=14;spacingTop=6;arcSize=6;{extra}")
        self.raw(f'<mxCell id="{cid}" value="{esc(label)}" style="{st}" vertex="1" parent="1">'
                 f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def text(self, cid, x, y, w, h, label, fs=12, bold=0, color=INK, align='center',
             valign='top', extra=''):
        st = (f"text;html=1;whiteSpace=wrap;fontSize={fs};fontStyle={bold};fontColor={color};"
              f"align={align};verticalAlign={valign};{extra}")
        self.raw(f'<mxCell id="{cid}" value="{esc(label)}" style="{st}" vertex="1" parent="1">'
                 f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def icon(self, cid, title, cx, y, label='', ih=46, lw=200, lfs=11, lcolor=INK, lbold=0):
        """Place a GCP icon horizontally centred on cx, top at y, with a caption below."""
        meta = ICONS[title]
        iw = round(ih * float(meta['w']) / float(meta['h']))
        x = cx - iw / 2.0
        st = ICON_STYLE.format(b64=meta['b64'])
        self.raw(f'<mxCell id="{cid}" value="" style="{st}" vertex="1" parent="1">'
                 f'<mxGeometry x="{x}" y="{y}" width="{iw}" height="{ih}" as="geometry"/></mxCell>')
        if label:
            self.text(cid + '_l', cx - lw / 2.0, y + ih + 4, lw, 40, label,
                      fs=lfs, bold=lbold, color=lcolor)
        return cid

    def edge(self, cid, src, tgt, label='', color=BLUE, dashed=0, sw=2, fs=11,
             exit=None, entry=None, extra='', style='orthogonalEdgeStyle'):
        pts = ''
        if exit:
            pts += f"exitX={exit[0]};exitY={exit[1]};exitDx=0;exitDy=0;"
        if entry:
            pts += f"entryX={entry[0]};entryY={entry[1]};entryDx=0;entryDy=0;"
        st = (f"edgeStyle={style};rounded=1;html=1;jettySize=auto;orthogonalLoop=1;"
              f"strokeColor={color};strokeWidth={sw};dashed={dashed};fontSize={fs};"
              f"fontColor={color};endArrow=block;endFill=1;labelBackgroundColor=#FFFFFF;"
              f"{pts}{extra}")
        self.raw(f'<mxCell id="{cid}" value="{esc(label)}" style="{st}" edge="1" parent="1" '
                 f'source="{src}" target="{tgt}"><mxGeometry relative="1" as="geometry"/></mxCell>')
        return cid

    def note(self, cid, x, y, w, h, html, fill='#FFFFFF', stroke='#DADCE0', fs=11, align='left'):
        st = (f"rounded=1;whiteSpace=wrap;html=1;fillColor={fill};strokeColor={stroke};"
              f"align={align};verticalAlign=top;fontSize={fs};spacingLeft=10;spacingTop=4;"
              f"spacingRight=8;arcSize=6;")
        self.raw(f'<mxCell id="{cid}" value="{esc(html)}" style="{st}" vertex="1" parent="1">'
                 f'<mxGeometry x="{x}" y="{y}" width="{w}" height="{h}" as="geometry"/></mxCell>')
        return cid

    def to_xml(self):
        body = '\n        '.join(self.cells)
        return (f'  <diagram name="{esc(self.name)}" id="{esc(self.name)}">\n'
                f'    <mxGraphModel dx="1200" dy="800" grid="0" gridSize="10" guides="1" '
                f'tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" '
                f'pageWidth="{self.w}" pageHeight="{self.h}" math="0" shadow="0">\n'
                f'      <root>\n        <mxCell id="0"/>\n        <mxCell id="1" parent="0"/>\n'
                f'        {body}\n      </root>\n    </mxGraphModel>\n  </diagram>')


def write_file(path, pages):
    xml = ('<mxfile host="app.diagrams.net" agent="Claude" version="24.7.17" type="device">\n'
           + '\n'.join(p.to_xml() for p in pages) + '\n</mxfile>\n')
    with open(path, 'w', encoding='utf-8') as f:
        f.write(xml)
    return len(xml)
