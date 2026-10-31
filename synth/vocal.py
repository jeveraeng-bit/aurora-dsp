"""Procesamiento vocal en tiempo real: detección de tono y corrección granular."""
from __future__ import annotations

import math
import numpy as np


SCALES = {
    "C mayor": (0, 2, 4, 5, 7, 9, 11),
    "C menor": (0, 2, 3, 5, 7, 8, 10),
    "C cromática": tuple(range(12)),
    "A menor": (0, 2, 3, 5, 7, 8, 10),
}


def hz_to_midi(hz: float) -> float:
    return 69 + 12 * math.log2(hz / 440)


def midi_to_hz(note: float) -> float:
    return 440 * 2 ** ((note - 69) / 12)


class PitchDetector:
    """Autocorrelación FFT estable para voz entre 75 y 750 Hz."""
    def __init__(self, sample_rate: int, size: int = 2048) -> None:
        self.sample_rate, self.size = sample_rate, size
        self.buffer = np.zeros(size, dtype=np.float32)
        self.position, self.counter = 0, 0
        self.window = np.hanning(size)

    def push(self, samples: np.ndarray) -> None:
        amount = len(samples)
        if amount >= self.size:
            self.buffer[:] = samples[-self.size:]
            self.position = 0
        else:
            end = self.position + amount
            if end <= self.size:
                self.buffer[self.position:end] = samples
            else:
                split = self.size - self.position
                self.buffer[self.position:] = samples[:split]
                self.buffer[:end % self.size] = samples[split:]
            self.position = end % self.size
        self.counter += amount

    def detect(self) -> tuple[float | None, float]:
        if self.counter < self.size:
            return None, 0.0
        frame = np.roll(self.buffer, -self.position).astype(np.float64)
        frame -= np.mean(frame)
        rms = float(np.sqrt(np.mean(frame * frame)))
        if rms < 0.004:
            return None, 0.0
        spectrum = np.fft.rfft(frame * self.window)
        correlation = np.fft.irfft(np.abs(spectrum) ** 2)
        low_lag, high_lag = int(self.sample_rate / 750), int(self.sample_rate / 75)
        section = correlation[low_lag:high_lag]
        lag = int(np.argmax(section)) + low_lag
        confidence = float(correlation[lag] / max(correlation[0], 1e-12))
        if confidence < 0.18:
            return None, confidence
        # Interpolación parabólica para una lectura menos temblorosa.
        if 1 <= lag < len(correlation) - 1:
            left, middle, right = correlation[lag - 1], correlation[lag], correlation[lag + 1]
            denominator = left - 2 * middle + right
            if abs(denominator) > 1e-12:
                lag += 0.5 * (left - right) / denominator
        return self.sample_rate / lag, confidence


class GranularPitchShifter:
    """Pitch-shifter de dos granos con latencia fija y ventanas cruzadas."""
    def __init__(self, sample_rate: int, grain_size: int = 1024) -> None:
        self.grain_size, self.hop = grain_size, grain_size // 2
        self.buffer = np.zeros(sample_rate, dtype=np.float32)
        self.write_position = self.absolute_position = 0
        self.latency = grain_size * 4
        self.grains: list[tuple[int, int]] = []  # (inicio de salida, inicio absoluto de fuente)

    def _read(self, absolute: float) -> float:
        position = absolute % len(self.buffer)
        left = int(position)
        fraction = position - left
        return float(self.buffer[left] * (1 - fraction) + self.buffer[(left + 1) % len(self.buffer)] * fraction)

    def process(self, samples: np.ndarray, ratio: float) -> np.ndarray:
        output = np.zeros_like(samples)
        ratio = float(np.clip(ratio, 0.72, 1.38))
        for i, sample in enumerate(samples):
            current = self.absolute_position
            self.buffer[self.write_position] = sample
            self.write_position = (self.write_position + 1) % len(self.buffer)
            if current % self.hop == 0:
                self.grains.append((current, current - self.latency))
            total = weight = 0.0
            next_grains = []
            for out_start, source_start in self.grains:
                age = current - out_start
                if age < self.grain_size:
                    window = math.sin(math.pi * (age + .5) / self.grain_size)
                    total += self._read(source_start + age * ratio) * window
                    weight += window
                    next_grains.append((out_start, source_start))
            self.grains = next_grains
            output[i] = total / weight if weight else 0.0
            self.absolute_position += 1
        return output


class VocalProcessor:
    """AutoTune educativo: tono detectado, escala elegida y cantidad de corrección."""
    def __init__(self, sample_rate: int) -> None:
        self.sample_rate = sample_rate
        self.detector, self.shifter = PitchDetector(sample_rate), GranularPitchShifter(sample_rate)
        self.scale_name, self.amount, self.mix = "C mayor", 0.82, 0.88
        self.detected_hz: float | None = None
        self.target_hz: float | None = None
        self._smoothed_ratio, self._since_detection = 1.0, 0

    def set_scale(self, scale_name: str) -> None:
        if scale_name in SCALES: self.scale_name = scale_name

    def nearest_scale_note(self, midi: float) -> float:
        allowed = SCALES[self.scale_name]
        candidates = [octave * 12 + degree for octave in range(-1, 12) for degree in allowed]
        return min(candidates, key=lambda candidate: abs(candidate - midi))

    def process(self, samples: np.ndarray) -> np.ndarray:
        self.detector.push(samples)
        self._since_detection += len(samples)
        if self._since_detection >= 768:
            self._since_detection = 0
            detected, confidence = self.detector.detect()
            if detected is not None and confidence > .2:
                self.detected_hz = detected
                self.target_hz = midi_to_hz(self.nearest_scale_note(hz_to_midi(detected)))
        ratio = 1.0
        if self.detected_hz and self.target_hz:
            raw_ratio = self.target_hz / self.detected_hz
            ratio = 1 + (raw_ratio - 1) * self.amount
        self._smoothed_ratio += .08 * (ratio - self._smoothed_ratio)
        corrected = self.shifter.process(samples, self._smoothed_ratio)
        return samples * (1 - self.mix) + corrected * self.mix
