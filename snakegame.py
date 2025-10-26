import pygame
import cv2
import numpy as np
import threading
import random
import sys
class HandTracker(threading.Thread):
    def __init__(self):
        super().__init__()
        self.cap = cv2.VideoCapture(0)

        # Set HD resolution
        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 1280)
        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 720)
        self.direction = "RIGHT"
        self.display_direction = "RIGHT"
        self.running = True
        self.overlay_color = (0, 180, 255)
        self.text_color = (255, 255, 255)

    def run(self):
        cv2.namedWindow("🎮 Hand Control (Press Q to quit)", cv2.WINDOW_NORMAL)
        cv2.resizeWindow("🎮 Hand Control (Press Q to quit)", 1280, 720)

        while self.running:
            ret, frame = self.cap.read()
            if not ret:
                break

            frame = cv2.flip(frame, 1)
            hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
            lower = np.array([0, 30, 60])
            upper = np.array([20, 150, 255])
            mask = cv2.inRange(hsv, lower, upper)
            mask = cv2.medianBlur(mask, 15)

            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                c = max(contours, key=cv2.contourArea)
                x, y, w, h = cv2.boundingRect(c)
                cx = x + w // 2
                cy = y + h // 2

                # bounding box around hand
                cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 100), 3)

                height, width, _ = frame.shape
                dx = cx - width // 2
                dy = cy - height // 2
                threshold = 80

                # Direction detection
                if abs(dx) > abs(dy):
                    if dx < -threshold:
                        self.direction = "LEFT"
                    elif dx > threshold:
                        self.direction = "RIGHT"
                else:
                    if dy < -threshold:
                        self.direction = "UP"
                    elif dy > threshold:
                        self.direction = "DOWN"

                self.display_direction = self.direction

                #helper lines
                cv2.line(frame, (width // 2, 0), (width // 2, height), (150, 150, 255), 1)
                cv2.line(frame, (0, height // 2), (width, height // 2), (150, 150, 255), 1)

                #Direction preview overlay
                cv2.putText(frame, f"Move: {self.display_direction}",
                            (40, 60), cv2.FONT_HERSHEY_DUPLEX, 1.5, self.text_color, 3)

                # Overlay arrows
                if self.display_direction == "LEFT":
                    cv2.putText(frame, "← Move Left", (60, height // 2),
                                cv2.FONT_HERSHEY_DUPLEX, 2, self.overlay_color, 3)
                elif self.display_direction == "RIGHT":
                    cv2.putText(frame, "Move Right →", (width - 400, height // 2),
                                cv2.FONT_HERSHEY_DUPLEX, 2, self.overlay_color, 3)
                elif self.display_direction == "UP":
                    cv2.putText(frame, "↑ Move Up", (width // 2 - 150, 100),
                                cv2.FONT_HERSHEY_DUPLEX, 2, self.overlay_color, 3)
                elif self.display_direction == "DOWN":
                    cv2.putText(frame, "↓ Move Down", (width // 2 - 180, height - 80),
                                cv2.FONT_HERSHEY_DUPLEX, 2, self.overlay_color, 3)

            # Show the full frame
            cv2.imshow(" Hand Control (Press Q to quit)", frame)

            # Quit camera window manually
            if cv2.waitKey(1) & 0xFF == ord('q'):
                self.stop()
                break

        self.cap.release()
        cv2.destroyAllWindows()

    def stop(self):
        self.running = False





class SnakeGame:
    def __init__(self, tracker):
        pygame.init()
        self.WIDTH, self.HEIGHT = 800, 600
        self.CELL = 20
        self.screen = pygame.display.set_mode((self.WIDTH, self.HEIGHT))
        pygame.display.set_caption("🐍 AI Hand-Controlled Snake by Lydia")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("Segoe UI", 28, bold=True)
        self.tracker = tracker
        self.SNAKE_COLOR = (50, 255, 100)
        self.FOOD_COLOR = (255, 80, 80)
        self.TEXT_COLOR = (255, 255, 255)

    def draw_gradient_background(self):
        top_color = np.array([40, 60, 180])
        bottom_color = np.array([20, 20, 70])
        for y in range(self.HEIGHT):
            color = top_color + (bottom_color - top_color) * (y / self.HEIGHT)
            pygame.draw.line(self.screen, color, (0, y), (self.WIDTH, y))

    def random_food(self):
        return [
            random.randrange(0, self.WIDTH - self.CELL, self.CELL),
            random.randrange(0, self.HEIGHT - self.CELL, self.CELL)
        ]

    def draw_snake(self, body):
        for i, segment in enumerate(body):
            shade = max(0, 255 - i * 5)
            color = (self.SNAKE_COLOR[0], shade, self.SNAKE_COLOR[2])
            pygame.draw.rect(self.screen, color, (*segment, self.CELL, self.CELL), border_radius=5)

    def show_text(self, text, x, y, color=None, size=None):
        font = self.font if not size else pygame.font.SysFont("Segoe UI", size, bold=True)
        label = font.render(text, True, color or self.TEXT_COLOR)
        self.screen.blit(label, (x, y))

    def game_loop(self):
        snake_pos = [400, 300]
        snake_body = [list(snake_pos)]
        direction = "RIGHT"
        food_pos = self.random_food()
        score = 0
        running = True

        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.tracker.stop()
                    pygame.quit()
                    sys.exit()

            #new direction
            new_dir = self.tracker.direction
            opposite = {"UP": "DOWN", "DOWN": "UP", "LEFT": "RIGHT", "RIGHT": "LEFT"}
            if new_dir != opposite.get(direction):
                direction = new_dir

            # Move snake
            if direction == "UP":
                snake_pos[1] -= self.CELL
            elif direction == "DOWN":
                snake_pos[1] += self.CELL
            elif direction == "LEFT":
                snake_pos[0] -= self.CELL
            elif direction == "RIGHT":
                snake_pos[0] += self.CELL

            # Wrap around edges
            if snake_pos[0] < 0:
                snake_pos[0] = self.WIDTH - self.CELL
            elif snake_pos[0] >= self.WIDTH:
                snake_pos[0] = 0
            if snake_pos[1] < 0:
                snake_pos[1] = self.HEIGHT - self.CELL
            elif snake_pos[1] >= self.HEIGHT:
                snake_pos[1] = 0

            snake_body.insert(0, list(snake_pos))

            # Eat food
            if snake_pos == food_pos:
                score += 1
                food_pos = self.random_food()
            else:
                snake_body.pop()

            # Collision with itself
            if snake_pos in snake_body[1:]:
                running = False

            # Draw everything
            self.draw_gradient_background()
            self.draw_snake(snake_body)
            pygame.draw.rect(self.screen, self.FOOD_COLOR,
                             (*food_pos, self.CELL, self.CELL), border_radius=6)

            # Display texts
            self.show_text(f"Score: {score}", 20, 20)
            self.show_text(f"Direction: {direction}", 20, 60, (200, 200, 255))

            pygame.display.update()
            self.clock.tick(10)

        self.game_over_screen()

    def game_over_screen(self):
        self.screen.fill((20, 20, 50))
        self.show_text("GAME OVER", self.WIDTH//2 - 110, self.HEIGHT//2 - 30, (255, 80, 80), size=40)
        self.show_text("Press R to Restart or Q to Quit", self.WIDTH//2 - 200, self.HEIGHT//2 + 20, (200, 200, 200), size=24)
        pygame.display.update()

        waiting = True
        while waiting:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    waiting = False
                    self.tracker.stop()
                    pygame.quit()
                    sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_r:
                        self.game_loop()
                    elif event.key == pygame.K_q:
                        waiting = False
                        self.tracker.stop()
                        pygame.quit()
                        sys.exit()



# Run

if __name__ == "__main__":
    tracker = HandTracker()
    tracker.start()
    game = SnakeGame(tracker)
    game.game_loop()
    tracker.stop()
