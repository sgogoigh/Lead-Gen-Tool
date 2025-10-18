import tldextract

def guess_email_patterns(company_name, domain):
    """
    Return a list of probable email patterns for common names.
    This is heuristic — for production use real enrichment APIs.
    """
    if not domain:
        return []
    domain = domain.lower()
    cname = (company_name or "").lower().replace(" ", "")
    patterns = [
        f"info@{domain}",
        f"hello@{domain}",
        f"contact@{domain}",
        f"sales@{domain}",
    ]
    return patterns

def short_text(txt, n=140):
    if not txt:
        return None
    return txt if len(txt) <= n else txt[:n-1].rsplit(" ",1)[0] + "…"
