import sys
import os
import json

# 添加项目路径到Python路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

try:
    # 导入增强分析器
    from app.parser_core.enhanced_analyzer import analyze_code_enhanced, analyze_code_with_full_report
    from app.parser_core.analyzer_config import AnalyzerConfig, PredefinedConfigs
    
    # 导入原始分析器进行对比
    from app.parser_core.analyzer import analyze_code
    
    print("所有模块导入成功！")
    
except ImportError as e:
    print(f"模块导入失败: {e}")
    print("请确保所有文件都放在正确的位置")
    sys.exit(1)

def test_basic_functionality():
    """测试基本功能"""
    print("\n=== 测试基本功能 ===")
    
    test_code = """
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
    
    try:
        result = analyze_code_enhanced(test_code)
        print("增强分析器运行成功")
        print(f"   - 函数数量: {len(result.quadruples)}")
        print(f"   - 警告数量: {len(result.warnings)}")
        print(f"   - 错误数量: {len(result.errors)}")
        
        if result.warnings:
            print("   - 警告列表:")
            for warning in result.warnings:
                print(f"     * {warning['message']}")
        
        return True
    except Exception as e:
        print(f"增强分析器运行失败: {e}")
        return False

def test_optimization():
    """测试优化功能"""
    print("\n=== 测试优化功能 ===")
    
    test_code = """
    fn test_optimization() -> i32 {
        let a = 5;
        let b = 10;
        let c = a + b * 2;  // 应该被优化为 5 + 20 = 25
        let d = c + 0;      // 应该被优化为 c
        let e = d * 1;      // 应该被优化为 d
        
        return e;
    }
    """
    
    try:
        # 不启用优化
        result_no_opt = analyze_code_enhanced(test_code, enable_optimization=False)
        
        # 启用优化
        result_with_opt = analyze_code_enhanced(test_code, enable_optimization=True)
        
        print("优化测试成功")
        
        if "test_optimization" in result_no_opt.quadruples:
            no_opt_count = len(result_no_opt.quadruples["test_optimization"])
            print(f"   - 未优化四元式数量: {no_opt_count}")
        
        if "test_optimization" in result_with_opt.quadruples:
            opt_count = len(result_with_opt.quadruples["test_optimization"])
            print(f"   - 优化后四元式数量: {opt_count}")
        
        if result_with_opt.optimization_report:
            print("   - 优化报告:")
            for key, value in result_with_opt.optimization_report.items():
                print(f"     * {key}: {value}")
        
        return True
    except Exception as e:
        print(f"优化测试失败: {e}")
        return False

def test_warnings():
    """测试警告系统"""
    print("\n=== 测试警告系统 ===")
    
    test_code = """
    fn unused_function() -> i32 {
        return 42;
    }
    
    fn warning_demo() -> i32 {
        let unused_var = 10;        // 应该产生未使用变量警告
        let mut x = 5;
        let y = 15;
        
        x = x + 1;                  // 使用x但不使用unused_var
        
        return x;
    }
    
    fn main() -> i32 {
        let result = warning_demo();
        return result;
    }
    """
    
    try:
        result = analyze_code_enhanced(test_code, enable_warnings=True)
        print("警告系统测试成功")
        print(f"   - 检测到 {len(result.warnings)} 个警告")
        
        for warning in result.warnings:
            print(f"     * [{warning['type']}] {warning['message']}")
        
        return True
    except Exception as e:
        print(f"警告系统测试失败: {e}")
        return False

def test_error_handling():
    """测试错误处理"""
    print("\n=== 测试错误处理 ===")
    
    error_code = """
    fn error_demo() -> i32 {
        let x = undefined_var;      // 未定义变量错误
        let immutable = 10;
        immutable = 20;             // 不可变变量赋值错误
        
        return x;
    }
    """
    
    try:
        result = analyze_code_enhanced(error_code)
        print("错误处理测试成功")
        print(f"   - 检测到 {len(result.errors)} 个错误")
        
        for error in result.errors:
            print(f"     * {error}")
        
        return True
    except Exception as e:
        print(f"错误处理测试失败: {e}")
        return False

def test_configurations():
    """测试配置系统"""
    print("\n=== 测试配置系统 ===")
    
    test_code = """
    fn config_test() -> i32 {
        let unused = 42;
        let x = 10;
        return x;
    }
    """
    
    try:
        # 测试不同配置
        configs = {
            "默认配置": AnalyzerConfig(),
            "严格模式": PredefinedConfigs.strict_config(),
            "宽松模式": PredefinedConfigs.permissive_config(),
        }
        
        for config_name, config in configs.items():
            result = analyze_code_enhanced(test_code, 
                                         enable_optimization=config.enable_optimization,
                                         enable_warnings=config.enable_warnings)
            print(f"   - {config_name}: {len(result.warnings)} 个警告")
        
        print("配置系统测试成功")
        return True
    except Exception as e:
        print(f"配置系统测试失败: {e}")
        return False

def compare_with_original():
    """与原始分析器对比"""
    print("\n=== 与原始分析器对比 ===")
    
    test_code = """
    fn main() -> i32 {
        let x: i32 = 10;
        let y: i32 = 20;
        let z = x + y;
        return z;
    }
    """
    
    try:
        # 原始分析器
        original_result = analyze_code(test_code)
        
        # 增强分析器
        enhanced_result = analyze_code_enhanced(test_code)
        
        print("对比测试成功")
        print("   原始分析器:")
        print(f"     - 函数数量: {len(original_result.get('quadruples', {}))}")
        print(f"     - 是否有错误: {'是' if original_result.get('error') else '否'}")
        
        print("   增强分析器:")
        print(f"     - 函数数量: {len(enhanced_result.quadruples)}")
        print(f"     - 警告数量: {len(enhanced_result.warnings)}")
        print(f"     - 错误数量: {len(enhanced_result.errors)}")
        print(f"     - 优化功能: {'启用' if enhanced_result.optimization_report else '未启用'}")
        
        return True
    except Exception as e:
        print(f"对比测试失败: {e}")
        return False

def generate_full_report():
    """生成完整报告"""
    print("\n=== 生成完整分析报告 ===")
    
    complex_code = """
    fn fibonacci(n: i32) -> i32 {
        if n <= 1 {
            return n;
        }
        
        return fibonacci(n - 1) + fibonacci(n - 2);
    }
    
    fn main() -> i32 {
        let result = fibonacci(8);
        let unused_var = 100;  // 未使用变量
        return result;
    }
    
    fn unused_function() -> i32 {  // 未使用函数
        return 42;
    }
    """
    
    try:
        # 生成完整报告
        output_dir = os.path.join(project_root, "output")
        report = analyze_code_with_full_report(complex_code, output_dir)
        
        print("完整报告生成成功")
        print(f"   - 报告已保存到: {output_dir}")
        print("   - 报告预览:")
        
        # 显示报告的前几行
        lines = report.split('\n')
        for line in lines[:15]:
            print(f"     {line}")
        
        if len(lines) > 15:
            print("     ... (报告内容较长，已截断)")
        
        return True
    except Exception as e:
        print(f"报告生成失败: {e}")
        return False

def create_sample_config():
    """创建示例配置文件"""
    print("\n=== 创建示例配置文件 ===")
    
    try:
        config = PredefinedConfigs.educational_config()
        
        # 转换为字典以便序列化
        config_dict = {
            "enable_warnings": config.enable_warnings,
            "enable_optimization": config.enable_optimization,
            "optimization_level": config.optimization_level.name,
            "strict_type_checking": config.strict_type_checking,
            "warn_unused_variables": config.warn_unused_variables,
            "warn_type_mismatch": config.warn_type_mismatch,
            "enable_constant_folding": config.enable_constant_folding,
            "enable_dead_code_elimination": config.enable_dead_code_elimination,
        }
        
        config_path = os.path.join(project_root, "config_example.json")
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump(config_dict, f, indent=2, ensure_ascii=False)
        
        print(f"示例配置文件创建成功: {config_path}")
        return True
    except Exception as e:
        print(f"配置文件创建失败: {e}")
        return False

def main():
    """主测试函数"""
    print("开始测试增强语义分析器")
    print("=" * 50)
    
    # 运行所有测试
    tests = [
        test_basic_functionality,
        test_optimization,
        test_warnings,
        test_error_handling,
        test_configurations,
        compare_with_original,
        generate_full_report,
        create_sample_config,
    ]
    
    passed = 0
    total = len(tests)
    
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"测试 {test.__name__} 发生异常: {e}")
    
    print("\n" + "=" * 50)
    print(f"测试完成: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("所有测试都通过了！增强语义分析器工作正常。")
        print("\n后续步骤:")
        print("1. 查看 output/ 目录中的分析结果")
        print("2. 阅读 高级语言特性实现文档.md")
        print("3. 尝试修改 config_example.json 并重新运行")
        print("4. 运行 python comprehensive_example.py 查看更多示例")
    else:
        print(f"  有 {total - passed} 个测试失败，请检查错误信息")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)