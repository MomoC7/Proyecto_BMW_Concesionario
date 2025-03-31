from flask import Flask, render_template, request, redirect, flash
from database_connection import connect_to_db

app = Flask(__name__)
db = connect_to_db()

app.secret_key = 'tu_clave_secreta'  # Requerido para usar flash

@app.route('/')
def index():
    try:
        sort = request.args.get('sort', 'brand')  # Valor por defecto: ordenar por marca
        page = int(request.args.get('page', 1))  # Página actual
        items_per_page = 5
        skip = (page - 1) * items_per_page

        # Ordenar los autos según el parámetro 'sort'
        cars = list(
        db.cars.find({}, {'_id': 0})
        .sort([('brand', 1), ('_id', 1)])  # Ordenar por marca, luego por _id
        .skip((page - 1) * items_per_page)  # Saltar registros según la página actual
        .limit(items_per_page)  # Limitar a la cantidad de autos por página
)
        total_cars = db.cars.count_documents({})
        total_pages = (total_cars + items_per_page - 1) // items_per_page

        # Enviar 'sort' como parte del contexto
        return render_template('index.html', cars=cars, car_to_edit=None, error=None, page=page, total_pages=total_pages, sort=sort)
    except Exception as e:
        print("Error al cargar autos:", e)
        return render_template('index.html', cars=[], car_to_edit=None, error="Error al cargar autos.", page=1, total_pages=1, sort='brand')

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
        flash(f"El auto {brand} - {model} fue agregado exitosamente.", "success")
        return redirect('/')
    except ValueError as ve:
        flash("Error: Los datos ingresados no son válidos. Revisa y vuelve a intentarlo.", "error")
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
        return render_template('index.html', cars=cars, car_to_edit=current_data, error=None, page=1, total_pages=1)
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
        
        # Mensaje de éxito
        flash(f"El auto {current_data['brand']} - {current_data['model']} se actualizó correctamente.", "success")
        return redirect('/')
    except Exception as e:
        # Mensaje de error general
        flash("Error: No se pudo actualizar el auto. Intenta de nuevo.", "error")
        print("Error al actualizar auto:", e)
        return redirect('/')

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
        
        # Mensaje de éxito
        flash(f"El auto {car_data['brand']} - {car_data['model']} fue eliminado exitosamente.", "success")
        return redirect('/')
    except Exception as e:
        # Mensaje de error general
        flash("Error: No se pudo eliminar el auto. Intenta de nuevo.", "error")
        print("Error al eliminar auto:", e)
        return redirect('/')
    
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

        # Mensaje de éxito
        flash(f"Resultados encontrados para: {query}.", "success")
        return render_template('index.html', cars=search_result, car_to_edit=None, error=None, page=1, total_pages=1)
    except Exception as e:
        # Mensaje de error general
        flash("Error: No se encontraron coincidencias para tu búsqueda.", "error")
        print("Error durante la búsqueda:", e)
        return render_template('index.html', cars=[], car_to_edit=None, error="Error durante la búsqueda.", page=1, total_pages=1)

@app.route('/filter-by-price', methods=['GET'])
def filter_by_price():
    try:
        min_price = float(request.args.get('min_price'))
        max_price = float(request.args.get('max_price'))

        # Verificar que el rango sea válido
        if min_price > max_price:
            raise ValueError("El precio mínimo no puede ser mayor que el precio máximo.")

        # Realizar el filtro en MongoDB
        filtered_cars = list(db.cars.find({
            'price': {'$gte': min_price, '$lte': max_price}
        }, {'_id': 0}))
        
        # Mensaje de éxito
        flash(f"Mostrando autos dentro del rango de precios: ${min_price} - ${max_price}.", "success")
        return render_template('index.html', cars=filtered_cars, car_to_edit=None, error=None, page=1, total_pages=1)
    except ValueError as ve:
        # Mensaje de error por validación
        flash("Error: El precio mínimo no puede ser mayor que el máximo.", "error")
        print("Error de validación:", ve)
        return render_template('index.html', cars=[], car_to_edit=None, error=str(ve), page=1, total_pages=1)
    except Exception as e:
        # Mensaje de error general
        flash("Error: No se pudo filtrar los autos. Intenta de nuevo.", "error")
        print("Error durante el filtrado:", e)
        return render_template('index.html', cars=[], car_to_edit=None, error="Error durante el filtrado.", page=1, total_pages=1)

if __name__ == '__main__':
    app.run(debug=True)