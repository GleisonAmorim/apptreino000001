# =========================
# IMPORTAÇÕES
# =========================

# Flask: framework web para criar o site
from flask import Flask, render_template, request, redirect, session, url_for

# sqlite3: banco de dados simples em arquivo (.db)
import sqlite3

# os: permite acessar variáveis do sistema e caminhos de arquivos
import os

# Funções prontas para criptografar senha e validar senha
from werkzeug.security import generate_password_hash, check_password_hash

# =========================
# CONFIGURAÇÃO DO FLASK
# =========================

# Cria a aplicação Flask
app = Flask(__name__)

# Chave secreta usada para segurança da sessão (login)
# Em produção, usa variável de ambiente
app.secret_key = os.environ.get('SECRET_KEY', 'dev_key')

# =========================
# CONFIGURAÇÃO DO BANCO
# =========================

# Caminho da pasta onde está o arquivo app.py
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
# Caminho completo do arquivo banco.db
DB_PATH = os.path.join(BASE_DIR, 'banco.db')

# Função que abre conexão com o banco
def get_db():
    return sqlite3.connect(DB_PATH)

# Função que cria as tabelas do banco (caso não existam)
def init_db():
    conn = get_db()
    cursor = conn.cursor()

    # Tabela de usuários
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usuarios (
        matricula INTEGER PRIMARY KEY AUTOINCREMENT,
        usuario TEXT UNIQUE NOT NULL,
        senha TEXT NOT NULL,
        email TEXT UNIQUE NOT NULL
    )
    """)

    # Tabela de treinos
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS treinos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula INTEGER NOT NULL,
        nome_treino TEXT NOT NULL,
        concluido INTEGER DEFAULT 0,
        FOREIGN KEY (matricula) REFERENCES usuarios (matricula)
    )
    """)

    # Tabela de exercícios de cada treino
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS exercicios (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        treino_id INTEGER NOT NULL,
        nome_exercicio TEXT NOT NULL,
        repeticoes TEXT NOT NULL,
        peso TEXT NOT NULL,
        FOREIGN KEY (treino_id) REFERENCES treinos (id)
    )
    """)

    # Tabela para controle da evolução de peso do usuário
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS evolucao_peso (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        matricula INTEGER NOT NULL,
        data TEXT NOT NULL,
        peso REAL NOT NULL,
        FOREIGN KEY (matricula) REFERENCES usuarios (matricula)
    )
    """)

    # Salva as alterações no banco
    conn.commit()
    conn.close()

# Executa a criação das tabelas ao iniciar o app
init_db()

# =========================
# ROTAS DO SISTEMA
# =========================

# Página inicial redireciona para login
@app.route('/')
def index():
    return redirect('/login')

# =========================
# LOGIN
# =========================
@app.route('/login', methods=['GET', 'POST'])
def login():
    # Se o formulário foi enviado
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']        
        
    # Busca o usuário no banco
        conn = get_db()
        cursor = conn.cursor()
        cursor.execute("SELECT matricula, senha FROM usuarios WHERE usuario=?", (usuario,))
        dados = cursor.fetchone()
        conn.close()

    # Verifica se a senha digitada bate com a senha criptografada
        if dados and check_password_hash(dados[1], senha):
    # Salva a matrícula na sessão (login ativo)
            session['matricula'] = dados[0]
            return redirect('/dashboard')

        return "Usuário ou senha inválidos"
    
    # Se for GET, apenas mostra a página
    return render_template('login.html')


