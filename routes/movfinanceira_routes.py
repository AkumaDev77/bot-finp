from flask import Blueprint, render_template, jsonify, request
from supabase import create_client
from database.supabase_client import supabase
from datetime import datetime, date
import locale
import yfinance as yf
import re
from difflib import get_close_matches


movfinanceira_route = Blueprint('movfinanceira', __name__)


# ============================================
# BIBLIOTECA DE MESES EM PORTUGUÊS
# ============================================
MESES_PT = {
    1: {'nome': 'Janeiro', 'abrev': 'Jan'},
    2: {'nome': 'Fevereiro', 'abrev': 'Fev'},
    3: {'nome': 'Março', 'abrev': 'Mar'},
    4: {'nome': 'Abril', 'abrev': 'Abr'},
    5: {'nome': 'Maio', 'abrev': 'Mai'},
    6: {'nome': 'Junho', 'abrev': 'Jun'},
    7: {'nome': 'Julho', 'abrev': 'Jul'},
    8: {'nome': 'Agosto', 'abrev': 'Ago'},
    9: {'nome': 'Setembro', 'abrev': 'Set'},
    10: {'nome': 'Outubro', 'abrev': 'Out'},
    11: {'nome': 'Novembro', 'abrev': 'Nov'},
    12: {'nome': 'Dezembro', 'abrev': 'Dez'}
}

def get_mes_pt(numero_mes):
    """Retorna o nome do mês em português"""
    return MESES_PT.get(numero_mes, {}).get('nome', '')

def get_mes_abrev_pt(numero_mes):
    """Retorna a abreviação do mês em português"""
    return MESES_PT.get(numero_mes, {}).get('abrev', '')


# ============================================
# DICIONÁRIO DE ABREVIAÇÕES (FÁCIL DE ATUALIZAR)
# ============================================
ABREVIACOES = {
    # Alimentação
    'padaria': 'Padaria',
    'pad': 'Padaria',
    'padi': 'Padaria',
    'supermercado': 'Supermercado',
    'mercado': 'Supermercado',
    'merc': 'Supermercado',
    'super': 'Supermercado',
    'restaurante': 'Restaurante',
    'rest': 'Restaurante',
    'lanches': 'Lanches por Delivery',
    'lanch': 'Lanches por Delivery',
    'lanche': 'Lanches por Delivery',
    'ifood': 'Lanches por Delivery',
    'cafe': 'Lanchonetes',
    'sorvete': 'Lanchonetes',
    'sorv': 'Lanchonetes',
    'sacolao': 'Sacolão',
    'sacol': 'Sacolão',
    'suplementos': 'Loja de Suplementos',
    'suple': 'Loja de Suplementos',
    'sup': 'Loja de Suplementos',
    
    # Transporte
    'uber': 'Uber',
    'ube': 'Uber',
    'ub': 'Uber',
    'posto': 'Posto de Gasolina',
    'gasolina': 'Posto de Gasolina',
    'gas': 'Posto de Gasolina',
    'mecanica': 'Mecânica',
    'mec': 'Mecânica',
    'mecan': 'Mecânica',
    'oficina': 'Mecânica',
    'ipva': 'IPVA',
    'seguro': 'Associação Avap',
    'consorcio': 'Consorcio',
    'consor': 'Consorcio',
    'financiamento': 'Consorcio',
    
    # Saúde e Bem-estar
    'drogaria': 'Drogaria',
    'farm': 'Drogaria',
    'farma': 'Drogaria',
    'academia': 'Mensalidade Academia',
    'acad': 'Mensalidade Academia',
    'barbearia': 'Barbearia',
    'barb': 'Barbearia',
    'cabelo': 'Barbearia',
    
    # Compras
    'inter shop': 'Inter Shop',
    'shop': 'Inter Shop',
    'shopping': 'Inter Shop',
    'roupas': 'Roupas/Calçados',
    'roupa': 'Roupas/Calçados',
    'calcado': 'Roupas/Calçados',
    'calcados': 'Roupas/Calçados',
    'pet shop': 'Pet Shop',
    'pet': 'Pet Shop',
    'vet': 'Pet Shop',
    'acessorios': 'Loja de Acessórios',
    'acess': 'Loja de Acessórios',
    'acessorio': 'Loja de Acessórios',
    'celular': 'Acessórios Celular',
    'cel': 'Acessórios Celular',
    
    # Lazer
    'bar': 'Bar/Balada',
    'balada': 'Bar/Balada',
    'show': 'Shows e Eventos',
    'evento': 'Shows e Eventos',
    'viagem': 'Viagem',
    'travel': 'Viagem',
    'jogos': 'Jogos de Video Game',
    'jogo': 'Jogos de Video Game',
    'game': 'Jogos de Video Game',
    'carnaval': 'Carnaval',
    'fest': 'Carnaval',
    'clube': 'Clube de lazer',
    
    # Educação
    'curso': 'Compra de Cursos',
    'cursos': 'Compra de Cursos',
    'livro': 'Compra de Cursos',
    'livros': 'Compra de Cursos',
    
    # Casa
    'internet': 'Internet',
    'net': 'Internet',
    'wifi': 'Internet',
    'aluguel': 'Aluguél',
    'alug': 'Aluguél',
    'luz': 'Custos de Casa',
    'agua': 'Custos de Casa',
    'condominio': 'Custos de Casa',
    'cond': 'Custos de Casa',
    
    # Rendas
    'salario': 'Remuneração Grupo Hinova',
    'lucro 031' 'Lucro 031 Assados'
    'lucro 031 assados' 'Lucro 031 Assados'
    'salário': 'Remuneração Grupo Hinova',
    'remuneracao': 'Remuneração Grupo Hinova',
    'remuneração': 'Remuneração Grupo Hinova',
    'renda extra': 'Renda Extra Web',
    'extra': 'Renda Extra Web',
    'milhas': 'Venda de milhas',
    'cashback inter': 'Cashback Inter',
    'cashback xp': 'Cashback Xp',
    'dividendos': 'Dividendos',
    'fundos imobiliarios': 'Fundos Imobiliários',
    'fundo': 'Fundos Imobiliários',
    'fii': 'Fundos Imobiliários',
    'acoes': 'Ações',
    'acao': 'Ações',
    'cdb': 'Resgate CDB',
    'fgts': 'FGTS',
    'ferias': 'Férias 1/12',
    'férias': 'Férias 1/12',
    'decimo': 'Décimo Terceiro 1/12',
    'décimo': 'Décimo Terceiro 1/12',
    '13': 'Décimo Terceiro 1/12',
    'pis': 'Pis/Pasep',
}

