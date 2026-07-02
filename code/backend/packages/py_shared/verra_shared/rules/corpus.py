"""Seeded corpus of Indian regulatory rules (income tax, SEBI, FEMA/RBI, IRDAI, GST).

Summaries are conservative plain-language paraphrases keyed to official citations.
Amounts and rates reflect AY 2025-26 (FY 2024-25) positions where year-versioned;
frequently-amended provisions say so explicitly. The corpus is the grounding set
for `search_rules` — it is NOT a substitute for the statutory text.
"""

from __future__ import annotations

from .models import AppliesTo, Regulator, RegulatoryRule

_AY = "2025-26"


def _r(  # noqa: PLR0913 — flat constructor keeps the corpus below readable
    rule_id: str,
    regulator: Regulator,
    section: str,
    title: str,
    summary: str,
    applies_to: AppliesTo,
    tags: list[str],
    source: str,
    assessment_year: str | None = None,
) -> RegulatoryRule:
    return RegulatoryRule(
        id=rule_id,
        regulator=regulator,
        section=section,
        title=title,
        summary=summary,
        applies_to=applies_to,
        tags=tags,
        assessment_year=assessment_year,
        source=source,
    )


_INCOME_TAX_RESIDENT: tuple[RegulatoryRule, ...] = (
    _r(
        "it-115bac",
        Regulator.income_tax,
        "115BAC",
        "New tax regime — default regime and concessional slab rates",
        "Section 115BAC makes the new regime the default from AY 2024-25, with "
        "concessional slab rates in exchange for forgoing most deductions and "
        "exemptions (e.g. 80C, HRA). Taxpayers may opt for the old regime, subject "
        "to timing restrictions for business income. Slab thresholds are revised by "
        "successive Finance Acts — verify current text for the relevant year.",
        AppliesTo.all,
        ["slabs", "new-regime", "regime-choice", "income-tax"],
        "Income-tax Act 1961, s.115BAC as amended by Finance (No. 2) Act 2024",
        _AY,
    ),
    _r(
        "it-slabs-old",
        Regulator.income_tax,
        "First Schedule (Finance Act rates)",
        "Old tax regime — slab rates with full deductions",
        "The old regime taxes individuals at 5%, 20% and 30% above a basic exemption "
        "of ₹2.5 lakh (₹3 lakh for senior citizens, ₹5 lakh for those 80+) for AY "
        "2025-26, while preserving deductions such as 80C, 80D and housing interest. "
        "Rates are set annually in the Finance Act's First Schedule — verify the "
        "schedule for the relevant year.",
        AppliesTo.all,
        ["slabs", "old-regime", "regime-choice", "income-tax"],
        "Finance (No. 2) Act 2024, First Schedule, Part I",
        _AY,
    ),
    _r(
        "it-87a",
        Regulator.income_tax,
        "87A",
        "Rebate for resident individuals with low total income",
        "Section 87A gives resident individuals a rebate that can reduce tax to nil: "
        "for AY 2025-26 up to ₹12,500 where total income does not exceed ₹5 lakh "
        "(old regime), and up to ₹25,000 where it does not exceed ₹7 lakh (new "
        "regime). The rebate is not available to non-residents. Limits are amended "
        "frequently by Finance Acts — verify current text.",
        AppliesTo.resident,
        ["rebate", "low-income", "income-tax"],
        "Income-tax Act 1961, s.87A as amended by Finance (No. 2) Act 2024",
        _AY,
    ),
    _r(
        "it-80c",
        Regulator.income_tax,
        "80C",
        "Deduction for specified investments and payments (₹1.5 lakh cap)",
        "Section 80C allows a deduction up to ₹1.5 lakh for specified items such as "
        "EPF/PPF contributions, life insurance premium, ELSS, principal repayment of "
        "housing loans and children's tuition fees. It is available only under the "
        "old regime. Some instruments (e.g. new PPF accounts) are restricted for "
        "non-residents — verify eligibility per instrument.",
        AppliesTo.all,
        ["deduction", "80c", "old-regime", "investments"],
        "Income-tax Act 1961, s.80C",
        _AY,
    ),
    _r(
        "it-80d",
        Regulator.income_tax,
        "80D",
        "Deduction for health insurance premium",
        "Section 80D allows a deduction for health insurance premium and preventive "
        "health check-ups: up to ₹25,000 for self and family (₹50,000 where the "
        "insured is a senior citizen) plus a similar amount for parents. Available "
        "only under the old regime. Verify the current sub-limits before relying on "
        "exact figures.",
        AppliesTo.all,
        ["deduction", "health-insurance", "insurance", "old-regime"],
        "Income-tax Act 1961, s.80D",
        _AY,
    ),
    _r(
        "it-80ccd1b",
        Regulator.income_tax,
        "80CCD(1B)",
        "Additional NPS deduction of ₹50,000",
        "Section 80CCD(1B) allows an additional deduction of up to ₹50,000 for "
        "contributions to the National Pension System, over and above the 80C/80CCD(1) "
        "limit. It is available only under the old regime for individual "
        "contributions; employer contributions are dealt with separately under "
        "80CCD(2).",
        AppliesTo.all,
        ["deduction", "nps", "retirement", "old-regime"],
        "Income-tax Act 1961, s.80CCD(1B)",
        _AY,
    ),
    _r(
        "it-24b",
        Regulator.income_tax,
        "24(b)",
        "Deduction for home loan interest",
        "Section 24(b) allows interest on borrowed capital for house property to be "
        "deducted from house property income — up to ₹2 lakh for a self-occupied "
        "property under the old regime (conditions on completion timelines apply). "
        "For let-out property the full interest is deductible, subject to the set-off "
        "cap on house property losses.",
        AppliesTo.all,
        ["deduction", "home-loan", "house-property", "old-regime"],
        "Income-tax Act 1961, s.24(b)",
        _AY,
    ),
    _r(
        "it-80tta",
        Regulator.income_tax,
        "80TTA",
        "Deduction for savings account interest (non-seniors)",
        "Section 80TTA allows individuals (other than senior citizens covered by "
        "80TTB) a deduction of up to ₹10,000 on interest from savings accounts with "
        "banks, co-operative societies or post offices. It does not cover fixed or "
        "recurring deposit interest and is available only under the old regime.",
        AppliesTo.all,
        ["deduction", "savings-interest", "old-regime"],
        "Income-tax Act 1961, s.80TTA",
        _AY,
    ),
    _r(
        "it-80ttb",
        Regulator.income_tax,
        "80TTB",
        "Deduction for deposit interest — resident senior citizens",
        "Section 80TTB allows resident senior citizens (60+) a deduction of up to "
        "₹50,000 on interest from deposits (savings, fixed and recurring) with banks, "
        "co-operative banks and post offices. Taxpayers claiming 80TTB cannot also "
        "claim 80TTA. Available only under the old regime.",
        AppliesTo.resident,
        ["deduction", "senior-citizen", "deposit-interest", "old-regime"],
        "Income-tax Act 1961, s.80TTB",
        _AY,
    ),
    _r(
        "it-16ia",
        Regulator.income_tax,
        "16(ia)",
        "Standard deduction from salary",
        "Section 16(ia) gives salaried taxpayers and pensioners a flat standard "
        "deduction: ₹50,000 under the old regime and ₹75,000 under the new regime "
        "for AY 2025-26 (raised by Finance (No. 2) Act 2024). No proof of expense is "
        "required. Verify the current amount, as it is revised by Finance Acts.",
        AppliesTo.all,
        ["deduction", "salary", "standard-deduction"],
        "Income-tax Act 1961, s.16(ia) as amended by Finance (No. 2) Act 2024",
        _AY,
    ),
    _r(
        "it-10-13a",
        Regulator.income_tax,
        "10(13A) r.w. Rule 2A",
        "House Rent Allowance (HRA) exemption",
        "Section 10(13A) read with Rule 2A exempts HRA to the extent of the least of: "
        "actual HRA received, rent paid minus 10% of salary, and 50% of salary in "
        "metro cities (40% elsewhere). Available only under the old regime and only "
        "where rent is actually paid.",
        AppliesTo.all,
        ["exemption", "hra", "salary", "old-regime"],
        "Income-tax Act 1961, s.10(13A) read with Income-tax Rules 1962, Rule 2A",
        _AY,
    ),
    _r(
        "it-80g",
        Regulator.income_tax,
        "80G",
        "Deduction for donations to approved funds and charities",
        "Section 80G allows a deduction of 50% or 100% of donations to approved "
        "institutions, with or without a qualifying-limit cap of 10% of adjusted "
        "gross total income depending on the donee. Cash donations above ₹2,000 do "
        "not qualify. Available only under the old regime; donee approval status "
        "should be verified.",
        AppliesTo.all,
        ["deduction", "donations", "old-regime"],
        "Income-tax Act 1961, s.80G",
        _AY,
    ),
    _r(
        "it-111a",
        Regulator.income_tax,
        "111A",
        "Short-term capital gains on listed equity — special rate",
        "Section 111A taxes short-term capital gains on listed equity shares and "
        "equity-oriented mutual funds (where STT is paid) at a special rate: 20% for "
        "transfers on or after 23 July 2024 (15% before that date), per Finance "
        "(No. 2) Act 2024. Holding period for 'short-term' here is 12 months or "
        "less. Verify current rates before computing.",
        AppliesTo.all,
        ["capital-gains", "stcg", "equity", "portfolio"],
        "Income-tax Act 1961, s.111A as amended by Finance (No. 2) Act 2024",
        _AY,
    ),
    _r(
        "it-112a",
        Regulator.income_tax,
        "112A",
        "Long-term capital gains on listed equity — 12.5% above ₹1.25 lakh",
        "Section 112A taxes long-term capital gains on listed equity shares and "
        "equity-oriented mutual funds (STT paid) at 12.5% on gains exceeding "
        "₹1.25 lakh per year, for transfers on or after 23 July 2024 (previously 10% "
        "over ₹1 lakh), without indexation. Gains within the ₹1.25 lakh exemption "
        "are tax-free, which enables planned gain harvesting. Verify current rates.",
        AppliesTo.all,
        ["capital-gains", "ltcg", "equity", "portfolio", "harvesting"],
        "Income-tax Act 1961, s.112A as amended by Finance (No. 2) Act 2024",
        _AY,
    ),
    _r(
        "it-54",
        Regulator.income_tax,
        "54",
        "Exemption on sale of residential house reinvested in another house",
        "Section 54 exempts long-term capital gains from the sale of a residential "
        "house to the extent reinvested in one residential house in India within "
        "1 year before or 2 years after transfer (3 years if constructing). The "
        "exemption is capped at ₹10 crore and unutilised amounts must be parked in "
        "the Capital Gains Account Scheme by the return due date.",
        AppliesTo.all,
        ["capital-gains", "exemption", "reinvestment", "house-property"],
        "Income-tax Act 1961, s.54",
        _AY,
    ),
    _r(
        "it-54ec",
        Regulator.income_tax,
        "54EC",
        "Exemption via specified bonds for land/building gains",
        "Section 54EC exempts long-term capital gains from land or buildings to the "
        "extent invested in specified bonds (e.g. REC, NHAI-class issuers notified "
        "from time to time) within 6 months of transfer, capped at ₹50 lakh per "
        "financial year. The bonds carry a 5-year lock-in; premature transfer "
        "revokes the exemption.",
        AppliesTo.all,
        ["capital-gains", "exemption", "bonds", "reinvestment"],
        "Income-tax Act 1961, s.54EC",
        _AY,
    ),
    _r(
        "it-54f",
        Regulator.income_tax,
        "54F",
        "Exemption on sale of any long-term asset reinvested in a house",
        "Section 54F exempts long-term capital gains from any capital asset other "
        "than a residential house, proportionately to the net consideration "
        "reinvested in one residential house in India within the prescribed window. "
        "Conditions include not owning more than one other house on the transfer "
        "date; the exemption is capped at ₹10 crore.",
        AppliesTo.all,
        ["capital-gains", "exemption", "reinvestment", "house-property"],
        "Income-tax Act 1961, s.54F",
        _AY,
    ),
    _r(
        "it-208-211",
        Regulator.income_tax,
        "208 & 211",
        "Advance tax — liability and instalment schedule",
        "Section 208 requires advance tax where the estimated tax liability for the "
        "year is ₹10,000 or more. Section 211 fixes the instalments for individuals: "
        "15% by 15 June, 45% by 15 September, 75% by 15 December and 100% by "
        "15 March. Resident senior citizens without business income are exempt "
        "under s.207(2).",
        AppliesTo.all,
        ["advance-tax", "instalments", "compliance", "deadlines"],
        "Income-tax Act 1961, ss.208 and 211",
        _AY,
    ),
    _r(
        "it-234b",
        Regulator.income_tax,
        "234B",
        "Interest for shortfall in advance tax",
        "Section 234B levies simple interest at 1% per month or part thereof where "
        "advance tax paid is less than 90% of the assessed tax, computed from 1 April "
        "of the assessment year until payment. It applies in addition to any 234C "
        "interest for instalment deferment.",
        AppliesTo.all,
        ["advance-tax", "interest", "234b", "compliance"],
        "Income-tax Act 1961, s.234B",
        _AY,
    ),
    _r(
        "it-234c",
        Regulator.income_tax,
        "234C",
        "Interest for deferment of advance tax instalments",
        "Section 234C levies interest at 1% per month for shortfalls against each "
        "advance tax instalment due under s.211, generally for three months per "
        "shortfall (one month for the March instalment). Relief applies to hard-to- "
        "estimate income such as capital gains and dividends if tax is paid in "
        "subsequent instalments.",
        AppliesTo.all,
        ["advance-tax", "interest", "234c", "compliance"],
        "Income-tax Act 1961, s.234C",
        _AY,
    ),
)

