"""
目标代码生成器配置文件
用于管理代码生成的各种选项和规则
"""

from dataclasses import dataclass
from typing import Dict, List, Set
from enum import Enum, auto

class TargetArchitecture(Enum):
    X86_64 = auto()     # x86-64架构
    ARM64 = auto()      # ARM64架构
    RISCV = auto()      # RISC-V架构
    CUSTOM = auto()     # 自定义架构

class OutputFormat(Enum):
    ASSEMBLY = auto()   # 汇编代码
    LLVM_IR = auto()    # LLVM中间表示
    C_CODE = auto()     # C代码
    BYTECODE = auto()   # 字节码

class OptimizationLevel(Enum):
    NONE = 0           # 无优化
    BASIC = 1          # 基础优化
    AGGRESSIVE = 2     # 激进优化
    SIZE = 3           # 优化代码大小

@dataclass
class CodeGeneratorConfig:
    """目标代码生成器配置类"""
    
    # === 基本设置 ===
    target_architecture: TargetArchitecture = TargetArchitecture.X86_64
    output_format: OutputFormat = OutputFormat.ASSEMBLY
    optimization_level: OptimizationLevel = OptimizationLevel.BASIC
    
    # === 代码生成选项 ===
    generate_debug_info: bool = True
    generate_comments: bool = False
    use_frame_pointer: bool = True
    stack_alignment: int = 16
    
    # === 寄存器分配 ===
    enable_register_allocation: bool = True
    max_registers: int = 8
    spill_to_memory: bool = True
    register_pressure_threshold: int = 6
    
    # === 优化选项 ===
    enable_peephole_optimization: bool = True
    enable_instruction_scheduling: bool = False
    enable_tail_call_optimization: bool = False
    eliminate_redundant_moves: bool = True
    
    # === 内存管理 ===
    stack_frame_optimization: bool = True
    local_variable_packing: bool = True
    constant_pool_optimization: bool = True
    
    # === 调试和输出设置 ===
    verbose_output: bool = False
    save_intermediate_files: bool = True
    generate_symbol_table: bool = True
    include_source_mapping: bool = True
    
    # === 平台特定设置 ===
    calling_convention: str = "System V"  # 调用约定
    pointer_size: int = 8  # 指针大小（字节）
    word_size: int = 8     # 字大小（字节）
    endianness: str = "little"  # 字节序

class RegisterConfig:
    """寄存器配置"""
    
    # x86-64寄存器配置
    X86_64_REGISTERS = {
        "general": ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11", "r12", "r13", "r14", "r15"],
        "parameter": ["rdi", "rsi", "rdx", "rcx", "r8", "r9"],
        "return": ["rax"],
        "callee_saved": ["rbx", "r12", "r13", "r14", "r15", "rbp"],
        "caller_saved": ["rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"],
        "special": ["rsp", "rbp"]
    }
    
    # ARM64寄存器配置
    ARM64_REGISTERS = {
        "general": [f"x{i}" for i in range(0, 31)],
        "parameter": [f"x{i}" for i in range(0, 8)],
        "return": ["x0"],
        "callee_saved": [f"x{i}" for i in range(19, 29)],
        "caller_saved": [f"x{i}" for i in range(0, 18)],
        "special": ["sp", "fp"]
    }

