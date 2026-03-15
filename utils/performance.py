import sqlite3, time

conn = sqlite3.connect("pos.database")
conn.execute('PRAGMA journal_mode=WAL;')  # Enable WAL mode
cur = conn.cursor()

start = time.time()

# Insert records
cur.execute("BEGIN")
for i in range(1000):
    cur.execute("""
        INSERT INTO Order_Cart (order_status, service_area_id, customer_id, subtotal, total, provided_name)
        VALUES (?, ?, ?, ?, ?, ?)""",
        (0, (i % 8) + 1, None, 1000 + i * 10, 1100 + i * 10, f'Test order #{i+1}')
    )
    conn.commit()

# Update records
    cur.execute("UPDATE Order_Cart SET order_status = 11 WHERE order_status = 10")
    conn.commit()
    cur.execute("select * from order_history order by timestamp;")

end = time.time()
print(f"Total time: {end - start:.4f} seconds")

