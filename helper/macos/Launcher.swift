import AppKit
import Foundation

@MainActor
final class HelperDelegate: NSObject, NSApplicationDelegate {
    private var statusItem: NSStatusItem!
    private let stateItem = NSMenuItem(title: "Помощник остановлен", action: nil, keyEquivalent: "")
    private var process: Process?
    private var receivedURL = false
    private var starting = false
    private var quitting = false

    func applicationDidFinishLaunching(_ notification: Notification) {
        statusItem = NSStatusBar.system.statusItem(withLength: NSStatusItem.variableLength)
        statusItem.button?.title = "α SEO"
        statusItem.button?.toolTip = "Помощник АЛЬФАПРОМ"
        let menu = NSMenu()
        menu.addItem(stateItem)
        menu.addItem(NSMenuItem.separator())
        let start = NSMenuItem(title: "Запустить помощника", action: #selector(startFromMenu), keyEquivalent: "")
        start.target = self
        menu.addItem(start)
        let stop = NSMenuItem(title: "Остановить помощника", action: #selector(stopFromMenu), keyEquivalent: "")
        stop.target = self
        menu.addItem(stop)
        let quit = NSMenuItem(title: "Завершить работу", action: #selector(quitFromMenu), keyEquivalent: "q")
        quit.target = self
        menu.addItem(quit)
        statusItem.menu = menu
        // Direct app launch starts the helper. A URL launch is validated first.
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.4) { [weak self] in
            guard let self = self, !self.receivedURL else { return }
            self.startHelper()
        }
    }

    func application(_ application: NSApplication, open urls: [URL]) {
        receivedURL = true
        if urls.contains(where: acceptsHelperURL) { startHelper() }
    }

    func applicationShouldHandleReopen(_ sender: NSApplication, hasVisibleWindows flag: Bool) -> Bool {
        startHelper()
        return false
    }

    @objc private func startFromMenu() { startHelper() }
    @objc private func stopFromMenu() {
        guard let p = process, p.isRunning else {
            stateItem.title = "Свой процесс помощника не запущен"
            return
        }
        stateItem.title = "Останавливаю помощника…"
        p.terminate()
    }
    @objc private func quitFromMenu() { NSApplication.shared.terminate(nil) }

    private func startHelper() {
        if process?.isRunning == true { stateItem.title = "Помощник работает"; return }
        if starting { return }
        starting = true
        stateItem.title = "Запускаю помощника…"
        var request = URLRequest(url: URL(string: "http://127.0.0.1:8766/health")!)
        request.timeoutInterval = 1
        URLSession.shared.dataTask(with: request) { [weak self] data, response, _ in
            let json = data.flatMap { try? JSONSerialization.jsonObject(with: $0) as? [String: Any] }
            let existing = (response as? HTTPURLResponse)?.statusCode == 200
                && json?["service"] as? String == "alfaprom-seo-helper"
            DispatchQueue.main.async {
                guard let self = self else { return }
                if existing {
                    self.starting = false
                    self.stateItem.title = "Помощник уже работает"
                } else { self.spawnHelper() }
            }
        }.resume()
    }

    private func spawnHelper() {
        guard let resources = Bundle.main.resourceURL else { fail("Не найдены файлы помощника."); return }
        let script = resources.appendingPathComponent("helper/alfaprom_helper.py")
        guard FileManager.default.fileExists(atPath: script.path) else { fail("Не найден модуль помощника."); return }
        let p = Process()
        p.executableURL = URL(fileURLWithPath: "/usr/bin/python3")
        p.arguments = [script.path]
        p.currentDirectoryURL = resources
        p.standardOutput = FileHandle.nullDevice
        p.standardError = FileHandle.nullDevice
        p.terminationHandler = { [weak self] finished in
            DispatchQueue.main.async {
                guard let self = self else { return }
                self.process = nil
                self.starting = false
                if !self.quitting {
                    self.stateItem.title = finished.terminationStatus == 0 ? "Помощник остановлен" : "Не удалось запустить помощника"
                }
            }
        }
        do {
            try p.run()
            process = p
            starting = false
            stateItem.title = "Помощник работает"
        } catch { fail("Не удалось запустить Python: \(error.localizedDescription)") }
    }

    private func fail(_ message: String) {
        starting = false
        stateItem.title = "Ошибка запуска"
        let alert = NSAlert()
        alert.messageText = "Помощник АЛЬФАПРОМ"
        alert.informativeText = message
        alert.runModal()
    }

    func applicationWillTerminate(_ notification: Notification) {
        quitting = true
        if let p = process, p.isRunning { p.terminate() }
    }
}

@main
struct HelperLauncher {
    @MainActor static func main() {
        let app = NSApplication.shared
        let delegate = HelperDelegate()
        app.delegate = delegate
        app.setActivationPolicy(.accessory)
        app.run()
    }
}
