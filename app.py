import sqlite3
import datetime
import random
import re
import math
from flask import Flask, render_template, request, redirect, url_for, jsonify, make_response
from jinja2 import Template
from weasyprint import HTML

app = Flask(__name__)

# ------------------- 数据库操作 -------------------
def get_db():
    """获取数据库连接，返回 sqlite3.Row 类型的结果"""
    conn = sqlite3.connect('experiments.db')
    conn.row_factory = sqlite3.Row
    return conn

# ------------------- 元素原子量字典 -------------------
ATOMIC_MASSES = {
    'H': 1.008, 'He': 4.0026, 'Li': 6.94, 'Be': 9.0122, 'B': 10.81,
    'C': 12.011, 'N': 14.007, 'O': 15.999, 'F': 18.998, 'Ne': 20.18,
    'Na': 22.99, 'Mg': 24.305, 'Al': 26.982, 'Si': 28.086, 'P': 30.974,
    'S': 32.06, 'Cl': 35.45, 'Ar': 39.95, 'K': 39.098, 'Ca': 40.078,
    'Sc': 44.956, 'Ti': 47.867, 'V': 50.942, 'Cr': 51.996, 'Mn': 54.938,
    'Fe': 55.845, 'Co': 58.933, 'Ni': 58.693, 'Cu': 63.546, 'Zn': 65.38,
    'Ga': 69.723, 'Ge': 72.63, 'As': 74.922, 'Se': 78.96, 'Br': 79.904,
    'Kr': 83.798, 'Rb': 85.468, 'Sr': 87.62, 'Y': 88.906, 'Zr': 91.224,
    'Nb': 92.906, 'Mo': 95.95, 'Tc': 98, 'Ru': 101.07, 'Rh': 102.91,
    'Pd': 106.42, 'Ag': 107.87, 'Cd': 112.41, 'In': 114.82, 'Sn': 118.71,
    'Sb': 121.76, 'Te': 127.6, 'I': 126.90, 'Xe': 131.29, 'Cs': 132.91,
    'Ba': 137.33, 'La': 138.91, 'Ce': 140.12, 'Pr': 140.91, 'Nd': 144.24,
    'Pm': 145, 'Sm': 150.36, 'Eu': 151.96, 'Gd': 157.25, 'Tb': 158.93,
    'Dy': 162.5, 'Ho': 164.93, 'Er': 167.26, 'Tm': 168.93, 'Yb': 173.05,
    'Lu': 174.97, 'Hf': 178.49, 'Ta': 180.95, 'W': 183.84, 'Re': 186.21,
    'Os': 190.23, 'Ir': 192.22, 'Pt': 195.08, 'Au': 196.97, 'Hg': 200.59,
    'Tl': 204.38, 'Pb': 207.2, 'Bi': 208.98, 'Th': 232.04, 'U': 238.03,
}

# ------------------- 化学式解析 -------------------
def parse_formula(formula):
    """解析化学式，返回元素及个数字典"""
    pattern = r'([A-Z][a-z]?)(\d*)|\(([A-Za-z0-9]+)\)(\d*)'
    result = {}
    for match in re.finditer(pattern, formula):
        if match.group(1):   # 普通元素
            elem = match.group(1)
            count = int(match.group(2)) if match.group(2) else 1
            result[elem] = result.get(elem, 0) + count
        elif match.group(3): # 括号内
            inside = match.group(3)
            multiplier = int(match.group(4)) if match.group(4) else 1
            sub = parse_formula(inside)
            for elem, cnt in sub.items():
                result[elem] = result.get(elem, 0) + cnt * multiplier
    return result

def calculate_molar_mass(formula):
    """计算摩尔质量，返回浮点数或 None（解析失败）"""
    elements = parse_formula(formula)
    mass = 0.0
    for elem, count in elements.items():
        if elem in ATOMIC_MASSES:
            mass += ATOMIC_MASSES[elem] * count
        else:
            return None
    return round(mass, 4)

