class FinancialAdvisor:
    def get_response(self, message: str):
        financial_responses = {
            "budget": "📊 Start with 50/30/20 rule: Needs(50%), Wants(30%), Savings(20%)",
            "loan": "🏦 Federal loans: Lower rates, income-driven repayment options",
            "credit": "💳 Build credit: Secured cards, <30% utilization, on-time payments",
            "investment": "📈 Start with index funds (SPY, VOO), consider Roth IRA",
            "emergency": "⚠️ 3-6 months expenses in high-yield savings account",
            "sidehustle": "💡 Freelancing, tutoring ($400+/mo avg for students)"
        }
        return financial_responses.get(message.lower(), 
            "Ask about: budget, loans, credit, investments, emergency funds, or side hustles")