import streamlit as st
import json
import os

st.set_page_config(page_title="SDR Talk Track Generator", page_icon=":telephone_receiver:", layout="wide")

PUBSEC_STORIES = [
    {
        "type": "Defense Contractor",
        "problem": "Fragmented data across 12 legacy ETL pipelines slowing program delivery",
        "solution": "Consolidated onto Snowflake with FedRAMP High on AWS GovCloud",
        "roi": "Cut data engineering cycle from weeks to days; reduced pipeline debugging from days to hours",
        "compliance": "FedRAMP High, DoD IL4/IL5",
    },
    {
        "type": "Federal Civilian Agency",
        "problem": "Siloed data across bureaus preventing cross-agency analytics and AI adoption",
        "solution": "Unified data platform with secure data sharing across agency boundaries — no data movement required",
        "roi": "Enabled agency-wide fraud detection models that were previously impossible; 60% faster reporting cycles",
        "compliance": "FedRAMP High, 400+ security controls",
    },
    {
        "type": "Intelligence Community Contractor",
        "problem": "Legacy on-prem data warehouse couldn't scale for ML workloads on classified programs",
        "solution": "Migrated to Snowflake on AWS GovCloud with IL5 authorization for controlled unclassified information",
        "roi": "10x faster query performance; analysts self-serve instead of waiting weeks for IT-built reports",
        "compliance": "DoD IL5, ITAR, CJIS",
    },
    {
        "type": "Defense Systems Integrator",
        "problem": "Multiple program offices each running their own data stack; no unified view of supply chain",
        "solution": "Single Snowflake platform with granular RBAC and live data sharing between program teams",
        "roi": "Reduced supply chain reporting from 3 weeks to same-day; $2M+ annual savings on duplicated infrastructure",
        "compliance": "FedRAMP High, DFARS",
    },
    {
        "type": "Federal Health Agency",
        "problem": "Needed real-time analytics for public health response but legacy systems couldn't handle data volume",
        "solution": "Snowflake's elastic compute scaled to handle 5x normal data volume during crisis response",
        "roi": "Response analytics went from 72-hour lag to near real-time; zero downtime during peak",
        "compliance": "FedRAMP High, HIPAA",
    },
    {
        "type": "Aerospace & Defense OEM",
        "problem": "Engineering and manufacturing data locked in separate systems; quality issues took weeks to trace",
        "solution": "Snowflake unified IoT sensor data, MES, and ERP into a single analytics layer",
        "roi": "Quality issue root-cause analysis reduced from 2 weeks to 2 hours; predictive maintenance saved $5M/year",
        "compliance": "FedRAMP Moderate, ITAR",
    },
]

SYSTEM_PROMPT = """You are an expert cold-call coach for a Snowflake Federal SDR (Sales Development Representative). You generate personalized cold call talk tracks based on a prospect's LinkedIn profile.

Your output MUST follow this exact 6-section framework, plus discovery questions and objection handling:

**1. PERSONA CLASSIFICATION**
Classify as high-level (executive) or low-level (practitioner). State: their title, what they own, what they likely care about, and their decision-making power.

**2. PERMISSION OPENER**
Write a natural, confident 10-second opening line customized to their title. It should acknowledge you're interrupting and ask for a moment. Keep it conversational, not robotic.

**3. PROBLEM + PROVOKE**
Connect their role and company to a specific data/AI problem. Reference something concrete — hiring patterns, tech stack clues, industry trends, or company news. Make them think "this person did their homework."

**4. CUSTOMER STORY + ROI**
Share a relevant Federal/PubSec customer win. Pick the story that best matches their industry and role. Include quantified outcomes. Keep it to 2-3 sentences.

Here are approved customer stories to draw from:
{stories}

**5. HYPOTHESIS OF NEED**
Make an educated guess about their specific pain point based on their role, company, and industry. Frame it as a question to validate. Start with "Am I off base in thinking..." or similar.

**6. CLOSE + NEXT STEPS**
A soft close proposing a short meeting. Be specific about timing and what they'll get out of it.

---

**DISCOVERY QUESTIONS** (3-5 questions)
Role-specific questions to deepen the conversation if they engage. Focus on: current data stack, pain points, upcoming initiatives, decision-making process, and timeline.

**OBJECTION HANDLING** (4 common objections with responses)
Include responses for these common Fed objections:
- "We already use [competitor]" (Databricks, AWS native, etc.)
- "Not a priority right now"
- "Send me an email"
- "We can't move to cloud / security concerns"
Tailor responses to their specific role and company context.

IMPORTANT RULES:
- Be conversational, not salesy
- Use their first name in the opener
- Keep the full talk track under 400 words (excluding discovery/objections)
- If the LinkedIn profile is sparse, note what's missing and still generate the best track you can
- For Federal/defense prospects, always mention FedRAMP High and relevant compliance (IL4/IL5, ITAR, etc.)
- If the prospect is technical, lead with technical value; if executive, lead with business outcomes"""


