import os
import sqlite3
import io
import qrcode
from qrcode.constants import ERROR_CORRECT_L
from flask import Flask, render_template_string, request, redirect, send_file

app = Flask(__name__)
DB_NAME = 'pets.db'

# --- CONFIGURAÇÃO DO BANCO DE DADOS ---
def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT id FROM pets LIMIT 1")
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
            status TEXT DEFAULT 'OK'
        )
    ''')
    
    cursor.execute("SELECT COUNT(*) FROM pets WHERE id = '1'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO pets (id, nome, raca, tutor, telefone, observacoes, status)
            VALUES ('1', 'Zoeyy', 'SDS - Só Deus Sabe', 'Joseanderson Langner', '5511999999999', 'Possui chip e precisa de medicação.', 'PERDIDO')
        ''')
    conn.commit()
    conn.close()

init_db()

# --- GERADOR DE QR CODE AJUSTADO PARA 20x20mm ---
def gerar_qr_code_20mm(link):
    qr = qrcode.QRCode(
        version=1,                           # Matriz estrita 21x21 módulos
        error_correction=ERROR_CORRECT_L,    # Blocos grandes
        box_size=10,                         # Define a proporção de cada pixel
        border=0                             # Sem margem branca extra
    )
    qr.add_data(link)
    qr.make(fit=False)
    
    img = qr.make_image(fill_color="black", back_color="white")
    
    # Redimensiona para exatamente 236x236 pixels (~20x20mm em 300 DPI)
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
            <a href="/cadastrar" class="footer-link">Área do Tutor</a>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, pet=pet_data)

@app.route('/pet/<pet_id>')
def visualizar_pet_antigo(pet_id):
    return redirect(f'/p/{pet_id}')

@app.route('/qrcode/<pet_id>')
def qrcode_pet(pet_id):
    host = request.host_url.replace('https://', '').replace('http://', '').rstrip('/')
    link = f"{host}/p/{pet_id}"
    img_buffer = gerar_qr_code_20mm(link)
    return send_file(img_buffer, mimetype='image/png')

@app.route('/cadastrar')
def cadastrar():
    return '''
    <div style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h2>Painel PlaquinhaPet</h2>
        <p><a href="/p/1">Ver perfil (ID 1)</a></p>
        <p><a href="/qrcode/1" target="_blank">Ver QR Code 20x20mm (ID 1)</a></p>
    </div>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
