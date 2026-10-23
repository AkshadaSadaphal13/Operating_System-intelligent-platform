"""Banker's safety analysis and multi-instance deadlock detection."""

import numpy as np


def _integer_array(value, name):
    try:
        raw = np.asarray(value)
        if np.issubdtype(raw.dtype, np.bool_):
            raise ValueError(f"{name} must contain finite integers.")
        numeric = raw.astype(float)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError(f"{name} must contain finite integers.") from exc
    if not np.all(np.isfinite(numeric)) or not np.all(numeric == np.floor(numeric)):
        raise ValueError(f"{name} must contain finite integers.")
    return numeric.astype(int)


def _matrix(value, name, columns=None):
    array = _integer_array(value, name)
    if array.ndim != 2 or (columns is not None and array.shape[1] != columns):
        raise ValueError(f"{name} must be a 2-D matrix with {columns or 'consistent'} resource columns.")
    if np.any(array < 0):
        raise ValueError(f"{name} cannot contain negative quantities.")
    return array


class BankerAlgorithm:
    def __init__(self, total_resources, allocation_matrix, max_matrix):
        self.total = _integer_array(total_resources, "total_resources")
        if self.total.ndim != 1 or self.total.size == 0 or np.any(self.total < 0):
            raise ValueError("total_resources must be a non-empty vector of non-negative integers.")
        self.allocation = _matrix(allocation_matrix, "allocation_matrix", len(self.total))
        self.max = _matrix(max_matrix, "max_matrix", len(self.total))
        if self.allocation.shape != self.max.shape:
            raise ValueError("Allocation and maximum matrices must have the same shape.")
        if np.any(self.allocation > self.max):
            raise ValueError("A current allocation cannot exceed its declared maximum.")
        allocated = np.sum(self.allocation, axis=0)
        if np.any(allocated > self.total):
            raise ValueError("Allocated resources cannot exceed system totals.")
        self.need = self.max - self.allocation
        self.available = self.total - allocated
        self.num_processes, self.num_resources = self.allocation.shape

    @staticmethod
    def _pid(index):
        return f"P{index}"

    def check_safety_state(self):
        work = self.available.copy()
        finish = [False] * self.num_processes
        safe_sequence = []
        while len(safe_sequence) < self.num_processes:
            candidate = next((p for p in range(self.num_processes)
                              if not finish[p] and np.all(self.need[p] <= work)), None)
            if candidate is None:
                return False, [], "System is in an UNSAFE state (no complete safe sequence exists)."
            work += self.allocation[candidate]
            finish[candidate] = True
            safe_sequence.append(self._pid(candidate))
        return True, safe_sequence, "System is in a SAFE state."

    def request_resources(self, process_id, request_vector):
        if isinstance(process_id, bool) or not isinstance(process_id, int) or not 0 <= process_id < self.num_processes:
            raise ValueError("process_id is outside the process matrix.")
        request = _integer_array(request_vector, "request_vector")
        if request.shape != (self.num_resources,) or np.any(request < 0):
            raise ValueError("request_vector must be a non-negative value per resource type.")
        if np.any(request > self.need[process_id]):
            return False, f"Error: {self._pid(process_id)} exceeded its declared maximum claim."
        if np.any(request > self.available):
            return False, f"{self._pid(process_id)} must wait; resources are unavailable."
        self.available -= request
        self.allocation[process_id] += request
        self.need[process_id] -= request
        safe, sequence, _ = self.check_safety_state()
        if safe:
            return True, f"Request granted. Safe sequence: {' -> '.join(sequence)}"
        self.available += request
        self.allocation[process_id] -= request
        self.need[process_id] += request
        return False, "Request denied; granting it would leave the system unsafe."

    def detect_deadlock(self, outstanding_request):
        """Apply the standard multi-instance detection algorithm.

        outstanding_request[p, r] is the quantity process p is currently
        requesting, not its maximum future claim.
        """
        request = _matrix(outstanding_request, "outstanding_request", self.num_resources)
        if request.shape != self.allocation.shape:
            raise ValueError("outstanding_request must match the allocation matrix shape.")
        work = self.available.copy()
        finish = [not bool(np.any(self.allocation[p])) for p in range(self.num_processes)]
        sequence = []
        while True:
            candidate = next((p for p in range(self.num_processes)
                              if not finish[p] and np.all(request[p] <= work)), None)
            if candidate is None:
                break
            work += self.allocation[candidate]
            finish[candidate] = True
            sequence.append(self._pid(candidate))
        deadlocked = [self._pid(p) for p, done in enumerate(finish) if not done]
        return {
            "deadlocked": bool(deadlocked),
            "processes": deadlocked,
            "completion_sequence": sequence,
            "message": (f"Deadlock detected among: {', '.join(deadlocked)}" if deadlocked
                        else "No deadlock detected for the supplied outstanding requests."),
        }

    def wait_for_graph(self, outstanding_request):
        """Return a dependency adjacency map for processes currently blocked.

        An edge P_i -> P_j means P_j holds a resource type requested by P_i.
        This graph is explanatory; multi-instance deadlock classification uses
        detect_deadlock(), not cycle presence alone.
        """
        request = _matrix(outstanding_request, "outstanding_request", self.num_resources)
        if request.shape != self.allocation.shape:
            raise ValueError("outstanding_request must match the allocation matrix shape.")
        graph = {self._pid(p): [] for p in range(self.num_processes)}
        for p in range(self.num_processes):
            blocked = np.any(request[p] > self.available)
            if blocked:
                for q in range(self.num_processes):
                    if p != q and np.any((request[p] > self.available) & (self.allocation[q] > 0)):
                        graph[self._pid(p)].append(self._pid(q))
        return graph


if __name__ == "__main__":
    total = [10, 5, 7]
    allocation = [[0, 1, 0], [2, 0, 0], [3, 0, 2], [2, 1, 1], [0, 0, 2]]
    maximum = [[7, 5, 3], [3, 2, 2], [9, 0, 2], [2, 2, 2], [4, 3, 3]]
    banker = BankerAlgorithm(total, allocation, maximum)
    print("Safety:", banker.check_safety_state())
    print("Current deadlock:", banker.detect_deadlock(np.zeros_like(banker.allocation)))
