# Resolución Parcial POO - Food Store

Guía de desarrollo con enfoque de construcción desde componentes independientes hacia los más dependientes (**Bottom-Up**), respetando las restricciones de [consignas.md](/docs/consignas.md) y las buenas prácticas de diseño de [javaismos_guia.md](/docs/javaismos_guia.md).

---

## Paso 1: Tipos base y dependencias aisladas
* **Estado:** [Completo]
* **Archivo(s) a modificar:** `catalogo.py` (con `libreria_externa.py` como referencia sin modificar)
* **Clase(s) a crear:** `UnidadMedida`, `Categoria`, `Exportable` (Protocol)
* **Requerimientos:** R1 (Modelado y encapsulamiento), R4 (Contratos: Protocol)  
* **Historias de Usuario:** HU-P1-01, HU-P1-04

### 1.1 `UnidadMedida` como Value Object inmutable - [Completo]
* **Objetivo:** Definir la clase de datos inmutable para las unidades de medida (kg, g, L, u).
* **Diseño e idioma Python:** Implementar con `@dataclass(frozen=True)`. Atributos: `nombre: str`, `simbolo: str`, `tipo: str`. Intentar mutar un campo en runtime debe lanzar `FrozenInstanceError`.

### 1.2 `Categoria` de catálogo - [Completo]
* **Objetivo:** Representar las categorías donde se clasifican los productos.
* **Diseño e idioma Python:** Constructor que recibe `nombre: str` y opcionalmente `descripcion: str = ""`. Exponer ambos atributos mediante `@property` de solo lectura (sin setters). Uso de guión bajo simple `_nombre`, `_descripcion`.

### 1.3 Contrato `Exportable` (Protocol) - [Completo]
* **Objetivo:** Declarar el contrato de exportación estructural para el catálogo.
* **Diseño e idioma Python:** Heredar de `typing.Protocol`. Declarar método `exportar(self) -> str: ...`. Ninguna clase del dominio hereda de `Exportable` (conformidad estructural / Duck Typing). `libreria_externa.py` permanece intacta.

### Implementación del Paso 1
```python
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


class Exportable(Protocol):
    def exportar(self) -> str:
        ...
```

**Fundamentación de diseño:**
* `UnidadMedida`: Se utiliza `@dataclass(frozen=True)` porque representa un *Value Object* sin identidad mutable. Cualquier intento de reasignación lanza `FrozenInstanceError`, protegiendo el catálogo contra efectos colaterales.
* `Categoria`: Se usa encapsulamiento idiomático mediante guión bajo simple `_`. Las propiedades `nombre` y `descripcion` solo tienen `getter` (`@property`) y carecen de `setter`, garantizando solo lectura sin caer en el javaísmo de métodos `get_nombre()`.
* `Exportable`: Al ser un `Protocol`, el tipado es estructural. Ninguna clase hereda formalmente de él, permitiendo que `FichaPuntoDeVenta` (externa y no modificable) y nuestras clases propias cumplan el contrato por el simple hecho de implementar `exportar() -> str`.

---

## Paso 2: Vínculo de Composición
* **Estado:** [Completo]
* **Archivo(s) a modificar:** `catalogo.py`
* **Clase(s) a crear:** `ProductoCategoria`
* **Requerimientos:** R2 (Relaciones estructurales)  
* **Historias de Usuario:** HU-P1-02

### 2.1 `ProductoCategoria` - [Completo]
* **Objetivo:** Clase intermedia que materializa la relación de composición entre un producto y una categoría, con estado propio `_es_principal`.
* **Diseño e idioma Python:**
  - Encapsular `_categoria: Categoria` y `_es_principal: bool`.
  - Properties de solo lectura `categoria` y `es_principal` (sin setters públicos).
  - Método protegido o de dominio (ej. `_marcar_principal(valor: bool)`) invocado únicamente por `Producto`, o reemplazo inmutable. El código cliente jamás debe instanciar esta clase directamente.

### Implementación del Paso 2
```python
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
```

