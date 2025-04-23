from flask import Blueprint, render_template
from models import Product

main = Blueprint('main', __name__)

@main.route('/shopping')
def shopping():
    # Get all products from the database
    products = Product.query.all()
    return render_template('shopping.html', products=products) 