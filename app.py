import configparser
import streamlit as st
import pandas as pd
import os
from openai import OpenAI  # 引入官方库用来获取模型列表
from core.ai_client import AIClient
from core.data_engine import DataEngine
from core.prompt_mgr import process_records

# 页面配置
st.set_page_config(layout="wide")
st.title("💊 Excel 批量多列 AI 数据生成器")

config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')
api_key = config['openai']['api_key']

# --- 初始化 session_state ---
if 'engine' not in st.session_state:
    st.session_state.engine = DataEngine()

if 'tasks' not in st.session_state:
    st.session_state.tasks = [{"column_name": "AI_处理结果_1", "template": ""}]


# --- 【新增功能】动态获取可用的 OpenAI 模型列表 ---
@st.cache_data(show_spinner="正在同步可用模型列表...")
def get_available_models(api_key):
    try:
        client = OpenAI(api_key=api_key)
        models_list = client.models.list()
        # 提取模型 ID 并排序
        model_ids = [model.id for model in models_list.data]
        model_ids.sort()
        return model_ids
    except Exception as e:
        # 如果获取失败，返回一组常用的备用模型，确保程序不崩溃
        return ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]


# 调用函数获取模型
available_models = get_available_models(api_key)

# --- 1. 侧边栏：上传区 & 模型选择区 ---
with st.sidebar:
    st.header("⚙️ 配置面板")

    # 动态模型选择下拉框
    selected_model = st.selectbox(
        "🤖 选择要调用的 AI 模型：",
        options=available_models,
        index=available_models.index("gpt-4o") if "gpt-4o" in available_models else 0,
        help="列表实时同步自您的 OpenAI 账号"
    )
    st.caption(f"当前选择：`{selected_model}`")

    st.divider()

    st.header("数据上传")
    uploaded_file = st.file_uploader("上传 Excel 或 CSV", type=['xlsx', 'xls', 'csv'])

if uploaded_file:
    temp_path = f"temp_{uploaded_file.name}"
    with open(temp_path, "wb") as f:
        f.write(uploaded_file.getbuffer())

    success = st.session_state.engine.load_file(temp_path)

    if success:
        st.sidebar.success("✅ 文件读取成功！")

        # 获取基础数据
        cols = st.session_state.engine.get_column_names()
        records = st.session_state.engine.get_all_records()

        # --- 2. 主界面布局 ---
        # 顶部：数据预览
        with st.expander("查看原始数据预览"):
            st.dataframe(st.session_state.engine.df)

        st.divider()

        # 中间：多任务 Prompt 设计区域
        st.subheader("🖋️ 第一步：配置多列 AI 生成任务")
        st.caption("可用变量 (请手动复制占位符到模板中)：")
        var_display = " ".join([f"`{{{c}}}`" for c in cols])
        st.write(var_display)

        # 动态控制任务数量的按钮
        col_btn1, col_btn2, _ = st.columns([1, 1, 8])
        with col_btn1:
            if st.button("➕ 添加一列 AI 任务", use_container_width=True):
                next_idx = len(st.session_state.tasks) + 1
                st.session_state.tasks.append({"column_name": f"AI_处理结果_{next_idx}", "template": ""})
                st.rerun()
        with col_btn2:
            if st.button("➖ 删除最后一列", use_container_width=True) and len(st.session_state.tasks) > 1:
                st.session_state.tasks.pop()
                st.rerun()

        st.write("")  # 留空

        # 循环渲染每一列的配置区与实时预览
        all_tasks_valid = True

        for idx, task in enumerate(st.session_state.tasks):
            with st.container(border=True):
                col_design, col_preview = st.columns([1, 1], gap="large")

                with col_design:
                    st.markdown(f"### 📋 任务 #{idx + 1}")
                    new_col_name = st.text_input(
                        f"请输入第 {idx + 1} 个生成的**新列名**：",
                        value=task["column_name"],
                        key=f"col_name_{idx}"
                    )
                    st.session_state.tasks[idx]["column_name"] = new_col_name

                    user_template = st.text_area(
                        f"任务 #{idx + 1} 的 Prompt 模板内容：",
                        value=task["template"],
                        placeholder="例如：请根据 {产品名称} 生成一句话的中文短描述...",
                        height=150,
                        key=f"template_{idx}"
                    )
                    st.session_state.tasks[idx]["template"] = user_template

                    if not user_template or not new_col_name:
                        all_tasks_valid = False

                with col_preview:
                    st.markdown("#### 👁️ 实时填充预览 (第一行数据)")
                    if user_template:
                        if records:
                            preview_list = process_records([records[0]], user_template)
                            st.markdown(f"""
                            <div style="background-color: #f0f2f6; padding: 15px; border-radius: 8px; border-left: 5px solid #1E90FF; color: #31333F;">
                                <strong>[{new_col_name}] 填充效果：</strong><br>{preview_list[0]}
                            </div>
                            """, unsafe_allow_html=True)
                        else:
                            st.warning("暂无记录可供预览")
                    else:
                        st.caption("⬅️ 请在左侧输入当前任务的列名和 Prompt 模板。")

        # --- 3. 底部：任务批量提交 ---
        st.divider()

        if all_tasks_valid:
            # 按钮文本上动态显示当前选中的模型，提醒更贴心
            if st.button(f"🚀 使用 {selected_model} 启动全部 AI 列并行生成", type="primary", use_container_width=True):

                # 【修改点】动态传入侧边栏选中的 selected_model
                ai_processor = AIClient(api_key=api_key, model=selected_model)

                with st.status(f"正在使用 {selected_model} 并行处理多列数据...", expanded=True) as status:

                    for idx, task in enumerate(st.session_state.tasks):
                        c_name = task["column_name"]
                        t_prompt = task["template"]

                        st.write(f"⏳ 正在处理任务 #{idx + 1}：使用 `{selected_model}` 写入新列 `[{c_name}]`...")

                        current_prompts = process_records(records, t_prompt)
                        final_results = ai_processor.batch_generate(current_prompts, max_workers=10)
                        st.session_state.engine.df[c_name] = final_results

                    status.update(label="🚀 所有 AI 列数据生成完成！", state="complete", expanded=False)

                st.balloons()
                st.success(f"✅ 成功使用 {selected_model} 并行生成了 {len(st.session_state.tasks)} 列 AI 数据！")

                # 展示最终表格
                st.subheader("📊 最终多列处理结果预览")
                st.dataframe(st.session_state.engine.df, use_container_width=True)

                # 提供下载功能
                output_path = "processed_data_multi.xlsx"
                st.session_state.engine.df.to_excel(output_path, index=False)

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 下载多列处理好的 Excel 文件",
                        data=f,
                        file_name="医药多列数据处理结果.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )
        else:
            st.warning("⚠️ 请确保上面所有添加的任务都填写了「新列名」和「Prompt 模板」，否则无法提交。")

    if os.path.exists(temp_path):
        os.remove(temp_path)
else:
    st.info("👋 请先在左侧侧边栏上传数据文件。")