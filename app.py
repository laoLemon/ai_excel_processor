import streamlit as st
import pandas as pd
import os
from core.data_engine import DataEngine
from core.prompt_mgr import process_records  # 确保你之前的 replace 逻辑在这个函数里

# 页面配置：使用宽屏模式方便并排显示
st.set_page_config(layout="wide")
st.title("💊 医药数据 AI Prompt 设计器")

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
                all_prompts = process_records(records, user_template)
                st.success(f"成功为 {len(all_prompts)} 行数据生成了 Prompt！")

                with st.expander("点击查看生成结果的前 5 条示例"):
                    for i, p in enumerate(all_prompts[:5]):
                        st.text_area(f"Row {i + 1}", p, height=100)

                # 1. 直接把这“一条”模板存入后端 session 或变量
                st.session_state.final_template = user_template

                st.success("✅ 模板已锁定！后端现在可以使用此模板动态生成数据。")

                # 展示后端拿到的到底是什么
                st.write("后端当前持有的模板变量：")
                st.code(st.session_state.final_template)

                # 2. 此时你可以调用后端的一个“总控方法”，只把模板传进去
                # backend_processor.run_all(st.session_state.final_template)
                # st.balloons()

    # 清理临时文件
    if os.path.exists(temp_path):
        os.remove(temp_path)
else:
    st.info("👋 请先在左侧侧边栏上传数据文件。")