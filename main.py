import logging
from scraper import BookScraper
from database import Neo4jHandler
from analytics import GraphAnalytics
from report import ReportGenerator

# --- KONFIGURACJA BAZY NEO4J ---
# Pamiętaj, aby zmienić hasło na swoje!
URI = "bolt://localhost:7687"
USER = "neo4j"
PASSWORD = "testtest" 

def main():
    print("\n" + "="*50)
    print("ROZPOCZĘCIE PROCESU: SCRAPING -> NEO4J -> ANALIZA -> PDF")
    print("="*50 + "\n")

    # KROK 1: Pobieranie danych (Scraper)
    print(">>> ETAP 1: Pobieranie danych ze strony internetowej...")
    scraper = BookScraper(seed_url="https://books.toscrape.com/")
    # Ustawiamy target na 55, aby z zapasem spełnić wymóg z zadania (min. 50 rekordów)
    books_data = scraper.run(target_count=55) 

    if not books_data:
        print("BŁĄD: Nie udało się pobrać danych. Przerywam proces.")
        return

    # KROK 2: Wgrywanie danych do Neo4j
    print("\n>>> ETAP 2: Zapis danych i modelowanie grafu w Neo4j...")
    db_handler = Neo4jHandler(URI, USER, PASSWORD)
    try:
        db_handler.setup_constraints()
        db_handler.insert_books_batch(books_data)
    except Exception as e:
        print(f"BŁĄD bazy danych: {e}")
        return
    finally:
        db_handler.close()

    # KROK 3: Wykonywanie zapytań analitycznych (Cypher) i wypisanie ich w konsoli
    print("\n>>> ETAP 3: Zapytania analityczne Cypher...")
    analytics = GraphAnalytics(URI, USER, PASSWORD)
    try:
        analytics.run_queries()
    except Exception as e:
        print(f"BŁĄD podczas analizy: {e}")
    finally:
        analytics.close()

    # KROK 4: Zbieranie statystyk i generowanie pliku PDF
    print("\n>>> ETAP 4: Generowanie raportu PDF...")
    report_gen = ReportGenerator(URI, USER, PASSWORD)
    try:
        dane_do_raportu = report_gen.fetch_data_for_report()
        report_gen.generate_pdf(dane_do_raportu, output_filename="Raport_Zaliczeniowy_Ksiazki.pdf")
    except Exception as e:
        print(f"BŁĄD podczas tworzenia PDF: {e}")
    finally:
        report_gen.close()

    print("\n" + "="*50)
    print("PROCES ZAKOŃCZONY POMYŚLNIE! Sprawdź folder projektu.")
    print("="*50 + "\n")


if __name__ == "__main__":
    # Upewniamy się, że główne logowanie jest ustawione tylko na ERROR lub INFO, 
    # żeby ładnie komponowało się z naszymi customowymi printami.
    logging.getLogger().setLevel(logging.INFO)
    main()