import pygame
import sys
import numpy as np
np.random.seed(42)


import GameFunction as GF
from AgentScript import Agent_2D, AgentController
from ObstacleScript import Obstacle

# https://www.famous1993.com.tw/tech/tech1016.html


class Game():
    def __init__(self, 
                 KeyBoardControl = False, 
                 MakeObstacle = True, 
                 AgentObstacleDetection = True, 
                 AddAttendantAgent = True):
        
        # Control variables for game settings
        # If True, the target position can be controlled by arrow keys, and the camera will follow the target. If False, the camera will follow the Main Agent.
        self.KeyBoardControl = KeyBoardControl 
        # If True, obstacles will be added into the game.
        self.MakeObstacle = MakeObstacle
        # If True, the agent will detect the obstacle and try to avoid it. If False, the agent will ignore the obstacle and may collide with it.
        self.AgentObstacleDetection = AgentObstacleDetection
        # If True, an Attendant Agent will be added into the game, which will pursue the Main Agent and Evade if too close to it. 
        self.AddAttendantAgent = AddAttendantAgent

        # Initialize pygame (must be called before using any pygame functions)
        pygame.init()

        # Set the window title
        pygame.display.set_caption("Game")

        self.screen_width = 1200
        self.screen_height = 700

        # Create the game window 
        self.screen = pygame.display.set_mode((self.screen_width, self.screen_height))
        self.screen_center = pygame.Vector2(self.screen_width//2, self.screen_height//2)

        # Create a clock object to control the frame rate
        self.clock = pygame.time.Clock()

        # Create a font object for rendering text
        self.font = pygame.font.SysFont(["consolas", "monaco", "monospace"], 24)
        self.HUD_font = pygame.font.SysFont(["consolas", "monaco", "monospace"], 16)

        # Add agents into this game
        self.AgentController = AgentController(num_of_agent = 1)

        # If self.MakeObstacle is True, add 4 obstacles into this game.
        self.ObstacleController = Obstacle()

        # Init camera position.
        self.camera_position = pygame.Vector2(0,0)
        
        # Background grid image.
        self.background = pygame.image.load("./Img/grid_1000x1000.png").convert_alpha()   # size: 1000 x 1000

        # Time per frame.
        self.delta_time = 1/60

        # Record number of frames passed since of start the game.
        self.total_frame_passed = 0

        # Record total score. (Torching the target will add 1 score)
        # If score reaches 100, the game will end.
        self.total_score = 0
        self.now_time = self.total_score * self.delta_time
        self.record_reached_target_time_list = [self.now_time]

        # Agent will seek this position.
        self.Set_target()

        # Swamp, which will make the Main Agent flee from it.
        # The position of Swamp will be added when the Main Agent torches the target.
        self.Swamp_list = []
        
    def Set_target(self):
        '''
        Set the target as the goal of the Main Agent, and the target will be reset when the Main Agent torches it.
        '''

        # Don't spawn inside obstacles.
        # Use a while loop to test if it meets the requirements.
        while 1:
            target = np.random.randn(2) * 500
            target = pygame.Vector2(target[0], target[1])

            isOk = True
            for obstacle in self.ObstacleController.Obstacle_list:
                if (target - obstacle.location).length() < 350:
                    isOk = False
            if isOk == True:
                break

        self.target_position = pygame.Vector2(target[0], target[1])

    def Add_Swamp(self):
        '''
        Add the Swamp to make the Main Agent flee from it
        '''

        rd_position = np.random.randn(2) * 500
        flee_target = pygame.Vector2(rd_position[0], rd_position[1])
        self.Swamp_list.append(flee_target)
        
    def Start(self):
        """
        Start the game. \n
        Press Z to Off/On keyboard control. \n 
        Press X to Add/Remove obstacles. \n 
        Press C to Off/On obstacle detection. \n 
        Press V to Add/Remove Attendant Agent.
        """
        # Control variable for the main loop
        running = True

        while running:    
            # Handle events (e.g., window close)
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

                # Keys for toggling features
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_z:
                        self.KeyBoardControl = not self.KeyBoardControl
                    if event.key == pygame.K_x:
                        self.MakeObstacle = not self.MakeObstacle
                    if event.key == pygame.K_c:                    
                        self.AgentObstacleDetection = not self.AgentObstacleDetection
                    if event.key == pygame.K_v:                    
                        self.AddAttendantAgent = not self.AddAttendantAgent

            # --- 1. Draw background, colliders, target, swamp and agents. ---
            # Draw the background.
            self.DrawBackground()

            # Draw the obstacle
            self.DrawObstacle()

            # Draw the Target and Swamps
            self.DrawTargetAndSwamp()

            # Draw a circle at the Agent's position
            self.DrawAgent()


            # --- 2. Handles the agent movement, and collision detection. ---
            # Update the agent movement, and collision detection
            self.AgentController.AgentMovement(target = self.target_position, 
                                               Swamp_list = self.Swamp_list, 
                                               ObstacleC = self.ObstacleController,
                                               isMakeObstacle = self.MakeObstacle,
                                               isObstacleDetection = self.AgentObstacleDetection,
                                               isAttendantAgent = self.AddAttendantAgent)
            self.AgentController.Update(self.delta_time)
            self.AgentController.ObstacleCollision(self.ObstacleController,
                                                   isMakeObstacle = self.MakeObstacle)


            # --- 3. Draw debug items. (collision, direction, velocity arrow, acceleration arrow) ---
            # Visual multi-agent collision debugging
            if self.AddAttendantAgent:
                self.MultiAgentCollisionDebugging(self.AgentController.MainAgent[0], self.AgentController.AttendantAgent[0])

            # Draw the Agent's state. (direction and trajectory) 
            self.AgentStateDraw(self.AgentController.MainAgent)

            # If Main Agent torches the target, the target's position will be reset.
            self.CheckTarget(self.AgentController.MainAgent)

            # Debugging the agent's obstacle detection with rays and whiskers.
            if self.MakeObstacle == True:
                self.DrawDebugRayWithWhiskers()

            # --- 4. Handles keyboard input and HUD. ---
            # Keyboard Detection to target movement and set camera position.
            self.KeyBoardDetectionAndSetCamera()

            # Draw the HUD(Head-Up Display about agent's position, velocity and acceleration)
            self.DrawHUD(self.AgentController.MainAgent[0])

            # Update the display (render everything to the screen)
            pygame.display.flip()

            # Limit the frame rate to 60 FPS
            self.total_frame_passed += 1
            self.clock.tick(60)
            self.now_time = self.total_frame_passed * self.delta_time

        # Clean up and exit
        pygame.quit()
        sys.exit()

    def DrawBackground(self):
        """
        fill the screen
        """
        self.screen.fill((0, 255, 255))
            
        LD = self.camera_position - self.screen_center
        LeftDown = np.floor(LD / 1000).astype(np.int32)
        RightUp = np.floor((LD + np.array([self.screen_width, self.screen_height])) / 1000).astype(np.int32)
        grid_points = [pygame.Vector2(x, y) for x in range(LeftDown[0], RightUp[0]+1) for y in range(LeftDown[1], RightUp[1]+1)]

        for i in range(len(grid_points)):
            self.screen.blit(self.background, GF.to_screen(1000 * grid_points[i] + self.screen_center - self.camera_position, self.screen_height) - pygame.Vector2(0, 1000))

    def DrawObstacle(self):
        """
        Draw the Obstacle in the screen
        """
        if self.MakeObstacle:
            for obstacle in self.ObstacleController.Obstacle_list:
                points_in_screen = [GF.to_screen(obstacle.points[i] + self.screen_center - self.camera_position, self.screen_height) for i in range(len(obstacle.points))]
                pygame.draw.polygon(self.screen, obstacle.color, points_in_screen)
        
    def DrawTargetAndSwamp(self):
        """
        Draw target and swamp.
        """
        # Draw a circle at the Swamp position
        for p in self.Swamp_list:
            pygame.draw.circle(self.screen, (0, 128, 128), GF.to_screen(p + self.screen_center - self.camera_position, self.screen_height), 10)

        # Draw a circle at the target position
        pygame.draw.circle(self.screen, (128, 128, 0), GF.to_screen(self.target_position + self.screen_center - self.camera_position, self.screen_height), 10)
        pygame.draw.line(self.screen, (128, 128, 128), 
                            GF.to_screen(self.target_position + self.screen_center - self.camera_position, self.screen_height),
                            GF.to_screen(self.AgentController.MainAgent[0].pos2D + self.screen_center - self.camera_position, self.screen_height),)

    def DrawAgent(self):
        """
        Draw agents
        """
        if self.AddAttendantAgent:
            for agent in self.AgentController.AttendantAgent:
                pygame.draw.circle(self.screen, agent.color, GF.to_screen(agent.pos2D + self.screen_center - self.camera_position, self.screen_height), agent.radius)
            
        for agent in self.AgentController.MainAgent:
            pygame.draw.circle(self.screen, agent.color, GF.to_screen(agent.pos2D + self.screen_center - self.camera_position, self.screen_height), agent.radius)

    def MultiAgentCollisionDebugging(self, agent_1 : Agent_2D, agent_2 : Agent_2D):
        """
        Debugging whether a collision will occur in the future
        """
        isCollision, collision_info = self.AgentController.FutureAgentsCollisionDebugger(agent_1, agent_2)
        if isCollision == True:
            agent_1_c_pos, agent_2_c_pos, t = collision_info[0], collision_info[1], collision_info[2]
            pygame.draw.line(self.screen, (0,0,0), 
                                GF.to_screen(agent_1.pos2D + self.screen_center - self.camera_position, self.screen_height),
                                GF.to_screen(agent_1_c_pos + self.screen_center - self.camera_position, self.screen_height))
            pygame.draw.circle(self.screen, agent_1.color, GF.to_screen(agent_1_c_pos + self.screen_center - self.camera_position, self.screen_height), agent_1.radius,
                                width=2)
            pygame.draw.line(self.screen, (0,0,0),
                                GF.to_screen(agent_2.pos2D + self.screen_center - self.camera_position, self.screen_height),
                                GF.to_screen(agent_2_c_pos + self.screen_center - self.camera_position, self.screen_height))
            pygame.draw.circle(self.screen, agent_2.color, GF.to_screen(agent_2_c_pos + self.screen_center - self.camera_position, self.screen_height), agent_2.radius,
                                width=2)
        else:
            pygame.draw.line(self.screen, (0,0,0), 
                                GF.to_screen(agent_1.pos2D + self.screen_center - self.camera_position, self.screen_height),
                                GF.to_screen(agent_1.pos2D + agent_1.vel2D.normalize() * 3000 + self.screen_center - self.camera_position, self.screen_height))
            pygame.draw.line(self.screen, (0,0,0), 
                                GF.to_screen(agent_2.pos2D + self.screen_center - self.camera_position, self.screen_height),
                                GF.to_screen(agent_2.pos2D + agent_2.vel2D.normalize() * 3000+ self.screen_center - self.camera_position, self.screen_height))
    
    def AgentStateDraw(self, agent_list : list[Agent_2D]):
        """
        Draw arrow about agent's velocity and acceleration, and trajectory of agent
        """
        for agent in agent_list:
            screen_pos = agent.pos2D + self.screen_center - self.camera_position

            # acceleration arrow
            arrow_start = GF.to_screen(screen_pos, self.screen_height)
            arrow_end = GF.to_screen(screen_pos + 200 * agent.acc2D / 1000, self.screen_height)
            GF.draw_arrow(self.screen, start=arrow_start, end=arrow_end, color=(0, 0, 255))
            
            # velocity arrow
            arrow_start = GF.to_screen(screen_pos, self.screen_height)
            arrow_end = GF.to_screen(screen_pos + 200 * agent.vel2D / 1000, self.screen_height)
            GF.draw_arrow(self.screen, start=arrow_start, end=arrow_end, color=(255, 0, 0))

            # agent trajectory
            # Draw afterimages (dots)
            for i, p in enumerate(agent.history_position):
                # dot radius
                radius = int((i + 1) / len(agent.history_position) * 5) # Older dot more smaller
                
                # dot position
                draw_position = GF.to_screen(p + self.screen_center - self.camera_position, self.screen_height) - pygame.Vector2(radius, radius)

                # draw dot
                temp_s = pygame.Surface((radius*2, radius*2), pygame.SRCALPHA)
                pygame.draw.circle(temp_s, agent.color, (radius, radius), radius)
                self.screen.blit(temp_s, draw_position)
    
    def CheckTarget(self, agent_list):
        """
        Draw targets
        """
        for agent in agent_list:
            if np.linalg.norm(self.target_position - agent.pos2D) < 20:
                self.total_score += 1
                self.record_reached_target_time_list.append(self.now_time)
                if self.total_score >= 100:
                    print("Time Passed:", self.now_time)

                    import matplotlib.pyplot as plt
                    t_list = np.array(self.record_reached_target_time_list)
                    delta_t_list = t_list[1:] - t_list[:-1]
                    plt.figure(figsize=(10, 5))
                    plt.plot(list(range(1, len(delta_t_list) + 1)), delta_t_list, marker='o')
                    plt.xlabel("Number of reached targets")
                    plt.ylabel("Time (s)")

                    plt.title("Time interval required to reach the target")
                    plt.show()

                    pygame.quit()
                    sys.exit()
                self.Set_target()
                self.Add_Swamp()

    def DrawDebugRayWithWhiskers(self):
        isC_list, hitInfo_list_list = self.ObstacleController.RayWithWhiskers(self.AgentController.MainAgent[0], 
                                                                            screen = self.screen, 
                                                                            center = self.screen_center-self.camera_position, 
                                                                            w = self.screen_height)
        for i, isC in enumerate(isC_list):
            if isC == True:
                pygame.draw.circle(self.screen, self.AgentController.MainAgent[0].color, 
                                GF.to_screen(hitInfo_list_list[i].hitPoint+self.screen_center-self.camera_position,self.screen_height), radius=10, width=2)
    
    def KeyBoardDetectionAndSetCamera(self):
        """
        If self.KeyBoardControl is True, the target position can be controlled by arrow keys, and the camera will follow the target. \n
        If self.KeyBoardControl is False, the camera will follow the Main Agent.
        """
        # Get current keyboard state (continuous input)
        keys = pygame.key.get_pressed()

        if self.KeyBoardControl:
            # Update position based on arrow key input
            speed = 400
            direction = pygame.Vector2(0, 0)
            if keys[pygame.K_LEFT]:
                direction.x -= 1
            if keys[pygame.K_RIGHT]:
                direction.x += 1
            if keys[pygame.K_UP]:
                direction.y += 1
            if keys[pygame.K_DOWN]:
                direction.y -= 1
            if direction.length_squared() != 0:
                self.target_position += direction.normalize() * speed * self.delta_time
            # Set the camera position to follow the target
            self.camera_position = self.target_position
        else:
            # Set the camera position to follow the Main Agent
            self.camera_position = self.AgentController.MainAgent[0].pos2D

    def DrawHUD(self, agent):
        """
        Draw the HUD(Head-Up Display) about main agent's velocity and acceleration
        """
        vel = agent.get_velocity()
        acc = agent.get_acceleration()
        texts = [
                f"Vel: {' ' * (5-len(str(vel)))} {int(vel)} px/s",
                f"Acc: {' ' * (5-len(str(acc)))} {int(acc)} px/s^2",
                f"Pos: ({int(agent.pos2D.x)}, {int(agent.pos2D.y)})",
                f"Score: {self.total_score}",
                f"Time: {self.now_time:.2f} s"
                ]
        
        max_HUD_len = 0
        for it in texts:
            max_HUD_len = max_HUD_len if max_HUD_len > len(it) else len(it)

        overlay = pygame.Surface((10*max_HUD_len, 130), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        self.screen.blit(overlay, (10, 10))

        for i, it in enumerate(texts):
            text_surf = self.HUD_font.render(it, True, (255, 255, 255))
            self.screen.blit(text_surf, (20, 18 + i * 25))


if __name__ == '__main__':
    game = Game()
    game.Start()