class RustParser:
    def __init__(self, tokens):
        self.tokens = tokens
        self.pos = 0
        self.current_token = None
        self.next_token()

    def next_token(self):
        if self.pos < len(self.tokens):
            self.current_token = self.tokens[self.pos]
            self.pos += 1
        else:
            self.current_token = None
        return self.current_token

    def peek_token(self, offset=0):
        if self.pos + offset < len(self.tokens):
            return self.tokens[self.pos + offset]
        return None

    def match(self, expected_type=None, expected_value=None):
        if self.current_token is None:
            raise SyntaxError(f"Unexpected end of input, expected {expected_type}")
        
        token_type, token_value, line, position = self.current_token
        
        if expected_type and token_type != expected_type:
            raise SyntaxError(f"Expected {expected_type}, got {token_type} at line {line}, position {position}")
        
        if expected_value and token_value != expected_value:
            raise SyntaxError(f"Expected '{expected_value}', got '{token_value}' at line {line}, position {position}")
        
        current = self.current_token
        self.next_token()
        return current

    # 0.1 变量声明内部
    def parse_variable_declaration_inner(self):
        # <变量声明内部> -> mut <ID> | <ID>
        result = {"type": "variable_declaration_inner"}
        
        if self.current_token and self.current_token[1] == 'mut':
            result["mutable"] = True
            self.match('KEYWORDS', 'mut')
            token_type, token_value, line, position = self.match('IDENTIFIER')
            result["identifier"] = token_value
        else:
            # 6.1 声明不可变变量
            token_type, token_value, line, position = self.match('IDENTIFIER')
            result["mutable"] = False
            result["identifier"] = token_value
            
        return result

    # 0.2 类型
    def parse_type(self):
        # <类型> -> i32
        result = {"type": "type_specifier"}
        token_type, token_value, line, position = self.match('KEYWORDS', 'i32')
        result["value"] = token_value
        return result

    # 0.3 可赋值元素
    def parse_assignable_element(self):
        # <可赋值元素> -> <ID>
        result = {"type": "assignable_element"}
        token_type, token_value, line, position = self.match('IDENTIFIER')
        result["identifier"] = token_value
        return result

    # 1.1 基础程序
    def parse_program(self):
        # Program -> <声明串>
        result = {"type": "program", "declarations": []}
        result["declarations"] = self.parse_declaration_list()
        return result

    def parse_declaration_list(self):
        # <声明串> -> 空 | <声明> <声明串>
        declarations = []
        
        while self.current_token is not None:
            declarations.append(self.parse_declaration())
            
        return declarations

    def parse_declaration(self):
        # <声明> -> <函数声明>
        if self.current_token and self.current_token[1] == 'fn':
            return self.parse_function_declaration()
        else:
            raise SyntaxError(f"Expected function declaration, got {self.current_token[1] if self.current_token else 'end of input'}")

    def parse_function_declaration(self):
        # <函数声明> -> <函数头声明> <语句块>
        result = {"type": "function_declaration"}
        
        # 解析函数头
        header = self.parse_function_header()
        result.update(header)  # 合并函数头信息
        
        # 解析函数体
        result["body"] = self.parse_statement_block()
        
        return result

    def parse_function_header(self):
        # <函数头声明> -> fn<ID> '(' <形参列表> ')' 
        # 1.5 函数输出 -> fn<ID> '(' <形参列表> ')' '->' <类型>
        result = {"type": "function_header"}
        
        self.match('KEYWORDS', 'fn')
        token_type, token_value, line, position = self.match('IDENTIFIER')
        result["name"] = token_value
        
        self.match('DELIMITERS', '(')
        result["parameters"] = self.parse_param_list()
        self.match('DELIMITERS', ')')
        
        # 检查是否有返回类型
        if self.current_token and self.current_token[1] == '->':
            self.match('SPECIAL_SYMBOLS', '->')
            result["return_type"] = self.parse_type()
        
        return result

    def parse_param_list(self):
        # <形参列表> -> 空
        # 1.4 函数输入 -> <形参> | <形参> ',' <形参列表>
        params = []
        
        # 空形参列表情况
        if self.current_token and self.current_token[1] == ')':
            return params
            
        # 有形参的情况
        params.append(self.parse_param())
        
        while self.current_token and self.current_token[1] == ',':
            self.match('SEPARATORS', ',')
            params.append(self.parse_param())
            
        return params

    def parse_param(self):
        # <形参> -> <变量声明内部> ':' <类型>
        result = {"type": "parameter"}
        
        result["variable"] = self.parse_variable_declaration_inner()
        self.match('SEPARATORS', ':')
        result["param_type"] = self.parse_type()
        
        return result

    def parse_statement_block(self):
        # <语句块> -> '{' <语句串> '}'
        result = {"type": "statement_block", "statements": []}
        
        self.match('DELIMITERS', '{')
        result["statements"] = self.parse_statement_list()
        self.match('DELIMITERS', '}')
        
        return result

    # 1.2 语句
    def parse_statement_list(self):
        # <语句串> -> 空 | <语句> <语句串>
        statements = []
        
        while self.current_token and self.current_token[1] != '}':
            statements.append(self.parse_statement())
            
        return statements

    def parse_statement(self):
        # <语句> -> ';' | <返回语句> | <变量声明语句> | <表达式> ';' | <赋值语句> | <if语句> | <循环语句> | break ';' | continue ';'
        
        if not self.current_token:
            raise SyntaxError("Unexpected end of input")
            
        token_type, token_value, line, position = self.current_token
        
        # 处理空语句
        if token_value == ';':
            self.match('SEPARATORS', ';')
            return {"type": "empty_statement"}
            
        # 处理return语句
        elif token_value == 'return':
            return self.parse_return_statement()
            
        # 处理let变量声明
        elif token_value == 'let':
            return self.parse_variable_declaration_statement()
            
        # 处理if语句
        elif token_value == 'if':
            return self.parse_if_statement()
            
        # 处理循环语句
        elif token_value in ['while', 'for', 'loop']:
            return self.parse_loop_statement()
            
        # 处理break
        elif token_value == 'break':
            self.match('KEYWORDS', 'break')
            self.match('SEPARATORS', ';')
            return {"type": "break_statement"}
            
        # 处理continue
        elif token_value == 'continue':
            self.match('KEYWORDS', 'continue')
            self.match('SEPARATORS', ';')
            return {"type": "continue_statement"}
            
        # 处理赋值语句或表达式语句
        else:
            # 通过向前看一个token来区分赋值语句和表达式语句
            if self.is_assignable_element() and self.peek_token() and self.peek_token()[1] == '=':
                return self.parse_assignment_statement()
            else:
                return self.parse_expression_statement()

    def is_assignable_element(self):
        if not self.current_token:
            return False
        token_type, token_value, line, position = self.current_token
        return token_type == 'IDENTIFIER'

    # 1.3 返回语句
    def parse_return_statement(self):
        # <返回语句> -> return ';'
        # 1.5 函数输出 -> return <表达式> ';'
        result = {"type": "return_statement"}
        
        self.match('KEYWORDS', 'return')
        
        # 检查是否有返回表达式
        if self.current_token and self.current_token[1] != ';':
            result["expression"] = self.parse_expression()
            
        self.match('SEPARATORS', ';')
        
        return result

    # 2.1 变量声明语句
    def parse_variable_declaration_statement(self):
        # <变量声明语句> -> let <变量声明内部> ':' <类型> ';'
        # <变量声明语句> -> let <变量声明内部> ';'
        result = {"type": "variable_declaration_statement"}
        
        self.match('KEYWORDS', 'let')
        result["variable"] = self.parse_variable_declaration_inner()
        
        # 检查是否有类型声明
        if self.current_token and self.current_token[1] == ':':
            self.match('SEPARATORS', ':')
            result["var_type"] = self.parse_type()
            
        # 检查是否有初始值
        if self.current_token and self.current_token[1] == '=':
            self.match('ASSIGNMENT', '=')
            result["initializer"] = self.parse_expression()
            
        self.match('SEPARATORS', ';')
        
        return result

    # 2.2 赋值语句
    def parse_assignment_statement(self):
        # <赋值语句> -> <可赋值元素> '=' <表达式> ';'
        result = {"type": "assignment_statement"}
        
        result["target"] = self.parse_assignable_element()
        self.match('ASSIGNMENT', '=')
        result["expression"] = self.parse_expression()
        self.match('SEPARATORS', ';')
        
        return result

    # 3.1 & 3.2 & 3.3 表达式相关
    def parse_expression_statement(self):
        # <语句> -> <表达式> ';'
        result = {"type": "expression_statement"}
        
        result["expression"] = self.parse_expression()
        self.match('SEPARATORS', ';')
        
        return result

    def parse_expression(self):
        # <表达式> -> <加法表达式> | <表达式> <比较运算符> <加法表达式> | <函数表达式语句块>
        
        # 检查是否是函数表达式块
        if self.current_token and self.current_token[1] == '{':
            return self.parse_function_expression_block()
            
        result = self.parse_additive_expression()
        
        # 检查是否有比较运算符
        if self.current_token and self.current_token[1] in ['<', '<=', '>', '>=', '==', '!=']:
            operator = self.parse_comparison_operator()
            right = self.parse_additive_expression()
            
            return {
                "type": "binary_expression",
                "operator": operator,
                "left": result,
                "right": right
            }
            
        return result

    def parse_comparison_operator(self):
        # <比较运算符> -> '<' | '<=' | '>' | '>=' | '==' | '!='
        token_type, token_value, line, position = self.match('OPERATORS')
        return token_value

    def parse_additive_expression(self):
        # <加法表达式> -> <项> | <加法表达式> <加减运算符> <项>
        result = self.parse_term()
        
        while self.current_token and self.current_token[1] in ['+', '-']:
            operator = self.parse_additive_operator()
            right = self.parse_term()
            
            result = {
                "type": "binary_expression",
                "operator": operator,
                "left": result,
                "right": right
            }
            
        return result

    def parse_additive_operator(self):
        # <加减运算符> -> '+' | '-'
        token_type, token_value, line, position = self.match('OPERATORS')
        return token_value

    def parse_term(self):
        # <项> -> <因子> | <项> <乘除运算符> <因子>
        result = self.parse_factor()
        
        while self.current_token and self.current_token[1] in ['*', '/']:
            operator = self.parse_multiplicative_operator()
            right = self.parse_factor()
            
            result = {
                "type": "binary_expression",
                "operator": operator,
                "left": result,
                "right": right
            }
            
        return result

    def parse_multiplicative_operator(self):
        # <乘除运算符> -> '*' | '/'
        token_type, token_value, line, position = self.match('OPERATORS')
        return token_value

    def parse_factor(self):
        # <因子> -> <元素>
        return self.parse_element()

    def parse_element(self):
        # <元素> -> <NUM> | <可赋值元素> | '(' <表达式> ')' | <ID> '(' <实参列表> ')'
        
        if not self.current_token:
            raise SyntaxError("Unexpected end of input")
            
        token_type, token_value, line, position = self.current_token
        
        # 处理数字
        if token_type == 'NUMBER':
            self.match('NUMBER')
            return {"type": "number_literal", "value": int(token_value)}
            
        # 处理括号表达式
        elif token_value == '(':
            self.match('DELIMITERS', '(')
            expr = self.parse_expression()
            self.match('DELIMITERS', ')')
            return expr
            
        # 处理函数调用或标识符
        elif token_type == 'IDENTIFIER':
            identifier = token_value
            self.next_token()
            
            # 检查是否是函数调用
            if self.current_token and self.current_token[1] == '(':
                self.match('DELIMITERS', '(')
                args = self.parse_argument_list()
                self.match('DELIMITERS', ')')
                
                return {
                    "type": "function_call",
                    "function": identifier,
                    "arguments": args
                }
            else:
                # 普通标识符
                return {"type": "identifier", "name": identifier}
        
        else:
            raise SyntaxError(f"Unexpected token {token_value} at line {line}, position {position}")

    def parse_argument_list(self):
        # <实参列表> -> 空 | <表达式> | <表达式> ',' <实参列表>
        args = []
        
        # 空参数列表情况
        if self.current_token and self.current_token[1] == ')':
            return args
            
        # 有参数的情况
        args.append(self.parse_expression())
        
        while self.current_token and self.current_token[1] == ',':
            self.match('SEPARATORS', ',')
            args.append(self.parse_expression())
            
        return args

    # 4.1 选择结构
    def parse_if_statement(self):
        # <if语句> -> if <表达式> <语句块> <else部分>
        result = {"type": "if_statement"}
        
        self.match('KEYWORDS', 'if')
        result["condition"] = self.parse_expression()
        result["then_branch"] = self.parse_statement_block()
        
        # 检查是否有else部分
        if self.current_token and self.current_token[1] == 'else':
            result["else_branch"] = self.parse_else_part()
            
        return result

    def parse_else_part(self):
        # <else部分> -> 空 | else <语句块>
        self.match('KEYWORDS', 'else')
        return self.parse_statement_block()

    # 5.1 & 5.2 & 5.3 循环结构
    def parse_loop_statement(self):
        # <循环语句> -> <while语句> | <for语句> | <loop语句>
        
        if not self.current_token:
            raise SyntaxError("Unexpected end of input")
            
        token_type, token_value, line, position = self.current_token
        
        if token_value == 'while':
            return self.parse_while_statement()
        elif token_value == 'for':
            return self.parse_for_statement()
        elif token_value == 'loop':
            return self.parse_loop_loop_statement()
        else:
            raise SyntaxError(f"Expected loop keyword, got {token_value} at line {line}, position {position}")

    def parse_while_statement(self):
        # <while语句> -> while <表达式> <语句块>
        result = {"type": "while_statement"}
        
        self.match('KEYWORDS', 'while')
        result["condition"] = self.parse_expression()
        result["body"] = self.parse_statement_block()
        
        return result

    def parse_for_statement(self):
        # <for语句> -> for <变量声明内部> in <可迭代结构> <语句块>
        result = {"type": "for_statement"}
        
        self.match('KEYWORDS', 'for')
        result["variable"] = self.parse_variable_declaration_inner()
        self.match('KEYWORDS', 'in')
        result["iterable"] = self.parse_iterable_structure()
        result["body"] = self.parse_statement_block()
        
        return result

    def parse_iterable_structure(self):
        # <可迭代结构> -> <表达式> '..' <表达式>
        result = {"type": "range"}
        
        result["start"] = self.parse_expression()
        self.match('SPECIAL_SYMBOLS', '..')
        result["end"] = self.parse_expression()
        
        return result

    def parse_loop_loop_statement(self):
        # <loop语句> -> loop <语句块>
        result = {"type": "loop_statement"}
        
        self.match('KEYWORDS', 'loop')
        result["body"] = self.parse_statement_block()
        
        return result

    # 7.1 函数表达式块
    def parse_function_expression_block(self):
        # <函数表达式语句块> -> '{' <函数表达式语句串> '}'
        result = {"type": "function_expression_block", "statements": []}
        
        self.match('DELIMITERS', '{')
        
        # 解析语句，除了最后一个
        while self.current_token and self.current_token[1] != '}':
            # 检查是否是最后一个表达式（没有分号结尾）
            if self.peek_token() and self.peek_token()[1] == '}' and self.current_token[1] != ';':
                result["return_expression"] = self.parse_expression()
                break
            else:
                result["statements"].append(self.parse_statement())
                
        self.match('DELIMITERS', '}')
        
        return result

    # 主解析函数
    def parse(self):
        return self.parse_program()