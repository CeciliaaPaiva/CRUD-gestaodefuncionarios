from flask import Flask, render_template, request, jsonify
import sqlite3
import pandas as pd

app = Flask(__name__)

DATABASE = "database.db"


def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/funcionarios")
def funcionarios():

    conn = get_db()

    funcionarios = conn.execute(
        "SELECT * FROM funcionarios"
    ).fetchall()

    conn.close()

    return render_template("lista.html", funcionarios=funcionarios)


@app.route("/add", methods=["POST"])
def add():

    data = request.json

    conn = get_db()

    conn.execute(
        """
        INSERT INTO funcionarios
        (nome,cargo,departamento,salario,admissao)
        VALUES (?,?,?,?,?)
        """,
        (
            data["nome"],
            data["cargo"],
            data["departamento"],
            float(data["salario"]),
            data["admissao"]
        )
    )

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})


@app.route("/delete/<int:id>")
def delete(id):

    conn = get_db()

    conn.execute("DELETE FROM funcionarios WHERE id=?", (id,))

    conn.commit()
    conn.close()

    return jsonify({"status": "ok"})

@app.route("/editar/<int:id>", methods=["POST"])
def editar(id):

    data = request.json

    conn = get_db()

    conn.execute("""
    UPDATE funcionarios
    SET nome=?, cargo=?, departamento=?, salario=?, admissao=?
    WHERE id=?
    """,
    (
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


@app.route("/data")
def data():

    conn = get_db()

    df = pd.read_sql_query(
        "SELECT nome, salario, departamento, admissao FROM funcionarios",
        conn
    )

    conn.close()

    df["admissao"] = pd.to_datetime(df["admissao"])

    # filtro
    departamento = request.args.get("departamento")

    if departamento and departamento != "todos":
        df = df[df["departamento"] == departamento]

    # métricas
    total_funcionarios = len(df)
    media_salarial = round(df["salario"].mean(), 2) if len(df) > 0 else 0
    maior_salario = df["salario"].max() if len(df) > 0 else 0
    menor_salario = df["salario"].min() if len(df) > 0 else 0

    # departamentos
    departamentos = df["departamento"].value_counts()

    # ranking salários
    ranking = df.sort_values(by="salario", ascending=False).head(5)

    # admissões por mês
    admissoes_mes = df["admissao"].dt.month.value_counts().sort_index()

    return jsonify({

        "nomes": df["nome"].tolist(),
        "salarios": df["salario"].tolist(),

        "departamentos_labels": departamentos.index.tolist(),
        "departamentos_valores": departamentos.values.tolist(),

        "ranking_nomes": ranking["nome"].tolist(),
        "ranking_salarios": ranking["salario"].tolist(),

        "meses": admissoes_mes.index.tolist(),
        "admissoes": admissoes_mes.values.tolist(),

        "metricas": {
            "total": total_funcionarios,
            "media": media_salarial,
            "maior": maior_salario,
            "menor": menor_salario
        }

    })


if __name__ == "__main__":
    app.run(debug=True)