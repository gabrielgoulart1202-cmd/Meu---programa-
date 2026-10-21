from datetime import datetime
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

# Dados mantidos em memória durante a execução
operadores = []
# 12 secadores: Secador 1 até Secador 12
secadores = {
    i: {
        'operador': '-',
        'inicio': '',
        'fim': '',
        'duracao': '-',
        'status': 'Livre',
        'alerta': False,
    }
    for i in range(1, 13)
}


@app.route('/', methods=['GET', 'POST'])
def home():
  if request.method == 'POST':
    # Cadastro de operador
    if 'cadastrar_operador' in request.form:
      nome = request.form.get('nome_operador', '').strip()
      if nome and nome not in operadores:
        operadores.append(nome)

    # Registro de Secagem
    elif 'registrar_secagem' in request.form:
      num_secador = int(request.form.get('secador'))
      operador = request.form.get('operador')
      inicio_str = request.form.get('inicio')
      fim_str = request.form.get('fim')

      if inicio_str and fim_str and operador:
        dt_inicio = datetime.strptime(inicio_str, '%Y-%m-%dT%H:%M')
        dt_fim = datetime.strptime(fim_str, '%Y-%m-%dT%H:%M')

        diferenca = dt_fim - dt_inicio
        horas = diferenca.total_seconds() / 3600.0

        if horas >= 0:
          duracao_formatada = f'{int(horas)}h {int((horas*60)%60)}m'
          alerta = horas > 3.0  # Alerta se passar de 3 horas de secagem

          secadores[num_secador] = {
              'operador': operador,
              'inicio': dt_inicio.strftime('%d/%m %H:%M'),
              'fim': dt_fim.strftime('%d/%m %H:%M'),
              'duracao': duracao_formatada,
              'status': 'Alerta (> 3h)' if alerta else 'Eficiente',
              'alerta': alerta,
          }

    # Limpar / Resetar secador
    elif 'limpar_secador' in request.form:
      num_secador = int(request.form.get('secador_id'))
      secadores[num_secador] = {
          'operador': '-',
          'inicio': '',
          'fim': '',
          'duracao': '-',
          'status': 'Livre',
          'alerta': False,
      }

    return redirect(url_for('home'))

  html_template = '''
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Controle de Secadores de Arroz</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; color: #333; }
            h1 { text-align: center; color: #2c3e50; margin-bottom: 25px; }
            .container { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .forms-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
            label { font-weight: bold; display: block; margin-top: 10px; font-size: 14px; }
            input, select, button { width: 100%; padding: 10px; margin-top: 5px; border-radius: 5px; border: 1px solid #ccc; box-sizing: border-box; }
            button { background-color: #27ae60; color: white; font-weight: bold; border: none; cursor: pointer; margin-top: 15px; }
            button:hover { background-color: #219150; }
            .btn-clear { background-color: #7f8c8d; margin-top: 5px; font-size: 12px; padding: 5px; }
            .btn-clear:hover { background-color: #636e72; }
            .secadores-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(220px, 1fr)); gap: 15px; margin-top: 10px; }
            .secador-card { border: 2px solid #bdc3c7; border-radius: 8px; padding: 15px; background: #fff; position: relative; }
            .secador-card.eficiente { border-color: #2ecc71; background-color: #e8f8f5; }
            .secador-card.alerta { border-color: #e74c3c; background-color: #fadbd8; animation: pulse 2s infinite; }
            .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; }
            .badge-livre { background-color: #95a5a6; }
            .badge-eficiente { background-color: #2ecc71; }
            .badge-alerta { background-color: #e74c3c; }
            @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(231, 76, 60, 0); } 100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); } }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>🌾 Painel de Controle de Secadores de Arroz</h1>

            <div class="forms-grid">
                <!-- Cadastro de Operador -->
                <div class="card">
                    <h3>👤 Cadastrar Operador</h3>
                    <form method="POST">
                        <input type="hidden" name="cadastrar_operador" value="1">
                        <label>Nome do Operador:</label>
                        <input type="text" name="nome_operador" placeholder="Ex: João Silva" required>
                        <button type="submit">Cadastrar</button>
                    </form>
                    <p style="font-size: 13px; color: #7f8c8d; margin-top: 10px;">
                        Operadores salvos: {{ operadores|join(', ') if operadores else 'Nenhum cadastrado' }}
                    </p>
                </div>

                <!-- Lançamento do Processo de Secagem -->
                <div class="card">
                    <h3>⏱️ Registrar Secagem</h3>
                    <form method="POST">
                        <input type="hidden" name="registrar_secagem" value="1">
                        
                        <label>Secador:</label>
                        <select name="secador" required>
                            {% for i in range(1, 13) %}
                                <option value="{{ i }}">Secador {{ i }}</option>
                            {% endfor %}
                        </select>

                        <label>Operador Responsável:</label>
                        <select name="operador" required>
                            {% if not operadores %}
                                <option value="">Cadastre um operador primeiro</option>
                            {% endif %}
                            {% for op in operadores %}
                                <option value="{{ op }}">{{ op }}</option>
                            {% endfor %}
                        </select>

                        <label>Data/Hora Início:</label>
                        <input type="datetime-local" name="inicio" required>

                        <label>Data/Hora Término:</label>
                        <input type="datetime-local" name="fim" required>

                        <button type="submit" {% if not operadores %}disabled style="background:#ccc"{% endif %}>Lançar Registros</button>
                    </form>
                </div>
            </div>

            <!-- Monitoramento dos 12 Secadores -->
            <div class="card">
                <h3>🏭 Status dos Secadores (1 a 12)</h3>
                <div class="secadores-grid">
                    {% for num, dados in secadores.items() %}
                        <div class="secador-card {% if dados.alerta %}alerta{% elif dados.status == 'Eficiente' %}eficiente{% endif %}">
                            <h4>Secador {{ num }}</h4>
                            <p><strong>Status:</strong> 
                                {% if dados.status == 'Livre' %}
                                    <span class="badge badge-livre">Livre</span>
                                {% elif dados.status == 'Eficiente' %}
                                    <span class="badge badge-eficiente">Eficiente (≤ 3h)</span>
                                {% else %}
                                    <span class="badge badge-alerta">⚠️ ALERTA (> 3h)</span>
                                {% endif %}
                            </p>
                            <p><strong>Operador:</strong> {{ dados.operador }}</p>
                            <p><strong>Início:</strong> {{ dados.inicio or '-' }}</p>
                            <p><strong>Fim:</strong> {{ dados.fim or '-' }}</p>
                            <p><strong>Duração:</strong> {{ dados.duracao }}</p>
                            
                            {% if dados.status != 'Livre' %}
                                <form method="POST">
                                    <input type="hidden" name="limpar_secador" value="1">
                                    <input type="hidden" name="secador_id" value="{{ num }}">
                                    <button type="submit" class="btn-clear">Liberar / Resetar</button>
                                </form>
                            {% endif %}
                        </div>
                    {% endfor %}
                </div>
            </div>
        </div>
    </body>
    </html>
    '''
  return render_template_string(
      html_template, operadores=operadores, secadores=secadores
  )


if __name__ == '__main__':
  app.run()
