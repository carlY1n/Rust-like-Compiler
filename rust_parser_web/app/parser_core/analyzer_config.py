"""
增强语义分析器配置文件
用于管理分析器的各种选项和规则
"""

from dataclasses import dataclass
from typing import Dict, List, Set
from enum import Enum, auto

class WarningLevel(Enum):
    ERROR = auto()      # 错误级别
    WARNING = auto()    # 警告级别
    INFO = auto()       # 信息级别
    HINT = auto()       # 提示级别

class OptimizationLevel(Enum):
    NONE = 0           # 无优化
    BASIC = 1          # 基础优化
    AGGRESSIVE = 2     # 激进优化

@dataclass
class AnalyzerConfig:
    """分析器配置类"""
    
    # === 基本设置 ===
    enable_warnings: bool = True
    enable_optimization: bool = True
    optimization_level: OptimizationLevel = OptimizationLevel.BASIC
    
    # === 警告设置 ===
    warning_level: WarningLevel = WarningLevel.WARNING
    treat_warnings_as_errors: bool = False
    
    # 具体警告类型开关
    warn_unused_variables: bool = True
    warn_unused_functions: bool = True
    warn_type_mismatch: bool = True
    warn_missing_return: bool = True
    warn_dead_code: bool = True
    warn_uninitialized_variables: bool = True
    warn_constant_conditions: bool = True
    warn_unreachable_code: bool = True
    
    # === 优化设置 ===
    enable_constant_folding: bool = True
    enable_constant_propagation: bool = True
    enable_dead_code_elimination: bool = True
    enable_algebraic_simplification: bool = True
    enable_common_subexpression_elimination: bool = False  # 高级优化
    enable_loop_optimization: bool = False  # 高级优化
    
    # === 类型检查设置 ===
    strict_type_checking: bool = True
    allow_implicit_conversions: bool = False
    check_array_bounds: bool = True  # 数组边界检查
    check_null_pointer: bool = True  # 空指针检查
    
    # === 代码风格检查 ===
    enforce_naming_convention: bool = False
    max_function_length: int = 100  # 最大函数长度
    max_nesting_depth: int = 5      # 最大嵌套深度
    
    # === 内存管理 ===
    check_memory_leaks: bool = False    # 内存泄漏检查（高级功能）
    stack_size_limit: int = 1024 * 1024  # 栈大小限制
    
    # === 调试和输出设置 ===
    generate_debug_info: bool = True
    verbose_output: bool = False
    save_intermediate_results: bool = True
    
    # === 扩展语言特性 ===
    support_generics: bool = False      # 泛型支持
    support_closures: bool = False      # 闭包支持
    support_async: bool = False         # 异步支持
    support_modules: bool = False       # 模块系统支持

# 预定义配置
class PredefinedConfigs:
    """预定义的配置模板"""
    
    @staticmethod
    def strict_config() -> AnalyzerConfig:
        """严格模式配置"""
        config = AnalyzerConfig()
        config.strict_type_checking = True
        config.treat_warnings_as_errors = True
        config.warning_level = WarningLevel.ERROR
        config.allow_implicit_conversions = False
        config.check_array_bounds = True
        config.check_null_pointer = True
        config.enforce_naming_convention = True
        return config
    
    @staticmethod
    def permissive_config() -> AnalyzerConfig:
        """宽松模式配置"""
        config = AnalyzerConfig()
        config.strict_type_checking = False
        config.treat_warnings_as_errors = False
        config.warning_level = WarningLevel.INFO
        config.allow_implicit_conversions = True
        config.warn_unused_variables = False
        config.warn_unused_functions = False
        return config
    
    @staticmethod
    def debug_config() -> AnalyzerConfig:
        """调试模式配置"""
        config = AnalyzerConfig()
        config.generate_debug_info = True
        config.verbose_output = True
        config.save_intermediate_results = True
        config.enable_optimization = False  # 调试时关闭优化
        return config
    
    @staticmethod
    def release_config() -> AnalyzerConfig:
        """发布模式配置"""
        config = AnalyzerConfig()
        config.optimization_level = OptimizationLevel.AGGRESSIVE
        config.enable_all_optimizations()
        config.warning_level = WarningLevel.ERROR
        config.treat_warnings_as_errors = True
        config.generate_debug_info = False
        return config

    @staticmethod
    def educational_config() -> AnalyzerConfig:
        """教育模式配置 - 适合学习编译原理"""
        config = AnalyzerConfig()
        config.verbose_output = True
        config.save_intermediate_results = True
        config.generate_debug_info = True
        config.warn_unused_variables = True
        config.warn_type_mismatch = True
        config.enable_optimization = True
        config.optimization_level = OptimizationLevel.BASIC
        return config

# 扩展 AnalyzerConfig 类
def enable_all_optimizations(self) -> None:
    """启用所有优化"""
    self.enable_constant_folding = True
    self.enable_constant_propagation = True
    self.enable_dead_code_elimination = True
    self.enable_algebraic_simplification = True
    self.enable_common_subexpression_elimination = True
    self.enable_loop_optimization = True

