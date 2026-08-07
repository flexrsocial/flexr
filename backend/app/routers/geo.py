from fastapi import APIRouter, HTTPException, Path

from ..geo import city_for_plz
from ..schemas import PlzLookupOut

router = APIRouter(prefix="/api/geo", tags=["geo"])


@router.get("/plz/{plz}", response_model=PlzLookupOut)
def lookup_plz(plz: str = Path(pattern=r"^\d{4}$")):
    """Amtlicher Ortsname zu einer österreichischen PLZ (öffentlich, wird schon
    bei der Registrierung gebraucht).

    Früher haben Web, Android und iOS dafür jeweils selbst openplzapi.org
    abgefragt. Das war aus zwei Gründen eine schlechte Idee: der Dienst hat
    Requests mit OkHttp-User-Agent mit HTTP 418 abgewiesen (die Android-App
    konnte dadurch überhaupt keine PLZ mehr auflösen), und seine Ortschaftsliste
    ist seitenweise begrenzt, sodass die Häufigkeits-Heuristik der Clients bei
    großen PLZ den falschen Ort gewählt hat. Jetzt liegt die Zuordnung als
    amtlicher Datensatz im Backend — eine Quelle, ein Ergebnis, kein
    Fremddienst zur Laufzeit.
    """
    city = city_for_plz(plz)
    if city is None:
        raise HTTPException(status_code=404, detail="Postleitzahl nicht gefunden. Bitte prüfen.")
    return PlzLookupOut(plz=plz, city=city)