# =========================
# CADASTRO DE USUÁRIO
# =========================
# Esta rota é responsável por cadastrar novos usuários no sistema
# Ela aceita dois métodos:
# GET  -> apenas exibe a página de cadastro
# POST -> recebe os dados do formulário e salva no banco
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():

    # Verifica se o formulário foi enviado (botão "Cadastrar" clicado)
    if request.method == 'POST':

        # Obtém o nome de usuário digitado no formulário HTML
        usuario = request.form['usuario']

        # Criptografa a senha antes de salvar no banco
        # Isso garante mais segurança e evita salvar a senha em texto puro
        senha = generate_password_hash(request.form['senha'])

        # Obtém o e-mail digitado no formulário HTML
        email = request.form['email']

        # Abre conexão com o banco de dados
        conn = get_db()

        # Cria um cursor para executar comandos SQL
        cursor = conn.cursor()

        try:
            # Insere o novo usuário na tabela 'usuarios'
            # Os ? evitam ataques de SQL Injection
            cursor.execute(
                "INSERT INTO usuarios (usuario, senha, email) VALUES (?, ?, ?)",
                (usuario, senha, email)
            )

            # Salva definitivamente as alterações no banco
            conn.commit()

        except sqlite3.IntegrityError:
            # Esse erro acontece se o usuário ou o e-mail já existir no banco
            conn.close()

            # Retorna uma mensagem informando o problema
            return "Usuário ou email já cadastrado"

        # Fecha a conexão com o banco de dados
        conn.close()

        # Após o cadastro com sucesso, redireciona para a tela de login
        return redirect('/login')

    # Caso o método seja GET, apenas exibe a página de cadastro
    return render_template('cadastro.html')


# =========================
# DASHBOARD (PAINEL PRINCIPAL)
# =========================
@app.route('/dashboard')
def dashboard():
    # Verifica se o usuário está logado
    if 'matricula' not in session:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    # Busca todos os treinos do usuário
    cursor.execute(
        "SELECT id, nome_treino, concluido FROM treinos WHERE matricula=?",
        (session['matricula'],)
    )
    treinos = cursor.fetchall()

    # Lista final com treinos + exercícios
    dados = []
    for treino in treinos:
        cursor.execute(
            "SELECT id, nome_exercicio, repeticoes, peso FROM exercicios WHERE treino_id=?",
            (treino[0],)
        )
        dados.append({
            'id': treino[0],
            'nome_treino': treino[1],
            'concluido': treino[2],
            'exercicios': cursor.fetchall()
        })

    conn.close()
    return render_template('dashboard.html', treinos=dados)


# =========================
# CRIAÇÃO DE TREINO
# =========================
@app.route('/novo_treino')
def novo_treino():
    if 'matricula' not in session:
        return redirect('/login')
    return render_template('novo_treino.html')


@app.route('/adicionar_treino', methods=['POST'])
def adicionar_treino():
    if 'matricula' not in session:
        return redirect('/login')

    conn = get_db()
    cursor = conn.cursor()

    # Cria o treino
    cursor.execute(
        "INSERT INTO treinos (matricula, nome_treino) VALUES (?, ?)",
        (session['matricula'], request.form['nome_treino'])
    )
    # Pega o ID do treino recém-criado
    treino_id = cursor.lastrowid

    # Listas vindas do formulário
    nomes = request.form.getlist('nome_exercicio')
    reps = request.form.getlist('repeticoes')
    pesos = request.form.getlist('peso')

    # Insere os exercícios
    for n, r, p in zip(nomes, reps, pesos):
        if n.strip() and r.strip() and p.strip():
            cursor.execute(
                "INSERT INTO exercicios (treino_id, nome_exercicio, repeticoes, peso) VALUES (?, ?, ?, ?)",
                (treino_id, n, r, p)
            )

    conn.commit()
    conn.close()
    return redirect('/dashboard')

