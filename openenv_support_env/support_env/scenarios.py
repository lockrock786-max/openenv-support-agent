from __future__ import annotations

from .models import TaskSpec, TicketScenario


TASKS = {
    "ticket_triage_easy": TaskSpec(
        task_id="ticket_triage_easy",
        name="Support ticket triage",
        difficulty="easy",
        description=(
            "Classify the ticket correctly and assign a sensible priority. "
            "Routing and response style are lightly checked."
        ),
        tickets=[
            TicketScenario(
                ticket_id="E1",
                subject="Invoice charged twice for March",
                body=(
                    "I noticed my card was charged twice for the same subscription invoice. "
                    "Please check the duplicate payment and refund the extra charge."
                ),
                customer_tier="pro",
                customer_sentiment="frustrated",
                gold_category="billing",
                gold_priority="high",
                gold_route="billing",
                gold_response_type="provide_solution",
                reference_reply=(
                    "Thanks for flagging the duplicate charge. I can help with a refund review "
                    "and billing reconciliation right away."
                ),
                critical_keywords=["refund", "duplicate", "charge"],
            ),
            TicketScenario(
                ticket_id="E2",
                subject="Cannot sign in after password reset",
                body=(
                    "I reset my password twice, but the login form still says the credentials are invalid. "
                    "Please help me regain access today."
                ),
                customer_tier="enterprise",
                customer_sentiment="angry",
                gold_category="account_access",
                gold_priority="urgent",
                gold_route="support",
                gold_response_type="ask_clarify",
                reference_reply=(
                    "I am sorry for the access issue. Please confirm whether you are using SSO or a local login, "
                    "and I will guide you through the quickest recovery path."
                ),
                critical_keywords=["login", "access", "reset"],
            ),
            TicketScenario(
                ticket_id="E3",
                subject="Suggestion: keyboard shortcut for exporting reports",
                body=(
                    "A shortcut to export CSV reports would save time for our operations team. "
                    "This is a feature suggestion rather than a bug."
                ),
                customer_tier="free",
                customer_sentiment="calm",
                gold_category="feature_request",
                gold_priority="low",
                gold_route="engineering",
                gold_response_type="acknowledge",
                reference_reply=(
                    "Thanks for the suggestion. I have logged the idea so the product team can review it "
                    "for future planning."
                ),
                critical_keywords=["suggestion", "feature", "export"],
            ),
            TicketScenario(
                ticket_id="E4",
                subject="Immediate concern: security alert about suspicious login",
                body=(
                    "A user on our team saw a login from an unexpected country. Please review the security event "
                    "and advise whether the account should be locked."
                ),
                customer_tier="enterprise",
                customer_sentiment="frustrated",
                gold_category="security",
                gold_priority="urgent",
                gold_route="security",
                gold_response_type="escalate",
                reference_reply=(
                    "This looks like a security-sensitive event. I am escalating it to the security team now "
                    "so they can review the login source and containment steps."
                ),
                allow_close=False,
                critical_keywords=["security", "suspicious", "login"],
            ),
        ],
    ),
    "ticket_triage_medium": TaskSpec(
        task_id="ticket_triage_medium",
        name="Support routing with response policy",
        difficulty="medium",
        description=(
            "Route each ticket to the right team, choose an action style, and avoid premature closure."
        ),
        tickets=[
            TicketScenario(
                ticket_id="M1",
                subject="Need a copy of last quarter's receipts",
                body=(
                    "Finance needs receipts for the last quarter for audit purposes. "
                    "Please resend them to the billing contact."
                ),
                customer_tier="enterprise",
                customer_sentiment="calm",
                gold_category="billing",
                gold_priority="normal",
                gold_route="billing",
                gold_response_type="provide_solution",
                reference_reply=(
                    "I can help with that. I will resend the receipt bundle and confirm the billing contact on file."
                ),
                allow_close=True,
                critical_keywords=["receipt", "billing", "resend"],
            ),
            TicketScenario(
                ticket_id="M2",
                subject="App crashes when uploading a 200MB file",
                body=(
                    "The upload starts and then the app closes unexpectedly. This happens every time with large files."
                ),
                customer_tier="pro",
                customer_sentiment="frustrated",
                gold_category="bug_report",
                gold_priority="high",
                gold_route="engineering",
                gold_response_type="escalate",
                reference_reply=(
                    "Thank you for the report. I am escalating the crash logs to engineering so they can reproduce the upload failure."
                ),
                allow_close=False,
                critical_keywords=["crash", "upload", "logs"],
            ),
            TicketScenario(
                ticket_id="M3",
                subject="Cancel at end of billing cycle",
                body=(
                    "We plan to leave next month, but we want the account to remain active until the current cycle ends."
                ),
                customer_tier="pro",
                customer_sentiment="calm",
                gold_category="cancellation",
                gold_priority="high",
                gold_route="retention",
                gold_response_type="offer_retention",
                reference_reply=(
                    "I understand. I can help schedule the cancellation for the end of the cycle and share options if you decide to stay."
                ),
                allow_close=False,
                critical_keywords=["cancel", "cycle", "stay"],
            ),
            TicketScenario(
                ticket_id="M4",
                subject="Can we whitelist the API webhook domain?",
                body=(
                    "Our integration is being blocked by a security filter. Please review whether the domain can be approved."
                ),
                customer_tier="enterprise",
                customer_sentiment="frustrated",
                gold_category="security",
                gold_priority="urgent",
                gold_route="security",
                gold_response_type="ask_clarify",
                reference_reply=(
                    "I can route this to security review. Please share the exact domain and the reason it needs webhook access."
                ),
                allow_close=False,
                critical_keywords=["whitelist", "domain", "webhook"],
            ),
        ],
    ),
    "ticket_triage_hard": TaskSpec(
        task_id="ticket_triage_hard",
        name="Customer support resolution drafting",
        difficulty="hard",
        description=(
            "Handle nuanced cases, draft context-aware replies, and make safe closure decisions."
        ),
        tickets=[
            TicketScenario(
                ticket_id="H1",
                subject="Refund denied after subscription downgrade",
                body=(
                    "The customer downgraded after the trial ended and is asking for a refund because the old plan was not used. "
                    "We should explain policy without sounding rude."
                ),
                customer_tier="pro",
                customer_sentiment="angry",
                gold_category="billing",
                gold_priority="high",
                gold_route="billing",
                gold_response_type="deny_request",
                reference_reply=(
                    "I understand the concern. Based on the billing policy, the charge is not refundable, but I can explain the timeline and help with plan options."
                ),
                allow_close=False,
                critical_keywords=["policy", "refund", "plan"],
            ),
            TicketScenario(
                ticket_id="H2",
                subject="Lost access after MFA reset and device change",
                body=(
                    "The user changed phones and lost their authenticator codes. They still need access to shared files for a customer launch today."
                ),
                customer_tier="enterprise",
                customer_sentiment="frustrated",
                gold_category="account_access",
                gold_priority="urgent",
                gold_route="support",
                gold_response_type="ask_clarify",
                reference_reply=(
                    "I can help restore access. Please confirm the account owner and whether backup codes are available so I can route the fastest recovery path."
                ),
                allow_close=False,
                critical_keywords=["mfa", "backup codes", "access"],
            ),
            TicketScenario(
                ticket_id="H3",
                subject="Repeated false-positive spam blocking our newsletters",
                body=(
                    "Our legitimate product updates keep landing in spam for some recipients. We need a safe remediation plan, not an immediate workaround."
                ),
                customer_tier="pro",
                customer_sentiment="calm",
                gold_category="bug_report",
                gold_priority="normal",
                gold_route="engineering",
                gold_response_type="escalate",
                reference_reply=(
                    "Thanks for the detailed report. I am escalating this deliverability issue so engineering can review the spam classification path."
                ),
                allow_close=False,
                critical_keywords=["spam", "deliverability", "engineering"],
            ),
            TicketScenario(
                ticket_id="H4",
                subject="Enterprise renewal negotiation and seat reduction",
                body=(
                    "The account wants to reduce seats at renewal but keep premium support. We need a retention-oriented reply that offers options."
                ),
                customer_tier="enterprise",
                customer_sentiment="calm",
                gold_category="cancellation",
                gold_priority="high",
                gold_route="retention",
                gold_response_type="offer_retention",
                reference_reply=(
                    "I can review renewal options and present a reduced-seat plan that keeps premium support available."
                ),
                allow_close=False,
                critical_keywords=["renewal", "support", "retention"],
            ),
        ],
    ),
}

