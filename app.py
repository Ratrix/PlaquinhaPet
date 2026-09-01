# =================================================================
# PROJETO: PLAQUINHA PET 3D
# DESENVOLVEDOR: Joseanderson Langner
# FORMAÇÃO: Engenharia de Controle e Automação
# DATA DE DESENVOLVIMENTO: Agosto de 2026
# DESCRIÇÃO: Sistema web dinâmico de identificação pet via QR Code 
#            otimizado para modelagem e impressão 3D (20x20mm).
# =================================================================

import os
import sqlite3
import io
import zipfile
import qrcode
import qrcode.image.svg
from qrcode.constants import ERROR_CORRECT_L
from flask import Flask, render_template_string, request, redirect, send_file, session
from PIL import Image, ImageDraw, ImageFont

app = Flask(__name__)
app.secret_key = 'chave_secreta_langner_assados_3d'
DB_NAME = 'pets.db'

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT senha FROM pets LIMIT 1")
    except sqlite3.OperationalError:
        cursor.execute("DROP TABLE IF EXISTS pets")

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            id TEXT PRIMARY KEY,
            nome TEXT NOT NULL,
            raca TEXT,
            tutor TEXT NOT NULL,
            telefone TEXT NOT NULL,
            observacoes TEXT,
            status TEXT DEFAULT 'OK',
            senha TEXT
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS config (
            chave TEXT PRIMARY KEY,
            valor TEXT NOT NULL
        )
    ''')

    cursor.execute("SELECT COUNT(*) FROM pets WHERE id = '1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO pets (id, nome, raca, tutor, telefone, observacoes, status, senha)
            VALUES ('1', 'Zoeyy', 'SDS - Só Deus Sabe', 'Joseanderson Langner', '11980837042', 'Possui chip e precisa de medicação.', 'PERDIDO', '1234')
        ''')
        
    cursor.execute("SELECT valor FROM config WHERE chave = 'senha_adm'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO config (chave, valor) VALUES ('senha_adm', '1234')")

    conn.commit()
    conn.close()

def get_senha_adm():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT valor FROM config WHERE chave = 'senha_adm'")
    row = cursor.fetchone()
    conn.close()
    return row[0] if row else '1234'

def set_senha_adm(nova_senha):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("UPDATE config SET valor = ? WHERE chave = 'senha_adm'", (nova_senha,))
    conn.commit()
    conn.close()

init_db()

# --- GERADORES DE QR CODE ---

def gerar_qr_code_20mm_png(link):
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_L, box_size=10, border=1)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB').resize((236, 236))
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', dpi=(300, 300))
    buffer.seek(0)
    return buffer

def gerar_qr_code_svg(link):
    factory = qrcode.image.svg.SvgPathImage
    qr = qrcode.QRCode(version=None, error_correction=ERROR_CORRECT_L, box_size=10, border=1, image_factory=factory)
    qr.add_data(link)
    qr.make(fit=True)
    img = qr.make_image()
    buffer = io.BytesIO()
    img.save(buffer)
    buffer.seek(0)
    return buffer

# --- GERADOR QUE UTILIZA A SUA IMAGEM "gabarito_osso.png" ---
def gerar_preview_plaquinha_50x30(pet_id, nome_pet):
    try:
        # Carrega a imagem enviada por você no GitHub
        img = Image.open('gabarito_osso.png').convert('RGB').resize((600, 380))
    except IOError:
        # Reserva de segurança caso o arquivo falhe
        img = Image.new('RGB', (600, 380), color=(20, 20, 20))

    draw = ImageDraw.Draw(img)

    # 1. Aplica o QR Code dinâmico sobreposto no rebaixo do gabarito
    host = request.host_url.replace('https://', '').replace('http://', '').rstrip('/')
    link = f"{host}/p/{pet_id}"
    qr_img = Image.open(gerar_qr_code_20mm_png(link)).resize((140, 140))
    
    # Posição centralizada para o QR Code
    img.paste(qr_img, (140, 115))

    # 2. Textos (ID do Pet e Instrução)
    try:
        font_sub = ImageFont.truetype("arial.ttf", 16)
    except IOError:
        font_sub = ImageFont.load_default()

    # Chamada e identificador dinâmico do pet
    draw.text((300, 285), f"PLAQUINHA #{pet_id}", fill=(255, 255, 255), font=font_sub, anchor="mm")

    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def home():
    return redirect('/p/1')

