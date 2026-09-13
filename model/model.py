import networkx as nx

from database.DAO import DAO


class Model:
    def __init__(self):
        self._grafo = nx.Graph()   # NON orientato (consegna 1b) - con DiGraph le
                                   # componenti connesse crashano (NetworkXNotImplemented)
        self._nodi = []            # lista di oggetti Attore (i vertici)
        self._idMap = {}           # id attore -> oggetto Attore
        self._camminoBest = []     # risultato della ricorsione del punto 2

    def getRatings(self):
        """Passa-carte verso il DAO: il controller non deve mai toccare
        il DAO direttamente (MVC), quindi passa sempre dal Model."""
        return DAO.getAllRatings()

    # ------------------------------------------------------------------
    # PUNTO 1 - costruzione del grafo
    # ------------------------------------------------------------------
    def buildGraph(self, minR, maxR):
        """Grafo NON orientato e pesato:
        - nodi  = attori con eta' valida nei film con voto nel range
        - archi = coppie di attori i cui film nel range (anche diversi)
                  condividono almeno una casa di produzione nota
        - peso  = numero di case di produzione DISTINTE in comune"""
        self._grafo.clear()   # senza clear, un secondo click su "Crea Grafo"
                              # accumulerebbe i nodi/archi del grafo precedente

        # --- NODI ---
        self._nodi = DAO.getNodi(minR, maxR)
        self._idMap = {a.id: a for a in self._nodi}
        self._grafo.add_nodes_from(self._nodi)

        # --- ARCHI ---
        # getEdges fa tutto in SQL: doppio join agganciato sulla
        # production_company + GROUP BY sulla coppia. Ogni riga e' un arco
        # definitivo con il suo peso (n. case distinte in comune).
        for row in DAO.getEdges(minR, maxR):
            # entrambi gli attori devono essere nodi validi (eta' calcolabile
            # e positiva), altrimenti l'idMap darebbe KeyError: la query degli
            # archi non filtra sulla data di nascita, quella dei nodi si'
            if row["a1"] in self._idMap and row["a2"] in self._idMap:
                self._grafo.add_edge(self._idMap[row["a1"]],
                                     self._idMap[row["a2"]],
                                     weight=row["peso"])

    # ------------------------------------------------------------------
    # PUNTO 1c - statistiche del grafo
    # ------------------------------------------------------------------
    def getNumNodi(self):
        return len(self._grafo.nodes)

    def getNumArchi(self):
        return len(self._grafo.edges)

    def getNodi(self):
        return self._nodi

    def getTop5Archi(self):
        """I 5 archi di peso maggiore, come triple (Attore, Attore, peso).
        edges(data=True) da' triple (n1, n2, {"weight": p}):
        ordino sul peso (e[2]["weight"]) decrescente e taglio con [:5]."""
        archi = sorted(self._grafo.edges(data=True),
                       key=lambda e: e[2]["weight"],
                       reverse=True)
        result = []
        for a1, a2, dati in archi[:5]:
            result.append((a1, a2, dati["weight"]))
        return result

    def getNumComponenti(self):
        """Quante 'isole' di attori: dentro ogni isola tutti raggiungibili
        tra loro, tra un'isola e l'altra nessun arco. Un nodo senza archi
        e' una componente da 1 (es. attori con soli film senza casa nota)."""
        return nx.number_connected_components(self._grafo)

    def getMaxComponente(self):
        """La componente connessa piu' grande, come lista di Attori.
        connected_components genera le componenti come SET di nodi;
        max(..., key=len) sceglie il set piu' numeroso (confronta le taglie,
        ma restituisce il set intero); list() lo converte per il controller."""
        if self.getNumNodi() == 0:
            return []   # max() su sequenza vuota lancia ValueError: va gestito
        return list(max(nx.connected_components(self._grafo), key=len))

    # ------------------------------------------------------------------
    # PUNTO 2 - cammino semplice piu' lungo con eta' strettamente decrescente
    # ------------------------------------------------------------------
    def getCamminoMax(self):
        """Lancia la ricorsione da OGNI nodo: il cammino migliore
        puo' iniziare ovunque, non lo so a priori."""
        self._camminoBest = []
        for nodo in self._grafo.nodes:
            self._ricorsione([nodo])
        return self._camminoBest

    def _ricorsione(self, parziale):
        # ogni parziale e' gia' un cammino valido: se batte il record lo salvo.
        # list(parziale) fa la COPIA: senza, i pop() successivi svuoterebbero
        # anche il best (sarebbero lo stesso oggetto lista)
        if len(parziale) > len(self._camminoBest):
            self._camminoBest = list(parziale)

        # provo ad allungare il cammino con i vicini dell'ultimo nodo
        for vicino in self._grafo.neighbors(parziale[-1]):
            # not in parziale  -> cammino SEMPLICE (nessun nodo ripetuto)
            # eta <  (stretto) -> "eta' strettamente decrescente" (consegna 2)
            if vicino not in parziale and vicino.eta < parziale[-1].eta:
                parziale.append(vicino)     # scelgo
                self._ricorsione(parziale)  # esploro
                parziale.pop()              # torno indietro (backtracking)
        # niente caso terminale esplicito: la ricorsione muore da sola
        # quando nessun vicino passa i due filtri