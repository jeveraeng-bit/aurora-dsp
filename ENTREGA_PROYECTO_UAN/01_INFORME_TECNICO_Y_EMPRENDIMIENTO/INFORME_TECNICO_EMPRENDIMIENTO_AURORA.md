# UNIVERSIDAD ANTONIO NARIÑO
## FACULTAD DE INGENIERÍA · PROGRAMA DE INGENIERÍA ELECTRÓNICA
### SEDE IBAGUÉ — CAPITAL MUSICAL DE COLOMBIA

---

# INFORME CIENTÍFICO, TÉCNICO Y PLAN DE NEGOCIO PARA LA CREACIÓN DE UNA EMPRESA DE AUDIO DIGITAL (SPIN-OFF)
## AURORA BY JUAN ESTEBAN VERA: ARQUITECTURA DSP HÍBRIDA (SUSTRACTIVA + FM-X) CON MOTION CONTROL SUPER KNOB Y PROCESAMIENTO EN TIEMPO REAL

```text
========================================================================================
Proyecto      : AURORA — PROFESSIONAL YAMAHA MONTAGE DSP WORKSTATION
Versión       : 2.1.0 Enterprise & Educational Edition
Autor         : Juan Esteban Vera Rodríguez
Institución   : Universidad Antonio Nariño (UAN), Sede Ibagué
Programa      : Ingeniería Electrónica
Enfoque       : Procesamiento Digital de Señales (DSP), Software de Audio e Innovación Emprendedora
Fecha         : Septiembre de 2026
========================================================================================
```

---

## DEDICATORIA INSTITUCIONAL

> *"A la **Universidad Antonio Nariño (UAN)**, mi alma mater, y a su distinguido claustro de profesores de la **Facultad de Ingeniería Electrónica de la Sede Ibagué**. En sus laboratorios, aulas y espacios académicos se consolidaron los fundamentos matemáticos del cálculo vectorial, el álgebra de señales y el diseño de sistemas de control que hicieron posible la concepción de esta obra.*
>
> *Dedico este trabajo a mi universidad como un testimonio tangible de gratitud y compromiso institucional. Los ingenieros nariñistas poseemos la vocación y el talento para convertir la ciencia exacta en bienestar, progreso económico y tecnología de vanguardia que traspase nuestras fronteras nacionales."*
>
> — **Juan Esteban Vera Rodríguez**

---

## MANIFIESTO DEL INGENIERO EMPRENDEDOR

> *"El desarrollo de **Aurora** no es únicamente un ejercicio de rigor científico en procesamiento de señales; es la proclamación de una postura frente al futuro de Colombia y de nuestra región. Históricamente, nuestro país ha sido visto como una nación receptora y consumidora de tecnología fabricada en los grandes centros industriales del norte global.*
>
> *Como futuro Ingeniero Electrónico de la Universidad Antonio Nariño, nacido y formado en Ibagué —la Capital Musical de Colombia—, me niego a aceptar esa limitación. Este proyecto nació para demostrar que la riqueza cultural de nuestro territorio puede unirse indisolublemente con la alta tecnología digital.*
>
> *Mi visión y motivación no terminan en la entrega de un documento académico: el propósito supremo es constituir una empresa de base tecnológica (Spin-off) con sede en Ibagué, capaz de comercializar sintetizadores, plugins de audio y procesadores DSP de nivel mundial que compitan de igual a igual con las marcas más prestigiosas de Japón, Alemania y Estados Unidos. Aurora es el primer pilar de esa empresa."*

---

## RESUMEN EJECUTIVO

El presente informe documenta de manera exhaustiva el modelado matemático, la arquitectura computacional, la validación experimental y la estructuración del plan de negocio para el sintetizador polifónico en tiempo real **Aurora By Juan Esteban Vera** (versión 2.1.0). El instrumento integra síntesis híbrida sustractiva y de frecuencia modulada (FM-X), inspirada en la arquitectura de los instrumentos emblemáticos **Yamaha MONTAGE**, **Yamaha DX7** y **Yamaha CS-80**. 

