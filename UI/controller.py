import flet as ft


class Controller:
    def __init__(self, view, model):
        # the view, with the graphical elements of the UI
        self._view = view
        # the model, which implements the logic of the program and holds the data
        self._model = model

    def fillDDsRating(self):
        ratings = self._model.getRatings()
        if not ratings:
            self._view.create_alert("Errore nel caricamento dei voti dal database")
            return
        for v in ratings:
            self._view._ddrating1.options.append(ft.dropdown.Option(str(v)))
            self._view._ddrating2.options.append(ft.dropdown.Option(str(v)))

    def handleCreaGrafo(self, e):
        v1 = self._view._ddrating1.value
        v2 = self._view._ddrating2.value
        if v1 is None or v2 is None:
            self._view.create_alert("Selezionare entrambi i voti")
            return
        try:
            minR = float(v1)
            maxR = float(v2)
        except ValueError:
            self._view.create_alert("Valori dei voti non validi")
            return
        if minR > maxR:
            self._view.create_alert("Il primo voto deve essere minore o uguale al secondo")
            return

        self._model.buildGraph(minR, maxR)

        self._view.txt_result.controls.clear()
        self._view.txt_result.controls.append(ft.Text("Grafo correttamente creato:"))
        self._view.txt_result.controls.append(ft.Text(f"Numero di nodi: {self._model.getNumNodi()}"))
        self._view.txt_result.controls.append(ft.Text(f"Numero di archi: {self._model.getNumArchi()}"))

        self._view.txt_result.controls.append(ft.Text("Top 5 archi:"))
        for a1, a2, peso in self._model.getTop5Archi():
            self._view.txt_result.controls.append(ft.Text(f"{a1.name} -> {a2.name} : {peso}"))

        self._view.txt_result.controls.append(
            ft.Text(f"Il grafo ha {self._model.getNumComponenti()} componenti connesse"))
        maxComp = self._model.getMaxComponente()
        self._view.txt_result.controls.append(
            ft.Text(f"La più grande componente connessa è lunga {len(maxComp)}:"))
        for attore in maxComp:
            self._view.txt_result.controls.append(ft.Text(attore.name))

        self._view.update_page()

    def handleCammino(self, e):
        if self._model.getNumNodi() == 0:
            self._view.create_alert("Creare prima il grafo")
            return

        cammino = self._model.getCamminoMax()
        self._view.txt_result.controls.clear()
        self._view.txt_result.controls.append(
            ft.Text(f"Il cammino più lungo ha {len(cammino)} attori:"))
        for attore in cammino:
            self._view.txt_result.controls.append(ft.Text(f"{attore.name} ({attore.eta} anni)"))
        self._view.update_page()