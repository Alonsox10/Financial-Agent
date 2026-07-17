from __future__ import annotations

import datetime
from dataclasses import dataclass
from decimal import Decimal
from typing import Literal


@dataclass
class Usuario:
    id: int
    phone_number: str
    nombre: str | None
    created_at: datetime.datetime


@dataclass
class PerfilCliente:
    id: int
    user_id: int
    scoring_crediticio: int | None
    productos_contratados: list | dict
    segmento: str | None
    updated_at: datetime.datetime


@dataclass
class Cuenta:
    id: int
    user_id: int
    tipo_cuenta: str
    saldo_disponible: Decimal
    saldo_bloqueado: Decimal
    moneda: str
    created_at: datetime.datetime


@dataclass
class Movimiento:
    id: int
    cuenta_id: int
    fecha: datetime.datetime
    monto: Decimal
    descripcion: str | None
    tipo: Literal["debito", "credito"]


@dataclass
class Operacion:
    id: int
    user_id: int
    cuenta_origen_id: int
    monto: Decimal
    destino: str
    estado: Literal["pendiente", "confirmada", "cancelada", "ejecutada"]
    created_at: datetime.datetime
    confirmed_at: datetime.datetime | None


@dataclass
class BankDocument:
    id: int
    content: str
    embedding: list[float]
    category: str | None
    metadata: dict
    created_at: datetime.datetime
