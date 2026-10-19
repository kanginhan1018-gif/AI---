"""Build the competition revision from verified tables and a short source document."""
from pathlib import Path
import csv
import re
import html
import json
import os
import zipfile

os.environ.setdefault("MPLCONFIGDIR", "/tmp/seoul-contest-matplotlib")
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
import numpy as np
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib import colors
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_LEFT
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak
from pypdf import PdfReader

ROOT = Path(__file__).resolve().parents[1]
ASSETS = ROOT / "docs/contest_assets"
ASSETS.mkdir(exist_ok=True)
OUT = ROOT / "outputs/reports"
OUT.mkdir(parents=True, exist_ok=True)
FONT = "/System/Library/Fonts/Supplemental/AppleGothic.ttf"
assert Path(FONT).exists()
fp = FontProperties(fname=FONT)
plt.rcParams.update({"font.family": fp.get_name(), "axes.unicode_minus": False,
                     "font.size": 12, "axes.spines.top": False, "axes.spines.right": False})


def read_csv(path):
    with path.open() as stream:
        return list(csv.DictReader(stream))


bands = [r for r in read_csv(ROOT / "outputs/tables/seoul_drt_policy/treatment_timeband_burden.csv") if r["district"] == "three_districts"]
assert sum(int(r["records"]) for r in bands) == 6683
assert sum(int(r["over_60_records"]) for r in bands) == 1374
labels = ["07~09시대", "10~14시대", "15~17시대", "그 밖의 시간"]
fig, axes = plt.subplots(1, 2, figsize=(12, 3.6), gridspec_kw={"width_ratios": [1.1, 1]})
ax = axes[0]
rates = [float(r["over_60_pct"]) for r in bands]
ax.barh(labels, rates, color=["#174e76", "#9babb5", "#66869d", "#abb7c0"], height=.55)
ax.invert_yaxis(); ax.set_xlim(0, 58); ax.set_xlabel("접수→승차 60분 초과 비율 (%)")
for i, r in enumerate(bands):
    ax.text(rates[i]+.7, i, f"{rates[i]:.2f}%\nn={int(r['records']):,}", va="center", fontsize=10)
ax.set_title("시간대별 시간 부담", loc="left", fontsize=14, pad=12)
ax = axes[1]
q = [float(r["queue_mean_min"]) for r in bands[:3]]
p = [float(r["pickup_mean_min"]) for r in bands[:3]]
ax.barh(labels[:3], q, label="접수→배차", color="#174e76", height=.55)
ax.barh(labels[:3], p, left=q, label="배차→승차", color="#9babb5", height=.55)
ax.invert_yaxis(); ax.set_xlim(0, 64); ax.set_xlabel("같은 집합의 평균 시간 (분)")
for i in range(3):
    ax.text(q[i]/2, i, f"{q[i]:.1f}", ha="center", va="center", color="white", fontsize=11)
    ax.text(q[i]+p[i]/2, i, f"{p[i]:.1f}", ha="center", va="center", fontsize=11)
ax.set_title("승차 전 단계 분해", loc="left", fontsize=14, pad=12)
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, -.23), ncol=2, fontsize=11)
fig.tight_layout(w_pad=2); fig.savefig(ASSETS / "time_and_stage.png", dpi=180, bbox_inches="tight"); plt.close(fig)

monthly = [r for r in read_csv(ROOT / "outputs/tables/public_service_necessity/purpose_burden_monthly.csv") if r["purpose_group"] == "explicit_treatment_rehab" and r["cohort"] == "within_1min" and r["district"] != "ALL"]
districts = ["중구", "성동구", "동대문구"]
assert len(monthly) == 36 and all(int(r["over_60_records"]) > 0 for r in monthly)
values = np.array([[float(next(r for r in monthly if r["district"] == d and r["month"] == f"2025-{m:02d}")["over_60_pct"]) for m in range(1, 13)] for d in districts])
fig, ax = plt.subplots(figsize=(12, 2.35))
im = ax.imshow(values, cmap="Blues", vmin=0, vmax=45, aspect="auto")
ax.set_yticks(range(3), districts); ax.set_xticks(range(12), [f"{m}월" for m in range(1, 13)])
for i in range(3):
    for j in range(12):
        ax.text(j, i, f"{values[i,j]:.1f}", ha="center", va="center", fontsize=11, color="white" if values[i,j]>25 else "#15364b")
