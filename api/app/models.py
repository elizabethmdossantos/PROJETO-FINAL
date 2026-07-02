"""Modelos do banco"""

from sqlalchemy import Column, Integer, String, Float, DateTime, ForeignKey, Date
from sqlalchemy.orm import relationship
from datetime import datetime
from api.app.database import Base

class Usuario(Base):
    __tablename__ = "usuarios"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False)
    senha_hash = Column(String(255), nullable=False)
    perfil = Column(String(20), nullable=False) # 'administrador' ou 'vendedor'

class Produto(Base):
    __tablename__ = "produtos"
    
    id = Column(Integer, primary_key=True, index=True)
    codigo = Column(String(50), unique=True, nullable=False)
    nome = Column(String(100), nullable=False)
    preco_custo = Column(Float, nullable=False)
    preco_venda = Column(Float, nullable=False)
    categoria = Column(String(50), nullable=False)
    quantidade = Column(Integer, default=0) # Estoque atual

    # Relacionamentos
    movimentacoes = relationship("Movimentacao", back_populates="produto")

class Venda(Base):
    __tablename__ = "vendas"
    
    id = Column(Integer, primary_key=True, index=True)
    data_venda = Column(DateTime, default=datetime.utcnow)
    total = Column(Float, default=0.0)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"))

    # Relacionamento N:N com Produtos através da tabela pivot ItemVenda
    itens = relationship("ItemVenda", back_populates="venda", cascade="all, delete-orphan")
    contas_receber = relationship("ContasReceber", back_populates="venda", cascade="all, delete-orphan")

class ItemVenda(Base):
    """Tabela Pivot do Relacionamento N:N (Vendas <-> Produtos)"""
    __tablename__ = "itens_venda"
    
    id = Column(Integer, primary_key=True, index=True)
    venda_id = Column(Integer, ForeignKey("vendas.id", ondelete="CASCADE"))
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade = Column(Integer, nullable=False)
    preco_unitario = Column(Float, nullable=False)

    venda = relationship("Venda", back_populates="itens")
    produto = relationship("Produto")

class Movimentacao(Base):
    """Histórico de Auditoria do Estoque"""
    __tablename__ = "movimentacoes"
    
    id = Column(Integer, primary_key=True, index=True)
    produto_id = Column(Integer, ForeignKey("produtos.id"))
    quantidade_entrada = Column(Integer, default=0)
    quantidade_saida = Column(Integer, default=0)
    tipo = Column(String(50)) # 'entrada_inicial', 'venda_pdv', etc.
    data = Column(DateTime, default=datetime.utcnow)

    produto = relationship("Produto", back_populates="movimentacoes")

class ContasReceber(Base):
    __tablename__ = "contas_receber"
    
    id = Column(Integer, primary_key=True, index=True)
    venda_id = Column(Integer, ForeignKey("vendas.id", ondelete="CASCADE"))
    valor = Column(Float, nullable=False)
    status = Column(String(20), default="pendente") # 'pendente' ou 'pago'
    data_vencimento = Column(Date, nullable=False)

    venda = relationship("Venda", back_populates="contas_receber")