from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum, auto

class SymbolType(Enum):
    FUNCTION = auto()
    VARIABLE = auto()
    PARAMETER = auto()

@dataclass
class Symbol:
    name: str
    type: SymbolType
    data_type: str  # For now just 'i32'
    is_mutable: bool
    scope_level: int
    offset: int  # For stack frame allocation
    is_initialized: bool = False

class Scope:
    def __init__(self, parent: Optional['Scope'] = None):
        self.symbols: Dict[str, Symbol] = {}
        self.parent = parent
        self.level = 0 if parent is None else parent.level + 1
        self.temp_counter = 0
        self.offset = 0

    def define(self, symbol: Symbol) -> None:
        if symbol.name in self.symbols:
            raise SemanticError(f"Symbol '{symbol.name}' already defined in current scope")
        symbol.scope_level = self.level
        symbol.offset = self.offset
        self.offset += 4  # Assuming 4 bytes for i32
        self.symbols[symbol.name] = symbol

    def resolve(self, name: str) -> Optional[Symbol]:
        symbol = self.symbols.get(name)
        if symbol is not None:
            return symbol
        if self.parent is not None:
            return self.parent.resolve(name)
        return None

    def new_temp(self) -> str:
        temp = f"t{self.temp_counter}"
        self.temp_counter += 1
        return temp

class Quadruple:
    def __init__(self, op: str, arg1: str, arg2: str, result: str):
        self.op = op
        self.arg1 = arg1
        self.arg2 = arg2
        self.result = result

    def __str__(self) -> str:
        return f"({self.op}, {self.arg1}, {self.arg2}, {self.result})"

class SemanticError(Exception):
    pass

