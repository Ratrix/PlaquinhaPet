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
    
    # Inserção de registro inicial para testes
    cursor.execute("SELECT COUNT(*) FROM pets WHERE id = 'PET001'")
    if cursor.fetchone()[0] == 0:
        cursor.execute('''
            INSERT INTO pets (id, nome, raca, tutor, telefone, observacoes, status)
            VALUES ('PET001', 'Zoeyy', 'SDS - Só Deus Sabe', 'Joseanderson Langner', '5511999999999', 'Possui chip e precisa de medicação.', 'PERDIDO')
        ''')
    conn.commit()
    conn.close()

init_db()

# --- GERADOR DE QR CODE MINIMALISTA (VERSÃO 1) ---
def gerar_qr_code_svg(link):
    qr = qrcode.QRCode(
        version=1,                           # Matriz mínima (21x21)
        error_correction=ERROR_CORRECT_L,    # Pouca redundância = blocos maiores e limpos
        box_size=10,
        border=1
    )
    qr.add_data(link)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    img.save(buffer, format='PNG')
    buffer.seek(0)
    return buffer

# --- ROTAS DA APLICAÇÃO ---

@app.route('/')
def home():
    # Redireciona a página inicial direto para o pet de teste
    return redirect('/p/PET001')

# Rota encurtada para leitura rápida e QR Code limpo
@app.route('/p/<pet_id>')
def visualizar_pet_curto(pet_id):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM pets WHERE id = ?", (pet_id,))
    pet = cursor.fetchone()
    conn.close()

    if not pet:
        return "Pet não encontrado", 404

    # Mapeamento do banco de dados
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
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f6f9; display: flex; justify-content: center; align-items: center; min-height: 100vh; margin: 0; }
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
            
            <a href="/cadastrar" class="footer-link">Área do Tutor (Editar / Cadastrar)</a>
        </div>
    </body>
    </html>
    '''
    return render_template_string(html_template, pet=pet_data)

# Mantém a compatibilidade com a rota antiga
@app.route('/pet/<pet_id>')
def visualizar_pet_antigo(pet_id):
    return redirect(f'/p/{pet_id}')

# Rota para gerar a imagem PNG do QR Code minimalista
@app.route('/qrcode/<pet_id>')
def qrcode_pet(pet_id):
    # Gera o link usando a rota curta /p/
    link = f"{request.host_url.rstrip('/')}/p/{pet_id}"
    img_buffer = gerar_qr_code_svg(link)
    return send_file(img_buffer, mimetype='image/png')

# Rota de cadastro/consulta simples
@app.route('/cadastrar')
def cadastrar():
    return '''
    <div style="font-family: sans-serif; text-align: center; padding: 50px;">
        <h2>Painel PlaquinhaPet</h2>
        <p>Sistema pronto e operando no Render!</p>
        <p><a href="/p/PET001">Ver perfil de exemplo (PET001)</a></p>
        <p><a href="/qrcode/PET001" target="_blank">Ver QR Code Simplificado (PET001)</a></p>
    </div>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
