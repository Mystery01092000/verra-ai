"""Realistic sample document texts used across ingestion tests."""

from __future__ import annotations

FORM16_TEXT = """\
FORM NO. 16
[See rule 31(1)(a)]
PART A
Certificate under section 203 of the Income-tax Act, 1961 for tax deducted
at source on salary paid to an employee under section 192

Certificate No.: ABCDEFG    Last updated on: 30-May-2024

Name and address of the Employer
ACME TECHNOLOGIES PRIVATE LIMITED
12th Floor, Tower B, Cyber Park, Bengaluru - 560103

Name and designation of the Employee
RAHUL SHARMA
Senior Software Engineer

PAN of the Deductor: AAACA1234F
TAN of the Deductor: BLRA12345B
PAN of the Employee: ABCPS6789Q

Assessment Year: 2024-25
Period with the Employer From: 01/04/2023 To: 31/03/2024

Summary of amount paid/credited and tax deducted at source thereon
Quarter Q1 Receipt Numbers QWERTYU Amount of tax deducted (Rs.) 45,000.00
Quarter Q2 Receipt Numbers ASDFGHJ Amount of tax deducted (Rs.) 45,000.00
Quarter Q3 Receipt Numbers ZXCVBNM Amount of tax deducted (Rs.) 45,000.00
Quarter Q4 Receipt Numbers POIUYTR Amount of tax deducted (Rs.) 46,500.00
Total (Rs.) 1,81,500.00

PART B
Details of Salary Paid and any other income and tax deducted

1. Gross Salary: 24,50,000.00
2. Less: Allowances to the extent exempt under section 10
   (a) House rent allowance under section 10(13A): 1,80,000.00
   (b) Leave travel concession under section 10(5): 50,000.00
3. Total amount of salary received: 22,20,000.00
4. Less: Deductions under section 16
   (a) Standard deduction under section 16(ia): 50,000.00
   (b) Tax on employment under section 16(iii): 2,400.00
5. Income chargeable under the head "Salaries": 21,67,600.00
6. Deductions under Chapter VI-A
   (a) Deduction in respect of life insurance premia etc. under section 80C: 1,50,000.00
   (b) Deduction in respect of health insurance premia under section 80D: 25,000.00
   (c) Deduction under section 80CCD(1B): 50,000.00
   (d) Deduction in respect of donations under section 80G: 10,000.00
7. Total taxable income: 19,32,600.00
8. Net tax payable: 1,81,500.00
"""

FORM26AS_TEXT = """\
Form 26AS
Annual Tax Statement under Section 203AA of the Income-tax Act, 1961
Permanent Account Number (PAN): ABCPS6789Q
Assessment Year: 2024-25

PART A - Details of Tax Deducted at Source
Sr.No. Name of Deductor TAN of Deductor Section Total Amount Paid/Credited \
Total Tax Deducted Total TDS Deposited
1 ACME TECHNOLOGIES PRIVATE LIMITED BLRA12345B 192 24,50,000.00 1,81,500.00 1,81,500.00
2 HDFC BANK LIMITED MUMH03189E 194A 42,000.00 4,200.00 4,200.00

PART C - Details of Tax Paid (Other than TDS or TCS)
Sr.No. Major Head Minor Head Tax Surcharge Education Cess Total BSR Code \
Date of Deposit Challan Serial Number
1 0021 300 25,000.00 0.00 0.00 25,000.00 0510308 15/03/2024 04567
"""

AIS_TEXT = """\
Annual Information Statement (AIS)
Permanent Account Number (PAN): ABCPS6789Q
Assessment Year: 2024-25
Financial Year: 2023-24

PART B - TDS/TCS Information
Sr.No. Information Category Information Source Deductor TAN Amount Paid Tax Deducted
Salary (Section 192) ACME TECHNOLOGIES PRIVATE LIMITED BLRA12345B 24,50,000.00 1,81,500.00
Interest from deposit (Section 194A) HDFC BANK LIMITED MUMH03189E 42,000.00 4,200.00

SFT Information
SFT-005 Time deposit HDFC BANK LIMITED 5,00,000.00
"""

# Weak Form 16 signal (only "PART A" survives) with garbled everything else.
GARBLED_TEXT = """\
F0RM N0. l6 c3rtif1cate xxxx PART A
s@l@ry st@tem3nt grbld txt 1,2,3 ~~ ??? deduxted @t sourse
"""

# Strong Form 16 header but no extractable amounts -> money-field review gate.
FORM16_HEADER_ONLY_TEXT = """\
FORM NO. 16
PART A
Certificate under section 203 of the Income-tax Act, 1961 for tax deducted
at source on salary
PART B
"""

UNKNOWN_TEXT = """\
Grocery list for the week: apples, bananas, milk, bread, eggs.
Remember to call the plumber about the kitchen sink.
"""
