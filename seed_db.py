"""Create data/retail.db with a synthetic Superstore-style dataset (4 related tables).

To use the real Superstore/Olist data instead, load your CSVs into SQLite with
pandas (df.to_sql) and keep the same read-only connection code.
"""
import os, random, sqlite3
from datetime import date, timedelta
from config import DB_PATH

random.seed(42)

SCHEMA = """
CREATE TABLE customers (
  customer_id INTEGER PRIMARY KEY, name TEXT, segment TEXT,
  city TEXT, state TEXT, region TEXT);
CREATE TABLE products (
  product_id INTEGER PRIMARY KEY, name TEXT, category TEXT,
  sub_category TEXT, unit_price REAL, unit_cost REAL);
CREATE TABLE orders (
  order_id INTEGER PRIMARY KEY, customer_id INTEGER REFERENCES customers(customer_id),
  order_date TEXT, ship_mode TEXT);
CREATE TABLE order_items (
  item_id INTEGER PRIMARY KEY, order_id INTEGER REFERENCES orders(order_id),
  product_id INTEGER REFERENCES products(product_id),
  quantity INTEGER, discount REAL);
"""

CITIES = [("Los Angeles","California","West"),("San Francisco","California","West"),
          ("Seattle","Washington","West"),("New York City","New York","East"),
          ("Philadelphia","Pennsylvania","East"),("Boston","Massachusetts","East"),
          ("Chicago","Illinois","Central"),("Houston","Texas","Central"),
          ("Dallas","Texas","Central"),("Atlanta","Georgia","South"),
          ("Miami","Florida","South"),("Nashville","Tennessee","South")]
CATALOG = {"Furniture": ["Chairs","Tables","Bookcases"],
           "Office Supplies": ["Binders","Paper","Storage","Labels"],
           "Technology": ["Phones","Accessories","Copiers","Laptops"]}
PRICE = {"Furniture": (60, 700), "Office Supplies": (3, 90), "Technology": (20, 1500)}
FIRST = "Aarav Maya Liam Sofia Noah Emma Ravi Priya Omar Lena Kai Zoe Arun Mei Ivan Nora".split()
LAST = "Smith Patel Garcia Chen Brown Khan Lopez Kim Singh Davis Moore Rossi".split()

def main():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
    con = sqlite3.connect(DB_PATH)
    con.executescript(SCHEMA)

    for cid in range(1, 301):
        city, state, region = random.choice(CITIES)
        con.execute("INSERT INTO customers VALUES (?,?,?,?,?,?)",
            (cid, f"{random.choice(FIRST)} {random.choice(LAST)}",
             random.choices(["Consumer","Corporate","Home Office"], [5,3,2])[0], city, state, region))

    pid = 0
    for cat, subs in CATALOG.items():
        for sub in subs:
            for n in range(1, 7):
                pid += 1
                lo, hi = PRICE[cat]
                price = round(random.uniform(lo, hi), 2)
                con.execute("INSERT INTO products VALUES (?,?,?,?,?,?)",
                    (pid, f"{sub} Model {n}", cat, sub, price, round(price * random.uniform(0.55, 0.9), 2)))
    n_products = pid

    start, end = date(2024, 1, 1), date(2026, 10, 28)
    span = (end - start).days
    item_id = 0
    for oid in range(1, 2501):
        d = start + timedelta(days=random.randint(0, span))
        # mild seasonality: more orders in Nov/Dec
        if d.month in (11, 12) and random.random() < 0.3:
            d = d.replace(day=random.randint(1, 28))
        con.execute("INSERT INTO orders VALUES (?,?,?,?)",
            (oid, random.randint(1, 300), d.isoformat(),
             random.choice(["Standard Class","Second Class","First Class","Same Day"])))
        for _ in range(random.randint(1, 4)):
            item_id += 1
            con.execute("INSERT INTO order_items VALUES (?,?,?,?,?)",
                (item_id, oid, random.randint(1, n_products), random.randint(1, 8),
                 random.choice([0, 0, 0, 0.1, 0.2, 0.3])))
    con.commit()
    con.close()
    print(f"Created {DB_PATH}")

if __name__ == "__main__":
    main()
