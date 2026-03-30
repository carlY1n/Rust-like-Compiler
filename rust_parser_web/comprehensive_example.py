"""
类Rust语言增强语义分析器综合示例（修复版）
展示高级语言特性的语义检查和中间代码生成
"""

import sys
import os

# 添加项目路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    from app.parser_core.enhanced_analyzer import analyze_code_enhanced, analyze_code_with_full_report
    from app.parser_core.analyzer_config import AnalyzerConfig, PredefinedConfigs, OptimizationLevel
    print("模块导入成功")
except ImportError as e:
    print(f"模块导入失败: {e}")
    print("请确保所有文件都在正确位置")
    sys.exit(1)

def format_quadruple(quad):
    """格式化四元式输出，兼容字典和对象格式"""
    if isinstance(quad, dict):
        return f"({quad['op']}, {quad['arg1']}, {quad['arg2']}, {quad['result']})"
    else:
        # Quadruple对象
        return f"({quad.op}, {quad.arg1}, {quad.arg2}, {quad.result})"

def test_basic_features():
    """测试基本语言特性"""
    print("=== 测试基本语言特性 ===\n")
    
    code = """
    fn main() -> i32 {
        let x: i32 = 10;
        let mut y: i32 = 20;
        let z = x + y;
        
        if z > 25 {
            y = y + 1;
        }
        
        return z;
    }
    """
    
    result = analyze_code_enhanced(code)
    print("函数数量:", len(result.quadruples))
    print("警告数量:", len(result.warnings))
    print("错误数量:", len(result.errors))
    
    if result.quadruples.get("main"):
        print("\n主函数四元式代码:")
        for i, quad in enumerate(result.quadruples["main"]):
            print(f"  {i:2d}: {format_quadruple(quad)}")

def test_advanced_type_checking():
    """测试高级类型检查"""
    print("\n=== 测试高级类型检查 ===\n")
    
    code = """
    fn calculate(x: i32, y: i32) -> i32 {
        let result = x * y + 10;
        return result;
    }
    
    fn main() -> i32 {
        let a: i32 = 5;
        let b: i32 = 3;
        let sum = calculate(a, b);
        
        return sum;
    }
    """
    
    result = analyze_code_enhanced(code, enable_optimization=True)
    
    print("类型表:")
    for type_name, type_info in result.type_table.items():
        print(f"  {type_name}: {type_info}")
    
    if result.warnings:
        print("\n警告:")
        for warning in result.warnings:
            print(f"  - {warning['message']} (类型: {warning['type']})")

def test_optimization_features():
    """测试代码优化功能"""
    print("\n=== 测试代码优化功能 ===\n")
    
    code = """
    fn compute() -> i32 {
        let a = 5;
        let b = 10;
        let c = a + b * 2;  // 常量折叠: 5 + 10 * 2 = 25
        let d = c + 0;      // 代数简化: c + 0 = c
        let e = d * 1;      // 代数简化: d * 1 = d
        
        return e;
    }
    
    fn dead_code_example() -> i32 {
        let x = 42;
        return x;
        let y = 100;  // 死代码
        return y;     // 死代码
    }
    
    fn main() -> i32 {
        return compute();
    }
    """
    
    # 不启用优化
    result_no_opt = analyze_code_enhanced(code, enable_optimization=False)
    
    # 启用优化
    result_with_opt = analyze_code_enhanced(code, enable_optimization=True)
    
    print("未优化的四元式数量:")
    for func, quads in result_no_opt.quadruples.items():
        print(f"  {func}: {len(quads)} 条")
    
    print("\n优化后的四元式数量:")
    for func, quads in result_with_opt.quadruples.items():
        print(f"  {func}: {len(quads)} 条")
    
    print("\n优化报告:")
    if result_with_opt.optimization_report:
        opt_report = result_with_opt.optimization_report
        for key, value in opt_report.items():
            print(f"  {key}: {value}")
    else:
        print("  优化报告不可用")

def test_warning_system():
    """测试警告系统"""
    print("\n=== 测试警告系统 ===\n")
    
    code = """
    fn unused_function() -> i32 {
        return 42;
    }
    
    fn warning_demo() -> i32 {
        let unused_var = 10;        // 未使用变量警告
        let mut x = 5;
        let y = 15;
        
        // 使用x但不使用unused_var
        x = x + 1;
        
        return x;
    }
    
    fn main() -> i32 {
        let result = warning_demo();
        return result;
    }
    """
    
    result = analyze_code_enhanced(code, enable_warnings=True)
    
    print("检测到的警告:")
    for warning in result.warnings:
        line_info = f" (第{warning['line']}行)" if warning.get('line') else ""
        print(f"  [{warning['type']}] {warning['message']}{line_info}")

def test_loop_constructs():
    """测试循环结构"""
    print("\n=== 测试循环结构 ===\n")
    
    code = """
    fn loop_examples() -> i32 {
        let mut sum = 0;
        let mut i = 0;
        
        // while循环
        while i < 10 {
            sum = sum + i;
            i = i + 1;
        }
        
        return sum;
    }
    
    fn main() -> i32 {
        return loop_examples();
    }
    """
    
    result = analyze_code_enhanced(code)
    
    print("循环相关的四元式:")
    if result.quadruples.get("loop_examples"):
        quads = result.quadruples["loop_examples"]
        for i, quad in enumerate(quads):
            # 兼容处理四元式格式
            if isinstance(quad, dict):
                op = quad['op']
                if op in ['label', 'if_false', 'goto']:
                    print(f"  {i:2d}: {format_quadruple(quad)}")
            else:
                if quad.op in ['label', 'if_false', 'goto']:
                    print(f"  {i:2d}: {format_quadruple(quad)}")

