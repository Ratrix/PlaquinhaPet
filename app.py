import sqlite3
import qrcode
import qrcode.image.svg
import os
from flask import Flask, render_template_string, request, redirect, url_for

app = Flask(__name__)
DB_NAME = "pets.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS pets (
            tag_id TEXT PRIMARY KEY,
            nome_pet TEXT,
            raca TEXT,
            nome_dono TEXT,
            telefone TEXT,
            senha TEXT DEFAULT '1234',
            status TEXT DEFAULT 'normal',
            observacoes TEXT
        )
    ''')
    conn.commit()
    conn.close()

def gerar_qr_code_svg(tag_id, domain="http://127.0.0.1:5000"):
    url = f"{domain}/pet/{tag_id}"
    
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=1,
    )
    qr.add_data(url)
    qr.make(fit=True)

    factory = qrcode.image.svg.SvgPathImage
    img = qr.make_image(image_factory=factory)
    
    if not os.path.exists('qrcodes_svg'):
        os.makedirs('qrcodes_svg')
        
    caminho_svg = f"qrcodes_svg/qr_{tag_id}.svg"
    img.save(caminho_svg)
    print(f"✅ QR Code SVG gerado: {caminho_svg}")

@app.route('/pet/<tag_id>')
def ver_pet(tag_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT nome_pet, raca, nome_dono, telefone, status, observacoes FROM pets WHERE tag_id = ?", (tag_id,))
    pet = cursor.fetchone()
    conn.close()

    if not pet:
        return "<h2 style='font-family:sans-serif; text-align:center; margin-top:50px;'>Plaquinha não cadastrada ou inválida.</h2>", 404

    tel_limpo = ''.join(filter(str.isdigit, pet[3])) if pet[3] else ""

    html_template = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Identificação do Pet</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; background-color: #f4f6f8; margin: 0; padding: 20px; text-align: center; }
            .card { background: white; max-width: 400px; margin: 20px auto; padding: 25px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
            .status-alerta { background-color: #e63946; color: white; padding: 12px; border-radius: 8px; font-weight: bold; margin-bottom: 20px; font-size: 15px; }
            h1 { color: #1d3557; margin-bottom: 5px; font-size: 28px; }
            .raca { color: #457b9d; font-size: 16px; margin-top: 0; margin-bottom: 20px; font-weight: 600; }
            .info-box { background: #f8f9fa; border-left: 4px solid #457b9d; text-align: left; padding: 12px 15px; border-radius: 4px; margin: 15px 0; font-size: 14px; }
            .info-box p { margin: 5px 0; color: #333; }
            .btn-whats { display: block; background-color: #25D366; color: white; text-decoration: none; padding: 16px; border-radius: 10px; font-weight: bold; margin-top: 25px; font-size: 18px; box-shadow: 0 4px 10px rgba(37, 211, 102, 0.3); }
            .btn-edit { display: inline-block; margin-top: 20px; color: #6c757d; text-decoration: underline; font-size: 13px; }
        </style>
    </head>
    <body>
        <div class="card">
            {% if pet[4] == 'perdido' %}
                <div class="status-alerta">🚨 ATENÇÃO: ESTE PET ESTÁ PERDIDO!</div>
            {% endif %}
            
            <h1>🐾 {{ pet[0] }}</h1>
            {% if pet[1] %}<p class="raca">{{ pet[1] }}</p>{% endif %}
            
            <div class="info-box">
                <p><strong>Tutor:</strong> {{ pet[2] }}</p>
                {% if pet[5] %}
                    <p style="margin-top:8px;"><strong>Observações:</strong> {{ pet[5] }}</p>
                {% endif %}
            </div>

            <a class="btn-whats" href="https://wa.me/55{{ tel_limpo }}?text=Olá!%20Encontrei%20o(a)%20{{ pet[0] }}" target="_blank">
                💬 Falar com Tutor no WhatsApp
            </a>

            <a class="btn-edit" href="/pet/{{ tag_id }}/editar">Área do Tutor (Editar Dados)</a>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, pet=pet, tag_id=tag_id, tel_limpo=tel_limpo)

@app.route('/pet/<tag_id>/editar', methods=['GET', 'POST'])
def editar_pet(tag_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    erro = None

    if request.method == 'POST':
        senha_digitada = request.form['senha']
        cursor.execute("SELECT senha FROM pets WHERE tag_id = ?", (tag_id,))
        resultado = cursor.fetchone()
        senha_correta = resultado[0] if resultado else '1234'

        if senha_digitada != senha_correta:
            erro = "❌ Senha incorreta! Apenas o tutor pode alterar os dados."
        else:
            nova_senha = request.form['nova_senha'] if request.form['nova_senha'] else senha_correta
            cursor.execute('''
                UPDATE pets 
                SET nome_pet = ?, raca = ?, nome_dono = ?, telefone = ?, status = ?, observacoes = ?, senha = ?
                WHERE tag_id = ?
            ''', (request.form['nome_pet'], request.form['raca'], request.form['nome_dono'], 
                  request.form['telefone'], request.form['status'], request.form['observacoes'], nova_senha, tag_id))
            conn.commit()
            conn.close()
            return redirect(url_for('ver_pet', tag_id=tag_id))

    cursor.execute("SELECT nome_pet, raca, nome_dono, telefone, status, observacoes FROM pets WHERE tag_id = ?", (tag_id,))
    pet = cursor.fetchone()
    conn.close()

    html_edit = '''
    <!DOCTYPE html>
    <html lang="pt-BR">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Editar Plaquinha</title>
        <style>
            body { font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif; padding: 20px; background: #f4f6f8; }
            form { max-width: 400px; margin: 20px auto; background: white; padding: 25px; border-radius: 16px; box-shadow: 0 4px 15px rgba(0,0,0,0.08); }
            h2 { color: #1d3557; margin-top: 0; text-align: center; }
            label { display: block; margin-top: 12px; font-weight: 600; font-size: 14px; color: #333; }
            input, select, textarea { width: 100%; padding: 10px; margin-top: 4px; box-sizing: border-box; border: 1px solid #ccc; border-radius: 8px; font-size: 15px; }
            textarea { height: 80px; resize: vertical; }
            .erro { color: #e63946; font-weight: bold; text-align: center; font-size: 14px; margin-bottom: 10px; }
            button { margin-top: 20px; width: 100%; padding: 12px; background: #1d3557; color: white; border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; }
        </style>
    </head>
    <body>
        <form method="POST">
            <h2>Área de Edição ({{ tag_id }})</h2>
            
            {% if erro %}
                <div class="erro">{{ erro }}</div>
            {% endif %}

            <label>Senha do Tutor (Padrão: 1234):</label>
            <input type="password" name="senha" required placeholder="Digite a senha para salvar">

            <hr style="margin-top:20px; border:0; border-top:1px solid #eee;">
            
            <label>Nome do Pet:</label>
            <input type="text" name="nome_pet" value="{{ pet[0] or '' }}" required>
            
            <label>Raça:</label>
            <input type="text" name="raca" value="{{ pet[1] or '' }}">
            
            <label>Nome do Tutor:</label>
            <input type="text" name="nome_dono" value="{{ pet[2] or '' }}" required>
            
            <label>Telefone / WhatsApp (com DDD):</label>
            <input type="text" name="telefone" value="{{ pet[3] or '' }}" required>
            
            <label>Status do Pet:</label>
            <select name="status">
                <option value="normal" {% if pet[4] == 'normal' %}selected{% endif %}>Normal</option>
                <option value="perdido" {% if pet[4] == 'perdido' %}selected{% endif %}>🚨 PET PERDIDO!</option>
            </select>
            
            <label>Observações:</label>
            <textarea name="observacoes">{{ pet[5] or '' }}</textarea>

            <label>Alterar Senha (Opcional):</label>
            <input type="password" name="nova_senha" placeholder="Digite uma nova senha se desejar">
            
            <button type="submit">Salvar Alterações</button>
        </form>
    </body>
    </html>
    '''
    return render_template_string(html_edit, pet=pet, tag_id=tag_id, erro=erro)

if __name__ == '__main__':
    init_db()
    TAG_TESTE = "PET001"
    
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR IGNORE INTO pets (tag_id, nome_pet, raca, nome_dono, telefone, observacoes) VALUES (?, ?, ?, ?, ?, ?)",
              (TAG_TESTE, 'Thor', 'Golden Retriever', 'Jose', '11999999999', 'Possui chip e precisa de medicação.'))
    conn.commit()
    conn.close()
    
    gerar_qr_code_svg(TAG_TESTE)
    app.run(debug=True, port=5000)