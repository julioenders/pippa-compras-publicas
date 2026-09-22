"""Reconstrucao alinhada a Matriz DOU+PNCP

Adiciona campos de prioridade Altissima e Alta da matriz:
- Contratacao: tipo_instrumento, beneficio_mpe detalhado, SRP, situacao,
  criterio_julgamento, modo_disputa, links, orcamento_sigiloso, margem_preferencia,
  resultado (fornecedor vencedor), unidade compradora
- Item: NCM/NBS, beneficio_mpe por item, material_ou_servico, resultado por item
- PCAItem: campos expandidos (unidade_requisitante, valores, localizacao)
- EventoContratacao: novo modelo para ciclo de vida

Revision ID: a2b3c4d5e6f7
Revises: 181a023fc28f
Create Date: 2026-09-22 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = 'a2b3c4d5e6f7'
down_revision: Union[str, None] = '181a023fc28f'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Nova tabela: eventos_contratacao ---
    op.create_table('eventos_contratacao',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('contratacao_id', sa.Integer(), nullable=False),
        sa.Column('tipo', sa.String(), nullable=False),
        sa.Column('data_evento', sa.DateTime(), nullable=True),
        sa.Column('descricao', sa.Text(), nullable=True),
        sa.Column('campo_alterado', sa.String(), nullable=True),
        sa.Column('valor_anterior', sa.Text(), nullable=True),
        sa.Column('valor_novo', sa.Text(), nullable=True),
        sa.Column('fonte', sa.String(), nullable=True),
        sa.Column('detalhes', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('(CURRENT_TIMESTAMP)'), nullable=True),
        sa.ForeignKeyConstraint(['contratacao_id'], ['contratacoes.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('ix_eventos_contratacao_contratacao_id', 'eventos_contratacao', ['contratacao_id'])

    # --- Novos campos em contratacoes ---
    with op.batch_alter_table('contratacoes') as batch_op:
        batch_op.add_column(sa.Column('unidade_codigo', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('unidade_nome', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('numero_processo', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('numero_contratacao', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('informacao_complementar', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('tipo_instrumento', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('amparo_legal', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('orcamento_sigiloso', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('poder', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('municipio_nome', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('beneficio_mpe', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('cota_reservada', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('subcontratacao_mpe', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('srp', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('criterio_julgamento', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('modo_disputa', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('link_sistema_origem', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('link_edital', sa.Text(), nullable=True))
        batch_op.add_column(sa.Column('situacao', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('situacao_descricao', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('data_ultima_atualizacao', sa.Date(), nullable=True))
        batch_op.add_column(sa.Column('margem_preferencia', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('margem_preferencia_percentual', sa.Numeric(precision=5, scale=2), nullable=True))
        batch_op.add_column(sa.Column('exigencia_conteudo_nacional', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('fonte', sa.String(), nullable=True, server_default='pncp'))
        batch_op.add_column(sa.Column('fornecedor_vencedor_cnpj', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('fornecedor_vencedor_nome', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('fornecedor_vencedor_porte', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('valor_adjudicado', sa.Numeric(precision=15, scale=2), nullable=True))

    op.create_index('ix_contratacoes_situacao', 'contratacoes', ['situacao'])
    op.create_index('ix_contratacoes_srp', 'contratacoes', ['srp'])
    op.create_index('ix_contratacoes_tipo_instrumento', 'contratacoes', ['tipo_instrumento'])

    # --- Novos campos em itens ---
    with op.batch_alter_table('itens') as batch_op:
        batch_op.add_column(sa.Column('tipo_catalogo', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('material_ou_servico', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('ncm', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('nbs', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('beneficio_mpe', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('cota_reservada', sa.Boolean(), nullable=True, server_default='0'))
        batch_op.add_column(sa.Column('valor_unitario_adjudicado', sa.Numeric(precision=15, scale=2), nullable=True))
        batch_op.add_column(sa.Column('beneficio_mpe_aplicado', sa.Boolean(), nullable=True))

    # --- Novos campos em pca_itens ---
    with op.batch_alter_table('pca_itens') as batch_op:
        batch_op.add_column(sa.Column('orgao_nome', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('unidade_requisitante', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('sequencial_pca', sa.Integer(), nullable=True))
        batch_op.add_column(sa.Column('categoria', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('valor_unitario', sa.Numeric(precision=15, scale=2), nullable=True))
        batch_op.add_column(sa.Column('valor_total', sa.Numeric(precision=15, scale=2), nullable=True))
        batch_op.add_column(sa.Column('valor_exercicio', sa.Numeric(precision=15, scale=2), nullable=True))
        batch_op.add_column(sa.Column('uf', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('municipio_ibge', sa.String(), nullable=True))
        batch_op.add_column(sa.Column('cnae_mapeado', sa.String(), nullable=True))


def downgrade() -> None:
    op.drop_index('ix_contratacoes_tipo_instrumento', 'contratacoes')
    op.drop_index('ix_contratacoes_srp', 'contratacoes')
    op.drop_index('ix_contratacoes_situacao', 'contratacoes')
    op.drop_index('ix_eventos_contratacao_contratacao_id', 'eventos_contratacao')
    op.drop_table('eventos_contratacao')

    with op.batch_alter_table('contratacoes') as batch_op:
        for col in [
            'unidade_codigo', 'unidade_nome', 'numero_processo', 'numero_contratacao',
            'informacao_complementar', 'tipo_instrumento', 'amparo_legal', 'orcamento_sigiloso',
            'poder', 'municipio_nome', 'beneficio_mpe', 'cota_reservada', 'subcontratacao_mpe',
            'srp', 'criterio_julgamento', 'modo_disputa', 'link_sistema_origem', 'link_edital',
            'situacao', 'situacao_descricao', 'data_ultima_atualizacao',
            'margem_preferencia', 'margem_preferencia_percentual', 'exigencia_conteudo_nacional',
            'fonte', 'fornecedor_vencedor_cnpj', 'fornecedor_vencedor_nome',
            'fornecedor_vencedor_porte', 'valor_adjudicado',
        ]:
            batch_op.drop_column(col)

    with op.batch_alter_table('itens') as batch_op:
        for col in [
            'tipo_catalogo', 'material_ou_servico', 'ncm', 'nbs',
            'beneficio_mpe', 'cota_reservada', 'valor_unitario_adjudicado', 'beneficio_mpe_aplicado',
        ]:
            batch_op.drop_column(col)

    with op.batch_alter_table('pca_itens') as batch_op:
        for col in [
            'orgao_nome', 'unidade_requisitante', 'sequencial_pca', 'categoria',
            'valor_unitario', 'valor_total', 'valor_exercicio', 'uf', 'municipio_ibge', 'cnae_mapeado',
        ]:
            batch_op.drop_column(col)
