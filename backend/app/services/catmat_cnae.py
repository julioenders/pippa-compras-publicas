"""
Servico de mapeamento CATMAT/CATSER -> CNAE.

Resolve codigos de materiais (CATMAT) e servicos (CATSER) do catalogo
federal de compras para divisoes da Classificacao Nacional de Atividades
Economicas (CNAE), permitindo cruzar "o que o governo compra" com
"o que as MPEs produzem".
"""

import json
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_MAPPING: dict | None = None


def _load_mapping() -> dict:
    """Carrega o mapeamento CATMAT/CATSER -> CNAE do arquivo JSON (lazy, singleton)."""
    global _MAPPING
    if _MAPPING is None:
        path = Path(__file__).parent.parent / "mappings" / "catmat_cnae.json"
        try:
            with open(path, encoding="utf-8") as f:
                _MAPPING = json.load(f)
            n_catmat = len(_MAPPING.get("catmat_groups", {}))
            n_catser = len(_MAPPING.get("catser_groups", {}))
            logger.info(
                "Mapeamento CATMAT/CATSER carregado: %d grupos CATMAT, %d grupos CATSER",
                n_catmat,
                n_catser,
            )
        except FileNotFoundError:
            logger.error("Arquivo de mapeamento nao encontrado: %s", path)
            _MAPPING = {"catmat_groups": {}, "catser_groups": {}}
        except json.JSONDecodeError as exc:
            logger.error("Erro ao decodificar JSON de mapeamento: %s", exc)
            _MAPPING = {"catmat_groups": {}, "catser_groups": {}}
    return _MAPPING


def catmat_para_cnae(codigo_catmat: str) -> dict | None:
    """
    Mapeia um codigo CATMAT para a divisao CNAE correspondente.

    Codigos CATMAT possuem 6+ digitos. Os 2 primeiros digitos representam
    o grupo no Catalogo Federal de Suprimentos (Federal Supply Classification).
    Usamos o grupo para encontrar o mapeamento CNAE.

    Args:
        codigo_catmat: Codigo CATMAT (ex: "701530" -> grupo "70" = TI).

    Returns:
        Dicionario com cnae_divisao, cnae_descricao e confianca, ou None.
    """
    if not codigo_catmat or not codigo_catmat.strip():
        return None

    mapping = _load_mapping()
    group = codigo_catmat.strip()[:2]

    entry = mapping.get("catmat_groups", {}).get(group)
    if entry:
        result = entry.copy()
        result["confianca"] = "alta"
        result["tipo_catalogo"] = "CATMAT"
        result["grupo"] = group
        return result

    return None


def catser_para_cnae(codigo_catser: str) -> dict | None:
    """
    Mapeia um codigo CATSER para a divisao CNAE correspondente.

    Codigos CATSER seguem padrao semelhante ao CATMAT -- os 2 primeiros
    digitos indicam o grupo de servico.

    Args:
        codigo_catser: Codigo CATSER (ex: "023456" -> grupo "02" = TI).

    Returns:
        Dicionario com cnae_divisao, cnae_descricao e confianca, ou None.
    """
    if not codigo_catser or not codigo_catser.strip():
        return None

    mapping = _load_mapping()
    group = codigo_catser.strip()[:2]

    entry = mapping.get("catser_groups", {}).get(group)
    if entry:
        result = entry.copy()
        result["confianca"] = "alta"
        result["tipo_catalogo"] = "CATSER"
        result["grupo"] = group
        return result

    return None


def resolver_cnae(catmat_catser: str, descricao: str | None = None) -> dict | None:
    """
    Tenta resolver um codigo CATMAT ou CATSER para CNAE.

    Estrategia em cascata:
      1. Tenta mapeamento CATMAT (material)
      2. Tenta mapeamento CATSER (servico)
      3. Se ambos falharem e houver descricao, faz matching por palavras-chave
      4. Retorna None se nenhum metodo encontrar correspondencia

    Args:
        catmat_catser: Codigo CATMAT ou CATSER.
        descricao: Descricao textual do item (opcional, usada como fallback).

    Returns:
        Dicionario com cnae_divisao, cnae_descricao e confianca, ou None.
    """
    if not catmat_catser:
        if descricao:
            return _match_by_keywords(descricao)
        return None

    result = catmat_para_cnae(catmat_catser)
    if result:
        return result

    result = catser_para_cnae(catmat_catser)
    if result:
        return result

    if descricao:
        return _match_by_keywords(descricao)

    logger.debug(
        "Nenhum mapeamento encontrado para codigo '%s' (descricao: %s)",
        catmat_catser,
        descricao,
    )
    return None


