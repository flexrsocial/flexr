package flexr.social.app.testing

import flexr.social.app.data.remote.dto.MyProfileDto
import flexr.social.app.data.remote.dto.PhotoDto
import flexr.social.app.data.remote.dto.ProfileDto

/**
 * Bausteine für Testdaten. Alles hat einen brauchbaren Vorgabewert, damit ein
 * Test nur die Felder nennen muss, um die es ihm geht — das hält die
 * Testfälle lesbar und übersteht neue Pflichtfelder in den DTOs.
 */

fun fotoDto(
    id: String = "foto-1",
    url: String = "https://cdn.example/foto.jpg",
    thumbUrl: String? = "https://cdn.example/foto-klein.jpg",
    position: Int = 0,
    status: String = "approved",
) = PhotoDto(id = id, url = url, thumbUrl = thumbUrl, position = position, status = status)

/** Kandidat im Swipe-Deck. */
fun profilDto(
    id: String,
    name: String = "Testperson",
    age: Int = 27,
    city: String = "Wien",
    gender: String = "frau",
    gym: String = "McFit — Laxenburger Straße 66, 1100 Wien",
    distanceKm: Int? = 0,
    photos: List<PhotoDto> = listOf(fotoDto(id = "$id-foto")),
) = ProfileDto(
    id = id,
    name = name,
    age = age,
    city = city,
    gender = gender,
    gym = gym,
    distanceKm = distanceKm,
    photos = photos,
)

/** Eigenes Profil. Radius und Gym sind die Stellschrauben der Umkreissuche. */
fun meinProfilDto(
    id: String = "ich",
    name: String = "Julian",
    gym: String = "McFit — Triester Straße 64, 1100",
    searchRadiusKm: Int = 20,
    plz: String = "1100",
    photos: List<PhotoDto> = listOf(fotoDto(id = "ich-foto")),
) = MyProfileDto(
    id = id,
    name = name,
    age = 30,
    city = "Wien",
    gender = "mann",
    gym = gym,
    plz = plz,
    birthdate = "1996-01-01",
    searchRadiusKm = searchRadiusKm,
    photos = photos,
)
