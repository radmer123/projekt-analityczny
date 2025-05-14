"""Program FastAPI - część druga"""

from fastapi import Depends, FastAPI, HTTPException, Query
from sqlalchemy.orm import Session
from datetime import date


import crud, schemas
from database import SessionLocal

api_description = """
Ten interfejs API zapewnia dostęp tylko do odczytu do informacji z interfejsu API Sports World Central (SWC) Fantasy Football. 
Punkty końcowe są pogrupowane w następujące kategorie:

## Analityka
Uzyskaj informacje o kondycji interfejsu API oraz liczbie lig, drużyn i zawodników.

## Zawodnik
Możesz uzyskać listę zawodników NFL lub wyszukać konkretnego zawodnika według identyfikatora player_id.

## Punktacja
Możesz uzyskać listę wyników zawodników NFL, w tym zdobytych przez nich punktów fantasy według systemu punktacji lig SWC.

## Członkostwo 
Uzyskaj informacje o wszystkich ligach fantasy football SWC i drużynach w nich występujących.

## Ogólne
Uzyskaj informacje o platformie SWC fantasy football jako całości.
"""

# Konstruktor FastAPI z dodatkowymi szczegółami dodanymi dla specyfikacji OpenAPI
app = FastAPI(
    description=api_description,
    title="Sports World Central (SWC) Fantasy Football API",
    version="0.2",
)


# Zależności
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.get(
    "/",
    summary="Sprawdzenie, czy interfejs API SWC fantasy football działa",
    description="""Ten punkt końcowy służy do sprawdzenia, czy interfejs API jest uruchomiony. Możesz również użyć go przed wykonaniem innych połączeń, aby upewnić się, że interfejs API działa.""",
    response_description="Rekord JSON z komunikatem. Jeśli interfejs API jest uruchomiony, komunikat informuje o powodzeniu.",
    operation_id="v0_health_check",
    tags=["analityka"],
)
async def root():
    return {"message": "Test stanu API zakończony sukcesem"}


@app.get(
    "/v0/players/",
    response_model=list[schemas.Player],
    summary="Pobierz wszystkich zawodników SWC, którzy spełniają warunki określone przez wszystkie parametry wysłane wraz z żądaniem.",
    description="""Użyj tego punktu końcowego, aby uzyskać listę zawodników SWC. Za pomocą parametrów można filtrować zawodników na liście. Nazwiska nie są unikatowe. Parametry skip i limit służą do stronicowania interfejsu API. Nie używaj wartości Player ID do zliczania. Nie ma gwarancji, że rekordy będą po kolei. """,
    response_description="Lista zawodników NFL, którzy biorą udział w rozgrywkach SWC fantasy football. Nie muszą należeć do żadnej drużyny.",
    operation_id="v0_get_players",
    tags=["zawodnicy"],
)
def read_players(
    skip: int = Query(
        0, description="Liczba elementów do pominięcia na początku wywołania API."
    ),
    limit: int = Query(
        100, description="Liczba rekordów, które API ma zwrócić po rekordach pominiętych."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="Minimalna data modyfikacji dla rekordów, które mają zostać zwrócone. Wyklucz wszystkie rekordy zmienione wcześniej.",
    ),
    first_name: str = Query(
        None, description="Imię zawodnika"
    ),
    last_name: str = Query(None, description="Nazwisko zawodnika"),
    db: Session = Depends(get_db),
):
    players = crud.get_players(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        first_name=first_name,
        last_name=last_name,
    )
    return players


