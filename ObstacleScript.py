
import pygame
from collections import deque
import numpy as np
import math

import GameFunction as GF

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from AgentScript import Agent_2D

class HitInfo():
    def __init__(self, ray_start : pygame.Vector2, ray_end : pygame.Vector2, hitPoint : pygame.Vector2, hitNormal : pygame.Vector2, hitDistance : pygame.Vector2):
        """
        ray_start : pygame.Vector2
            starting position of the ray
        ray_end : pygame.Vector2
            ending position of the ray
        hitPoint : pygame.Vector2
            hit position
        hitNotmal : pygame.Vector2
            Normal direction of the colliding object
        hitDistance : float
            Distance between collider and target
        """
        self.ray_start = ray_start
        self.ray_end = ray_end

        self.hitPoint = hitPoint
        self.hitNormal = hitNormal
        self.hitDistance = hitDistance

        # How long it travels before hitting the obstacle. 
        # Negitive value means that it won't hit the obstacle.
        self.t = -1

class ObstaclesByShape():
    def __init__(self, shape_info, location : pygame.Vector2, rotation_deg : float, scale : pygame.Vector2):
        """
        shape_info:  points list of a face (nd.array or list, shape = [N, 2])
        """

        self.num_of_points = len(shape_info)
        self.rotation_deg = rotation_deg
        self.location = location

        # [N, 2], points list of a face
        self.points = [pygame.Vector2(shape_info[i][0] * scale[0], shape_info[i][1] * scale[1]) for i in range(self.num_of_points)]
        self.ApplyRotation()
        self.ApplyLocation()

        self.color = (200,200,200)

        # [N, 2], index of all lines to the points
        self.lines_index = [[i, (i+1) % self.num_of_points] for i in range(self.num_of_points)]

        # normal vector of the line
        self.normals = self.GetNormal()

    def GetNormal(self):
        normals = []
        for line_index in self.lines_index:
            edge = self.points[line_index[0]] - self.points[line_index[1]]
            if edge.length() > 0:
                n = pygame.Vector2(-edge.y, edge.x).normalize()
            else:
                n = pygame.Vector2(0, 0) 
            normals.append(n)
        return normals

    def ApplyRotation(self):
        for i in range(self.num_of_points):
            self.points[i] = self.points[i].rotate(self.rotation_deg)

    def ApplyLocation(self):
        for i in range(self.num_of_points):
            self.points[i] = self.points[i] + self.location
    