# ------------------- 滴定模拟器 -------------------
def simulate_titration(acid_conc, acid_vol, base_conc):
    """
    强酸强碱滴定模拟
    参数：
        acid_conc: 酸浓度 (mol/L)
        acid_vol:  酸体积 (mL)
        base_conc: 碱浓度 (mol/L)
    返回：
        volumes: 滴定剂体积数组 (mL)
        pH_values: 对应的 pH 数组
    """
    max_vol = acid_vol * 2
    volumes = [max_vol * i / 99 for i in range(100)]  # 0 到 max_vol
    pH_values = []

    for v in volumes:
        if v < acid_vol:
            # 计量点前：剩余酸浓度
            remaining_acid = acid_conc * acid_vol - base_conc * v
            total_vol = acid_vol + v
            H_conc = remaining_acid / total_vol
            pH = -math.log10(H_conc) if H_conc > 0 else 7
        else:
            # 计量点后：过量碱浓度
            excess_base = base_conc * (v - acid_vol)
            total_vol = acid_vol + v
            OH_conc = excess_base / total_vol
            pH = 14 - (-math.log10(OH_conc)) if OH_conc > 0 else 7
        pH_values.append(round(pH, 2))

    return volumes, pH_values

# ------------------- 反应规则库 -------------------
REACTION_RULES = [
    {
        "name": "酯化",
        "reactants": ["羧酸", "醇"],
        "product_smiles": "C(=O)OC",
        "condition": "含羧基(-COOH)和羟基(-OH)的反应物",
        "detect": {
            "羧酸": lambda s: "C(=O)O" in s,
            "醇": lambda s: "O" in s and not "C(=O)O" in s
        }
    },
    {
        "name": "加成（烯烃+卤素）",
        "reactants": ["烯烃", "卤素"],
        "product_smiles": "C(Br)CBr",
        "condition": "含碳碳双键(C=C)和卤素(Br2/Cl2)",
        "detect": {
            "烯烃": lambda s: "C=C" in s,
            "卤素": lambda s: "Br" in s or "Cl" in s
        }
    }
]

def predict_reaction(reactant1, reactant2):
    """根据规则库预测反应"""
    for rule in REACTION_RULES:
        conditions = list(rule["detect"].values())
        if conditions[0](reactant1) and conditions[1](reactant2):
            return rule["name"], rule["product_smiles"]
        if conditions[0](reactant2) and conditions[1](reactant1):
            return rule["name"], rule["product_smiles"]
    return None, None

# ------------------- 报告模板库 -------------------
REPORT_TEMPLATES = {
    "default": {
        "name": "标准实验报告模板",
        "content": """
# {{ experiment.name }} 实验报告

**姓名**：{{ user_name }}  
**日期**：{{ experiment.date }}  

## 实验目的
{{ experiment.purpose if experiment.purpose else "（请填写实验目的）" }}

## 实验原理
{{ experiment.principle if experiment.principle else "（请填写实验原理）" }}

## 仪器与试剂
- 试剂：{{ experiment.reagent }}
- 浓度：{{ experiment.concentration }} mol/L
- 体积：{{ experiment.volume }} mL
- 温度：{{ experiment.temperature }} ℃

## 实验步骤
{{ experiment.steps if experiment.steps else "（请填写实验步骤）" }}

## 数据记录与处理
（请在此处添加数据记录表格和计算结果）

## 结果与讨论
（请填写结果分析和讨论）

## 结论
（请填写实验结论）
        """
    },
    "short": {
        "name": "简洁报告模板",
        "content": """
# {{ experiment.name }} 实验报告
**日期**：{{ experiment.date }}  
**试剂**：{{ experiment.reagent }}  

**实验内容**：  
{{ experiment.note if experiment.note else "无" }}

**结论**：  
（请填写结论）
        """
    }
}

