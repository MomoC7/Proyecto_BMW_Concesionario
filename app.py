from flask import Flask, render_template, request, redirect
from database_connection import connect_to_db

app = Flask(__name__)
db = connect_to_db()

@app.route('/')
def index():
    # Obtener autos de MongoDB
    cars = list(db.cars.find({}, {'_id': 0}))
    return render_template('index.html', cars=cars)

@app.route('/add-car', methods=['POST'])
def add_car():
    try:
        # Obtener datos del formulario
        car_data = {
            'brand': request.form['brand'],
            'model': request.form['model'],
            'year': int(request.form['year']),
            'price': float(request.form['price'])
        }
        # Insertar datos en la colección de MongoDB
        db.cars.insert_one(car_data)
        print("Auto agregado con éxito:", car_data)
        return redirect('/')
    except Exception as e:
        print("Error al agregar auto:", e)
        return "Error al agregar auto", 500

if __name__ == '__main__':
    app.run(debug=True)