import Foundation
import Security

/// Minimaler Keychain-Zugriff für den Sitzungs-Token.
///
/// Der Token ist ein Anmeldegeheimnis und gehört deshalb nicht in die
/// `UserDefaults` — das ist der Unterschied zur Android-Fassung, die alles in
/// einem DataStore hält. `kSecAttrAccessibleAfterFirstUnlock` erlaubt dem
/// Hintergrundabgleich für neue Nachrichten den Zugriff, ohne dass das Gerät
/// gerade entsperrt sein muss.
enum Keychain {

    static func string(for key: String) -> String? {
        var query = baseQuery(key)
        query[kSecReturnData as String] = true
        query[kSecMatchLimit as String] = kSecMatchLimitOne

        var item: CFTypeRef?
        guard SecItemCopyMatching(query as CFDictionary, &item) == errSecSuccess,
              let data = item as? Data
        else { return nil }
        return String(data: data, encoding: .utf8)
    }

    static func set(_ value: String?, for key: String) {
        guard let value, let data = value.data(using: .utf8) else {
            remove(key)
            return
        }

        let query = baseQuery(key)
        let attributes: [String: Any] = [
            kSecValueData as String: data,
            kSecAttrAccessible as String: kSecAttrAccessibleAfterFirstUnlock,
        ]

        let status = SecItemUpdate(query as CFDictionary, attributes as CFDictionary)
        if status == errSecItemNotFound {
            var insert = query
            insert.merge(attributes) { current, _ in current }
            SecItemAdd(insert as CFDictionary, nil)
        }
    }

    static func remove(_ key: String) {
        SecItemDelete(baseQuery(key) as CFDictionary)
    }

    private static func baseQuery(_ key: String) -> [String: Any] {
        [
            kSecClass as String: kSecClassGenericPassword,
            kSecAttrService as String: "social.flexr.app",
            kSecAttrAccount as String: key,
        ]
    }
}
