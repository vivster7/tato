from typing import TYPE_CHECKING
import random

if TYPE_CHECKING:
    from typing import List


class Animal:
    def __init__(self, name: str, age: int):
        self.name = name
        self.age = age

    def speak(self):
        raise NotImplementedError("Subclasses must implement this method")

    def __str__(self):
        return f"{self.name}, {self.age} years old"


class Dog(Animal):
    def speak(self):
        return "Woof!"


class Cat(Animal):
    def speak(self):
        return "Meow!"


class Bird(Animal):
    def speak(self):
        return "Tweet!"


def main():
    random.seed(42)  # For reproducible results
    num_animals = 10
    animals = generate_random_animals(num_animals)

    print("Animals:")
    for animal in animals:
        print(animal)

    print("\nAnimal Sounds:")
    print_animal_sounds(animals)

    oldest_animal = find_oldest_animal(animals)
    print(
        f"\nThe oldest animal is {oldest_animal.name}, who is {oldest_animal.age} years old."
    )


def generate_random_animals(num_animals: int) -> List[Animal]:
    animals = []
    for _ in range(num_animals):
        animal_type = random.choice([Dog, Cat, Bird])
        name = random.choice(["Max", "Bella", "Charlie", "Molly", "Buddy", "Luna"])
        age = random.randint(1, 15)
        animal = animal_type(name, age)
        animals.append(animal)
    return animals


def print_animal_sounds(animals: List[Animal]):
    for animal in animals:
        print(f"{animal.name} says {animal.speak()}")


def find_oldest_animal(animals: List[Animal]) -> Animal:
    oldest = max(animals, key=lambda animal: animal.age)
    return oldest


if __name__ == "__main__":
    main()
