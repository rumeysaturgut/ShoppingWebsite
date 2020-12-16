import os
import secrets
from PIL import Image
from flask import render_template, url_for, flash, redirect, request, abort
from websitem import app, db, bcrypt
from websitem.forms import *
from websitem.models import *
from flask_login import login_user, current_user, logout_user
from functools import wraps
import sys


# rollere göre giriş hakı vermek için flask_login'in login_required metodu override edildi.

def login_required(role="ANY"):
    def wrapper(fn):
        @wraps(fn)
        def decorated_view(*args, **kwargs):

            if not current_user.is_authenticated:
               return app.login_manager.unauthorized()
            urole = current_user.get_urole()
            if ( (urole != role) and (role != "ANY")):
                return render_template('unauthorized_page.html')
            return fn(*args, **kwargs)
        return decorated_view

    return wrapper

#anasayfa
@app.route("/", methods=['GET', 'POST'])
@app.route("/home", methods=['GET', 'POST'])
def home():
    form1 = CategoryForm()
    cats = Category.query.all()
    ordered = {}
    #eğer form submit edilmişse
    if form1.validate_on_submit() and form1.submit.data:
        #kategori id al
        cat_id = form1.category.data
        #eğer forma tarih aralığı girilmişse
        if form1.start_date.data and form1.end_date.data:
            start_date = form1.start_date.data
            end_date = form1.end_date.data
            ordered = populate_dic(ordered, cat_id, start_date, end_date)
        else:
            ordered = populate_dic(ordered, cat_id, None, None)
    else:
        print("default home -->", file=sys.stdout)
        ordered = populate_dic(ordered,0,None,None)

    return render_template('home.html', ordered=ordered, cats=cats,form1=form1)

# anasayfadki ürünleri kategoriye yada satış sayısına göre sıralayan metod.
def populate_dic(dic,id,start,end):
    dic2 = {}
    if int(id) == 0:
        #DropDown'dan 'hepsi' seçilmişse tüm ürünleri getir
        products = Product.query.all()

    else:
        #eğer belli bir kategori seçilmişse o kategorideki ürünleri getir
        cat = Category.query.filter_by(id=id).first()
        products = cat.products

    #Bu döngüde her ürünün satış sayısı hesaplanıyor.
    for product in products:
        count = 0
        purchased_items = Purchased_items.query.filter_by(product_id=product.id)
        for item in purchased_items:
            #eğer tarih aralığı girilmişse
            if (start is not None and end is not None):
                if item.date_purchased.date() >= start and item.date_purchased.date() <= end:
                    #girilen tarih aralığı ürünün satışının gerçekleştiği tarih ile eşleşiyorsa o tarih aralığındaki satış sayısını hesapla.
                    count = count + item.count
            else:
                count = count + item.count
        #sözlüğe ekle.
        dic[product] = count

    #sözlük anahtarları yani ürünler satış sayısına göre sırlanıyor ve ikinci bir sözlüğe atanıyor.
    for w in sorted(dic, key=dic.get, reverse=True):
        dic2[w] = dic[w]
    return dic2


