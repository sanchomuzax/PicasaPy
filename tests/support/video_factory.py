"""Közös teszt-fixture: kis MP4 generálás OpenCV VideoWriterrel."""

import cv2
import numpy as np


def make_mp4(path, size=(64, 32), frames=5, fps=10):
    writer = cv2.VideoWriter(str(path), cv2.VideoWriter_fourcc(*"mp4v"), fps, size)
    if not writer.isOpened():
        raise RuntimeError(f"VideoWriter nem nyitható: {path}")
    width, height = size
    for index in range(frames):
        writer.write(np.full((height, width, 3), (index * 40) % 256, np.uint8))
    writer.release()
    return path