_INCOME_TAX_NRI: tuple[RegulatoryRule, ...] = (
    _r(
        "it-6-residential-status",
        Regulator.income_tax,
        "6(1)",
        "Residential status — 182-day and 60/120-day tests",
        "Section 6(1) treats an individual as resident if present in India 182 days "
        "or more in the year, or 60 days plus 365 days over the prior four years. "
        "For Indian citizens/PIOs visiting India with India-sourced income above "
        "₹15 lakh, the 60-day limb is relaxed to 120 days (with RNOR treatment in "
        "some cases); for crew and citizens leaving for employment it is 182 days. "
        "Day counts must be verified against travel records.",
        AppliesTo.all,
        ["nri", "residency", "residential-status", "day-count"],
        "Income-tax Act 1961, s.6(1) as amended by Finance Act 2020",
        _AY,
    ),
    _r(
        "it-6-1a-deemed-resident",
        Regulator.income_tax,
        "6(1A)",
        "Deemed residency for stateless high-income Indian citizens",
        "Section 6(1A) deems an Indian citizen with India-sourced income above "
        "₹15 lakh to be resident in India if not liable to tax in any other country "
        "by reason of domicile or residence. A deemed resident is treated as "
        "resident-but-not-ordinarily-resident (RNOR), so foreign income generally "
        "remains outside Indian tax. Interaction with DTAAs should be verified.",
        AppliesTo.nri,
        ["nri", "residency", "deemed-resident", "rnor"],
        "Income-tax Act 1961, s.6(1A) inserted by Finance Act 2020",
        _AY,
    ),
    _r(
        "it-195-tds-nri",
        Regulator.income_tax,
        "195",
        "TDS on payments to non-residents",
        "Section 195 requires any person paying a non-resident any sum chargeable to "
        "tax in India (interest, rent, capital gains proceeds, fees, etc.) to deduct "
        "tax at the rates in force before payment. Lower/nil deduction certificates "
        "under s.195(2)/(3) or 197 and DTAA rates (with a valid TRC) can reduce the "
        "deduction. Buyers of property from NRIs must also deduct under s.195.",
        AppliesTo.nri,
        ["nri", "tds", "withholding", "payments"],
        "Income-tax Act 1961, s.195",
        _AY,
    ),
    _r(
        "it-10-4-nre-interest",
        Regulator.income_tax,
        "10(4)(ii)",
        "NRE account interest — exempt while non-resident under FEMA",
        "Section 10(4)(ii) exempts interest on Non-Resident (External) — NRE — "
        "rupee accounts for individuals who are 'person resident outside India' "
        "under FEMA or permitted account holders. On return to India, the exemption "
        "ceases once FEMA residency changes, even if income-tax residency lags. "
        "Both principal and interest are freely repatriable under FEMA.",
        AppliesTo.nri,
        ["nri", "nre", "accounts", "interest", "exemption", "fema"],
        "Income-tax Act 1961, s.10(4)(ii)",
        _AY,
    ),
    _r(
        "it-nro-taxation",
        Regulator.income_tax,
        "56 r.w. 195 (NRO interest)",
        "NRO account interest — fully taxable with 30% TDS",
        "Interest on Non-Resident Ordinary (NRO) accounts is fully taxable in India "
        "as income from other sources, with TDS under s.195 at 30% (plus surcharge/ "
        "cess) unless reduced by an applicable DTAA with a tax residency "
        "certificate. Repatriation from NRO accounts is limited to USD 1 million per "
        "financial year under FEMA, with Form 15CA/15CB compliance.",
        AppliesTo.nri,
        ["nri", "nro", "accounts", "interest", "tds"],
        "Income-tax Act 1961, ss.56 and 195; FEMA remittance rules for NRO accounts",
        _AY,
    ),
    _r(
        "it-10-15-fcnr",
        Regulator.income_tax,
        "10(15)(iv)(fa)",
        "FCNR(B) deposit interest — exempt for non-residents and RNOR",
        "Interest on Foreign Currency Non-Resident (FCNR(B)) deposits is exempt "
        "under s.10(15)(iv)(fa) while the holder is non-resident or resident-but-"
        "not-ordinarily-resident. The deposits are foreign-currency denominated, so "
        "the holder bears no INR depreciation risk, and are fully repatriable under "
        "FEMA.",
        AppliesTo.nri,
        ["nri", "fcnr", "accounts", "interest", "exemption"],
        "Income-tax Act 1961, s.10(15)(iv)(fa)",
        _AY,
    ),
    _r(
        "it-90-91-dtaa",
        Regulator.income_tax,
        "90 & 91",
        "DTAA relief and unilateral foreign tax credit",
        "Section 90 gives treaty relief where India has a DTAA — the taxpayer may "
        "apply treaty or domestic law, whichever is more beneficial, subject to a "
        "tax residency certificate under s.90(4) and Form 10F. Section 91 gives "
        "unilateral credit for foreign tax paid in non-treaty countries. Foreign tax "
        "credit claims require Form 67 under Rule 128.",
        AppliesTo.all,
        ["nri", "dtaa", "foreign-tax-credit", "treaty", "trc"],
        "Income-tax Act 1961, ss.90 and 91; Income-tax Rules 1962, Rule 128",
        _AY,
    ),
    _r(
        "it-schedule-fa",
        Regulator.income_tax,
        "139(1) proviso r.w. ITR Schedule FA",
        "Schedule FA — foreign asset disclosure for ordinarily residents",
        "Residents who are ordinarily resident must disclose all foreign assets — "
        "bank accounts, equity/debt interests, immovable property, custodial "
        "accounts, and signing authority — in Schedule FA of the return, even if "
        "income is nil. Non-disclosure attracts penalties under the Black Money Act "
        "2015. NRIs and RNORs are not required to file Schedule FA.",
        AppliesTo.resident,
        ["foreign-assets", "disclosure", "schedule-fa", "compliance"],
        "Income-tax Act 1961, s.139; Black Money (Undisclosed Foreign Income and Assets) Act 2015",
        _AY,
    ),
    _r(
        "it-115c-115i",
        Regulator.income_tax,
        "115C–115I (Chapter XII-A)",
        "Special regime for NRI investment income from forex assets",
        "Chapter XII-A (ss.115C–115I) offers NRIs a special regime for investment "
        "income and long-term capital gains from specified foreign-exchange assets "
        "acquired in convertible foreign exchange: concessional flat rates, no "
        "return-filing in limited cases where TDS is complete, and continuation "
        "options after return to India. Rates were revised by Finance (No. 2) Act "
        "2024 — verify current text before applying.",
        AppliesTo.nri,
        ["nri", "investment-income", "forex-assets", "special-regime"],
        "Income-tax Act 1961, Chapter XII-A (ss.115C–115I)",
        _AY,
    ),
    _r(
        "it-206c1g-tcs-lrs",
        Regulator.income_tax,
        "206C(1G)",
        "TCS on foreign remittances under LRS",
        "Section 206C(1G) requires banks to collect tax at source on Liberalised "
        "Remittance Scheme remittances: broadly 20% above a ₹7 lakh annual threshold "
        "for general purposes, with lower rates for education (loan-funded) and "
        "medical remittances, and specific treatment for overseas tour packages. TCS "
        "is creditable against the remitter's tax liability. Rates and thresholds "
        "change frequently — verify current text.",
        AppliesTo.resident,
        ["lrs", "tcs", "remittance", "nri", "compliance"],
        "Income-tax Act 1961, s.206C(1G)",
        _AY,
    ),
)

