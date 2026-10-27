from __future__ import annotations

"""Generate the InsightForge AIML-451 project dissertation as a DOCX file.

The repository does not include python-docx or LibreOffice, so this generator
uses the Office Open XML package format directly.  It is intentionally
reproducible: all project facts, screenshots, code excerpts, and report text
come from this workspace.
"""

from pathlib import Path
from textwrap import dedent
from xml.sax.saxutils import escape, quoteattr
from zipfile import ZIP_DEFLATED, ZipFile
import re


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "docs" / "InsightForge_Minor_Project_Dissertation_AIML451.docx"
DASHBOARD_IMAGE = ROOT / "docs" / "screenshots" / "dashboard.png"
ANALYSIS_IMAGE = ROOT / "docs" / "screenshots" / "analysis.png"
INSTITUTE_LOGO = ROOT / "docs" / "report_assets" / "institute_logo.jpeg"
DIAGRAM_DIR = ROOT / "docs" / "report_assets" / "diagrams"
DIAGRAMS = {
    "architecture": ("rId8", 8),
    "context_dfd": ("rId9", 9),
    "upload_flow": ("rId10", 10),
    "structure_chart": ("rId11", 11),
    "agent_flow": ("rId12", 12),
    "analysis_pipeline": ("rId13", 13),
    "api_boundary": ("rId14", 14),
    "er_model": ("rId17", 17),
    "job_states": ("rId15", 15),
    "deployment": ("rId16", 16),
}

NS_W = "http://schemas.openxmlformats.org/wordprocessingml/2006/main"
NS_R = "http://schemas.openxmlformats.org/officeDocument/2006/relationships"
NS_WP = "http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing"
NS_A = "http://schemas.openxmlformats.org/drawingml/2006/main"
NS_PIC = "http://schemas.openxmlformats.org/drawingml/2006/picture"


def clean_text(value: str) -> str:
    value = value.replace("\u2011", "-").replace("\u00a0", " ")
    return "".join(ch for ch in value if ch in "\n\t" or ord(ch) >= 32)


def xml_text(value: str) -> str:
    return escape(clean_text(value), {"\"": "&quot;"})


def run(text: str, *, bold: bool = False, italic: bool = False, size: int = 24,
        font: str = "Times New Roman", color: str | None = None,
        underline: bool = False) -> str:
    props = [f'<w:rFonts w:ascii={quoteattr(font)} w:hAnsi={quoteattr(font)} w:eastAsia={quoteattr(font)}/>']
    props.append(f'<w:sz w:val="{size}"/><w:szCs w:val="{size}"/>')
    if bold:
        props.append("<w:b/><w:bCs/>")
    if italic:
        props.append("<w:i/><w:iCs/>")
    if underline:
        props.append('<w:u w:val="single"/>')
    if color:
        props.append(f'<w:color w:val="{color}"/>')
    return f'<w:r><w:rPr>{"".join(props)}</w:rPr><w:t xml:space="preserve">{xml_text(text)}</w:t></w:r>'


def break_run(kind: str = "line") -> str:
    return f'<w:r><w:br w:type="{kind}"/></w:r>'


def paragraph(text: str = "", *, style: str | None = None, align: str = "both",
              bold: bool = False, italic: bool = False, size: int = 24,
              font: str = "Times New Roman", color: str | None = None,
              before: int = 0, after: int = 120, line: int = 360,
              first_indent: int = 0, left_indent: int = 0,
              keep_next: bool = False, outline: int | None = None,
              shade: str | None = None, border: str | None = None,
              page_break_before: bool = False,
              runs: list[dict] | None = None) -> str:
    ppr: list[str] = [f'<w:jc w:val="{align}"/>', f'<w:spacing w:before="{before}" w:after="{after}" w:line="{line}" w:lineRule="auto"/>']
    if style:
        ppr.insert(0, f'<w:pStyle w:val="{style}"/>')
    if first_indent:
        ppr.append(f'<w:ind w:firstLine="{first_indent}"/>')
    if left_indent:
        ppr.append(f'<w:ind w:left="{left_indent}"/>')
    if keep_next:
        ppr.append("<w:keepNext/>")
    if page_break_before:
        ppr.append("<w:pageBreakBefore/>")
    if outline is not None:
        ppr.append(f'<w:outlineLvl w:val="{outline}"/>')
    if shade:
        ppr.append(f'<w:shd w:val="clear" w:color="auto" w:fill="{shade}"/>')
    if border:
        ppr.append(f'<w:pBdr><w:top w:val="single" w:sz="4" w:space="4" w:color="{border}"/><w:bottom w:val="single" w:sz="4" w:space="4" w:color="{border}"/><w:left w:val="single" w:sz="4" w:space="4" w:color="{border}"/><w:right w:val="single" w:sz="4" w:space="4" w:color="{border}"/></w:pBdr>')
    if runs is None:
        runs = [{"text": text, "bold": bold, "italic": italic, "size": size, "font": font, "color": color}]
    run_xml: list[str] = []
    for item in runs:
        if item.get("break"):
            run_xml.append(break_run(item.get("break", "line")))
            continue
        run_xml.append(run(
            str(item.get("text", "")),
            bold=bool(item.get("bold", False)),
            italic=bool(item.get("italic", False)),
            size=int(item.get("size", size)),
            font=str(item.get("font", font)),
            color=item.get("color", color),
            underline=bool(item.get("underline", False)),
        ))
    return f'<w:p><w:pPr>{"".join(ppr)}</w:pPr>{"".join(run_xml)}</w:p>'


def page_break() -> str:
    return paragraph(runs=[{"break": "page"}], after=0, line=240)


def heading(text: str, level: int = 1, *, page: bool = False) -> str:
    if level == 1:
        return paragraph(text, style="Heading1", align="left", bold=True, size=32,
                         before=0, after=240, line=360, keep_next=True, outline=0,
                         page_break_before=page)
    if level == 2:
        return paragraph(text, style="Heading2", align="left", bold=True, size=28,
                         before=180, after=120, line=360, keep_next=True, outline=1,
                         page_break_before=page)
    return paragraph(text, style="Heading3", align="left", italic=True, size=24,
                     before=120, after=80, line=360, keep_next=True, outline=2,
                     page_break_before=page)


def body(text: str, *, indent: bool = True, after: int = 120) -> str:
    return paragraph(clean_text(text), align="both", size=24, after=after,
                     first_indent=360 if indent else 0)


def bullet(text: str, level: int = 0) -> str:
    prefix = "• " if level == 0 else "◦ "
    return paragraph(prefix + text, align="left", size=24, after=60, first_indent=0, left_indent=360 + level * 240)


def code_block(text: str, *, size: int = 18) -> str:
    lines = clean_text(dedent(text).strip("\n")).splitlines()
    runs: list[dict] = []
    for index, line_text in enumerate(lines):
        if index:
            runs.append({"break": "line"})
        runs.append({"text": line_text, "font": "Courier New", "size": size})
    return paragraph(runs=runs, align="left", after=120, line=240, shade="F2F2F2", border="B7B7B7")


def caption(text: str) -> str:
    # Use a SEQ field inside every caption so Word can renumber figures/tables
    # after edits. The surrounding paragraph uses the university's Caption
    # style, allowing the List of Figures/Tables fields to update automatically.
    match = re.match(r"^(Figure|Table)\s+(\d+)\.\s+(.*)$", text)
    if not match:
        return paragraph(text, style="Caption", align="center", italic=True, size=20, after=160, line=240)
    label, number, title = match.groups()
    ppr = '<w:pStyle w:val="Caption"/><w:jc w:val="center"/><w:spacing w:after="160" w:line="240" w:lineRule="auto"/>'
    field = (
        f'<w:fldSimple w:instr="SEQ {label} \\* ARABIC">'
        f'<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:i/><w:sz w:val="20"/></w:rPr>'
        f'<w:t>{number}</w:t></w:r></w:fldSimple>'
    )
    return (
        f'<w:p><w:pPr>{ppr}</w:pPr>'
        f'{run(label + " ", italic=True, size=20)}{field}'
        f'{run(". " + title, italic=True, size=20)}</w:p>'
    )


def table(headers: list[str], rows: list[list[str]], *, widths: list[int] | None = None,
          font_size: int = 19) -> str:
    widths = widths or [2200] * len(headers)
    grid = "".join(f'<w:gridCol w:w="{width}"/>' for width in widths)
    parts = [f'<w:tbl><w:tblPr><w:tblW w:w="{sum(widths)}" w:type="dxa"/><w:tblLayout w:type="fixed"/><w:tblBorders><w:top w:val="single" w:sz="6" w:color="808080"/><w:left w:val="single" w:sz="6" w:color="808080"/><w:bottom w:val="single" w:sz="6" w:color="808080"/><w:right w:val="single" w:sz="6" w:color="808080"/><w:insideH w:val="single" w:sz="4" w:color="BFBFBF"/><w:insideV w:val="single" w:sz="4" w:color="BFBFBF"/></w:tblBorders></w:tblPr><w:tblGrid>{grid}</w:tblGrid>']
    all_rows = [headers] + rows
    for row_index, row_values in enumerate(all_rows):
        cells: list[str] = []
        for col_index, value in enumerate(row_values):
            fill = "D9EAF7" if row_index == 0 else "FFFFFF"
            cell_props = f'<w:tcPr><w:tcW w:w="{widths[col_index]}" w:type="dxa"/><w:shd w:val="clear" w:color="auto" w:fill="{fill}"/></w:tcPr>'
            cell_text = paragraph(str(value), align="left", bold=row_index == 0, size=font_size, after=40, line=240)
            cells.append(f'<w:tc>{cell_props}{cell_text}</w:tc>')
        tr_props = "<w:trPr><w:tblHeader/></w:trPr>" if row_index == 0 else ""
        parts.append(f'<w:tr>{tr_props}{"".join(cells)}</w:tr>')
    parts.append("</w:tbl>")
    return "".join(parts)


def section_properties(*, footer_id: str | None = None, page_format: str | None = None,
                       page_start: int | None = None, next_page: bool = False) -> str:
    type_xml = '<w:type w:val="nextPage"/>' if next_page else ""
    footer_xml = f'<w:footerReference w:type="default" r:id="{footer_id}"/>' if footer_id else ""
    num_xml = ""
    if page_format:
        num_xml = f'<w:pgNumType w:fmt="{page_format}"' + (f' w:start="{page_start}"' if page_start is not None else "") + '/>'
    return (
        f'<w:sectPr>{type_xml}{footer_xml}{num_xml}'
        '<w:pgSz w:w="11906" w:h="16838"/><w:pgMar w:top="1440" w:right="1440" w:bottom="1440" w:left="2160" w:header="720" w:footer="720" w:gutter="0"/>'
        '<w:cols w:space="720"/><w:docGrid w:linePitch="360"/></w:sectPr>'
    )


def section_break(*, footer_id: str | None = None, page_format: str | None = None,
                  page_start: int | None = None) -> str:
    return f'<w:p><w:pPr>{section_properties(footer_id=footer_id, page_format=page_format, page_start=page_start, next_page=True)}</w:pPr></w:p>'


def image_paragraph(rel_id: str, image_id: int, *, width_in: float = 6.2, height_in: float = 3.49) -> str:
    cx = int(width_in * 914400)
    cy = int(height_in * 914400)
    return (
        '<w:p><w:pPr><w:jc w:val="center"/><w:spacing w:after="80"/><w:keepNext/></w:pPr>'
        '<w:r><w:rPr><w:noProof/></w:rPr><w:drawing>'
        f'<wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{cx}" cy="{cy}"/><wp:docPr id="{image_id}" name="Picture {image_id}"/>'
        '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
        '<pic:pic><pic:nvPicPr><pic:cNvPr id="0" name="image.png"/><pic:cNvPicPr/></pic:nvPicPr>'
        '<pic:blipFill><a:blip r:embed="' + rel_id + '"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
        '<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="' + str(cx) + '" cy="' + str(cy) + '"/></a:xfrm><a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr>'
        '</pic:pic></a:graphicData></a:graphic></wp:inline>'
        '</w:drawing></w:r></w:p>'
    )


def toc_field(instruction: str) -> str:
    return paragraph(runs=[{"text": ""}])[:-len('</w:p>')] + f'<w:fldSimple w:instr={quoteattr(instruction)}><w:r><w:t>Updating field…</w:t></w:r></w:fldSimple></w:p>'


def footer_xml(page_format: str) -> str:
    field = '<w:fldSimple w:instr="PAGE"><w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:t>1</w:t></w:r></w:fldSimple>'
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        '<w:ftr xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">'
        '<w:p><w:pPr><w:tabs><w:tab w:val="right" w:pos="9000"/></w:tabs><w:spacing w:after="0"/></w:pPr>'
        '<w:r><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="20"/></w:rPr><w:t>Department of Artificial Intelligence and Machine Learning</w:t></w:r>'
        '<w:r><w:tab/></w:r>' + field + '</w:p></w:ftr>'
    )


def styles_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman" w:eastAsia="Times New Roman"/><w:sz w:val="24"/><w:szCs w:val="24"/></w:rPr></w:rPrDefault><w:pPrDefault><w:pPr><w:spacing w:after="120" w:line="360" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
  <w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:sz w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:after="360"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="40"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading1"><w:name w:val="heading 1"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="240" w:after="240"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="32"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading2"><w:name w:val="heading 2"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="180" w:after="120"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:b/><w:sz w:val="28"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Heading3"><w:name w:val="heading 3"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/><w:pPr><w:keepNext/><w:spacing w:before="120" w:after="80"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:i/><w:sz w:val="24"/></w:rPr></w:style>
  <w:style w:type="paragraph" w:styleId="Caption"><w:name w:val="caption"/><w:basedOn w:val="Normal"/><w:qFormat/><w:pPr><w:jc w:val="center"/><w:spacing w:after="160"/></w:pPr><w:rPr><w:rFonts w:ascii="Times New Roman" w:hAnsi="Times New Roman"/><w:i/><w:sz w:val="20"/></w:rPr></w:style>
</w:styles>'''


def document_xml(body_xml: str) -> str:
    return (
        '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
        f'<w:document xmlns:w="{NS_W}" xmlns:r="{NS_R}" xmlns:wp="{NS_WP}" xmlns:a="{NS_A}" xmlns:pic="{NS_PIC}">'
        f'<w:body>{body_xml}{section_properties(footer_id="rId3", page_format="decimal", page_start=1)}</w:body></w:document>'
    )


def relationships_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
  <Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
  <Relationship Id="rId2" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footerFront.xml"/>
  <Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/footer" Target="footerBody.xml"/>
  <Relationship Id="rId4" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/dashboard.png"/>
  <Relationship Id="rId5" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/analysis.png"/>
  <Relationship Id="rId6" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/institute_logo.jpeg"/>
  <Relationship Id="rId7" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/settings" Target="settings.xml"/>
  <Relationship Id="rId8" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/architecture.png"/>
  <Relationship Id="rId9" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/context_dfd.png"/>
  <Relationship Id="rId10" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/upload_flow.png"/>
  <Relationship Id="rId11" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/structure_chart.png"/>
  <Relationship Id="rId12" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/agent_flow.png"/>
  <Relationship Id="rId13" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/analysis_pipeline.png"/>
  <Relationship Id="rId14" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/api_boundary.png"/>
  <Relationship Id="rId15" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/job_states.png"/>
  <Relationship Id="rId16" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/deployment.png"/>
  <Relationship Id="rId17" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/er_model.png"/>
</Relationships>'''


def content_types_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
  <Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
  <Default Extension="xml" ContentType="application/xml"/>
  <Default Extension="png" ContentType="image/png"/>
  <Default Extension="jpeg" ContentType="image/jpeg"/>
  <Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
  <Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
  <Override PartName="/word/footerFront.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/word/footerBody.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.footer+xml"/>
  <Override PartName="/word/settings.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.settings+xml"/>
  <Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
  <Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''


def settings_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:settings xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
  <w:updateFields w:val="true"/>
  <w:zoom w:percent="100"/>
</w:settings>'''


def core_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
  <dc:title>InsightForge: AI Data Analyst — AIML-451 Minor Project Dissertation</dc:title>
  <dc:creator>Manan Lall</dc:creator>
  <dc:subject>Development-based project dissertation</dc:subject>
  <dc:description>Project report generated from the InsightForge workspace.</dc:description>
  <dcterms:created xsi:type="dcterms:W3CDTF">2026-10-26T00:00:00Z</dcterms:created>
</cp:coreProperties>'''