**Fundamentación de diseño:**
* **Composición y encapsulamiento:** El objeto `ProductoCategoria` no tiene razón de existir de forma independiente en el negocio; solo tiene sentido como parte constitutiva del ciclo de vida de un `Producto`.
* **Inmutabilidad hacia el cliente:** Las properties `categoria` y `es_principal` son de solo lectura (sin `@es_principal.setter`), impidiendo que código cliente modifique el estado de la clasificación directamente desde afuera.
* **Control de invariante:** El método `_marcar_principal` tiene visibilidad protegida (guión bajo inicial) para ser invocado exclusivamente por la clase dueña de la composición (`Producto`), permitiendo mantener el invariante de exactamente una clasificación principal sin exponer setters públicos.

---

## Paso 3: Clase Abstracta Base (Producto)
* **Estado:** [Completo]
* **Archivo(s) a modificar:** `catalogo.py`
* **Clase(s) a crear:** `Producto` (Clase Abstracta)
* **Requerimientos:** R1 (Modelado y encapsulamiento), R2 (Relaciones estructurales), R3 (Herencia), R4 (Contratos)  
* **Historias de Usuario:** HU-P1-01, HU-P1-02, HU-P1-03, HU-P1-04

### 3.1 Encapsulamiento y constructor defensivo - [Completo]
* **Objetivo:** Inicializar el estado interno protegido de todo producto y validar las reglas de dominio al construir.
* **Diseño e idioma Python:**
  - Heredar de `abc.ABC`.
  - Atributos internos con guión bajo simple: `_nombre: str`, `_precio_base: float`, `_stock_cantidad: float`, `_habilitado: bool`, `_unidad_venta: UnidadMedida | None`, `_clasificaciones: list[ProductoCategoria]`.
  - Evitar defaults mutables en la firma.
  - Validación de dominio: `nombre` no vacío, `precio_base >= 0`, `stock_cantidad >= 0`. Lanzar `ValueError` si alguna no se cumple.
  - Métodos mutadores con intención de dominio: `habilitar()` y `deshabilitar()`.

### 3.2 Composición e invariante de clasificación principal - [Completo]
* **Objetivo:** Administrar el ciclo de vida de los vínculos `ProductoCategoria` garantizando que siempre haya exactamente una categoría principal.
* **Diseño e idioma Python:**
  - El constructor recibe la categoría principal obligatoria y fabrica internamente el primer vínculo con `es_principal=True`.
  - Método `clasificar_en(categoria: Categoria, es_principal: bool = False)`: construye internamente el vínculo. Si `es_principal=True`, desmarca la anterior. Si se clasifica dos veces en la misma categoría, lanza `ValueError`.
  - Invariante de dominio: en todo momento hay exactamente una principal (ni cero ni dos).
  - Retorno protegido: `categorias()` devuelve `tuple[ProductoCategoria, ...]` (copia inmutable defensiva).
  - Método `categoria_principal() -> Categoria` que devuelve la categoría principal, no el vínculo.

### 3.3 Properties de estado y formato - [Completo]
* **Objetivo:** Exponer datos derivados y calculados sin exponer el estado interno.
* **Diseño e idioma Python:**
  - `@property def nombre(self) -> str` y `@property def precio_base(self) -> float`: solo lectura sin setters.
  - `@property def unidad_venta(self) -> UnidadMedida | None`: solo lectura sin setters.
  - `@property def disponible(self) -> bool`: estado derivado (`self._habilitado and self._stock_cantidad > 0`).
  - `@property def precio_publicado(self) -> str`: formateado como `f"$ {self._precio_base:.2f} / {self._unidad_venta.simbolo}"` si tiene unidad, o `f"$ {self._precio_base:.2f}"` si es `None`.

### 3.4 Contratos: Polimorfismo y Exportación - [Completo]
* **Objetivo:** Definir el contrato abstracto de cálculo y cumplir con la exportación.
* **Diseño e idioma Python:**
  - `@abstractmethod def precio_final(self, cantidad: float) -> float`: garantiza fallo temprano al instanciar (`TypeError`) si no se implementa en las subclases.
  - Método concreto `def exportar(self) -> str`: satisface estructuralmente el `Protocol` `Exportable`.

