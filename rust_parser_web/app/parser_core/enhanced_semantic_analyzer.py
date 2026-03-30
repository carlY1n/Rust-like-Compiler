from typing import Dict, List, Optional, Any, Set, Union
from dataclasses import dataclass, field
from enum import Enum, auto
import copy

class SymbolType(Enum):
    FUNCTION = auto()
    VARIABLE = auto()
    PARAMETER = auto()
    ARRAY = auto()
    STRUCT = auto()
    ENUM = auto()

class DataType(Enum):
    I32 = "i32"
    BOOL = "bool"
    CHAR = "char"
    STRING = "string"
    VOID = "void"
    ARRAY = "array"
    STRUCT = "struct"
    ENUM = "enum"
    FUNCTION = "function"

@dataclass
class TypeInfo:
    """类型信息，支持复合类型"""
    base_type: DataType
    element_type: Optional['TypeInfo'] = None  # 数组元素类型
    size: Optional[int] = None  # 数组大小
    struct_fields: Optional[Dict[str, 'TypeInfo']] = None  # 结构体字段
    param_types: Optional[List['TypeInfo']] = None  # 函数参数类型
    return_type: Optional['TypeInfo'] = None  # 函数返回类型
    
    def __str__(self):
        if self.base_type == DataType.ARRAY:
            return f"[{self.element_type}; {self.size}]"
        elif self.base_type == DataType.FUNCTION:
            params = ", ".join(str(p) for p in self.param_types or [])
            return f"fn({params}) -> {self.return_type}"
        return self.base_type.value
    
    def is_compatible(self, other: 'TypeInfo') -> bool:
        """检查类型兼容性"""
        if self.base_type != other.base_type:
            return False
        if self.base_type == DataType.ARRAY:
            return (self.element_type.is_compatible(other.element_type) and 
                   self.size == other.size)
        return True

@dataclass
class Symbol:
    name: str
    type: SymbolType
    data_type: TypeInfo
    is_mutable: bool
    scope_level: int
    offset: int
    is_initialized: bool = False
    is_used: bool = False  # 用于检测未使用变量
    declaration_line: int = 0  # 声明行号
    is_const: bool = False  # 常量标记
    initial_value: Any = None  # 常量初始值

