from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime, timedelta
from reservabook_db import get_connection, ensure_schema

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}})

# Initialize database connection
try:
    conn = get_connection()
    ensure_schema(conn)
    print("✅ Database connection established!")
except Exception as e:
    print(f"❌ Database connection failed: {e}")
    conn = None

def _price_to_str(cents: int) -> str:
    """Convert price in cents to formatted string"""
    return f"${cents/100:.0f}" if cents % 100 == 0 else f"${cents/100:.2f}"

# ========== SERVICES CRUD ==========

@app.route("/api/services", methods=["GET"])
def get_services():
    """Get all services"""
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, code, name, duration_min, price_cents FROM services ORDER BY id")
        rows = cur.fetchall()
        cur.close()
        return jsonify([
            {
                "id": r["id"],
                "code": r["code"],
                "name": r["name"],
                "duration_min": r["duration_min"],
                "price": _price_to_str(r["price_cents"]),
            } for r in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/services/<string:code>", methods=["GET"])
def get_service(code):
    """Get single service by code"""
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("SELECT id, code, name, duration_min, price_cents FROM services WHERE code=%s", (code,))
        row = cur.fetchone()
        cur.close()
        if not row:
            return jsonify({"error": "Service not found"}), 404
        return jsonify({
            "id": row["id"],
            "code": row["code"],
            "name": row["name"],
            "duration_min": row["duration_min"],
            "price": _price_to_str(row["price_cents"]),
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== BOOKINGS CRUD ==========

@app.route("/api/bookings", methods=["GET"])
def get_bookings():
    """Get all bookings (with optional filters)"""
    try:
        email = request.args.get("email")
        date = request.args.get("date")
        
        cur = conn.cursor(dictionary=True)
        query = """
            SELECT b.id, b.service_code, b.booking_date, b.booking_time,
                   b.first_name, b.last_name, b.email, b.phone, b.notes,
                   b.created_at, s.name as service_name
            FROM bookings b
            JOIN services s ON s.code = b.service_code
            WHERE 1=1
        """
        params = []
        
        if email:
            query += " AND b.email = %s"
            params.append(email)
        if date:
            query += " AND b.booking_date = %s"
            params.append(date)
        
        query += " ORDER BY b.booking_date DESC, b.booking_time DESC"
        
        cur.execute(query, params)
        rows = cur.fetchall()
        cur.close()
        
        return jsonify([
            {
                "id": r["id"],
                "service_code": r["service_code"],
                "service_name": r["service_name"],
                "booking_date": r["booking_date"].isoformat() if r["booking_date"] else None,
                "booking_time": r["booking_time"],
                "first_name": r["first_name"],
                "last_name": r["last_name"],
                "email": r["email"],
                "phone": r["phone"],
                "notes": r["notes"],
                "created_at": r["created_at"].isoformat() if r["created_at"] else None,
            } for r in rows
        ])
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bookings/<int:booking_id>", methods=["GET"])
def get_booking(booking_id):
    """Get single booking by ID"""
    try:
        cur = conn.cursor(dictionary=True)
        cur.execute("""
            SELECT b.id, b.service_code, b.booking_date, b.booking_time,
                   b.first_name, b.last_name, b.email, b.phone, b.notes,
                   b.created_at, s.name as service_name
            FROM bookings b
            JOIN services s ON s.code = b.service_code
            WHERE b.id = %s
        """, (booking_id,))
        row = cur.fetchone()
        cur.close()
        
        if not row:
            return jsonify({"error": "Booking not found"}), 404
        
        return jsonify({
            "id": row["id"],
            "service_code": row["service_code"],
            "service_name": row["service_name"],
            "booking_date": row["booking_date"].isoformat() if row["booking_date"] else None,
            "booking_time": row["booking_time"],
            "first_name": row["first_name"],
            "last_name": row["last_name"],
            "email": row["email"],
            "phone": row["phone"],
            "notes": row["notes"],
            "created_at": row["created_at"].isoformat() if row["created_at"] else None,
        })
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bookings", methods=["POST"])
def create_booking():
    """Create new booking"""
    try:
        data = request.get_json(silent=True) or {}
        required = ["service", "date", "time", "first_name", "last_name", "email", "phone"]
        missing = [k for k in required if not data.get(k)]
        if missing:
            return jsonify({"error": f"Missing fields: {', '.join(missing)}"}), 400

        # Validate date
        try:
            date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        cur = conn.cursor()
        
        # Verify service exists
        cur.execute("SELECT 1 FROM services WHERE code=%s", (data["service"],))
        if cur.fetchone() is None:
            cur.close()
            return jsonify({"error": "Unknown service"}), 400

        # Check for duplicate booking
        cur.execute(
            "SELECT id FROM bookings WHERE booking_date=%s AND booking_time=%s",
            (date_obj.isoformat(), data["time"]),
        )
        existing = cur.fetchone()
        if existing:
            cur.close()
            return jsonify({"error": "Time slot already booked"}), 409

        # Insert booking
        cur.execute("""
            INSERT INTO bookings (service_code, booking_date, booking_time, first_name, last_name, email, phone, notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        """, (
            data["service"],
            date_obj.isoformat(),
            data["time"],
            data["first_name"].strip(),
            data["last_name"].strip(),
            data["email"].strip(),
            data["phone"].strip(),
            (data.get("notes") or "").strip() or None,
        ))
        
        cur.execute("SELECT LAST_INSERT_ID()")
        (booking_id,) = cur.fetchone()
        cur.close()

        return jsonify({
            "message": "Booking confirmed",
            "booking_id": booking_id
        }), 201
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bookings/<int:booking_id>", methods=["PUT"])
def update_booking(booking_id):
    """Update existing booking"""
    try:
        data = request.get_json(silent=True) or {}
        
        cur = conn.cursor()
        
        # Check if booking exists
        cur.execute("SELECT id FROM bookings WHERE id=%s", (booking_id,))
        if cur.fetchone() is None:
            cur.close()
            return jsonify({"error": "Booking not found"}), 404

        # Build update query dynamically
        updates = []
        params = []
        
        if "service" in data:
            # Verify service exists
            cur.execute("SELECT 1 FROM services WHERE code=%s", (data["service"],))
            if cur.fetchone() is None:
                cur.close()
                return jsonify({"error": "Unknown service"}), 400
            updates.append("service_code = %s")
            params.append(data["service"])
        
        if "date" in data:
            try:
                date_obj = datetime.strptime(data["date"], "%Y-%m-%d").date()
                updates.append("booking_date = %s")
                params.append(date_obj.isoformat())
            except ValueError:
                cur.close()
                return jsonify({"error": "Invalid date format"}), 400
        
        if "time" in data:
            updates.append("booking_time = %s")
            params.append(data["time"])
        
        if "first_name" in data:
            updates.append("first_name = %s")
            params.append(data["first_name"].strip())
        
        if "last_name" in data:
            updates.append("last_name = %s")
            params.append(data["last_name"].strip())
        
        if "email" in data:
            updates.append("email = %s")
            params.append(data["email"].strip())
        
        if "phone" in data:
            updates.append("phone = %s")
            params.append(data["phone"].strip())
        
        if "notes" in data:
            updates.append("notes = %s")
            params.append((data["notes"] or "").strip() or None)

        if not updates:
            cur.close()
            return jsonify({"error": "No fields to update"}), 400

        # Check for duplicate booking if date/time changed
        if "date" in data or "time" in data:
            check_date = data.get("date")
            if check_date:
                try:
                    check_date_obj = datetime.strptime(check_date, "%Y-%m-%d").date()
                except:
                    check_date_obj = None
            else:
                cur.execute("SELECT booking_date FROM bookings WHERE id=%s", (booking_id,))
                result = cur.fetchone()
                check_date_obj = result[0] if result else None
            
            check_time = data.get("time")
            if not check_time:
                cur.execute("SELECT booking_time FROM bookings WHERE id=%s", (booking_id,))
                result = cur.fetchone()
                check_time = result[0] if result else None
            
            if check_date_obj and check_time:
                cur.execute(
                    "SELECT id FROM bookings WHERE booking_date=%s AND booking_time=%s AND id != %s",
                    (check_date_obj.isoformat(), check_time, booking_id),
                )
                if cur.fetchone():
                    cur.close()
                    return jsonify({"error": "Time slot already booked"}), 409

        # Execute update
        params.append(booking_id)
        query = f"UPDATE bookings SET {', '.join(updates)} WHERE id = %s"
        cur.execute(query, params)
        cur.close()

        return jsonify({"message": "Booking updated successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/api/bookings/<int:booking_id>", methods=["DELETE"])
def delete_booking(booking_id):
    """Delete booking"""
    try:
        cur = conn.cursor()
        cur.execute("SELECT id FROM bookings WHERE id=%s", (booking_id,))
        if cur.fetchone() is None:
            cur.close()
            return jsonify({"error": "Booking not found"}), 404

        cur.execute("DELETE FROM bookings WHERE id=%s", (booking_id,))
        cur.close()
        return jsonify({"message": "Booking deleted successfully"})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ========== TIME SLOTS ==========

@app.route("/api/slots", methods=["GET"])
def get_slots():
    """Get available time slots for a date"""
    date_str = request.args.get("date")
    if not date_str:
        return jsonify({"error": "Missing date parameter (YYYY-MM-DD)"}), 400
    
    try:
        day = datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    # Fetch booked times
    cur = conn.cursor()
    cur.execute("SELECT booking_time FROM bookings WHERE booking_date=%s", (date_str,))
    booked = {t[0] for t in cur.fetchall()}
    cur.close()

    # Generate time slots (9 AM to 5 PM, 30-minute intervals)
    start = day.replace(hour=9, minute=0)
    end = day.replace(hour=17, minute=0)
    slots = []
    now = datetime.now()
    t = start
    
    while t <= end:
        label = t.strftime("%I:%M %p").lstrip("0")
        is_past = (t < now and t.date() == now.date())
        is_booked = label in booked
        
        slots.append({
            "time": label,
            "available": not is_past and not is_booked,
            "booked": is_booked
        })
        t += timedelta(minutes=30)
    
    return jsonify(slots)

# ========== HEALTH CHECK ==========

@app.route("/", methods=["GET"])
def health():
    """Health check endpoint"""
    return jsonify({
        "message": "Reservabook API is running",
        "status": "healthy",
        "endpoints": {
            "services": "GET /api/services",
            "service": "GET /api/services/<code>",
            "bookings": "GET /api/bookings",
            "booking": "GET /api/bookings/<id>",
            "create_booking": "POST /api/bookings",
            "update_booking": "PUT /api/bookings/<id>",
            "delete_booking": "DELETE /api/bookings/<id>",
            "slots": "GET /api/slots?date=YYYY-MM-DD"
        }
    })

if __name__ == "__main__":
    if conn:
        print("🚀 Reservabook backend starting on http://127.0.0.1:5500")
        print("📊 API endpoints available at:")
        print("   GET  /api/services")
        print("   GET  /api/bookings")
        print("   POST /api/bookings")
        print("   PUT  /api/bookings/<id>")
        print("   DELETE /api/bookings/<id>")
        app.run(host="127.0.0.1", port=5500, debug=True)
    else:
        print("❌ Cannot start server: Database connection failed")

