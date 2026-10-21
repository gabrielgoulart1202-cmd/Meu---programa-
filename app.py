from flask import Flask, render_template_string

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <html>
        <body style="font-family: Arial; text-align: center; margin-top: 50px; background: #f0f2f5;">
            <div style="background: white; padding: 30px; display: inline-block; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.1);">
                <h1>Meu Programa no Vercel!</h1>
                <p>Rodando na nuvem sem precisar de nada instalado no PC.</p>
                <button onclick="alert('Clicado com sucesso!')" style="padding: 10px 20px; background: #0070f3; color: white; border: none; border-radius: 5px; cursor: pointer;">Clique Aqui</button>
            </div>
        </body>
    </html>
    '''

if __name__ == '__main__':
    app.run()
