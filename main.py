from flask import Flask, render_template, request
import gspread as gp
from datetime import datetime

import dotenv

from threading import Thread
import os
from flask_mail import Mail, Message

dotenv.load_dotenv()

app = Flask(__name__)

PASSWORD = os.getenv("PASSWORD")

GSA_TYPE = os.getenv("TYPE")
GSA_PROJECT_ID = os.getenv("PROJECT_ID")
GSA_PRIVATE_KEY_ID = os.getenv("PRIVATE_KEY_ID")
GSA_PRIVATE_KEY = os.getenv("PRIVATE_KEY").replace('\\n', '\n')
GSA_CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
GSA_CLIENT_ID = os.getenv("CLIENT_ID")
GSA_AUTH_URI = os.getenv("AUTH_URI")
GSA_TOKEN_URI = os.getenv("TOKEN_URI")
GSA_AUTH_PROVIDER_X509_CERT_URL = os.getenv("AUTH_PROVIDER_X509_CERT_URL")
GSA_CLIENT_X509_CERT_URL = os.getenv("CLIENT_X509_CERT_URL")

gc = gp.service_account_from_dict({
    'type': GSA_TYPE,
    'project_id': GSA_PROJECT_ID,
    'private_key_id': GSA_PRIVATE_KEY_ID,
    'private_key': GSA_PRIVATE_KEY,
    'client_email': GSA_CLIENT_EMAIL,
    'client_id': GSA_CLIENT_ID,
    'auth_uri': GSA_AUTH_URI,
    'token_uri': GSA_TOKEN_URI,
    'auth_provider_x509_cert_url': GSA_AUTH_PROVIDER_X509_CERT_URL,
    'client_x509_cert_url': GSA_CLIENT_X509_CERT_URL
})

# configuração do email
app.config['MAIL_SERVER'] = 'smtp.gmail.com'
app.config['MAIL_PORT'] = 587
app.config['MAIL_USERNAME'] = 'sender@marketinglabs.com.br'
app.config['MAIL_PASSWORD'] = PASSWORD
app.config['MAIL_USE_TLS'] = True
app.config['MAIL_USE_SSL'] = False

# instantiating the mail service only after the 'app.config' to avoid error
mail = Mail(app)

# unidades dos dados
dadosUnidades = {
    'Quantidade de animais': 'animais',
    'Peso inicial': 'Kg',
    'Aditivo utilizado': '',
    'GMD': 'gramas/dia',
    'Preço Arroba Atual': 'R$/arroba',
    'Preço suplemento sem aditivo (R$/Kg)': 'R$/Kg',
    'consumo indicado ': 'gramas/cabeça/dia'
}

listasUnidades = {
    'pesoInicial': 'Kg',
    'pesoFinal': 'Kg',
    'gmd': 'gramas/dia',
    'ganhoPeso': 'Kg/cabeça',
    'producaoArroba': 'arrobas/cabeça',
    'producaoTotalArroba': 'arrobas/lote',
    'receitaProduzida': 'R$',
    'aumentoReceita': '%',
    'custoDiarioSuplemento': 'R$/cabeça/dia',
    'desembolsoAdicional': 'R$',
    'receitaExtra': 'R$',
    'lucroLiquido': 'R$',
    'ROI': '',
    'ganhoPeso%': '%',
    'ganhoArroba%': '%'

}


# defino função para executar em várias Threads.
def async_slow_function(funct, some_object):
    thr = Thread(target=funct, args=[some_object])
    thr.start()
    return thr