class Obstacle():
    def __init__(self, make_init_obstacle = True):
        self.num_of_obs = 4

        self.shape_square = [[1,1],[-1,1],[-1,-1],[1,-1]]
        self.shape_triangle = [[0,1],[-0.866,-0.5],[0.866,-0.5]]
        self.obstacle_location = [pygame.Vector2(500, 0), pygame.Vector2(-500, 0), pygame.Vector2(0, 500), pygame.Vector2(0, -500)]

        self.shape_list = [self.shape_square, self.shape_triangle, self.shape_square, self.shape_triangle]
        self.Obstacle_list = []
        
        if make_init_obstacle:
            self.Obstacle_list.append(ObstaclesByShape(self.shape_square, 
                                                    pygame.Vector2(500, 0), 
                                                    45, 
                                                    pygame.Vector2(100,300)))
            
            self.Obstacle_list.append(ObstaclesByShape(self.shape_triangle, 
                                                    pygame.Vector2(-500, 0), 
                                                    60, 
                                                    pygame.Vector2(250,250)))
            
            self.Obstacle_list.append(ObstaclesByShape(self.shape_square, 
                                                    pygame.Vector2(0, 500), 
                                                    115, 
                                                    pygame.Vector2(100, 300)))
            
            self.Obstacle_list.append(ObstaclesByShape(self.shape_triangle, 
                                                    pygame.Vector2(0, -500), 
                                                    160, 
                                                    pygame.Vector2(300,300)))
            
        pass

    def RayWithWhiskers(self, agent : "Agent_2D", whisker_length = 200, screen = None, center = None, w = None):
        """
        One main front ray, and two short angled rays.
        
        If center not none, this function will draw debug Line

        Returns
        -------
        list[Bool], 
            A list containing:
            [is_front_ray_collision, is_left_whisker_collision, is_right_whisker_collision]
        list[HitInfo]
            A list containing:
            [front_ray_hit, Left_whisker_hit, right_whisker_hit]
        """
        isC_list = []
        hitInfo_list = []

        # If the velocity is 0, disable collision detection.
        if agent.vel2D.length_squared() == 0:
            isC_list = [False, False, False]
            hitInfo_list = [None, None, None]
            return isC_list, hitInfo_list

        ray_start = agent.pos2D

        # Front Ray
        ray_end = agent.pos2D + agent.vel2D.normalize() * 4000
        isC, hitInfo = self.CollisionDetectionByRay(ray_start, ray_end)
        isC_list.append(isC)
        if isC:
            r_der = (hitInfo.hitPoint - ray_start)
            t = r_der.length() / (agent.vel2D.dot(r_der.normalize()))
            if abs(t) > 0.001:
                hitInfo.t = t
        hitInfo_list.append(hitInfo)
        if screen is not None and center is not None:
            pygame.draw.line(screen, (0,0,0), 
                                GF.to_screen(ray_start + center, w),
                                GF.to_screen(ray_end + center, w))

        # Left Whisker
        ray_end = agent.pos2D +  agent.vel2D.normalize().rotate(45) * whisker_length
        isC, hitInfo = self.CollisionDetectionByRay(ray_start, ray_end)
        if isC:
            r_der = (hitInfo.hitPoint - ray_start)
            t = r_der.length() / (agent.vel2D.dot(r_der.normalize()))
            if abs(t) > 0.001:
                hitInfo.t = t
        isC_list.append(isC)
        hitInfo_list.append(hitInfo)
        if screen is not None and center is not None:
            pygame.draw.line(screen, (0,0,0), 
                                GF.to_screen(ray_start + center, w),
                                GF.to_screen(ray_end + center, w))
        
        # Right Whisker
        ray_end = agent.pos2D + agent.vel2D.normalize().rotate(-45) * whisker_length
        isC, hitInfo = self.CollisionDetectionByRay(ray_start, ray_end)
        if isC:
            r_der = (hitInfo.hitPoint - ray_start)
            t = r_der.length() / (agent.vel2D.dot(r_der.normalize()))
            if abs(t) > 0.001:
                hitInfo.t = t
        isC_list.append(isC)
        hitInfo_list.append(hitInfo)
        if screen is not None and center is not None:
            pygame.draw.line(screen, (0,0,0), 
                                GF.to_screen(ray_start + center, w),
                                GF.to_screen(ray_end + center, w))
        
        return isC_list, hitInfo_list
        pass

    def CollisionDetectionByRay(self, ray_start, ray_end):
        """
        Collision Detection By Ray

        Returns
        -------
        return isCollider:Bool, hitInfo:HitInfo
        """
        isC = False                 # is collision
        hitInfo = None
        min_t = float('inf')        # to find the nearest impact point

        # Every obstacle
        for obstacle in self.Obstacle_list:
            """
            Collision detection by ray
            """
            # Traverse all edges of the obstacle
            for i, idx_pair in enumerate(obstacle.lines_index):
                p1 = obstacle.points[idx_pair[0]]
                p2 = obstacle.points[idx_pair[1]]

                r = ray_end - ray_start
                s = p2 - p1
                
                # cross
                cross = r.x * s.y - r.y * s.x
                
                # If the denominator is 0, it means that the two line segments are parallel.
                if abs(cross) < 1e-6:
                    continue

                # ray_start + t * r = p1 + u * s
                diff = p1 - ray_start
                # t * r - u * s = diff
                # cross(t*r - u*s, s) = cross(diff, s)
                # t * cross(r, s) - u * cross(s, s) = cross(diff, s)
                # t = cross(diff, s) / cross(r, s)
                # u = cross(diff, t) / cross(r, s)
                t = (diff.x * s.y - diff.y * s.x) / cross
                u = (diff.x * r.y - diff.y * r.x) / cross

                # 3. 判斷交點是否在兩條線段的範圍內
                # t 在 [0, 1] 表示在 Agent 預測路徑上
                # u 在 [0, 1] 表示在障礙物的該條邊上
                if 0 <= t <= 1 and 0 <= u <= 1:
                    if t < min_t:
                        min_t = t
                        # Calculate collision position
                        closest_hit_point = ray_start + t * r
                        current_dist = t * (ray_end - ray_start).length()
                        hitInfo = HitInfo(ray_start = ray_start, ray_end = ray_end, 
                                          hitPoint = closest_hit_point, hitNormal = obstacle.normals[i], hitDistance = current_dist)
                        isC = True

        return isC, hitInfo

    def HandleCollision(self, agent : "Agent_2D", restitution=0.5):
        """
        When the agent touches the wall, bounce it away.
        """
        for obstacle in self.Obstacle_list:
            for i, idx_pair in enumerate(obstacle.lines_index):
                p1 = obstacle.points[idx_pair[0]]
                p2 = obstacle.points[idx_pair[1]]
                normal = obstacle.normals[i]

                p1_to_p2 = p2 - p1
                agent_to_p1 = agent.pos2D - p1
                
                # Projection scale t (from p1 to p2)
                t = agent_to_p1.dot(p1_to_p2) / p1_to_p2.length_squared()

                # t = 0, This means the projection point is exactly at p1
                # t = 1, This means the projection point is exactly at p2
                t = max(0, min(1, t))
                
                # The point on the line segment closest to the Agent
                closest_point = p1 + t * p1_to_p2
                agent_to_line = agent.pos2D - closest_point
                distance = agent_to_line.length()

                # Check collision (distance < radius).
                if distance < agent.radius:
                    overlap = agent.radius - distance
                    
                    # Adjust agent position
                    agent.pos2D += normal * overlap

                    # Velocity bounce
                    agent.vel2D = agent.vel2D - (1 + restitution) * agent.vel2D.dot(normal) * normal
                    agent.acc2D *= 0

    def check_obstacle_collision(self, agent : "Agent_2D"):
        """
        Detect whether the Agent will collide with the edge of a polygonal obstacle in the near future.
        """
 
        ray_start = agent.pos2D
        ray_end = agent.pos2D + agent.vel2D.normalize() * 4000
        isC, closest_hit_point = self.CollisionDetectionByRay(ray_start, ray_end)

        return isC, closest_hit_point