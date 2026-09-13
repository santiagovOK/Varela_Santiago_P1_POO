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

    def clasificar_en(self, categoria: Categoria, es_principal: bool = False) -> None:
        """Agrega una clasificación adicional al producto.

        Si es_principal es True, la clasificación que era principal deja de serlo.
        Clasificar dos veces en la misma categoría lanza ValueError.
        """
        for pc in self._clasificaciones:
            if pc.categoria == categoria:
                raise ValueError(f"El producto ya está clasificado en la categoría '{categoria.nombre}'.")

        if es_principal:
            for pc in self._clasificaciones:
                if pc.es_principal:
                    pc._marcar_principal(False)

        self._clasificaciones.append(ProductoCategoria(categoria, es_principal=es_principal))

    def categorias(self) -> tuple[ProductoCategoria, ...]:
        """Retorna las clasificaciones del producto como tupla inmutable defensiva."""
        return tuple(self._clasificaciones)

    def categoria_principal(self) -> Categoria:
        """Retorna la Categoria principal del producto (no el vínculo)."""
        for pc in self._clasificaciones:
            if pc.es_principal:
                return pc.categoria
        raise RuntimeError("Invariante violado: el producto no posee categoría principal.")

    @property
    def nombre(self) -> str:
        """Nombre del producto (solo lectura)."""
        return self._nombre

    @property
    def precio_base(self) -> float:
        """Precio base del producto (solo lectura)."""
        return self._precio_base

    @property
    def unidad_venta(self) -> UnidadMedida | None:
        """Unidad de medida para la venta (solo lectura, puede ser None)."""
        return self._unidad_venta

    @property
    def disponible(self) -> bool:
        """Estado derivado: True si está habilitado y posee stock mayor a cero."""
        return self._habilitado and self._stock_cantidad > 0

    @property
    def precio_publicado(self) -> str:
        """Precio formateado para exhibición con dos decimales y unidad si aplica."""
        if self._unidad_venta is not None:
            return f"$ {self._precio_base:.2f} / {self._unidad_venta.simbolo}"
        return f"$ {self._precio_base:.2f}"

    @abstractmethod
    def precio_final(self, cantidad: float) -> float:
        """Calcula el precio final para una cantidad dada.
        
        Debe ser implementado por cada subclase concreta.
        """
        ...

    def exportar(self) -> str:
        """Exporta el producto con formato para el punto de venta.
        
        Satisface el contrato estructural del Protocol Exportable sin acoplamiento.
        """
        return f"{self._nombre} | {self.precio_publicado} | {self.categoria_principal().nombre}"


class ProductoSimple(Producto):
    """Producto que se vende por unidad o pieza entera."""

    def precio_final(self, cantidad: float) -> float:
        """Calcula el precio final para una cantidad entera de piezas (>= 1)."""
        try:
            if type(cantidad) is bool or int(cantidad) != cantidad or cantidad < 1:
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError(
                f"La cantidad para ProductoSimple debe ser un valor entero >= 1, recibido: {cantidad}"
            )
        return self._precio_base * cantidad


class ProductoPorPeso(Producto):
    """Producto que se vende a granel por masa o medida continua."""

    def precio_final(self, cantidad: float) -> float:
        """Calcula el precio final para una cantidad continua > 0, redondeado a 2 decimales."""
        try:
            if type(cantidad) is bool or cantidad <= 0:
                raise ValueError
            return round(self._precio_base * float(cantidad), 2)
        except (ValueError, TypeError):
            raise ValueError(
                f"La cantidad para ProductoPorPeso debe ser un número > 0, recibido: {cantidad}"
            )


class Exportable(Protocol):
    def exportar(self) -> str:
        ...
