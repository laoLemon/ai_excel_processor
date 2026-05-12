import pandas as pd
import os


class DataEngine:
    def __init__(self):
        self.df = None
        self.file_path = None

    def load_file(self, file_path):
        """支持 Excel 和 CSV，返回是否加载成功"""
        try:
            ext = os.path.splitext(file_path)[-1].lower()
            if ext == '.csv':
                # 尝试多种编码读取 CSV
                try:
                    self.df = pd.read_csv(file_path, encoding='utf-8')
                except:
                    self.df = pd.read_csv(file_path, encoding='gbk')
            elif ext in ['.xlsx', '.xls']:
                self.df = pd.read_excel(file_path)
            # 【新增这一行】强制把列名都变成字符串
            self.df.columns = [str(c) for c in self.df.columns]

            # 清洗：将所有 NaN 替换为空字符串，防止 Prompt 出现 "nan" 字样
            self.df = self.df.fillna("")
            self.file_path = file_path
            return True
        except Exception as e:
            print(f"读取文件失败: {e}")
            return False

    def get_all_records(self):
        """一次性返回所有行的字典列表，适合批量处理"""
        if self.df is not None:
            # orient='records' 会直接生成 [{列1:值, 列2:值}, {...}] 的结构
            return self.df.to_dict(orient='records')
        return []

    def get_column_names(self):
        """获取 Excel 中所有的列名"""
        if self.df is not None:
            return self.df.columns.tolist()
        return []

    def get_row_data(self, index):
        """获取指定行的数据，并转为字典（Key 是列名，Value 是内容）"""
        if self.df is not None and index < len(self.df):
            return self.df.iloc[index].to_dict()
        return None

    def save_result(self, results, output_column="AI_Result"):
        """将 AI 生成的列表写回 DataFrame 并保存"""
        self.df[output_column] = results
        output_path = f"processed_{os.path.basename(self.file_path)}"
        self.df.to_excel(output_path, index=False)
        return output_path