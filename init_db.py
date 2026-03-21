import sqlite3

# 连接到数据库（如果不存在则会自动创建）
conn = sqlite3.connect('experiments.db')
cursor = conn.cursor()

# 创建 experiments 表
cursor.execute('''
    CREATE TABLE IF NOT EXISTS experiments (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        date TEXT NOT NULL,
        reagent TEXT,
        concentration REAL,
        volume REAL,
        temperature REAL,
        note TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
''')

conn.commit()
conn.close()

print("数据库初始化完成！")