def _match_by_keywords(descricao: str) -> dict | None:
    """
    Fallback: tenta mapear pela descricao textual do item usando palavras-chave.

    A confianca retornada e 'media' pois o matching e heuristico.

    Args:
        descricao: Descricao do item de compra.

    Returns:
        Dicionario com cnae_divisao, cnae_descricao e confianca, ou None.
    """
    if not descricao:
        return None

    descricao_lower = descricao.lower()

    keyword_map: dict[tuple[str, ...], tuple[str, str]] = {
        # Tecnologia da Informacao
        ("software", "licenca", "sistema", "informatica", "computador", "notebook",
         "servidor", "rede", "switch", "roteador", "firewall", "nuvem", "cloud"):
            ("J62", "Atividades dos servicos de tecnologia da informacao"),
        # Alimentos
        ("alimento", "genero alimenticio", "refeicao", "merenda", "carne", "leite",
         "arroz", "feijao", "hortifruti", "fruta", "legume", "verdura"):
            ("C10", "Fabricacao de produtos alimenticios"),
        # Farmaceuticos / Saude
        ("medicamento", "farmaceutico", "remedio", "vacina", "seringa", "agulha",
         "curativo", "esparadrapo", "gaze", "luva cirurgica"):
            ("C21", "Fabricacao de produtos farmaceuticos"),
        # Combustiveis
        ("combustivel", "gasolina", "diesel", "etanol", "gas", "lubrificante", "oleo diesel"):
            ("C19", "Fabricacao de coque, de produtos derivados do petroleo e de biocombustiveis"),
        # Construcao
        ("construcao", "obra", "reforma", "engenharia", "cimento", "tijolo",
         "concreto", "telha", "estrutura metalica"):
            ("F41", "Construcao de edificios"),
        # Limpeza (servico)
        ("limpeza", "higienizacao", "conservacao", "zeladoria", "asseio"):
            ("N81", "Servicos para edificios e atividades paisagisticas"),
        # Seguranca / Vigilancia
        ("vigilancia", "seguranca", "monitoramento", "portaria", "controle de acesso"):
            ("N80", "Atividades de vigilancia, seguranca e investigacao"),
        # Transporte
        ("transporte", "frete", "mudanca", "veiculo", "onibus", "ambulancia"):
            ("H49", "Transporte terrestre"),
        # Treinamento / Educacao
        ("treinamento", "capacitacao", "curso", "palestra", "workshop", "seminario"):
            ("P85", "Educacao"),
        # Mobiliario
        ("mobiliario", "movel", "cadeira", "mesa", "estante", "armario", "arquivo"):
            ("C31", "Fabricacao de moveis"),
        # Papelaria / Escritorio
        ("papel", "papelaria", "escritorio", "caneta", "lapis", "envelope", "toner",
         "cartucho", "impressora"):
            ("C17", "Fabricacao de celulose, papel e produtos de papel"),
        # Vestuario / Uniformes
        ("uniforme", "fardamento", "vestuario", "roupa", "calcado", "bota", "sapato",
         "camisa", "calca"):
            ("C14", "Confeccao de artigos do vestuario e acessorios"),
        # Produtos quimicos / Limpeza (material)
        ("detergente", "desinfetante", "sabao", "alcool", "produto quimico",
         "saneante", "agua sanitaria"):
            ("C20", "Fabricacao de produtos quimicos"),
        # Equipamentos medicos / laboratorio
        ("equipamento medico", "equipamento hospitalar", "laboratorio", "reagente",
         "microscopio", "centrifuga", "estufa"):
            ("C32", "Fabricacao de produtos diversos"),
        # Telecomunicacoes
        ("telefone", "telefonia", "telecomunicacao", "celular", "radio comunicacao"):
            ("J61", "Telecomunicacoes"),
        # Consultoria
        ("consultoria", "assessoria", "auditoria", "parecer tecnico"):
            ("M70", "Atividades de consultoria em gestao empresarial"),
        # Publicidade / Comunicacao
        ("publicidade", "propaganda", "comunicacao visual", "banner", "outdoor"):
            ("M73", "Publicidade e pesquisa de mercado"),
        # Locacao
        ("locacao", "aluguel", "arrendamento"):
            ("N77", "Alugueis nao-imobiliarios e gestao de ativos intangiveis nao-financeiros"),
        # Manutencao predial
        ("manutencao predial", "manutencao eletrica", "manutencao hidraulica",
         "pintura predial", "reparos"):
            ("F43", "Servicos especializados para construcao"),
    }

    for keywords, (divisao, desc) in keyword_map.items():
        if any(kw in descricao_lower for kw in keywords):
            return {
                "cnae_divisao": divisao,
                "cnae_descricao": desc,
                "confianca": "media",
                "tipo_catalogo": "keyword_match",
                "grupo": None,
            }

    logger.debug("Nenhuma palavra-chave encontrada na descricao: '%s'", descricao)
    return None


def listar_grupos_catmat() -> dict:
    """Retorna todos os grupos CATMAT mapeados."""
    return _load_mapping().get("catmat_groups", {})


def listar_grupos_catser() -> dict:
    """Retorna todos os grupos CATSER mapeados."""
    return _load_mapping().get("catser_groups", {})


def estatisticas() -> dict:
    """Retorna estatisticas sobre a cobertura do mapeamento."""
    mapping = _load_mapping()
    catmat = mapping.get("catmat_groups", {})
    catser = mapping.get("catser_groups", {})

    # Divisoes CNAE unicas cobertas
    divisoes_catmat = {v["cnae_divisao"] for v in catmat.values()}
    divisoes_catser = {v["cnae_divisao"] for v in catser.values()}
    todas_divisoes = divisoes_catmat | divisoes_catser

    return {
        "total_grupos_catmat": len(catmat),
        "total_grupos_catser": len(catser),
        "total_divisoes_cnae_cobertas": len(todas_divisoes),
        "divisoes_cnae": sorted(todas_divisoes),
        "versao": mapping.get("meta", {}).get("versao", "desconhecida"),
    }
