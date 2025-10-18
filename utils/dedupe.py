import pandas as pd
from rapidfuzz import fuzz

def dedupe_dataframe(records):
    df = pd.DataFrame(records)
    # Basic dedupe by domain or source_url
    if "domain" in df.columns:
        df = df.drop_duplicates(subset=["domain"], keep="first")
    df = df.drop_duplicates(subset=["source_url"], keep="first")
    # fuzzy dedupe on company names
    df = df.reset_index(drop=True)
    keep = []
    seen = []
    for idx, row in df.iterrows():
        name = str(row.get("company_name") or "").strip()
        if not name:
            keep.append(idx); seen.append(name)
            continue
        dup = False
        for s in seen:
            if s and fuzz.token_sort_ratio(name, s) > 90:
                dup = True; break
        if not dup:
            keep.append(idx); seen.append(name)
    return df.loc[keep].reset_index(drop=True)
