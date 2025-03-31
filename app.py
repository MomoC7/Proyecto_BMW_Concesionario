from flask import Flask, render_template, request, redirect
from database_connection import connect_to_db

app = Flask(__name__)
db = connect_to_db()

@app.route('/')
def index():
    # Obtener autos de MongoDB
    cars = list(db.cars.find({}, {'_id': 0}))
    return render_template('index.html', cars=cars, car_to_edit=None, error=None)

@app.route('/add-car', methods=['POST'])
def add_car():
    try:
        # Validar que los campos no estén vacíos
        brand = request.form['brand'].strip()
        model = request.form['model'].strip()
        year = request.form['year'].strip()
        price = request.form['price'].strip()

        # Validar datos
        if not brand or not model or not year.isdigit() or not price.replace('.', '', 1).isdigit():
            raise ValueError("Datos inválidos: asegúrate de ingresar datos válidos.")

        # Preparar datos validados
        car_data = {
            'brand': brand,
            'model': model,
            'year': int(year),
            'price': float(price)
        }
        db.cars.insert_one(car_data)
        print("Auto agregado con éxito:", car_data)
        return redirect('/')
    except ValueError as ve:
        print("Error de validación:", ve)
        return render_template('index.html', cars=list(db.cars.find({}, {'_id': 0})), error=str(ve), car_to_edit=None)
    except Exception as e:
        print("Error al agregar auto:", e)
        return "Error al agregar auto", 500

@app.route('/edit-car', methods=['POST'])
def edit_car():
    try:
        # Datos actuales del auto
        current_data = {
            'brand': request.form['brand'],
            'model': request.form['model'],
            'year': int(request.form['year']),
            'price': float(request.form['price'])
        }
        # Renderizar la página con el formulario de edición
        cars = list(db.cars.find({}, {'_id': 0}))
        return render_template('index.html', cars=cars, car_to_edit=current_data, error=None)
    except Exception as e:
        print("Error al cargar edición:", e)
        return "Error al cargar edición", 500

@app.route('/update-car', methods=['POST'])
def update_car():
    try:
        # Datos actuales del auto
        current_data = {
            'brand': request.form['brand'],
            'model': request.form['model'],
            'year': int(request.form['year']),
            'price': float(request.form['price'])
        }
        # Datos nuevos que reemplazarán al auto actual
        new_data = {
            'brand': request.form['new_brand'],
            'model': request.form['new_model'],
            'year': int(request.form['new_year']),
            'price': float(request.form['new_price'])
        }
        # Actualizar el auto en MongoDB
        db.cars.update_one(current_data, {'$set': new_data})
        print(f"Auto actualizado: {current_data} -> {new_data}")
        return redirect('/')
    except Exception as e:
        print("Error al actualizar auto:", e)
        return "Error al actualizar auto", 500

@app.route('/delete-car', methods=['POST'])
def delete_car():
    try:
        # Datos del auto a eliminar
        car_data = {
            'brand': request.form['brand'],
            'model': request.form['model'],
            'year': int(request.form['year']),
            'price': float(request.form['price'])
        }
        # Eliminar el auto de la base de datos
        db.cars.delete_one(car_data)
        print("Auto eliminado con éxito:", car_data)
        return redirect('/')
    except Exception as e:
        print("Error al eliminar auto:", e)
        return "Error al eliminar auto", 500
    
@app.route('/search-cars', methods=['GET'])
def search_cars():
    try:
        query = request.args.get('query', '').strip()
        # Realizar búsqueda en la colección 'cars'
        search_result = list(db.cars.find({
            '$or': [
                {'brand': {'$regex': query, '$options': 'i'}},
                {'model': {'$regex': query, '$options': 'i'}},
                {'year': {'$regex': query}},
                {'price': {'$regex': query}}
            ]
        }, {'_id': 0}))

        return render_template('index.html', cars=search_result, car_to_edit=None, error=None)
    except Exception as e:
        print("Error durante la búsqueda:", e)
        return render_template('index.html', cars=[], car_to_edit=None, error="Error durante la búsqueda.")

if __name__ == '__main__':
    app.run(debug=True)