def disable_all_optimizations(self) -> None:
    """禁用所有优化"""
    self.enable_constant_folding = False
    self.enable_constant_propagation = False
    self.enable_dead_code_elimination = False
    self.enable_algebraic_simplification = False
    self.enable_common_subexpression_elimination = False
    self.enable_loop_optimization = False

def enable_all_warnings(self) -> None:
    """启用所有警告"""
    self.warn_unused_variables = True
    self.warn_unused_functions = True
    self.warn_type_mismatch = True
    self.warn_missing_return = True
    self.warn_dead_code = True
    self.warn_uninitialized_variables = True
    self.warn_constant_conditions = True
    self.warn_unreachable_code = True

def disable_all_warnings(self) -> None:
    """禁用所有警告"""
    self.warn_unused_variables = False
    self.warn_unused_functions = False
    self.warn_type_mismatch = False
    self.warn_missing_return = False
    self.warn_dead_code = False
    self.warn_uninitialized_variables = False
    self.warn_constant_conditions = False
    self.warn_unreachable_code = False

# 将方法绑定到类
AnalyzerConfig.enable_all_optimizations = enable_all_optimizations
AnalyzerConfig.disable_all_optimizations = disable_all_optimizations
AnalyzerConfig.enable_all_warnings = enable_all_warnings
AnalyzerConfig.disable_all_warnings = disable_all_warnings

class LanguageFeatureConfig:
    """语言特性配置"""
    
    # 支持的数据类型
    SUPPORTED_BASIC_TYPES = {"i32", "bool", "char", "string", "void"}
    SUPPORTED_COMPLEX_TYPES = {"array", "struct", "enum", "function", "pointer"}
    
    # 支持的运算符
    ARITHMETIC_OPERATORS = {"+", "-", "*", "/", "%"}
    COMPARISON_OPERATORS = {"<", "<=", ">", ">=", "==", "!="}
    LOGICAL_OPERATORS = {"&&", "||", "!"}
    BITWISE_OPERATORS = {"&", "|", "^", "<<", ">>"}
    ASSIGNMENT_OPERATORS = {"=", "+=", "-=", "*=", "/="}
    
    # 支持的控制结构
    CONTROL_STRUCTURES = {"if", "while", "for", "loop", "match", "break", "continue", "return"}
    
    # 命名约定规则
    NAMING_CONVENTIONS = {
        "variables": r"^[a-z][a-z0-9_]*$",      # 变量：小写字母开头
        "functions": r"^[a-z][a-z0-9_]*$",      # 函数：小写字母开头
        "constants": r"^[A-Z][A-Z0-9_]*$",      # 常量：大写字母开头
        "types": r"^[A-Z][a-zA-Z0-9]*$",        # 类型：大写字母开头驼峰
    }

class ErrorMessages:
    """错误和警告消息模板"""
    
    # 语法错误
    SYNTAX_ERROR_UNEXPECTED_TOKEN = "Unexpected token '{token}' at line {line}"
    SYNTAX_ERROR_MISSING_SEMICOLON = "Missing semicolon at line {line}"
    SYNTAX_ERROR_MISMATCHED_BRACES = "Mismatched braces at line {line}"
    
    # 语义错误
    SEMANTIC_ERROR_UNDEFINED_VARIABLE = "Undefined variable '{name}' at line {line}"
    SEMANTIC_ERROR_REDEFINED_VARIABLE = "Variable '{name}' already defined at line {line}"
    SEMANTIC_ERROR_TYPE_MISMATCH = "Type mismatch: expected '{expected}', got '{actual}' at line {line}"
    SEMANTIC_ERROR_IMMUTABLE_ASSIGNMENT = "Cannot assign to immutable variable '{name}' at line {line}"
    SEMANTIC_ERROR_UNINITIALIZED_VARIABLE = "Variable '{name}' used before initialization at line {line}"
    SEMANTIC_ERROR_MISSING_RETURN = "Function '{name}' missing return statement"
    SEMANTIC_ERROR_INVALID_OPERATION = "Invalid operation '{op}' for types '{left}' and '{right}' at line {line}"
    
    # 警告消息
    WARNING_UNUSED_VARIABLE = "Unused variable '{name}' at line {line}"
    WARNING_UNUSED_FUNCTION = "Unused function '{name}'"
    WARNING_DEAD_CODE = "Unreachable code at line {line}"
    WARNING_CONSTANT_CONDITION = "Condition is always {value} at line {line}"
    WARNING_IMPLICIT_CONVERSION = "Implicit type conversion from '{from_type}' to '{to_type}' at line {line}"
    WARNING_SHADOWED_VARIABLE = "Variable '{name}' shadows previous declaration at line {line}"
    
    @staticmethod
    def format_message(template: str, **kwargs) -> str:
        """格式化错误消息"""
        return template.format(**kwargs)

