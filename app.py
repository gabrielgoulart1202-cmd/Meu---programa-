from datetime import datetime, timedelta
from flask import Flask, redirect, render_template_string, request, url_for

app = Flask(__name__)

operadores = []
historico = []
proximo_id = 1

secadores = {
    i: {
        'operador': '-',
        'inicio': '',
        'fim': '',
        'duracao': '-',
        'status': 'Livre',
        'alerta': False,
    }
    for i in range(2, 13)
}


def recalcular_status_secador(num_secador):
  registros = [r for r in historico if r['secador'] == num_secador]
  if registros:
    ultimo = registros[0]
    secadores[num_secador] = {
        'operador': ultimo['operador'],
        'inicio': ultimo['inicio_fmt_card'],
        'fim': ultimo['fim_fmt_card'],
        'duracao': ultimo['duracao_str'],
        'status': 'Alerta (> 3h)' if ultimo['alerta'] else 'Eficiente',
        'alerta': ultimo['alerta'],
    }
  else:
    secadores[num_secador] = {
        'operador': '-',
        'inicio': '',
        'fim': '',
        'duracao': '-',
        'status': 'Livre',
        'alerta': False,
    }


def calcular_medias(secador_num=None):
  agora_brasil = datetime.utcnow() - timedelta(hours=3)
  hoje_str = agora_brasil.strftime('%Y-%m-%d')
  semana_atual = agora_brasil.isocalendar()[1]
  mes_atual = agora_brasil.month
  ano_atual = agora_brasil.year

  registros = historico
  if secador_num:
    registros = [r for r in historico if r['secador'] == secador_num]

  def media_horas(filtrados):
    if not filtrados:
      return '-'
    total = sum(r['horas'] for r in filtrados)
    avg = total / len(filtrados)
    return f'{int(avg)}h {int((avg*60)%60)}m'

  m_dia = media_horas(
      [r for r in registros if r['data_fim'].strftime('%Y-%m-%d') == hoje_str]
  )
  m_semana = media_horas([
      r
      for r in registros
      if r['data_fim'].isocalendar()[1] == semana_atual
      and r['data_fim'].year == ano_atual
  ])
  m_mes = media_horas([
      r
      for r in registros
      if r['data_fim'].month == mes_atual and r['data_fim'].year == ano_atual
  ])

  return {'dia': m_dia, 'semana': m_semana, 'mes': m_mes}


