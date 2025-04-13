from flask import Flask, render_template, request, redirect, session, url_for
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta'

@app.route('/')
def index():
    return redirect('/login')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()
        cursor.execute("SELECT matricula, senha FROM usuarios WHERE usuario=?", (usuario,))
        dados = cursor.fetchone()
        conn.close()

        if dados and check_password_hash(dados[1], senha):
            session['matricula'] = dados[0]
            return redirect('/dashboard')
        else:
            return "Usuário ou senha inválidos"
    return render_template('login.html')

@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = generate_password_hash(request.form['senha'])
        email = request.form['email']
        conn = sqlite3.connect('banco.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO usuarios (usuario, senha, email) VALUES (?, ?, ?)", (usuario, senha, email))
        conn.commit()
        conn.close()
        return redirect('/login')
    return render_template('cadastro.html')

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'matricula' not in session:
        return redirect('/login')

    matricula = session['matricula']
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, nome_treino, concluido FROM treinos WHERE matricula=?", (matricula,))
    treinos = cursor.fetchall()

    dados = []
    for treino in treinos:
        cursor.execute("SELECT id, nome_exercicio, repeticoes, peso FROM exercicios WHERE treino_id=?", (treino[0],))
        exercicios = cursor.fetchall()
        dados.append({
            'id': treino[0],
            'nome_treino': treino[1],
            'concluido': treino[2],
            'exercicios': exercicios
        })

    conn.close()
    return render_template('dashboard.html', treinos=dados)

@app.route('/novo_treino', methods=['GET'])
def novo_treino():
    if 'matricula' not in session:
        return redirect('/dashboard')
    return render_template('novo_treino.html')

@app.route('/adicionar_treino', methods=['POST'])
def adicionar_treino():
    if 'matricula' not in session:
        return redirect('/login')

    matricula = session['matricula']
    nome_treino = request.form['nome_treino']

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO treinos (matricula, nome_treino) VALUES (?, ?)", (matricula, nome_treino))
    treino_id = cursor.lastrowid

    # Obtemos as listas de exercícios, repetições e pesos
    nomes = request.form.getlist('nome_exercicio')
    reps = request.form.getlist('repeticoes')
    pesos = request.form.getlist('peso')

    # Inserção de múltiplos exercícios de uma vez
    for n, r, p in zip(nomes, reps, pesos):
        if n.strip() and r.strip() and p.strip():  # Verificação para evitar valores vazios
            cursor.execute("INSERT INTO exercicios (treino_id, nome_exercicio, repeticoes, peso) VALUES (?, ?, ?, ?)",
                           (treino_id, n, r, p))

    conn.commit()
    conn.close()
    return redirect('/dashboard')


@app.route('/excluir_treino/<int:treino_id>', methods=['POST'])
def excluir_treino(treino_id):
    if 'matricula' not in session:
        return redirect('/login')

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute("DELETE FROM exercicios WHERE treino_id=?", (treino_id,))
    cursor.execute("DELETE FROM treinos WHERE id=?", (treino_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

# Parte do backend onde os novos exercícios são adicionados ao editar treino











@app.route('/editar_treino/<int:treino_id>', methods=['GET', 'POST'])
def editar_treino(treino_id):
    if 'matricula' not in session:
        return redirect('/login')

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        nome_treino = request.form['nome_treino']
        cursor.execute("UPDATE treinos SET nome_treino=? WHERE id=?", (nome_treino, treino_id))

        # Atualizar exercícios existentes
        exercicio_ids = request.form.getlist('exercicio_id')
        nomes_exist = request.form.getlist('nome_exercicio_existente')
        reps_exist = request.form.getlist('repeticoes_existente')
        pesos_exist = request.form.getlist('peso_existente')

        for ex_id, nome, rep, peso in zip(exercicio_ids, nomes_exist, reps_exist, pesos_exist):
            if nome.strip() and rep.strip() and peso.strip():
                cursor.execute("""
                    UPDATE exercicios
                    SET nome_exercicio=?, repeticoes=?, peso=?
                    WHERE id=? AND treino_id=?
                """, (nome, rep, peso, ex_id, treino_id))

        # Remover exercícios marcados para exclusão
        excluir_ids = request.form.getlist('excluir_exercicio_id')
        for ex_id in excluir_ids:
            cursor.execute("DELETE FROM exercicios WHERE id=? AND treino_id=?", (ex_id, treino_id))

        # Adicionar novos exercícios
        nomes_novos = request.form.getlist('nome_exercicio')
        reps_novos = request.form.getlist('repeticoes')
        pesos_novos = request.form.getlist('peso')

        for n, r, p in zip(nomes_novos, reps_novos, pesos_novos):
            if n.strip() and r.strip() and p.strip():
                cursor.execute("INSERT INTO exercicios (treino_id, nome_exercicio, repeticoes, peso) VALUES (?, ?, ?, ?)",
                            (treino_id, n, r, p))

        conn.commit()
        conn.close()
        return redirect('/dashboard')

    # GET - carrega os dados para edição
    cursor.execute("SELECT nome_treino FROM treinos WHERE id=?", (treino_id,))
    nome_treino = cursor.fetchone()[0]

    cursor.execute("SELECT id, nome_exercicio, repeticoes, peso FROM exercicios WHERE treino_id=?", (treino_id,))
    exercicios = cursor.fetchall()

    conn.close()
    return render_template('editar_treino.html', treino_id=treino_id, nome_treino=nome_treino, exercicios=exercicios)

@app.route('/sobre')
def sobre():
    return render_template('sobre.html')


@app.route('/concluir_treino/<int:treino_id>', methods=['POST'])
def concluir_treino(treino_id):
    if 'matricula' not in session:
        return redirect('/login')

    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE treinos SET concluido=1 WHERE id=?", (treino_id,))
    conn.commit()
    conn.close()
    return redirect('/dashboard')

@app.route('/evolucao_peso', methods=['GET', 'POST'])
def evolucao_peso():
    if 'matricula' not in session:
        return redirect('/login')

    matricula = session['matricula']
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        data = request.form['data_peso']
        peso = float(request.form['peso'])
        cursor.execute("INSERT INTO evolucao_peso (matricula, data, peso) VALUES (?, ?, ?)", (matricula, data, peso))
        conn.commit()

    cursor.execute("SELECT data, peso, id FROM evolucao_peso WHERE matricula=? ORDER BY data", (matricula,))
    registros = cursor.fetchall()
    datas = [r[0] for r in registros]
    pesos = [r[1] for r in registros]

    progresso_total = 0
    if len(pesos) >= 2:
        progresso_total = round(pesos[-1] - pesos[0], 1)

    conn.close()
    return render_template('evolucao_peso.html', registros=registros, datas=datas, pesos=pesos, progresso_total=progresso_total)


@app.route('/excluir_peso/<int:id>', methods=['POST'])
def excluir_peso(id):
    if 'matricula' not in session:
        return redirect('/login')

    matricula = session['matricula']
    conn = sqlite3.connect('banco.db')
    cursor = conn.cursor()
    
    # Apenas exclui se o registro pertencer ao usuário logado
    cursor.execute("DELETE FROM evolucao_peso WHERE id=? AND matricula=?", (id, matricula))
    conn.commit()
    conn.close()

    return redirect(url_for('evolucao_peso'))

@app.route('/logout')
def logout():
    session.clear()
    return redirect('/login')

if __name__ == '__main__':
    app.run()