### Implementación del Paso 3
```python
from abc import ABC, abstractmethod


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
```

**Fundamentación de diseño:**
* **Encapsulamiento y convención Python:** Todos los atributos de instancia se definen protegidos mediante guión bajo simple `_` (`_nombre`, `_precio_base`, etc.). Se descarta el doble guión `__` conforme a la guía de javaísmos, evitando name-mangling innecesario que dificulta la herencia.
* **Constructor conciso y sin simulación de compilador:** Siguiendo las directrices de `javaismos_guia.md`, se evitan chequeos defensivos manuales con `isinstance(...)` en runtime (delegando la verificación de tipos a los type hints y a `mypy`). En runtime se validan exclusivamente las restricciones de dominio que exige el Requerimiento 1 (nombre no vacío, precio >= 0 y stock >= 0).
* **Composición garantizada:** Todo producto nace con su primera categoría principal obligatoria, fabricando internamente la primera instancia de `ProductoCategoria(categoria, es_principal=True)` sin que el código cliente deba instanciarla.
* **Invariante de clasificación principal:** En todo momento existe exactamente una categoría principal (ni cero ni dos). El cliente no muta vínculos directamente: solicita clasificar mediante `clasificar_en(categoria, es_principal=True)`, y `Producto` desmarca la anterior mediante el método protegido `_marcar_principal(False)`.
* **Retorno protegido en colecciones:** El método `categorias()` retorna `tuple(self._clasificaciones)`, garantizando que ningún cliente externo pueda usar `.append()` para saltarse las validaciones de composición del producto.
* **Mutación con semántica de dominio:** En lugar de exponer un setter indiscriminado para `_habilitado`, se ofrecen métodos explícitos con intención de dominio: `habilitar()` y `deshabilitar()`.
* **Properties idiomáticas vs Getters/Setters de Java:** De acuerdo al Capítulo 2 de la guía de javaísmos, se rechazan métodos artificiales como `get_nombre()`, `get_precio_base()` o `is_disponible()`. Se definen properties `@property` para lectura inmutable (`nombre`, `precio_base`, `unidad_venta`), estado derivado (`disponible`) y formato de presentación (`precio_publicado`). Al no definir `@setter`, cualquier intento de asignación externa produce un `AttributeError` inmediato sin requerir boilerplate defensivo.
* **Fallo temprano con ABC y @abstractmethod:** Siguiendo el Capítulo 7 de la guía de javaísmos, `Producto` hereda de `ABC` y decora `precio_final` con `@abstractmethod`. Esto garantiza que Python impida instanciar directamente `Producto` o cualquier subclase que omita su implementación, lanzando `TypeError` en el momento de la construcción en lugar de un `AttributeError` tardío.
* **Tipado estructural con Protocol (Duck Typing) sin acoplamiento:** Para la exportación al punto de venta (Requerimiento 4), `Producto` implementa el método `exportar() -> str` pero **NO** hereda explícitamente de `Exportable`. Satisface el contrato estructuralmente. Esto desacopla totalmente el catálogo de librerías externas cerradas como `FichaPuntoDeVenta` (que tampoco hereda de `Exportable`), permitiendo polimorfismo puro sin necesidad de adaptadores artificiales (Design Patterns clásicos de Java).

---

## Paso 4: Subclases de Venta
* **Estado:** [Completo]
* **Archivo(s) a modificar:** `catalogo.py`
* **Clase(s) a crear:** `ProductoSimple`, `ProductoPorPeso`, `ProductoCombo`
* **Requerimientos:** R2 (Agregación), R3 (Herencia y polimorfismo)  
* **Historias de Usuario:** HU-P1-02, HU-P1-03

