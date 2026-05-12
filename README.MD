ai_excel_processor/
├── app.py                # 主程序入口（前端界面与交互逻辑）
├── core/                 # 核心逻辑层
│   ├── __init__.py
│   ├── data_engine.py    # Excel读取、变量解析、结果回填
│   ├── ai_client.py      # AI API 调用、并发处理、重试机制
│   └── prompt_mgr.py     # Prompt 模板管理、占位符替换逻辑
├── config/               # 配置层
│   └── settings.py       # API Key、模型参数、合规词库配置
├── templates/            # 预设提示词库
│   └── medical_desc.txt  # 存放你那个复杂的生物医药 Prompt 模板
├── data/                 # 数据存放区
│   ├── input/            # 用户上传的原始表
│   └── output/           # 生成后的结果表
└── requirements.txt      # 项目依赖