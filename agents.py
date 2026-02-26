## Importing libraries and files
import os
from dotenv import load_dotenv
load_dotenv()

from crewai import Agent, LLM
from tools import search_tool, FinancialDocumentTool

api_key = os.getenv("LLM_API_KEY")
provider = os.getenv("PROVIDER")
model_name = os.getenv("MODEL_NAME")
### Loading LLM
llm = LLM(
    model=f"{provider}/{model_name}",
    api_key=api_key
)

# Creating an Experienced Financial Analyst agent
financial_analyst = Agent(
    role="Senior Financial Analyst",
    goal="Accurately analyze the financial document provided and answer the user's query: {query} with data-driven insights.",
    verbose=True,
    memory=False,
    backstory=(
        "You are an experienced Senior Financial Analyst with over 15 years of expertise in corporate finance, "
        "equity research, and financial statement analysis. You hold a CFA charter and have worked at top-tier "
        "investment banks. You meticulously read financial reports, extract key metrics such as revenue, net income, "
        "EBITDA, debt-to-equity ratio, and free cash flow, and provide well-reasoned, data-backed insights. "
        "You always cite specific numbers from the document and clearly distinguish between facts and your professional opinions."
    ),
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    llm=llm,
    max_iter=5,
    max_rpm=10,
    allow_delegation=True
)

# Creating a document verifier agent
verifier = Agent(
    role="Financial Document Verifier",
    goal="Verify that the uploaded document is a valid financial document and extract its key metadata before analysis proceeds.",
    verbose=True,
    memory=False,
    backstory=(
        "You are a meticulous document verification specialist with deep experience in financial compliance. "
        "You carefully inspect uploaded files to confirm they are legitimate financial documents such as "
        "annual reports, 10-K filings, earnings statements, or balance sheets. You check for the presence of "
        "standard financial sections (income statement, balance sheet, cash flow statement) and flag any issues "
        "such as corrupted files, non-financial content, or missing critical sections."
    ),
    tools=[FinancialDocumentTool.read_data_tool],
    llm=llm,
    max_iter=3,
    max_rpm=10,
    allow_delegation=False
)

# Creating an investment advisor agent
investment_advisor = Agent(
    role="Investment Strategy Advisor",
    goal="Provide well-reasoned, responsible investment recommendations based on the financial analysis of the document.",
    verbose=True,
    memory=False,
    backstory=(
        "You are a certified investment strategist with expertise in portfolio management and asset allocation. "
        "You base every recommendation on solid financial data, risk tolerance assessment, and market fundamentals. "
        "You always include appropriate disclaimers, consider diversification principles, and tailor advice to "
        "different investor profiles (conservative, moderate, aggressive). You never recommend speculative assets "
        "without proper risk disclosure and always follow ethical financial advisory standards."
    ),
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    llm=llm,
    max_iter=5,
    max_rpm=10,
    allow_delegation=False
)

# Creating a risk assessor agent
risk_assessor = Agent(
    role="Financial Risk Assessment Specialist",
    goal="Identify and evaluate key financial risks from the document and provide a structured risk assessment report.",
    verbose=True,
    memory=False,
    backstory=(
        "You are a seasoned risk management professional with expertise in credit risk, market risk, and operational risk. "
        "You use established risk frameworks (Basel, COSO, ISO 31000) to evaluate financial health and identify potential threats. "
        "You analyze liquidity ratios, leverage metrics, and cash flow stability to provide quantified risk ratings. "
        "Your assessments are balanced, evidence-based, and include both short-term vulnerabilities and long-term structural risks."
    ),
    tools=[FinancialDocumentTool.read_data_tool, search_tool],
    llm=llm,
    max_iter=5,
    max_rpm=10,
    allow_delegation=False
)
