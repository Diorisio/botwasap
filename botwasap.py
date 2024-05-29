from flask import Flask, request, jsonify
from twilio.twiml.messaging_response import Body, Message, Redirect, MessagingResponse
import sqlite3

app = Flask(__name__)

def init_db():
    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS reservations
                 (id INTEGER PRIMARY KEY AUTOINCREMENT, customer TEXT, pickup TEXT, destination TEXT, distance REAL, price REAL, driver TEXT, status TEXT)''')
    conn.commit()
    conn.close()

if __name__ == '__main__':
    init_db()


# Cálculo del precio
PRICE_PER_KM = 1500

# Endpoint para recibir mensajes de WhatsApp
@app.route('/', methods=['GET'])
def saludo():
    """
    Crea una respuesta de Twilio con un mensaje y una redirección opcional.

    :param body_text: El texto del mensaje de respuesta.
    :param redirect_url: La URL a la que redirigir, si es aplicable.
    :return: La respuesta de Twilio como una cadena.
    """
    redirect_url = 'https://demo.twilio.com/welcome/sms/'
    body_text = 'Hello World!'
    response = MessagingResponse()
    message = Message()
    message.body(body_text)
    response.append(message)
    print(response)
    
    if redirect_url:
        response.redirect(redirect_url)
    return str(response)

# Ejemplo de uso



@app.route('/webhook', methods=['POST'])
def webhook():
    incoming_msg = request.values.get('Body', '').lower()
    from_number = request.values.get('From', '')

    resp = MessagingResponse()
    msg = resp.message()

    if 'reserva' in incoming_msg:
        msg.body('Por favor envíe su lugar de recogida, destino y distancia en km (Ej: Recogida: Calle 123, Destino: Calle 456, Distancia: 5).')
    elif 'recogida:' in incoming_msg and 'destino:' in incoming_msg and 'distancia:' in incoming_msg:
        try:
            parts = incoming_msg.split(',')
            pickup = parts[0].split(':')[1].strip()
            destination = parts[1].split(':')[1].strip()
            distance = float(parts[2].split(':')[1].strip())
            price = distance * PRICE_PER_KM

            # Guardar reserva en la base de datos
            conn = sqlite3.connect('reservations.db')
            c = conn.cursor()
            c.execute("INSERT INTO reservations (customer, pickup, destination, distance, price, status) VALUES (?, ?, ?, ?, ?, ?)",
                      (from_number, pickup, destination, distance, price, 'pending'))
            conn.commit()
            conn.close()

            msg.body(
                f'Su reserva ha sido registrada. El precio es {price} COP. Estamos buscando un conductor para usted.')
            # Aquí puedes implementar la lógica para notificar a los conductores.
        except Exception as e:
            msg.body(
                f'Error al procesar su solicitud. Asegúrese de seguir el formato correcto.')
    else:
        msg.body(
            'No entendí su mensaje. Por favor, envíe "reserva" para iniciar una nueva reserva.')

    return str(resp)

# Endpoint para que los conductores acepten el servicio


@app.route('/accept_service', methods=['POST'])
def accept_service():
    reservation_id = request.values.get('reservation_id')
    driver = request.values.get('driver')

    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("UPDATE reservations SET driver = ?, status = ? WHERE id = ? AND status = 'pending'",
              (driver, 'accepted', reservation_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})

# Endpoint para confirmar la finalización del servicio


@app.route('/complete_service', methods=['POST'])
def complete_service():
    reservation_id = request.values.get('reservation_id')

    conn = sqlite3.connect('reservations.db')
    c = conn.cursor()
    c.execute("UPDATE reservations SET status = ? WHERE id = ?",
              ('completed', reservation_id))
    conn.commit()
    conn.close()

    return jsonify({'status': 'success'})


if __name__ == '__main__':
    app.run(debug=True)
 