ax.set_title("2025년 월별 60분 초과 비율 (%)", loc="left", fontsize=14, pad=12)
fig.colorbar(im, ax=ax, fraction=.025, pad=.02)
fig.tight_layout(); fig.savefig(ASSETS / "monthly_burden.png", dpi=180, bbox_inches="tight"); plt.close(fig)

costs = read_csv(ROOT / "outputs/tables/seoul_cost_verification/central_case.csv")
assert len(costs) == 3
fig, ax = plt.subplots(figsize=(12, 3.3))
amounts = [float(r["recurring_krw_per_capacity_equivalent"])/10000 for r in costs]
ax.barh(["1대", "2대", "3대"], amounts, color="#738795", height=.55); ax.invert_yaxis()
for i, amount in enumerate(amounts): ax.text(amount+.12, i, f"{amount:.2f}", va="center", fontsize=12)
ax.axvline(5.97, color="#174e76", lw=1.5, linestyle="--", label="장애인콜택시 공개 평균 5.97만원")
ax.axvline(4.4025, color="#a66c26", lw=1.5, linestyle=":", label="법인특장택시 공개 평균 4.40만원")
ax.set_xlim(0, 11.5); ax.set_xlabel("가정에 따른 처리능력 환산 1건당 반복비용 (만원)")
ax.set_title("구매비 제외 기준 가정도 비교값 초과", loc="left", fontsize=14, pad=12)
ax.legend(frameon=False, loc="upper left", bbox_to_anchor=(0, -.44), ncol=2, fontsize=10)
fig.tight_layout(); fig.savefig(ASSETS / "cost_screen.png", dpi=180, bbox_inches="tight"); plt.close(fig)

source = (ROOT / "docs/2026-10-18-contest-submission.md").read_text()
assert source.count("<!-- pagebreak -->") == 5
body = source.split("---", 2)[2].strip()
pdfmetrics.registerFont(TTFont("Korean", FONT))
base = dict(fontName="Korean", wordWrap="CJK", alignment=TA_LEFT, textColor=colors.HexColor("#20292e"))
styles = {"body": ParagraphStyle("body", fontSize=10, leading=15.3, spaceAfter=7, **base),
          "h2": ParagraphStyle("h2", fontSize=14, leading=19, spaceAfter=10, keepWithNext=True, **base),
          "h3": ParagraphStyle("h3", fontSize=10.7, leading=15.5, spaceBefore=5, spaceAfter=5, keepWithNext=True, **base),
          "cell": ParagraphStyle("cell", fontSize=9, leading=12.8, **base),
          "title": ParagraphStyle("title", fontSize=18, leading=24, spaceAfter=7, **base)}


def inline(text):
    text = html.escape(text)
    text = re.sub(r"https?://[^\s<]+", lambda m: f'<link href="{m.group(0)}" color="#174e76">{m.group(0)}</link>', text)
    text = re.sub(r"\*\*(.*?)\*\*", r"<b>\1</b>", text)
    text = re.sub(r"`([^`]+)`", r"\1", text)
    return text


story = [Paragraph("서울 치료 재활 이동지원의 시간 부담과<br/>요일별 운영 개선", styles["title"]),
         Paragraph("망젤이네  |  교통문제 데이터 분석 공모전  |  2026.10.19", styles["body"]), Spacer(1, 8)]