@app.route('/', methods=['GET', 'POST'])
def home():
  global proximo_id, historico

  if request.method == 'POST':
    if 'cadastrar_operador' in request.form:
      nome = request.form.get('nome_operador', '').strip()
      if nome and nome not in operadores:
        operadores.append(nome)

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
          alerta = horas > 3.0

          registro = {
              'id': proximo_id,
              'secador': num_secador,
              'operador': operador,
              'inicio_str': dt_inicio.strftime('%d/%m/%Y %H:%M'),
              'fim_str': dt_fim.strftime('%d/%m/%Y %H:%M'),
              'inicio_fmt_card': dt_inicio.strftime('%d/%m %H:%M'),
              'fim_fmt_card': dt_fim.strftime('%d/%m %H:%M'),
              'horas': horas,
              'duracao_str': duracao_formatada,
              'alerta': alerta,
              'data_fim': dt_fim,
          }
          proximo_id += 1
          historico.insert(0, registro)
          recalcular_status_secador(num_secador)

    elif 'apagar_registro' in request.form:
      reg_id = int(request.form.get('registro_id'))
      secador_afetado = next(
          (r['secador'] for r in historico if r['id'] == reg_id), None
      )
      historico = [r for r in historico if r['id'] != reg_id]
      if secador_afetado:
        recalcular_status_secador(secador_afetado)

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

    return redirect(
        url_for('home', filtro_secador=request.args.get('filtro_secador', ''))
    )

  filtro_secador = request.args.get('filtro_secador', '')
  if filtro_secador.isdigit():
    secador_filtro_num = int(filtro_secador)
    historico_exibicao = [
        r for r in historico if r['secador'] == secador_filtro_num
    ]
  else:
    historico_exibicao = historico

  agora_brasil = datetime.utcnow() - timedelta(hours=3)
  data_hoje_inicio = agora_brasil.strftime('%Y-%m-%dT%H:%M')
  data_hoje_fim = (agora_brasil + timedelta(hours=3)).strftime('%Y-%m-%dT%H:%M')

  medias_gerais = calcular_medias()
  medias_por_secador = {i: calcular_medias(i) for i in range(2, 13)}

  # Imagem da logo Rampinelli embutida diretamente em Base64
  logo_base64 = "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAARgAAABaCAYAAAB2bYxXAAAAAXNSR0IArs4c6QAAAARnQU1BAACxjwv8YQUAAAAJcEhZcwAADsMAAA7DAcdvqGQAAAVjSURBVHhe7Z1BchoxEEU33v/KcILs2SAnSK7A3iU3yAnSGSAnSG6AEyAnQHaAnAAn4I55VdXpX12/3epWW+qXqmIwq9X9erfVki3LMgIghAnECCECCUGAAPmBvI4S4f9O3k8A30C8S0qE124C5APy/M/J6/3H63p32y96T9A/Inyf3m32eP138loC8g3I52e0vX/m/m3/efp38noC8glI7Xfy030v+/Lz4kQC8k/iOQ6f4/TfTf8f5xKQXxC/bvb/z9z+42f0H+M/XkB+R54397k5+m+nv3//eR/3E5Dfl3L3e414fvx5m4M/vI/44X3I10m5/19H/Nvhf4znE5BPXf93o92x/T3oJv1O/qO85i4A8g3iO3l11933/6Dvyet3P/C3pED+iPxI/v+/v9cR/z544m8XAN9AvEtKxP+dvJ7An5O/U143L8y1/x2QT/xInid3eI2fn5d/m34A1yCvO3f++L6X4O84/A2pE+f5+0E+IbdxeO3dD/4x/u1s3X8e/3qXAHmFn4+f4/e/p013z4/f2RvlA/L1+NvdP/1tD8gLJO423cbfbvI8X/3lAn+5An85x3XkF8jL+3T9L7H602vXvwP53YhzS4A8f0665f8H5B2eR4D8k/0R+A9S4e803dM1S4s4t/a9f9L93/29uI4c5x03Ea+/An/53+0fIG8vAnx2015H9vf/9QPI1xN33S23Sbgd+DsfXvfX/d8C5Pchx99/C/l5cvefXj29D3kO9/4C+fs3u+/y261v8LdtE304O8m/CchfC9/J83S9u1vu8N/1eG83AfIEic3439eRvEwE5B3vI2B5911f+/498s/Ecfh5vD/+3mH92/vjfw/vN3eC3A73v+/o3c9//P3u/QXI84e3WfL4516Q5/pPj79e5v913vj/qSvfP1P/A/m/43+MByT//2qR10433V39T+S/7e/38Pf/fA/yR14nAfn/qSveR/za7/q/Xf+f3AJA/mO65x4A5P8LAnwB5BmA13sJkGcA/j1LgDwDcIsfAfgH4n6AAt/5AvIC37sI4LtfQC4g8I9+8JdL+JcL+JdP/C1+i0cI339b3+LX4B+2/C2A3+S3/10C/P4GfgL/0oXvYvgX7+3fDvx+/10Af1H/dQDkE/I1O5Jvd+D72NfL2+G3X9xIAD/vQ74eXicB+Zbc57s/IPl2B36O/S/70bvdA9/T5/YvFvj9BfyN6Z3f30j+5m2k+v13B394H/HD+5APyP/sPvx8iR8x/vXb37f8yS1+z4D8T7fB/x8E4G0I2OInIAt8pAn4C4H8P/4E8L/1/wfwN/7pEvg7At8f/O3/tQv8eQL/vEa3E4D/+T3mR84/2QeA/03uO3434p+P2397+f0+5PfI236/AHzfR/L96W75O/T9/X/7S14nAfL3qP/1B3wfebr3533/uY/3iP/2+A9vPflm/NspLqTf1Tf/S/D9nO/99/3X+E3A//2H9xFv+B0AAnwQ4A/eR4D/3C0fAAn/93m3AvkG4d8n/xIAt/L95O/4vwMInyNvhf+O39P//f3vH3y3A/x58rA5fT6d/sX1BOSv53yN4x+P368g3y+/0R38uOvuuv/3m+S8iA83XyNvhv/On428N7oA/vK8vJm3m5D3vRze/u0g7Xp/fA2A3Eee5Ovl73b7C8hj+I71+DvyvM3p/39/I/u7yI8I7e4v//I38hIvh/3f/+/f3yOvh//7f99I34M/3wS3O38G3/0e/e3P305+/p402+u4/QnyHfI63e9f/eS/y/53s2f704Bf/A=="

  html_template = """
    <!DOCTYPE html>
    <html lang="pt-br">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PPCP Rampinelli - Controle de Secadores</title>
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; background-color: #f4f7f6; margin: 0; padding: 20px; color: #333; }
            .header-container { text-align: center; margin-bottom: 25px; background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .header-title-box { display: flex; align-items: center; justify-content: center; gap: 15px; flex-wrap: wrap; }
            .logo-img { height: 55px; width: auto; object-fit: contain; }
            h1 { color: #2c3e50; margin: 0; font-size: 26px; }
            .subtitle { color: #b03a2e; font-size: 18px; font-weight: bold; margin-top: 8px; letter-spacing: 1px; }
            .container { max-width: 1200px; margin: 0 auto; display: flex; flex-direction: column; gap: 20px; }
            .card { background: white; padding: 20px; border-radius: 10px; box-shadow: 0 4px 6px rgba(0,0,0,0.05); }
            .forms-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(320px, 1fr)); gap: 20px; }
            label { font-weight: bold; display: block; margin-top: 10px; font-size: 14px; }
            input, select, button { width: 100%; padding: 10px; margin-top: 5px; border-radius: 5px; border: 1px solid #ccc; box-sizing: border-box; }
            button { background-color: #27ae60; color: white; font-weight: bold; border: none; cursor: pointer; margin-top: 15px; }
            button:hover { background-color: #219150; }
            .btn-danger { background-color: #e74c3c; color: white; border: none; padding: 6px 10px; border-radius: 4px; cursor: pointer; font-size: 12px; }
            .btn-danger:hover { background-color: #c0392b; }
            .btn-clear { background-color: #7f8c8d; margin-top: 5px; font-size: 12px; padding: 5px; }
            .btn-clear:hover { background-color: #636e72; }
            .secadores-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(230px, 1fr)); gap: 15px; margin-top: 10px; }
            .secador-card { 
                border: 2px solid #bdc3c7; 
                border-radius: 8px; 
                padding: 15px; 
                background-color: #fff; 
                position: relative; 
                overflow: hidden;
            }
            .secador-card.eficiente { border-color: #2ecc71; background-color: #e8f8f5; }
            .secador-card.alerta { border-color: #e74c3c; background-color: #fadbd8; animation: pulse 2s infinite; }
            .badge { display: inline-block; padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; color: white; }
            .badge-livre { background-color: #95a5a6; }
            .badge-eficiente { background-color: #2ecc71; }
            .badge-alerta { background-color: #e74c3c; }
            .stats-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 15px; text-align: center; }
            .stat-box { background: #ebf5fb; padding: 15px; border-radius: 8px; border-left: 5px solid #3498db; }
            .stat-box h4 { margin: 0; color: #2980b9; font-size: 14px; }
            .stat-box p { margin: 5px 0 0 0; font-size: 20px; font-weight: bold; color: #2c3e50; }
            table { width: 100%; border-collapse: collapse; margin-top: 15px; font-size: 14px; }
            th, td { border: 1px solid #ddd; padding: 10px; text-align: center; }
            th { background-color: #34495e; color: white; }
            tr:nth-child(even) { background-color: #f9f9f9; }
            .filter-bar { display: flex; align-items: center; gap: 10px; margin-bottom: 10px; }
            .filter-bar select { width: auto; margin-top: 0; }
            @keyframes pulse { 0% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0.4); } 70% { box-shadow: 0 0 0 10px rgba(231, 76, 60, 0); } 100% { box-shadow: 0 0 0 0 rgba(231, 76, 60, 0); } }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header-container">
                <div class="header-title-box">
                    <img src="{{ logo_base64 }}" alt="Rampinelli Alimentos" class="logo-img">
                    <h1>Painel de Controle de Secadores de Arroz</h1>
                </div>
                <div class="subtitle">PPCP Rampinelli Alimentos</div>
            </div>

            <div class="card">
                <h3>⚡ Média Geral em Tempo Real (Todos os Secadores)</h3>
                <div class="stats-grid">
                    <div class="stat-box">
                        <h4>Média do Dia</h4>
                        <p>{{ medias_gerais.dia }}</p>
                    </div>
                    <div class="stat-box">
                        <h4>Média da Semana</h4>
                        <p>{{ medias_gerais.semana }}</p>
                    </div>
                    <div class="stat-box">
                        <h4>Média do Mês</h4>
                        <p>{{ medias_gerais.mes }}</p>
                    </div>
                </div>
            </div>

            <div class="forms-grid">
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

                <div class="card">
                    <h3>⏱️ Registrar Secagem</h3>
                    <form method="POST">
                        <input type="hidden" name="registrar_secagem" value="1">
                        
                        <label>Secador (2 ao 12):</label>
                        <select name="secador" required>
                            {% for i in range(2, 13) %}
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
                        <input type="datetime-local" name="inicio" value="{{ data_hoje_inicio }}" required>

                        <label>Data/Hora Término:</label>
                        <input type="datetime-local" name="fim" value="{{ data_hoje_fim }}" required>

                        <button type="submit" {% if not operadores %}disabled style="background:#ccc"{% endif %}>Lançar Registros</button>
                    </form>
                </div>
            </div>

            <div class="card">
                <h3>🏭 Status e Médias Individuais (Secadores 2 a 12)</h3>
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
                            <p><strong>Duração Última:</strong> {{ dados.duracao }}</p>
                            
                            <hr style="border: 0; border-top: 1px solid #ddd; margin: 10px 0;">
                            <p style="font-size: 12px; margin: 2px 0;"><strong>Médias em Tempo Real:</strong></p>
                            <p style="font-size: 11px; margin: 2px 0;">• Dia: <strong>{{ medias_por_secador[num].dia }}</strong></p>
                            <p style="font-size: 11px; margin: 2px 0;">• Semana: {{ medias_por_secador[num].semana }}</p>
                            <p style="font-size: 11px; margin: 2px 0;">• Mês: {{ medias_por_secador[num].mes }}</p>

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

            <div class="card">
                <h3>📜 Histórico de Secagens</h3>
                
                <div class="filter-bar">
                    <label style="margin-top:0;">Filtrar por Secador:</label>
                    <form method="GET" style="display:inline-block;">
                        <select name="filtro_secador" onchange="this.form.submit()">
                            <option value="">Todos os Secadores</option>
                            {% for i in range(2, 13) %}
                                <option value="{{ i }}" {% if filtro_secador == i|string %}selected{% endif %}>Secador {{ i }}</option>
                            {% endfor %}
                        </select>
                    </form>
                </div>

                {% if historico_exibicao %}
                    <table>
                        <thead>
                            <tr>
                                <th>Secador</th>
                                <th>Operador</th>
                                <th>Início</th>
                                <th>Fim</th>
                                <th>Duração</th>
                                <th>Status</th>
                                <th>Ação</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for reg in historico_exibicao %}
                                <tr>
                                    <td><strong>Secador {{ reg.secador }}</strong></td>
                                    <td>{{ reg.operador }}</td>
                                    <td>{{ reg.inicio_str }}</td>
                                    <td>{{ reg.fim_str }}</td>
                                    <td>{{ reg.duracao_str }}</td>
                                    <td>
                                        {% if reg.alerta %}
                                            <span class="badge badge-alerta">⚠️ Alerta (> 3h)</span>
                                        {% else %}
                                            <span class="badge badge-eficiente">Eficiente</span>
                                        {% endif %}
                                    </td>
                                    <td>
                                        <form method="POST" style="display:inline;" onsubmit="return confirm('Tem certeza que deseja apagar este lançamento?');">
                                            <input type="hidden" name="apagar_registro" value="1">
                                            <input type="hidden" name="registro_id" value="{{ reg.id }}">
                                            <button type="submit" class="btn-danger">🗑️ Apagar</button>
                                        </form>
                                    </td>
                                </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                {% else %}
                    <p style="text-align: center; color: #7f8c8d; margin-top:20px;">Nenhum registro encontrado para este filtro.</p>
                {% endif %}
            </div>
        </div>
    </body>
    </html>
    """
  return render_template_string(
      html_template,
      operadores=operadores,
      secadores=secadores,
      historico=historico,
      historico_exibicao=historico_exibicao,
      filtro_secador=filtro_secador,
      data_hoje_inicio=data_hoje_inicio,
      data_hoje_fim=data_hoje_fim,
      medias_gerais=medias_gerais,
      medias_por_secador=medias_por_secador,
      logo_base64=logo_base64,
  )


if __name__ == '__main__':
  app.run()
