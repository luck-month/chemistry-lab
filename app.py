from flask import Flask

# 创建Flask应用实例
app = Flask(__name__)

# 定义路由和视图函数
@app.route('/')
def home():
    return '<h1>化学实验模拟平台</h1><p>正在建设中...</p>'

@app.route('/about')
def about():
    return '<h1>关于本平台</h1><p>这是一个为化学专业同学设计的实验辅助工具。</p>'

# 启动开发服务器
if __name__ == '__main__':
    app.run(debug=True)