_FEMA: tuple[RegulatoryRule, ...] = (
    _r(
        "fema-nri-accounts",
        Regulator.rbi_fema,
        "FEMA (Deposit) Regulations 2016",
        "NRE/NRO/FCNR account framework for NRIs",
        "Under FEMA and the RBI's Deposit Regulations, a person becoming resident "
        "outside India must re-designate resident accounts: NRO for India-sourced "
        "income (repatriation capped at USD 1 million/year), NRE for freely "
        "repatriable rupee funds, and FCNR(B) for foreign-currency term deposits. "
        "Holding an ordinary resident account after becoming an NRI is a FEMA "
        "contravention.",
        AppliesTo.nri,
        ["nri", "fema", "accounts", "nre", "nro", "fcnr", "repatriation"],
        "Foreign Exchange Management (Deposit) Regulations 2016, FEMA 5(R)",
    ),
    _r(
        "fema-lrs",
        Regulator.rbi_fema,
        "LRS (Master Direction on LRS)",
        "Liberalised Remittance Scheme — USD 250,000 per year",
        "The RBI's Liberalised Remittance Scheme permits resident individuals to "
        "remit up to USD 250,000 per financial year for permitted capital and "
        "current account purposes, including foreign investment, education and "
        "travel. Remittances beyond the limit need prior RBI approval, and TCS under "
        "s.206C(1G) applies at the bank. LRS is available only to residents.",
        AppliesTo.resident,
        ["lrs", "fema", "remittance", "foreign-investment"],
        "RBI Master Direction on Liberalised Remittance Scheme (FED Master "
        "Direction No. 7/2015-16, as updated)",
    ),
)