# Funções para distribuir os Leads tanto para gmail quanto google Sheets
def sendGmail(lista_dados):
    lista_contato = lista_dados[0]
    dados = lista_dados[1]
    lista_atual = lista_dados[2]
    lista_zimprova = lista_dados[3]

    name = "Elanco - Calculadora Zimprova"
    Subject = "Lead-Zimprova"

    # Construção do corpo de email
    itens = ""
    for x in lista_contato:
        itens = str(itens) + '<tr "> <td style="width:100px;">' + x + '</td>' + '<td>' + lista_contato[
            x] + '</td> </tr>'

    resultados = '<tr> <td width:200px;">' + '</td>' + '<td width:100px;> Atualmente </td>' + '<td width:150px;> Com Zimprova </td></tr> '
    for x in lista_zimprova:
        resultados = str(resultados) + '<tr> <td  style="width:250px;"><b>' + x + '</b> (' + listasUnidades[
            x] + ')</td>' + '<td style="width:150px;"> ' + str(
            lista_atual[x]) + '</td>' + '<td style="width:150px;">' + str(lista_zimprova[x]) + '</td> </tr>'

    fazenda = ''
    for x in dados:
        fazenda = str(fazenda) + '<tr> <td style="width:250px; ">' + x + '</td>' + '<td style="width:150px; ">' + str(
            dados[x]) + ' <span style="fontsize:8px;">' + dadosUnidades[x] + '</span></td> </tr>'

    content = f'''
    
    <h2 style="color:black"> Dados de Contato</h2>
    <table style="color:black">{itens}</table>
   
    <h2 style="color:black"> Dados da Fazenda</h2>
    <table style="color:black">{fazenda}</table>
    
    <h2 style="color:black"> Resultados</h2>
    <table style="color:black">{resultados}</table>
    
    '''

    with app.app_context():
        msg = Message(Subject, sender=(name, 'sender@marketinglabs.com.br'), recipients=['sender@marketinglabs.com.br'])
        msg.html = content
        mail.send(msg)


# Função para enviar o lead ao google sheet. obs: não mudar o nome da planilha. Se o fizer, mudar aqui também.
spreadsheet = gc.open("Leads Zimprova")


def RegistraGoogleSheets(lista_dados):
    lead = []
    worksheet = spreadsheet.get_worksheet(0)
    data = worksheet.get_all_values()

    cols = int(len(data[0])) + 1
    row = len(data) + 1

    id = row - 2
    horario = (str(datetime.now()).split(" "))[0]

    lead.append(id)
    lead.append(horario)

    # vou adicionar as infos
    for item in lista_dados:
        for x in item:
            if x != 'pesoInicial' and x != 'ganhoPeso%' and x != 'ganhoArroba%':
                lead.append(item[x])

    # registrando lead
    for i in range(0, len(lead)):
        worksheet.update_cell(row, i + 1, lead[i])


# app routes
@app.route("/")
def home():
    return render_template('index.html')


