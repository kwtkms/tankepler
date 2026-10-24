from gpiozero import Motor

class RobotMotors:
    def __init__(self, default_speed: float = 0.7):
        # L298N : PWM doit être sur ENA/ENB (enable)
        # Donc on passe enable=..., et gpiozero gère le PWM sur enable quand pwm=True
        self.left = Motor(forward=23, backward=24, enable=18, pwm=True)   # ENA = 18
        self.right = Motor(forward=27, backward=22, enable=13, pwm=True)  # ENB = 13

        self.speed = 0.0
        self.set_speed(default_speed)
        self.stop()

    def set_speed(self, s: float):
        # clamp 0..1
        if s is None:
            return
        s = float(s)
        if s < 0.0:
            s = 0.0
        elif s > 1.0:
            s = 1.0
        self.speed = s

    def forward(self):
        self.left.forward(self.speed)
        self.right.forward(self.speed)

    def backward(self):
        self.left.backward(self.speed)
        self.right.backward(self.speed)

    def left_turn(self):
        # tourne sur place : gauche recule, droite avance
        self.left.backward(self.speed)
        self.right.forward(self.speed)

    def right_turn(self):
        self.left.forward(self.speed)
        self.right.backward(self.speed)

    def stop(self):
        self.left.stop()
        self.right.stop()
