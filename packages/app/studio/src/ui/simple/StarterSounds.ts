import {asInstanceOf, byte, int, UUID} from "@opendaw/lib-std"
import {ClassicWaveform, PPQN} from "@opendaw/lib-dsp"
import {VoicingMode} from "@opendaw/studio-enums"
import {InstrumentFactories} from "@opendaw/studio-adapters"
import {
    AudioUnitBox, DattorroReverbDeviceBox, NoteRegionBox, TidalDeviceBox, TrackBox, VaporisateurDeviceBox
} from "@opendaw/studio-boxes"
import {EffectFactories, Project} from "@opendaw/studio-core"

export namespace StarterSounds {
    type Pad = { readonly note: byte, readonly uuid: string, readonly name: string, readonly duration: number }
    type Note = readonly [step: int, pitch: int, length: int, velocity: number]
    type Synth = {
        readonly waveforms: readonly [ClassicWaveform, ClassicWaveform]
        readonly volumes: readonly [number, number]
        readonly octaves: readonly [int, int]
        readonly unison: 1 | 3 | 5
        readonly detune: number
        readonly cutoff: number
        readonly resonance: number
        readonly filterEnvelope: number
        readonly attack: number
        readonly decay: number
        readonly sustain: number
        readonly release: number
        readonly mono: boolean
    }
    type SynthKind = "supersaw" | "pad" | "bass" | "pluck" | "lead"
    export type Kind = "drums909" | "drums808" | SynthKind

    const Drums909: ReadonlyArray<Pad> = [
        {note: 36, uuid: "fa1ce6f2-c354-5d3b-880d-c986f76a07f3", name: "Festival Kick", duration: 0.45},
        {note: 37, uuid: "2808b84d-904c-5b22-ac38-02358c68bbfb", name: "909 Rim", duration: 0.1181},
        {note: 38, uuid: "e9ff3168-5ca5-5770-a4e2-b3ab17f5d070", name: "909 Snare", duration: 0.2894},
        {note: 39, uuid: "6c5128e2-5ac7-5cf3-8c77-b0035962d7fe", name: "Festival Clap", duration: 0.6},
        {note: 42, uuid: "0bb4f8f6-1edb-52ad-a571-2a3cece649d1", name: "909 Closed Hat", duration: 0.1057},
        {note: 46, uuid: "ed12c724-67f0-5ac6-82cb-ef28ee040514", name: "909 Open Hat", duration: 0.5474},
        {note: 49, uuid: "afd19ba6-7ec5-5bf6-a4d2-e31eb893abbd", name: "909 Crash", duration: 0.9278},
        {note: 51, uuid: "acd8fa2f-441a-5375-b7e4-ad996329fe23", name: "909 Ride", duration: 2.1567},
        {note: 70, uuid: "9700177f-532a-5591-806e-4d9a609278f9", name: "Shaker", duration: 0.039}
    ]
    const Drums808: ReadonlyArray<Pad> = [
        {note: 36, uuid: "32f1e917-511c-577e-b05d-22eab754fd20", name: "808 Kick", duration: 0.4986},
        {note: 38, uuid: "b6c9f3f6-b8b0-5f08-9886-7156e1537bef", name: "808 Snare", duration: 0.2296},
        {note: 39, uuid: "7804c1be-365d-5b9d-8713-8999becc8e5e", name: "808 Clap", duration: 0.3491},
        {note: 42, uuid: "ca6fd55e-ba6b-56ea-bd23-46a0b56d1128", name: "808 Closed Hat", duration: 0.1152},
        {note: 46, uuid: "0693b74f-d5e2-5d21-91a2-0482094b537b", name: "808 Open Hat", duration: 0.406},
        {note: 56, uuid: "5aa031bf-4b5f-5c0b-bbc7-ab047e40b0d3", name: "Cowbell", duration: 1.1355},
        {note: 75, uuid: "48f9aa57-faa9-5223-a8ee-a0cc0ae9cdaf", name: "Claves", duration: 0.0597}
    ]

