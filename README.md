# 🐾 PlaquinhaPet 3D

Sistema web dinâmico de identificação pet via QR Code, desenvolvido para integração direta com modelagem e impressão 3D (matriz otimizada em 20x20mm).

---

## 📌 Sobre o Projeto

O **PlaquinhaPet** permite que tutores cadastrem e gerenciem os dados de seus pets através do escaneamento do QR Code presente na plaquinha física. O sistema conta com recursos de segurança, personalização de status e ferramentas exclusivas de geração de vetores para produção industrial/DIY.

### 🚀 Principais Funcionalidades

* **Página Pública do Pet:** Exibe informações de contato do tutor e botão direto para chamada no WhatsApp.
* **Status Dinâmico:** Alertas visuais para pets com status `🟢 Seguro`, `🚨 PERDIDO!`, `⚠️ ROUBADO!` ou status customizados.
* **Área do Tutor Protegida:** Acesso via senha padronizada (`1234` no primeiro acesso) com opção de alteração de senha.
* **Painel do Desenvolvedor (ADM):**
  * Geração e download em lote de arquivos vetoriais **.SVG** numerados sequencialmente em arquivo **ZIP** (prontos para importação no Fusion 360).
  * Gerenciamento de Senha Mestre de Administrador.

---

## 🛠️ Tecnologias Utilizadas

* **Linguagem:** Python 3.14
* **Framework Web:** Flask
* **Banco de Dados:** SQLite3
* **Geração de QR Code:** Python-qrcode & Pillow (PIL)
* **Hospedagem:** Render / Gunicorn

---

## 👨‍💻 Desenvolvedor

* **Autor:** Joseanderson Langner
* **Formação:** Engenharia de Controle e Automação
