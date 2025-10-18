import streamlit as st
import pandas as pd
from scraper.scraper import scrape_urls
from scraper.enricher import enrich_records
from utils.dedupe import dedupe_dataframe
from io import BytesIO

st.set_page_config(page_title="LeadGen Tool", layout="wide")

st.title("LeadGen Prototype — Scrape ▶ Enrich ▶ Export")

with st.expander("Instructions"):
    st.markdown("""
    1. Provide a list of target landing page URLs (one per line) or upload a .txt file.
    2. Run "Scrape & Enrich".
    3. Filter results and export CSV.
    """)

col1, col2 = st.columns([2,1])

with col1:
    uploaded = st.file_uploader("Upload a .txt file of URLs (one per line)", type=["txt"])
    manual = st.text_area("Or paste URLs (one per line)", height=120)
    if st.button("Load sample targets"):
        with open("data/sample_targets.txt","r") as f:
            manual = f.read()
            st.experimental_rerun()

with col2:
    max_workers = st.number_input("Concurrency (workers)", min_value=1, max_value=20, value=5)
    run_btn = st.button("Scrape & Enrich")

targets = []
if uploaded:
    content = uploaded.getvalue().decode("utf-8")
    targets = [l.strip() for l in content.splitlines() if l.strip()]
elif manual:
    targets = [l.strip() for l in manual.splitlines() if l.strip()]

if run_btn:
    if not targets:
        st.error("Provide at least one target URL.")
    else:
        with st.spinner(f"Scraping {len(targets)} targets..."):
            records = scrape_urls(targets, workers=max_workers)
        st.success("Scrape complete — running enrichment...")
        with st.spinner("Enriching records..."):
            enriched = enrich_records(records, workers=max_workers)
        df = pd.DataFrame(enriched)
        df = dedupe_dataframe(df)
        st.session_state["df"] = df
        st.success("Done — results ready.")

if "df" in st.session_state:
    df = st.session_state["df"]
    st.subheader("Results")
    st.write(f"{len(df)} leads")
    cols = st.multiselect("Columns to show", options=list(df.columns), default=list(df.columns))
    st.dataframe(df[cols].fillna(""))

    st.markdown("### Filters")
    q = st.text_input("Search (company, domain, title, description)")
    if q:
        mask = df.apply(lambda row: row.astype(str).str.contains(q, case=False).any(), axis=1)
        df_filtered = df[mask]
    else:
        df_filtered = df

    st.write(f"{len(df_filtered)} filtered rows")
    st.dataframe(df_filtered[cols].fillna(""))

    def to_csv_bytes(df_in):
        out = BytesIO()
        df_in.to_csv(out, index=False)
        out.seek(0)
        return out

    csv_bytes = to_csv_bytes(df_filtered)
    st.download_button("Export CSV", data=csv_bytes, file_name="leads.csv", mime="text/csv")

    st.markdown("---")
    st.markdown("**Note:** This is a demo prototype. For higher quality enrichment integrate paid APIs (Clearbit, Hunter, FullContact) and add rate-limit/proxy handling.")
