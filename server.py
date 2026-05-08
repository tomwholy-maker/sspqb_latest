# -*- coding: utf-8 -*-
"""
固体物理题库后端服务
运行方式: python server.py
需要安装: pip install flask flask-cors openai python-dotenv
"""

import os
import base64
import re
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
from openai import OpenAI

# ========== 加载环境变量 ==========
try:
    from dotenv import load_dotenv
    load_dotenv()
    print("已加载.env配置文件")
except ImportError:
    print("未安装python-dotenv，将只使用系统环境变量")
except Exception as e:
    print(f"加载.env文件失败: {e}")

app = Flask(__name__)
CORS(app)

# ========== 获取API Key ==========
DEEPSEEK_API_KEY = os.environ.get('DEEPSEEK_API_KEY')

if not DEEPSEEK_API_KEY:
    print("\n" + "=" * 60)
    print("⚠️ 错误: 未找到 DEEPSEEK_API_KEY")
    print("=" * 60)
    print("\n请选择以下方式之一设置API Key：\n")
    print("方式1【推荐】: 创建 .env 文件")
    print(" 在server.py同目录下创建 .env 文件，内容为：")
    print(" DEEPSEEK_API_KEY=sk-你的真实key\n")
    print("方式2【临时】: 在终端设置环境变量")
    print(" Windows: set DEEPSEEK_API_KEY=sk-你的真实key")
    print(" Mac/Linux: export DEEPSEEK_API_KEY='sk-你的真实key'\n")
    print("=" * 60)
    
    user_input = input("\n是否手动输入API Key？(y/n): ")
    if user_input.lower() == 'y':
        DEEPSEEK_API_KEY = input("请输入你的DeepSeek API Key: ").strip()
        if not DEEPSEEK_API_KEY:
            print("错误: API Key不能为空")
            exit(1)
    else:
        exit(1)

# 初始化OpenAI客户端
client = OpenAI(
    api_key=DEEPSEEK_API_KEY,
    base_url="https://api.deepseek.com"
)

# 固体物理知识库的系统提示词
SYSTEM_PROMPT = """你是一位固体物理教学助手，基于黄昆《固体物理学》教材知识回答问题。
你的特点：
1. 回答要准确、专业，使用正确的物理术语
2. 对于公式推导，要给出清晰的步骤
3. 对于抽象概念，要结合物理图像解释
4. 回答要简洁明了，便于学生理解"""


@app.route('/api/chat', methods=['POST'])
def chat():
    """AI对话接口"""
    try:
        data = request.get_json()
        user_message = data.get('message', '')
        
        if not user_message:
            return jsonify({'success': False, 'error': '消息不能为空'})
        
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": user_message}
            ],
            temperature=0.7,
            max_tokens=2000,
            stream=False
        )
        
        reply = response.choices[0].message.content
        return jsonify({'success': True, 'reply': reply})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/generate-question', methods=['POST'])
def generate_question():
    """根据知识点智能生成题目"""
    try:
        data = request.get_json()
        knowledge = data.get('knowledge', '')
        question_type = data.get('type', '计算题')
        difficulty = data.get('difficulty', 'medium')
        
        difficulty_map = {'easy': '基础', 'medium': '中等', 'hard': '困难'}
        
        prompt = f"""请根据以下信息生成一道固体物理{question_type}：

知识点：{knowledge}
难度：{difficulty_map.get(difficulty, '中等')}

要求：
1. 题目要符合固体物理教学要求
2. 题目表述清晰、严谨
3. 最后附上参考答案和详细解析
4. 格式：【题目】xxx【答案】xxx【解析】xxx
5. 公式请使用LaTeX格式，如 \\(E = \\hbar\\omega\\)"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是固体物理出题专家，擅长出高质量的物理题目。公式请使用LaTeX格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.8,
            max_tokens=1500,
            stream=False
        )
        
        result = response.choices[0].message.content
        return jsonify({'success': True, 'question': result})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/explain-concept', methods=['POST'])
def explain_concept():
    """解释物理概念"""
    try:
        data = request.get_json()
        concept = data.get('concept', '')
        
        if not concept:
            return jsonify({'success': False, 'error': '概念不能为空'})
        
        prompt = f"""请解释固体物理概念：{concept}

要求：
1. 给出准确定义
2. 说明物理意义
3. 举例说明（如果适用）
4. 控制在300字以内
5. 公式请使用LaTeX格式"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是固体物理教学助手，擅长用通俗语言解释复杂概念。公式请使用LaTeX格式。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.5,
            max_tokens=800,
            stream=False
        )
        
        explanation = response.choices[0].message.content
        return jsonify({'success': True, 'explanation': explanation})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/analyze-mistake', methods=['POST'])
