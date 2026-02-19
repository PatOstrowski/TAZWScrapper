# Web Scraper & Neo4j Graph Analysis 

---

## 📖 Opis projektu
Aplikacja w języku Python realizująca pełen proces ETL (Extract, Transform, Load) połączony z analizą grafową i raportowaniem. Projekt pobiera dane ze strony internetowej (crawler/scraper), modeluje je w grafowej bazie danych **Neo4j**, wykonuje analityczne zapytania w języku **Cypher**, a na koniec generuje podsumowujący raport w formacie **PDF**.

Projekt wykorzystuje edukacyjny serwis `books.toscrape.com`.

## ✨ Zrealizowane wymagania

### 1. Crawler / Scraper (`scraper.py`)
* **Seed URL:** `https://books.toscrape.com/`
* **Głębokość:** 2 poziomy (paginacja -> szczegóły książki).
* **Pobrane rekordy:** Skonfigurowane na minimum 50 sztuk (domyślnie 55).
* **Obsługa błędów sieci:** Zaimplementowany mechanizm *retry* oraz *timeout*.
* **Logowanie:** Przebieg działania logowany w konsoli (INFO/WARN/ERROR).
* **Wymagania "na plus":** Zastosowano *rate limit* (`time.sleep()`), by nie obciążać serwera docelowego.

### 2. Baza Grafowa Neo4j (`database.py`)
* **Model grafowy:**
  * **Węzły:** `Book` (isbn, title, year, price, url), `Author` (name), `Publisher` (name).
  * **Relacje:** `(Author)-[:WROTE]->(Book)`, `(Book)-[:PUBLISHED_BY]->(Publisher)`.
* **Constraints/Indeksy:** Nałożono unikalność na `Book.isbn`, `Author.name` oraz `Publisher.name` zapobiegając duplikatom.
* **Transakcyjność:** Inserty zrealizowane paczkowo (batch insert) za pomocą klauzuli `UNWIND` w Cypherze i operacji `MERGE`.

### 3. Zapytania Analityczne Cypher (`analytics.py`)
Wykonano 5 zapytań prezentowanych w tabelach tekstowych w konsoli:
1. Filtr po wartości liczbowej (Cena < 20).
2. Filtr po dacie (Książki wydane po 2015).
3. Ranking / Top (Top 5 najtańszych książek).
4. Agregacja (Średnia cena i liczba książek per Autor).
5. Zapytanie relacyjne (Zestawienie: Autor -> Książka -> Wydawnictwo).

### 4. Eksport do PDF (`report.py`)
Automatyczne generowanie pliku `Raport_Zaliczeniowy_Ksiazki.pdf` zawierającego:
* Stronę tytułową z parametrami crawlera.
* Podsumowanie (liczba rekordów, ceny min/avg/max, top 5 autorów).
* Tabelę z rekordami (Top 20 najtańszych książek).
* Wynik analizy Cypher (Książki wydane po 2015 roku wraz z wydawnictwem).

---

## 🛠️ Wykorzystane technologie
Zamiast Javy (zgodnie z ustaleniami) wykorzystano ekosystem Pythona:
* **Python 3.x**
* **Requests** (pobieranie HTML)
* **BeautifulSoup4** (parsowanie HTML / odpowiednik jsoup)
* **neo4j** (oficjalny sterownik Neo4j dla Pythona)
