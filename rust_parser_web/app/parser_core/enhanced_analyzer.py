from .Lexer import RustLexer
from .Parser import RustParser
from .enhanced_semantic_analyzer import EnhancedSemanticAnalyzer, SemanticError
import json
import os
from typing import Dict, Any, List
from .enhanced_code_generator import EnhancedCodeGenerator
from .target_code_config import CodeGeneratorConfig, PredefinedCodeGenConfigs

class CodeAnalysisResult:
    """代码分析结果类"""
    def __init__(self):
        self.tokens: List[str] = []
        self.ast: Dict[str, Any] = {}
        self.quadruples: Dict[str, List[Dict]] = {}
        self.warnings: List[Dict] = []
        self.errors: List[str] = []
        self.symbol_table: Dict[str, Any] = {}
        self.type_table: Dict[str, str] = {}
        self.constant_table: Dict[str, Any] = {}
        self.analysis_summary: Dict[str, Any] = {}
        self.optimization_report: Dict[str, Any] = {}
        self.target_code: str = ""
        self.codegen_statistics: Dict[str, Any] = {}

def save_analysis_results(results: CodeAnalysisResult, output_dir: str):
    """保存分析结果到文件"""
    os.makedirs(output_dir, exist_ok=True)
    
    # 保存各种分析结果
    files_to_save = {
        'ast.json': results.ast,
        'quadruples.json': results.quadruples,
        'warnings.json': results.warnings,
        'symbol_table.json': results.symbol_table,
        'type_table.json': results.type_table,
        'constant_table.json': results.constant_table,
        'analysis_summary.json': results.analysis_summary
    }
    
    for filename, data in files_to_save.items():
        filepath = os.path.join(output_dir, filename)
        with open(filepath, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

def analyze_code_enhanced(code: str, enable_optimization: bool = True, 
                         enable_warnings: bool = True) -> CodeAnalysisResult:
    """
    增强的代码分析函数
    
    Args:
        code: 源代码字符串
        enable_optimization: 是否启用代码优化
        enable_warnings: 是否启用警告检查
    
    Returns:
        CodeAnalysisResult: 包含所有分析结果的对象
    """
    result = CodeAnalysisResult()
    
    try:
        # 1. 词法分析
        lexer = RustLexer()
        tokens = lexer.tokenize(code)
        
        result.tokens = [
            f'{i}: [{t[0]}] "{t[1]}" at line {t[2]}, position {t[3]}'
            for i, t in enumerate(tokens)
        ]
        
        # 2. 语法分析
        parser = RustParser(tokens)
        result.ast = parser.parse()
        
        # 3. 增强语义分析
        semantic_analyzer = EnhancedSemanticAnalyzer()
        semantic_analyzer.optimization_enabled = enable_optimization
        
        analysis_results = semantic_analyzer.analyze(result.ast)
        
        # 提取分析结果
        serializable_quads = {}
        for func_name, quads in analysis_results["function_blocks"].items():
            serializable_quads[func_name] = []
            for quad in quads:
                if hasattr(quad, 'op'):  # Quadruple对象
                    serializable_quads[func_name].append({
                        "op": quad.op,
                        "arg1": quad.arg1,
                        "arg2": quad.arg2,
                        "result": quad.result
                    })
                else:  # 已经是字典格式
                    serializable_quads[func_name].append(quad)
        
        result.quadruples = serializable_quads
        result.warnings = analysis_results["warnings"] if enable_warnings else []
        result.type_table = analysis_results["type_table"]
        result.constant_table = analysis_results["constant_table"]
        
        # 4. 生成符号表报告
        result.symbol_table = semantic_analyzer.generate_symbol_table_report()
        
        # 5. 生成分析摘要
        result.analysis_summary = semantic_analyzer.get_analysis_summary()
        
        # 6. 额外的语义规则检查
        semantic_errors = semantic_analyzer.check_semantic_rules()
        result.errors.extend(semantic_errors)
        
        # 7. 优化报告
        if enable_optimization:
            result.optimization_report = {
                "constant_propagation": len(result.constant_table) > 0,
                "dead_code_elimination": semantic_analyzer.dead_code_elimination,
                "algebraic_simplification": True,
                "total_optimizations": _count_optimizations(result.quadruples)
            }
        
        return result
        
    except SyntaxError as e:
        result.errors.append(f"Syntax error: {str(e)}")
        return result
    except SemanticError as e:
        result.errors.append(f"Semantic error: {str(e)}")
        return result
    except Exception as e:
        result.errors.append(f"Unexpected error: {str(e)}")
        return result

def _count_optimizations(quadruples: Dict[str, List[Dict]]) -> int:
    """统计优化次数（简化实现）"""
    optimization_count = 0
    
    for func_name, quads in quadruples.items():
        for quad in quads:
            # 检查是否有优化痕迹（例如常量折叠后的赋值）
            if (quad.get("op") == "=" and 
                quad.get("arg1", "").isdigit() and 
                quad.get("arg2") == "_"):
                optimization_count += 1
                
    return optimization_count

def compare_with_basic_analyzer(code: str) -> Dict[str, Any]:
    """
    比较增强分析器与基础分析器的差异
    """
    # 使用增强分析器
    enhanced_result = analyze_code_enhanced(code)
    
    # 使用基础分析器（假设存在）
    try:
        from .semantic_analyzer import SemanticAnalyzer
        basic_analyzer = SemanticAnalyzer()
        lexer = RustLexer()
        parser = RustParser(lexer.tokenize(code))
        ast = parser.parse()
        basic_quads = basic_analyzer.analyze(ast)
        
        comparison = {
            "enhanced_functions": len(enhanced_result.quadruples),
            "basic_functions": len(basic_quads),
            "enhanced_warnings": len(enhanced_result.warnings),
            "basic_warnings": 0,  # 基础版本没有警告系统
            "enhanced_optimizations": enhanced_result.optimization_report.get("total_optimizations", 0),
            "basic_optimizations": 0,  # 基础版本没有优化
            "features_added": [
                "Type checking",
                "Constant folding",
                "Dead code elimination",
                "Unused variable detection",
                "Enhanced error reporting",
                "Symbol table analysis",
                "Code optimization"
            ]
        }
        
        return comparison
        
    except ImportError:
        return {"error": "Basic analyzer not available for comparison"}

def generate_analysis_report(result: CodeAnalysisResult) -> str:
    """生成人类可读的分析报告"""
    report_lines = []
    
    # 标题
    report_lines.append("=== 类Rust语言增强语义分析报告 ===\n")
    
    # 分析摘要
    summary = result.analysis_summary
    report_lines.append(f"函数总数: {summary.get('total_functions', 0)}")
    report_lines.append(f"四元式总数: {summary.get('total_quadruples', 0)}")
    report_lines.append(f"错误数: {len(result.errors)}")
    report_lines.append(f"警告数: {len(result.warnings)}")
    report_lines.append(f"常量数: {summary.get('constants_found', 0)}")
    report_lines.append("")
    
    # 错误报告
    if result.errors:
        report_lines.append("=== 错误列表 ===")
        for i, error in enumerate(result.errors, 1):
            report_lines.append(f"{i}. {error}")
        report_lines.append("")
    
    # 警告报告
    if result.warnings:
        report_lines.append("=== 警告列表 ===")
        for i, warning in enumerate(result.warnings, 1):
            line_info = f" (Line {warning['line']})" if warning.get('line') else ""
            report_lines.append(f"{i}. [{warning['type']}] {warning['message']}{line_info}")
        report_lines.append("")
    
    # 类型表
    if result.type_table:
        report_lines.append("=== 类型表 ===")
        for type_name, type_info in result.type_table.items():
            report_lines.append(f"{type_name}: {type_info}")
        report_lines.append("")
    
    # 常量表
    if result.constant_table:
        report_lines.append("=== 常量表 ===")
        for const_name, const_value in result.constant_table.items():
            report_lines.append(f"{const_name} = {const_value}")
        report_lines.append("")
    
    # 优化报告
    if result.optimization_report:
        report_lines.append("=== 优化报告 ===")
        opt_report = result.optimization_report
        report_lines.append(f"常量传播: {'启用' if opt_report.get('constant_propagation') else '未启用'}")
        report_lines.append(f"死代码消除: {'启用' if opt_report.get('dead_code_elimination') else '未启用'}")
        report_lines.append(f"代数简化: {'启用' if opt_report.get('algebraic_simplification') else '未启用'}")
        report_lines.append(f"优化次数: {opt_report.get('total_optimizations', 0)}")
        report_lines.append("")
    
    # 四元式代码
    if result.quadruples:
        report_lines.append("=== 中间代码 (四元式) ===")
        for func_name, quads in result.quadruples.items():
            report_lines.append(f"\n--- 函数 {func_name} ---")
            for i, quad in enumerate(quads):
                op = quad.get('op', '')
                arg1 = quad.get('arg1', '')
                arg2 = quad.get('arg2', '')
                result_val = quad.get('result', '')
                report_lines.append(f"{i:3d}: ({op}, {arg1}, {arg2}, {result_val})")
    
    return "\n".join(report_lines)

def analyze_code_with_full_report(code: str, output_dir: str = None) -> str:
    """
    分析代码并生成完整报告
    
    Args:
        code: 源代码
        output_dir: 输出目录，如果指定则保存文件
    
    Returns:
        str: 分析报告
    """
    # 执行增强分析
    result = analyze_code_enhanced(code)
    
    # 保存结果到文件（如果指定了输出目录）
    if output_dir:
        save_analysis_results(result, output_dir)
    
    # 生成并返回报告
    return generate_analysis_report(result)

def analyze_code_with_codegen(code: str, enable_optimization: bool = True, 
                             enable_warnings: bool = True,
                             generate_target_code: bool = True) -> Dict[str, Any]:
    """
    增强的代码分析函数，包含目标代码生成
    """
    # 执行基础分析
    result = analyze_code_enhanced(code, enable_optimization, enable_warnings)
    
    # 如果基础分析成功且需要生成目标代码
    if not result.errors and generate_target_code and result.quadruples:
        try:
            # 配置代码生成器
            if enable_optimization:
                codegen_config = PredefinedCodeGenConfigs.release_config()
            else:
                codegen_config = PredefinedCodeGenConfigs.debug_config()
            
            # 创建代码生成器
            code_generator = EnhancedCodeGenerator(codegen_config)
            
            # 生成目标代码
            target_code = code_generator.generate(result.quadruples)
            
            # 添加到结果中
            result.target_code = target_code
            result.codegen_statistics = code_generator.get_enhanced_statistics()
            
        except Exception as e:
            result.errors.append(f"目标代码生成失败: {str(e)}")
    
    return result


# 示例用法和测试函数
def test_enhanced_analyzer():
    """测试增强分析器"""
    test_code = """
    fn main() -> i32 {
        let mut x: i32 = 10;
        let y: i32 = 5;
        let z = x + y * 2;
        
        if z > 15 {
            x = x + 1;
        }
        
        while x < 20 {
            x = x + 1;
        }
        
        return x;
    }
    
    fn unused_function() -> i32 {
        let unused_var = 42;
        return 0;
    }
    """
    
    print("=== 测试增强语义分析器 ===")
    report = analyze_code_with_full_report(test_code)
    print(report)
    
    print("\n=== 与基础分析器对比 ===")
    comparison = compare_with_basic_analyzer(test_code)
    print(json.dumps(comparison, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_enhanced_analyzer()