# ============================================
# CACHE DO CADASTRO
# ============================================
class CadastroCache:
    def __init__(self):
        self.cadastros = {}
        self.descricao_para_cod = {}
        self.carregar_cadastros()
    
    def carregar_cadastros(self):
        """Carrega todos os cadastros do Supabase e cria índices"""
        try:
            result = supabase.table('finp_cad').select('*').execute()
            
            # Limpa caches
            self.cadastros = {}
            self.descricao_para_cod = {}
            
            # Popula caches
            for item in result.data:
                cod = item['cod']
                self.cadastros[cod] = item
                self.descricao_para_cod[item['descricao'].lower()] = cod
            
            print(f"✅ Cadastros carregados: {len(self.cadastros)} itens")
            return True
        except Exception as e:
            print(f"❌ Erro ao carregar cadastros: {e}")
            return False
    
    def buscar_por_cod(self, cod):
        """Busca cadastro pelo código"""
        return self.cadastros.get(cod)
    
    def buscar_por_descricao_exata(self, descricao):
        """Busca cadastro pela descrição exata"""
        descricao_lower = descricao.lower().strip()
        cod = self.descricao_para_cod.get(descricao_lower)
        if cod:
            return self.cadastros.get(cod)
        return None
    
    def buscar_por_abreviacao(self, descricao):
        """Busca pela abreviação e retorna o código"""
        descricao_lower = descricao.lower().strip()
        
        # Tenta encontrar a abreviação no dicionário
        for abrev, desc_completa in ABREVIACOES.items():
            # Verifica se a abreviação está contida na descrição (case insensitive)
            if abrev in descricao_lower:
                # Busca a descrição completa no cadastro
                cadastro = self.buscar_por_descricao_exata(desc_completa)
                if cadastro:
                    return cadastro
        return None
    
    def buscar_por_palavra_chave(self, descricao):
        """Busca por palavra-chave na descrição (apenas palavras com 4+ letras)"""
        descricao_lower = descricao.lower().strip()
        palavras = descricao_lower.split()
        
        # Filtra palavras com 4+ letras para evitar falsos positivos
        palavras_importantes = [p for p in palavras if len(p) >= 4]
        
        for cod, cadastro in self.cadastros.items():
            desc_item = cadastro['descricao'].lower()
            for palavra in palavras_importantes:
                if palavra in desc_item:
                    return cadastro
        return None
    
    def buscar_por_similaridade(self, descricao, cutoff=0.8):
        """Busca por similaridade usando difflib (apenas com cutoff alto)"""
        descricao_lower = descricao.lower().strip()
        
        # Se a descrição for muito curta, não usa similaridade
        if len(descricao_lower) < 4:
            return None
        
        descricoes = list(self.descricao_para_cod.keys())
        
        matches = get_close_matches(descricao_lower, descricoes, n=1, cutoff=cutoff)
        
        if matches:
            cod = self.descricao_para_cod.get(matches[0])
            if cod:
                return self.cadastros.get(cod)
        return None
    
    def buscar_inteligente(self, descricao):
        """Busca inteligente combinando várias estratégias (mais rigoroso)"""
        # 1. Tenta busca exata (prioridade máxima)
        resultado = self.buscar_por_descricao_exata(descricao)
        if resultado:
            return resultado, 'exata'
        
        # 2. Tenta busca por abreviação (segunda prioridade)
        resultado = self.buscar_por_abreviacao(descricao)
        if resultado:
            return resultado, 'abreviacao'
        
        # 3. Tenta busca por palavra-chave (apenas palavras com 4+ letras)
        resultado = self.buscar_por_palavra_chave(descricao)
        if resultado:
            return resultado, 'palavra_chave'
        
        # 4. Tenta busca por similaridade (apenas com cutoff alto)
        resultado = self.buscar_por_similaridade(descricao, cutoff=0.85)
        if resultado:
            return resultado, 'similaridade'
        
        # 5. NÃO USA MAIS SIMILARIDADE COM CUTOFF BAIXO PARA EVITAR FALSOS POSITIVOS
        return None, None
    
    def sugerir_descricoes(self, descricao, limite=5):
        """Sugere descrições similares quando não encontra match"""
        descricao_lower = descricao.lower().strip()
        
        # Se for muito curto, não sugere nada
        if len(descricao_lower) < 3:
            return []
        
        descricoes = list(self.descricao_para_cod.keys())
        
        # Usa cutoff mais baixo apenas para sugestões
        matches = get_close_matches(descricao_lower, descricoes, n=limite, cutoff=0.4)
        return matches if matches else []