class SemanticAnalyzer:
    def __init__(self):
        self.current_scope = Scope()
        self.quadruples: List[Quadruple] = []
        self.next_label = 0
        self.current_function: Optional[str] = None
        self.function_blocks: Dict[str, List[Quadruple]] = {}  # 存储每个函数的四元式
        self.current_block: List[Quadruple] = []  # 当前正在生成的函数块

    def new_label(self) -> str:
        label = f"L{self.next_label}"
        self.next_label += 1
        return label

    def emit(self, op: str, arg1: str, arg2: str, result: str) -> None:
        """生成四元式并添加到当前函数块"""
        quad = Quadruple(op, arg1, arg2, result)
        self.current_block.append(quad)

    def enter_scope(self) -> None:
        self.current_scope = Scope(self.current_scope)

    def exit_scope(self) -> None:
        if self.current_scope.parent is None:
            raise SemanticError("Cannot exit global scope")
        self.current_scope = self.current_scope.parent

    def analyze(self, ast: Dict[str, Any]) -> Dict[str, List[Quadruple]]:
        """Main entry point for semantic analysis and code generation"""
        if ast["type"] != "program":
            raise SemanticError("Expected program node")
        
        # 清空之前的分析结果
        self.function_blocks = {}
        self.current_scope = Scope()
        self.next_label = 0
        self.current_function = None
        
        # 分析所有声明
        for decl in ast["declarations"]:
            if decl["type"] == "function_header":
                # 先注册函数符号
                func_name = decl["name"]
                func_symbol = Symbol(
                    name=func_name,
                    type=SymbolType.FUNCTION,
                    data_type=decl.get("return_type", {}).get("value", "void"),
                    is_mutable=False,
                    scope_level=0,
                    offset=0
                )
                self.current_scope.define(func_symbol)
        
        # 分析每个函数
        for decl in ast["declarations"]:
            if decl["type"] == "function_header":
                self.analyze_function_declaration(decl)
        
        return self.function_blocks

    def analyze_function_declaration(self, func: Dict[str, Any]) -> None:
        """Analyze a function declaration"""
        func_name = func["name"]
        self.current_function = func_name
        
        # 创建新的函数块
        self.current_block = []
        self.function_blocks[func_name] = self.current_block
        
        # 生成函数入口标签
        self.emit("label", f"func_{func_name}", "_", "_")
        
        # 进入函数作用域
        self.enter_scope()
        
        # 分析参数
        for param in func.get("parameters", []):
            self.analyze_parameter(param)
        
        # 分析函数体
        if "body" in func:
            self.analyze_statement_block(func["body"])
        else:
            raise SemanticError(f"Function '{func_name}' has no body")
        
        # 如果函数没有显式的return语句，且返回类型不是void，添加默认return
        if func_name != "main":
            func_symbol = self.current_scope.resolve(func_name)
            if func_symbol and func_symbol.data_type != "void":
                # 检查最后一个语句是否是return
                if not self.current_block or self.current_block[-1].op != "return":
                    self.emit("return", "0", "_", "_")  # 默认返回0
        
        # 退出函数作用域
        self.exit_scope()
        self.current_function = None

    def analyze_parameter(self, param: Dict[str, Any]) -> None:
        """Analyze a function parameter"""
        var_decl = param["variable"]
        param_name = var_decl["identifier"]
        
        param_symbol = Symbol(
            name=param_name,
            type=SymbolType.PARAMETER,
            data_type=param["param_type"]["value"],
            is_mutable=var_decl["mutable"],
            scope_level=self.current_scope.level,
            offset=self.current_scope.offset,
            is_initialized=True  # 参数总是被初始化的
        )
        self.current_scope.define(param_symbol)

    def analyze_statement_block(self, block: Dict[str, Any]) -> None:
        """Analyze a statement block"""
        if block["type"] != "statement_block":
            raise SemanticError(f"Expected statement block, got {block['type']}")
        
        self.enter_scope()
        for stmt in block["statements"]:
            self.analyze_statement(stmt)
        self.exit_scope()

    def analyze_statement(self, stmt: Dict[str, Any]) -> None:
        """Analyze a single statement"""
        stmt_type = stmt["type"]
        
        if stmt_type == "variable_declaration_statement":
            self.analyze_variable_declaration(stmt)
        elif stmt_type == "assignment_statement":
            self.analyze_assignment(stmt)
        elif stmt_type == "if_statement":
            self.analyze_if_statement(stmt)
        elif stmt_type == "while_statement":
            self.analyze_while_statement(stmt)
        elif stmt_type == "return_statement":
            self.analyze_return_statement(stmt)
        elif stmt_type == "expression_statement":
            self.analyze_expression_statement(stmt)
        elif stmt_type == "empty_statement":
            pass  # 空语句不需要处理
        else:
            raise SemanticError(f"Unsupported statement type: {stmt_type}")

    def analyze_variable_declaration(self, stmt: Dict[str, Any]) -> None:
        """Analyze a variable declaration statement"""
        var_decl = stmt["variable"]
        var_name = var_decl["identifier"]
        
        # 检查变量是否已定义
        if self.current_scope.resolve(var_name):
            raise SemanticError(f"Variable '{var_name}' already defined in current scope")
        
        # 创建变量符号
        var_symbol = Symbol(
            name=var_name,
            type=SymbolType.VARIABLE,
            data_type=stmt.get("var_type", {}).get("value", "i32"),
            is_mutable=var_decl["mutable"],
            scope_level=self.current_scope.level,
            offset=self.current_scope.offset
        )
        self.current_scope.define(var_symbol)
        
        # 处理初始化
        if "initializer" in stmt:
            # 直接使用表达式的结果，避免生成额外的临时变量
            init_value = self.analyze_expression(stmt["initializer"])
            self.emit("=", init_value, "_", var_name)
            var_symbol.is_initialized = True
        elif "var_type" in stmt:
            # 有类型声明但没有初始化，直接初始化为0
            self.emit("=", "0", "_", var_name)
            var_symbol.is_initialized = True

    def analyze_assignment(self, stmt: Dict[str, Any]) -> None:
        """Analyze an assignment statement"""
        target = stmt["target"]["identifier"]
        target_symbol = self.current_scope.resolve(target)
        
        if not target_symbol:
            raise SemanticError(f"Undefined variable '{target}'")
        if not target_symbol.is_mutable:
            raise SemanticError(f"Cannot assign to immutable variable '{target}'")
        
        # 直接使用表达式的结果，避免生成额外的临时变量
        value = self.analyze_expression(stmt["expression"])
        self.emit("=", value, "_", target)
        target_symbol.is_initialized = True

    def analyze_if_statement(self, stmt: Dict[str, Any]) -> None:
        """Analyze an if statement and generate code"""
        # Generate condition code
        condition = self.analyze_expression(stmt["condition"])
        false_label = self.new_label()
        end_label = self.new_label()
        
        # Emit conditional jump
        self.emit("if_false", condition, "_", false_label)
        
        # Generate then branch
        self.analyze_statement_block(stmt["then_branch"])
        
        if "else_branch" in stmt:
            # If there's an else branch, jump to end after then branch
            self.emit("goto", "_", "_", end_label)
            # Emit false label and else branch
            self.emit("label", false_label, "_", "_")
            self.analyze_statement_block(stmt["else_branch"])
            # Emit end label
            self.emit("label", end_label, "_", "_")
        else:
            # If no else branch, just emit false label
            self.emit("label", false_label, "_", "_")

    def analyze_while_statement(self, stmt: Dict[str, Any]) -> None:
        """Analyze a while statement and generate code"""
        start_label = self.new_label()
        end_label = self.new_label()
        
        # Emit start label
        self.emit("label", start_label, "_", "_")
        
        # Generate condition code
        condition = self.analyze_expression(stmt["condition"])
        
        # Emit conditional jump to end
        self.emit("if_false", condition, "_", end_label)
        
        # Generate loop body
        self.analyze_statement_block(stmt["body"])
        
        # Jump back to start
        self.emit("goto", "_", "_", start_label)
        
        # Emit end label
        self.emit("label", end_label, "_", "_")

    def analyze_return_statement(self, stmt: Dict[str, Any]) -> None:
        """Analyze a return statement"""
        if not self.current_function:
            raise SemanticError("Return statement outside of function")
        
        if "expression" in stmt:
            value = self.analyze_expression(stmt["expression"])
            # 检查返回类型是否匹配
            func_symbol = self.current_scope.resolve(self.current_function)
            if func_symbol.data_type != "void":
                self.emit("return", value, "_", "_")
            else:
                raise SemanticError(f"Function '{self.current_function}' declared as void but returns a value")
        else:
            # 检查函数是否声明为void
            func_symbol = self.current_scope.resolve(self.current_function)
            if func_symbol.data_type != "void":
                raise SemanticError(f"Function '{self.current_function}' must return a value")
            self.emit("return", "_", "_", "_")

    def analyze_expression_statement(self, stmt: Dict[str, Any]) -> None:
        """Analyze an expression statement"""
        self.analyze_expression(stmt["expression"])

    def analyze_expression(self, expr: Dict[str, Any]) -> str:
        """Analyze an expression and return the temporary holding its value"""
        expr_type = expr["type"]
        
        if expr_type == "number_literal":
            # 对于字面量，直接返回其值，让调用者决定是否需要临时变量
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
            temp = self.current_scope.new_temp()
            self.emit(expr["operator"], left, right, temp)
            return temp
            
        elif expr_type == "function_call":
            return self.analyze_function_call(expr)
            
        else:
            raise SemanticError(f"Unsupported expression type: {expr_type}")

    def analyze_function_call(self, call: Dict[str, Any]) -> str:
        """Analyze a function call and return the temporary holding its result"""
        func_name = call["function"]
        func_symbol = self.current_scope.resolve(func_name)
        
        if not func_symbol or func_symbol.type != SymbolType.FUNCTION:
            raise SemanticError(f"Undefined function '{func_name}'")
        
        # 分析参数
        args = []
        for arg in call["arguments"]:
            arg_value = self.analyze_expression(arg)
            args.append(arg_value)
        
        # 生成调用代码
        result_temp = self.current_scope.new_temp()
        
        # 生成参数传递代码
        for arg in args:
            self.emit("param", arg, "_", "_")
        
        # 生成函数调用代码
        self.emit("call", f"func_{func_name}", str(len(args)), result_temp)
        
        return result_temp 