@app.route('/p/<pet_id>')
def visualizar_pet_curto(pet_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
    pet = cursor.fetchone()
    conn.close()

    if not pet:
        pet_data = {
            'id': pet_id,
            'nome': f'Plaquinha #{pet_id} (Não Cadastrada)',
            'raca': '',
            'tutor': 'Aguardando Cadastro do Tutor',
            'telefone': '',
            'observacoes': 'Esta plaquinha ainda não foi configurada pelo tutor.',
            'status': 'NOVA'
        }
    else:
        pet_data = {
            'id': pet[0],
            'nome': pet[1],
            'raca': pet[2],
            'tutor': pet[3],
            'telefone': pet[4],
            'observacoes': pet[5],
            'status': pet[6]
        }

    html_template = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Plaquinha Pet - {{ pet.nome }}</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
            .card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 90%; max-width: 380px; text-align: center; }
            .alert-danger { background-color: #e74c3c; color: white; padding: 10px; border-radius: 8px; font-weight: bold; font-size: 14px; margin-bottom: 15px; }
            .alert-warning { background-color: #d35400; color: white; padding: 10px; border-radius: 8px; font-weight: bold; font-size: 14px; margin-bottom: 15px; }
            .nome { font-size: 26px; color: #2c3e50; margin: 5px 0; font-weight: bold; }
            .raca { font-size: 14px; color: #7f8c8d; margin-bottom: 20px; }
            .info-box { background: #f8f9fa; text-align: left; padding: 12px; border-radius: 8px; border-left: 4px solid #3498db; font-size: 13px; margin-bottom: 20px; color: #34495e; }
            .btn-wsp { display: block; background-color: #25d366; color: white; text-decoration: none; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 16px; margin-top: 10px; }
            .footer-link { margin-top: 15px; display: block; font-size: 12px; color: #95a5a6; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="card">
            {% if 'PERDIDO' in pet.status.upper() %}
                <div class="alert-danger">🚨 ATENÇÃO: {{ pet.status.upper() }}</div>
            {% elif 'ROUBADO' in pet.status.upper() %}
                <div class="alert-warning">⚠️ ALERTA: {{ pet.status.upper() }}</div>
            {% elif pet.status != 'OK' and pet.status != 'NOVA' and pet.status != '' %}
                <div class="alert-warning">ℹ️ STATUS: {{ pet.status.upper() }}</div>
            {% endif %}

            <div class="nome">🐾 {{ pet.nome }}</div>
            
            {% if pet.raca %}
                <div class="raca"><strong>Raça:</strong> {{ pet.raca }}</div>
            {% endif %}

            <div class="info-box">
                <p style="margin: 3px 0;"><strong>Tutor:</strong> {{ pet.tutor }}</p>
                <p style="margin: 3px 0;"><strong>Observações:</strong> {{ pet.observacoes }}</p>
            </div>

            {% if pet.telefone %}
            <a href="https://wa.me/{{ pet.telefone }}?text=Olá,%20encontrei%20o(a)%20{{ pet.nome }}!" class="btn-wsp" target="_blank">
                💬 Falar com Tutor no WhatsApp
            </a>
            {% endif %}

            <a href="/cadastrar?id={{ pet.id }}" class="footer-link">Área do Tutor (Editar Dados)</a>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, pet=pet_data)

@app.route('/qrcode/<pet_id>')
def qrcode_pet(pet_id):
    host = request.host_url.replace('https://', '').replace('http://', '').rstrip('/')
    link = f"{host}/p/{pet_id}"
    img_buffer = gerar_qr_code_20mm_png(link)
    return send_file(img_buffer, mimetype='image/png')

@app.route('/qrcode/svg/<pet_id>')
def qrcode_pet_svg(pet_id):
    host = request.host_url.replace('https://', '').replace('http://', '').rstrip('/')
    link = f"{host}/p/{pet_id}"
    img_buffer = gerar_qr_code_svg(link)
    return send_file(img_buffer, mimetype='image/svg+xml', as_attachment=True, download_name=f'qrcode_plaquinha_{pet_id}.svg')

@app.route('/preview/plaquinha/<pet_id>')
def preview_plaquinha(pet_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome FROM pets WHERE id = ?", (pet_id,))
    pet = cursor.fetchone()
    conn.close()
    
    nome_pet = pet[0] if pet else "PET"
    img_buffer = gerar_preview_plaquinha_50x30(pet_id, nome_pet)
    return send_file(img_buffer, mimetype='image/png')

# --- ÁREA EXCLUSIVA DO TUTOR ---
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    erro = None
    autenticado_tutor = False

    pet_id = request.args.get('id') or request.form.get('id') or '1'

    if request.method == 'POST':
        senha_informada = request.form.get('senha_atual', '')

        cursor.execute("SELECT senha FROM pets WHERE id = ?", (pet_id,))
        pet_existente = cursor.fetchone()
        senha_correta = pet_existente[0] if (pet_existente and pet_existente[0]) else '1234'

        if senha_informada != senha_correta:
            erro = "Senha incorreta! A senha padrão de primeiro acesso é 1234."
        else:
            if 'salvar' in request.form:
                nome = request.form['nome']
                raca = request.form['raca']
                tutor = request.form['tutor']
                telefone = request.form['telefone']
                observacoes = request.form['observacoes']
                status_opcao = request.form['status_select']
                status_custom = request.form.get('status_custom', '').strip()
                nova_senha = request.form.get('nova_senha', '')

                status_final = status_custom if status_opcao == 'CUSTOM' and status_custom else status_opcao
                senha_final = nova_senha if nova_senha.strip() != '' else senha_correta

                cursor.execute('''
                    INSERT INTO pets (id, nome, raca, tutor, telefone, observacoes, status, senha)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    ON CONFLICT(id) DO UPDATE SET
                        nome=excluded.nome, raca=excluded.raca, tutor=excluded.tutor,
                        telefone=excluded.telefone, observacoes=excluded.observacoes,
                        status=excluded.status, senha=excluded.senha
                ''', (pet_id, nome, raca, tutor, telefone, observacoes, status_final, senha_final))
                
                conn.commit()
                conn.close()
                return redirect(f'/p/{pet_id}')
            else:
                autenticado_tutor = True

    cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
    pet = cursor.fetchone()
    conn.close()

    html_form = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Área do Tutor - PlaquinhaPet</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
            .form-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.1); width: 100%; max-width: 400px; }
            h2 { color: #2c3e50; text-align: center; margin-top: 0; font-size: 20px; }
            .erro { background-color: #e74c3c; color: white; padding: 10px; border-radius: 6px; font-size: 13px; text-align: center; margin-bottom: 15px; }
            label { font-size: 13px; color: #34495e; font-weight: bold; display: block; margin-top: 10px; }
            input, select, textarea { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
            .sec-pass { background: #edf2f7; padding: 12px; border-radius: 8px; margin-top: 15px; border: 1px solid #cbd5e0; }
            .help-text { font-size: 11px; color: #7f8c8d; margin-top: 3px; display: block; }
            button { width: 100%; background-color: #3498db; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 16px; margin-top: 20px; cursor: pointer; }
            .qr-link { display: block; text-align: center; margin-top: 15px; color: #27ae60; text-decoration: none; font-size: 13px; font-weight: bold; }
            .svg-link { display: block; text-align: center; margin-top: 8px; color: #8e44ad; text-decoration: none; font-size: 12px; font-weight: bold; }
            .preview-link { display: block; text-align: center; margin-top: 8px; color: #d35400; text-decoration: none; font-size: 12px; font-weight: bold; }
            
            .header-id-container { display: flex; align-items: center; justify-content: space-between; margin-bottom: 15px; }
            .num-badge { border: 2px solid #e74c3c; color: #e74c3c; font-weight: bold; font-size: 18px; padding: 4px 12px; border-radius: 6px; }
            .num-label { font-size: 10px; color: #e74c3c; font-weight: bold; text-transform: uppercase; letter-spacing: 0.5px; display: block; margin-bottom: 2px; }
        </style>
        <script>
            function toggleCustomStatus(selectObject) {
                var customInput = document.getElementById("status_custom_div");
                if (selectObject.value === "CUSTOM") { customInput.style.display = "block"; } 
                else { customInput.style.display = "none"; }
            }
        </script>
    </head>
    <body>
        <div class="form-card">
            
            {% if erro %}
                <div class="erro">{{ erro }}</div>
            {% endif %}

            {% if not autenticado_tutor %}
                <form method="POST" action="/cadastrar?id={{ pet_id }}">
                    <input type="hidden" name="id" value="{{ pet_id }}">

                    <div>
                        <span class="num-label">NÚMERO DA PLAQUINHA</span>
                        <div class="header-id-container">
                            <div class="num-badge">{{ pet_id }}</div>
                            <h2>⚙️ Área do Tutor</h2>
                        </div>
                    </div>

                    <div class="sec-pass">
                        <label style="margin-top:0;">🔑 Digite a Senha:</label>
                        <input type="password" name="senha_atual" placeholder="Digite a senha" required autofocus>
                        <span class="help-text">ℹ️ Primeiro acesso: <strong>1234</strong></span>
                    </div>

                    <button type="submit" name="entrar">🔓 Acessar Dados</button>
                </form>

            {% else %}
                <h2>⚙️ Área do Tutor</h2>
                <form method="POST" action="/cadastrar?id={{ pet_id }}">
                    <input type="hidden" name="id" value="{{ pet_id }}">

                    <label>ID da Plaquinha:</label>
                    <input type="text" value="{{ pet[0] if pet else pet_id }}" disabled style="background:#e9ecef;">

                    <label>Nome do Pet:</label>
                    <input type="text" name="nome" value="{{ pet[1] if pet else '' }}" placeholder="Ex: Zoey" required>

                    <label>Raça / Espécie:</label>
                    <input type="text" name="raca" value="{{ pet[2] if pet else '' }}" placeholder="Ex: Poodle / Vira-lata">

                    <label>Nome do Tutor:</label>
                    <input type="text" name="tutor" value="{{ pet[3] if pet else '' }}" placeholder="Seu nome completo" required>

                    <label>Telefone/WhatsApp (com DDD):</label>
                    <input type="text" name="telefone" value="{{ pet[4] if pet else '' }}" placeholder="Ex: 11999999999" required>

                    <label>Status do Pet:</label>
                    <select name="status_select" onchange="toggleCustomStatus(this)">
                        <option value="OK" {% if pet and pet[6] == 'OK' %}selected{% endif %}>🟢 Seguro (Normal)</option>
                        <option value="PERDIDO" {% if pet and pet[6] == 'PERDIDO' %}selected{% endif %}>🚨 PERDIDO!</option>
                        <option value="ROUBADO" {% if pet and pet[6] == 'ROUBADO' %}selected{% endif %}>⚠️ ROUBADO!</option>
                        <option value="CUSTOM" {% if pet and pet[6] not in ['OK', 'PERDIDO', 'ROUBADO'] and pet[6] %}selected{% endif %}>✏️ Personalizado (Escrever)</option>
                    </select>

                    <div id="status_custom_div" style="display: {% if pet and pet[6] not in ['OK', 'PERDIDO', 'ROUBADO'] and pet[6] %}block{% else %}none{% endif %};">
                        <label>✏️ Digite o Status Personalizado:</label>
                        <input type="text" name="status_custom" placeholder="Ex: Em Lar Temporário / Procurado" value="{{ pet[6] if pet and pet[6] not in ['OK', 'PERDIDO', 'ROUBADO'] else '' }}">
                    </div>

                    <label>Observações / Recomendações:</label>
                    <textarea name="observacoes" rows="3" placeholder="Possui chip, toma medicação...">{{ pet[5] if pet else '' }}</textarea>

                    <div class="sec-pass">
                        <input type="hidden" name="senha_atual" value="{{ pet[7] if pet else '1234' }}">
                        <label style="margin-top:0;">🔒 Nova Senha (Opcional):</label>
                        <input type="password" name="nova_senha" placeholder="Digite para alterar a senha">
                    </div>

                    <button type="submit" name="salvar" style="background-color: #27ae60;">💾 Salvar Alterações</button>
                </form>
            {% endif %}

            <a href="/preview/plaquinha/{{ pet_id }}" target="_blank" class="preview-link">🦴 Ver Modelo 3D (Gabarito Real)</a>
            <a href="/qrcode/{{ pet_id }}" target="_blank" class="qr-link">🔍 Visualizar QR Code PNG (ID {{ pet_id }})</a>
            <a href="/qrcode/svg/{{ pet_id }}" target="_blank" class="svg-link">📐 Baixar Vetor SVG para Fusion 360 (ID {{ pet_id }})</a>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_form, pet=pet, erro=erro, autenticado_tutor=autenticado_tutor, pet_id=pet_id)

# --- ROTA RESTRITA EXCLUSIVA DO PAINEL ADM ---
@app.route('/admin', methods=['GET', 'POST'])
def admin():
    erro = None
    sucesso = None
    autenticado_adm = session.get('is_admin', False)
    senha_adm_atual = get_senha_adm()

    if request.method == 'POST':
        if 'login_adm' in request.form:
            senha_ingres = request.form.get('senha_adm_login', '')
            if senha_ingres == senha_adm_atual:
                session['is_admin'] = True
                autenticado_adm = True
            else:
                erro = "Senha Mestre do Administrador incorreta!"

        elif 'gerar_lote' in request.form and autenticado_adm:
            inicio = int(request.form.get('inicio', 1))
            quantidade = int(request.form.get('quantidade', 150))
            host = request.host_url.replace('https://', '').replace('http://', '').rstrip('/')
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zip_file:
                for i in range(inicio, inicio + quantidade):
                    pid = str(i)
                    link = f"{host}/p/{pid}"
                    svg_data = gerar_qr_code_svg(link).getvalue()
                    zip_file.writestr(f"plaquinha_{i:03d}.svg", svg_data)
            
            zip_buffer.seek(0)
            return send_file(zip_buffer, mimetype='application/zip', as_attachment=True, download_name=f'lote_plaquinhas_{inicio}_a_{inicio + quantidade - 1}.zip')

        elif 'alterar_senha_adm' in request.form and autenticado_adm:
            nova_senha_mestre = request.form.get('nova_senha_mestre', '').strip()
            if nova_senha_mestre:
                set_senha_adm(nova_senha_mestre)
                sucesso = "Senha Mestre alterada com sucesso!"
            else:
                erro = "A nova senha Mestre não pode estar em branco."

    html_admin = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Painel ADM - PlaquinhaPet</title>
        <style>
            body { font-family: 'Segoe UI', sans-serif; background-color: #2c3e50; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; padding: 20px; }
            .form-card { background: white; padding: 25px; border-radius: 15px; box-shadow: 0 4px 15px rgba(0,0,0,0.2); width: 100%; max-width: 400px; }
            h2 { color: #2c3e50; text-align: center; margin-top: 0; font-size: 20px; }
            .erro { background-color: #e74c3c; color: white; padding: 10px; border-radius: 6px; font-size: 13px; text-align: center; margin-bottom: 15px; }
            .sucesso { background-color: #27ae60; color: white; padding: 10px; border-radius: 6px; font-size: 13px; text-align: center; margin-bottom: 15px; }
            label { font-size: 13px; color: #34495e; font-weight: bold; display: block; margin-top: 10px; }
            input { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
            .sec-pass { background: #edf2f7; padding: 12px; border-radius: 8px; margin-top: 15px; border: 1px solid #cbd5e0; }
            button { width: 100%; background-color: #8e44ad; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 16px; margin-top: 15px; cursor: pointer; }
            .logout-adm { display: block; text-align: center; margin-top: 15px; color: #e74c3c; font-size: 12px; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="form-card">
            <h2>🛠️ Painel do Desenvolvedor</h2>

            {% if erro %}<div class="erro">{{ erro }}</div>{% endif %}
            {% if sucesso %}<div class="sucesso">{{ sucesso }}</div>{% endif %}

            {% if not autenticado_adm %}
                <form method="POST">
                    <label>🔑 Digite a Senha Mestre ADM:</label>
                    <input type="password" name="senha_adm_login" placeholder="Digite sua senha Mestre" required autofocus>
                    <button type="submit" name="login_adm">Acessar Painel</button>
                </form>
            {% else %}
                <form method="POST">
                    <label>🔢 ID do Primeiro Número:</label>
                    <input type="number" name="inicio" value="1" min="1" required>

                    <label>📦 Quantidade de QR Codes (Lote):</label>
                    <input type="number" name="quantidade" value="150" min="1" max="500" required>

                    <button type="submit" name="gerar_lote">🚀 Baixar Lote SVG (ZIP)</button>
                </form>

                <form method="POST">
                    <div class="sec-pass">
                        <label style="margin-top:0;">🔐 Nova Senha Mestre:</label>
                        <input type="password" name="nova_senha_mestre" placeholder="Sua nova senha pessoal" required>
                        <button type="submit" name="alterar_senha_adm" style="background-color: #e67e22; font-size: 14px; padding: 8px;">🔑 Salvar Senha Mestre</button>
                    </div>
                </form>

                <a href="/admin_logout" class="logout-adm">Sair do Painel ADM</a>
            {% endif %}
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_admin, erro=erro, sucesso=sucesso, autenticado_adm=autenticado_adm)

@app.route('/admin_logout')
def admin_logout():
    session.pop('is_admin', None)
    return redirect('/admin')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
