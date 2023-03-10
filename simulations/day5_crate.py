# Code areas
# player spawns at pixel standing pos of (288,352)
# direction is ALWAYS UP (0) based on the day/tile loc for the club
# Game1.createItemDebris(Item..., origin={X=352,Y=352}, direction=0)
# - updates the origin in switch
# - creates a Debris object at this origin (debrisType == -2)
# public Debris(int debrisType=-2, int numberOfChunks=1, Vector2 debrisOrigin, Vector2 playerPosition, float velocityMultiplyer)
# - if (playerPosition.Y >= debrisOrigin.Y - 32f && playerPosition.Y <= debrisOrigin.Y + 32f) 
# - else if (playerPosition.Y < debrisOrigin.Y - 32f) will fail as well
# - else 
# -     this clause runs and sets min/max y velocity to 350/400
# creates a chunk with yVelocity = random.NextInt(350,400)/40f
# runs the updateChunks call every frame which is where the nonsense logic goes in
# only worrying about Y positioning because we're within that 128px horizontal range (2 tiles)

import math
from collections import defaultdict
from csrandom import CSRandom

from scipy.stats import chisquare

def gen_samples(seed=0, n_samples=1000):
    r = CSRandom(seed)

    last_val = r.Sample()
    second_last_val = r.Sample()

    sample_counts = defaultdict(int)
    for i in range(n_samples):
        offset = int(second_last_val * 32)
        x_vel = (int(last_val*100)-50)/40 # doesn't matter, you'll be within 2 tiles
        n = r.Sample()
        y_vel = (int(n*50) + 350)
        second_last_val, last_val = last_val, n
        key = (offset, y_vel)
        sample_counts[key] = sample_counts[key] + 1
    return sample_counts

def roughly_equiv_distributed(n_samples=10_000_000):
    # want to ensure that calling random for the initial setup is uniform
    seed = 0
    sample_counts = gen_samples(seed, n_samples)
    counts = list(sample_counts.values())
    chi, p = chisquare(counts)
    assert p >= 0.05, "likely not uniformly distributed"
    print(f'chi: {chi}\tp: {p}')

class Day5Crate:
    def __init__(self, origin, velocity, farmer_y_pos):
        
        self.farmer_y_pos = farmer_y_pos
        self.tick = 0
        self.farmer = None

        self.movingFinalYLevel = True
        self.chunkFinalYLevel = origin - 1
        self.chunkFinalYTarget = origin - 96
        self.movingUp = True
        self.chunk_velocity = velocity / 40
        self.chunk_pos = origin - 32
        self.bounces = 0
        self.hasPassedRestingLineOnce = False
        self.timeSinceDoneBouncing = 0
        self.chunksMoveTowardPlayer = False

    def update(self):
        self.tick += 1
        self.timeSinceDoneBouncing += 16 # ms ticks are truncated from 16.6667
        if self.timeSinceDoneBouncing >= 600:
            self.chunksMoveTowardPlayer = True
            self.timeSinceDoneBouncing = 0
        if self.chunksMoveTowardPlayer:
            self.farmer = self.player_in_range()
        
        if self.farmer:
            if self.chunk_pos + 32 < self.farmer_y_pos - 12:
                self.chunk_velocity = max(self.chunk_velocity - 0.8, -8)
            elif self.chunk_velocity + 32 > self.farmer_y_pos + 12:
                self.chunk_velocity = min(self.chunk_velocity + 0.8, 8)
            self.chunk_pos -= self.chunk_velocity
            return self.success()
        else:
            self.chunk_pos -= self.chunk_velocity
            if self.movingFinalYLevel:
                self.chunkFinalYLevel -= int(math.ceil(self.chunk_velocity/2))
                if self.chunkFinalYLevel <= self.chunkFinalYTarget:
                    self.chunkFinalYLevel = self.chunkFinalYTarget
                    self.movingFinalYLevel = False

            if self.bounces <= 2:
                self.chunk_velocity -= 0.4

            if self.chunk_pos >= self.chunkFinalYLevel and self.hasPassedRestingLineOnce and self.bounces <= 2:
                self.bounces += 1
                self.chunk_velocity = abs(self.chunk_velocity * 2/3)

            if self.chunk_pos < self.chunkFinalYLevel:
                self.hasPassedRestingLineOnce = True

            if self.bounces > 2:
                self.chunk_velocity = 0
        return self.chunk_velocity == 0

    def player_in_range(self):
        return abs(self.chunk_pos + 32 - self.farmer_y_pos) <= 128
    
    def success(self):
        return abs(self.chunk_pos  + 32 - self.farmer_y_pos) <= 64

def sim_all(farmer_pos):
    res = []
    for offset in range(32):
        origin = 352 - 128 - offset
        for velocity in range(350,400):
            c = Day5Crate(origin, velocity, farmer_pos)
            while not c.update(): pass
            c.farmer_y_pos = 337 # scrub the wall to check
            if c.player_in_range():
                while not c.update(): pass
            if c.success():
                res.append((offset, velocity))
    return len(res) / 1600

if __name__ == '__main__':
    roughly_equiv_distributed(10_000_000)
    # 337 => up against the wall
    success_hold_wall = sim_all(337)
    # 352 => y height you spawn at
    # holds right, then up after the item comes to rest
    success_spawn_y = sim_all(352) 
    print("holding wall: ",success_hold_wall)
    print("spawn pos: ", success_spawn_y)