def analyze_mistake():
    """分析错题原因"""
    try:
        data = request.get_json()
        question = data.get('question', '')
        user_answer = data.get('user_answer', '')
        correct_answer = data.get('correct_answer', '')
        
        prompt = f"""请分析以下错题：

题目：{question}
学生答案：{user_answer}
正确答案：{correct_answer}

请分析：
1. 学生可能错在哪里
2. 涉及的知识点
3. 给出学习建议"""

        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": "你是固体物理辅导老师，擅长分析学生错误原因。"},
                {"role": "user", "content": prompt}
            ],
            temperature=0.6,
            max_tokens=500,
            stream=False
        )
        
        analysis = response.choices[0].message.content
        return jsonify({'success': True, 'analysis': analysis})
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/grade-image', methods=['POST'])
def grade_image():
    """判断图片答案是否正确（支持多模态视觉识别）"""
    try:
        # 获取表单数据
        question = request.form.get('question', '')
        correct_answer = request.form.get('correct_answer', '')
        user_text_answer = request.form.get('user_answer', '')
        
        # 获取上传的图片文件
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': '请上传图片'})
        
        image_file = request.files['image']
        if image_file.filename == '':
            return jsonify({'success': False, 'error': '请选择图片'})
        
        # 读取图片为base64
        image_bytes = image_file.read()
        image_base64 = base64.b64encode(image_bytes).decode('utf-8')
        
        # 图片格式（固定为png，兼容Python 3.13）
        img_type = 'png'
        
        # 调用多模态API
        response = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": """你是一位固体物理老师，负责批改学生作业。
请根据题目和参考答案，判断学生上传的答案图片是否正确。

评分标准：
- 完全正确：9-10分
- 基本正确但有小错误：7-8分
- 部分正确：5-6分
- 错误较多：3-4分
- 完全错误：0-2分

请用以下JSON格式回复（不要有其他文字）：
{
    "correct": true/false,
    "score": 数字,
    "analysis": "详细分析学生答案的对错",
    "suggestion": "改进建议"
}"""},
                {"role": "user", "content": [
                    {"type": "text", "text": f"""请判断以下学生答案是否正确。

【题目】
{question}

【参考答案】
{correct_answer}

【学生文字答案】（如果有）
{user_text_answer if user_text_answer else '未提供'}

