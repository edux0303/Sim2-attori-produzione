from database.DB_connect import DBConnect
from model.attore import Attore
class DAO():
    def __init__(self):
        pass

    @staticmethod
    def getAllRatings():
        cnx = DBConnect.get_connection()
        if cnx is None:
            return None
        result = []
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT DISTINCT r.avg_rating AS media 
                   FROM ratings r 
                   ORDER BY media ASC"""
        try:
            cursor.execute(query)
            for row in cursor:
                result.append(row["media"])
        except Exception as e:
            print(e)
            result = None
        finally:
            cursor.close()
            cnx.close()
        return result



    """
    Un nodo e' un attore che:
    - ha recitato in almeno un film con voto medio tra minR e maxR;
    - ha una data di nascita nota (eta' calcolabile);
    - ha un'eta' sensata (strettamente positiva).
    NB: per i NODI la casa di produzione NON conta (la consegna la usa
    solo per gli archi): un attore i cui film nel range hanno tutti
    production_company NULL e' comunque un vertice (restera' isolato).
    """
    @staticmethod
    def getNodi(minR,maxR):
        cnx = DBConnect.get_connection()
        result = []
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT DISTINCT n.id,n.name, TIMESTAMPDIFF(YEAR, n.date_of_birth, CURDATE()) AS eta
                    FROM names n, role_mapping rm, ratings r
                    WHERE  n.id = rm.name_id AND rm.movie_id = r.movie_id
                    AND n.date_of_birth IS NOT NULL
                    AND r.avg_rating BETWEEN %s AND %s
                    AND TIMESTAMPDIFF(YEAR, n.date_of_birth, CURDATE()) > 0 """
        try:
            cursor.execute(query, (minR,maxR))
            for row in cursor:
                result.append(Attore(**row))
        except Exception as e:
            print(f"Errore in getNodi: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result

    """
    Arco tra due attori se esiste ALMENO una casa di produzione in comune
    tra i loro film nel range (anche film DIVERSI: percio' servono DUE
    catene di join separate, una per attore, agganciate solo dall'uguaglianza
    delle production_company). Peso = numero di case distinte in comune.
    - m.production_company IS NOT NULL: la consegna considera solo i film
      con casa di produzione nota (basta metterlo su m1: l'uguaglianza
      m1.pc = m2.pc esclude da sola i NULL di m2, ma lo esplicito per chiarezza)
    - COUNT(DISTINCT ...) e' essenziale: la stessa casa condivisa tramite
      piu' coppie di film deve contare UNA volta sola
    - rm1.name_id < rm2.name_id: ogni coppia esce una volta, niente self-loop
    """
    @staticmethod
    def getEdges(minR, maxR):

        cnx = DBConnect.get_connection()
        result = []
        if cnx is None:
            return result
        cursor = cnx.cursor(dictionary=True)
        query = """SELECT rm1.name_id AS a1, rm2.name_id AS a2,
                          COUNT(DISTINCT m1.production_company) AS peso
                    FROM role_mapping rm1, movie m1, ratings r1,
                         role_mapping rm2, movie m2, ratings r2
                    WHERE rm1.movie_id = m1.id AND m1.id = r1.movie_id
                    AND rm2.movie_id = m2.id AND m2.id = r2.movie_id
                    AND m1.production_company = m2.production_company
                    AND m1.production_company IS NOT NULL
                    AND m2.production_company IS NOT NULL
                    AND rm1.name_id < rm2.name_id
                    AND r1.avg_rating BETWEEN %s AND %s
                    AND r2.avg_rating BETWEEN %s AND %s
                    GROUP BY rm1.name_id, rm2.name_id
                        """

        try:
            cursor.execute(query, (minR, maxR, minR, maxR))
            for row in cursor:
                result.append(row)
        except Exception as e:
            print(f"Errore in getEdges: {e}")
        finally:
            cursor.close()
            cnx.close()
        return result