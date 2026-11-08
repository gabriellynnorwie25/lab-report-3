
import json
import operator
import streamlit as st
import pandas as pd
from datetime import datetime

# ==========================================
# PAGE CONFIGURATION
# ==========================================

st.set_page_config(
    page_title="Scholarship Advisory System",
    page_icon="🎓",
    layout="centered"
)

# ==========================================
# INITIALISE SESSION STATE
# ==========================================

if "evaluation_history" not in st.session_state:
    st.session_state.evaluation_history = []

if "latest_result" not in st.session_state:
    st.session_state.latest_result = None

# ==========================================
# EXACT FIVE RULES FROM LAB SHEET
# ==========================================

DEFAULT_RULES = """[
    {
        "name": "Top merit candidate",
        "priority": 100,
        "conditions": [
            ["cgpa", ">=", 3.7],
            ["co_curricular_score", ">=", 80],
            ["family_income", "<=", 8000],
            ["disciplinary_actions", "==", 0]
        ],
        "action": {
            "decision": "AWARD_FULL",
            "reason": "Excellent academic & co-curricular performance, with acceptable need"
        }
    },
    {
        "name": "Good candidate - partial scholarship",
        "priority": 80,
        "conditions": [
            ["cgpa", ">=", 3.3],
            ["co_curricular_score", ">=", 60],
            ["family_income", "<=", 12000],
            ["disciplinary_actions", "<=", 1]
        ],
        "action": {
            "decision": "AWARD_PARTIAL",
            "reason": "Good academic & involvement record with moderate need"
        }
    },
    {
        "name": "Need-based review",
        "priority": 70,
        "conditions": [
            ["cgpa", ">=", 2.5],
            ["family_income", "<=", 4000]
        ],
        "action": {
            "decision": "REVIEW",
            "reason": "High need but borderline academic score"
        }
    },
    {
        "name": "Low CGPA – not eligible",
        "priority": 95,
        "conditions": [
            ["cgpa", "<", 2.5]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "CGPA below minimum scholarship requirement"
        }
    },
    {
        "name": "Serious disciplinary record",
        "priority": 90,
        "conditions": [
            ["disciplinary_actions", ">=", 2]
        ],
        "action": {
            "decision": "REJECT",
            "reason": "Too many disciplinary records"
        }
    }
]"""

# ==========================================
# OPERATORS
# ==========================================

OPERATORS = {
    "==": operator.eq,
    "!=": operator.ne,
    ">": operator.gt,
    ">=": operator.ge,
    "<": operator.lt,
    "<=": operator.le
}

VALID_FIELDS = {
    "cgpa",
    "family_income",
    "co_curricular_score",
    "community_service_hours",
    "semester",
    "disciplinary_actions"
}

VALID_DECISIONS = {
    "AWARD_FULL",
    "AWARD_PARTIAL",
    "REVIEW",
    "REJECT"
}

# ==========================================
# RULE VALIDATION
# ==========================================

def validate_rules(rules):

    if not isinstance(rules, list) or not rules:
        raise ValueError("Rules must be a non-empty JSON list.")

    # Ensure exactly five rules are used
    if len(rules) != 5:
        raise ValueError("Exactly five scholarship rules are required.")

    required_rule_keys = {
        "name",
        "priority",
        "conditions",
        "action"
    }

    for index, rule in enumerate(rules, start=1):

        if not isinstance(rule, dict):
            raise ValueError(f"Rule {index} must be a dictionary.")

        if not required_rule_keys.issubset(rule):
            raise ValueError(
                f"Rule {index} must contain name, priority, conditions and action."
            )

        if not isinstance(rule["name"], str) or not rule["name"].strip():
            raise ValueError(f"Rule {index} must have a valid name.")

        if (
            not isinstance(rule["priority"], (int, float))
            or isinstance(rule["priority"], bool)
        ):
            raise ValueError(f"Rule {index} must have a numeric priority.")

        if not isinstance(rule["conditions"], list) or not rule["conditions"]:
            raise ValueError(f"Rule {index} must have at least one condition.")

        if not isinstance(rule["action"], dict):
            raise ValueError(f"Rule {index} action must be a dictionary.")

        if not {"decision", "reason"}.issubset(rule["action"]):
            raise ValueError(
                f"Rule {index} action must contain decision and reason."
            )

        if rule["action"]["decision"] not in VALID_DECISIONS:
            raise ValueError(f"Rule {index} has an invalid decision.")

        if not isinstance(rule["action"]["reason"], str):
            raise ValueError(f"Rule {index} reason must be text.")

        for condition in rule["conditions"]:

            if not isinstance(condition, list) or len(condition) != 3:
                raise ValueError(
                    f"Each condition in rule {index} must have 3 elements."
                )

            field, symbol, threshold = condition

            if field not in VALID_FIELDS:
                raise ValueError(
                    f"Unknown applicant field in rule {index}: {field}"
                )

            if symbol not in OPERATORS:
                raise ValueError(
                    f"Unsupported operator in rule {index}: {symbol}"
                )

            if (
                not isinstance(threshold, (int, float))
                or isinstance(threshold, bool)
            ):
                raise ValueError(
                    f"Threshold in rule {index} must be numeric."
                )

    return True


