---
name: msoffice-document-automation
description: >-
  Automating Microsoft Word (.docx) and Excel (.xlsx) via Python COM and FastMCP
  for architectural transmittals, BIM schedules, specification reports, and automated document generation.
author: "Asanka (Sri Lanka) - Curated by Dilu"
office: "Sri Lanka & Maldives"
discipline: "Documentation / Specifications / Schedules"
version: "1.0.0"
---

# Microsoft Office (Word & Excel) Automation via Python

Use this skill whenever generating, reading, editing, or converting Microsoft Word documents and Excel spreadsheets from Antigravity.

---

## 1. Microsoft Word COM Automation (`win32com.client`)

### A. Safe Application Connection Pattern
```python
import win32com.client

def get_word_app():
    """Connect to running Word instance or start a new background instance."""
    try:
        word = win32com.client.GetActiveObject("Word.Application")
    except Exception:
        word = win32com.client.Dispatch("Word.Application")
    word.Visible = False  # Set to True if user wants to see it
    return word
```

### B. Creating a Report / Transmittal Document
```python
def create_bim_report(file_path, title, headings_and_paragraphs):
    word = get_word_app()
    doc = word.Documents.Add()
    
    # Title
    p_title = doc.Paragraphs.Add()
    p_title.Range.Text = title
    p_title.Range.Font.Bold = True
    p_title.Range.Font.Size = 18
    p_title.Range.InsertParagraphAfter()
    
    # Body sections
    for heading, text in headings_and_paragraphs:
        p_head = doc.Paragraphs.Add()
        p_head.Range.Text = heading
        p_head.Range.Font.Bold = True
        p_head.Range.Font.Size = 13
        p_head.Range.InsertParagraphAfter()
        
        p_body = doc.Paragraphs.Add()
        p_body.Range.Text = text
        p_body.Range.Font.Bold = False
        p_body.Range.Font.Size = 11
        p_body.Range.InsertParagraphAfter()
        
    doc.SaveAs2(file_path)
    doc.Close()
```

### C. Converting Word Document to PDF
```python
def export_word_to_pdf(docx_path, pdf_path):
    word = get_word_app()
    doc = word.Documents.Open(docx_path)
    # 17 corresponds to wdExportFormatPDF
    doc.ExportAsFixedFormat(pdf_path, 17)
    doc.Close()
```

---

## 2. Microsoft Excel Automation (`win32com.client` & OpenPyXL)

### A. Extracting Table Data from Active Excel Workbook
```python
def read_active_excel_range(sheet_index=1):
    excel = win32com.client.GetActiveObject("Excel.Application")
    wb = excel.ActiveWorkbook
    ws = wb.Worksheets(sheet_index)
    
    used_range = ws.UsedRange
    data = used_range.Value  # Returns a tuple of tuples containing all cell data
    return data
```

### B. Writing BIM Schedule Quantities into Excel
```python
def populate_excel_schedule(excel_path, data_rows, headers):
    excel = win32com.client.Dispatch("Excel.Application")
    excel.Visible = False
    wb = excel.Workbooks.Add()
    ws = wb.Worksheets(1)
    
    # Write headers
    for col_idx, h in enumerate(headers, 1):
        cell = ws.Cells(1, col_idx)
        cell.Value = h
        cell.Font.Bold = True
        cell.Interior.Color = 0xD9D9D9  # Light Slate Gray
        
    # Write rows
    for row_idx, row in enumerate(data_rows, 2):
        for col_idx, val in enumerate(row, 1):
            ws.Cells(row_idx, col_idx).Value = val
            
    ws.Columns.AutoFit()
    wb.SaveAs(excel_path)
    wb.Close()
    excel.Quit()
```