@app.route("/", methods=['POST'])
def home_calc():
    if request.method == 'POST':
        # Informações de contato
        nome = request.form['nome']
        sobrenome = request.form['sobrenome']
        cidade = request.form['cidade']
        estado = request.form['estado']
        melhorEmail = request.form['melhor-email']
        tel = request.form['telefone']
        #autorizacao = request.form['autorizacao']

        # Informações do cálculo
        quantidade_animais = request.form['quantidade_animais']
        peso_medio = request.form['peso_medio']
        # duracao_periodo = request.form['duracao_periodo']
        duracao_periodo = 180
        aditivo_utilizado = request.form['aditivo_utilizado']
        gmd = request.form['gmd']
        preco_arroba = request.form['preco_arroba']
        preco_suplemento = request.form['preco_suplemento']
        suplemento_atual = request.form['suplemento_atual']

        quantidade_animais = int(quantidade_animais) if quantidade_animais != "" else 1
        peso_medio = float(peso_medio) if peso_medio != "" else 1
        duracao_periodo = int(duracao_periodo) if duracao_periodo != "" else 1
        aditivo_utilizado = int(aditivo_utilizado) if aditivo_utilizado != "" else 1
        gmd = int(gmd) if gmd != "" else 1
        preco_arroba = float(preco_arroba) if preco_arroba != "" else 1
        preco_suplemento = float(preco_suplemento) if preco_suplemento != "" else 1
        suplemento_atual = float(suplemento_atual) if suplemento_atual != "" else 1

        Peso_inicial = peso_medio
        Preco = 430
        dolar = 5.14
        margem_premixeira = 40

        # Cenario atual
        Peso_final_atual = Peso_inicial + (duracao_periodo * gmd / 1000)
        gmd_atual = gmd
        producao_arroba_animal_atual = (Peso_final_atual - Peso_inicial) / 30
        producao_arroba_total_atual = producao_arroba_animal_atual * quantidade_animais
        receita_atual = producao_arroba_total_atual * preco_arroba

        # Zimprova
        gmd_zim = aditivo_utilizado + gmd
        Peso_final_zim = Peso_inicial + (duracao_periodo * gmd_zim / 1000)
        ganho_peso_zim = Peso_final_zim - Peso_final_atual
        producao_arroba_animal_zim = (Peso_final_zim - Peso_inicial) / 30
        producao_arroba_total_zim = producao_arroba_animal_zim * quantidade_animais
        receita_zim = producao_arroba_total_zim * preco_arroba
        aumento_receita = ((receita_zim / receita_atual) - 1) * 100

        # Calculos intermediários

        conferencia_garantia = 26 / (suplemento_atual / ((Peso_final_zim + Peso_inicial) / 2) * 100) * 1000
        inclusao_ton = 26 / (suplemento_atual / ((Peso_final_zim + Peso_inicial) / 2) * 100) / 0.12
        custo_adicional = inclusao_ton * (Preco * dolar * (1 + margem_premixeira / 100)) / 25 / 1000
        preco_suplemento_zim = (Preco * dolar) * (1 + margem_premixeira / 100)
        custo_estimado_zim = custo_adicional + preco_suplemento
        custo_total_suplementacao_atual = suplemento_atual / 1000 * duracao_periodo * quantidade_animais * preco_suplemento
        custo_total_suplementacao_zim = suplemento_atual / ((Peso_final_atual + Peso_inicial) / 2) * ((
                                                                                                                  Peso_final_zim + Peso_inicial) / 2) / 1000 * quantidade_animais * duracao_periodo * custo_estimado_zim
        custo_cabeca_zim = (
                                       custo_total_suplementacao_zim - custo_total_suplementacao_atual) / quantidade_animais / duracao_periodo

        # Cenario atual
        custoDiarioSuplemento_atual = custo_total_suplementacao_atual / duracao_periodo / quantidade_animais

        # zimprova
        custoDiarioSuplemento_zim = custo_total_suplementacao_zim / duracao_periodo / quantidade_animais
        desembolsoAdicional_zim = custo_total_suplementacao_zim - custo_total_suplementacao_atual
        receitaExtra = receita_zim - receita_atual
        lucroLiquido = receitaExtra - desembolsoAdicional_zim
        roi = lucroLiquido / desembolsoAdicional_zim

        aditivo = {
            '96': 'Sem Aditivo',
            '94': 'Salinomicina',
            '59': 'Lasalocida',
            '98': 'Virginamicina',
            '65': 'Flavomicina'
        }

        dados = {
            'Quantidade de animais': quantidade_animais,
            'Peso inicial': peso_medio,
            'Aditivo utilizado': aditivo[str(aditivo_utilizado)],
            'GMD': gmd,
            'Preço Arroba Atual': preco_arroba,
            'Preço suplemento sem aditivo (R$/Kg)': preco_suplemento,
            'consumo indicado ': suplemento_atual
        }

        lista_contato = {
            'Nome': nome,
            'Sobrenome': sobrenome,
            'Cidade': cidade,
            'Estado': estado,
            'Melhor email': melhorEmail,
            'Telefone': tel
        }

        lista_atual = {
            'pesoInicial': ("{:,}".format(int(round(Peso_inicial, 0)))).replace(",", "_").replace(".", ",").replace("_",
                                                                                                                    "."),
            'pesoFinal': ("{:,}".format(int(round(Peso_final_atual, 0)))).replace(",", "_").replace(".", ",").replace(
                "_", "."),
            'gmd': ("{:,}".format(gmd_atual)).replace(",", "_").replace(".", ",").replace("_", "."),
            'ganhoPeso': 0,
            'producaoArroba': ("{:,.1f}".format(round(producao_arroba_animal_atual, 1))).replace(",", "_").replace(".",
                                                                                                                   ",").replace(
                "_", "."),
            'producaoTotalArroba': ("{:,}".format(int(round(producao_arroba_total_atual, 0)))).replace(",",
                                                                                                       "_").replace(".",
                                                                                                                    ",").replace(
                "_", "."),
            'receitaProduzida': ("{:,.2f}".format(round(receita_atual, 2))).replace(",", "_").replace(".", ",").replace(
                "_", "."),
            'aumentoReceita': '-',
            'custoDiarioSuplemento': ("{:,.2f}".format(round(custoDiarioSuplemento_atual, 2))).replace(",",
                                                                                                       "_").replace(".",
                                                                                                                    ",").replace(
                "_", "."),
            'desembolsoAdicional': '-',
            'receitaExtra': '-',
            'lucroLiquido': '-',
            'ROI': '-',
            'ganhoPeso%': '-',
            'ganhoArroba%': '-'
        }

        lista_zimprova = {
            'pesoInicial': ("{:,}".format(int(Peso_inicial))).replace(",", "_").replace(".", ",").replace("_", "."),
            'pesoFinal': ("{:,}".format(float(round(Peso_final_zim, 1)))).replace(",", "_").replace(".", ",").replace("_",
                                                                                                                    "."),
            'gmd': ("{:,}".format(gmd_zim)).replace(",", "_").replace(".", ",").replace("_", "."),
            'ganhoPeso': ("{:,}".format(float(round(ganho_peso_zim,1)))).replace(",", "_").replace(".", ",").replace("_", "."),
            'producaoArroba': ("{:,}".format(round(producao_arroba_animal_zim, 2))).replace(",", "_").replace(".",
                                                                                                              ",").replace(
                "_", "."),
            'producaoTotalArroba': ("{:,}".format(float(round(producao_arroba_total_zim,1)))).replace(",","_").replace(".",",").replace("_","."),
            'receitaProduzida': ("{:,.2f}".format(round(receita_zim, 2))).replace(",", "_").replace(".", ",").replace(
                "_", "."),
            'aumentoReceita': ("{:,.1f}".format(round(aumento_receita, 1))).replace(",", "_").replace(".", ",").replace(
                "_", "."),
            'custoDiarioSuplemento': ("{:,.2f}".format(round(custoDiarioSuplemento_zim, 2))).replace(",", "_").replace(
                ".", ",").replace("_", "."),
            'desembolsoAdicional': ("{:,.2f}".format(round(desembolsoAdicional_zim, 2))).replace(",", "_").replace(".",
                                                                                                                   ",").replace(
                "_", "."),
            'receitaExtra': ("{:,.2f}".format(round(receitaExtra, 2))).replace(",", "_").replace(".", ",").replace("_",
                                                                                                                   "."),
            'lucroLiquido': ("{:,.2f}".format(round(lucroLiquido, 2))).replace(",", "_").replace(".", ",").replace("_",
                                                                                                                   "."),
            'ROI': ("{:,.2f}".format(round(roi, 2))).replace(",", "_").replace(".", ",").replace("_", "."),
            'ganhoPeso%': ("{:,}".format(round(100*ganho_peso_zim/( Peso_final_atual),1))).replace(",","_").replace(".",",").replace("_","."),
            'ganhoArroba%': ("{:,}".format(
                round((100 * (producao_arroba_total_zim - producao_arroba_total_atual) / producao_arroba_total_atual),
                      1))).replace(",", "_").replace(".", ",").replace("_", ".")
        }

        lista_atual_filtered = {
            'pesoFinal': lista_atual['pesoFinal'],
            'gmd': lista_atual['gmd'],
            'producaoArroba': lista_atual['producaoArroba'],
            'producaoTotalArroba': lista_atual['producaoTotalArroba'],
            'receitaProduzida': lista_atual['receitaProduzida'],
            'custoDiarioSuplemento': lista_atual['custoDiarioSuplemento']
        }

        async_slow_function(RegistraGoogleSheets, [lista_contato, dados, lista_atual_filtered, lista_zimprova])
        async_slow_function(sendGmail, [lista_contato, dados, lista_atual, lista_zimprova])

        return render_template('resultado.html', lista_atual_res=lista_atual, lista_zimprova_res=lista_zimprova,
                               lista_contato_res=lista_contato,
                               dados=dados)  # return render_template('obrigado.html', quantidade_animais_answer = quantidade_animais, peso_medio_answer =peso_medio, duracao_periodo_answer=duracao_periodo,aditivo_utilizado_answer=aditivo_utilizado, gmd_answer=gmd, preco_arroba_answer= preco_arroba, preco_suplemento_answer =preco_suplemento, suplemento_atual_answer=suplemento_atual)


if __name__ == '__main__':
    app.run(debug=True)
