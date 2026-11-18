import pandas as pd
import streamlit as st
from db import get_conn

st.set_page_config(page_title="Progress History")
st.title("Progress History")

conn = get_conn()
df = pd.read_sql_query("SELECT * FROM answers ORDER BY created_at", conn)
conn.close()

if df.empty:
    st.info("No answers saved yet. Analyze an answer first, then come back.")
    st.stop()

df["created_at"] = pd.to_datetime(df["created_at"])

c1, c2, c3 = st.columns(3)
c1.metric("Answers recorded", len(df))
c2.metric("Sessions", df["session_id"].nunique())
c3.metric("Average WPM", round(df["wpm"].mean()))

st.subheader("Scores over time (per session average)")
by_session = (
    df.groupby("session_id")
    .agg(
        date=("created_at", "min"),
        relevance=("relevance", "mean"),
        structure=("structure", "mean"),
        depth=("depth", "mean"),
        wpm=("wpm", "mean"),
        long_pauses=("long_pauses", "sum"),
        fillers=("fillers", "sum"),
    )
    .sort_values("date")
    .reset_index()
)
st.line_chart(by_session.set_index("date")[["relevance", "structure", "depth"]])

st.subheader("Delivery over time")
st.line_chart(by_session.set_index("date")[["wpm", "long_pauses", "fillers"]])

st.subheader("All answers")
st.dataframe(
    df[["created_at", "mode", "question", "wpm", "long_pauses", "fillers",
        "relevance", "structure", "depth"]].sort_values("created_at", ascending=False),
    use_container_width=True,
)