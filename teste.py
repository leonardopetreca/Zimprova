lista_contato ={
            'nome': 'nome',
            'email': 'email',
            'local': 'local',
            'melhor-email': 'melhorEmai',
            'telefone':'tel'
        }
itens=''
for x in lista_contato:
    itens = str(itens) + '<tr> <td>'+ x +'</td>' +'<td>'+ lista_contato[x] +'</td> </tr>'

content =f'resultados: {itens}'
print(content)