class InMemoryStore:
    def __init__(self):
        self._data = {}

    def get(self, run_id):
        return self._data.get(run_id)

    def set(self, run_id, state):
        self._data[run_id] = state


store = InMemoryStore()
