import openai
import os
import logging
import time
from openai import OpenAI, RateLimitError
from models.database import Session, User, ChatSession, ChatMessage
from typing import Dict, List
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

class PersonalizedFinancialAssistant:
    def __init__(self, user_id: int):
        self.user_id = user_id
        self.user_profile = self._load_user_profile()
        self.conversation_history: List[Dict[str, str]] = []
        self.last_request_time = 0  # For rate limiting
        self.financial_keywords = [
            'scholarship', 'loan', 'debt', 'budget', 'save', 'spend', 'invest',
            'money', 'finance', 'expense', 'income', 'credit', 'textbook', 'meal',
            'financial', 'planning', 'savings', 'cost', 'afford', 'pay', 'fee',
            'grant', 'aid', 'repayment', 'interest', 'discount', 'emergency fund'
        ]
        self.student_resources = {
            'scholarships': "https://studentaid.gov/understand-aid/types/scholarships",
            'loan_guides': "https://www.nerdwallet.com/article/loans/student-loans/student-loan-basics",
            'budget_tools': "https://www.mint.com/student-budget-template"
        }

    def _load_user_profile(self) -> Dict:
        """Load user profile from the database."""
        db = Session()
        try:
            user = db.get(User, self.user_id)
            if not user:
                return {}
            profile = user.financial_profile
            return {
                "income": profile.get("income", 0),
                "expenses": profile.get("expenses", 0),
                "debt": profile.get("debt", 0),
                "goals": profile.get("goals", []),
                "student_status": profile.get("student_status", "Undergraduate"),
                "graduation_year": profile.get("graduation_year", datetime.now().year + 2)
            }
        except Exception as e:
            logger.error(f"Error loading user profile: {str(e)}")
            return {}
        finally:
            db.close()

    def _is_financial_query(self, query: str) -> bool:
        """Check if the query is related to finances."""
        return any(keyword in query.lower() for keyword in self.financial_keywords)

    def get_response(self, query: str) -> str:
        """Generate a response to the user's query."""
        try:
            query = query.strip().lower()
            
            # Redirect non-financial queries
            if not self._is_financial_query(query):
                return "👋 Hi! I specialize in student finances. Ask me about scholarships, loans, or budgeting!"
            
            # Direct responses for common queries
            direct_responses = {
                'scholarships': self._get_scholarship_info,
                'loan': self._get_loan_advice,
                'budget': self._get_budgeting_tips
            }
            
            for keyword, handler in direct_responses.items():
                if keyword in query:
                    return handler()

            # Use AI for complex queries
            return self._generate_ai_response(query)
            
        except Exception as e:
            logger.error(f"Error generating response: {str(e)}")
            return "🔧 Our financial tools are temporarily upgrading. Please try again later."

    def _generate_ai_response(self, query: str) -> str:
        """Generate an AI response with rate limiting and retries."""
        self.conversation_history.append({"role": "user", "content": query})
        
        try:
            # Rate limiting: Ensure at least 1.2 seconds between requests
            current_time = time.time()
            if current_time - self.last_request_time < 1.2:
                time.sleep(1.2 - (current_time - self.last_request_time))
            
            # Generate response using OpenAI API
            response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[{
                    "role": "system",
                    "content": self._format_prompt(query)
                }, {
                    "role": "user",
                    "content": query
                }],
                temperature=0.7,
                max_tokens=300,
                timeout=20
            )
            
            self.last_request_time = time.time()  # Update last request time
            answer = response.choices[0].message.content
            self._store_conversation(query, answer)
            return answer
            
        except RateLimitError:
            # Retry once after a short delay
            time.sleep(30)
            try:
                response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[{
                        "role": "system",
                        "content": self._format_prompt(query)
                    }, {
                        "role": "user",
                        "content": query
                    }],
                    temperature=0.7,
                    max_tokens=300,
                    timeout=20
                )
                self.last_request_time = time.time()
                answer = response.choices[0].message.content
                self._store_conversation(query, answer)
                return answer
            except Exception as e:
                logger.error(f"Retry failed: {str(e)}")
                return "⏳ Our advisors are still busy. Please try again in a few minutes."
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            return "🔧 Technical difficulty. Please try again later."

    def _format_prompt(self, query: str) -> str:
        """Format the prompt for the AI model."""
        profile = self.user_profile
        return f"""You are a financial advisor for students. Help this {profile['student_status']} student:
        - Income: ${profile['income']}/mo | Expenses: ${profile['expenses']}/mo
        - Debt: ${profile['debt']} | Goals: {', '.join(profile['goals'])}
        Focus on: meal budgeting, textbook costs, student loans
        Recent chat history: {self._format_history()}
        Query: {query}
        Provide 2-3 actionable steps with examples and numbers."""

    def _format_history(self) -> str:
        """Format the conversation history for context."""
        return "\n".join([f"{m['role']}: {m['content']}" for m in self.conversation_history[-3:]])

    def _store_conversation(self, query: str, answer: str):
        """Store the conversation in the database."""
        db = Session()
        try:
            session = db.query(ChatSession).filter_by(user_id=self.user_id).first()
            if not session:
                session = ChatSession(user_id=self.user_id)
                db.add(session)
                db.commit()
                db.refresh(session)
            
            db.add(ChatMessage(session_id=session.id, content=query, is_bot=0))
            db.add(ChatMessage(session_id=session.id, content=answer, is_bot=1))
            db.commit()
        except Exception as e:
            logger.error(f"Error saving conversation: {str(e)}")
            db.rollback()
        finally:
            db.close()

    def _get_scholarship_info(self) -> str:
        """Provide scholarship information."""
        return f"""🎓 Scholarship Opportunities:
        1. Federal Pell Grants: Up to $6,495/year ({self.student_resources['scholarships']})
        2. University awards: Check department office
        3. Local community scholarships: Easier to win!"""

    def _get_loan_advice(self) -> str:
        """Provide loan management advice."""
        return f"""📉 Loan Management:
        1. Prioritize federal loans
        2. Income-driven repayment plans
        3. Pay interest early ({self.student_resources['loan_guides']})"""

    def _get_budgeting_tips(self) -> str:
        """Provide budgeting tips."""
        savings = max(self.user_profile['income'] - self.user_profile['expenses'], 0)
        return f"""💰 Budgeting Tips:
        1. Track spending with apps
        2. Save ${savings}/mo minimum
        3. Student discounts ({self.student_resources['budget_tools']})"""

    def _get_fallback_response(self, query: str) -> str:
        """Provide a fallback response for API failures."""
        fallbacks = {
            'save': self._get_budgeting_tips(),
            'debt': self._get_loan_advice(),
            'scholarship': self._get_scholarship_info()
        }
        for kw, resp in fallbacks.items():
            if kw in query:
                return f"⚠️ System Upgrade - Cached Advice:\n{resp}"
        return "💡 Pro Tip: Save 20% by renting textbooks! Ask me specific questions."