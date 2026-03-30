import re

# 定义类Rust词法规则
TOKEN_TYPES = {
    'KEYWORDS': r'\b(?:i32|let|if|else|while|return|mut|fn|for|in|loop|break|continue)\b',
    'IDENTIFIER': r'\b[a-zA-Z_][a-zA-Z0-9_]*\b',
    'NUMBER': r'\b\d+\b',
    'SPECIAL_SYMBOLS': r'->|\.\.|\.',
    'OPERATORS': r'==|!=|>=|<=|[+\-*/<>]',
    'ASSIGNMENT': r'=',
    'DELIMITERS': r'[\(\)\{\}\[\]]',
    'SEPARATORS': r'[;:,]',
    'COMMENTS': r'//.*|/\*.*?\*/', 
    'WHITESPACE': r'\s+',
    'END': r'#'
}

token_regex = '|'.join([f'(?P<{key}>{val})' for key, val in TOKEN_TYPES.items()])

class RustLexer:
    def __init__(self):
        self.regex = re.compile(token_regex)

    def tokenize(self, code):
        line_number = 1
        position = 0
        tokens = []
        for match in re.finditer(self.regex, code):
            kind = match.lastgroup
            value = match.group()
            if kind == 'WHITESPACE' or kind == 'COMMENTS':
                continue  # 忽略空格与注释
            elif kind == 'END':
                break
            elif kind == 'IDENTIFIER' and value in ['i32', 'let', 'if', 'else', 'while', 'return', 'mut', 'fn', 'for', 'in', 'loop', 'break', 'continue']:
                kind = 'KEYWORDS'  # 修正识别为关键字
            else:
                tokens.append((kind, value, line_number, position))
            position += len(value)
            if '\n' in value:
                line_number += value.count('\n')
        return tokens