def app_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>InsightForge report generator</Application><DocSecurity>0</DocSecurity><ScaleCrop>false</ScaleCrop><HeadingPairs><vt:vector xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes" size="2" baseType="variant"><vt:variant><vt:lpstr>Heading 1</vt:lpstr></vt:variant><vt:variant><vt:i4>8</vt:i4></vt:variant></vt:vector></HeadingPairs><TitlesOfParts xmlns:vt="http://schemas.openxmlformats.org/officeDocument/2006/docPropsVTypes"><vt:vector size="8" baseType="lpstr"><vt:lpstr>Cover</vt:lpstr><vt:lpstr>Declaration</vt:lpstr><vt:lpstr>Certificate</vt:lpstr><vt:lpstr>Acknowledgement</vt:lpstr><vt:lpstr>Abstract</vt:lpstr><vt:lpstr>Contents</vt:lpstr><vt:lpstr>Chapters</vt:lpstr><vt:lpstr>Appendix</vt:lpstr></vt:vector></TitlesOfParts></Properties>'''


def root_rels_xml() -> str:
    return '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships"><Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/><Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/><Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>'''


class ReportBuilder:
    def __init__(self) -> None:
        self.parts: list[str] = []
        self.figure_number = 0
        self.table_number = 0

    def add(self, xml: str) -> None:
        self.parts.append(xml)

    def page(self) -> None:
        self.add(page_break())

    def h(self, text: str, level: int = 1, *, page: bool = False) -> None:
        self.add(heading(text, level, page=page))

    def p(self, text: str, *, indent: bool = True) -> None:
        self.add(body(text, indent=indent))

    def bullets(self, values: list[str]) -> None:
        for value in values:
            self.add(bullet(value))

    def code(self, text: str) -> None:
        self.add(code_block(text))

    def add_table(self, title: str, headers: list[str], rows: list[list[str]], widths: list[int] | None = None) -> None:
        self.table_number += 1
        self.add(caption(f"Table {self.table_number}. {title}"))
        self.add(table(headers, rows, widths=widths))

    def add_diagram(self, title: str, diagram: str) -> None:
        self.figure_number += 1
        self.code(diagram)
        self.add(caption(f"Figure {self.figure_number}. {title}"))

    def add_image(self, rel_id: str, image_id: int, title: str, *, width: float = 6.2, height: float = 3.49) -> None:
        self.figure_number += 1
        self.add(image_paragraph(rel_id, image_id, width_in=width, height_in=height))
        self.add(caption(f"Figure {self.figure_number}. {title}"))

    def output_xml(self) -> str:
        return document_xml("".join(self.parts))


def add_front_matter(r: ReportBuilder) -> None:
    # Cover page — deliberately no footer/page number.
    r.add(paragraph("UNIVERSITY SCHOOL OF AUTOMATION AND ROBOTICS", align="center", bold=True, size=28, after=100))
    r.add(paragraph("GURU GOBIND SINGH INDRAPRASTHA UNIVERSITY", align="center", bold=True, size=28, after=480))
    if INSTITUTE_LOGO.exists():
        r.add(image_paragraph("rId6", 6, width_in=1.25, height_in=0.72))
    r.add(paragraph("AIML-451: MINOR PROJECT - DISSERTATION", align="center", bold=True, size=26, after=500))
    r.add(paragraph("INSIGHTFORGE: AI DATA ANALYST", align="center", bold=True, size=40, after=520))
    r.add(paragraph("An intelligent, secure, and grounded web platform for conversational CSV analytics", align="center", italic=True, size=24, after=650))
    r.add(paragraph("Submitted in partial fulfillment of the requirements for the award of the degree of", align="center", size=22, after=120))
    r.add(paragraph("Bachelor of Technology in Artificial Intelligence and Machine Learning", align="center", bold=True, size=24, after=420))
    r.add(paragraph("Submitted by", align="center", size=22, after=100))
    r.add(paragraph("MANAN LALL", align="center", bold=True, size=26, after=80))
    r.add(paragraph("Enrollment No.: ______________________________", align="center", size=22, after=360))
    r.add(paragraph("Under the supervision of", align="center", size=22, after=100))
    r.add(paragraph("Ms. Nibha", align="center", bold=True, size=24, after=60))
    r.add(paragraph("Assistant Professor", align="center", size=22, after=420))
    r.add(paragraph("Department of Artificial Intelligence and Machine Learning", align="center", bold=True, size=22, after=60))
    r.add(paragraph("Dr. Akhilesh Das Gupta Institute of Professional Studies", align="center", size=22, after=60))
    r.add(paragraph("FC-26, Shastri Park, New Delhi", align="center", size=22, after=300))
    r.add(paragraph("November 2026", align="center", bold=True, size=24, after=0))
    # The cover is the only page without a footer. The preliminary section is
    # assigned its Roman footer at the section break before Chapter 1.
    r.add(section_break())

    r.h("DECLARATION", 1, page=True)
    r.p("I, Manan Lall, declare that the material embodied in this Minor Project - Dissertation titled “InsightForge: AI Data Analyst” is my original work submitted in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology in Artificial Intelligence and Machine Learning.")
    r.p("The work presented in this report describes the design, implementation, and evaluation of a web-based data analysis platform developed during the academic project. The implementation, experiments, screenshots, tables, and test results have been prepared from the project repository and the sample datasets available in the workspace.")
    r.p("It is further certified that this Minor Project - Dissertation has not been submitted in full or in part to this university or any other university for the award of any other degree or diploma. All external ideas, libraries, frameworks, documentation, and datasets used in the work have been acknowledged at the relevant places and in the bibliography.")
    r.add(paragraph("", after=480))
    r.add(paragraph("Signature of the Student: ______________________________", align="left", size=24, after=220))
    r.add(paragraph("Name: Manan Lall", align="left", size=24, after=100))
    r.add(paragraph("Enrollment No.: ______________________________", align="left", size=24, after=100))
    r.add(paragraph("Date: ____________________", align="left", size=24, after=0))

    r.h("CERTIFICATE", 1, page=True)
    r.p("This is to certify that the work embodied in this Minor Project - Dissertation titled “InsightForge: AI Data Analyst”, submitted in partial fulfillment of the requirements for the award of the degree of Bachelor of Technology in Artificial Intelligence and Machine Learning, is an original project work carried out by Manan Lall under the supervision and guidance of Ms. Nibha, Assistant Professor, Department of Artificial Intelligence and Machine Learning.")
    r.p("The project demonstrates the development of an end-to-end web application for CSV ingestion, data profiling, grounded natural-language analytics, interactive visualization, anomaly detection, and persistent user-scoped analysis sessions. The report has been prepared in accordance with the prescribed academic format for the AIML-451 Minor Project - Dissertation.")
    r.p("It is further certified that, to the best of my knowledge and belief, the work has not been submitted in full or in part to this university or any other university for the award of any other degree or diploma.")
    r.add(paragraph("", after=480))
    r.add_table("Certificate approval block", ["Role", "Name / Signature", "Date"], [
        ["Faculty Supervisor", "Ms. Nibha — __________________", "____________"],
        ["Head of Department", "______________________________", "____________"],
        ["Institute", "Dr. Akhilesh Das Gupta Institute of Professional Studies", "____________"],
    ], widths=[2200, 4600, 1600])

    r.h("ACKNOWLEDGEMENT", 1, page=True)
    r.p("I express my sincere gratitude to my faculty supervisor, Ms. Nibha, Assistant Professor, Department of Artificial Intelligence and Machine Learning, for her guidance, feedback, and encouragement throughout the development of this project. Her suggestions helped shape the problem definition, system architecture, and evaluation strategy described in this dissertation.")
    r.p("I am thankful to the Department of Artificial Intelligence and Machine Learning, the Head of Department, the Principal, and Dr. Akhilesh Das Gupta Institute of Professional Studies for providing the academic environment, laboratory access, and institutional support required to complete the project. I also acknowledge the faculty members who contributed indirectly through classroom instruction and technical discussions.")
    r.p("I acknowledge the open-source communities behind FastAPI, Next.js, React, Pandas, DuckDB, scikit-learn, SQLAlchemy, LangGraph, Plotly, and the other libraries used in InsightForge. Their documentation and engineering work made it possible to construct a secure and reproducible prototype within the project timeframe.")
    r.p("Finally, I thank my family, classmates, peers, and friends for their patience, encouragement, and constructive feedback during the design, debugging, and testing of the application.")
    r.add(paragraph("", after=450))
    r.add(paragraph("Manan Lall", align="right", bold=True, size=24, after=0))

    r.h("ABSTRACT", 1, page=True)
    r.p("InsightForge is a web-based AI Data Analyst platform designed to reduce the friction between raw tabular data and actionable understanding. Many users can collect data in spreadsheets or CSV files but cannot translate the data into reliable summaries, trends, comparisons, and recommendations without specialized query languages or statistical tooling. InsightForge addresses this gap by combining a browser-based workspace with a FastAPI analytical backend, deterministic semantic dataset understanding, secure query execution, automated insight generation, interactive charts, anomaly detection, and conversational analysis.")
    r.p("The platform accepts CSV datasets, validates their structure, persists dataset metadata, detects domain and record grain, distinguishes meaningful business measures from identifiers, and produces an automatic analysis report. A user can ask natural-language questions such as which category has the highest sales, how a metric changes over time, or which records may be anomalous. The application returns grounded answers with confidence, assumptions, limitations, charts, and supporting rows. Optional Gemini and Upstash services can enrich tool selection and memory, but deterministic analysis remains the safety-oriented source of truth when external services are unavailable.")
    r.p("The project is implemented using Next.js and TypeScript on the frontend and FastAPI with Python on the backend. Pandas provides tabular computation, DuckDB executes read-only SQL over registered DataFrames, an AST allowlist constrains generated Pandas expressions, and Isolation Forest provides unsupervised anomaly scoring. User-scoped database models preserve datasets, sessions, messages, and reports. The current repository was verified with 51 passing backend tests and a successful frontend production build. The Sample Superstore evaluation contains 9,994 records, total sales of $2,297,200.86, and total profit of $286,397.02.")
    r.p("The result is a practical development project that demonstrates how deterministic analytics, optional generative AI, web engineering, and security guardrails can be combined into an accessible data analysis workflow. The report documents the requirements, architecture, implementation, testing evidence, limitations, and future work of the system.")
    # The preliminary pages use Roman pagination; the final document section
    # restarts the main chapters at Arabic page 1.

    r.h("TABLE OF CONTENTS", 1, page=True)
    r.p("The following field is a Word-generated table of contents. Open the document in Microsoft Word and select Update Field to calculate the final page numbers after any manual edits.", indent=False)
    r.add(toc_field('TOC \\o "1-3" \\h \\z \\u'))

    r.h("LIST OF FIGURES", 1, page=True)
    r.p("The list below is a Word-generated field based on Caption-style figure paragraphs. Update fields in Word after opening the report.", indent=False)
    r.add(toc_field('TOC \\c "Figure" \\h \\z \\u'))

    r.h("LIST OF TABLES", 1, page=True)
    r.p("The list below is a Word-generated field based on Caption-style table paragraphs. Update fields in Word after opening the report.", indent=False)
    r.add(toc_field('TOC \\c "Table" \\h \\z \\u'))

    r.h("LIST OF ABBREVIATIONS", 1, page=True)
    r.add_table("Abbreviations used in the report", ["Abbreviation", "Meaning"], [
        ["AI", "Artificial Intelligence"],
        ["AIML", "Artificial Intelligence and Machine Learning"],
        ["API", "Application Programming Interface"],
        ["AST", "Abstract Syntax Tree"],
        ["CSV", "Comma-Separated Values"],
        ["DFD", "Data Flow Diagram"],
        ["ER", "Entity Relationship"],
        ["JWT", "JSON Web Token"],
        ["LLM", "Large Language Model"],
        ["ML", "Machine Learning"],
        ["RAG", "Retrieval-Augmented Generation"],
        ["SRS", "Software Requirements Specification"],
        ["UI", "User Interface"],
    ], widths=[2200, 6200])
    r.add(section_break(footer_id="rId2", page_format="lowerRoman", page_start=1))


def page_block(r: ReportBuilder, title: str, paragraphs: list[str] | None = None,
               *, bullets: list[str] | None = None, table_data: tuple[str, list[str], list[list[str]], list[int] | None] | None = None,
               diagram: tuple[str, str] | None = None, code: str | None = None,
               image: tuple[str, int, str, float, float] | None = None) -> None:
    # Subsections flow naturally under the university's 1.5-line layout. Major
    # chapters still begin on fresh pages; avoiding a page break for every
    # subsection keeps the report near the requested 65–75 page range.
    r.h(title, 2)
    for text in paragraphs or []:
        r.p(text)
    if bullets:
        r.bullets(bullets)
    if table_data:
        table_title, headers, rows, widths = table_data
        r.add_table(table_title, headers, rows, widths=widths)
    if diagram:
        r.add_diagram(diagram[0], diagram[1])
    if code:
        r.code(code)
    if image:
        rel_id, image_id, image_title, width, height = image
        r.add_image(rel_id, image_id, image_title, width=width, height=height)


def add_chapter_1(r: ReportBuilder) -> None:
    r.h("CHAPTER 1: INTRODUCTION", 1, page=True)
    r.p("InsightForge is a development-based project that explores how a web application can make routine data analysis more accessible without removing the controls required for trustworthy computation. The project sits at the intersection of software engineering, applied data science, user-interface design, and responsible use of generative AI. This chapter introduces the context, motivation, scope, contribution, and organisation of the dissertation.")

    page_block(r, "1.1 Background: from files to decisions", [
        "Organisations of every size accumulate operational data in CSV exports, spreadsheets, and database extracts. The file is easy to create, but the decision-making process that follows is often difficult. A user may need to identify the correct date column, distinguish an order line from an order, select the right measure, group by a meaningful business dimension, and communicate the result to another person. These steps require a mixture of domain knowledge, spreadsheet skill, SQL, statistics, and visualisation judgement.",
        "InsightForge treats a dataset as more than a collection of columns. Its semantic understanding layer inspects names, data types, uniqueness, date-like values, and domain terms to build a compact analytical contract. The contract separates identifiers such as Row ID and Postal Code from meaningful measures such as Sales and Profit. This early distinction is important because an apparently valid numerical calculation can still be an analytically meaningless answer.",
        "The platform then exposes the same understanding through automatic insights and conversational analysis. The result is a workflow in which a user can upload a file, inspect data quality, receive a first report, ask follow-up questions, and review supporting evidence in one browser workspace."
    ])
    add_chapter_1_tail(r)


