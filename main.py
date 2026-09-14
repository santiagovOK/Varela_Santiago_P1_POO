"""Demostración ejecutable del catálogo Food Store (Requerimiento 5).

Este script demuestra en ejecución todas las reglas de negocio, contratos
y decisiones de diseño requeridas para la defensa del Primer Parcial de POO:
  1. Tipos base inmutables y categorías (R1).
  2. Composición e invariante de clasificación principal (R2).
  3. Agregación y ciclo de vida de componentes en combos (R2).
  4. Encapsulamiento y disponibilidad dinámica (R1).
  5. Rol dinámico de ProductoDestacado sin herencia espuria (R3 / HU-P1-05).
  6. Cálculo polimórfico de precio_final sin condicionales de tipo (R3).
  7. Falla temprana al instanciar subclases incompletas de una ABC (R3).
  8. Tipado estructural y Duck Typing con Protocol y libreria_externa (R4).
"""

from catalogo import (
    Categoria,
    Exportable,
    Producto,
    ProductoCombo,
    ProductoPorPeso,
    ProductoSimple,
    UnidadMedida,
    exportar_catalogo,
)
from libreria_externa import FichaPuntoDeVenta


def separador(titulo: str) -> None:
    print("\n" + "=" * 72)
    print(f"  {titulo}")
    print("=" * 72)


