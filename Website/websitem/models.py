from datetime import datetime
from websitem import db, login_manager
from flask_login import UserMixin



@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class User(db.Model, UserMixin):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    urole = db.Column(db.String(80))
    purchased = db.relationship('Product',secondary='purchased_items')

    def __repr__(self):
        return f"User('{self.username}', '{self.email}', '{self.image_file}','{self.urole}')"
    def get_urole(self):
        return self.urole

class Purchased_items(db.Model):
    __tablename__ = 'purchased_items'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))
    date_purchased = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    count = db.Column(db.Integer,default=1)
    def __repr__(self):
        return f"purchased_item('{self.user_id}', '{self.product_id}', '{self.count}')"

class Cart(db.Model):
    __tablename__ = 'cart'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    products = db.relationship('Product', secondary='cart_product')

    def clear_all(self):
        self.products.clear()

class Cart_product(db.Model):
    __tablename__ = 'cart_product'
    id = db.Column(db.Integer, primary_key=True)
    cart_id = db.Column(db.Integer, db.ForeignKey('cart.id'))
    product_id = db.Column(db.Integer, db.ForeignKey('product.id'))

class Product(db.Model):
    __tablename__ = 'product'
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    price = db.Column(db.Integer,nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    image_file = db.Column(db.String(20), nullable=False, default='default2.png')
    category_id = db.Column(db.Integer,db.ForeignKey('category.id'))

    def __repr__(self):
        return f"Product('{self.title}', '{self.price}','{self.category_id}')"

class Category(db.Model):
    __tablename__ = 'category'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20),nullable=False)
    products = db.relationship('Product')