# Instância global do cache
cadastro_cache = CadastroCache()


# ============================================
# HELPERS DE PARSING
# ============================================
def parse_mensagem_inteligente(mensagem):
    """Interpreta mensagem natural e extrai dados usando o cadastro"""
    mensagem = mensagem.strip()
    
    # Padrões de reconhecimento (agora com captura do texto extra)
    padrao_simples = r'^(.+?)\s+([\d,]+\.?\d*)(?:\s+(.+))?$'
    padrao_completo = r'^(ganho|gasto|receita|despesa|investimento)\s+(.+?)\s+([\d,]+\.?\d*)(?:\s+(.+))?$'
    
    descricao = None
    valor = None
    tipo_usuario = None
    observacao = None
    
    # Tenta padrão completo primeiro
    match = re.match(padrao_completo, mensagem, re.IGNORECASE)
    if match:
        tipo_usuario = match.group(1).lower()
        descricao = match.group(2).strip()
        valor_str = match.group(3).replace(',', '.')
        valor = float(valor_str)
        observacao = match.group(4).strip() if match.group(4) else None
    else:
        # Tenta padrão simples
        match = re.match(padrao_simples, mensagem)
        if match:
            descricao = match.group(1).strip()
            valor_str = match.group(2).replace(',', '.')
            valor = float(valor_str)
            observacao = match.group(3).strip() if match.group(3) else None
    
    if not descricao or not valor:
        return None
    
    # Verifica se a descrição é muito curta (menos de 3 caracteres)
    if len(descricao.strip()) < 3:
        return {
            'valor': valor,
            'descricao_original': descricao,
            'observacao': observacao,
            'cadastro_encontrado': False,
            'sugestoes': [],
            'erro': 'descricao_muito_curta'
        }
    
    # Busca inteligente no cadastro (mais rigoroso)
    cadastro, metodo = cadastro_cache.buscar_inteligente(descricao)
    
    if cadastro:
        # USA TODOS OS DADOS DO CADASTRO
        return {
            'valor': valor,
            'tipo': tipo_usuario,
            'cod': cadastro['cod'],
            'descricao_cadastro': cadastro['descricao'],
            'tipo_cadastro': cadastro['tipo'],
            'categoria': cadastro['categoria'],
            'grupo': cadastro['grupo'],
            'natureza_cadastro': cadastro['natureza'],
            'cadastro_encontrado': True,
            'metodo_match': metodo,
            'descricao_original': descricao,
            'observacao': observacao
        }
    else:
        # NÃO ENCONTROU - retorna apenas com as sugestões
        sugestoes = cadastro_cache.sugerir_descricoes(descricao)
        return {
            'valor': valor,
            'tipo_usuario': tipo_usuario,
            'descricao_original': descricao,
            'observacao': observacao,
            'cadastro_encontrado': False,
            'sugestoes': sugestoes,
            'erro': 'descricao_nao_encontrada'
        }


