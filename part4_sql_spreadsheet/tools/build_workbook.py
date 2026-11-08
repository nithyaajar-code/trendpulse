"""Step 1 of the workbook build: write data, formulas, named ranges, filter/sort and conditional formatting
with openpyxl.  Run from part4_sql_spreadsheet/:  python tools/build_workbook.py
(Step 2, tools/add_pivot_libreoffice.py, adds the real PivotTable and recalculates; see README.)"""
import pandas as pd
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill, Alignment
from openpyxl.formatting.rule import Rule
from openpyxl.styles.differential import DifferentialStyle
from openpyxl.workbook.defined_name import DefinedName
from openpyxl.worksheet.table import Table  # noqa: F401  (not used: plain ranges keep VLOOKUP simple)

OUT = "trendpulse_workbook_base.xlsx"
cats = pd.read_csv("data/categories.csv")
vids = pd.read_csv("data/videos.csv")
recs = pd.read_csv("data/trending_records.csv")

records = recs.merge(vids[["video_id", "title", "channel_title", "category_id"]], on="video_id", how="left")
records = records.sort_values("views", ascending=False).reset_index(drop=True)     # sorted: most-viewed first
cols = ["record_id", "video_id", "country", "trending_date", "title", "channel_title", "category_id",
        "category_name", "views", "likes", "dislikes", "comment_count"]
N = len(records)
last = N + 1
HEADER = Font(bold=True, color="FFFFFF")
HFILL = PatternFill("solid", fgColor="2A78D6")

wb = Workbook()

# ---------------- Records sheet
ws = wb.active
ws.title = "Records"
ws.append(cols)
for i, r in enumerate(records.itertuples(index=False), start=2):
    ws.append([r.record_id, r.video_id, r.country, pd.Timestamp(r.trending_date).to_pydatetime(), r.title,
               r.channel_title, r.category_id, f"=VLOOKUP(G{i},cat_table,2,FALSE)",
               r.views, r.likes, r.dislikes, r.comment_count])
for c in ws[1]:
    c.font, c.fill = HEADER, HFILL
for row in ws.iter_rows(min_row=2, min_col=4, max_col=4):
    row[0].number_format = "yyyy-mm-dd"
for col in "IJKL":
    for row in ws[f"{col}2:{col}{last}"]:
        row[0].number_format = "#,##0"
widths = dict(A=10, B=14, C=8, D=12, E=46, F=24, G=11, H=22, I=14, J=12, K=11, L=14)
for k, v in widths.items():
    ws.column_dimensions[k].width = v
ws.freeze_panes = "A2"
ws.auto_filter.ref = f"A1:L{last}"
ws.auto_filter.add_sort_condition(f"I2:I{last}", descending=True)

# conditional formatting: top 10% of views
dxf = DifferentialStyle(fill=PatternFill("solid", bgColor="FFE699", fgColor="FFE699"), font=Font(bold=True, color="9C5700"))
rule = Rule(type="top10", rank=10, percent=True, dxf=dxf)
ws.conditional_formatting.add(f"I2:I{last}", rule)

# ---------------- Categories (lookup) sheet
wc = wb.create_sheet("Categories")
wc.append(["category_id", "category_name"])
for r in cats.itertuples(index=False):
    wc.append([r.category_id, r.category_name])
for c in wc[1]:
    c.font, c.fill = HEADER, HFILL
wc.column_dimensions["A"].width, wc.column_dimensions["B"].width = 12, 26
wc["D1"], wc["E1"] = "Try a lookup:", "category_id"
wc["E2"], wc["F1"] = 25, "category_name (VLOOKUP)"
wc["F2"] = "=VLOOKUP(E2,cat_table,2,FALSE)"
wc["D1"].font = Font(bold=True)
wc.column_dimensions["F"].width = 26

# ---------------- named ranges
cat_rows = len(cats) + 1
wb.defined_names["cat_table"] = DefinedName("cat_table", attr_text=f"Categories!$A$2:$B${cat_rows}")
wb.defined_names["views_col"] = DefinedName("views_col", attr_text=f"Records!$I$2:$I${last}")
wb.defined_names["country_col"] = DefinedName("country_col", attr_text=f"Records!$C$2:$C${last}")
wb.defined_names["category_col"] = DefinedName("category_col", attr_text=f"Records!$H$2:$H${last}")

# ---------------- Summary sheet (headline numbers)
s = wb.create_sheet("Summary", 0)
s["A1"] = "TrendPulse - headline numbers"
s["A1"].font = Font(bold=True, size=14)
s.append([])
s.append(["Metric", "Value", "Formula (as text)"])
for c in s[3]:
    c.font, c.fill = HEADER, HFILL
rows = [
    ("Records - US", '=COUNTIF(country_col,"US")'),
    ("Records - GB", '=COUNTIF(country_col,"GB")'),
    ("Records - IN", '=COUNTIF(country_col,"IN")'),
    ("Records - total", "=COUNTA(country_col)"),
    ("Total views (all records)", "=SUM(views_col)"),
    ("Overall average views", "=AVERAGE(views_col)"),
    ("Average views - US", '=AVERAGEIF(country_col,"US",views_col)'),
    ("Average views - Music", '=AVERAGEIF(category_col,"Music",views_col)'),
    ("Records in Music", '=COUNTIF(category_col,"Music")'),
    ("Top-10% views threshold (90th percentile)", "=PERCENTILE(views_col,0.9)"),
    ("Records highlighted as top 10%", '=COUNTIF(views_col,">="&B13)'),
]
for i, (label, f) in enumerate(rows, start=4):
    s.cell(row=i, column=1, value=label)
    s.cell(row=i, column=2, value=f).number_format = "#,##0.00" if "AVERAGE" in f or "PERCENTILE" in f else "#,##0"
    s.cell(row=i, column=3, value=f.lstrip("="))
s.column_dimensions["A"].width, s.column_dimensions["B"].width, s.column_dimensions["C"].width = 42, 20, 46
s["A17"] = "Pivot table: see sheet 'Pivot' (rows = category_name, columns = country, values = average of views)."
s["A18"] = "Named ranges: cat_table, views_col, country_col, category_col (Formulas > Name Manager)."

wb.save(OUT)
print("wrote", OUT, "rows:", N)
