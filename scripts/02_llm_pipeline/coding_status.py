"""Separate substantive stance labels from technical response failures."""

VALID_SCORES = {-99, -1, 0, 1}
TECHNICAL_STATUSES = {
    "Safety_Blocked", "Missing_Or_Safety_Blocked", "Missing_Score",
    "Missing_Response", "API_Error", "Parse_Error", "Invalid_Score",
}


def normalize_record(row):
    """Preserve the imported score; clear technical failures in LLM_Score."""
    result = dict(row)
    original = row.get("LLM_Score_Original", row.get("LLM_Score", ""))
    reason = (row.get("LLM_Reasoning") or "").upper()
    status = row.get("Coding_Status", "")
    if not status:
        if "MISSING_FROM_GCP_OR_SAFETY" in reason:
            status = "Missing_Or_Safety_Blocked"
        elif "SAFETY_BLOCK" in reason:
            status = "Safety_Blocked"
        elif str(original).strip() == "":
            status = "Missing_Score"
        else:
            status = "Coded"
    if status == "Coded":
        try:
            score = float(original)
        except (TypeError, ValueError) as exc:
            raise ValueError("Coded record has no valid numeric score") from exc
        if score not in VALID_SCORES:
            raise ValueError(f"Invalid stance score: {original!r}")
        result["LLM_Score"] = original
    elif status in TECHNICAL_STATUSES:
        result["LLM_Score"] = ""
    else:
        raise ValueError(f"Unknown Coding_Status: {status}")
    result["LLM_Score_Original"] = original
    result["Coding_Status"] = status
    return result