# ============================================
# ROTAS DO BLUEPRINT
# ============================================

@movfinanceira_route.route('/')
def index():
    return render_template('pages/bot.html')

@movfinanceira_route.route('/api/mensagem', methods=['POST'])
def processar_mensagem():
    """Processa mensagem do chat e executa ação"""
    data = request.json
    mensagem = data.get('mensagem', '').strip()
    
    if not mensagem:
        return jsonify({'error': 'Mensagem vazia'}), 400
    
    # Comandos especiais
    if mensagem.lower() == '/listar':
        return listar_lancamentos()
    
    if mensagem.lower().startswith('/ultimos'):
        try:
            limite = int(mensagem.split()[1]) if len(mensagem.split()) > 1 else 5
            return listar_lancamentos(limite)
        except:
            return listar_lancamentos(5)
    
    if mensagem.lower() == '/saldo':
        return calcular_saldo()
    
    if mensagem.lower() == '/recarregar':
        cadastro_cache.carregar_cadastros()
        return jsonify({
            'type': 'mensagem',
            'conteudo': {
                'texto': '✅ Cadastro recarregado com sucesso!',
                'tipo': 'sucesso'
            }
        })
    
    if mensagem.lower() == '/cadastros':
        total = len(cadastro_cache.cadastros)
        return jsonify({
            'type': 'mensagem',
            'conteudo': {
                'texto': f'📚 <b>Total de cadastros:</b> {total}<br><br>Use /recarregar para atualizar o cache',
                'tipo': 'sistema'
            }
        })
    
    if mensagem.lower() == '/ajuda':
        return jsonify({
            'type': 'mensagem',
            'conteudo': {
                'texto': '📋 <b>Comandos disponíveis:</b><br><br>' +
                        '• <b>[descrição] [valor]</b> - Ex: "Padaria 5,50"<br>' +
                        '• <b>gasto [descrição] [valor]</b> - Ex: "gasto Uber 25,00"<br>' +
                        '• <b>ganho [descrição] [valor]</b> - Ex: "ganho Salário 1500"<br>' +
                        '• <b>/listar</b> - Lista todos lançamentos<br>' +
                        '• <b>/ultimos [n]</b> - Lista últimos N lançamentos<br>' +
                        '• <b>/saldo</b> - Mostra saldo atual<br>' +
                        '• <b>/deletar [id]</b> - Deleta um lançamento<br>' +
                        '• <b>/recarregar</b> - Recarrega o cadastro<br>' +
                        '• <b>/cadastros</b> - Mostra total de cadastros<br><br>' +
                        '💡 <b>Dica:</b> O bot reconhece automaticamente<br>' +
                        'abreviações como "Ube" para "Uber" ou "Merc" para "Supermercado"<br><br>' +
                        '⚠️ <b>Importante:</b> Só lança se encontrar a descrição no cadastro!',
                'tipo': 'sistema'
            }
        })
    
    # Comando para deletar
    if mensagem.lower().startswith('/deletar'):
        try:
            id_lancamento = int(mensagem.split()[1])
            return deletar_lancamento(id_lancamento)
        except:
            return jsonify({
                'type': 'mensagem',
                'conteudo': {
                    'texto': '❌ Use: /deletar [id] - Ex: /deletar 5',
                    'tipo': 'sistema'
                }
            })
    
    # Tenta parsear mensagem natural
    dados = parse_mensagem_inteligente(mensagem)
    
    if dados:
        # VERIFICAÇÃO: Se NÃO encontrou cadastro, NÃO LANÇA
        if not dados.get('cadastro_encontrado', False):
            sugestoes = dados.get('sugestoes', [])
            desc_original = dados.get('descricao_original', '')
            valor = dados.get('valor', 0)
            
            # Verifica se é erro de descrição muito curta
            if dados.get('erro') == 'descricao_muito_curta':
                mensagem_erro = (
                    f"❌ <b>Descrição muito curta!</b><br><br>"
                    f"📝 Você digitou: <b>{desc_original}</b><br>"
                    f"💰 Valor: R$ {valor:.2f}<br><br>"
                    f"💡 A descrição precisa ter pelo menos 3 caracteres.<br>"
                    f"🔄 Tente uma descrição mais completa."
                )
            elif sugestoes:
                texto_sugestoes = '<br>'.join([f'&nbsp;&nbsp;• {s}' for s in sugestoes[:5]])
                mensagem_erro = (
                    f"❌ <b>Descrição não encontrada no cadastro!</b><br><br>"
                    f"📝 Você digitou: <b>{desc_original}</b><br>"
                    f"💰 Valor: R$ {valor:.2f}<br><br>"
                    f"💡 <b>Sugestões disponíveis:</b><br>{texto_sugestoes}<br><br>"
                    f"🔄 Tente novamente com uma das sugestões acima ou use /ajuda"
                )
            else:
                mensagem_erro = (
                    f"❌ <b>Descrição não encontrada no cadastro!</b><br><br>"
                    f"📝 Você digitou: <b>{desc_original}</b><br>"
                    f"💰 Valor: R$ {valor:.2f}<br><br>"
                    f"💡 Nenhuma sugestão disponível.<br>"
                    f"🔄 Tente usar uma descrição mais comum ou use /ajuda"
                )
            
            return jsonify({
                'type': 'mensagem',
                'conteudo': {
                    'texto': mensagem_erro,
                    'tipo': 'erro'
                }
            })
        
        # SÓ CHEGA AQUI SE ENCONTROU O CADASTRO
        return criar_lancamento(dados)
    
    return jsonify({
        'type': 'mensagem',
        'conteudo': {
            'texto': '❓ Não entendi. Tente: "[descrição] [valor]" ou "/ajuda" para ver comandos',
            'tipo': 'sistema'
        }
    })

