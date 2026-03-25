from flask import Flask, render_template, request, jsonify, redirect, url_for
import sqlite3
import pandas as pd
import plotly.express as px
import plotly
import json

app = Flask(__name__)

def get_db():
    conn = sqlite3.connect("database.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute("""
    CREATE TABLE IF NOT EXISTS funcionarios(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT,
        cargo TEXT,
        departamento TEXT,
        salario REAL,
        admissao TEXT
    )
    """)
    conn.commit()
    conn.close()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/lista")
def lista():
    conn = get_db()
    funcionarios = conn.execute("SELECT * FROM funcionarios").fetchall()
    conn.close()
    return render_template("lista.html", funcionarios=funcionarios)

@app.route("/add", methods=["POST"])
def add():

    data = request.json

    conn = get_db()

    conn.execute("""
    INSERT INTO funcionarios(nome,cargo,departamento,salario,admissao)
    VALUES(?,?,?,?,?)
    """,(data["nome"],data["cargo"],data["departamento"],float(data["salario"]),data["admissao"]))

    conn.commit()
    conn.close()

    return jsonify({"status":"ok"})


@app.route("/data")
def data():

    conn = get_db()

    df = pd.read_sql_query("SELECT * FROM funcionarios", conn)

    conn.close()

    if df.empty:
        return jsonify({"status":"empty"})

    # métricas
    total_func = len(df)
    media_sal = df["salario"].mean()
    maior_sal = df["salario"].max()
    custo_total = df["salario"].sum()

    # gráfico barras

    
    
    
    fig_bar = px.scatter(
        df,
        x="nome",
        y="salario",
        color="departamento",
        size="salario",
        title="Distribuição de Salários dos Funcionários"
    )

    fig_bar.update_traces(
        text=df["salario"],
        textposition="top center"
    )

    # gráfico pizza
    fig_pizza = px.pie(
        df,
        names="departamento",
        values="salario",
        title="Custo por Departamento"
    )

    # gráfico funcionários por depto
    fig_depto = px.histogram(
        df,
        x="departamento",
        title="Funcionários por Departamento"
    )

    return jsonify({

        "total": total_func,
        "media": round(media_sal,2),
        "maior": maior_sal,
        "custo": custo_total,

        "barra": json.dumps(fig_bar, cls=plotly.utils.PlotlyJSONEncoder),
        "pizza": json.dumps(fig_pizza, cls=plotly.utils.PlotlyJSONEncoder),
        "depto": json.dumps(fig_depto, cls=plotly.utils.PlotlyJSONEncoder)

    })


@app.route("/delete/<int:id>")
def delete(id):

    conn = get_db()
    conn.execute("DELETE FROM funcionarios WHERE id=?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for("lista"))


@app.route("/edit/<int:id>", methods=["POST"])
def edit(id):

    data = request.json

    conn = get_db()

    conn.execute("""
    UPDATE funcionarios
    SET nome=?, cargo=?, departamento=?, salario=?, admissao=?
    WHERE id=?
    """,(
        data["nome"],
        data["cargo"],
        data["departamento"],
        float(data["salario"]),
        data["admissao"],
        id
    ))

    conn.commit()
    conn.close()

    return jsonify({"status":"ok"})

if __name__ == "__main__":
    init_db()
    app.run(debug=True)