    const pattern = (steps: string, pitch: int, velocity: number): ReadonlyArray<Note> =>
        Array.from(steps).flatMap((char, step): ReadonlyArray<Note> =>
            char === "x" ? [[step, pitch, 1, velocity]] : char === "o" ? [[step, pitch, 1, velocity * 0.6]] : [])
    const HouseBeat: ReadonlyArray<Note> = [
        ...pattern("x---x---x---x---", 36, 1.0),
        ...pattern("----x-------x---", 39, 0.9),
        ...pattern("--x---x---x---x-", 46, 0.7),
        ...pattern("x-o-x-o-x-o-x-o-", 42, 0.45),
        ...pattern("-o-o-o-o-o-o-o-o", 70, 0.6)
    ]
    const TrapBeat: ReadonlyArray<Note> = [
        ...pattern("x---x---x---x---", 36, 1.0),
        ...pattern("----x-------x---", 39, 0.9),
        ...pattern("xoxoxoxoxoxoxoxo", 42, 0.6),
        ...pattern("--x---x---x---x-", 46, 0.5)
    ]
    const Progression: ReadonlyArray<ReadonlyArray<int>> = [[57, 60, 64, 69], [53, 57, 60, 65], [55, 60, 64, 67], [55, 59, 62, 67]]
    const BassRoots: ReadonlyArray<int> = [45, 41, 48, 43]
    const MinorScale: ReadonlyArray<int> = [0, 2, 3, 5, 7, 8, 10]
    const MelodyRows: ReadonlyArray<readonly [int, int, int]> = [
        [0, 4, 2], [3, 7, 1], [6, 6, 2], [10, 4, 2], [14, 2, 2], [16, 5, 2], [19, 7, 1], [22, 9, 2], [26, 7, 2],
        [30, 5, 2], [32, 4, 2], [35, 6, 1], [38, 9, 2], [42, 6, 2], [46, 4, 2], [48, 3, 2], [51, 6, 1], [54, 8, 2],
        [58, 6, 3], [62, 1, 2]]
    const rowToPitch = (row: int, base: int): int =>
        base + MinorScale[row % 7] + 12 * Math.floor(row / 7)
    const chords = (length: int, steps: ReadonlyArray<int>): ReadonlyArray<Note> =>
        Progression.flatMap((pitches, bar) => steps.flatMap(step =>
            pitches.map((pitch): Note => [bar * 16 + step, pitch, length, 0.85])))
    const melody = (base: int): ReadonlyArray<Note> =>
        MelodyRows.map(([step, row, length]): Note => [step, rowToPitch(row, base), length, 0.9])
    const offbeatBass: ReadonlyArray<Note> =
        BassRoots.flatMap((root, bar) => [2, 6, 10, 14].map((step): Note => [bar * 16 + step, root, 2, 0.95]))

    const saw = ClassicWaveform.saw
    const square = ClassicWaveform.square
    const Synths: Record<SynthKind, Synth> = {
        supersaw: {waveforms: [saw, saw], volumes: [-6, -14], octaves: [0, 1], unison: 5, detune: 28, cutoff: 7000,
            resonance: 0.5, filterEnvelope: 0, attack: 0.008, decay: 0.4, sustain: 0.9, release: 0.35, mono: false},
        pad: {waveforms: [saw, saw], volumes: [-8, -18], octaves: [0, 1], unison: 5, detune: 14, cutoff: 1800,
            resonance: 0.4, filterEnvelope: 0, attack: 0.7, decay: 1, sustain: 1, release: 1.4, mono: false},
        bass: {waveforms: [saw, square], volumes: [-6, -10], octaves: [0, -1], unison: 1, detune: 10, cutoff: 380,
            resonance: 1.2, filterEnvelope: 0.45, attack: 0.003, decay: 0.16, sustain: 0.7, release: 0.06, mono: true},
        pluck: {waveforms: [saw, saw], volumes: [-6, -12], octaves: [0, 0], unison: 3, detune: 12, cutoff: 700,
            resonance: 1.5, filterEnvelope: 0.65, attack: 0.002, decay: 0.28, sustain: 0.0, release: 0.2, mono: false},
        lead: {waveforms: [saw, saw], volumes: [-6, -12], octaves: [0, 1], unison: 5, detune: 22, cutoff: 6500,
            resonance: 0.6, filterEnvelope: 0, attack: 0.005, decay: 0.3, sustain: 0.85, release: 0.15, mono: false}
    }

