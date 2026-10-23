"""FIFO, LRU, and Optimal page replacement simulations."""


class PageReplacementSimulator:
    def __init__(self, reference_string, frame_capacity):
        self.pages = list(reference_string)
        if isinstance(frame_capacity, bool) or not isinstance(frame_capacity, int) or frame_capacity < 1:
            raise ValueError("frame_capacity must be a positive integer.")
        if any(isinstance(page, bool) or not isinstance(page, int) or page < 0 for page in self.pages):
            raise ValueError("Page references must be non-negative integers.")
        self.capacity = frame_capacity

    def _simulate(self, algorithm):
        frames = []
        snapshots, outcomes = [], []
        faults = hits = 0
        for index, page in enumerate(self.pages):
            if page in frames:
                hits += 1
                outcomes.append("Hit")
                if algorithm == "LRU":
                    frames.remove(page)
                    frames.append(page)
            else:
                faults += 1
                outcomes.append("Fault")
                if len(frames) < self.capacity:
                    frames.append(page)
                elif algorithm == "FIFO" or algorithm == "LRU":
                    frames.pop(0)
                    frames.append(page)
                else:
                    future = self.pages[index + 1:]
                    next_use = {frame: (future.index(frame) if frame in future else float("inf")) for frame in frames}
                    victim = max(frames, key=lambda frame: next_use[frame])
                    frames[frames.index(victim)] = page
            snapshots.append(list(frames))
        total = len(self.pages)
        return {
            "algorithm": algorithm, "page_faults": faults, "hits": hits,
            "hit_ratio": round(hits / total * 100, 2) if total else 0.0,
            "fault_ratio": round(faults / total * 100, 2) if total else 0.0,
            "frame_snapshots": snapshots, "outcomes": outcomes,
        }

    def fifo(self):
        return self._simulate("FIFO")

    def lru(self):
        return self._simulate("LRU")

    def optimal(self):
        return self._simulate("Optimal")


if __name__ == "__main__":
    simulator = PageReplacementSimulator([7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3], 3)
    print("FIFO:", simulator.fifo())
    print("LRU:", simulator.lru())
    print("Optimal:", simulator.optimal())
