"""
基础目标代码生成器
将四元式中间代码转换为目标机器代码
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass
from enum import Enum, auto
import copy

from .target_code_config import (
    CodeGeneratorConfig, TargetArchitecture, OutputFormat,
    RegisterConfig, InstructionTemplates, CodeGenErrorMessages
)

class RegisterStatus(Enum):
    FREE = auto()      # 空闲
    OCCUPIED = auto()  # 被占用
    RESERVED = auto()  # 保留

@dataclass
class Register:
    name: str
    status: RegisterStatus
    variable: Optional[str] = None  # 当前存储的变量
    last_used: int = 0             # 最后使用时间

@dataclass
class StackFrame:
    """栈帧信息"""
    size: int = 0
    variables: Dict[str, int] = None  # 变量名 -> 栈偏移
    parameters: Dict[str, int] = None # 参数名 -> 栈偏移
    
    def __post_init__(self):
        if self.variables is None:
            self.variables = {}
        if self.parameters is None:
            self.parameters = {}

@dataclass
class GeneratedInstruction:
    """生成的指令"""
    mnemonic: str           # 助记符
    operands: List[str]     # 操作数
    comment: str = ""       # 注释
    line_number: int = 0    # 对应源代码行号
    
    def __str__(self) -> str:
        operand_str = ", ".join(self.operands) if self.operands else ""
        instruction = f"{self.mnemonic} {operand_str}".strip()
        if self.comment:
            instruction += f" ; {self.comment}"
        return instruction

class CodeGenerationError(Exception):
    """代码生成错误"""
    pass

class BasicCodeGenerator:
    """基础目标代码生成器"""
    
    def __init__(self, config: CodeGeneratorConfig = None):
        self.config = config or CodeGeneratorConfig()
        self.instructions: List[GeneratedInstruction] = []
        self.current_function: Optional[str] = None
        self.label_counter = 0
        self.temp_counter = 0
        
        # 寄存器管理
        self.registers: Dict[str, Register] = {}
        self.register_allocation_map: Dict[str, str] = {}  # 变量 -> 寄存器
        self.instruction_counter = 0
        
        # 栈帧管理
        self.current_frame: Optional[StackFrame] = None
        self.frame_stack: List[StackFrame] = []
        
        # 符号表和地址分配
        self.symbol_table: Dict[str, Dict[str, Any]] = {}
        self.string_literals: Dict[str, str] = {}
        self.constant_pool: Dict[str, Any] = {}
        
        # 初始化寄存器
        self._init_registers()
        
        # 指令模板
        self.templates = self._get_instruction_templates()
    
    def _init_registers(self):
        """初始化寄存器"""
        if self.config.target_architecture == TargetArchitecture.X86_64:
            reg_config = RegisterConfig.X86_64_REGISTERS
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            reg_config = RegisterConfig.ARM64_REGISTERS
        else:
            reg_config = RegisterConfig.X86_64_REGISTERS  # 默认
        
        # 初始化通用寄存器
        for reg_name in reg_config["general"]:
            status = RegisterStatus.RESERVED if reg_name in reg_config["special"] else RegisterStatus.FREE
            self.registers[reg_name] = Register(reg_name, status)
    
    def _get_instruction_templates(self) -> Dict[str, str]:
        """获取指令模板"""
        if self.config.target_architecture == TargetArchitecture.X86_64:
            return InstructionTemplates.X86_64_TEMPLATES
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            return InstructionTemplates.ARM64_TEMPLATES
        else:
            return InstructionTemplates.X86_64_TEMPLATES
    
    def generate(self, quadruples: Dict[str, List[Any]]) -> str:
        """
        主要代码生成入口点
        
        Args:
            quadruples: 函数名 -> 四元式列表的字典
            
        Returns:
            生成的目标代码字符串
        """
        try:
            self.instructions.clear()
            
            # 生成程序头部
            self._generate_program_header()
            
            # 为每个函数生成代码
            for func_name, quads in quadruples.items():
                self._generate_function_code(func_name, quads)
            
            # 生成程序尾部
            self._generate_program_footer()
            
            # 返回完整的目标代码
            return self._format_output()
            
        except Exception as e:
            raise CodeGenerationError(f"代码生成失败: {str(e)}")
    
    def _generate_program_header(self):
        """生成程序头部"""
        if self.config.output_format == OutputFormat.ASSEMBLY:
            if self.config.target_architecture == TargetArchitecture.X86_64:
                self._emit(".section .text")
                self._emit(".global _start")
                if self.config.generate_comments:
                    self._emit_comment("程序入口")
                self._emit("_start:")
                # 调用main函数
                self._emit("call", ["main"])
                # 退出程序
                self._emit("mov", ["rax", "60"])      # sys_exit
                self._emit("mov", ["rdi", "0"])       # exit code
                self._emit("syscall")
            elif self.config.target_architecture == TargetArchitecture.ARM64:
                self._emit(".section .text")
                self._emit(".global _start")
                self._emit("_start:")
                self._emit("bl", ["main"])
                self._emit("mov", ["x8", "#93"])      # sys_exit
                self._emit("mov", ["x0", "#0"])       # exit code
                self._emit("svc", ["#0"])
    
    def _generate_program_footer(self):
        """生成程序尾部"""
        if self.config.generate_symbol_table:
            self._generate_symbol_table()
        
        if self.string_literals:
            self._generate_string_section()
        
        if self.constant_pool:
            self._generate_constant_section()
    
    def _generate_function_code(self, func_name: str, quadruples: List[Any]):
        """为单个函数生成代码"""
        self.current_function = func_name
        
        # 创建新的栈帧
        self._enter_function(func_name)
        
        if self.config.generate_comments:
            self._emit_comment(f"函数: {func_name}")
        
        # 函数标签
        self._emit_label(f"func_{func_name}")
        
        # 函数序言
        self._generate_function_prologue()
        
        # 分析函数的变量使用情况
        self._analyze_variable_usage(quadruples)
        
        # 为每个四元式生成代码
        for i, quad in enumerate(quadruples):
            self.instruction_counter = i
            self._generate_quadruple_code(quad)
        
        # 函数尾声
        self._generate_function_epilogue()
        
        # 退出函数
        self._exit_function()
    
    def _enter_function(self, func_name: str):
        """进入函数，创建新栈帧"""
        frame = StackFrame()
        if self.current_frame:
            self.frame_stack.append(self.current_frame)
        self.current_frame = frame
        
        # 重置寄存器分配
        for reg in self.registers.values():
            if reg.status != RegisterStatus.RESERVED:
                reg.status = RegisterStatus.FREE
                reg.variable = None
        self.register_allocation_map.clear()
    
    def _exit_function(self):
        """退出函数，恢复栈帧"""
        if self.frame_stack:
            self.current_frame = self.frame_stack.pop()
        else:
            self.current_frame = None
        self.current_function = None
    
    def _analyze_variable_usage(self, quadruples: List[Any]):
        """分析变量使用情况，用于寄存器分配"""
        variables = set()
        for quad in quadruples:
            if hasattr(quad, 'arg1') and quad.arg1 != "_" and not quad.arg1.isdigit():
                variables.add(quad.arg1)
            if hasattr(quad, 'arg2') and quad.arg2 != "_" and not quad.arg2.isdigit():
                variables.add(quad.arg2)
            if hasattr(quad, 'result') and quad.result != "_" and not quad.result.isdigit():
                variables.add(quad.result)
        
        # 为变量分配栈空间或寄存器
        for var in variables:
            if self.config.enable_register_allocation and len(self.register_allocation_map) < self.config.max_registers:
                reg = self._allocate_register(var)
                if reg:
                    self.register_allocation_map[var] = reg
                else:
                    self._allocate_stack_space(var)
            else:
                self._allocate_stack_space(var)
    
    def _allocate_register(self, variable: str) -> Optional[str]:
        """为变量分配寄存器"""
        # 寻找空闲寄存器
        for reg_name, reg in self.registers.items():
            if reg.status == RegisterStatus.FREE:
                reg.status = RegisterStatus.OCCUPIED
                reg.variable = variable
                reg.last_used = self.instruction_counter
                return reg_name
        
        # 如果允许溢出到内存，寻找最久未使用的寄存器
        if self.config.spill_to_memory:
            oldest_reg = min(
                (reg for reg in self.registers.values() if reg.status == RegisterStatus.OCCUPIED),
                key=lambda r: r.last_used,
                default=None
            )
            if oldest_reg:
                # 溢出当前变量到内存
                if oldest_reg.variable:
                    self._spill_to_memory(oldest_reg.variable, oldest_reg.name)
                # 分配给新变量
                oldest_reg.variable = variable
                oldest_reg.last_used = self.instruction_counter
                return oldest_reg.name
        
        return None
    
    def _allocate_stack_space(self, variable: str):
        """为变量在栈上分配空间"""
        if self.current_frame:
            offset = self.current_frame.size
            self.current_frame.variables[variable] = offset
            self.current_frame.size += self.config.word_size
    
    def _spill_to_memory(self, variable: str, register: str):
        """将寄存器中的变量溢出到内存"""
        if variable in self.register_allocation_map:
            del self.register_allocation_map[variable]
        
        # 分配栈空间
        self._allocate_stack_space(variable)
        
        # 生成存储指令
        offset = self.current_frame.variables[variable]
        if self.config.target_architecture == TargetArchitecture.X86_64:
            self._emit("mov", [f"[rbp-{offset}]", register])
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            self._emit("str", [register, f"[sp, #{offset}]"])
    
    def _generate_function_prologue(self):
        """生成函数序言"""
        if self.config.target_architecture == TargetArchitecture.X86_64:
            if self.config.use_frame_pointer:
                self._emit("push", ["rbp"])
                self._emit("mov", ["rbp", "rsp"])
            
            # 为局部变量分配栈空间
            if self.current_frame and self.current_frame.size > 0:
                aligned_size = (self.current_frame.size + self.config.stack_alignment - 1) & ~(self.config.stack_alignment - 1)
                self._emit("sub", ["rsp", str(aligned_size)])
                
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            if self.config.use_frame_pointer:
                self._emit("stp", ["fp", "lr", "[sp, #-16]!"])
                self._emit("mov", ["fp", "sp"])
            
            if self.current_frame and self.current_frame.size > 0:
                aligned_size = (self.current_frame.size + self.config.stack_alignment - 1) & ~(self.config.stack_alignment - 1)
                self._emit("sub", ["sp", "sp", f"#{aligned_size}"])
    
    def _generate_function_epilogue(self):
        """生成函数尾声"""
        if self.config.target_architecture == TargetArchitecture.X86_64:
            if self.config.use_frame_pointer:
                self._emit("mov", ["rsp", "rbp"])
                self._emit("pop", ["rbp"])
            self._emit("ret")
            
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            if self.config.use_frame_pointer:
                self._emit("ldp", ["fp", "lr", "[sp], #16"])
            self._emit("ret")
    
    def _generate_quadruple_code(self, quad: Any):
        """为单个四元式生成代码"""
        if not hasattr(quad, 'op'):
            return
        
        op = quad.op
        arg1 = quad.arg1 if hasattr(quad, 'arg1') else "_"
        arg2 = quad.arg2 if hasattr(quad, 'arg2') else "_"
        result = quad.result if hasattr(quad, 'result') else "_"
        
        if self.config.generate_comments:
            self._emit_comment(f"({op}, {arg1}, {arg2}, {result})")
        
        # 根据操作类型生成相应代码
        if op == "=":
            self._generate_assignment(arg1, result)
        elif op in ["+", "-", "*", "/"]:
            self._generate_arithmetic(op, arg1, arg2, result)
        elif op in ["<", "<=", ">", ">=", "==", "!="]:
            self._generate_comparison(op, arg1, arg2, result)
        elif op == "goto":
            self._generate_goto(result)
        elif op == "if_false":
            self._generate_conditional_jump(arg1, result, False)
        elif op == "if_true":
            self._generate_conditional_jump(arg1, result, True)
        elif op == "label":
            self._emit_label(arg1)
        elif op == "call":
            self._generate_function_call(arg1, arg2, result)
        elif op == "param":
            self._generate_parameter_passing(arg1)
        elif op == "return":
            self._generate_return(arg1)
        else:
            if self.config.generate_comments:
                self._emit_comment(f"未处理的操作: {op}")
    
    def _generate_assignment(self, source: str, dest: str):
        """生成赋值代码"""
        src_operand = self._get_operand(source)
        dest_operand = self._get_operand(dest, is_destination=True)
        
        if self.config.target_architecture == TargetArchitecture.X86_64:
            if source.isdigit():
                # 立即数赋值
                self._emit("mov", [dest_operand, source])
            else:
                # 变量赋值
                if src_operand != dest_operand:  # 避免无意义的移动
                    self._emit("mov", [dest_operand, src_operand])
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            if source.isdigit():
                self._emit("mov", [dest_operand, f"#{source}"])
            else:
                if src_operand != dest_operand:
                    self._emit("mov", [dest_operand, src_operand])
    
    def _generate_arithmetic(self, op: str, left: str, right: str, result: str):
        """生成算术运算代码"""
        left_operand = self._get_operand(left)
        right_operand = self._get_operand(right)
        result_operand = self._get_operand(result, is_destination=True)
        
        if self.config.target_architecture == TargetArchitecture.X86_64:
            # x86-64的算术指令通常修改第一个操作数
            if left_operand != result_operand:
                self._emit("mov", [result_operand, left_operand])
            
            if op == "+":
                self._emit("add", [result_operand, right_operand])
            elif op == "-":
                self._emit("sub", [result_operand, right_operand])
            elif op == "*":
                self._emit("imul", [result_operand, right_operand])
            elif op == "/":
                # 除法需要特殊处理
                self._emit("mov", ["rax", left_operand])
                self._emit("cqo")  # 符号扩展
                self._emit("idiv", [right_operand])
                self._emit("mov", [result_operand, "rax"])
                
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            if op == "+":
                self._emit("add", [result_operand, left_operand, right_operand])
            elif op == "-":
                self._emit("sub", [result_operand, left_operand, right_operand])
            elif op == "*":
                self._emit("mul", [result_operand, left_operand, right_operand])
            elif op == "/":
                self._emit("udiv", [result_operand, left_operand, right_operand])
    
    def _generate_comparison(self, op: str, left: str, right: str, result: str):
        """生成比较代码"""
        left_operand = self._get_operand(left)
        right_operand = self._get_operand(right)
        result_operand = self._get_operand(result, is_destination=True)
        
        if self.config.target_architecture == TargetArchitecture.X86_64:
            self._emit("cmp", [left_operand, right_operand])
            # 根据比较操作设置结果
            if op == "<":
                self._emit("setl", ["al"])
            elif op == "<=":
                self._emit("setle", ["al"])
            elif op == ">":
                self._emit("setg", ["al"])
            elif op == ">=":
                self._emit("setge", ["al"])
            elif op == "==":
                self._emit("sete", ["al"])
            elif op == "!=":
                self._emit("setne", ["al"])
            # 将结果扩展到完整寄存器
            self._emit("movzx", [result_operand, "al"])
            
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            self._emit("cmp", [left_operand, right_operand])
            if op == "<":
                self._emit("cset", [result_operand, "lt"])
            elif op == "<=":
                self._emit("cset", [result_operand, "le"])
            elif op == ">":
                self._emit("cset", [result_operand, "gt"])
            elif op == ">=":
                self._emit("cset", [result_operand, "ge"])
            elif op == "==":
                self._emit("cset", [result_operand, "eq"])
            elif op == "!=":
                self._emit("cset", [result_operand, "ne"])
    
    def _generate_goto(self, label: str):
        """生成无条件跳转"""
        if self.config.target_architecture == TargetArchitecture.X86_64:
            self._emit("jmp", [label])
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            self._emit("b", [label])
    
    def _generate_conditional_jump(self, condition: str, label: str, jump_if_true: bool):
        """生成条件跳转"""
        cond_operand = self._get_operand(condition)
        
        if self.config.target_architecture == TargetArchitecture.X86_64:
            self._emit("test", [cond_operand, cond_operand])
            if jump_if_true:
                self._emit("jnz", [label])
            else:
                self._emit("jz", [label])
                
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            self._emit("cmp", [cond_operand, "#0"])
            if jump_if_true:
                self._emit("b.ne", [label])
            else:
                self._emit("b.eq", [label])
    
    def _generate_function_call(self, func_name: str, arg_count: str, result: str):
        """生成函数调用代码"""
        if self.config.target_architecture == TargetArchitecture.X86_64:
            # 保存调用者保存的寄存器
            caller_saved = ["rax", "rcx", "rdx", "rsi", "rdi", "r8", "r9", "r10", "r11"]
            for reg in caller_saved:
                if reg in self.register_allocation_map.values():
                    self._emit("push", [reg])
            
            # 调用函数
            self._emit("call", [func_name])
            
            # 恢复调用者保存的寄存器
            for reg in reversed(caller_saved):
                if reg in self.register_allocation_map.values():
                    self._emit("pop", [reg])
            
            # 如果有返回值，存储到结果变量
            if result != "_":
                result_operand = self._get_operand(result, is_destination=True)
                self._emit("mov", [result_operand, "rax"])
                
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            self._emit("bl", [func_name])
            if result != "_":
                result_operand = self._get_operand(result, is_destination=True)
                self._emit("mov", [result_operand, "x0"])
    
    def _generate_parameter_passing(self, param: str):
        """生成参数传递代码"""
        param_operand = self._get_operand(param)
        
        # 简化实现：假设参数通过栈传递
        if self.config.target_architecture == TargetArchitecture.X86_64:
            self._emit("push", [param_operand])
        elif self.config.target_architecture == TargetArchitecture.ARM64:
            self._emit("str", [param_operand, "[sp, #-16]!"])
    
    def _generate_return(self, value: str):
        """生成返回代码"""
        if value != "_":
            value_operand = self._get_operand(value)
            if self.config.target_architecture == TargetArchitecture.X86_64:
                self._emit("mov", ["rax", value_operand])
            elif self.config.target_architecture == TargetArchitecture.ARM64:
                self._emit("mov", ["x0", value_operand])
        
        # 跳转到函数尾声
        self._generate_function_epilogue()
    
    def _get_operand(self, operand: str, is_destination: bool = False) -> str:
        """获取操作数的实际表示（寄存器或内存地址）"""
        if operand == "_":
            return ""
        
        if operand.isdigit():
            # 立即数
            if self.config.target_architecture == TargetArchitecture.X86_64:
                return operand
            elif self.config.target_architecture == TargetArchitecture.ARM64:
                return f"#{operand}"
        
        # 检查是否在寄存器中
        if operand in self.register_allocation_map:
            reg = self.register_allocation_map[operand]
            # 更新最后使用时间
            if reg in self.registers:
                self.registers[reg].last_used = self.instruction_counter
            return reg
        
        # 检查是否在栈上
        if self.current_frame and operand in self.current_frame.variables:
            offset = self.current_frame.variables[operand]
            if self.config.target_architecture == TargetArchitecture.X86_64:
                return f"[rbp-{offset}]"
            elif self.config.target_architecture == TargetArchitecture.ARM64:
                return f"[sp, #{offset}]"
        
        # 如果是目标操作数且不存在，尝试分配
        if is_destination:
            if self.config.enable_register_allocation:
                reg = self._allocate_register(operand)
                if reg:
                    self.register_allocation_map[operand] = reg
                    return reg
            
            # 分配栈空间
            self._allocate_stack_space(operand)
            offset = self.current_frame.variables[operand]
            if self.config.target_architecture == TargetArchitecture.X86_64:
                return f"[rbp-{offset}]"
            elif self.config.target_architecture == TargetArchitecture.ARM64:
                return f"[sp, #{offset}]"
        
        # 默认返回原始操作数
        return operand
    
    def _emit(self, mnemonic: str, operands: List[str] = None, comment: str = ""):
        """生成一条指令"""
        instruction = GeneratedInstruction(
            mnemonic=mnemonic,
            operands=operands or [],
            comment=comment,
            line_number=self.instruction_counter
        )
        self.instructions.append(instruction)
    
    def _emit_label(self, label: str):
        """生成标签"""
        self._emit(f"{label}:")
    
    def _emit_comment(self, comment: str):
        """生成注释"""
        if self.config.generate_comments:
            self._emit(f"; {comment}")
    
    def _generate_symbol_table(self):
        """生成符号表"""
        self._emit_comment("符号表")
        for func_name in self.symbol_table:
            self._emit_comment(f"函数: {func_name}")
    
    def _generate_string_section(self):
        """生成字符串常量段"""
        self._emit(".section .rodata")
        for label, value in self.string_literals.items():
            self._emit(f"{label}:")
            self._emit(".ascii", [f'"{value}"'])
    
    def _generate_constant_section(self):
        """生成常量段"""
        self._emit(".section .data")
        for name, value in self.constant_pool.items():
            self._emit(f"{name}:")
            self._emit(".quad", [str(value)])
    
    def _format_output(self) -> str:
        """格式化输出"""
        lines = []
        
        if self.config.generate_comments:
            lines.append("; 由类Rust编译器生成的汇编代码")
            lines.append(f"; 目标架构: {self.config.target_architecture.name}")
            lines.append(f"; 优化级别: {self.config.optimization_level.name}")
            lines.append("")
        
        for instruction in self.instructions:
            lines.append(str(instruction))
        
        return "\n".join(lines)
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取代码生成统计信息"""
        return {
            "total_instructions": len(self.instructions),
            "register_usage": len(self.register_allocation_map),
            "functions_generated": len(set(self.symbol_table.keys())),
            "memory_locations": sum(len(frame.variables) for frame in [self.current_frame] + self.frame_stack if frame),
            "optimization_level": self.config.optimization_level.name,
            "target_architecture": self.config.target_architecture.name
        }