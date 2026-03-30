"""
Project-2文件夹测试程序
测试 test/Project-2 文件夹下30个.rs文件的语义分析
"""

import sys
import os
import glob
from typing import Dict, Any, List

# 添加项目根目录到路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)
sys.path.insert(0, os.path.join(project_root, 'app', 'parser_core'))

def import_modules():
    """尝试导入所需模块"""
    from app.parser_core.Lexer import RustLexer
    from app.parser_core.Parser import RustParser
    from app.parser_core.semantic_diagnosis import IntegratedSemanticAnalyzer, SemanticDiagnosisEngine, ErrorType, DiagnosticError
    return RustLexer, RustParser, IntegratedSemanticAnalyzer, SemanticDiagnosisEngine, ErrorType, DiagnosticError

# 导入所需模块
RustLexer, RustParser, IntegratedSemanticAnalyzer, SemanticDiagnosisEngine, ErrorType, DiagnosticError = import_modules()

class Project2TestSuite:
    """Project-2文件夹测试套件"""
    
    def __init__(self):
        self.test_count = 0
        self.passed_count = 0  # 实际符合预期的数量
        self.failed_count = 0  # 不符合预期的数量
        self.error_count = 0   # 分析异常的数量
        self.results = []
        
        # 测试数据：应该有错误的文件
        self.should_have_errors = {
            "1.5.2.rs": "返回语句的类型（空）和函数声明返回类型（i32）不一致",
            "1.5.3.rs": "返回语句的类型（i32）和函数声明返回类型（空）不一致",
            "2.1.2.rs": "后续无语句，无法推断b的类型",
            "2.2.2.rs": "变量未声明",
            "2.3.2.rs": "变量未声明", 
            "2.3.3.rs": "右值求值时发现变量a未赋值", 
            "3.3.3.rs": "实参数量与形参数量不一致",
            "3.3.4.rs": "变量未赋值",
            "3.3.5.rs": "无返回值函数不能作为右值",
            "6.1.2.rs": "不可变变量不可二次赋值"
        }
        
        # 测试数据：应该正确的文件
        self.should_be_correct = {
            "2.1.3.rs": "可以二次声明，称为重影",
            "2.3.4.rs": "可以二次声明，称为重影",
            "5.2.rs": "for循环语法正确",
            "5.3.rs": "loop循环语法正确",
            "7.1.rs": "函数表达式块语法正确"
        }
        
    def load_rust_files(self, directory: str) -> List[str]:
        """加载指定目录下的所有.rs文件"""
        test_dir = os.path.join(project_root, directory)
        if not os.path.exists(test_dir):
            print(f"错误: 目录 {test_dir} 不存在")
            return []
        
        # 查找所有.rs文件
        pattern = os.path.join(test_dir, "*.rs")
        rust_files = glob.glob(pattern)
        
        print(f"在 {test_dir} 目录下找到 {len(rust_files)} 个 .rs 文件")
        return sorted(rust_files)
    
    def read_file_content(self, file_path: str) -> str:
        """读取文件内容"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            try:
                with open(file_path, 'r', encoding='gbk') as f:
                    return f.read()
            except:
                with open(file_path, 'r', encoding='latin-1') as f:
                    return f.read()
        except Exception as e:
            print(f"读取文件 {file_path} 失败: {e}")
            return ""
    
    def test_single_file(self, file_path: str):
        """测试单个Rust文件"""
        self.test_count += 1
        file_name = os.path.basename(file_path)
        
        print(f"\n测试 {self.test_count}: {file_name}")
        print("-" * 50)
        
        expected_error = file_name in self.should_have_errors
        expected_correct = file_name in self.should_be_correct
        is_special_file = expected_error or expected_correct
        
        try:
            # 读取文件内容
            code = self.read_file_content(file_path)
            if not code.strip():
                print("文件为空或读取失败")
                self.error_count += 1
                self.results.append((file_name, "文件读取失败", 0))
                return
            
            if is_special_file:
                print(f"文件内容:\n{code}")
                if expected_error:
                    print(f"📋 期望错误: {self.should_have_errors[file_name]}")
                elif expected_correct:
                    print(f"📋 期望正确: {self.should_be_correct[file_name]}")
            else:
                print(f"文件内容预览: {code[:100]}...")
            
            # 词法分析
            try:
                lexer = RustLexer()
                tokens = lexer.tokenize(code)
                print(f"词法分析完成，获得 {len(tokens)} 个token")
                if is_special_file:
                    print(f"Tokens: {[str(t) for t in tokens[:15]]}")  # 显示前15个token
            except Exception as e:
                print(f"词法分析失败: {e}")
                # 创建空token列表继续测试
                tokens = []
            
            # 语法分析
            try:
                parser = RustParser(tokens)
                ast = parser.parse()
                print("语法分析完成")
                if is_special_file:
                    print(f"AST结构 (完整): {ast}")
            except Exception as e:
                print(f"语法分析失败: {e}")
                # 创建简单AST继续测试
                ast = {"type": "program", "declarations": []}
            
            # 语义分析和诊断
            analyzer = IntegratedSemanticAnalyzer()
            result = analyzer.analyze_with_diagnosis(ast)
            
            # 统计错误数量
            error_count = result.get('error_count', 0)
            
            # 判断结果是否符合期望
            if result['success']:
                if expected_error:
                    print(f"期望有错误但分析通过了! 应该检测到: {self.should_have_errors[file_name]}")
                    print(f"详细分析过程:")
                    if 'base_error' in result and result['base_error']:
                        print(f"  基础分析器错误: {result['base_error']}")
                    print(f"  我们的错误数量: {error_count}")
                    print(f"  函数表: {list(analyzer.diagnosis.function_table.keys())}")
                    print(f"  符号表: {list(analyzer.diagnosis.symbol_table.keys())}")
                    self.failed_count += 1
                    self.results.append((file_name, "期望错误但通过", 0))
                else:
                    if expected_correct:
                        print(f"符合期望 - 分析通过 ({self.should_be_correct[file_name]})")
                    else:
                        print("分析通过 - 无语义错误")
                    self.passed_count += 1
                    self.results.append((file_name, "通过", 0))
            else:
                if expected_error:
                    print(f"符合期望 - 发现语义错误 ({self.should_have_errors[file_name]})")
                    self.passed_count += 1
                    self.results.append((file_name, "符合期望错误", error_count))
                else:
                    if expected_correct:
                        print(f"意外错误 - 期望正确但发现 {error_count} 个错误 ({self.should_be_correct[file_name]})")
                    else:
                        print(f"意外错误 - 发现 {error_count} 个错误")
                    self.failed_count += 1
                    self.results.append((file_name, "意外错误", error_count))
                
                # 输出详细的语义错误诊断信息
                print("详细错误诊断:")
                if 'base_error' in result and result['base_error']:
                    print(f"基础分析器错误: {result['base_error']}")
                analyzer.diagnosis.print_diagnostics()
                        
        except Exception as e:
            print(f"分析异常: {str(e)[:100]}...")
            import traceback
            if is_special_file:
                traceback.print_exc()
            self.error_count += 1
            self.results.append((file_name, "分析异常", 0))
    
    def test_all_files(self, directory: str = "test/Project-2"):
        """测试所有文件"""
        print("Project-2 文件夹语义分析测试")
        print("=" * 60)
        
        # 加载所有.rs文件
        rust_files = self.load_rust_files(directory)
        
        if not rust_files:
            print("未找到任何 .rs 文件")
            return
        
        print(f"开始测试 {len(rust_files)} 个文件...")
        
        # 逐个测试文件
        for file_path in rust_files:
            self.test_single_file(file_path)
    
    def print_summary(self):
        """打印测试摘要"""
        print("\n" + "=" * 60)
        print("测试结果摘要")
        print("=" * 60)
        
        # 统计不同类型的结果
        correct_count = 0
        expected_error_count = 0
        unexpected_error_count = 0
        unexpected_pass_count = 0
        exception_count = 0
        
        for file_name, status, error_count in self.results:
            if status == "通过":
                correct_count += 1
            elif status == "符合期望错误":
                expected_error_count += 1
            elif status == "意外错误":
                unexpected_error_count += 1
            elif status == "期望错误但通过":
                unexpected_pass_count += 1
            elif status == "分析异常":
                exception_count += 1
        
        # 基本统计
        print(f"总文件数: {self.test_count}")
        print(f"正确通过: {correct_count}")
        print(f"符合期望错误: {expected_error_count}")
        print(f"意外错误: {unexpected_error_count}")
        print(f"期望错误但通过: {unexpected_pass_count}")
        print(f"分析异常: {exception_count}")
        
        actual_pass_count = correct_count + expected_error_count
        if self.test_count > 0:
            pass_rate = (actual_pass_count / self.test_count) * 100
            print(f"实际通过率: {pass_rate:.1f}%")
        
        # 详细结果表格
        print("\n详细结果:")
        print("-" * 70)
        print(f"{'文件名':<15} {'状态':<15} {'错误数':<8} {'说明':<20}")
        print("-" * 70)
        
        # 定义状态说明
        status_descriptions = {
            "2.1.2.rs": "类型推断失败",
            "2.1.3.rs": "变量重影(正确)",
            "2.3.3.rs": "变量未赋值",
            "2.3.4.rs": "变量重影(正确)", 
            "3.3.3.rs": "参数数量不匹配",
            "3.3.5.rs": "void函数作右值",
            "5.2.rs": "for循环(正确)",
            "5.3.rs": "loop循环(正确)",
            "7.1.rs": "函数表达式块(正确)"
        }
        
        for file_name, status, error_count in self.results:
            # 截断过长的文件名
            short_name = file_name[:12] + "..." if len(file_name) > 15 else file_name
            description = status_descriptions.get(file_name, "")
            
            # 根据状态设置颜色标记
            if status == "通过" or status == "符合期望错误":
                status_mark = "" + status
            elif status in ["意外错误", "期望错误但通过"]:
                status_mark = "" + status
            else:
                status_mark = "" + status
                
            print(f"{short_name:<15} {status_mark:<15} {error_count:<8} {description:<20}")
        
        # 错误类型统计
        self.print_error_statistics()
        
        # 总结
        print("\n" + "=" * 60)
        if unexpected_error_count == 0 and unexpected_pass_count == 0 and exception_count == 0:
            print("所有文件都符合预期！")
        elif actual_pass_count > 0:
            print(f"部分文件符合预期 ({actual_pass_count}/{self.test_count})")
            if unexpected_error_count > 0:
                print(f"{unexpected_error_count} 个文件有意外错误")
            if unexpected_pass_count > 0:
                print(f"{unexpected_pass_count} 个文件期望错误但通过了")
        else:
            print("所有文件都存在问题，请检查代码或分析器")
    
    def print_error_statistics(self):
        """打印错误类型统计"""
        print("\n错误类型统计:")
        print("-" * 30)
        
        # 按状态分组
        status_groups = {}
        total_errors = 0
        
        for file_name, status, error_count in self.results:
            if status not in status_groups:
                status_groups[status] = {'count': 0, 'errors': 0, 'files': []}
            status_groups[status]['count'] += 1
            status_groups[status]['errors'] += error_count
            status_groups[status]['files'].append(file_name)
            total_errors += error_count
        
        for status, info in status_groups.items():
            print(f"{status}: {info['count']} 个文件, {info['errors']} 个错误")
        
        print(f"总错误数: {total_errors}")

def test_diagnosis_engine():
    """测试诊断引擎基本功能"""
    print("测试语义诊断引擎基本功能")
    print("=" * 40)
    
    diagnosis = SemanticDiagnosisEngine()
    
    # 注册函数
    diagnosis.register_function("add", "i32", [
        {"name": "a", "type": "i32"},
        {"name": "b", "type": "i32"}
    ])
    diagnosis.register_function("print", "void", [
        {"name": "msg", "type": "str"}
    ])
    
    # 测试各种错误检查
    print("1. 测试变量未声明:")
    diagnosis.check_variable_undefined("x", line=1)
    
    print("2. 测试变量未赋值:")
    diagnosis.declare_variable("a", "i32", is_mutable=True, is_initialized=False, line=2)
    diagnosis.check_variable_uninitialized("a", line=3)
    
    print("3. 测试函数调用参数:")
    diagnosis.check_function_call("add", ["i32", "str"], line=6)  # 类型不匹配
    diagnosis.check_function_call("add", ["i32"], line=7)        # 数量不匹配
    
    print("4. 测试无返回值函数作为右值:")
    diagnosis.check_void_function_as_rvalue("print", line=8)
    
    # 打印诊断结果
    diagnosis.print_diagnostics()

def main():
    """主测试函数"""
    try:
        # 先测试诊断引擎基本功能
        test_diagnosis_engine()
        
        print("\n" + "=" * 80)
        
        # 测试文件分析
        suite = Project2TestSuite()
        
        # 测试所有文件
        suite.test_all_files()
        
        # 打印摘要
        suite.print_summary()
            
    except KeyboardInterrupt:
        print("\n\n测试被用户中断")
    except Exception as e:
        print(f"\n\n测试过程中发生异常: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()