### 4.1 `ProductoSimple` (Venta por pieza) - [Completo]
* **Objetivo:** Venta unitaria de artículos.
* **Diseño e idioma Python:**
  - Herencia directa de `__init__`: no redefine el constructor, heredando la inicialización y validaciones completas de `Producto`.
  - Implementar `precio_final(cantidad: float) -> float`: valida que `cantidad` sea de valor entero y `>= 1` (ej. `3` o `3.0` válido, `2.5` lanza `ValueError`).
  - Fórmula: `precio_base * cantidad`.

### 4.2 `ProductoPorPeso` (Venta a granel) - [Completo]
* **Objetivo:** Venta pesable donde la cantidad admite decimales.
* **Diseño e idioma Python:**
  - Herencia directa de `__init__`: no redefine el constructor, heredando la inicialización y validaciones completas de `Producto`.
  - Implementar `precio_final(cantidad: float) -> float`: valida `cantidad > 0` (admite decimales como `0.250`).
  - Fórmula: `round(precio_base * cantidad, 2)` (única subclase que redondea explícitamente a 2 decimales).

### 4.3 `ProductoCombo` (Agregación de productos) - [Completo]
* **Objetivo:** Agrupar 2..* productos preexistentes con descuento sobre la suma.
* **Diseño e idioma Python:**
  - Recibe componentes ya construidos (agregación: existen antes y sobreviven al combo).
  - Validación: menos de 2 componentes lanza `ValueError`. Descuento en `[0, 1)`.
  - Retorno protegido: `componentes() -> tuple[Producto, ...]`.
  - Decisión de dominio para `precio_base` derivado dinámicamente de sus componentes y `disponible` condicionado a la disponibilidad de todos los componentes.
  - Implementar `precio_final(cantidad: float) -> float`: valida cantidad entera `>= 1`. Fórmula: `(suma de componente.precio_final(1)) * (1 - descuento) * cantidad`. Soporta anidamiento recursivo de combos polimórficamente sin condicionales de tipo.

### Implementación del Paso 4
```python
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
    ) -> None:
        super().__init__(
            nombre=nombre,
            precio_base=0.0,
            categoria=categoria,
            unidad_venta=unidad_venta,
            stock_cantidad=0.0,
            habilitado=habilitado,
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
```

**Fundamentación de diseño:**
* **Herencia idiomática de constructores vs javaísmo de reenvío:** En Java los constructores no se heredan, lo que obliga al programador a declarar un constructor idéntico en cada subclase exclusivamente para hacer `super(nombre, precio, ...)`. En Python, por el contrario, los métodos (incluido `__init__`) se heredan naturalmente vía el MRO. Cuando una subclase no incorpora nuevos atributos de instancia ni altera el proceso de inicialización (como ocurre con `ProductoSimple` y `ProductoPorPeso`, que solo refinan el cálculo de `precio_final`), redeclarar `__init__` es una ceremonia vacía y un vicio de Java. Omitir el constructor en estas subclases respeta el principio DRY y coincide con el diagrama UML de las consignas, donde ninguna de las dos declara atributos ni constructor propio.
* **Cuándo sí se debe redefinir `__init__`:** Únicamente cuando la subclase incorpora atributos propios que la superclase desconoce, como ocurre con `ProductoCombo`, que agrega `_componentes` y `_descuento`. En este caso, la regla de `javaismos_guia.md` exige que se invoque explícitamente a `super().__init__(...)` para inicializar el estado común (`nombre`, `categoria`, etc.).
* **Relación de Agregación (`1 o-- 2..*`):** A diferencia de la composición de categorías (donde `Producto` fabrica y gestiona el ciclo de vida de `ProductoCategoria`), `ProductoCombo` implementa agregación: recibe componentes ya construidos que existen previamente y que siguen existiendo en el sistema aunque el combo sea eliminado. Para proteger la integridad interna, el constructor realiza una copia defensiva (`list(componentes)`) y el método `componentes()` retorna una tupla inmutable (`tuple(self._componentes)`), impidiendo que mutaciones externas alteren la colección del combo.
* **Decisiones de dominio para `precio_base` y `disponible`:** Las consignas solicitan decidir cómo tratar estos atributos en un combo:
  - `precio_base`: No es un valor estático fijado arbitrariamente, sino un estado derivado dinámico calculado como `(suma de componentes) * (1 - descuento)`. Al modificar `Producto.precio_publicado` para que acceda a la property `self.precio_base` en lugar del atributo privado `_precio_base`, el precio publicado del combo se mantiene siempre sincronizado y actualizado ante variaciones de sus componentes.
  - `disponible`: Un combo no posee inventario físico propio en un depósito; su disponibilidad depende directamente de que esté habilitado y de que **todos** sus componentes estén disponibles (`self._habilitado and all(c.disponible for c in self._componentes)`). Si cualquiera de los productos del combo se queda sin stock o es deshabilitado, el combo pasa automáticamente a no disponible sin requerir sincronizaciones manuales propensas a errores.