def add_chapter_7(r: ReportBuilder) -> None:
    r.h("CHAPTER 7: SUMMARY AND CONCLUSION", 1, page=True)
    r.p("This chapter summarises the work completed, evaluates the objectives, discusses the project result, and closes with the conclusion supported by the implementation and test evidence.")

    page_block(r, "7.1 Summary of the implemented system", [
        "InsightForge implements a browser-based analytical workspace for CSV datasets. A user can authenticate, upload a file, inspect its structure, receive an automatic report, ask conversational questions, inspect charts and supporting rows, restore a session, and delete the dataset. The backend combines FastAPI route policies, CSV ingestion, a dataset registry, SQLAlchemy persistence, background jobs, semantic understanding, automatic insight generation, chart specifications, anomaly detection, safe SQL and Pandas tools, and layered conversation memory.",
        "The central engineering decision is to make deterministic semantic understanding the foundation of analysis. The system does not allow an optional language model to decide silently that any numeric column is a business measure. Instead, the project identifies likely identifiers and measures first, then uses the result to drive the automatic report and common chat answers.",
        "The result is a modular monolith that is suitable for academic evaluation and can be extended toward a more distributed production design."
    ])

    page_block(r, "7.2 Objective-wise evaluation", [
        "The upload and validation objective was achieved through CsvIngestionService, which checks file type, size, encoding, parser output, headers, row count, and date conversion. The persistence objective was achieved through SQLAlchemy models, DatasetRegistry, file rehydration, chat history, and report storage. The semantic-analysis objective was achieved through domain, grain, identifier, dimension, measure, and derived-metric detection.",
        "The conversational-analysis objective was achieved through deterministic business-question handling and the LangGraph/Gemini-compatible workflow. The safety objective was achieved through SELECT-only DuckDB queries, AST-allowlisted Pandas expressions, timeouts, owner checks, JWT authentication, and rate limits. The user-interface objective was supported by a successful frontend production build and the dashboard/analysis screens.",
        "The verification objective was supported by 51 passing backend tests under isolated SQLite/deterministic-provider settings and a passing frontend production build. The automated HTTP tests cover authentication, upload/list/profile/row/SQL routes, asynchronous jobs, and access isolation; a single full browser journey through chat, history, and report refresh was not independently executed."
    ], table_data=("Objective completion summary", ["Objective", "Status", "Evidence"], [
        ["CSV ingestion and validation", "Achieved", "Ingestion service and tests"],
        ["Semantic dataset understanding", "Achieved", "Understanding engine and regressions"],
        ["Automatic insight report", "Achieved", "AutoAnalysisEngine and Sample Superstore"],
        ["Conversational analytics", "Implemented; route-level evidence", "Planner/graph code, deterministic regression tests, route contracts"],
        ["Secure execution", "Achieved for prototype", "SQL/Pandas validation tests"],
        ["Durable sessions and tenant scope", "Achieved for local architecture", "Persistence tests"],
        ["Distributed production scale", "Future work", "Not claimed in current scope"],
    ], [3000, 2100, 3800]))

    page_block(r, "7.3 Project results", [
        "The Sample Superstore evaluation shows that the application can transform a 9,994-row CSV into a structured business report. It correctly identifies the sales domain and order-line grain, separates identifier-like columns, calculates sales and profit totals, detects category and regional leaders, identifies monthly extremes, surfaces a loss-making sub-category and product, and provides recommendations framed as investigation actions.",
        "The application also demonstrates transparency. The report contains data quality warnings, confidence and domain confidence, evidence fields, chart data, limitations, and optional generated SQL. The user can inspect not only what the system says but also what fields and operations were used to produce it.",
        "The implementation is therefore successful as a development project. It is not a replacement for a governed enterprise BI platform or a domain expert, and the limitations in Chapter 8 remain part of the conclusion."
    ])

    page_block(r, "7.4 Conclusion", [
        "The project demonstrates that an accessible natural-language data interface can be built without making the analytical layer entirely dependent on a language model. The combination of deterministic semantic understanding, structured contracts, safe tools, optional agent planning, and explicit fallbacks provides a practical balance between convenience and control.",
        "The most important lesson is that correctness in data analysis begins before the query is generated. A field can be numeric and still be an identifier; a row can represent an order line rather than an order; a trend can be unavailable when dates are not reliable; and an anomaly can be unusual without being wrong. InsightForge makes these distinctions part of the software design.",
        "Within the scope of the AIML-451 minor project, the system meets its primary objective and provides a solid foundation for future work in scalable storage, collaborative workspaces, stronger sandboxing, richer semantic modelling, and measurable production performance."
    ])

    page_block(r, "7.5 Lessons learned", [
        "The project required simultaneous attention to user experience and backend correctness. A feature is incomplete if an endpoint works but the interface cannot explain its response, and it is incomplete if the interface looks polished but the backend chooses the wrong measure. The development process therefore moved between source inspection, tests, local smoke runs, and deployed-behaviour checks.",
        "A second lesson was the value of fallbacks. Optional providers can be useful, but they introduce a dependency boundary that must be tested. Keeping the deterministic engine as the source of truth allowed the project to continue even after Redis and Vector were unavailable and made the most important regression easier to reproduce.",
        "A final lesson was the need to document what is not implemented. Honest limitations make the system easier to evaluate and provide a more useful roadmap than a broad list of unverified claims."
    ])


def add_chapter_8(r: ReportBuilder) -> None:
    r.h("CHAPTER 8: LIMITATIONS AND FUTURE WORK", 1, page=True)
    r.p("No development project is complete in the sense of solving every adjacent problem. This chapter records the limitations that remain in the current implementation and proposes a prioritised roadmap. The limitations are not failures of the project scope; they define the boundary of the prototype and identify the engineering work needed for a stronger production system.")

    page_block(r, "8.1 External service and provider limitations", [
        "The current application can use Gemini, Redis, and Vector when configured, but local verification relies primarily on deterministic analysis and database/in-process fallbacks. The absence of a provider means that model-assisted wording, hot memory, or semantic retrieval may not be available. Provider latency, quotas, model changes, and network failures are not fully represented in the local test suite.",
        "Future work should introduce provider contract tests using mocks, explicit timeout and retry policies, structured telemetry for provider calls, and a documented configuration matrix. The application should continue to expose whether a provider was used and should never allow provider output to replace computed evidence silently.",
        "The current report intentionally distinguishes optional integrations from verified local behaviour."
    ])

    page_block(r, "8.2 Scalability and deployment limitations", [
        "The in-process ThreadPoolExecutor is appropriate for local execution but is not a durable distributed queue. Jobs are lost when the process is restarted, and multiple application instances do not share the same job registry. File storage is also local to the process environment unless a durable volume or object store is configured.",
        "A production design would move jobs to Celery, a managed queue, or another durable worker system backed by Redis or a message broker. Uploaded files would be stored in object storage with signed access, and report metadata would be written to PostgreSQL with migrations and backup procedures. Horizontal scaling would require shared session state and a consistent cache strategy.",
        "These changes should be measured with a workload model rather than introduced solely as architectural labels."
    ])

    page_block(r, "8.3 Analytical and semantic limitations", [
        "The semantic engine uses column names, data types, uniqueness, and simple vocabulary. It cannot reliably infer a business definition that is missing from the dataset or encoded in an unfamiliar abbreviation. Domain confidence is a useful warning but not a formal ontology score. The current system also does not perform causal inference, forecasting, uncertainty estimation for every metric, or domain-specific validation rules.",
        "Future work should allow users to confirm or correct the detected grain and measures, save a dataset-specific semantic profile, and provide a vocabulary mapping for custom domains. A schema contract could include unit, currency, timezone, aggregation policy, and sensitive-field classification. These additions would reduce ambiguity without making the core system dependent on a model.",
        "The user should remain able to inspect and override assumptions rather than receiving a hidden semantic decision."
    ])

    page_block(r, "8.4 Security, privacy, and governance limitations", [
        "The SQL and Pandas restrictions are defence-in-depth controls inside the application process. They are not equivalent to a separate OS-level sandbox or a security review. The project does not provide enterprise SSO, formal audit trails, encryption-at-rest configuration, data retention enforcement, PII discovery, or policy-based redaction. These controls are necessary before accepting sensitive production datasets.",
        "Future work should isolate generated computation in a separate worker process or container, add database row-level security where appropriate, encrypt files and secrets, implement audit events, add retention and deletion policies, and classify sensitive columns before displaying them in previews or embeddings. Security tests should be expanded with fuzzing and dependency scanning.",
        "The current implementation should therefore be treated as a controlled prototype and not as a compliance claim."
    ])

    page_block(r, "8.5 Prioritised future-work roadmap", [
        "Future work is prioritised by risk and user value. The first priority is to keep analytical correctness and access control strong while improving deployment durability. The second priority is to improve semantic configuration and user feedback. The third priority is collaboration and richer analysis. Each item should be accompanied by tests and measurable acceptance criteria.",
        "A staged roadmap allows the project to grow without weakening the deterministic core. The first release after the academic prototype should add a durable job queue and object storage. The next should add user-confirmed semantic profiles, provider contract tests, and better evaluation datasets. Later releases can add collaborative workspaces, streaming progress, forecasting, and domain plugins.",
        "The following matrix records the recommended order."
    ], table_data=("Future-work prioritisation", ["Priority", "Work item", "Reason", "Acceptance evidence"], [
        ["P0", "Durable queue and object storage", "Restart and scale resilience", "Jobs survive restart; files rehydrate from object store"],
        ["P0", "Process/container sandbox", "Reduce risk of generated execution", "Isolation tests and resource policies"],
        ["P1", "User-confirmed semantic profile", "Reduce column-name ambiguity", "Saved mappings and override tests"],
        ["P1", "Provider contract tests", "Make optional services observable", "Mocked timeout/fallback matrix"],
        ["P2", "Collaborative workspaces", "Shared team analysis", "Role and sharing tests"],
        ["P2", "Streaming progress and reasoning summary", "Improve long-task UX", "SSE/WebSocket integration test"],
        ["P3", "Forecasting and domain plugins", "Extend analytical depth", "Benchmark per domain and model"],
    ], [1000, 3000, 2600, 3000]))


def add_bibliography_and_appendices(r: ReportBuilder) -> None:
    r.h("BIBLIOGRAPHY", 1, page=True)
    refs = [
        "[1] G. G. S. Indraprastha University, University School of Automation and Robotics, “Guidelines for Preparation of Final Report of the Minor Project - Dissertation (AIML-451),” academic report-format document, 2026.",
        "[3] FastAPI, “FastAPI documentation,” [Online]. Available: https://fastapi.tiangolo.com/. [Accessed: Oct. 26, 2026].",
        "[4] Vercel, “Next.js documentation,” [Online]. Available: https://nextjs.org/docs. [Accessed: Oct. 26, 2026].",
        "[5] The pandas development team, “pandas documentation,” [Online]. Available: https://pandas.pydata.org/docs/. [Accessed: Oct. 26, 2026].",
        "[6] DuckDB Foundation, “DuckDB documentation,” [Online]. Available: https://duckdb.org/docs/. [Accessed: Oct. 26, 2026].",
        "[7] F. T. Liu, K. M. Ting, and Z.-H. Zhou, “IsolationForest,” scikit-learn API reference, [Online]. Available: https://scikit-learn.org/stable/modules/generated/sklearn.ensemble.IsolationForest.html. [Accessed: Oct. 26, 2026].",
        "[8] LangChain, “LangGraph documentation,” [Online]. Available: https://langchain-ai.github.io/langgraph/. [Accessed: Oct. 26, 2026].",
        "[9] SQLAlchemy authors, “SQLAlchemy documentation,” [Online]. Available: https://docs.sqlalchemy.org/. [Accessed: Oct. 26, 2026].",
        "[10] Plotly Technologies Inc., “Plotly Python documentation,” [Online]. Available: https://plotly.com/python/. [Accessed: Oct. 26, 2026].",
        "[11] Python Software Foundation, “ast — Abstract syntax trees,” [Online]. Available: https://docs.python.org/3/library/ast.html. [Accessed: Oct. 26, 2026].",
        "[12] M. Ester, H.-P. Kriegel, J. Sander, and X. Xu, “A density-based algorithm for discovering clusters in large spatial databases with noise,” in Proceedings of KDD, 1996. Cited as background for unsupervised outlier reasoning; the implementation uses Isolation Forest instead.",
        "[13] F. T. Liu, K. M. Ting, and Z.-H. Zhou, “Isolation Forest,” in Proceedings of the Eighth IEEE International Conference on Data Mining, 2008, pp. 413–422.",
        "[14] OWASP Foundation, “Application Security Verification Standard,” [Online]. Available: https://owasp.org/www-project-application-security-verification-standard/. [Accessed: Oct. 26, 2026].",
        "[15] M. Jones, J. Bradley, and N. Sakimura, “JSON Web Token (JWT),” RFC 7519, May 2015, [Online]. Available: https://datatracker.ietf.org/doc/html/rfc7519.",
        "[16] Google, “Gemini API documentation,” [Online]. Available: https://ai.google.dev/gemini-api/docs. [Accessed: Oct. 26, 2026].",
        "[17] Upstash, “Upstash documentation,” [Online]. Available: https://upstash.com/docs. [Accessed: Oct. 26, 2026].",
        "[18] Microsoft, “Office Open XML file formats,” [Online]. Available: https://learn.microsoft.com/en-us/openspecs/office_standards/ms-oi29500/. [Accessed: Oct. 26, 2026].",
    ]
    for ref in refs:
        r.add(paragraph(ref, align="left", size=22, after=120, line=360, first_indent=-360, left_indent=360))

    page_block(r, "Reference mapping and source evidence", [
        "The bibliography contains the academic template, the project synopsis, primary framework documentation, and background references for the analytical and security mechanisms used in the implementation. The source repository is the primary evidence for project-specific claims. In particular, backend/app/analytics/understanding.py and backend/app/analytics/auto_analysis.py are the source of the semantic and automatic insight descriptions; backend/app/tools/sql_tool.py and backend/app/tools/pandas_tool.py are the source of the execution-safety descriptions; and backend/tests provides the test evidence.",
        "The report deliberately avoids citing a generic model paper as proof that InsightForge is accurate. Model or framework documentation explains capability, while the project tests and Sample Superstore calculations demonstrate what this implementation actually did.",
        "When this report is submitted, the author should add access dates for online references if required by the institute and verify that the final reference style matches the department’s preferred IEEE formatting."
    ], table_data=("Project evidence map", ["Claim in report", "Primary evidence"], [
        ["CSV validation", "backend/app/services/ingestion.py"],
        ["Semantic fields and grain", "backend/app/analytics/understanding.py"],
        ["Automatic cards and quality", "backend/app/analytics/auto_analysis.py"],
        ["Chat and ranking answers", "backend/app/agents/planner.py"],
        ["SQL/Pandas safety", "backend/app/tools/sql_tool.py and pandas_tool.py"],
        ["Persistence and owner scope", "backend/app/database/models.py, registry.py, memory/session.py"],
        ["Verification", "backend/tests and frontend npm run build"],
    ], [3600, 4400]))

    r.h("APPENDIX A: API ENDPOINT REFERENCE", 1, page=True)
    r.p("The following appendix collects the main application endpoints for reviewers and future maintainers. All protected endpoints require a bearer token unless stated otherwise.")
    r.add_table("Implemented API endpoints", ["Endpoint", "Method", "Purpose"], [
        ["/health", "GET", "Service health check"],
        ["/api/auth/register", "POST", "Create a user account"],
        ["/api/auth/login", "POST", "Authenticate and issue a JWT"],
        ["/api/auth/me", "GET", "Return current user profile"],
        ["/api/upload", "POST", "Synchronous CSV upload"],
        ["/api/upload/async", "POST", "Background CSV upload"],
        ["/api/jobs/{id}", "GET", "Poll background job"],
        ["/api/datasets", "GET/DELETE", "List or clear owner datasets"],
        ["/api/datasets/{id}", "DELETE", "Delete one dataset"],
        ["/api/datasets/{id}/profile", "GET", "Return profile and schema"],
        ["/api/datasets/{id}/rows", "GET", "Return paginated/searchable rows"],
        ["/api/chat", "POST", "Run conversational analysis"],
        ["/api/chat/history/{session_id}", "GET/DELETE", "Read or clear session history"],
        ["/api/generate-sql", "POST", "Run validated read-only SQL"],
        ["/api/generate-pandas", "POST", "Run AST-allowlisted Pandas"],
        ["/api/generate-chart", "POST", "Create chart specification"],
        ["/api/detect-anomalies", "POST", "Run anomaly detection"],
        ["/api/datasets/{id}/insights", "GET", "Read or start automatic report"],
    ], [3000, 1500, 3900])

    page_block(r, "Appendix B: Sample Superstore schema", [
        "The Sample Superstore CSV is used as the principal evaluation dataset. The schema contains identifiers, dates, categorical dimensions, and numerical measures. The distinction between Row ID, Order ID, and the analytical measures is central to the semantic regression tests.",
    ], table_data=("Sample Superstore columns", ["Column", "Role in analysis", "Type in source"], [
        ["Row ID", "Identifier", "int64"],
        ["Order ID", "Order identifier; repeated across order lines", "object"],
        ["Order Date", "Primary time dimension", "object parsed to datetime"],
        ["Ship Date", "Secondary time field", "object parsed to datetime"],
        ["Ship Mode", "Operational dimension", "object"],
        ["Customer ID / Name", "Customer identifiers/dimension", "object"],
        ["Segment, Region, Category", "Business dimensions", "object"],
        ["Product ID / Name", "Product identifiers/dimension", "object"],
        ["Sales", "Revenue measure", "float64"],
        ["Quantity", "Volume measure", "int64"],
        ["Discount", "Pricing measure", "float64"],
        ["Profit", "Profitability measure", "float64"],
    ], [2500, 4300, 1600]))

    page_block(r, "Appendix C: Example automatic report output", [
        "The following example is a condensed representation of the data that the automatic report exposes to the frontend. It is not a hard-coded fixture inside the application. The values are calculated from the supplied Sample Superstore file and are included so that a reviewer can compare the prose, metrics, charts, and evidence fields.",
    ], code='''{
  "domain": "sales",
  "grain": "order line",
  "rows": 9994,
  "columns": 21,
  "key_metrics": {
    "revenue": 2297200.8603,
    "profit": 286397.0217,
    "quantity": 37873
  },
  "quality": {
    "duplicate_rows": 0,
    "warnings": []
  },
  "finding": "Technology leads category sales; November 2017 is the peak month.",
  "limitation": "Anomaly signals require business review and do not prove error."
}''')

    page_block(r, "Appendix D: Secure execution excerpts", [
        "The excerpts below summarise the controls that should be reviewed before any production deployment. The current implementation is designed to reduce common risks but should be strengthened with process isolation and a formal threat model for untrusted generated code.",
    ], code='''# SQL: only read-only SELECT statements
_ALLOWED_PATTERN = re.compile(r"^\\s*select\\b", re.IGNORECASE)
_FORBIDDEN_KEYWORDS = re.compile(
    r"\\b(insert|update|delete|drop|create|alter|truncate|copy|attach|"
    r"detach|load|install|call|pragma|read_csv|read_parquet|glob)\\b",
    re.IGNORECASE,
)

# Pandas: reject unknown names and unapproved calls
if isinstance(node, ast.Name) and node.id not in ALLOWED_NAME_IDS:
    raise UnsafeExpression(f"Disallowed variable: {node.id}")''')

    page_block(r, "Appendix E: Verification transcript", [
        "The following commands were executed against the current workspace. The backend result was 51 passed and one warning. The frontend build completed successfully. These results should be repeated after any manual report metadata edits that require code or test changes.",
    ], code='''C:\\Users\\Manan\\Desktop\\AI-Data-Analyst>
"backend/.venv/Scripts/python.exe" -m pytest -q
51 passed, 1 warning

C:\\Users\\Manan\\Desktop\\AI-Data-Analyst\\frontend>
npm run build
next build
Compiled successfully; type checking and static generation passed.''')

    page_block(r, "Appendix F: Local installation and user guide", [
        "For local development, create or activate the backend virtual environment, install backend requirements, configure the environment file, and start Uvicorn. In a second terminal, install frontend dependencies and run the Next.js development server. Open the frontend URL, register a user, upload a CSV, wait for the insight report, and open Analyse or Explore.",
        "A minimal local flow does not require Redis or Vector. SQLite and the deterministic analysis path are sufficient for the core evaluation. A PostgreSQL connection, Gemini key, Redis URL, or Vector credentials can be added later through environment configuration when the corresponding capability is needed.",
        "The recommended user checklist is: verify the row/column summary, inspect the profile and quality warnings, ask a question whose expected measure is known, open the evidence or generated query, review limitations, and delete test data after evaluation."
    ], code='''# Backend (Windows PowerShell)
cd backend
.\\.venv\\Scripts\\Activate.ps1
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8000

# Frontend
cd frontend
npm install
npm run dev''')