# =========================
# EDIÇÃO DE TREINO E EXERCÍCIOS
# =========================
# Esta rota permite editar um treino existente:
# - Alterar o nome do treino
# - Editar exercícios já cadastrados
# - Excluir exercícios
# - Adicionar novos exercícios ao treino
@app.route('/editar_treino/<int:treino_id>', methods=['GET', 'POST'])
def editar_treino(treino_id):

    # Verifica se o usuário está logado
    # Se não estiver, redireciona para a tela de login
    if 'matricula' not in session:
        return redirect('/login')

    # Abre conexão com o banco de dados
    conn = get_db()
    cursor = conn.cursor()

    # =========================
    # QUANDO O FORMULÁRIO É ENVIADO (POST)
    # =========================
    if request.method == 'POST':

        # Atualiza o nome do treino no banco de dados
        cursor.execute(
            "UPDATE treinos SET nome_treino=? WHERE id=?",
            (request.form['nome_treino'], treino_id)
        )

        # Recebe os dados dos exercícios já existentes no formulário
        ids = request.form.getlist('exercicio_id')                 # IDs dos exercícios
        nomes = request.form.getlist('nome_exercicio_existente')   # Nomes dos exercícios
        reps = request.form.getlist('repeticoes_existente')        # Repetições
        pesos = request.form.getlist('peso_existente')             # Pesos

        # Atualiza cada exercício existente
        for ex_id, n, r, p in zip(ids, nomes, reps, pesos):
            cursor.execute(
                "UPDATE exercicios SET nome_exercicio=?, repeticoes=?, peso=? WHERE id=?",
                (n, r, p, ex_id)
            )

        # Recebe os IDs dos exercícios que o usuário marcou para excluir
        excluir_ids = request.form.getlist('excluir_exercicio_id')

        # Exclui os exercícios selecionados
        for ex_id in excluir_ids:
            cursor.execute(
                "DELETE FROM exercicios WHERE id=?",
                (ex_id,)
            )

        # Recebe os dados dos novos exercícios adicionados no formulário
        novos_nomes = request.form.getlist('nome_exercicio')
        novos_reps = request.form.getlist('repeticoes')
        novos_pesos = request.form.getlist('peso')

        # Insere novos exercícios no banco de dados
        for n, r, p in zip(novos_nomes, novos_reps, novos_pesos):
            # Verifica se os campos não estão vazios
            if n.strip() and r.strip() and p.strip():
                cursor.execute(
                    "INSERT INTO exercicios (treino_id, nome_exercicio, repeticoes, peso) VALUES (?, ?, ?, ?)",
                    (treino_id, n, r, p)
                )

        # Salva todas as alterações feitas no banco
        conn.commit()

        # Fecha a conexão com o banco
        conn.close()

        # Após salvar, redireciona o usuário para o dashboard
        return redirect('/dashboard')

    # =========================
    # QUANDO APENAS ABRE A PÁGINA (GET)
    # =========================

    # Busca o nome do treino para exibir no formulário
    cursor.execute(
        "SELECT nome_treino FROM treinos WHERE id=?",
        (treino_id,)
    )
    nome_treino = cursor.fetchone()[0]

    # Busca todos os exercícios relacionados a esse treino
    cursor.execute(
        "SELECT id, nome_exercicio, repeticoes, peso FROM exercicios WHERE treino_id=?",
        (treino_id,)
    )
    exercicios = cursor.fetchall()

    # Fecha a conexão com o banco
    conn.close()

    # Renderiza a página de edição do treino,
    # enviando os dados necessários para o HTML
    return render_template(
        'editar_treino.html',
        treino_id=treino_id,
        nome_treino=nome_treino,
        exercicios=exercicios
    )



