import streamlit as st
from supabase import create_client, Client
from datetime import date
import pandas as pd

# ===============================
# Supabase 接続
# ===============================
url = st.secrets["SUPABASE_URL"]
key = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

# ===============================
# 定数
# ===============================
CATEGORIES = ["食費", "交通費", "日用品", "娯楽", "その他"]

PERSONALITY = {
    "食費": "🍚『ちゃんと生きてる証拠』",
    "交通費": "🚃『移動にも人生がある』",
    "日用品": "🧻『地味だけど削れない』",
    "娯楽": "🎮『逃げ場は必要』",
    "その他": "💸『正体不明の支出…』"
}

# ===============================
# 自動カテゴリ判定
# ===============================
def auto_category(item: str):
    rules = supabase.table("category_rules").select("*").execute().data
    for r in rules:
        if r["keyword"] in item:
            return r["category"]
    return "その他"

# ===============================
# タイトル
# ===============================
st.title("💰 感情つき・変な家計簿（完成版）")

# ===============================
# 時給設定
# ===============================
st.sidebar.header("⚙️ 設定")
hourly_wage = st.sidebar.number_input(
    "あなたの時給（円）",
    min_value=0,
    value=1200,
    step=100
)

# ===============================
# 支出入力
# ===============================
st.subheader("➕ 支出を追加")

with st.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("日付", value=date.today())
    item = st.text_input("項目")
    amount = st.number_input("金額（円）", min_value=0, step=100)

    auto_cat = auto_category(item) if item else "その他"
    category = st.selectbox(
        "カテゴリ（自動判定）",
        CATEGORIES,
        index=CATEGORIES.index(auto_cat)
    )

    emotion = st.selectbox("今の気持ち", ["😊 満足", "😐 まあまあ", "😞 後悔"])
    reason = st.text_input("理由（任意）")
    reason_tag = st.selectbox(
        "やめられなかった理由",
        ["習慣", "ストレス", "ご褒美", "逃避", "なんとなく"]
    )

    submit = st.form_submit_button("保存")

    if submit and item and amount > 0:
        supabase.table("expenses").insert({
            "date": expense_date.isoformat(),
            "item": item,
            "amount": amount,
            "category": category,
            "emotion": emotion,
            "reason": reason,
            "reason_tag": reason_tag
        }).execute()

        st.success("✅ 保存しました")
        st.rerun()

# ===============================
# データ取得
# ===============================
expenses = (
    supabase.table("expenses")
    .select("*")
    .order("date", desc=True)
    .execute()
    .data
)

st.divider()

# ===============================
# 表示・分析
# ===============================
if expenses:
    df = pd.DataFrame(expenses)

    total_amount = df["amount"].sum()
    st.metric("📊 合計支出", f"{total_amount:,} 円")

    if hourly_wage > 0:
        st.caption(f"⏳ 労働換算：約 {total_amount / hourly_wage:.1f} 時間")

    st.subheader("📊 カテゴリ別支出")
    st.bar_chart(df.groupby("category")["amount"].sum())

    st.subheader("💭 感情別支出")
    st.bar_chart(df.groupby("emotion")["amount"].sum())

    st.subheader("🧾 履歴")

    for e in expenses:
        cols = st.columns([4, 2, 2, 1])

        cols[0].write(f"**{e['item']}**（{e['category']}）")
        cols[0].caption(f"{e['emotion']}｜{e['reason_tag']}")
        if e["reason"]:
            cols[0].caption(f"💬 {e['reason']}")

        cols[1].write(f"{e['amount']:,} 円")
        if hourly_wage > 0:
            cols[1].caption(f"⏳ {e['amount'] / hourly_wage:.1f}h")

        cols[2].write(e["date"])

        if cols[3].button("🗑", key=e["id"]):
            supabase.table("expenses").delete().eq("id", e["id"]).execute()
            st.rerun()

        st.caption(PERSONALITY.get(e["category"], ""))

else:
    st.info("まだ記録がありません。")