def build_report() -> ReportBuilder:
    report = ReportBuilder()
    add_front_matter(report)
    add_chapter_1(report)
    add_chapter_2(report)
    add_chapter_3(report)
    add_chapter_4(report)
    add_chapter_5(report)
    add_chapter_6(report)
    add_chapter_7(report)
    add_chapter_8(report)
    add_bibliography_and_appendices(report)
    return report


def write_docx(report: ReportBuilder) -> None:
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with ZipFile(OUTPUT, "w", ZIP_DEFLATED) as archive:
        archive.writestr("[Content_Types].xml", content_types_xml())
        archive.writestr("_rels/.rels", root_rels_xml())
        archive.writestr("word/document.xml", report.output_xml())
        archive.writestr("word/_rels/document.xml.rels", relationships_xml())
        archive.writestr("word/styles.xml", styles_xml())
        archive.writestr("word/settings.xml", settings_xml())
        archive.writestr("word/footerFront.xml", footer_xml("lowerRoman"))
        archive.writestr("word/footerBody.xml", footer_xml("decimal"))
        archive.writestr("docProps/core.xml", core_xml())
        archive.writestr("docProps/app.xml", app_xml())
        if DASHBOARD_IMAGE.exists():
            archive.writestr("word/media/dashboard.png", DASHBOARD_IMAGE.read_bytes())
        if ANALYSIS_IMAGE.exists():
            archive.writestr("word/media/analysis.png", ANALYSIS_IMAGE.read_bytes())
        if INSTITUTE_LOGO.exists():
            archive.writestr("word/media/institute_logo.jpeg", INSTITUTE_LOGO.read_bytes())
        for name in DIAGRAMS:
            image = DIAGRAM_DIR / f"{name}.png"
            if image.exists():
                archive.writestr(f"word/media/{name}.png", image.read_bytes())


def main() -> None:
    report = build_report()
    write_docx(report)
    page_units = sum(1 for part in report.parts if 'w:type="page"' in part) + 1
    print(f"Wrote {OUTPUT}")
    print(f"Figures: {report.figure_number}; tables: {report.table_number}; explicit page units: {page_units}")


def add_chapter_1_tail(r: ReportBuilder) -> None:
    page_block(r, "1.2 Motivation and project context", [
        "The motivation for InsightForge came from a practical gap between data availability and analytical confidence. Existing business-intelligence tools can be powerful, but they often require configuration, a defined data model, or familiarity with specialised interfaces. A small team or an individual student may instead want to upload one CSV and ask a direct question. The difficulty is not only generating a chart; it is choosing the appropriate field and explaining the limitations of the result.",
        "The project therefore focuses on a controlled form of AI-assisted analysis. Natural language is used as the entry point, but the response is grounded in validated DataFrame operations, read-only SQL, structured response contracts, and explicit assumptions and limitations. Optional language-model support can select or formulate tools, while deterministic fallbacks keep the basic application useful when provider keys, Redis, Vector, or other external services are unavailable.",
        "This design reflects an academic and engineering objective: demonstrate a complete application rather than a single model experiment. The project includes ingestion, authentication, persistence, job management, analytics, visualisation, testing, and interface work in a single system."
    ])

    page_block(r, "1.3 Existing workflow and its limitations", [
        "A conventional ad-hoc workflow begins with downloading a CSV, opening it in a spreadsheet, manually inspecting headers, creating formulas or pivot tables, and exporting a chart or written summary. This workflow is workable for a small question but becomes fragile when the same dataset is analysed repeatedly. Manual steps are difficult to reproduce, assumptions may remain implicit, and the person creating the chart may not be the person who needs to interpret it.",
        "A second workflow uses a notebook or SQL client. This improves reproducibility, but it moves the burden to code literacy and environment setup. It also encourages a technically correct but semantically weak pattern: selecting the first numeric column or the first categorical column without checking whether the columns represent identifiers, measures, or dimensions. The earlier deployment inspection of InsightForge demonstrated this exact risk when an identifier-like Postal Code field was selected for a category-level question.",
        "InsightForge addresses these weaknesses by making the analytical contract visible in the result. The answer can state the detected domain and grain, include a confidence value, expose generated SQL or metadata, and identify limitations. This does not eliminate the need for human judgement; it makes the judgement easier to inspect."
    ])

    page_block(r, "1.4 Project vision and intended users", [
        "The vision of InsightForge is a compact data workspace in which a user can move from an uploaded CSV to an evidence-backed analytical explanation in a small number of steps. The intended user is not assumed to be a database administrator. The user may be a student, a business analyst, a project coordinator, or a small-team operator who understands the business question but does not want to write every SQL query manually.",
        "The application supports two complementary modes. The first is an automatic mode that generates a profile, key metrics, charts, quality warnings, insights, and recommendations immediately after upload. The second is a conversational mode in which the user asks a question and receives a structured response. Both modes use the same dataset registry and semantic understanding so that the automatic report and the chat answer do not silently disagree about the data grain or primary measure.",
        "The design also recognises that different users need different degrees of transparency. A novice can read the executive summary and cards. A technical user can inspect the chart specification, SQL, assumptions, limitations, or returned rows."
    ])

    page_block(r, "1.5 Scope of the project", [
        "The implemented scope is deliberately bounded around CSV-based tabular analysis. The backend accepts CSV files, validates file size and row count, parses date-like fields, detects duplicate headers, stores the dataset, and triggers automatic analysis. The frontend provides authentication, dataset listing, upload, exploration, analysis, insights, and session-history flows. The project includes REST endpoints for profiling, chat, SQL, Pandas expressions, chart generation, anomaly detection, background jobs, and cached insight reports.",
        "The scope does not include a full enterprise data warehouse, collaborative editing, unrestricted arbitrary code execution, or a guarantee that an AI-generated statement is correct without inspection. Excel and Parquet ingestion are not claimed as part of the verified current flow. Redis and Vector are optional integrations with graceful fallbacks rather than mandatory requirements for local execution. The current job manager is an in-process thread pool, not a distributed Celery deployment.",
        "This boundary allows the dissertation to evaluate a coherent end-to-end prototype and to identify specific, credible next steps instead of presenting a broad but unverified feature list."
    ], table_data=("Project scope and boundary", ["Area", "Included", "Not claimed in the verified scope"], [
        ["Input", "CSV upload, validation, preview", "Excel, Parquet, streaming ingestion"],
        ["Analysis", "Profiling, semantic measures, trends, rankings, anomalies", "Causal inference, forecasting, prescriptive optimisation"],
        ["AI", "Optional Gemini tool selection and deterministic fallback", "Guaranteed factuality or provider availability"],
        ["Storage", "SQLite/PostgreSQL metadata and local file rehydration", "Multi-region distributed storage"],
        ["Collaboration", "User-scoped datasets and sessions", "Shared workspaces and role-based collaboration"],
    ], [1800, 3300, 3300]))

    page_block(r, "1.6 Contributions of the project", [
        "The first contribution is an end-to-end architecture that connects a modern web interface to an analytical backend without requiring every interaction to be mediated by an external model. The system combines upload validation, a registry, persisted metadata, background jobs, automatic insights, chat, chart specifications, and security controls in a single repository. The web/API split follows the request-validation and dependency-injection model supported by FastAPI [3].",
        "The second contribution is a semantic guardrail for tabular analysis. The DataUnderstandingEngine identifies a domain, a likely grain, dates, dimensions, identifiers, meaningful measures, and derived metrics. This is intentionally deterministic and explainable. It does not attempt to understand every business vocabulary; instead, it provides a safe baseline that prevents common mistakes and creates a stable input for optional AI reasoning.",
        "The third contribution is the combination of transparency and graceful degradation. AnalysisResponse and AutoAnalysisResponse carry answers alongside reasoning, confidence, assumptions, limitations, evidence, and chart data. If Gemini, Redis, or Vector is absent, the application still performs grounded statistical work. This architecture supports academic evaluation because the response can be traced back to code and data rather than to an opaque claim."
    ])

    page_block(r, "1.7 Ethical, security, and academic context", [
        "Data analysis tools can create harm when they expose private data, confuse an identifier with a metric, or present a correlation as a cause. InsightForge addresses these risks at the prototype level through owner-scoped dataset access, password hashing, signed JWT authentication, read-only SQL, an AST allowlist for Pandas expressions, resource limits, confidence and limitation fields, and careful language around statistical associations.",
        "The application does not decide what a user should do. Recommendations are presented as follow-up actions such as checking a loss-making segment, reviewing discount policy, or investigating an anomalous record. The user remains responsible for validating the data, understanding the context, and deciding whether an action is appropriate. This distinction is important in a dissertation because a technically correct computation can still be unsuitable for a real decision if the data is incomplete or the business definition is different.",
        "The report therefore documents not only capabilities but also boundaries. Academic integrity is supported by linking project claims to source files, test results, and the Sample Superstore calculations reproduced from the repository."
    ])

    page_block(r, "1.8 Organisation of the dissertation", [
        "Chapter 1 introduces the project and its context. Chapter 2 defines the problem and translates it into objectives and measurable success criteria. Chapter 3 presents the software requirements specification, feasibility study, technology selection, and analysis models. Chapter 4 explains the architecture, modules, data flows, persistence model, and security boundaries.",
        "Chapter 5 documents the implementation, including ingestion, semantic understanding, analysis, tools, persistence, frontend screens, API examples, and representative source-code excerpts. Chapter 6 presents the testing strategy and evidence from the backend suite, frontend build, TestClient route/job coverage, security cases, and Sample Superstore evaluation. Chapter 7 summarises the work and concludes the project. Chapter 8 records limitations and a prioritised future-work roadmap, followed by the bibliography and appendices.",
        "The sequence follows the prescribed development-based project format so that requirements lead to design, design leads to implementation, and implementation is supported by test evidence."
    ])


def add_chapter_2(r: ReportBuilder) -> None:
    r.h("CHAPTER 2: PROBLEM STATEMENT", 1, page=True)
    r.p("This chapter converts the general motivation into a precise project problem, objectives, success criteria, assumptions, and constraints. The problem is framed as a software-development problem rather than as a research hypothesis: the goal is to engineer and evaluate a usable analytical workflow.")

    page_block(r, "2.1 Problem definition", [
        "Users frequently possess tabular data but do not have a reliable, low-friction path from a raw CSV file to an interpretable analytical result. Existing manual workflows make users responsible for discovering the schema, selecting correct measures, writing queries, choosing visualisations, and documenting assumptions. When a conversational model is introduced without sufficient guardrails, the problem can become worse: a fluent response may use an identifier as a measure, generate a query that is unsafe, or present an unsupported interpretation.",
        "The project problem is therefore defined as follows: design and implement a secure web platform that accepts a CSV dataset, understands enough of its structure to select meaningful analytical fields, provides automatic and conversational analysis, and returns transparent, reproducible outputs while continuing to operate when optional AI or memory services are unavailable.",
        "The definition includes both user value and engineering quality. A response is not considered successful merely because it contains text. It should be grounded in computed data, use an appropriate semantic field, respect access boundaries, and expose the evidence needed for a reviewer to understand how the answer was produced."
    ])

    page_block(r, "2.2 Project objectives", [
        "The primary objective is to build a complete AI-assisted data analyst prototype that a user can operate through a browser. The secondary objectives define the behaviour needed to make the prototype reliable enough for academic demonstration and local reuse.",
    ], bullets=[
        "Accept CSV uploads with clear validation for empty content, malformed syntax, duplicate headers, file size, and row-count limits.",
        "Persist dataset metadata and file storage in an owner-scoped manner so that datasets and conversations can be restored after a process restart.",
        "Detect domain, grain, date fields, identifiers, dimensions, measures, and derived metrics before generating insight cards or answers.",
        "Provide automatic summaries, quality reports, trends, rankings, correlations, anomaly signals, charts, recommendations, and evidence.",
        "Support conversational questions through deterministic business-question handling, optional LangGraph/Gemini planning, and safe fallbacks.",
        "Constrain SQL and Pandas execution so that generated analysis cannot freely mutate the host environment or read arbitrary files.",
        "Enforce authentication, tenant isolation, rate limiting, asynchronous job status, and structured response contracts.",
        "Verify the system with automated backend tests, a frontend production build, route-level HTTP integration tests, and dataset-based evaluation."
    ])

    page_block(r, "2.3 Success criteria", [
        "The intended acceptance journey is that a fresh local setup can register a user, authenticate, upload a valid CSV, list and preview the dataset, obtain a profile and automatic insight report, ask a question, receive a grounded response, inspect a chart or returned rows, reload the session history, and delete the dataset. The current automated evidence covers these stages in separate route, service, persistence, and regression tests; it does not constitute one full browser journey.",
        "The analytical success criteria are intentionally concrete. The system must not select Row ID or Postal Code as a business measure when a valid Sales or Profit column exists. It must identify the Sample Superstore file as sales-like, identify an order-line grain, parse Order Date, calculate the correct total sales and profit, surface category and period results, and label anomaly outputs as statistical signals rather than confirmed errors.",
        "The engineering success criteria are also concrete: the backend tests must pass, the frontend build must complete, and failure of optional Redis, Vector, or Gemini services must not prevent the deterministic path from returning a useful response."
    ], table_data=("Success criteria and evidence", ["Criterion", "Evidence used in this report"], [
        ["Upload and validation", "Ingestion tests and TestClient route tests"],
        ["Semantic correctness", "Grounded insight regression tests and Sample Superstore metrics"],
        ["Secure execution", "SQL and AST sandbox tests"],
        ["Persistence", "Owner-scoped registry and conversation-memory tests"],
        ["Usable interface", "Successful Next.js production build and screenshots"],
        ["Resilience", "Deterministic fallback when optional services are unavailable"],
    ], [3300, 5100]))

    page_block(r, "2.4 Assumptions and constraints", [
        "The design assumes that a dataset is primarily tabular and that column names provide useful, though imperfect, signals about the data. The semantic engine uses names, types, uniqueness, and date parsing; it cannot infer a business definition that is absent from the file. A column named Amount may be a revenue value in one dataset and a tax value in another, so the output must remain inspectable.",
        "The local prototype assumes a Python 3.12 environment, Node.js with the frontend dependencies, and either SQLite or a configured PostgreSQL connection for metadata. The current background job queue is an in-process thread pool. This is adequate for a college project and local deployment, but it is not equivalent to a horizontally scalable worker system.",
        "The project also assumes responsible use of uploaded data. Authentication and owner-scoped queries reduce accidental cross-user exposure, but they do not replace organisational data governance, encryption policy, retention policy, or legal review."
    ])

    page_block(r, "2.5 Problem-to-solution mapping", [
        "A useful way to evaluate the project is to map each problem to a design response. The lack of schema awareness is addressed by DataUnderstandingEngine. The lack of reproducible first-pass analysis is addressed by StatisticalPass and DeterministicFallback. The risk of unsafe generated code is addressed by SqlTool and PandasTool. The risk of losing conversation context is addressed by ConversationMemory and database-backed chat messages. The risk of slow upload or anomaly analysis is addressed by JobManager and polling endpoints.",
        "This mapping demonstrates that the system is not a collection of disconnected features. The same concerns are carried from requirement to architecture and then to testing. For example, the requirement that a user should not see another user’s dataset becomes an owner_id filter in models and registry queries, an authentication dependency in routes, and a test in test_persistence.py.",
        "The remainder of the report uses this mapping as a traceability principle. Claims about the system are tied to code modules and verification evidence rather than to the marketing description in README.md alone."
    ])


