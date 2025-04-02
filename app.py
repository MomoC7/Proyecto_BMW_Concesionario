from flask import Flask, render_template, request, redirect, flash
import mysql.connector

app = Flask(__name__)

# Conectar a MySQL
def connect_to_db():
    return mysql.connector.connect(
        host="localhost", 
        user="root", 
        password="M1023622510", 
        database="bmw_concesionario",
        port=3307
    )

app.secret_key = 'tu_clave_secreta'  # Requerido para usar flash

@app.route('/')
def index():
    try:
        # Obtener el campo por el que ordenar, con un valor por defecto 'brand'
        sort = request.args.get('sort', 'brand')
        print(f"Campo de ordenamiento recibido: {sort}")
        
        # Validar que el campo de ordenamiento sea uno de los permitidos
        valid_sort_fields = ['brand', 'model', 'yearm', 'price']
        if sort not in valid_sort_fields:
            sort = 'brand'  # Si no es válido, usar 'brand' por defecto

        page = int(request.args.get('page', 1))  # Página actual
        items_per_page = 5  # Número de autos por página
        skip = (page - 1) * items_per_page  # Calcular el desplazamiento

        # Conectar a la base de datos
        db = connect_to_db()
        cursor = db.cursor(dictionary=True)

        # Obtener los autos de la base de datos con el orden y paginación especificados
        cursor.execute(f"SELECT brand, model, yearm, price FROM cars ORDER BY {sort} LIMIT {items_per_page} OFFSET {skip}")
        cars = cursor.fetchall()

        # Obtener el número total de autos
        cursor.execute("SELECT COUNT(*) FROM cars")
        total_cars = cursor.fetchone()['COUNT(*)']

        total_pages = (total_cars + items_per_page - 1) // items_per_page  # Calcular el total de páginas

        # Cerrar la conexión
        cursor.close()
        db.close()

        # Renderizar la página con los autos, error, y parámetros de paginación
        return render_template('index.html', cars=cars, car_to_edit=None, error=None, page=page, total_pages=total_pages, sort=sort)
    
    except Exception as e:
        # Capturar cualquier error y renderizar la página con un mensaje de error
        print("Error al cargar autos:", e)
        return render_template('index.html', cars=[], car_to_edit=None, error="Error al cargar autos.", page=1, total_pages=1, sort='brand')

@app.route('/add-car', methods=['POST'])
def add_car():
    try:
        # Obtener los datos del formulario y eliminar espacios innecesarios
        brand = request.form['brand'].strip()
        model = request.form['model'].strip()
        yearm = request.form['yearm'].strip()
        price = request.form['price'].strip()

        # Validar que los campos no estén vacíos y los datos sean correctos
        if not brand or not model or not yearm.isdigit() or not price.replace('.', '', 1).isdigit():
            raise ValueError("Datos inválidos: asegúrate de ingresar datos válidos.")

        # Preparar los datos para insertar en la base de datos
        car_data = {
            'brand': brand,
            'model': model,
            'yearm': int(yearm),
            'price': float(price)
        }

        # Conectar a la base de datos
        db = connect_to_db()
        cursor = db.cursor()

        # Insertar el auto en la base de datos
        cursor.execute("""
            INSERT INTO cars (brand, model, yearm, price) 
            VALUES (%s, %s, %s, %s)
        """, (car_data['brand'], car_data['model'], car_data['yearm'], car_data['price']))
        db.commit()

        # Cerrar la conexión
        cursor.close()
        db.close()

        print("Auto agregado con éxito:", car_data)

        # Mostrar un mensaje de éxito con flash
        flash(f"El auto {brand} - {model} fue agregado exitosamente.", "success")
        return redirect('/')  # Redirigir a la página principal
    
    except ValueError as ve:
        # En caso de error de validación, mostrar un mensaje adecuado
        flash("Error: Los datos ingresados no son válidos. Revisa y vuelve a intentarlo.", "error")
        print("Error de validación:", ve)
        return render_template('index.html', cars=[], error=str(ve), car_to_edit=None)

    except Exception as e:
        # Capturar cualquier otro error
        print("Error al agregar auto:", e)
        return "Error al agregar auto", 500

@app.route('/edit-car', methods=['POST'])
def edit_car():
    try:
        # Obtener los datos del auto a editar desde el formulario
        current_data = {
            'brand': request.form['brand'],
            'model': request.form['model'],
            'yearm': int(request.form['yearm']),
            'price': float(request.form['price'])
        }

        # Obtener todos los autos para renderizar el formulario de edición
        db = connect_to_db()
        cursor = db.cursor(dictionary=True)

        cursor.execute("SELECT brand, model, yearm, price FROM cars")
        cars = cursor.fetchall()

        cursor.close()
        db.close()

        return render_template('index.html', cars=cars, car_to_edit=current_data, error=None, page=1, total_pages=1)
    
    except Exception as e:
        print("Error al cargar edición:", e)
        return "Error al cargar edición", 500

