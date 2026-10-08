# LumenWealth Advisor Workstation Guide

> Fictional sample document created for the Agentic RAG demo. LumenWealth is not a real product.

## 1. Overview

The LumenWealth Advisor Workstation is the front office application used by relationship managers (RMs) and investment advisors. It brings together client profiles, portfolios, orders and compliance tasks in one screen.

## 2. Signing in

1. Open the Advisor Workstation from the company portal.
2. Enter your network username and password.
3. Approve the sign-in on your LumenKey token (see the Secure Access Token Guide).
4. Sessions time out after 20 minutes of inactivity. Unsaved order drafts are kept for 24 hours.

## 3. Client dashboard

The client dashboard shows:

- **Total assets under management (AUM)** across all of the client's portfolios, in the client's reporting currency.
- **Asset allocation** by asset class (equities, fixed income, cash, alternatives).
- **Performance** for 1 month, 3 months, year to date and since inception.
- **Alerts**, such as expiring KYC documents, cash balances above the client's limit, or portfolios outside their risk band.

To open a client, search by client name, client ID (format `CL-` followed by 6 digits) or portfolio number.

## 4. Placing an order

1. Open the client and select the portfolio.
2. Click **New Order** and choose the instrument by ISIN or name.
3. Enter the quantity or amount, order type (market or limit) and validity (day or good-till-cancelled).
4. The system runs a **suitability check** against the client's risk profile. If the check fails, the order cannot be submitted until the advisor records a justification and a supervisor approves it.
5. Click **Submit**. Orders above 250,000 in the portfolio currency require four-eyes approval from a second advisor.

Orders can be cancelled from **Order Blotter** until they are sent to the market.

## 5. Risk profiles

Every client has one of five risk profiles: Conservative, Moderately Conservative, Balanced, Growth and Aggressive. The risk profile is set during onboarding through the risk questionnaire and must be reviewed every 24 months, or sooner after a major life event.

## 6. Compliance tasks

The **Tasks** panel lists actions due for the advisor's clients:

- KYC document renewals (passport or ID expiring within 60 days)
- Risk profile reviews that are due
- Unsigned client agreements

Overdue tasks are escalated to the team lead after 10 business days.

## 7. Getting help

For access problems, contact the Service Desk at extension 4400. For questions about products or suitability rules, contact the Investment Office.