* **Validación de cantidad idiomática sin `isinstance`:** En lugar de simular un chequeo de tipos estático con `isinstance(cantidad, (int, float))` (javaísmo de compilador), se aplica una validación de dominio limpia bajo la filosofía **EAFP** (Easier to Ask for Forgiveness than Permission). En `ProductoSimple` y `ProductoCombo` se exige un valor numérico entero $\ge 1$, mientras que en `ProductoPorPeso` se admiten magnitudes continuas fraccionarias $> 0$ (como `0.250` kg). En todos los casos, tipos incompatibles o valores booleanos disparan `ValueError` sin requerir introspección pesada.
* **Redondeo explícito exclusivo:** De acuerdo a las consignas, `ProductoPorPeso` es la única subclase que redondea explícitamente a 2 decimales (`round(..., 2)`) para reflejar transacciones continuas por peso sin acumular residuos de coma flotante.
* **Polimorfismo puro y combos anidados:** Todas las subclases implementan el método abstracto `precio_final(cantidad)` satisfaciendo el contrato de `Producto`. En `ProductoCombo`, al invocar `c.precio_final(1)` sobre cada componente, el cálculo soporta combos anidados recursivamente de forma transparente y sin ningún condicional de tipo (`isinstance`), delegando el cálculo a cada componente polimórficamente.

---

## Paso 5: Rediseño de Producto Destacado
* **Estado:** [Completo]
* **Archivo(s) a modificar:** `catalogo.py`
* **Clase(s) a crear:** Ninguna (se elimina `ProductoDestacado` del modelo y se enriquece la clase base `Producto`)
* **Requerimientos:** R3 (Herencia justificada por dominio)  
* **Historias de Usuario:** HU-P1-05

### 5.1 Análisis crítico de la herencia ("es-un") - [Resuelto]
* **Objetivo:** Analizar la pertinencia de la herencia según el criterio «es-un» del dominio y justificar por qué se descarta la clase `ProductoDestacado` como subclase de `Producto`.
* **Resolución y Justificación de Dominio (HU-P1-05):**
  - **Decisión:** Se descarta la herencia modelada en el diagrama preliminar (`Producto <|-- ProductoDestacado : herencia a revisar`). `ProductoDestacado` no formará parte de la jerarquía de clases.
  - **Criterio «es-un»:** La herencia legítima en el dominio del catálogo modela la modalidad de venta y cálculo económico (`ProductoSimple` por unidad entera, `ProductoPorPeso` por masa continua y `ProductoCombo` por agregación promocional). Un producto *es un* producto simple, o *es un* producto por peso, o *es un* combo.
  - **Confusión entre identidad y rol temporal:** "Estar destacado" no es una especialización intrínseca de lo que el producto es, ni define cómo se calcula su precio. Es un **rol o estado promocional transitorio en runtime** (una posición asignada en la vidriera de la tienda). Como explica el Capítulo 6 y 7 de `javaismos_guia.md`, en Java la herencia suele usarse para darle un tipo común al compilador; en Python esa ceremonia es innecesaria y perjudicial.
  - **Ausencia de regla de precio:** Como `Producto` es abstracta con `@abstractmethod def precio_final(self, cantidad: float) -> float`, mantener `ProductoDestacado` como subclase obligaría a asignarle un algoritmo de cálculo propio, pero la tabla de requerimientos no define ningún precio para destacados porque un producto en vidriera cobra según su tipo de venta (por unidad, por peso o combo).
  - **Imposibilidad del cruce de jerarquías:** En herencia simple, un producto por peso o un combo no podría estar destacado sin recurrir a herencia múltiple compleja o a una explosión combinatoria de clases (`ProductoSimpleDestacado`, `ProductoPorPesoDestacado`, `ProductoComboDestacado`), lo cual constituye un grave antipatrón de diseño.
  - **Rigidez estática:** La herencia es fija al momento de instanciar. Si un producto entra y sale de la vidriera comercial entre semanas, con herencia se requeriría mutar la clase del objeto en memoria (`__class__`) o destruir y recrear la instancia.

