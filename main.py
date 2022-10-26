import re
from kodland_db import db
from random import randint
from datetime import datetime, timedelta
from flask import Flask, render_template, request, url_for, redirect, jsonify
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user
app = Flask(__name__)
app.config.update(
    SECRET_KEY = 'WOW SUCH SECRET')

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
class User(UserMixin):
    def __init__(self, id):
        self.id = id
@login_manager.user_loader
def load_user(login):
    return User(login)
all_orders = []

@app.route('/')
@login_required
def index():
    return render_template('index.html')

@app.route('/order', methods=['GET', 'POST'])
@login_required
def order():
    if request.method == 'POST':
        for key in request.form:
            if request.form[key] == '':
                return render_template('order.html', error='Не все поля заполнены!')
            if key == 'email':
                if not re.match('\\w+@\\w+\\.(ru|com)', request.form[key]):
                    return render_template('order.html', error='Неправильный формат почты')
            if key == 'phone_number':
                if not re.match('\\+7\\d{9}', request.form[key]):
                    return render_template('order.html', error='Неправильный формат номера телефона')
        all_orders.append(request.form)
        cart_data = db.cart.get_all()
        order_data = db.orders.get_all()
        if not order_data:
            last_id = 1
        else:
            last_id = order_data[-1].id + 1
        for row in cart_data:
            data = {'id':last_id, 'item_id':row.item_id, 'amount':row.amount}
            db.orders.put(data)
            db.cart.delete('item_id', row.item_id)
        return redirect(url_for("cart"))
    return render_template('order.html')


@app.route('/products/', methods=["GET", "POST"])
@login_required
def products():
    if request.method == "POST":
        id_ = request.form["item_id"]
        data = db.cart.get("item_id", id_)
        if not data:
            db.cart.put({"item_id": id_, "amount": 1})
        else:
            amount = data.amount + 1
            db.cart.delete("item_id", id_)
            db.cart.put({"item_id": id_, "amount": amount})

    data = db.items.get_all()
    return render_template('products.html', products=data)



@app.route('/cart')
def cart():
    data = db.cart.get_all()
    total_sum = 0
    for row in data:
        item_row = db.items.get('id', row.item_id)
        row.name = item_row.name
        row.description = item_row.description
        row.price = item_row.price
        row.total = row.amount * item_row.price
        total_sum += row.total
    return render_template('cart.html', data=data, sum = total_sum)

@app.route('/contacts')
@login_required
def contacts():
    return render_template('contacts.html')

@app.route('/about')
@login_required
def about():
    return render_template('about.html')

@app.route('/product1')
@login_required
def product1():
    end_date = datetime.now() + timedelta(days=7)
    end_date = end_date.strftime('%d.%m.%Y')
    return render_template('product1.html', action_name='Весенние скидки!', end_date=end_date, lucky_num=randint(1,5))

@app.route('/product2')
@login_required
def product2():
    brands = ['Colla', 'Pepppssi', 'Orio', 'Macdak']
    return render_template('product2.html', brands=brands)

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        row = db.users.get('login', request.form['login'])
        if not row:
            return render_template('login.html', message='Неправильный логин или пароль')
        if request.form["password"] == row.password:
            user = User(login)
            login_user(user)
            return redirect(url_for('index'))
        else:
            return render_template('login.html', message='Логин или пароль введены неверно')
    return render_template('login.html')

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return render_template('login.html', message='Вы вышли из своей учётной записи')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        for key in request.form:
            if request.form[key] == '':
                return render_template('register.html', message='Все поля должны быть заполнены!')
        if request.form['password'] != request.form['password2']:
            return render_template('register.html', message='Пароли не совпадают')
        if db.users.get("login", request.form["login"]):
            return render_template("register.html", message='Такой пользователь уже существует')
        if db.users.get("email", request.form["email"]):
            return render_template("register.html", message='Такой email уже существует')
        if db.users.get("phone_number", request.form["phone_number"]):
            return render_template("register.html", message='Такой номер телефона уже есть')
        data = dict(request.form)
        data.pop('password2')
        db.users.put(data=data)
        return redirect(url_for("login"))
    return render_template('register.html')

@app.route('/api/orders')
def api_orders():
    return jsonify(all_orders)

@app.route('/lootbox')
@login_required
def lootbox():
    num = randint(1, 100)
    if num < 50:
        chance = 50
    elif 50 < num < 95:
        chance = 45
    elif 95 < num < 99:
        chance = 4
    else:
        chance = 1
    return render_template('lootbox.html', chance=chance)

@app.route('/test')
@login_required
def test():
    return render_template('test.html')

if __name__ == "__main__":
    app.run(host='0.0.0.0')
