import pygame
from collections import deque
import numpy as np
import math

import GameFunction as GF

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from ObstacleScript import Obstacle

class Agent_2D():
    def __init__(self, x, y, radius = 10, max_velocity=500.0, max_acceleration=999.0, color=(0, 0, 255)):
        self.pos2D = pygame.Vector2(x, y)
        self.vel2D = pygame.Vector2(0, 0)
        self.acc2D = pygame.Vector2(0, 0)
        
        self.max_velocity = max_velocity
        self.max_acceleration = max_acceleration
        self.color = color
        self.radius = radius
        self.mass = radius * radius

        # Record the total number of frames passed and the history position for trajectory visualization.
        self.total_frame_passed = 0 
        self.history_position = deque(maxlen=50)

    def get_velocity(self):
        return pygame.Vector2(self.vel2D).length()
    
    def get_acceleration(self):
        return pygame.Vector2(self.acc2D).length()
    
    def set_position(self, pos2D):
        self.pos2D = pygame.Vector2(pos2D)

    def set_velocity(self, vel_vec):
        self.vel2D = pygame.Vector2(vel_vec)

        # Limit maximum speed
        if self.vel2D.length() > self.max_velocity:
            self.vel2D.scale_to_length(self.max_velocity)

    def set_acceleration(self, acc_vec):
        next_acc2D = pygame.Vector2(acc_vec)

        # Limit maximum acceleration
        if next_acc2D.length() > self.max_acceleration:
            next_acc2D.scale_to_length(self.max_acceleration)
        
        # Vector Linear Interpolation
        self.acc2D = self.acc2D * 0.5 + next_acc2D * 0.5

    # --- 角度計算 ---
    def get_vel_orientation_deg(self):
        # Pygame's angle is 0 degrees pointing to the right (1, 0)
        # Returns to a value between -180 and 180.
        if self.vel2D.length() == 0: 
            return 0
        
        # Vector2.as_polar() returns (length, angle).
        return self.vel2D.as_polar()[1]
    
    def get_acc_orientation_deg(self):
        if self.acc2D.length() == 0: 
            return 0
        
        return self.acc2D.as_polar()[1]

    def Update(self, delta_time):
        old_vel = pygame.Vector2(self.vel2D)

        # Update speed: v = v0 + a * dt
        new_vel = self.vel2D + self.acc2D * delta_time
        self.set_velocity(new_vel)

        # Update position: p = p0 + (v0 + v1)/2 * dt
        self.pos2D += (old_vel + self.vel2D) * 0.5 * delta_time

        # Record trajectory
        self.total_frame_passed += 1
        if self.total_frame_passed % 10 == 0:
            self.history_position.append(pygame.Vector2(self.pos2D))
    
