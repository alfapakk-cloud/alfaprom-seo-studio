import Foundation

// Launch only. URLs never supply commands, paths, credentials, or article content.
func acceptsHelperURL(_ url: URL) -> Bool {
    guard let c = URLComponents(url: url, resolvingAgainstBaseURL: false) else { return false }
    return c.scheme?.lowercased() == "alfaprom-seo"
        && c.host?.lowercased() == "start"
        && (c.path.isEmpty || c.path == "/")
        && c.user == nil && c.password == nil && c.port == nil
        && c.query == nil && c.fragment == nil
}