@movfinanceira_route.route('/api/lancamentos', methods=['GET'])
def listar_lancamentos(limite=None):
    """Lista lançamentos"""
    try:
        query = supabase.table('finp_movfin').select('*').order('id', desc=True)
        
        if limite:
            query = query.limit(limite)
        
        result = query.execute()
        lancamentos = result.data
        
        if lancamentos:
            mensagem = "📊 <b>Últimos Lançamentos:</b><br><br>"
            for idx, item in enumerate(lancamentos[:limite or 10], 1):
                valor = float(item['valor'])
                natureza = item['natureza']
                emoji = '📤' if natureza == 'D' else '📥'
                sinal = '-' if natureza == 'D' else '+'
                mensagem += f"{emoji} <b>{item['descricao']}</b> - {sinal}R$ {valor:.2f}<br>"
                mensagem += f"&nbsp;&nbsp;🆔 ID: {item['id']} | 📅 {item['data']} | {item['categoria']}<br><br>"
        else:
            mensagem = "📭 Nenhum lançamento encontrado"
        
        return jsonify({
            'type': 'mensagem',
            'conteudo': {
                'texto': mensagem,
                'tipo': 'lista',
                'dados': lancamentos[:limite or 10] if lancamentos else []
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@movfinanceira_route.route('/api/lancamentos', methods=['POST'])
def criar_lancamento(dados=None):
    """Cria um novo lançamento usando TODOS os dados do cadastro"""
    try:
        if not dados:
            dados = request.json
        
        # VERIFICAÇÃO: Se não tem cadastro, NÃO LANÇA
        if not dados.get('cadastro_encontrado', False):
            return jsonify({
                'type': 'mensagem',
                'conteudo': {
                    'texto': '❌ <b>Não é possível lançar sem cadastro!</b><br><br>' +
                            'Use uma descrição que exista no cadastro ou veja /ajuda',
                    'tipo': 'erro'
                }
            })
        
        hoje = date.today()
        mes_num = hoje.month
        
        # =============================================
        # CONVERTE OS DADOS DO CADASTRO PARA O FORMATO DO BANCO
        # =============================================
        
        # 1. Tipo: 'Entrada' ou 'Saída' -> 'ganho' ou 'gasto'
        tipo_cadastro = dados.get('tipo_cadastro', '')
        if tipo_cadastro == 'Entrada':
            tipo_banco = 'ganho'
        elif tipo_cadastro == 'Saída':
            tipo_banco = 'gasto'
        else:
            tipo_banco = 'gasto'
        
        # 2. Natureza: Pega a primeira letra
        natureza_cadastro = dados.get('natureza_cadastro', '')
        if natureza_cadastro and natureza_cadastro[0] in ['C', 'D']:
            natureza_banco = natureza_cadastro[0]
        else:
            natureza_banco = 'C' if tipo_cadastro == 'Entrada' else 'D'
        
        # 3. Descrição: Usa a descrição EXATA do cadastro
        descricao_banco = dados.get('descricao_cadastro', '')

        cod = dados.get('cod')

         # Buscar os dados na tabela "despesa" pelo código informado
        response = supabase.table("finp_cad").select("tipo, categoria, grupo, natureza").eq("cod", cod).execute()

        if not response.data:
            return jsonify({"error": "Código não encontrado na tabela Finp_cad"}), 400

        despesa = response.data[0]  # Pegamos o primeiro resultado


        
        # Prepara dados para inserção
        novo_lancamento = {
            'data': hoje.strftime('%Y-%m-%d'),
            'mes': get_mes_pt(mes_num),
            'ano': hoje.strftime('%Y'),
            'id_mes': mes_num,
            'mes_abrev': get_mes_abrev_pt(mes_num),
            'cod': cod,
            'descricao': descricao_banco,
            'tipo': despesa["tipo"],
            'categoria': despesa["categoria"],
            'grupo': despesa["grupo"],
            'natureza': despesa["natureza"],
            'valor': float(dados.get('valor', 0)),
            'observacao': dados.get('observacao', ''),
            'data_lanc': hoje.strftime('%Y-%m-%d %H:%M:%S')
        }
        
        print(f"📝 Dados do lançamento:")
        print(f"  - Descrição: {descricao_banco}")
        print(f"  - Tipo: {tipo_banco} (cadastro: {tipo_cadastro})")
        print(f"  - Natureza: {natureza_banco} (cadastro: {natureza_cadastro})")
        print(f"  - Categoria: {dados.get('categoria')}")
        print(f"  - Grupo: {dados.get('grupo')}")
        print(f"  - Código: {dados.get('cod')}")
        print(f"  - Match: {dados.get('metodo_match')}")
        
        result = supabase.table('finp_movfin').insert(novo_lancamento).execute()
        
        if result.data:
            # Define emoji baseado no tipo do cadastro
            emoji = '📤' if tipo_cadastro == 'Saída' else '📥'
            sinal = '-' if tipo_cadastro == 'Saída' else '+'
            
            # Mensagem de sucesso detalhada
            metodo = dados.get('metodo_match', '')
            desc_original = dados.get('descricao_original', '')
            desc_cadastro = dados.get('descricao_cadastro', '')
            
            if metodo == 'exata':
                msg_match = "✅ Match exato com o cadastro!"
            elif metodo == 'abreviacao':
                msg_match = f"🔍 <b>{desc_original}</b> → <b>{desc_cadastro}</b> (abreviação)"
            elif metodo == 'palavra_chave':
                msg_match = f"🔍 Palavra-chave reconhecida: <b>{desc_cadastro}</b>"
            elif metodo == 'similaridade':
                msg_match = f"🔍 Similar a: <b>{desc_cadastro}</b>"
            else:
                msg_match = f"✅ Encontrado no cadastro: <b>{desc_cadastro}</b>"

            observacao_texto = f"<br>📝 Obs: {dados.get('observacao', '')}" if dados.get('observacao') else ''
            
            return jsonify({
                'type': 'mensagem',
                'conteudo': {
                    'texto': f"✅ <b>Lançamento realizado com sucesso!</b><br><br>" +
                            f"{emoji} <b>{descricao_banco}</b><br>" +
                            f"{sinal}R$ {float(dados.get('valor', 0)):.2f}<br>" +
                            f"📅 {hoje.strftime('%d/%m/%Y')}<br>" +
                            f"🏷️ {dados.get('categoria')} &gt; {dados.get('grupo')}<br>" +
                            f"📋 Tipo: {tipo_cadastro} | Natureza: {dados.get('natureza_cadastro')}<br>" +
                            f"🆔 ID: {result.data[0]['id']}{observacao_texto}<br><br>" +
                            f"🔎 {msg_match}",
                    'tipo': 'sucesso',
                    'dados': result.data[0]
                }
            })
        else:
            return jsonify({'error': 'Erro ao criar lançamento'}), 500
            
    except Exception as e:
        print(f"❌ Erro ao criar lançamento: {e}")
        return jsonify({'error': str(e)}), 500

@movfinanceira_route.route('/api/saldo', methods=['GET'])
def calcular_saldo():
    """Calcula saldo atual"""
    try:
        result = supabase.table('finp_movfin').select('tipo, valor').execute()
        
        if not result.data:
            return jsonify({
                'type': 'mensagem',
                'conteudo': {
                    'texto': '💰 <b>Saldo Atual</b><br><br>Nenhum lançamento encontrado. Saldo: R$ 0,00',
                    'tipo': 'saldo',
                    'dados': {
                        'total_credito': 0,
                        'total_debito': 0,
                        'saldo': 0
                    }
                }
            })
        
        total_credito = sum(float(item['valor']) for item in result.data if item['tipo'] == 'Entrada')
        total_debito = sum(float(item['valor']) for item in result.data if item['tipo'] == 'Saída')
        saldo = total_credito - total_debito
        
        mensagem = f"💰 <b>Saldo Atual</b><br><br>📥 Total Receitas: R$ {total_credito:.2f}<br>📤 Total Despesas: R$ {total_debito:.2f}<br>──────────────────────────────<br>📊 <b>Saldo: R$ {saldo:.2f}</b>"
        
        return jsonify({
            'type': 'mensagem',
            'conteudo': {
                'texto': mensagem,
                'tipo': 'saldo',
                'dados': {
                    'total_credito': total_credito,
                    'total_debito': total_debito,
                    'saldo': saldo
                }
            }
        })
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@movfinanceira_route.route('/api/lancamentos/<int:id>', methods=['DELETE'])
def deletar_lancamento(id):
    """Deleta um lançamento"""
    try:
        # Primeiro, busca o lançamento para confirmar que existe
        busca = supabase.table('finp_movfin').select('*').eq('id', id).execute()
        
        if not busca.data:
            return jsonify({
                'type': 'mensagem',
                'conteudo': {
                    'texto': f'❌ Lançamento com ID {id} não encontrado',
                    'tipo': 'sistema'
                }
            })
        
        # Deleta o lançamento
        result = supabase.table('finp_movfin').delete().eq('id', id).execute()
        
        if result.data:
            return jsonify({
                'type': 'mensagem',
                'conteudo': {
                    'texto': f'🗑️ <b>Lançamento deletado com sucesso!</b><br><br>ID: {id}<br>Descrição: {busca.data[0]["descricao"]}<br>Valor: R$ {float(busca.data[0]["valor"]):.2f}',
                    'tipo': 'sucesso'
                }
            })
        else:
            return jsonify({'error': 'Erro ao deletar lançamento'}), 500
    except Exception as e:
        return jsonify({'error': str(e)}), 500