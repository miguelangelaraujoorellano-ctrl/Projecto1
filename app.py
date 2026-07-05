from flask import Flask, request, jsonify
from flask_cors import CORS
import psycopg2

app = Flask(__name__)
CORS(app)

# ==================================
# DASHBOARD
# =================================

@app.route('/dashboard')
def dashboard():

    conexion = conectar()
    cursor = conexion.cursor()

    # Productos
    cursor.execute("""
        SELECT COUNT(*)
        FROM productos
    """)
    productos = cursor.fetchone()[0]

    # Usuarios
    cursor.execute("""
        SELECT COUNT(*)
        FROM usuarios
    """)
    usuarios = cursor.fetchone()[0]

    # Pedidos
    cursor.execute("""
        SELECT COUNT(*)
        FROM pedidos
    """)
    pedidos = cursor.fetchone()[0]

    # Ventas
    cursor.execute("""
        SELECT COALESCE(SUM(total),0)
        FROM ventas
    """)
    ventas = cursor.fetchone()[0]

    # PEDIDOS PENDIENTES
    cursor.execute("""
        SELECT COUNT(*)
        FROM pedidos
        WHERE estado='Pendiente'
    """)
    pendientes = cursor.fetchone()[0]

    return jsonify({
        "productos": productos,
        "usuarios": usuarios,
        "pedidos": pedidos,
        "ventas": float(ventas),
        "pendientes": pendientes
    })

# ==================================
# VENTAS SEMANALES
# =================================

@app.route('/ventas-semanales')
def ventas_semanales():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT fecha_venta,
               SUM(total)
        FROM ventas
        GROUP BY fecha_venta
        ORDER BY fecha_venta DESC
        LIMIT 7
    """)

    datos = cursor.fetchall()

    return jsonify(datos)



# ==================================
# CONEXIÓN A POSTGRESQL
# ==================================

def conectar():

    conexion = psycopg2.connect(
        host="localhost",
        database="brosteria_premium",
        user="postgres",
        password="7132",
        port="5432"
    )

    return conexion

# ==================================
# INICIO
# ==================================

@app.route('/')
def inicio():
    return "Servidor Flask funcionando"

# CATEGORIAS PARA SELECT

@app.route('/categorias-select')
def categorias_select():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id,nombre
        FROM categorias
        ORDER BY nombre
    """)

    datos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return jsonify([
        {
            "id": c[0],
            "nombre": c[1]
        }
        for c in datos
    ])


# LISTAR CATEGORIAS

@app.route('/categorias')
def listar_categorias():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT id,nombre
        FROM categorias
        ORDER BY id
    """)

    datos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return jsonify([
        {
            "id": c[0],
            "nombre": c[1]
        }
        for c in datos
    ])

# REGISTRAR CATEGORIA

@app.route('/categorias', methods=['POST'])
def guardar_categoria():

    conexion = conectar()
    cursor = conexion.cursor()

    nombre = request.form['nombre']

    cursor.execute("""
        INSERT INTO categorias(nombre)
        VALUES(%s)
    """, (nombre,))

    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({
        "success": True
    })


# EDITAR CATEGORIA

@app.route('/categorias/<int:id>', methods=['PUT'])
def editar_categoria(id):

    conexion = conectar()
    cursor = conexion.cursor()

    datos = request.json

    cursor.execute("""
        UPDATE categorias
        SET nombre=%s
        WHERE id=%s
    """, (
        datos['nombre'],
        id
    ))

    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({
        "success": True
    })

# ELIMINAR CATEGORIA

@app.route('/categorias/<int:id>', methods=['DELETE'])
def eliminar_categoria(id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM categorias
        WHERE id=%s
    """, (id,))

    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({
        "success": True
    })


# ==================================
# LISTAR PRODUCTOS
# ==================================

@app.route('/productos')
def listar_productos():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT
        p.id,
        p.nombre,
        p.precio,
        p.stock,
        c.nombre

        FROM productos p

        INNER JOIN categorias c
        ON p.categoria_id = c.id

    """)

    datos = cursor.fetchall()

    cursor.close()
    conexion.close()

    return jsonify([

        {
            "id": p[0],
            "nombre": p[1],
            "precio": float(p[2]),
            "stock": p[3],
            "categoria": p[4]
        }

        for p in datos

    ])

# ==================================
# REGISTRAR PRODUCTOS
# ==================================


@app.route(
    '/productos',
    methods=['POST']
)
def guardar_producto():

    conexion = conectar()
    cursor = conexion.cursor()

    nombre = request.form['nombre']
    precio = request.form['precio']
    stock = request.form['stock']
    categoria = request.form['categoria']

    cursor.execute("""

        INSERT INTO productos(
            nombre,
            precio,
            stock,
            categoria_id
        )

        VALUES(
            %s,%s,%s,%s
        )

    """,
    (
        nombre,
        precio,
        stock,
        categoria
    ))

    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({
        "success": True
    })


# ==================================
# ELIMINAR PRODUCTOS
# ==================================

@app.route(
    '/productos/<int:id>',
    methods=['DELETE']
)
def eliminar_producto(id):

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        DELETE FROM productos
        WHERE id=%s
    """,(id,))

    conexion.commit()

    cursor.close()
    conexion.close()

    return jsonify({
        "success":True
    })

# ==================================
#  REPORTE DE VENTAS
# ==================================

@app.route('/reporte-ventas')
def reporte_ventas():

    inicio = request.args.get('inicio')
    fin = request.args.get('fin')

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""
        SELECT
        fecha_venta,
        total

        FROM ventas

        WHERE fecha_venta
        BETWEEN %s AND %s

        ORDER BY fecha_venta
    """,
    (
        inicio,
        fin
    ))

    datos = cursor.fetchall()

    return jsonify([
        {
            "fecha": str(v[0]),
            "total": float(v[1])
        }
        for v in datos
    ])

# ==================================
#  PRODUCTOS MAS VENDIDOS
# ==================================

@app.route('/reporte-productos')
def reporte_productos():

    conexion = conectar()
    cursor = conexion.cursor()

    cursor.execute("""

        SELECT
        p.nombre,
        SUM(d.cantidad)

        FROM detalle_pedido d

        INNER JOIN productos p
        ON d.producto_id=p.id

        GROUP BY p.nombre

        ORDER BY SUM(d.cantidad)
        DESC

    """)

    datos = cursor.fetchall()

    return jsonify([
        {
            "producto": p[0],
            "cantidad": int(p[1])
        }
        for p in datos
    ])


# ==================================
#  PRODUCTOS MAS VENDIDOS
# ==================================


# LOGIN
@app.route('/login', methods=['POST'])
def login():

    print("===== LOGIN =====")

    conexion = conectar()
    cursor = conexion.cursor()

    usuario = request.form['usuario']
    password = request.form['password']

    print("Usuario:", usuario)
    print("Password:", password)

    cursor.execute("""
        SELECT u.nombre,
               r.nombre
        FROM usuarios u
        INNER JOIN roles r
        ON u.rol_id = r.id
        WHERE usuario=%s
        AND password=%s
    """, (usuario, password))

    resultado = cursor.fetchone()

    print("Resultado:", resultado)

    cursor.close()
    conexion.close()

    if resultado:
        return jsonify({
            "success": True,
            "nombre": resultado[0],
            "rol": resultado[1]
        })

    return jsonify({
        "success": False
    })

    
if __name__ == '__main__':
    app.run(
        host="127.0.0.1",
        port=5000,
        debug=True
    )