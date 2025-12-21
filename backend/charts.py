import os
from typing import List
import matplotlib.pyplot as plt


def _ensure_dir(path: str) -> None:
    os.makedirs(os.path.dirname(path), exist_ok=True)


def draw_confidence_histogram(confidences: List[float], path: str) -> None:
    _ensure_dir(path)
    plt.figure()
    plt.hist(confidences, bins=10)
    plt.title("Confidence Distribution")
    plt.xlabel("confidence")
    plt.ylabel("count")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()


def draw_confidence_trend(confidences: List[float], path: str) -> None:
    _ensure_dir(path)
    plt.figure()
    plt.plot(confidences)
    plt.title("Confidence Trend")
    plt.xlabel("index")
    plt.ylabel("confidence")
    plt.tight_layout()
    plt.savefig(path)
    plt.close()