_SEBI: tuple[RegulatoryRule, ...] = (
    _r(
        "sebi-mf-riskometer",
        Regulator.sebi,
        "SEBI/HO/IMD/DF3/CIR/P/2020/197",
        "Mutual fund riskometer — product risk labelling",
        "SEBI's product-labelling circular requires every mutual fund scheme to "
        "display a riskometer with six risk levels from Low to Very High, evaluated "
        "monthly from the actual portfolio. Investors and advisers should match "
        "scheme risk levels to the investor's risk profile. Riskometer methodology "
        "is updated by subsequent circulars — verify current text.",
        AppliesTo.all,
        ["sebi", "mutual-fund", "riskometer", "portfolio", "risk"],
        "SEBI circular SEBI/HO/IMD/DF3/CIR/P/2020/197 (Product Labeling in Mutual "
        "Fund schemes — Risk-o-meter), 5 October 2020",
    ),
    _r(
        "sebi-mf-categorization",
        Regulator.sebi,
        "SEBI/HO/IMD/DF3/CIR/P/2017/114",
        "Mutual fund scheme categorization and rationalization",
        "SEBI's categorization circular groups mutual fund schemes into five groups "
        "(equity, debt, hybrid, solution-oriented, others) with defined categories "
        "and one scheme per category per fund house, so that scheme names reflect "
        "actual mandates. Portfolio reviews should use these categories when "
        "assessing diversification and overlap.",
        AppliesTo.all,
        ["sebi", "mutual-fund", "categorization", "portfolio", "allocation"],
        "SEBI circular SEBI/HO/IMD/DF3/CIR/P/2017/114 (Categorization and "
        "Rationalization of Mutual Fund Schemes), 6 October 2017",
    ),
    _r(
        "sebi-ia-suitability",
        Regulator.sebi,
        "IA Regulations 2013, reg. 17",
        "Investment advice must be suitable to the client",
        "Regulation 17 of the SEBI (Investment Advisers) Regulations 2013 requires "
        "all investment advice to be suitable: based on the client's risk profile "
        "and financial situation, with documented reasonable basis, and only after "
        "assessing that the product is appropriate for the client's experience and "
        "objectives. Unsuitable or un-profiled recommendations breach the "
        "regulations.",
        AppliesTo.all,
        ["sebi", "advisory", "suitability", "portfolio", "compliance"],
        "SEBI (Investment Advisers) Regulations 2013, regulation 17",
    ),
    _r(
        "sebi-ia-risk-profiling",
        Regulator.sebi,
        "IA Regulations 2013, reg. 16",
        "Mandatory client risk profiling before advice",
        "Regulation 16 of the SEBI (Investment Advisers) Regulations 2013 requires "
        "advisers to obtain and document each client's age, income, investment "
        "objectives, horizon, liabilities and risk appetite, and to communicate the "
        "resulting risk profile to the client before giving advice. Profiles must be "
        "kept current and advice must trace back to them.",
        AppliesTo.all,
        ["sebi", "advisory", "risk-profiling", "kyc", "compliance"],
        "SEBI (Investment Advisers) Regulations 2013, regulation 16",
    ),
    _r(
        "sebi-pms-minimum",
        Regulator.sebi,
        "PMS Regulations 2020, reg. 23",
        "Portfolio Management Services — ₹50 lakh minimum investment",
        "The SEBI (Portfolio Managers) Regulations 2020 set a minimum investment of "
        "₹50 lakh (funds and/or securities) per client for discretionary and "
        "non-discretionary PMS. Clients below this threshold should be directed to "
        "mutual funds or advisory arrangements instead. Verify current threshold, "
        "which SEBI revises from time to time.",
        AppliesTo.all,
        ["sebi", "pms", "portfolio", "minimum-investment"],
        "SEBI (Portfolio Managers) Regulations 2020, regulation 23",
    ),
)

