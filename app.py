from flask import Flask, render_template, request, redirect, url_for, flash, session, send_file, current_app, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import os
from werkzeug.utils import secure_filename
from reportlab.pdfgen import canvas
from io import BytesIO
from models import db, User, Product, PurchaseOrder, OrderItem, Feedback, Brand
from routes import main
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from forms import RegistrationForm

app = Flask(__name__)
app.config['SECRET_KEY'] = 'Enter_your_SECRET_KEY'
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql://username:password@localhost/database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['UPLOAD_FOLDER'] = 'static/uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

# Initialize database
db.init_app(app)

# Create database tables
with app.app_context():
    try:
        print("Creating database tables...")
        db.create_all()
        print("Database tables created successfully")
    except Exception as e:
        print(f"Error creating database tables: {str(e)}")

# Initialize login manager
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Register blueprints
app.register_blueprint(main)

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Routes
@app.route('/')
def home():
    brands = Brand.query.all()
    return render_template('home.html', brands=brands)

@app.route('/brand/<int:brand_id>')
def brand_products(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    products = Product.query.filter_by(brand_id=brand_id).all()
    return render_template('brand_products.html', brand=brand, products=products)

@app.route('/add_brand', methods=['GET', 'POST'])
@login_required
def add_brand():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        min_price = float(request.form['min_price'])
        max_price = float(request.form['max_price'])
        
        # Handle logo upload
        if 'logo' not in request.files:
            flash('No logo file selected')
            return redirect(request.url)
        
        file = request.files['logo']
        if file.filename == '':
            flash('No logo selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            logo_url = f"/static/uploads/{filename}"
        else:
            flash('Invalid file type')
            return redirect(request.url)
        
        brand = Brand(
            name=name,
            description=description,
            logo_url=logo_url,
            min_price=min_price,
            max_price=max_price
        )
        
        db.session.add(brand)
        db.session.commit()
        flash('Brand added successfully')
        return redirect(url_for('home'))
    
    return render_template('add_brand.html')

@app.route('/add_product', methods=['GET', 'POST'])
@login_required
def add_product():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = float(request.form['price'])
        stock_quantity = int(request.form['stock_quantity'])
        category = request.form['category']
        brand_id = int(request.form['brand_id'])
        
        # Handle image upload
        if 'image' not in request.files:
            flash('No image file selected')
            return redirect(request.url)
        
        file = request.files['image']
        if file.filename == '':
            flash('No image selected')
            return redirect(request.url)
        
        if file and allowed_file(file.filename):
            filename = secure_filename(file.filename)
            filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            image_url = f"/static/uploads/{filename}"
        else:
            flash('Invalid file type')
            return redirect(request.url)
        
        product = Product(
            name=name,
            description=description,
            price=price,
            image_url=image_url,
            stock_quantity=stock_quantity,
            category=category,
            brand_id=brand_id
        )
        
        db.session.add(product)
        db.session.commit()
        flash('Product added successfully')
        return redirect(url_for('brand_products', brand_id=brand_id))
    
    brands = Brand.query.all()
    return render_template('add_product.html', brands=brands)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        try:
            # Get form data
            username = request.form.get('username')
            user_id = request.form.get('user_id')
            email = request.form.get('email')
            phone = request.form.get('phone')
            password = request.form.get('password')
            password2 = request.form.get('password2')

            # Basic validation
            if not all([username, user_id, email, phone, password, password2]):
                flash('All fields are required', 'danger')
                return redirect(url_for('register'))

            if password != password2:
                flash('Passwords do not match', 'danger')
                return redirect(url_for('register'))

            # Check if user exists
            existing_user = User.query.filter(
                (User.username == username) | 
                (User.user_id == user_id) | 
                (User.email == email)
            ).first()

            if existing_user:
                if existing_user.username == username:
                    flash('Username already exists', 'danger')
                elif existing_user.user_id == user_id:
                    flash('User ID already exists', 'danger')
                else:
                    flash('Email already exists', 'danger')
                return redirect(url_for('register'))

            # Create new user
            user = User(
                username=username,
                user_id=user_id,
                email=email,
                phone=phone,
                created_at=datetime.utcnow()
            )
            user.set_password(password)

            # Save to database
            db.session.add(user)
            db.session.commit()

            flash('Registration successful! Please login.', 'success')
            return redirect(url_for('login'))

        except Exception as e:
            print(f"Error: {str(e)}")
            db.session.rollback()
            flash('An error occurred. Please try again.', 'danger')
            return redirect(url_for('register'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user_id = request.form.get('user_id')
        password = request.form.get('password')
        
        if not user_id or not password:
            flash('Please enter both User ID and password', 'danger')
            return redirect(url_for('login'))
            
        user = User.query.filter_by(user_id=user_id).first()
        
        if user and user.check_password(password):
            login_user(user)
            user.update_last_login()
            flash('Login successful!', 'success')
            return redirect(url_for('home'))
        
        flash('Invalid User ID or password', 'danger')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/product/<int:product_id>')
def product_detail(product_id):
    product = Product.query.get_or_404(product_id)
    related_products = Product.query.filter_by(category=product.category).limit(4).all()
    return render_template('product_detail.html', product=product, related_products=related_products)

@app.route('/add_to_cart/<int:product_id>')
@login_required
def add_to_cart(product_id):
    if not current_user.is_authenticated:
        flash('Please login to add items to cart')
        return redirect(url_for('login'))
        
    if 'cart' not in session:
        session['cart'] = {}
    
    cart = session['cart']
    if str(product_id) in cart:
        cart[str(product_id)] += 1
    else:
        cart[str(product_id)] = 1
    
    session['cart'] = cart
    flash('Product added to cart')
    return redirect(url_for('product_detail', product_id=product_id))

@app.route('/update_cart_quantity/<int:product_id>/<action>')
@login_required
def update_cart_quantity(product_id, action):
    if 'cart' not in session:
        return redirect(url_for('cart'))
    
    cart = session['cart']
    product_id_str = str(product_id)
    
    if product_id_str in cart:
        if action == 'increase':
            cart[product_id_str] += 1
        elif action == 'decrease':
            if cart[product_id_str] > 1:
                cart[product_id_str] -= 1
            else:
                del cart[product_id_str]
                flash('Item removed from cart')
                return redirect(url_for('cart'))
    
    session['cart'] = cart
    return redirect(url_for('cart'))

@app.route('/remove_from_cart/<int:product_id>')
@login_required
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    if str(product_id) in cart:
        del cart[str(product_id)]
        session['cart'] = cart
        flash('Item removed from cart')
    return redirect(url_for('cart'))

@app.route('/cart')
@login_required
def cart():
    cart = session.get('cart', {})
    products = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product:
            products.append({
                'product': product,
                'quantity': quantity,
                'subtotal': product.price * quantity
            })
            total += product.price * quantity
    
    return render_template('cart.html', products=products, total=total)

@app.route('/checkout', methods=['GET', 'POST'])
@login_required
def checkout():
    # Get cart items and calculate total
    cart = session.get('cart', {})
    products = []
    total = 0
    
    for product_id, quantity in cart.items():
        product = Product.query.get(product_id)
        if product:
            subtotal = product.price * quantity
            products.append({
                'product': product,
                'quantity': quantity,
                'subtotal': subtotal
            })
            total += subtotal

    if request.method == 'POST':
        payment_method = request.form['payment_method']
        
        # Create order
        order = PurchaseOrder(
            user_id=current_user.id,
            total_amount=total,
            status='Pending' if payment_method == 'cash_on_delivery' else 'Paid'
        )
        db.session.add(order)
        db.session.commit()
        
        # Add order items
        for product_id, quantity in cart.items():
            product = Product.query.get(product_id)
            if product:
                order_item = OrderItem(
                    purchase_order_id=order.id,
                    product_id=product.id,
                    quantity=quantity,
                    price=product.price
                )
                db.session.add(order_item)
        
        db.session.commit()
        
        # Clear cart
        session['cart'] = {}
        
        # Render the bill template
        return render_template('bill.html', order=order)
    
    return render_template('checkout.html', products=products, total=total)

@app.route('/submit_feedback/<int:order_id>', methods=['POST'])
@login_required
def submit_feedback(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Check if the order belongs to the current user
    if order.user_id != current_user.id:
        flash('You are not authorized to submit feedback for this order.')
        return redirect(url_for('home'))
    
    rating = request.form.get('rating')
    comment = request.form.get('comment')
    
    if not rating:
        flash('Please provide a rating.')
        return redirect(url_for('order_details', order_id=order_id))
    
    # Create or update feedback
    feedback = Feedback.query.filter_by(order_id=order_id).first()
    if feedback:
        feedback.rating = rating
        feedback.comment = comment
    else:
        feedback = Feedback(
            order_id=order_id,
            rating=rating,
            comment=comment
        )
        db.session.add(feedback)
    
    db.session.commit()
    flash('Thank you for your feedback!')
    return redirect(url_for('order_details', order_id=order_id))

@app.route('/order/<int:order_id>')
@login_required
def order_details(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    # Check if the order belongs to the current user
    if order.user_id != current_user.id:
        flash('You are not authorized to view this order.')
        return redirect(url_for('home'))
    
    return render_template('order_details.html', order=order)

@app.route('/order/<int:order_id>/download-bill')
@login_required
def download_bill(order_id):
    order = PurchaseOrder.query.get_or_404(order_id)
    
    if order.user_id != current_user.id:
        flash('You are not authorized to download this bill.')
        return redirect(url_for('home'))
    
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    story.append(Paragraph("Order Bill", styles['Title']))
    story.append(Spacer(1, 20))
    
    # Order Info
    story.append(Paragraph(f"Order ID: {order.id}", styles['Normal']))
    story.append(Paragraph(f"Date: {order.order_date.strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
    story.append(Paragraph(f"Customer: {order.customer.username}", styles['Normal']))
    story.append(Paragraph(f"Mobile: {order.customer.phone}", styles['Normal']))
    story.append(Spacer(1, 20))
    
    # Items Table
    data = [['Product', 'Quantity', 'Price', 'Subtotal']]
    for item in order.items:
        data.append([
            item.product.name,
            str(item.quantity),
            f"₹{item.price}",
            f"₹{item.price * item.quantity}"
        ])
    
    table = Table(data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 14),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 20))
    
    # Total
    story.append(Paragraph(f"Total Amount: ₹{order.total_amount}", styles['Heading2']))
    story.append(Spacer(1, 20))
    
    # Footer with text symbols instead of emojis
    story.append(Paragraph("Payment Successful [✓]", styles['Normal']))
    story.append(Paragraph("[X] Don't return any product without box and with any damage & also carry the receipt.", styles['Normal']))
    story.append(Paragraph("Thank you for shopping with us! [🤝]", styles['Normal']))
    
    doc.build(story)
    buffer.seek(0)
    
    return send_file(
        buffer,
        as_attachment=True,
        download_name=f'bill_{order.id}.pdf',
        mimetype='application/pdf'
    )

@app.route('/manage/brands')
@login_required
def manage_brands():
    brands = Brand.query.all()
    return render_template('manage_brands.html', brands=brands)

@app.route('/manage/products')
@login_required
def manage_products():
    products = Product.query.all()
    return render_template('manage_products.html', products=products)

@app.route('/brand/<int:brand_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    if request.method == 'POST':
        brand.name = request.form['name']
        brand.description = request.form['description']
        brand.min_price = float(request.form['min_price'])
        brand.max_price = float(request.form['max_price'])
        
        if 'logo' in request.files and request.files['logo'].filename:
            file = request.files['logo']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                brand.logo_url = f"/static/uploads/{filename}"
        
        db.session.commit()
        flash('Brand updated successfully')
        return redirect(url_for('manage_brands'))
    
    return render_template('edit_brand.html', brand=brand)

@app.route('/product/<int:product_id>/edit', methods=['GET', 'POST'])
@login_required
def edit_product(product_id):
    product = Product.query.get_or_404(product_id)
    brands = Brand.query.all()
    
    if request.method == 'POST':
        product.name = request.form['name']
        product.description = request.form['description']
        product.price = float(request.form['price'])
        product.stock_quantity = int(request.form['stock_quantity'])
        product.category = request.form['category']
        product.brand_id = int(request.form['brand_id'])
        
        if 'image' in request.files and request.files['image'].filename:
            file = request.files['image']
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                filename = f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_{filename}"
                file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                product.image_url = f"/static/uploads/{filename}"
        
        db.session.commit()
        flash('Product updated successfully')
        return redirect(url_for('manage_products'))
    
    return render_template('edit_product.html', product=product, brands=brands)

@app.route('/brand/<int:brand_id>/delete', methods=['POST'])
@login_required
def delete_brand(brand_id):
    brand = Brand.query.get_or_404(brand_id)
    db.session.delete(brand)
    db.session.commit()
    flash('Brand deleted successfully')
    return redirect(url_for('manage_brands'))

@app.route('/product/<int:product_id>/delete', methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    db.session.delete(product)
    db.session.commit()
    flash('Product deleted successfully')
    return redirect(url_for('manage_products'))

@app.route('/purchase_history')
@login_required
def purchase_history():
    # Get all paid orders for the current user
    orders = PurchaseOrder.query.filter_by(
        user_id=current_user.id,
        status='Paid'
    ).order_by(PurchaseOrder.order_date.desc()).all()
    
    return render_template('purchase_history.html', orders=orders)

if __name__ == '__main__':
    with app.app_context():
        try:
            # First drop all tables
            db.drop_all()
            
            # Create all tables with new schema
            db.create_all()
            
            # Add some sample brands
            sample_brands = [
                Brand(
                    name="Smartphone",
                    description="New brand Smartphone.",
                    logo_url="/static/uploads/phone.jpg",
                    min_price=10000,
                    max_price=400000
                ),
                Brand(
                    name="Smartwatch",
                    description="New brand Smartwatch.",
                    logo_url="/static/uploads/watch.jpg",
                    min_price=1000,
                    max_price=5000
                ),
                Brand(
                    name="Laptop",
                    description="New brand Laptop.",
                    logo_url="/static/uploads/laptop.jpg",
                    min_price=20000,
                    max_price=80000
                ),
                Brand(
                    name="Earphones",
                    description="Premium quality earphones with noise cancellation.",
                    logo_url="/static/uploads/h.jpg",
                    min_price=1000,
                    max_price=4000
                ),
                 Brand(
                    name="Tablet",
                    description="New brand Tablet.",
                    logo_url="/static/uploads/t.jpg",
                    min_price=10000,
                    max_price=40000
                ),
                  Brand(
                    name="Monitors",
                    description="New brand Monitors.",
                    logo_url="/static/uploads/m.jpg",
                    min_price=5999,
                    max_price=19999,
                ),
                  Brand(
                    name="Cameras",
                    description="New brand Cameras.",
                    logo_url="/static/uploads/c1.jpg",
                    min_price=40999,
                    max_price=99999,
                ),
                   Brand(
                    name="Speakers",
                    description="New brand Cameras.",
                    logo_url="/static/uploads/s.jpg",
                    min_price=499,
                    max_price=6999,
                )
            ]
            
            # Add brands to database
            for brand in sample_brands:
                db.session.add(brand)
            
            # Add some sample products
            sample_products = [
                Product(
                    name="Galaxy S21",
                    description="Samsung Galaxy S21 5G (Phantom White, 8GB RAM, 128GB Storage) + Galaxy Buds Pro @990",
                    price=38999.00,
                    image_url="/static/uploads/Galaxy S21.jpg",
                    stock_quantity=50,
                    category="Smartphones",
                    brand_id=1
                ),
                Product(
                    name="iPhone 13",
                    description="Apple iPhone 13 with 128GB storage",
                    price=39900.00,
                    image_url="/static/uploads/iphone-13.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                Product(
                    name="Smart Watch",
                    description="Smart Watch for Men Kids Women Boys Girls Original ID116 1.3, HD Display, Sleep Monitor with Heart Rate Activity Tracker, Blood Pressure, OLED Touchscreen for Compatible (Charger Not Included)",
                    price=999.00,
                    image_url="/static/uploads/w1.jpg",
                    stock_quantity=100,
                    category="Smartwatches",
                    brand_id=2
                ),
                Product(
                    name="Smart Watch Pro",
                    description="Smart Watch for Men Kids Women Boys Girls Original ID116 1.3, HD Display, Sleep Monitor with Heart Rate Activity Tracker, Blood Pressure, OLED Touchscreen for Compatible (Charger Not Included)",
                    price=1499.00,
                    image_url="/static/uploads/W3.jpg",
                    stock_quantity=100,
                    category="Smartwatches",
                    brand_id=2
                ),
                Product(
                    name="Surface Laptop",
                    description="Microsoft New Surface Laptop (7th Edition) - Windows 11 Home Copilot + PC - 13.8 LCD PixelSense Touchscreen - Qualcomm Snapdragon X Elite (12 Core) - 16GB RAM - 512GB SSD - Graphite - ZGP-00059",
                    price=75999.00,
                    image_url="/static/uploads/l1.jpg",
                    stock_quantity=100,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="Lenovo Laptop",
                    description="Lenovo IdeaPad Slim 3 12th Gen Intel Core i3-1215U 15.6 (39.62cm) FHD Thin & Light Laptop (8GB/512GB SSD/Intel UHD Graphics/Windows 11/Office Home 2024/1Yr ADP Free/Arctic Grey/1.63Kg), 82RK01ABIN",
                    price=34475.00,
                    image_url="/static/uploads/l2.jpg",
                    stock_quantity=100,
                    category="Laptops",
                    brand_id=3
                ),
                  Product(
                    name="OnePlus Buds Pro",
                    description="OnePlus Nord Buds 3 Pro Truly Wireless Bluetooth in Ear Earbuds with Upto 49Db Active Noise Cancellation,12.4Mm Dynamic Drivers,10Mins for 11Hrs Fast Charging with Upto 44Hrs Music Playback[Black]",
                    price=2999.00,
                    image_url="/static/uploads/h1.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                  Product(
                    name="Bluetooth Headphones",
                    description="Boult Q Over Ear Bluetooth Headphones with 70H Playtime, 40mm Bass Drivers, Zen™ ENC Mic, Type-C Fast Charging, 4 EQ Modes, Bluetooth 5.4, AUX Option, Easy Controls, IPX5 Wireless Headphones (Beige)",
                    price=2999.00,
                    image_url="/static/uploads/h2.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="Lenovo Tab M11",
                    description="Tab M11 27.94 cms (11) 4 GB 128 GB Wi-Fi + LTE + Lenovo Folio Case",
                    price=31297.00,
                    image_url="/static/uploads/t1.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Xiaomi Pad 7",
                    description="Xiaomi Pad 7 |Qualcomm Snapdragon 7+ Gen 3 |28.35cm(11.16) Display |8GB, 128GB |3.2K CrystalRes Display |HyperOS 2 |68 Billion+ Colours |Dolby Vision Atmos |Quad Speakers |Wi-Fi 6 |Graphite Grey",
                    price=27999.00,
                    image_url="/static/uploads/t2.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="LG ",
                    description="LG 68.58 cm (27 inch) Full HD IPS Panel with Vga, Hdmi, Display Port Monitor (27MP60G-BB.ATRZJSN)  (AMD Free Sync, Response Time: 5 ms, 75 Hz Refresh Rate)",
                    price=10450.00,
                    image_url="/static/uploads/m.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="Lenovo ",
                    description="Lenovo 54.61 cm (21.5 inch) Full HD VA Panel Monitor (L22e-40)  (Response Time: 4 ms, 60 Hz Refresh Rate)",
                    price=15699.00,
                    image_url="/static/uploads/m2.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="LG ",
                    description="LG 80.01 cm (31.5 inch) Full HD IPS Panel with webOS, Apple AirPlay 2, HomeKit compatibility, 5Wx2 speakers, Magic remote compatible Smart Monitor (32SR50F-WA.ATREMSN)  (Response Time: 5 ms, 60 Hz Refresh Rate)",
                    price=17399.00,
                    image_url="/static/uploads/m1.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="ViewSonic",
                    description="ViewSonic 68.58 cm (27 inch) Quad HD IPS Panel with HDR10, 137 sRGB, Height Adjustment, Swivel, Tilt, Pivot, Eye Care, 2 x HDMI, Display Port Gaming Monitor (VX2758A-2K-PRO-2)  (AMD Free Sync, Response Time: 1 ms, 185 Hz Refresh Rate))",
                    price=16499.00,
                    image_url="/static/uploads/m3.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="Motorola Edge 50 Pro",
                    description="Motorola Edge 50 Pro 5G with 125W Charger (Caneel Bay, 256 GB)  (12 GB RAM)",
                    price=29900.00,
                    image_url="/static/uploads/p1.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="realme P3x 5G",
                    description="realme P3x 5G (Midnight Blue, 128 GB)  (6 GB RAM)",
                    price=13999.00,
                    image_url="/static/uploads/p2.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="Noise Colorfit Icon 2",
                    description="Noise Colorfit Icon 2 1.8'' Display with Bluetooth Calling, AI Voice Assistant Smartwatch  (Grey Strap, Regular)",
                    price=1199.00,
                    image_url="/static/uploads/w4.jpg",
                    stock_quantity=30,
                    category="Smartwatches",
                    brand_id=2
                ),
                 Product(
                    name="Noise Pro 5",
                    description="Noise Pro 5 1.85 AMOLED Always-on Display, DIY Watch face, SoS Technology, BT Calling Smartwatch  (Elite Black Strap, Regular)",
                    price=3999.00,
                    image_url="/static/uploads/w5.jpg",
                    stock_quantity=30,
                    category="Smartwatches",
                    brand_id=2
                ),
                 Product(
                    name="HP 15s",
                    description="HP 15s Backlit Keyboard AMD Ryzen 3 Quad Core 7320U - (8 GB/512 GB SSD/Windows 11 Home) 15-fc0026AU Thin and Light Laptop  (15.6 Inch, Natural Silver, 1.59 kg, With MS Office)",
                    price=30990.00,
                    image_url="/static/uploads/l3.jpg",
                    stock_quantity=30,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="ASUS Vivobook Go 15",
                    description="ASUS Vivobook Go 15 OLED AMD Ryzen 3 Quad Core 7320U - (8 GB/512 GB SSD/Windows 11 Home) E1504FA-LK323WS Thin and Light Laptop  (15.6 Inch, Green Grey, 1.63 Kg, With MS Office)",
                    price=39900.00,
                    image_url="/static/uploads/l4.jpg",
                    stock_quantity=30,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="realme Buds T200 Lite",
                    description="realme Buds T200 Lite with 12.4mm Driver, 48hrs Playback, AI ENC & Dual-Device Pairing Bluetooth  (Volt Black, True Wireless)",
                    price=1399.00,
                    image_url="/static/uploads/h3.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="Noise 3 / Airwave max 3",
                    description="Noise 3 / Airwave max 3,70 Hrs Playtime,ENC, Dual pairing & Ultra-low latency of 45ms Bluetooth  (Midnight Blue, On the Ear)",
                    price=1999.00,
                    image_url="/static/uploads/h4.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="OnePlus Pad 2",
                    description="OnePlus Pad 2 8 GB RAM 128 GB ROM 12.1 inch with Wi-Fi Only Tablet (Nimbus Gray)",
                    price=36999.00,
                    image_url="/static/uploads/t3.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Samsung Galaxy Tab A9+",
                    description="SAMSUNG Galaxy Tab A9+ 8 GB RAM 128 GB ROM 11.0 inch with Wi-Fi+5G Tablet (Graphite)",
                    price=21999.00,
                    image_url="/static/uploads/t4.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Lenovo Tab M11",
                    description="Tab M11 27.94 cms (11) 4 GB 128 GB Wi-Fi + LTE + Lenovo Folio Case",
                    price=31297.00,
                    image_url="/static/uploads/t1.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Xiaomi Pad 7",
                    description="Xiaomi Pad 7 |Qualcomm Snapdragon 7+ Gen 3 |28.35cm(11.16) Display |8GB, 128GB |3.2K CrystalRes Display |HyperOS 2 |68 Billion+ Colours |Dolby Vision Atmos |Quad Speakers |Wi-Fi 6 |Graphite Grey",
                    price=27999.00,
                    image_url="/static/uploads/t2.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                Product(
                    name="OnePlus Buds Pro",
                    description="OnePlus Nord Buds 3 Pro Truly Wireless Bluetooth in Ear Earbuds with Upto 49Db Active Noise Cancellation,12.4Mm Dynamic Drivers,10Mins for 11Hrs Fast Charging with Upto 44Hrs Music Playback[Black]",
                    price=2999.00,
                    image_url="/static/uploads/h1.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                  Product(
                    name="Bluetooth Headphones",
                    description="Boult Q Over Ear Bluetooth Headphones with 70H Playtime, 40mm Bass Drivers, Zen™ ENC Mic, Type-C Fast Charging, 4 EQ Modes, Bluetooth 5.4, AUX Option, Easy Controls, IPX5 Wireless Headphones (Beige)",
                    price=2999.00,
                    image_url="/static/uploads/h2.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                Product(
                    name="Surface Laptop",
                    description="Microsoft New Surface Laptop (7th Edition) - Windows 11 Home Copilot + PC - 13.8 LCD PixelSense Touchscreen - Qualcomm Snapdragon X Elite (12 Core) - 16GB RAM - 512GB SSD - Graphite - ZGP-00059",
                    price=75999.00,
                    image_url="/static/uploads/l1.jpg",
                    stock_quantity=100,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="Lenovo Laptop",
                    description="Lenovo IdeaPad Slim 3 12th Gen Intel Core i3-1215U 15.6 (39.62cm) FHD Thin & Light Laptop (8GB/512GB SSD/Intel UHD Graphics/Windows 11/Office Home 2024/1Yr ADP Free/Arctic Grey/1.63Kg), 82RK01ABIN",
                    price=34475.00,
                    image_url="/static/uploads/l2.jpg",
                    stock_quantity=100,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="Smart Watch",
                    description="Smart Watch for Men Kids Women Boys Girls Original ID116 1.3, HD Display, Sleep Monitor with Heart Rate Activity Tracker, Blood Pressure, OLED Touchscreen for Compatible (Charger Not Included)",
                    price=999.00,
                    image_url="/static/uploads/w1.jpg",
                    stock_quantity=100,
                    category="Smartwatches",
                    brand_id=2
                ),
                Product(
                    name="Smart Watch Pro",
                    description="Smart Watch for Men Kids Women Boys Girls Original ID116 1.3, HD Display, Sleep Monitor with Heart Rate Activity Tracker, Blood Pressure, OLED Touchscreen for Compatible (Charger Not Included)",
                    price=1499.00,
                    image_url="/static/uploads/W3.jpg",
                    stock_quantity=100,
                    category="Smartwatches",
                    brand_id=2
                ),
                Product(
                    name="Galaxy S21",
                    description="Samsung Galaxy S21 5G (Phantom White, 8GB RAM, 128GB Storage) + Galaxy Buds Pro @990",
                    price=38999.00,
                    image_url="/static/uploads/Galaxy S21.jpg",
                    stock_quantity=50,
                    category="Smartphones",
                    brand_id=1
                ),
                Product(
                    name="iPhone 13",
                    description="Apple iPhone 13 with 128GB storage",
                    price=39900.00,
                    image_url="/static/uploads/iphone-13.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="Lenovo ",
                    description="Lenovo 54.61 cm (21.5 inch) Full HD VA Panel Monitor (L22e-40)  (Response Time: 4 ms, 60 Hz Refresh Rate)",
                    price=15699.00,
                    image_url="/static/uploads/m2.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="LG ",
                    description="LG 80.01 cm (31.5 inch) Full HD IPS Panel with webOS, Apple AirPlay 2, HomeKit compatibility, 5Wx2 speakers, Magic remote compatible Smart Monitor (32SR50F-WA.ATREMSN)  (Response Time: 5 ms, 60 Hz Refresh Rate)",
                    price=17399.00,
                    image_url="/static/uploads/m1.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                Product(
                    name="LG ",
                    description="LG 68.58 cm (27 inch) Full HD IPS Panel with Vga, Hdmi, Display Port Monitor (27MP60G-BB.ATRZJSN)  (AMD Free Sync, Response Time: 5 ms, 75 Hz Refresh Rate)",
                    price=10450.00,
                    image_url="/static/uploads/m.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="Motorola Edge 50 Pro",
                    description="Motorola Edge 50 Pro 5G with 125W Charger (Caneel Bay, 256 GB)  (12 GB RAM)",
                    price=29900.00,
                    image_url="/static/uploads/p1.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="realme P3x 5G",
                    description="realme P3x 5G (Midnight Blue, 128 GB)  (6 GB RAM)",
                    price=13999.00,
                    image_url="/static/uploads/p2.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="Noise Colorfit Icon 2",
                    description="Noise Colorfit Icon 2 1.8'' Display with Bluetooth Calling, AI Voice Assistant Smartwatch  (Grey Strap, Regular)",
                    price=1199.00,
                    image_url="/static/uploads/w4.jpg",
                    stock_quantity=30,
                    category="Smartwatches",
                    brand_id=2
                ),
                 Product(
                    name="Noise Pro 5",
                    description="Noise Pro 5 1.85 AMOLED Always-on Display, DIY Watch face, SoS Technology, BT Calling Smartwatch  (Elite Black Strap, Regular)",
                    price=3999.00,
                    image_url="/static/uploads/w5.jpg",
                    stock_quantity=30,
                    category="Smartwatches",
                    brand_id=2
                ),
                 Product(
                    name="HP 15s",
                    description="HP 15s Backlit Keyboard AMD Ryzen 3 Quad Core 7320U - (8 GB/512 GB SSD/Windows 11 Home) 15-fc0026AU Thin and Light Laptop  (15.6 Inch, Natural Silver, 1.59 kg, With MS Office)",
                    price=30990.00,
                    image_url="/static/uploads/l3.jpg",
                    stock_quantity=30,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="ASUS Vivobook Go 15",
                    description="ASUS Vivobook Go 15 OLED AMD Ryzen 3 Quad Core 7320U - (8 GB/512 GB SSD/Windows 11 Home) E1504FA-LK323WS Thin and Light Laptop  (15.6 Inch, Green Grey, 1.63 Kg, With MS Office)",
                    price=39900.00,
                    image_url="/static/uploads/l4.jpg",
                    stock_quantity=30,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="realme Buds T200 Lite",
                    description="realme Buds T200 Lite with 12.4mm Driver, 48hrs Playback, AI ENC & Dual-Device Pairing Bluetooth  (Volt Black, True Wireless)",
                    price=1399.00,
                    image_url="/static/uploads/h3.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="Noise 3 / Airwave max 3",
                    description="Noise 3 / Airwave max 3,70 Hrs Playtime,ENC, Dual pairing & Ultra-low latency of 45ms Bluetooth  (Midnight Blue, On the Ear)",
                    price=1999.00,
                    image_url="/static/uploads/h4.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="OnePlus Pad 2",
                    description="OnePlus Pad 2 8 GB RAM 128 GB ROM 12.1 inch with Wi-Fi Only Tablet (Nimbus Gray)",
                    price=36999.00,
                    image_url="/static/uploads/t3.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Samsung Galaxy Tab A9+",
                    description="SAMSUNG Galaxy Tab A9+ 8 GB RAM 128 GB ROM 11.0 inch with Wi-Fi+5G Tablet (Graphite)",
                    price=21999.00,
                    image_url="/static/uploads/t4.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Lenovo Tab M11",
                    description="Tab M11 27.94 cms (11) 4 GB 128 GB Wi-Fi + LTE + Lenovo Folio Case",
                    price=31297.00,
                    image_url="/static/uploads/t1.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Xiaomi Pad 7",
                    description="Xiaomi Pad 7 |Qualcomm Snapdragon 7+ Gen 3 |28.35cm(11.16) Display |8GB, 128GB |3.2K CrystalRes Display |HyperOS 2 |68 Billion+ Colours |Dolby Vision Atmos |Quad Speakers |Wi-Fi 6 |Graphite Grey",
                    price=27999.00,
                    image_url="/static/uploads/t2.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                Product(
                    name="SONY ZV-E10L ",
                    description="SONY ZV-E10L Mirrorless Camera Body with 1650 mm Power Zoom Lens Vlog  (Black)",
                    price=61490.00,
                    image_url="/static/uploads/c1.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="Panasonic DMC-G85KGW-K ",
                    description="Panasonic DMC-G85KGW-K Mirrorless Camera Body with 14 - 42 mm Lens  (Black)",
                    price=50999.00,
                    image_url="/static/uploads/c2.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="Canon EOS R50 ",
                    description="Canon EOS R50 Mirrorless Camera RF - S 18 - 45 mm f/4.5 - 6.3 IS STM and RF - S 55 - 210 mm f/5 - 7.1 IS STM  (Black)",
                    price=88999.00,
                    image_url="/static/uploads/c3.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="NIKON Z 50 ",
                    description="NIKON Z 50 Mirrorless Camera Body with 16-50mm & 50-250mm Lenses  (Black)",
                    price=89999.00,
                    image_url="/static/uploads/c4.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="NIKON ZFC-28MM ",
                    description="NIKON ZFC-28MM Mirrorless Camera 28MM  (Silver)",
                    price=94079.00,
                    image_url="/static/uploads/c5.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="SONY Alpha ILCE-6600 ",
                    description="SONY Alpha ILCE-6600 APS-C Mirrorless Camera Body Only Featuring Eye AF and 4K movie recording  (Black)",
                    price=79999.00,
                    image_url="/static/uploads/c6.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="Panasonic DMC-G85HAGWK ",
                    description="Panasonic DMC-G85HAGWK Mirrorless Camera Body with 14 - 140 mm/F3.5-5.6 ASPH Lens  (Black)",
                    price=69990.00,
                    image_url="/static/uploads/c7.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="NIKON Z50 ",
                    description="NIKON Z50 Mirrorless Camera Nikkor Z DX 18-140 mm f/3.5-6.3 VR  (Black)",
                    price=98999.00,
                    image_url="/static/uploads/c8.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="boAt Stone 350 Pro/358 Pro",
                    description="boAt Stone 350 Pro/358 Pro with Dynamic RGB LEDs,12 HRS Playback, IPX5 & TWS Feature 14 W Bluetooth Speaker  (Raging Black, Mono Channel)",
                    price=1699.00,
                    image_url="/static/uploads/s1.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ),
                 Product(
                    name="Mivi ROAM2",
                    description="Mivi ROAM2 24HRS Playback, Bass Boosted, TWS Feature, IPX67 5 W Bluetooth Speaker  (Blue, Mono Channel)",
                    price=799.00,
                    image_url="/static/uploads/s2.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="F FERONS ",
                    description="F FERONS Wireless rechargeable brand new portable Premium bass Multimedia FFRTG-113 9 W Bluetooth Speaker  (Black, Stereo Channel)",
                    price=580.00,
                    image_url="/static/uploads/s3.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="boAt Aavante Bar 480",
                    description="boAt Aavante Bar 480 with 7 HRS Playback, Dual Full Range Drivers & TWS Feature 10 W Bluetooth Soundbar  (Black, 2.0 Channel)",
                    price=1199.00,
                    image_url="/static/uploads/s4.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="MZ M423SP ",
                    description="MZ M423SP (PORTABLE HOME TV) Dynamic Thunder Sound 2400mAh Battery 10 W Bluetooth Soundbar  (Black, Stereo Channel)",
                    price=623.00,
                    image_url="/static/uploads/s5.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="Mivi Play ",
                    description="Mivi Play 12HRS Playback, Bass Boosted,TWS Feature, IPX4 5 W Portable Bluetooth Speaker  (Black, Mono Channel)",
                    price=740.00,
                    image_url="/static/uploads/s6.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="Mivi Fort H350 ",
                    description="Mivi Fort H350 Soundbar, 350 Watts, 5.1 Channel, Multi-Input and EQ Modes, BT v5.1 350 W Bluetooth Soundbar  (Black, 5.1 Channel)",
                    price=6990.00,
                    image_url="/static/uploads/s7.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="F FERONS Tune pro ",
                    description="F FERONS Tune pro Dynamic bass Stereo Audio Led lighting Portable Wireless 5 W Bluetooth Speaker  (White, 5.0 Channel)",
                    price=879.00,
                    image_url="/static/uploads/s8.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ),
                Product(
                    name="Galaxy S21",
                    description="Samsung Galaxy S21 5G (Phantom White, 8GB RAM, 128GB Storage) + Galaxy Buds Pro @990",
                    price=38999.00,
                    image_url="/static/uploads/Galaxy S21.jpg",
                    stock_quantity=50,
                    category="Smartphones",
                    brand_id=1
                ),
                Product(
                    name="iPhone 13",
                    description="Apple iPhone 13 with 128GB storage",
                    price=39900.00,
                    image_url="/static/uploads/iphone-13.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                Product(
                    name="Smart Watch",
                    description="Smart Watch for Men Kids Women Boys Girls Original ID116 1.3, HD Display, Sleep Monitor with Heart Rate Activity Tracker, Blood Pressure, OLED Touchscreen for Compatible (Charger Not Included)",
                    price=999.00,
                    image_url="/static/uploads/w1.jpg",
                    stock_quantity=100,
                    category="Smartwatches",
                    brand_id=2
                ),
                Product(
                    name="Smart Watch Pro",
                    description="Smart Watch for Men Kids Women Boys Girls Original ID116 1.3, HD Display, Sleep Monitor with Heart Rate Activity Tracker, Blood Pressure, OLED Touchscreen for Compatible (Charger Not Included)",
                    price=1499.00,
                    image_url="/static/uploads/W3.jpg",
                    stock_quantity=100,
                    category="Smartwatches",
                    brand_id=2
                ),
                Product(
                    name="Surface Laptop",
                    description="Microsoft New Surface Laptop (7th Edition) - Windows 11 Home Copilot + PC - 13.8 LCD PixelSense Touchscreen - Qualcomm Snapdragon X Elite (12 Core) - 16GB RAM - 512GB SSD - Graphite - ZGP-00059",
                    price=75999.00,
                    image_url="/static/uploads/l1.jpg",
                    stock_quantity=100,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="Lenovo Laptop",
                    description="Lenovo IdeaPad Slim 3 12th Gen Intel Core i3-1215U 15.6 (39.62cm) FHD Thin & Light Laptop (8GB/512GB SSD/Intel UHD Graphics/Windows 11/Office Home 2024/1Yr ADP Free/Arctic Grey/1.63Kg), 82RK01ABIN",
                    price=34475.00,
                    image_url="/static/uploads/l2.jpg",
                    stock_quantity=100,
                    category="Laptops",
                    brand_id=3
                ),
                  Product(
                    name="OnePlus Buds Pro",
                    description="OnePlus Nord Buds 3 Pro Truly Wireless Bluetooth in Ear Earbuds with Upto 49Db Active Noise Cancellation,12.4Mm Dynamic Drivers,10Mins for 11Hrs Fast Charging with Upto 44Hrs Music Playback[Black]",
                    price=2999.00,
                    image_url="/static/uploads/h1.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                  Product(
                    name="Bluetooth Headphones",
                    description="Boult Q Over Ear Bluetooth Headphones with 70H Playtime, 40mm Bass Drivers, Zen™ ENC Mic, Type-C Fast Charging, 4 EQ Modes, Bluetooth 5.4, AUX Option, Easy Controls, IPX5 Wireless Headphones (Beige)",
                    price=2999.00,
                    image_url="/static/uploads/h2.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="Lenovo Tab M11",
                    description="Tab M11 27.94 cms (11) 4 GB 128 GB Wi-Fi + LTE + Lenovo Folio Case",
                    price=31297.00,
                    image_url="/static/uploads/t1.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Xiaomi Pad 7",
                    description="Xiaomi Pad 7 |Qualcomm Snapdragon 7+ Gen 3 |28.35cm(11.16) Display |8GB, 128GB |3.2K CrystalRes Display |HyperOS 2 |68 Billion+ Colours |Dolby Vision Atmos |Quad Speakers |Wi-Fi 6 |Graphite Grey",
                    price=27999.00,
                    image_url="/static/uploads/t2.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="LG ",
                    description="LG 68.58 cm (27 inch) Full HD IPS Panel with Vga, Hdmi, Display Port Monitor (27MP60G-BB.ATRZJSN)  (AMD Free Sync, Response Time: 5 ms, 75 Hz Refresh Rate)",
                    price=10450.00,
                    image_url="/static/uploads/m.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="Lenovo ",
                    description="Lenovo 54.61 cm (21.5 inch) Full HD VA Panel Monitor (L22e-40)  (Response Time: 4 ms, 60 Hz Refresh Rate)",
                    price=15699.00,
                    image_url="/static/uploads/m2.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="LG ",
                    description="LG 80.01 cm (31.5 inch) Full HD IPS Panel with webOS, Apple AirPlay 2, HomeKit compatibility, 5Wx2 speakers, Magic remote compatible Smart Monitor (32SR50F-WA.ATREMSN)  (Response Time: 5 ms, 60 Hz Refresh Rate)",
                    price=17399.00,
                    image_url="/static/uploads/m1.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="ViewSonic",
                    description="ViewSonic 68.58 cm (27 inch) Quad HD IPS Panel with HDR10, 137 sRGB, Height Adjustment, Swivel, Tilt, Pivot, Eye Care, 2 x HDMI, Display Port Gaming Monitor (VX2758A-2K-PRO-2)  (AMD Free Sync, Response Time: 1 ms, 185 Hz Refresh Rate))",
                    price=16499.00,
                    image_url="/static/uploads/m3.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="Motorola Edge 50 Pro",
                    description="Motorola Edge 50 Pro 5G with 125W Charger (Caneel Bay, 256 GB)  (12 GB RAM)",
                    price=29900.00,
                    image_url="/static/uploads/p1.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="realme P3x 5G",
                    description="realme P3x 5G (Midnight Blue, 128 GB)  (6 GB RAM)",
                    price=13999.00,
                    image_url="/static/uploads/p2.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="Noise Colorfit Icon 2",
                    description="Noise Colorfit Icon 2 1.8'' Display with Bluetooth Calling, AI Voice Assistant Smartwatch  (Grey Strap, Regular)",
                    price=1199.00,
                    image_url="/static/uploads/w4.jpg",
                    stock_quantity=30,
                    category="Smartwatches",
                    brand_id=2
                ),
                 Product(
                    name="Noise Pro 5",
                    description="Noise Pro 5 1.85 AMOLED Always-on Display, DIY Watch face, SoS Technology, BT Calling Smartwatch  (Elite Black Strap, Regular)",
                    price=3999.00,
                    image_url="/static/uploads/w5.jpg",
                    stock_quantity=30,
                    category="Smartwatches",
                    brand_id=2
                ),
                 Product(
                    name="HP 15s",
                    description="HP 15s Backlit Keyboard AMD Ryzen 3 Quad Core 7320U - (8 GB/512 GB SSD/Windows 11 Home) 15-fc0026AU Thin and Light Laptop  (15.6 Inch, Natural Silver, 1.59 kg, With MS Office)",
                    price=30990.00,
                    image_url="/static/uploads/l3.jpg",
                    stock_quantity=30,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="ASUS Vivobook Go 15",
                    description="ASUS Vivobook Go 15 OLED AMD Ryzen 3 Quad Core 7320U - (8 GB/512 GB SSD/Windows 11 Home) E1504FA-LK323WS Thin and Light Laptop  (15.6 Inch, Green Grey, 1.63 Kg, With MS Office)",
                    price=39900.00,
                    image_url="/static/uploads/l4.jpg",
                    stock_quantity=30,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="realme Buds T200 Lite",
                    description="realme Buds T200 Lite with 12.4mm Driver, 48hrs Playback, AI ENC & Dual-Device Pairing Bluetooth  (Volt Black, True Wireless)",
                    price=1399.00,
                    image_url="/static/uploads/h3.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="Noise 3 / Airwave max 3",
                    description="Noise 3 / Airwave max 3,70 Hrs Playtime,ENC, Dual pairing & Ultra-low latency of 45ms Bluetooth  (Midnight Blue, On the Ear)",
                    price=1999.00,
                    image_url="/static/uploads/h4.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="OnePlus Pad 2",
                    description="OnePlus Pad 2 8 GB RAM 128 GB ROM 12.1 inch with Wi-Fi Only Tablet (Nimbus Gray)",
                    price=36999.00,
                    image_url="/static/uploads/t3.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Samsung Galaxy Tab A9+",
                    description="SAMSUNG Galaxy Tab A9+ 8 GB RAM 128 GB ROM 11.0 inch with Wi-Fi+5G Tablet (Graphite)",
                    price=21999.00,
                    image_url="/static/uploads/t4.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Lenovo Tab M11",
                    description="Tab M11 27.94 cms (11) 4 GB 128 GB Wi-Fi + LTE + Lenovo Folio Case",
                    price=31297.00,
                    image_url="/static/uploads/t1.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Xiaomi Pad 7",
                    description="Xiaomi Pad 7 |Qualcomm Snapdragon 7+ Gen 3 |28.35cm(11.16) Display |8GB, 128GB |3.2K CrystalRes Display |HyperOS 2 |68 Billion+ Colours |Dolby Vision Atmos |Quad Speakers |Wi-Fi 6 |Graphite Grey",
                    price=27999.00,
                    image_url="/static/uploads/t2.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                Product(
                    name="OnePlus Buds Pro",
                    description="OnePlus Nord Buds 3 Pro Truly Wireless Bluetooth in Ear Earbuds with Upto 49Db Active Noise Cancellation,12.4Mm Dynamic Drivers,10Mins for 11Hrs Fast Charging with Upto 44Hrs Music Playback[Black]",
                    price=2999.00,
                    image_url="/static/uploads/h1.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                  Product(
                    name="Bluetooth Headphones",
                    description="Boult Q Over Ear Bluetooth Headphones with 70H Playtime, 40mm Bass Drivers, Zen™ ENC Mic, Type-C Fast Charging, 4 EQ Modes, Bluetooth 5.4, AUX Option, Easy Controls, IPX5 Wireless Headphones (Beige)",
                    price=2999.00,
                    image_url="/static/uploads/h2.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                Product(
                    name="Surface Laptop",
                    description="Microsoft New Surface Laptop (7th Edition) - Windows 11 Home Copilot + PC - 13.8 LCD PixelSense Touchscreen - Qualcomm Snapdragon X Elite (12 Core) - 16GB RAM - 512GB SSD - Graphite - ZGP-00059",
                    price=75999.00,
                    image_url="/static/uploads/l1.jpg",
                    stock_quantity=100,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="Lenovo Laptop",
                    description="Lenovo IdeaPad Slim 3 12th Gen Intel Core i3-1215U 15.6 (39.62cm) FHD Thin & Light Laptop (8GB/512GB SSD/Intel UHD Graphics/Windows 11/Office Home 2024/1Yr ADP Free/Arctic Grey/1.63Kg), 82RK01ABIN",
                    price=34475.00,
                    image_url="/static/uploads/l2.jpg",
                    stock_quantity=100,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="Smart Watch",
                    description="Smart Watch for Men Kids Women Boys Girls Original ID116 1.3, HD Display, Sleep Monitor with Heart Rate Activity Tracker, Blood Pressure, OLED Touchscreen for Compatible (Charger Not Included)",
                    price=999.00,
                    image_url="/static/uploads/w1.jpg",
                    stock_quantity=100,
                    category="Smartwatches",
                    brand_id=2
                ),
                Product(
                    name="Smart Watch Pro",
                    description="Smart Watch for Men Kids Women Boys Girls Original ID116 1.3, HD Display, Sleep Monitor with Heart Rate Activity Tracker, Blood Pressure, OLED Touchscreen for Compatible (Charger Not Included)",
                    price=1499.00,
                    image_url="/static/uploads/W3.jpg",
                    stock_quantity=100,
                    category="Smartwatches",
                    brand_id=2
                ),
                Product(
                    name="Galaxy S21",
                    description="Samsung Galaxy S21 5G (Phantom White, 8GB RAM, 128GB Storage) + Galaxy Buds Pro @990",
                    price=38999.00,
                    image_url="/static/uploads/Galaxy S21.jpg",
                    stock_quantity=50,
                    category="Smartphones",
                    brand_id=1
                ),
                Product(
                    name="iPhone 13",
                    description="Apple iPhone 13 with 128GB storage",
                    price=39900.00,
                    image_url="/static/uploads/iphone-13.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="Lenovo ",
                    description="Lenovo 54.61 cm (21.5 inch) Full HD VA Panel Monitor (L22e-40)  (Response Time: 4 ms, 60 Hz Refresh Rate)",
                    price=15699.00,
                    image_url="/static/uploads/m2.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="LG ",
                    description="LG 80.01 cm (31.5 inch) Full HD IPS Panel with webOS, Apple AirPlay 2, HomeKit compatibility, 5Wx2 speakers, Magic remote compatible Smart Monitor (32SR50F-WA.ATREMSN)  (Response Time: 5 ms, 60 Hz Refresh Rate)",
                    price=17399.00,
                    image_url="/static/uploads/m1.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                Product(
                    name="LG ",
                    description="LG 68.58 cm (27 inch) Full HD IPS Panel with Vga, Hdmi, Display Port Monitor (27MP60G-BB.ATRZJSN)  (AMD Free Sync, Response Time: 5 ms, 75 Hz Refresh Rate)",
                    price=10450.00,
                    image_url="/static/uploads/m.jpg",
                    stock_quantity=30,
                    category="Monitors",
                    brand_id=6
                ),
                 Product(
                    name="Motorola Edge 50 Pro",
                    description="Motorola Edge 50 Pro 5G with 125W Charger (Caneel Bay, 256 GB)  (12 GB RAM)",
                    price=29900.00,
                    image_url="/static/uploads/p1.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="realme P3x 5G",
                    description="realme P3x 5G (Midnight Blue, 128 GB)  (6 GB RAM)",
                    price=13999.00,
                    image_url="/static/uploads/p2.jpg",
                    stock_quantity=30,
                    category="Smartphones",
                    brand_id=1
                ),
                 Product(
                    name="Noise Colorfit Icon 2",
                    description="Noise Colorfit Icon 2 1.8'' Display with Bluetooth Calling, AI Voice Assistant Smartwatch  (Grey Strap, Regular)",
                    price=1199.00,
                    image_url="/static/uploads/w4.jpg",
                    stock_quantity=30,
                    category="Smartwatches",
                    brand_id=2
                ),
                 Product(
                    name="Noise Pro 5",
                    description="Noise Pro 5 1.85 AMOLED Always-on Display, DIY Watch face, SoS Technology, BT Calling Smartwatch  (Elite Black Strap, Regular)",
                    price=3999.00,
                    image_url="/static/uploads/w5.jpg",
                    stock_quantity=30,
                    category="Smartwatches",
                    brand_id=2
                ),
                 Product(
                    name="HP 15s",
                    description="HP 15s Backlit Keyboard AMD Ryzen 3 Quad Core 7320U - (8 GB/512 GB SSD/Windows 11 Home) 15-fc0026AU Thin and Light Laptop  (15.6 Inch, Natural Silver, 1.59 kg, With MS Office)",
                    price=30990.00,
                    image_url="/static/uploads/l3.jpg",
                    stock_quantity=30,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="ASUS Vivobook Go 15",
                    description="ASUS Vivobook Go 15 OLED AMD Ryzen 3 Quad Core 7320U - (8 GB/512 GB SSD/Windows 11 Home) E1504FA-LK323WS Thin and Light Laptop  (15.6 Inch, Green Grey, 1.63 Kg, With MS Office)",
                    price=39900.00,
                    image_url="/static/uploads/l4.jpg",
                    stock_quantity=30,
                    category="Laptops",
                    brand_id=3
                ),
                 Product(
                    name="realme Buds T200 Lite",
                    description="realme Buds T200 Lite with 12.4mm Driver, 48hrs Playback, AI ENC & Dual-Device Pairing Bluetooth  (Volt Black, True Wireless)",
                    price=1399.00,
                    image_url="/static/uploads/h3.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="Noise 3 / Airwave max 3",
                    description="Noise 3 / Airwave max 3,70 Hrs Playtime,ENC, Dual pairing & Ultra-low latency of 45ms Bluetooth  (Midnight Blue, On the Ear)",
                    price=1999.00,
                    image_url="/static/uploads/h4.jpg",
                    stock_quantity=30,
                    category="Earphones",
                    brand_id=4
                ),
                 Product(
                    name="OnePlus Pad 2",
                    description="OnePlus Pad 2 8 GB RAM 128 GB ROM 12.1 inch with Wi-Fi Only Tablet (Nimbus Gray)",
                    price=36999.00,
                    image_url="/static/uploads/t3.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Samsung Galaxy Tab A9+",
                    description="SAMSUNG Galaxy Tab A9+ 8 GB RAM 128 GB ROM 11.0 inch with Wi-Fi+5G Tablet (Graphite)",
                    price=21999.00,
                    image_url="/static/uploads/t4.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Lenovo Tab M11",
                    description="Tab M11 27.94 cms (11) 4 GB 128 GB Wi-Fi + LTE + Lenovo Folio Case",
                    price=31297.00,
                    image_url="/static/uploads/t1.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                 Product(
                    name="Xiaomi Pad 7",
                    description="Xiaomi Pad 7 |Qualcomm Snapdragon 7+ Gen 3 |28.35cm(11.16) Display |8GB, 128GB |3.2K CrystalRes Display |HyperOS 2 |68 Billion+ Colours |Dolby Vision Atmos |Quad Speakers |Wi-Fi 6 |Graphite Grey",
                    price=27999.00,
                    image_url="/static/uploads/t2.jpg",
                    stock_quantity=30,
                    category="Tablets",
                    brand_id=5
                ),
                Product(
                    name="SONY ZV-E10L ",
                    description="SONY ZV-E10L Mirrorless Camera Body with 1650 mm Power Zoom Lens Vlog  (Black)",
                    price=61490.00,
                    image_url="/static/uploads/c1.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="Panasonic DMC-G85KGW-K ",
                    description="Panasonic DMC-G85KGW-K Mirrorless Camera Body with 14 - 42 mm Lens  (Black)",
                    price=50999.00,
                    image_url="/static/uploads/c2.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="Canon EOS R50 ",
                    description="Canon EOS R50 Mirrorless Camera RF - S 18 - 45 mm f/4.5 - 6.3 IS STM and RF - S 55 - 210 mm f/5 - 7.1 IS STM  (Black)",
                    price=88999.00,
                    image_url="/static/uploads/c3.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="NIKON Z 50 ",
                    description="NIKON Z 50 Mirrorless Camera Body with 16-50mm & 50-250mm Lenses  (Black)",
                    price=89999.00,
                    image_url="/static/uploads/c4.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="NIKON ZFC-28MM ",
                    description="NIKON ZFC-28MM Mirrorless Camera 28MM  (Silver)",
                    price=94079.00,
                    image_url="/static/uploads/c5.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="SONY Alpha ILCE-6600 ",
                    description="SONY Alpha ILCE-6600 APS-C Mirrorless Camera Body Only Featuring Eye AF and 4K movie recording  (Black)",
                    price=79999.00,
                    image_url="/static/uploads/c6.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="Panasonic DMC-G85HAGWK ",
                    description="Panasonic DMC-G85HAGWK Mirrorless Camera Body with 14 - 140 mm/F3.5-5.6 ASPH Lens  (Black)",
                    price=69990.00,
                    image_url="/static/uploads/c7.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="NIKON Z50 ",
                    description="NIKON Z50 Mirrorless Camera Nikkor Z DX 18-140 mm f/3.5-6.3 VR  (Black)",
                    price=98999.00,
                    image_url="/static/uploads/c8.jpg",
                    stock_quantity=30,
                    category="Cameras",
                    brand_id=7
                ),
                Product(
                    name="boAt Stone 350 Pro/358 Pro",
                    description="boAt Stone 350 Pro/358 Pro with Dynamic RGB LEDs,12 HRS Playback, IPX5 & TWS Feature 14 W Bluetooth Speaker  (Raging Black, Mono Channel)",
                    price=1699.00,
                    image_url="/static/uploads/s1.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ),
                 Product(
                    name="Mivi ROAM2",
                    description="Mivi ROAM2 24HRS Playback, Bass Boosted, TWS Feature, IPX67 5 W Bluetooth Speaker  (Blue, Mono Channel)",
                    price=799.00,
                    image_url="/static/uploads/s2.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="F FERONS ",
                    description="F FERONS Wireless rechargeable brand new portable Premium bass Multimedia FFRTG-113 9 W Bluetooth Speaker  (Black, Stereo Channel)",
                    price=580.00,
                    image_url="/static/uploads/s3.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="boAt Aavante Bar 480",
                    description="boAt Aavante Bar 480 with 7 HRS Playback, Dual Full Range Drivers & TWS Feature 10 W Bluetooth Soundbar  (Black, 2.0 Channel)",
                    price=1199.00,
                    image_url="/static/uploads/s4.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="MZ M423SP ",
                    description="MZ M423SP (PORTABLE HOME TV) Dynamic Thunder Sound 2400mAh Battery 10 W Bluetooth Soundbar  (Black, Stereo Channel)",
                    price=623.00,
                    image_url="/static/uploads/s5.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="Mivi Play ",
                    description="Mivi Play 12HRS Playback, Bass Boosted,TWS Feature, IPX4 5 W Portable Bluetooth Speaker  (Black, Mono Channel)",
                    price=740.00,
                    image_url="/static/uploads/s6.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="Mivi Fort H350 ",
                    description="Mivi Fort H350 Soundbar, 350 Watts, 5.1 Channel, Multi-Input and EQ Modes, BT v5.1 350 W Bluetooth Soundbar  (Black, 5.1 Channel)",
                    price=6990.00,
                    image_url="/static/uploads/s7.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                ), Product(
                    name="F FERONS Tune pro ",
                    description="F FERONS Tune pro Dynamic bass Stereo Audio Led lighting Portable Wireless 5 W Bluetooth Speaker  (White, 5.0 Channel)",
                    price=879.00,
                    image_url="/static/uploads/s8.jpg",
                    stock_quantity=30,
                    category="Speakers",
                    brand_id=8
                )

            ]
            
            # Add products to database
            for product in sample_products:
                db.session.add(product)
            
            # Commit the changes
            db.session.commit()
            print("Database initialized successfully with sample data!")
            
        except Exception as e:
            print(f"Error initializing database: {e}")
            db.session.rollback()
    
    app.run(debug=True) 
