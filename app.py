import configparser

import streamlit as st
import pandas as pd
import os
from core.ai_client import AIClient
from core.data_engine import DataEngine
from core.prompt_mgr import process_records  # 确保你之前的 replace 逻辑在这个函数里

# 页面配置：使用宽屏模式方便并排显示
st.set_page_config(layout="wide")
st.title("💊 Execl批量生成AI数据")

config = configparser.ConfigParser()
config.read('config/config.ini', encoding='utf-8')

# 初始化 session_state
if 'engine' not in st.session_state:
    st.session_state.engine = DataEngine()

# --- 1. 侧边栏：上传区 ---
with st.sidebar:
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
        # 顶部：数据预览（折叠显示，节省空间）
        with st.expander("查看原始数据预览"):
            st.dataframe(st.session_state.engine.df)

        st.divider()

        # 中间：Prompt 设计区域
        col_design, col_preview = st.columns([1, 1], gap="large")

        with col_design:
            st.subheader("🖋️ 第一步：编写 Prompt 模板")
            st.write("点击下方变量可快速引用：")

            # 以小标签形式展示可用变量
            # 这里的目的是让用户知道该怎么写占位符
            st.caption("可用变量 (直接复制到下方框中)：")
            var_display = " ".join([f"`{{{c}}}`" for c in cols])
            st.write(var_display)

            user_template = st.text_area(
                "Prompt 模板内容：",
                placeholder="例如：产品 {数值} 的 abc 属性是 {abc}，请根据这些信息生成描述。",
                height=300,
                key="template_input"
            )

        with col_preview:
            st.subheader("👁️ 第二步：实时填充预览")
            if user_template:
                # 拿第一行数据做实时效果展示
                if records:
                    # 调用你 core.prompt_mgr 里的 process_records
                    # 我们只传入第一条记录 [records[0]] 进行单条预览
                    preview_list = process_records([records[0]], user_template)

                    st.info("💡 这是第一行数据的填充效果：")
                    # 修改后：
                    st.markdown(f"""
                    <div style="background-color: #f0f2f6; padding: 20px; border-radius: 10px; border-left: 5px solid #ff4b4b; color: #31333F;">
                        {preview_list[0]}
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    st.warning("暂无记录可供预览")
            else:
                st.write("⬅️ 请在左侧输入 Prompt 模板，预览将在此实时生成。")

        # --- 3. 底部：任务提交 ---
        st.divider()
        if user_template:
            if st.button("🚀 生成全部数据 Prompt", type="primary", use_container_width=True):
                # 1. 生成并调用 AI
                all_prompts = process_records(records, user_template)

                with st.status("正在调用 AI 处理数据...", expanded=True) as status:
                    ai_processor = AIClient(api_key=config['openai']['api_key'], model="gpt-4o-mini")
                    final_results = ai_processor.batch_generate(all_prompts, max_workers=10)
                    status.update(label="处理完成！", state="complete", expanded=False)

                # 2. 将结果写回 session_state 中的 dataframe
                # 假设我们将结果列命名为 "AI_处理结果"
                st.session_state.engine.df["AI_处理结果"] = final_results

                # 3. 界面反馈
                st.balloons()
                st.success(f"✅ 已完成 {len(final_results)} 行数据的 AI 处理！")

                # 4. 展示最终表格
                st.subheader("📊 处理结果预览")
                st.dataframe(st.session_state.engine.df, use_container_width=True)

                # 5. 提供下载功能
                # 将结果保存为字节流提供下载
                output_path = "processed_data.xlsx"
                st.session_state.engine.df.to_excel(output_path, index=False)

                with open(output_path, "rb") as f:
                    st.download_button(
                        label="📥 下载处理好的 Excel 文件",
                        data=f,
                        file_name="医药数据处理结果.xlsx",
                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
                    )

    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)
else:
    st.info("👋 请先在左侧侧边栏上传数据文件。")