"""Interpret the upload's check status, not navigation controls or old posts."""


def checks_outcome(progress, details="", warning=False):
    if warning:
        return "pending"
    progress = (progress or "").lower()
    details = (details or "").lower().replace("\u2019", "'")
    if "checks complete" not in progress:
        return "pending"
    if "no issues found" in progress:
        return "complete"
    if "claimed content found" in progress:
        if "this claim doesn't affect your video's visibility or features" in details:
            return "complete"
        return "review"
    return "review"