def main() -> None:
    separador("FOOD STORE - SISTEMA DE CATÁLOGO (DEMO R5)")

    # -------------------------------------------------------------------------
    # 1. Unidades de Medida y Categorías
    # -------------------------------------------------------------------------
    print("\n[1] Creación de Unidades de Medida (Value Objects) y Categorías:")
    u_kg = UnidadMedida("Kilogramo", "kg", "masa")
    u_unidad = UnidadMedida("Unidad", "u", "unidad")
    u_botella = UnidadMedida("Botella", "bot", "volumen")
    u_taza = UnidadMedida("Taza", "tza", "volumen")

    cat_almacen = Categoria("Almacén", "Comestibles y provisiones generales")
    cat_bebidas = Categoria("Bebidas", "Bebidas frías y gaseosas")
    cat_fiambreria = Categoria("Fiambrería", "Fiambres, embutidos y quesos")
    cat_cafeteria = Categoria("Cafetería", "Infusiones, café y pastelería")
    cat_ofertas = Categoria("Ofertas Especiales", "Promociones destacadas")

    print(f"  - Unidad inmutable: {u_kg.nombre} ({u_kg.simbolo}), tipo: {u_kg.tipo}")
    print(f"  - Categoría: {cat_almacen.nombre} -> '{cat_almacen.descripcion}'")

    # -------------------------------------------------------------------------
    # 2. Productos y Demostración de COMPOSICIÓN (R2)
    # -------------------------------------------------------------------------
    separador("DEMOSTRACIÓN DE COMPOSICIÓN (Producto -> ProductoCategoria)\n")
    print("Regla: ProductoCategoria SOLO nace dentro de Producto. El cliente no lo construye, no lo recibe de clasificar_en() y no puede reemplazarlo.\n")

    # Componentes que luego se agruparán en combos
    cafe = ProductoSimple("Café Expresso", 1200.0, cat_cafeteria, u_taza, stock_cantidad=20.0)
    medialuna = ProductoSimple("Medialuna de Manteca", 500.0, cat_cafeteria, u_unidad, stock_cantidad=35.0)

    # 4 Productos del catálogo principal (sin contar los componentes del combo)
    gaseosa = ProductoSimple("Gaseosa Coca Cola 1.5L", 1800.0, cat_bebidas, u_botella, stock_cantidad=25.0)
    aceite = ProductoSimple("Aceite de Oliva 500ml", 4500.0, cat_almacen, u_botella, stock_cantidad=15.0)
    queso_gouda = ProductoPorPeso("Queso Gouda", 9200.0, cat_fiambreria, u_kg, stock_cantidad=8.5)

    print(f"Producto creado: {gaseosa.nombre}")
    print(f"  - Categoría principal inicial: {gaseosa.categoria_principal().nombre}")
    print(f"  - Clasificaciones actuales: {[pc.categoria.nombre for pc in gaseosa.categorias()]}")

    print("\nAcción: Clasificamos gaseosa también en 'Ofertas Especiales' como secundaria.")
    gaseosa.clasificar_en(cat_ofertas, es_principal=False)
    print(f"  - Clasificaciones: {[pc.categoria.nombre for pc in gaseosa.categorias()]}")
    print(f"  - Categoría principal sigue siendo: {gaseosa.categoria_principal().nombre}")

    print(f"\nAcción: Cambiamos la categoría principal a '{cat_almacen.nombre}' (es_principal=True)...")
    gaseosa.clasificar_en(cat_almacen, es_principal=True)
    print(f"  - Nueva categoría principal: {gaseosa.categoria_principal().nombre}")
    print("  - Comprobación del invariante: exactamente 1 categoría principal:")
    for pc in gaseosa.categorias():
        print(f"    * {pc.categoria.nombre:18} | es_principal = {pc.es_principal}")

    print("\nProtección defensiva: categorias() retorna una tupla inmutable:")
    try:
        gaseosa.categorias().append(None)  # type: ignore
    except AttributeError as e:
        print(f"  - Intento de mutar categorias(): Capturado AttributeError ({e})")

    # -------------------------------------------------------------------------
    # 3. AGREGACIÓN: ProductoCombo y supervivencia de componentes (R2 y R3)
    # -------------------------------------------------------------------------
    separador("DEMOSTRACIÓN DE AGREGACIÓN (ProductoCombo o-- Producto)")
    print("Regla: Los componentes existen antes del combo y sobreviven a él.\n")

    combo_desayuno = ProductoCombo(
        nombre="Combo Desayuno Clásico",
        componentes=[cafe, medialuna],
        descuento=0.15,
        categoria=cat_cafeteria,
    )

    print(f"Combo creado: {combo_desayuno.nombre}")
    print(f"  - Componentes: {[c.nombre for c in combo_desayuno.componentes()]}")
    print(f"  - Descuento aplicado: {combo_desayuno.descuento * 100:.0f}%")
    print(f"  - Precio base derivado: $ {combo_desayuno.precio_base:.2f}")
    print(f"  - Precio publicado: {combo_desayuno.precio_publicado}")

    print("\nComprobación de supervivencia (Agregación):")
    print(f"  - Café sigue existiendo por su cuenta: {cafe.nombre} -> $ {cafe.precio_final(1):.2f}")
    print(f"  - Medialuna sigue existiendo por su cuenta: {medialuna.nombre} -> $ {medialuna.precio_final(1):.2f}")
    print("  - Reagrupamos 'cafe' en un nuevo combo sin problemas:")
    combo_doble_cafe = ProductoCombo("Promo Doble Café", [cafe, cafe], 0.20, cat_cafeteria)
    print(f"    * {combo_doble_cafe.nombre} -> {combo_doble_cafe.precio_publicado}")

    # -------------------------------------------------------------------------
    # 4. Encapsulamiento y Disponibilidad Dinámica (R1)
    # -------------------------------------------------------------------------
    separador("ENCAPSULAMIENTO Y DISPONIBILIDAD DINÁMICA")
    print(f"Estado inicial de '{aceite.nombre}':")
    print(f"  - Stock: {aceite._stock_cantidad} | Habilitado: {aceite._habilitado} -> disponible: {aceite.disponible}")
    print("Acción: deshabilitamos el aceite con aceite.deshabilitar()...")
    aceite.deshabilitar()
    print(f"  - Habilitado: {aceite._habilitado} -> disponible: {aceite.disponible}")
    print("Acción: rehabilitamos el aceite con aceite.habilitar()...")
    aceite.habilitar()
    print(f"  - Habilitado: {aceite._habilitado} -> disponible: {aceite.disponible}")

    print(f"\nDisponibilidad derivada del Combo '{combo_desayuno.nombre}':")
    print(f"  - Combo disponible: {combo_desayuno.disponible} (todos los componentes tienen stock y están habilitados)")
    print("Acción: deshabilitamos el componente 'medialuna'...")
    medialuna.deshabilitar()
    print(f"  - Combo disponible tras deshabilitar medialuna: {combo_desayuno.disponible}")
    medialuna.habilitar()
    print(f"  - Combo disponible tras rehabilitar medialuna: {combo_desayuno.disponible}")

    # -------------------------------------------------------------------------
    # 5. Rediseño de Producto Destacado (R3 / HU-P1-05)
    # -------------------------------------------------------------------------
    separador("REDISEÑO DE PRODUCTO DESTACADO (Rol en vidriera sin herencia)")
    print("Decisión: En lugar de una subclase rígida, '_orden_vidriera' vive en Producto.")
    print("Cualquier producto concreto puede ingresar o salir de la vidriera comercial.\n")

    print(f"Estado inicial: {queso_gouda.nombre} -> es_destacado = {queso_gouda.es_destacado}")
    print("Acción: destacamos el queso con orden 1 en la vidriera:")
    queso_gouda.destacar(1)
    print(f"  - {queso_gouda.nombre} -> orden_vidriera = {queso_gouda.orden_vidriera}, es_destacado = {queso_gouda.es_destacado}")

    print("Acción: también podemos destacar un combo promocional:")
    combo_desayuno.destacar(2)
    print(f"  - {combo_desayuno.nombre} -> orden_vidriera = {combo_desayuno.orden_vidriera}, es_destacado = {combo_desayuno.es_destacado}")

    print("Acción: quitamos de vidriera el queso con quitar_destacado():")
    queso_gouda.quitar_destacado()
    print(f"  - {queso_gouda.nombre} -> es_destacado = {queso_gouda.es_destacado}")

    # -------------------------------------------------------------------------
    # 6. Cálculo Polimórfico de precio_final (R3)
    # -------------------------------------------------------------------------
    separador("CÁLCULO POLIMÓRFICO DE PRECIO FINAL (Sin if / isinstance)")
    print("Cada subclase resuelve su propia regla de negocio polimórficamente:\n")

    productos_demo: list[Producto] = [gaseosa, aceite, queso_gouda, combo_desayuno]

    cantidades_prueba = [
        (gaseosa, 3),        # Simple: cantidad entera
        (aceite, 2.0),       # Simple: float de valor entero
        (queso_gouda, 0.450),# PorPeso: cantidad decimal (0.450 kg)
        (combo_desayuno, 2), # Combo: cantidad entera con descuento
    ]

    for prod, cant in cantidades_prueba:
        total = prod.precio_final(cant)
        unidad_str = f" {prod.unidad_venta.simbolo}" if prod.unidad_venta else ""
        print(f"  - {prod.nombre:26} | Cantidad: {cant:5}{unidad_str:4} | Total a pagar: $ {total:8.2f}")

    # -------------------------------------------------------------------------
    # 7. Contratos: Falla Temprana con ABC (R3)
    # -------------------------------------------------------------------------
    separador("FALLA TEMPRANA AL INCLUIR SUBCLASES INCOMPLETAS (ABC)")
    print("Regla: Si una subclase olvida implementar precio_final(), Python debe")
    print("fallar inmediatamente al CONSTRUIR con TypeError, no al usar.\n")

    class ProductoIncompleto(Producto):
        """Subclase ficticia que olvida implementar precio_final."""
        pass

    try:
        _ = ProductoIncompleto("Incompleto", 100.0, cat_almacen)
    except TypeError as e:
        print("  - Intento de instanciar 'ProductoIncompleto':")
        print(f"    CAPTURA EXITOSA (TypeError al construir): {e}")

    # -------------------------------------------------------------------------
    # 8. Exportación Polimórfica al Punto de Venta (R4 / Protocol)
    # -------------------------------------------------------------------------
    separador("EXPORTACIÓN CONJUNTA AL PUNTO DE VENTA (Protocol / Duck Typing)")
    print("Regla: exportar_catalogo recibe productos propios y fichas externas en")
    print("una misma lista sin que nadie herede de Exportable ni existan adaptadores.\n")

    ficha_externa_1 = FichaPuntoDeVenta("POS-0091", "Cigarrillos Rubios 20u")
    ficha_externa_2 = FichaPuntoDeVenta("POS-0092", "Recarga Virtual Prepaga")

    # Lista heterogénea unificada cumpliendo structural typing list[Exportable]
    items_a_exportar: list[Exportable] = [
        gaseosa,
        aceite,
        queso_gouda,
        combo_desayuno,
        ficha_externa_1,
        ficha_externa_2,
    ]

    lineas_exportadas = exportar_catalogo(items_a_exportar)

    print("Salida generada por exportar_catalogo(items):")
    for i, linea in enumerate(lineas_exportadas, 1):
        print(f"  [{i}] {linea}")

    separador("DEMOSTRACIÓN FINALIZADA CON ÉXITO")


if __name__ == "__main__":
    main()
