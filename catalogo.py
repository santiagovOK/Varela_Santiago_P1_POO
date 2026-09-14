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
        orden_vidriera: int | None = None, # Parte de la Resolución obligatoria de ProductoDestacado
    ) -> None:
        if not nombre or not nombre.strip():
            raise ValueError("El nombre no puede estar vacío.")
        if precio_base < 0:
            raise ValueError("El precio base no puede ser negativo.")
        if stock_cantidad < 0:
            raise ValueError("El stock no puede ser negativo.")

        # Parte de la Resolución obligatoria de ProductoDestacado
        if orden_vidriera is not None:
            try:
                if type(orden_vidriera) is bool or int(orden_vidriera) != orden_vidriera or orden_vidriera < 1:
                    raise ValueError
            except (ValueError, TypeError):
                raise ValueError(
                    f"El orden de vidriera debe ser un valor entero >= 1, recibido: {orden_vidriera}"
                )

        self._nombre = nombre.strip()
        self._precio_base = float(precio_base)
        self._stock_cantidad = float(stock_cantidad)
        self._habilitado = habilitado
        self._unidad_venta = unidad_venta
        self._orden_vidriera: int | None = int(orden_vidriera) if orden_vidriera is not None else None # Parte de la Resolución obligatoria de ProductoDestacado
        self._clasificaciones: list[ProductoCategoria] = [
            ProductoCategoria(categoria, es_principal=True)
        ]

    # Parte de la Resolución obligatoria de ProductoDestacado
    def destacar(self, orden: int) -> None:
        """Asigna al producto un lugar en la vidriera promocional (entero >= 1)."""
        try:
            if type(orden) is bool or int(orden) != orden or orden < 1:
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError(
                f"El orden de vidriera debe ser un valor entero >= 1, recibido: {orden}"
            )
        self._orden_vidriera = int(orden)

    def quitar_destacado(self) -> None:
        """Remueve el producto de la vidriera promocional."""
        self._orden_vidriera = None

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
            return f"$ {self.precio_base:.2f} / {self._unidad_venta.simbolo}"
        return f"$ {self.precio_base:.2f}"

    # Parte de la Resolución obligatoria de ProductoDestacado
    
    @property
    def orden_vidriera(self) -> int | None:
        """Número de orden en vidriera si el producto está destacado, o None."""
        return self._orden_vidriera

    @property
    def es_destacado(self) -> bool:
        """Indica si el producto tiene asignado un lugar destacado en vidriera."""
        return self._orden_vidriera is not None

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


class ProductoCombo(Producto):
    """Agrupación de productos promocionales por agregación (R2 y R3)."""

    def __init__(
        self,
        nombre: str,
        componentes: list[Producto] | tuple[Producto, ...],
        descuento: float,
        categoria: Categoria,
        unidad_venta: UnidadMedida | None = None,
        habilitado: bool = True,
        orden_vidriera: int | None = None, # Parte de la Resolución obligatoria de ProductoDestacado
    ) -> None:
        super().__init__(
            nombre=nombre,
            precio_base=0.0,
            categoria=categoria,
            unidad_venta=unidad_venta,
            stock_cantidad=0.0,
            habilitado=habilitado,
            orden_vidriera=orden_vidriera, # Parte de la Resolución obligatoria de ProductoDestacado
        )

        try:
            componentes_lista = list(componentes)
        except TypeError:
            raise ValueError("Los componentes del combo deben proporcionarse en una colección iterable.")

        if len(componentes_lista) < 2:
            raise ValueError("Un combo debe tener al menos 2 componentes.")

        try:
            if type(descuento) is bool or not (0.0 <= float(descuento) < 1.0):
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError("El descuento del combo debe estar en el intervalo [0, 1).")

        self._componentes: list[Producto] = list(componentes_lista)
        self._descuento: float = float(descuento)

    def componentes(self) -> tuple[Producto, ...]:
        """Retorna los componentes del combo como tupla inmutable defensiva."""
        return tuple(self._componentes)

    @property
    def descuento(self) -> float:
        """Porcentaje de descuento aplicado sobre la suma de componentes (solo lectura)."""
        return self._descuento

    @property
    def precio_base(self) -> float:
        """Precio base derivado dinámicamente de sus componentes con descuento."""
        return sum(c.precio_final(1) for c in self._componentes) * (1.0 - self._descuento)

    @property
    def disponible(self) -> bool:
        """Un combo está disponible si está habilitado y todos sus componentes lo están."""
        return self._habilitado and all(c.disponible for c in self._componentes)

    def precio_final(self, cantidad: float) -> float:
        """Calcula el precio final aplicando la fórmula con descuento y admitiendo anidamiento."""
        try:
            if type(cantidad) is bool or int(cantidad) != cantidad or cantidad < 1:
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError(
                f"La cantidad para ProductoCombo debe ser un valor entero >= 1, recibido: {cantidad}"
            )
        return self.precio_base * cantidad


class Exportable(Protocol):
    def exportar(self) -> str:
        ...


def exportar_catalogo(items: list[Exportable]) -> list[str]:
    """Exporta en una sola operación productos del catálogo y fichas de punto de venta.

    Aplica Duck Typing y tipado estructural: recorre los elementos invocando
    item.exportar() de manera polimórfica.
    """
    return [item.exportar() for item in items]

