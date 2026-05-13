import time
from openai import OpenAI
from concurrent.futures import ThreadPoolExecutor

class AIClient:
    def __init__(self, api_key, model="gpt-4o-mini"):
        # 记录配置，而不是直接把对象丢进线程
        self.api_key = api_key
        self.model = model
        # 在主线程初始化一个 client 供单次测试使用
        self.client = OpenAI(api_key=self.api_key)

    def generate(self, prompt, timeout=60):
        """
        单条生成：为了线程安全，我们在函数内部确保使用正确的 client
        """
        try:
            # 使用标准的 2026 Responses API 语法
            response = self.client.responses.create(
                model=self.model,
                tools=[{"type": "web_search_preview"}],
                input=prompt,
                timeout=timeout
            )
            return response.output_text.strip()
        except Exception as e:
            return f"Error: {str(e)}"

    def batch_generate(self, prompts, max_workers=10):
        print(f"🚀 开始并发处理，共 {len(prompts)} 条数据...")
        start_time = time.time()

        # 重点：在 Jupyter/多线程环境下，直接传 self.generate 最稳妥
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # 放弃 lambda，直接绑定方法引用
            results = list(executor.map(self.generate, prompts))

        end_time = time.time()
        print(f"✅ 完成！总耗时: {end_time - start_time:.2f} 秒")
        return results