import streamlit as st
from supabase import create_client

st.title("接続テスト")

supabase = create_client(
    st.secrets["SUPABASE_URL"],
    st.secrets["SUPABASE_KEY"]
)

st.success("✅ Supabase に接続できました！")
