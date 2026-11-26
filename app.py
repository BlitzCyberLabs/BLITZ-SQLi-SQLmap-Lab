from flask import Flask, render_template, request, redirect, url_for, session, flash
import json, os, secrets, socket, random, string, re
import mysql.connector
from mysql.connector import Error
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
CONFIG_PATH = BASE_DIR / "lab_config.json"

app = Flask(__name__)
app.secret_key = secrets.token_hex(32)

DB_CONFIG = {
    "host": os.getenv("BLITZ_DB_HOST", "127.0.0.1"),
    "port": int(os.getenv("BLITZ_DB_PORT", "3306")),
    "user": os.getenv("BLITZ_DB_USER", "blitzlab"),
    "password": os.getenv("BLITZ_DB_PASSWORD", "BlitzLab_DB_Only_Local_2026"),
    "database": "blitz_store",
}

def get_db():
    return mysql.connector.connect(**DB_CONFIG)

def make_readable_password():
    words = ["Amber", "Cedar", "Falcon", "Harbor", "Maple", "Orbit", "Velvet", "Willow", "Copper", "River", "Pixel", "Summit", "Mango", "Silver", "Breeze", "Comet"]
    return f"{random.choice(words)}{random.choice(words)}!{random.randint(10, 99)}"

def create_lab_config():
    """Create or update the local lab config with a permanent training flag."""
    if CONFIG_PATH.exists():
        config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    else:
        config = {}

    # Keep admin credentials stable across restarts; generate them only if missing.
    config.setdefault("admin_username", "admin_" + secrets.token_hex(3))
    if not re.fullmatch(r"[A-Z][a-z]+[A-Z][a-z]+!\d{2}", config.get("admin_password", "")):
        config["admin_password"] = make_readable_password()

    # This flag is intentionally identical for every student and fresh installation.
    config["final_flag"] = "BLITZ{a67b1c38938e29bc7bae1dce}"

    CONFIG_PATH.write_text(json.dumps(config, indent=2), encoding="utf-8")
    return config