@app.get(
    "/v0/players/{player_id}",
    response_model=schemas.Player,
    summary="Pobierz dane jednego zawodnika z użyciem identyfikatora, który jest wewnętrzny dla SWC",
    description="Jeśli dysponujesz identyfikatorem SWC zawodnika z innego wywołania API, np. v0_get_players, możesz wywołać to API z użyciem identyfikatora zawodnika",
    response_description="One NFL player",
    operation_id="v0_get_players_by_player_id",
    tags=["zawodnicy"],
)
def read_player(player_id: int, db: Session = Depends(get_db)):
    player = crud.get_player(db, player_id=player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono zawodnika")
    return player


@app.get(
    "/v0/performances/",
    response_model=list[schemas.Performance],
    summary="Pobierz listę wszystkich występów, które spełniają warunki określone przez wszystkie parametry przesłane wraz z żądaniem.",
    description="""Użyj tego punktu końcowego, aby uzyskać listy tygodniowych występów zawodników w SWC. Parametry skip i limit służą do stronicowania interfejsu API. Nie używaj identyfikatora występu do zliczania lub analityki, ponieważ jest to wewnętrzny identyfikator i nie ma gwarancji, że będzie on sekwencyjny.""",
    response_description="Lista cotygodniowych występów. Może obejmować wielu zawodników.",
    operation_id="v0_get_performances",
    tags=["punktacja"],
)
def read_performances(
    skip: int = Query(
        0, description="Liczba elementów do pominięcia na początku wywołania API."
    ),
    limit: int = Query(
        100, description="Liczba rekordów do zwrócenia po pominiętych rekordach."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="Minimalne dane zmiany, które mają zostać zwrócone. Wyklucz wszystkie rekordy zmienione wcześniej.",
    ),
    db: Session = Depends(get_db),
):
    performances = crud.get_performances(
        db, skip=skip, limit=limit, min_last_changed_date=minimum_last_changed_date
    )
    return performances


@app.get(
    "/v0/leagues/{league_id}",
    response_model=schemas.League,
    summary="Pobierz jedną ligę według identyfikatora",
    description="""Użyj tego punktu końcowego, aby uzyskać dane pojedynczej ligi, która pasuje do identyfikatora ligi podanego przez użytkownika.""",
    response_description="An SWC league",
    operation_id="v0_get_league_by_league_id",
    tags=["członkostwo"],
)
def read_league(league_id: int, db: Session = Depends(get_db)):
    league = crud.get_league(db, league_id=league_id)
    if league is None:
        raise HTTPException(status_code=404, detail="Nie znaleziono ligi")
    return league


@app.get(
    "/v0/leagues/",
    response_model=list[schemas.League],
    summary="Pobierz wszystkie ligi SWC fantasy football, które pasują do wysłanych parametrów",
    description="""Użyj tego punktu końcowego, aby uzyskać listy lig futbolu fantasy SWC. Możesz użyć parametry skip i limit do obsługi stronicowania wynikós. Nazwa ligi nie jest unikatowa. Nie używaj identyfikatora ligi do zliczania lub analityki, ponieważ jest to wewnętrzny identyfikator i nie ma gwarancji, że będzie on sekwencyjny.""",
    response_description="Lista lig na stronie SWC fantasy football.",
    operation_id="v0_get_leagues",
    tags=["członkostwo"],
)
def read_leagues(
    skip: int = Query(
        0, description="Liczba elementów do pominięcia na początku wywołania API."
    ),
    limit: int = Query(
        100, description="Liczba rekordów do zwrócenia po pominiętych rekordach."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="Minimalne dane zmiany, które mają zostać zwrócone. Wyklucz wszystkie rekordy zmienione wcześniej.",
    ),
    league_name: str = Query(
        None, description="Nazwy lig do zwrócenia. W SWC nie są unikatowe"
    ),
    db: Session = Depends(get_db),
):
    leagues = crud.get_leagues(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        league_name=league_name,
    )
    return leagues


@app.get(
    "/v0/teams/",
    response_model=list[schemas.Team],
    summary="Uzyskaj wszystkie drużyny SWC fantasy football, które pasują do przesłanych parametrów",
    description="""Użyj tego punktu końcowego, aby uzyskać listy drużyn SWC fantasy football. Możesz użyć opcji pomijania i ograniczania, aby zastosować stronicowanie wyników interfejsu API. Nazwa drużyny nie musi być unikatowa. Jeśli uzyskasz identyfikator drużyny z innego zapytania, możesz dopasować go do identyfikatora drużyny z tego zapytania. Nie używaj identyfikatora drużyny do zliczania lub innych obliczeń.""",
    response_description="Lista drużyn na stronie SWC fantasy football.",
    operation_id="v0_get_teams",
    tags=["członkostwo"],
)
def read_teams(
    skip: int = Query(
        0, description="Liczba elementów do pominięcia na początku wywołania API."
    ),
    limit: int = Query(
        100, description="Liczba rekordów do zwrócenia po pominiętych rekordach."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="Minimalne dane zmiany, które mają zostać zwrócone. Wyklucz wszystkie rekordy zmienione wcześniej.",
    ),
    team_name: str = Query(
        None,
        description="Nazwy drużyn do zwrócenia. Nie jest unikatowa w całej lidze SWC, ale jest unikatowa wewnątrz ligi.",
    ),
    league_id: int = Query(
        None, description="Identyfikator ligi drużyn do zwrócenia. Unikatowy w SWC."
    ),
    db: Session = Depends(get_db),
):
    teams = crud.get_teams(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
        team_name=team_name,
        league_id=league_id,
    )
    return teams


@app.get(
    "/v0/counts/",
    response_model=schemas.Counts,
    summary="Uzyskaj liczbę lig, drużyn i graczy w systemie SWC fantasy football",
    description="""Użyj tego punktu końcowego, aby zliczyć liczbę lig, drużyn i graczy w systemie SWC fantasy football. Użyj w połączeniu z parametrami skip i limit  w v0_get leagues, v0_get_teams lub v0_get_players. Użyj tego punktu końcowego, aby uzyskać te liczby zamiast wywoływać inne interfejsy API.""",
    response_description="Lista drużyn w systemie SWC fantasy football.",
    operation_id="v0_get_counts",
    tags=["analityka"],
)

def get_count(db: Session = Depends(get_db)):
    counts = schemas.Counts(
        league_count=crud.get_league_count(db),
        team_count=crud.get_team_count(db),
        player_count=crud.get_player_count(db),
        week_count=crud.get_week_count(db), #v0.2
    )
    return counts

#v0.2
@app.get(
    "/v0/weeks/",
    response_model=list[schemas.Week],
    summary="Pobierz wszystkie tygodnie SWC, które spełniają wszystkie parametry przesłane wraz z żądaniem.",
    description="""Użyj tego punktu końcowego, aby uzyskać listę tygodni w SWC. Za pomocą parametrów można filtrować tygodnie na liście. Użyj w połączeniu z parametrami skip i limit, aby zastosować stronicowanie interfejsu API.""",
    response_description="Lista tygodni w SWC fantasy football.",
    operation_id="v0_get_weeks",
    tags=["ogólne"],
)
def read_weeks(
    skip: int = Query(
        0, description="Liczba elementów do pominięcia na początku wywołania API."
    ),
    limit: int = Query(
        100, description="Liczba rekordów do zwrócenia po pominiętych rekordach."
    ),
    minimum_last_changed_date: date = Query(
        None,
        description="Minimalne dane zmiany, które mają zostać zwrócone. Wyklucz wszystkie rekordy zmienione wcześniej.",
    ),
    db: Session = Depends(get_db),
):
    weeks = crud.get_weeks(
        db,
        skip=skip,
        limit=limit,
        min_last_changed_date=minimum_last_changed_date,
    )
    return weeks
