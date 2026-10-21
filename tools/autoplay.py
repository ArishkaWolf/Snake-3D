"""Только инструмент тестирования: поиск короткого безопасного пути к яблоку."""
from collections import deque
from game.snake import Direction


def choose_direction(game):
    head=game.body[0]
    queue=deque([(head,[])])
    visited={head}
    blocked=set(game.body[1:])|set(game.obstacles)
    while queue:
        cell,path=queue.popleft()
        if cell==game.food:
            return path[0] if path else game.direction
        for direction in Direction:
            if not path and (direction-game.direction)%4==2:
                continue
            dx,dy=direction.vector
            next_cell=(cell[0]+dx,cell[1]+dy)
            if (0<=next_cell[0]<game.size and 0<=next_cell[1]<game.size and
                    next_cell not in visited and next_cell not in blocked):
                visited.add(next_cell)
                queue.append((next_cell,path+[direction]))
    # Если яблоко отрезано телом, выбираем безопасный ход и ждём освобождения пути.
    for direction in (game.direction,Direction((game.direction+1)%4),Direction((game.direction-1)%4)):
        dx,dy=direction.vector
        cell=(head[0]+dx,head[1]+dy)
        if (0<=cell[0]<game.size and 0<=cell[1]<game.size and
                cell not in set(game.body[:-1])|set(game.obstacles)):
            return direction
    return game.direction
