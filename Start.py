

import sys
import PyQt5.QtWidgets as QtWidgets

from MainCore import Game

class Q1(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)

        layout = QtWidgets.QVBoxLayout(self)


        # === Environment settings ===
        IoadImageBox = QtWidgets.QGroupBox("Environment settings")
        layout.addWidget(IoadImageBox)

        inner_layout = QtWidgets.QVBoxLayout()
        IoadImageBox.setLayout(inner_layout)


        # === Checkboxes ===
        self.KeyBoardControl = QtWidgets.QCheckBox("Is KeyBoard Control")
        self.KeyBoardControl.setChecked(False)
        inner_layout.addWidget(self.KeyBoardControl)

        self.MakeObstacle = QtWidgets.QCheckBox("Add Obstacles")
        self.MakeObstacle.setChecked(True)
        inner_layout.addWidget(self.MakeObstacle)

        self.AgentObstacleDetection = QtWidgets.QCheckBox("Agent obstacle detection")
        self.AgentObstacleDetection.setChecked(True)
        inner_layout.addWidget(self.AgentObstacleDetection)

        self.AddAttendantAgent = QtWidgets.QCheckBox("Add Pursue and Evade Agent")
        self.AddAttendantAgent.setChecked(True)
        inner_layout.addWidget(self.AddAttendantAgent)


        # === Start Game ===
        self.exec_button = QtWidgets.QPushButton("Start Game")
        self.exec_button.clicked.connect(self.run_selected)
        layout.addWidget(self.exec_button)


    def run_selected(self):
        game = Game(KeyBoardControl = self.KeyBoardControl.isChecked(),
                    MakeObstacle = self.MakeObstacle.isChecked(),
                    AgentObstacleDetection = self.AgentObstacleDetection.isChecked(),
                    AddAttendantAgent = self.AddAttendantAgent.isChecked()
                    )
        game.Start()

class MyGame(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game")
        self.setGeometry(100, 100, 300, 200)

        self.q1_widget = Q1()
        self.setCentralWidget(self.q1_widget)


app = QtWidgets.QApplication(sys.argv)
window = MyGame()
window.show()
sys.exit(app.exec_())