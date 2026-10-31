"""Motor DSP independiente de la interfaz inspirado en sintetizadores YAMAHA."""
from __future__ import annotations

from dataclasses import dataclass, replace
from queue import Empty, SimpleQueue
import math
import numpy as np


@dataclass(frozen=True)
class SynthParameters:
    # Osciladores principales
    waveform_1: str = "sine"
    waveform_2: str = "triangle"
    osc2_mix: float = 0.18
    detune_cents: float = 0.0
    osc2_semitones: float = 0.0

    # Síntesis FM (Yamaha DX / FM-X style)
    fm_depth: float = 0.0

    # Envolvente ADSR
    attack: float = 0.012
    decay: float = 0.18
    sustain: float = 0.72
    release: float = 0.32

    # Filtro & Resonancia (Yamaha CS-80 style)
    cutoff: float = 6500.0
    resonance: float = 0.0

    # Procesador de Efectos (Yamaha MONTAGE Insertion FX)
    drive: float = 0.0
    delay_time: float = 0.25
    delay_feedback: float = 0.35
    delay_mix: float = 0.0

    # Modulación, espacio y volumen
    vibrato_rate: float = 5.0
    vibrato_depth: float = 0.0
    master_gain: float = 0.35
    reverb_mix: float = 0.18
    reverb_room: float = 0.55

    # Mando maestro Motion Control (Yamaha MONTAGE Super Knob)
    super_knob: float = 0.0


def midi_to_hz(note: int | float) -> float:
    return 440.0 * 2.0 ** ((note - 69) / 12.0)


def _poly_blep(phase: np.ndarray, increment: float) -> np.ndarray:
    result = np.zeros_like(phase)
    first = phase < increment
    t = phase[first] / increment
    result[first] = 2.0 * t - t * t - 1.0
    last = phase > 1.0 - increment
    t = (phase[last] - 1.0) / increment
    result[last] = t * t + 2.0 * t + 1.0
    return result


def oscillator(phase: np.ndarray, increment: float, shape: str) -> np.ndarray:
    """Osciladores de banda limitada para sierra y cuadrada (PolyBLEP)."""
    if shape == "sine":
        return np.sin(2.0 * np.pi * phase)
    if shape == "triangle":
        return 1.0 - 4.0 * np.abs(np.round(phase) - phase)
    if shape == "noise":
        return np.random.uniform(-1, 1, phase.size)
    if shape == "saw":
        return 2.0 * phase - 1.0 - _poly_blep(phase, increment)
    signal = np.where(phase < 0.5, 1.0, -1.0)
    signal += _poly_blep(phase, increment)
    signal -= _poly_blep((phase + 0.5) % 1.0, increment)
    return signal


class ADSR:
    def __init__(self, params: SynthParameters, sample_rate: int) -> None:
        self.params, self.sample_rate = params, sample_rate
        self.stage, self.level = "attack", 0.0

    @property
    def done(self) -> bool:
        return self.stage == "done"

    def release(self) -> None:
        if not self.done:
            self.stage = "release"

    def render(self, frames: int) -> np.ndarray:
        values = np.empty(frames, dtype=np.float32)
        p = self.params
        offset = 0
        while offset < frames and not self.done:
            if self.stage == "attack":
                step = 1 / max(1, int(p.attack * self.sample_rate))
                count = min(frames - offset, max(1, math.ceil((1 - self.level) / step)))
                segment = self.level + step * np.arange(1, count + 1)
                values[offset:offset + count] = np.minimum(segment, 1.0)
                self.level = float(values[offset + count - 1]); offset += count
                if self.level >= 1: self.level, self.stage = 1.0, "decay"
            elif self.stage == "decay":
                step = (1 - p.sustain) / max(1, int(p.decay * self.sample_rate))
                count = min(frames - offset, max(1, math.ceil((self.level - p.sustain) / max(step, 1e-12))))
                segment = self.level - step * np.arange(1, count + 1)
                values[offset:offset + count] = np.maximum(segment, p.sustain)
                self.level = float(values[offset + count - 1]); offset += count
                if self.level <= p.sustain + 1e-6: self.level, self.stage = p.sustain, "sustain"
            elif self.stage == "sustain":
                values[offset:] = self.level
                offset = frames
            elif self.stage == "release":
                step = 1 / max(1, int(p.release * self.sample_rate))
                count = min(frames - offset, max(1, math.ceil(self.level / step)))
                segment = self.level - step * np.arange(1, count + 1)
                values[offset:offset + count] = np.maximum(segment, 0.0)
                self.level = float(values[offset + count - 1]); offset += count
                if self.level <= 0: self.level, self.stage = 0.0, "done"
        if offset < frames: values[offset:] = 0
        return values