def add_chapter_3(r: ReportBuilder) -> None:
    r.h("CHAPTER 3: ANALYSIS", 1, page=True)
    r.p("This chapter presents the Software Requirements Specification, functional and non-functional requirements, feasibility study, technology choices, use-case analysis, data-flow models, and traceability. The requirements describe the expected behaviour of the current project while acknowledging the boundary between implemented functionality and planned enhancements.")

    page_block(r, "3.1 Software Requirements Specification overview", [
        "InsightForge is specified as a client-server web application. The client runs in a browser and communicates with a FastAPI backend over HTTP. The backend is responsible for authentication, dataset access, ingestion, analytical execution, jobs, memory, and persistence. The system is designed around explicit JSON response contracts so that the frontend can render an answer, reasoning, confidence, limitations, charts, anomalies, and rows without parsing an unstructured paragraph.",
        "The primary system actors are the authenticated user, the optional language-model provider, the database, and the background worker pool. The user initiates uploads and questions. The provider, when configured, can help select a tool or formulate a response. The database stores durable metadata and messages. The worker pool executes longer tasks without blocking the upload or request thread.",
        "The SRS treats security and observability as system requirements rather than optional implementation details. A valid user experience must not bypass owner checks, and a failed optional provider must not cause the application to invent a result."
    ])

    page_block(r, "3.2 Stakeholders and user needs", [
        "The direct stakeholder is the analyst or student who uploads a dataset and asks questions. The supervisor and evaluator are secondary stakeholders who need a clear explanation of the architecture, evidence of testing, and reproducible outputs. The future maintainer is another stakeholder because the code must be modular enough to extend with new domains, providers, or storage mechanisms.",
        "The stakeholder needs are expressed in terms of outcomes: the user needs a short path to a meaningful answer; the evaluator needs traceability; the maintainer needs stable module boundaries; and the organisation needs controls for access and execution. These needs are not identical. A novice may value a concise card, while an evaluator may value the generated SQL and test case. The response contract supports both views.",
        "The platform therefore uses progressive disclosure. The interface presents an executive result first and allows deeper inspection through metadata, charts, rows, generated code, and history."
    ], table_data=("Stakeholder needs", ["Stakeholder", "Need", "Design response"], [
        ["End user", "Ask questions without writing every query", "Conversational chat and deterministic planner"],
        ["Data reviewer", "Inspect schema and data quality", "Profile endpoint, explorer, warnings, quality score"],
        ["Evaluator", "Verify correctness and reproducibility", "Evidence fields, tests, source excerpts, sample metrics"],
        ["Maintainer", "Extend analytics without rewriting UI", "Modular services, contracts, registry, planner"],
        ["System owner", "Protect data and resources", "JWT, owner filters, rate limits, sandboxes"],
    ], [1900, 3300, 3200]))

    page_block(r, "3.3 Functional requirements: ingestion and identity", [
        "FR-01: The system shall permit a registered user to authenticate using an email and password. Passwords shall be stored as bcrypt hashes, and successful login shall return a signed bearer token. FR-02: Protected dataset and chat routes shall require a valid authenticated user. FR-03: The system shall accept one or more CSV files through the upload route and return dataset summaries containing an identifier, filename, row count, column count, and preview rows.",
        "FR-04: The system shall reject empty files, unsupported extensions, malformed CSV content, duplicate headers, files over the configured size limit, and files over the configured row limit. FR-05: Date-like object columns shall be parsed when a high proportion of values can be converted. FR-06: Dataset identifiers shall be generated deterministically from the owner scope, filename, and content unless a valid explicit identifier is provided.",
        "FR-07: The system shall list and delete datasets owned by the current user. FR-08: Dataset rows shall be available through a paginated endpoint with optional substring search. These requirements establish the first stage of the workflow and provide the data boundary for later analysis."
    ])

    page_block(r, "3.4 Functional requirements: analysis and conversation", [
        "FR-09: The system shall profile a dataset and return rows, columns, duplicate count, column-level information, and numeric summaries. FR-10: The system shall infer a domain, grain, date column, dimensions, identifiers, meaningful measures, and derived metrics. FR-11: The system shall generate an automatic report containing an executive summary, trend story, insight cards, charts, recommendations, actions, key metrics, quality information, and an anomaly note.",
        "FR-12: The chat endpoint shall store the user turn, load relevant recent history, run the planner, store the assistant response and analysis data, and return an AnalysisResponse. FR-13: The planner shall support executive summaries, profiling, rankings, trends, anomaly requests, and generic fallbacks. FR-14: The system shall provide read-only SQL, restricted Pandas, chart, and anomaly endpoints. FR-15: Long-running upload and analysis work shall be represented as background jobs with a status endpoint.",
        "FR-16: The system shall expose limitations and assumptions when interpretation is inferred. FR-17: The frontend shall render the result in dashboard, explorer, analysis, and insights views, and shall restore user-scoped session data after a page reload."
    ])

    page_block(r, "3.5 Non-functional requirements", [
        "Security: dataset, session, job, and report access must be filtered by owner. Generated SQL must be read-only and must not access the filesystem. Generated Pandas expressions must be validated before execution and must run within a timeout. Authentication failures must return an HTTP 401 response rather than silently exposing protected data.",
        "Reliability: the deterministic analysis path should work without Gemini, Redis, or Vector credentials. Persistence failures should be logged and should not create a cross-user result. Background jobs should transition to completed or failed states and preserve an error message when a task fails. The UI should handle an expired session by clearing stale browser state.",
        "Usability and maintainability: responses should use stable Pydantic contracts, charts should use a frontend-readable specification, and modules should have clear responsibilities. Performance: uploads and anomaly work should not block the request loop unnecessarily, and results should be capped where returning unlimited rows would create memory or rendering problems."
    ], table_data=("Non-functional requirements", ["Quality attribute", "Requirement", "Implementation evidence"], [
        ["Security", "Owner isolation and restricted execution", "JWT dependencies, registry filters, SQL/Pandas validation"],
        ["Reliability", "Graceful fallback and explicit failure states", "Deterministic planner, job status, warnings"],
        ["Usability", "Progressive disclosure and clear response fields", "Dashboard, analysis UI, response schemas"],
        ["Maintainability", "Modular services and typed contracts", "FastAPI routes, Pydantic models, focused modules"],
        ["Performance", "Bounded work and asynchronous heavy tasks", "Row/file limits, ThreadPoolExecutor, capped output"],
    ], [1700, 3600, 3100]))

    page_block(r, "3.6 Technical feasibility", [
        "The project is technically feasible because the required operations are supported by mature libraries and a modest local data scope. Pandas can parse and aggregate CSV files. DuckDB can execute analytical SQL over registered DataFrames. FastAPI provides request validation and dependency injection. Next.js and React provide a component-oriented frontend. SQLAlchemy provides a database abstraction for SQLite or PostgreSQL. Scikit-learn provides a practical Isolation Forest implementation.",
        "The main technical risks are not the basic calculations but the boundaries between components. Generated code must be restricted, user identity must be carried through each access path, optional providers must not be treated as mandatory, and background work must not create stale or duplicate reports. The architecture handles these risks through small services and response contracts.",
        "The current verification results support the feasibility assessment. The backend suite completed with 51 passing tests under isolated SQLite and deterministic-provider settings, and the frontend production build passed. The route-level evidence is strong for upload, profile, SQL, jobs, and access isolation; a full browser-level chat/history journey remains unexecuted."
    ])

    page_block(r, "3.7 Operational, economic, and legal feasibility", [
        "Operationally, InsightForge can run locally with a Python virtual environment, a Node.js frontend, and SQLite when a PostgreSQL connection is not supplied. The user flow is short enough for demonstration and does not require an administrator to create a schema for every CSV file. Optional cloud services can be added later, but the current fallback path keeps the prototype usable offline.",
        "Economically, the project uses open-source frameworks and libraries. The main potential cost is the optional use of hosted model, database, or memory providers. Because deterministic computation remains available, a development or evaluation environment can avoid provider costs while still demonstrating the core analytical workflow.",
        "Legally and ethically, the application must be treated as a prototype. Uploaded data may contain personal or commercially sensitive fields; a production deployment would require explicit retention, consent, encryption, and access policies. The report avoids presenting the platform as a compliance-certified system."
    ], table_data=("Feasibility study", ["Dimension", "Assessment", "Conclusion"], [
        ["Technical", "Mature Python/JS analytics stack; risks controlled by modules and tests", "Feasible"],
        ["Operational", "Local setup supports SQLite and deterministic fallback", "Feasible for project scope"],
        ["Economic", "Open-source core; optional provider costs", "Low-cost prototype"],
        ["Legal/ethical", "Requires governance for real sensitive datasets", "Feasible with safeguards"],
    ], [1800, 5200, 1400]))

    page_block(r, "3.8 Tools, technologies, and platform", [
        "The frontend uses React through the Next.js App Router, TypeScript, Zustand, Plotly, and CSS/Tailwind-compatible styling. The repository currently declares Next.js 15.1.7 in package.json, while earlier project documentation describes the architecture using the Next.js 14 App Router terminology. The report records the package version currently used by the workspace rather than repeating a stale badge [4].",
        "The backend uses Python 3.12, FastAPI, Uvicorn, Pydantic, SQLAlchemy, Pandas, DuckDB, scikit-learn, LangGraph, bcrypt, Python-JOSE, SlowAPI, and optional provider libraries. Pandas and DuckDB provide the tabular and analytical operations documented by their respective projects [5], [6]. PostgreSQL is supported for durable deployment, while SQLite is useful for local evaluation. The platform is organised as a monorepo with a backend directory, a frontend directory, sample datasets, screenshots, and tests.",
        "The selection favours composability. Each technology solves a clearly bounded problem, and the deterministic core can be tested without requiring a live model or a browser session."
    ], table_data=("Technology stack", ["Layer", "Technology", "Purpose"], [
        ["Frontend", "Next.js, React, TypeScript", "Dashboard, explorer, analysis, insights"],
        ["API", "FastAPI, Uvicorn, Pydantic", "HTTP routes, validation, response contracts"],
        ["Data", "Pandas, NumPy, DuckDB", "Parsing, computation, read-only SQL"],
        ["ML", "scikit-learn Isolation Forest", "Unsupervised anomaly signals"],
        ["Agent workflow", "LangGraph, optional Gemini", "Intent, tool selection, retries, synthesis"],
        ["Persistence", "SQLAlchemy, SQLite/PostgreSQL", "Users, datasets, sessions, reports"],
        ["Testing", "Pytest, Next.js build", "Backend regression and frontend verification"],
    ], [1700, 3200, 3500]))

    page_block(r, "3.9 Use-case model", [
        "The primary use case begins with authentication and ends with an evidence-backed answer. The user registers or logs in, uploads a CSV, waits for validation and automatic analysis, opens the dataset explorer or insights page, and asks a question in the analysis page. The system reads the owner-scoped dataset, retrieves recent conversation context, selects a deterministic or optional model-assisted tool, executes the tool inside a controlled boundary, validates the result, stores the turn, and returns the response.",
        "Secondary use cases include viewing profile details, searching paginated rows, generating a direct chart, executing a read-only SQL query, executing a restricted Pandas expression, triggering anomaly detection, polling a background job, restoring chat history, clearing chat history, and deleting a dataset. Each secondary flow shares the same authentication and registry boundary.",
        "The use-case model demonstrates that the user does not directly access the DataFrame or the database. The API is the policy boundary, and the backend services perform the analytical work."
    ], image=("rId8", 8, "High-level InsightForge architecture", 6.2, 3.49))

    page_block(r, "3.10 Context-level data flow", [
        "At the context level, the user sends an upload or question to InsightForge. The system exchanges authentication information with the identity service, reads and writes dataset metadata with the persistence layer, and optionally calls an external model or memory provider. The key boundary is that the browser never sends raw executable Python to the server without passing through the Pandas validation path, and it never receives a dataset belonging to another owner.",
        "The context diagram also shows why response contracts matter. A question can produce text, rows, a chart, generated SQL, confidence, assumptions, limitations, and tool metadata. The user interface does not need to know which internal service produced each field; it only needs to render the contract.",
        "This data flow is intentionally narrower than the README marketing architecture. It describes the verified project behaviour and does not imply that every optional service is always online."
    ], image=("rId9", 9, "Context-level data flow diagram", 6.2, 3.49))

    page_block(r, "3.11 Level-1 upload and analysis flow", [
        "The upload route reads the file bytes and passes the filename, content, owner identifier, and optional dataset identifier to CsvIngestionService. The service validates the extension and content, decodes common encodings, parses the CSV, checks headers and row limits, converts reliable date columns, creates an owner-scoped dataset identifier, registers the DataFrame, and submits an auto-analysis job. Ingestion returns a summary without waiting for every analysis card to be written.",
        "The insights endpoint first checks ownership and reads a cached AutoAnalysisReportModel record. If no record exists, it returns a processing state while a job is active or submits a new job. The job runs StatisticalPass and DeterministicFallback, then persists the report. This design makes the UI responsive and allows the report to be refreshed independently of the original upload.",
        "The flow also includes failure paths. Malformed data is rejected before registration. Analysis submission errors are logged without making the upload endpoint unusable. A failed background job exposes an error state through the job endpoint."
    ], image=("rId10", 10, "Level-1 upload and analysis data flow", 6.2, 3.49))

    page_block(r, "3.12 Requirement traceability", [
        "Traceability ensures that the report can answer three questions: where a requirement is implemented, how it is exposed to a user, and how it is verified. The matrix below links representative requirements to repository modules and evidence. The same principle is applied in later chapters to the more detailed test cases.",
        "The traceability exercise also reveals gaps. The project has strong evidence for CSV upload, deterministic analysis, owner-scoped persistence, restricted execution, and frontend build. It has weaker evidence for distributed scaling, long-running production observability, and multi-user collaboration because those features are intentionally future work. Recording the gap is more credible than treating an architectural idea as an implemented feature.",
        "The report uses this distinction throughout: implemented, optional, and future are separate categories."
    ], table_data=("Requirement traceability matrix", ["ID", "Requirement", "Primary module", "Evidence"], [
        ["FR-04", "Reject malformed/oversized CSV", "services/ingestion.py", "pytest + TestClient routes"],
        ["FR-10", "Infer domain/grain/measures", "analytics/understanding.py", "grounded insight tests"],
        ["FR-11", "Generate automatic report", "analytics/auto_analysis.py", "Sample Superstore report"],
        ["FR-12", "Persist chat turns", "api/routes.py, memory/session.py", "persistence tests"],
        ["FR-14", "Restrict SQL/Pandas", "tools/sql_tool.py, tools/pandas_tool.py", "security tests"],
        ["FR-15", "Run background work", "services/jobs.py", "job polling tests"],
        ["FR-17", "Render analytical UI", "frontend/app and components", "npm run build"],
    ], [1100, 3000, 2900, 2000]))


