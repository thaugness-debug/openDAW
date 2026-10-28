import css from "./Dashboard.sass?inline"
import {Lifecycle} from "@opendaw/lib-std"
import {createElement} from "@opendaw/lib-jsx"
import {StudioService} from "@/service/StudioService.ts"
import {Html} from "@opendaw/lib-dom"
import {Resources} from "@/ui/dashboard/Resources"
import {IntroTiles} from "@/ui/dashboard/IntroTiles"
import {ActionButtons} from "@/ui/dashboard/ActionButtons"
import {Backup} from "@/ui/dashboard/Backup"
import {Sponsors} from "@/ui/dashboard/Sponsors"
import {Contributors} from "@/ui/dashboard/Contributors"
import {SampleProviders} from "@/ui/dashboard/SampleProviders"
import {HelpFeedback} from "@/ui/dashboard/HelpFeedback"
import {Links} from "@/ui/dashboard/Links"

const className = Html.adoptStyleSheet(css, "Dashboard")

type Construct = {
    lifecycle: Lifecycle
    service: StudioService
}

export const Dashboard = ({lifecycle, service}: Construct) => (
    <div className={className}>
        <div className="intro">
            <header className="hero">
                <h1>Dropverket</h1>
                <div className="tagline">Lag din egen festival-låt</div>
            </header>
            <ActionButtons lifecycle={lifecycle} service={service}/>
        </div>
        <div className="main">
            <div className="panel">
                <Resources lifecycle={lifecycle} service={service}/>
            </div>
            <div className="rail advanced-only">
                <HelpFeedback/>
                <Backup service={service}/>
                <Links/>
                <Sponsors/>
                <SampleProviders/>
                <Contributors/>
            </div>
        </div>
        <div className="advanced-only">
            <IntroTiles/>
        </div>
    </div>
)