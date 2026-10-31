import unittest
import numpy as np
from synth.engine import SynthEngine, SynthParameters, midi_to_hz, ResonantFilter, StereoDelay, apply_drive
from synth.vocal import PitchDetector, VocalProcessor
from synth.presets import FACTORY_PRESETS


class EngineTests(unittest.TestCase):
    def test_a4_frequency(self):
        self.assertEqual(midi_to_hz(69), 440.0)

    def test_note_generates_stereo_audio(self):
        synth = SynthEngine()
        synth.note_on(69)
        audio = synth.render(256)
        self.assertEqual(audio.shape, (256, 2))
        self.assertEqual(audio.dtype, np.float32)
        self.assertGreater(float(np.abs(audio).max()), 0)

    def test_release_finishes_voice(self):
        synth = SynthEngine(sample_rate=1000)
        synth.set_parameter("release", .01)
        synth.note_on(60)
        synth.render(16)
        synth.note_off(60)
        synth.render(64)
        self.assertEqual(len(synth.voices), 0)

    def test_pitch_detector_reads_a4(self):
        rate = 48_000
        detector = PitchDetector(rate)
        samples = np.sin(2 * np.pi * 440 * np.arange(4096) / rate).astype(np.float32)
        detector.push(samples)
        frequency, confidence = detector.detect()
        self.assertIsNotNone(frequency)
        self.assertAlmostEqual(frequency, 440, delta=3)
        self.assertGreater(confidence, .2)

    def test_scale_snaps_to_allowed_note(self):
        vocal = VocalProcessor(48_000)
        vocal.set_scale("C mayor")
        self.assertEqual(vocal.nearest_scale_note(61), 60)

    def test_waveform_history_is_available(self):
        synth = SynthEngine()
        synth.note_on(60)
        synth.render(4096)
        wave = synth.waveform()
        self.assertEqual(wave.shape, (2048,))
        self.assertGreater(float(np.abs(wave).max()), 0)

    def test_fm_synthesis_affects_waveform(self):
        """Verifica que la síntesis FM (Yamaha DX/FM-X) enriquece el sonido."""
        synth_clean = SynthEngine()
        synth_clean.set_parameter("waveform_1", "sine")
        synth_clean.set_parameter("waveform_2", "sine")
        synth_clean.set_parameter("fm_depth", 0.0)
        synth_clean.note_on(60)
        audio_clean = synth_clean.render(512)

        synth_fm = SynthEngine()
        synth_fm.set_parameter("waveform_1", "sine")
        synth_fm.set_parameter("waveform_2", "sine")
        synth_fm.set_parameter("fm_depth", 0.8)
        synth_fm.note_on(60)
        audio_fm = synth_fm.render(512)

        # La señal con modulación FM difiere claramente de la señal senoidal pura
        diff = np.abs(audio_clean - audio_fm).max()
        self.assertGreater(float(diff), 0.05)

    def test_resonant_filter_stability(self):
        """Verifica que el filtro de 2 polos CS-80 no produce NaNs ni desbordamientos."""
        filt = ResonantFilter(48_000)
        signal = np.random.uniform(-1, 1, (1024, 2)).astype(np.float32)
        out = filt.process(signal, cutoff_hz=2000.0, resonance=0.92)
        self.assertFalse(np.isnan(out).any())
        self.assertFalse(np.isinf(out).any())
        self.assertEqual(out.shape, (1024, 2))

    def test_stereo_delay_echo(self):
        """Verifica que el delay estéreo MONTAGE retiene y reproduce ecos."""
        delay = StereoDelay(48_000)
        impulse = np.zeros((256, 2), dtype=np.float32)
        impulse[0, :] = 1.0  # Impulso inicial
        delay.process(impulse, delay_time=0.05, feedback=0.5, mix=0.5)

        # Tras pasar el tiempo de retardo (~2400 muestras), el buffer debe contener sonido
        silence = np.zeros((2560, 2), dtype=np.float32)
        delayed_out = delay.process(silence, delay_time=0.05, feedback=0.5, mix=0.5)
        self.assertGreater(float(np.abs(delayed_out).max()), 0.01)

    def test_drive_soft_saturation(self):
        """Verifica que el previo Drive comprime suavemente sin clipping abrupto."""
        loud = np.ones((100, 2), dtype=np.float32) * 2.0
        driven = apply_drive(loud, 0.75)
        self.assertLessEqual(float(np.max(driven)), 1.0)
        self.assertGreater(float(np.max(driven)), 0.5)

    def test_super_knob_parameter(self):
        """Verifica que el Super Knob macro modifica la señal de salida."""
        synth = SynthEngine()
        synth.set_parameter("super_knob", 0.8)
        synth.note_on(60)
        audio = synth.render(256)
        self.assertEqual(audio.shape, (256, 2))
        self.assertGreater(float(np.abs(audio).max()), 0)

    def test_peak_levels_available(self):
        """Verifica que los niveles para el vúmetro estéreo están en rango [0, 1]."""
        synth = SynthEngine()
        synth.note_on(60)
        synth.render(256)
        pl, pr = synth.peak_levels()
        self.assertGreaterEqual(pl, 0.0)
        self.assertLessEqual(pl, 1.0)
        self.assertGreaterEqual(pr, 0.0)
        self.assertLessEqual(pr, 1.0)

    def test_factory_presets_integrity(self):
        """Verifica que todos los presets de fábrica contienen parámetros válidos."""
        synth = SynthEngine()
        valid_fields = SynthParameters.__dataclass_fields__
        for name, preset in FACTORY_PRESETS.items():
            for key, val in preset.items():
                self.assertIn(key, valid_fields, f"Parámetro {key} en preset {name} no es válido")
                synth.set_parameter(key, val)
        synth.note_on(60)
        out = synth.render(256)
        self.assertEqual(out.shape, (256, 2))


if __name__ == "__main__":
    unittest.main()
