import Foundation

@main struct HelperURLTests {
    static func main() {
        let accepted = ["alfaprom-seo://start", "alfaprom-seo://start/", "ALFAPROM-SEO://START"]
        let rejected = ["https://start", "alfaprom-seo://stop", "alfaprom-seo://start/exec", "alfaprom-seo://start?cmd=whoami", "alfaprom-seo://start#secret", "alfaprom-seo://user@start", "alfaprom-seo://start:123", "alfaprom-seo://start/%2e%2e", "alfaprom-seo://start?", "alfaprom-seo://start#"]
        for value in accepted { precondition(acceptsHelperURL(URL(string: value)!), "Rejected: \(value)") }
        for value in rejected { precondition(!acceptsHelperURL(URL(string: value)!), "Accepted: \(value)") }
        print("13 URL-handler cases passed")
    }
}
