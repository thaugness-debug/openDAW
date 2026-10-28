import css from "./SoundPicker.sass?inline"
import {Color, isAbsent, Lifecycle, RuntimeNotifier, UUID} from "@opendaw/lib-std"
import {Promises} from "@opendaw/lib-runtime"
import {createElement} from "@opendaw/lib-jsx"
import {Html} from "@opendaw/lib-dom"
import {Colors, IconSymbol} from "@opendaw/studio-enums"
import {InstrumentFactories} from "@opendaw/studio-adapters"
import type {StudioService} from "@/service/StudioService"
import {Icon} from "@/ui/components/Icon"
import {PresetApplication} from "@/ui/browse/PresetApplication"
import {SpotlightCreate} from "@/ui/spotlight/SpotlightCreate"
import {CreateTrack} from "@/ui/browse/CreateTrackButtons"

const className = Html.adoptStyleSheet(css, "SoundPicker")

type Sound = {
    readonly title: string
    readonly subtitle: string
    readonly icon: IconSymbol
    readonly color: Color
    readonly preset?: { readonly uuid: UUID.String, readonly device: InstrumentFactories.Keys }
}

const Sounds: ReadonlyArray<Sound> = [
    {title: "Trommer", subtitle: "House (909)", icon: IconSymbol.DrumSet, color: Colors.orange,
        preset: {uuid: "bdd30b37-2d5c-4c72-b72d-fe2ba65a193e", device: "Playfield"}},
    {title: "Trommer", subtitle: "808", icon: IconSymbol.DrumSet, color: Colors.orange,
        preset: {uuid: "7095d4f6-737d-42b7-b182-76d512b1ac8a", device: "Playfield"}},
    {title: "Bass", subtitle: "House-bass", icon: IconSymbol.BassGuitar, color: Colors.purple,
        preset: {uuid: "1fa2b765-e712-4300-bc88-a3f06479e613", device: "Neon"}},
    {title: "Bass", subtitle: "Reese (DnB)", icon: IconSymbol.BassGuitar, color: Colors.purple,
        preset: {uuid: "90b25d75-5029-4be4-811d-34a6bb198e43", device: "Apparat"}},
    {title: "Akkorder", subtitle: "Stor synth", icon: IconSymbol.Piano, color: Colors.green,
        preset: {uuid: "9f01ab16-9870-401f-9db6-a84e634c7a53", device: "Tubular"}},
    {title: "Akkorder", subtitle: "Myk pad", icon: IconSymbol.Piano, color: Colors.green,
        preset: {uuid: "fe0fb565-964d-4755-97ba-339d74abdef4", device: "Apparat"}},
    {title: "Piano", subtitle: "Ekte piano", icon: IconSymbol.Piano, color: Colors.cream,
        preset: {uuid: "d90f8d36-36e6-4bb4-bbf9-f2a2c365fa2a", device: "Soundfont"}},
    {title: "Melodi", subtitle: "Pluck", icon: IconSymbol.Note, color: Colors.red,
        preset: {uuid: "16b13127-6580-4f35-a7e9-18fd3a5b5d3f", device: "Vaporisateur"}},
    {title: "Melodi", subtitle: "Brass-lead", icon: IconSymbol.Note, color: Colors.red,
        preset: {uuid: "6023bee2-4a10-4604-b0a9-d3681294ef2f", device: "Neon"}},
    {title: "Stemme", subtitle: "Ta opp sang", icon: IconSymbol.Microphone, color: Colors.blue}
]

const addSound = async (service: StudioService, sound: Sound): Promise<void> => {
    if (!service.hasProfile) {await service.newProject()}
    const {preset} = sound
    if (isAbsent(preset)) {
        CreateTrack.audioTrack(service)
        return
    }
    const result = await Promises.tryCatch(PresetApplication.createNewAudioUnitFromInstrument(
        service, preset.uuid, preset.device, "stock", SpotlightCreate.anchorAfterEditing(service.project)))
    if (result.status === "rejected") {
        console.warn(result.error)
        RuntimeNotifier.notify({message: "Fikk ikke lastet lyden. Prøv igjen.", icon: "Warning"})
    }
}

export const SoundPicker = ({service}: { lifecycle: Lifecycle, service: StudioService }): HTMLElement => (
    <div className={className}>
        <h4>Velg en lyd for å lage et nytt spor</h4>
        <div className="tiles">
            {Sounds.map(sound => (
                <button className="tile"
                        onInit={element => element.style.setProperty("--tile-color", sound.color.toString())}
                        onclick={() => addSound(service, sound)}>
                    <Icon symbol={sound.icon}/>
                    <span className="title">{sound.title}</span>
                    <span className="subtitle">{sound.subtitle}</span>
                </button>
            ))}
        </div>
    </div>
)
