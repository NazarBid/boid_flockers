"""
Flockers
=============================================================
A Mesa implementation of Craig Reynolds's Boids flocker model.
Uses numpy arrays to represent vectors.
"""

import mesa
import numpy as np


class Boid(mesa.Agent):
    """
    A Boid-style flocker agent.

    The agent follows three behaviors to flock:
        - Cohesion: steering towards neighboring agents.
        - Separation: avoiding getting too close to any other agent.
        - Alignment: try to fly in the same direction as the neighbors.

    Boids have a vision that defines the radius in which they look for their
    neighbors to flock with. Their speed (a scalar) and direction (a vector)
    define their movement. Separation is their desired minimum distance from
    any other Boid.
    """

    def __init__(
        self,
        unique_id,
        model,
        speed,
        direction,
        vision,
        separation,
        cohere=0.03,
        separate=0.015,
        match=0.05,
    ):
        """
        Create a new Boid flocker agent.

        Args:
            speed: Distance to move per step.
            direction: numpy vector for the Boid's direction of movement.
            vision: Radius to look around for nearby Boids.
            separation: Minimum distance to maintain from other Boids.
            cohere: the relative importance of matching neighbors' positions
            separate: the relative importance of avoiding close neighbors
            match: the relative importance of matching neighbors' headings
        """
        super().__init__(unique_id,model)
        self.speed = speed
        self.direction = direction
        self.vision = vision
        self.separation = separation
        self.cohere_factor = cohere
        self.separate_factor = separate
        self.match_factor = match
        self.neighbors = None

    def step(self):
        """
        Get the Boid's neighbors, compute the new vector, and move accordingly.
        """

        self.neighbors = self.model.space.get_neighbors(self.pos, self.vision, False)
        n = 0
        match_vector, separation_vector, cohere = np.zeros((3, 2))
        for neighbor in self.neighbors:
            n += 1
            heading = self.model.space.get_heading(self.pos, neighbor.pos)
            cohere += heading
            if self.model.space.get_distance(self.pos, neighbor.pos) < self.separation:
                separation_vector -= heading
            match_vector += neighbor.direction
        n = max(n, 1)
        cohere = cohere * self.cohere_factor
        separation_vector = separation_vector * self.separate_factor
        match_vector = match_vector * self.match_factor
        self.direction += (cohere + separation_vector + match_vector) / n
        self.direction /= np.linalg.norm(self.direction)
        new_pos = self.pos + self.direction * self.speed
        self.model.space.move_agent(self, new_pos)


class BoidFlockers(mesa.Model):
    """
    Flocker model class. Handles agent creation, placement, and scheduling.
    """

    def __init__(
            self,
            seed=None,
            population=100,
            width=100,
            height=100,
            vision=10,
            speed=1,
            separation=1,
            cohere=0.03,
            separate=0.015,
            match=0.05,
    ):
        """
        Create a new Flockers model.
        """
        super().__init__(seed=seed)
        self.population = population
        self.vision = vision
        self.speed = speed
        self.separation = separation

        self.space = mesa.space.ContinuousSpace(width, height, True)
        self.factors = {"cohere": cohere, "separate": separate, "match": match}

        # Use RandomActivation scheduler
        self.schedule = mesa.time.RandomActivation(self)

        self.make_agents()

    def make_agents(self):
        """
        Create self.population agents, with random positions and starting headings.
        """
        for i in range(self.population):
            x = self.random.random() * self.space.x_max
            y = self.random.random() * self.space.y_max
            pos = np.array((x, y))
            direction = np.random.random(2) * 2 - 1
            boid = Boid(
                model=self,
                unique_id=i,
                speed=self.speed,
                direction=direction,
                vision=self.vision,
                separation=self.separation,
                **self.factors,
            )
            self.space.place_agent(boid, pos)

            # Add the boid to the scheduler instead of a list
            self.schedule.add(boid)

    def step(self):
        # Call the step method on each agent in the schedule
        self.schedule.step()