class InstructionTemplates:
    """指令模板"""
    
    X86_64_TEMPLATES = {
        # 数据移动
        "move": "mov {dest}, {src}",
        "load": "mov {dest}, [{src}]",
        "store": "mov [{dest}], {src}",
        "load_immediate": "mov {dest}, {value}",
        
        # 算术运算
        "add": "add {dest}, {src}",
        "sub": "sub {dest}, {src}",
        "mul": "imul {dest}, {src}",
        "div": "idiv {src}",
        
        # 比较和跳转
        "compare": "cmp {op1}, {op2}",
        "jump": "jmp {label}",
        "jump_equal": "je {label}",
        "jump_not_equal": "jne {label}",
        "jump_less": "jl {label}",
        "jump_greater": "jg {label}",
        "jump_less_equal": "jle {label}",
        "jump_greater_equal": "jge {label}",
        
        # 函数调用
        "call": "call {function}",
        "return": "ret",
        "push": "push {reg}",
        "pop": "pop {reg}",
        
        # 标签和指令
        "label": "{label}:",
        "nop": "nop"
    }
    
    ARM64_TEMPLATES = {
        # 数据移动
        "move": "mov {dest}, {src}",
        "load": "ldr {dest}, [{src}]",
        "store": "str {src}, [{dest}]",
        "load_immediate": "mov {dest}, #{value}",
        
        # 算术运算
        "add": "add {dest}, {op1}, {op2}",
        "sub": "sub {dest}, {op1}, {op2}",
        "mul": "mul {dest}, {op1}, {op2}",
        "div": "udiv {dest}, {op1}, {op2}",
        
        # 比较和跳转
        "compare": "cmp {op1}, {op2}",
        "jump": "b {label}",
        "jump_equal": "b.eq {label}",
        "jump_not_equal": "b.ne {label}",
        "jump_less": "b.lt {label}",
        "jump_greater": "b.gt {label}",
        "jump_less_equal": "b.le {label}",
        "jump_greater_equal": "b.ge {label}",
        
        # 函数调用
        "call": "bl {function}",
        "return": "ret",
        "push": "str {reg}, [sp, #-16]!",
        "pop": "ldr {reg}, [sp], #16",
        
        # 标签和指令
        "label": "{label}:",
        "nop": "nop"
    }

class PredefinedCodeGenConfigs:
    """预定义的代码生成配置模板"""
    
    @staticmethod
    def debug_config() -> CodeGeneratorConfig:
        """调试模式配置"""
        config = CodeGeneratorConfig()
        config.optimization_level = OptimizationLevel.NONE
        config.generate_debug_info = True
        config.generate_comments = False
        config.verbose_output = True
        config.save_intermediate_files = True
        config.enable_register_allocation = False
        return config
    
    @staticmethod
    def release_config() -> CodeGeneratorConfig:
        """发布模式配置"""
        config = CodeGeneratorConfig()
        config.optimization_level = OptimizationLevel.AGGRESSIVE
        config.generate_debug_info = False
        config.generate_comments = False
        config.enable_peephole_optimization = True
        config.enable_instruction_scheduling = True
        config.enable_tail_call_optimization = True
        return config
    
    @staticmethod
    def size_optimized_config() -> CodeGeneratorConfig:
        """代码大小优化配置"""
        config = CodeGeneratorConfig()
        config.optimization_level = OptimizationLevel.SIZE
        config.stack_frame_optimization = True
        config.local_variable_packing = True
        config.constant_pool_optimization = True
        config.eliminate_redundant_moves = True
        return config
    
    @staticmethod
    def educational_config() -> CodeGeneratorConfig:
        """教育模式配置 - 适合学习编译原理"""
        config = CodeGeneratorConfig()
        config.generate_comments = False
        config.verbose_output = True
        config.save_intermediate_files = True
        config.generate_symbol_table = True
        config.include_source_mapping = True
        config.enable_register_allocation = True
        config.max_registers = 4  # 限制寄存器数量以便观察溢出
        return config

# 错误和警告消息
class CodeGenErrorMessages:
    """代码生成错误和警告消息模板"""
    
    REGISTER_ALLOCATION_FAILED = "寄存器分配失败: 变量 '{var}' 无法分配寄存器"
    UNSUPPORTED_OPERATION = "不支持的操作: '{op}' 在目标架构 '{arch}' 上"
    INVALID_ADDRESSING_MODE = "无效的寻址模式: '{mode}'"
    STACK_OVERFLOW = "栈溢出: 局部变量占用空间超过限制"
    FUNCTION_TOO_LARGE = "函数 '{func}' 过大，可能影响性能"
    UNREACHABLE_CODE = "检测到不可达代码在 '{func}' 中"
    
    @staticmethod
    def format_message(template: str, **kwargs) -> str:
        """格式化错误消息"""
        return template.format(**kwargs)

class TargetCodeMetrics:
    """目标代码质量指标"""
    
    # 代码质量阈值
    MAX_FUNCTION_INSTRUCTIONS = 1000  # 最大函数指令数
    MAX_BASIC_BLOCK_SIZE = 50        # 最大基本块大小
    MAX_CALL_DEPTH = 20              # 最大调用深度
    MAX_STACK_FRAME_SIZE = 4096      # 最大栈帧大小
    
    # 性能指标阈值
    REGISTER_USAGE_WARNING = 0.8     # 寄存器使用率警告阈值
    MEMORY_ACCESS_WARNING = 0.3      # 内存访问比例警告阈值
    BRANCH_PREDICTION_THRESHOLD = 0.9 # 分支预测准确率阈值

