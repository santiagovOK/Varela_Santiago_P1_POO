# Primer Examen Parcial -  - Programación IV - UTN TUPaD

✨ Estudiante

- Nombre: Varela, Santiago Octavio
- Email institucional: santiago.varela@tupad.utn.edu.ar

# Links de relevancia para la evaluación

**Link al repositorio en Github:**

**- [Video explicativo](/link_video.txt)**
**- Video explicativo (link B):**

**- Presentación utilizada en el video:**

Resumen breve de resolución de cada una de las consignas (principalmente para guiarme yo). Pueden verlo aquí: [docs/resolucion_parcial.md](docs/resolucion_parcial.md)

Diagrama UML [aquí](/uml/modelo_final.md). También disponible en [.png](/uml/modelo_final.png)

## Objetivo General

Modelar e implementar el catálogo de productos para el comercio **Food Store** en memoria utilizando **Python 3.12+** y programación orientada a objetos, respetando las buenas prácticas de diseño y evitando vicios de traslación desde Java (*javaísmos*):
* **Encapsulamiento defensivo:** Proteger el estado interno mediante validaciones de dominio e invariantes, exponiendo properties `@property` de solo lectura y estado derivado sin caer en pares getter/setter artificiales.
* **Relaciones estructurales:** Modelar con precisión la **composición**, **agregación** y **asociación** distinguiéndolas por su ciclo de vida observable en el código.
* **Herencia y polimorfismo:** Justificar la herencia mediante el criterio estricto del dominio «es-un», empleando clases base abstractas (`ABC`) con `@abstractmethod` para garantizar falla temprana en construcción, y rediseñando roles transitorios (vidriera) como atributos dinámicos en lugar de jerarquías rígidas.
* **Contratos estructurales:** Utilizar `typing.Protocol` (*Duck Typing*) para exportar conjuntamente productos propios y fichas externas de terceros sin requerir adaptadores artificiales ni modificar librerías ajenas.

### Resumen de funcionalidades implementadas:

* **Requerimiento 1 — Modelado del dominio y encapsulamiento (HU-P1-01):**
  - `UnidadMedida`: *Value Object* inmutable implementado con `@dataclass(frozen=True)`.
  - `Categoria`: Agrupador de catálogo con atributos protegidos y properties de solo lectura (`nombre`, `descripcion`).
  - `Producto`: Clase base con validaciones de invariantes en construcción (`ValueError`), métodos de dominio (`habilitar()`, `deshabilitar()`) y properties calculadas (`disponible`, `precio_publicado`).
* **Requerimiento 2 — Relaciones estructurales del catálogo (HU-P1-02):**
  - **Composición (`1 *-- 1..*`):** `Producto` fabrica y encapsula sus clasificaciones `ProductoCategoria`, garantizando en todo momento exactamente una categoría principal y retornando tuplas inmutables defensivas en `categorias()`.
  - **Agregación (`1 o-- 2..*`):** `ProductoCombo` agrupa $\ge 2$ productos preexistentes que sobreviven a la desintegración del combo y pueden reagruparse en otros.
  - **Asociación (`0..* --> 0..1`):** `Producto` asocia opcionalmente una `UnidadMedida` independiente.
* **Requerimiento 3 — Herencia justificada por dominio (HU-P1-03, HU-P1-05):**
  - `Producto` como `ABC` con `@abstractmethod def precio_final(cantidad: float) -> float`.
  - Subclases de venta concretas: `ProductoSimple` (por unidad entera), `ProductoPorPeso` (por peso continuo, redondeado a 2 decimales) y `ProductoCombo` (con descuento sobre la suma de componentes).
  - **Resolución de `ProductoDestacado` (HU-P1-05):** Se descarta la herencia del diagrama preliminar al ser un rol transitorio de vidriera. Se incorpora el estado dinámico `_orden_vidriera` y métodos `destacar(orden)` / `quitar_destacado()` en `Producto`, permitiendo destacar cualquier producto del catálogo sin explosión combinatoria de clases.
* **Requerimiento 4 — Contratos: ABC vs. Protocol (HU-P1-04):**
  - `Exportable` resuelto como `Protocol` con método `exportar() -> str`.
  - Función independiente `exportar_catalogo(items: list[Exportable]) -> list[str]` que procesa polimórficamente productos y fichas externas `FichaPuntoDeVenta` (de `libreria_externa.py`) sin modificar la librería ajena ni requerir herencia nominal.
* **Requerimiento 5 — Diagrama UML final y demo ejecutable:**
  - Diagrama de clases final Mermaid en `uml/modelo_final.md` reflejando el rediseño sin `ProductoDestacado`.
  - Script demostrativo completo en `main.py` evidenciando en consola todas las reglas de negocio, ciclo de vida, polimorfismo y respuestas para la defensa oral.

### Estructura del proyecto

```text
Varela_Santiago_P1_POO/
├── README.md            # Descripción del proyecto, requerimientos e instrucciones de ejecución
├── catalogo.py          # Modelo de dominio completo del catálogo (Requerimientos 1 al 4)
├── libreria_externa.py  # FichaPuntoDeVenta provista por un tercero (SE ENTREGA SIN MODIFICAR)
├── main.py              # Script ejecutable de demostración del catálogo (Requerimiento 5)
├── link_video.txt       # Enlace público al video de defensa oral obligatoria
└── uml/
    └── modelo_final.md  # Diagrama de clases UML final en sintaxis Mermaid y fundamentaciones
```

#### Instrucciones de ejecución

El proyecto está desarrollado exclusivamente con la biblioteca estándar de **Python 3.12+** y no requiere ninguna dependencia externa ni la creación de entornos virtuales:

1. **Ejecutar la demostración interactiva:**
   ```bash
   python3 main.py
   ```
2. **Ejecutar la suite de pruebas unitarias:**
   ```bash
   python3 test/test_catalogo.py
   ```

## Licencia

Este proyecto se distribuye bajo la [Licencia MIT](LICENCE.TXT).