def add_chapter_4(r: ReportBuilder) -> None:
    r.h("CHAPTER 4: DESIGN AND ARCHITECTURE", 1, page=True)
    r.p("The design of InsightForge is organised around a browser client, a policy-enforcing API, modular analytical services, safe execution tools, and owner-scoped persistence. This chapter explains the structure chart, work breakdown, modules, flows, data model, memory model, security boundary, and deployment considerations.")

    page_block(r, "4.1 Architecture principles", [
        "The first design principle is deterministic grounding before optional generation. The semantic understanding engine produces the analytical contract from the DataFrame. Automatic insights and deterministic business-question answers use that contract to select measures and dimensions. An external model can assist with tool selection or wording, but it must operate inside the same tool and validation boundaries.",
        "The second principle is a narrow policy boundary. Routes authenticate the user, retrieve only an owner-scoped dataset, and call services with typed inputs. The SQL and Pandas tools do not receive arbitrary filesystem access. The persistence layer stores metadata and analysis data, while the registry controls which DataFrames are available to a request.",
        "The third principle is graceful degradation. Optional Redis, Vector, Gemini, and hosted database services may improve the experience, but absence of those services should produce a warning, fallback, or local path rather than an empty result or an invented answer."
    ])

    page_block(r, "4.2 Structure chart and work breakdown", [
        "The work breakdown decomposes the system into six major streams: interface, API and identity, ingestion and persistence, analytics and reasoning, safe execution, and verification. Each stream is further divided into modules with a small public responsibility. This decomposition makes it possible to test the semantic engine without starting a browser and to test the frontend build without a live database.",
        "At the top level, the frontend contains pages and reusable components. The backend API connects those pages to authentication, dataset routes, chat, jobs, and insights. Under the API are services such as ingestion, jobs, authentication, registry, memory, analytics, charts, and tools. The tests exercise cross-cutting properties such as owner isolation and persistence in addition to individual calculations.",
        "The structure is intentionally not a microservice deployment. It is a modular monolith appropriate for the project scope, with boundaries that can be separated later if scale requires it."
    ], image=("rId11", 11, "Structure chart / work breakdown structure", 6.2, 3.49))

    page_block(r, "4.3 Frontend module design", [
        "The frontend uses the App Router and divides the user journey into pages rather than placing all behaviour in a single dashboard component. The datasets page manages uploads and dataset cards. The explorer page exposes rows, schema, and profile information. The analysis page provides conversation and result rendering. The insights page presents the automatic report with cards, charts, actions, and quality warnings.",
        "Services separate transport from visual components. api.ts adds authentication headers, serialises requests, handles expired tokens, and calls the backend endpoints. sessionStore.ts maintains user-namespaced browser data so that cached identifiers from one account do not appear in another account. Components such as UploadPanel, Navbar, AuthModal, and AppShell provide shared behaviour and navigation.",
        "This design gives the interface a stable dependency on response contracts rather than on internal Python objects. A backend response can include a chart specification or metadata, and the frontend can render it through the corresponding component without knowing how the result was calculated."
    ])

    page_block(r, "4.4 API gateway and route design", [
        "FastAPI routes are the gateway between the browser and the application services. Protected routes use require_current_user, which depends on JWT validation and rejects anonymous access. Dataset lookup is centralised in get_dataset, which accepts an owner identifier and converts a missing or inaccessible dataset into a 404 response. This prevents route handlers from accidentally retrieving a record without a tenant constraint.",
        "The chat route writes the user turn, loads recent history and relevant memory, invokes the planner, writes the assistant response and analysis data, and returns the typed response. The insights routes use the same ownership guard before reading or generating a report. The SQL, Pandas, chart, and anomaly routes provide direct tools while preserving authentication and dataset lookup.",
        "Rate limiting is applied at the upload and chat boundaries. The limits are not a complete denial-of-service solution, but they reduce accidental request storms and document the intended operational boundary."
    ], image=("rId14", 14, "API route and policy boundary", 6.2, 3.49))

    page_block(r, "4.5 Ingestion and dataset registry", [
        "CsvIngestionService is responsible for turning untrusted upload bytes into a validated DataFrame. It checks the filename, rejects empty content, enforces the maximum byte size, attempts UTF-8 with common fallbacks, calls pandas.read_csv, checks headers and row count, parses reliable date columns, and creates a deterministic identifier. The owner scope is included in the identifier seed so identical filenames and contents owned by different users do not overwrite one another.",
        "DatasetRegistry stores an in-memory Dataset object and persists the file and metadata needed for rehydration. The registry exposes add, get, list, delete, and clear operations with an owner_id filter. Routes use these operations instead of holding a global unscoped dictionary. The design makes local evaluation simple while preserving a path toward a durable PostgreSQL-backed deployment.",
        "Automatic analysis is submitted after registration. This separation means a valid file can appear in the dataset list even when a report job is still processing, and a temporary report failure does not erase the dataset."
    ], code='''# Owner-scoped dataset retrieval in the API boundary
def get_dataset(dataset_id: str, owner_id: str | None = None):
    try:
        return registry.get(dataset_id, owner_id=owner_id)
    except KeyError as exc:
        raise HTTPException(404, str(exc)) from exc''')

    page_block(r, "4.6 Semantic understanding layer", [
        "DataUnderstandingEngine is the central semantic guardrail. It first detects a date column, preferring an existing datetime dtype and otherwise parsing object columns whose names suggest dates or times and whose conversion success exceeds a threshold. It scores domain vocabulary across sales, marketing, finance, support, inventory, and operations. If the best score is weak or ambiguous, the domain is set to generic rather than overstated.",
        "The engine classifies identifier-like fields using name terms such as id, code, zip, postal, phone, row, and number together with uniqueness. Numeric columns that are identifiers are excluded from meaningful measures. Dimensions are selected from non-numeric columns with controlled cardinality and ranked by business vocabulary. Measures are mapped to revenue, profit, cost, quantity, discount, spend, impressions, clicks, and conversions, and derived metrics such as profit_margin, CTR, conversion_rate, CPC, CPA, and ROAS are recorded when the required fields exist.",
        "This layer produces a compact dictionary that includes domain, confidence, grain, date range, dimensions, measures, identifiers, metric columns, derived metrics, rows, columns, and the working DataFrame. public_understanding removes the DataFrame before returning the model to API or UI code."
    ], code='''# Meaningful numeric fields exclude identifier-like columns
numeric = [
    str(col) for col in working.select_dtypes(include="number").columns
    if not is_identifier_column(str(col), working[col])
]
identifiers = [
    str(col) for col in working.columns
    if is_identifier_column(str(col), working[col])
]''')

    page_block(r, "4.7 Planner and agent workflow", [
        "The project supports a LangGraph state graph with classification, tool selection, execution, validation, and synthesis nodes. classify_intent recognises visualisation, anomaly, profiling, computation, or general query intents. select_tool can ask Gemini for a JSON plan when a key is configured. If the provider is missing or fails, a rule-based fallback selects a safe default. execute_tool invokes SQL, Pandas, chart, profile, anomaly, or descriptive-statistics paths.",
        "validate_result inspects the error field. A failed execution can be retried up to two times with error feedback. If retries are exhausted, the graph routes to fallback_deterministic rather than returning an unvalidated result. synthesize_answer builds an AnalysisResponse with answer, reasoning, confidence, generated query or code, chart, anomalies, and metadata.",
        "The newer deterministic business-question path in PlannerAgent runs before the generic graph fallback for common requests. It handles executive summaries, rankings, trends, profiles, and anomalies using the semantic model. This improves the consistency of answers where choosing the correct business measure matters more than free-form generation."
    ], image=("rId12", 12, "Conversation and tool-execution activity flow", 6.2, 3.49))

    page_block(r, "4.8 Safe SQL and Pandas execution", [
        "SqlTool creates a fresh in-memory DuckDB connection for each request, registers the owner-visible DataFrames, disables external access, applies memory and temporary-directory limits, and executes only a cleaned query that begins with SELECT. The validator rejects mutations, multiple statements through semicolon removal, and filesystem/table functions such as read_csv, read_parquet, scan_csv, and glob. Results are capped to 500 rows before conversion to JSON-compatible records.",
        "PandasTool parses the expression or short script into an AST and walks the tree. Only allowed node types, method names, identifiers, and assignment targets are permitted. Dunder names, dynamic calls, imports, file operations, and unapproved methods are rejected. Execution occurs with a restricted environment and a five-second thread timeout. Series results are normalised to a DataFrame-like record list, and results are capped at 500 rows.",
        "These controls are not a replacement for a hardened sandbox process. They are a defence-in-depth layer appropriate for the current prototype and are explicitly documented as such."
    ], code='''# SQL hardening: read-only query boundary
if not self._ALLOWED_PATTERN.match(query):
    raise ValueError("Only SELECT queries are allowed.")
if self._FORBIDDEN_KEYWORDS.search(query):
    raise ValueError("Query contains forbidden keyword.")

con = duckdb.connect(":memory:", config={"enable_external_access": False})
con.execute("SET memory_limit='256MB'")''')

    page_block(r, "4.9 Automatic analysis architecture", [
        "StatisticalPass combines semantic understanding, descriptive statistics, top-value counts, grouped aggregations, period aggregations, charts, null analysis, duplicate detection, and a health score. The primary measure is chosen from a meaningful revenue column or the primary measure fallback. A primary dimension is selected from the ranked dimensions. Charts include a categorical bar view, a monthly trend view when a date is available, a distribution histogram, and a correlation heatmap when at least two meaningful numeric measures exist.",
        "DeterministicFallback turns the statistical output into an executive summary, insight cards, recommendations, actions, and anomaly notes. For a sales dataset it can report revenue, profit, margin, leading dimensions, category comparisons, time periods, and loss-making groups. The evidence field on a card stores the dimension, label, and value used to construct the statement.",
        "The design keeps facts and wording separate. A future language model may improve the prose, but it should receive the structured result rather than inventing the underlying value."
    ], image=("rId13", 13, "Automatic analysis pipeline", 6.2, 3.49))

    page_block(r, "4.10 Persistence data model", [
        "The SQLAlchemy models represent users, datasets, chat sessions, chat messages, and automatic analysis reports. User-owned records carry owner_id and dataset references. DatasetModel stores filename, storage key, row count, column schema, and creation time. ChatSessionModel links a conversation to a dataset and owner. ChatMessageModel stores role, content, optional analysis_data, and creation time. AutoAnalysisReportModel stores the JSON report and provider-use flags.",
        "The relationships are intentionally simple. Dataset deletion cascades to its report and can set a chat dataset reference to NULL where appropriate. User deletion cascades to owned records. In local SQLite evaluation, the same models provide a durable source of truth even when Redis is missing.",
        "The model does not store every DataFrame cell in the relational database. The physical file is managed by the registry/storage path, while the database stores the metadata required to identify, list, restore, and scope the dataset."
    ], table_data=("Persistence entities", ["Entity", "Important fields", "Purpose"], [
        ["User", "id, email, hashed_password", "Authentication and owner identity"],
        ["DatasetModel", "id, owner_id, filename, storage_key, schema", "Dataset metadata and rehydration"],
        ["ChatSessionModel", "id, owner_id, dataset_id", "Conversation scope"],
        ["ChatMessageModel", "session_id, role, content, analysis_data", "Cold chat history and result data"],
        ["AutoAnalysisReportModel", "dataset_id, owner_id, report_json", "Cached automatic report"],
    ], [2200, 3900, 2800]))
    r.add_image("rId17", 17, "Entity-relationship model", width=6.2, height=3.49)

    page_block(r, "4.11 Conversation memory layers", [
        "ConversationMemory models three layers. Layer 1 is an optional Upstash Redis list for recent hot turns with a configurable window and TTL. Layer 2 is an optional Upstash Vector index for semantic retrieval of relevant prior turns. Layer 3 is the SQLite or PostgreSQL database, which stores the durable full history and analysis data. When Redis or Vector is absent, the implementation uses an in-process cache and database path instead.",
        "The add method persists the session and message first, then attempts Redis and Vector writes. The get method checks Redis, then the in-process cache, then the database, and backfills Redis when possible. The get_relevant method returns an empty list when Vector or embeddings are not configured. This structure permits local testing without cloud credentials and preserves a migration path to richer memory later.",
        "The memory design is also an access-control design. Redis keys and Vector namespaces include owner and session identifiers, and database queries join the session owner before returning messages."
    ], code='''# Memory falls back when optional Redis is unavailable
if redis:
    raw = redis.lrange(_redis_key(session_id, owner_id), 0, -1)
else:
    cache_key = f"{owner_id or 'anonymous'}:{session_id}"
    return self._cache.get(cache_key, [])''')

    page_block(r, "4.12 Authentication and tenant isolation", [
        "The authentication service hashes passwords with bcrypt and verifies them on login. A signed JWT contains the user identifier and expiry. This use of a compact claims token is consistent with the JWT specification [15]. get_current_user decodes the token and confirms that the user still exists in the database. require_current_user rejects requests without a valid identity. The route dependency is used for uploads, dataset listing, profile, rows, chat, direct tools, anomalies, jobs, and insight reports.",
        "Tenant isolation is enforced at more than one layer. The registry accepts owner_id, database models index owner_id, chat sessions and messages are joined through the owner, and background jobs retain a user_id that is checked during polling. This defence in depth reduces the chance that a future route forgets to perform a second access check.",
        "The current prototype does not claim enterprise identity management, SSO, audit logging, or encryption-at-rest configuration. Those concerns belong in production hardening and are listed as future work."
    ], code='''# Authentication boundary used by protected routes
    current_user_id: Optional[str] = Depends(get_current_user),
) -> str:
    if not current_user_id:
        raise HTTPException(status_code=401, detail="Authentication required")
    return current_user_id''')

    page_block(r, "4.13 Error, retry, and job state design", [
        "Errors are handled at the boundary where they can be explained. CSV validation raises an HTTPException with a user-readable reason. Direct SQL, Pandas, and chart routes convert tool errors into HTTP 400 responses. The graph stores an error in state and retries a failed tool at most twice. The deterministic business-question path avoids the graph for common requests and can still return limitations when an input is incomplete.",
        "Background jobs use a small state machine: processing, completed, or failed. The JobManager stores a job record under a lock, submits the work to a four-worker ThreadPoolExecutor, and updates the result or error. The job endpoint filters by user ID. Automatic insight routes attach a dataset ID to the job so the frontend can distinguish a report for one dataset from another.",
        "This design makes failure visible rather than silent. A completed upload with a still-processing report is a normal state; a failed report has an explicit path for investigation."
    ], image=("rId15", 15, "Background job state transition", 6.2, 3.49))

    page_block(r, "4.14 Deployment topology and operational boundary", [
        "The intended deployment topology places the Next.js frontend at the browser-facing edge and the FastAPI backend behind a configured API URL. The backend connects to SQLite for local use or PostgreSQL for durable deployment and stores uploaded files under the dataset storage path. Optional provider adapters connect to Gemini for model assistance, Redis for hot memory, and Vector for semantic retrieval.",
        "The current local topology is intentionally simpler: the backend can run in its virtual environment, the frontend can run through the Next.js development or production command, and SQLite provides the metadata path. This is sufficient to reproduce the project and run the automated suite. A production topology would add a distributed worker, managed object storage, observability, TLS policy, secret management, and backup procedures.",
        "The earlier Vercel deployment inspection found that the deployed behaviour diverged from the corrected local implementation. The report therefore treats the local repository and its tests as the evaluation target and lists deployment synchronisation as operational follow-up rather than presenting the older deployment as proof of current correctness."
    ], image=("rId16", 16, "Operational deployment boundary", 6.2, 3.49))


