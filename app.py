import sqlite3
import datetime
import random
from flask import Flask, render_template, request, redirect, url_for

app = Flask(__name__)

# ------------------- 数据库操作函数 -------------------
def get_db():
    """获取数据库连接，并设置 row_factory 以便像字典一样操作行"""
    conn = sqlite3.connect('experiments.db')
    conn.row_factory = sqlite3.Row
    return conn

# ------------------- 实验教学库数据（字典模拟） -------------------
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

# ------------------- 首页路由 -------------------
@app.route('/')
def home():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    site_name = "化学实验模拟平台"
    features = ["实验记录管理", "化学计算器", "滴定模拟器", "反应预测", "实验教学库", "报告生成"]
    # 随机推荐一个实验
    exp_list = list(experiments_library.items())
    random_exp = random.choice(exp_list) if exp_list else None
    return render_template('index.html',
                           current_time=current_time,
                           site_name=site_name,
                           features=features,
                           random_exp=random_exp)

# ------------------- 关于页面 -------------------
@app.route('/about')
def about():
    return render_template('about.html')

# ------------------- 实验教学库（基于字典） -------------------
@app.route('/experiments')
def experiments():
    """实验教学库列表页"""
    return render_template('experiments.html', experiments=experiments_library)

@app.route('/experiment/<int:exp_id>')
def experiment_detail(exp_id):
    """实验教学库详情页"""
    exp = experiments_library.get(exp_id)
    if exp:
        return render_template('experiment_detail.html', exp=exp, exp_id=exp_id)
    else:
        return f"实验ID {exp_id} 不存在", 404

# ------------------- 用户实验记录管理（基于SQLite） -------------------
@app.route('/add', methods=['GET', 'POST'])
def add_experiment():
    """添加实验记录"""
    if request.method == 'POST':
        # 获取表单数据
        name = request.form['name']
        date = request.form['date']
        reagent = request.form.get('reagent')
        concentration = request.form.get('concentration')
        volume = request.form.get('volume')
        temperature = request.form.get('temperature')
        note = request.form.get('note')

        # 插入数据库
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO experiments (name, date, reagent, concentration, volume, temperature, note)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (name, date, reagent, concentration, volume, temperature, note))
        conn.commit()
        conn.close()

        # 重定向到实验记录列表页
        return redirect(url_for('records'))

    # GET 请求显示表单
    return render_template('add_experiment.html')

@app.route('/records')
def records():
    """显示用户添加的实验记录列表"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('SELECT * FROM experiments ORDER BY created_at DESC')
    records = cursor.fetchall()
    conn.close()
    return render_template('records.html', records=records)

# ------------------- 编辑实验记录 -------------------
@app.route('/edit/<int:record_id>', methods=['GET', 'POST'])
def edit_record(record_id):
    conn = get_db()
    cursor = conn.cursor()

    if request.method == 'POST':
        # 获取表单数据
        name = request.form['name']
        date = request.form['date']
        reagent = request.form.get('reagent')
        concentration = request.form.get('concentration')
        volume = request.form.get('volume')
        temperature = request.form.get('temperature')
        note = request.form.get('note')

        # 更新数据库
        cursor.execute('''
            UPDATE experiments
            SET name = ?, date = ?, reagent = ?, concentration = ?, volume = ?, temperature = ?, note = ?
            WHERE id = ?
        ''', (name, date, reagent, concentration, volume, temperature, note, record_id))
        conn.commit()
        conn.close()
        return redirect(url_for('records'))

    # GET 请求：获取当前记录并显示编辑表单
    cursor.execute('SELECT * FROM experiments WHERE id = ?', (record_id,))
    record = cursor.fetchone()
    conn.close()
    if record:
        return render_template('edit_experiment.html', record=record)
    else:
        return "记录不存在", 404

# ------------------- 删除实验记录 -------------------
@app.route('/delete/<int:record_id>')
def delete_record(record_id):
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute('DELETE FROM experiments WHERE id = ?', (record_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('records'))

# ------------------- 启动应用 -------------------
if __name__ == '__main__':
    app.run(debug=True)