@app.route('/update-car', methods=['POST'])
def update_car():
    try:
        # Datos actuales y nuevos para actualizar el auto
        current_data = {
            'brand': request.form['brand'],
            'model': request.form['model'],
            'yearm': int(request.form['yearm']),
            'price': float(request.form['price'])
        }
        new_data = {
            'brand': request.form['new_brand'],
            'model': request.form['new_model'],
            'yearm': int(request.form['new_yearm']),
            'price': float(request.form['new_price'])
        }

        # Conectar a la base de datos
        db = connect_to_db()
        cursor = db.cursor()

        # Realizar la actualización en MySQL
        cursor.execute("""
            UPDATE cars
            SET brand = %s, model = %s, yearm = %s, price = %s
            WHERE brand = %s AND model = %s AND yearm = %s AND price = %s
        """, (new_data['brand'], new_data['model'], new_data['yearm'], new_data['price'], current_data['brand'], current_data['model'], current_data['yearm'], current_data['price']))
        
        db.commit()

        cursor.close()
        db.close()

        flash(f"El auto {current_data['brand']} - {current_data['model']} se actualizó correctamente.", "success")
        return redirect('/')

    except Exception as e:
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
            'yearm': int(request.form['yearm']),
            'price': float(request.form['price'])
        }

        # Conectar a la base de datos
        db = connect_to_db()
        cursor = db.cursor()

        # Eliminar el auto de la base de datos
        cursor.execute("""
            DELETE FROM cars WHERE brand = %s AND model = %s AND yearm = %s AND price = %s
        """, (car_data['brand'], car_data['model'], car_data['yearm'], car_data['price']))

        db.commit()

        cursor.close()
        db.close()

        flash(f"El auto {car_data['brand']} - {car_data['model']} fue eliminado exitosamente.", "success")
        return redirect('/')

    except Exception as e:
        flash("Error: No se pudo eliminar el auto. Intenta de nuevo.", "error")
        print("Error al eliminar auto:", e)
        return redirect('/')

@app.route('/search-cars', methods=['GET'])
def search_cars():
    try:
        # Obtener la consulta de búsqueda
        query = request.args.get('query', '').strip()

        # Conectar a la base de datos
        db = connect_to_db()
        cursor = db.cursor(dictionary=True)

        # Buscar autos que coincidan con la consulta
        cursor.execute("""
            SELECT brand, model, yearm, price FROM cars
            WHERE brand LIKE %s OR model LIKE %s OR yearm LIKE %s OR price LIKE %s
        """, (f'%{query}%', f'%{query}%', f'%{query}%', f'%{query}%'))
        search_result = cursor.fetchall()

        cursor.close()
        db.close()

        flash(f"Resultados encontrados para: {query}.", "success")
        return render_template('index.html', cars=search_result, car_to_edit=None, error=None, page=1, total_pages=1)
    
    except Exception as e:
        flash("Error: No se encontraron coincidencias para tu búsqueda.", "error")
        print("Error durante la búsqueda:", e)
        return render_template('index.html', cars=[], car_to_edit=None, error="Error durante la búsqueda.", page=1, total_pages=1)

@app.route('/filter-by-price', methods=['GET'])
def filter_by_price():
    try:
        # Obtener el rango de precios
        min_price = float(request.args.get('min_price'))
        max_price = float(request.args.get('max_price'))

        # Validar el rango de precios
        if min_price > max_price:
            raise ValueError("El precio mínimo no puede ser mayor que el precio máximo.")

        # Conectar a la base de datos
        db = connect_to_db()
        cursor = db.cursor(dictionary=True)

        # Filtrar los autos por el rango de precios
        cursor.execute("""
            SELECT brand, model, yearm, price FROM cars 
            WHERE price BETWEEN %s AND %s
        """, (min_price, max_price))
        filtered_cars = cursor.fetchall()

        cursor.close()
        db.close()

        flash(f"Mostrando autos dentro del rango de precios: ${min_price} - ${max_price}.", "success")
        return render_template('index.html', cars=filtered_cars, car_to_edit=None, error=None, page=1, total_pages=1)

    except ValueError as ve:
        flash("Error: El precio mínimo no puede ser mayor que el máximo.", "error")
        print("Error de validación:", ve)
        return render_template('index.html', cars=[], car_to_edit=None, error=str(ve), page=1, total_pages=1)
    
    except Exception as e:
        flash("Error: No se pudo filtrar los autos. Intenta de nuevo.", "error")
        print("Error durante el filtrado:", e)
        return render_template('index.html', cars=[], car_to_edit=None, error="Error durante el filtrado.", page=1, total_pages=1)

if __name__ == '__main__':
    app.run(debug=True)
