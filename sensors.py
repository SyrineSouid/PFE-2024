import random

class Pressure:
    def __init__(self, channel, values=None):
        self.channel = channel
        self.values = values  # La liste des valeurs de pression
        self.current_index = 0  # Un index pour suivre la position actuelle dans la liste

    def get_value(self):
        if self.values is not None:
            # Parcourir les valeurs en inversant l'ordre (utilisation de reversed)
            reversed_values = list(reversed(self.values))  # Inverser les valeurs
            value = round(reversed_values[self.current_index] + random.uniform(0.0, 0.9), 2)
            self.current_index = (self.current_index + 1) % len(reversed_values)  # Tourner dans la liste inversée
            return [value]  # Retourner la valeur dans une liste comme demandé
        else:
            return ["no sensor connected"]  # Si aucune valeur, indiquer l'absence du capteur