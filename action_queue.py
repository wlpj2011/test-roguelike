from __future__ import annotations

from typing import Optional,List,Tuple,TYPE_CHECKING

if TYPE_CHECKING:
    from actions import Action
    from entity import Actor

class PriorityQueue:
    def __init__(self):
        self.__queue: List[List[Action, int]] = []

    def __len__(self):
        return len(self.__queue)

    def enqueue(self, action: Action, priority: float = 0.0)-> None:
        """
            Append a new element to the queue
            according to its priority.
        """

        tuple = [priority, action]

        # Insert the tuple in sorted position in the queue.  If a
        # tuple with equal priority is encountered, the new tuple is
        # inserted after it.

        finalPos = 0
        high = len(self)
        while finalPos < high:
            middle = (finalPos + high) // 2
            if tuple[0] < self.__queue[middle][0]:
                high = middle
            else:
                finalPos = middle + 1

        self.__queue.insert(finalPos, tuple)

    def adjust_priorities(self, add: int)->None:
        """
            Increases all priorities.
        """

        for v in self.__queue:
            v[0] += add

    def dequeue(self)->Action:
        """
            Pop the value with the lowest priority.
        """

        return self.__queue.pop(0)[1]

    def dequeue_with_key(self)->Tuple[int,Action]:
        """
            Pop the (priority, value) tuple with the lowest priority.
        """

        return self.__queue.pop(0)

    def erase(self, action: Action)->None:
        """
            Removes an element from the queue by value.
        """

        self.__erase(action, lambda a, b: a == b)

    def erase_ref(self, action: Action)->None:
        """
            Removes an element from the queue by reference.
        """

        self.__erase(action, lambda a, b: a is b)

    def __erase(self, action: Action, test)->None:
        """
            All tupples t are removed from the queue
            if test(t[1], value) evaluates to True.
        """

        i = 0
        while i < len(self.__queue):
            if test(self.__queue[i][1], action):
                del self.__queue[i]
            else:
                i += 1



class TimeSchedule(object):
    """
        Represents a series of events that occur over time.
    """

    def __init__(self):
        self.__scheduled_events: PriorityQueue = PriorityQueue()

    def schedule_action(self, action: Action, delay: float = 0.0)-> None:
        """
            Schedules an event to occur after a certain delay.
        """

        if action is not None:
            self.__scheduled_events.enqueue(action, delay)

    def next_actor(self)->Actor:
        priority, action = self.__scheduled_events.dequeue_with_key()
        self.schedule_action(action,priority)
        return action.entity

    def next_action(self)->Action:
        """
            Dequeues and returns the next event to occur.
        """

        time, action = self.__scheduled_events.dequeue_with_key()
        self.__scheduled_events.adjust_priorities(-time)

        return action

    def cancel_action(self, action)->None:
        """
            Cancels a pending event.
        """

        self.__scheduled_events.erase_ref(action)


class Thing(object):
    """
        Just something to test.
        Assumes that the maximum speed of a thing is 10.
    """

    BASE_TIME = 10.0

    def __init__(self, id, speed):
        self.id = id
        self.speed = speed

    def __str__(self):
        return self.id

    def action_delay(self):
        return Thing.BASE_TIME / self.speed

#---------------------------------------------------------------------



if __name__ == '__main__':
    TURN_ROUNDS = 3
    things = [Thing('a', 1), Thing('b', 2), Thing('c', 1)]
    q = TimeSchedule()

    turns = 0
    turnsTaken = {}
    for t in things:
        q.schedule_action(t, t.action_delay())
        turns += t.speed
        turnsTaken[t] = 0

    turns *= TURN_ROUNDS

    while turns > 0:
        thing = q.next_action()

        turnsTaken[thing] += 1
        print (thing)
        turns -= 1

        q.schedule_action(thing, thing.action_delay())

    for thing, numTurns in turnsTaken.items():
        assert numTurns == (thing.speed * TURN_ROUNDS)

    for id, numTurns in turnsTaken.items():
        print (id, numTurns)