    const applySynth = (box: VaporisateurDeviceBox, synth: Synth): void => {
        const oscillators = box.oscillators.fields()
        oscillators.forEach((oscillator, index) => {
            oscillator.waveform.setValue(synth.waveforms[index])
            oscillator.volume.setValue(synth.volumes[index])
            oscillator.octave.setValue(synth.octaves[index])
        })
        box.unisonCount.setValue(synth.unison)
        box.unisonDetune.setValue(synth.detune)
        box.unisonStereo.setValue(1.0)
        box.cutoff.setValue(synth.cutoff)
        box.resonance.setValue(synth.resonance)
        box.filterEnvelope.setValue(synth.filterEnvelope)
        box.filterOrder.setValue(2)
        box.attack.setValue(synth.attack)
        box.decay.setValue(synth.decay)
        box.sustain.setValue(synth.sustain)
        box.release.setValue(synth.release)
        box.voicingMode.setValue(synth.mono ? VoicingMode.Monophonic : VoicingMode.Polyphonic)
    }

    const addReverb = (project: Project, unit: AudioUnitBox, index: int, wet: number): void => {
        const box = asInstanceOf(EffectFactories.AudioNamed.DattorroReverb.create(project, unit.audioEffects, index),
            DattorroReverbDeviceBox)
        box.wet.setValue(wet)
        box.decay.setValue(0.82)
    }

    const addPump = (project: Project, unit: AudioUnitBox, index: int, depth: number): void => {
        const box = asInstanceOf(EffectFactories.AudioNamed.Tidal.create(project, unit.audioEffects, index), TidalDeviceBox)
        box.depth.setValue(depth)
    }

    const addRegion = (project: Project, trackBox: TrackBox, start: number, bars: int, loopBars: int,
                       notes: ReadonlyArray<Note>, name: string): NoteRegionBox => {
        const {api} = project
        const regionBox = api.createNoteRegion({
            trackBox, position: start, duration: bars * PPQN.Bar, loopDuration: loopBars * PPQN.Bar, name
        })
        notes.forEach(([step, pitch, length, velocity]) => api.createNoteEvent({
            owner: regionBox, position: step * PPQN.SemiQuaver, duration: length * PPQN.SemiQuaver * 0.95,
            pitch, velocity
        }))
        return regionBox
    }

    const pads = (kit: ReadonlyArray<Pad>): InstrumentFactories.PlayfieldAttachment =>
        kit.map(({note, uuid, name, duration}) => ({
            note, uuid: UUID.parse(uuid), name, durationInSeconds: duration, exclude: false
        }))

    export const create = (project: Project, kind: Kind, start: number): NoteRegionBox => {
        const {api, rootBox, timelineBox} = project
        if (rootBox.audioUnits.pointerHub.incoming().length <= 1) {timelineBox.bpm.setValue(128)}
        if (kind === "drums909" || kind === "drums808") {
            const is909 = kind === "drums909"
            const {trackBox} = api.createInstrument(InstrumentFactories.Playfield, {
                name: is909 ? "Trommer 909" : "Trommer 808", attachment: pads(is909 ? Drums909 : Drums808)
            })
            return addRegion(project, trackBox, start, 4, 1, is909 ? HouseBeat : TrapBeat, "Beat")
        }
        const names: Record<SynthKind, string> = {
            supersaw: "Supersaw-akkorder", pad: "Myk pad", bass: "House-bass", pluck: "Pluck-melodi", lead: "Supersaw-lead"
        }
        const {audioUnitBox, instrumentBox, trackBox} = api.createInstrument(InstrumentFactories.Vaporisateur,
            {name: names[kind]})
        applySynth(asInstanceOf(instrumentBox, VaporisateurDeviceBox), Synths[kind])
        switch (kind) {
            case "supersaw":
                addPump(project, audioUnitBox, 0, 0.6)
                addReverb(project, audioUnitBox, 1, -12)
                return addRegion(project, trackBox, start, 4, 4, chords(16, [0]), "Akkorder")
            case "pad":
                addReverb(project, audioUnitBox, 0, -8)
                return addRegion(project, trackBox, start, 4, 4, chords(16, [0]), "Pad")
            case "bass":
                addPump(project, audioUnitBox, 0, 0.35)
                return addRegion(project, trackBox, start, 4, 4, offbeatBass, "Bass")
            case "pluck":
                addReverb(project, audioUnitBox, 0, -10)
                return addRegion(project, trackBox, start, 4, 4, melody(69), "Melodi")
            case "lead":
                addReverb(project, audioUnitBox, 0, -12)
                return addRegion(project, trackBox, start, 4, 4, melody(69), "Lead")
        }
    }
}