【学生图片答案】
请仔细查看上传的图片中的解题过程，判断是否正确。"""},
                    {"type": "image_url", "image_url": {"url": f"data:image/{img_type};base64,{image_base64}"}}
                ]}
            ],
            temperature=0.3,
            max_tokens=1000
        )
        
        result = response.choices[0].message.content
        print(f"AI返回结果: {result}")
        
        # 解析JSON结果
        json_match = re.search(r'\{[^{}]*"correct"[^{}]*\}', result, re.DOTALL)
        if json_match:
            try:
                parsed = json.loads(json_match.group())
                return jsonify({
                    'success': True, 
                    'correct': parsed.get('correct', False),
                    'score': parsed.get('score', 0),
                    'analysis': parsed.get('analysis', ''),
                    'suggestion': parsed.get('suggestion', '')
                })
            except:
                pass
        
        # 如果JSON解析失败，返回原始结果
        return jsonify({
            'success': True, 
            'correct': '正确' in result or '✓' in result,
            'score': 8 if '正确' in result else 5,
            'analysis': result,
            'suggestion': '请参考参考答案'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/health', methods=['GET'])
def health():
    """健康检查"""
    return jsonify({'status': 'ok', 'message': '固体物理题库后端服务运行正常'})


if __name__ == '__main__':
    print("\n" + "=" * 50)
    print("🔬 固体物理题库后端服务")
    print("=" * 50)
    print(f"服务地址: http://localhost:5000")
    print("可用接口:")
    print("  POST /api/chat            - AI对话")
    print("  POST /api/generate-question - 生成题目")
    print("  POST /api/explain-concept  - 解释概念")
    print("  POST /api/analyze-mistake  - 错题分析")
    print("  POST /api/grade-image      - 图片判题")
    print("  GET  /api/health          - 健康检查")
    print("=" * 50 + "\n")
    app.run(host='0.0.0.0', port=5000, debug=True)
# 在 server.py 末尾添加（需要安装 matplotlib, numpy）

import matplotlib
matplotlib.use('Agg')  # 使用非交互式后端
import matplotlib.pyplot as plt
import numpy as np
import io
import base64

@app.route('/api/generate-graph', methods=['POST'])
def generate_graph():
    """生成物理图形（布里渊区、能带等）"""
    try:
        data = request.get_json()
        graph_type = data.get('type', 'brillouin')
        params = data.get('params', {'a': 1, 'n': 3})
        
        a = params.get('a', 1)
        n = params.get('n', 3)
        
        fig, ax = plt.subplots(figsize=(8, 8))
        
        if graph_type == 'brillouin':
            # 绘制二维正方晶格布里渊区
            ax.set_title('第一布里渊区 (二维正方晶格)', fontsize=14)
            ax.set_xlabel('$k_x$', fontsize=12)
            ax.set_ylabel('$k_y$', fontsize=12)
            
            # 倒格点
            G = 2 * np.pi / a
            for i in range(-n, n+1):
                for j in range(-n, n+1):
                    ax.plot(i*G, j*G, 'o', color='orange', markersize=4)
                    if abs(i) + abs(j) <= 2:
                        ax.annotate(f'({i},{j})', (i*G+0.1, j*G+0.1), fontsize=8)
            
            # 布里渊区边界（正方形）
            boundary = G / 2
            square = plt.Rectangle((-boundary, -boundary), 2*boundary, 2*boundary, 
                                   fill=True, alpha=0.1, color='blue', edgecolor='red', linewidth=2)
            ax.add_patch(square)
            
            # 高对称点
            ax.plot(0, 0, 'o', color='blue', markersize=8)
            ax.annotate('Γ', (0, 0), fontsize=14, ha='right')
            ax.plot(boundary, 0, 'o', color='blue', markersize=6)
            ax.annotate('X', (boundary, 0), fontsize=12)
            ax.plot(boundary, boundary, 'o', color='blue', markersize=6)
            ax.annotate('M', (boundary, boundary), fontsize=12)
            
            ax.axhline(y=0, color='gray', linestyle='-', linewidth=0.5)
            ax.axvline(x=0, color='gray', linestyle='-', linewidth=0.5)
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            
        elif graph_type == 'band_structure':
            ax.set_title('能带结构示意图', fontsize=14)
            ax.set_xlabel('波矢 k', fontsize=12)
            ax.set_ylabel('能量 E', fontsize=12)
            
            # 绘制能带
            k = np.linspace(0, np.pi, 100)
            valence = -np.cos(k) * 0.5
            conduction = 1 + np.cos(k) * 0.5
            
            ax.plot(k, valence, 'b-', linewidth=2.5, label='价带')
            ax.plot(k, conduction, 'r-', linewidth=2.5, label='导带')
            ax.fill_between(k, valence, conduction, alpha=0.1, color='gray')
            
            # 标注带隙
            ax.annotate('带隙 $E_g$', xy=(np.pi/2, 0.5), xytext=(np.pi/2+0.5, 0.8),
                       arrowprops=dict(arrowstyle='->'), fontsize=11)
            
            ax.axhline(y=0, color='gray', linestyle='--', linewidth=0.8)
            ax.legend()
            ax.set_xticks([0, np.pi/2, np.pi])
            ax.set_xticklabels(['Γ', 'X', 'M'])
            ax.grid(True, alpha=0.3)
            
        elif graph_type == 'dispersion':
            ax.set_title('声子色散关系 (一维双原子链)', fontsize=14)
            ax.set_xlabel('波矢 q', fontsize=12)
            ax.set_ylabel('频率 ω', fontsize=12)
            
            q = np.linspace(0, np.pi, 200)
            # 简化的色散关系
            acoustic = np.sin(q/2)
            optical = 0.8 + 0.2 * np.sin(q)
            
            ax.plot(q, acoustic, 'b-', linewidth=2.5, label='声学支')
            ax.plot(q, optical, 'r-', linewidth=2.5, label='光学支')
            
            ax.axvline(x=np.pi/2, color='gray', linestyle='--', alpha=0.5)
            ax.annotate('带隙', xy=(np.pi/2, 0.5), xytext=(np.pi/2+0.3, 0.6), fontsize=10)
            
            ax.legend()
            ax.set_xticks([0, np.pi/2, np.pi])
            ax.set_xticklabels(['0', 'π/(2a)', 'π/a'])
            ax.grid(True, alpha=0.3)
            
        elif graph_type == 'dos':
            ax.set_title('态密度 (自由电子气)', fontsize=14)
            ax.set_xlabel('能量 E', fontsize=12)
            ax.set_ylabel('态密度 g(E)', fontsize=12)
            
            E = np.linspace(0, 1, 100)
            g = np.sqrt(E)
            
            ax.plot(E, g, 'b-', linewidth=2.5)
            ax.fill_between(E, 0, g, alpha=0.3, color='blue')
            ax.axvline(x=0.5, color='red', linestyle='--', alpha=0.7)
            ax.annotate('费米能级', xy=(0.5, 0.5), xytext=(0.55, 0.6), fontsize=10)
            ax.grid(True, alpha=0.3)
            
        elif graph_type == 'fermi_surface_2d':
            ax.set_title('二维自由电子费米面', fontsize=14)
            ax.set_xlabel('$k_x$', fontsize=12)
            ax.set_ylabel('$k_y$', fontsize=12)
            
            theta = np.linspace(0, 2*np.pi, 100)
            k_F = 1
            x = k_F * np.cos(theta)
            y = k_F * np.sin(theta)
            
            ax.plot(x, y, 'b-', linewidth=2.5)
            ax.fill(x, y, alpha=0.2, color='blue')
            ax.set_aspect('equal')
            ax.grid(True, alpha=0.3)
            ax.annotate('费米面', xy=(0.7, 0.7), fontsize=12)
            
        # 保存为base64
        buf = io.BytesIO()
        plt.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        img_base64 = base64.b64encode(buf.getvalue()).decode('utf-8')
        plt.close(fig)
        
        return jsonify({
            'success': True,
            'image': f'data:image/png;base64,{img_base64}'
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'success': False, 'error': str(e)})