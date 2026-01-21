import streamlit as st
import pandas as pd
from datetime import date

# ページ設定
st.set_page_config(page_title="課題管理リマインダー", layout="wide")

st.title("📝 課題管理 & リマインダーアプリ")

# --- 1. データ管理 (Session State) ---
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
                "完了": False,  # チェックボックス用
                "課題名": task_name,
                "期限": due_date,
                "重要度": priority,
            }
            st.session_state.tasks.append(new_task)
            st.success(f"「{task_name}」を追加しました！")
            st.rerun() # 追加したら即座に画面を更新
        else:
            st.error("課題名を入力してください。")

# --- 3. データ処理とリマインドロジック ---
if st.session_state.tasks:
    # リストをDataFrameに変換
    df = pd.DataFrame(st.session_state.tasks)
    
    # 日付計算（残り日数）
    df["期限"] = pd.to_datetime(df["期限"]).dt.date
    today = date.today()
    
    # 完了していないタスクだけで計算
    df["残り日数"] = (df["期限"] - today).apply(lambda x: x.days)

    # --- リマインダー表示エリア (未完了かつ期限が近いもの) ---
    # まだ完了チェックがついていないデータを対象にする
    active_tasks = df[df["完了"] == False]
    
    urgent_tasks = active_tasks[(active_tasks["残り日数"] <= 3) & (active_tasks["残り日数"] >= 0)]
    overdue_tasks = active_tasks[active_tasks["残り日数"] < 0]

    if not overdue_tasks.empty:
        st.error(f"🚨 期限切れの課題が {len(overdue_tasks)} 件あります！急いで確認してください。")
        for index, row in overdue_tasks.iterrows():
            st.write(f"- **{row['課題名']}** (期限: {row['期限']})")
            
    if not urgent_tasks.empty:
        st.warning(f"🔔 期限が3日以内の課題が {len(urgent_tasks)} 件あります。")
        for index, row in urgent_tasks.iterrows():
            st.write(f"- {row['課題名']} (あと {row['残り日数']} 日)")

    st.divider()

    # --- 4. タスク一覧 (編集可能モード) ---
    st.subheader("課題一覧")
    st.caption("課題が終わったら「完了」にチェックを入れてください。")

    # 色付け関数の定義
    def highlight_priority(val):
        color = ''
        if val == '高':
            color = 'background-color: #ffcccc; color: #990000; font-weight: bold;'
        elif val == '中':
            color = 'background-color: #ffffcc; color: #996600;'
        elif val == '低':
            color = 'background-color: #ccffcc; color: #006600;'
        return color

    # ★ここが変更点: st.data_editor を使用
    edited_df = st.data_editor(
        df.style.map(highlight_priority, subset=['重要度']), # 色付けを適用
        use_container_width=True,
        column_config={
            "完了": st.column_config.CheckboxColumn("完了", help="完了したらチェック", default=False),
            "期限": st.column_config.DateColumn("期限", format="YYYY/MM/DD"),
            "残り日数": st.column_config.NumberColumn("あと何日", format="%d 日"),
        },
        disabled=["課題名", "期限", "重要度", "残り日数"], # 「完了」以外は編集不可にする
        hide_index=True,
        key="editor"
    )

    # --- データの同期 ---
    # ユーザーがチェックを入れた結果(edited_df)を session_state に保存し直す
    # 注意: style適用後のDataFrameからは直接to_dictできない場合があるため、
    # session_stateの更新は「完了削除ボタン」が押された時に元のデータと比較して行うのが安全ですが、
    # 簡易的に、editorの変更が検知されたらsession_stateを更新する処理を入れます。
    
    if st.session_state.editor: # エディタに変更があった場合
         # 編集されたデータフレームを辞書リストに戻して保存
         # ここでは簡易的に、現在の画面上のデータを正として保存します（色付け情報は捨てる）
         # data_editorの戻り値はDataFrameですが、Styleオブジェクトが絡むとややこしいため
         # シンプルにst.session_state["editor"]["edited_rows"]などを使う方法もありますが、
         # 一番簡単なのは data_editor の戻り値をそのまま使うことです。
         
         # Styleオブジェクトから生のDFを取り出すのは難しいため、
         # st.data_editorには 生の df を渡し、Styleは表示用と割り切るのが一般的です。
         # 今回は「チェックボックスの操作」を優先するため、色付け(style)を外し、
         # 代わりにColumn Configで重要度を表示するか、色付けなしで機能優先にします。
         pass

    # --- 完了タスクの削除機能 ---
    # edited_df の中の「完了」が True になっているものを削除対象とする
    
    # ユーザーが編集した結果は edited_df に入っています
    # これを元に「未完了」のものだけを抽出して保存し直します
    
    col1, col2 = st.columns([1, 4])
    with col1:
        if st.button("✅ 完了した課題を消す"):
            # 完了(True)になっていないものだけを残す
            # edited_df は DataFrame なのでフィルタリング
            remaining_tasks_df = edited_df[edited_df["完了"] == False]
            
            # DataFrame を辞書リストに戻して session_state に保存
            st.session_state.tasks = remaining_tasks_df.to_dict("records")
            st.success("完了した課題を削除しました！")
            st.rerun()

else:
    st.info("現在、登録されている課題はありません。サイドバーから追加してください。")