# ==========================================
# INFERENCE ENGINE
# ==========================================

def evaluate_case(applicant, rules):

    validate_rules(rules)

    matching_rules = []
    rule_details = []

    # Check every rule
    for rule in rules:

        matches = True
        condition_details = []

        # Check every condition within the rule
        for field, symbol, threshold in rule["conditions"]:

            actual_value = applicant[field]

            condition_result = OPERATORS[symbol](
                actual_value,
                threshold
            )

            condition_details.append({
                "Field": field,
                "Operator": symbol,
                "Required Value": threshold,
                "Applicant Value": actual_value,
                "Result": "Passed" if condition_result else "Failed"
            })

            if not condition_result:
                matches = False

        # Store rule evaluation details
        rule_details.append({
            "Rule Name": rule["name"],
            "Priority": rule["priority"],
            "Status": "Matched" if matches else "Not Matched",
            "Conditions": condition_details
        })

        if matches:
            matching_rules.append(rule)

    # No matching rule
    if not matching_rules:

        return {
            "decision": "NO_MATCH",
            "reason": "No scholarship rule matched. Refer the application for manual assessment.",
            "rule_name": "No matching rule",
            "priority": None,
            "matching_rules": [],
            "rule_details": rule_details
        }

    # Select the rule with the highest priority
    selected = max(
        matching_rules,
        key=lambda item: item["priority"]
    )

    return {
        "decision": selected["action"]["decision"],
        "reason": selected["action"]["reason"],
        "rule_name": selected["name"],
        "priority": selected["priority"],
        "matching_rules": [
            rule["name"] for rule in matching_rules
        ],
        "rule_details": rule_details
    }


# ==========================================
# APPLICATION HEADER
# ==========================================

st.title("🎓 Scholarship Advisory System")

st.write(
    "A transparent rule-based decision support system. "
    "Enter an applicant's information and the system will "
    "evaluate scholarship eligibility using IF-THEN rules."
)

st.divider()

# ==========================================
# 1. APPLICANT INFORMATION
# ==========================================

st.header("1. Applicant Information")

with st.expander("Enter Applicant Details", expanded=True):

    cgpa = st.number_input(
        "Cumulative GPA (CGPA)",
        min_value=0.0,
        max_value=4.0,
        value=3.50,
        step=0.01,
        format="%.2f"
    )

    family_income = st.number_input(
        "Monthly Family Income (RM)",
        min_value=0,
        max_value=100000,
        value=5000,
        step=100
    )

    co_curricular_score = st.number_input(
        "Co-curricular Involvement Score (0-100)",
        min_value=0,
        max_value=100,
        value=70,
        step=1
    )

    community_service_hours = st.number_input(
        "Community Service Hours",
        min_value=0,
        max_value=10000,
        value=20,
        step=1
    )

    semester = st.number_input(
        "Current Semester of Study",
        min_value=1,
        max_value=20,
        value=3,
        step=1
    )

    disciplinary_actions = st.number_input(
        "Number of Disciplinary Actions",
        min_value=0,
        max_value=50,
        value=0,
        step=1
    )

# Store applicant information

applicant = {
    "cgpa": cgpa,
    "family_income": family_income,
    "co_curricular_score": co_curricular_score,
    "community_service_hours": community_service_hours,
    "semester": semester,
    "disciplinary_actions": disciplinary_actions
}

# ==========================================
# 2. RULE CONFIGURATION
# ==========================================

st.divider()

st.header("2. Rule Configuration")

st.caption(
    "The JSON editor contains exactly five rules from the lab sheet. "
    "You can modify their conditions, priorities and actions."
)

rules_text = st.text_area(
    "JSON Rules",
    value=DEFAULT_RULES,
    height=430
)

# ==========================================
# 3. SCHOLARSHIP EVALUATION
# ==========================================

st.divider()

st.header("3. Scholarship Evaluation")

