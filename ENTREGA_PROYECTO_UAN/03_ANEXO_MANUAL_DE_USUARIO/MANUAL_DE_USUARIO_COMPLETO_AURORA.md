# MANUAL OFICIAL DE USUARIO E INTERPRETACIÓN MUSICAL
## AURORA BY JUAN ESTEBAN VERA — YAMAHA MONTAGE DSP WORKSTATION
### Universidad Antonio Nariño · Sede Ibagué · Ingeniería Electrónica
**Versión de Software:** 2.1.0 Enterprise & Educational  
**Autor y Desarrollador:** Juan Esteban Vera Rodríguez

---

## 1. INTRODUCCIÓN AL INSTRUMENTO

**Aurora By Juan Esteban Vera** es un sintetizador polifónico híbrido y procesador digital de señales (DSP) en tiempo real, concebido para brindar la máxima fidelidad acústica, calidez analógica y versatilidad tímbrica tanto en el estudio de producción musical como en presentaciones en vivo.

El instrumento fusiona la calidez del **modelado analógico sustractivo** clásico (Yamaha CS-80) con la riqueza espectral de la **síntesis por Modulación de Frecuencia** (Yamaha DX7 / FM-X), coronado por el célebre **Motion Control System con Super Knob** del sintetizador insignia **Yamaha MONTAGE**.

---

## 2. REQUISITOS DEL SISTEMA Y PUESTA EN MARCHA

### 2.1. Requisitos de Hardware y Software
- **Sistema Operativo:** Windows 10 / 11 (64 bits), macOS 11+ o GNU/Linux.
- **Procesador:** Intel Core i3 / AMD Ryzen 3 o superior (optimizado para arquitecturas multi-núcleo).
- **Memoria RAM:** Mínimo 2 GB (el software consume $< 45\text{ MB}$).
- **Dispositivo de Sonido:** Compatible con WASAPI, ASIO o CoreAudio para monitoreo de ultra-baja latencia.
- **Entorno de Ejecución:** Python 3.10 o superior con dependencias `numpy` y `sounddevice`.

### 2.2. Instrucciones de Inicio Rápido
1. Abra una terminal en el directorio raíz de la aplicación.
2. Inicie el entorno e instale dependencias si aún no lo ha hecho:
   ```powershell
   python -m pip install -r requirements.txt
   ```
3. Ejecute la aplicación principal:
   ```powershell
   python main.py
   ```
4. Se abrirá inmediatamente la consola de trabajo principal con el preset predeterminado *Yamaha DX7 E-Piano*.

---

## 3. MAPA Y DISTRIBUCIÓN DEL TECLADO EXTENDIDO (25 TECLAS)

Aurora cuenta con un teclado virtual de 25 teclas continuas en pantalla (15 blancas y 10 negras), que abarcan dos octavas simultáneas por defecto (de Do3 a Do5):

```text
  Teclas Negras:     [C#3] [D#3]       [F#3] [G#3] [A#3]       [C#4] [D#4]       [F#4] [G#4] [A#4]
  Teclas Blancas: [C3]  [D3]  [E3]  [F3]  [G3]  [A3]  [B3]  [C4]  [D4]  [E4]  [F4]  [G4]  [A4]  [B4]  [C5]
```

### 3.1. Interpretación con Ratón
- **Clic Individual:** Toca la nota con ataque instantáneo.
- **Arrastre Glissando:** Mantenga presionado el botón izquierdo del ratón y deslícelo por el teclado para realizar un barrido melódico continuo.

### 3.2. Mapeo del Teclado de la Computadora (Doble Octava)
Puede interpretar acordes y melodías complejas utilizando las teclas de su ordenador:

