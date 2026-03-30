from flask import Blueprint, render_template, request, redirect, url_for, flash
import os
from .parser_core.analyzer import analyze_code

main = Blueprint('main', __name__)

@main.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        if 'file' not in request.files:
            flash('没有选择文件')
            return redirect(request.url)
        
        file = request.files['file']
        if file.filename == '':
            flash('没有选择文件')
            return redirect(request.url)
        
        if file and file.filename.endswith('.rs'):
            # 读取文件内容
            content = file.read().decode('utf-8')
            
            # 分析代码
            result = analyze_code(content)
            
            # 获取分析结果
            quadruples = result.get('quadruples', {})
            target_code = result.get('target_code', '')  # 新增
            error = result.get('error')
            codegen_error = result.get('codegen_error')  # 新增
            
            # 如果有代码生成错误，添加到错误信息中
            if codegen_error and not error:
                error = codegen_error
            
            # 渲染结果页面
            return render_template('result.html',
                                tokens=result['tokens'],
                                ast=result['ast'],
                                quadruples=quadruples,
                                target_code=target_code,  # 新增
                                error=error)
        else:
            flash('请上传.rs文件')
            return redirect(request.url)
    
    return render_template('index.html')