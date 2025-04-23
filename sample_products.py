import os
import shutil
from app import app, db, Product
from datetime import datetime

def add_sample_products():
    # Sample product data
    sample_products = [
        {
            "name": "Computers",
            "brand": "BenQ GW2490",
            "price": 999.99,
            "description": "BenQ GW2490 60.96 cm (24 inch) Full HD LED Backlit IPS Panel 99% sRGB, Eye-careU, Dual HDMI, Display Port, Bezel-Less, Eyesafe, VESA MediaSync, Brightness Intelligence, Low Blue Light, Speakers 2Wx2, VESA Wall mountable Monitor (GW2490)  (Response Time: 5 ms, 100 Hz Refresh Rate)",
            "image_url": "pc.jpg",
            "stock_quantity": 50,
            "category": "Electronics"
        },
        {
            "name": "Laptop Pro",
            "brand": "CompTech",
            "price": 1299.99,
            "description": "High-performance laptop for professionals",
            "image_url": "laptop.jpg",
            "stock_quantity": 30,
            "category": "Electronics"
        },
        {
            "name": "Wireless Headphones",
            "brand": "SoundMaster",
            "price": 199.99,
            "description": "Premium wireless headphones with noise cancellation",
            "image_url": "headphones.jpg",
            "stock_quantity": 100,
            "category": "Accessories"
        },
        {
            "name": "Smart Watch",
            "brand": "TechWear",
            "price": 299.99,
            "description": "Feature-rich smartwatch with health monitoring",
            "image_url": "smartwatch.jpg",
            "stock_quantity": 75,
            "category": "Wearables"
        },
        {
            "name": "Tablet Pro",
            "brand": "TechCo",
            "price": 799.99,
            "description": "Powerful tablet for work and entertainment",
            "image_url": "tablet.jpg",
            "stock_quantity": 40,
            "category": "Electronics"
        }
    ]

    # Create uploads directory if it doesn't exist
    uploads_dir = os.path.join(app.static_folder, 'uploads')
    if not os.path.exists(uploads_dir):
        os.makedirs(uploads_dir)

    # Copy sample images to uploads directory
    sample_images_dir = os.path.join(app.static_folder, 'sample_images')
    if not os.path.exists(sample_images_dir):
        os.makedirs(sample_images_dir)
        print("Please add sample images to the 'static/sample_images' directory")
        return

    with app.app_context():
        # Clear existing products
        Product.query.delete()
        
        # Add new products
        for product_data in sample_products:
            # Copy image to uploads directory
            src_image = os.path.join(sample_images_dir, product_data['image_url'])
            if os.path.exists(src_image):
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                new_filename = f"{timestamp}_{product_data['image_url']}"
                dst_image = os.path.join(uploads_dir, new_filename)
                shutil.copy2(src_image, dst_image)
                
                # Update image URL
                product_data['image_url'] = f"/static/uploads/{new_filename}"
                
                # Create product
                product = Product(**product_data)
                db.session.add(product)
        
        # Commit changes
        db.session.commit()
        print("Sample products added successfully!")

if __name__ == '__main__':
    add_sample_products() 