_IRDAI: tuple[RegulatoryRule, ...] = (
    _r(
        "irdai-free-look",
        Regulator.irdai,
        "Protection of Policyholders' Interests Regulations 2024",
        "Free-look period to return a new insurance policy",
        "IRDAI's policyholder-protection framework gives a free-look period — 30 "
        "days from receipt of the policy document under the 2024 regulations — "
        "during which a life or health policyholder may return the policy and "
        "receive a refund net of proportionate risk premium and charges. Earlier "
        "rules provided 15 days for many channels — verify the period applicable to "
        "the policy.",
        AppliesTo.all,
        ["irdai", "insurance", "free-look", "policyholder-protection"],
        "IRDAI (Protection of Policyholders' Interests, Operations and Allied "
        "Matters of Insurers) Regulations 2024",
    ),
    _r(
        "irdai-life-min-cover",
        Regulator.irdai,
        "Non-Linked & Unit Linked Insurance Products Regulations 2019",
        "Minimum death benefit in life insurance products",
        "IRDAI's product regulations require life insurance products to carry a "
        "minimum death benefit — broadly at least 7 times annualized premium for "
        "regular-premium products (higher multiples also affect tax exemption under "
        "s.10(10D) of the Income-tax Act, which needs sum assured of at least 10x "
        "premium). Adequacy of life cover should additionally be assessed against "
        "income and liabilities, not just regulatory minimums.",
        AppliesTo.all,
        ["irdai", "insurance", "life-insurance", "cover-adequacy", "protection"],
        "IRDAI (Non-Linked Insurance Products) Regulations 2019 and (Unit Linked "
        "Insurance Products) Regulations 2019",
    ),
)

