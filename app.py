import os
import sqlite3
import io
import qrcode
from qrcode.constants import ERROR_CORRECT_L
from flask import Flask, render_template_string, request, redirect, send_file

app = Flask(__name__)
DB_NAME = 'pets.db'

# --- CONFIGURAÇÃO DO BANCO DE DADOS COM SENHA ---
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
    
    cursor.execute("SELECT COUNT(*) FROM pets WHERE id = '1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO pets (id, nome, raca, tutor, telefone, observacoes, status, senha)
            VALUES ('1', 'Zoeyy', 'SDS - Só Deus Sabe', 'Joseanderson Langner', '11980837042', 'Possui chip e precisa de medicação.', 'PERDIDO', '1234')
        ''')
    conn.commit()
    conn.close()

init_db()

# --- GERADOR DE QR CODE MÍNIMO (20x20mm) ---
def gerar_qr_code_20mm(link):
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_L,
        box_size=10,
        border=1
    )
    qr.add_data(link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white").convert('RGB')
    img = img.resize((236, 236))
    
    buffer = io.BytesIO()
    img.save(buffer, format='PNG', dpi=(300, 300))
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
        return "Pet não encontrado", 404

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
            .alert { background-color: #e74c3c; color: white; padding: 10px; border-radius: 8px; font-weight: bold; font-size: 14px; margin-bottom: 15px; }
            .nome { font-size: 26px; color: #2c3e50; margin: 5px 0; font-weight: bold; }
            .raca { font-size: 14px; color: #7f8c8d; margin-bottom: 20px; }
            .info-box { background: #f8f9fa; text-align: left; padding: 12px; border-radius: 8px; border-left: 4px solid #3498db; font-size: 13px; margin-bottom: 20px; color: #34495e; }
            .btn-wsp { display: block; background-color: #25d366; color: white; text-decoration: none; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 16px; margin-top: 10px; }
            .footer-link { margin-top: 15px; display: block; font-size: 12px; color: #95a5a6; text-decoration: none; }
        </style>
    </head>
    <body>
        <div class="card">
            {% if pet.status == 'PERDIDO' %}
                <div class="alert">🚨 ATENÇÃO: ESTE PET ESTÁ PERDIDO!</div>
            {% endif %}
            <div class="nome">🐾 {{ pet.nome }}</div>
            <div class="raca">{{ pet.raca }}</div>
            <div class="info-box">
                <p style="margin: 3px 0;"><strong>Tutor:</strong> {{ pet.tutor }}</p>
                <p style="margin: 3px 0;"><strong>Observações:</strong> {{ pet.observacoes }}</p>
            </div>
            <a href="https://wa.me/{{ pet.telefone }}?text=Olá,%20encontrei%20o(a)%20{{ pet.nome }}!" class="btn-wsp" target="_blank">
                💬 Falar com Tutor no WhatsApp
            </a>
            <a href="/cadastrar" class="footer-link">Área do Tutor (Editar Dados)</a>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, pet=pet_data)

@app.route('/qrcode/<pet_id>')
def qrcode_pet(pet_id):
    host = request.host_url.replace('https://', '').replace('http://', '').rstrip('/')
    link = f"{host}/p/{pet_id}"
    img_buffer = gerar_qr_code_20mm(link)
    return send_file(img_buffer, mimetype='image/png')

# --- PAINEL DO TUTOR COM SEGURANÇA E ALTERAÇÃO DE SENHA ---
@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    erro = None

    if request.method == 'POST':
        pet_id = request.form['id']
        nome = request.form['nome']
        raca = request.form['raca']
        tutor = request.form['tutor']
        telefone = request.form['telefone']
        observacoes = request.form['observacoes']
        status = request.form['status']
        senha_informada = request.form.get('senha_atual', '')
        nova_senha = request.form.get('nova_senha', '')

        cursor.execute("SELECT senha FROM pets WHERE id = ?", (pet_id,))
        pet_existente = cursor.fetchone()

        if pet_existente and pet_existente[0]:
            if pet_existente[0] != senha_informada:
                erro = "Senha atual incorreta! As alterações não foram salvas."
                cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
                pet = cursor.fetchone()
                conn.close()
                return render_template_string(html_form, pet=pet, erro=erro)

        senha_final = nova_senha if nova_senha.strip() != '' else (pet_existente[0] if pet_existente else senha_informada)

        cursor.execute('''
            INSERT INTO pets (id, nome, raca, tutor, telefone, observacoes, status, senha)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                nome=excluded.nome,
                raca=excluded.raca,
                tutor=excluded.tutor,
                telefone=excluded.telefone,
                observacoes=excluded.observacoes,
                status=excluded.status,
                senha=excluded.senha
        ''', (pet_id, nome, raca, tutor, telefone, observacoes, status, senha_final))
        
        conn.commit()
        conn.close()
        return redirect(f'/p/{pet_id}')

    cursor.execute("SELECT * FROM pets WHERE id = '1'")
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
            h2 { color: #2c3e50; text-align: center; margin-top: 0; }
            .erro { background-color: #e74c3c; color: white; padding: 10px; border-radius: 6px; font-size: 13px; text-align: center; margin-bottom: 15px; }
            label { font-size: 13px; color: #34495e; font-weight: bold; display: block; margin-top: 10px; }
            input, select, textarea { width: 100%; padding: 10px; margin-top: 5px; border: 1px solid #ccc; border-radius: 6px; box-sizing: border-box; }
            .sec-pass { background: #edf2f7; padding: 12px; border-radius: 8px; margin-top: 15px; border: 1px solid #cbd5e0; }
            button { width: 100%; background-color: #3498db; color: white; border: none; padding: 12px; border-radius: 8px; font-weight: bold; font-size: 16px; margin-top: 20px; cursor: pointer; }
            .qr-link { display: block; text-align: center; margin-top: 15px; color: #27ae60; text-decoration: none; font-size: 13px; font-weight: bold; }
        </style>
    </head>
    <body>
        <div class="form-card">
            <h2>⚙️ Área do Tutor</h2>
            
            {% if erro %}
                <div class="erro">{{ erro }}</div>
            {% endif %}

            <form method="POST">
                <label>ID da Plaquinha:</label>
                <input type="text" name="id" value="{{ pet[0] if pet else '1' }}" required>

                <label>Nome do Pet:</label>
                <input type="text" name="nome" value="{{ pet[1] if pet else '' }}" required>

                <label>Raça / Espécie:</label>
                <input type="text" name="raca" value="{{ pet[2] if pet else '' }}">

                <label>Nome do Tutor:</label>
                <input type="text" name="tutor" value="{{ pet[3] if pet else '' }}" required>

                <label>Telefone/WhatsApp (com DDD):</label>
                <input type="text" name="telefone" value="{{ pet[4] if pet else '' }}" required>

                <label>Status do Pet:</label>
                <select name="status">
                    <option value="OK" {% if pet and pet[6] == 'OK' %}selected{% endif %}>🟢 Seguro (Normal)</option>
                    <option value="PERDIDO" {% if pet and pet[6] == 'PERDIDO' %}selected{% endif %}>🚨 PERDIDO!</option>
                </select>

                <label>Observações / Recomendações:</label>
                <textarea name="observacoes" rows="3">{{ pet[5] if pet else '' }}</textarea>

                <div class="sec-pass">
                    <label style="margin-top:0;">🔑 Senha Atual (Para Autorizar):</label>
                    <input type="password" name="senha_atual" placeholder="Digite a senha atual" required>

                    <label>🔒 Nova Senha (Opcional):</label>
                    <input type="password" name="nova_senha" placeholder="Deixe em branco para manter a mesma">
                </div>

                <button type="submit">💾 Salvar Alterações</button>
            </form>
            <a href="/qrcode/1" target="_blank" class="qr-link">🔍 Baixar QR Code 20x20mm (ID 1)</a>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_form, pet=pet, erro=erro)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
