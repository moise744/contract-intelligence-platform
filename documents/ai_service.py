import os
import json
from langchain_openai import ChatOpenAI
from langchain_core.prompts import PromptTemplate


class AIService:
    """
    Enterprise AI Service wrapper for OpenAI/LangChain.
    Falls back to deterministic mock data when no API key is present,
    allowing the platform to be demonstrated without incurring API costs.
    """

    def __init__(self):
        self.api_key = os.environ.get('OPENAI_API_KEY')
        if self.api_key:
            self.llm = ChatOpenAI(
                temperature=0,
                model="gpt-3.5-turbo",
                openai_api_key=self.api_key
            )
        else:
            self.llm = None
            print("WARNING: No OPENAI_API_KEY provided. Using mock AI service.")

    # ------------------------------------------------------------------
    # Internal helper
    # ------------------------------------------------------------------
    def _invoke(self, prompt_template, variables):
        """Invoke the LLM with a PromptTemplate and return the raw string response."""
        prompt = PromptTemplate(
            input_variables=list(variables.keys()),
            template=prompt_template
        )
        chain = prompt | self.llm
        response = chain.invoke(variables)
        return response.content

    # ------------------------------------------------------------------
    # 1. EXECUTIVE SUMMARY
    # ------------------------------------------------------------------
    def generate_summary(self, text):
        """
        Generates an executive summary, key findings, and action items.
        Uses a MapReduce-style approach: truncates to fit context window.
        Returns a dict: { executive_summary, key_findings, action_items }
        """
        if not self.llm:
            return {
                "executive_summary": (
                    "This Service Level Agreement establishes a managed IT services "
                    "engagement between Acme Corp (Client) and TechPro Solutions (Provider) "
                    "for a term of 36 months commencing January 1, 2024. The agreement "
                    "covers 24/7 infrastructure support, cloud migration services, and "
                    "cybersecurity monitoring at a total contract value of $1,800,000 USD. "
                    "Key obligations include 99.9% uptime SLA, monthly performance reporting, "
                    "and a 90-day termination notice period. Early termination by the Client "
                    "incurs a penalty equal to 20% of the remaining contract value."
                ),
                "key_findings": [
                    "Contract value: $1,800,000 USD over 36 months.",
                    "Uptime SLA commitment: 99.9% (approximately 8.7 hours downtime/year).",
                    "Termination clause requires 90-day written notice from either party.",
                    "Liability cap set at 12 months of fees paid ($600,000).",
                    "Governing law: State of Delaware, USA.",
                    "Renewal: Automatic 12-month renewal unless 60 days notice given."
                ],
                "action_items": [
                    "Legal team to review early termination penalty clause (Section 8.3).",
                    "Finance to confirm monthly payment schedule aligns with budget cycle.",
                    "IT Director to validate 99.9% SLA against current infrastructure metrics.",
                    "Compliance to verify GDPR and SOC2 data handling requirements (Exhibit C).",
                    "Procurement to set calendar reminder for renewal opt-out (60 days prior)."
                ]
            }

        template = """You are a senior legal and financial analyst at a Fortune 500 company.
Analyze the following contract text and return a JSON object with exactly these three keys:
- "executive_summary": A 2-paragraph executive summary (plain text, no markdown).
- "key_findings": A JSON list of 5-8 concise strings identifying the most important facts (values, dates, parties, obligations).
- "action_items": A JSON list of 4-6 actionable strings for the legal/compliance team.

Return ONLY valid JSON, no other text.

Contract Text:
{text}

JSON Output:"""

        try:
            raw = self._invoke(template, {"text": text[:12000]})
            # Strip markdown code fences if present
            raw = raw.strip().strip("```json").strip("```").strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[AIService] Error in generate_summary: {e}")
            return {
                "executive_summary": "Summary generation encountered an error.",
                "key_findings": [],
                "action_items": []
            }

    # ------------------------------------------------------------------
    # 2. RISK DETECTION
    # ------------------------------------------------------------------
    def detect_risks(self, text):
        """
        Identifies legal and financial risks in the document.
        Returns a list of dicts: [{ risk_type, description, risk_level, clause_reference }]
        """
        if not self.llm:
            return [
                {
                    "risk_type": "Financial",
                    "description": "Early termination penalty of 20% of remaining contract value (~$360,000) creates significant financial exposure if business needs change.",
                    "risk_level": "High",
                    "clause_reference": "Section 8.3 — Early Termination"
                },
                {
                    "risk_type": "Compliance",
                    "description": "Data processing addendum references GDPR Article 28 but does not specify sub-processor restrictions, which may violate regulatory requirements.",
                    "risk_level": "High",
                    "clause_reference": "Exhibit C — Data Processing"
                },
                {
                    "risk_type": "Operational",
                    "description": "SLA credit mechanism (Section 5.2) caps service credits at 10% of monthly fees, which may be insufficient for mission-critical downtime.",
                    "risk_level": "Medium",
                    "clause_reference": "Section 5.2 — SLA Credits"
                },
                {
                    "risk_type": "Legal",
                    "description": "Unilateral amendment clause allows Provider to modify service terms with 30-day notice, giving Client limited recourse.",
                    "risk_level": "Medium",
                    "clause_reference": "Section 12.1 — Amendments"
                },
                {
                    "risk_type": "Financial",
                    "description": "Annual price escalation clause (CPI + 3%) not capped, creating unpredictable cost increases over the 36-month term.",
                    "risk_level": "Low",
                    "clause_reference": "Section 6.4 — Price Adjustments"
                }
            ]

        template = """You are a senior legal risk analyst. Analyze this contract for legal, financial, operational, and compliance risks.
Return a JSON list of risk objects. Each object must have:
- "risk_type": string (Financial | Compliance | Operational | Legal | Reputational)
- "description": string (one clear sentence explaining the risk)
- "risk_level": string (High | Medium | Low)
- "clause_reference": string (relevant section/exhibit reference, or empty string)

Return ONLY a valid JSON array, no other text.

Contract Text:
{text}

JSON Array Output:"""

        try:
            raw = self._invoke(template, {"text": text[:12000]})
            raw = raw.strip().strip("```json").strip("```").strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[AIService] Error in detect_risks: {e}")
            return []

    # ------------------------------------------------------------------
    # 3. CLAUSE EXTRACTION
    # ------------------------------------------------------------------
    def extract_clauses(self, text):
        """
        Extracts key contractual clauses.
        Returns a list of dicts: [{ clause_type, text, is_standard }]
        """
        if not self.llm:
            return [
                {
                    "clause_type": "Termination",
                    "text": "Either party may terminate this Agreement upon 90 days written notice. Early termination by Client shall incur a penalty equal to 20% of the remaining contract value.",
                    "is_standard": False
                },
                {
                    "clause_type": "Confidentiality",
                    "text": "Each party agrees to maintain in confidence all Confidential Information of the other party for a period of 5 years following termination.",
                    "is_standard": True
                },
                {
                    "clause_type": "Limitation of Liability",
                    "text": "In no event shall either party's total liability exceed the total fees paid in the 12 months preceding the claim giving rise to liability.",
                    "is_standard": False
                },
                {
                    "clause_type": "Payment Terms",
                    "text": "Client shall pay all invoices within 30 days of receipt. Late payments accrue interest at 1.5% per month.",
                    "is_standard": True
                },
                {
                    "clause_type": "Intellectual Property",
                    "text": "All custom deliverables created under this Agreement shall be considered work-for-hire and owned exclusively by Client upon full payment.",
                    "is_standard": True
                },
                {
                    "clause_type": "Force Majeure",
                    "text": "Neither party shall be liable for delays caused by circumstances beyond their reasonable control, provided written notice is given within 5 business days.",
                    "is_standard": True
                }
            ]

        template = """You are a senior contract lawyer. Extract the most important clauses from the following contract text.
Return a JSON list of clause objects. Each object must have:
- "clause_type": string (e.g. Termination, Payment, Confidentiality, Liability, IP, Force Majeure, Governing Law)
- "text": string (the verbatim or paraphrased clause text, max 3 sentences)
- "is_standard": boolean (true = standard boilerplate, false = custom/negotiated/unusual)

Return ONLY a valid JSON array, no other text.

Contract Text:
{text}

JSON Array Output:"""

        try:
            raw = self._invoke(template, {"text": text[:12000]})
            raw = raw.strip().strip("```json").strip("```").strip()
            return json.loads(raw)
        except Exception as e:
            print(f"[AIService] Error in extract_clauses: {e}")
            return []

    # ------------------------------------------------------------------
    # 4. QUESTION & ANSWER
    # ------------------------------------------------------------------
    def answer_question(self, context_text, question):
        """
        Answers a specific question about the document using the extracted text as context.
        Returns a plain-text string answer.
        """
        if not self.llm:
            mock_answers = {
                "termination": "The contract requires 90 days written notice for termination. Early termination by the Client incurs a penalty equal to 20% of the remaining contract value.",
                "value": "The total contract value is $1,800,000 USD over a 36-month term, payable in monthly installments of $50,000.",
                "sla": "The Provider commits to 99.9% uptime. Service credits of up to 10% of the monthly fee apply if this SLA is breached.",
                "governing": "This Agreement is governed by the laws of the State of Delaware, USA.",
                "renewal": "The contract auto-renews for 12-month periods unless either party provides 60 days written notice of non-renewal.",
                "liability": "Each party's total liability is capped at 12 months of fees paid, approximately $600,000.",
            }
            question_lower = question.lower()
            for keyword, answer in mock_answers.items():
                if keyword in question_lower:
                    return answer
            return (
                f"Based on the contract analysis: The document is a 36-month managed IT services "
                f"agreement valued at $1,800,000. Your question '{question}' relates to a specific "
                f"provision that would require the full OpenAI API key to answer precisely. "
                f"Key provisions include termination (Section 8), SLA (Section 5), payment (Section 6), "
                f"and liability (Section 9)."
            )

        template = """You are a senior legal analyst. Using ONLY the contract text provided below as context,
answer the following question accurately and concisely in 2-4 sentences.
If the answer is not found in the text, say "This information is not explicitly stated in the document."

Contract Context:
{context}

Question: {question}

Answer:"""

        try:
            return self._invoke(template, {"context": context_text[:8000], "question": question})
        except Exception as e:
            print(f"[AIService] Error in answer_question: {e}")
            return "I was unable to process your question at this time. Please try again."
