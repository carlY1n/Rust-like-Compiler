"""
类Rust语言编译器前端 - 解析器核心模块

包含词法分析、语法分析、语义分析和中间代码生成功能
支持基础版本和增强版本的语义分析器
"""

# 基础模块
from .Lexer import RustLexer
from .Parser import RustParser
from .semantic_analyzer import SemanticAnalyzer, SemanticError
from .analyzer import analyze_code

# 增强模块
try:
    from .enhanced_semantic_analyzer import (
        EnhancedSemanticAnalyzer,
        TypeInfo,
        DataType,
        Symbol,
        SymbolType,
        Scope,
        Quadruple,
        Warning
    )
    from .enhanced_analyzer import (
        analyze_code_enhanced,
        analyze_code_with_full_report,
        CodeAnalysisResult,
        compare_with_basic_analyzer
    )
    from .analyzer_config import (
        AnalyzerConfig,
        PredefinedConfigs,
        WarningLevel,
        OptimizationLevel,
        LanguageFeatureConfig,
        ErrorMessages
    )
    
    ENHANCED_AVAILABLE = True
    
except ImportError as e:
    print(f"增强功能不可用: {e}")
    ENHANCED_AVAILABLE = False

# 版本信息
__version__ = "2.0.0"
__author__ = "Your Name"

# 公开接口
__all__ = [
    # 基础模块
    'RustLexer',
    'RustParser', 
    'SemanticAnalyzer',
    'SemanticError',
    'analyze_code',
    
    # 增强模块（如果可用）
    'EnhancedSemanticAnalyzer',
    'analyze_code_enhanced',
    'analyze_code_with_full_report',
    'AnalyzerConfig',
    'PredefinedConfigs',
    'CodeAnalysisResult',
    
    # 数据类型
    'TypeInfo',
    'DataType',
    'Symbol',
    'SymbolType',
    'Scope',
    'Quadruple',
    'Warning',
    
    # 配置类型
    'WarningLevel',
    'OptimizationLevel',
    'LanguageFeatureConfig',
    'ErrorMessages',
    
    # 工具函数
    'compare_with_basic_analyzer',
    
    # 元信息
    'ENHANCED_AVAILABLE',
    '__version__',
]

def get_version_info():
    """获取版本信息"""
    info = {
        'version': __version__,
        'basic_analyzer': True,
        'enhanced_analyzer': ENHANCED_AVAILABLE,
        'features': {
            'lexical_analysis': True,
            'syntax_analysis': True,
            'semantic_analysis': True,
            'intermediate_code_generation': True,
            'type_checking': ENHANCED_AVAILABLE,
            'code_optimization': ENHANCED_AVAILABLE,
            'warning_system': ENHANCED_AVAILABLE,
            'configuration_system': ENHANCED_AVAILABLE,
        }
    }
    return info

def print_version_info():
    """打印版本信息"""
    info = get_version_info()
    print(f"类Rust语言编译器前端 v{info['version']}")
    print(f"基础分析器: {'✓' if info['basic_analyzer'] else '✗'}")
    print(f"增强分析器: {'✓' if info['enhanced_analyzer'] else '✗'}")
    print("\n功能特性:")
    for feature, available in info['features'].items():
        status = '✓' if available else '✗'
        print(f"  {feature}: {status}")

# 兼容性检查
def check_compatibility():
    """检查模块兼容性"""
    issues = []
    
    try:
        # 测试基础功能
        lexer = RustLexer()
        tokens = lexer.tokenize("fn main() {}")
        parser = RustParser(tokens)
        ast = parser.parse()
        analyzer = SemanticAnalyzer()
        result = analyzer.analyze(ast)
        
    except Exception as e:
        issues.append(f"基础分析器问题: {e}")
    
    if ENHANCED_AVAILABLE:
        try:
            # 测试增强功能
            from .enhanced_analyzer import analyze_code_enhanced
            result = analyze_code_enhanced("fn main() {}")
            
        except Exception as e:
            issues.append(f"增强分析器问题: {e}")
    
    return issues

# 模块初始化
if __name__ == "__main__":
    print_version_info()
    
    print("\n检查兼容性...")
    issues = check_compatibility()
    
    if not issues:
        print("所有功能正常工作")
    else:
        print("⚠️ 发现以下问题:")
        for issue in issues:
            print(f"  - {issue}")