from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import json, os, random
from datetime import datetime, timedelta
from collections import Counter, defaultdict

app = Flask(__name__, static_folder='.', static_url_path='')
CORS(app)

DB_FILE = 'submissions.json'
ANALYTICS_FILE = 'analytics.json'
RATINGS_FILE = 'ratings.json'
PAYMENTS_FILE = 'payments.json'
UPLOAD_FOLDER = 'uploads/results'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def load_db():
    if not os.path.exists(DB_FILE):
        return []
    try:
        with open(DB_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_db(data):
    with open(DB_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_analytics():
    if not os.path.exists(ANALYTICS_FILE):
        return {"visits": [], "pageViews": [], "events": []}
    try:
        with open(ANALYTICS_FILE, 'r') as f:
            return json.load(f)
    except:
        return {"visits": [], "pageViews": [], "events": []}

def save_analytics(data):
    with open(ANALYTICS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_ratings():
    if not os.path.exists(RATINGS_FILE):
        return []
    try:
        with open(RATINGS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_ratings(data):
    with open(RATINGS_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def load_payments():
    if not os.path.exists(PAYMENTS_FILE):
        return []
    try:
        with open(PAYMENTS_FILE, 'r') as f:
            return json.load(f)
    except:
        return []

def save_payments(data):
    with open(PAYMENTS_FILE, 'w') as f:
        json.dump(data, f, indent=2)


@app.route('/')
def serve_index():
    return send_from_directory('.', 'index.html')

@app.route('/admin')
def serve_admin():
    return send_from_directory('.', 'ADMIN-BACKEND-LIVE.html')

@app.route('/analytics')
def serve_analytics():
    return send_from_directory('.', 'ANALYTICS-STUDIO.html')

@app.route('/custom')
def serve_custom():
    return send_from_directory('.', 'CUSTOM-ANALYTICS.html')

@app.route('/api/track', methods=['POST'])
def track():
    try:
        data = request.get_json() or {}
        analytics = load_analytics()
        
        now = datetime.now()
        visit = {
            "id": f"V-{random.randint(10000,99999)}",
            "timestamp": now.isoformat(),
            "date": now.strftime("%Y-%m-%d"),
            "time": now.strftime("%H:%M:%S"),
            "page": data.get('page', '/'),
            "service": data.get('service', ''),
            "action": data.get('action', 'view'),
            "userAgent": request.headers.get('User-Agent', '')[:200],
            "ip": request.remote_addr,
            "referrer": data.get('referrer', request.headers.get('Referer','')),
            "device": "Mobile" if "Mobile" in request.headers.get('User-Agent','') else "Desktop",
            "sessionId": data.get('sessionId', '')
        }
        
        analytics["visits"].append(visit)
        # Keep only last 5000 visits to avoid huge file
        if len(analytics["visits"]) > 5000:
            analytics["visits"] = analytics["visits"][-5000:]
        
        save_analytics(analytics)
        
        return jsonify({"success": True})
    except Exception as e:
        print(f"Track error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/analytics', methods=['GET'])
def get_analytics():
    analytics = load_analytics()
    db = load_db()
    
    visits = analytics.get("visits", [])
    now = datetime.now()
    
    # Calculate stats
    total_views = len(visits)
    unique_sessions = len(set(v.get('sessionId','') for v in visits if v.get('sessionId')))
    
    # Online now - visited in last 5 minutes
    five_min_ago = now - timedelta(minutes=5)
    online_visits = [v for v in visits if datetime.fromisoformat(v['timestamp']) > five_min_ago]
    online_now = len(set(v.get('sessionId','') for v in online_visits))
    
    # Views last 7 days
    last_7_days = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        count = len([v for v in visits if v.get('date')==day])
        last_7_days.append({"date": day, "count": count, "label": (now - timedelta(days=i)).strftime("%a")})
    
    # Top services
    services = [v.get('service','') for v in visits if v.get('service')]
    service_counts = Counter(services)
    top_services = [{"service": k or "General", "count": v} for k,v in service_counts.most_common(10)]
    
    # Device breakdown
    devices = Counter(v.get('device','Unknown') for v in visits)
    
    # Page views
    pages = Counter(v.get('page','/') for v in visits)
    
    # Recent visitors (last 20)
    recent = sorted(visits, key=lambda x: x['timestamp'], reverse=True)[:20]
    
    # Active now details
    active_now = sorted(online_visits, key=lambda x: x['timestamp'], reverse=True)[:10]
    
    # Hourly today
    hourly = []
    for h in range(24):
        count = len([v for v in visits if v.get('date')==now.strftime("%Y-%m-%d") and datetime.fromisoformat(v['timestamp']).hour==h])
        hourly.append({"hour": h, "count": count})
    
    return jsonify({
        "totalViews": total_views,
        "uniqueVisitors": unique_sessions,
        "onlineNow": online_now,
        "totalSubmissions": len(db),
        "last7Days": last_7_days,
        "topServices": top_services,
        "devices": dict(devices),
        "pages": dict(pages),
        "recentVisitors": recent,
        "activeNow": active_now,
        "hourlyToday": hourly,
        "allVisits": visits[-100:]  # Last 100 for table
    })

@app.route('/api/submit', methods=['POST'])
def submit():
    try:
        data = request.get_json() or request.form.to_dict()
        
        order_id = f"AH-{random.randint(1000, 9999)}"
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        submission = {
            "orderId": order_id,
            "date": now,
            "name": data.get('name',''),
            "phone": data.get('phone',''),
            "service": data.get('service',''),
            "topic": data.get('topic',''),
            "school": data.get('school',''),
            "dept": data.get('dept',''),
            "level": data.get('level',''),
            "pages": data.get('pages',''),
            "deadline": data.get('deadline',''),
            "supervisor": data.get('supervisor',''),
            "bizName": data.get('bizName',''),
            "bizType": data.get('bizType',''),
            "webNeeds": data.get('webNeeds',''),
            "budget": data.get('budget',''),
            "files": data.get('files', []),
            "notes": data.get('notes',''),
            "status": "New - Just Received"
        }
        
        db = load_db()
        db.insert(0, submission)
        save_db(db)
        
        # Also track as event
        analytics = load_analytics()
        analytics["visits"].append({
            "id": f"E-{random.randint(10000,99999)}",
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "page": "/#order",
            "service": submission["service"],
            "action": "submission",
            "userAgent": request.headers.get('User-Agent','')[:200],
            "ip": request.remote_addr,
            "sessionId": data.get('sessionId',''),
            "orderId": order_id
        })
        save_analytics(analytics)
        
        print(f"✅ NEW SUBMISSION: {order_id} - {submission['name']} - {submission['service']}")
        
        return jsonify({"success": True, "orderId": order_id, "data": submission})
    except Exception as e:
        print(f"Error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/submissions', methods=['GET'])
def get_submissions():
    db = load_db()
    return jsonify(db)

@app.route('/api/submissions/<order_id>/status', methods=['PUT'])
def update_status(order_id):
    try:
        data = request.get_json()
        new_status = data.get('status','')
        db = load_db()
        for sub in db:
            if sub['orderId'] == order_id:
                sub['status'] = new_status
                sub['updatedAt'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                save_db(db)
                return jsonify({"success": True})
        return jsonify({"success": False, "error": "Not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/submissions/<order_id>', methods=['DELETE'])
def delete_submission(order_id):
    db = load_db()
    db = [s for s in db if s['orderId'] != order_id]
    save_db(db)
    return jsonify({"success": True})

@app.route('/api/ratings', methods=['GET'])
def get_ratings():
    ratings = load_ratings()
    total = len(ratings)
    avg = sum(r.get('stars',0) for r in ratings) / total if total>0 else 0
    return jsonify({"ratings": ratings, "total": total, "average": round(avg,1)})

@app.route('/api/ratings', methods=['POST'])
def submit_rating():
    try:
        data = request.get_json() or {}
        ratings = load_ratings()
        
        rating = {
            "id": f"R-{random.randint(10000,99999)}",
            "stars": int(data.get('stars',5)),
            "name": data.get('name','Anonymous'),
            "review": data.get('review',''),
            "service": data.get('service',''),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": datetime.now().isoformat()
        }
        
        ratings.insert(0, rating)
        if len(ratings) > 200:
            ratings = ratings[:200]
        save_ratings(ratings)
        
        print(f"⭐ NEW RATING: {rating['stars']} stars from {rating['name']}")
        
        return jsonify({"success": True, "rating": rating})
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/payments', methods=['GET'])
def get_payments():
    payments = load_payments()
    total_revenue = sum(p.get('amount',0) for p in payments if p.get('status')=='success')
    today_str = datetime.now().strftime("%Y-%m-%d")
    today_revenue = sum(p.get('amount',0) for p in payments if p.get('date','').startswith(today_str) and p.get('status')=='success')
    # This month
    month_str = datetime.now().strftime("%Y-%m")
    month_revenue = sum(p.get('amount',0) for p in payments if p.get('date','').startswith(month_str) and p.get('status')=='success')
    return jsonify({"payments": payments, "total": len(payments), "totalRevenue": total_revenue, "todayRevenue": today_revenue, "monthRevenue": month_revenue})

@app.route('/api/payments', methods=['POST'])
def create_payment():
    try:
        data = request.get_json() or {}
        payments = load_payments()
        
        payment = {
            "id": f"PAY-{random.randint(10000,99999)}",
            "reference": data.get('reference', f"REF-{random.randint(100000,999999)}"),
            "name": data.get('name',''),
            "email": data.get('email',''),
            "phone": data.get('phone',''),
            "service": data.get('service',''),
            "orderId": data.get('orderId',''),
            "amount": int(data.get('amount',0)),
            "status": data.get('status','success'),
            "gateway": data.get('gateway','paystack'),
            "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "timestamp": datetime.now().isoformat()
        }
        
        payments.insert(0, payment)
        if len(payments) > 500:
            payments = payments[:500]
        save_payments(payments)
        
        # Also track as analytics event
        analytics = load_analytics()
        analytics["visits"].append({
            "id": f"PAY-{random.randint(10000,99999)}",
            "timestamp": datetime.now().isoformat(),
            "date": datetime.now().strftime("%Y-%m-%d"),
            "time": datetime.now().strftime("%H:%M:%S"),
            "page": "/#pay",
            "service": payment["service"],
            "action": "payment",
            "userAgent": request.headers.get('User-Agent','')[:200],
            "ip": request.remote_addr,
            "sessionId": data.get('sessionId',''),
            "orderId": payment["orderId"],
            "amount": payment["amount"]
        })
        save_analytics(analytics)
        
        print(f"💰 NEW PAYMENT: ₦{payment['amount']} from {payment['name']} - {payment['service']}")
        
        return jsonify({"success": True, "payment": payment})
    except Exception as e:
        print(f"Payment error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/revenue', methods=['GET'])
def get_revenue():
    payments = load_payments()
    now = datetime.now()
    total = sum(p.get('amount',0) for p in payments if p.get('status')=='success')
    today = sum(p.get('amount',0) for p in payments if p.get('date','').startswith(now.strftime("%Y-%m-%d")) and p.get('status')=='success')
    week_ago = now - timedelta(days=7)
    week = sum(p.get('amount',0) for p in payments if p.get('status')=='success' and datetime.fromisoformat(p['timestamp']) > week_ago)
    month = sum(p.get('amount',0) for p in payments if p.get('date','').startswith(now.strftime("%Y-%m")) and p.get('status')=='success')
    
    # Daily last 7 days revenue
    daily = []
    for i in range(6, -1, -1):
        day = (now - timedelta(days=i)).strftime("%Y-%m-%d")
        amt = sum(p.get('amount',0) for p in payments if p.get('date','').startswith(day) and p.get('status')=='success')
        daily.append({"date": day, "label": (now - timedelta(days=i)).strftime("%a"), "amount": amt})
    
    # By service
    by_service = {}
    for p in payments:
        if p.get('status')=='success':
            svc = p.get('service','General') or 'General'
            by_service[svc] = by_service.get(svc,0) + p.get('amount',0)
    
    return jsonify({
        "totalRevenue": total,
        "todayRevenue": today,
        "weekRevenue": week,
        "monthRevenue": month,
        "totalPayments": len([p for p in payments if p.get('status')=='success']),
        "dailyRevenue": daily,
        "byService": by_service,
        "payments": payments[:50]
    })

# ===== CLIENT PORTAL - TRACK ORDER & DOWNLOAD =====
@app.route('/api/track/<order_id>', methods=['GET'])
def track_order(order_id):
    db = load_db()
    order = next((s for s in db if s['orderId'].upper() == order_id.upper()), None)
    if not order:
        return jsonify({"success": False, "error": "Order not found"}), 404
    # Check if result file exists
    result_files = []
    result_dir = UPLOAD_FOLDER
    if os.path.exists(result_dir):
        for f in os.listdir(result_dir):
            if f.startswith(order_id):
                result_files.append(f)
    return jsonify({"success": True, "order": order, "resultFiles": result_files})

@app.route('/api/client/<phone>', methods=['GET'])
def client_orders(phone):
    db = load_db()
    clean_phone = ''.join(filter(str.isdigit, phone))[-10:]  # last 10 digits
    orders = [s for s in db if clean_phone in ''.join(filter(str.isdigit, s.get('phone','')))]
    return jsonify({"success": True, "orders": orders, "total": len(orders)})

@app.route('/api/submissions/<order_id>/result', methods=['POST'])
def upload_result(order_id):
    try:
        db = load_db()
        order = next((s for s in db if s['orderId'] == order_id), None)
        if not order:
            return jsonify({"success": False, "error": "Order not found"}), 404
        
        if 'file' not in request.files:
            return jsonify({"success": False, "error": "No file"}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({"success": False, "error": "No file selected"}), 400
        
        # Secure filename with orderId prefix
        ext = file.filename.rsplit('.', 1)[-1] if '.' in file.filename else 'pdf'
        filename = f"{order_id}_result_{datetime.now().strftime('%Y%m%d_%H%M%S')}.{ext}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)
        
        # Update order
        for sub in db:
            if sub['orderId'] == order_id:
                sub['resultFile'] = filename
                sub['resultUploadedAt'] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                sub['status'] = request.form.get('status', 'Ready for Download')
                sub['adminNote'] = request.form.get('note', '')
                save_db(db)
                break
        
        print(f"📤 RESULT UPLOADED: {order_id} -> {filename}")
        return jsonify({"success": True, "filename": filename, "orderId": order_id})
    except Exception as e:
        print(f"Upload result error: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/results/<filename>')
def download_result(filename):
    # Security: only allow files in UPLOAD_FOLDER
    return send_from_directory(UPLOAD_FOLDER, filename, as_attachment=True)

@app.route('/api/download/<order_id>')
def download_by_order(order_id):
    db = load_db()
    order = next((s for s in db if s['orderId'] == order_id), None)
    if not order or not order.get('resultFile'):
        return jsonify({"success": False, "error": "No result file"}), 404
    return send_from_directory(UPLOAD_FOLDER, order['resultFile'], as_attachment=True)

@app.route('/<path:path>')
def serve_static(path):
    if os.path.exists(path):
        return send_from_directory('.', path)
    return send_from_directory('.', 'FINAL-WITH-WEBSITE-DEV.html')

if __name__ == '__main__':
    print("🚀 Classic Research Institute Backend + Analytics Starting...")
    print("📂 Main: http://localhost:8000/")
    print("📊 Admin: http://localhost:8000/admin")
    print("📈 Analytics (YouTube Studio): http://localhost:8000/analytics")
    print("📡 API: http://localhost:8000/api/analytics")
    print("💰 Payments: http://localhost:8000/api/payments")
    if not os.path.exists(DB_FILE):
        save_db([])
    if not os.path.exists(ANALYTICS_FILE):
        save_analytics({"visits": [], "pageViews": [], "events": []})
    if not os.path.exists(RATINGS_FILE):
        save_ratings([])
    if not os.path.exists(PAYMENTS_FILE):
        save_payments([])
    app.run(host='0.0.0.0', port=8000, debug=True)
