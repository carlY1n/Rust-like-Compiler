"""
增强目标代码生成器
提供更高级的优化和代码生成功能
"""

from typing import Dict, List, Optional, Any, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum, auto
import copy
import re

from .code_generator import BasicCodeGenerator, CodeGenerationError, GeneratedInstruction, StackFrame
from .target_code_config import (
    CodeGeneratorConfig, TargetArchitecture, OutputFormat, OptimizationLevel,
    CodeGenErrorMessages, TargetCodeMetrics
)

class OptimizationPass(Enum):
    PEEPHOLE = auto()           # 窥孔优化
    DEAD_CODE_ELIMINATION = auto()  # 死代码消除
    REGISTER_COALESCING = auto()    # 寄存器合并
    INSTRUCTION_SCHEDULING = auto() # 指令调度
    CONSTANT_PROPAGATION = auto()   # 常量传播
    ALGEBRAIC_SIMPLIFICATION = auto() # 代数简化

@dataclass
class BasicBlock:
    """基本块"""
    label: str
    instructions: List[GeneratedInstruction] = field(default_factory=list)
    predecessors: Set[str] = field(default_factory=set)
    successors: Set[str] = field(default_factory=set)
    live_in: Set[str] = field(default_factory=set)   # 活跃输入变量
    live_out: Set[str] = field(default_factory=set)  # 活跃输出变量

@dataclass
class FlowGraph:
    """控制流图"""
    blocks: Dict[str, BasicBlock] = field(default_factory=dict)
    entry_block: Optional[str] = None
    exit_blocks: Set[str] = field(default_factory=set)

@dataclass
class OptimizationResult:
    """优化结果"""
    instructions_eliminated: int = 0
    registers_saved: int = 0
    memory_accesses_reduced: int = 0
    cycles_saved: int = 0
    optimizations_applied: List[str] = field(default_factory=list)

