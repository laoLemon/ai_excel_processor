import re
def process_records(records, template):
    """
    输入: records (list[dict])
    输入: template (Prompt模板)
    输出: 一个包含所有生成 Prompt 的列表
    """
    final_prompts = []

    # 1. 预先提取模板中所有 {变量名}
    # 正则表达式解释：寻找被 {} 包裹的任何内容
    variables = re.findall(r'\{(.*?)\}', template)

    for row_dict in records:
        current_prompt = template

        for var in variables:
            # 2. 核心兼容逻辑
            # 我们把 row_dict 里的 key 全部转为字符串来匹配
            # 这样无论 Excel 里是数字 1483 还是字符串 "1483" 都能匹配上

            # 尝试直接获取（支持字符串和数字作为 key）
            val = row_dict.get(var)

            # 如果没找到（可能是因为 var 是字符串 "1483" 但字典 key 是数字 1483）
            if val is None:
                try:
                    # 尝试把变量名转成数字去匹配
                    val = row_dict.get(int(var))
                except ValueError:
                    val = None

            # 如果最后还是找不到，就填空字符串，避免显示 {变量名}
            val_str = str(val) if val is not None else ""

            # 3. 执行替换
            current_prompt = current_prompt.replace(f"{{{var}}}", val_str)

        final_prompts.append(current_prompt)

    return final_prompts