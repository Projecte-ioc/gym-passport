import psycopg2
from flask import Flask, request, jsonify

from database_models_tea2 import User, GymEvent, List_user_events
from utils_tea_2 import Connexion

app = Flask(__name__)
db = Connexion()


#  __keys_events__ = ['id', 'name', 'whereisit', 'qty_max_attendes', 'qty_got_it', 'user_id',
#                      'gym_id', 'done','date', 'hour', 'minute', 'duration']

# __key_list_events__=['id_gym', 'id_user', 'id_event', 'rating_event']
def insert_simple(id_gym, id_user, id_event, connection, cursor):
    """
    Aquesta funció insereix a un usuari a la llista d'usuaris apuntats al event.
    :param id_gym:
    :param id_user:
    :param id_event:
    :param connection:
    :param cursor:
    :return:
    """
    List_user_events.id_gym = id_gym
    List_user_events.id_user = id_user
    List_user_events.id_event = id_event
    List_user_events.rating_event = 0
    try:
        cursor.execute(
            f"INSERT INTO {List_user_events.__table_name__} (id_gym, id_user, id_event, rating_event) VALUES ("
            "%s, %s, %s, %s)", (List_user_events.id_gym,
                                List_user_events.id_user, List_user_events.id_event, List_user_events.rating_event
                                ))
        connection.commit()
    except psycopg2.Error:
        print(psycopg2.Error)
    finally:
        cursor.close()
        connection.close()


def delete_simple(id_event, cursor, connection):
    try:
        cursor.execute(
            f"DELETE FROM {List_user_events.__table_name__} WHERE id_event = %s", (id_event,))
        connection.commit()
    except psycopg2.Error as e:
        print(e)
    finally:
        cursor.close()
        connection.close()


@app.route('/obtener_eventos', methods=['GET'])
def get_all_events():
    token = request.headers.get('Authorization')
    rol_user, id, user_name, gym_name = db.validate_rol_user(token)
    results = db.get_elements_filtered(id, GymEvent.__table_name__, 'gym_id', '*')
    if results:
        results_dict = [dict(zip(GymEvent.__keys_events__, row)) for row in results]
        return jsonify(results_dict), 200
    else:
        return jsonify({'message': 'No es possible recuperar les dades'}), 404


@app.route('/filtrar_eventos', methods=['POST'])
def get_filtered_events():
    token = request.headers.get('Authorization')
    rol_user, id, user_name, gym_name = db.validate_rol_user(token)
    user_name_params = request.args.get('user_name')
    id_gym_user_params = db.get_elements_filtered(user_name_params, User.__table_name__, 'user_name', 'gym_id')
    id_user = db.get_elements_filtered(user_name_params, User.__table_name__, 'user_name', 'id')
    if id_gym_user_params[0][0] == id:
        results = db.get_elements_filtered(id_user[0][0], GymEvent.__table_name__, 'user_id', '*')
        results_dict = [dict(zip(GymEvent.__keys_events__, row)) for row in results]
        return jsonify(results_dict), 200
    else:
        return jsonify({'message': 'Error al recuperar les dades solicitades'}), 404


@app.route('/events_with_filters', methods=['POST'])
def get_events_some_filters():
    # TODO cogerá el nombre de las llaves del body, que seràn las mismos datos que los nombres de cada columna.
    pass


@app.route('/insertar_evento', methods=['POST'])
def insert_event():
    '''
    Insereix un event nou.
    ESTRUCTURA JSON:
    {
        'date':'',
        'done': false,
        'hour': 10,
        'minute':15,
        'duration':45,
        'name': "",
        'qty_max_attendes':20,
        'whereisit': ""
    }
    :return: 200 if ok, 500 some insert error
    '''
    connection, cursor = db.get_connection_to_db()
    token = request.headers.get('Authorization')
    rol_user, id, user_name, gym_name = db.validate_rol_user(token)
    data = request.get_json(force=True)
    if isinstance(data, dict):
        GymEvent.date = data.get('date')
        GymEvent.done = data.get('done')
        GymEvent.gym_id = id
        GymEvent.hour = data.get('hour')
        GymEvent.minute = data.get('minute')
        GymEvent.duration = data.get('duration')
        GymEvent.name = data.get('name')
        GymEvent.qty_got_it = 0
        GymEvent.qty_max_attendes = data.get('qty_max_attendes')
        user_id = db.get_elements_filtered(user_name, User.__table_name__, 'user_name', 'id')
        GymEvent.user_id = user_id[0][0]
        GymEvent.whereisit = data.get('whereisit')
    else:
        for item in data:
            GymEvent.date = item['date']
            GymEvent.done = item['done']
            GymEvent.gym_id = id
            GymEvent.hour = item['hour']
            GymEvent.minute = item['minute']
            GymEvent.duration = item['duration']
            GymEvent.name = item['name']
            GymEvent.qty_got_it = 0
            GymEvent.qty_max_attendes = item['qty_max_attendes']
            user_id = db.get_elements_filtered(user_name, User.__table_name__, 'user_name', 'id')
            GymEvent.user_id = user_id[0][0]
            GymEvent.whereisit = item['whereisit']
    try:
        cursor.execute(
            f"INSERT INTO {GymEvent.__table_name__} (name, whereisit, qty_max_attendes, qty_got_it, user_id, gym_id, "
            f"done, date, hour, minute, duration) VALUES ("
            "%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (GymEvent.name,
                                                            GymEvent.whereisit, GymEvent.qty_max_attendes,
                                                            GymEvent.qty_got_it,
                                                            GymEvent.user_id, GymEvent.gym_id,
                                                            GymEvent.done, GymEvent.date,
                                                            GymEvent.hour, GymEvent.minute,
                                                            GymEvent.duration
                                                            ))
        connection.commit()
        return jsonify({'message': 'Esdeveniment enregistrat correctament'}), 201
    except psycopg2.Error as e:
        print(e)
        return jsonify({'message': 'Error al inserir'}), 500
    finally:
        cursor.close()
        connection.close()


