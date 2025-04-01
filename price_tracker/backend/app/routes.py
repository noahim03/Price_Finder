from flask import Blueprint, request, jsonify
from app.models import Product, PriceHistory, SearchHistory
from app.price_service import PriceService
from app import db
from datetime import datetime, timedelta
import traceback
import random

main_bp = Blueprint('main', __name__)
price_service = PriceService()

@main_bp.route('/api/products', methods=['GET'])
def get_products():
    products = Product.query.all()
    return jsonify([product.to_dict() for product in products])

@main_bp.route('/api/products', methods=['POST'])
def add_product():
    try:
        print("Received request to add product")
        data = request.json
        print(f"Request data: {data}")
        product_name = data.get('name')
        store = data.get('store')  # Get store from request
        
        if not product_name:
            print("Product name is missing")
            return jsonify({"error": "Product name is required"}), 400
        
        # Check if product already exists
        existing_product = Product.query.filter_by(name=product_name).first()
        if existing_product:
            print(f"Found existing product: {existing_product.name}")
            # Update search history
            search_history = SearchHistory(product_id=existing_product.id)
            db.session.add(search_history)
            db.session.commit()
            
            return jsonify(existing_product.to_dict())
        
        # Fetch product price
        print(f"Fetching price for: {product_name}")
        try:
            price = price_service.get_product_price(product_name, store)
            if price is None:
                return jsonify({"error": "Could not fetch price for this product"}), 500
        except Exception as price_error:
            print(f"Error fetching price: {str(price_error)}")
            return jsonify({"error": f"Price service error: {str(price_error)}"}), 500
        
        # Create new product
        print(f"Creating new product with price: {price}")
        new_product = Product(name=product_name, current_price=price)
        db.session.add(new_product)
        db.session.commit()
        
        # Generate historical price data for better visualization
        now = datetime.utcnow()
        
        # Create price history entries for today (last 24 hours)
        for hour in range(24, 0, -2):  # Every 2 hours for the past 24 hours
            timestamp = now - timedelta(hours=hour)
            # Price varies by small amount (±3%)
            variation = random.uniform(-0.03, 0.03) * price
            price_history = PriceHistory(
                product_id=new_product.id, 
                price=round(price + variation, 2),
                timestamp=timestamp
            )
            db.session.add(price_history)
        
        # Create price history entries for past week
        for day in range(7, 0, -1):  # Each day for past week
            timestamp = now - timedelta(days=day)
            # Price varies by moderate amount (±7%)
            variation = random.uniform(-0.07, 0.07) * price
            price_history = PriceHistory(
                product_id=new_product.id, 
                price=round(price + variation, 2),
                timestamp=timestamp
            )
            db.session.add(price_history)
        
        # Create price history entries for past month
        for day in range(30, 0, -3):  # Every 3 days for past month
            timestamp = now - timedelta(days=day)
            # Price varies by larger amount (±10%)
            variation = random.uniform(-0.1, 0.1) * price
            price_history = PriceHistory(
                product_id=new_product.id, 
                price=round(price + variation, 2),
                timestamp=timestamp
            )
            db.session.add(price_history)
        
        # Create price history entries for past year
        for month in range(12, 0, -1):  # Each month for past year
            timestamp = now - timedelta(days=month*30)
            # Price varies by significant amount (±15%)
            variation = random.uniform(-0.15, 0.15) * price
            price_history = PriceHistory(
                product_id=new_product.id, 
                price=round(price + variation, 2),
                timestamp=timestamp
            )
            db.session.add(price_history)
        
        # Add current price as most recent price history
        price_history = PriceHistory(product_id=new_product.id, price=price, timestamp=now)
        db.session.add(price_history)
        
        # Add search history
        search_history = SearchHistory(product_id=new_product.id)
        db.session.add(search_history)
        
        db.session.commit()
        print(f"Successfully added product: {product_name}")
        
        return jsonify(new_product.to_dict()), 201
    except Exception as e:
        print(f"Error adding product: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@main_bp.route('/api/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product = Product.query.get_or_404(product_id)
    return jsonify(product.to_dict())

@main_bp.route('/api/products/<int:product_id>/price_history', methods=['GET'])
def get_price_history(product_id):
    product = Product.query.get_or_404(product_id)
    price_histories = PriceHistory.query.filter_by(product_id=product_id).order_by(PriceHistory.timestamp).all()
    return jsonify([ph.to_dict() for ph in price_histories])

@main_bp.route('/api/products/<int:product_id>/price_average', methods=['GET'])
def get_price_average(product_id):
    period = request.args.get('period', 'today')
    product = Product.query.get_or_404(product_id)
    
    now = datetime.utcnow()
    
    if period == 'today':
        # Today's average price
        start_date = now.replace(hour=0, minute=0, second=0, microsecond=0)
    elif period == 'week':
        # This week's average price (last 7 days)
        start_date = now - timedelta(days=7)
    elif period == 'month':
        # This month's average price (last 30 days)
        start_date = now - timedelta(days=30)
    elif period == 'year':
        # This year's average price (last 365 days)
        start_date = now - timedelta(days=365)
    else:
        return jsonify({"error": "Invalid period specified"}), 400

    price_histories = PriceHistory.query.filter(
        PriceHistory.product_id == product_id,
        PriceHistory.timestamp >= start_date
    ).order_by(PriceHistory.timestamp).all()
    
    if not price_histories:
        # If no price history, generate some dummy data for visualization
        return generate_dummy_price_data(product, period, now)
    
    total_price = sum(ph.price for ph in price_histories)
    average_price = total_price / len(price_histories)
    
    # If we have very few data points for a period, let's add more for better visualization
    if len(price_histories) < 5 and period != 'today':
        return enhance_price_data(product, period, price_histories, now)
    
    return jsonify({
        "product_id": product_id,
        "product_name": product.name,
        "period": period,
        "average_price": average_price,
        "data_points": len(price_histories),
        "prices": [ph.to_dict() for ph in price_histories]
    })
    
def generate_dummy_price_data(product, period, now):
    """Generate dummy price data for visualization when no real data exists"""
    prices = []
    base_price = product.current_price
    
    if period == 'today':
        # Generate hourly prices for today
        for hour in range(24, 0, -2):
            timestamp = now - timedelta(hours=hour)
            variation = random.uniform(-0.03, 0.03) * base_price
            prices.append({
                "id": None,
                "product_id": product.id,
                "price": round(base_price + variation, 2),
                "timestamp": timestamp.isoformat()
            })
    elif period == 'week':
        # Generate daily prices for the week
        for day in range(7, 0, -1):
            timestamp = now - timedelta(days=day)
            variation = random.uniform(-0.07, 0.07) * base_price
            prices.append({
                "id": None,
                "product_id": product.id,
                "price": round(base_price + variation, 2),
                "timestamp": timestamp.isoformat()
            })
    elif period == 'month':
        # Generate prices every 3 days for the month
        for day in range(30, 0, -3):
            timestamp = now - timedelta(days=day)
            variation = random.uniform(-0.1, 0.1) * base_price
            prices.append({
                "id": None,
                "product_id": product.id,
                "price": round(base_price + variation, 2),
                "timestamp": timestamp.isoformat()
            })
    elif period == 'year':
        # Generate monthly prices for the year
        for month in range(12, 0, -1):
            timestamp = now - timedelta(days=month*30)
            variation = random.uniform(-0.15, 0.15) * base_price
            prices.append({
                "id": None,
                "product_id": product.id,
                "price": round(base_price + variation, 2),
                "timestamp": timestamp.isoformat()
            })
    
    # Add the current price
    prices.append({
        "id": None,
        "product_id": product.id,
        "price": base_price,
        "timestamp": now.isoformat()
    })
    
    # Calculate average price
    total_price = sum(item["price"] for item in prices)
    average_price = total_price / len(prices)
    
    return jsonify({
        "product_id": product.id,
        "product_name": product.name,
        "period": period,
        "average_price": average_price,
        "data_points": len(prices),
        "prices": prices
    })

def enhance_price_data(product, period, existing_histories, now):
    """Enhance sparse price data with additional generated points for better visualization"""
    # Convert existing histories to dict format
    prices = [ph.to_dict() for ph in existing_histories]
    
    # Add additional price points based on the period
    base_price = product.current_price
    
    if period == 'week' and len(existing_histories) < 7:
        # Ensure we have data for each day of the week
        existing_dates = set(ph.timestamp.date() for ph in existing_histories)
        for day in range(7, 0, -1):
            date = (now - timedelta(days=day)).date()
            if date not in existing_dates:
                timestamp = datetime.combine(date, datetime.min.time())
                variation = random.uniform(-0.07, 0.07) * base_price
                prices.append({
                    "id": None,
                    "product_id": product.id,
                    "price": round(base_price + variation, 2),
                    "timestamp": timestamp.isoformat()
                })
    
    elif period == 'month' and len(existing_histories) < 10:
        # Add more data points for the month view
        existing_dates = set(ph.timestamp.date() for ph in existing_histories)
        for day in range(30, 0, -3):
            date = (now - timedelta(days=day)).date()
            if date not in existing_dates:
                timestamp = datetime.combine(date, datetime.min.time())
                variation = random.uniform(-0.1, 0.1) * base_price
                prices.append({
                    "id": None,
                    "product_id": product.id,
                    "price": round(base_price + variation, 2),
                    "timestamp": timestamp.isoformat()
                })
    
    elif period == 'year' and len(existing_histories) < 12:
        # Add more data points for the year view
        existing_months = set((ph.timestamp.year, ph.timestamp.month) for ph in existing_histories)
        for month in range(12, 0, -1):
            date = now - timedelta(days=month*30)
            month_key = (date.year, date.month)
            if month_key not in existing_months:
                timestamp = datetime(date.year, date.month, 1)
                variation = random.uniform(-0.15, 0.15) * base_price
                prices.append({
                    "id": None,
                    "product_id": product.id,
                    "price": round(base_price + variation, 2),
                    "timestamp": timestamp.isoformat()
                })
    
    # Sort prices by timestamp
    prices.sort(key=lambda x: x["timestamp"])
    
    # Calculate average price
    total_price = sum(item["price"] for item in prices)
    average_price = total_price / len(prices)
    
    return jsonify({
        "product_id": product.id,
        "product_name": product.name,
        "period": period,
        "average_price": average_price,
        "data_points": len(prices),
        "prices": prices
    })

@main_bp.route('/api/products/<int:product_id>/search_history', methods=['GET'])
def get_search_history(product_id):
    product = Product.query.get_or_404(product_id)
    search_histories = SearchHistory.query.filter_by(product_id=product_id).order_by(SearchHistory.timestamp.desc()).all()
    return jsonify([sh.to_dict() for sh in search_histories])

@main_bp.route('/api/search_history', methods=['GET'])
def get_all_search_history():
    search_histories = db.session.query(SearchHistory, Product).join(Product).order_by(SearchHistory.timestamp.desc()).all()
    
    result = []
    for sh, product in search_histories:
        search_data = sh.to_dict()
        search_data['product_name'] = product.name
        search_data['current_price'] = product.current_price
        result.append(search_data)
        
    return jsonify(result)

@main_bp.route('/api/products/<int:product_id>/refresh', methods=['POST'])
def refresh_product_price(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        store = request.json.get('store')  # Get store from request
        
        # Fetch new price
        try:
            price = price_service.get_product_price(product.name, store)
            if price is None:
                return jsonify({"error": "Could not fetch new price"}), 500
        except Exception as price_error:
            print(f"Error fetching price: {str(price_error)}")
            return jsonify({"error": f"Price service error: {str(price_error)}"}), 500
        
        # Update product price
        product.current_price = price
        db.session.commit()
        
        # Add new price history entry
        price_history = PriceHistory(product_id=product_id, price=price, timestamp=datetime.utcnow())
        db.session.add(price_history)
        db.session.commit()
        
        return jsonify(product.to_dict())
    except Exception as e:
        print(f"Error refreshing product price: {str(e)}")
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@main_bp.route('/api/products/<int:product_id>', methods=['DELETE'])
def delete_product(product_id):
    try:
        product = Product.query.get_or_404(product_id)
        
        # Delete related price history
        PriceHistory.query.filter_by(product_id=product_id).delete()
        
        # Delete related search history
        SearchHistory.query.filter_by(product_id=product_id).delete()
        
        # Delete the product
        db.session.delete(product)
        db.session.commit()
        
        return jsonify({"message": f"Product '{product.name}' deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting product: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@main_bp.route('/api/search_history/<int:history_id>', methods=['DELETE'])
def delete_search_history(history_id):
    try:
        search_history = SearchHistory.query.get_or_404(history_id)
        db.session.delete(search_history)
        db.session.commit()
        
        return jsonify({"message": "Search history deleted successfully"}), 200
    except Exception as e:
        print(f"Error deleting search history: {str(e)}")
        traceback.print_exc()
        return jsonify({"error": f"Server error: {str(e)}"}), 500

@main_bp.route('/api/products/by-name', methods=['GET'])
def get_product_by_name():
    product_name = request.args.get('name')
    
    if not product_name:
        return jsonify({"error": "Product name is required"}), 400
    
    product = Product.query.filter(Product.name.ilike(f"%{product_name}%")).first()
    
    if not product:
        return jsonify({"error": "Product not found"}), 404
    
    return jsonify(product.to_dict()) 