class AgentController():
    def __init__(self, num_of_agent = 1):
        self.num_of_agent = num_of_agent

        # Main Agent will seek to the target
        self.MainAgent = [Agent_2D(0, 0) for i in range(num_of_agent)]

        # Approaching the search for attendant agent, but not too close.
        # It will predict the agent's future location and move closer or further away from it.
        self.AttendantAgent = [Agent_2D(100, 0, color = (255, 0, 255), radius=20) for i in range(1)]

        # Acceleration scale.
        self.acc_scale = 2

        # Record the total number of collisions between main agent and attendant agent.
        self.total_agent_collision_count = 0

    def AgentMovement(self, target, Swamp_list, 
                      ObstacleC : "Obstacle", isMakeObstacle = True, isObstacleDetection = True,
                      isAttendantAgent = True):
        """
        Adjusting Agent's Steering.
        Calculate the acceleration of agents according to the target, swamp, and obstacles, and set the acceleration to agents. \n
        """

        # Collision interaction between main agent and attendant agent
        # Warning: Now only describes the collision interaction between a single main agent and a single attendant agent.
        if isAttendantAgent:
            self.AgentCollision(self.MainAgent[0], self.AttendantAgent[0])

        # --- Main agent part ---
        for agent in self.MainAgent:
            velocity = agent.get_velocity()

            # Calculate three steering forces: flee from swamp, seek to target, and avoid obstacle.
            flee_steer_acc, seek_steer_acc, obs_steer_acc = pygame.Vector2(0,0), pygame.Vector2(0,0), pygame.Vector2(0,0)

            # 1. Flee swamp
            # Find the closest swamp, and flee from it. The closer to the swamp, the stronger the flee force.
            # (Special Design) 
            # When the target is generated too close to a swamp, the agent may be unable to reach it.
            # To avoid this issue, the system is designed such that when the agent's speed decreases, the swamp detection range is also reduced.
            # This allows the agent to approach the swamp more slowly and eventually reach the target.
            min_dis = float('inf')
            for p in Swamp_list:
                relative_distance = agent.pos2D - p
                dis = relative_distance.length()
                # The lower the speed, the shorter the detection range.
                if min(min_dis, velocity * 0.5) > dis:
                    min_dis = dis
                    flee_steer_acc = ((agent.max_velocity * 0.3) * relative_distance / dis - agent.vel2D)

            # 2. Seek target
            # If the agent is too close to the swamp, it will stop seeking the target.
            # And limit the maximum seek acceleration when the agent is far from the target.
            if min_dis > 100:
                relative_distance = target - agent.pos2D
                seek_steer_acc = (relative_distance - agent.vel2D)
                if seek_steer_acc.length() > agent.max_acceleration:
                    seek_steer_acc = agent.max_acceleration * seek_steer_acc / seek_steer_acc.length()

            # 3. obstacle avoid. Use whisker to detect obstacle and avoid it.
            obs_steer_list = [pygame.Vector2(0, 0), pygame.Vector2(0, 0), pygame.Vector2(0, 0)]
            record_tangent = [pygame.Vector2(0, 0), pygame.Vector2(0, 0)]
            normal_thrust = pygame.Vector2(0, 0)
            if isObstacleDetection and isMakeObstacle:
                isC_list, hitInfo_list_list = ObstacleC.RayWithWhiskers(agent)
                # Main ray steering control. (It also utilizes flee's special design)
                if isC_list[0]:
                    # The lower the speed, the shorter the detection range.
                    if 0 < hitInfo_list_list[0].t and hitInfo_list_list[0].t < 0.5:
                        obs_steer_list[0] = (200 - hitInfo_list_list[0].hitDistance) * 2 * hitInfo_list_list[0].hitNormal - agent.vel2D


                # Two whiskers steering control.
                for i in range(1, 3):
                    # The lower the speed, the shorter the detection range.
                    if isC_list[i] == True:
                        slide_velocity = pygame.Vector2(0, 0)
                        hitNormal = hitInfo_list_list[i].hitNormal
                        if hitInfo_list_list[i].hitDistance < min(200, velocity):
                            # Obtain the tangent direction of the obstacle.
                            tangent = pygame.Vector2(hitNormal.y, -hitNormal.x)

                            # Calculate the angle between the ray and the tangent of the obstacle. 
                            # If the angle is too small, it means that the ray is almost parallel to the obstacle. 
                            # In this case, we will ignore the steering force of this ray to avoid oscillations.
                            ray_angle = abs((hitInfo_list_list[i].ray_end - hitInfo_list_list[i].ray_start).angle_to(tangent)) % 180
                            if ray_angle > 90:
                                ray_angle = 180 - ray_angle
                            if ray_angle < 40: 
                                continue


                            # current velocity direction
                            current_velocity_dir = (agent.vel2D).normalize()

                            # Make the tangent direction and the velocity direction go in the same direction.
                            if current_velocity_dir.dot(tangent) < 0:
                                tangent = -tangent

                            # Set the desired speed to "along the tangent".
                            slide_velocity += tangent * agent.max_velocity * 0.8

                            # Add normal thrust, to avoid the agent getting too close to the obstacle.
                            # The closer to the obstacle, the greater the thrust.
                            if hitInfo_list_list[i].hitDistance < 100:
                                normal_thrust += hitNormal * (100 - hitInfo_list_list[i].hitDistance) * 1.6
                                
                            steer_force = slide_velocity - agent.vel2D
                            obs_steer_list[i] = steer_force


                # If the front ray detects an obstacle, it will steer according to the front ray.
                obs_steer_acc += obs_steer_list[0]

                # Add normal thrust, to avoid the agent getting too close to the obstacle.
                obs_steer_acc += normal_thrust

                # If the front ray detect an obstacle.
                
                if isC_list[0] == True:
                    # If both whiskers detect an obstacle, the agent will steer according to the closer one.
                    if isC_list[1] == isC_list[2] == True:
                        if hitInfo_list_list[1].hitDistance < hitInfo_list_list[2].hitDistance:
                            obs_steer_acc += obs_steer_list[1]
                        else:
                            obs_steer_acc += obs_steer_list[2]

                    # If only one of the whiskers detects an obstacle.
                    elif isC_list[1] == True:
                        # If the two hit points are close and have the same normal, it means that the front ray and the whisker are detecting the same obstacle edge.
                        # So the agent will steer according to the front ray to avoid oscillation. Otherwise, it will steer according to the whisker.
                        if (hitInfo_list_list[0].hitDistance < hitInfo_list_list[1].hitDistance and 
                            hitInfo_list_list[0].hitNormal == hitInfo_list_list[1].hitNormal and obs_steer_list[1].length() != 0):

                            obs_steer_acc += (hitInfo_list_list[0].hitPoint - hitInfo_list_list[1].hitPoint).normalize() * agent.max_velocity
                        else:
                            obs_steer_acc += obs_steer_list[1]
                    elif isC_list[2] == True:
                        if (hitInfo_list_list[0].hitDistance < hitInfo_list_list[2].hitDistance and 
                            hitInfo_list_list[0].hitNormal == hitInfo_list_list[2].hitNormal and obs_steer_list[2].length() != 0):
                            obs_steer_acc += (hitInfo_list_list[0].hitPoint - hitInfo_list_list[2].hitPoint).normalize() * agent.max_velocity
                        else:
                            obs_steer_acc += obs_steer_list[2]

                else:
                    # If the front ray does not detect an obstacle, but the whisker detects an obstacle, it means that the obstacle is beside the agent. 
                    # In this case, the agent will steer according to the whisker to avoid getting too close to the obstacle.
                    obs_steer_acc += obs_steer_list[1] + obs_steer_list[2]


            # If the agent is about to collide with a wall, set seek_steer_acc and flee_steer_acc to 0.
            if obs_steer_acc.length() > 100:
                seek_steer_acc = pygame.Vector2(0, 0)
                flee_steer_acc = pygame.Vector2(0, 0)

            steer = (flee_steer_acc + seek_steer_acc + obs_steer_acc * 3) * self.acc_scale
            agent.set_acceleration(steer)


        # --- Attendant agent part ---
        for agent in self.AttendantAgent:
            steer_acc = pygame.Vector2(0, 0)

            # Find the closest main agent
            closest_main_agent = -1
            closest_distance = 100000
            agent_position = agent.pos2D
            for i, main_agent in enumerate(self.MainAgent):
                distance = (main_agent.pos2D - agent_position).length()
                if closest_distance > distance:
                    closest_distance = distance
                    closest_main_agent = i

            # Predict the future position of the main agent and adjust the acceleration of the attendant agent accordingly.
            if closest_main_agent != -1:
                main_agent = self.MainAgent[closest_main_agent]

                # position in the next 0.1 second 
                main_future_position = main_agent.pos2D + main_agent.vel2D * 0.1
                distance = (main_future_position - agent_position).length()
                # If the agent is too close to the main agent, it will flee from the main agent. Otherwise, it will seek to the main agent.
                if distance < 150:
                    relative_distance = agent_position - main_future_position
                    steer_acc = ((agent.max_velocity / 2) * relative_distance / distance - agent.vel2D)
                else:
                    relative_distance = main_future_position - agent_position
                    steer_acc = (relative_distance - agent.vel2D)

                steer = (steer_acc) * self.acc_scale
                agent.set_acceleration(steer)

    def AgentCollision(self, agent_1 : Agent_2D, agent_2 : Agent_2D):
        """
        Collision interaction between main agent and attendant agent \n
        Warning: Now only describes the collision interaction between a single main agent and a single attendant agent.
        """
        relative_pos = agent_2.pos2D - agent_1.pos2D
        distance = relative_pos.length()
        min_distance = agent_1.radius + agent_2.radius

        # Check if a collision has occurred
        if distance < min_distance:
            normal = relative_pos.normalize()

            # --- Position
            # To prevent two agents from getting stuck together, push them apart.
            overlap = min_distance - distance
            agent_1.pos2D -= normal * (overlap * 0.5)
            agent_2.pos2D += normal * (overlap * 0.5)

            # --- Speed
            relative_velocity = agent_2.vel2D - agent_1.vel2D
            
            # Calculate normal velocity
            velocity_along_normal = relative_velocity.dot(normal)

            # Simple elastic collision formula
            impulse_magnitude = -(2 * velocity_along_normal) / (agent_1.mass + agent_2.mass)
            
            # Update speed
            impulse = impulse_magnitude * normal
            agent_1.vel2D -= impulse * agent_2.mass
            agent_2.vel2D += impulse * agent_1.mass

            self.total_agent_collision_count += 1
            print(f"Collision occurred! Total collisions: {self.total_agent_collision_count}")

    def FutureAgentsCollisionDebugger(self, agent_1 : Agent_2D, agent_2 : Agent_2D):
        """
        return future collision between two agent ->  (bool, (pygame.vector2, pygame.vector2, float))
        """

        # analyze their relative motion
        relative_pos = agent_2.pos2D - agent_1.pos2D
        relative_vel = agent_2.vel2D - agent_1.vel2D
  
        vel_dot_pos = relative_vel.dot(relative_pos)

        # If vel_dot_pos >= 0, mean t < 0, no collision will occur.
        if vel_dot_pos >= 0:
            return False, None
        
        # Find a time t such that the distance between two points is r_1 + r_2.
        # in future t, |P+Vt| <= (r_1 + r_2)
        # -> |P|^2  +  2 * (P · V) * t  +  |V|^2 * t^2 <= (r_1 + r_2)^2
        # -> (|V|^2)t^2 + (2*(P · V))t - (|P|^2 - (r_1 + r_2)) <= 0
        # -> at^2 + bt + c <= 0
        a = relative_vel.length_squared()
        b = 2 * vel_dot_pos
        c = relative_pos.length_squared() - ((agent_1.radius + agent_2.radius)**2)

        # Avoid dividing by zero
        if a < 0.0001:
            return False, None
        
        # Judgment discriminant, If the discriminant < 0, it means that the path will never encounter a collision.
        discriminant = b**2 - 4 * a * c
        if discriminant < 0:
            return False, None
        else:
            t = (-b - math.sqrt(discriminant)) / (2 * a)

            if t > 0 and t < 1:
                agent_1_c_pos = agent_1.pos2D + agent_1.vel2D * t
                agent_2_c_pos = agent_2.pos2D + agent_2.vel2D * t
                return True, (agent_1_c_pos, agent_2_c_pos, t)
            else:
                return False, None

    def Update(self, delta_time):
        """
        Updata agents position
        """
        for agent in self.MainAgent:
            agent.Update(delta_time)
        for agent in self.AttendantAgent:
            agent.Update(delta_time)

    def ObstacleCollision(self, ObstacleC : "Obstacle", isMakeObstacle = True):
        """
        Handle Collision
        """
        if isMakeObstacle:
            for agent in self.MainAgent:
                ObstacleC.HandleCollision(agent)
            for agent in self.AttendantAgent:
                ObstacleC.HandleCollision(agent)