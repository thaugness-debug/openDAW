import {DefaultObservableValue, tryCatch} from "@opendaw/lib-std"

export namespace SimpleMode {
    const StorageKey = "dropverket-simple-mode"
    const readStored = (): boolean => {
        const result = tryCatch(() => localStorage.getItem(StorageKey))
        return result.status === "success" ? result.value !== "false" : true
    }
    export const enabled = new DefaultObservableValue<boolean>(readStored())
    enabled.catchupAndSubscribe(owner => {
        const value = owner.getValue()
        document.documentElement.classList.toggle("simple-mode", value)
        tryCatch(() => localStorage.setItem(StorageKey, String(value)))
    })
}