lines = body.splitlines(); i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line: i += 1; continue
    if line == "<!-- pagebreak -->": story.append(PageBreak()); i += 1; continue
    if line.startswith("### "): story.append(Paragraph(inline(line[4:]), styles["h3"])); i += 1; continue
    if line.startswith("## "): story.append(Paragraph(inline(line[3:]), styles["h2"])); i += 1; continue
    if line.startswith("!["):
        path = ROOT / "docs" / re.search(r"\]\((.*?)\)", line).group(1)
        img = Image(str(path)); img.drawHeight *= 502/img.drawWidth; img.drawWidth=502
        story.extend([img, Spacer(1, 7)]); i += 1; continue
    if line.startswith("|"):
        table_rows = []
        while i < len(lines) and lines[i].strip().startswith("|"):
            raw = lines[i].strip()
            if not re.fullmatch(r"[|:\-\s]+", raw):
                table_rows.append([Paragraph(inline(c.strip()), styles["cell"]) for c in raw.strip("|").split("|")])
            i += 1
        n = len(table_rows[0]); assert all(len(r)==n for r in table_rows)
        widths = [154, 348] if n == 2 else ([125, 300, 77] if "활용 데이터" in table_rows[0][0].getPlainText() else [145, 265, 92])
        table = Table(table_rows, colWidths=widths, repeatRows=1)
        table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.HexColor("#e8eff3")),
                                   ("VALIGN", (0,0), (-1,-1), "TOP"),
                                   ("LINEBELOW", (0,0), (-1,0), .6, colors.HexColor("#879cab")),
                                   ("LINEBELOW", (0,1), (-1,-1), .25, colors.HexColor("#cbd5db")),
                                   ("LEFTPADDING", (0,0), (-1,-1), 7), ("RIGHTPADDING", (0,0), (-1,-1), 7),
                                   ("TOPPADDING", (0,0), (-1,-1), 6), ("BOTTOMPADDING", (0,0), (-1,-1), 6)]))
        story.extend([table, Spacer(1, 8)]); continue
    paragraph = [line]; i += 1
    while i < len(lines) and lines[i].strip() and not lines[i].strip().startswith(("#", "|", "![", "<!--")):
        paragraph.append(lines[i].strip()); i += 1
    story.append(Paragraph(inline(" ".join(paragraph)), styles["body"]))


def furniture(canvas, doc):
    canvas.setFont("Korean", 8)
    canvas.setFillColor(colors.HexColor("#65757f"))
    canvas.drawString(46, 816, "망젤이네  ·  서울 필수 이동의 시간 격차")
    canvas.drawRightString(549, 28, f"{doc.page}" if doc.page<=5 else "참고문헌")


pdf_path = OUT / "망젤이네_분석보고서.pdf"
doc = SimpleDocTemplate(str(pdf_path), pagesize=(595.28, 841.89), leftMargin=46, rightMargin=46,
                        topMargin=43, bottomMargin=43, title="서울 치료 재활 이동지원의 시간 부담과 요일별 운영 개선", author="망젤이네")
doc.build(story, onFirstPage=furniture, onLaterPages=furniture)
reader = PdfReader(pdf_path)
assert len(reader.pages) == 6, f"Expected five body pages and references; got {len(reader.pages)}"
assert sum(len(page.images) for page in reader.pages) >= 3
for number, heading in [(1, "분석 배경"), (2, "분석과정 및 방법"), (3, "분석 내용"), (4, "정책제안"), (5, "적용 대상"), (6, "참고문헌")]:
    assert heading in reader.pages[number-1].extract_text(), (number, heading)

# Pandoc gets explicit Word page breaks from the same content.
word_break = '```{=openxml}\n<w:p><w:r><w:br w:type="page"/></w:r></w:p>\n```'
(OUT / "contest_submission_for_word.md").write_text(source.replace("<!-- pagebreak -->", word_break))
(OUT / "contest_submission_checks.json").write_text(json.dumps({"body_pages":5,"references_pages":1,"embedded_images":sum(len(p.images) for p in reader.pages),"code_url_confirmed":True,"code_url":"https://github.com/kanginhan1018-gif/AI---","source":"docs/2026-10-18-contest-submission.md"},ensure_ascii=False,indent=2))
(OUT / "망젤이네_분석보고서_수정본.pdf").write_bytes(pdf_path.read_bytes())
print(f"Created {pdf_path}; five body pages, references, and three result images checked.")
