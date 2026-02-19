from neo4j import GraphDatabase
import logging

class Neo4jHandler:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))
        logging.info("Połączono z bazą Neo4j.")

    def close(self):
        self.driver.close()
        logging.info("Zamknięto połączenie z Neo4j.")

    def setup_constraints(self):
        """Tworzy constraints (wymaganie z zadania: unikalność)."""
        queries = [
            "CREATE CONSTRAINT book_isbn_unique IF NOT EXISTS FOR (b:Book) REQUIRE b.isbn IS UNIQUE",
            "CREATE CONSTRAINT author_name_unique IF NOT EXISTS FOR (a:Author) REQUIRE a.name IS UNIQUE",
            "CREATE CONSTRAINT publisher_name_unique IF NOT EXISTS FOR (p:Publisher) REQUIRE p.name IS UNIQUE"
        ]
        with self.driver.session() as session:
            for query in queries:
                session.run(query)
        logging.info("Nałożono constraints na bazę (unikalność węzłów).")

    def insert_books_batch(self, books_data):
        """Wstawia dane w formie paczki (batch insert) używając UNWIND."""
        cypher_query = """
        UNWIND $books AS book
        
        // 1. Tworzenie lub znajdowanie książki (MERGE zapobiega duplikatom)
        MERGE (b:Book {isbn: book.isbn})
        ON CREATE SET b.title = book.title, 
                      b.year = book.year, 
                      b.price = book.price, 
                      b.url = book.url
        ON MATCH SET b.price = book.price // Aktualizacja ceny, jeśli książka już istnieje
        
        // 2. Tworzenie lub znajdowanie autora
        MERGE (a:Author {name: book.author})
        
        // 3. Tworzenie lub znajdowanie wydawnictwa
        MERGE (p:Publisher {name: book.publisher})
        
        // 4. Tworzenie relacji
        MERGE (a)-[:WROTE]->(b)
        MERGE (b)-[:PUBLISHED_BY]->(p)
        """
        
        with self.driver.session() as session:
            # Uruchamiamy transakcję
            result = session.run(cypher_query, books=books_data)
            summary = result.consume()
            
        logging.info(f"Zakończono import. Utworzono węzłów: {summary.counters.nodes_created}, "
                     f"utworzono relacji: {summary.counters.relationships_created}.")


# === TESTOWANIE BAZY ===
if __name__ == "__main__":
    from scraper import BookScraper
    
    # 1. Zbieramy dane (zmniejszamy do 5 na czas testów bazy, żeby było szybciej)
    scraper = BookScraper(seed_url="https://books.toscrape.com/")
    dane_ksiazek = scraper.run(target_count=5) 
    
    # 2. Konfiguracja połączenia z Neo4j (Zmień hasło na swoje!)
    URI = "bolt://localhost:7687"  # Domyślny port dla Neo4j Desktop
    USER = "neo4j"
    PASSWORD = "testtest"   # <--- TUTAJ WPISZ SWOJE HASŁO
    
    # 3. Import do bazy
    db = Neo4jHandler(URI, USER, PASSWORD)
    try:
        db.setup_constraints()
        if dane_ksiazek:
            db.insert_books_batch(dane_ksiazek)
    finally:
        db.close()