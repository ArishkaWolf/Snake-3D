from random import Random
import pytest
from game.levels import LEVELS
from game.snake import SnakeGame
from tools.autoplay import choose_direction


@pytest.mark.parametrize("level",LEVELS,ids=lambda l:l.id)
@pytest.mark.parametrize("seed",range(10))
def test_complete_level_with_real_movement(level,seed):
    game=SnakeGame(goal=level.goal,obstacles=level.obstacles,rng=Random(seed))
    for _ in range(6000):
        direction=choose_direction(game)
        if direction!=game.direction:
            assert game.request_direction(direction)
        game.step()
        if game.status!="playing":
            break
    assert game.status=="won"
    assert game.score==level.goal
    assert len(game.body)==4+level.goal