_GST: tuple[RegulatoryRule, ...] = (
    _r(
        "gst-registration-threshold",
        Regulator.gst,
        "CGST Act 2017, s.22",
        "GST registration turnover thresholds",
        "Section 22 of the CGST Act requires registration once aggregate turnover "
        "exceeds ₹40 lakh for suppliers of goods (₹20 lakh for services), with lower "
        "limits of ₹20/10 lakh in special category states. Certain persons (e.g. "
        "inter-state suppliers of goods, e-commerce operators) must register "
        "irrespective of turnover under s.24. Verify state-specific thresholds.",
        AppliesTo.all,
        ["gst", "registration", "threshold", "compliance"],
        "Central Goods and Services Tax Act 2017, ss.22 and 24",
    ),
    _r(
        "gst-gstr3b",
        Regulator.gst,
        "CGST Rules 2017, rule 61 (GSTR-3B)",
        "GSTR-3B — monthly summary return and tax payment",
        "GSTR-3B is the self-declared summary return through which registered "
        "persons report outward supplies, input tax credit and pay net GST — "
        "monthly by the 20th (staggered dates by state), or quarterly under the "
        "QRMP scheme for taxpayers up to ₹5 crore turnover. Late filing attracts "
        "late fees and 18% interest on unpaid tax.",
        AppliesTo.all,
        ["gst", "filing", "gstr-3b", "compliance", "deadlines"],
        "Central Goods and Services Tax Rules 2017, rule 61; CGST Act 2017, ss.39, 47 and 50",
    ),
)

RULES_CORPUS: tuple[RegulatoryRule, ...] = (
    *_INCOME_TAX_RESIDENT,
    *_INCOME_TAX_NRI,
    *_FEMA,
    *_SEBI,
    *_IRDAI,
    *_GST,
)

RULES_BY_ID: dict[str, RegulatoryRule] = {rule.id: rule for rule in RULES_CORPUS}