1. **Octava Inferior (Grave / Registro C3 a B3):**
   - **Notas Naturales (Blancas):** `Z` (Do3), `X` (Re3), `C` (Mi3), `V` (Fa3), `B` (Sol3), `N` (La3), `M` (Si3).
   - **Alteraciones (Negras):** `S` (Do#3), `D` (Re#3), `G` (Fa#3), `H` (Sol#3), `J` (La#3).

2. **Octava Superior (Aguda / Registro C4 a C5):**
   - **Notas Naturales (Blancas):** `Q` (Do4), `W` (Re4), `E` (Mi4), `R` (Fa4), `T` (Sol4), `Y` (La4), `U` (Si4), `I` (Do5).
   - **Alteraciones (Negras):** `2` (Do#4), `3` (Re#4), `5` (Fa#4), `6` (Sol#4), `7` (La#4).

3. **Mapeo Tradicional Fila Central (C4 a C5):**
   - `A, W, S, E, D, F, T, G, Y, H, U, J, K`.

### 3.3. Transposición Dinámica de Octavas (`OCT -` / `OCT +`)
- Presione el botón **`[ ◀ OCT - ]`** para descender una octava, permitiendo acceder a frecuencias sub-graves (hasta **C1** $\approx 32.7\text{ Hz}$).
- Presione el botón **`[ OCT + ▶ ]`** para ascender una octava, alcanzando registros solistas agudos y brillantes (hasta **C7**).
- La etiqueta central le indicará en todo momento el rango activo.

### 3.4. Botón de Pánico / Silenciado de Emergencia
- Presione la tecla **`Escape (Esc)`** en cualquier momento o haga clic en **`[ ⏹ SILENCIAR TODO ]`** en la cabecera superior para cancelar todas las voces activas de forma inmediata.

---

## 4. GUÍA DETALLADA DE MÓDULOS Y CONTROLES

### 4.1. Módulo de Osciladores y Modulación FM (DX7 / FM-X)
Ubicado en la pestaña **🎹 SINTETIZADOR & FM**:
- **Forma Onda OSC 1 y OSC 2:** Seleccione entre *Sine* (seno puro), *Triangle* (triangular con armónicos impares suaves), *Saw* (diente de sierra rica en armónicos con corrección PolyBLEP), *Square* (cuadrada hueca con PolyBLEP) y *Noise* (ruido blanco estocástico).
- **Mezcla OSC 2 (`osc2_mix`):** Controla la proporción relativa entre el Oscilador 1 y el Oscilador 2 (de 0.0 a 1.0).
- **Desafinación en Cents (`detune_cents`):** Desafina ligeramente el OSC 2 respecto al OSC 1 ($\pm 40\text{ cents}$) para crear el clásico efecto de coro analógico natural (\textit{chorusing}).
- **Intervalo Semitonos (`osc2_semitones`):** Fija un intervalo armónico en el OSC 2 (ej. $+7\text{ semitonos}$ para una quinta justa, $+12$ para una octava superior o $-12$ para un sub-oscilador).
- **⚡ Modulación FM (`fm_depth`):** Modula la fase instantánea del OSC 1 con la señal producida por el OSC 2. A valores bajos ($0.05 - 0.20$), añade brillo sutil; a valores medios ($0.30 - 0.60$), genera timbres de piano eléctrico FM y campanas; a valores altos ($> 0.70$), produce agresividad y texturas industriales complejas.

### 4.2. Filtro Resonante VCF (Yamaha CS-80)
- **Frecuencia de Corte (`cutoff`):** Rango de $50\text{ Hz}$ a $14.000\text{ Hz}$. Determina el punto donde el filtro empieza a atenuar los armónicos superiores a razón de $-12\text{ dB/octava}$.
- **Resonancia Q (`resonance`):** Rango de $0.0$ a $0.95$. Enfatiza la banda de frecuencias justo en el corte, produciendo el característico "silbido" o pico armónico analógico. Gracias a la topología TPT SVF, el filtro nunca entra en desbordamiento numérico inestable.
- **Vibrato LFO (`vibrato_rate` y `vibrato_depth`):** Genera una modulación periódica de tono sobre las voces para una expresividad orgánica.

### 4.3. Envolvente ADSR de Amplitud
Modela la curva temporal del volumen de cada voz de forma independiente:
- **Attack (Ataque):** Tiempo que tarda el sonido en alcanzar su amplitud máxima desde que se presiona la tecla ($1\text{ ms}$ a $2.5\text{ s}$).
- **Decay (Decaimiento):** Tiempo que tarda en descender desde el pico hasta el nivel de sostenimiento ($10\text{ ms}$ a $2.5\text{ s}$).
- **Sustain (Sostenimiento):** Nivel de volumen mantenido mientras la tecla continúa presionada ($0.0$ a $1.0$).
- **Release (Liberación):** Tiempo que tarda el sonido en extinguirse tras soltar la tecla ($10\text{ ms}$ a $3.5\text{ s}$).

### 4.4. El Motion Control Super Knob (Pestaña 🎛️ SUPER KNOB & EFECTOS)
El mando maestro central de gran tamaño permite la modulación multidimensional:
- **Interacción:** Arrastre verticalmente con el ratón o utilice la rueda de desplazamiento (\textit{scroll wheel}) sobre el dial.
- **Comportamiento:** A medida que se incrementa el porcentaje ($0\% \to 100\%$):
  1. Abre la frecuencia de corte del filtro progresivamente.
  2. Eleva la resonancia para mayor presencia armónica.
  3. Incrementa el índice de modulación FM.
  4. Satura el previo con saturación armónica analógica (*Drive*).
  5. Expande las dimensiones del retardo estéreo y la difusión de la reverberación.

### 4.5. Procesador de Efectos MONTAGE
- **Drive Analógico:** Genera saturación cálida ($\tanh$) para empujar la mezcla.
- **Analog Stereo Delay:** Retardo con rebote estéreo ping-pong (canal derecho desfasado un $15\%$) y realimentación suave con limitador analógico.
- **Reverberación Schroeder:** Algoritmo multi-tap con retardos primos cruzados que simulan la acústica de salas de concierto.

---

## 5. GUÍA DEL SECUENCIADOR POR PASOS (PESTAÑA 🎼 SECUENCIADOR)

1. Seleccione el tempo deseado con el deslizador **Tempo (BPM)** (de 50 a 200 BPM).
2. La cuadrícula inferior contiene **16 pasos**. Haga clic sobre cualquier botón para alternar cíclicamente la nota deseada (Silencio $\to$ C4 $\to$ C\#4 $\to$ D4 $\dots \to$ C5).
3. Presione **`▶ REPRODUCIR`** para iniciar el bucle rítmico sincronizado. El paso activo se resaltará en tiempo real.
4. Puede guardar su patrón musical y preset asociado utilizando **`💾 GUARDAR SECUENCIA`** (archivo `.aurora-song.json`) y volver a cargarlo en cualquier momento con **`📂 ABRIR SECUENCIA`**.

---

## 6. GUÍA DEL PROCESADOR VOCAL Y AFINADOR (PESTAÑA 🎤 VOZ / AFINACIÓN)

1. **Requisito fundamental:** Conecte auriculares a su ordenador para evitar el acople acústico (*feedback*) entre los altavoces y el micrófono.
2. Active la casilla de verificación **"Activar monitorización y afinación de micrófono"**.
3. Seleccione la escala musical deseada en el menú desplegable (*C mayor*, *C menor*, *A menor*, *C cromática*).
4. Cante o hable por el micrófono:
   - El detector FFT calculará en milisegundos su tono exacto en Hertz.
   - El algoritmo granular ajustará el tono hacia la nota afinada más cercana dentro de la escala seleccionada.
   - Ajuste la **Intensidad de Corrección** ($0.50$ para un resultado natural, $1.00$ para el clásico efecto electrónico autotune marcado).