def init_db():
    config = create_lab_config()
    # Reproducible static training dataset on every application start.
    # Seed after config creation so first-run admin credential generation cannot
    # change the classroom dataset.
    random.seed(20261126)
    conn = get_db()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INT AUTO_INCREMENT PRIMARY KEY,
            sku VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(120) NOT NULL,
            category VARCHAR(60) NOT NULL,
            description TEXT NOT NULL,
            price DECIMAL(10,2) NOT NULL,
            stock INT NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password VARCHAR(160) NOT NULL,
            role VARCHAR(30) NOT NULL,
            email VARCHAR(150) NOT NULL,
            department VARCHAR(80) NOT NULL,
            account_status VARCHAR(20) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS orders (
            id INT AUTO_INCREMENT PRIMARY KEY,
            order_ref VARCHAR(30) UNIQUE NOT NULL,
            customer_username VARCHAR(80) NOT NULL,
            product_sku VARCHAR(20) NOT NULL,
            quantity INT NOT NULL,
            order_status VARCHAR(30) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS support_tickets (
            id INT AUTO_INCREMENT PRIMARY KEY,
            ticket_ref VARCHAR(30) UNIQUE NOT NULL,
            submitted_by VARCHAR(80) NOT NULL,
            subject VARCHAR(180) NOT NULL,
            priority VARCHAR(20) NOT NULL,
            status VARCHAR(30) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS customer_addresses (
            id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(80) NOT NULL,
            city VARCHAR(80) NOT NULL, state VARCHAR(80) NOT NULL,
            postal_code VARCHAR(12) NOT NULL, address_type VARCHAR(20) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS payments (
            id INT AUTO_INCREMENT PRIMARY KEY, payment_ref VARCHAR(32) UNIQUE NOT NULL,
            order_ref VARCHAR(30) NOT NULL, payment_method VARCHAR(30) NOT NULL,
            amount DECIMAL(10,2) NOT NULL, payment_status VARCHAR(24) NOT NULL
        )
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS audit_logs (
            id INT AUTO_INCREMENT PRIMARY KEY, username VARCHAR(80) NOT NULL,
            action VARCHAR(100) NOT NULL, source_ip VARCHAR(45) NOT NULL,
            event_time DATETIME NOT NULL, result VARCHAR(24) NOT NULL
        )
    """)
    # Every launch starts with a clean database. Student changes from the previous
    # run are discarded and the same deterministic training dataset is restored.
    for table in ("audit_logs", "payments", "customer_addresses", "support_tickets", "orders", "users", "products"):
        cur.execute(f"DELETE FROM {table}")
        cur.execute(f"ALTER TABLE {table} AUTO_INCREMENT = 1")

    cur.execute("SELECT COUNT(*) FROM products")
    if cur.fetchone()[0] == 0:
        products = [
            ("BZ-AX41", "Arc Wireless Mouse", "Accessories", "Precision wireless mouse with adjustable DPI", 749.00, 42),
            ("BZ-KB82", "Nimbus Mechanical Keyboard", "Accessories", "Compact hot-swappable mechanical keyboard", 3299.00, 17),
            ("BZ-ST19", "Vault USB Drive 128GB", "Storage", "USB 3.2 portable flash storage", 899.00, 63),
            ("BZ-HD57", "Orbit External SSD 1TB", "Storage", "Portable high-speed solid state drive", 6499.00, 9),
            ("BZ-WC33", "Clarity HD Webcam", "Peripherals", "Full HD webcam with dual microphones", 2199.00, 24),
            ("BZ-MN64", "Aster 24-inch Monitor", "Displays", "IPS monitor with 100Hz refresh rate", 10499.00, 11),
            ("BZ-HS28", "Pulse USB Headset", "Audio", "Over-ear headset with noise-reducing mic", 1599.00, 31),
            ("BZ-NW73", "LinkPro Gigabit Adapter", "Networking", "USB-C to Gigabit Ethernet adapter", 1199.00, 28),
        ]
        cur.executemany(
            "INSERT INTO products (sku,name,category,description,price,stock) VALUES (%s,%s,%s,%s,%s,%s)",
            products
        )
    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        users = [
            (config["admin_username"], config["admin_password"], "admin",
             "platform.admin@blitz-training.local", "IT Operations", "active"),
            ("casey.morgan", secrets.token_urlsafe(10), "support",
             "casey.morgan@blitz-training.local", "Customer Support", "active"),
            ("riley.patel", secrets.token_urlsafe(10), "analyst",
             "riley.patel@blitz-training.local", "Security Operations", "active"),
            ("jordan.lee", secrets.token_urlsafe(10), "inventory",
             "jordan.lee@blitz-training.local", "Inventory", "active"),
            ("taylor.fern", secrets.token_urlsafe(10), "auditor",
             "taylor.fern@blitz-training.local", "Compliance", "disabled"),
        ]
        cur.executemany(
            "INSERT INTO users (username,password,role,email,department,account_status) VALUES (%s,%s,%s,%s,%s,%s)",
            users
        )
    cur.execute("SELECT COUNT(*) FROM orders")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO orders (order_ref,customer_username,product_sku,quantity,order_status) VALUES (%s,%s,%s,%s,%s)",
            [
                ("ORD-7K2P91", "casey.morgan", "BZ-AX41", 2, "processing"),
                ("ORD-4M8Q32", "riley.patel", "BZ-NW73", 1, "shipped"),
                ("ORD-9T5R16", "jordan.lee", "BZ-ST19", 3, "delivered"),
                ("ORD-2C6V84", "casey.morgan", "BZ-HS28", 1, "pending"),
            ]
        )
    cur.execute("SELECT COUNT(*) FROM support_tickets")
    if cur.fetchone()[0] == 0:
        cur.executemany(
            "INSERT INTO support_tickets (ticket_ref,submitted_by,subject,priority,status) VALUES (%s,%s,%s,%s,%s)",
            [
                ("TKT-81QZ", "casey.morgan", "Delivery address update", "medium", "open"),
                ("TKT-29LP", "riley.patel", "Unrecognized account activity", "high", "investigating"),
                ("TKT-63WD", "jordan.lee", "Stock mismatch report", "low", "closed"),
            ]
        )
    # Keep exactly one active administrator synchronized with lab_config.json.
    # Older lab builds could leave an administrator under a previous generated username.
    # Reconcile that record instead of creating a second admin or leaving stale credentials.
    cur.execute("SELECT id FROM users WHERE username=%s AND role <> 'admin'", (config["admin_username"],))
    conflicting_user = cur.fetchone()
    if conflicting_user:
        cur.execute("UPDATE users SET username=%s WHERE id=%s", (f"legacy_user_{conflicting_user[0]}", conflicting_user[0]))
    cur.execute("SELECT id FROM users WHERE role='admin' ORDER BY id LIMIT 1")
    admin_row = cur.fetchone()
    if admin_row:
        admin_id = admin_row[0]
        cur.execute(
            "UPDATE users SET username=%s,password=%s,role='admin',email=%s,department=%s,account_status='active' WHERE id=%s",
            (config["admin_username"], config["admin_password"], "platform.admin@blitz-training.local", "IT Operations", admin_id)
        )
        cur.execute("UPDATE users SET role='customer' WHERE role='admin' AND id<>%s", (admin_id,))
    else:
        cur.execute(
            "INSERT INTO users (username,password,role,email,department,account_status) VALUES (%s,%s,'admin',%s,%s,'active')",
            (config["admin_username"], config["admin_password"], "platform.admin@blitz-training.local", "IT Operations")
        )
    # Replace older machine-generated sample passwords with human-readable lab credentials.
    cur.execute("SELECT id, password FROM users WHERE username <> %s", (config["admin_username"],))
    for old_id, old_password in cur.fetchall():
        if not re.fullmatch(r"[A-Z][a-z]+[A-Z][a-z]+!\d{2}", old_password or ""):
            cur.execute("UPDATE users SET password=%s WHERE id=%s", (make_readable_password(), old_id))
    first_names = ["Aarav", "Maya", "Ishaan", "Anika", "Rohan", "Diya", "Kabir", "Meera", "Arjun", "Tara", "Neil", "Sana", "Dev", "Ira", "Kiran", "Zoya", "Adrian", "Nina", "Ethan", "Leah"]
    last_names = ["Sharma", "Nair", "Menon", "Patel", "Rao", "Thomas", "Iyer", "Kapoor", "Fernandes", "Das", "Pillai", "Morris", "Reed", "Bennett", "D'Souza", "Varma"]
    departments = ["Customer Support", "Security Operations", "Inventory", "Finance", "Logistics", "Marketing", "IT Operations", "Compliance", "Sales", "Procurement"]
    roles = ["customer", "support", "analyst", "inventory", "auditor"]
    cur.execute("SELECT COUNT(*) FROM users")
    current_user_count = cur.fetchone()[0]
    cur.execute("SELECT username FROM users")
    used_users = {r[0] for r in cur.fetchall()}
    user_rows=[]
    for i in range(current_user_count + 1, 1201):
        first=random.choice(first_names); last=random.choice(last_names)
        username=f"{first.lower()}.{last.lower().replace(chr(39), '')}{i:04d}"
        if username in used_users: continue
        used_users.add(username)
        email=f"{first.lower()}.{last.lower().replace(chr(39), '')}{i:04d}@blitz-training.local"
        user_rows.append((username, make_readable_password(), random.choice(roles), email, random.choice(departments), "active" if i % 17 else "disabled"))
    cur.executemany("INSERT IGNORE INTO users (username,password,role,email,department,account_status) VALUES (%s,%s,%s,%s,%s,%s)", user_rows)
    cur.execute("SELECT username FROM users")
    usernames = [r[0] for r in cur.fetchall() if r[0] != config["admin_username"]]

    product_names=["Wireless Charging Pad", "USB-C Hub", "Studio Microphone", "Ergonomic Laptop Stand", "Portable SSD", "Bluetooth Speaker", "Mechanical Keyboard", "Dual-Band Router", "Webcam Privacy Cover", "Noise-Cancelling Headphones", "Smart LED Strip", "Gaming Mouse Pad", "Travel Power Adapter", "HDMI Capture Card", "Laptop Sleeve", "Desk Monitor Light", "USB Conference Speaker", "Compact Card Reader"]
    categories=["Accessories", "Storage", "Audio", "Networking", "Peripherals", "Displays"]
    existing_skus=set()
    cur.execute("SELECT sku FROM products")
    existing_skus={r[0] for r in cur.fetchall()}
    product_rows=[]
    for i in range(1, 121):
        sku=f"BZ-{i+100:04d}"
        if sku in existing_skus: continue
        name=f"{random.choice(product_names)} {random.choice(['Lite','Pro','Plus','Air','X'])} {i}"
        product_rows.append((sku,name,random.choice(categories),f"Reliable everyday technology with a considered design, tested for the BLITZ Store catalogue. Model reference {sku}.",round(random.uniform(399,18999),2),random.randint(0,180)))
    cur.executemany("INSERT IGNORE INTO products (sku,name,category,description,price,stock) VALUES (%s,%s,%s,%s,%s,%s)",product_rows)

    cur.execute("SELECT order_ref FROM orders")
    existing_orders={r[0] for r in cur.fetchall()}
    usernames=list(used_users - {config["admin_username"]})
    cur.execute("SELECT sku FROM products")
    skus=[r[0] for r in cur.fetchall()]
    order_rows=[]
    statuses=["processing","shipped","delivered","pending","refunded"]
    for i in range(1, 3501):
        ref=f"ORD-{i:06d}"
        if ref not in existing_orders:
            order_rows.append((ref,random.choice(usernames),random.choice(skus),random.randint(1,5),random.choice(statuses)))
    cur.executemany("INSERT IGNORE INTO orders (order_ref,customer_username,product_sku,quantity,order_status) VALUES (%s,%s,%s,%s,%s)",order_rows)

    cur.execute("SELECT ticket_ref FROM support_tickets")
    existing_tickets={r[0] for r in cur.fetchall()}
    ticket_rows=[]
    subjects=["Delivery status request","Warranty registration","Invoice correction","Unexpected sign-in notification","Product replacement request","Payment confirmation","Account email update","Order cancellation request"]
    for i in range(1, 901):
        ref=f"TKT-{i:06d}"
        if ref not in existing_tickets:
            ticket_rows.append((ref,random.choice(usernames),random.choice(subjects),random.choice(["low","medium","high"]),random.choice(["open","closed","investigating","pending"])))
    cur.executemany("INSERT IGNORE INTO support_tickets (ticket_ref,submitted_by,subject,priority,status) VALUES (%s,%s,%s,%s,%s)",ticket_rows)

    cur.execute("SELECT COUNT(*) FROM customer_addresses")
    if cur.fetchone()[0] == 0:
        cities=[("Kochi","Kerala"),("Bengaluru","Karnataka"),("Chennai","Tamil Nadu"),("Hyderabad","Telangana"),("Pune","Maharashtra"),("Mumbai","Maharashtra"),("Thrissur","Kerala"),("Coimbatore","Tamil Nadu")]
        address_rows=[(u,*random.choice(cities),str(random.randint(100000,999999)),random.choice(["home","work"])) for u in usernames[:1000]]
        cur.executemany("INSERT INTO customer_addresses (username,city,state,postal_code,address_type) VALUES (%s,%s,%s,%s,%s)",address_rows)
    cur.execute("SELECT COUNT(*) FROM payments")
    if cur.fetchone()[0] == 0:
        cur.execute("SELECT order_ref FROM orders")
        refs=[r[0] for r in cur.fetchall()]
        payment_rows=[(f"PAY-{i:07d}",ref,random.choice(["UPI","Credit Card","Debit Card","Net Banking"]),round(random.uniform(399,25000),2),random.choice(["success","success","pending","refunded"])) for i,ref in enumerate(refs[:2500],1)]
        cur.executemany("INSERT INTO payments (payment_ref,order_ref,payment_method,amount,payment_status) VALUES (%s,%s,%s,%s,%s)",payment_rows)
    cur.execute("SELECT COUNT(*) FROM audit_logs")
    if cur.fetchone()[0] == 0:
        actions=["LOGIN_SUCCESS","LOGIN_FAILED","PRODUCT_VIEW","CART_UPDATED","ORDER_CREATED","PASSWORD_RESET_REQUEST","PROFILE_UPDATED","LOGOUT"]
        audit_rows=[]
        for i in range(5000):
            audit_rows.append((random.choice(usernames),random.choice(actions),f"192.0.2.{random.randint(1,254)}",f"2026-{random.randint(1,11):02d}-{random.randint(1,28):02d} {random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}",random.choice(["success","denied"])) )
        cur.executemany("INSERT INTO audit_logs (username,action,source_ip,event_time,result) VALUES (%s,%s,%s,%s,%s)",audit_rows)

    conn.commit()
    cur.close()
    conn.close()

@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    search = request.args.get("q", "").strip()
    category = request.args.get("category", "").strip()
    sql = "SELECT * FROM products WHERE 1=1"
    params = []
    if search:
        sql += " AND (name LIKE %s OR sku LIKE %s OR description LIKE %s)"
        params.extend([f"%{search}%"] * 3)
    if category:
        sql += " AND category=%s"
        params.append(category)
    sql += " ORDER BY id LIMIT 16"
    cur.execute(sql, params)
    products = cur.fetchall()
    cur.execute("SELECT DISTINCT category FROM products ORDER BY category")
    categories = [r["category"] for r in cur.fetchall()]
    cur.close()
    conn.close()
    image_map = {
        "BZ-AX41": "https://images.unsplash.com/photo-1527814050087-3793815479db?w=900&q=85",
        "BZ-KB82": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=900&q=85",
        "BZ-ST19": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=900&q=85",
        "BZ-HD57": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=900&q=85",
        "BZ-WC33": "https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=900&q=85",
        "BZ-MN64": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=900&q=85",
        "BZ-HS28": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=900&q=85",
        "BZ-NW73": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=900&q=85",
    }
    for product in products:
        product["image_url"] = image_map.get(product["sku"], "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=1200&q=85")
    return render_template("index.html", products=products, categories=categories, search=search, selected_category=category)

@app.route("/product")
def product():
    product_id = request.args.get("id", "1")
    conn = get_db()
    cur = conn.cursor(dictionary=True)
    try:
        # INTENTIONALLY VULNERABLE: unsafe interpolation for this isolated SQLi exercise.
        query = f"SELECT * FROM products WHERE id = {product_id}"
        cur.execute(query)
        rows = cur.fetchall()
        image_map = {
            "BZ-AX41": "https://images.unsplash.com/photo-1527814050087-3793815479db?w=1200&q=85",
            "BZ-KB82": "https://images.unsplash.com/photo-1587829741301-dc798b83add3?w=1200&q=85",
            "BZ-ST19": "https://images.unsplash.com/photo-1591488320449-011701bb6704?w=1200&q=85",
            "BZ-HD57": "https://images.unsplash.com/photo-1597872200969-2b65d56bd16b?w=1200&q=85",
            "BZ-WC33": "https://images.unsplash.com/photo-1587826080692-f439cd0b70da?w=1200&q=85",
            "BZ-MN64": "https://images.unsplash.com/photo-1527443224154-c4a3942d3acf?w=1200&q=85",
            "BZ-HS28": "https://images.unsplash.com/photo-1505740420928-5e560c06d30e?w=1200&q=85",
            "BZ-NW73": "https://images.unsplash.com/photo-1558618666-fcd25c85cd64?w=1200&q=85",
        }
        for product in rows:
            product["image_url"] = image_map.get(product["sku"], "https://images.unsplash.com/photo-1498049794561-7780e7231661?w=1200&q=85")
        return render_template("product.html", products=rows, product_id=product_id)
    except Error as exc:
        # Deliberately visible SQL error for this isolated SQL injection exercise.
        return render_template("product.html", products=[], product_id=product_id,
                               error=str(exc)), 500
    finally:
        cur.close()
        conn.close()

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "")
        password = request.form.get("password", "")
        conn = get_db()
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT * FROM users WHERE username=%s AND password=%s", (username, password))
        user = cur.fetchone()
        cur.close()
        conn.close()
        if user and user["account_status"] == "active":
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("home"))
        flash("Invalid credentials or inactive account.", "error")
    return render_template("login.html")

@app.route("/home")
def home():
    if not session.get("username"):
        return redirect(url_for("login"))
    cfg = create_lab_config()
    is_admin = session.get("role") == "admin"
    return render_template("home.html", username=session["username"],
                           role=session["role"], is_admin=is_admin,
                           final_flag=cfg["final_flag"] if is_admin else None)

@app.route("/dashboard")
def dashboard():
    return redirect(url_for("home"))

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))

def get_lan_ip():
    s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        s.connect(("192.0.2.1", 80))
        return s.getsockname()[0]
    except OSError:
        return "YOUR-KALI-IP"
    finally:
        s.close()

if __name__ == "__main__":
    import time
    for attempt in range(20):
        try:
            init_db()
            break
        except Error as exc:
            if attempt == 19:
                print("\\n[BLITZ SQLi Lab] Database connection failed.")
                print("Run the setup script and confirm MariaDB/MySQL is running.")
                print(f"Details: {exc}")
                raise SystemExit(1)
            print(f"[BLITZ SQLi Lab] Waiting for local database ({attempt + 1}/20)...")
            time.sleep(2)
    ip = get_lan_ip()
    print("\\n[BLITZ SQLi Lab] Local URL: http://127.0.0.1:5000")
    print(f"[BLITZ SQLi Lab] Network URL: http://{ip}:5000")
    print("[!] Vulnerable endpoint: /product?id=1")
    print("[!] Isolated, trusted lab network only. Do not expose publicly.")
    app.run(host="0.0.0.0", port=5000, debug=False)