def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===\n")
    
    error_code = """
    fn error_demo() -> i32 {
        let x = undefined_var;  // 未定义变量错误
        let immutable = 10;
        immutable = 20;         // 不可变变量赋值错误
        
        return x;
    }
    
    fn type_error() -> i32 {
        let a: i32 = 10;
        let b: i32 = 20;
        return a + b;
    }
    """
    
    result = analyze_code_enhanced(error_code)
    
    print("检测到的错误:")
    for error in result.errors:
        print(f"  - {error}")

def test_symbol_table():
    """测试符号表分析"""
    print("\n=== 测试符号表分析 ===\n")
    
    code = """
    fn outer_function(param1: i32, param2: i32) -> i32 {
        let local_var = param1 + param2;
        
        if local_var > 10 {
            let inner_var = local_var * 2;
            local_var = inner_var;
        }
        
        return local_var;
    }
    
    fn main() -> i32 {
        let result = outer_function(5, 7);
        return result;
    }
    """
    
    result = analyze_code_enhanced(code)
    
    def print_scope(scope_info, indent=0):
        """递归打印作用域信息"""
        prefix = "  " * indent
        print(f"{prefix}作用域 (级别 {scope_info['level']}, 类型: {scope_info['type']}):")
        
        for name, symbol in scope_info['symbols'].items():
            print(f"{prefix}  {name}: {symbol['type']} ({symbol['data_type']})")
            if symbol.get('declaration_line'):
                print(f"{prefix}    声明行: {symbol['declaration_line']}")
        
        for child in scope_info.get('children', []):
            print_scope(child, indent + 1)
    
    print("符号表结构:")
    if result.symbol_table:
        print_scope(result.symbol_table)
    else:
        print("  符号表不可用")

def comprehensive_demo():
    """综合演示"""
    print("\n=== 类Rust语言增强语义分析器综合演示 ===\n")
    
    # 复杂示例代码
    complex_code = """
    fn fibonacci(n: i32) -> i32 {
        if n <= 1 {
            return n;
        }
        
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
    
    fn array_sum() -> i32 {
        let mut sum = 0;
        let mut i = 0;
        
        while i < 10 {
            sum = sum + i * i;
            i = i + 1;
        }
        
        return sum;
    }
    
    fn main() -> i32 {
        let fib_result = fibonacci(8);
        let sum_result = array_sum();
        let total = fib_result + sum_result;
        
        if total > 100 {
            return total;
        } else {
            return 0;
        }
    }
    
    fn unused_complex_function(x: i32, y: i32) -> i32 {
        let temp1 = x * 2;
        let temp2 = y + 5;
        let unused_var = temp1 - temp2;  // 未使用变量
        
        return temp1 + temp2;
    }
    """
    
    # 使用不同配置进行分析
    configs = {
        "默认配置": AnalyzerConfig(),
        "严格模式": PredefinedConfigs.strict_config(),
        "教育模式": PredefinedConfigs.educational_config(),
    }
    
    for config_name, config in configs.items():
        print(f"\n--- {config_name} ---")
        
        if config_name == "严格模式":
            config.enable_optimization = True
            config.optimization_level = OptimizationLevel.AGGRESSIVE
        
        result = analyze_code_enhanced(complex_code, 
                                     enable_optimization=config.enable_optimization,
                                     enable_warnings=config.enable_warnings)
        
        print(f"函数数量: {len(result.quadruples)}")
        print(f"总四元式: {result.analysis_summary.get('total_quadruples', 0)}")
        print(f"警告数量: {len(result.warnings)}")
        print(f"错误数量: {len(result.errors)}")
        print(f"常量数量: {len(result.constant_table)}")
        
        if result.warnings:
            print("主要警告:")
            for warning in result.warnings[:3]:  # 只显示前3个
                print(f"  - {warning['message']}")
    
    # 生成完整报告
    print("\n" + "="*50)
    print("完整分析报告:")
    print("="*50)
    
    try:
        output_dir = os.path.join(project_root, "output")
        report = analyze_code_with_full_report(complex_code, output_dir)
        
        # 只显示报告的前20行，避免输出过长
        lines = report.split('\n')
        for line in lines[:20]:
            print(line)
        
        if len(lines) > 20:
            print("... (完整报告已保存到 output/ 目录)")
            print(f"总共 {len(lines)} 行报告")
        
    except Exception as e:
        print(f"生成报告时出错: {e}")

def main():
    """主函数"""
    print("🚀 开始运行综合示例")
    print("=" * 60)
    
    try:
        # 运行所有测试
        test_basic_features()
        test_advanced_type_checking()
        test_optimization_features()
        test_warning_system()
        test_loop_constructs()
        test_error_handling()
        test_symbol_table()
        
        # 最后运行综合演示
        comprehensive_demo()
        
        print("\n" + "=" * 60)
        print("所有示例运行完成！")
        print("\n生成的文件:")
        output_dir = os.path.join(project_root, "output")
        if os.path.exists(output_dir):
            for file in os.listdir(output_dir):
                print(f"  - {os.path.join(output_dir, file)}")
        
    except Exception as e:
        print(f"\n运行过程中出现错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()