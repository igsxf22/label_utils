"""
Steps:

Create and fill a mosaic with downsized images and predicted labels
Users will click any labels that need to be corrected

main componets:
BinaryClassDataLoader: loads images and labels, and creates a list of samples

Currently written for 16:9 images, can rewrite for square images uses the create_square_aspect_mosaic

"""
import pygame
from pathlib import Path
import random

pygame.init()
WIDTH = 960
BAR_HEIGHT = 24
HEIGHT = 540 + BAR_HEIGHT 
MAX_FPS = 60
fpsClock = pygame.time.Clock()
screen = pygame.display.set_mode((WIDTH, HEIGHT))

LABEL_FONT = pygame.font.Font(None, 18)
CLOUDS_COLOR = (0, 0, 155)
CLEAR_COLOR = (0, 155, 0)

mosaic = pygame.rect.Rect(0, 0, WIDTH, HEIGHT - BAR_HEIGHT)
bar = pygame.rect.Rect(0, HEIGHT - BAR_HEIGHT, WIDTH, BAR_HEIGHT)

def create_wide_aspect_mosaic(mosaic_width=960, mosaic_height=540, 
                              resize_image_width=320, resize_image_height=180):
    cols = mosaic_width // resize_image_width
    rows = mosaic_height // resize_image_height
    boxes = []
    for row in range(rows):
        for col in range(cols):
            l = col * resize_image_width
            t = row * resize_image_height
            w = resize_image_width
            h = resize_image_height
            boxes.append((l, t, w, h))
    return boxes

def create_square_aspect_mosaic(mosaic_width=1024, mosaic_height=768, 
                                resize_image_width=256, resize_image_height=256):
    cols = mosaic_width // resize_image_width
    rows = mosaic_height // resize_image_height
    boxes = []
    for row in range(rows):
        for col in range(cols):
            l = col * resize_image_width
            t = row * resize_image_height
            w = resize_image_width
            h = resize_image_height
            boxes.append((l, t, w, h))
    return boxes

def get_best_pred_cloud_classifier(label, names=["clear", "clouds"]):
    label_text = label.read_text().strip().splitlines()
    if "clear" in label_text[0]:
        return 0
    else:
        return 1

class MosaicBox:
    """
    MosaicBox is a box that contains an image and a label
    If user clicks, label flip flops to opposite and the box is marked as corrected.
    """
    def __init__(self, rect, image, pred=0):
        self.rect = rect
        self.image_path = image
        self.image = pygame.image.load(image) if image else pygame.Surface((rect.width, rect.height))
        self.pred = pred
        self.corrected = False

    def draw(self, screen):
        return screen.blit(self.image, self.rect)
    
    def draw_label(self, screen):
        label_text = "CLEAR" if self.pred == 0 else "CLOUDS"
        label = LABEL_FONT.render(label_text, True, (255, 255, 255))
        label_rect = label.get_rect(topleft=(self.rect.left, self.rect.top))
        if self.pred is not None:
            pygame.draw.rect(screen, (CLEAR_COLOR, CLOUDS_COLOR)[self.pred], label_rect)
            screen.blit(label, label_rect)
        return screen

class Mosaic:
    """
    Mosaic is a collection of MosaicBoxes
    Each screen in pygame is a Mosaic
    """
    def __init__(self, rects):
        self.rects = rects
        self.boxes = []

    def get_boxes(self, sample):
        for i, (img_path, label) in enumerate(sample):
            rect = self.rects[i]
            new_box = MosaicBox(rect, img_path, label)
            self.boxes.append(new_box)

    def draw(self, screen):
        for box in self.boxes:
            box.draw(screen)
            box.draw_label(screen)
        return screen

class BinaryClassDataLoader:
    def __init__(self, images, labels, sample_size=9):
        self.images = images
        self.labels = labels
        self.sample_size = sample_size
        self.data = list(zip(self.images, self.labels))
        self.samples = self.data_to_sublists()

    def data_to_sublists(self):
        labeled_pairs = self.data
        sublists = []
        while labeled_pairs:
            sampled = random.sample(labeled_pairs, min(len(labeled_pairs), self.sample_size))
            labeled_pairs = [pair for pair in labeled_pairs if pair not in sampled]
            while len(sampled) < self.sample_size:
                sampled.append((None, None))
            sublists.append(sampled)
        return sublists

labeled_images = Path(input("Path to data folder"))
images = list(labeled_images.glob("*.jpg"))
labels = []

for image_path in images:
    label = get_best_pred_cloud_classifier(image_path.with_suffix(".txt"))
    labels.append(label)


data = BinaryClassDataLoader(images, labels)

mosaic_rects = [pygame.rect.Rect(*i) for i in create_wide_aspect_mosaic()]
mosaics = []
for sample in data.samples:
    new_mosaic = Mosaic(mosaic_rects)
    new_mosaic.get_boxes(sample)
    mosaics.append(new_mosaic)
    
print("NUM MOSAICS:", len(mosaics))

NEW_FRAME = True

mosaic_idx = 0
current_mosaic = mosaics[0]

RUN = True
while RUN:

    if NEW_FRAME:
        screen.fill((0, 0, 0))
        screen.fill((20, 20, 20), bar)
        current_mosaic = mosaics[mosaic_idx]
        current_mosaic.draw(screen)

    events = pygame.event.get() # get the events

    mx, my = pygame.mouse.get_pos()
    dx, dy = 0, 0
    mouse_action = None
    
    for event in events:
        if event.type == pygame.QUIT: # allow to click on the X button to close the window
            RUN = False
            break

        if event.type == pygame.MOUSEBUTTONDOWN:
            if event.button == 1:
                mouse_action = "DOWN"
                
        if event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                mouse_action = "UP"

        if event.type == pygame.MOUSEMOTION:
            mouse_action = "MOTION"
            dx, dy = event.rel

        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_q:
                mosaic_idx -= 1
                if mosaic_idx < 0:
                    mosaic_idx = len(mosaics) - 1
            elif event.key == pygame.K_e:
                mosaic_idx += 1
                if mosaic_idx > len(mosaics) - 1:
                    mosaic_idx = 0

    for box in current_mosaic.boxes:
        if mouse_action == "DOWN" and box.rect.collidepoint(mx, my):
            box.pred = 1 if box.pred == 0 else 0
            box.corrected = True
            NEW_FRAME = True
            break

    pygame.display.update()
    fpsClock.tick(MAX_FPS)

pygame.quit()

for mosaic in mosaics:
    for box in mosaic.boxes:
        if not box.image_path == None:
            print(" Image Path:", box.image_path, " Pred:", box.pred, " Corrected:", box.corrected)
