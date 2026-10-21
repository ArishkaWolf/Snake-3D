from random import Random
import pytest
from game.snake import SnakeGame, Direction


def test_initial_body_and_movement():
    game=SnakeGame(rng=Random(0))
    before=list(game.body)
    game.food=(0,0)
    assert game.step()=="moved"
    assert game.body==[(before[0][0],before[0][1]+1)]+before[:-1]
    assert game.previous==before


@pytest.mark.parametrize("size",[6,8,20])
def test_spawn_body_inside_arena(size):
    game=SnakeGame(size=size)
    assert len(game.body)==len(set(game.body))==4
    assert all(0<=x<size and 0<=y<size for x,y in game.body)


@pytest.mark.parametrize("direction",list(Direction))
@pytest.mark.parametrize("side",[-1,1])
def test_relative_turns(direction,side):
    game=SnakeGame()
    game.direction=direction
    assert game.turn(side)
    assert game.pending_direction==Direction((direction+side)%4)
    assert game.direction==direction  # Направление меняется на границе шага.


@pytest.mark.parametrize("direction",list(Direction))
def test_no_reverse(direction):
    game=SnakeGame()
    game.direction=direction
    assert not game.request_direction((direction+2)%4)
    assert game.pending_direction is None
    assert not game.request_direction(direction)


def test_one_turn_per_step_and_queue_released():
    game=SnakeGame()
    game.food=(0,0)
    assert game.turn(1)
    assert not game.turn(1)
    assert not game.turn(-1)
    game.step()
    assert game.direction==Direction.EAST
    assert game.turn(1)
    game.step()
    assert game.direction==Direction.SOUTH


def test_growth_retains_tail_and_food_changes():
    game=SnakeGame(rng=Random(1))
    tail=game.body[-1]
    x,y=game.body[0]
    game.food=(x,y+1)
    assert game.step()=="ate"
    assert len(game.body)==5
    assert game.body[-1]==tail
    assert game.score==1
    assert game.food not in game.body


@pytest.mark.parametrize("head,direction",[((5,19),Direction.NORTH),((19,5),Direction.EAST),((5,0),Direction.SOUTH),((0,5),Direction.WEST)])
def test_wall_collision(head,direction):
    game=SnakeGame()
    game.body=[head]
    game.direction=direction
    assert game.step()=="lost"
    assert game.body==[head]
    assert game.step()=="idle"
    assert not game.turn(1)


def test_body_collision():
    game=SnakeGame()
    game.body=[(3,3),(3,2),(4,2),(4,3),(4,4)]
    game.direction=Direction.EAST
    game.food=(0,0)
    assert game.step()=="lost"


def test_can_move_into_departing_tail():
    game=SnakeGame()
    game.body=[(3,3),(3,2),(4,2),(4,3)]
    game.direction=Direction.EAST
    game.food=(0,0)
    assert game.step()=="moved"
    assert game.body[0]==(4,3)
    assert len(set(game.body))==4


def test_obstacle_collision():
    game=SnakeGame(obstacles={(10,10)})
    assert game.step()=="lost"
    assert "камень" in game.reason


def test_food_never_spawns_on_body_or_obstacles():
    game=SnakeGame(obstacles={(0,0),(0,1)},rng=Random(7))
    for _ in range(500):
        food=game.spawn_food()
        assert food not in game.body and food not in game.obstacles
        assert 0<=food[0]<20 and 0<=food[1]<20


def test_full_board_wins_without_random_choice_on_empty_sequence():
    game=SnakeGame(size=6)
    game.body=[(1,0)]+[(x,y) for x in range(6) for y in range(6) if (x,y) not in ((1,0),(0,0))]
    game.direction=Direction.WEST
    game.food=(0,0)
    assert game.step()=="won"
    assert game.food is None
    assert len(game.body)==36


@pytest.mark.parametrize("goal",[5,10,15])
def test_goals(goal):
    game=SnakeGame(goal=goal)
    game.score=goal-1
    game.food=(10,10)
    assert game.step()=="won"
    assert game.score==goal


def test_endless_does_not_end_at_fifteen():
    game=SnakeGame()
    game.score=14
    game.food=(10,10)
    assert game.step()=="ate"
    assert game.status=="playing"


def test_interpolation_and_growth_tail():
    game=SnakeGame()
    old=list(game.body)
    game.food=(10,10)
    game.step()
    assert game.interpolated(0)==old+[old[-1]]
    assert game.interpolated(1)==game.body
    assert game.interpolated(0.5)[0]==(10,9.5)
    assert game.interpolated(-1)==game.interpolated(0)


def test_invalid_inputs():
    with pytest.raises(ValueError):
        SnakeGame(size=5)
    with pytest.raises(ValueError):
        SnakeGame().turn(0)