if st.button(
    "Evaluate Scholarship Eligibility",
    type="primary",
    use_container_width=True
):

    try:

        # Convert JSON text into Python objects
        configured_rules = json.loads(rules_text)

        # Validate rule configuration
        validate_rules(configured_rules)

        # Run inference engine
        result = evaluate_case(applicant, configured_rules)

        # Save applicant evaluation
        history_record = {
            "Date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "CGPA": cgpa,
            "Family Income (RM)": family_income,
            "Co-curricular Score": co_curricular_score,
            "Community Service Hours": community_service_hours,
            "Semester": semester,
            "Disciplinary Actions": disciplinary_actions,
            "Decision": result["decision"],
            "Matched Rule": result["rule_name"],
            "Priority": result["priority"]
        }

        st.session_state.evaluation_history.append(history_record)

        # Save latest result
        st.session_state.latest_result = result

    except json.JSONDecodeError as error:

        st.session_state.latest_result = None

        st.error(f"Invalid JSON configuration: {error}")

    except (ValueError, TypeError, KeyError) as error:

        st.session_state.latest_result = None

        st.error(f"Rule configuration error: {error}")


# ==========================================
# DISPLAY DECISION RESULT
# ==========================================

if st.session_state.latest_result is not None:

    result = st.session_state.latest_result

    st.subheader("Decision Result")

    decision = result["decision"]

    # Colour-coded decision output
    if decision == "AWARD_FULL":

        st.success("🎉 FULL SCHOLARSHIP AWARDED")

    elif decision == "AWARD_PARTIAL":

        st.success("PARTIAL SCHOLARSHIP AWARDED")

    elif decision == "REVIEW":

        st.warning("APPLICATION REQUIRES FURTHER REVIEW")

    elif decision == "REJECT":

        st.error("APPLICATION REJECTED")

    else:

        st.info("NO MATCHING RULE FOUND")

    st.metric(
        label="Scholarship Decision",
        value=decision
    )

    st.write("**Matched Rule:**", result["rule_name"])

    st.write("**Reason:**", result["reason"])

    if result["priority"] is not None:

        st.write("**Rule Priority:**", result["priority"])

    # Display all matching rules
    with st.expander("View All Matching Rules"):

        if result["matching_rules"]:

            for rule_name in result["matching_rules"]:
                st.write(f"✓ {rule_name}")

        else:

            st.write("No rules matched.")

    # Display detailed rule evaluation
    with st.expander("View Detailed Rule Evaluation"):

        for rule in result["rule_details"]:

            st.markdown(f"### {rule['Rule Name']}")

            st.write(
                f"Priority: {rule['Priority']}"
            )

            if rule["Status"] == "Matched":

                st.success("All conditions satisfied - Rule Matched")

            else:

                st.warning("One or more conditions failed - Rule Not Matched")

            details_df = pd.DataFrame(rule["Conditions"])

            st.dataframe(
                details_df,
                use_container_width=True,
                hide_index=True
            )

    st.info(
        "This prototype provides an advisory result only. "
        "The scholarship committee should verify applications "
        "and make the final decision."
    )


# ==========================================
# HOW THE SYSTEM WORKS
# ==========================================

st.divider()

with st.expander("How the System Works"):

    st.markdown("""
    **Step 1: Applicant Information**

    The system collects applicant details such as CGPA, family income,
    co-curricular score, community service hours, semester and
    disciplinary records.

    **Step 2: Knowledge Representation**

    Scholarship eligibility criteria are represented using
    IF-THEN rules stored in JSON format.

    **Step 3: Rule Validation**

    The system checks whether exactly five rules are provided
    and whether their structure, fields, operators and actions
    are valid.

    **Step 4: Inference Engine**

    The inference engine compares applicant information against
    every condition in the five rules.

    **Step 5: Priority-Based Conflict Resolution**

    If multiple rules match, the system selects the rule
    with the highest priority.

    **Step 6: Decision Output**

    The system displays the scholarship decision, matched rule,
    priority and reason for the decision.

    **Step 7: Evaluation History**

    Each successful evaluation is recorded and can be
    downloaded as a CSV file.
    """)


# ==========================================
# 4. APPLICANT EVALUATION HISTORY
# ==========================================

st.divider()

st.header("4. Applicant Evaluation History")

if st.session_state.evaluation_history:

    history_df = pd.DataFrame(
        st.session_state.evaluation_history
    )

    # Display history table
    st.dataframe(
        history_df,
        use_container_width=True,
        hide_index=True
    )

    # Total evaluations
    st.metric(
        "Total Applications Evaluated",
        len(st.session_state.evaluation_history)
    )

    # Download history as CSV
    csv = history_df.to_csv(
        index=False
    ).encode("utf-8")

    st.download_button(
        label="📥 Download History (CSV)",
        data=csv,
        file_name="scholarship_history.csv",
        mime="text/csv",
        use_container_width=True
    )

    # Clear history
    if st.button(
        "Clear Evaluation History",
        use_container_width=True
    ):

        st.session_state.evaluation_history = []
        st.session_state.latest_result = None

        st.rerun()

else:

    st.info(
        "No applicant evaluation history available. "
        "Evaluate an applicant to create a history record."
    )


# ==========================================
# FOOTER
# ==========================================

st.divider()

st.caption(
    "Scholarship Advisory System | BSD3513 Introduction to Artificial Intelligence"
)