Se detallan las formulaciones analíticas para la supresión de aliasing espectral mediante la corrección cuadrática *PolyBLEP*, la resolución implícita de ecuaciones de estado mediante el filtro resonante de 2 polos basado en la transformada preservadora de topología (*TPT State-Variable Filter*), la distorsión armónica no lineal modelada mediante tangente hiperbólica adaptativa ($\tanh$), la dispersión espacial con retardo estéreo analógico (*Ping-Pong Delay*), la reverberación multi-tap de Schroeder y la detección de frecuencia fundamental ($f_0$) en tiempo real utilizando el teorema de Wiener-Khinchin. La arquitectura de software desarrollada en Python y acelerada mediante operaciones vectoriales nativas SIMD de NumPy garantiza una latencia determinista de $5.33\text{ ms}$ y una carga de procesamiento inferior al $2.8\%$ de CPU. Finalmente, se formula el modelo comercial de la empresa tecnológica naciente, con proyecciones financieras a tres años, análisis de mercado (TAM/SAM/SOM) y estrategia de protección de propiedad intelectual ante la DNDA y la SIC en Colombia.

---

## ÍNDICE GENERAL DEL INFORME

1. **Marco Institucional, Contexto Socioeconómico y Motivación del Emprendedor**
   - 1.1 Contexto de Ibagué como Ciudad Creativa de la Música (UNESCO)
   - 1.2 El Papel de la Universidad Antonio Nariño en la Formación de Emprendedores
   - 1.3 Objetivos del Proyecto (General y Específicos)
2. **Estado del Arte e Ingeniería Inversa: La Arquitectura Yamaha**
   - 2.1 Evolución Histórica de los Sintetizadores Yamaha (CS-80, DX7, MONTAGE)
   - 2.2 Análisis del Motion Control System y la Filosofía del Super Knob
3. **Fundamentación Teórica y Modelado Matemático Riguroso (DSP)**
   - 3.1 Muestreo Discreto y el Desafío del Aliasing Espectral
   - 3.2 Deducción Analítica del Algoritmo PolyBLEP
   - 3.3 Síntesis por Modulación de Frecuencia y Fase (FM / PM de Chowning)
   - 3.4 Filtro Resonante Analógico Virtual TPT SVF de 2 Polos (Vadim Zavalishin)
   - 3.5 Saturación Armónica Analógica (Drive) y Series de Taylor de $\tanh$
   - 3.6 Procesamiento Vocal por Autocorrelación FFT (Teorema de Wiener-Khinchin)
4. **Arquitectura de Software y Técnicas de Vectorización para Tiempo Real**
   - 4.1 Desafíos de Latencia en Sistemas de Alto Nivel
   - 4.2 Procesamiento por Bloques Vectorizados SIMD con NumPy
   - 4.3 Buffers Circulares Módulo-Indexados sin Desplazamiento de Memoria
   - 4.4 Concurrencia Thread-Safe y Desacoplamiento de Hilos con `SimpleQueue`
5. **Verificación Experimental, Pruebas Unitarias y Benchmarking**
   - 5.1 Validación de las 13 Pruebas Unitarias Automatizadas
   - 5.2 Medición del Presupuesto Temporal de Procesamiento (Budget de $5.33\text{ ms}$)
   - 5.3 Análisis Espectral y Atenuación de Aliasing ($> 36\text{ dB}$)
6. **Plan de Negocio y Modelo de Emprendimiento Tecnológico (Spin-off)**
   - 6.1 Oportunidad en el Mercado Global de Audio (\$1.280M USD TAM)
   - 6.2 Estrategia de Producto y Monetización (Freemium, Pro \$49 USD, OEM B2B)
   - 6.3 Proyección Financiera a 3 Años y Punto de Equilibrio
   - 6.4 Estrategia de Propiedad Intelectual en Colombia (DNDA y SIC)
7. **Conclusiones y Trabajo Futuro**
8. **Referencias Bibliográficas**

---

*(Consulte la versión completa diagramada e impresa de 14 páginas en [informe_aurora_uan.pdf](file:///c:/Users/juane/OneDrive/Desktop/sintentizador/ENTREGA_PROYECTO_UAN/01_INFORME_TECNICO_Y_EMPRENDIMIENTO/informe_aurora_uan.pdf)).*
