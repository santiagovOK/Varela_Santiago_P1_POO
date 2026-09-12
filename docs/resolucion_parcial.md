# Resolución Parcial POO - Food Store

Guía de desarrollo con enfoque de construcción desde componentes independientes hacia los más dependientes (**Bottom-Up**), respetando las restricciones de [consignas.md](/docs/consignas.md) y las buenas prácticas de diseño de [javaismos_guia.md](/docs/javaismos_guia.md).

---

## Paso 1: Tipos base y dependencias aisladas
* **Estado:** [Completo]
* **Archivo(s) a modificar:** `catalogo.py` (con `libreria_externa.py` como referencia sin modificar)
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
        if not isinstance(categoria, Categoria):
            raise ValueError("categoria debe ser una instancia de Categoria")
        self._categoria = categoria
        self._es_principal = bool(es_principal)

    @property
    def categoria(self) -> Categoria:
        return self._categoria

    @property
    def es_principal(self) -> bool:
        return self._es_principal

    def _marcar_principal(self, valor: bool) -> None:
        self._es_principal = bool(valor)

    def __repr__(self) -> str:
        return f"ProductoCategoria(categoria={self._categoria.nombre!r}, es_principal={self._es_principal})"
```

**Fundamentación de diseño:**
* **Composición y encapsulamiento:** El objeto `ProductoCategoria` no tiene razón de existir de forma independiente en el negocio; solo tiene sentido como parte constitutiva del ciclo de vida de un `Producto`.
* **Inmutabilidad hacia el cliente:** Las properties `categoria` y `es_principal` son de solo lectura (sin `@es_principal.setter`), impidiendo que código cliente modifique el estado de la clasificación directamente desde afuera.
* **Control de invariante:** El método `_marcar_principal` tiene visibilidad protegida (guión bajo inicial) para ser invocado exclusivamente por la clase dueña de la composición (`Producto`), permitiendo mantener el invariante de exactamente una clasificación principal sin exponer setters públicos.

---

## Paso 3: Clase Abstracta Base (Producto)
* **Estado:** [Pendiente]
* **Archivo(s) a modificar:** `catalogo.py`
* **Requerimientos:** R1 (Modelado y encapsulamiento), R2 (Relaciones estructurales), R3 (Herencia), R4 (Contratos)  
* **Historias de Usuario:** HU-P1-01, HU-P1-02, HU-P1-03, HU-P1-04

### 3.1 Encapsulamiento y constructor defensivo - [Pendiente]
* **Objetivo:** Inicializar el estado interno protegido de todo producto y validar las reglas de dominio al construir.
* **Diseño e idioma Python:**
  - Heredar de `abc.ABC`.
  - Atributos internos con guión bajo simple: `_nombre: str`, `_precio_base: float`, `_stock_cantidad: float`, `_habilitado: bool`, `_unidad_venta: UnidadMedida | None`, `_clasificaciones: list[ProductoCategoria]`.
  - Evitar defaults mutables en la firma.
  - Validación de dominio: `nombre` no vacío, `precio_base >= 0`, `stock_cantidad >= 0`. Lanzar `ValueError` si alguna no se cumple.
  - Métodos mutadores con intención de dominio: `habilitar()` y `deshabilitar()`.

### 3.2 Composición e invariante de clasificación principal - [Pendiente]
* **Objetivo:** Administrar el ciclo de vida de los vínculos `ProductoCategoria` garantizando que siempre haya exactamente una categoría principal.
* **Diseño e idioma Python:**
  - El constructor recibe la categoría principal obligatoria y fabrica internamente el primer vínculo con `es_principal=True`.
  - Método `clasificar_en(categoria: Categoria, es_principal: bool = False)`: construye internamente el vínculo. Si `es_principal=True`, desmarca la anterior. Si se clasifica dos veces en la misma categoría, lanza `ValueError`.
  - Invariante de dominio: en todo momento hay exactamente una principal (ni cero ni dos).
  - Retorno protegido: `categorias()` devuelve `tuple[ProductoCategoria, ...]` (copia inmutable defensiva).
  - Método `categoria_principal() -> Categoria` que devuelve la categoría principal, no el vínculo.

### 3.3 Properties de estado y formato - [Pendiente]
* **Objetivo:** Exponer datos derivados y calculados sin exponer el estado interno.
* **Diseño e idioma Python:**
  - `@property def nombre(self) -> str` y `@property def precio_base(self) -> float`: solo lectura.
  - `@property def unidad_venta(self) -> UnidadMedida | None`: solo lectura.
  - `@property def disponible(self) -> bool`: estado derivado (`self._habilitado and self._stock_cantidad > 0`).
  - `@property def precio_publicado(self) -> str`: formateado como `f"$ {self._precio_base:.2f} / {self._unidad_venta.simbolo}"` si tiene unidad, o `f"$ {self._precio_base:.2f}"` si es `None`.

### 3.4 Contratos: Polimorfismo y Exportación - [Pendiente]
* **Objetivo:** Definir el contrato abstracto de cálculo y cumplir con la exportación.
* **Diseño e idioma Python:**
  - `@abstractmethod def precio_final(self, cantidad: float) -> float`: garantiza fallo temprano al instanciar (`TypeError`) si no se implementa en las subclases.
  - Método concreto `def exportar(self) -> str`: satisface estructuralmente el `Protocol` `Exportable`.

### Implementación del Paso 3
*(Espacio reservado para código y fundamentación)*

---

## Paso 4: Subclases de Venta
* **Estado:** [Pendiente]
* **Archivo(s) a modificar:** `catalogo.py`
* **Requerimientos:** R2 (Agregación), R3 (Herencia y polimorfismo)  
* **Historias de Usuario:** HU-P1-02, HU-P1-03

### 4.1 `ProductoSimple` (Venta por pieza) - [Pendiente]
* **Objetivo:** Venta unitaria de artículos.
* **Diseño e idioma Python:**
  - Invocar `super().__init__(...)`.
  - Implementar `precio_final(cantidad: float) -> float`: valida que `cantidad` sea de valor entero y `>= 1` (ej. `3` o `3.0` válido, `2.5` lanza `ValueError`).
  - Fórmula: `precio_base * cantidad`.

### 4.2 `ProductoPorPeso` (Venta a granel) - [Pendiente]
* **Objetivo:** Venta pesable donde la cantidad admite decimales.
* **Diseño e idioma Python:**
  - Invocar `super().__init__(...)`.
  - Implementar `precio_final(cantidad: float) -> float`: valida `cantidad > 0` (admite decimales como `0.250`).
  - Fórmula: `round(precio_base * cantidad, 2)` (única subclase que redondea explícitamente a 2 decimales).

### 4.3 `ProductoCombo` (Agregación de productos) - [Pendiente]
* **Objetivo:** Agrupar 2..* productos preexistentes con descuento sobre la suma.
* **Diseño e idioma Python:**
  - Recibe componentes ya construidos (agregación: existen antes y sobreviven al combo).
  - Validación: menos de 2 componentes lanza `ValueError`. Descuento en `[0, 1)`.
  - Retorno protegido: `componentes() -> tuple[Producto, ...]`.
  - Decisión de dominio para `precio_base` y `stock_cantidad`/`disponible` del combo.
  - Implementar `precio_final(cantidad: float) -> float`: valida cantidad entera `>= 1`. Fórmula: `(suma de componente.precio_final(1)) * (1 - descuento) * cantidad`. Soporta anidamiento recursivo de combos polimórficamente.

### Implementación del Paso 4
*(Espacio reservado para código y fundamentación)*

---

## Paso 5: Rediseño de Producto Destacado
* **Estado:** [Pendiente]
* **Archivo(s) a modificar:** `catalogo.py`
* **Requerimientos:** R3 (Herencia justificada por dominio)  
* **Historias de Usuario:** HU-P1-05

### 5.1 Análisis crítico de la herencia ("es-un") - [Pendiente]
* **Objetivo:** Evaluar por qué "ser destacado" no es una especialización de venta sino un estado/rol promocional de cualquier producto.
* **Fundamentación:** Con herencia, un `ProductoDestacado` no podría a la vez ser `ProductoPorPeso` o `ProductoCombo` sin herencia múltiple compleja o explosión combinatoria de clases.

### 5.2 Implementación del rediseño - [Pendiente]
* **Objetivo:** Materializar la alternativa elegida:
  - **Opción A:** Atributo opcional `_orden_vidriera: int | None = None` en `Producto` base con property de lectura y método `destacar(orden: int)`.
  - **Opción B:** Objeto `Destacado` por composición/asociación externa.

### Implementación del Paso 5
*(Espacio reservado para código y fundamentación)*

---

## Paso 6: Función Exportadora
* **Estado:** [Pendiente]
* **Archivo(s) a modificar:** `catalogo.py`
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