def load_codegen_config_from_file(filepath: str) -> CodeGeneratorConfig:
    """从文件加载代码生成配置"""
    import json
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            config_dict = json.load(f)
        
        config = CodeGeneratorConfig()
        for key, value in config_dict.items():
            if hasattr(config, key):
                # 处理枚举类型
                if key == "target_architecture":
                    setattr(config, key, TargetArchitecture[value])
                elif key == "output_format":
                    setattr(config, key, OutputFormat[value])
                elif key == "optimization_level":
                    setattr(config, key, OptimizationLevel[value])
                else:
                    setattr(config, key, value)
        
        return config
    except FileNotFoundError:
        print(f"代码生成配置文件 {filepath} 未找到，使用默认配置")
        return CodeGeneratorConfig()
    except json.JSONDecodeError as e:
        print(f"解析配置文件时出错: {e}")
        return CodeGeneratorConfig()

def save_codegen_config_to_file(config: CodeGeneratorConfig, filepath: str) -> None:
    """保存代码生成配置到文件"""
    import json
    from dataclasses import asdict
    
    config_dict = asdict(config)
    # 转换枚举值为字符串
    for key, value in config_dict.items():
        if hasattr(value, 'name'):  # 枚举类型
            config_dict[key] = value.name
    
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(config_dict, f, indent=2, ensure_ascii=False)

def create_codegen_config_template() -> str:
    """创建代码生成配置文件模板"""
    template = """
{
  "_comment": "类Rust语言目标代码生成器配置文件",
  
  "target_architecture": "X86_64",
  "output_format": "ASSEMBLY",
  "optimization_level": "BASIC",
  
  "generate_debug_info": true,
  "generate_comments": true,
  "use_frame_pointer": true,
  "stack_alignment": 16,
  
  "enable_register_allocation": true,
  "max_registers": 8,
  "spill_to_memory": true,
  "register_pressure_threshold": 6,
  
  "enable_peephole_optimization": true,
  "enable_instruction_scheduling": false,
  "enable_tail_call_optimization": false,
  "eliminate_redundant_moves": true,
  
  "stack_frame_optimization": true,
  "local_variable_packing": true,
  "constant_pool_optimization": true,
  
  "verbose_output": false,
  "save_intermediate_files": true,
  "generate_symbol_table": true,
  "include_source_mapping": true,
  
  "calling_convention": "System V",
  "pointer_size": 8,
  "word_size": 8,
  "endianness": "little"
}
"""
    return template.strip()

# 使用示例
def example_usage():
    """配置使用示例"""
    print("=== 目标代码生成配置系统使用示例 ===\n")
    
    # 1. 使用默认配置
    print("1. 默认配置:")
    default_config = CodeGeneratorConfig()
    print(f"   目标架构: {default_config.target_architecture.name}")
    print(f"   输出格式: {default_config.output_format.name}")
    print(f"   优化级别: {default_config.optimization_level.name}")
    
    # 2. 使用预定义配置
    print("\n2. 调试模式配置:")
    debug_config = PredefinedCodeGenConfigs.debug_config()
    print(f"   生成调试信息: {debug_config.generate_debug_info}")
    print(f"   详细输出: {debug_config.verbose_output}")
    print(f"   寄存器分配: {debug_config.enable_register_allocation}")
    
    # 3. 发布模式配置
    print("\n3. 发布模式配置:")
    release_config = PredefinedCodeGenConfigs.release_config()
    print(f"   优化级别: {release_config.optimization_level.name}")
    print(f"   窥孔优化: {release_config.enable_peephole_optimization}")
    print(f"   尾调用优化: {release_config.enable_tail_call_optimization}")
    
    # 4. 教育模式配置
    print("\n4. 教育模式配置:")
    edu_config = PredefinedCodeGenConfigs.educational_config()
    print(f"   生成注释: {edu_config.generate_comments}")
    print(f"   最大寄存器数: {edu_config.max_registers}")
    print(f"   包含源码映射: {edu_config.include_source_mapping}")

if __name__ == "__main__":
    example_usage()