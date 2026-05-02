# Manual de Usuario: Resolución de SEL por LU

Bienvenido al manual oficial del software de **Resolución de Sistemas de Ecuaciones Lineales (SEL)** mediante la **Descomposición LU (Algoritmo de Doolittle)**. Este documento proporciona una guía detallada sobre cómo utilizar la aplicación y una explicación técnica de su funcionamiento.

---

## 📋 Índice
1. [Introducción](#introducción)
2. [Guía de Instalación](#guía-de-instalación)
3. [Guía de Uso](#guía-de-uso)
    - [Selección del Tamaño](#selección-del-tamaño)
    - [Ingreso de Coeficientes](#ingreso-de-coeficientes)
    - [Ejecución y Resultados](#ejecución-y-resultados)
4. [Explicación Técnica](#explicación-técnica)
    - [Descomposición LU (Doolittle)](#descomposición-lu-doolittle)
    - [Pivoteo Parcial](#pivoteo-parcial)
    - [Sustituciones](#sustituciones)
5. [Solución de Problemas](#solución-de-problemas)

---

## 🚀 Introducción
Este software ha sido diseñado para estudiantes y profesionales que requieren resolver sistemas de ecuaciones de forma exacta, visualizando el proceso matemático paso a paso. La herramienta permite manejar matrices desde 2x2 hasta 8x8, ofreciendo una representación en LaTeX de alta calidad.

---

## 🛠️ Guía de Instalación

Para ejecutar la aplicación en su entorno local, siga estos pasos:

1. **Requisitos Previos:** Asegúrese de tener instalado Python 3.8 o superior.
2. **Dependencias:** Instale las librerías necesarias ejecutando:
   ```bash
   pip install -r requirements.txt
   ```
3. **Ejecución:** Inicie el programa con el comando:
   ```bash
   python app.py
   ```

---

## 🖱️ Guía de Uso

### Selección del Tamaño
En el panel izquierdo, encontrará botones para seleccionar la dimensión de su sistema ($n \times n$). Al hacer clic en un botón (ej. **4x4**), la cuadrícula de entrada se actualizará automáticamente.

### Ingreso de Coeficientes
- **Matriz de Coeficientes ($A$):** Ingrese los valores numéricos en las celdas de la izquierda.
- **Vector de Términos Independientes ($b$):** Ingrese los valores en la columna resaltada a la derecha.
- **Atajo:** Use la tecla `Enter` para saltar rápidamente a la siguiente celda.
- **Prueba Rápida:** Use el botón **Ejemplo 4x4** para cargar datos de prueba predefinidos.

### Ejecución y Resultados
Presione el botón azul **Resolver →**. El software mostrará:
1. **Banner de Éxito:** Si el sistema tiene solución única.
2. **Paso a Paso:** Una lista detallada de cada etapa de la descomposición y las sustituciones.
3. **Código LaTeX:** Use **Copiar LaTeX** para obtener el código listo para informes académicos.

---

## 🧠 Explicación Técnica

El núcleo del programa implementa el **Algoritmo de Doolittle** con **Pivoteo Parcial**.

### Descomposición LU (Doolittle)
Se busca descomponer la matriz $A$ tal que $PA = LU$, donde:
- **$P$**: Matriz de permutación (registra intercambios de filas).
- **$L$**: Matriz triangular inferior con 1s en la diagonal.
- **$U$**: Matriz triangular superior.

### Pivoteo Parcial
Para evitar divisiones por cero y minimizar errores de redondeo, el programa busca en cada paso el elemento de mayor valor absoluto en la columna actual y permuta las filas si es necesario.

### Sustituciones
Una vez obtenidas $L$ y $U$, el sistema se resuelve en dos fases:
1. **Sustitución hacia adelante:** $Lz = Pb$
2. **Sustitución hacia atrás:** $Ux = z$

---

## ⚠️ Solución de Problemas

- **Matriz Singular:** Si el determinante de la matriz es 0, el programa detectará que no tiene solución única y mostrará un mensaje de advertencia.
- **Datos Inválidos:** Asegúrese de que todas las celdas contengan valores numéricos válidos. Las fracciones deben ingresarse como decimales o serán ignoradas si no son válidas.

---

*Desarrollado para la cátedra de Análisis Numérico.*