@app.route('/reserva_evento', methods=['PATCH'])
def got_it_place():
    """
    Reserva plaça a l'event
    /reserva_evento?event_id=
    :return:
    """
    event_id = request.args.get('event_id')
    print(type(event_id))
    token = request.headers.get('Authorization')
    connex, cursor = db.get_connection_to_db()
    rol_user, id, user_name, gym_name = db.validate_rol_user(token)
    query = f"SELECT qty_got_it, qty_max_attendes FROM {GymEvent.__table_name__} WHERE id = %s AND gym_id = %s"
    cursor.execute(query, (event_id, id))
    result = cursor.fetchone()
    qty_got_it_now = result[0]
    qty_max = result[1]
    print(str(qty_got_it_now))
    print(str(qty_max))
    if result:
        GymEvent.qty_got_it = qty_got_it_now + 1
    if qty_max == qty_got_it_now:
        return jsonify({'message': 'No queden places disponibles'}), 401
    update_query = f"UPDATE {GymEvent.__table_name__} SET qty_got_it = %s WHERE id = %s"
    cursor.execute(update_query, (GymEvent.qty_got_it, event_id))
    user_id = db.get_elements_filtered(user_name, User.__table_name__, "user_name", "id")
    user_id_exact = user_id[0][0]
    insert_simple(id_gym=id, id_user=user_id_exact, id_event=event_id, connection=connex, cursor=cursor)
    return jsonify({'message': 'Has reservat plaça correctament!'}), 201


@app.route('/eliminar_reserva_evento', methods=['PATCH'])
def delete_reservation():
    """
        Reserva plaça a l'event
        /eliminar_reserva_evento?event_id=
        :return:
        """
    event_id = request.args.get('event_id')
    token = request.headers.get('Authorization')
    connex, cursor = db.get_connection_to_db()
    rol_user, id, user_name, gym_name = db.validate_rol_user(token)
    query = f"SELECT qty_got_it, qty_max_attendes FROM {GymEvent.__table_name__} WHERE id = %s AND gym_id = %s"
    cursor.execute(query, (event_id, id))
    result = cursor.fetchone()
    qty_got_it_now = result[0]
    qty_max = result[1]
    print(str(qty_got_it_now))
    print(str(qty_max))
    if result:
        if qty_got_it_now == 1:
            GymEvent.qty_got_it = 0
        else:
            GymEvent.qty_got_it = qty_got_it_now - 1
    if qty_max == qty_got_it_now:
        return jsonify({'message': 'No queden places disponibles'}), 401
    update_query = f"UPDATE {GymEvent.__table_name__} SET qty_got_it = %s WHERE id = %s"
    cursor.execute(update_query, (GymEvent.qty_got_it, event_id))
    user_id = db.get_elements_filtered(user_name, User.__table_name__, "user_name", "id")
    user_id_exact = user_id[0][0]
    delete_query = f"DELETE FROM  {List_user_events.__table_name__} WHERE id_user = %s"
    cursor.execute(delete_query, (user_id_exact, ))
    connex.commit()
    connex.close()
    return jsonify({'message': 'Has reservat plaça correctament!'}), 201


@app.route('/modificar_evento', methods=['PATCH'])
def update_event():
    """
    OBTENEMOS POR ID DEL EVENTO, POR LO TANTO TIENE QUE IR EN EL BODY, COMO PRIMER VALOR EL ID Y LOS DATOS A MODIFICAR.
    """
    pass


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=6000)
