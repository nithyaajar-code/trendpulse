"""Step 2 of the workbook build (optional automation - the same pivot can be inserted by hand in Excel, see README).
Opens trendpulse_workbook_base.xlsx in LibreOffice Calc, inserts a real PivotTable (DataPilot) on a new 'Pivot' sheet,
recalculates every formula and saves trendpulse_workbook.xlsx.

Start LibreOffice first:  soffice --headless --accept="socket,host=localhost,port=2002;urp;" &
Then run with LibreOffice's bundled Python, from part4_sql_spreadsheet/:
    <libreoffice>/program/python tools/add_pivot_libreoffice.py
"""
import os
import time
import uno
from com.sun.star.beans import PropertyValue
from com.sun.star.table import CellAddress, CellRangeAddress
from com.sun.star.sheet.DataPilotFieldOrientation import ROW, COLUMN, DATA
from com.sun.star.sheet.GeneralFunction import AVERAGE

def prop(name, value):
    p = PropertyValue(); p.Name = name; p.Value = value; return p

here = os.path.abspath(".")
src = uno.systemPathToFileUrl(os.path.join(here, "trendpulse_workbook_base.xlsx"))
dst = uno.systemPathToFileUrl(os.path.join(here, "trendpulse_workbook.xlsx"))

local = uno.getComponentContext()
resolver = local.ServiceManager.createInstanceWithContext("com.sun.star.bridge.UnoUrlResolver", local)
for _ in range(30):
    try:
        ctx = resolver.resolve("uno:socket,host=localhost,port=2002;urp;StarOffice.ComponentContext")
        break
    except Exception:
        time.sleep(1)
desktop = ctx.ServiceManager.createInstanceWithContext("com.sun.star.frame.Desktop", ctx)
doc = desktop.loadComponentFromURL(src, "_blank", 0, (prop("Hidden", True),))
doc.calculateAll()

sheets = doc.Sheets
records = sheets.getByName("Records")
cursor = records.createCursor(); cursor.gotoEndOfUsedArea(False)
last_row = cursor.RangeAddress.EndRow          # 0-based
last_col = cursor.RangeAddress.EndColumn

sheets.insertNewByName("Pivot", 1)
pivot_sheet = sheets.getByName("Pivot")
pivot_sheet.getCellByPosition(0, 0).String = "Average views per trending record, by category (rows) and country (columns)"

tables = pivot_sheet.getDataPilotTables()
desc = tables.createDataPilotDescriptor()
rng = CellRangeAddress(); rng.Sheet = sheets.getElementNames().index("Records")
rng.StartColumn, rng.StartRow, rng.EndColumn, rng.EndRow = 0, 0, last_col, last_row
desc.setSourceRange(rng)
fields = desc.getDataPilotFields()
names = [fields.getByIndex(i).Name for i in range(fields.Count)]
f_cat = fields.getByIndex(names.index("category_name")); f_cat.Orientation = ROW
f_cty = fields.getByIndex(names.index("country")); f_cty.Orientation = COLUMN
f_v = fields.getByIndex(names.index("views")); f_v.Orientation = DATA; f_v.Function = AVERAGE
desc.ShowFilterButton = False
dest = CellAddress(); dest.Sheet = sheets.getElementNames().index("Pivot"); dest.Column, dest.Row = 0, 2
tables.insertNewByName("AvgViewsPivot", dest, desc)
doc.calculateAll()

doc.storeToURL(dst, (prop("FilterName", "Calc MS Excel 2007 XML"),))
doc.close(True)
print("saved", dst)

# LibreOffice re-anchors the AutoFilter sort condition to column A on export; point it back at the views column (I).
import re
import shutil
import zipfile

path = os.path.join(here, "trendpulse_workbook.xlsx")
tmp = path + ".tmp"
with zipfile.ZipFile(path) as zin, zipfile.ZipFile(tmp, "w", zipfile.ZIP_DEFLATED) as zout:
    for item in zin.infolist():
        data = zin.read(item.filename)
        if item.filename.startswith("xl/worksheets/sheet") and b"<sortState" in data:
            data = re.sub(rb'<sortCondition ref="A(\d+):A(\d+)"', rb'<sortCondition ref="I\1:I\2"', data)
        zout.writestr(item, data)
shutil.move(tmp, path)
os.remove(os.path.join(here, "trendpulse_workbook_base.xlsx"))
print("fixed sort condition; removed the intermediate base workbook")
