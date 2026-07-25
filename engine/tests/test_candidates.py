import pytest
import numpy as np
from astrax_engine.detection.candidates import Candidate, link_candidates

def test_link_candidates_empty():
    current = []
    previous = []
    
    linked = link_candidates(current, previous)
    assert len(linked) == 0

def test_link_candidates_match():
    # Previous candidates
    c1 = Candidate(x=10.0, y=10.0, frame_index=0)
    
    # Current candidates slightly moved
    c2 = Candidate(x=12.0, y=12.0, frame_index=1)
    
    linked = link_candidates([c2], [c1], max_distance=5.0)
    
    assert len(linked) == 1
    assert linked[0].motion_dx == 2.0
    assert linked[0].motion_dy == 2.0
    assert linked[0].detection_count == 2
    assert linked[0].persistence_score > c2.persistence_score

def test_link_candidates_no_match():
    c1 = Candidate(x=10.0, y=10.0, frame_index=0)
    c2 = Candidate(x=100.0, y=100.0, frame_index=1)
    
    # Too far apart to link
    linked = link_candidates([c2], [c1], max_distance=5.0)
    
    assert len(linked) == 1
    assert linked[0].detection_count == 1
    assert linked[0].motion_dx == 0.0
