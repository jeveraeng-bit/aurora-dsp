# Aurora By Juan Esteban Vera — Professional YAMAHA Edition

Sintetizador polifónico híbrido (Sustractivo + FM) y procesador de efectos DSP en tiempo real, desarrollado por **Juan Esteban Vera**. Inspirado en la arquitectura del **YAMAHA MONTAGE**, **DX7** y **CS-80**.

Versión: **2.1.0**.

---

## Tienda Web y Plataforma Comercial de Plugins (Landing Page)

El proyecto cuenta con su propia **plataforma web comercial y tienda online** en la carpeta [`web/`](file:///c:/Users/juane/OneDrive/Desktop/sintentizador/web/index.html):
- **Catálogo de Plugins VST3 / AU / AAX**: Venta de licencias individuales (*Aurora Pro Workstation*, *Aurora Vocal Tune*, *CS-80 Analog Filter*) y *Aurora Creator Suite Bundle*.
- **Demo Web Audio DSP en Vivo**: Sintetizador virtual interactivo con osciloscopio en tiempo real y **Super Knob** operativo directamente desde el navegador web.
- **Carrito de Compras y Generador de Licencias**: Soporte multidivisa (USD / COP), cupones promocionales (`UAN2026`) y emisión de seriales criptográficos.
- **Acceso Directo al Dossier UAN**: Enlaces de descarga a los 6 informes técnicos y manuales en PDF.

Para abrir la tienda en tu navegador:
```powershell
# Opción 1: Servidor local automático
python web/serve.py

# Opción 2: Abrir directamente el archivo HTML
Start-Process "web\index.html"
```

---

## Desarrollador
- **Creador**: Juan Esteban Vera
- **Arquitectura**: Síntesis Híbrida Sustractiva / FM-X en tiempo real con modelado analógico y Motion Control.

---

## Tienda Web y Plataforma Comercial de Plugins (Landing Page)

El proyecto cuenta con su propia **plataforma web comercial y tienda online** en la carpeta [`web/`](file:///c:/Users/juane/OneDrive/Desktop/sintentizador/web/index.html):
- **Catálogo de Plugins VST3 / AU / AAX**: Venta de licencias individuales (*Aurora Pro Workstation*, *Aurora Vocal Tune*, *CS-80 Analog Filter*) y *Aurora Creator Suite Bundle*.
- **Demo Web Audio DSP en Vivo**: Sintetizador virtual interactivo con osciloscopio en tiempo real y **Super Knob** operativo directamente desde el navegador web.
- **Carrito de Compras y Generador de Licencias**: Soporte multidivisa (USD / COP), cupones promocionales (`UAN2026`) y emisión de seriales criptográficos.
- **Acceso Directo al Dossier UAN**: Enlaces de descarga a los 6 informes técnicos y manuales en PDF.

Para abrir la tienda en tu navegador:
```powershell
# Opción 1: Servidor local automático
python web/serve.py

# Opción 2: Abrir directamente el archivo HTML
Start-Process "web\index.html"
```

---

## Novedades y Capacidades (Inspiración YAMAHA)

- **Teclado Extendido de 25 Teclas (2 Octavas)**:
  - Teclado visual interactivo con 15 teclas blancas y 10 teclas negras completas.
  - Botones de transposición de octavas `[◀ OCT -]` y `[OCT + ▶]` para navegar desde C1 hasta C7.
  - Soporte para tocar con ratón y con teclado de computadora en dos octavas completas (`Z–M` para graves, `Q–I` para agudas, o la fila central `A–K`).
- **Menú y Guía de Uso Integrada ("CÓMO USARLO")**:
  - Botón prominente en la barra de herramientas y menú superior de ayuda con manual interactivo paso a paso:
    1. Cómo tocar notas y atajos de teclado.
    2. Manejo del Super Knob y síntesis FM.
    3. Uso de presets de fábrica y secuenciador de 16 pasos.
    4. Afinación vocal y autotune en vivo.
- **Ventana de Créditos del Desarrollador**:
  - Botón `[ 👤 DESARROLLADOR ]` en la barra superior con información técnica del proyecto y autoría de Juan Esteban Vera.
- **Motion Control System & Super Knob**:
  - Mando maestro multidimensional interactivo inspirado en el **Yamaha MONTAGE**. Permite morphing sonoro en tiempo real alterando armónicos FM, apertura de corte, resonancia, distorsión drive y dimensiones espaciales de delay y reverb simultáneamente.
- **Síntesis FM (Frecuencia Modulada estilo FM-X / DX7)**:
  - Modulación de fase y frecuencia directa del Oscilador 2 sobre el Oscilador 1. Permite crear desde los icónicos pianos eléctricos de los 80s y campanas cristalinas hasta bajos gruñidos y texturas metálicas.
- **Filtro Resonante TPT de 2 Polos (Estilo Yamaha CS-80)**:
  - Filtro pasa-bajos State-Variable con control de **Resonancia (Q)** incondicionalmente estable en todo el rango audible, permitiendo picos armónicos característicos de los sintetizadores analógicos.
- **Cadena de Efectos MONTAGE (DSP Insertion & Master)**:
  - **Analog Stereo Delay**: Línea de retardo con realimentación estéreo y calidez analógica.
  - **Drive & Saturación Armónica**: Modelado de saturación suave para dar cuerpo y presencia a bajos y solos.
  - **Reverberación Estéreo Schroeder**: Amplitud acústica y difusión espacial.
- **Performances & Presets de Fábrica**:
  - Selector instantáneo de interpretaciones clásicas:
    - *Yamaha DX7 E-Piano*
    - *Yamaha CS-80 Vangelis Pad*
    - *Montage Super Lead*
    - *TX81Z Lately Bass*
    - *Ambient Cosmic Dream*
    - *Acid Resonant Synth*
    - *Init Clean Patch*
- **Vúmetro Estéreo en Tiempo Real**: Indicador de nivel de señal (Output VU Meter) con gradiente verde/amarillo/rojo.

---

## Tienda Web y Plataforma Comercial de Plugins (Landing Page)

El proyecto cuenta con su propia **plataforma web comercial y tienda online** en la carpeta [`web/`](file:///c:/Users/juane/OneDrive/Desktop/sintentizador/web/index.html):
- **Catálogo de Plugins VST3 / AU / AAX**: Venta de licencias individuales (*Aurora Pro Workstation*, *Aurora Vocal Tune*, *CS-80 Analog Filter*) y *Aurora Creator Suite Bundle*.
- **Demo Web Audio DSP en Vivo**: Sintetizador virtual interactivo con osciloscopio en tiempo real y **Super Knob** operativo directamente desde el navegador web.
- **Carrito de Compras y Generador de Licencias**: Soporte multidivisa (USD / COP), cupones promocionales (`UAN2026`) y emisión de seriales criptográficos.
- **Acceso Directo al Dossier UAN**: Enlaces de descarga a los 6 informes técnicos y manuales en PDF.

Para abrir la tienda en tu navegador:
```powershell
# Opción 1: Servidor local automático
python web/serve.py

# Opción 2: Abrir directamente el archivo HTML
Start-Process "web\index.html"
```

---

## Requisitos y Ejecución

Instala las dependencias y ejecuta la aplicación en PowerShell / CMD:

```powershell
python -m pip install -r requirements.txt
python main.py
```

### Controles de interpretación:
- **Teclado de computadora (2 octavas)**:
  - Octava 1 (Grave): `Z, S, X, D, C, V, G, B, H, N, J, M`
  - Octava 2 (Aguda): `Q, 2, W, 3, E, R, 5, T, 6, Y, 7, U, I`
  - Fila central clásica: `A, W, S, E, D, F, T, G, Y, H, U, J, K`
- `Escape`: Silencia todas las notas activas inmediatamente.
- Haz clic o arrastra sobre el teclado de piano en pantalla para tocar con el ratón.
- Arrastra verticalmente o gira la rueda sobre el **Super Knob** para realizar barridos tímbricos multidimensionales.

---

## Tienda Web y Plataforma Comercial de Plugins (Landing Page)

El proyecto cuenta con su propia **plataforma web comercial y tienda online** en la carpeta [`web/`](file:///c:/Users/juane/OneDrive/Desktop/sintentizador/web/index.html):
- **Catálogo de Plugins VST3 / AU / AAX**: Venta de licencias individuales (*Aurora Pro Workstation*, *Aurora Vocal Tune*, *CS-80 Analog Filter*) y *Aurora Creator Suite Bundle*.
- **Demo Web Audio DSP en Vivo**: Sintetizador virtual interactivo con osciloscopio en tiempo real y **Super Knob** operativo directamente desde el navegador web.
- **Carrito de Compras y Generador de Licencias**: Soporte multidivisa (USD / COP), cupones promocionales (`UAN2026`) y emisión de seriales criptográficos.
- **Acceso Directo al Dossier UAN**: Enlaces de descarga a los 6 informes técnicos y manuales en PDF.

Para abrir la tienda en tu navegador:
```powershell
# Opción 1: Servidor local automático
python web/serve.py

# Opción 2: Abrir directamente el archivo HTML
Start-Process "web\index.html"
```

---

## Pruebas Unitarias

Para verificar el correcto funcionamiento del motor DSP:

```powershell
python -m unittest discover -s tests -v
```
