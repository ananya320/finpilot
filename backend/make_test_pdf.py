import os
import pymupdf

lines = [
    "ABC BANK - ACCOUNT STATEMENT",
    "Account: XXXX1234 (fake)   Period: 01/10/2026 - 31/10/2026",
    "",
    "Opening balance: 10000.00",
    "",
    "Date        Description                  Debit      Credit",
    "02/10/2026  ACME SUPPLIES INV-1001       500.00",
    "05/10/2026  GLOBEX LTD INV-1002          1180.00",
    "07/10/2026  OFFICE COFFEE                12.50",
    "",
    "Closing balance: 8307.50",
]

doc = pymupdf.open()
page = doc.new_page()
y = 72
for line in lines:
    page.insert_text((50, y), line, fontsize=10, fontname="cour")
    y += 18

os.makedirs("../samples", exist_ok=True)
doc.save("../samples/test_statement.pdf")
print("Created ../samples/test_statement.pdf")