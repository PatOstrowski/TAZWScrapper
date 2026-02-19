from fpdf import FPDF, XPos, YPos
from neo4j import GraphDatabase
from datetime import datetime

# Pomocnicza funkcja do usuwania polskich/specjalnych znaków dla domyślnej czcionki
def clean_text(text):
    if text is None:
        return ""
    return str(text).encode('ascii', 'ignore').decode('ascii')

class PDFReport(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 12)
        self.cell(0, 10, "Raport Scrapowania - Ksiegarnia", border=False, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Strona {self.page_no()}", align="C", new_x=XPos.RMARGIN, new_y=YPos.TOP)

class ReportGenerator:
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def fetch_data_for_report(self):
        data = {}
        with self.driver.session() as session:
            # 1. Podsumowanie
            res_stats = session.run("""
                MATCH (b:Book) 
                RETURN count(b) AS total, 
                       round(min(b.price),2) AS min_price, 
                       round(avg(b.price),2) AS avg_price, 
                       round(max(b.price),2) AS max_price
            """).single()
            data['stats'] = res_stats

            # 2. Top 5 autorów
            res_authors = session.run("""
                MATCH (a:Author)-[:WROTE]->(b:Book)
                RETURN a.name AS author, count(b) AS count
                ORDER BY count DESC LIMIT 5
            """)
            data['top_authors'] = [{"author": r["author"], "count": r["count"]} for r in res_authors]

            # 3. Top 20 książek do tabeli
            res_books = session.run("""
                MATCH (b:Book)
                RETURN b.title AS title, b.year AS year, b.price AS price
                ORDER BY b.price ASC LIMIT 20
            """)
            data['top_books'] = [{"title": r["title"][:40], "year": r["year"], "price": r["price"]} for r in res_books]

            # 4. Wynik analizy
            res_analysis = session.run("""
                MATCH (b:Book)-[:PUBLISHED_BY]->(p:Publisher)
                WHERE b.year > 2015
                RETURN b.title AS title, p.name AS publisher, b.year AS year
                LIMIT 10
            """)
            data['analysis'] = [{"title": r["title"][:35], "pub": r["publisher"], "year": r["year"]} for r in res_analysis]

        return data

    def generate_pdf(self, data, output_filename="raport_ksiazki.pdf"):
        pdf = PDFReport()
        pdf.set_auto_page_break(auto=True, margin=15)
        
        # --- STRONA TYTUŁOWA ---
        pdf.add_page()
        pdf.set_font("helvetica", "B", 24)
        pdf.cell(0, 40, "Raport z pobierania danych", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", "", 14)
        pdf.cell(0, 10, f"Temat: Ksiazki (Wariant B)", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, "Autor: Patryk Ostrowski", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Data generowania: {datetime.now().strftime('%Y-%m-%d %H:%M')}", align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.ln(20)
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 10, "Parametry Crawlera:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", "", 12)
        pdf.cell(0, 10, "- Seed URL: https://books.toscrape.com/", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, "- Zakres: Poziom 1 (Paginacja) & Poziom 2 (Szczegoly)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        # --- STRONA 2: PODSUMOWANIE ---
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Podsumowanie Statystyczne", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        pdf.set_font("helvetica", "", 12)
        stats = data['stats']
        pdf.cell(0, 10, f"Liczba pobranych rekordow: {stats['total']}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Odrzucone duplikaty: Obslugiwane na poziomie bazy (MERGE)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Cena Minimalna: {stats['min_price']} GBP", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Cena Srednia: {stats['avg_price']} GBP", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Cena Maksymalna: {stats['max_price']} GBP", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.ln(10)
        pdf.set_font("helvetica", "B", 14)
        pdf.cell(0, 10, "Top 5 Autorow (wg liczby ksiazek):", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", "", 12)
        for item in data['top_authors']:
            safe_author = clean_text(item['author'])
            pdf.cell(0, 10, f"- {safe_author}: {item['count']} ksiazek", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # --- STRONA 3: TABELA (TOP 20) ---
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Tabela Rekordow (Top 20 najtanszych)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(120, 10, "Tytul (skrocony)", border=1)
        pdf.cell(30, 10, "Rok", border=1, align="C")
        pdf.cell(40, 10, "Cena (GBP)", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", "", 10)
        for book in data['top_books']:
            safe_title = clean_text(book['title'])
            pdf.cell(120, 10, safe_title, border=1)
            pdf.cell(30, 10, str(book['year']), border=1, align="C")
            pdf.cell(40, 10, str(book['price']), border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        # --- STRONA 4: WYNIK ANALIZY (Zapytanie Cypher) ---
        pdf.add_page()
        pdf.set_font("helvetica", "B", 16)
        pdf.cell(0, 10, "Wynik Analizy (Cypher)", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", "I", 12)
        pdf.cell(0, 10, "Zapytanie: Ksiazki wydane po 2015 roku wraz z wydawnictwem", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        
        pdf.set_font("helvetica", "B", 10)
        pdf.cell(100, 10, "Tytul", border=1)
        pdf.cell(60, 10, "Wydawnictwo", border=1)
        pdf.cell(30, 10, "Rok", border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        
        pdf.set_font("helvetica", "", 10)
        for row in data['analysis']:
            safe_title = clean_text(row['title'])
            safe_pub = clean_text(row['pub'])
            pdf.cell(100, 10, safe_title, border=1)
            pdf.cell(60, 10, safe_pub, border=1)
            pdf.cell(30, 10, str(row['year']), border=1, align="C", new_x=XPos.LMARGIN, new_y=YPos.NEXT)

        pdf.output(output_filename)
        print(f"\nUkończono! Wygenerowano raport PDF: {output_filename}")


# === URUCHOMIENIE ===
if __name__ == "__main__":
    URI = "bolt://localhost:7687"
    USER = "neo4j"
    PASSWORD = "testtest" # <--- ZMIEŃ NA SWOJE HASŁO

    report_gen = ReportGenerator(URI, USER, PASSWORD)
    try:
        dane_do_raportu = report_gen.fetch_data_for_report()
        report_gen.generate_pdf(dane_do_raportu)
    finally:
        report_gen.close()