@app.route("/register", methods=['GET', 'POST'])
def register():
    #giriş yapan bir kullanıcı zaten varsa Home'a yönlendir.
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    #eğer kayıt olma formu submit edildiyse formdaki bilgileri al ve yeni kullanıcı oluşturup veritabanına kaydet.
    if form.validate_on_submit():
        hashed_password = bcrypt.generate_password_hash(form.password.data).decode('utf-8')
        user = User(username=form.username.data, email=form.email.data, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        flash('Hesabınız oluşturuldu. Giriş yapabilirsiniz.', 'success')
        cart = Cart(user_id=user.id)
        db.session.add(cart)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html', title='Register', form=form)


@app.route("/login", methods=['GET', 'POST'])
def login():
    # giriş yapan bir kullanıcı zaten varsa Home'a yönlendir.
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    #giriş formu submit edildiyse formdaki bilgileri al ve veritabanındaki kullanıcı bilgileriyle karşılaştır.Email ve şifre eşleşiyorsa
    #kullanıcı giriş gerçekleşsin
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and bcrypt.check_password_hash(user.password, form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('Giriş başarısız. Lütfen email ve parolayı kontrol ediniz.', 'danger')
    return render_template('login.html', title='Login', form=form)


@app.route("/logout")
def logout():
    #Çıkış yapılmadan mevcut kullanıcının sepetini boşalt.
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart.clear_all()
    db.session.commit()
    logout_user()
    return redirect(url_for('home'))

#ürün ve kullanıcı profil resimlerini 'profile_pics' dosyasına kaydeden metod.
def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/profile_pics', picture_fn)

    output_size = (320,320)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)

    return picture_fn


@app.route("/account", methods=['GET', 'POST'])
@login_required(role="ANY")
def account():
    #Eğer kullanıcı bilgilerini güncellemek için formu submit ettiyse kullanıcı bilgilerini formdaki bilgilerle güncelle.
    form = UpdateAccountForm()
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            current_user.image_file = picture_file
        current_user.username = form.username.data
        current_user.email = form.email.data
        db.session.commit()
        flash('Hesabınız güncelleştirildi.', 'success')
        return redirect(url_for('account'))
    #Kullanıcı bilgilerini güncellemek için 'account' uzantısına gittiyse formdaki alanları kullanıcının bilgileriyle doldur.
    elif request.method == 'GET':
        form.username.data = current_user.username
        form.email.data = current_user.email
    image_file = url_for('static', filename='profile_pics/' + current_user.image_file)
    return render_template('account.html', title='Hesabım',
                           image_file=image_file, form=form)


@app.route('/new_product', methods=['GET', 'POST'])
@login_required(role="ADMIN")
def new_product():
    form = ProductForm()
    #Yeni ürün ekleme formu submit edilmişse formdaki bilgilerle yeni ürün kaydı oluşturup veritabanına kaydet.
    if form.validate_on_submit():
        print(form.category.data, file=sys.stdout)
        product = Product(title=form.title.data, price=form.price.data,category_id=form.category.data)
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            product.image_file = picture_file
        db.session.add(product)
        db.session.commit()
        flash('Ürün eklendi.', 'success')
        return redirect(url_for('home'))
    return render_template('new_product.html',title="Yeni Ürün",form=form,legend="Yeni Ürün")

@app.route("/product/<int:product_id>")
def product(product_id):
    #ürün ismi,fiyatı,sepete ekle butonu ve diğer ürün ayrıntılarını içeren sayfa.
    product = Product.query.get_or_404(product_id)
    cat = Category.query.filter_by(id=product.category_id).first()
    image_file = url_for('static', filename='profile_pics/' + product.image_file)
    return render_template('product.html', title=product.title, product=product,image_file=image_file,cat=cat)

@app.route("/product/<int:product_id>/update", methods=['GET', 'POST'])
@login_required(role="ADMIN")
#Ürün bilgisini güncellemek için bu sayfaya gidilir.
def update_product(product_id):
    product = Product.query.get_or_404(product_id)
    form = ProductForm()
    #Eğer ürün güncelleme formu submit edildiyse.Veritabanındaki ürün bilgisini güncelle.
    if form.validate_on_submit():
        if form.picture.data:
            picture_file = save_picture(form.picture.data)
            product.image_file = picture_file
        product.title = form.title.data
        product.price = form.price.data
        product.category_id=form.category.data
        db.session.commit()
        print('1. image file=' + product.image_file, file=sys.stdout)
        flash('Ürün bilgisi güncellendi', 'success')
        return redirect(url_for('new_product', product_id=product.id))
    elif request.method == 'GET':
        #Eğer admin ürün bilgisini güncellemek için ürün güncelleme sayfasına gittiyse o sayfadaki alanları ürün bilgiyle doldur.
        form.title.data = product.title
        form.price.data = product.price
        print(product.category_id, file=sys.stdout)
        form.category.data = product.category_id
        image_file = url_for('static', filename='profile_pics/' + product.image_file)
        print('2. image file=' + image_file, file=sys.stdout)
    return render_template('new_product.html', title='Ürün bilgisini güncelle',
                           form=form, legend='Ürün bilgisini güncelle',resim=image_file)

@app.route("/product/<int:product_id>/delete", methods=['POST'])
@login_required(role="ADMIN")
def delete_product(product_id):
    #ürünü id nosuna göre sil
    product = Product.query.get_or_404(product_id)
    Purchased_items.query.filter_by(product_id=product.id).delete()
    db.session.delete(product)
    db.session.commit()
    flash('urun silindi!', 'success')
    return redirect(url_for('home'))

@app.route("/product/<int:product_id>/add", methods=['POST','GET'])
@login_required(role="ANY")
def add_to_cart2(product_id):
    #product sayfasından ürünu sepete eklemek için
    productt = Product.query.get_or_404(product_id)
    cartt = Cart.query.filter_by(user_id=current_user.id).first()
    cartt.products.append(productt)
    db.session.commit()
    flash('Ürün sepete eklendi.','success')
    return redirect(url_for('product',product_id=productt.id))

@app.route("/home/<int:product_id>/add", methods=['POST','GET'])
@login_required(role="ANY")
def add_to_cart1(product_id):
    # home sayfasından ürünu sepete eklemek için
    product = Product.query.get_or_404(product_id)
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart.products.append(product)
    db.session.commit()
    flash('Ürün sepete eklendi.','success')
    return redirect(url_for('home'))

@app.route("/cart", methods=['POST','GET'])
@login_required(role="ANY")
#benim sepetim sayfası
def cart():
    print(request.method, file=sys.stdout)
    if request.method == 'POST':
        #eğer kullanıcı satın al butonuna tıkladıysa sepeteki ürünleri satın al ve sepeti boşalt
        cart = Cart.query.filter_by(user_id=current_user.id).first()
        user = User.query.filter_by(id=current_user.id).first()
        print('PURCHASING......', file=sys.stdout)
        x = 0
        for product in cart.products:
            x = x + 1
            name = 'adet' + str(x)
            adet = request.form.get(name, None)
            purchased_item = Purchased_items(user_id=user.id,product_id=product.id,count=adet)
            db.session.add(purchased_item)
            db.session.commit()
        cart.products.clear()
        db.session.commit()
        flash('Siparişiniz alınmıştır.', 'success')
        return redirect(url_for('home'))
    user = current_user
    cartB = Cart.query.filter_by(user_id=user.id).first()
    return render_template('cart.html', cart=cartB,dict=dict)

@app.route("/cart/<int:product_id>/remove", methods=['POST','GET'])
@login_required(role="ANY")
#sepeten bir ürün kaldırmak için
def cart_remove(product_id):
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    product = Product.query.get_or_404(product_id)
    cart.products.remove(product)
    db.session.commit()
    return redirect(url_for('cart'))



@app.route("/cart/clear", methods=['POST','GET'])
@login_required(role="ANY")
#sepetin tümünü temizlemek için
def cart_clear():
    cart = Cart.query.filter_by(user_id=current_user.id).first()
    cart.products.clear()
    db.session.commit()
    return redirect(url_for('cart'))

@app.route("/orders", methods=['POST','GET'])
@login_required(role="ANY")
#Siparişlerim sayfası
def orders():
    user = User.query.filter_by(id=current_user.id).first()
    items = Purchased_items.query.filter_by(user_id=user.id)
    return render_template('orders.html',items=items)

@app.route("/users", methods=['GET'])
@login_required(role="ADMIN")
#tüm kullanıcıları listeleyen metod.
def users():
    users=User.query.all()
    return render_template('users.html',users=users)