# ------------------- 实验教学库数据 -------------------
experiments_library = {
    1: {
        "name": "酸碱滴定",
        "date": "2026-03-20",
        "reagent": "HCl, NaOH",
        "description": "强酸强碱滴定，学习滴定操作。",
        "purpose": "掌握酸碱滴定原理和操作，学会使用甲基橙指示剂判断终点。",
        "principle": "HCl + NaOH → NaCl + H₂O，强酸强碱滴定，计量点 pH=7。",
        "steps": """1. 用移液管准确量取 25.00 mL HCl 溶液于锥形瓶中。\n2. 加入 2 滴甲基橙指示剂，溶液呈红色。\n3. 用 NaOH 溶液滴定至溶液由红色变为橙色，记录消耗体积。\n4. 重复滴定 3 次，计算平均值。""",
        "precautions": "滴定速度不宜过快，接近终点时要半滴操作。",
        "reagents": "HCl 溶液（约 0.1 mol/L）、NaOH 溶液（约 0.1 mol/L）、甲基橙指示剂"
    },
    2: {
        "name": "高锰酸钾标定",
        "date": "2026-03-21",
        "reagent": "KMnO4, Na2C2O4",
        "description": "氧化还原滴定，标定高锰酸钾浓度。",
        "purpose": "学习氧化还原滴定法，掌握高锰酸钾溶液的标定方法。",
        "principle": "2MnO₄⁻ + 5C₂O₄²⁻ + 16H⁺ → 2Mn²⁺ + 10CO₂ + 8H₂O",
        "steps": """1. 准确称取 0.15-0.20 g Na₂C₂O₄ 基准物于锥形瓶中。\n2. 加入 50 mL 蒸馏水和 10 mL 3 mol/L H₂SO₄，加热至 75-85℃。\n3. 用 KMnO₄ 溶液滴定至溶液呈微红色并保持 30 秒不褪色。\n4. 记录消耗体积，计算 KMnO₄ 浓度。""",
        "precautions": "滴定温度控制在 75-85℃，过高会导致草酸分解。",
        "reagents": "KMnO₄ 溶液（约 0.02 mol/L）、Na₂C₂O₄ 基准物、3 mol/L H₂SO₄"
    },
    3: {
        "name": "重结晶",
        "date": "2026-03-22",
        "reagent": "乙酰苯胺, 水",
        "description": "利用溶解度差异提纯固体。",
        "purpose": "学习重结晶法提纯固体有机化合物的原理和操作。",
        "principle": "利用不同温度下溶解度差异，使杂质留在母液中。",
        "steps": """1. 将粗乙酰苯胺溶于适量热水中（近沸），制成饱和溶液。\n2. 加入少量活性炭脱色，趁热过滤除去不溶物。\n3. 滤液自然冷却结晶，抽滤，干燥。""",
        "precautions": "热过滤时要预热漏斗，防止结晶堵塞。",
        "reagents": "粗乙酰苯胺、蒸馏水、活性炭"
    },
    4: {
        "name": "离子交换树脂的测定",
        "date": "2026-03-23",
        "reagent": "732型H型阳离子交换树脂, HCl, NaOH, Na2SO4, 酚酞, 邻苯二甲酸氢钾基准物",
        "description": "测定离子交换树脂的交换容量。",
        "purpose": "学习离子交换树脂的预处理和交换容量的测定方法。",
        "principle": "阳离子交换树脂中的 H⁺ 与溶液中的阳离子发生交换，通过滴定流出液的酸度计算交换容量。",
        "steps": """1. 树脂预处理：用 1 mol/L HCl 浸泡 24 小时，然后用去离子水洗至中性。\n2. 装柱，用 1 mol/L HCl 转型，再用去离子水洗至中性。\n3. 将待测溶液通过交换柱，收集流出液。\n4. 用 NaOH 标准溶液滴定流出液，计算交换容量。""",
        "precautions": "树脂装柱时避免气泡；滴定终点要准确判断。",
        "reagents": "732型H型阳离子交换树脂、1 mol/L HCl、0.1 mol/L NaOH、酚酞指示剂、邻苯二甲酸氢钾基准物"
    }
}

# ------------------- 首页 -------------------
@app.route('/')
def home():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    site_name = "化学实验模拟平台"
    features = ["实验记录管理", "化学计算器", "滴定模拟器", "反应预测", "实验教学库", "报告生成"]
    exp_list = list(experiments_library.items())
    random_exp = random.choice(exp_list) if exp_list else None
    return render_template('index.html',
                           current_time=current_time,
                           site_name=site_name,
                           features=features,
                           random_exp=random_exp)

