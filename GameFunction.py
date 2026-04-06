import pygame
import math

def to_pygame_degree(degree):
    degree = degree + 270
    return degree

def to_screen(pos, screen_height):
    return pygame.Vector2(pos.x, screen_height - pos.y)

def draw_arrow(screen, start, end, color = (255, 0, 0), body_width = 2, head_width = 10):
    # Draw line segment
    pygame.draw.line(screen, color, start, end, body_width)
    
    # Calculate angle
    dx = end[0] - start[0]
    dy = end[1] - start[1]
    angle = math.atan2(dy, dx)

    # Calculate the three points at the head of the arrow.
    p1 = (end[0] - head_width * math.cos(angle - math.pi / 6),
          end[1] - head_width * math.sin(angle - math.pi / 6))
    p2 = (end[0] - head_width * math.cos(angle + math.pi / 6),
          end[1] - head_width * math.sin(angle + math.pi / 6))
    
    # Draw the head of the arrow
    pygame.draw.polygon(screen, color, [end, p1, p2])