class Voice:
    def __init__(self, note: int, velocity: float, params: SynthParameters, rate: int) -> None:
        self.note, self.velocity, self.frequency = note, velocity, midi_to_hz(note)
        self.phase_1 = self.phase_2 = 0.0
        self.envelope = ADSR(params, rate)
        self.pan = float(np.clip((note - 60) / 36, -0.75, 0.75))

    def render(self, frames: int, params: SynthParameters, rate: int, vibrato: np.ndarray, super_knob: float = 0.0) -> np.ndarray:
        """Renderiza con modulación FM, vibrato continuo y panoramización estéreo."""
        inc1 = (self.frequency / rate) * 2 ** (vibrato * params.vibrato_depth / 1200)
        inc2 = inc1 * 2 ** ((params.detune_cents + params.osc2_semitones * 100) / 1200)
        p1 = (self.phase_1 + np.cumsum(inc1) - inc1[0]) % 1
        p2 = (self.phase_2 + np.cumsum(inc2) - inc2[0]) % 1

        osc2 = oscillator(p2, float(np.max(inc2)), params.waveform_2)

        # Síntesis FM (Yamaha FM-X / DX7): Modulación de fase por el Oscilador 2
        effective_fm = params.fm_depth + (super_knob * 0.35 if super_knob > 0 else 0.0)
        if effective_fm > 0.001:
            p1_mod = (p1 + osc2 * (effective_fm * 0.5)) % 1
            osc1 = oscillator(p1_mod, float(np.max(inc1)), params.waveform_1)
        else:
            osc1 = oscillator(p1, float(np.max(inc1)), params.waveform_1)

        sound = osc1 * (1.0 - params.osc2_mix) + osc2 * params.osc2_mix
        self.phase_1 = float((self.phase_1 + np.sum(inc1)) % 1)
        self.phase_2 = float((self.phase_2 + np.sum(inc2)) % 1)
        sound *= self.envelope.render(frames) * self.velocity
        left, right = math.sqrt((1 - self.pan) / 2), math.sqrt((1 + self.pan) / 2)
        return np.column_stack((sound * left, sound * right)).astype(np.float32)


