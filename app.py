from flask import Flask, render_template, request, redirect, url_for, session
from models import db, User, Order, Product

app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ecommerce.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'mysecretkey'

db.init_app(app)


@app.route('/')
def home():
    products = Product.query.all()
    return render_template('index.html', products=products)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        existing_user = User.query.filter_by(username=username).first()

        if existing_user:
            return "Username already exists!"

        new_user = User(
            username=username,
            password=password,
            role='user'
        )

        db.session.add(new_user)
        db.session.commit()

        return redirect(url_for('login'))

    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = User.query.filter_by(
            username=username,
            password=password
        ).first()

        if user:
            session['username'] = user.username
            session['role'] = user.role
            return redirect(url_for('home'))

        return "Invalid username or password!"

    return render_template('login.html')
@app.route('/add_to_cart/<int:product_id>')
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)

    cart = session.get('cart', [])

    cart.append({
        'name': product.name,
        'price': product.price
    })

    session['cart'] = cart

    return redirect(url_for('cart'))



@app.route('/cart')
def cart():
    cart_items = session.get('cart', [])
    total = sum(item['price'] for item in cart_items)

    return render_template(
        'cart.html',
        cart=cart_items,
        total=total
    )
@app.route('/checkout', methods=['GET', 'POST'])
def checkout():
    if 'username' not in session:
        return redirect(url_for('login'))

    cart_items = session.get('cart', [])
    total = sum(item['price'] for item in cart_items)

    if request.method == 'POST':
        for item in cart_items:
            new_order = Order(
                username=session['username'],
                product_name=item['name'],
                status='Order Placed'
            )
            db.session.add(new_order)

        db.session.commit()
        session['cart'] = []

        return redirect(url_for('orders'))

    return render_template(
        'checkout.html',
        cart=cart_items,
        total=total
    )
@app.route('/orders')
def orders():
    if 'username' not in session:
        return redirect(url_for('login'))

    user_orders = Order.query.filter_by(
        username=session['username']
    ).all()

    return render_template(
        'orders.html',
        orders=user_orders
    )
@app.route('/admin')
def admin():
    if 'username' not in session:
        return redirect(url_for('login'))

    if session.get('role') != 'admin':
        return "Access Denied! Admins only."

    all_orders = Order.query.all()

    return render_template(
        'admin.html',
        orders=all_orders
    )
@app.route('/admin/add-product', methods=['GET', 'POST'])
def add_product():
    if 'username' not in session or session.get('role') != 'admin':
        return "Access Denied! Admins only."

    if request.method == 'POST':
        name = request.form['name']
        price = float(request.form['price'])
        description = request.form['description']

        new_product = Product(
            name=name,
            price=price,
            description=description
        )

        db.session.add(new_product)
        db.session.commit()

        return redirect(url_for('admin'))

    return render_template('add_product.html')
@app.route('/admin/update-order/<int:order_id>', methods=['POST'])
def update_order(order_id):
    if 'username' not in session or session.get('role') != 'admin':
        return "Access Denied! Admins only."

    order = Order.query.get_or_404(order_id)

    order.status = request.form['status']

    db.session.commit()

    return redirect(url_for('admin'))
@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('home'))


if __name__ == '__main__':
    with app.app_context():
        db.create_all()

    app.run(debug=True)