import secrets
import os
from PIL import Image
from flask import Flask, render_template, url_for, flash, redirect, request, abort
from flask_login import LoginManager, login_user, current_user, logout_user, login_required
from models import db, User, Product, Comment, CartItem  # 👈 记得导入 CartItem
from forms import RegistrationForm, LoginForm, ProductForm, CommentForm

app = Flask(__name__)
app.config['SECRET_KEY'] = '123456'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///site.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def save_picture(form_picture):
    random_hex = secrets.token_hex(8)
    _, f_ext = os.path.splitext(form_picture.filename)
    picture_fn = random_hex + f_ext
    picture_path = os.path.join(app.root_path, 'static/product_pics', picture_fn)
    
    output_size = (500, 500)
    i = Image.open(form_picture)
    i.thumbnail(output_size)
    i.save(picture_path)
    return picture_fn

# --- 基础路由 ---

@app.route("/")
@app.route("/home")
def home():
    products = Product.query.order_by(Product.date_posted.desc()).all()
    return render_template('home.html', products=products)

@app.route("/register", methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = RegistrationForm()
    if form.validate_on_submit():
        user = User(username=form.username.data, email=form.email.data)
        user.set_password(form.password.data)
        db.session.add(user)
        db.session.commit()
        flash('账号创建成功！现在可以登录了', 'success')
        return redirect(url_for('login'))
    return render_template('register.html', title='注册', form=form)

@app.route("/login", methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('home'))
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user and user.check_password(form.password.data):
            login_user(user, remember=form.remember.data)
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('home'))
        else:
            flash('登录失败，请检查邮箱或密码', 'danger')
    return render_template('login.html', title='登录', form=form)

@app.route("/logout")
def logout():
    logout_user()
    if request.args.get('next') == 'login':
        return redirect(url_for('login'))
    return redirect(url_for('home'))

# --- 商品相关路由 ---

@app.route("/product/new", methods=['GET', 'POST'])
@login_required
def new_product():
    form = ProductForm()
    if form.validate_on_submit():
        picture_file = 'default.jpg'
        if form.image.data:
            picture_file = save_picture(form.image.data)
        
        product = Product(name=form.name.data, 
                          price=form.price.data,
                          description=form.description.data, 
                          image_file=picture_file,
                          owner=current_user)
        db.session.add(product)
        db.session.commit()
        flash('商品发布成功！', 'success')
        return redirect(url_for('home'))
    return render_template('create_product.html', title='发布商品', form=form)

@app.route("/product/<int:product_id>", methods=['GET', 'POST'])
def product(product_id):
    product = Product.query.get_or_404(product_id)
    form = CommentForm()
    
    if form.validate_on_submit():
        if not current_user.is_authenticated:
            flash('请先登录再评论', 'info')
            return redirect(url_for('login'))
            
        comment = Comment(content=form.content.data, author=current_user, product=product)
        db.session.add(comment)
        db.session.commit()
        flash('评论已发布！', 'success')
        return redirect(url_for('product', product_id=product.id))
    
    comments = Comment.query.filter_by(product_id=product.id).order_by(Comment.date_posted.desc()).all()
    return render_template('product.html', title=product.name, product=product, form=form, comments=comments)

@app.route("/product/<int:product_id>/delete", methods=['POST'])
@login_required
def delete_product(product_id):
    product = Product.query.get_or_404(product_id)
    if product.owner != current_user:
        abort(403)
    db.session.delete(product)
    db.session.commit()
    flash('您的商品已成功下架删除！', 'success')
    return redirect(url_for('home'))

@app.route("/comment/<int:comment_id>/delete", methods=['POST'])
@login_required
def delete_comment(comment_id):
    comment = Comment.query.get_or_404(comment_id)
    if comment.author != current_user:
        abort(403)
    product_id = comment.product_id
    db.session.delete(comment)
    db.session.commit()
    flash('评论已删除', 'success')
    return redirect(url_for('product', product_id=product_id))

# --- 购物车与购买功能 ---

@app.route("/add_to_cart/<int:product_id>")
@login_required
def add_to_cart(product_id):
    product = Product.query.get_or_404(product_id)
    
    # 1. 卖家不能买自己的商品
    if product.owner == current_user:
        flash('无法购买自己发布的商品', 'warning')
        return redirect(url_for('product', product_id=product_id))

    # 2. 检查是否已经在购物车
    existing_item = CartItem.query.filter_by(user_id=current_user.id, product_id=product_id).first()
    if existing_item:
        flash('该商品已经在购物车里了，去结账吧！', 'info')
    else:
        cart_item = CartItem(buyer=current_user, product=product)
        db.session.add(cart_item)
        db.session.commit()
        flash('已成功加入购物车！', 'success')
    
    return redirect(url_for('cart'))

@app.route("/cart")
@login_required
def cart():
    cart_items = CartItem.query.filter_by(buyer=current_user).all()
    total_price = sum([item.product.price for item in cart_items])
    return render_template('cart.html', cart_items=cart_items, total=total_price)

@app.route("/cart/remove/<int:item_id>")
@login_required
def remove_from_cart(item_id):
    item = CartItem.query.get_or_404(item_id)
    if item.buyer != current_user:
        abort(403)
    db.session.delete(item)
    db.session.commit()
    flash('商品已移除', 'info')
    return redirect(url_for('cart'))

@app.route("/checkout")
@login_required
def checkout():
    cart_items = CartItem.query.filter_by(buyer=current_user).all()
    if not cart_items:
        flash('购物车为空', 'warning')
        return redirect(url_for('home'))
    
    # 模拟支付成功，清空购物车
    for item in cart_items:
        db.session.delete(item)
    db.session.commit()
    flash('支付成功！感谢您的购买！(模拟)', 'success')
    return redirect(url_for('home'))

# --- 账号切换功能 ---

@app.route("/switch_account_page")
def switch_account_page():
    return render_template('switch_account.html')

@app.route("/direct_login/<int:user_id>")
def direct_login(user_id):
    logout_user()
    user = User.query.get_or_404(user_id)
    login_user(user)
    flash(f'欢迎回来，{user.username}！', 'success')
    return redirect(url_for('home'))

if __name__ == '__main__':
    if not os.path.exists('site.db'):
        with app.app_context():
            db.create_all()
    app.run(debug=True)