## Importing libraries and files
from crewai import Task

from agents import financial_analyst, verifier, investment_advisor, risk_assessor
from tools import search_tool, FinancialDocumentTool

## Task 1: Verify the uploaded document is a valid financial document
verification = Task(
    description="Read the document at path: {file_path} and verify whether it is a valid financial document.\n\
Check for the presence of standard financial sections such as income statements, balance sheets, \
cash flow statements, or earnings data. Identify the document type (e.g., 10-K, annual report, \
quarterly earnings) and extract key metadata such as the company name, reporting period, and currency.",

    expected_output="""A structured verification report containing:
- Document type (e.g., Annual Report, 10-K Filing, Earnings Statement)
- Company name and reporting period
- Key sections identified in the document
- Confirmation of whether the document is a valid financial report
- Any issues or missing sections flagged""",

    agent=verifier,
    tools=[FinancialDocumentTool.read_data_tool],
    async_execution=False,
)

## Task 2: Analyze the financial document based on user's query
analyze_financial_document = Task(
    description="Read the financial document at path: {file_path} and thoroughly analyze it to answer the user's query: {query}.\n\
Extract and interpret key financial metrics including revenue, net income, operating margins, \
EPS, debt levels, and cash flow. Compare year-over-year performance where applicable. \
Use the search tool to find relevant market context and industry benchmarks if needed.",

    expected_output="""A comprehensive financial analysis containing:
- Executive summary addressing the user's query
- Key financial metrics extracted from the document (with specific numbers)
- Year-over-year trends and performance analysis
- Industry context and relevant market comparisons
- Clear, data-backed conclusions
- Sources referenced for any external data""",

    agent=financial_analyst,
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    async_execution=False,
)

## Task 3: Provide investment analysis and recommendations
investment_analysis = Task(
    description="Based on the financial analysis of the document at {file_path} and the user's query: {query}, \
provide well-reasoned investment recommendations.\n\
Evaluate the company's financial health, growth prospects, and competitive positioning. \
Consider valuation metrics (P/E, P/B, EV/EBITDA) and compare with industry peers. \
Tailor recommendations for different investor profiles (conservative, moderate, aggressive).",

    expected_output="""A structured investment analysis containing:
- Investment thesis summary
- Key strengths and weaknesses of the company
- Valuation assessment with relevant metrics
- Investment recommendations for different risk profiles
- Entry/exit considerations and time horizon
- Important disclaimers and risk disclosures
Note: This is for informational purposes only and does not constitute financial advice.""",

    agent=investment_advisor,
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    async_execution=False,
)

## Task 4: Assess financial risks
risk_assessment = Task(
    description="Based on the financial document at {file_path} and the user's query: {query}, \
perform a thorough risk assessment.\n\
Analyze liquidity risk (current ratio, quick ratio), leverage risk (debt-to-equity, interest coverage), \
market risk exposure, and operational risks. Identify both short-term vulnerabilities and long-term structural risks. \
Provide a risk rating and actionable mitigation recommendations.",

    expected_output="""A comprehensive risk assessment report containing:
- Overall risk rating (Low / Moderate / High / Critical)
- Liquidity risk analysis with key ratios
- Leverage and solvency risk evaluation
- Market and competitive risks identified
- Operational and regulatory risks
- Risk mitigation recommendations
- Summary of key risk factors ranked by severity""",

    agent=risk_assessor,
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    async_execution=False,
)