### 5.2 Implementación del rediseño (Alternativa A: `_orden_vidriera` en `Producto`) - [Completo]
* **Objetivo:** Materializar la solución desacoplada mediante un rol/estado dinámico en la clase base `Producto`.
* **Resolución técnica y respuestas a la consigna (HU-P1-05):**
  - **¿Con qué se reemplaza la herencia?:** Se reemplaza por un atributo de estado/rol opcional (`_orden_vidriera: int | None`) y métodos con semántica de dominio explícita en la clase base `Producto`.
  - **¿Dónde vive `_orden_vidriera`?:** Vive directamente encapsulado en la clase base `Producto`. Nace por defecto en `None` (o configurable opcionalmente en el constructor).
  - **Properties de solo lectura:**
    - `@property def orden_vidriera(self) -> int | None`: expone el número de orden en vidriera o `None`.
    - `@property def es_destacado(self) -> bool`: estado derivado que retorna `self._orden_vidriera is not None`.
  - **Métodos de mutación con semántica de dominio:**
    - `def destacar(self, orden: int) -> None`: valida que `orden` sea un valor entero $\ge 1$ (disparando `ValueError` mediante EAFP ante valores inválidos o booleanos) y fija `self._orden_vidriera = int(orden)`.
    - `def quitar_destacado(self) -> None`: restablece `self._orden_vidriera = None`.
  - **¿Qué productos del catálogo pueden destacarse con tu diseño?:** **Todos los productos del catálogo**. Tanto `ProductoSimple`, como `ProductoPorPeso` y `ProductoCombo` heredan esta capacidad de `Producto`. Cualquier producto puede ingresar o salir de la vidriera en tiempo de ejecución sin cambiar de clase ni alterar su identidad.
  - **¿Qué regla de `precio_final(cantidad)` tiene?:** No introduce ninguna regla nueva ni artificial. Cada producto conserva su propia implementación polimórfica según su modalidad de venta (`ProductoSimple` por unidad, `ProductoPorPeso` por peso con redondeo a 2 decimales, `ProductoCombo` con descuento sobre la suma de componentes).

### Implementación del Paso 5
```python
# Modificaciones consolidadas en Producto (catalogo.py):

class Producto(ABC):
    """Clase base abstracta para todos los productos comercializados en el catálogo."""

    def __init__(
        self,
        nombre: str,
        precio_base: float,
        categoria: Categoria,
        unidad_venta: UnidadMedida | None = None,
        stock: float = 0.0,
        habilitado: bool = True,
        orden_vidriera: int | None = None,
    ) -> None:
        # Validaciones de invariantes previas...
        # Validación de orden_vidriera (rol opcional de destacado):
        if orden_vidriera is not None:
            try:
                if type(orden_vidriera) is bool or int(orden_vidriera) != orden_vidriera or orden_vidriera < 1:
                    raise ValueError
            except (ValueError, TypeError):
                raise ValueError(
                    f"El orden_vidriera debe ser un entero >= 1 o None, recibido: {orden_vidriera}"
                )
            self._orden_vidriera: int | None = int(orden_vidriera)
        else:
            self._orden_vidriera = None

        # Inicializaciones restantes...

    @property
    def orden_vidriera(self) -> int | None:
        """Número de orden en la vidriera comercial, o None si no está destacado."""
        return self._orden_vidriera

    @property
    def es_destacado(self) -> bool:
        """Estado derivado: True si el producto tiene asignado un orden en vidriera."""
        return self._orden_vidriera is not None

    def destacar(self, orden: int) -> None:
        """Asigna un número de orden en vidriera >= 1 marcando al producto como destacado."""
        try:
            if type(orden) is bool or int(orden) != orden or orden < 1:
                raise ValueError
        except (ValueError, TypeError):
            raise ValueError(
                f"El orden de vidriera debe ser un entero >= 1, recibido: {orden}"
            )
        self._orden_vidriera = int(orden)

    def quitar_destacado(self) -> None:
        """Remueve al producto de la vidriera comercial."""
        self._orden_vidriera = None
```