def add_chapter_5(r: ReportBuilder) -> None:
    r.h("CHAPTER 5: IMPLEMENTATION", 1, page=True)
    r.p("This chapter documents how the design is realised in the repository. It follows the execution path from environment setup and upload through semantic understanding, automatic insights, conversation, safe tools, persistence, frontend presentation, and representative source modules.")

    page_block(r, "5.1 Development environment and repository layout", [
        "The repository is organised as a monorepo named AI-Data-Analyst. The backend contains the FastAPI entry point, configuration, authentication, API routes, agents, analytics, charts, core utilities, database, memory, schemas, services, tools, and tests. The frontend contains Next.js pages, reusable components, services, state, and type definitions. The datasets directory contains the Sample Superstore file and two additional CSV samples. The docs directory contains interface screenshots used in this report.",
        "The local backend environment is a Python 3.12 virtual environment at backend/.venv. The frontend uses the package manager configuration in frontend/package.json. The report generator itself is kept in scripts/generate_report.py and writes the Word artifact under docs. The production code remains separate from the report-generation helper.",
        "The implementation uses environment configuration for database URLs, JWT secrets, provider keys, file limits, and optional integrations. Secrets are not embedded in this report."
    ], code='''AI-Data-Analyst/
├── backend/app/
│   ├── api/ agents/ analytics/ charts/ core/
│   ├── database/ memory/ schemas/ services/ tools/
│   └── main.py
├── backend/tests/
├── frontend/app/
├── frontend/components/ frontend/services/
├── datasets/
├── docs/screenshots/
└── scripts/generate_report.py''')

    page_block(r, "5.2 Upload validation and dataset creation", [
        "The upload implementation begins at POST /api/upload. The route requires authentication, accepts a list of UploadFile objects, and passes each file to CsvIngestionService. The service performs validation before registering the DataFrame. It supports UTF-8 with BOM, UTF-8, Windows-1252, and Latin-1 decoding attempts, which improves compatibility with CSV files exported from different desktop tools.",
        "The service rejects non-CSV extensions, blank content, oversized files, malformed parser output, empty frames, duplicate column names, and excessive row counts. Date parsing is deliberately conservative: only object columns whose names suggest dates or times are parsed, and the conversion must succeed for at least 70 percent of values. Numeric identifiers such as YEAR_ID or POSTAL_CODE remain numeric rather than being converted into dates.",
        "After validation, the service registers the Dataset and submits an automatic-analysis task. This gives the frontend a summary immediately while the report becomes available through the insights endpoint."
    ], code='''# Date conversion remains conservative during ingestion
for col in frame.columns:
    if frame[col].dtype == "object":
        if any(term in str(col).lower() for term in ("date", "time", "timestamp")):
            parsed = pd.to_datetime(frame[col], format="mixed", errors="coerce")
            if len(parsed) and float(parsed.notna().mean()) >= 0.7:
                frame[col] = parsed''')

    page_block(r, "5.3 Semantic dataset understanding", [
        "Once the DataFrame is available, DataUnderstandingEngine creates the semantic model used by both automatic insights and chat. The engine searches for a reliable date, scores domain terms, calculates a confidence ratio, identifies identifiers, selects bounded dimensions, ranks numeric measures, and maps business concepts to columns. For the Sample Superstore file, the model identifies a sales domain, an order-line grain, Order Date as the date column, Sales as revenue, Profit as profit, Quantity as quantity, Discount as discount, and fields such as Row ID, Order ID, Customer ID, Product ID, and Postal Code as identifiers or identifier-like fields.",
        "The grain calculation prevents a common analytical error. Because multiple rows share an Order ID, the file represents order lines rather than unique orders. The report therefore distinguishes the 9,994 order-line records from the 5,009 unique orders. A user asking for order count should not be given a row count without that distinction.",
        "The public model removes the DataFrame before it is returned to the API or stored in report JSON. This keeps the response compact and avoids serialising raw data into a metadata contract."
    ], table_data=("Sample Superstore semantic model", ["Semantic field", "Detected value"], [
        ["Domain", "sales"],
        ["Grain", "order line"],
        ["Date column", "Order Date"],
        ["Revenue measure", "Sales"],
        ["Profit measure", "Profit"],
        ["Quantity measure", "Quantity"],
        ["Discount measure", "Discount"],
        ["Dimensions", "Category, Sub-Category, Region, Segment, State, City"],
        ["Identifier-like fields", "Row ID, Order ID, Customer ID, Product ID, Postal Code"],
    ], [3000, 5000]))

    page_block(r, "5.4 Profiling, quality scoring, and key metrics", [
        "StatisticalPass calculates descriptive statistics for meaningful measures and frequency counts for bounded dimensions. It computes duplicate rows, null percentages, healthy column count, and a health score. The health score starts at 100 and applies an average null penalty and a duplicate penalty capped at 20 points. The quality object also stores domain, domain confidence, grain, and date column so that a user can see why a trend is or is not available.",
        "For the Sample Superstore dataset, every field is populated and no duplicate complete rows were detected. The file has 9,994 rows and 21 columns. The primary financial measures are Sales and Profit. The computed total sales is 2,297,200.8603 and total profit is 286,397.0217, giving an overall profit margin of approximately 12.5 percent when profit is divided by sales.",
        "The implementation does not hide missingness. If a date is absent for a domain where a period trend would normally be useful, the quality warnings state that period trends are unavailable. This behaviour is preferable to silently fabricating a time axis."
    ], table_data=("Sample Superstore data profile", ["Metric", "Value"], [
        ["Rows", "9,994"],
        ["Columns", "21"],
        ["Unique orders", "5,009"],
        ["Unique customers", "793"],
        ["Total sales", "$2,297,200.86"],
        ["Total profit", "$286,397.02"],
        ["Total quantity", "37,873"],
        ["Average discount", "15.62%"],
        ["Duplicate complete rows", "0"],
        ["Null values", "0 across the supplied file"],
    ], [3600, 4400]))

    page_block(r, "5.5 Automatic insight generation", [
        "The automatic report is generated by AutoAnalysisEngine, which combines StatisticalPass and DeterministicFallback. For sales data, the fallback adds an executive summary with record count, revenue, profit, and margin. It identifies the leading primary dimension, compares Category where available, describes a period peak and weakest period, and can add profit warnings for loss-making groups. Recommendations are written as actions to investigate rather than as causal claims.",
        "The automatic cards carry a title, body, optional metric, type, importance, severity, evidence, and recommendation. This structure gives the frontend enough information to render different visual treatments and gives a reviewer enough information to trace a card back to a grouped calculation. Charts are stored as data and layout specifications rather than as screenshots generated by the backend.",
        "The response schema contains provider-use flags for observability, but the current AutoAnalysisEngine sets both flags to false and computes the report deterministically. This keeps optional provider configuration from being mistaken for verified model use."
    ], code='''# Example card evidence produced by the deterministic fallback
cards.append({
    "title": f"Top {primary_dimension} by {revenue_col}",
    "body": f"{label} leads {revenue_col} with {metric} across {records:,} records.",
    "metric": metric,
    "severity": "positive",
    "evidence": {"dimension": primary_dimension, "label": label, "value": value},
})''')

    page_block(r, "5.6 Conversational question handling", [
        "The current deterministic planner recognises several high-value user intents before invoking a generic fallback. Executive-summary requests call the automatic analysis engine and return a structured summary. Anomaly questions call Isolation Forest. Profiling questions return rows, columns, duplicates, and semantic information. Ranking questions identify a requested dimension such as category, product, region, or segment and select Profit or Sales based on the wording. Trend questions parse the primary date field and aggregate the selected measure by month.",
        "The result includes answer, reasoning, confidence, assumptions, limitations, chart, data, and metadata. For a ranking query, metadata records the dimension and measure and the generated SQL string describes the equivalent grouping. For a time query, the result records the date column and period rows. These fields make the response useful for both a human user and the frontend renderer.",
        "When a request does not match the deterministic business-question path, the planner uses the general response flow and may use the LangGraph agent. If the model is absent or fails, the deterministic executive-summary fallback remains available."
    ], code='''# Ranking questions select a semantic dimension and meaningful measure
measure = profit if any(term in lower for term in ("profit", "margin")) else revenue
if measure is None:
    measure = numeric[0] if numeric else None
if dimension and measure:
    grouped = temp.dropna().groupby(dimension)[measure].agg(["sum", "mean", "count"])
    grouped = grouped.sort_values("sum", ascending=not descending).head(5)''')

    page_block(r, "5.7 Direct SQL analysis", [
        "The direct SQL endpoint is useful for technical users and for the agent workflow. A request contains a dataset ID and query string. The route checks the dataset owner, collects all visible datasets into a table mapping, and calls SqlTool. SqlTool removes code fences and semicolons, validates the query against a SELECT-only pattern and a forbidden-keyword list, registers DataFrames in DuckDB, applies resource settings, executes the query, and returns up to 500 rows.",
        "A typical generated query for a category ranking uses a GROUP BY and SUM over Sales, ordered descending with a limit of five. The chart builder can use the returned non-numeric field as x and numeric total as y. The response includes generated_sql and metadata rows so the user can inspect the computation rather than receiving an unexplained chart.",
        "The SQL boundary prevents common destructive or exfiltrating operations, but it is not presented as a formal database isolation guarantee. A production deployment would still restrict network access, use least-privilege credentials, and monitor resource consumption."
    ], code='''SELECT Category,
       SUM(Sales) AS total_Sales,
       COUNT(*) AS records
FROM dataset_<id>
GROUP BY Category
ORDER BY total_Sales DESC
LIMIT 5''')

    page_block(r, "5.8 Restricted Pandas analysis", [
        "The Pandas endpoint is intended for expressions that are more natural in DataFrame syntax than in SQL. The tool strips optional Markdown fences and a simple result assignment, parses the remaining code in eval or exec mode, walks the AST, and checks every node. The use of Python’s abstract syntax tree representation is based on the standard-library AST model [11]. Allowed names are limited to df, pd, result-like assignment targets, and a small set of built-in functions. Allowed method calls include aggregation, sorting, grouping, missing-value handling, correlations, joins, date conversion, quantiles, and related transformations.",
        "The execution environment exposes a restricted builtins dictionary and a copy of the DataFrame. A ThreadPoolExecutor enforces a five-second timeout. Results must be a DataFrame or Series and are capped to 500 rows before conversion. The design avoids importing modules, opening files, evaluating dynamic code, or calling unapproved DataFrame methods.",
        "The test suite treats the AST validator as a security boundary and includes rejection cases. The report records the mechanism and its limitations so that a future implementation can move high-risk execution into a separate process or service."
    ], code='''# AST validation rejects unapproved method calls and names
if isinstance(node, ast.Call):
    func = node.func
    if isinstance(func, ast.Attribute):
        if func.attr not in ALLOWED_CALL_NAMES:
            raise UnsafeExpression(f"Disallowed method call: {func.attr}")
    elif isinstance(func, ast.Name):
        if func.id not in ALLOWED_BUILTIN_CALLS:
            raise UnsafeExpression(f"Disallowed function call: {func.id}")''')

    page_block(r, "5.9 Interactive chart generation", [
        "InsightForge supports chart specifications for bar, line or scatter-style trends, pie, histogram, and heatmap outputs. The backend produces a serialisable object containing data traces and a layout. The frontend uses the chart type and data values to render an interactive visual. A chart result is accompanied by the answer and reasoning so that a visual is not detached from the question that created it.",
        "Automatic analysis selects a categorical bar chart for the leading dimension, a monthly trend chart for the primary date and measure, a distribution histogram for the primary measure, and a heatmap when multiple meaningful numeric fields exist. Direct chart requests use ChartFactory with validated dataset fields. Generic agent synthesis can also construct a chart from returned rows when the result contains at least two columns.",
        "The chart design deliberately avoids using identifier-like fields as default measures. This is one of the main reasons for carrying semantic understanding into the chart and chat paths rather than treating visualisation as a purely presentational step."
    ], table_data=("Chart outputs", ["Chart", "Typical input", "Purpose"], [
        ["Bar", "Category + Sales", "Compare groups"],
        ["Trend", "Order Date + Sales", "Show monthly movement"],
        ["Pie", "Category + Sales", "Show composition for bounded groups"],
        ["Histogram", "Sales", "Inspect distribution"],
        ["Heatmap", "Sales, Quantity, Discount, Profit", "Inspect meaningful correlations"],
    ], [1800, 3600, 3200]))

    page_block(r, "5.10 Isolation Forest anomaly detection", [
        "Anomaly detection is implemented as a statistical signal rather than a business verdict. AnomalyService selects numeric columns, drops incomplete rows, requires at least ten records and one numeric column, fits IsolationForest with a fixed random state and a low contamination setting, and uses the decision function to rank unusual observations. This interpretation follows the documented Isolation Forest score semantics, where lower decision scores indicate more abnormal observations [7]. It returns up to fifteen rows with row index, numeric values, and a reason based on the fields that differ most from the median relative to standard deviation.",
        "On the Sample Superstore data, a broader diagnostic using the numeric Sales, Quantity, Discount, and Profit fields identifies many statistical outliers. The user-facing service limits the returned list for readability. The report does not label these rows as fraud, errors, or root causes. The appropriate interpretation is that the rows deserve inspection in the original business context.",
        "The asynchronous anomaly endpoint copies the DataFrame and submits detection to JobManager, which is useful when the dataset is large enough that the model should not block the request thread."
    ], code='''# The service returns a bounded list of interpretable signals
outliers = (
    numeric_with_scores[numeric_with_scores["_score"] < 0]
    .sort_values("_score")
    .head(max_anomalies)
)''')

    page_block(r, "5.11 Persistence of sessions and analysis data", [
        "The chat route persists both the user’s message and the assistant’s response. The assistant turn stores analysis_data, which can include charts, SQL, rows, anomalies, and metadata. This makes a session more than a text transcript: it is a record of the analytical result rendered to the user. The history endpoint can restore those turns for the same owner and session.",
        "The memory implementation first writes the durable database record and then attempts the optional fast and semantic layers. If a database column is not yet migrated to support analysis_data, a compatibility branch writes the core role/content fields rather than failing the whole message. The design supports gradual schema evolution during development.",
        "Deleting chat history clears all available layers for the owner-scoped session. Dataset deletion removes the dataset and related report, reducing the chance that a stale browser entry points to a deleted resource."
    ])

    page_block(r, "5.12 Dashboard and dataset workspace", [
        "The dashboard screenshot shows the intended high-level workspace. It contains the InsightForge brand, navigation, dataset cards, row and column totals, upload controls, and suggested questions. The cards provide entry points to Analyse and Explore, which keeps the first interaction understandable for a user who has not yet written a query.",
        "The dashboard is a presentation of dataset registry state rather than a separate analytics engine. It uses the API client and user-scoped state to list datasets and calculate the visible totals. The interface is designed with a dark analytical theme, focused status badges, and clear actions for uploading or clearing data.",
        "The screenshot was captured during development with the repository’s sample datasets. It is included as an interface illustration; exact displayed totals may vary depending on the datasets currently loaded in a local session."
    ], image=("rId4", 4, "InsightForge dashboard with dataset cards, totals, and suggested questions", 6.2, 3.49))

    page_block(r, "5.13 Conversational analysis interface", [
        "The analysis screenshot shows the conversational response pattern: a user prompt, an AI response card, a chart, generated SQL, confidence/provider badges, an explanatory paragraph, and an input field for a follow-up question. This layout demonstrates progressive disclosure. A user can read the answer first and open the generated query when they need technical detail.",
        "The current corrected local implementation improves on the older screenshot by grounding common business questions through the deterministic planner. The screenshot remains valuable because it shows the product interaction and visual hierarchy rather than serving as a claim that every displayed answer is the current output of the local code.",
        "The interface also supports history restoration and authenticated state handling. When a token expires, the frontend clears stale user-scoped information and directs the user back through authentication instead of continuing with an ambiguous session."
    ], image=("rId5", 5, "Conversational analysis page with chart, generated SQL, and explanation", 6.2, 3.49))

    page_block(r, "5.14 API response contracts", [
        "AnalysisResponse is the main conversational contract. It includes answer, reasoning, confidence, assumptions, limitations, generated_sql, generated_pandas, chart, insights, anomalies, data, and metadata. Defaults allow a response to contain only the fields relevant to a question while preserving a stable schema for the frontend.",
        "AutoAnalysisResponse contains dataset_id, executive_summary, trend_story, insight cards, charts, recommendations, actions, key metrics, domain, domain confidence, grain, data quality, anomaly note, generation time, provider flags, and status. DataQualityReport contains row and column totals, duplicate rows, null columns, healthy columns, health score, warnings, domain, confidence, grain, and date column.",
        "Typed contracts are important in a system that combines deterministic code and optional generative services. They create a boundary where incomplete or unexpected provider output can be rejected, defaulted, or converted into a controlled fallback."
    ], code='''class AnalysisResponse(BaseModel):
    answer: str
    reasoning: str = ""
    confidence: float = Field(default=0.5, ge=0, le=1)
    assumptions: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    generated_sql: str | None = None
    chart: dict[str, Any] | None = None
    anomalies: list[dict[str, Any]] = Field(default_factory=list)
    data: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)''')

    page_block(r, "5.15 Representative implementation: ingestion route", [
        "The ingestion route is intentionally thin. It applies the rate limiter, requires the current user, reads the optional dataset identifier header for a single-file update, and delegates file handling to CsvIngestionService. The route then converts the Dataset object to DatasetSummary. Keeping parsing outside the route makes the service testable and prevents HTTP details from leaking into analytical code.",
        "The asynchronous route follows the same policy boundary but copies file bytes into a closure and submits a job. The job result contains summaries for the uploaded files. In both cases, the owner ID is carried into ingestion so that the registry and metadata records use the same scope.",
        "This pattern is repeated throughout the API: route handlers validate access and shape responses, while domain services own the computation."
    ], code='''@router.post('/upload', response_model=list[DatasetSummary])
@limiter.limit("10/minute")
async def upload(
    request: Request,
    files: list[UploadFile] = File(...),
    current_user: str = Depends(require_current_user)
):
    requested_id = request.headers.get("X-Dataset-ID") if len(files) == 1 else None
    return [summary(await ingestion.ingest(
        f, owner_id=current_user, dataset_id=requested_id
    )) for f in files]''')

    page_block(r, "5.16 Representative implementation: semantic engine", [
        "The semantic engine uses small helper functions rather than a single opaque model. _tokens normalises names, _name_score ranks terms, is_identifier_column combines vocabulary and uniqueness, _detect_date_column checks types and parse ratios, and _detect_grain uses domain-specific patterns. DataUnderstandingEngine.run then combines those components into one result.",
        "This design is easy to extend. A future domain can add terms to DOMAIN_TERMS and provide a grain rule. A new business measure can be mapped in the metric_columns dictionary. The tests can add a small fixture to confirm that the new field is selected without changing the planner or frontend.",
        "The trade-off is that column-name heuristics are not a complete ontology. The system reports domain confidence and limitations so that a user can recognise when the inference is weak."
    ], code='''domain, best_score = max(
    scores.items(), key=lambda item: item[1], default=("generic", 0)
)
confidence = min(0.99, best_score / max(total_score, 1)) if best_score else 0.0
if best_score < 2 or confidence < 0.22:
    domain = "generic"
    confidence = min(confidence, 0.4)''')

    page_block(r, "5.17 Representative implementation: deterministic planner", [
        "PlannerAgent._answer_business_question is the most important implementation detail for the corrected local behaviour. It computes understanding once, retrieves the meaningful metrics, and then branches by question type. The executive summary path invokes AutoAnalysisEngine. The ranking path identifies a preferred dimension, selects Profit for profit questions or Revenue for other business totals, groups and sorts the rows, and constructs a chart. The trend path parses the date and aggregates by month.",
        "The planner returns confidence values that reflect the deterministic nature of the operation, but those values are not statistical accuracy estimates. A confidence of 0.97 indicates that the system matched a well-defined deterministic pattern; it does not mean that the input data is complete or that the business interpretation is universally correct.",
        "This distinction is recorded in the report to avoid confusing program certainty with data quality."
    ], code='''if any(term in lower for term in ("executive summary", "key metrics", "overview")):
    report = self.auto_analysis.run(dataset_id, working)
    return AnalysisResponse(
        answer=report.executive_summary,
        reasoning="The deterministic insight engine classified the dataset.",
        confidence=0.94,
        limitations=report.data_quality.warnings[:3],
        insights=[card.body for card in report.insights[:5]],
        metadata={"tool": "executive_summary", "report": report.model_dump()},
     )''')


    page_block(r, "5.18 Representative implementation: memory and persistence", [
        "The memory implementation demonstrates the project’s approach to optional infrastructure. It always attempts the database path first because durable history is the source of truth. Redis is used only when a client is available, and Vector is used only when a client and embedding are available. A warning is logged for provider failures, while the user-facing request continues through the fallback path.",
        "This implementation is useful in a college project because it avoids an all-or-nothing setup. A reviewer can run the local application with SQLite and no Redis credentials, observe the same basic chat workflow, and later add the external services to test hot memory and semantic retrieval. The report treats those services as optional rather than implying they were always active during testing.",
        "The durable records include owner and dataset scope, which provides the basis for history restoration and deletion."
    ], code='''# Assistant results retain structured analysis data
memory.add(
    body.session_id,
    'assistant',
    response.answer,
    owner_id=current_user,
    dataset_id=body.dataset_id,
    analysis_data=response.model_dump(),
)''')


