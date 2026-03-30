# 🦀 Class-Rust Compiler  
*A complete compiler pipeline from source code to target assembly*

## Overview  
This project implements a **complete compiler** for a Rust-like programming language. It performs lexical analysis, syntax analysis, semantic checking, intermediate code generation (quadruples), and target code generation (x86-64 assembly). The compiler is built as a single-pass system with a web-based frontend for interactive visualization of the compilation process.

The compiler supports core Rust-style features: immutable and mutable variables, functions with parameters and return values, if-else conditionals, while/loop/for loops, break/continue statements, and static type checking. It produces efficient target code with basic optimizations like constant folding and algebraic simplification.

## Tech Stack  
| Layer          | Technology                                                      |
|----------------|------------------------------------------------------------------|
| Frontend       | Flask, HTML/CSS, JavaScript, D3.js                               |
| Backend        | Python 3, Custom lexer/parser, AST, semantic analyzer            |
| Code Generation| Python, x86-64 assembly (NASM syntax)                            |
| Testing        | Custom test suites, JUnit-style (Python unittest)                |
| Platform       | Cross-platform (Windows, Linux, macOS)                           |

## Core Features  

### Lexical Analysis
- Tokenizes Rust-like source code into a stream of tokens (keywords, identifiers, numbers, operators, separators).
- Handles whitespace and comments.
- Outputs token list with line and column positions.

<img width="299" height="453" alt="image" src="https://github.com/user-attachments/assets/2d2750bf-cb89-4a08-9f3f-f2f9e8904a6e" />

### Syntax Analysis
- Recursive‑descent parser constructs an **Abstract Syntax Tree (AST)**.
- Supports function definitions, variable declarations, statements, expressions.
- Detects and reports syntax errors with precise locations.

<img width="809" height="240" alt="image" src="https://github.com/user-attachments/assets/8cd944df-af0f-4f2b-85f7-e712adc56b85" />

### Semantic Analysis
- Implements **symbol tables** with nested scope support.
- Type checking for primitive types (`i32`, `bool`, `char`).
- Checks for: undeclared variables, duplicate definitions, type mismatches, invalid assignments to immutable variables, function argument count/type mismatches, return type consistency, and proper use of `break`/`continue` in loops.
- Tracks variable initialization to prevent use-before-initialize errors.

<img width="381" height="572" alt="image" src="https://github.com/user-attachments/assets/a95b9963-fe0a-43c9-9534-c4dd6568a459" />

### Intermediate Code Generation
- Translates AST into **quadruple** (three‑address code) representation: `(op, arg1, arg2, result)`.
- Generates code for arithmetic, logical, and relational operations, function calls, and control flow (labels, conditional jumps).
- Manages temporary variables and labels.

### Code Optimization
- **Constant folding** – computes constant expressions at compile time.
- **Algebraic simplification** – reduces expressions like `x + 0` → `x`.
- **Dead code elimination** – removes unreachable code.

### Target Code Generation
- Maps quadruples to **x86‑64 assembly** (NASM format).
- Implements a simple **register allocator** with LRU eviction and spilling to stack.
- Generates function prologue/epilogue, stack frame management.
- Supports arithmetic operations, comparisons, jumps, and function call conventions.

### Web Interface
- Upload `.rs` files through a Flask web app.
- Displays token list, AST as interactive D3.js tree, and generated target code.
- Supports downloading the generated assembly.

<img width="521" height="579" alt="image" src="https://github.com/user-attachments/assets/90ebc10f-ba85-48b3-882e-a2fcf9b5d94f" />

<img width="350" height="474" alt="image" src="https://github.com/user-attachments/assets/dc10ab6c-ad73-49bc-a541-f01fb43b0e50" />

<img width="505" height="320" alt="image" src="https://github.com/user-attachments/assets/a078d565-a5d0-451f-ad12-9fccbe124fd6" />

<img width="154" height="354" alt="image" src="https://github.com/user-attachments/assets/00833830-8971-47b7-97bd-87c77d0b1f60" />

## System Architecture  
```
Source File (.rs) ──► Flask Backend
│
▼
Lexer (Regex-based)
│
▼
Parser (Recursive Descent)
│
▼
AST (JSON)
│
▼
Semantic Analyzer & IR Generator
│
▼
Quadruple Sequence
│
▼
Target Code Generator
│
▼
x86-64 Assembly (.asm)
```

## Key Modules  

| Module | Description |
|--------|-------------|
| `lexer.py` | Tokenizer using regular expressions, produces token stream. |
| `parser.py` | Recursive‑descent parser, builds AST nodes for each production. |
| `ast.py` | AST node definitions (Program, FunctionDecl, Statement, Expression, etc.). |
| `semantic.py` | Symbol tables, scope management, type checking, error reporting. |
| `ir_generator.py` | Quadruple generation with temporary variables and labels. |
| `optimizer.py` | Constant folding, algebraic simplification, dead code elimination. |
| `codegen.py` | x86‑64 assembly generation with register allocation and stack management. |
| `web_app.py` | Flask routes, file handling, rendering results. |

## Testing & Results  

The compiler was tested against **30+ test cases** covering:

- Lexical and syntax correctness.
- Semantic errors (undeclared variables, type mismatches, return type violations, etc.).
- Intermediate code generation.
- Target code generation.

All test cases passed successfully. The web interface allows uploading test files and viewing outputs.

### Sample Output (Target Code for `fn add(a: i32, b: i32) -> i32 { a + b }`):
```asm
add:
    push rbp
    mov rbp, rsp
    ; function body
    mov eax, [rbp+16]    ; a
    add eax, [rbp+24]    ; b
    pop rbp
    ret
```

## How to Run
### Prerequisites
Python 3.8+

Flask (pip install flask)

(Optional) NASM for assembling generated code

### Start the Web Server
```bash
cd rust_parser_web
python app.py
Open http://localhost:5000 in your browser.
```

### Run from Command Line
```bash
python analyze.py sample.rs
```

## Project Structure
```
rust_parser_web/
├── app.py                 # Flask application entry
├── routes.py              # URL routes and view logic
├── templates/             # HTML templates
├── static/                # CSS, JS, D3.js
├── analyzer/              # Compiler modules
│   ├── lexer.py
│   ├── parser.py
│   ├── ast.py
│   ├── semantic.py
│   ├── ir_generator.py
│   ├── optimizer.py
│   └── codegen.py
├── tests/                 # Test cases
└── output/                # Generated results
```
