from .Lexer import RustLexer
from .Parser import RustParser
from .semantic_analyzer import SemanticAnalyzer, SemanticError
from .enhanced_code_generator import EnhancedCodeGenerator  # 新增导入
from .target_code_config import CodeGeneratorConfig, PredefinedCodeGenConfigs  # 新增导入
import json
import os

def save_ast_to_json(ast, filename):
    """Save AST to a JSON file"""
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(ast, f, ensure_ascii=False, indent=2)

def save_quadruples_to_json(quadruples, filename):
    """Save quadruples to a JSON file"""
    # 将函数块转换为可序列化的格式
    serializable_quads = {
        func_name: [
            {
                "op": q.op,
                "arg1": q.arg1,
                "arg2": q.arg2,
                "result": q.result
            }
            for q in quads
        ]
        for func_name, quads in quadruples.items()
    }
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(serializable_quads, f, ensure_ascii=False, indent=2)

def save_target_code_to_file(target_code, filename):
    """Save target code to a file"""
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(target_code)

def analyze_code(code):
    # Lexical analysis
    lexer = RustLexer()
    tokens = lexer.tokenize(code)

    token_lines = [
        f'{i}: [{t[0]}] "{t[1]}" at line {t[2]}, position {t[3]}'
        for i, t in enumerate(tokens)
    ]

    # Syntax analysis
    parser = RustParser(tokens)
    try:
        ast = parser.parse()
        
        # Semantic analysis and intermediate code generation
        semantic_analyzer = SemanticAnalyzer()
        try:
            quadruples = semantic_analyzer.analyze(ast)
            
            # 将四元式转换为可序列化的格式
            serializable_quads = {
                func_name: [
                    {
                        "op": q.op,
                        "arg1": q.arg1,
                        "arg2": q.arg2,
                        "result": q.result
                    }
                    for q in quads
                ]
                for func_name, quads in quadruples.items()
            }
            
            # 新增：目标代码生成
            target_code = ""
            codegen_error = None
            try:
                # 创建代码生成器配置（使用调试配置以获得更多注释）
                config = PredefinedCodeGenConfigs.debug_config()
                
                # 创建代码生成器
                code_generator = EnhancedCodeGenerator(config)
                
                # 生成目标代码
                target_code = code_generator.generate(quadruples)
                
            except Exception as e:
                codegen_error = f"Target code generation error: {str(e)}"
                print(f"目标代码生成失败: {e}")  # 调试信息
            
            # Save files
            output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'static', 'output')
            os.makedirs(output_dir, exist_ok=True)
            
            ast_path = os.path.join(output_dir, 'ast.json')
            save_ast_to_json(ast, ast_path)
            
            quad_path = os.path.join(output_dir, 'quadruples.json')
            save_quadruples_to_json(quadruples, quad_path)
            
            # 保存目标代码
            if target_code:
                target_code_path = os.path.join(output_dir, 'target_code.s')
                save_target_code_to_file(target_code, target_code_path)
            
            return {
                "tokens": token_lines,
                "ast": ast,
                "quadruples": serializable_quads,
                "target_code": target_code,  # 新增
                "codegen_error": codegen_error,  # 新增
                "error": None
            }
            
        except SemanticError as e:
            return {
                "tokens": token_lines,
                "ast": ast,
                "quadruples": None,
                "target_code": "",  # 新增
                "codegen_error": None,  # 新增
                "error": f"Semantic error: {str(e)}"
            }
            
    except SyntaxError as e:
        return {
            "tokens": token_lines,
            "ast": None,
            "quadruples": None,
            "target_code": "",  # 新增
            "codegen_error": None,  # 新增
            "error": f"Syntax error: {str(e)}"
        }