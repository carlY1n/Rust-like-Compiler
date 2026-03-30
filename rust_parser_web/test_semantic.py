from app.parser_core.analyzer import analyze_code
import json

def test_semantic_analysis():
    # 读取测试文件
    with open('test/semantic_test.rs', 'r', encoding='utf-8') as f:
        code = f.read()
    
    # 运行分析
    result = analyze_code(code)
    
    # 打印词法分析结果
    print("\n=== 词法分析结果 ===")
    for token in result["tokens"]:
        print(token)
    
    # 打印语法分析结果（AST）
    print("\n=== 语法分析结果 (AST) ===")
    print(json.dumps(result["ast"], indent=2, ensure_ascii=False))
    
    # 打印语义分析结果（四元式）
    print("\n=== 语义分析结果 (四元式) ===")
    if result["quadruples"]:
        for func_name, quads in result["quadruples"].items():
            print(f"\n{func_name} 函数的四元式:")
            for i, quad in enumerate(quads):
                print(f"{i}: {quad}")
    else:
        print("没有生成四元式")
    
    # 打印错误信息（如果有）
    if result["error"]:
        print("\n=== 错误信息 ===")
        print(result["error"])

if __name__ == "__main__":
    test_semantic_analysis() 