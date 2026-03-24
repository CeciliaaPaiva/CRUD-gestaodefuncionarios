from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import pandas as pd
import plotly.express as px
import plotly.utils
import json

app = Flask(__name__)

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS funcionarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            cargo TEXT NOT NULL,
            departamento TEXT NOT NULL,
            salario REAL NOT NULL,
            admissao TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/lista')
def lista():
    conn = get_db_connection()
    funcionarios = conn.execute('SELECT * FROM funcionarios').fetchall()
    conn.close()
    return render_template('lista.html', funcionarios=funcionarios)

@app.route('/add', methods=['POST'])
def add_funcionario():
    data = request.json
    try:
        # Forçamos a conversão para garantir que o gráfico funcione
        sal_float = float(str(data['salario']).replace(',', '.'))
        conn = get_db_connection()
        conn.execute('''INSERT INTO funcionarios (nome, cargo, departamento, salario, admissao) 
                     VALUES (?, ?, ?, ?, ?)''',
                     (data['nome'], data['cargo'], data['departamento'], sal_float, data['admissao']))
        conn.commit()
        conn.close()
        return jsonify({"status": "sucesso"})
    except Exception as e:
        print(f"Erro ao inserir: {e}")
        return jsonify({"status": "erro"}), 500

@app.route('/data')
def get_data():
    conn = sqlite3.connect('database.db')
    df = pd.read_sql_query("SELECT * FROM funcionarios", conn)
    conn.close()
    
    if df.empty:
        return jsonify({"barraJSON": None})
    
    # 1. Limpeza rigorosa: converte para numérico e remove o que não for número
    df['salario'] = pd.to_numeric(df['salario'], errors='coerce').fillna(0)

    # 2. Só gera o gráfico se houver salários maiores que zero
    max_salario = df['salario'].max()
    
    fig_barra = px.bar(
        df, 
        x='nome', 
        y='salario', 
        color='departamento',
        title="Salários por Colaborador",
        text_auto='.2s', # Mostra o valor em cima da barra
        labels={'salario': 'Salário (R$)', 'nome': 'Funcionário'}
    )

    # FORÇAR O EIXO Y: Isso garante que as colunas apareçam
    fig_barra.update_layout(
        yaxis=dict(range=[0, max_salario * 1.2], autorange=False),
        xaxis={'type': 'category'} # Garante que os nomes não virem números
    )

    fig_pizza = px.pie(
        df, 
        names='departamento', 
        values='salario', 
        title="Distribuição de Custos por Departamento"
    )
    
    return jsonify({
        "barraJSON": json.dumps(fig_barra, cls=plotly.utils.PlotlyJSONEncoder),
        "pizzaJSON": json.dumps(fig_pizza, cls=plotly.utils.PlotlyJSONEncoder)
    })

@app.route('/delete/<int:id>')
def delete(id):
    conn = get_db_connection()
    conn.execute('DELETE FROM funcionarios WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))

if __name__ == '__main__':
    init_db()
    app.run(debug=True)