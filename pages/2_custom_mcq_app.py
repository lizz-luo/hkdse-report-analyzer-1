import pandas as pd
import streamlit as st

from pdf_utils import extract_mcq_analysis

st.set_page_config(page_title="MCQ Analysis", page_icon="🎯", layout="wide")
st.title("🎯 自定義 MCQ 分析 app")
st.caption("此頁會讀取主 app 已處理好的資料。請先回主 app 上載 PDF，並按『處理檔案並啟用自定義分析 app』。")

if "mcq_custom_cols" not in st.session_state:
    st.session_state.mcq_custom_cols = []
if "mcq_col_options_history" not in st.session_state:
    st.session_state.mcq_col_options_history = {}
if "item_custom_values" not in st.session_state:
    st.session_state.item_custom_values = {}
if "mcq_custom_values" not in st.session_state:
    st.session_state.mcq_custom_values = {}
if "mcq_clear_inputs" not in st.session_state:
    st.session_state.mcq_clear_inputs = False
if "mcq_save_note" not in st.session_state:
    st.session_state.mcq_save_note = ""

def prepare_mcq_analysis_for_custom(df):
    df = df.copy()
    def get_top_option(row, prefix):
        opts = {
            "A": row.get(f"{prefix} A_No.", 0),
            "B": row.get(f"{prefix} B_No.", 0),
            "C": row.get(f"{prefix} C_No.", 0),
            "D": row.get(f"{prefix} D_No.", 0),
        }
        for k in opts:
            try:
                opts[k] = float(opts[k])
            except:
                opts[k] = 0
        return max(opts, key=opts.get)
    df["Your school Top Option"] = df.apply(lambda r: get_top_option(r, "Your school"), axis=1)
    df["Day schools Top Option"] = df.apply(lambda r: get_top_option(r, "Day schools"), axis=1)
    return df

def highlight_mcq_row(row):
    your_top = str(row.get("Your school Top Option", "")).strip()
    day_top = str(row.get("Day schools Top Option", "")).strip()
    corr_ans = str(row.get("Corr. Ans", "")).replace("☑️", "").strip()
    cond1 = (your_top != corr_ans)
    cond2 = (your_top != day_top)
    if cond1 and cond2:
        return ["background-color: #f8d7da"] * len(row)
    elif cond1:
        return ["background-color: #fff3cd"] * len(row)
    elif cond2:
        return ["background-color: #d1ecf1"] * len(row)
    else:
        return [""] * len(row)

st.page_link("app.py", label="⬅️ 返回主 app", icon="⬅️")

if "processed_mcq_df" not in st.session_state or st.session_state.processed_mcq_df is None:
    source_pdf_bytes = st.session_state.get("source_pdf_bytes")
    if isinstance(source_pdf_bytes, (bytes, bytearray)) and source_pdf_bytes:
        st.session_state.processed_mcq_df = extract_mcq_analysis(source_pdf_bytes)

if "processed_mcq_df" not in st.session_state or st.session_state.processed_mcq_df is None:
    st.warning("尚未找到已處理好的 MCQ 資料。請先回主 app 完成前處理。")
    st.stop()

df_mcq_c = st.session_state.processed_mcq_df.copy()
source_name = st.session_state.get("source_pdf_name", "未命名檔案")
st.success(f"已載入主 app 處理完成的資料：{source_name}")

