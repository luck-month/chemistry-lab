from flask import Flask, render_template
import datetime

app = Flask(__name__)

@app.route('/')
def home():
    # 创建一些示例变量
    current_time = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    site_name = "化学实验模拟平台"
    features = ["实验记录管理", "化学计算器", "滴定模拟器", "反应预测", "实验教学库", "报告生成"]
    return render_template('index.html',
                           current_time=current_time,
                           site_name=site_name,
                           features=features)

@app.route('/about')
def about():
    return render_template('about.html')

@app.route('/experiment/<int:exp_id>')
def experiment_detail(exp_id):
    # 模拟从数据库获取实验数据
    experiments = {
        1: {"name": "酸碱滴定", "date": "2026-03-20", "reagent": "HCI, NaOH"},
        2: {"name": "高锰酸钾标定", "date": "2026-03-21", "reagent": "KMnO4, Na2C2O4"},
        3: {"name": "重结晶", "date": "2026-03-22", "reagent": "乙酰苯胺, 水"},
        4: {"name": "离子交换树脂的测定", "date": "2026-03-23", "reagent": "732型H型阳离子交换树脂,HCI,NAOH,NA2SO4,酚酞,邻苯二甲酸氢钾基准物"}
    }
    exp = experiments.get(exp_id)
    if exp:
        return render_template('experiment_detail.html', exp=exp, exp_id=exp_id)
    else:
        return f"实验ID {exp_id} 不存在", 404

if __name__ == '__main__':
    app.run(debug=True)