class Scope:
    def __init__(self, parent: Optional['Scope'] = None, scope_type: str = "block"):
        self.symbols: Dict[str, Symbol] = {}
        self.parent = parent
        self.level = 0 if parent is None else parent.level + 1
        self.temp_counter = 0
        self.offset = 0
        self.scope_type = scope_type  # "block", "function", "loop"
        self.children: List['Scope'] = []
        if parent:
            parent.children.append(self)

    def define(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            raise SemanticError(f"Symbol '{symbol.name}' already defined in current scope")
        symbol.scope_level = self.level
        symbol.offset = self.offset
        # 根据类型计算大小
        size = self._calculate_type_size(symbol.data_type)
        self.offset += size
        self.symbols[symbol.name] = symbol

    def _calculate_type_size(self, type_info: TypeInfo) -> int:
        """计算类型大小"""
        if type_info.base_type == DataType.I32:
            return 4
        elif type_info.base_type == DataType.BOOL:
            return 1
        elif type_info.base_type == DataType.CHAR:
            return 1
        elif type_info.base_type == DataType.ARRAY:
            element_size = self._calculate_type_size(type_info.element_type)
            return element_size * (type_info.size or 0)
        elif type_info.base_type == DataType.STRUCT:
            total_size = 0
            for field_type in (type_info.struct_fields or {}).values():
                total_size += self._calculate_type_size(field_type)
            return total_size
        return 4  # 默认大小

    def resolve(self, name: str) -> Optional[Symbol]:
        symbol = self.symbols.get(name)
        if symbol is not None:
            symbol.is_used = True  # 标记为已使用
            return symbol
        if self.parent is not None:
            return self.parent.resolve(name)
        return None

    def new_temp(self) -> str:
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp

    def get_unused_variables(self) -> List[Symbol]:
        """获取未使用的变量"""
        unused = []
        for symbol in self.symbols.values():
            if (symbol.type == SymbolType.VARIABLE and 
                not symbol.is_used and 
                not symbol.name.startswith('_')):  # 下划线开头的变量允许未使用
                unused.append(symbol)
        return unused

class Quadruple:
    def __init__(self, op: str, arg1: str, arg2: str, result: str, line: int = 0):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result
        self.line = line  # 对应源代码行号

    def __str__(self) -> str:
        return f"({self.op}, {self.arg1}, {self.arg2}, {self.result})"

class SemanticError(Exception):
    def __init__(self, message: str, line: int = 0):
        self.message = message
        self.line = line
        super().__init__(f"Line {line}: {message}" if line else message)

class Warning:
    def __init__(self, message: str, line: int = 0, warning_type: str = "general"):
        self.message = message
        self.line = line
        self.warning_type = warning_type

class EnhancedSemanticAnalyzer:
    def __init__(self):
        self.current_scope = Scope()
        self.quadruples: List[Quadruple] = []
        self.next_label = 0
        self.current_function: Optional[str] = None
        self.function_blocks: Dict[str, List[Quadruple]] = {}
        self.current_block: List[Quadruple] = []
        self.current_line = 0
        
        # 增强功能
        self.warnings: List[Warning] = []
        self.loop_stack: List[str] = []  # 循环标签栈，用于break/continue
        self.type_table: Dict[str, TypeInfo] = {}  # 用户定义类型表
        self.constant_table: Dict[str, Any] = {}  # 常量表
        self.optimization_enabled = True  # 是否启用优化
        self.dead_code_elimination = True  # 死代码消除
        
        # 内置类型
        self._init_builtin_types()

    def _init_builtin_types(self):
        """初始化内置类型"""
        self.type_table.update({
            "i32": TypeInfo(DataType.I32),
            "bool": TypeInfo(DataType.BOOL),
            "char": TypeInfo(DataType.CHAR),
            "string": TypeInfo(DataType.STRING),
            "void": TypeInfo(DataType.VOID)
        })

    def add_warning(self, message: str, warning_type: str = "general", line: int = None):
        """添加警告"""
        self.warnings.append(Warning(message, line or self.current_line, warning_type))

    def new_label(self) -> str:
        label = f"L{self.next_label}"
        self.next_label += 1
        return label

    def emit(self, op: str, arg1: str = "_", arg2: str = "_", result: str = "_") -> None:
        """生成四元式并添加到当前函数块"""
        quad = Quadruple(op, arg1, arg2, result, self.current_line)
        self.current_block.append(quad)

    def enter_scope(self, scope_type: str = "block") -> None:
        self.current_scope = Scope(self.current_scope, scope_type)

    def exit_scope(self) -> None:
        if self.current_scope.parent is None:
            raise SemanticError("Cannot exit global scope")
        
        # 检查未使用的变量
        unused_vars = self.current_scope.get_unused_variables()
        for var in unused_vars:
            self.add_warning(f"Unused variable '{var.name}'", "unused_variable", var.declaration_line)
        
        self.current_scope = self.current_scope.parent

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, Any]:
        """主要分析入口点"""
        if ast["type"] != "program":
            raise SemanticError("Expected program node")
        
        # 清空之前的分析结果
        self._reset_analyzer()
        
        # 第一遍：收集所有函数声明和类型定义
        self._collect_declarations(ast["declarations"])
        
        # 第二遍：分析函数体
        for decl in ast["declarations"]:
            if decl["type"] == "function_header":
                self.analyze_function_declaration(decl)
        
        # 生成优化后的代码
        if self.optimization_enabled:
            self._optimize_code()
        
        return {
            "function_blocks": self.function_blocks,
            "warnings": [{"message": w.message, "line": w.line, "type": w.warning_type} 
                        for w in self.warnings],
            "type_table": {name: str(type_info) for name, type_info in self.type_table.items()},
            "constant_table": self.constant_table
        }

    def _reset_analyzer(self):
        """重置分析器状态"""
        self.function_blocks = {}
        self.current_scope = Scope()
        self.next_label = 0
        self.current_function = None
        self.warnings = []
        self.loop_stack = []
        self.constant_table = {}
        self._init_builtin_types()

    def _collect_declarations(self, declarations: List[Dict[str, Any]]):
        """收集所有声明信息"""
        for decl in declarations:
            if decl["type"] == "function_header":
                self._register_function(decl)
            # 这里可以扩展支持结构体、枚举等类型声明

    def _register_function(self, func: Dict[str, Any]):
        """注册函数符号"""
        func_name = func["name"]
        
        # 构建函数类型信息
        param_types = []
        for param in func.get("parameters", []):
            param_type = self._parse_type_info(param["param_type"])
            param_types.append(param_type)
        
        return_type = TypeInfo(DataType.VOID)
        if "return_type" in func:
            return_type = self._parse_type_info(func["return_type"])
        
        func_type = TypeInfo(
            DataType.FUNCTION,
            param_types=param_types,
            return_type=return_type
        )
        
        func_symbol = Symbol(
            name=func_name,
            type=SymbolType.FUNCTION,
            data_type=func_type,
            is_mutable=False,
            scope_level=0,
            offset=0
        )
        self.current_scope.define(func_symbol)

    def _parse_type_info(self, type_node: Dict[str, Any]) -> TypeInfo:
        """解析类型信息"""
        if isinstance(type_node, dict) and "value" in type_node:
            type_str = type_node["value"]
        else:
            type_str = str(type_node)
        
        # 基本类型映射
        type_mapping = {
            "i32": DataType.I32,
            "bool": DataType.BOOL,
            "char": DataType.CHAR,
            "string": DataType.STRING,
            "void": DataType.VOID
        }
        
        if type_str in type_mapping:
            return TypeInfo(type_mapping[type_str])
        
        # 这里可以扩展处理数组、结构体等复合类型
        return TypeInfo(DataType.I32)  # 默认类型

    def analyze_function_declaration(self, func: Dict[str, Any]) -> None:
        """分析函数声明"""
        func_name = func["name"]
        self.current_function = func_name
        
        # 创建新的函数块
        self.current_block = []
        self.function_blocks[func_name] = self.current_block
        
        # 生成函数入口标签
        self.emit("label", f"func_{func_name}")
        
        # 进入函数作用域
        self.enter_scope("function")
        
        # 分析参数
        for param in func.get("parameters", []):
            self.analyze_parameter(param)
        
        # 分析函数体
        if "body" in func:
            self.analyze_statement_block(func["body"])
        else:
            raise SemanticError(f"Function '{func_name}' has no body")
        
        # 检查返回值
        self._check_function_return(func)
        
        # 退出函数作用域
        self.exit_scope()
        self.current_function = None

    def _check_function_return(self, func: Dict[str, Any]):
        """检查函数返回值"""
        func_name = func["name"]
        has_return_type = "return_type" in func
        
        # 检查是否有return语句
        has_return = any(quad.op == "return" for quad in self.current_block)
        
        if has_return_type and not has_return:
            self.add_warning(f"Function '{func_name}' should return a value", "missing_return")
        elif not has_return_type and func_name != "main":
            # 为非main函数添加默认return
            self.emit("return")

    def analyze_parameter(self, param: Dict[str, Any]) -> None:
        """分析函数参数"""
        var_decl = param["variable"]
        param_name = var_decl["identifier"]
        param_type = self._parse_type_info(param["param_type"])
        
        param_symbol = Symbol(
            name=param_name,
            type=SymbolType.PARAMETER,
            data_type=param_type,
            is_mutable=var_decl["mutable"],
            scope_level=self.current_scope.level,
            offset=self.current_scope.offset,
            is_initialized=True,
            declaration_line=self.current_line
        )
        self.current_scope.define(param_symbol)

    def analyze_statement_block(self, block: Dict[str, Any]) -> None:
        """分析语句块"""
        if block["type"] != "statement_block":
            raise SemanticError(f"Expected statement block, got {block['type']}")
        
        self.enter_scope("block")
        for stmt in block["statements"]:
            self.analyze_statement(stmt)
        self.exit_scope()

    def analyze_statement(self, stmt: Dict[str, Any]) -> None:
        """分析单个语句"""
        stmt_type = stmt["type"]
        
        statement_handlers = {
            "variable_declaration_statement": self.analyze_variable_declaration,
            "assignment_statement": self.analyze_assignment,
            "if_statement": self.analyze_if_statement,
            "while_statement": self.analyze_while_statement,
            "for_statement": self.analyze_for_statement,
            "loop_statement": self.analyze_loop_statement,
            "break_statement": self.analyze_break_statement,
            "continue_statement": self.analyze_continue_statement,
            "return_statement": self.analyze_return_statement,
            "expression_statement": self.analyze_expression_statement,
            "empty_statement": lambda x: None
        }
        
        handler = statement_handlers.get(stmt_type)
        if handler:
            handler(stmt)
        else:
            raise SemanticError(f"Unsupported statement type: {stmt_type}")

    def analyze_variable_declaration(self, stmt: Dict[str, Any]) -> None:
        """分析变量声明语句"""
        var_decl = stmt["variable"]
        var_name = var_decl["identifier"]
        
        # 检查变量名冲突
        if self.current_scope.symbols.get(var_name):
            raise SemanticError(f"Variable '{var_name}' already defined in current scope")
        
        # 解析类型
        var_type = TypeInfo(DataType.I32)  # 默认类型
        if "var_type" in stmt:
            var_type = self._parse_type_info(stmt["var_type"])
        
        # 创建变量符号
        var_symbol = Symbol(
            name=var_name,
            type=SymbolType.VARIABLE,
            data_type=var_type,
            is_mutable=var_decl["mutable"],
            scope_level=self.current_scope.level,
            offset=self.current_scope.offset,
            declaration_line=self.current_line
        )
        
        # 处理初始化
        if "initializer" in stmt:
            init_value = self.analyze_expression(stmt["initializer"])
            
            # 类型检查
            init_type = self._infer_expression_type(stmt["initializer"])
            if not var_type.is_compatible(init_type):
                raise SemanticError(f"Type mismatch in variable '{var_name}' initialization")
            
            # 常量折叠
            if self._is_constant_expression(stmt["initializer"]):
                const_value = self._evaluate_constant_expression(stmt["initializer"])
                var_symbol.initial_value = const_value
                var_symbol.is_const = not var_decl["mutable"]
                if var_symbol.is_const:
                    self.constant_table[var_name] = const_value
            
            self.emit("=", init_value, "_", var_name)
            var_symbol.is_initialized = True
        elif "var_type" in stmt:
            # 有类型声明但没有初始化
            self.emit("=", "0", "_", var_name)
            var_symbol.is_initialized = True
        
        self.current_scope.define(var_symbol)

    def analyze_assignment(self, stmt: Dict[str, Any]) -> None:
        """分析赋值语句"""
        target = stmt["target"]["identifier"]
        target_symbol = self.current_scope.resolve(target)
        
        if not target_symbol:
            raise SemanticError(f"Undefined variable '{target}'")
        if not target_symbol.is_mutable:
            raise SemanticError(f"Cannot assign to immutable variable '{target}'")
        if target_symbol.is_const:
            raise SemanticError(f"Cannot assign to constant variable '{target}'")
        
        # 类型检查
        expr_type = self._infer_expression_type(stmt["expression"])
        if not target_symbol.data_type.is_compatible(expr_type):
            raise SemanticError(f"Type mismatch in assignment to '{target}'")
        
        value = self.analyze_expression(stmt["expression"])
        self.emit("=", value, "_", target)
        target_symbol.is_initialized = True

    def analyze_for_statement(self, stmt: Dict[str, Any]) -> None:
        """分析for循环语句"""
        start_label = self.new_label()
        end_label = self.new_label()
        continue_label = self.new_label()
        
        # 进入循环作用域
        self.enter_scope("loop")
        self.loop_stack.append(end_label)
        
        # 分析循环变量
        var_decl = stmt["variable"]
        var_name = var_decl["identifier"]
        
        # 分析迭代范围
        iterable = stmt["iterable"]
        if iterable["type"] == "range":
            start_val = self.analyze_expression(iterable["start"])
            end_val = self.analyze_expression(iterable["end"])
            
            # 初始化循环变量
            var_symbol = Symbol(
                name=var_name,
                type=SymbolType.VARIABLE,
                data_type=TypeInfo(DataType.I32),
                is_mutable=True,
                scope_level=self.current_scope.level,
                offset=self.current_scope.offset,
                is_initialized=True,
                declaration_line=self.current_line
            )
            self.current_scope.define(var_symbol)
            
            self.emit("=", start_val, "_", var_name)
            
            # 循环条件检查
            self.emit("label", start_label)
            temp_cond = self.current_scope.new_temp()
            self.emit("<", var_name, end_val, temp_cond)
            self.emit("if_false", temp_cond, "_", end_label)
            
            # 循环体
            self.analyze_statement_block(stmt["body"])
            
            # 循环变量递增
            self.emit("label", continue_label)
            temp_inc = self.current_scope.new_temp()
            self.emit("+", var_name, "1", temp_inc)
            self.emit("=", temp_inc, "_", var_name)
            self.emit("goto", "_", "_", start_label)
        
        self.emit("label", end_label)
        self.loop_stack.pop()
        self.exit_scope()

    def analyze_break_statement(self, stmt: Dict[str, Any]) -> None:
        """分析break语句"""
        if not self.loop_stack:
            raise SemanticError("Break statement not in loop")
        
        break_label = self.loop_stack[-1]
        self.emit("goto", "_", "_", break_label)

    def analyze_continue_statement(self, stmt: Dict[str, Any]) -> None:
        """分析continue语句"""
        if not self.loop_stack:
            raise SemanticError("Continue statement not in loop")
        
        # 这里简化处理，跳转到循环开始
        continue_label = self.loop_stack[-1].replace("end", "start")
        self.emit("goto", "_", "_", continue_label)

    def analyze_if_statement(self, stmt: Dict[str, Any]) -> None:
        """分析if语句"""
        condition = self.analyze_expression(stmt["condition"])
        
        # 类型检查：条件必须是布尔类型
        cond_type = self._infer_expression_type(stmt["condition"])
        if cond_type.base_type not in [DataType.BOOL, DataType.I32]:  # 允许i32作为条件
            self.add_warning("Condition should be boolean type", "type_warning")
        
        false_label = self.new_label()
        end_label = self.new_label()
        
        self.emit("if_false", condition, "_", false_label)
        self.analyze_statement_block(stmt["then_branch"])
        
        if "else_branch" in stmt:
            self.emit("goto", "_", "_", end_label)
            self.emit("label", false_label)
            self.analyze_statement_block(stmt["else_branch"])
            self.emit("label", end_label)
        else:
            self.emit("label", false_label)

    def analyze_while_statement(self, stmt: Dict[str, Any]) -> None:
        """分析while循环语句"""
        start_label = self.new_label()
        end_label = self.new_label()
        
        self.loop_stack.append(end_label)
        
        self.emit("label", start_label)
        condition = self.analyze_expression(stmt["condition"])
        self.emit("if_false", condition, "_", end_label)
        
        self.enter_scope("loop")
        self.analyze_statement_block(stmt["body"])
        self.exit_scope()
        
        self.emit("goto", "_", "_", start_label)
        self.emit("label", end_label)
        
        self.loop_stack.pop()

    def analyze_loop_statement(self, stmt: Dict[str, Any]) -> None:
        """分析无限循环语句"""
        start_label = self.new_label()
        end_label = self.new_label()
        
        self.loop_stack.append(end_label)
        
        self.emit("label", start_label)
        self.enter_scope("loop")
        self.analyze_statement_block(stmt["body"])
        self.exit_scope()
        
        self.emit("goto", "_", "_", start_label)
        self.emit("label", end_label)
        
        self.loop_stack.pop()

    def analyze_return_statement(self, stmt: Dict[str, Any]) -> None:
        """分析return语句"""
        if not self.current_function:
            raise SemanticError("Return statement outside of function")
        
        func_symbol = self.current_scope.resolve(self.current_function)
        expected_return_type = func_symbol.data_type.return_type
        
        if "expression" in stmt:
            value = self.analyze_expression(stmt["expression"])
            expr_type = self._infer_expression_type(stmt["expression"])
            
            # 类型检查
            if not expected_return_type.is_compatible(expr_type):
                raise SemanticError(f"Return type mismatch in function '{self.current_function}'")
            
            self.emit("return", value)
        else:
            if expected_return_type.base_type != DataType.VOID:
                raise SemanticError(f"Function '{self.current_function}' must return a value")
            self.emit("return")

    def analyze_expression_statement(self, stmt: Dict[str, Any]) -> None:
        """分析表达式语句"""
        self.analyze_expression(stmt["expression"])

    def analyze_expression(self, expr: Dict[str, Any]) -> str:
        """分析表达式并返回结果临时变量"""
        expr_type = expr["type"]
        
        if expr_type == "number_literal":
            return str(expr["value"])
            
        elif expr_type == "identifier":
            name = expr["name"]
            symbol = self.current_scope.resolve(name)
            if not symbol:
                raise SemanticError(f"Undefined variable '{name}'")
            if not symbol.is_initialized and symbol.type != SymbolType.PARAMETER:
                raise SemanticError(f"Variable '{name}' used before initialization")
            return name
            
        elif expr_type == "binary_expression":
            left = self.analyze_expression(expr["left"])
            right = self.analyze_expression(expr["right"])
            
            # 类型检查
            left_type = self._infer_expression_type(expr["left"])
            right_type = self._infer_expression_type(expr["right"])
            if not left_type.is_compatible(right_type):
                self.add_warning("Operand type mismatch", "type_warning")
            
            # 常量折叠优化
            if (self._is_constant_expression(expr["left"]) and 
                self._is_constant_expression(expr["right"])):
                result = self._evaluate_constant_expression(expr)
                return str(result)
            
            temp = self.current_scope.new_temp()
            self.emit(expr["operator"], left, right, temp)
            return temp
            
        elif expr_type == "function_call":
            return self.analyze_function_call(expr)
            
        else:
            raise SemanticError(f"Unsupported expression type: {expr_type}")

    def analyze_function_call(self, call: Dict[str, Any]) -> str:
        """分析函数调用"""
        func_name = call["function"]
        func_symbol = self.current_scope.resolve(func_name)
        
        if not func_symbol or func_symbol.type != SymbolType.FUNCTION:
            raise SemanticError(f"Undefined function '{func_name}'")
        
        # 参数类型检查
        expected_params = func_symbol.data_type.param_types or []
        actual_args = call["arguments"]
        
        if len(expected_params) != len(actual_args):
            raise SemanticError(f"Function '{func_name}' expects {len(expected_params)} arguments, got {len(actual_args)}")
        
        # 分析参数并检查类型
        args = []
        for i, (expected_type, arg) in enumerate(zip(expected_params, actual_args)):
            arg_value = self.analyze_expression(arg)
            arg_type = self._infer_expression_type(arg)
            
            if not expected_type.is_compatible(arg_type):
                raise SemanticError(f"Argument {i+1} type mismatch in call to '{func_name}'")
            
            args.append(arg_value)
        
        # 生成调用代码
        result_temp = self.current_scope.new_temp()
        
        for arg in args:
            self.emit("param", arg)
        
        self.emit("call", f"func_{func_name}", str(len(args)), result_temp)
        return result_temp

    def _infer_expression_type(self, expr: Dict[str, Any]) -> TypeInfo:
        """推断表达式类型"""
        expr_type = expr["type"]
        
        if expr_type == "number_literal":
            return TypeInfo(DataType.I32)
            
        elif expr_type == "identifier":
            name = expr["name"]
            symbol = self.current_scope.resolve(name)
            if symbol:
                return symbol.data_type
            return TypeInfo(DataType.I32)  # 默认类型
            
        elif expr_type == "binary_expression":
            left_type = self._infer_expression_type(expr["left"])
            right_type = self._infer_expression_type(expr["right"])
            
            # 比较运算符返回布尔类型
            if expr["operator"] in ["<", "<=", ">", ">=", "==", "!="]:
                return TypeInfo(DataType.BOOL)
            
            # 算术运算符保持操作数类型
            return left_type if left_type.is_compatible(right_type) else TypeInfo(DataType.I32)
            
        elif expr_type == "function_call":
            func_name = expr["function"]
            func_symbol = self.current_scope.resolve(func_name)
            if func_symbol and func_symbol.data_type.return_type:
                return func_symbol.data_type.return_type
            return TypeInfo(DataType.VOID)
            
        return TypeInfo(DataType.I32)  # 默认类型

    def _is_constant_expression(self, expr: Dict[str, Any]) -> bool:
        """检查是否为常量表达式"""
        expr_type = expr["type"]
        
        if expr_type == "number_literal":
            return True
            
        elif expr_type == "identifier":
            name = expr["name"]
            symbol = self.current_scope.resolve(name)
            return symbol and symbol.is_const
            
        elif expr_type == "binary_expression":
            return (self._is_constant_expression(expr["left"]) and 
                   self._is_constant_expression(expr["right"]))
            
        return False

    def _evaluate_constant_expression(self, expr: Dict[str, Any]) -> Any:
        """计算常量表达式的值"""
        expr_type = expr["type"]
        
        if expr_type == "number_literal":
            return expr["value"]
            
        elif expr_type == "identifier":
            name = expr["name"]
            if name in self.constant_table:
                return self.constant_table[name]
            return 0
            
        elif expr_type == "binary_expression":
            left_val = self._evaluate_constant_expression(expr["left"])
            right_val = self._evaluate_constant_expression(expr["right"])
            op = expr["operator"]
            
            # 算术运算
            if op == "+":
                return left_val + right_val
            elif op == "-":
                return left_val - right_val
            elif op == "*":
                return left_val * right_val
            elif op == "/":
                return left_val // right_val if right_val != 0 else 0
            elif op == "<":
                return 1 if left_val < right_val else 0
            elif op == "<=":
                return 1 if left_val <= right_val else 0
            elif op == ">":
                return 1 if left_val > right_val else 0
            elif op == ">=":
                return 1 if left_val >= right_val else 0
            elif op == "==":
                return 1 if left_val == right_val else 0
            elif op == "!=":
                return 1 if left_val != right_val else 0
                
        return 0

    def _optimize_code(self):
        """代码优化"""
        if not self.optimization_enabled:
            return
            
        for func_name, quads in self.function_blocks.items():
            optimized_quads = []
            
            # 常量传播和死代码消除
            i = 0
            while i < len(quads):
                quad = quads[i]
                
                # 跳过死代码（unreachable code）
                if self.dead_code_elimination and self._is_dead_code(quads, i):
                    self.add_warning(f"Unreachable code in function '{func_name}'", "dead_code")
                    i += 1
                    continue
                
                # 常量传播
                if quad.op == "=" and quad.arg1.isdigit():
                    # 记录常量赋值
                    self._propagate_constant(quads, i, quad.result, quad.arg1)
                
                # 代数简化
                if quad.op in ["+", "-", "*", "/"]:
                    optimized_quad = self._algebraic_simplification(quad)
                    if optimized_quad != quad:
                        optimized_quads.append(optimized_quad)
                        i += 1
                        continue
                
                optimized_quads.append(quad)
                i += 1
            
            self.function_blocks[func_name] = optimized_quads

    def _is_dead_code(self, quads: List[Quadruple], index: int) -> bool:
        """检查是否为死代码"""
        if index == 0:
            return False
            
        prev_quad = quads[index - 1]
        current_quad = quads[index]
        
        # 如果前一条指令是无条件跳转或return，且当前不是标签，则为死代码
        if (prev_quad.op in ["goto", "return"] and 
            current_quad.op != "label"):
            return True
            
        return False

    def _propagate_constant(self, quads: List[Quadruple], start_index: int, var_name: str, constant_value: str):
        """常量传播"""
        for i in range(start_index + 1, len(quads)):
            quad = quads[i]
            
            # 如果变量被重新赋值，停止传播
            if quad.result == var_name:
                break
                
            # 替换使用该变量的地方
            if quad.arg1 == var_name:
                quad.arg1 = constant_value
            if quad.arg2 == var_name:
                quad.arg2 = constant_value

    def _algebraic_simplification(self, quad: Quadruple) -> Quadruple:
        """代数简化"""
        op = quad.op
        arg1 = quad.arg1
        arg2 = quad.arg2
        
        # 常量折叠
        if arg1.isdigit() and arg2.isdigit():
            val1, val2 = int(arg1), int(arg2)
            
            if op == "+":
                result_val = val1 + val2
            elif op == "-":
                result_val = val1 - val2
            elif op == "*":
                result_val = val1 * val2
            elif op == "/" and val2 != 0:
                result_val = val1 // val2
            else:
                return quad
                
            return Quadruple("=", str(result_val), "_", quad.result, quad.line)
        
        # 代数恒等式优化
        if op == "+":
            if arg1 == "0":
                return Quadruple("=", arg2, "_", quad.result, quad.line)
            if arg2 == "0":
                return Quadruple("=", arg1, "_", quad.result, quad.line)
        elif op == "*":
            if arg1 == "0" or arg2 == "0":
                return Quadruple("=", "0", "_", quad.result, quad.line)
            if arg1 == "1":
                return Quadruple("=", arg2, "_", quad.result, quad.line)
            if arg2 == "1":
                return Quadruple("=", arg1, "_", quad.result, quad.line)
        elif op == "-":
            if arg2 == "0":
                return Quadruple("=", arg1, "_", quad.result, quad.line)
        elif op == "/":
            if arg2 == "1":
                return Quadruple("=", arg1, "_", quad.result, quad.line)
        
        return quad

    def check_semantic_rules(self) -> List[str]:
        """额外的语义规则检查"""
        errors = []
        
        # 检查main函数是否存在
        if not self.current_scope.resolve("main"):
            errors.append("Missing main function")
        
        # 检查函数是否都有返回值（如果需要的话）
        for func_name, quads in self.function_blocks.items():
            func_symbol = self.current_scope.resolve(func_name)
            if (func_symbol and 
                func_symbol.data_type.return_type.base_type != DataType.VOID and
                not any(q.op == "return" for q in quads)):
                errors.append(f"Function '{func_name}' missing return statement")
        
        return errors

    def generate_symbol_table_report(self) -> Dict[str, Any]:
        """生成符号表报告"""
        def collect_symbols(scope: Scope) -> Dict[str, Any]:
            scope_info = {
                "level": scope.level,
                "type": scope.scope_type,
                "symbols": {},
                "children": []
            }
            
            for name, symbol in scope.symbols.items():
                scope_info["symbols"][name] = {
                    "type": symbol.type.name,
                    "data_type": str(symbol.data_type),
                    "is_mutable": symbol.is_mutable,
                    "is_initialized": symbol.is_initialized,
                    "is_used": symbol.is_used,
                    "offset": symbol.offset,
                    "declaration_line": symbol.declaration_line
                }
            
            for child in scope.children:
                scope_info["children"].append(collect_symbols(child))
            
            return scope_info
        
        return collect_symbols(self.current_scope)

    def get_analysis_summary(self) -> Dict[str, Any]:
        """获取分析摘要"""
        total_quads = sum(len(quads) for quads in self.function_blocks.values())
        error_count = len([w for w in self.warnings if w.warning_type == "error"])
        warning_count = len([w for w in self.warnings if w.warning_type != "error"])
        
        return {
            "total_functions": len(self.function_blocks),
            "total_quadruples": total_quads,
            "total_errors": error_count,
            "total_warnings": warning_count,
            "optimization_enabled": self.optimization_enabled,
            "constants_found": len(self.constant_table)
        }