def build_prompt(linkedin_text: str, company_override: str, notes: str) -> str:
    stories_text = "\n".join(
        f"- {s['type']}: {s['problem']} → {s['solution']}. ROI: {s['roi']} ({s['compliance']})"
        for s in PUBSEC_STORIES
    )

    user_msg = f"""Generate a cold call talk track for this prospect.

LINKEDIN PROFILE:
{linkedin_text}
"""
    if company_override.strip():
        user_msg += f"\nCOMPANY (override): {company_override.strip()}\n"
    if notes.strip():
        user_msg += f"\nADDITIONAL CONTEXT / NOTES:\n{notes.strip()}\n"

    system = SYSTEM_PROMPT.format(stories=stories_text)
    return system, user_msg


def main():
    st.title(":telephone_receiver: SDR Talk Track Generator")
    st.caption("Paste a LinkedIn profile, get a cold call script based on the SDR Playbook framework.")

    with st.container(border=True):
        linkedin_text = st.text_area(
            "Paste LinkedIn profile text",
            height=200,
            placeholder="Copy the prospect's LinkedIn profile page and paste it here...\n\n(Name, title, company, about section, experience, skills — whatever you can grab)",
        )
        col1, col2 = st.columns(2)
        with col1:
            company_override = st.text_input(
                "Company name (optional override)",
                placeholder="e.g., RTX, Lockheed Martin, DISA",
            )
        with col2:
            notes = st.text_input(
                "Your notes (optional)",
                placeholder="e.g., Referred by John, hiring Snowflake engineers",
            )

        generate = st.button(":sparkles: Generate Talk Track", type="primary", use_container_width=True)

    if generate:
        if not linkedin_text.strip():
            st.warning("Paste a LinkedIn profile above to generate a talk track.")
            return

        system_prompt, user_message = build_prompt(linkedin_text, company_override, notes)

        with st.spinner("Building your talk track..."):
            prompt = f"""<|system|>{system_prompt}<|end|>
<|user|>{user_message}<|end|>
<|assistant|>"""
            session = st.connection(
                "snowflake",
                connection_name=os.getenv("SNOWFLAKE_DEFAULT_CONNECTION_NAME") or "default",
            ).session()
            result = session.sql(
                "SELECT SNOWFLAKE.CORTEX.COMPLETE(?, ?)",
                params=["llama3.1-70b", prompt],
            ).collect()[0][0]

        st.divider()

        sections = result.split("**")
        talk_track_md = result

        col_main, col_side = st.columns([3, 1])
        with col_main:
            st.markdown(talk_track_md)
        with col_side:
            st.markdown("##### :clipboard: Quick Copy")
            plain_text = result.replace("**", "").replace("---", "---")
            st.code(plain_text, language=None)


if __name__ == "__main__":
    main()
