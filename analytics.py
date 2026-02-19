from neo4j import GraphDatabase
import logging

logging.basicConfig(level=logging.INFO, format='%(message)s')

class GraphAnalytics:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def print_table(self, title, columns, records):
        """Pomocnicza funkcja do ładnego wypisywania tabeli w konsoli."""
        print(f"\n--- {title} ---")
        header = " | ".join([f"{col:<25}" for col in columns])
        print(header)
        print("-" * len(header))
        for record in records:
            row = " | ".join([f"{str(record[col]):<25}" for col in columns])
            print(row)
        print("-" * len(header))

    def run_queries(self):
        with self.driver.session() as session:
            
            # 1. Filtr po wartości liczbowej (np. cena < 20)
            print("\n1. FILTR PO CENIE (Cena < 20)")
            result_1 = session.run("MATCH (b:Book) WHERE b.price < 20 RETURN b.title AS Tytul, b.price AS Cena LIMIT 5")
            self.print_table("Książki tańsze niż £20", ["Tytul", "Cena"], result_1.data())

            # 2. Filtr po dacie (np. książki wydane po 2015)
            print("\n2. FILTR PO ROKU (Wydane po 2015)")
            result_2 = session.run("MATCH (b:Book) WHERE b.year > 2015 RETURN b.title AS Tytul, b.year AS Rok LIMIT 5")
            self.print_table("Nowsze książki (>2015)", ["Tytul", "Rok"], result_2.data())

            # 3. Ranking / Top (Top 5 najtańszych książek)
            print("\n3. RANKING (Top 5 najtańszych)")
            result_3 = session.run("MATCH (b:Book) RETURN b.title AS Tytul, b.price AS Cena ORDER BY b.price ASC LIMIT 5")
            self.print_table("Top 5 najtańszych", ["Tytul", "Cena"], result_3.data())

            # 4. Agregacja (średnia, min i max cena per autor)
            print("\n4. AGREGACJA (Statystyki cenowe per Autor)")
            query_4 = """
            MATCH (a:Author)-[:WROTE]->(b:Book) 
            RETURN a.name AS Autor, 
                   round(avg(b.price), 2) AS Srednia_Cena, 
                   count(b) AS Liczba_Ksiazek
            ORDER BY Srednia_Cena DESC
            """
            result_4 = session.run(query_4)
            self.print_table("Statystyki wg. Autora", ["Autor", "Srednia_Cena", "Liczba_Ksiazek"], result_4.data())

            # 5. Zapytanie relacyjne (Jakie książki wydał "Znak" napisane przez konkretnego autora?)
            # Uwaga: Używamy LIMIT, by pokazać próbkę relacyjną
            print("\n5. ZAPYTANIE RELACYJNE (Książki z wydawnictwami i autorami)")
            query_5 = """
            MATCH (a:Author)-[:WROTE]->(b:Book)-[:PUBLISHED_BY]->(p:Publisher)
            RETURN a.name AS Autor, b.title AS Tytul, p.name AS Wydawnictwo
            LIMIT 5
            """
            result_5 = session.run(query_5)
            self.print_table("Książki - Autor - Wydawnictwo", ["Autor", "Tytul", "Wydawnictwo"], result_5.data())


# === URUCHOMIENIE ===
if __name__ == "__main__":
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "testtest" # <--- ZMIEŃ NA SWOJE HASŁO

    analytics = GraphAnalytics(URI, USER, PASSWORD)
    try:
        analytics.run_queries()
    finally:
        analytics.close()