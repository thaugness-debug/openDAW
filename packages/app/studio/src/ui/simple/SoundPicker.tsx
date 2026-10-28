import css from "./SoundPicker.sass?inline"
import {Color, isAbsent, Lifecycle} from "@opendaw/lib-std"
import {PPQN} from "@opendaw/lib-dsp"
import {createElement} from "@opendaw/lib-jsx"
import {Html} from "@opendaw/lib-dom"
import {Colors, IconSymbol} from "@opendaw/studio-enums"
import type {StudioService} from "@/service/StudioService"
import {Icon} from "@/ui/components/Icon"
import {CreateTrack} from "@/ui/browse/CreateTrackButtons"
import {StarterSounds} from "@/ui/simple/StarterSounds"

const className = Html.adoptStyleSheet(css, "SoundPicker")

type Sound = {
    readonly title: string
    readonly subtitle: string
    readonly icon: IconSymbol
    readonly color: Color
    readonly kind?: StarterSounds.Kind
}

const Sounds: ReadonlyArray<Sound> = [
    {title: "Trommer", subtitle: "House-beat (909)", icon: IconSymbol.DrumSet, color: Colors.orange, kind: "drums909"},
    {title: "Trommer", subtitle: "808-beat", icon: IconSymbol.DrumSet, color: Colors.orange, kind: "drums808"},
    {title: "Akkorder", subtitle: "Supersaw", icon: IconSymbol.Piano, color: Colors.green, kind: "supersaw"},
    {title: "Akkorder", subtitle: "Myk pad", icon: IconSymbol.Piano, color: Colors.green, kind: "pad"},
    {title: "Bass", subtitle: "House-bass", icon: IconSymbol.BassGuitar, color: Colors.purple, kind: "bass"},
    {title: "Melodi", subtitle: "Pluck", icon: IconSymbol.Note, color: Colors.red, kind: "pluck"},
    {title: "Melodi", subtitle: "Supersaw-lead", icon: IconSymbol.Note, color: Colors.red, kind: "lead"},
    {title: "Stemme", subtitle: "Ta opp sang", icon: IconSymbol.Microphone, color: Colors.blue}
]

const addSound = async (service: StudioService, sound: Sound): Promise<void> => {
    if (!service.hasProfile) {await service.newProject()}
    const {kind} = sound
    if (isAbsent(kind)) {
        CreateTrack.audioTrack(service)
        return
    }
    const {project} = service
    const start = Math.floor(project.engine.position.getValue() / PPQN.Bar) * PPQN.Bar
    project.editing.modify(() => {
        const regionBox = StarterSounds.create(project, kind, start)
        project.regionSelection.deselectAll()
        project.selection.select(regionBox)
        project.userEditingManager.timeline.edit(regionBox)
    })
}

export const SoundPicker = ({service}: { lifecycle: Lifecycle, service: StudioService }): HTMLElement => (
    <div className={className}>
        <h4>Velg en lyd. Du får et spor med noe ferdig å spille på, som du kan endre i piano rollen.</h4>
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
        <h4>Flere lyder, loops og effekter finner du under «Samples» rett nedenfor. Dra dem inn i låta.</h4>
    </div>
)
