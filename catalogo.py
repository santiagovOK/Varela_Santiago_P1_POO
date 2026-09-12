from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True)
class UnidadMedida:
    nombre: str
    simbolo: str
    tipo: str


class Categoria:
    def __init__(self, nombre: str, descripcion: str = "") -> None:
        self._nombre = nombre
        self._descripcion = descripcion

    @property
    def nombre(self) -> str:
        return self._nombre

    @property
    def descripcion(self) -> str:
        return self._descripcion


class ProductoCategoria:
    """Vínculo de composición entre un Producto y una Categoria."""

    def __init__(self, categoria: Categoria, es_principal: bool = False) -> None:
        self._categoria = categoria
        self._es_principal = es_principal

    @property
    def categoria(self) -> Categoria:
        return self._categoria

    @property
    def es_principal(self) -> bool:
        return self._es_principal

    def _marcar_principal(self, valor: bool) -> None:
        self._es_principal = valor

    def __repr__(self) -> str:
        return f"ProductoCategoria(categoria={self._categoria.nombre!r}, es_principal={self._es_principal})"


class Producto(ABC):
    """Clase abstracta base del catálogo."""

    def __init__(
        self,
        nombre: str,
        precio_base: float,
        categoria: Categoria,
        unidad_venta: UnidadMedida | None = None,
        stock_cantidad: float = 0.0,
        habilitado: bool = True,
    ) -> None:
        if not nombre or not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        if precio_base < 0:
            raise ValueError("El precio base no puede ser negativo.")
        if stock_cantidad < 0:
            raise ValueError("El stock no puede ser negativo.")

        self._nombre = nombre.strip()
        self._precio_base = float(precio_base)
        self._stock_cantidad = float(stock_cantidad)
        self._habilitado = habilitado
        self._unidad_venta = unidad_venta
        self._clasificaciones: list[ProductoCategoria] = [
            ProductoCategoria(categoria, es_principal=True)
        ]

    def habilitar(self) -> None:
        """Habilita el producto para su venta."""
        self._habilitado = True

    def deshabilitar(self) -> None:
        """Deshabilita el producto para su venta."""
        self._habilitado = False


class Exportable(Protocol):
    def exportar(self) -> str:
        ...
