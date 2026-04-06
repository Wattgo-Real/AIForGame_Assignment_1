# Assignment 1

![image](https://github.com/Wattgo-Real/AIForGame_Assignment_1/blob/main/Img/GameScreen.png)

## Environment and Dependencies

This game was made using Python 3.11.15.

Dependencies
* numpy = =2.4.3
* matplotlib == 3.10.8
* PyQt5 == 5.15.11
* pygame == 2.6.1

## Installation steps

```
git clone https://Wattgo-Real/AIForGame_Assignment_1
cd AIForGame_Assignment_1
pip install -r requirements.txt
```

## Run Command
If you want to adjust game settings. Run:

```
python Start.py
```

If you just want to open the game directly. Run:

```
python MainCore.py
```

Alternatively, you can launch the game by directly opening the Start.exe file.

## Controls
The game includes the following toggle sitting.

• KeyBoardControl (The initial setting is false. Switch: Key Z)

    If True, the target position can be controlled by arrow keys, and the camera will follow the target. If False, the camera will follow the Main Agent.
• MakeObstacle (The initial setting is true. Switch: Key X)

    If True, obstacles will be added into the game.
• AgentObstacleDetection (The initial setting is true. Switch: Key C)

    If True, the agent will detect the obstacle and try to avoid it. If False, the agent will ignore the obstacle and may collide with it.
• AddAttendantAgent (The initial setting is true. Switch: Key V)

    If True, an Attendant Agent will be added into the game, which will pursue the Main Agent and evade if too close to it. 

## Description of Available Demo Scenarios

1. Seek and Flee Test

    • Use this setting

        KeyBoardControl = True
        MakeObstacle = False
        AgentObstacleDetection = False
        AddAttendantAgent = False

    • The purpose is to test the main agent’s Seek and Flee behavior
2. Pursue and Evade Test

    • Use this setting

        KeyBoardControl = False
        MakeObstacle = False
        AgentObstacleDetection = False
        AddAttendantAgent = True

    • The main purpose is to test the attendant agent’s behavior in
response to the main agent’s pursue and evade actions.
3. Obstacles Test

    • Use this setting

        KeyBoardControl = False
        MakeObstacle = True
        AgentObstacleDetection = True
        AddAttendantAgent = True

    • Collisions exist between obstacles and the agent, and the main agent will actively avoid obstacles. The main purpose is to study how to design the main agent so that it does not get stuck against walls while still approaching the target.