# =========================
# EVOLUÇÃO DE PESO DO USUÁRIO
# =========================
# Esta funcionalidade permite:
# - Registrar o peso do usuário por data
# - Listar o histórico de pesos
# - Gerar dados para o gráfico de evolução
# - Calcular o progresso total (ganho ou perda de peso)
@app.route('/evolucao_peso', methods=['GET', 'POST'])
def evolucao_peso():

    # Verifica se o usuário está logado
    # Caso não esteja, redireciona para o login
    if 'matricula' not in session:
        return redirect('/login')

    # Abre conexão com o banco de dados
    conn = get_db()
    cursor = conn.cursor()

    # =========================
    # QUANDO O FORMULÁRIO É ENVIADO (POST)
    # =========================
    if request.method == 'POST':

        # Insere um novo registro de peso no banco
        # Cada registro possui:
        # - matrícula do usuário
        # - data informada
        # - peso convertido para número decimal
        cursor.execute(
            "INSERT INTO evolucao_peso (matricula, data, peso) VALUES (?, ?, ?)",
            (
                session['matricula'],              # Identifica o usuário logado
                request.form['data_peso'],          # Data do registro
                float(request.form['peso'])         # Peso informado
            )
        )

        # Salva a alteração no banco
        conn.commit()

    # =========================
    # BUSCA DOS DADOS PARA EXIBIÇÃO
    # =========================

    # Busca todos os registros de peso do usuário
    # Ordena os dados pela data (do mais antigo para o mais recente)
    cursor.execute(
        "SELECT data, peso, id FROM evolucao_peso WHERE matricula=? ORDER BY data",
        (session['matricula'],)
    )
    registros = cursor.fetchall()

    # =========================
    # PREPARAÇÃO DOS DADOS PARA O GRÁFICO
    # =========================

    # Lista apenas as datas dos registros
    datas = [r[0] for r in registros] if registros else []

    # Lista apenas os pesos dos registros
    pesos = [r[1] for r in registros] if registros else []

    # =========================
    # CÁLCULO DO PROGRESSO TOTAL
    # =========================

    # Inicia o progresso como zero
    progresso_total = 0

    # Se houver pelo menos dois registros,
    # calcula a diferença entre o primeiro e o último peso
    if len(pesos) >= 2:
        progresso_total = round(pesos[-1] - pesos[0], 1)

    # Fecha a conexão com o banco
    conn.close()

    # Envia os dados para o HTML:
    # - histórico de pesos
    # - listas para o gráfico
    # - progresso total
    return render_template(
        'evolucao_peso.html',
        registros=registros,
        datas=datas,
        pesos=pesos,
        progresso_total=progresso_total
    )


# =========================
# EXCLUSÃO DE REGISTRO DE PESO
# =========================
# Permite ao usuário excluir um registro específico de peso
@app.route('/excluir_peso/<int:id>', methods=['POST'])
def excluir_peso(id):

    # Verifica se o usuário está logado
    if 'matricula' not in session:
        return redirect('/login')

    # Abre conexão com o banco de dados
    conn = get_db()
    cursor = conn.cursor()

    # Remove o registro de peso apenas se pertencer ao usuário logado
    cursor.execute(
        "DELETE FROM evolucao_peso WHERE id=? AND matricula=?",
        (id, session['matricula'])
    )

    # Confirma a exclusão
    conn.commit()

    # Fecha a conexão
    conn.close()

    # Retorna para a página de evolução de peso
    return redirect(url_for('evolucao_peso'))

# =========================
# VÍDEOS DE TREINO
# =========================
@app.route('/videos')
def videos():
    # Garante que o usuário esteja logado
    if 'matricula' not in session:
        return redirect('/login')

    # Caminho da pasta de vídeos
    pasta_videos = os.path.join(app.static_folder, 'videos')

    # Lista apenas arquivos de vídeo
    extensoes_validas = ('.mp4', '.webm', '.ogg')
    lista_videos = []

    if os.path.exists(pasta_videos):
        for arquivo in os.listdir(pasta_videos):
            if arquivo.lower().endswith(extensoes_validas):
                lista_videos.append(arquivo)

    return render_template('videos.html', videos=lista_videos)

# =========================
# LOGOUT DO USUÁRIO
# =========================
# Esta rota é responsável por encerrar a sessão do usuário.
# Quando o logout é executado:
# - Todos os dados da sessão são apagados
# - O usuário é redirecionado para a tela de login
@app.route('/logout')
def logout():

    # Remove todas as informações armazenadas na sessão
    # Exemplo: matrícula do usuário logado
    session.clear()

    # Após limpar a sessão, redireciona para a página de login
    return redirect('/login')


# =========================
# EXECUÇÃO DA APLICAÇÃO
# =========================
# Este bloco garante que o servidor Flask só será iniciado
# quando este arquivo for executado diretamente
# (e não quando for importado por outro arquivo)
if __name__ == '__main__':

    # Define a porta do servidor:
    # - Usa a variável de ambiente PORT (caso exista)
    # - Caso contrário, utiliza a porta padrão 5000
    port = int(os.environ.get('PORT', 5000))

    # Inicia o servidor Flask
    # host='0.0.0.0' permite acesso externo (ex: rede/local ou deploy)
    # debug=True ativa mensagens de erro detalhadas (apenas para desenvolvimento)
    app.run(host='0.0.0.0', port=port, debug=True)