class ResonantFilter:
    """Filtro pasa-bajos de 2 polos resonante TPT (Topology-Preserving Transform SVF).
    Incondicionalmente estable para todo el rango audible, modelando la respuesta analógica del Yamaha CS-80.
    """
    def __init__(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self.s1 = np.zeros(2, dtype=np.float32)
        self.s2 = np.zeros(2, dtype=np.float32)

    def reset(self) -> None:
        self.s1.fill(0.0)
        self.s2.fill(0.0)

    def process(self, audio: np.ndarray, cutoff_hz: float, resonance: float) -> np.ndarray:
        frames = len(audio)
        fc = max(20.0, min(float(cutoff_hz), self.sample_rate * 0.48))
        g = float(math.tan(math.pi * fc / self.sample_rate))
        res_clipped = float(np.clip(resonance, 0.0, 0.98))
        R = float(max(0.03, 1.0 - res_clipped * 0.96))
        h = float(1.0 / (1.0 + 2.0 * R * g + g * g))

        s1_0, s1_1 = float(self.s1[0]), float(self.s1[1])
        s2_0, s2_1 = float(self.s2[0]), float(self.s2[1])

        out = np.empty((frames, 2), dtype=np.float32)
        in0, in1 = audio[:, 0], audio[:, 1]
        rg = 2.0 * R + g

        for i in range(frames):
            hp0 = (in0[i] - rg * s1_0 - s2_0) * h
            bp0 = g * hp0 + s1_0
            s1_0 = g * hp0 + bp0
            lp0 = g * bp0 + s2_0
            s2_0 = g * bp0 + lp0
            out[i, 0] = lp0

            hp1 = (in1[i] - rg * s1_1 - s2_1) * h
            bp1 = g * hp1 + s1_1
            s1_1 = g * hp1 + bp1
            lp1 = g * bp1 + s2_1
            s2_1 = g * bp1 + lp1
            out[i, 1] = lp1

        self.s1[0] = s1_0 if not math.isnan(s1_0) else 0.0
        self.s1[1] = s1_1 if not math.isnan(s1_1) else 0.0
        self.s2[0] = s2_0 if not math.isnan(s2_0) else 0.0
        self.s2[1] = s2_1 if not math.isnan(s2_1) else 0.0

        return out


class StereoDelay:
    """Línea de retardo estéreo con realimentación y espacialidad (Yamaha MONTAGE Delay)."""
    def __init__(self, sample_rate: int, max_time: float = 1.5) -> None:
        self.sample_rate = sample_rate
        self.max_frames = int(sample_rate * max_time)
        self.buffer = np.zeros((self.max_frames, 2), dtype=np.float32)
        self.write_pos = 0

    def process(self, audio: np.ndarray, delay_time: float, feedback: float, mix: float) -> np.ndarray:
        if mix <= 0.001:
            return audio
        frames = len(audio)
        dt = max(0.02, min(delay_time, 1.4))
        # Ligero desfase estéreo para efecto espacial amplio
        samples_l = max(1, min(int(dt * self.sample_rate), self.max_frames - frames - 1))
        samples_r = max(1, min(int(dt * 1.15 * self.sample_rate), self.max_frames - frames - 1))

        read_l = (self.write_pos - samples_l + np.arange(frames)) % self.max_frames
        read_r = (self.write_pos - samples_r + np.arange(frames)) % self.max_frames

        wet = np.empty_like(audio)
        wet[:, 0] = self.buffer[read_l, 0]
        wet[:, 1] = self.buffer[read_r, 1]

        fb = np.clip(feedback, 0.0, 0.88)
        write_idx = (self.write_pos + np.arange(frames)) % self.max_frames
        # Realimentación estéreo cruzada con recorte suave analógico
        feedback_sig = np.column_stack((wet[:, 1] * (fb * 0.25) + wet[:, 0] * (fb * 0.75),
                                        wet[:, 0] * (fb * 0.25) + wet[:, 1] * (fb * 0.75)))
        self.buffer[write_idx] = audio + np.tanh(feedback_sig)
        self.write_pos = int((self.write_pos + frames) % self.max_frames)

        return audio * (1.0 - mix) + wet * mix


def apply_drive(audio: np.ndarray, drive: float) -> np.ndarray:
    """Saturación armónica cálida inspirada en previos de hardware analógico."""
    if drive <= 0.001:
        return audio
    factor = 1.0 + drive * 4.5
    return np.tanh(audio * factor) / (1.0 + drive * 0.4)


class StereoReverb:
    """Reverb de retardos cruzados procesado por bloques, apto para tiempo real."""
    def __init__(self, rate: int) -> None:
        delays = [0.0297, 0.0371, 0.0411, 0.0437]
        self.buffers = [np.zeros((int(rate * seconds), 2), np.float32) for seconds in delays]
        self.positions = [0] * len(self.buffers)

    def process(self, audio: np.ndarray, params: SynthParameters) -> np.ndarray:
        frames = len(audio)
        wet = np.zeros_like(audio)
        for index, buffer in enumerate(self.buffers):
            positions = (self.positions[index] + np.arange(frames)) % len(buffer)
            delayed = buffer[positions].copy()
            wet += delayed
            feedback = delayed[:, ::-1] * params.reverb_room
            buffer[positions] = audio + feedback
            self.positions[index] = int((self.positions[index] + frames) % len(buffer))
        return audio * (1 - params.reverb_mix) + wet * (params.reverb_mix / len(self.buffers))


class SynthEngine:
    """Motor de síntesis polifónica en tiempo real inspirado en YAMAHA MONTAGE."""
    def __init__(self, sample_rate: int = 48_000, max_voices: int = 6) -> None:
        self.sample_rate, self.max_voices = sample_rate, max_voices
        self.parameters, self.voices = SynthParameters(), []
        self.commands = SimpleQueue()
        self.lfo_phase = 0.0

        # Módulos de Procesamiento DSP
        self.filter = ResonantFilter(sample_rate)
        self.delay = StereoDelay(sample_rate)
        self.reverb = StereoReverb(sample_rate)

        # Buffers de Análisis y Medición
        self.analysis_buffer, self.analysis_position = np.zeros(2048, np.float32), 0
        self.waveform_buffer, self.waveform_position = np.zeros(2048, np.float32), 0
        self.peak_l, self.peak_r = 0.0, 0.0

    def note_on(self, note: int, velocity: float = 1.0) -> None:
        self.commands.put(("on", int(note), float(np.clip(velocity, 0, 1))))

    def note_off(self, note: int) -> None:
        self.commands.put(("off", int(note)))

    def all_notes_off(self) -> None:
        self.commands.put(("all_off",))

    def set_parameter(self, name: str, value: object) -> None:
        if name not in SynthParameters.__dataclass_fields__:
            raise ValueError(f"Parámetro desconocido: {name}")
        self.commands.put(("set", name, value))

    def peak_levels(self) -> tuple[float, float]:
        """Nivel pico estéreo actual (0.0 a 1.0) para el vúmetro de la interfaz."""
        return self.peak_l, self.peak_r

    def _consume(self) -> None:
        while True:
            try:
                cmd = self.commands.get_nowait()
            except Empty:
                return
            if cmd[0] == "on":
                if len(self.voices) >= self.max_voices:
                    self.voices.pop(0)
                self.voices.append(Voice(cmd[1], cmd[2], self.parameters, self.sample_rate))
            elif cmd[0] == "off":
                for voice in self.voices:
                    if voice.note == cmd[1]:
                        voice.envelope.release()
            elif cmd[0] == "all_off":
                for voice in self.voices:
                    voice.envelope.release()
            else:
                self.parameters = replace(self.parameters, **{cmd[1]: cmd[2]})

    def _store_analysis(self, audio: np.ndarray) -> None:
        mono = audio.mean(axis=1)
        amount, size = len(mono), len(self.analysis_buffer)
        if amount >= size:
            self.analysis_buffer[:] = mono[-size:]
            self.analysis_position = 0
        else:
            end = self.analysis_position + amount
            if end <= size:
                self.analysis_buffer[self.analysis_position:end] = mono
            else:
                split = size - self.analysis_position
                self.analysis_buffer[self.analysis_position:] = mono[:split]
                self.analysis_buffer[:end % size] = mono[split:]
            self.analysis_position = end % size

        wave_size = len(self.waveform_buffer)
        if amount >= wave_size:
            self.waveform_buffer[:] = mono[-wave_size:]
            self.waveform_position = 0
        else:
            wave_end = self.waveform_position + amount
            if wave_end <= wave_size:
                self.waveform_buffer[self.waveform_position:wave_end] = mono
            else:
                split = wave_size - self.waveform_position
                self.waveform_buffer[self.waveform_position:] = mono[:split]
                self.waveform_buffer[:wave_end % wave_size] = mono[split:]
            self.waveform_position = wave_end % wave_size

    def spectrum(self) -> np.ndarray:
        """Copia segura del último bloque FFT, en dB, para la interfaz."""
        samples = np.roll(self.analysis_buffer, -self.analysis_position) * np.hanning(len(self.analysis_buffer))
        return 20 * np.log10(np.maximum(np.abs(np.fft.rfft(samples)), 1e-7))

    def waveform(self) -> np.ndarray:
        """Últimos 2048 samples mono, ordenados para dibujar el osciloscopio."""
        return np.roll(self.waveform_buffer, -self.waveform_position).copy()

    def render(self, frames: int) -> np.ndarray:
        self._consume()
        p = self.parameters

        # Modulación multidimensional Super Knob (Yamaha MONTAGE Motion Control)
        sk = float(np.clip(p.super_knob, 0.0, 1.0))
        effective_cutoff = min(self.sample_rate * 0.42, p.cutoff * (1.0 + sk * 1.5))
        effective_res = min(0.92, p.resonance + sk * 0.22)
        effective_drive = min(0.85, p.drive + sk * 0.20)
        effective_delay_mix = min(0.70, p.delay_mix + sk * 0.30)
        effective_reverb_mix = min(0.75, p.reverb_mix + sk * 0.25)

        audio = np.zeros((frames, 2), np.float32)
        vibrato = np.sin(2 * np.pi * (self.lfo_phase + p.vibrato_rate * np.arange(frames) / self.sample_rate))
        self.lfo_phase = float((self.lfo_phase + p.vibrato_rate * frames / self.sample_rate) % 1)

        for voice in self.voices:
            audio += voice.render(frames, p, self.sample_rate, vibrato, sk)

        self.voices = [voice for voice in self.voices if not voice.envelope.done]

        # 1. Filtro Resonante de 2 polos
        audio = self.filter.process(audio, effective_cutoff, effective_res)

        # 2. Drive / Saturación Armónica Analógica
        if effective_drive > 0.001:
            audio = apply_drive(audio, effective_drive)

        # 3. Stereo Delay (Efecto de inserción MONTAGE)
        if effective_delay_mix > 0.001:
            audio = self.delay.process(audio, p.delay_time, p.delay_feedback, effective_delay_mix)

        # 4. Stereo Reverb Schroeder
        if effective_reverb_mix > 0.001:
            reverb_params = replace(p, reverb_mix=effective_reverb_mix)
            audio = self.reverb.process(audio, reverb_params)

        # 5. Master Gain y Limitador suave
        audio = np.tanh(audio * p.master_gain).astype(np.float32)

        # Registro para vúmetro estéreo
        if frames > 0:
            self.peak_l = float(np.max(np.abs(audio[:, 0])))
            self.peak_r = float(np.max(np.abs(audio[:, 1])))
        else:
            self.peak_l = self.peak_r = 0.0

        self._store_analysis(audio)
        return audio
