import streamlit as st
import pandas as pd
from datetime import date, timedelta

# ページ設定
st.set_page_config(page_title="課題管理リマインダー", layout="wide")

st.title("📝 課題管理 & リマインダーアプリ")

# --- 1. データ管理 (Session State) ---
# 本格的な運用ではデータベース(Google SheetsやFirestore等)への保存が推奨されますが、
# ここでは動作確認用にセッション状態で管理します。
if "tasks" not in st.session_state:
    st.session_state.tasks = []

# --- 2. 新規課題の追加 (サイドバー) ---
with st.sidebar:
    st.header("新しい課題を追加")
    task_name = st.text_input("課題名")
    due_date = st.date_input("期限", min_value=date.today())
    priority = st.selectbox("重要度", ["高", "中", "低"])
    
    if st.button("追加する"):
        if task_name:
            new_task = {
                "課題名": task_name,
                "期限": due_date,
                "重要度": priority,
                "完了": False
            }
            st.session_state.tasks.append(new_task)
            st.success(f"「{task_name}」を追加しました！")
        else:
            st.error("課題名を入力してください。")

# --- 3. データ処理とリマインドロジック ---
if st.session_state.tasks:
    df = pd.DataFrame(st.session_state.tasks)
    
    # 日付計算（残り日数）
    df["期限"] = pd.to_datetime(df["期限"]).dt.date
    today = date.today()
    df["残り日数"] = (df["期限"] - today).apply(lambda x: x.days)

    # --- リマインダー表示エリア (期限が3日以内のものを強調) ---
    urgent_tasks = df[(df["残り日数"] <= 3) & (df["残り日数"] >= 0) & (df["完了"] == False)]
    overdue_tasks = df[(df["残り日数"] < 0) & (df["完了"] == False)]

    if not overdue_tasks.empty:
        st.error(f"🚨 期限切れの課題が {len(overdue_tasks)} 件あります！急いで確認してください。")
        for index, row in overdue_tasks.iterrows():
            st.write(f"- **{row['課題名']}** (期限: {row['期限']})")
            
    if not urgent_tasks.empty:
        st.warning(f"🔔 期限が3日以内の課題が {len(urgent_tasks)} 件あります。")
        for index, row in urgent_tasks.iterrows():
            st.write(f"- {row['課題名']} (残り {row['残り日数']} 日)")

    st.divider()

    # --- 4. タスク一覧と重要度の可視化 ---
    st.subheader("課題一覧")

    # スタイルの適用関数
    def highlight_priority(val):
        color = ''
        if val == '高':
            color = 'background-color: #ffcccc; color: #990000; font-weight: bold;' # 薄い赤背景に濃い赤文字
        elif val == '中':
            color = 'background-color: #ffffcc; color: #996600;' # 薄い黄色
        elif val == '低':
            color = 'background-color: #ccffcc; color: #006600;' # 薄い緑
        return color

    # データフレームの表示（Pandas Stylerを使用）
    # 完了フラグなどでフィルタリングも可能ですが、ここでは全件表示し、重要度で色付けします
    st.dataframe(
        df.style.map(highlight_priority, subset=['重要度']),
        use_container_width=True,
        column_config={
            "期限": st.column_config.DateColumn("期限", format="YYYY/MM/DD"),
            "残り日数": st.column_config.NumberColumn("あと何日", format="%d 日"),
        }
    )

    # 完了タスクの削除機能（簡易的）
    if st.button("完了した課題をリセット（全削除）"):
        st.session_state.tasks = []
        st.rerun()

else:
    st.info("現在、登録されている課題はありません。サイドバーから追加してください。")