# ------------------- 关于 -------------------
@app.route('/about')
def about():
    return render_template('about.html')

# ------------------- 实验教学库 -------------------
@app.route('/experiments')
def experiments():
    return render_template('experiments.html', experiments=experiments_library)

@app.route('/experiment/<int:exp_id>')
def experiment_detail(exp_id):
    exp = experiments_library.get(exp_id)
    if exp:
        return render_template('experiment_detail.html', exp=exp, exp_id=exp_id)
    else:
        return f"实验ID {exp_id} 不存在", 404

# ------------------- 用户实验记录管理 -------------------
@app.route('/add', methods=['GET', 'POST'])
def add_experiment():
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        reagent = request.form.get('reagent')
        concentration = request.form.get('concentration')
        volume = request.form.get('volume')
        temperature = request.form.get('temperature')
        note = request.form.get('note')

        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO experiments (name, date, reagent, concentration, volume, temperature, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, date, reagent, concentration, volume, temperature, note))
        conn.commit()
        conn.close()
        return redirect(url_for('records'))
    return render_template('add_experiment.html')

@app.route('/records')
def records():
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM experiments ORDER BY created_at DESC')
    records = cursor.fetchall()
    conn.close()
    return render_template('records.html', records=records)

@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    conn = get_db()
    cursor = conn.cursor()
    if request.method == 'POST':
        name = request.form['name']
        date = request.form['date']
        reagent = request.form.get('reagent')
        concentration = request.form.get('concentration')
        volume = request.form.get('volume')
        temperature = request.form.get('temperature')
        note = request.form.get('note')
        cursor.execute('''
            UPDATE experiments
            SET name=?, date=?, reagent=?, concentration=?, volume=?, temperature=?, note=?
            WHERE id=?
        ''', (name, date, reagent, concentration, volume, temperature, note, record_id))
        conn.commit()
        conn.close()
        return redirect(url_for('records'))
    cursor.execute('SELECT * FROM experiments WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    conn.close()
    if record:
        return render_template('edit_experiment.html', record=record)
    else:
        return "记录不存在", 404

@app.route('/delete/<int:record_id>')
def delete_record(record_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM experiments WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('records'))

# ------------------- 化学计算器 -------------------
@app.route('/calculator/molar_mass', methods=['GET', 'POST'])
def molar_mass_calculator():
    result = None
    error = None
    if request.method == 'POST':
        formula = request.form.get('formula', '').strip()
        if formula:
            molar_mass = calculate_molar_mass(formula)
            if molar_mass is not None:
                result = f"{formula} 的摩尔质量为 {molar_mass} g/mol"
            else:
                error = f"无法解析化学式：{formula}，请检查元素符号是否正确。"
        else:
            error = "请输入化学式。"
    return render_template('molar_mass.html', result=result, error=error)

@app.route('/calculator/solution', methods=['GET', 'POST'])
def solution_calculator():
    result = None
    error = None
    if request.method == 'POST':
        try:
            concentration = float(request.form.get('concentration', 0))
            volume = float(request.form.get('volume', 0))
            molar_mass = float(request.form.get('molar_mass', 0))
            if concentration <= 0 or volume <= 0 or molar_mass <= 0:
                error = "所有值必须为正数。"
            else:
                volume_l = volume / 1000  # mL -> L
                mass = concentration * volume_l * molar_mass
                result = f"所需溶质质量：{mass:.4f} g"
        except ValueError:
            error = "请输入有效的数字。"
    return render_template('solution.html', result=result, error=error)

@app.route('/calculator/unit_converter', methods=['GET', 'POST'])
def unit_converter():
    result = None
    error = None
    if request.method == 'POST':
        conv_type = request.form.get('conv_type')
        value = request.form.get('value')
        try:
            value = float(value)
            if conv_type == 'concentration':
                molar_mass = request.form.get('molar_mass')
                if not molar_mass:
                    error = "请输入摩尔质量。"
                else:
                    molar_mass = float(molar_mass)
                    result = f"{value} mol/L = {value * molar_mass} g/L"
            elif conv_type == 'volume':
                unit_from = request.form.get('unit_from')
                unit_to = request.form.get('unit_to')
                if unit_from == 'mL' and unit_to == 'L':
                    result = f"{value} mL = {value / 1000} L"
                elif unit_from == 'L' and unit_to == 'mL':
                    result = f"{value} L = {value * 1000} mL"
                else:
                    error = "请选择有效的单位对。"
            elif conv_type == 'temperature':
                unit_from = request.form.get('unit_from')
                unit_to = request.form.get('unit_to')
                if unit_from == '℃' and unit_to == '℉':
                    result = f"{value} ℃ = {value * 9/5 + 32} ℉"
                elif unit_from == '℉' and unit_to == '℃':
                    result = f"{value} ℉ = {(value - 32) * 5/9} ℃"
                else:
                    error = "请选择有效的温度单位。"
            else:
                error = "未知的换算类型。"
        except ValueError:
            error = "请输入有效的数字。"
    return render_template('unit_converter.html', result=result, error=error)

# ------------------- 滴定模拟器 -------------------
@app.route('/titration')
def titration():
    return render_template('titration.html')

@app.route('/api/titration', methods=['POST'])
def titration_api():
    data = request.get_json()
    try:
        acid_conc = float(data.get('acid_conc', 0.1))
        acid_vol = float(data.get('acid_vol', 20))
        base_conc = float(data.get('base_conc', 0.1))
        if acid_conc <= 0 or acid_vol <= 0 or base_conc <= 0:
            return jsonify({'error': '所有参数必须为正数'}), 400
        volumes, pH_values = simulate_titration(acid_conc, acid_vol, base_conc)
        return jsonify({'volumes': volumes, 'pH': pH_values})
    except Exception as e:
        return jsonify({'error': str(e)}), 400

# ------------------- 反应预测 -------------------
@app.route('/reaction', methods=['GET', 'POST'])
def reaction():
    result = None
    product = None
    error = None
    if request.method == 'POST':
        reactant1 = request.form.get('reactant1', '').strip()
        reactant2 = request.form.get('reactant2', '').strip()
        if reactant1 and reactant2:
            rule_name, product_smiles = predict_reaction(reactant1, reactant2)
            if rule_name:
                result = f"匹配规则：{rule_name}"
                product = f"可能产物 SMILES：{product_smiles}"
            else:
                error = "未匹配到已知反应规则，请尝试其他反应物或检查 SMILES 格式。"
        else:
            error = "请输入两个反应物的 SMILES。"
    return render_template('reaction.html', result=result, product=product, error=error)

# ------------------- 报告生成 -------------------
@app.route('/generate_report/<int:record_id>')
def select_template(record_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM experiments WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    conn.close()
    if not record:
        return "记录不存在", 404
    templates = REPORT_TEMPLATES
    return render_template('select_template.html', templates=templates, record=record)

@app.route('/preview_report', methods=['POST'])
def preview_report():
    template_key = request.form.get('template_key')
    record_id = request.form.get('record_id')
    if not template_key or not record_id:
        return "参数错误", 400
    template = REPORT_TEMPLATES.get(template_key)
    if not template:
        return "模板不存在", 404
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM experiments WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    conn.close()
    if not record:
        return "记录不存在", 404
    context = {
        'experiment': dict(record),
        'user_name': "张三",  # 后续可改为登录用户
    }
    jinja_template = Template(template['content'])
    rendered_html = jinja_template.render(**context)
    return render_template('edit_report.html',
                           content=rendered_html,
                           record_id=record_id,
                           template_key=template_key)

@app.route('/export_pdf', methods=['POST'])
def export_pdf():
    data = request.get_json()
    html_content = data.get('html', '')
    if not html_content:
        return "内容为空", 400
    try:
        pdf = HTML(string=html_content).write_pdf()
        response = make_response(pdf)
        response.headers['Content-Type'] = 'application/pdf'
        response.headers['Content-Disposition'] = 'attachment; filename=report.pdf'
        return response
    except Exception as e:
        return str(e), 500

# ------------------- 启动应用 -------------------
if __name__ == '__main__':
    app.run(debug=True)