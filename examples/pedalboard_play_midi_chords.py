"""Play chords imported from a MIDI file through a pedalboard VST instrument.

This script intentionally reuses PyTheory's MIDI importer so the harmony is
rebuilt as real ``pytheory.Chord`` objects, then copied into a fresh score and
played with the pedalboard engine.

Example:

    python examples/pedalboard_play_midi_chords.py ^
        --plugin "C:\\VST3\\YourInstrument.vst3"
"""

from __future__ import annotations

import argparse
from pathlib import Path

from pytheory import (
    Chord,
    PluginSpec,
    Score,
    play_score,
    set_engine,
)


DEFAULT_MIDI_PATH = Path(
    r"C:\Users\lssilva30\pessoal\code\free-midi-chords"
    r"\free-midi-progressions-20260314\Minor"
    r"\A - i iv VI v - Sad Hopeful.mid"
)


def _display_chord(chord: Chord) -> str:
    return chord.symbol or chord.identify() or str(chord)


def _choose_harmonic_part(score: Score):
    candidates = []
    for name, part in score.parts.items():
        chord_count = sum(isinstance(note.tone, Chord) for note in part.notes)
        note_count = sum(note.tone is not None for note in part.notes)
        if chord_count:
            candidates.append((chord_count, note_count, name, part))
    if not candidates:
        raise ValueError("No imported part contained chord objects.")
    candidates.sort(reverse=True)
    return candidates[0][3]


def _extract_chord_progression(imported: Score) -> list:
    part = _choose_harmonic_part(imported)
    progression = []
    for note in part.notes:
        if note.tone is None:
            progression.append(("rest", note.beats))
        elif isinstance(note.tone, Chord):
            progression.append(("chord", note.tone, note.beats, note.velocity))
    if not any(item[0] == "chord" for item in progression):
        raise ValueError("The selected MIDI part did not contain any chords.")
    return progression


def build_score_from_midi_chords(midi_path: Path, plugin_path: Path) -> tuple[Score, list[Chord]]:
    imported = Score.from_midi(str(midi_path))
    progression = _extract_chord_progression(imported)

    score = Score(str(imported.time_signature), bpm=imported.bpm)
    part = score.part(
        "progression",
        synth="midi_chords_vst",
        envelope="none",
        vst_instrument=PluginSpec(path=str(plugin_path)),
        volume=0.9,
    )

    chords = []
    for item in progression:
        if item[0] == "rest":
            _, beats = item
            part.rest(beats)
            continue
        _, chord, beats, velocity = item
        part.add(chord, beats, velocity=velocity)
        chords.append(chord)

    return score, chords


def main():
    parser = argparse.ArgumentParser(
        description="Play PyTheory chords imported from a MIDI file through a pedalboard VST3 instrument."
    )
    parser.add_argument(
        "--midi",
        type=Path,
        default=DEFAULT_MIDI_PATH,
        help=f"Path to the MIDI chord progression file. Default: {DEFAULT_MIDI_PATH}",
    )
    parser.add_argument(
        "--plugin",
        type=Path,
        required=True,
        help="Path to the VST3 instrument plugin to host with pedalboard.",
    )
    args = parser.parse_args()

    if not args.midi.exists():
        raise FileNotFoundError(f"MIDI file not found: {args.midi}")
    if not args.plugin.exists():
        raise FileNotFoundError(f"Plugin not found: {args.plugin}")

    score, chords = build_score_from_midi_chords(args.midi, args.plugin)

    print("Extracted PyTheory chords:")
    for index, chord in enumerate(chords, start=1):
        print(f"{index:>2}. {_display_chord(chord)}")

    set_engine("pedalboard")
    play_score(score, engine="pedalboard")


if __name__ == "__main__":
    main()
