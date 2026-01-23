import streamlit as st
from supabase import create_client, Client

# --- 1. Supabase 接続設定 ---
url: str = st.secrets["SUPABASE_URL"]
key: str = st.secrets["SUPABASE_KEY"]
supabase: Client = create_client(url, key)

st.title("💰 シンプル支出管理アプリ")

# --- 2. データの入力エリア (Create) ---
with st.expander("新しい支出を追加する"):
    with st.form("expense_form"):
        item = st.text_input("項目（例：ランチ）")
        amount = st.number_input("金額 (円)", min_value=0, step=100)
        category = st.selectbox("カテゴリ", ["食費", "交通費", "日用品", "娯楽", "その他"])
        submit = st.form_submit_button("保存する")

        if submit and item and amount > 0:
            # データベースへ挿入
            data = {
                "item": item,
                "amount": amount,
                "category": category
            }
            supabase.table("expenses").insert(data).execute()
            st.success(f"「{item}」を記録しました！")
            st.rerun()

# --- 3. データの取得と集計 (Read) ---
response = supabase.table("expenses").select("*").order("created_at", desc=True).execute()
expenses = response.data

if expenses:
    # 合計金額の計算
    total_amount = sum(exp["amount"] for exp in expenses)
    st.metric("今月の合計支出", f"{total_amount:,} 円")

    st.subheader("履歴")
    # テーブル形式で表示
    for exp in expenses:
        col1, col2, col3, col4 = st.columns([4, 2, 2, 1])
        col1.write(f"**{exp['item']}** ({exp['category']})")
        col2.write(f"{exp['amount']:,} 円")
        col3.write(exp['created_at'][:10]) # 日付のみ表示
        
        # 削除ボタン
        if col4.button("🗑️", key=f"del_{exp['id']}"):
            supabase.table("expenses").delete().eq("id", exp["id"]).execute()
            st.rerun()
else:
    st.info("まだ記録がありません。上のフォームから入力してください。")