**Fundamentación de diseño del Paso 5:**
* **Eliminación de herencia espuria:** Descartar `ProductoDestacado` como subclase corrige el acoplamiento rígido y resuelve el problema de modelar un estado transitorio con herencia estructural.
* **Cohesión y extensibilidad:** Al situar el rol opcional en la clase base abstracta `Producto`, cualquier producto concreto (`ProductoSimple`, `ProductoPorPeso` o `ProductoCombo`) puede destacarse en la vidriera en tiempo de ejecución sin duplicar código ni alterar la lógica económica de cálculo de precios.
* **Validación idiomática EAFP:** La asignación del orden de vidriera valida estrictamente que sea un entero $\ge 1$, rechazando booleanos y valores no numéricos con `ValueError`, manteniendo consistencia con las validaciones del resto del dominio.

---

## Paso 6: Función Exportadora
* **Estado:** [Pendiente]
* **Archivo(s) a modificar:** `catalogo.py`
* **Clase(s) a crear:** Ninguna (se crea la función independiente `exportar_catalogo`)
* **Requerimientos:** R4 (Contratos: Protocol vs ABC)  
* **Historias de Usuario:** HU-P1-04

### 6.1 `exportar_catalogo` - [Pendiente]
* **Objetivo:** Exportar en una sola operación productos propios y fichas externas `FichaPuntoDeVenta`.
* **Diseño e idioma Python:**
  - Firma: `exportar_catalogo(items: list[Exportable]) -> list[str]`.
  - Duck typing y tipado estructural puro: recorre la lista llamando `item.exportar()` sin isinstance ni acoplamientos a clases concretas.

### Implementación del Paso 6
*(Espacio reservado para código y fundamentación)*

---

## Paso 7: Modelado UML y Demo Ejecutable
* **Estado:** [Pendiente]
* **Archivo(s) a modificar:** `uml/modelo_final.md` y `main.py`
* **Clase(s) a crear:** Ninguna (script ejecutable `main.py` y diagrama UML)
* **Requerimientos:** R5 (Diagrama UML final y demo ejecutable)  
* **Historias de Usuario:** Criterios generales y preguntas de defensa (sección 6.3)

### 7.1 Diagrama UML final (`uml/modelo_final.md`) - [Pendiente]
* **Objetivo:** Reflejar el diseño final exacto en sintaxis Mermaid, mostrando composición (`*--`), agregación (`o--`), asociación (`-->`), realización de Protocol (`..|>`) y la resolución de `ProductoDestacado`.

### 7.2 Script ejecutable (`main.py`) - [Pendiente]
* **Objetivo:** Demostrar en ejecución todas las reglas y decisiones requeridas para el video de defensa:
  - Creación de catálogo con al menos 4 productos (cubriendo Simple, PorPeso y Combo).
  - Clasificación en categorías y cambio de categoría principal (demostrando composición).
  - Componentes sobreviviendo al combo (demostrando agregación).
  - Falla temprana al intentar instanciar una clase abstracta sin `precio_final`.
  - Exportación conjunta de productos y `FichaPuntoDeVenta` mediante `exportar_catalogo`.
  - Salida formateada y clara por consola.

### Implementación del Paso 7
*(Espacio reservado para código del script y pruebas de verificación)*