if not df_mcq_c.empty:
    df_mcq_c = prepare_mcq_analysis_for_custom(df_mcq_c)
    if "題號" not in df_mcq_c.columns:
        df_mcq_c.insert(0, "題號", df_mcq_c.get("Question Number", range(1, len(df_mcq_c) + 1)))
    if "初始序列" not in df_mcq_c.columns:
        df_mcq_c.insert(0, "初始序列", range(1, len(df_mcq_c) + 1))

    sel_q_mcq = None
    step1_col, step2_col = st.columns([1, 1])

    with step1_col:
        st.info("Step 1：建立 MCQ 自定義欄位 (最多 6 個)")
        if st.session_state.mcq_custom_cols:
            st.success(f"目前建立的欄位：{', '.join(st.session_state.mcq_custom_cols)}")
        else:
            st.warning("目前尚未建立任何 MCQ 自定義欄位。可先在此頁新增欄位名稱。")

        with st.form("mcq_add_field_form", clear_on_submit=True):
            new_col = st.text_input("輸入新自定義欄位名稱：", key="new_col_input_mcq")
            submitted = st.form_submit_button("➕ 新增欄位")
            if submitted:
                if new_col and new_col not in st.session_state.mcq_custom_cols and len(st.session_state.mcq_custom_cols) < 6:
                    st.session_state.mcq_custom_cols.append(new_col)
                    st.session_state.mcq_col_options_history[new_col] = []

    with step2_col:
        st.info("Step 2：為每一題設定分類 (下拉聯想與新增)")
        question_options = [f"{row['題號']} [{row['初始序列']}]" for _, row in df_mcq_c.iterrows()]
        seq_map = {f"{row['題號']} [{row['初始序列']}]": row['初始序列'] for _, row in df_mcq_c.iterrows()}
        sel_q_mcq_display = st.multiselect("選擇要輸入標籤的題號：", question_options, default=question_options[:1], key="mcq_q_sel")
        sel_q_mcq = [seq_map[q] for q in sel_q_mcq_display]

        if st.session_state.mcq_clear_inputs:
            for col in st.session_state.mcq_custom_cols:
                sel_key = f"sel_mcq_{col}"
                new_key = f"new_val_mcq_{col}"
                st.session_state[sel_key] = ""
                st.session_state[new_key] = ""
            st.session_state.mcq_clear_inputs = False

        if sel_q_mcq_display:
            selected_display = ", ".join(sel_q_mcq_display)
            st.write(f"**正在編輯：{selected_display}**")
            all_values = [st.session_state.mcq_custom_values.get(idx, {}) for idx in sel_q_mcq]
            curr_vals_mcq = {}
            for col in st.session_state.mcq_custom_cols:
                values_for_col = {v.get(col, "") for v in all_values}
                curr_vals_mcq[col] = values_for_col.pop() if len(values_for_col) == 1 else ""
        else:
            st.warning("請先選擇至少一題。")
            curr_vals_mcq = {}

        input_results_m = {}
        for col in st.session_state.mcq_custom_cols:
            history_opts = st.session_state.mcq_col_options_history.get(col, [])
            options = [""] + history_opts + ["輸入新文本"]
            default_idx = 0
            curr_val = curr_vals_mcq.get(col, "")
            if curr_val in options:
                default_idx = options.index(curr_val)
            sel_col, new_col = st.columns([1, 1])
            with sel_col:
                sel_key = f"sel_mcq_{col}"
                sel_val = st.selectbox(f"{col}:", options=options, index=default_idx, key=sel_key)
            with new_col:
                if sel_val == "輸入新文本":
                    new_key = f"new_val_mcq_{col}"
                    if new_key not in st.session_state:
                        st.session_state[new_key] = ""
                    new_val = st.text_input(f"請輸入新的「{col}」:", key=new_key)
                    input_results_m[col] = new_val
                else:
                    input_results_m[col] = sel_val

        submit_col, note_col = st.columns([1, 1])
        with submit_col:
            submit_btn_m = st.button("📥 儲存設定", key=f"mcq_save_btn_{'_'.join(str(x) for x in sel_q_mcq)}")
        save_note_m = note_col.empty()
        if st.session_state.mcq_save_note:
            save_note_m.caption(st.session_state.mcq_save_note)

        if submit_btn_m and sel_q_mcq:
            for idx in sel_q_mcq:
                if idx not in st.session_state.mcq_custom_values:
                    st.session_state.mcq_custom_values[idx] = {}
                for col, val in input_results_m.items():
                    if val:
                        st.session_state.mcq_custom_values[idx][col] = val
                        if val not in st.session_state.mcq_col_options_history[col]:
                            st.session_state.mcq_col_options_history[col].append(val)
            st.session_state["mcq_last_saved_q"] = sel_q_mcq
            st.session_state["mcq_save_note"] = f"已為 {selected_display} 設定分類"
            st.session_state.mcq_clear_inputs = True
            st.rerun()

    df_mcq_display = df_mcq_c.copy()
    for col in st.session_state.mcq_custom_cols:
        df_mcq_display[col] = df_mcq_display["初始序列"].apply(lambda x: st.session_state.mcq_custom_values.get(x, {}).get(col, ""))

    st.write("📊 **總覽表 (自動更新)：**")
    st.dataframe(df_mcq_display, use_container_width=True, hide_index=True)

    st.markdown("---")
    st.info("Step 3：篩選與高亮分析")

    f_cols_mcq = st.columns(max(len(st.session_state.mcq_custom_cols), 1))
    active_filters_mcq = {}
    for i, col in enumerate(st.session_state.mcq_custom_cols):
        with f_cols_mcq[i]:
            u_vals_mcq = [x for x in df_mcq_display[col].unique() if str(x).strip()]
            active_filters_mcq[col] = st.multiselect(f"篩選 {col}", u_vals_mcq, key=f"filter_mcq_{col}")

    final_mcq_df = df_mcq_display.copy()
    for col, s_filters in active_filters_mcq.items():
        if s_filters:
            final_mcq_df = final_mcq_df[final_mcq_df[col].isin(s_filters)]

    st.markdown("""
    🔍 顏色說明：紅色 = 貴校最高選項既非正答亦不同於日校；黃色 = 非正答；藍色 = 與日校最高選項不同。
    """)
    st.dataframe(final_mcq_df.style.apply(highlight_mcq_row, axis=1), use_container_width=True, hide_index=True)
else:
    st.error("找不到可用的 MCQ 分析資料。")

st.markdown("---")