class EnhancedCodeGenerator(BasicCodeGenerator):
    """增强目标代码生成器"""
    
    def __init__(self, config: CodeGeneratorConfig = None):
        super().__init__(config)
        
        # 优化相关
        self.optimization_passes: List[OptimizationPass] = []
        self.optimization_results: Dict[str, OptimizationResult] = {}
        self.flow_graphs: Dict[str, FlowGraph] = {}
        
        # 增强分析
        self.live_variables: Dict[str, Set[str]] = {}
        self.interference_graph: Dict[str, Set[str]] = {}
        self.register_coloring: Dict[str, str] = {}
        
        # 性能计数器
        self.performance_metrics: Dict[str, Any] = {}
        
        # 初始化优化通路
        self._init_optimization_passes()
    
    def _init_optimization_passes(self):
        """初始化优化通路"""
        if self.config.optimization_level == OptimizationLevel.NONE:
            return
        
        # 基础优化
        if self.config.optimization_level >= OptimizationLevel.BASIC:
            if self.config.enable_peephole_optimization:
                self.optimization_passes.append(OptimizationPass.PEEPHOLE)
            if self.config.eliminate_redundant_moves:
                self.optimization_passes.append(OptimizationPass.DEAD_CODE_ELIMINATION)
            self.optimization_passes.append(OptimizationPass.CONSTANT_PROPAGATION)
        
        # 激进优化
        if self.config.optimization_level >= OptimizationLevel.AGGRESSIVE:
            self.optimization_passes.append(OptimizationPass.REGISTER_COALESCING)
            if self.config.enable_instruction_scheduling:
                self.optimization_passes.append(OptimizationPass.INSTRUCTION_SCHEDULING)
            self.optimization_passes.append(OptimizationPass.ALGEBRAIC_SIMPLIFICATION)
    
    def generate(self, quadruples: Dict[str, List[Any]]) -> str:
        """
        增强的代码生成入口点
        """
        try:
            # 执行基本代码生成
            result = super().generate(quadruples)
            
            # 执行优化通路
            if self.optimization_passes:
                self._perform_optimizations()
                result = self._format_output()
            
            # 生成优化报告
            if self.config.verbose_output:
                self._generate_optimization_report()
            
            return result
            
        except Exception as e:
            raise CodeGenerationError(f"增强代码生成失败: {str(e)}")
    
    def _generate_function_code(self, func_name: str, quadruples: List[Any]):
        """为单个函数生成代码（增强版本）"""
        # 构建控制流图
        flow_graph = self._build_control_flow_graph(func_name, quadruples)
        self.flow_graphs[func_name] = flow_graph
        
        # 活跃变量分析
        self._analyze_liveness(flow_graph)
        
        # 寄存器分配优化
        if self.config.enable_register_allocation:
            self._advanced_register_allocation(func_name, flow_graph)
        
        # 调用基础代码生成
        super()._generate_function_code(func_name, quadruples)
        
        # 记录性能指标
        self._update_performance_metrics(func_name)
    
    def _build_control_flow_graph(self, func_name: str, quadruples: List[Any]) -> FlowGraph:
        """构建控制流图"""
        flow_graph = FlowGraph()
        current_block = None
        block_counter = 0
        
        for i, quad in enumerate(quadruples):
            if not hasattr(quad, 'op'):
                continue
                
            # 开始新的基本块
            if quad.op == "label" or i == 0:
                if quad.op == "label":
                    block_label = quad.arg1
                else:
                    block_label = f"{func_name}_bb_{block_counter}"
                    block_counter += 1
                
                current_block = BasicBlock(label=block_label)
                flow_graph.blocks[block_label] = current_block
                
                if i == 0:
                    flow_graph.entry_block = block_label
            
            # 添加指令到当前基本块
            if current_block:
                instruction = GeneratedInstruction(
                    mnemonic=quad.op,
                    operands=[quad.arg1, quad.arg2, quad.result],
                    line_number=i
                )
                current_block.instructions.append(instruction)
                
                # 处理控制流
                if quad.op in ["goto", "if_false", "if_true", "return"]:
                    if quad.op == "goto":
                        current_block.successors.add(quad.result)
                    elif quad.op in ["if_false", "if_true"]:
                        current_block.successors.add(quad.result)
                        # 添加下一个基本块作为后继
                        if i + 1 < len(quadruples):
                            next_block_label = f"{func_name}_bb_{block_counter}"
                            current_block.successors.add(next_block_label)
                    elif quad.op == "return":
                        flow_graph.exit_blocks.add(current_block.label)
                    
                    # 结束当前基本块
                    current_block = None
        
        # 建立前驱关系
        for block_label, block in flow_graph.blocks.items():
            for successor_label in block.successors:
                if successor_label in flow_graph.blocks:
                    flow_graph.blocks[successor_label].predecessors.add(block_label)
        
        return flow_graph
    
    def _analyze_liveness(self, flow_graph: FlowGraph):
        """活跃变量分析"""
        # 初始化活跃变量集合
        for block in flow_graph.blocks.values():
            block.live_in.clear()
            block.live_out.clear()
        
        # 迭代计算活跃变量
        changed = True
        while changed:
            changed = False
            for block_label in reversed(list(flow_graph.blocks.keys())):
                block = flow_graph.blocks[block_label]
                
                # 计算live_out
                old_live_out = block.live_out.copy()
                block.live_out.clear()
                for successor_label in block.successors:
                    if successor_label in flow_graph.blocks:
                        successor = flow_graph.blocks[successor_label]
                        block.live_out.update(successor.live_in)
                
                # 计算live_in
                old_live_in = block.live_in.copy()
                block.live_in = block.live_out.copy()
                
                # 处理每条指令
                for instruction in reversed(block.instructions):
                    # 定义的变量从live_in中移除
                    defined_vars = self._get_defined_variables(instruction)
                    for var in defined_vars:
                        block.live_in.discard(var)
                    
                    # 使用的变量加入live_in
                    used_vars = self._get_used_variables(instruction)
                    block.live_in.update(used_vars)
                
                if old_live_in != block.live_in or old_live_out != block.live_out:
                    changed = True
    
    def _get_defined_variables(self, instruction: GeneratedInstruction) -> Set[str]:
        """获取指令定义的变量"""
        defined = set()
        
        # 根据指令类型判断定义的变量
        if instruction.mnemonic in ["mov", "add", "sub", "mul", "imul", "setl", "setle", "setg", "setge", "sete", "setne"]:
            if instruction.operands and len(instruction.operands) >= 1:
                dest = instruction.operands[0]
                if self._is_variable(dest):
                    defined.add(dest)
        
        return defined
    
    def _get_used_variables(self, instruction: GeneratedInstruction) -> Set[str]:
        """获取指令使用的变量"""
        used = set()
        
        # 根据指令类型判断使用的变量
        if instruction.mnemonic in ["mov", "add", "sub", "mul", "imul", "cmp", "test"]:
            for i, operand in enumerate(instruction.operands):
                # 第一个操作数通常是目标，但在某些指令中也会被使用
                if instruction.mnemonic in ["add", "sub", "mul", "imul"] and i == 0:
                    if self._is_variable(operand):
                        used.add(operand)
                elif i > 0 and self._is_variable(operand):
                    used.add(operand)
        
        return used
    
    def _is_variable(self, operand: str) -> bool:
        """判断操作数是否为变量"""
        if not operand or operand == "_":
            return False
        if operand.isdigit():
            return False
        if operand.startswith("#"):  # ARM64立即数
            return False
        if operand.startswith("[") or operand.endswith("]"):  # 内存引用
            return False
        if operand in ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "rsp", "rbp"] + [f"r{i}" for i in range(8, 16)]:
            return False  # x86-64寄存器
        if re.match(r"^[xw]\d+$", operand):  # ARM64寄存器
            return False
        return True
    
    def _advanced_register_allocation(self, func_name: str, flow_graph: FlowGraph):
        """高级寄存器分配"""
        # 构建干扰图
        self._build_interference_graph(flow_graph)
        
        # 图着色寄存器分配
        self._graph_coloring_allocation(func_name)
        
        # 应用寄存器分配结果
        self._apply_register_allocation(func_name)
    
    def _build_interference_graph(self, flow_graph: FlowGraph):
        """构建变量干扰图"""
        self.interference_graph.clear()
        
        # 收集所有变量
        all_variables = set()
        for block in flow_graph.blocks.values():
            all_variables.update(block.live_in)
            all_variables.update(block.live_out)
        
        # 初始化干扰图
        for var in all_variables:
            self.interference_graph[var] = set()
        
        # 构建干扰关系
        for block in flow_graph.blocks.values():
            # 在每个程序点，活跃的变量之间都有干扰关系
            live_vars = block.live_out.copy()
            
            for instruction in reversed(block.instructions):
                # 定义的变量与所有当前活跃变量干扰
                defined_vars = self._get_defined_variables(instruction)
                for def_var in defined_vars:
                    for live_var in live_vars:
                        if def_var != live_var:
                            self.interference_graph[def_var].add(live_var)
                            self.interference_graph[live_var].add(def_var)
                
                # 更新活跃变量集合
                live_vars -= defined_vars
                used_vars = self._get_used_variables(instruction)
                live_vars.update(used_vars)
    
    def _graph_coloring_allocation(self, func_name: str):
        """图着色寄存器分配算法"""
        self.register_coloring.clear()
        
        # 可用寄存器（简化）
        if self.config.target_architecture == TargetArchitecture.X86_64:
            available_registers = ["rax", "rbx", "rcx", "rdx", "rsi", "rdi", "r8", "r9"]
        else:
            available_registers = [f"x{i}" for i in range(0, 8)]
        
        # 简化的贪心着色算法
        variables = list(self.interference_graph.keys())
        variables.sort(key=lambda v: len(self.interference_graph[v]), reverse=True)
        
        for variable in variables:
            # 找到不与干扰变量冲突的寄存器
            used_registers = set()
            for interfering_var in self.interference_graph[variable]:
                if interfering_var in self.register_coloring:
                    used_registers.add(self.register_coloring[interfering_var])
            
            # 分配第一个可用寄存器
            for register in available_registers:
                if register not in used_registers:
                    self.register_coloring[variable] = register
                    break
            else:
                # 如果没有可用寄存器，溢出到内存
                self._allocate_stack_space(variable)
    
    def _apply_register_allocation(self, func_name: str):
        """应用寄存器分配结果"""
        # 更新寄存器分配映射
        for variable, register in self.register_coloring.items():
            self.register_allocation_map[variable] = register
            if register in self.registers:
                self.registers[register].status = self.registers[register].status  # 保持状态
                self.registers[register].variable = variable
    
    def _perform_optimizations(self):
        """执行优化通路"""
        total_result = OptimizationResult()
        
        for optimization_pass in self.optimization_passes:
            if optimization_pass == OptimizationPass.PEEPHOLE:
                result = self._peephole_optimization()
            elif optimization_pass == OptimizationPass.DEAD_CODE_ELIMINATION:
                result = self._dead_code_elimination()
            elif optimization_pass == OptimizationPass.CONSTANT_PROPAGATION:
                result = self._constant_propagation()
            elif optimization_pass == OptimizationPass.REGISTER_COALESCING:
                result = self._register_coalescing()
            elif optimization_pass == OptimizationPass.INSTRUCTION_SCHEDULING:
                result = self._instruction_scheduling()
            elif optimization_pass == OptimizationPass.ALGEBRAIC_SIMPLIFICATION:
                result = self._algebraic_simplification()
            else:
                continue
            
            # 累计优化结果
            total_result.instructions_eliminated += result.instructions_eliminated
            total_result.registers_saved += result.registers_saved
            total_result.memory_accesses_reduced += result.memory_accesses_reduced
            total_result.cycles_saved += result.cycles_saved
            total_result.optimizations_applied.extend(result.optimizations_applied)
        
        self.optimization_results["total"] = total_result
    
    def _peephole_optimization(self) -> OptimizationResult:
        """窥孔优化"""
        result = OptimizationResult()
        new_instructions = []
        i = 0
        
        while i < len(self.instructions):
            instruction = self.instructions[i]
            optimized = False
            
            # 优化模式1: 移除冗余移动 mov reg, reg
            if (instruction.mnemonic == "mov" and 
                len(instruction.operands) == 2 and 
                instruction.operands[0] == instruction.operands[1]):
                result.instructions_eliminated += 1
                result.optimizations_applied.append("冗余移动消除")
                optimized = True
            
            # 优化模式2: 常量折叠 mov reg, #imm1; add reg, #imm2 -> mov reg, #(imm1+imm2)
            elif (i + 1 < len(self.instructions) and
                  instruction.mnemonic == "mov" and
                  len(instruction.operands) == 2 and
                  instruction.operands[1].isdigit()):
                next_inst = self.instructions[i + 1]
                if (next_inst.mnemonic == "add" and
                    len(next_inst.operands) == 2 and
                    next_inst.operands[0] == instruction.operands[0] and
                    next_inst.operands[1].isdigit()):
                    
                    # 折叠常量
                    val1 = int(instruction.operands[1])
                    val2 = int(next_inst.operands[1])
                    new_val = val1 + val2
                    
                    new_instruction = GeneratedInstruction(
                        mnemonic="mov",
                        operands=[instruction.operands[0], str(new_val)],
                        comment="常量折叠优化"
                    )
                    new_instructions.append(new_instruction)
                    
                    result.instructions_eliminated += 1
                    result.optimizations_applied.append("常量折叠")
                    i += 2  # 跳过下一条指令
                    optimized = True
            
            if not optimized:
                new_instructions.append(instruction)
                i += 1
        
        self.instructions = new_instructions
        return result
    
    def _dead_code_elimination(self) -> OptimizationResult:
        """死代码消除"""
        result = OptimizationResult()
        
        # 标记被使用的指令
        used_instructions = set()
        
        # 从函数调用、返回语句、跳转等开始标记
        for i, instruction in enumerate(self.instructions):
            if instruction.mnemonic in ["call", "ret", "jmp", "je", "jne", "jl", "jg", "jle", "jge"]:
                used_instructions.add(i)
        
        # 反向数据流分析，标记产生这些指令所需数据的指令
        changed = True
        while changed:
            changed = False
            for i in range(len(self.instructions) - 1, -1, -1):
                if i in used_instructions:
                    instruction = self.instructions[i]
                    # 标记产生所需数据的指令
                    for used_var in self._get_used_variables(instruction):
                        for j in range(i - 1, -1, -1):
                            prev_inst = self.instructions[j]
                            if used_var in self._get_defined_variables(prev_inst):
                                if j not in used_instructions:
                                    used_instructions.add(j)
                                    changed = True
                                break
        
        # 移除未使用的指令
        new_instructions = []
        for i, instruction in enumerate(self.instructions):
            if i in used_instructions:
                new_instructions.append(instruction)
            else:
                result.instructions_eliminated += 1
                result.optimizations_applied.append("死代码消除")
        
        self.instructions = new_instructions
        return result
    
    def _constant_propagation(self) -> OptimizationResult:
        """常量传播"""
        result = OptimizationResult()
        constants = {}  # 变量 -> 常量值
        
        for instruction in self.instructions:
            # 检测常量赋值
            if (instruction.mnemonic == "mov" and 
                len(instruction.operands) == 2 and 
                instruction.operands[1].isdigit()):
                constants[instruction.operands[0]] = instruction.operands[1]
            
            # 传播常量
            for i, operand in enumerate(instruction.operands):
                if operand in constants:
                    instruction.operands[i] = constants[operand]
                    result.optimizations_applied.append("常量传播")
            
            # 检查变量是否被重新定义
            defined_vars = self._get_defined_variables(instruction)
            for var in defined_vars:
                if var in constants and instruction.mnemonic != "mov":
                    del constants[var]
        
        return result
    
    def _register_coalescing(self) -> OptimizationResult:
        """寄存器合并"""
        result = OptimizationResult()
        
        # 寻找可以合并的寄存器分配
        coalescing_candidates = []
        
        for instruction in self.instructions:
            if (instruction.mnemonic == "mov" and 
                len(instruction.operands) == 2):
                src, dst = instruction.operands
                if (self._is_variable(src) and self._is_variable(dst) and
                    src in self.register_allocation_map and 
                    dst in self.register_allocation_map):
                    coalescing_candidates.append((src, dst))
        
        # 执行合并
        for src_var, dst_var in coalescing_candidates:
            if (src_var not in self.interference_graph or 
                dst_var not in self.interference_graph.get(src_var, set())):
                # 可以合并
                src_reg = self.register_allocation_map[src_var]
                self.register_allocation_map[dst_var] = src_reg
                result.registers_saved += 1
                result.optimizations_applied.append("寄存器合并")
        
        return result
    
    def _instruction_scheduling(self) -> OptimizationResult:
        """指令调度"""
        result = OptimizationResult()
        
        # 简单的指令重排，将不相关的指令提前
        scheduled_instructions = []
        i = 0
        
        while i < len(self.instructions):
            current_inst = self.instructions[i]
            scheduled_instructions.append(current_inst)
            
            # 寻找可以与当前指令并行执行的指令
            for j in range(i + 1, min(i + 4, len(self.instructions))):
                candidate = self.instructions[j]
                if self._can_execute_in_parallel(current_inst, candidate):
                    # 可以重排
                    scheduled_instructions.append(candidate)
                    self.instructions.pop(j)
                    result.cycles_saved += 1
                    result.optimizations_applied.append("指令调度")
                    break
            
            i += 1
        
        self.instructions = scheduled_instructions
        return result
    
    def _can_execute_in_parallel(self, inst1: GeneratedInstruction, inst2: GeneratedInstruction) -> bool:
        """检查两条指令是否可以并行执行"""
        # 简化的并行性检查
        def1 = self._get_defined_variables(inst1)
        use1 = self._get_used_variables(inst1)
        def2 = self._get_defined_variables(inst2)
        use2 = self._get_used_variables(inst2)
        
        # 检查数据依赖
        if def1 & use2 or def2 & use1 or def1 & def2:
            return False
        
        # 检查特殊指令
        if inst1.mnemonic in ["call", "ret", "jmp"] or inst2.mnemonic in ["call", "ret", "jmp"]:
            return False
        
        return True
    
    def _algebraic_simplification(self) -> OptimizationResult:
        """代数简化"""
        result = OptimizationResult()
        
        for instruction in self.instructions:
            # 简化 add reg, 0 -> nop
            if (instruction.mnemonic == "add" and 
                len(instruction.operands) == 2 and 
                instruction.operands[1] == "0"):
                instruction.mnemonic = "nop"
                instruction.operands = []
                result.optimizations_applied.append("加零消除")
            
            # 简化 mul reg, 1 -> nop
            elif (instruction.mnemonic in ["mul", "imul"] and 
                  len(instruction.operands) == 2 and 
                  instruction.operands[1] == "1"):
                instruction.mnemonic = "nop"
                instruction.operands = []
                result.optimizations_applied.append("乘一消除")
            
            # 简化 mul reg, 0 -> mov reg, 0
            elif (instruction.mnemonic in ["mul", "imul"] and 
                  len(instruction.operands) == 2 and 
                  instruction.operands[1] == "0"):
                instruction.mnemonic = "mov"
                instruction.operands = [instruction.operands[0], "0"]
                result.optimizations_applied.append("乘零简化")
        
        return result
    
    def _update_performance_metrics(self, func_name: str):
        """更新性能指标"""
        metrics = {
            "instruction_count": len([inst for inst in self.instructions if inst.mnemonic != "nop"]),
            "register_usage": len(self.register_allocation_map),
            "memory_operations": len([inst for inst in self.instructions if "[" in str(inst)]),
            "branches": len([inst for inst in self.instructions if inst.mnemonic.startswith("j")]),
            "function_calls": len([inst for inst in self.instructions if inst.mnemonic == "call"])
        }
        
        self.performance_metrics[func_name] = metrics
    
    def _generate_optimization_report(self):
        """生成优化报告"""
        if "total" in self.optimization_results:
            result = self.optimization_results["total"]
            
            print("\n=== 优化报告 ===")
            print(f"消除指令数: {result.instructions_eliminated}")
            print(f"节省寄存器数: {result.registers_saved}")
            print(f"减少内存访问: {result.memory_accesses_reduced}")
            print(f"节省周期数: {result.cycles_saved}")
            print(f"应用的优化: {', '.join(set(result.optimizations_applied))}")
            
            print("\n=== 性能指标 ===")
            for func_name, metrics in self.performance_metrics.items():
                print(f"函数 {func_name}:")
                for metric, value in metrics.items():
                    print(f"  {metric}: {value}")
    
    def get_enhanced_statistics(self) -> Dict[str, Any]:
        """获取增强的统计信息"""
        base_stats = super().get_statistics()
        
        enhanced_stats = {
            **base_stats,
            "optimization_passes": len(self.optimization_passes),
            "basic_blocks": sum(len(fg.blocks) for fg in self.flow_graphs.values()),
            "interference_edges": sum(len(neighbors) for neighbors in self.interference_graph.values()) // 2,
            "optimizations_applied": len(set(
                opt for result in self.optimization_results.values() 
                for opt in result.optimizations_applied
            )),
            "performance_metrics": self.performance_metrics
        }
        
        return enhanced_stats
    
    def save_debug_information(self, output_dir: str):
        """保存调试信息"""
        import os
        import json
        
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存控制流图
        flow_graph_data = {}
        for func_name, flow_graph in self.flow_graphs.items():
            flow_graph_data[func_name] = {
                "blocks": {
                    label: {
                        "instructions": [str(inst) for inst in block.instructions],
                        "predecessors": list(block.predecessors),
                        "successors": list(block.successors),
                        "live_in": list(block.live_in),
                        "live_out": list(block.live_out)
                    }
                    for label, block in flow_graph.blocks.items()
                },
                "entry_block": flow_graph.entry_block,
                "exit_blocks": list(flow_graph.exit_blocks)
            }
        
        with open(os.path.join(output_dir, "flow_graphs.json"), "w", encoding="utf-8") as f:
            json.dump(flow_graph_data, f, indent=2, ensure_ascii=False)
        
        # 保存干扰图
        interference_data = {
            var: list(neighbors) for var, neighbors in self.interference_graph.items()
        }
        with open(os.path.join(output_dir, "interference_graph.json"), "w", encoding="utf-8") as f:
            json.dump(interference_data, f, indent=2, ensure_ascii=False)
        
        # 保存寄存器分配
        with open(os.path.join(output_dir, "register_allocation.json"), "w", encoding="utf-8") as f:
            json.dump(self.register_coloring, f, indent=2, ensure_ascii=False)
        
        # 保存优化结果
        optimization_data = {}
        for key, result in self.optimization_results.items():
            optimization_data[key] = {
                "instructions_eliminated": result.instructions_eliminated,
                "registers_saved": result.registers_saved,
                "memory_accesses_reduced": result.memory_accesses_reduced,
                "cycles_saved": result.cycles_saved,
                "optimizations_applied": result.optimizations_applied
            }
        
        with open(os.path.join(output_dir, "optimization_results.json"), "w", encoding="utf-8") as f:
            json.dump(optimization_data, f, indent=2, ensure_ascii=False)

# 使用示例和测试函数
def test_enhanced_code_generator():
    """测试增强代码生成器"""
    from .target_code_config import PredefinedCodeGenConfigs
    
    # 创建测试四元式
    test_quadruples = {
        "main": [
            type("Quad", (), {"op": "=", "arg1": "10", "arg2": "_", "result": "x"})(),
            type("Quad", (), {"op": "=", "arg1": "5", "arg2": "_", "result": "y"})(),
            type("Quad", (), {"op": "+", "arg1": "x", "arg2": "y", "result": "z"})(),
            type("Quad", (), {"op": "return", "arg1": "z", "arg2": "_", "result": "_"})()
        ]
    }
    
    print("=== 测试增强目标代码生成器 ===")
    
    # 使用调试配置
    config = PredefinedCodeGenConfigs.debug_config()
    generator = EnhancedCodeGenerator(config)
    
    try:
        result = generator.generate(test_quadruples)
        print("生成的汇编代码:")
        print(result)
        
        print("\n增强统计信息:")
        stats = generator.get_enhanced_statistics()
        for key, value in stats.items():
            print(f"{key}: {value}")
            
    except Exception as e:
        print(f"代码生成失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_enhanced_code_generator()