def add_chapter_6(r: ReportBuilder) -> None:
    r.h("CHAPTER 6: TESTING", 1, page=True)
    r.p("Testing evaluates whether the implemented system satisfies the requirements and whether the analytical results are grounded in the supplied data. The project uses a layered strategy: unit tests for helpers and guards, regression tests for semantic behaviour, persistence tests for owner isolation, TestClient route/integration tests for HTTP workflows, dataset-based evaluation, and a frontend production build for TypeScript and route compilation.")

    page_block(r, "6.1 Testing strategy", [
        "The testing strategy follows the risk profile of the project. Ordinary arithmetic is relatively easy to verify, but semantic field selection, untrusted code execution, authentication scope, asynchronous state, and optional-service fallback can fail in less obvious ways. Tests therefore cover both positive and negative paths. A valid SQL query should return rows, while a mutation or filesystem function should be rejected. A valid dataset should be available to its owner, while another user should receive no access.",
        "The analytics tests use small DataFrames and the Sample Superstore file to make results reproducible. The persistence tests create isolated database state and verify that chat messages, sessions, datasets, and reports are associated with the correct user. Frontend verification uses the project’s actual npm build command rather than a mocked compilation.",
        "The test suite is not a claim of exhaustive production coverage. It is evidence that the core project paths and known failure modes are exercised."
    ])

    page_block(r, "6.2 Test environment and execution", [
        "Backend tests were executed from the workspace root using the Python interpreter in backend/.venv. The final run completed with 51 passing tests and one warning. The test environment uses local database configuration and deterministic services so that the suite does not depend on live Gemini, Redis, Vector, or a remote PostgreSQL instance.",
        "The frontend was verified from frontend with npm run build. The successful build performed Next.js compilation, TypeScript checking, page generation, and static route processing for the application pages. The build output included the dashboard, dataset, analysis, exploration, and insights routes used by the user workflow.",
        "The automated TestClient tests exercised registration and authentication, synchronous and asynchronous upload, dataset listing, row/profile/SQL routes, asynchronous anomaly polling, job ownership isolation, and HTTP error paths. Persistence tests separately exercised registry rehydration and owner-scoped conversation memory. A single full browser journey through automatic insights, chat, history, and deletion was not executed as one test."
    ], table_data=("Verification commands and results", ["Check", "Command", "Result / evidence"], [
        ["Backend suite", "pytest -q with SQLite and optional providers disabled", "51 passed, 1 warning"],
        ["Frontend build", "npm run build", "Passed"],
        ["Syntax check", "python -m py_compile on changed backend modules", "Passed"],
        ["HTTP integration", "pytest TestClient route/job tests", "Passed for covered routes; full browser journey not executed"],
    ], [2600, 4100, 1800]))

    page_block(r, "6.3 Unit and regression test design", [
        "Unit tests target small modules such as SQL validation, AST validation, profiling, anomaly output, dataset registration, and response contracts. Regression tests target behaviour that previously produced a misleading result. The strongest regression is semantic: a request about a category or executive summary should use Sales or Profit when present rather than average Postal Code or Row ID.",
        "The tests also protect compatibility behaviour. Chat history should remain readable when the analysis_data column is not present in an older local schema. Session data should be restored from the database when the fast in-process cache is empty. Dataset identifiers should be owner-scoped and stable for identical content within the same ownership scope.",
        "Test names and fixtures act as executable documentation. They show future maintainers which behaviours are intentional and which changes require a deliberate update to both code and evidence."
    ], table_data=("Representative backend test cases", ["ID", "Test objective", "Expected result"], [
        ["T-01", "Valid CSV ingestion", "Dataset summary returned and dataset registered"],
        ["T-02", "Empty or malformed CSV", "HTTP 400 with explanatory message"],
        ["T-03", "Oversized file or row count", "HTTP 413/400 guard triggers"],
        ["T-04", "Duplicate headers", "Upload rejected"],
        ["T-05", "Identifier exclusion", "Row ID/Postal Code not selected as primary measure"],
        ["T-06", "Sales ranking", "Correct dimension and total measure returned"],
        ["T-07", "Monthly trend", "Peak and weakest periods computed from date column"],
        ["T-08", "Chat persistence", "User and assistant turns reload from database"],
        ["T-09", "Owner isolation", "User B cannot read User A dataset/history"],
        ["T-10", "Background job", "Job transitions to completed or failed with result/error"],
    ], [1000, 3900, 3600]))

    page_block(r, "6.4 Ingestion validation tests", [
        "Ingestion tests verify that valid CSV bytes become a DataFrame with the expected columns and that date-like fields are converted only when parsing succeeds for a high proportion of values. The negative cases cover empty bytes, unsupported extensions, parser errors, duplicate headers, empty frames, too many rows, and oversized payloads. These cases matter because an invalid DataFrame would otherwise create misleading downstream insights.",
        "The service also tests the dataset identifier path. The owner scope and content are included in a hash seed, while an explicitly supplied identifier is accepted only when it matches the allowed pattern. This prevents a malformed identifier from becoming a filesystem or database key.",
        "The outcome is a clear boundary: later analytics can assume that the input has headers, at least one row, unique column names, and a bounded size."
    ], table_data=("Ingestion validation matrix", ["Input condition", "Expected status", "Reason"], [
        ["Valid CSV", "200", "DataFrame registered"],
        ["Empty content", "400", "No data to analyse"],
        ["Non-CSV filename", "400", "Unsupported input type"],
        ["Malformed parser input", "400", "Cannot trust the frame"],
        ["Duplicate header", "400", "Ambiguous schema"],
        ["Oversized bytes", "413", "Resource guard"],
        ["Too many rows", "400", "Resource guard"],
    ], [3300, 1800, 3400]))

    page_block(r, "6.5 Security and restricted-execution tests", [
        "The SQL tests verify that only SELECT statements are accepted and that mutating operations such as INSERT, UPDATE, DELETE, DROP, CREATE, ALTER, TRUNCATE, COPY, ATTACH, DETACH, LOAD, INSTALL, CALL, and PRAGMA are rejected. Filesystem table functions such as read_csv and read_parquet are also rejected. The per-request DuckDB connection is closed after execution.",
        "The Pandas tests verify that allowed expressions such as df.head(), groupby, sum, mean, and value_counts return DataFrame-like records. Negative tests target imports, dunder attributes, unapproved method calls, unknown variables, unsafe assignment targets, and invalid result types. The timeout path is included as a safety requirement even though a short local fixture may not exercise every scheduler condition.",
        "Authentication tests verify that missing or invalid bearer tokens produce a 401 response. Owner-scope tests verify that a valid token does not grant access to another user’s dataset, session, job, or report."
    ], table_data=("Security validation cases", ["Case", "Attack or failure", "Control"], [
        ["S-01", "SQL mutation", "SELECT-only pattern and keyword blocklist"],
        ["S-02", "SQL filesystem scan", "Forbidden table functions and external access disabled"],
        ["S-03", "Pandas import", "AST node/name allowlist"],
        ["S-04", "Pandas dunder access", "Prefix rejection"],
        ["S-05", "Pandas long execution", "Thread timeout"],
        ["S-06", "Missing JWT", "require_current_user returns 401"],
        ["S-07", "Cross-user dataset lookup", "owner_id filter in registry"],
    ], [1800, 3600, 3100]))

    page_block(r, "6.6 Persistence and tenant-isolation tests", [
        "Persistence tests verify that users, datasets, sessions, messages, and reports can be stored and retrieved through the local database path. The tests cover the transition from an empty in-process cache to a database-backed history load and confirm that assistant analysis_data can be preserved when the schema supports it.",
        "The most important isolation assertion is negative: a user with a valid token must not receive another user’s dataset merely by knowing its identifier. The same principle is applied to chat sessions and background jobs. The owner ID is passed through route dependencies, registry operations, database filters, and job polling.",
        "This evidence supports the claim that the current project has application-level tenant isolation. It does not claim that a production database has row-level security enabled; that would be a separate deployment control."
    ], code='''# Owner scope is part of every dataset retrieval
# Chat history joins the session owner before returning messages
.filter(
    ChatMessageModel.session_id == session_id,
    ChatSessionModel.owner_id == owner_id,
)''')

    page_block(r, "6.7 Semantic insight regression tests", [
        "The semantic regression tests are designed around the main project failure mode: the application must not choose a numeric identifier when a meaningful business measure exists. Fixtures with fields such as Row ID, Postal Code, Sales, Profit, Category, and Order Date verify that the semantic model classifies the fields correctly and that automatic cards and chat responses use the correct measure.",
        "The tests also verify that category questions select Category rather than the first available dimension, that profit questions choose Profit rather than Sales, and that trend questions aggregate by the detected date column. They inspect response metadata and rows in addition to the prose answer, which makes a test less dependent on exact wording.",
        "This approach is important for AI-assisted applications: a response can be linguistically different and still be correct if its selected tool, measure, dimension, and evidence are correct."
    ], table_data=("Grounded insight regression checks", ["Question type", "Expected semantic behaviour", "Evidence"], [
        ["Executive summary", "Sales/profit metrics used", "Report key_metrics and cards"],
        ["Top categories by sales", "Category grouped by Sales", "Rows, dimension, measure metadata"],
        ["Worst products by profit", "Product grouped by Profit ascending", "Rows and generated query"],
        ["Monthly trend", "Order Date parsed and grouped by month", "Period rows and peak/worst"],
        ["Profile", "Identifiers separated from measures", "Understanding metadata"],
        ["Anomaly request", "Numeric measures scored; signal labelled", "Anomaly list and limitation"],
    ], [2500, 3900, 2100]))

    page_block(r, "6.8 HTTP integration and asynchronous-job coverage", [
        "The executed TestClient coverage is distributed across route and job tests rather than one monolithic smoke test. Authentication fixtures register and log in temporary users. The route tests upload CSV content, list datasets, retrieve rows and profiles, execute validated SQL, and assert response status and payloads.",
        "The asynchronous-job tests submit CSV ingestion and anomaly-detection jobs, poll GET /api/jobs/{id} until completion, verify returned results, and check that another user cannot poll the owner’s job. These tests validate route wiring, JobManager state changes, response serialisation, and owner checks.",
        "The full browser sequence involving the insights page, chat response, history restoration, and deletion remains a manual or future integration-test item. It is therefore reported as unexecuted rather than being described as a passed end-to-end test."
    ])

    page_block(r, "6.9 Frontend production build", [
        "The frontend build is a static and type-level verification of the user interface. It checks that page modules, components, service calls, types, and dependencies compile under the configured Next.js toolchain. The successful build is important because a backend endpoint can be correct while a TypeScript mismatch prevents the feature from being used.",
        "The build covered the application routes for the workspace, datasets, analysis, exploration, and insights flows. It also validates that the current insight types agree with the backend response shape closely enough for production bundling. It does not replace browser interaction testing, but it is a real project check rather than a synthetic assertion.",
        "The final report includes screenshots because visual layout and information hierarchy cannot be established by a build alone."
    ], table_data=("Frontend build coverage", ["Route or area", "Purpose", "Verification"], [
        ["Workspace/dashboard", "Dataset cards and upload entry point", "Next.js build"],
        ["Datasets", "Upload/list/delete flow", "Next.js build; route tests cover upload/list"],
        ["Explore/[id]", "Rows, search, profile", "Next.js build"],
        ["Analyse/[id]", "Chat, charts, response details", "Next.js build + screenshot"],
        ["Insights/[id]", "Automatic report and actions", "Next.js build; browser journey not executed"],
    ], [2200, 4200, 2100]))

    page_block(r, "6.10 Performance and resource boundaries", [
        "The project does not claim a formal performance benchmark, but it includes practical resource limits. Uploads are capped at 25 MB by default and row counts at 500,000. SQL results and Pandas results are capped at 500 rows. DuckDB memory and temporary-directory limits are configured per connection. Pandas execution has a five-second timeout. Rate limits apply to uploads and chat.",
        "The ThreadPoolExecutor moves ingestion, automatic analysis, and asynchronous anomaly detection away from the immediate request path. This improves responsiveness for moderate workloads, but an in-process queue has a limited capacity and is lost when the process restarts. A distributed queue is therefore a future deployment improvement, not a current performance guarantee.",
        "The report focuses on correctness and bounded behaviour rather than reporting unmeasured latency numbers. A future performance study should record dataset sizes, hardware, provider state, cold/warm cache, and percentile latency before making comparative claims."
    ])

    page_block(r, "6.11 Sample Superstore evaluation results", [
        "The Sample Superstore file provides a useful end-to-end validation fixture because it contains dates, business dimensions, identifiers, and several measures. It has 9,994 order-line rows, 21 columns, 5,009 unique orders, 793 unique customers, and no missing values or duplicate complete rows in the supplied file.",
        "The computed totals are Sales = $2,297,200.86, Profit = $286,397.02, Quantity = 37,873, and mean Discount = 15.62 percent. Technology leads category sales with $836,154.03, while Furniture leads the category-level profit warning because its total profit is only $18,451.27 compared with Technology at $145,454.95 and Office Supplies at $122,490.80. West leads regional sales at $725,457.82.",
        "The time aggregation identifies November 2017 as the peak month at $118,447.83 and February 2014 as the weakest month at $4,519.89. Tables is the weakest sub-category by total profit at -$17,725.48. Cubify CubeX 3D Printer Double Head Print is the largest loss-making product in the grouped result at approximately -$8,879.97. These values are used as report evidence, not as general claims about all sales data."
    ], table_data=("Evaluation results from Sample Superstore", ["Finding", "Value"], [
        ["Top category by Sales", "Technology — $836,154.03"],
        ["Top region by Sales", "West — $725,457.82"],
        ["Peak month", "2017-11 — $118,447.83"],
        ["Weakest month", "2014-02 — $4,519.89"],
        ["Weakest sub-category by Profit", "Tables — -$17,725.48"],
        ["Largest loss-making product", "Cubify CubeX 3D Printer Double Head Print — -$8,879.97"],
    ], [3600, 4400]))

    page_block(r, "6.12 Defect analysis and corrective changes", [
        "The deployment inspection identified two important defects in an older deployed state: a category-level question selected Postal Code as the measure, and the executive summary also reported an average Postal Code instead of business sales or profit. Automatic charts could likewise select Row ID because generic first-numeric selection did not understand identifiers. These defects were not treated as cosmetic issues; they indicated a semantic contract failure.",
        "The corrective implementation added DataUnderstandingEngine, identifier detection, domain and grain inference, metric mapping, deterministic automatic analysis, and deterministic business-question handling. The planner now chooses a requested dimension and a meaningful measure. The chart and insight paths receive the same semantic model. Regression tests were added for grounded answers, while persistence tests were extended for owner-scoped history and analysis data.",
        "This defect-and-correction record demonstrates the value of evaluating the user-visible result rather than relying only on compilation. A model or route can be technically connected and still produce a business-invalid answer."
    ])


if __name__ == "__main__":
    main()