class PerformanceMetrics:
    """性能指标配置"""
    
    # 复杂度阈值
    MAX_CYCLOMATIC_COMPLEXITY = 10     # 最大圈复杂度
    MAX_COGNITIVE_COMPLEXITY = 15      # 最大认知复杂度
    MAX_FUNCTION_PARAMETERS = 8        # 最大函数参数数量
    MAX_LOCAL_VARIABLES = 20           # 最大局部变量数量
    
    # 性能警告阈值
    PERFORMANCE_WARNING_THRESHOLDS = {
        "deep_nesting": 4,              # 深度嵌套警告
        "long_function": 50,            # 长函数警告（行数）
        "many_variables": 15,           # 变量过多警告
        "complex_expression": 5,        # 复杂表达式警告（操作符数量）
    }

class CompilerDirectives:
    """编译器指令支持"""
    
    # 支持的编译器指令
    SUPPORTED_DIRECTIVES = {
        "#pragma": "compiler_optimization",
        "#warning": "compile_time_warning",
        "#error": "compile_time_error",
        "#ifdef": "conditional_compilation",
        "#ifndef": "conditional_compilation",
        "#define": "macro_definition",
    }
    
    # 优化指令
    OPTIMIZATION_DIRECTIVES = {
        "optimize_off": "disable_optimization",
        "optimize_on": "enable_optimization",
        "inline": "force_inline",
        "noinline": "prevent_inline",
    }

def load_config_from_file(filepath: str) -> AnalyzerConfig:
    """从文件加载配置"""
    import json
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        config = AnalyzerConfig()
        for key, value in config_dict.items():
            if hasattr(config, key):
                setattr(config, key, value)
        
        return config
    except FileNotFoundError:
        print(f"Configuration file {filepath} not found, using default config")
        return AnalyzerConfig()
    except json.JSONDecodeError as e:
        print(f"Error parsing configuration file: {e}")
        return AnalyzerConfig()

def save_config_to_file(config: AnalyzerConfig, filepath: str) -> None:
    """保存配置到文件"""
    import json
    from dataclasses import asdict
    
    config_dict = asdict(config)
    # 转换枚举值为字符串
    for key, value in config_dict.items():
        if hasattr(value, 'name'):  # 枚举类型
            config_dict[key] = value.name
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)

def create_config_template() -> str:
    """创建配置文件模板"""
    template = """
{
  "_comment": "类Rust语言增强语义分析器配置文件",
  
  "enable_warnings": true,
  "enable_optimization": true,
  "optimization_level": "BASIC",
  
  "warning_level": "WARNING",
  "treat_warnings_as_errors": false,
  
  "warn_unused_variables": true,
  "warn_unused_functions": true,
  "warn_type_mismatch": true,
  "warn_missing_return": true,
  "warn_dead_code": true,
  "warn_uninitialized_variables": true,
  "warn_constant_conditions": true,
  "warn_unreachable_code": true,
  
  "enable_constant_folding": true,
  "enable_constant_propagation": true,
  "enable_dead_code_elimination": true,
  "enable_algebraic_simplification": true,
  "enable_common_subexpression_elimination": false,
  "enable_loop_optimization": false,
  
  "strict_type_checking": true,
  "allow_implicit_conversions": false,
  "check_array_bounds": true,
  "check_null_pointer": true,
  
  "enforce_naming_convention": false,
  "max_function_length": 100,
  "max_nesting_depth": 5,
  
  "generate_debug_info": true,
  "verbose_output": false,
  "save_intermediate_results": true
}
"""
    return template.strip()

# 使用示例
def example_usage():
    """配置使用示例"""
    print("=== 配置系统使用示例 ===\n")
    
    # 1. 使用默认配置
    print("1. 默认配置:")
    default_config = AnalyzerConfig()
    print(f"   启用警告: {default_config.enable_warnings}")
    print(f"   优化级别: {default_config.optimization_level.name}")
    
    # 2. 使用预定义配置
    print("\n2. 严格模式配置:")
    strict_config = PredefinedConfigs.strict_config()
    print(f"   严格类型检查: {strict_config.strict_type_checking}")
    print(f"   警告视为错误: {strict_config.treat_warnings_as_errors}")
    
    # 3. 自定义配置
    print("\n3. 自定义配置:")
    custom_config = AnalyzerConfig()
    custom_config.enable_all_optimizations()
    custom_config.optimization_level = OptimizationLevel.AGGRESSIVE
    print(f"   常量折叠: {custom_config.enable_constant_folding}")
    print(f"   死代码消除: {custom_config.enable_dead_code_elimination}")
    
    # 4. 保存和加载配置
    print("\n4. 配置文件操作:")
    save_config_to_file(custom_config, "custom_config.json")
    loaded_config = load_config_from_file("custom_config.json")
    print(f"   配置已保存和加载")
    
    # 5. 生成配置模板
    print("\n5. 配置文件模板:")
    template = create_config_template()
    print("   模板已生成（部分内容）:")
    print("   " + "\n   ".join(template.split('\n')[:10]) + "...")

if __name__ == "__main__":
    example_usage()